"""
Phase Management Mixin
======================

Phase machine and transition handling for the executor.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..context_models import Fact, FactCategory
from ..phase_machine import PhaseContext, PhaseMachine
from ..state_store import Phase, TaskState
from ..working_memory import WorkingMemoryManager
from .helpers import determine_target_phase_legacy, determine_target_phase_with_machine

if TYPE_CHECKING:
    from ..state_store import TaskStateStore
    from .step_outcome import StepOutcome


class PhaseMixin:
    """
    Mixin for phase management in executor.

    Handles phase machine integration, transitions, and recovery.
    """

    # Type hints for attributes from main class
    use_phase_machine: bool
    state_store: "TaskStateStore"

    def _build_phase_context(
        self,
        machine: PhaseMachine,
        state: TaskState,
        last_action: str | None = None,
        last_action_result: str | None = None,
    ) -> PhaseContext:
        """Build PhaseContext for guard evaluation."""
        task_dir = self.state_store._task_dir(state.task_id)
        memory_manager = WorkingMemoryManager(task_dir)
        fact_dicts = memory_manager.get_facts(current_step=state.current_step)

        facts = [
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

        return PhaseContext(
            current_phase=machine.current_phase,
            steps_in_phase=machine.steps_in_phase,
            total_steps=state.current_step,
            verification_passing=state.verification.checks_failing == 0,
            tests_passing=state.verification.tests_passing,
            files_modified=state.context_data.get("files_modified", []),
            facts=facts,
            last_action=last_action,
            last_action_result=last_action_result,
        )

    def _handle_phase_transition(
        self,
        task_id: str,
        action_name: str,
        action_result: dict[str, Any],
        state: TaskState,
    ) -> None:
        """Handle phase transitions using PhaseMachine."""
        if not self.use_phase_machine:
            self._handle_legacy_phase_transition(task_id, action_name, action_result)
            return

        machine = state.get_phase_machine()
        context = self._build_phase_context(
            machine=machine, state=state,
            last_action=action_name, last_action_result=action_result.get("status"),
        )
        machine.advance_step()

        # Handle cannot_fix reason storage
        if action_name == "cannot_fix":
            reason = action_result.get("cannot_fix_reason", "Unknown reason")
            self.state_store.update_context_data(task_id, "cannot_fix_reason", reason)

        # Handle fatal error storage
        if action_result.get("status") == "failure" and action_result.get("fatal"):
            self.state_store.set_error(task_id, action_result.get("error", "Unknown error"))

        target_phase = determine_target_phase_with_machine(action_name, action_result, machine, context)
        self._apply_phase_transition(task_id, machine, target_phase, context)

    def _handle_legacy_phase_transition(
        self, task_id: str, action_name: str, action_result: dict[str, Any]
    ) -> None:
        """Handle phase transition in legacy mode (no phase machine)."""
        target_phase = determine_target_phase_legacy(action_name, action_result)
        if target_phase:
            self.state_store.update_phase(task_id, target_phase)
        if action_name == "cannot_fix":
            reason = action_result.get("cannot_fix_reason", "Unknown reason")
            self.state_store.update_context_data(task_id, "cannot_fix_reason", reason)
        if action_result.get("status") == "failure" and action_result.get("fatal"):
            self.state_store.set_error(task_id, action_result.get("error", "Unknown error"))

    def _apply_phase_transition(
        self, task_id: str, machine, target_phase: Phase | None, context
    ) -> None:
        """Apply phase transition to state store."""
        if not target_phase:
            self.state_store.update_phase_machine(task_id, machine)
            return

        if machine.can_transition(target_phase, context):
            machine.transition(target_phase, context)
            self.state_store.update_phase(task_id, target_phase)
        elif target_phase in (Phase.COMPLETE, Phase.ESCALATED, Phase.FAILED):
            machine._current_phase = target_phase
            machine._steps_in_phase = 0
            self.state_store.update_phase(task_id, target_phase)
        self.state_store.update_phase_machine(task_id, machine)

    def _check_phase_recovery_from_loop(
        self, task_id: str, outcome: "StepOutcome"
    ) -> tuple[bool, str | None]:
        """Check if phase transition should allow continuation despite loop detection."""
        state = self.state_store.load(task_id)
        if not state or not self.use_phase_machine:
            return False, None

        machine = state.get_phase_machine()
        phase_context = self._build_phase_context(
            machine=machine,
            state=state,
            last_action=outcome.action_name,
            last_action_result=outcome.result,
        )
        target_phase = machine.should_auto_transition(phase_context)
        if target_phase and target_phase != machine.current_phase:
            return True, f"Phase transition to {target_phase.value} pending"
        return False, None

    def _update_phase_from_action(self, task_id: str, action_name: str) -> None:
        """Update task phase based on action taken."""
        state = self.state_store.load(task_id)
        if not state:
            return

        phase_map = {
            "read_file": Phase.ANALYZE,
            "analyze_dependencies": Phase.ANALYZE,
            "detect_patterns": Phase.ANALYZE,
            "write_file": Phase.IMPLEMENT,
            "edit_file": Phase.IMPLEMENT,
            "run_check": Phase.VERIFY,
            "run_single_test": Phase.VERIFY,
        }

        new_phase = phase_map.get(action_name)
        if new_phase and new_phase != state.phase:
            self.state_store.update_phase(task_id, new_phase)
