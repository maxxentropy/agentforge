# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
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
- LLM-driven stage executors (Phase 2)
- Design pipeline stages: INTAKE, CLARIFY, ANALYZE, SPEC (Phase 2)
- TDD pipeline stages: RED, GREEN (Phase 3)

Example usage:
    from agentforge.core.pipeline import PipelineController, PipelineState

    # Create controller
    controller = PipelineController(project_path)

    # Create and execute a pipeline
    state = controller.create("Add a logout button", template="implement")
    state = controller.execute(state.pipeline_id)

    # Check status
    print(f"Pipeline status: {state.status.value}")

    # Register design stages
    from agentforge.core.pipeline.stages import register_design_stages
    register_design_stages(get_registry())
"""

# State management
# Phase 2: Artifact dataclasses
from .artifacts import (
    AnalyzeArtifact,
    ClarifyArtifact,
    DeliverArtifact,
    GreenArtifact,
    IntakeArtifact,
    RedArtifact,
    RefactorArtifact,
    SpecArtifact,
)

# Phase 6: Configuration System
from .config import (
    ConfigurationLoader,
    GlobalSettings,
    PipelineConfig,
    PipelineTemplate,
    PipelineTemplateLoader,
    StageConfig,
    expand_env_vars,
)
from .config_validator import (
    ConfigValidator,
)
from .config_validator import (
    ValidationError as ConfigValidationError,
)

# Pipeline controller
from .controller import (
    PipelineController,
    PipelineError,
    PipelineNotFoundError,
    PipelineResult,
    PipelineStateError,
)

# Escalation handling
from .escalation import (
    Escalation,
    EscalationHandler,
    EscalationStatus,
    EscalationType,
    generate_escalation_id,
)

# Phase 2: LLM Stage Executors
from .llm_stage_executor import (
    LLMStageExecutor,
    OutputValidation,
    ToolBasedStageExecutor,
)

# Stage registry
from .registry import (
    DuplicateStageError,
    StageExecutorRegistry,
    StageNotFoundError,
    get_registry,
    register_stage,
)

# Stage executor interface
from .stage_executor import (
    PassthroughExecutor,
    StageContext,
    StageExecutor,
    StageResult,
)
from .state import (
    PIPELINE_TEMPLATES,
    PipelineState,
    PipelineStatus,
    StageState,
    StageStatus,
    create_pipeline_state,
    generate_pipeline_id,
)

# State persistence
from .state_store import PipelineStateStore

# Artifact validation
from .validator import (
    ArtifactValidator,
    ValidationError,
    validate_artifacts,
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
    "PipelineResult",
    # Phase 2: LLM Stage Executors
    "LLMStageExecutor",
    "ToolBasedStageExecutor",
    "OutputValidation",
    # Phase 2: Artifacts
    "IntakeArtifact",
    "ClarifyArtifact",
    "AnalyzeArtifact",
    "SpecArtifact",
    "RedArtifact",
    "GreenArtifact",
    "RefactorArtifact",
    "DeliverArtifact",
    # Phase 6: Configuration
    "StageConfig",
    "PipelineTemplate",
    "GlobalSettings",
    "PipelineConfig",
    "ConfigurationLoader",
    "PipelineTemplateLoader",
    "expand_env_vars",
    "ConfigValidator",
    "ConfigValidationError",
]
