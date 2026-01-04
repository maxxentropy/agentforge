"""
Executor Helper Functions
=========================

Standalone helper functions for the executor module.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..context_models import Fact, FactCategory
    from ..state_store import Phase
    from ..working_memory import WorkingMemoryManager


def determine_target_phase_legacy(
    action_name: str, action_result: dict[str, Any]
) -> "Phase | None":
    """Determine target phase from action (legacy mode)."""
    from ..state_store import Phase

    if action_name == "complete" and action_result.get("status") == "success":
        return Phase.COMPLETE
    if action_name in ("escalate", "cannot_fix"):
        return Phase.ESCALATED
    if action_result.get("status") == "failure" and action_result.get("fatal"):
        return Phase.FAILED
    return None


def determine_target_phase_with_machine(
    action_name: str, action_result: dict[str, Any], machine, context
) -> "Phase | None":
    """Determine target phase from action with phase machine."""
    from ..state_store import Phase

    if action_name == "complete" and action_result.get("status") == "success":
        return Phase.COMPLETE
    if action_name in ("escalate", "cannot_fix"):
        return Phase.ESCALATED
    if action_result.get("status") == "failure" and action_result.get("fatal"):
        return Phase.FAILED
    return machine.should_auto_transition(context)


def convert_actions_to_dicts(recent_actions, fallback_step: int) -> list[dict]:
    """Convert recent actions to dict format for loop detection."""
    return [
        {
            "step": a.step if hasattr(a, 'step') else fallback_step,
            "action": a.action,
            "target": a.target if hasattr(a, 'target') else None,
            "parameters": a.parameters,
            "result": a.result,
            "summary": a.summary,
            "error": a.error,
        }
        for a in recent_actions
    ]


def load_facts_for_loop_detection(
    memory_manager: "WorkingMemoryManager", current_step: int
) -> list["Fact"]:
    """Load facts from working memory for loop detection."""
    from ..context_models import Fact, FactCategory

    fact_dicts = memory_manager.get_facts(current_step=current_step)
    return [
        Fact(
            id=f.get("id", ""),
            category=FactCategory(f.get("category", "inference")),
            statement=f.get("statement", ""),
            confidence=f.get("confidence", 0.5),
            source=f.get("source", "unknown"),
            step=f.get("step", 0),
        )
        for f in fact_dicts
    ]


def determine_final_status(outcomes: list) -> str:
    """Determine final task status from outcomes."""
    if not outcomes:
        return "no_outcomes"
    last = outcomes[-1]
    if last.action_name == "complete":
        return "completed"
    if last.action_name in ("escalate", "cannot_fix"):
        return "escalated"
    if last.error:
        return "failed"
    return "stopped"
