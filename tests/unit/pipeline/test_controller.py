# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-controller

"""Tests for pipeline controller."""

import pytest

from agentforge.core.pipeline import (
    PipelineController,
    PipelineState,
    PipelineStatus,
    PipelineStateStore,
    StageExecutor,
    StageContext,
    StageResult,
    StageStatus,
    StageExecutorRegistry,
    EscalationHandler,
    PipelineNotFoundError,
    PipelineStateError,
    PassthroughExecutor,
)


class TestPipelineController:
    """Tests for PipelineController."""

    @pytest.fixture
    def registry_with_stages(self, fresh_registry):
        """Create registry with all implement template stages."""
        stages = ["intake", "clarify", "analyze", "spec", "red", "green", "refactor", "deliver"]
        for stage in stages:
            fresh_registry.register(stage, lambda s=stage: PassthroughExecutor(s))
        return fresh_registry

    @pytest.fixture
    def controller(self, temp_project, registry_with_stages):
        """Create a controller with test registry."""
        return PipelineController(
            project_path=temp_project,
            registry=registry_with_stages,
        )

    def test_create_pipeline(self, controller):
        """create() creates and persists a new pipeline."""
        state = controller.create(
            request="Add a logout button",
            template="implement",
        )

        assert state.pipeline_id.startswith("PL-")
        assert state.template == "implement"
        assert state.status == PipelineStatus.PENDING
        assert state.request == "Add a logout button"

        # Should be persisted
        loaded = controller.get_status(state.pipeline_id)
        assert loaded.pipeline_id == state.pipeline_id

    def test_create_with_config(self, controller):
        """create() accepts configuration."""
        state = controller.create(
            request="Test",
            config={"verbose": True, "timeout": 60},
        )

        assert state.config["verbose"] is True
        assert state.config["timeout"] == 60

    def test_execute_single_stage(self, temp_project, fresh_registry):
        """execute() runs through a single-stage pipeline."""
        fresh_registry.register("analyze", lambda: PassthroughExecutor("analyze"))

        controller = PipelineController(
            project_path=temp_project,
            registry=fresh_registry,
        )

        state = controller.create("Test", template="test")  # test template: ["analyze", "red"]
        # But red isn't registered, so it should fail

        # Register red too
        fresh_registry.register("red", lambda: PassthroughExecutor("red"))

        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.COMPLETED

    def test_execute_multi_stage(self, controller):
        """execute() runs through multiple stages in order."""
        state = controller.create("Multi-stage test")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.COMPLETED

        # All stages should be completed
        for stage_name in state.stage_order:
            stage = state.stages[stage_name]
            assert stage.status == StageStatus.COMPLETED

    def test_execute_already_terminal(self, controller):
        """execute() raises error for terminal pipeline."""
        state = controller.create("Test")
        state = controller.execute(state.pipeline_id)

        with pytest.raises(PipelineStateError) as exc_info:
            controller.execute(state.pipeline_id)

        assert "terminal" in str(exc_info.value).lower()

    def test_execute_with_failure(self, temp_project, fresh_registry):
        """execute() stops on stage failure."""

        class FailingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.failed("Intentional failure")

        fresh_registry.register("intake", lambda: PassthroughExecutor("intake"))
        fresh_registry.register("clarify", FailingExecutor)  # Will fail

        controller = PipelineController(
            project_path=temp_project,
            registry=fresh_registry,
        )

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.FAILED
        assert state.stages["clarify"].status == StageStatus.FAILED
        assert state.stages["clarify"].error == "Intentional failure"

    def test_execute_with_escalation(self, temp_project, fresh_registry):
        """execute() pauses on escalation."""

        class EscalatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.escalate(
                    escalation_type="approval_required",
                    message="Please approve",
                )

        fresh_registry.register("intake", EscalatingExecutor)
        fresh_registry.register("clarify", lambda: PassthroughExecutor("clarify"))
        fresh_registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        fresh_registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(
            project_path=temp_project,
            registry=fresh_registry,
        )

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.WAITING_APPROVAL

        # Escalation should be created
        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        assert len(pending) == 1
        assert pending[0].message == "Please approve"

    def test_pause_and_resume(self, controller):
        """pause() and resume() work correctly."""
        state = controller.create("Test")
        state.status = PipelineStatus.RUNNING
        state.current_stage = "intake"
        controller.state_store.save(state)

        # Pause
        state = controller.pause(state.pipeline_id)
        assert state.status == PipelineStatus.PAUSED

        # Resume
        state = controller.resume(state.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED  # Runs to completion

    def test_resume_with_pending_escalation(self, temp_project, fresh_registry):
        """resume() fails if there are pending escalations."""

        class EscalatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.escalate(
                    escalation_type="approval_required",
                    message="Approve first",
                )

        fresh_registry.register("intake", EscalatingExecutor)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        # Should be waiting for approval
        assert state.status == PipelineStatus.WAITING_APPROVAL

        # Resume should fail
        with pytest.raises(PipelineStateError) as exc_info:
            controller.resume(state.pipeline_id)

        assert "pending escalations" in str(exc_info.value).lower()

    def test_approve_escalation(self, temp_project, fresh_registry):
        """approve() resolves escalation and continues."""
        call_count = [0]

        class EscalatingOnce(StageExecutor):
            def execute(self, context):
                call_count[0] += 1
                if call_count[0] == 1:
                    return StageResult.escalate(
                        escalation_type="approval_required",
                        message="Approve first",
                    )
                return StageResult.success()

        fresh_registry.register("intake", EscalatingOnce)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.WAITING_APPROVAL

        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        esc_id = pending[0].escalation_id

        # Approve should continue
        state = controller.approve(state.pipeline_id, esc_id, "Approved!")

        assert state.status == PipelineStatus.COMPLETED

    def test_reject_escalation(self, temp_project, fresh_registry):
        """reject() aborts the pipeline."""

        class EscalatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.escalate(
                    escalation_type="approval_required",
                    message="Approve first",
                )

        fresh_registry.register("intake", EscalatingExecutor)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        esc_id = pending[0].escalation_id

        state = controller.reject(state.pipeline_id, esc_id, "Not approved")

        assert state.status == PipelineStatus.ABORTED

    def test_abort_pipeline(self, controller):
        """abort() stops a running pipeline."""
        state = controller.create("Test")
        state.status = PipelineStatus.RUNNING
        state.current_stage = "clarify"
        state.stages["clarify"].mark_running()
        controller.state_store.save(state)

        state = controller.abort(state.pipeline_id, "User cancelled")

        assert state.status == PipelineStatus.ABORTED
        assert state.stages["clarify"].status == StageStatus.FAILED
        assert "User cancelled" in state.stages["clarify"].error

    def test_abort_already_terminal(self, controller):
        """abort() raises error for terminal pipeline."""
        state = controller.create("Test")
        state = controller.execute(state.pipeline_id)

        with pytest.raises(PipelineStateError):
            controller.abort(state.pipeline_id)

    def test_get_status(self, controller):
        """get_status() returns current pipeline state."""
        state = controller.create("Test")
        loaded = controller.get_status(state.pipeline_id)

        assert loaded.pipeline_id == state.pipeline_id
        assert loaded.status == state.status

    def test_get_status_not_found(self, controller):
        """get_status() raises error for unknown pipeline."""
        with pytest.raises(PipelineNotFoundError):
            controller.get_status("PL-99999999-nonexist")

    def test_stage_executor_not_found(self, temp_project, fresh_registry):
        """execute() handles missing stage executor."""
        # Only register intake
        fresh_registry.register("intake", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        # intake succeeds, clarify fails (not registered)
        assert state.status == PipelineStatus.FAILED
        assert "not registered" in state.stages["clarify"].error.lower()

    def test_stage_next_override(self, temp_project, fresh_registry):
        """Stage can override next stage."""

        class SkipToSpec(StageExecutor):
            def execute(self, context):
                return StageResult.success(next_stage="spec")

        fresh_registry.register("intake", SkipToSpec)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        # Should skip clarify and analyze
        assert state.stages["intake"].status == StageStatus.COMPLETED
        assert state.stages["clarify"].status == StageStatus.PENDING
        assert state.stages["analyze"].status == StageStatus.PENDING
        assert state.stages["spec"].status == StageStatus.COMPLETED

    def test_artifacts_flow_between_stages(self, temp_project, fresh_registry):
        """Artifacts from earlier stages flow to later stages."""
        received_artifacts = []

        class ArtifactProducer(StageExecutor):
            def execute(self, context):
                return StageResult.success({"produced_by": "producer"})

        class ArtifactConsumer(StageExecutor):
            def execute(self, context):
                received_artifacts.append(dict(context.input_artifacts))
                return StageResult.success()

        fresh_registry.register("intake", ArtifactProducer)
        fresh_registry.register("clarify", ArtifactConsumer)
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        state = controller.create("Test", template="design")
        controller.execute(state.pipeline_id)

        assert len(received_artifacts) == 1
        assert received_artifacts[0]["produced_by"] == "producer"

    def test_input_validation_failure(self, temp_project, fresh_registry):
        """Stage fails if input validation fails."""

        class ValidatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

            def get_required_inputs(self):
                return ["required_artifact"]

        fresh_registry.register("intake", lambda: PassthroughExecutor())
        fresh_registry.register("clarify", ValidatingExecutor)
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        state = controller.create("Test", template="design")
        state = controller.execute(state.pipeline_id)

        assert state.status == PipelineStatus.FAILED
        assert "required_artifact" in state.stages["clarify"].error
