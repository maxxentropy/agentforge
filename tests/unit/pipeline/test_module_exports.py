# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-init

"""Tests for pipeline module exports."""

import pytest


class TestModuleExports:
    """Tests for module public API exports."""

    def test_state_exports(self):
        """State management classes are exported."""
        from agentforge.core.pipeline import (
            PipelineState,
            PipelineStatus,
            StageState,
            StageStatus,
            create_pipeline_state,
            generate_pipeline_id,
            PIPELINE_TEMPLATES,
        )

        assert PipelineStatus.PENDING is not None
        assert StageStatus.COMPLETED is not None

    def test_state_store_exports(self):
        """State store class is exported."""
        from agentforge.core.pipeline import PipelineStateStore

        assert PipelineStateStore is not None

    def test_stage_executor_exports(self):
        """Stage executor classes are exported."""
        from agentforge.core.pipeline import (
            StageContext,
            StageExecutor,
            StageResult,
            PassthroughExecutor,
        )

        assert StageExecutor is not None
        assert PassthroughExecutor is not None

    def test_registry_exports(self):
        """Registry classes and functions are exported."""
        from agentforge.core.pipeline import (
            StageExecutorRegistry,
            StageNotFoundError,
            DuplicateStageError,
            get_registry,
            register_stage,
        )

        assert StageExecutorRegistry is not None
        assert get_registry is not None

    def test_validator_exports(self):
        """Validator classes are exported."""
        from agentforge.core.pipeline import (
            ArtifactValidator,
            ValidationError,
            validate_artifacts,
        )

        assert ArtifactValidator is not None
        assert ValidationError is not None

    def test_escalation_exports(self):
        """Escalation classes are exported."""
        from agentforge.core.pipeline import (
            Escalation,
            EscalationHandler,
            EscalationStatus,
            EscalationType,
            generate_escalation_id,
        )

        assert EscalationType.APPROVAL_REQUIRED is not None
        assert EscalationStatus.PENDING is not None

    def test_controller_exports(self):
        """Controller class and exceptions are exported."""
        from agentforge.core.pipeline import (
            PipelineController,
            PipelineError,
            PipelineNotFoundError,
            PipelineStateError,
        )

        assert PipelineController is not None
        assert issubclass(PipelineNotFoundError, PipelineError)
        assert issubclass(PipelineStateError, PipelineError)

    def test_all_defined(self):
        """__all__ is defined and complete."""
        from agentforge.core import pipeline

        assert hasattr(pipeline, "__all__")
        assert len(pipeline.__all__) > 0

        # Verify all items in __all__ are actually exported
        for name in pipeline.__all__:
            assert hasattr(pipeline, name), f"Missing export: {name}"

    def test_convenience_imports(self):
        """Common imports work from package level."""
        # This is the most common usage pattern
        from agentforge.core.pipeline import PipelineController, PipelineState

        # Can instantiate
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            controller = PipelineController(Path(td))
            state = controller.create("Test request")
            assert state.request == "Test request"
