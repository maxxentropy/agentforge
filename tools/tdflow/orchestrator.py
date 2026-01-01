# @spec_file: .agentforge/specs/tdflow-v1.yaml
# @spec_id: tdflow-v1
# @component_id: tools-tdflow-orchestrator
# @test_path: tests/unit/tools/tdflow/test_orchestrator.py

"""
TDFLOW Orchestrator
===================

Main orchestrator that coordinates the TDFLOW workflow.

Supports optional LLM-powered code generation via GenerationEngine.
When no generator is available, falls back to template-based generation.
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from tools.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    PhaseResult,
    TDFlowPhase,
    TDFlowSession,
    VerificationReport,
)
from tools.tdflow.phases.green import GreenPhaseExecutor
from tools.tdflow.phases.red import RedPhaseExecutor
from tools.tdflow.phases.refactor import RefactorPhaseExecutor
from tools.tdflow.phases.verify import VerifyPhaseExecutor
from tools.tdflow.runners.base import TestRunner
from tools.tdflow.session import SessionManager

if TYPE_CHECKING:
    from tools.generate.engine import GenerationEngine


class TDFlowOrchestrator:
    """
    Main orchestrator for TDFLOW workflow.

    Coordinates session management, phase execution, and progress tracking.
    Optionally integrates with LLM generation for intelligent code creation.
    """

    def __init__(
        self,
        project_path: Optional[Path] = None,
        generator: Optional["GenerationEngine"] = None,
    ):
        """
        Initialize TDFLOW orchestrator.

        Args:
            project_path: Root path of the project. Defaults to current directory.
            generator: Optional LLM generation engine for intelligent code generation.
                      When provided, phase executors use LLM for code/test generation.
                      When None, falls back to template-based generation.
        """
        self.project_path = project_path or Path.cwd()
        self.session_manager = SessionManager(self.project_path)
        self._session: Optional[TDFlowSession] = None
        self._runner: Optional[TestRunner] = None
        self._generator: Optional["GenerationEngine"] = generator

    @property
    def generator(self) -> Optional["GenerationEngine"]:
        """Get the generation engine if available."""
        return self._generator

    @generator.setter
    def generator(self, value: Optional["GenerationEngine"]) -> None:
        """Set the generation engine."""
        self._generator = value

    @property
    def session(self) -> Optional[TDFlowSession]:
        """Get current session, loading latest if not set."""
        if self._session is None:
            self._session = self.session_manager.get_latest()
        return self._session

    @property
    def runner(self) -> TestRunner:
        """Get test runner, detecting if not set."""
        if self._runner is None:
            if self.session:
                self._runner = TestRunner.for_framework(
                    self.session.test_framework,
                    self.project_path,
                )
            else:
                self._runner = TestRunner.detect(self.project_path)
        return self._runner

    def start(
        self,
        spec_file: Path,
        test_framework: str = "xunit",
        coverage_threshold: float = 80.0,
    ) -> TDFlowSession:
        """
        Start a new TDFLOW session.

        Args:
            spec_file: Path to specification.yaml
            test_framework: Test framework to use
            coverage_threshold: Required coverage percentage

        Returns:
            New TDFlowSession
        """
        self._session = self.session_manager.create(
            spec_file=spec_file,
            test_framework=test_framework,
            coverage_threshold=coverage_threshold,
        )
        self._runner = TestRunner.for_framework(test_framework, self.project_path)

        return self._session

    def run_red(self, component_name: Optional[str] = None) -> PhaseResult:
        """
        Execute RED phase for a component.

        Args:
            component_name: Specific component, or next pending

        Returns:
            PhaseResult from execution
        """
        if not self.session:
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component="",
                errors=["No active session. Run 'tdflow start' first."],
            )

        # Get component
        component = self._get_component(component_name)
        if not component:
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component_name or "",
                errors=["No component to process"],
            )

        # Execute RED phase
        executor = RedPhaseExecutor(self.session, self.runner, generator=self._generator)
        result = executor.execute(component)

        # Update session
        self.session.current_phase = TDFlowPhase.RED
        self.session.current_component = component.name
        self.session.add_history(
            action="red_phase",
            phase=TDFlowPhase.RED,
            component=component.name,
            details="success" if result.success else f"failed: {result.errors}",
        )
        self.session_manager.save(self.session)

        return result

    def run_green(self, component_name: Optional[str] = None) -> PhaseResult:
        """
        Execute GREEN phase for a component.

        Args:
            component_name: Specific component, or current component

        Returns:
            PhaseResult from execution
        """
        if not self.session:
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component="",
                errors=["No active session. Run 'tdflow start' first."],
            )

        # Get component
        component = self._get_component(component_name, status=ComponentStatus.RED)
        if not component:
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component=component_name or "",
                errors=["No component in RED state. Run 'tdflow red' first."],
            )

        # Execute GREEN phase
        executor = GreenPhaseExecutor(self.session, self.runner, generator=self._generator)
        result = executor.execute(component)

        # Update session
        self.session.current_phase = TDFlowPhase.GREEN
        self.session.current_component = component.name
        self.session.add_history(
            action="green_phase",
            phase=TDFlowPhase.GREEN,
            component=component.name,
            details="success" if result.success else f"failed: {result.errors}",
        )
        self.session_manager.save(self.session)

        return result

    def run_refactor(self, component_name: Optional[str] = None) -> PhaseResult:
        """
        Execute REFACTOR phase for a component.

        Args:
            component_name: Specific component, or current component

        Returns:
            PhaseResult from execution
        """
        if not self.session:
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=False,
                component="",
                errors=["No active session. Run 'tdflow start' first."],
            )

        # Get component
        component = self._get_component(component_name, status=ComponentStatus.GREEN)
        if not component:
            return PhaseResult(
                phase=TDFlowPhase.REFACTOR,
                success=False,
                component=component_name or "",
                errors=["No component in GREEN state. Run 'tdflow green' first."],
            )

        # Execute REFACTOR phase
        executor = RefactorPhaseExecutor(self.session, self.runner, generator=self._generator)
        result = executor.execute(component)

        # Update session
        self.session.current_phase = TDFlowPhase.REFACTOR
        self.session.current_component = component.name
        self.session.add_history(
            action="refactor_phase",
            phase=TDFlowPhase.REFACTOR,
            component=component.name,
            details="success" if result.success else f"failed: {result.errors}",
        )
        self.session_manager.save(self.session)

        return result

    def verify(self, component_name: Optional[str] = None) -> VerificationReport:
        """
        Execute VERIFY phase for a component.

        Args:
            component_name: Specific component, or all components

        Returns:
            VerificationReport
        """
        if not self.session:
            return VerificationReport(
                component="",
                tests_passing=0,
                tests_total=0,
                coverage=0.0,
                conformance_violations=0,
                verified=False,
            )

        executor = VerifyPhaseExecutor(self.session, self.runner)

        if component_name:
            # Verify specific component
            component = self.session.get_component(component_name)
            if not component:
                return VerificationReport(
                    component=component_name,
                    tests_passing=0,
                    tests_total=0,
                    coverage=0.0,
                    conformance_violations=0,
                    verified=False,
                )

            result = executor.execute(component)

            # Update session
            self.session.current_phase = TDFlowPhase.VERIFY
            self.session.add_history(
                action="verify_phase",
                phase=TDFlowPhase.VERIFY,
                component=component.name,
                details="verified" if result.success else f"failed: {result.errors}",
            )
            self.session_manager.save(self.session)

            return executor._load_report(component)
        else:
            # Verify all components
            reports = executor.verify_all()

            # Update session
            self.session.current_phase = TDFlowPhase.VERIFY
            self.session.add_history(
                action="verify_all",
                phase=TDFlowPhase.VERIFY,
                details=f"verified {len(reports)} components",
            )

            if self.session.all_verified():
                self.session.current_phase = TDFlowPhase.DONE
                self.session.add_history(action="session_complete")

            self.session_manager.save(self.session)

            # Return summary report
            if reports:
                return VerificationReport(
                    component="all",
                    tests_passing=sum(r.tests_passing for r in reports),
                    tests_total=sum(r.tests_total for r in reports),
                    coverage=sum(r.coverage for r in reports) / len(reports),
                    conformance_violations=sum(r.conformance_violations for r in reports),
                    traceability=[t for r in reports for t in r.traceability],
                    verified=all(r.verified for r in reports),
                )

            return VerificationReport(
                component="all",
                tests_passing=0,
                tests_total=0,
                coverage=0.0,
                conformance_violations=0,
                verified=False,
            )

    def resume(self) -> None:
        """
        Resume an interrupted session.

        Loads the latest session and continues from where it left off.
        """
        self._session = self.session_manager.get_latest()
        if self._session:
            self._runner = TestRunner.for_framework(
                self._session.test_framework,
                self.project_path,
            )
            self._session.add_history(action="session_resumed")
            self.session_manager.save(self._session)

    def get_status(self) -> dict:
        """
        Get current session status.

        Returns:
            Dictionary with session status information
        """
        if not self.session:
            return {"active": False, "message": "No active session"}

        return {
            "active": True,
            "session_id": self.session.session_id,
            "started_at": self.session.started_at.isoformat(),
            "spec_file": str(self.session.spec_file),
            "current_phase": self.session.current_phase.value,
            "current_component": self.session.current_component,
            "progress": self.session.get_progress_summary(),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "coverage": c.coverage,
                    "conformance_clean": c.conformance_clean,
                }
                for c in self.session.components
            ],
        }

    def _get_component(
        self,
        name: Optional[str] = None,
        status: Optional[ComponentStatus] = None,
    ) -> Optional[ComponentProgress]:
        """
        Get component by name or find appropriate one.

        Args:
            name: Component name, or None to find next
            status: Required status filter

        Returns:
            ComponentProgress or None
        """
        if not self.session:
            return None

        if name:
            component = self.session.get_component(name)
            if component and (status is None or component.status == status):
                return component
            return None

        # Find by status
        if status:
            for comp in self.session.components:
                if comp.status == status:
                    return comp
            return None

        # Return current or next pending
        if self.session.current_component:
            return self.session.get_component(self.session.current_component)

        return self.session.get_next_pending()
