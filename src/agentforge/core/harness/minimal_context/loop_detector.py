# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: harness-minimal_context-loop_detector
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Loop Detector
=============

Detects semantic loops and error cycling, not just repeated identical actions.

Types of loops detected:
1. IDENTICAL_ACTION: Same action + params repeated
2. SEMANTIC_LOOP: Different actions, same outcome
3. ERROR_CYCLE: A fails -> B fails -> A again
4. NO_PROGRESS: Actions succeed but nothing changes
5. OSCILLATION: Flip-flopping between states
"""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .context_models import ActionRecord, ActionResult, Fact, FactCategory


class LoopType(str, Enum):
    """Types of loops we can detect."""

    IDENTICAL_ACTION = "identical_action"  # Same action + params repeated
    SEMANTIC_LOOP = "semantic_loop"  # Different actions, same outcome
    ERROR_CYCLE = "error_cycle"  # A fails -> B fails -> A again
    NO_PROGRESS = "no_progress"  # Actions succeed but nothing changes
    OSCILLATION = "oscillation"  # Flip-flopping between states


@dataclass
class LoopDetection:
    """Result of loop detection."""

    detected: bool
    loop_type: Optional[LoopType] = None
    confidence: float = 0.0
    description: str = ""
    suggestions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)


@dataclass
class ActionSignature:
    """
    Semantic signature of an action for comparison.

    Two actions with the same signature are considered "semantically equivalent"
    even if their exact parameters differ.
    """

    action_type: str  # e.g., "edit", "extract", "check"
    target_file: Optional[str]  # Normalized file path
    target_entity: Optional[str]  # Function/class name
    outcome: ActionResult
    error_category: Optional[str] = None  # Normalized error type

    def matches(self, other: "ActionSignature", strict: bool = False) -> bool:
        """Check if signatures match."""
        if self.action_type != other.action_type:
            return False
        if self.outcome != other.outcome:
            return False
        if strict:
            return (
                self.target_file == other.target_file
                and self.target_entity == other.target_entity
            )
        return True


class LoopDetector:
    """
    Detects various types of loops in agent execution.

    Goes beyond simple "same action repeated" to detect:
    - Semantic loops (different actions with same result)
    - Error cycling (A->B->A pattern)
    - No-progress loops (actions succeed but state unchanged)
    - Oscillation (flip-flopping between states)
    """

    def __init__(
        self,
        identical_threshold: int = 3,
        semantic_threshold: int = 4,
        cycle_threshold: int = 2,
        no_progress_threshold: int = 4,
    ):
        """
        Initialize detector with configurable thresholds.

        Args:
            identical_threshold: Consecutive identical actions to trigger
            semantic_threshold: Semantically similar actions to trigger
            cycle_threshold: Error cycles (A->B->A) to trigger
            no_progress_threshold: No-progress steps to trigger
        """
        self.identical_threshold = identical_threshold
        self.semantic_threshold = semantic_threshold
        self.cycle_threshold = cycle_threshold
        self.no_progress_threshold = no_progress_threshold

        # State tracking
        self._action_history: List[ActionSignature] = []
        self._outcome_history: List[str] = []  # Normalized outcomes
        self._progress_markers: Set[str] = set()  # Things that indicate progress

    def check(
        self,
        actions: List[ActionRecord],
        facts: Optional[List[Fact]] = None,
    ) -> LoopDetection:
        """
        Check for loops in recent actions.

        Args:
            actions: Recent action records (most recent last)
            facts: Recent facts for context

        Returns:
            LoopDetection with results and suggestions
        """
        if len(actions) < 2:
            return LoopDetection(detected=False)

        # Extract signatures for comparison
        signatures = [self._to_signature(a) for a in actions]

        # Check each loop type in order of specificity

        # 1. Identical action loop (most specific)
        identical_result = self._check_identical(actions)
        if identical_result.detected:
            return identical_result

        # 2. Error cycle detection
        cycle_result = self._check_error_cycle(signatures)
        if cycle_result.detected:
            return cycle_result

        # 3. Semantic loop (different actions, same outcome)
        semantic_result = self._check_semantic_loop(signatures, facts)
        if semantic_result.detected:
            return semantic_result

        # 4. No-progress loop
        no_progress_result = self._check_no_progress(actions, facts)
        if no_progress_result.detected:
            return no_progress_result

        return LoopDetection(detected=False)

    def _to_signature(self, action: ActionRecord) -> ActionSignature:
        """Convert action record to semantic signature."""
        # Determine action type
        action_type = self._categorize_action(action.action)

        # Extract target info
        target_file = action.target
        target_entity = action.parameters.get(
            "function_name"
        ) or action.parameters.get("source_function")

        # Categorize error if present
        error_category = None
        if action.error:
            error_category = self._categorize_error(action.error)

        return ActionSignature(
            action_type=action_type,
            target_file=target_file,
            target_entity=target_entity,
            outcome=action.result,
            error_category=error_category,
        )

    def _categorize_action(self, action_name: str) -> str:
        """Categorize action into semantic groups."""
        categories = {
            "edit": ["edit_file", "replace_lines", "insert_lines", "write_file"],
            "extract": ["extract_function", "simplify_conditional"],
            "check": ["run_check", "run_conformance_check", "run_tests"],
            "read": ["read_file", "load_context"],
            "complete": ["complete", "escalate", "cannot_fix"],
        }
        for category, actions in categories.items():
            if action_name in actions:
                return category
        return action_name

    def _categorize_error(self, error: str) -> str:
        """Categorize error into semantic groups."""
        error_lower = error.lower()
        if "not found" in error_lower:
            return "not_found"
        if "syntax" in error_lower:
            return "syntax_error"
        if "control flow" in error_lower or "cannot extract" in error_lower:
            return "extraction_blocked"
        if "broke tests" in error_lower or "reverted" in error_lower:
            return "test_regression"
        return "other"

    def _check_identical(self, actions: List[ActionRecord]) -> LoopDetection:
        """Check for identical repeated actions."""
        if len(actions) < self.identical_threshold:
            return LoopDetection(detected=False)

        recent = actions[-self.identical_threshold :]

        # All same action name
        if len(set(a.action for a in recent)) != 1:
            return LoopDetection(detected=False)

        # All failures
        if not all(a.result == ActionResult.FAILURE for a in recent):
            return LoopDetection(detected=False)

        # Same parameters (or same error)
        first_params = recent[0].parameters
        first_error = recent[0].error
        all_same = True
        for a in recent[1:]:
            if a.parameters != first_params and a.error != first_error:
                all_same = False
                break

        if not all_same:
            return LoopDetection(detected=False)

        return LoopDetection(
            detected=True,
            loop_type=LoopType.IDENTICAL_ACTION,
            confidence=1.0,
            description=f"Action '{recent[0].action}' has failed {len(recent)} consecutive times with same parameters",
            suggestions=self._suggest_for_identical(recent),
            evidence=[f"Step {a.step}: {a.action} -> {a.result.value}" for a in recent],
        )

    def _check_error_cycle(
        self, signatures: List[ActionSignature]
    ) -> LoopDetection:
        """Check for A->B->A error cycling patterns."""
        if len(signatures) < 3:
            return LoopDetection(detected=False)

        # Look for cycles in failure sequences
        failures = [s for s in signatures if s.outcome == ActionResult.FAILURE]
        if len(failures) < 3:
            return LoopDetection(detected=False)

        # Check for A->B->A pattern
        cycle_count = 0
        for i in range(len(failures) - 2):
            if (
                failures[i].action_type == failures[i + 2].action_type
                and failures[i].action_type != failures[i + 1].action_type
            ):
                cycle_count += 1

        if cycle_count >= self.cycle_threshold:
            return LoopDetection(
                detected=True,
                loop_type=LoopType.ERROR_CYCLE,
                confidence=0.9,
                description="Detected error cycling: alternating between failed approaches",
                suggestions=[
                    "Both approaches have failed repeatedly",
                    "Consider a fundamentally different strategy",
                    "The code structure may not support the intended refactoring",
                    "Use 'cannot_fix' if no viable approach exists",
                ],
                evidence=[
                    f"{s.action_type} ({s.error_category})" for s in failures[-5:]
                ],
            )

        return LoopDetection(detected=False)

    def _check_semantic_loop(
        self,
        signatures: List[ActionSignature],
        facts: Optional[List[Fact]],
    ) -> LoopDetection:
        """Check for different actions with same semantic outcome."""
        if len(signatures) < self.semantic_threshold:
            return LoopDetection(detected=False)

        recent = signatures[-self.semantic_threshold :]

        # Different actions but all same outcome
        action_types = set(s.action_type for s in recent)
        if len(action_types) < 2:
            return LoopDetection(detected=False)  # Handled by identical check

        # All failures with same error category
        if all(s.outcome == ActionResult.FAILURE for s in recent):
            error_cats = set(s.error_category for s in recent if s.error_category)
            if len(error_cats) == 1:
                return LoopDetection(
                    detected=True,
                    loop_type=LoopType.SEMANTIC_LOOP,
                    confidence=0.85,
                    description=f"Multiple different approaches all failing with '{error_cats.pop()}' error",
                    suggestions=[
                        "The underlying issue persists across approaches",
                        "Re-examine the root cause before trying more variations",
                        "Consider if the violation is fixable automatically",
                    ],
                    evidence=[f"{s.action_type}: {s.error_category}" for s in recent],
                )

        # Check facts for repeated outcomes
        if facts:
            recent_facts = [f for f in facts if f.category == FactCategory.ERROR]
            error_statements = [f.statement for f in recent_facts[-5:]]
            # Check for similar error messages
            if len(set(error_statements)) == 1 and len(error_statements) >= 3:
                return LoopDetection(
                    detected=True,
                    loop_type=LoopType.SEMANTIC_LOOP,
                    confidence=0.8,
                    description="Different actions producing identical error outcome",
                    suggestions=["Address the common error before continuing"],
                    evidence=error_statements[:3],
                )

        return LoopDetection(detected=False)

    def _check_no_progress(
        self,
        actions: List[ActionRecord],
        facts: Optional[List[Fact]],
    ) -> LoopDetection:
        """Check for successful actions that don't advance the goal."""
        if len(actions) < self.no_progress_threshold:
            return LoopDetection(detected=False)

        recent = actions[-self.no_progress_threshold :]

        # Actions succeeded but all are just reading/checking
        non_mutating = {"read_file", "load_context", "run_check", "run_tests"}
        if all(a.action in non_mutating for a in recent):
            return LoopDetection(
                detected=True,
                loop_type=LoopType.NO_PROGRESS,
                confidence=0.75,
                description=f"Last {len(recent)} actions were read/check operations with no modifications",
                suggestions=[
                    "Analysis phase appears complete",
                    "Make an actual code modification",
                    "Use extract_function or edit_file to fix the violation",
                ],
                evidence=[f"Step {a.step}: {a.action}" for a in recent],
            )

        # Check if verification state hasn't changed
        if facts:
            verification_facts = [
                f
                for f in facts
                if f.category == FactCategory.VERIFICATION
                and "check" in f.statement.lower()
            ]
            if len(verification_facts) >= 3:
                # Same check result repeated
                statements = [f.statement for f in verification_facts[-3:]]
                if len(set(statements)) == 1:
                    return LoopDetection(
                        detected=True,
                        loop_type=LoopType.NO_PROGRESS,
                        confidence=0.7,
                        description="Verification status unchanged despite actions",
                        suggestions=["Actions are not affecting the violation"],
                        evidence=statements,
                    )

        return LoopDetection(detected=False)

    def _suggest_for_identical(self, actions: List[ActionRecord]) -> List[str]:
        """Generate suggestions for breaking identical action loops."""
        action = actions[0].action
        error = actions[0].error or ""

        suggestions = []

        if action == "edit_file":
            if "not found" in error.lower():
                suggestions.extend(
                    [
                        "The text to replace may have changed - re-read the file",
                        "Use replace_lines with line numbers instead of text matching",
                        "Check for whitespace differences (tabs vs spaces)",
                    ]
                )
            else:
                suggestions.append("Try a different edit approach")

        elif action == "extract_function":
            if "control flow" in error.lower():
                suggestions.extend(
                    [
                        "The selected lines contain early returns or breaks",
                        "Try simplify_conditional first to restructure the code",
                        "Select a different range that doesn't cross control flow boundaries",
                    ]
                )
            else:
                suggestions.extend(
                    [
                        "Check that line numbers are still valid (file may have changed)",
                        "Re-analyze the function to get updated extraction suggestions",
                    ]
                )

        elif action in ("run_check", "run_tests"):
            suggestions.extend(
                [
                    "Repeated checking without modification won't change the result",
                    "Make a code change before checking again",
                ]
            )

        # Generic suggestions
        if not suggestions:
            suggestions = [
                "Try a fundamentally different approach",
                "Re-analyze the problem from scratch",
                "Consider using 'escalate' if stuck",
            ]

        return suggestions

    def get_summary(self, actions: List[ActionRecord]) -> Dict[str, Any]:
        """Get summary statistics about action patterns."""
        if not actions:
            return {"total": 0}

        by_type: Dict[str, int] = defaultdict(int)
        by_result: Dict[str, int] = defaultdict(int)

        for a in actions:
            by_type[a.action] += 1
            by_result[a.result.value] += 1

        return {
            "total": len(actions),
            "by_action": dict(by_type),
            "by_result": dict(by_result),
            "success_rate": by_result.get("success", 0) / len(actions),
            "most_common": max(by_type.items(), key=lambda x: x[1])[0]
            if by_type
            else None,
        }

    def reset(self) -> None:
        """Reset internal state."""
        self._action_history = []
        self._outcome_history = []
        self._progress_markers = set()
