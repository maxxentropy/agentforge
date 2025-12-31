"""
Minimal Context Architecture
============================

Implements stateless step execution with verified state.

Key principle: Each step is a fresh conversation with exactly 2 messages:
1. System prompt (phase-appropriate)
2. Current context (built from persisted state)

Context size: 4-8K tokens ALWAYS, regardless of step number.

Enhanced Context Engineering (v2):
- Pydantic v2 models for validated, typed context
- Fact-based understanding instead of raw tool output
- Enhanced loop detection with semantic analysis
- Explicit phase machine with guards and transitions
"""

from .state_store import TaskStateStore, TaskState, TaskPhase
from .token_budget import TokenBudget, TOKEN_BUDGET_LIMITS
from .working_memory import WorkingMemoryManager, WorkingMemoryItem
from .context_schemas import ContextSchema, FixViolationSchema, get_schema_for_task
from .context_builder import ContextBuilder
from .executor import MinimalContextExecutor, StepOutcome
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

__all__ = [
    # State (legacy)
    "TaskStateStore",
    "TaskState",
    "TaskPhase",
    # Token Budget
    "TokenBudget",
    "TOKEN_BUDGET_LIMITS",
    # Working Memory
    "WorkingMemoryManager",
    "WorkingMemoryItem",
    # Context Schemas (legacy)
    "ContextSchema",
    "FixViolationSchema",
    "get_schema_for_task",
    # Context Building (legacy)
    "ContextBuilder",
    # Execution
    "MinimalContextExecutor",
    "StepOutcome",
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
]
