"""Tests for TDFLOW domain entities."""

from datetime import datetime
from pathlib import Path

import pytest

from agentforge.core.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    TDFlowPhase,
    TDFlowSession,
    RunResult,
    VerificationReport,
)


class TestTDFlowPhase:
    """Tests for TDFlowPhase enum."""

    def test_phase_values(self):
        """Verify all phase values exist."""
        assert TDFlowPhase.INIT.value == "init", "Expected TDFlowPhase.INIT.value to equal 'init'"
        assert TDFlowPhase.RED.value == "red", "Expected TDFlowPhase.RED.value to equal 'red'"
        assert TDFlowPhase.GREEN.value == "green", "Expected TDFlowPhase.GREEN.value to equal 'green'"
        assert TDFlowPhase.REFACTOR.value == "refactor", "Expected TDFlowPhase.REFACTOR.value to equal 'refactor'"
        assert TDFlowPhase.VERIFY.value == "verify", "Expected TDFlowPhase.VERIFY.value to equal 'verify'"
        assert TDFlowPhase.DONE.value == "done", "Expected TDFlowPhase.DONE.value to equal 'done'"


class TestComponentStatus:
    """Tests for ComponentStatus enum."""

    def test_status_values(self):
        """Verify all status values exist."""
        assert ComponentStatus.PENDING.value == "pending", "Expected ComponentStatus.PENDING.value to equal 'pending'"
        assert ComponentStatus.RED.value == "red", "Expected ComponentStatus.RED.value to equal 'red'"
        assert ComponentStatus.GREEN.value == "green", "Expected ComponentStatus.GREEN.value to equal 'green'"
        assert ComponentStatus.REFACTORED.value == "refactored", "Expected ComponentStatus.REFACTORED.... to equal 'refactored'"
        assert ComponentStatus.VERIFIED.value == "verified", "Expected ComponentStatus.VERIFIED.value to equal 'verified'"
        assert ComponentStatus.FAILED.value == "failed", "Expected ComponentStatus.FAILED.value to equal 'failed'"


class TestRunResult:
    """Tests for RunResult dataclass."""

    def test_all_passed_when_all_pass(self):
        """All passed returns true when all tests pass."""
        result = RunResult(
            total=5, passed=5, failed=0, errors=0, duration_seconds=1.0, output=""
        )
        assert result.all_passed is True, "Expected result.all_passed is True"

    def test_all_passed_false_when_some_fail(self):
        """All passed returns false when some fail."""
        result = RunResult(
            total=5, passed=3, failed=2, errors=0, duration_seconds=1.0, output=""
        )
        assert result.all_passed is False, "Expected result.all_passed is False"

    def test_all_passed_false_when_errors(self):
        """All passed returns false when there are errors."""
        result = RunResult(
            total=5, passed=5, failed=0, errors=1, duration_seconds=1.0, output=""
        )
        assert result.all_passed is False, "Expected result.all_passed is False"

    def test_all_passed_false_when_no_tests(self):
        """All passed returns false when no tests exist."""
        result = RunResult(
            total=0, passed=0, failed=0, errors=0, duration_seconds=0.0, output=""
        )
        assert result.all_passed is False, "Expected result.all_passed is False"

    def test_all_failed_when_none_pass(self):
        """All failed returns true when no tests pass."""
        result = RunResult(
            total=5, passed=0, failed=5, errors=0, duration_seconds=1.0, output=""
        )
        assert result.all_failed is True, "Expected result.all_failed is True"


class TestVerificationReport:
    """Tests for VerificationReport dataclass."""

    def test_to_dict(self):
        """Verify to_dict serialization."""
        report = VerificationReport(
            component="TestComponent",
            tests_passing=8,
            tests_total=10,
            coverage=85.5,
            conformance_violations=2,
            traceability=[{"requirement": "R1", "test": "T1"}],
            verified=True,
        )

        result = report.to_dict()

        assert result["component"] == "TestComponent", "Expected result['component'] to equal 'TestComponent'"
        assert result["tests"]["passing"] == 8, "Expected result['tests']['passing'] to equal 8"
        assert result["tests"]["total"] == 10, "Expected result['tests']['total'] to equal 10"
        assert result["coverage"] == 85.5, "Expected result['coverage'] to equal 85.5"
        assert result["conformance_violations"] == 2, "Expected result['conformance_violati... to equal 2"
        assert result["verified"] is True, "Expected result['verified'] is True"
        assert len(result["traceability"]) == 1, "Expected len(result['traceability']) to equal 1"


class TestTDFlowSession:
    """Tests for TDFlowSession dataclass."""

    @pytest.fixture
    def session(self) -> TDFlowSession:
        """Create a test session."""
        return TDFlowSession(
            session_id="test_session",
            started_at=datetime.utcnow(),
            spec_file=Path("test_spec.yaml"),
            spec_hash="abc123",
            components=[
                ComponentProgress(name="Component1", status=ComponentStatus.PENDING),
                ComponentProgress(name="Component2", status=ComponentStatus.RED),
                ComponentProgress(name="Component3", status=ComponentStatus.VERIFIED),
            ],
        )

    def test_get_component_found(self, session: TDFlowSession):
        """Get component returns component when found."""
        comp = session.get_component("Component2")
        assert comp is not None, "Expected comp is not None"
        assert comp.name == "Component2", "Expected comp.name to equal 'Component2'"
        assert comp.status == ComponentStatus.RED, "Expected comp.status to equal ComponentStatus.RED"

    def test_get_component_not_found(self, session: TDFlowSession):
        """Get component returns None when not found."""
        comp = session.get_component("NonExistent")
        assert comp is None, "Expected comp is None"

    def test_get_next_pending(self, session: TDFlowSession):
        """Get next pending returns first pending component."""
        comp = session.get_next_pending()
        assert comp is not None, "Expected comp is not None"
        assert comp.name == "Component1", "Expected comp.name to equal 'Component1'"
        assert comp.status == ComponentStatus.PENDING, "Expected comp.status to equal ComponentStatus.PENDING"

    def test_all_verified_false(self, session: TDFlowSession):
        """All verified returns false when not all verified."""
        assert session.all_verified() is False, "Expected session.all_verified() is False"

    def test_all_verified_true(self):
        """All verified returns true when all verified."""
        session = TDFlowSession(
            session_id="test",
            started_at=datetime.utcnow(),
            spec_file=Path("test.yaml"),
            spec_hash="abc",
            components=[
                ComponentProgress(name="C1", status=ComponentStatus.VERIFIED),
                ComponentProgress(name="C2", status=ComponentStatus.VERIFIED),
            ],
        )
        assert session.all_verified() is True, "Expected session.all_verified() is True"

    def test_add_history(self, session: TDFlowSession):
        """Add history appends entry."""
        initial_count = len(session.history)

        session.add_history(
            action="test_action",
            phase=TDFlowPhase.RED,
            component="Component1",
            details="test details",
        )

        assert len(session.history) == initial_count + 1, "Expected len(session.history) to equal initial_count + 1"
        assert session.history[-1].action == "test_action", "Expected session.history[-1].action to equal 'test_action'"
        assert session.history[-1].phase == TDFlowPhase.RED, "Expected session.history[-1].phase to equal TDFlowPhase.RED"

    def test_get_progress_summary(self, session: TDFlowSession):
        """Get progress summary returns status counts."""
        summary = session.get_progress_summary()

        assert summary["pending"] == 1, "Expected summary['pending'] to equal 1"
        assert summary["red"] == 1, "Expected summary['red'] to equal 1"
        assert summary["verified"] == 1, "Expected summary['verified'] to equal 1"
