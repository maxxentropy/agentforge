"""
History Storage for Conformance Tracking
=========================================

Manages history/ directory for trend analysis.
One snapshot per day (YYYY-MM-DD.yaml).
"""

from pathlib import Path
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
import yaml

from .domain import HistorySnapshot, ConformanceSummary
from .stores import AtomicFileWriter


class HistoryStore:
    """
    Manages history/ directory for trend analysis.

    One snapshot per day (YYYY-MM-DD.yaml). Later runs on the same day
    overwrite the previous snapshot.
    """

    def __init__(self, agentforge_path: Path, retention_days: int = 90):
        self.history_path = agentforge_path / "history"
        self.retention_days = max(7, min(365, retention_days))

    def ensure_directory(self) -> None:
        """Create history directory if needed."""
        self.history_path.mkdir(parents=True, exist_ok=True)
        gitkeep = self.history_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def save_snapshot(self, snapshot: HistorySnapshot) -> None:
        """Save or overwrite daily snapshot."""
        self.ensure_directory()
        file_path = self.history_path / f"{snapshot.date.isoformat()}.yaml"

        data = {
            "schema_version": snapshot.schema_version,
            "date": snapshot.date.isoformat(),
            "generated_at": snapshot.generated_at.isoformat(),
            "summary": {
                "total": snapshot.summary.total,
                "passed": snapshot.summary.passed,
                "failed": snapshot.summary.failed,
                "exempted": snapshot.summary.exempted,
                "stale": snapshot.summary.stale,
            },
            "by_severity": snapshot.by_severity,
            "by_contract": snapshot.by_contract,
            "files_analyzed": snapshot.files_analyzed,
            "contracts_checked": snapshot.contracts_checked,
        }

        with AtomicFileWriter(file_path) as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_snapshot(self, snapshot_date: date) -> Optional[HistorySnapshot]:
        """Get snapshot for specific date."""
        file_path = self.history_path / f"{snapshot_date.isoformat()}.yaml"
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return self._dict_to_snapshot(data)
        except Exception:
            return None

    def _dict_to_snapshot(self, data: Dict) -> HistorySnapshot:
        """Convert dictionary to HistorySnapshot."""
        summary_data = data["summary"]
        return HistorySnapshot(
            schema_version=data["schema_version"],
            date=date.fromisoformat(data["date"]),
            generated_at=datetime.fromisoformat(data["generated_at"]),
            summary=ConformanceSummary(
                total=summary_data["total"],
                passed=summary_data["passed"],
                failed=summary_data["failed"],
                exempted=summary_data["exempted"],
                stale=summary_data.get("stale", 0),
            ),
            by_severity=data["by_severity"],
            by_contract=data["by_contract"],
            files_analyzed=data["files_analyzed"],
            contracts_checked=data["contracts_checked"],
        )

    def get_range(self, start_date: date, end_date: date) -> List[HistorySnapshot]:
        """Get snapshots for date range (inclusive)."""
        snapshots = []
        current = start_date

        while current <= end_date:
            snapshot = self.get_snapshot(current)
            if snapshot:
                snapshots.append(snapshot)
            current = current + timedelta(days=1)

        return snapshots

    def get_latest(self, n: int = 1) -> List[HistorySnapshot]:
        """Get the N most recent snapshots."""
        if not self.history_path.exists():
            return []

        files = sorted(
            self.history_path.glob("*.yaml"),
            key=lambda p: p.stem,
            reverse=True
        )

        snapshots = []
        for file_path in files[:n]:
            if file_path.name.startswith("."):
                continue
            try:
                snapshot_date = date.fromisoformat(file_path.stem)
                snapshot = self.get_snapshot(snapshot_date)
                if snapshot:
                    snapshots.append(snapshot)
            except ValueError:
                continue

        return snapshots

    def prune_old_snapshots(self) -> int:
        """Delete snapshots older than retention period."""
        if not self.history_path.exists():
            return 0

        cutoff = date.today() - timedelta(days=self.retention_days)
        count = 0

        for file_path in self.history_path.glob("*.yaml"):
            if file_path.name.startswith("."):
                continue
            try:
                file_date = date.fromisoformat(file_path.stem)
                if file_date < cutoff:
                    file_path.unlink()
                    count += 1
            except ValueError:
                continue

        return count

    def get_trend(self, days: int = 7) -> Dict[str, List]:
        """Get trend data for visualization."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        snapshots = self.get_range(start_date, end_date)

        return {
            "dates": [s.date.isoformat() for s in snapshots],
            "failed": [s.summary.failed for s in snapshots],
            "passed": [s.summary.passed for s in snapshots],
            "exempted": [s.summary.exempted for s in snapshots],
            "total": [s.summary.total for s in snapshots],
        }
