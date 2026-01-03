# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-init

"""Tests for pipeline module exports."""



class TestModuleExports:
    """Tests for module public API exports."""

    def test_state_exports(self):
        """State management classes are exported."""
        from agentforge.core.pipeline import (
            PipelineStatus,
            StageStatus,
        )

        assert PipelineStatus.PENDING is not None, "Expected PipelineStatus.PENDING is not None"
        assert StageStatus.COMPLETED is not None, "Expected StageStatus.COMPLETED is not None"

    def test_state_store_exports(self):
        """State store class is exported."""
        from agentforge.core.pipeline import PipelineStateStore

        assert PipelineStateStore is not None, "Expected PipelineStateStore is not None"

    def test_stage_executor_exports(self):
        """Stage executor classes are exported."""
        from agentforge.core.pipeline import (
            PassthroughExecutor,
            StageExecutor,
        )

        assert StageExecutor is not None, "Expected StageExecutor is not None"
        assert PassthroughExecutor is not None, "Expected PassthroughExecutor is not None"

    def test_registry_exports(self):
        """Registry classes and functions are exported."""
        from agentforge.core.pipeline import (
            StageExecutorRegistry,
            get_registry,
        )

        assert StageExecutorRegistry is not None, "Expected StageExecutorRegistry is not None"
        assert get_registry is not None, "Expected get_registry is not None"

    def test_validator_exports(self):
        """Validator classes are exported."""
        from agentforge.core.pipeline import (
            ArtifactValidator,
            ValidationError,
        )

        assert ArtifactValidator is not None, "Expected ArtifactValidator is not None"
        assert ValidationError is not None, "Expected ValidationError is not None"

    def test_escalation_exports(self):
        """Escalation classes are exported."""
        from agentforge.core.pipeline import (
            EscalationStatus,
            EscalationType,
        )

        assert EscalationType.APPROVAL_REQUIRED is not None, "Expected EscalationType.APPROVAL_REQ... is not None"
        assert EscalationStatus.PENDING is not None, "Expected EscalationStatus.PENDING is not None"

    def test_controller_exports(self):
        """Controller class and exceptions are exported."""
        from agentforge.core.pipeline import (
            PipelineController,
            PipelineError,
            PipelineNotFoundError,
            PipelineStateError,
        )

        assert PipelineController is not None, "Expected PipelineController is not None"
        assert issubclass(PipelineNotFoundError, PipelineError), "Expected issubclass() to be truthy"
        assert issubclass(PipelineStateError, PipelineError), "Expected issubclass() to be truthy"

    def test_all_defined(self):
        """__all__ is defined and complete."""
        from agentforge.core import pipeline

        assert hasattr(pipeline, "__all__"), "Expected hasattr() to be truthy"
        assert len(pipeline.__all__) > 0, "Expected len(pipeline.__all__) > 0"

        # Verify all items in __all__ are actually exported
        for name in pipeline.__all__:
            assert hasattr(pipeline, name), f"Missing export: {name}"

    def test_convenience_imports(self):
        """Common imports work from package level."""
        # This is the most common usage pattern
        import tempfile

        # Can instantiate and use
        from pathlib import Path

        from agentforge.core.pipeline import (
            PipelineController,
            PipelineResult,
            PipelineState,
        )

        with tempfile.TemporaryDirectory() as td:
            controller = PipelineController(Path(td))
            # execute() is the public API - returns PipelineResult
            result = controller.execute("Test request", template="test")
            assert isinstance(result, PipelineResult), "Expected isinstance() to be truthy"
            # get_status() returns PipelineState
            state = controller.get_status(result.pipeline_id)
            assert isinstance(state, PipelineState), "Expected isinstance() to be truthy"
            assert state.request == "Test request", "Expected state.request to equal 'Test request'"
