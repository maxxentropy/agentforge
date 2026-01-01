# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: harness-minimal_context-__init__
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Minimal Context Architecture
============================

Implements stateless step execution with verified state.

Key principle: Each step is a fresh conversation with exactly 2 messages:
1. System prompt (phase-appropriate)
2. Current context (built from persisted state)

Context size: ~5000 tokens per step.

Enhanced Context Engineering (v2) - Always Enabled
--------------------------------------------------
All enhanced features are now the default:

- **PhaseMachine**: Explicit phase transitions with guards
- **EnhancedContextBuilder**: Pydantic v2 models for validated, typed context
- **Understanding Extraction**: Fact-based reasoning instead of raw tool output
- **Enhanced Loop Detection**: Semantic analysis (identical actions, error cycles)
- **Token Budget Enforcement**: Progressive compaction when over budget
- **Fact Compaction**: Proactive pruning (max 20 facts, prioritized by value)
- **Value Hints**: Precomputed context mapped to action parameter hints

Usage
-----
    from agentforge.core.harness.minimal_context import (
        MinimalContextFixWorkflow,
        create_minimal_fix_workflow,
    )

    # Direct instantiation
    workflow = MinimalContextFixWorkflow(project_path=Path("."))

    # Factory function
    workflow = create_minimal_fix_workflow(project_path=Path("."))

    # Fix a violation
    result = workflow.fix_violation("V-abc123")
"""

from .state_store import TaskStateStore, TaskState, TaskPhase, SCHEMA_VERSION
from .token_budget import TokenBudget, TOKEN_BUDGET_LIMITS, ENHANCED_TOKEN_LIMITS
from .working_memory import WorkingMemoryManager, WorkingMemoryItem
from .context_schemas import ContextSchema, FixViolationSchema, get_schema_for_task
from .context_builder import ContextBuilder
from .enhanced_context_builder import EnhancedContextBuilder, create_enhanced_context_builder
from .executor import MinimalContextExecutor, StepOutcome, AdaptiveBudget
from .fix_workflow import MinimalContextFixWorkflow, create_minimal_fix_workflow

# Enhanced Context Engineering (v2)
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

# Context Management V2 (with AGENT.md config, fingerprints, templates, audit)
from .executor_v2 import (
    MinimalContextExecutorV2,
    create_executor_v2,
    should_use_v2,
)
from .template_context_builder import (
    TemplateContextBuilder,
    TemplateStepContext,
)

__all__ = [
    # State
    "TaskStateStore",
    "TaskState",
    "TaskPhase",
    "SCHEMA_VERSION",
    # Token Budget
    "TokenBudget",
    "TOKEN_BUDGET_LIMITS",
    "ENHANCED_TOKEN_LIMITS",
    # Working Memory
    "WorkingMemoryManager",
    "WorkingMemoryItem",
    # Context Schemas (legacy)
    "ContextSchema",
    "FixViolationSchema",
    "get_schema_for_task",
    # Context Building (legacy)
    "ContextBuilder",
    # Context Building (enhanced - Phase 5)
    "EnhancedContextBuilder",
    "create_enhanced_context_builder",
    # Execution
    "MinimalContextExecutor",
    "StepOutcome",
    "AdaptiveBudget",
    # Fix Workflow
    "MinimalContextFixWorkflow",
    "create_minimal_fix_workflow",
    # ═══════════════════════════════════════════════════════════════════════════
    # Enhanced Context Engineering (v2)
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
    # Context Management V2 (AGENT.md, fingerprints, templates, audit)
    # ═══════════════════════════════════════════════════════════════════════════
    "MinimalContextExecutorV2",
    "create_executor_v2",
    "should_use_v2",
    "TemplateContextBuilder",
    "TemplateStepContext",
]
