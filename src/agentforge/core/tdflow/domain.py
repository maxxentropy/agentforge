# @spec_file: .agentforge/specs/core-tdflow-v1.yaml
# @spec_id: core-tdflow-v1
# @component_id: core-tdflow-domain
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
TDFLOW Domain Model
===================

Domain entities for the Test-Driven Flow workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class TDFlowPhase(Enum):
    """Phases in the TDFLOW workflow."""

    INIT = "init"
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    VERIFY = "verify"
    DONE = "done"


class ComponentStatus(Enum):
    """Status of a component in TDFLOW."""

    PENDING = "pending"
    RED = "red"  # Tests generated, failing
    GREEN = "green"  # Implementation passes tests
    REFACTORED = "refactored"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class TestCase:
    """A generated test case."""

    name: str
    method_under_test: str
    scenario: str
    expected_result: str
    status: str = "pending"  # pending | pass | fail | error


@dataclass
class TestFile:
    """A generated test file."""

    path: Path
    content: str
    test_cases: list[TestCase] = field(default_factory=list)
    framework: str = "xunit"  # xunit | nunit | pytest | jest


@dataclass
class ImplementationFile:
    """A generated implementation file."""

    path: Path
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    coverage: float = 0.0


@dataclass
class ComponentProgress:
    """Progress tracking for a single component."""

    name: str
    status: ComponentStatus = ComponentStatus.PENDING
    tests: TestFile | None = None
    implementation: ImplementationFile | None = None
    coverage: float = 0.0
    conformance_clean: bool = True
    errors: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of running tests."""

    total: int
    passed: int
    failed: int
    errors: int
    duration_seconds: float
    output: str
    coverage: float | None = None

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed with no errors."""
        return self.passed == self.total and self.errors == 0 and self.total > 0

    @property
    def all_failed(self) -> bool:
        """Check if all tests failed or no tests passed."""
        return self.failed == self.total or self.passed == 0


@dataclass
class PhaseResult:
    """Result of executing a phase."""

    phase: TDFlowPhase
    success: bool
    component: str
    artifacts: dict[str, Path] = field(default_factory=dict)
    test_result: TestResult | None = None
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class VerificationReport:
    """Final verification report for a component."""

    component: str
    tests_passing: int
    tests_total: int
    coverage: float
    conformance_violations: int
    traceability: list[dict[str, str]] = field(default_factory=list)
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "component": self.component,
            "tests": {
                "passing": self.tests_passing,
                "total": self.tests_total,
            },
            "coverage": round(self.coverage, 2),
            "conformance_violations": self.conformance_violations,
            "traceability": self.traceability,
            "verified": self.verified,
        }


@dataclass
class SessionHistory:
    """A history entry in the session."""

    timestamp: datetime
    action: str
    phase: TDFlowPhase | None = None
    component: str | None = None
    details: str | None = None


@dataclass
class TDFlowSession:
    """
    TDFLOW session state.

    Persisted to disk to allow resume after interruption.
    """

    session_id: str
    started_at: datetime
    spec_file: Path
    spec_hash: str

    # Configuration
    test_framework: str = "xunit"
    coverage_threshold: float = 80.0
    auto_refactor: bool = False

    # Progress
    components: list[ComponentProgress] = field(default_factory=list)
    current_phase: TDFlowPhase = TDFlowPhase.INIT
    current_component: str | None = None

    # History
    history: list[SessionHistory] = field(default_factory=list)

    def get_component(self, name: str) -> ComponentProgress | None:
        """Get component by name."""
        for comp in self.components:
            if comp.name == name:
                return comp
        return None

    def get_next_pending(self) -> ComponentProgress | None:
        """Get next component to process."""
        for comp in self.components:
            if comp.status == ComponentStatus.PENDING:
                return comp
        return None

    def get_current_component(self) -> ComponentProgress | None:
        """Get the current component being worked on."""
        if self.current_component:
            return self.get_component(self.current_component)
        return self.get_next_pending()

    def all_verified(self) -> bool:
        """Check if all components are verified."""
        return all(c.status == ComponentStatus.VERIFIED for c in self.components)

    def add_history(
        self,
        action: str,
        phase: TDFlowPhase | None = None,
        component: str | None = None,
        details: str | None = None,
    ) -> None:
        """Add history entry."""
        self.history.append(
            SessionHistory(
                timestamp=datetime.utcnow(),
                action=action,
                phase=phase,
                component=component,
                details=details,
            )
        )

    def get_progress_summary(self) -> dict[str, int]:
        """Get summary of component statuses."""
        summary: dict[str, int] = {}
        for comp in self.components:
            status = comp.status.value
            summary[status] = summary.get(status, 0) + 1
        return summary
