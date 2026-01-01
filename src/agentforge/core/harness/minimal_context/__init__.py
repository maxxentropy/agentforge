# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: harness-minimal_context-__init__
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Minimal Context Architecture
============================

Implements stateless step execution with verified state.

Key principle: Each step is a fresh conversation with exactly 2 messages:
1. System prompt (phase-appropriate)
2. Current context (built from persisted state)

Context size: ~4000 tokens per step.

Features
--------
- **TemplateContextBuilder**: Task-type specific context templates
- **AGENT.md Configuration**: Hierarchical configuration chain
- **Dynamic Fingerprinting**: Project context generation
- **Audit Trail**: Full context snapshots for debugging
- **Progressive Compaction**: Token budget enforcement
- **PhaseMachine**: Explicit phase transitions with guards
- **Enhanced Loop Detection**: Semantic analysis (identical actions, error cycles)
- **Understanding Extraction**: Fact-based reasoning instead of raw tool output

Usage
-----
    from agentforge.core.harness.minimal_context import (
        MinimalContextFixWorkflow,
        create_minimal_fix_workflow,
    )

    # Factory function (recommended)
    workflow = create_minimal_fix_workflow(project_path=Path("."))

    # Fix a violation
    result = workflow.fix_violation("V-abc123")
"""

from .state_store import TaskStateStore, TaskState, TaskPhase, SCHEMA_VERSION
from .working_memory import WorkingMemoryManager, WorkingMemoryItem
from .executor import (
    MinimalContextExecutor,
    StepOutcome,
    AdaptiveBudget,
    create_executor,
    should_use_native_tools,
)
from .fix_workflow import MinimalContextFixWorkflow, create_minimal_fix_workflow

# Context Models
from .context_models import (
    # Enums
    FactCategory,
    ActionResult,
    # Core models
    Fact,
    ActionDef,
    ActionRecord,
    # Specs (immutable)
    TaskSpec,
    ViolationSpec,
    # State (mutable)
    VerificationState,
    Understanding,
    PhaseState,
    StateSpec,
    # Actions
    ActionsSpec,
    # Top-level
    AgentContext,
    AgentResponse,
)
from .understanding import (
    ExtractionRule,
    ExtractionRuleSet,
    UnderstandingExtractor,
    FactStore,
)
from .loop_detector import (
    LoopType,
    LoopDetection,
    ActionSignature,
    LoopDetector,
)
from .phase_machine import (
    Phase,
    PhaseContext,
    Transition,
    PhaseConfig,
    PhaseMachine,
)

# Template-based context building
from .template_context_builder import (
    TemplateContextBuilder,
    TemplateStepContext,
)
from .native_tool_executor import (
    NativeToolExecutor,
    ActionResult as NativeActionResult,
    create_standard_handlers,
)

__all__ = [
    # State
    "TaskStateStore",
    "TaskState",
    "TaskPhase",
    "SCHEMA_VERSION",
    # Working Memory
    "WorkingMemoryManager",
    "WorkingMemoryItem",
    # Execution
    "MinimalContextExecutor",
    "StepOutcome",
    "AdaptiveBudget",
    # Fix Workflow
    "MinimalContextFixWorkflow",
    "create_minimal_fix_workflow",
    # ═══════════════════════════════════════════════════════════════════════════
    # Context Engineering
    # ═══════════════════════════════════════════════════════════════════════════
    # Context Models - Enums
    "FactCategory",
    "ActionResult",
    # Context Models - Core
    "Fact",
    "ActionDef",
    "ActionRecord",
    # Context Models - Specs (immutable)
    "TaskSpec",
    "ViolationSpec",
    # Context Models - State (mutable)
    "VerificationState",
    "Understanding",
    "PhaseState",
    "StateSpec",
    # Context Models - Actions
    "ActionsSpec",
    # Context Models - Top-level
    "AgentContext",
    "AgentResponse",
    # Understanding Extraction
    "ExtractionRule",
    "ExtractionRuleSet",
    "UnderstandingExtractor",
    "FactStore",
    # Loop Detection
    "LoopType",
    "LoopDetection",
    "ActionSignature",
    "LoopDetector",
    # Phase Machine
    "Phase",
    "PhaseContext",
    "Transition",
    "PhaseConfig",
    "PhaseMachine",
    # ═══════════════════════════════════════════════════════════════════════════
    # Context Management (templates, AGENT.md config, fingerprints, audit)
    # ═══════════════════════════════════════════════════════════════════════════
    "create_executor",
    "should_use_native_tools",
    "TemplateContextBuilder",
    "TemplateStepContext",
    # Native Tool Execution
    "NativeToolExecutor",
    "NativeActionResult",
    "create_standard_handlers",
]
