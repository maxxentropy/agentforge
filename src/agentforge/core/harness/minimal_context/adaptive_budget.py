# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: adaptive-budget
# @test_path: tests/unit/harness/test_executor.py

"""
Adaptive Budget Manager
=======================

Manages dynamic step budgets with loop detection to prevent runaway execution.
Extracted from executor.py for modularity.

Key behaviors:
1. LOOP DETECTION: Enhanced detection via LoopDetector
   - Identical action loops
   - Semantic loops (different actions, same outcome)
   - Error cycling (A->B->A patterns)
   - No-progress loops
2. PROGRESS EXTENSION: Extend budget when making progress
3. HARD CEILING: Never exceed max_budget (cost control)
"""

import re
from typing import Any

from .context_models import ActionRecord, ActionResult
from .loop_detector import LoopDetection, LoopDetector


class AdaptiveBudget:
    """
    Adaptive step budget that prevents runaway while allowing complex tasks.

    Tracks progress and dynamically adjusts the step budget based on
    whether the agent is making meaningful progress toward the goal.
    """

    def __init__(
        self,
        base_budget: int = 15,
        max_budget: int = 50,
        runaway_threshold: int = 3,
        no_progress_threshold: int = 3,
        use_enhanced_loop_detection: bool = True,
    ):
        """
        Initialize adaptive budget.

        Args:
            base_budget: Starting step budget
            max_budget: Hard ceiling on steps (cost control)
            runaway_threshold: Failures before runaway detection
            no_progress_threshold: Steps without progress before stopping
            use_enhanced_loop_detection: Use enhanced LoopDetector
        """
        self.base_budget = base_budget
        self.max_budget = max_budget
        self.runaway_threshold = runaway_threshold
        self.no_progress_threshold = no_progress_threshold
        self._progress_count = 0
        self._no_progress_streak = 0
        self._last_violation_count: int | None = None

        # Enhanced loop detection
        self.use_enhanced_loop_detection = use_enhanced_loop_detection
        self.loop_detector = LoopDetector(
            identical_threshold=runaway_threshold,
            semantic_threshold=runaway_threshold + 1,
            cycle_threshold=2,
            no_progress_threshold=no_progress_threshold,
        ) if use_enhanced_loop_detection else None

        self._last_loop_detection: LoopDetection | None = None

    def check_continue(
        self,
        step_number: int,
        recent_actions: list[dict[str, Any]],
        facts: list[Any] | None = None,
    ) -> tuple[bool, str, LoopDetection | None]:
        """
        Determine if execution should continue.

        Args:
            step_number: Current step number (1-indexed)
            recent_actions: Last N action records
            facts: Optional list of facts for enhanced loop detection

        Returns:
            Tuple of (should_continue, reason, loop_detection)
        """
        self._last_loop_detection = None

        # 1. Enhanced loop detection
        if self.use_enhanced_loop_detection and self.loop_detector:
            loop_result = self._check_enhanced_loops(recent_actions, facts)
            if loop_result and loop_result.detected:
                self._last_loop_detection = loop_result
                return (
                    False,
                    f"STOPPED: {loop_result.loop_type.value.upper()} - {loop_result.description}",
                    loop_result,
                )
        else:
            if self._detect_runaway_legacy(recent_actions):
                return False, "STOPPED: Runaway detected (same action failed 3+ times)", None

        # 2. Update progress tracking
        progress_made = self._update_progress(recent_actions)

        # 3. No-progress detection
        if not progress_made:
            self._no_progress_streak += 1
            if self._no_progress_streak >= self.no_progress_threshold:
                return False, f"STOPPED: No progress for {self._no_progress_streak} consecutive steps", None
        else:
            self._no_progress_streak = 0

        # 4. Calculate dynamic budget
        dynamic_budget = self._calculate_budget()

        # 5. Check if within budget
        if step_number >= dynamic_budget:
            return False, f"STOPPED: Budget exhausted ({step_number}/{dynamic_budget} steps)", None

        return True, f"Continue (step {step_number}/{dynamic_budget})", None

    def _check_enhanced_loops(
        self,
        recent_actions: list[dict[str, Any]],
        facts: list[Any] | None = None,
    ) -> LoopDetection | None:
        """Use enhanced LoopDetector for semantic loop detection."""
        if not self.loop_detector or not recent_actions:
            return None

        action_records = []
        for i, action_dict in enumerate(recent_actions):
            result_str = action_dict.get("result", "success")
            result_enum = {
                "success": ActionResult.SUCCESS,
                "failure": ActionResult.FAILURE,
                "partial": ActionResult.PARTIAL,
            }.get(result_str, ActionResult.SUCCESS)

            record = ActionRecord(
                step=action_dict.get("step", i + 1),
                action=action_dict.get("action", "unknown"),
                target=action_dict.get("target"),
                parameters=action_dict.get("parameters", {}),
                result=result_enum,
                summary=action_dict.get("summary", ""),
                error=action_dict.get("error"),
            )
            action_records.append(record)

        return self.loop_detector.check(action_records, facts)

    def _detect_runaway_legacy(self, recent_actions: list[dict[str, Any]]) -> bool:
        """Legacy runaway detection: repeated identical failures."""
        if len(recent_actions) < self.runaway_threshold:
            return False

        last_n = recent_actions[-self.runaway_threshold:]

        if not all(a.get("result") == "failure" for a in last_n):
            return False

        actions = [a.get("action") for a in last_n]
        if len(set(actions)) != 1:
            return False

        first_params = last_n[0].get("parameters", {})
        for a in last_n[1:]:
            if a.get("parameters", {}) != first_params:
                if a.get("error") != last_n[0].get("error"):
                    return False

        return True

    def get_last_loop_detection(self) -> LoopDetection | None:
        """Get the last loop detection result."""
        return self._last_loop_detection

    def get_loop_suggestions(self) -> list[str]:
        """Get suggestions from the last loop detection."""
        if self._last_loop_detection and self._last_loop_detection.detected:
            return self._last_loop_detection.suggestions
        return []

    def _update_progress(self, recent_actions: list[dict[str, Any]]) -> bool:
        """Check if the most recent action made progress."""
        if not recent_actions:
            return False

        latest = recent_actions[-1]
        result = latest.get("result", "failure")
        action = latest.get("action", "")
        summary = latest.get("summary", "")

        # File modifications count as progress
        if result == "success" and action in [
            "write_file", "edit_file", "replace_lines", "insert_lines", "extract_function"
        ]:
            self._progress_count += 1
            return True

        # Passing checks count as major progress
        if "Check PASSED" in summary or "✓" in summary:
            self._progress_count += 3
            return True

        # Successful reads count as minor progress
        if result == "success" and action in ["read_file", "load_context"]:
            return True

        # Reducing violations counts as progress
        if action == "run_check" and "Violations" in summary:
            current_count = self._parse_violation_count(summary)
            if current_count is not None:
                if self._last_violation_count is not None:
                    if current_count < self._last_violation_count:
                        self._progress_count += 2
                        self._last_violation_count = current_count
                        return True
                self._last_violation_count = current_count

        return False

    def _parse_violation_count(self, summary: str) -> int | None:
        """Parse violation count from run_check summary."""
        match = re.search(r'Violations?\s*\((\d+)\)', summary)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)\s+violations?', summary, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _calculate_budget(self) -> int:
        """Calculate dynamic budget based on progress."""
        extension = self._progress_count * 3
        dynamic_budget = min(self.base_budget + extension, self.max_budget)
        return dynamic_budget

    def reset(self) -> None:
        """Reset budget state for a new task."""
        self._progress_count = 0
        self._no_progress_streak = 0
        self._last_violation_count = None
        self._last_loop_detection = None
        if self.loop_detector:
            self.loop_detector = LoopDetector(
                identical_threshold=self.runaway_threshold,
                semantic_threshold=self.runaway_threshold + 1,
                cycle_threshold=2,
                no_progress_threshold=self.no_progress_threshold,
            )
