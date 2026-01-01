# @spec_file: .agentforge/specs/conformance-v1.yaml
# @spec_id: conformance-v1
# @component_id: tools-conformance-stores
# @impl_path: tools/conformance/stores.py

"""Tests for conformance storage layer."""

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
import sys
import yaml

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
    HistorySnapshot,
)
from conformance.stores import (
    AtomicFileWriter,
    ViolationStore,
    ExemptionRegistry,
    HistoryStore,
)


class TestAtomicFileWriter:
    """Tests for AtomicFileWriter."""

    def test_successful_write(self, tmp_path: Path):
        """Test successful atomic write."""
        target = tmp_path / "test.txt"

        with AtomicFileWriter(target) as f:
            f.write("Hello, World!")

        assert target.exists()
        assert target.read_text() == "Hello, World!"

    def test_failed_write_no_partial(self, tmp_path: Path):
        """Test failed write doesn't leave partial file."""
        target = tmp_path / "test.txt"

        with pytest.raises(ValueError):
            with AtomicFileWriter(target) as f:
                f.write("Partial content")
                raise ValueError("Simulated failure")

        assert not target.exists()

    def test_creates_parent_directories(self, tmp_path: Path):
        """Test parent directories are created."""
        target = tmp_path / "nested" / "dir" / "test.txt"

        with AtomicFileWriter(target) as f:
            f.write("content")

        assert target.exists()
        assert target.read_text() == "content"

    def test_overwrites_existing(self, tmp_path: Path):
        """Test atomic write overwrites existing file."""
        target = tmp_path / "test.txt"
        target.write_text("old content")

        with AtomicFileWriter(target) as f:
            f.write("new content")

        assert target.read_text() == "new content"


class TestViolationStore:
    """Tests for ViolationStore."""

    @pytest.fixture
    def store(self, tmp_path: Path):
        """Create a violation store."""
        return ViolationStore(tmp_path)

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

    def test_ensure_directory(self, store, tmp_path: Path):
        """Test directory creation."""
        store.ensure_directory()
        assert (tmp_path / "violations").is_dir()

    def test_save_and_load(self, store, violation):
        """Test saving and loading a violation."""
        store.ensure_directory()
        store.save(violation)

        loaded = store.load_all()
        assert len(loaded) == 1
        assert loaded[0].violation_id == violation.violation_id
        assert loaded[0].contract_id == violation.contract_id
        assert loaded[0].severity == violation.severity

    def test_get_by_id(self, store, violation):
        """Test getting violation by ID."""
        store.ensure_directory()
        store.save(violation)
        store.load_all()  # Populate cache

        found = store.get(violation.violation_id)
        assert found is not None
        assert found.violation_id == violation.violation_id

    def test_get_nonexistent(self, store, violation):
        """Test getting nonexistent violation."""
        store.ensure_directory()
        store.save(violation)
        store.load_all()

        assert store.get("V-nonexistent") is None

    def test_delete(self, store, violation):
        """Test deleting a violation."""
        store.ensure_directory()
        store.save(violation)

        store.delete(violation.violation_id)

        violations = store.load_all()
        assert len(violations) == 0

    def test_find_by_contract(self, store):
        """Test finding violations by contract."""
        store.ensure_directory()

        v1 = Violation(
            violation_id="V-111",
            contract_id="contract-a",
            check_id="check1",
            severity=Severity.MAJOR,
            file_path="a.py",
            message="msg",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
        )
        v2 = Violation(
            violation_id="V-222",
            contract_id="contract-b",
            check_id="check1",
            severity=Severity.MAJOR,
            file_path="b.py",
            message="msg",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
        )
        store.save(v1)
        store.save(v2)
        store.load_all()

        found = list(store.find_by_contract("contract-a"))
        assert len(found) == 1
        assert found[0].violation_id == "V-111"

    def test_find_by_status(self, store):
        """Test finding violations by status."""
        store.ensure_directory()

        v1 = Violation(
            violation_id="V-111",
            contract_id="c",
            check_id="k",
            severity=Severity.MAJOR,
            file_path="a.py",
            message="msg",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
        )
        v2 = Violation(
            violation_id="V-222",
            contract_id="c",
            check_id="k",
            severity=Severity.MAJOR,
            file_path="b.py",
            message="msg",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.RESOLVED,
        )
        store.save(v1)
        store.save(v2)
        store.load_all()

        open_violations = list(store.find_by_status(ViolationStatus.OPEN))
        assert len(open_violations) == 1
        assert open_violations[0].violation_id == "V-111"

    def test_violation_yaml_format(self, store, violation, tmp_path: Path):
        """Test violation file is valid YAML."""
        store.ensure_directory()
        store.save(violation)

        file_path = tmp_path / "violations" / f"{violation.violation_id}.yaml"
        assert file_path.exists()

        with open(file_path) as f:
            data = yaml.safe_load(f)

        assert data["violation_id"] == violation.violation_id
        assert data["contract_id"] == violation.contract_id
        assert data["severity"] == "major"
        assert data["status"] == "open"


class TestExemptionRegistry:
    """Tests for ExemptionRegistry."""

    @pytest.fixture
    def registry(self, tmp_path: Path):
        """Create an exemption registry."""
        return ExemptionRegistry(tmp_path)

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

    def test_ensure_directory(self, registry, tmp_path: Path):
        """Test directory creation."""
        registry.ensure_directory()
        assert (tmp_path / "exemptions").is_dir()

    def test_save_and_load(self, registry, exemption):
        """Test saving and loading an exemption."""
        registry.ensure_directory()
        registry.save(exemption)

        loaded = registry.load_all()
        assert len(loaded) == 1
        assert loaded[0].id == exemption.id
        assert loaded[0].contract_id == exemption.contract_id
        assert loaded[0].scope.type == ExemptionScopeType.FILE_PATTERN

    def test_get_active(self, registry, exemption):
        """Test getting active exemptions."""
        registry.ensure_directory()
        registry.save(exemption)

        expired = Exemption(
            id="expired-one",
            contract_id="c",
            check_ids=["k"],
            reason="reason",
            approved_by="user",
            approved_date=date.today(),
            status=ExemptionStatus.EXPIRED,
            scope=ExemptionScope(type=ExemptionScopeType.GLOBAL),
        )
        registry.save(expired)
        registry.load_all()

        active = registry.get_active()
        assert len(active) == 1
        assert active[0].id == "legacy-logging"

    def test_get_expired(self, registry):
        """Test getting expired exemptions."""
        registry.ensure_directory()

        expired = Exemption(
            id="expired-one",
            contract_id="c",
            check_ids=["k"],
            reason="reason",
            approved_by="user",
            approved_date=date.today() - timedelta(days=30),
            expires=date.today() - timedelta(days=1),
            status=ExemptionStatus.ACTIVE,  # Status still active but expired
            scope=ExemptionScope(type=ExemptionScopeType.GLOBAL),
        )
        registry.save(expired)
        registry.load_all()

        found_expired = registry.get_expired()
        assert len(found_expired) == 1

    def test_get_needs_review(self, registry):
        """Test getting exemptions needing review."""
        registry.ensure_directory()

        needs_review = Exemption(
            id="review-me",
            contract_id="c",
            check_ids=["k"],
            reason="reason",
            approved_by="user",
            approved_date=date.today() - timedelta(days=30),
            review_date=date.today() - timedelta(days=1),
            status=ExemptionStatus.ACTIVE,
            scope=ExemptionScope(type=ExemptionScopeType.GLOBAL),
        )
        registry.save(needs_review)
        registry.load_all()

        found = registry.get_needs_review()
        assert len(found) == 1
        assert found[0].id == "review-me"

    def test_find_for_violation(self, registry, exemption):
        """Test finding exemption for a violation."""
        registry.ensure_directory()
        registry.save(exemption)
        registry.load_all()

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

        found = registry.find_for_violation(violation)
        assert found is not None
        assert found.id == "legacy-logging"

    def test_find_for_violation_no_match(self, registry, exemption):
        """Test no exemption found for non-matching violation."""
        registry.ensure_directory()
        registry.save(exemption)
        registry.load_all()

        violation = Violation(
            violation_id="V-456",
            contract_id="other-contract",
            check_id="other-check",
            severity=Severity.MAJOR,
            file_path="src/main.py",
            message="msg",
            detected_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=ViolationStatus.OPEN,
        )

        found = registry.find_for_violation(violation)
        assert found is None

    def test_update_status(self, registry, exemption):
        """Test updating exemption status."""
        registry.ensure_directory()
        registry.save(exemption)
        registry.load_all()

        registry.update_status("legacy-logging", ExemptionStatus.EXPIRED)

        # Reload to verify persistence
        registry.load_all()
        found = registry.get("legacy-logging")
        assert found is not None
        assert found.status == ExemptionStatus.EXPIRED


class TestHistoryStore:
    """Tests for HistoryStore."""

    @pytest.fixture
    def store(self, tmp_path: Path):
        """Create a history store."""
        return HistoryStore(tmp_path)

    @pytest.fixture
    def snapshot(self):
        """Create a test snapshot."""
        return HistorySnapshot(
            schema_version="1.0",
            date=date.today(),
            generated_at=datetime.utcnow(),
            summary=ConformanceSummary(total=100, passed=80, failed=15, exempted=5),
            by_severity={"blocker": 5, "major": 10},
            by_contract={"a": 10, "b": 5},
            files_analyzed=200,
            contracts_checked=["a", "b"],
        )

    def test_ensure_directory(self, store, tmp_path: Path):
        """Test directory creation."""
        store.ensure_directory()
        assert (tmp_path / "history").is_dir()

    def test_save_snapshot(self, store, snapshot):
        """Test saving a snapshot."""
        store.ensure_directory()
        store.save_snapshot(snapshot)

        # Check file exists with correct name
        expected_path = store.history_path / f"{snapshot.date.isoformat()}.yaml"
        assert expected_path.exists()

    def test_get_snapshot(self, store, snapshot):
        """Test getting a snapshot by date."""
        store.ensure_directory()
        store.save_snapshot(snapshot)

        loaded = store.get_snapshot(snapshot.date)
        assert loaded is not None
        assert loaded.date == snapshot.date
        assert loaded.summary.failed == snapshot.summary.failed

    def test_get_snapshot_nonexistent(self, store):
        """Test getting nonexistent snapshot."""
        store.ensure_directory()
        loaded = store.get_snapshot(date.today() - timedelta(days=100))
        assert loaded is None

    def test_get_range(self, store):
        """Test getting snapshots in date range."""
        store.ensure_directory()

        for i in range(5):
            snapshot = HistorySnapshot(
                schema_version="1.0",
                date=date.today() - timedelta(days=i),
                generated_at=datetime.utcnow(),
                summary=ConformanceSummary(total=100, failed=10 + i),
                by_severity={},
                by_contract={},
                files_analyzed=100,
                contracts_checked=[],
            )
            store.save_snapshot(snapshot)

        start = date.today() - timedelta(days=3)
        end = date.today()
        snapshots = store.get_range(start, end)

        assert len(snapshots) == 4  # days 0, 1, 2, 3
        # Should be sorted by date
        assert snapshots[0].date < snapshots[-1].date

    def test_prune_old_snapshots(self, tmp_path):
        """Test pruning old snapshots."""
        # Create store with short retention
        store = HistoryStore(tmp_path, retention_days=30)
        store.ensure_directory()

        # Create snapshots: some old, some recent
        for i in range(100):
            snapshot = HistorySnapshot(
                schema_version="1.0",
                date=date.today() - timedelta(days=i),
                generated_at=datetime.utcnow(),
                summary=ConformanceSummary(),
                by_severity={},
                by_contract={},
                files_analyzed=100,
                contracts_checked=[],
            )
            store.save_snapshot(snapshot)

        # Prune based on retention set in constructor
        store.prune_old_snapshots()

        remaining = list(store.history_path.glob("*.yaml"))
        assert len(remaining) <= 31  # 30 days + possible .gitkeep

    def test_snapshot_overwrites_same_day(self, store):
        """Test saving multiple snapshots on same day overwrites."""
        store.ensure_directory()

        snapshot1 = HistorySnapshot(
            schema_version="1.0",
            date=date.today(),
            generated_at=datetime.utcnow(),
            summary=ConformanceSummary(failed=10),
            by_severity={},
            by_contract={},
            files_analyzed=100,
            contracts_checked=[],
        )
        snapshot2 = HistorySnapshot(
            schema_version="1.0",
            date=date.today(),
            generated_at=datetime.utcnow(),
            summary=ConformanceSummary(failed=20),
            by_severity={},
            by_contract={},
            files_analyzed=100,
            contracts_checked=[],
        )

        store.save_snapshot(snapshot1)
        store.save_snapshot(snapshot2)

        loaded = store.get_snapshot(date.today())
        assert loaded.summary.failed == 20  # Second snapshot
