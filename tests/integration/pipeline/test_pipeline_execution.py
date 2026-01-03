# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1

"""End-to-end pipeline execution integration tests."""


from agentforge.core.pipeline import (
    PassthroughExecutor,
    PipelineController,
    PipelineStatus,
    StageExecutorRegistry,
    StageStatus,
)

from .conftest import ApprovalRequiredExecutor, FailAfterNExecutor


class TestSimplePipelineExecution:
    """Tests for simple pipeline execution scenarios."""

    def test_simple_design_pipeline(self, pipeline_controller):
        """Execute a simple design pipeline from start to finish."""
        result = pipeline_controller.execute(
            request="Add a logout button to the header",
            template="design",
        )

        assert result.success is True, "Expected result.success is True"
        assert result.pipeline_id.startswith("PL-"), "Expected result.pipeline_id.startswith() to be truthy"

        state = pipeline_controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"

        for stage_name in ["intake", "clarify", "analyze", "spec"]:
            assert state.stages[stage_name].status == StageStatus.COMPLETED, "Expected state.stages[stage_name].st... to equal StageStatus.COMPLETED"
            assert state.stages[stage_name].completed_at is not None, "Expected state.stages[stage_name].co... is not None"

    def test_full_implement_pipeline(self, pipeline_controller):
        """Execute a full implement pipeline with all 8 stages."""
        result = pipeline_controller.execute(
            request="Implement user authentication",
            template="implement",
        )

        assert result.success is True, "Expected result.success is True"
        state = pipeline_controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"

        expected_stages = [
            "intake", "clarify", "analyze", "spec",
            "red", "green", "refactor", "deliver"
        ]
        for stage_name in expected_stages:
            assert state.stages[stage_name].status == StageStatus.COMPLETED, "Expected state.stages[stage_name].st... to equal StageStatus.COMPLETED"

    def test_artifacts_flow_through_pipeline(self, pipeline_controller):
        """Verify artifacts from earlier stages are available to later stages."""
        result = pipeline_controller.execute(
            request="Test artifacts flow",
            template="design",
        )

        state = pipeline_controller.get_status(result.pipeline_id)
        all_artifacts = state.collect_artifacts()

        assert "parsed_request" in all_artifacts, "Expected 'parsed_request' in all_artifacts"
        assert "assumptions" in all_artifacts, "Expected 'assumptions' in all_artifacts"
        assert "affected_files" in all_artifacts, "Expected 'affected_files' in all_artifacts"
        assert "spec" in all_artifacts, "Expected 'spec' in all_artifacts"


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

        result = controller.execute("Test escalation", template="design")

        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.WAITING_APPROVAL, "Expected state.status to equal PipelineStatus.WAITING_APPR..."
        assert state.current_stage == "clarify", "Expected state.current_stage to equal 'clarify'"

        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        assert len(pending) == 1, "Expected len(pending) to equal 1"
        assert "Approve clarifications" in pending[0].message, "Expected 'Approve clarifications' in pending[0].message"

    def test_approve_and_continue(self, real_project_path):
        """Approving an escalation continues the pipeline."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))
        registry.register("clarify", lambda: ApprovalRequiredExecutor("Need approval"))
        registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(real_project_path, registry=registry)

        result = controller.execute("Test approval", template="design")

        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.WAITING_APPROVAL, "Expected state.status to equal PipelineStatus.WAITING_APPR..."

        success = controller.approve(state.pipeline_id)
        assert success is True, "Expected success is True"

        state = controller.get_status(state.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"

    def test_reject_aborts_pipeline(self, real_project_path):
        """Rejecting an escalation aborts the pipeline."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))
        registry.register("clarify", lambda: ApprovalRequiredExecutor("Need approval"))
        registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(real_project_path, registry=registry)

        result = controller.execute("Test rejection", template="design")

        success = controller.reject(result.pipeline_id, "Not approved")
        assert success is True, "Expected success is True"

        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.ABORTED, "Expected state.status to equal PipelineStatus.ABORTED"


class TestPipelineResumeAfterRestart:
    """Tests for pipeline state persistence and resume."""

    def test_state_survives_restart(self, real_project_path, full_registry):
        """Pipeline state survives controller restart."""
        controller1 = PipelineController(real_project_path, registry=full_registry)
        state = controller1._create("Persistence test", "design", {})
        pipeline_id = state.pipeline_id

        state.status = PipelineStatus.RUNNING
        state.current_stage = "intake"
        controller1.state_store.save(state)

        controller2 = PipelineController(real_project_path, registry=full_registry)

        loaded = controller2.get_status(pipeline_id)
        assert loaded.pipeline_id == pipeline_id, "Expected loaded.pipeline_id to equal pipeline_id"
        assert loaded.request == "Persistence test", "Expected loaded.request to equal 'Persistence test'"

    def test_resume_paused_pipeline(self, real_project_path, full_registry):
        """Paused pipeline can be resumed."""
        controller = PipelineController(real_project_path, registry=full_registry)

        state = controller._create("Resume test", "design", {})
        state.status = PipelineStatus.PAUSED
        state.current_stage = "clarify"
        state.stages["intake"].mark_completed({"done": True})
        controller.state_store.save(state)

        result = controller.resume(state.pipeline_id)

        assert result.success is True, "Expected result.success is True"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"


class TestPipelineAbort:
    """Tests for pipeline abort scenarios."""

    def test_abort_running_pipeline(self, real_project_path, full_registry):
        """Running pipeline can be aborted."""
        controller = PipelineController(real_project_path, registry=full_registry)

        state = controller._create("Abort test", "implement", {})
        state.status = PipelineStatus.RUNNING
        state.current_stage = "analyze"
        state.stages["analyze"].mark_running()
        controller.state_store.save(state)

        success = controller.abort(state.pipeline_id, "User cancelled")
        assert success is True, "Expected success is True"

        state = controller.get_status(state.pipeline_id)
        assert state.status == PipelineStatus.ABORTED, "Expected state.status to equal PipelineStatus.ABORTED"
        assert state.stages["analyze"].error == "User cancelled", "Expected state.stages['analyze'].error to equal 'User cancelled'"

    def test_abort_cleanup(self, real_project_path, full_registry):
        """Abort properly cleans up pipeline state."""
        controller = PipelineController(real_project_path, registry=full_registry)

        result = controller.execute("Cleanup test", template="design")

        # Should be completed, abort returns False
        success = controller.abort(result.pipeline_id)
        assert success is False, "Expected success is False"


class TestConcurrentPipelines:
    """Tests for running multiple pipelines concurrently."""

    def test_multiple_pipelines_isolation(self, real_project_path, full_registry):
        """Multiple pipelines run independently."""
        controller = PipelineController(real_project_path, registry=full_registry)

        result1 = controller.execute("Pipeline 1", template="design")
        result2 = controller.execute("Pipeline 2", template="design")
        result3 = controller.execute("Pipeline 3", template="design")

        assert result1.success is True, "Expected result1.success is True"
        assert result2.success is True, "Expected result2.success is True"
        assert result3.success is True, "Expected result3.success is True"

        state1 = controller.get_status(result1.pipeline_id)
        state2 = controller.get_status(result2.pipeline_id)
        state3 = controller.get_status(result3.pipeline_id)

        assert state1.collect_artifacts()["parsed_request"] == "Pipeline 1", "Expected state1.collect_artifacts()[... to equal 'Pipeline 1'"
        assert state2.collect_artifacts()["parsed_request"] == "Pipeline 2", "Expected state2.collect_artifacts()[... to equal 'Pipeline 2'"
        assert state3.collect_artifacts()["parsed_request"] == "Pipeline 3", "Expected state3.collect_artifacts()[... to equal 'Pipeline 3'"

    def test_list_active_pipelines(self, real_project_path, full_registry):
        """Can list all active pipelines."""
        controller = PipelineController(real_project_path, registry=full_registry)

        p1 = controller._create("Active 1", "implement", {})
        p2 = controller._create("Active 2", "implement", {})
        controller._create("Will complete", "design", {})

        controller.execute("Will complete", template="design")

        active = controller.state_store.list_active()
        active_ids = [s.pipeline_id for s in active]

        assert p1.pipeline_id in active_ids, "Expected p1.pipeline_id in active_ids"
        assert p2.pipeline_id in active_ids, "Expected p2.pipeline_id in active_ids"


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

        result = controller.execute("Failure test", template="design")

        assert result.success is False, "Expected result.success is False"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.FAILED, "Expected state.status to equal PipelineStatus.FAILED"
        assert state.stages["clarify"].status == StageStatus.FAILED, "Expected state.stages['clarify'].status to equal StageStatus.FAILED"
        assert "Clarify failed" in state.stages["clarify"].error, "Expected 'Clarify failed' in state.stages['clarify'].error"

        assert state.stages["analyze"].status == StageStatus.PENDING, "Expected state.stages['analyze'].status to equal StageStatus.PENDING"
        assert state.stages["spec"].status == StageStatus.PENDING, "Expected state.stages['spec'].status to equal StageStatus.PENDING"

    def test_missing_executor_fails_gracefully(self, real_project_path):
        """Missing stage executor causes graceful failure."""
        registry = StageExecutorRegistry()
        registry.register("intake", lambda: PassthroughExecutor("intake"))

        controller = PipelineController(real_project_path, registry=registry)

        result = controller.execute("Missing executor test", template="design")

        assert result.success is False, "Expected result.success is False"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.FAILED, "Expected state.status to equal PipelineStatus.FAILED"
        assert state.stages["intake"].status == StageStatus.COMPLETED, "Expected state.stages['intake'].status to equal StageStatus.COMPLETED"
        assert state.stages["clarify"].status == StageStatus.FAILED, "Expected state.stages['clarify'].status to equal StageStatus.FAILED"
        assert "not registered" in state.stages["clarify"].error.lower(), "Expected 'not registered' in state.stages['clarify'].err..."
