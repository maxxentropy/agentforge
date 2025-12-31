"""
REFACTOR Phase Executor
=======================

Cleans up implementation while maintaining passing tests.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def execute(self, component: ComponentProgress) -> PhaseResult:
        """
        Execute REFACTOR phase for a component.

        Args:
            component: Component to refactor

        Returns:
            PhaseResult indicating success/failure
        """
        start_time = time.time()

        # 1. Verify component is in GREEN state
        if component.status != ComponentStatus.GREEN:
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=False,
                component=component.name,
                errors=[f"Component must be in GREEN state, not {component.status.value}"],
                duration_seconds=time.time() - start_time,
            )

        # 2. Verify we have implementation
        if not component.implementation:
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=False,
                component=component.name,
                errors=["No implementation found - run GREEN phase first"],
                duration_seconds=time.time() - start_time,
            )

        # 3. Run conformance checks
        violations = self._run_conformance_check(component)

        # 4. If no violations and no obvious improvements, skip refactor
        if not violations and self._is_clean(component):
            # Mark as refactored without changes
            component.status = ComponentStatus.REFACTORED
            component.conformance_clean = True

            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=True,
                component=component.name,
                artifacts={"implementation": component.implementation.path},
                duration_seconds=time.time() - start_time,
            )

        # 5. Generate refactored implementation
        impl_path = component.implementation.path
        original_content = impl_path.read_text()

        refactored_content = self._refactor_implementation(
            component,
            original_content,
            violations,
        )

        if not refactored_content or refactored_content == original_content:
            # No changes made - that's OK
            component.status = ComponentStatus.REFACTORED
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=True,
                component=component.name,
                artifacts={"implementation": impl_path},
                duration_seconds=time.time() - start_time,
            )

        # 6. Write refactored implementation
        impl_path.write_text(refactored_content)

        # 7. Build and verify tests still pass
        if not self.runner.build():
            # Revert
            impl_path.write_text(original_content)
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=False,
                component=component.name,
                errors=["Refactored code failed to build - reverted"],
                duration_seconds=time.time() - start_time,
            )

        result = self.runner.run_tests(filter_pattern=component.name)

        if not result.all_passed:
            # Revert
            impl_path.write_text(original_content)
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=False,
                component=component.name,
                test_result=result,
                errors=["Tests failed after refactor - reverted"],
                duration_seconds=time.time() - start_time,
            )

        # 8. Verify no new conformance violations
        new_violations = self._run_conformance_check(component)
        if len(new_violations) > len(violations):
            # Revert
            impl_path.write_text(original_content)
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=False,
                component=component.name,
                errors=["Refactor introduced new conformance violations - reverted"],
                duration_seconds=time.time() - start_time,
            )

        # 9. Update component
        component.status = ComponentStatus.REFACTORED
        component.implementation = ImplementationFile(
            path=impl_path,
            content=refactored_content,
        )
        component.conformance_clean = len(new_violations) == 0
        component.coverage = self.runner.get_coverage()

        return PhaseResult(
            phase=TDFlowPhase.REFACTOR,
            success=True,
            component=component.name,
            artifacts={"implementation": impl_path},
            test_result=result,
            duration_seconds=time.time() - start_time,
        )

    def _run_conformance_check(self, component: ComponentProgress) -> List[Dict[str, Any]]:
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
        violations: List[Dict[str, Any]],
    ) -> Optional[str]:
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
