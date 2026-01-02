# @spec_file: .agentforge/specs/core-conformance-v1.yaml
# @spec_id: core-conformance-v1
# @component_id: tools-conformance-manager
# @impl_path: tools/conformance/manager.py

"""Tests for ConformanceManager."""

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from agentforge.core.conformance.domain import (
    Exemption,
    ExemptionScope,
    ExemptionScopeType,
    ExemptionStatus,
    Severity,
    Violation,
    ViolationStatus,
)
from agentforge.core.conformance.manager import ConformanceManager


def _make_violation(vid: str, message: str, detected: datetime, status: ViolationStatus) -> Violation:
    """Helper to create test violations."""
    return Violation(
        violation_id=vid, contract_id="c", check_id="k", severity=Severity.MAJOR,
        file_path=f"{vid}.py", message=message, detected_at=detected, last_seen_at=detected, status=status)


class TestConformanceManagerInit:
    """Tests for ConformanceManager initialization."""

    def test_init_paths(self, tmp_path: Path):
        """Test path initialization."""
        manager = ConformanceManager(tmp_path)

        assert manager.repo_root == tmp_path
        assert manager.agentforge_path == tmp_path / ".agentforge"

    def test_is_initialized_false(self, tmp_path: Path):
        """Test is_initialized returns false when not initialized."""
        manager = ConformanceManager(tmp_path)
        assert not manager.is_initialized()

    def test_is_initialized_true(self, tmp_path: Path):
        """Test is_initialized returns true after init."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()
        assert manager.is_initialized()


class TestConformanceManagerInitialize:
    """Tests for ConformanceManager.initialize()."""

    def test_initialize_creates_directories(self, tmp_path: Path):
        """Test initialize creates required directories."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()

        assert (tmp_path / ".agentforge").is_dir()
        assert (tmp_path / ".agentforge" / "violations").is_dir()
        assert (tmp_path / ".agentforge" / "exemptions").is_dir()
        assert (tmp_path / ".agentforge" / "history").is_dir()

    def test_initialize_creates_report(self, tmp_path: Path):
        """Test initialize creates initial report."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()

        report_path = tmp_path / ".agentforge" / "conformance_report.yaml"
        assert report_path.exists()

    def test_initialize_updates_gitignore_new(self, tmp_path: Path):
        """Test gitignore is created if missing."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".agentforge/local.yaml" in gitignore.read_text()

    def test_initialize_updates_gitignore_existing(self, tmp_path: Path):
        """Test gitignore is updated if exists."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# Existing content\n*.pyc\n")

        manager = ConformanceManager(tmp_path)
        manager.initialize()

        content = gitignore.read_text()
        assert "*.pyc" in content
        assert ".agentforge/local.yaml" in content

    def test_initialize_fails_if_exists(self, tmp_path: Path):
        """Test initialize fails if already initialized."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()

        with pytest.raises(FileExistsError):
            manager.initialize()

    def test_initialize_force(self, tmp_path: Path):
        """Test initialize with force reinitializes."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()
        manager.initialize(force=True)  # Should not raise

        assert manager.is_initialized()


class TestConformanceCheck:
    """Tests for run_conformance_check."""

    @pytest.fixture
    def manager(self, tmp_path: Path):
        """Create and initialize a manager."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()
        return manager

    def test_creates_violations(self, manager):
        """Test violations are created from results."""
        results = [
            {
                "contract_id": "test-contract",
                "check_id": "no-print",
                "file": "src/main.py",
                "line": 10,
                "message": "Found print statement",
                "severity": "error",
            }
        ]

        report = manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["test-contract"],
            files_checked=10,
            is_full_run=True,
        )

        assert report.summary.failed == 1
        violations = manager.list_violations()
        assert len(violations) == 1
        assert violations[0].message == "Found print statement"

    def test_deterministic_violation_ids(self, manager):
        """Test same result produces same violation ID."""
        results = [
            {
                "contract_id": "test-contract",
                "check_id": "check1",
                "file": "src/file.py",
                "line": 5,
                "message": "Issue found",
            }
        ]

        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["test-contract"],
            files_checked=1,
        )

        v1_id = manager.list_violations()[0].violation_id

        # Run again - should produce same ID
        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["test-contract"],
            files_checked=1,
        )

        v2_id = manager.list_violations()[0].violation_id
        assert v1_id == v2_id

    def test_updates_last_seen(self, manager):
        """Test last_seen_at is updated on re-detection."""
        results = [
            {
                "contract_id": "c",
                "check_id": "k",
                "file": "f.py",
                "line": 1,
                "message": "msg",
            }
        ]

        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
        )
        first_seen = manager.list_violations()[0].last_seen_at

        # Run again - timestamp should be updated
        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
        )
        second_seen = manager.list_violations()[0].last_seen_at

        assert second_seen >= first_seen

    def test_full_run_marks_resolved(self, manager):
        """Test full run marks missing violations as resolved."""
        # First run with violation
        results = [
            {
                "contract_id": "c",
                "check_id": "k",
                "file": "f.py",
                "line": 1,
                "message": "msg",
            }
        ]
        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
            is_full_run=True,
        )

        # Second run without violation
        manager.run_conformance_check(
            verification_results=[],
            contracts_checked=["c"],
            files_checked=1,
            is_full_run=True,
        )

        violations = manager.list_violations(status=ViolationStatus.RESOLVED)
        assert len(violations) == 1

    def test_incremental_run_marks_stale(self, manager):
        """Test incremental run marks missing violations as stale."""
        results = [
            {
                "contract_id": "c",
                "check_id": "k",
                "file": "f.py",
                "line": 1,
                "message": "msg",
            }
        ]
        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
            is_full_run=False,
        )

        manager.run_conformance_check(
            verification_results=[],
            contracts_checked=["c"],
            files_checked=1,
            is_full_run=False,
        )

        violations = manager.list_violations(status=ViolationStatus.STALE)
        assert len(violations) == 1

    def test_reopens_resolved_violation(self, manager):
        """Test resolved violation is reopened if seen again."""
        results = [
            {
                "contract_id": "c",
                "check_id": "k",
                "file": "f.py",
                "line": 1,
                "message": "msg",
            }
        ]

        # First run
        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
            is_full_run=True,
        )

        # Resolve it
        v = manager.list_violations()[0]
        manager.resolve_violation(v.violation_id, "Fixed")

        # Third run - same violation appears
        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
            is_full_run=True,
        )

        violations = manager.list_violations(status=ViolationStatus.OPEN)
        assert len(violations) == 1

    def test_report_trend_calculation(self, manager):
        """Test trend is calculated from previous report."""
        # First run
        results1 = [
            {"contract_id": "c", "check_id": "k", "file": "a.py", "line": 1, "message": "m"},
            {"contract_id": "c", "check_id": "k", "file": "b.py", "line": 1, "message": "m"},
        ]
        manager.run_conformance_check(
            verification_results=results1,
            contracts_checked=["c"],
            files_checked=2,
        )

        # Second run with one fewer violation
        results2 = [
            {"contract_id": "c", "check_id": "k", "file": "a.py", "line": 1, "message": "m"},
        ]
        report = manager.run_conformance_check(
            verification_results=results2,
            contracts_checked=["c"],
            files_checked=1,
            is_full_run=True,
        )

        assert report.trend is not None
        assert report.trend["failed_delta"] == -1


class TestExemptionHandling:
    """Tests for exemption handling in conformance checks."""

    @pytest.fixture
    def manager(self, tmp_path: Path):
        """Create and initialize a manager."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()
        return manager

    def test_exemption_applied_to_violation(self, manager):
        """Test exemption is applied to matching violation."""
        # Create exemption first
        exemption = Exemption(
            id="test-exemption",
            contract_id="c",
            check_ids=["k"],
            reason="Test exemption",
            approved_by="user",
            approved_date=date.today(),
            status=ExemptionStatus.ACTIVE,
            scope=ExemptionScope(type=ExemptionScopeType.GLOBAL),
        )
        manager.exemption_registry.ensure_directory()
        manager.exemption_registry.save(exemption)

        # Run check
        results = [
            {"contract_id": "c", "check_id": "k", "file": "f.py", "line": 1, "message": "m"},
        ]
        report = manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
        )

        assert report.summary.exempted == 1
        assert report.summary.failed == 0

        violations = manager.list_violations()
        assert violations[0].exemption_id == "test-exemption"

    def test_expired_exemption_handled(self, manager):
        """Test expired exemption marks violation as exemption_expired."""
        # Create expired exemption
        exemption = Exemption(
            id="expired-exemption",
            contract_id="c",
            check_ids=["k"],
            reason="Expired",
            approved_by="user",
            approved_date=date.today() - timedelta(days=30),
            expires=date.today() - timedelta(days=1),
            status=ExemptionStatus.ACTIVE,
            scope=ExemptionScope(type=ExemptionScopeType.GLOBAL),
        )
        manager.exemption_registry.ensure_directory()
        manager.exemption_registry.save(exemption)

        # Create a violation with this exemption
        violation = Violation(
            violation_id="V-123",
            contract_id="c",
            check_id="k",
            severity=Severity.MAJOR,
            file_path="f.py",
            message="m",
            detected_at=datetime.utcnow() - timedelta(days=30),
            last_seen_at=datetime.utcnow() - timedelta(days=30),
            status=ViolationStatus.OPEN,
            exemption_id="expired-exemption",
        )
        manager.violation_store.ensure_directory()
        manager.violation_store.save(violation)

        # Run check - should process expired exemption
        manager.run_conformance_check(
            verification_results=[],
            contracts_checked=["c"],
            files_checked=1,
        )

        manager.exemption_registry.load_all()
        updated_exemption = manager.exemption_registry.get("expired-exemption")
        assert updated_exemption is not None
        assert updated_exemption.status == ExemptionStatus.EXPIRED


class TestListViolations:
    """Tests for list_violations filtering."""

    @pytest.fixture
    def manager_with_violations(self, tmp_path: Path):
        """Create manager with multiple violations."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()

        violations = [
            Violation(
                violation_id="V-001",
                contract_id="contract-a",
                check_id="check1",
                severity=Severity.BLOCKER,
                file_path="src/main.py",
                message="Blocker issue",
                detected_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                status=ViolationStatus.OPEN,
            ),
            Violation(
                violation_id="V-002",
                contract_id="contract-a",
                check_id="check2",
                severity=Severity.MAJOR,
                file_path="src/utils.py",
                message="Major issue",
                detected_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                status=ViolationStatus.OPEN,
            ),
            Violation(
                violation_id="V-003",
                contract_id="contract-b",
                check_id="check1",
                severity=Severity.MINOR,
                file_path="tests/test_main.py",
                message="Minor issue",
                detected_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                status=ViolationStatus.RESOLVED,
            ),
        ]

        for v in violations:
            manager.violation_store.save(v)

        return manager

    def test_filter_by_status(self, manager_with_violations):
        """Test filtering by status."""
        open_violations = manager_with_violations.list_violations(status=ViolationStatus.OPEN)
        assert len(open_violations) == 2

        resolved = manager_with_violations.list_violations(status=ViolationStatus.RESOLVED)
        assert len(resolved) == 1

    def test_filter_by_severity(self, manager_with_violations):
        """Test filtering by severity."""
        blockers = manager_with_violations.list_violations(severity=Severity.BLOCKER)
        assert len(blockers) == 1
        assert blockers[0].violation_id == "V-001"

    def test_filter_by_contract(self, manager_with_violations):
        """Test filtering by contract."""
        contract_a = manager_with_violations.list_violations(contract_id="contract-a")
        assert len(contract_a) == 2

    def test_filter_by_file_pattern(self, manager_with_violations):
        """Test filtering by file pattern."""
        tests = manager_with_violations.list_violations(file_pattern="tests/*.py")
        assert len(tests) == 1
        assert tests[0].violation_id == "V-003"

    def test_filter_limit(self, manager_with_violations):
        """Test result limit."""
        limited = manager_with_violations.list_violations(limit=1)
        assert len(limited) == 1

    def test_sorted_by_severity(self, manager_with_violations):
        """Test results are sorted by severity."""
        all_violations = manager_with_violations.list_violations()
        # Should be sorted: blocker, major, minor
        assert all_violations[0].severity == Severity.BLOCKER
        assert all_violations[-1].severity == Severity.MINOR


class TestPruneViolations:
    """Tests for prune_violations."""

    @pytest.fixture
    def manager(self, tmp_path: Path):
        """Create manager with old violations."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()

        old = datetime.utcnow() - timedelta(days=60)
        recent = datetime.utcnow() - timedelta(days=5)
        violations = [
            _make_violation("V-old-resolved", "old resolved", old, ViolationStatus.RESOLVED),
            _make_violation("V-old-stale", "old stale", old, ViolationStatus.STALE),
            _make_violation("V-recent-resolved", "recent resolved", recent, ViolationStatus.RESOLVED),
            _make_violation("V-open", "open", old, ViolationStatus.OPEN),
        ]
        for v in violations:
            manager.violation_store.save(v)
        return manager

    def test_prune_dry_run(self, manager):
        """Test dry run doesn't delete."""
        count = manager.prune_violations(older_than_days=30, dry_run=True)
        assert count == 2  # old-resolved and old-stale

        # Verify nothing deleted
        all_violations = manager.list_violations()
        assert len(all_violations) == 4

    def test_prune_actual(self, manager):
        """Test actual prune deletes old violations."""
        count = manager.prune_violations(older_than_days=30, dry_run=False)
        assert count == 2

        all_violations = manager.list_violations()
        assert len(all_violations) == 2

        # Open violations preserved
        assert any(v.violation_id == "V-open" for v in all_violations)
        # Recent resolved preserved
        assert any(v.violation_id == "V-recent-resolved" for v in all_violations)


class TestGetSummaryStats:
    """Tests for get_summary_stats."""

    def test_not_initialized(self, tmp_path: Path):
        """Test stats when not initialized."""
        manager = ConformanceManager(tmp_path)
        stats = manager.get_summary_stats()

        assert stats["initialized"] is False

    def test_initialized_with_data(self, tmp_path: Path):
        """Test stats with initialized data."""
        manager = ConformanceManager(tmp_path)
        manager.initialize()

        results = [
            {"contract_id": "c", "check_id": "k", "file": "f.py", "line": 1, "message": "m"},
        ]
        manager.run_conformance_check(
            verification_results=results,
            contracts_checked=["c"],
            files_checked=1,
        )

        stats = manager.get_summary_stats()

        assert stats["initialized"] is True
        assert "last_run" in stats
        assert stats["violations"]["open"] == 1
        assert "c" in stats["contracts_checked"]
