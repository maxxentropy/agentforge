# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow-testing

"""
Test Verification Mixin
=======================

Methods for test verification and auto-revert functionality.
Implements the CORRECTNESS FIRST principle: modifications must not
break existing tests.
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import MinimalContextFixWorkflow
    from ..state_store import TaskState


class TestingMixin:
    """
    Test verification methods for fix workflow.

    Provides:
    - Pre/post test verification for file modifications
    - Automatic revert on test regression
    - Test failure counting
    """

    # Type hints for mixin - these are provided by the main class
    project_path: Path
    test_tools: Any
    state_store: Any

    def _save_file_for_revert(self, file_path: str | None) -> tuple[str | None, bool]:
        """Save file content for potential revert. Returns (content, existed)."""
        if not file_path:
            return None, False
        full_path = self.project_path / file_path
        if full_path.exists():
            return full_path.read_text(), True
        return None, False

    def _revert_file_changes(
        self, file_path: str | None, original_content: str | None, file_existed: bool
    ) -> None:
        """Revert file to original state."""
        if not file_path:
            return
        full_path = self.project_path / file_path
        if file_existed and original_content is not None:
            full_path.write_text(original_content)
        elif not file_existed and full_path.exists():
            full_path.unlink()

    def _build_test_revert_result(
        self, test_path: str | None, baseline_failures: int,
        after_failures: int, after_output: str
    ) -> dict[str, Any]:
        """Build failure result for reverted test failure."""
        return {
            "status": "failure",
            "error": "Modification broke tests - REVERTED",
            "summary": "✗ REVERTED - tests got worse",
            "output": (
                f"--- CORRECTNESS CHECK FAILED ---\n"
                f"✗ Modification introduced new test failures - changes REVERTED\n\n"
                f"Test path: {test_path or 'all tests'}\n"
                f"Before: {baseline_failures} failures\n"
                f"After: {after_failures} failures\n\n"
                f"Test output:\n{after_output[:800] if after_output else 'No output'}\n\n"
                f"The change was syntactically valid but broke behavior.\n"
                f"Original file content has been restored.\n"
                f"Try a different approach that preserves existing functionality."
            ),
        }

    def _count_test_failures(self, output: str) -> int:
        """Count test failures from pytest output."""
        import re
        if not output:
            return 0
        match = re.search(r"(\d+) failed", output)
        if match:
            return int(match.group(1))
        return 0

    def _check_tests_worsened(self, baseline_result: Any, after_result: Any) -> bool:
        """Check if tests got worse after modification."""
        baseline_failures = self._count_test_failures(baseline_result.output)
        after_failures = self._count_test_failures(after_result.output)
        return (
            (baseline_result.success and not after_result.success) or
            (after_failures > baseline_failures)
        )

    def _with_test_verification(self, action_fn: Callable) -> Callable:
        """
        Wrap a file-modifying action with test verification and auto-revert.

        CORRECTNESS FIRST principle: We cannot go from "violation" to "broken".
        """
        def wrapper(action_name: str, params: dict[str, Any], state: "TaskState") -> dict[str, Any]:
            file_path = params.get("path") or params.get("file_path") or state.context_data.get("file_path")
            test_path = state.context_data.get("test_path")

            # Run baseline tests
            baseline_result = self.test_tools.run_tests(
                "run_tests", {"test_path": test_path} if test_path else {}
            )
            baseline_failures = self._count_test_failures(baseline_result.output)

            original_content, file_existed = self._save_file_for_revert(file_path)
            result = action_fn(action_name, params, state)

            if result.get("status") == "failure":
                return result

            after_result = self.test_tools.run_tests(
                "run_tests", {"test_path": test_path} if test_path else {}
            )
            after_failures = self._count_test_failures(after_result.output)

            tests_got_worse = (
                (baseline_result.success and not after_result.success) or
                (after_failures > baseline_failures)
            )

            if tests_got_worse:
                self._revert_file_changes(file_path, original_content, file_existed)
                return self._build_test_revert_result(
                    test_path, baseline_failures, after_failures, after_result.output
                )

            test_status = "✓ Tests verified" if after_result.success else "○ No new failures"
            result["summary"] = f"{result.get('summary', '')} | {test_status}"
            result["output"] = (
                f"{result.get('output', '')}\n\n"
                f"--- CORRECTNESS VERIFIED ---\n"
                f"{test_status} (tested: {test_path or 'all'}, before: {baseline_failures}, after: {after_failures})"
            )

            return result

        return wrapper

    def _build_revert_result(
        self,
        action_name: str,
        file_path: str,
        error_msg: str,
        validation_output: str,
    ) -> dict[str, Any]:
        """Build failure result when validation fails and changes are reverted."""
        return {
            "status": "failure",
            "error": f"Validation failed - REVERTED: {error_msg}",
            "summary": f"✗ REVERTED - {action_name} produced invalid code",
            "output": (
                f"--- VALIDATION FAILED ---\n"
                f"✗ The modification produced invalid Python code - changes REVERTED\n\n"
                f"File: {file_path}\n"
                f"Error: {error_msg}\n\n"
                f"Validation output:\n{validation_output}\n\n"
                f"The original file content has been restored.\n"
                f"Try a different approach that produces valid Python code."
            ),
        }
