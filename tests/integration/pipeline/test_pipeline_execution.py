# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1

"""End-to-end pipeline execution integration tests."""

import pytest

from agentforge.core.pipeline import (
    PipelineController,
    PipelineState,
    PipelineStatus,
    PipelineStateStore,
    StageStatus,
    StageExecutorRegistry,
    PassthroughExecutor,
)

from .conftest import ApprovalRequiredExecutor, FailAfterNExecutor


class TestSimplePipelineExecution:
    """Tests for simple pipeline execution scenarios."""

    def test_simple_design_pipeline(self, pipeline_controller):
        """Execute a simple design pipeline from start to finish."""
        state = pipeline_controller.create(
            request="Add a logout button to the header",
            template="design",
        )

        assert state.status == PipelineStatus.PENDING
        assert state.pipeline_id.startswith("PL-")

        # Execute to completion
        state = pipeline_controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.COMPLETED

        # All stages should be completed
        for stage_name in ["intake", "clarify", "analyze", "spec"]:
            assert state.stages[stage_name].status == StageStatus.COMPLETED
            assert state.stages[stage_name].completed_at is not None

    def test_full_implement_pipeline(self, pipeline_controller):
        """Execute a full implement pipeline with all 8 stages."""
        state = pipeline_controller.create(
            request="Implement user authentication",
            template="implement",
        )

        state = pipeline_controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.COMPLETED

        # All 8 stages should be completed
        expected_stages = [
            "intake", "clarify", "analyze", "spec",
            "red", "green", "refactor", "deliver"
        ]
        for stage_name in expected_stages:
            assert state.stages[stage_name].status == StageStatus.COMPLETED

    def test_artifacts_flow_through_pipeline(self, pipeline_controller):
        """Verify artifacts from earlier stages are available to later stages."""
        state = pipeline_controller.create(
            request="Test artifacts flow",
            template="design",
        )

        state = pipeline_controller.execute(state.pipeline_id)

        # Collect all artifacts
        all_artifacts = state.collect_artifacts()

        # Should have artifacts from all completed stages
        assert "parsed_request" in all_artifacts  # From intake
        assert "assumptions" in all_artifacts  # From clarify
        assert "affected_files" in all_artifacts  # From analyze
        assert "spec" in all_artifacts  # From spec


class TestPipelineWithEscalation:
    """Tests for pipelines that require human intervention."""

    def test_pipeline_pauses_on_escalation(self, real_project_path):
        """Pipeline pauses when a stage escalates."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))
        registry.register("clarify", lambda: ApprovalRequiredExecutor("Approve clarifications"))
        registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(real_project_path, registry=registry)

        state = controller.create("Test escalation", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.WAITING_APPROVAL
        assert state.current_stage == "clarify"

        # Escalation should be recorded
        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        assert len(pending) == 1
        assert "Approve clarifications" in pending[0].message

    def test_approve_and_continue(self, real_project_path):
        """Approving an escalation continues the pipeline."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))
        registry.register("clarify", lambda: ApprovalRequiredExecutor("Need approval"))
        registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(real_project_path, registry=registry)

        state = controller.create("Test approval", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.WAITING_APPROVAL

        # Get escalation and approve
        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        esc_id = pending[0].escalation_id

        state = controller.approve(state.pipeline_id, esc_id, "Looks good!")

        # Pipeline should continue to completion
        assert state.status == PipelineStatus.COMPLETED

    def test_reject_aborts_pipeline(self, real_project_path):
        """Rejecting an escalation aborts the pipeline."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))
        registry.register("clarify", lambda: ApprovalRequiredExecutor("Need approval"))
        registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(real_project_path, registry=registry)

        state = controller.create("Test rejection", template="design")
        state = controller.execute(state.pipeline_id)

        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        esc_id = pending[0].escalation_id

        state = controller.reject(state.pipeline_id, esc_id, "Not approved")

        assert state.status == PipelineStatus.ABORTED


class TestPipelineResumeAfterRestart:
    """Tests for pipeline state persistence and resume."""

    def test_state_survives_restart(self, real_project_path, full_registry):
        """Pipeline state survives controller restart."""
        # Create first controller and start pipeline
        controller1 = PipelineController(real_project_path, registry=full_registry)
        state = controller1.create("Persistence test", template="design")
        pipeline_id = state.pipeline_id

        # Execute first stage only (simulate partial execution by pausing)
        state.status = PipelineStatus.RUNNING
        state.current_stage = "intake"
        controller1.state_store.save(state)

        # "Restart" - create new controller
        controller2 = PipelineController(real_project_path, registry=full_registry)

        # Load and verify state is preserved
        loaded = controller2.get_status(pipeline_id)
        assert loaded.pipeline_id == pipeline_id
        assert loaded.request == "Persistence test"

    def test_resume_paused_pipeline(self, real_project_path, full_registry):
        """Paused pipeline can be resumed."""
        controller = PipelineController(real_project_path, registry=full_registry)

        state = controller.create("Resume test", template="design")
        state.status = PipelineStatus.RUNNING
        state.current_stage = "clarify"
        state.stages["intake"].mark_completed({"done": True})
        controller.state_store.save(state)

        # Pause
        state = controller.pause(state.pipeline_id)
        assert state.status == PipelineStatus.PAUSED

        # Resume
        state = controller.resume(state.pipeline_id)

        # Should complete
        assert state.status == PipelineStatus.COMPLETED


class TestPipelineAbort:
    """Tests for pipeline abort scenarios."""

    def test_abort_running_pipeline(self, pipeline_controller):
        """Running pipeline can be aborted."""
        state = pipeline_controller.create("Abort test")
        state.status = PipelineStatus.RUNNING
        state.current_stage = "analyze"
        state.stages["analyze"].mark_running()
        pipeline_controller.state_store.save(state)

        state = pipeline_controller.abort(state.pipeline_id, "User cancelled")

        assert state.status == PipelineStatus.ABORTED
        assert state.stages["analyze"].error == "User cancelled"

    def test_abort_cleanup(self, real_project_path, full_registry):
        """Abort properly cleans up pipeline state."""
        controller = PipelineController(real_project_path, registry=full_registry)

        state = controller.create("Cleanup test")
        state = controller.execute(state.pipeline_id)

        # Should be completed, can't abort
        with pytest.raises(Exception):
            controller.abort(state.pipeline_id)


class TestConcurrentPipelines:
    """Tests for running multiple pipelines concurrently."""

    def test_multiple_pipelines_isolation(self, real_project_path, full_registry):
        """Multiple pipelines run independently."""
        controller = PipelineController(real_project_path, registry=full_registry)

        # Create multiple pipelines
        state1 = controller.create("Pipeline 1", template="design")
        state2 = controller.create("Pipeline 2", template="design")
        state3 = controller.create("Pipeline 3", template="design")

        # Execute all
        state1 = controller.execute(state1.pipeline_id)
        state2 = controller.execute(state2.pipeline_id)
        state3 = controller.execute(state3.pipeline_id)

        # All should complete independently
        assert state1.status == PipelineStatus.COMPLETED
        assert state2.status == PipelineStatus.COMPLETED
        assert state3.status == PipelineStatus.COMPLETED

        # Each should have its own artifacts
        assert state1.collect_artifacts()["parsed_request"] == "Pipeline 1"
        assert state2.collect_artifacts()["parsed_request"] == "Pipeline 2"
        assert state3.collect_artifacts()["parsed_request"] == "Pipeline 3"

    def test_list_active_pipelines(self, real_project_path, full_registry):
        """Can list all active pipelines."""
        controller = PipelineController(real_project_path, registry=full_registry)

        # Create pipelines, some active, some completed
        p1 = controller.create("Active 1")
        p2 = controller.create("Active 2")
        p3 = controller.create("Will complete")

        # Complete p3
        controller.execute(p3.pipeline_id)

        # List active
        active = controller.state_store.list_active()
        active_ids = [s.pipeline_id for s in active]

        assert p1.pipeline_id in active_ids
        assert p2.pipeline_id in active_ids
        assert p3.pipeline_id not in active_ids  # Completed


class TestPipelineFailures:
    """Tests for pipeline failure scenarios."""

    def test_stage_failure_stops_pipeline(self, real_project_path):
        """Pipeline stops when a stage fails."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))
        registry.register("clarify", lambda: FailAfterNExecutor(0, "Clarify failed"))
        registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(real_project_path, registry=registry)

        state = controller.create("Failure test", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.FAILED
        assert state.stages["clarify"].status == StageStatus.FAILED
        assert "Clarify failed" in state.stages["clarify"].error

        # Subsequent stages should still be pending
        assert state.stages["analyze"].status == StageStatus.PENDING
        assert state.stages["spec"].status == StageStatus.PENDING

    def test_missing_executor_fails_gracefully(self, real_project_path):
        """Missing stage executor causes graceful failure."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))
        # clarify not registered

        controller = PipelineController(real_project_path, registry=registry)

        state = controller.create("Missing executor test", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.FAILED
        assert state.stages["intake"].status == StageStatus.COMPLETED
        assert state.stages["clarify"].status == StageStatus.FAILED
        assert "not registered" in state.stages["clarify"].error.lower()
