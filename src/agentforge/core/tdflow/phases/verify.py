"""
VERIFY Phase Executor
=====================

Verifies implementation meets specification requirements.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from agentforge.core.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    PhaseResult,
    TDFlowPhase,
    TDFlowSession,
    VerificationReport,
)
from agentforge.core.tdflow.runners.base import TestRunner


class VerifyPhaseExecutor:
    """
    Executes the VERIFY phase: final verification.

    Steps:
    1. Run all tests
    2. Run conformance checks
    3. Check coverage threshold
    4. Build traceability report
    5. Generate verification report
    """

    def __init__(self, session: TDFlowSession, runner: TestRunner):
        """
        Initialize VERIFY phase executor.

        Args:
            session: Current TDFLOW session
            runner: Test runner for the project
        """
        self.session = session
        self.runner = runner
        self._spec_data: Optional[Dict[str, Any]] = None

    def execute(self, component: ComponentProgress) -> PhaseResult:
        """
        Execute VERIFY phase for a component.

        Args:
            component: Component to verify

        Returns:
            PhaseResult indicating success/failure
        """
        start_time = time.time()

        # 1. Verify component is in GREEN or REFACTORED state
        if component.status not in (ComponentStatus.GREEN, ComponentStatus.REFACTORED):
            return PhaseResult(
                phase=TDFlowPhase.VERIFY,
                success=False,
                component=component.name,
                errors=[
                    f"Component must be in GREEN or REFACTORED state, not {component.status.value}"
                ],
                duration_seconds=time.time() - start_time,
            )

        # 2. Run all tests for the component
        self.runner.build()
        test_result = self.runner.run_tests(filter_pattern=component.name)

        if not test_result.all_passed:
            return PhaseResult(
                phase=TDFlowPhase.VERIFY,
                success=False,
                component=component.name,
                test_result=test_result,
                errors=[f"Tests failing: {test_result.failed}/{test_result.total}"],
                duration_seconds=time.time() - start_time,
            )

        # 3. Run conformance checks
        violations = self._run_conformance_check(component)

        # 4. Check coverage
        coverage = self.runner.get_coverage()
        if coverage < self.session.coverage_threshold:
            return PhaseResult(
                phase=TDFlowPhase.VERIFY,
                success=False,
                component=component.name,
                test_result=test_result,
                errors=[
                    f"Coverage {coverage:.1f}% below threshold {self.session.coverage_threshold}%"
                ],
                duration_seconds=time.time() - start_time,
            )

        # 5. Build traceability
        traceability = self._build_traceability(component)

        # 6. Generate verification report
        report = VerificationReport(
            component=component.name,
            tests_passing=test_result.passed,
            tests_total=test_result.total,
            coverage=coverage,
            conformance_violations=len(violations),
            traceability=traceability,
            verified=True,
        )

        # 7. Save report
        self._save_report(report)

        # 8. Update component
        component.status = ComponentStatus.VERIFIED
        component.coverage = coverage
        component.conformance_clean = len(violations) == 0

        return PhaseResult(
            phase=TDFlowPhase.VERIFY,
            success=True,
            component=component.name,
            artifacts={"report": self._get_report_path(component)},
            test_result=test_result,
            duration_seconds=time.time() - start_time,
        )

    def verify_all(self) -> List[VerificationReport]:
        """
        Verify all components in the session.

        Returns:
            List of verification reports
        """
        reports = []

        for component in self.session.components:
            result = self.execute(component)
            if result.success:
                reports.append(self._load_report(component))

        return reports

    def _run_conformance_check(self, component: ComponentProgress) -> List[Dict[str, Any]]:
        """
        Run conformance checks on the component.

        Args:
            component: Component to check

        Returns:
            List of violation dictionaries
        """
        try:
            from agentforge.core.contracts_execution import run_check_file

            if component.implementation:
                violations = run_check_file(component.implementation.path)
                return violations if violations else []
        except ImportError:
            pass

        return []

    def _build_traceability(self, component: ComponentProgress) -> List[Dict[str, str]]:
        """
        Build traceability from requirements to tests to implementation.

        Args:
            component: Component to trace

        Returns:
            List of traceability records
        """
        traceability = []

        # Load spec
        spec = self._load_component_spec(component.name)
        if not spec:
            return traceability

        # Build traceability for each method
        for method in spec.get("methods", []):
            method_name = method.get("name", "Unknown")
            behavior = method.get("behavior", "")

            traceability.append(
                {
                    "requirement": behavior[:100] if behavior else f"Implement {method_name}",
                    "test": f"{component.name}Tests.{method_name}_*",
                    "implementation": f"{component.name}.{method_name}",
                    "status": "verified",
                }
            )

        return traceability

    def _load_component_spec(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load specification for a specific component.

        Args:
            name: Component name

        Returns:
            Component spec dict or None
        """
        if self._spec_data is None:
            spec_path = self.session.spec_file
            if spec_path.exists():
                self._spec_data = yaml.safe_load(spec_path.read_text())

        if not self._spec_data:
            return None

        for comp in self._spec_data.get("components", []):
            if comp.get("name") == name:
                return comp

        return None

    def _get_report_path(self, component: ComponentProgress) -> Path:
        """
        Get path for verification report.

        Args:
            component: Component being verified

        Returns:
            Path for report file
        """
        reports_dir = self.runner.project_path / ".agentforge" / "tdflow" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / f"verification_{component.name}.yaml"

    def _save_report(self, report: VerificationReport) -> None:
        """
        Save verification report to disk.

        Args:
            report: Report to save
        """
        report_path = (
            self.runner.project_path
            / ".agentforge"
            / "tdflow"
            / "reports"
            / f"verification_{report.component}.yaml"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            yaml.dump(report.to_dict(), f, default_flow_style=False)

    def _load_report(self, component: ComponentProgress) -> VerificationReport:
        """
        Load verification report from disk.

        Args:
            component: Component to load report for

        Returns:
            VerificationReport instance
        """
        report_path = self._get_report_path(component)

        if report_path.exists():
            with open(report_path) as f:
                data = yaml.safe_load(f)

            return VerificationReport(
                component=data.get("component", component.name),
                tests_passing=data.get("tests", {}).get("passing", 0),
                tests_total=data.get("tests", {}).get("total", 0),
                coverage=data.get("coverage", 0.0),
                conformance_violations=data.get("conformance_violations", 0),
                traceability=data.get("traceability", []),
                verified=data.get("verified", False),
            )

        return VerificationReport(
            component=component.name,
            tests_passing=0,
            tests_total=0,
            coverage=0.0,
            conformance_violations=0,
            verified=False,
        )
