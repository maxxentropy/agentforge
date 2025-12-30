"""Tests for conformance domain entities."""

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
import sys

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'tools'))

from conformance.domain import (
    Severity,
    ViolationStatus,
    ExemptionStatus,
    ExemptionScopeType,
    ExemptionScope,
    Violation,
    Exemption,
    ConformanceSummary,
    ConformanceReport,
    HistorySnapshot,
)


class TestSeverity:
    """Tests for Severity enum."""

    def test_from_contract_severity_error(self):
        """Test mapping error -> blocker."""
        assert Severity.from_contract_severity("error") == Severity.BLOCKER

    def test_from_contract_severity_warning(self):
        """Test mapping warning -> major."""
        assert Severity.from_contract_severity("warning") == Severity.MAJOR

    def test_from_contract_severity_info(self):
        """Test mapping info -> minor."""
        assert Severity.from_contract_severity("info") == Severity.MINOR

    def test_from_contract_severity_unknown(self):
        """Test unknown severity defaults to major."""
        assert Severity.from_contract_severity("unknown") == Severity.MAJOR

    def test_from_contract_severity_case_insensitive(self):
        """Test case insensitivity."""
        assert Severity.from_contract_severity("ERROR") == Severity.BLOCKER
        assert Severity.from_contract_severity("Warning") == Severity.MAJOR

    def test_weight_ordering(self):
        """Test severity weights are ordered correctly."""
        assert Severity.BLOCKER.weight > Severity.CRITICAL.weight
        assert Severity.CRITICAL.weight > Severity.MAJOR.weight
        assert Severity.MAJOR.weight > Severity.MINOR.weight
        assert Severity.MINOR.weight > Severity.INFO.weight


class TestViolationId:
    """Tests for Violation.generate_id()."""

    def test_deterministic_id_generation(self):
        """Test same inputs produce same ID."""
        id1 = Violation.generate_id("contract1", "check1", "src/file.py", 10)
        id2 = Violation.generate_id("contract1", "check1", "src/file.py", 10)
        assert id1 == id2

    def test_different_inputs_different_ids(self):
        """Test different inputs produce different IDs."""
        id1 = Violation.generate_id("contract1", "check1", "src/file.py", 10)
        id2 = Violation.generate_id("contract1", "check1", "src/file.py", 11)
        assert id1 != id2

    def test_id_format(self):
        """Test ID follows V-xxxx format."""
        violation_id = Violation.generate_id("contract1", "check1", "file.py", 1)
        assert violation_id.startswith("V-")
        assert len(violation_id) == 14  # V- + 12 hex chars

    def test_path_normalization(self):
        """Test Windows paths are normalized."""
        id1 = Violation.generate_id("c", "k", "src/file.py", 1)
        id2 = Violation.generate_id("c", "k", "src\\file.py", 1)
        assert id1 == id2

    def test_file_level_violation(self):
        """Test file-level violation (no line number)."""
        violation_id = Violation.generate_id("c", "k", "file.py", None)
        assert violation_id.startswith("V-")

    def test_rule_id_affects_hash(self):
        """Test rule_id is included in hash."""
        id1 = Violation.generate_id("c", "k", "f.py", 1, rule_id="R1")
        id2 = Violation.generate_id("c", "k", "f.py", 1, rule_id="R2")
        assert id1 != id2


class TestViolation:
    """Tests for Violation entity."""

    @pytest.fixture
    def violation(self):
        """Create a test violation."""
        return Violation(
            violation_id="V-123456789abc",
            contract_id="test-contract",
            check_id="no-print",
            severity=Severity.MAJOR,
            file_path="src/module.py",
            message="Found print statement",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
            line_number=42,
        )

    def test_mark_resolved(self, violation):
        """Test marking violation as resolved."""
        violation.mark_resolved("Fixed the issue", resolved_by="user")

        assert violation.status == ViolationStatus.RESOLVED
        assert violation.resolution is not None
        assert violation.resolution["reason"] == "Fixed the issue"
        assert violation.resolution["resolved_by"] == "user"

    def test_mark_stale(self, violation):
        """Test marking violation as stale."""
        violation.mark_stale()
        assert violation.status == ViolationStatus.STALE

    def test_mark_exemption_expired(self, violation):
        """Test marking exemption as expired."""
        violation.exemption_id = "EX-001"
        violation.mark_exemption_expired()

        assert violation.status == ViolationStatus.EXEMPTION_EXPIRED
        assert violation.exemption_expired_at is not None

    def test_reopen_resolved(self, violation):
        """Test reopening a resolved violation."""
        violation.mark_resolved("Fixed")
        violation.reopen()

        assert violation.status == ViolationStatus.OPEN
        assert violation.resolution is None

    def test_reopen_stale(self, violation):
        """Test reopening a stale violation."""
        violation.mark_stale()
        violation.reopen()

        assert violation.status == ViolationStatus.OPEN


class TestExemptionScope:
    """Tests for ExemptionScope."""

    def test_global_scope_matches_any_file(self):
        """Test global scope matches any file."""
        scope = ExemptionScope(type=ExemptionScopeType.GLOBAL)
        assert scope.matches_file("any/file/path.py")
        assert scope.matches_file("another.ts")

    def test_file_pattern_scope(self):
        """Test file pattern matching."""
        scope = ExemptionScope(
            type=ExemptionScopeType.FILE_PATTERN,
            patterns=["tests/*.py", "scripts/*.py"]
        )
        assert scope.matches_file("tests/test_foo.py")
        assert scope.matches_file("scripts/run.py")
        assert not scope.matches_file("src/main.py")

    def test_violation_id_scope(self):
        """Test violation ID matching."""
        scope = ExemptionScope(
            type=ExemptionScopeType.VIOLATION_ID,
            violation_ids=["V-abc123", "V-def456"]
        )
        assert scope.matches_violation_id("V-abc123")
        assert scope.matches_violation_id("V-def456")
        assert not scope.matches_violation_id("V-other")

    def test_line_range_matching(self):
        """Test line range matching."""
        scope = ExemptionScope(
            type=ExemptionScopeType.FILE_PATTERN,
            patterns=["*"],
            lines=(10, 20)
        )
        assert scope.matches_line(10)
        assert scope.matches_line(15)
        assert scope.matches_line(20)
        assert not scope.matches_line(9)
        assert not scope.matches_line(21)

    def test_no_lines_matches_any(self):
        """Test no line restriction matches any line."""
        scope = ExemptionScope(type=ExemptionScopeType.GLOBAL)
        assert scope.matches_line(1)
        assert scope.matches_line(1000)
        assert scope.matches_line(None)


class TestExemption:
    """Tests for Exemption entity."""

    @pytest.fixture
    def exemption(self):
        """Create a test exemption."""
        return Exemption(
            id="legacy-logging",
            contract_id="python-patterns",
            check_ids=["no-print-statements"],
            reason="Legacy module uses print for CLI output",
            approved_by="tech-lead@example.com",
            approved_date=date.today(),
            status=ExemptionStatus.ACTIVE,
            scope=ExemptionScope(
                type=ExemptionScopeType.FILE_PATTERN,
                patterns=["cli/*.py"]
            ),
        )

    def test_is_expired_without_expiry(self, exemption):
        """Test exemption without expiry is not expired."""
        assert not exemption.is_expired()

    def test_is_expired_future_expiry(self, exemption):
        """Test exemption with future expiry is not expired."""
        exemption.expires = date.today() + timedelta(days=30)
        assert not exemption.is_expired()

    def test_is_expired_past_expiry(self, exemption):
        """Test exemption with past expiry is expired."""
        exemption.expires = date.today() - timedelta(days=1)
        assert exemption.is_expired()

    def test_is_active_when_active(self, exemption):
        """Test exemption is active when status is active and not expired."""
        assert exemption.is_active()

    def test_is_active_when_expired(self, exemption):
        """Test exemption is not active when expired."""
        exemption.expires = date.today() - timedelta(days=1)
        assert not exemption.is_active()

    def test_is_active_when_status_not_active(self, exemption):
        """Test exemption is not active when status is not active."""
        exemption.status = ExemptionStatus.EXPIRED
        assert not exemption.is_active()

    def test_needs_review_without_date(self, exemption):
        """Test no review needed without review date."""
        assert not exemption.needs_review()

    def test_needs_review_future_date(self, exemption):
        """Test no review needed with future date."""
        exemption.review_date = date.today() + timedelta(days=7)
        assert not exemption.needs_review()

    def test_needs_review_past_date(self, exemption):
        """Test review needed with past date."""
        exemption.review_date = date.today() - timedelta(days=1)
        assert exemption.needs_review()

    def test_needs_review_today(self, exemption):
        """Test review needed on review date."""
        exemption.review_date = date.today()
        assert exemption.needs_review()

    def test_covers_check_explicit(self, exemption):
        """Test explicit check coverage."""
        assert exemption.covers_check("no-print-statements")
        assert not exemption.covers_check("other-check")

    def test_covers_check_wildcard(self, exemption):
        """Test wildcard check coverage."""
        exemption.check_ids = ["*"]
        assert exemption.covers_check("any-check")
        assert exemption.covers_check("another-check")

    def test_covers_violation_matching(self, exemption):
        """Test violation coverage."""
        violation = Violation(
            violation_id="V-123",
            contract_id="python-patterns",
            check_id="no-print-statements",
            severity=Severity.MAJOR,
            file_path="cli/main.py",
            message="Found print",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
        )
        assert exemption.covers_violation(violation)

    def test_covers_violation_wrong_contract(self, exemption):
        """Test violation not covered with wrong contract."""
        violation = Violation(
            violation_id="V-123",
            contract_id="other-contract",
            check_id="no-print-statements",
            severity=Severity.MAJOR,
            file_path="cli/main.py",
            message="Found print",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
        )
        assert not exemption.covers_violation(violation)

    def test_covers_violation_wrong_file(self, exemption):
        """Test violation not covered with wrong file."""
        violation = Violation(
            violation_id="V-123",
            contract_id="python-patterns",
            check_id="no-print-statements",
            severity=Severity.MAJOR,
            file_path="src/main.py",  # Not in cli/*.py
            message="Found print",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
        )
        assert not exemption.covers_violation(violation)


class TestConformanceSummary:
    """Tests for ConformanceSummary."""

    def test_default_values(self):
        """Test default summary values."""
        summary = ConformanceSummary()
        assert summary.total == 0
        assert summary.passed == 0
        assert summary.failed == 0
        assert summary.exempted == 0
        assert summary.stale == 0

    def test_total_adjusted_if_needed(self):
        """Test total is adjusted if too small."""
        summary = ConformanceSummary(total=5, passed=10, failed=5, exempted=2)
        assert summary.total >= summary.passed + summary.failed + summary.exempted

    def test_compliance_rate_empty(self):
        """Test compliance rate with no checks."""
        summary = ConformanceSummary()
        assert summary.compliance_rate == 1.0

    def test_compliance_rate_calculation(self):
        """Test compliance rate calculation."""
        summary = ConformanceSummary(total=100, passed=80, failed=15, exempted=5)
        assert summary.compliance_rate == 0.8

    def test_open_issues(self):
        """Test open issues count."""
        summary = ConformanceSummary(failed=10, stale=5)
        assert summary.open_issues == 15


class TestConformanceReport:
    """Tests for ConformanceReport."""

    @pytest.fixture
    def report(self):
        """Create a test report."""
        return ConformanceReport(
            schema_version="1.0",
            generated_at=datetime.utcnow(),
            run_id="run-123",
            run_type="full",
            summary=ConformanceSummary(total=50, passed=40, failed=8, exempted=2),
            by_severity={"blocker": 2, "major": 4, "minor": 2},
            by_contract={"contract-a": 5, "contract-b": 3},
            contracts_checked=["contract-a", "contract-b"],
            files_checked=100,
        )

    def test_has_blockers_true(self, report):
        """Test has_blockers with blockers."""
        assert report.has_blockers()

    def test_has_blockers_false(self, report):
        """Test has_blockers without blockers."""
        report.by_severity = {"major": 5}
        assert not report.has_blockers()

    def test_has_critical_true(self, report):
        """Test has_critical with critical."""
        report.by_severity["critical"] = 1
        assert report.has_critical()

    def test_has_critical_false(self, report):
        """Test has_critical without critical."""
        assert not report.has_critical()

    def test_is_passing_with_blockers(self, report):
        """Test is_passing fails with blockers at blocker threshold."""
        assert not report.is_passing(threshold=Severity.BLOCKER)

    def test_is_passing_without_blockers(self, report):
        """Test is_passing succeeds without blockers at blocker threshold."""
        report.by_severity = {"major": 5}
        assert report.is_passing(threshold=Severity.BLOCKER)

    def test_is_passing_at_major_threshold(self, report):
        """Test is_passing at major threshold."""
        report.by_severity = {"major": 5}
        assert not report.is_passing(threshold=Severity.MAJOR)


class TestHistorySnapshot:
    """Tests for HistorySnapshot."""

    @pytest.fixture
    def snapshots(self):
        """Create two test snapshots."""
        old = HistorySnapshot(
            schema_version="1.0",
            date=date.today() - timedelta(days=7),
            generated_at=datetime.utcnow() - timedelta(days=7),
            summary=ConformanceSummary(total=100, passed=80, failed=15, exempted=5),
            by_severity={"blocker": 5, "major": 10},
            by_contract={"a": 10, "b": 5},
            files_analyzed=200,
            contracts_checked=["a", "b"],
        )
        new = HistorySnapshot(
            schema_version="1.0",
            date=date.today(),
            generated_at=datetime.utcnow(),
            summary=ConformanceSummary(total=100, passed=90, failed=8, exempted=2),
            by_severity={"blocker": 2, "major": 6},
            by_contract={"a": 5, "b": 3},
            files_analyzed=200,
            contracts_checked=["a", "b"],
        )
        return old, new

    def test_delta_calculation(self, snapshots):
        """Test delta calculation between snapshots."""
        old, new = snapshots
        delta = new.delta_from(old)

        assert delta["passed_delta"] == 10  # 90 - 80
        assert delta["failed_delta"] == -7  # 8 - 15
        assert delta["exempted_delta"] == -3  # 2 - 5
