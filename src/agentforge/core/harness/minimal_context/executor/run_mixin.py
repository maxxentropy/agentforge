"""
Run Management Mixin
====================

Run lifecycle, loop detection, and audit logging for the executor.
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ....context import ContextAuditLogger
from ..adaptive_budget import AdaptiveBudget
from ..context_models import ActionResult
from ..state_store import Phase
from ..working_memory import WorkingMemoryManager
from .helpers import convert_actions_to_dicts, determine_final_status, load_facts_for_loop_detection
from .step_outcome import StepOutcome

if TYPE_CHECKING:
    from ..state_store import TaskState, TaskStateStore
    from ..understanding import UnderstandingExtractor


class RunMixin:
    """
    Mixin for run management in executor.

    Handles run lifecycle, loop detection, and audit logging.
    """

    # Type hints for attributes from main class
    project_path: Path
    state_store: "TaskStateStore"
    audit_enabled: bool
    current_audit_logger: ContextAuditLogger | None
    _compaction_events: int
    _tokens_saved: int
    understanding_extractor: "UnderstandingExtractor"
    use_phase_machine: bool

    # Methods from other mixins
    _check_phase_recovery_from_loop: Callable
    _build_phase_context: Callable

    def _initialize_run(self, task_id: str) -> None:
        """Initialize audit logger and reset tracking for a run."""
        if self.audit_enabled:
            self.current_audit_logger = ContextAuditLogger(
                project_path=self.project_path,
                task_id=task_id,
            )
        self._compaction_events = 0
        self._tokens_saved = 0

    def _log_step(self, outcome: StepOutcome, task_id: str) -> None:
        """Log step to audit trail."""
        if not self.current_audit_logger:
            return

        state = self.state_store.load(task_id)
        if not state:
            return

        context = {
            "step": state.current_step,
            "phase": state.phase.value,
            "action": outcome.action_name,
            "action_params": outcome.action_params,
            "result": outcome.result,
        }

        token_breakdown = {
            "action": len(str(outcome.action_params)) // 4,
            "result": len(outcome.summary) // 4,
        }

        self.current_audit_logger.log_step(
            step=state.current_step,
            context=context,
            token_breakdown=token_breakdown,
            response=outcome.summary,
        )

    def _log_run_summary(self, outcomes: list[StepOutcome]) -> None:
        """Log task summary if audit is enabled."""
        if self.current_audit_logger and outcomes:
            final_status = determine_final_status(outcomes)
            total_tokens = sum(o.tokens_used for o in outcomes)
            self.current_audit_logger.log_task_summary(
                total_steps=len(outcomes),
                final_status=final_status,
                total_tokens=total_tokens,
                cached_tokens=0,
                compaction_events=self._compaction_events,
                tokens_saved=self._tokens_saved,
            )

    def _handle_loop_stop(
        self, outcomes: list[StepOutcome], loop_detection
    ) -> None:
        """Handle loop detection stop - update outcome and print suggestions."""
        if not loop_detection or not loop_detection.detected:
            return

        last_outcome = outcomes[-1]
        outcomes[-1] = StepOutcome(
            success=last_outcome.success,
            action_name=last_outcome.action_name,
            action_params=last_outcome.action_params,
            result=last_outcome.result,
            summary=last_outcome.summary,
            should_continue=False,
            tokens_used=last_outcome.tokens_used,
            duration_ms=last_outcome.duration_ms,
            error=last_outcome.error,
            loop_detected=loop_detection,
        )

        if loop_detection.suggestions:
            print("  Suggestions:")
            for suggestion in loop_detection.suggestions[:3]:
                print(f"    - {suggestion}")

    def _get_loop_detection_facts(self, task_id: str, budget: AdaptiveBudget):
        """Get facts for loop detection if enhanced detection is enabled."""
        if not budget.use_enhanced_loop_detection:
            return None
        task_dir = self.state_store._task_dir(task_id)
        memory_manager = WorkingMemoryManager(task_dir)
        state = self.state_store.load(task_id)
        if state:
            return load_facts_for_loop_detection(memory_manager, state.current_step)
        return None

    def _check_loop_continuation(
        self, task_id: str, outcome: StepOutcome, step: int, budget: AdaptiveBudget
    ) -> tuple[bool, str | None]:
        """Check if execution should continue based on budget and loop detection."""
        recent = self.state_store.get_recent_actions(task_id, limit=5)
        recent_dicts = convert_actions_to_dicts(recent, fallback_step=step)
        facts = self._get_loop_detection_facts(task_id, budget)

        should_continue, reason, loop_detection = budget.check_continue(step, recent_dicts, facts)

        # Allow phase transition even if loop detected
        if not should_continue and loop_detection and loop_detection.detected:
            can_recover, recovery_reason = self._check_phase_recovery_from_loop(task_id, outcome)
            if can_recover:
                print(f"  (Loop detected but {recovery_reason.lower()})")
                return True, None

        if not should_continue:
            self._handle_loop_stop([], loop_detection)
            return False, reason

        return True, None

    def _extract_and_store_facts(
        self,
        action_name: str,
        action_result: dict[str, Any],
        step: int,
        memory_manager: WorkingMemoryManager,
    ) -> None:
        """Extract facts from action result and store in working memory."""
        if not self.understanding_extractor:
            return

        status = action_result.get("status", "success")
        result_enum = {
            "success": ActionResult.SUCCESS,
            "failure": ActionResult.FAILURE,
            "partial": ActionResult.PARTIAL,
        }.get(status, ActionResult.SUCCESS)

        output = action_result.get("summary", "")
        if action_result.get("error"):
            output += f"\nError: {action_result['error']}"
        if action_result.get("raw_output"):
            output += f"\n{action_result['raw_output']}"

        facts = self.understanding_extractor.extract(
            tool_name=action_name,
            output=output,
            result=result_enum,
            step=step,
            use_llm_fallback=False,
        )

        if facts:
            memory_manager.add_facts_from_list(facts, step=step)

    def run_until_complete(
        self,
        task_id: str,
        max_iterations: int = 50,
        on_step: Callable[[StepOutcome], None] | None = None,
        adaptive_budget: AdaptiveBudget | None = None,
    ) -> list[StepOutcome]:
        """Run task until completion or budget exhausted."""
        self._initialize_run(task_id)

        outcomes = []
        budget = adaptive_budget or AdaptiveBudget(base_budget=15, max_budget=max_iterations)

        for i in range(max_iterations):
            outcome = self.execute_step(task_id)
            outcomes.append(outcome)
            self._log_step(outcome, task_id)

            if on_step:
                on_step(outcome)

            if not outcome.should_continue:
                break

            should_continue, reason = self._check_loop_continuation(task_id, outcome, i + 1, budget)
            if not should_continue:
                print(f"  {reason}")
                break

        self._log_run_summary(outcomes)
        return outcomes
