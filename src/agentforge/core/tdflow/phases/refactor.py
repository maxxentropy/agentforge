"""
REFACTOR Phase Executor
=======================

Cleans up implementation while maintaining passing tests.
"""

import time
from typing import Any

from agentforge.core.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    ImplementationFile,
    PhaseResult,
    TDFlowPhase,
    TDFlowSession,
)
from agentforge.core.tdflow.runners.base import TestRunner


class RefactorPhaseExecutor:
    """
    Executes the REFACTOR phase: clean up implementation.

    Steps:
    1. Load passing implementation
    2. Run conformance checks
    3. Identify improvement opportunities
    4. Generate refactored implementation
    5. Verify tests still pass
    6. Verify no new conformance violations
    """

    def __init__(self, session: TDFlowSession, runner: TestRunner):
        """
        Initialize REFACTOR phase executor.

        Args:
            session: Current TDFLOW session
            runner: Test runner for the project
        """
        self.session = session
        self.runner = runner

    def _fail(self, component: str, errors: list[str], start_time: float,
              test_result: Any = None) -> PhaseResult:
        """Create a failure PhaseResult."""
        return PhaseResult(
            phase=TDFlowPhase.REFACTOR, success=False, component=component,
            errors=errors, test_result=test_result,
            duration_seconds=time.time() - start_time)

    def _success(self, component: str, artifacts: dict, start_time: float,
                 test_result: Any = None) -> PhaseResult:
        """Create a success PhaseResult."""
        return PhaseResult(
            phase=TDFlowPhase.REFACTOR, success=True, component=component,
            artifacts=artifacts, test_result=test_result,
            duration_seconds=time.time() - start_time)

    def execute(self, component: ComponentProgress) -> PhaseResult:
        """Execute REFACTOR phase for a component."""
        start_time = time.time()

        # 1. Validate preconditions
        if component.status != ComponentStatus.GREEN:
            return self._fail(component.name,
                [f"Component must be in GREEN state, not {component.status.value}"], start_time)
        if not component.implementation:
            return self._fail(component.name,
                ["No implementation found - run GREEN phase first"], start_time)

        # 2. Run conformance checks
        violations = self._run_conformance_check(component)

        # 3. If already clean, skip refactor
        if not violations and self._is_clean(component):
            component.status = ComponentStatus.REFACTORED
            component.conformance_clean = True
            return self._success(component.name,
                {"implementation": component.implementation.path}, start_time)

        # 4. Generate refactored implementation
        impl_path = component.implementation.path
        original_content = impl_path.read_text()
        refactored_content = self._refactor_implementation(component, original_content, violations)

        if not refactored_content or refactored_content == original_content:
            component.status = ComponentStatus.REFACTORED
            return self._success(component.name, {"implementation": impl_path}, start_time)

        # 5. Apply and verify refactored implementation
        impl_path.write_text(refactored_content)
        result = self._verify_refactoring(component, impl_path, original_content, violations)
        if result:
            return result  # Verification failed, already reverted

        # 6. Update component state
        test_result = self.runner.run_tests(filter_pattern=component.name)
        component.status = ComponentStatus.REFACTORED
        component.implementation = ImplementationFile(path=impl_path, content=refactored_content)
        component.conformance_clean = len(self._run_conformance_check(component)) == 0
        component.coverage = self.runner.get_coverage()

        return self._success(component.name, {"implementation": impl_path}, start_time, test_result)

    def _verify_refactoring(self, component: ComponentProgress, impl_path: Any,
                            original_content: str, violations: list) -> PhaseResult | None:
        """Verify refactoring didn't break anything. Returns failure result or None if OK."""
        start_time = time.time()

        if not self.runner.build():
            impl_path.write_text(original_content)
            return self._fail(component.name, ["Refactored code failed to build - reverted"], start_time)

        result = self.runner.run_tests(filter_pattern=component.name)
        if not result.all_passed:
            impl_path.write_text(original_content)
            return self._fail(component.name, ["Tests failed after refactor - reverted"], start_time, result)

        new_violations = self._run_conformance_check(component)
        if len(new_violations) > len(violations):
            impl_path.write_text(original_content)
            return self._fail(component.name,
                ["Refactor introduced new conformance violations - reverted"], start_time)

        return None  # Verification passed

    def _run_conformance_check(self, component: ComponentProgress) -> list[dict[str, Any]]:
        """
        Run conformance checks on the component.

        Args:
            component: Component to check

        Returns:
            List of violation dictionaries
        """
        # Import conformance checking if available
        try:
            from agentforge.core.contracts_execution import run_check_file

            if component.implementation:
                violations = run_check_file(component.implementation.path)
                return violations if violations else []
        except ImportError:
            pass

        return []

    def _is_clean(self, component: ComponentProgress) -> bool:
        """
        Check if implementation is already clean.

        Args:
            component: Component to check

        Returns:
            True if no obvious improvements needed
        """
        # Simple heuristic - could be enhanced
        if not component.implementation:
            return True

        content = component.implementation.path.read_text()

        # Check for obvious issues
        issues = [
            "TODO" in content,
            "FIXME" in content,
            "NotImplementedException" in content,
            "raise NotImplementedError" in content,
        ]

        return not any(issues)

    def _refactor_implementation(
        self,
        component: ComponentProgress,
        content: str,
        violations: list[dict[str, Any]],
    ) -> str | None:
        """
        Generate refactored implementation.

        Uses tdflow.refactor.v1 prompt contract.

        Args:
            component: Component being refactored
            content: Current implementation content
            violations: List of conformance violations

        Returns:
            Refactored content or None
        """
        # For now, just return the original content
        # In a full implementation, this would use LLM with prompt contract
        return content
