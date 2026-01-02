# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-init
# @test_path: tests/unit/pipeline/test_module_exports.py

"""
Pipeline Controller Package
===========================

Core orchestration engine for autonomous development pipelines.

This module provides:
- Pipeline state management with YAML persistence
- Stage executor base classes and registry
- Pipeline controller for orchestrating stage execution
- Artifact validation and flow between stages
- Escalation handling for human intervention

Example usage:
    from agentforge.core.pipeline import PipelineController, PipelineState

    # Create controller
    controller = PipelineController(project_path)

    # Create and execute a pipeline
    state = controller.create("Add a logout button", template="implement")
    state = controller.execute(state.pipeline_id)

    # Check status
    print(f"Pipeline status: {state.status.value}")
"""

# State management
from .state import (
    PipelineState,
    PipelineStatus,
    StageState,
    StageStatus,
    create_pipeline_state,
    generate_pipeline_id,
    PIPELINE_TEMPLATES,
)

# State persistence
from .state_store import PipelineStateStore

# Stage executor interface
from .stage_executor import (
    StageContext,
    StageExecutor,
    StageResult,
    PassthroughExecutor,
)

# Stage registry
from .registry import (
    StageExecutorRegistry,
    StageNotFoundError,
    DuplicateStageError,
    get_registry,
    register_stage,
)

# Artifact validation
from .validator import (
    ArtifactValidator,
    ValidationError,
    validate_artifacts,
)

# Escalation handling
from .escalation import (
    Escalation,
    EscalationHandler,
    EscalationStatus,
    EscalationType,
    generate_escalation_id,
)

# Pipeline controller
from .controller import (
    PipelineController,
    PipelineError,
    PipelineNotFoundError,
    PipelineStateError,
)

__all__ = [
    # State
    "PipelineState",
    "PipelineStatus",
    "StageState",
    "StageStatus",
    "create_pipeline_state",
    "generate_pipeline_id",
    "PIPELINE_TEMPLATES",
    # State store
    "PipelineStateStore",
    # Stage executor
    "StageContext",
    "StageExecutor",
    "StageResult",
    "PassthroughExecutor",
    # Registry
    "StageExecutorRegistry",
    "StageNotFoundError",
    "DuplicateStageError",
    "get_registry",
    "register_stage",
    # Validator
    "ArtifactValidator",
    "ValidationError",
    "validate_artifacts",
    # Escalation
    "Escalation",
    "EscalationHandler",
    "EscalationStatus",
    "EscalationType",
    "generate_escalation_id",
    # Controller
    "PipelineController",
    "PipelineError",
    "PipelineNotFoundError",
    "PipelineStateError",
]
