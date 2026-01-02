# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: step-outcome
# @test_path: tests/unit/harness/test_executor.py

"""
Step Outcome Model
==================

Dataclass representing the result of executing a single agent step.
Extracted from executor.py for modularity.
"""

from dataclasses import dataclass
from typing import Any

from .loop_detector import LoopDetection


@dataclass
class StepOutcome:
    """
    Result of executing a single agent step.

    Attributes:
        success: Whether the step executed without errors
        action_name: Name of the action that was executed
        action_params: Parameters passed to the action
        result: Result status ("success", "failure", "partial")
        summary: Human-readable summary of the outcome
        should_continue: Whether execution should continue
        tokens_used: Number of tokens consumed in this step
        duration_ms: Execution time in milliseconds
        error: Error message if step failed
        loop_detected: Loop detection result if a loop was detected
    """

    success: bool
    action_name: str
    action_params: dict[str, Any]
    result: str  # "success", "failure", "partial"
    summary: str
    should_continue: bool
    tokens_used: int
    duration_ms: int
    error: str | None = None
    loop_detected: LoopDetection | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary representation.

        Used for serialization and audit logging.
        """
        result = {
            "success": self.success,
            "action_name": self.action_name,
            "action_params": self.action_params,
            "result": self.result,
            "summary": self.summary,
            "should_continue": self.should_continue,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }
        if self.loop_detected and self.loop_detected.detected:
            result["loop_detection"] = {
                "type": self.loop_detected.loop_type.value if self.loop_detected.loop_type else None,
                "description": self.loop_detected.description,
                "confidence": self.loop_detected.confidence,
                "suggestions": self.loop_detected.suggestions,
            }
        return result

    def is_terminal(self) -> bool:
        """Check if this outcome represents a terminal state."""
        return self.action_name in ("complete", "escalate", "cannot_fix") or not self.should_continue

    def is_error(self) -> bool:
        """Check if this outcome represents an error."""
        return self.error is not None or self.result == "failure"
