"""
Minimal Context Architecture
============================

Implements stateless step execution with verified state.

Key principle: Each step is a fresh conversation with exactly 2 messages:
1. System prompt (phase-appropriate)
2. Current context (built from persisted state)

Context size: 4-8K tokens ALWAYS, regardless of step number.
"""

from .state_store import TaskStateStore, TaskState, TaskPhase
from .token_budget import TokenBudget, TOKEN_BUDGET_LIMITS
from .working_memory import WorkingMemoryManager, WorkingMemoryItem
from .context_schemas import ContextSchema, FixViolationSchema, get_schema_for_task
from .context_builder import ContextBuilder
from .executor import MinimalContextExecutor, StepOutcome
from .fix_workflow import MinimalContextFixWorkflow, create_minimal_fix_workflow

__all__ = [
    # State
    "TaskStateStore",
    "TaskState",
    "TaskPhase",
    # Token Budget
    "TokenBudget",
    "TOKEN_BUDGET_LIMITS",
    # Working Memory
    "WorkingMemoryManager",
    "WorkingMemoryItem",
    # Context Schemas
    "ContextSchema",
    "FixViolationSchema",
    "get_schema_for_task",
    # Context Building
    "ContextBuilder",
    # Execution
    "MinimalContextExecutor",
    "StepOutcome",
    # Fix Workflow
    "MinimalContextFixWorkflow",
    "create_minimal_fix_workflow",
]
