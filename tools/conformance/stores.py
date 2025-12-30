"""
Conformance Storage Infrastructure
==================================

File-based storage for violations, exemptions, and history.
All writes use atomic operations (write to temp, then rename).

Directory Structure:
    .agentforge/
    ├── violations/          # One YAML file per violation
    │   └── V-{hash}.yaml
    ├── exemptions/          # One YAML file per exemption
    │   └── {id}.yaml
    └── history/             # Daily snapshots
        └── YYYY-MM-DD.yaml
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Set
from datetime import date, datetime, timedelta
import yaml

from .domain import (
    Violation, ViolationStatus, Severity,
    Exemption, ExemptionStatus, ExemptionScope, ExemptionScopeType,
    HistorySnapshot, ConformanceSummary, ConformanceReport
)


class AtomicFileWriter:
    """
    Context manager for atomic file writes.

    Writes to a temporary file first, then atomically renames to target.
    This prevents file corruption if the process is interrupted.
    """

    def __init__(self, target_path: Path):
        self.target_path = target_path
        self.temp_path = None
        self.file = None

    def __enter__(self):
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        fd, self.temp_path = tempfile.mkstemp(
            dir=self.target_path.parent,
            suffix=".tmp"
        )
        self.file = os.fdopen(fd, 'w', encoding='utf-8')
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        if exc_type is None:
            # Success - atomically replace target
            shutil.move(self.temp_path, self.target_path)
        else:
            # Error - clean up temp file
            try:
                os.unlink(self.temp_path)
            except OSError:
                pass
        return False


class ViolationStore:
    """
    Manages violations/ directory.

    Each violation is stored as a separate YAML file: V-{hash}.yaml
    This makes Git merges cleaner and allows parallel updates.
    """

    def __init__(self, agentforge_path: Path):
        self.violations_path = agentforge_path / "violations"
        self._cache: Dict[str, Violation] = {}

    def ensure_directory(self) -> None:
        """Create violations directory if needed."""
        self.violations_path.mkdir(parents=True, exist_ok=True)
        gitkeep = self.violations_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def load_all(self) -> List[Violation]:
        """Load all violations from disk into cache."""
        self._cache.clear()
        violations = []

        if not self.violations_path.exists():
            return violations

        for file_path in self.violations_path.glob("V-*.yaml"):
            violation = self._load_violation(file_path)
            if violation:
                self._cache[violation.violation_id] = violation
                violations.append(violation)

        return violations

    def _load_violation(self, file_path: Path) -> Optional[Violation]:
        """Load a single violation from YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return self._dict_to_violation(data)
        except Exception:
            return None

    def _dict_to_violation(self, data: Dict) -> Violation:
        """Convert dictionary to Violation object."""
        return Violation(
            violation_id=data["violation_id"],
            contract_id=data["contract_id"],
            check_id=data["check_id"],
            severity=Severity(data["severity"]),
            file_path=data["file_path"],
            message=data["message"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
            last_seen_at=datetime.fromisoformat(data["last_seen_at"]),
            status=ViolationStatus(data["status"]),
            line_number=data.get("line_number"),
            column_number=data.get("column_number"),
            rule_id=data.get("rule_id"),
            fix_hint=data.get("fix_hint"),
            code_snippet=data.get("code_snippet"),
            resolution=data.get("resolution"),
            exemption_id=data.get("exemption_id"),
            exemption_expired_at=(
                datetime.fromisoformat(data["exemption_expired_at"])
                if data.get("exemption_expired_at") else None
            ),
        )

    def _violation_to_dict(self, violation: Violation) -> Dict:
        """Convert Violation object to dictionary for YAML."""
        data = {
            "schema_version": "1.0",
            "violation_id": violation.violation_id,
            "contract_id": violation.contract_id,
            "check_id": violation.check_id,
            "severity": violation.severity.value,
            "file_path": violation.file_path,
            "message": violation.message,
            "detected_at": violation.detected_at.isoformat(),
            "last_seen_at": violation.last_seen_at.isoformat(),
            "status": violation.status.value,
        }

        # Optional fields
        if violation.line_number is not None:
            data["line_number"] = violation.line_number
        if violation.column_number is not None:
            data["column_number"] = violation.column_number
        if violation.rule_id:
            data["rule_id"] = violation.rule_id
        if violation.fix_hint:
            data["fix_hint"] = violation.fix_hint
        if violation.code_snippet:
            data["code_snippet"] = violation.code_snippet
        if violation.resolution:
            data["resolution"] = violation.resolution
        if violation.exemption_id:
            data["exemption_id"] = violation.exemption_id
        if violation.exemption_expired_at:
            data["exemption_expired_at"] = violation.exemption_expired_at.isoformat()

        return data

    def get(self, violation_id: str) -> Optional[Violation]:
        """Get violation by ID (from cache or disk)."""
        if violation_id in self._cache:
            return self._cache[violation_id]

        file_path = self.violations_path / f"{violation_id}.yaml"
        if file_path.exists():
            violation = self._load_violation(file_path)
            if violation:
                self._cache[violation_id] = violation
            return violation
        return None

    def save(self, violation: Violation) -> None:
        """Save violation to disk atomically."""
        self.ensure_directory()
        file_path = self.violations_path / f"{violation.violation_id}.yaml"
        data = self._violation_to_dict(violation)

        with AtomicFileWriter(file_path) as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        self._cache[violation.violation_id] = violation

    def delete(self, violation_id: str) -> bool:
        """Delete violation file."""
        file_path = self.violations_path / f"{violation_id}.yaml"
        if file_path.exists():
            file_path.unlink()
            self._cache.pop(violation_id, None)
            return True
        return False

    def find_by_file(self, file_path: str) -> List[Violation]:
        """Find violations for a specific file."""
        return [v for v in self._cache.values() if v.file_path == file_path]

    def find_by_contract(self, contract_id: str) -> List[Violation]:
        """Find violations for a specific contract."""
        return [v for v in self._cache.values() if v.contract_id == contract_id]

    def find_by_check(self, check_id: str) -> List[Violation]:
        """Find violations for a specific check."""
        return [v for v in self._cache.values() if v.check_id == check_id]

    def find_by_status(self, status: ViolationStatus) -> List[Violation]:
        """Find violations by status."""
        return [v for v in self._cache.values() if v.status == status]

    def find_by_severity(self, severity: Severity) -> List[Violation]:
        """Find violations by severity."""
        return [v for v in self._cache.values() if v.severity == severity]

    def count_by_status(self) -> Dict[ViolationStatus, int]:
        """Count violations by status."""
        counts = {status: 0 for status in ViolationStatus}
        for v in self._cache.values():
            counts[v.status] += 1
        return counts

    def count_by_severity(self) -> Dict[Severity, int]:
        """Count violations by severity."""
        counts = {severity: 0 for severity in Severity}
        for v in self._cache.values():
            if v.status == ViolationStatus.OPEN:
                counts[v.severity] += 1
        return counts

    def mark_stale(
        self,
        except_files: Set[str],
        except_contracts: Set[str]
    ) -> int:
        """Mark violations as stale except for specified scope."""
        count = 0
        for violation in self._cache.values():
            if violation.status != ViolationStatus.OPEN:
                continue
            if violation.file_path in except_files:
                continue
            if violation.contract_id in except_contracts:
                continue
            violation.mark_stale()
            self.save(violation)
            count += 1
        return count


class ExemptionRegistry:
    """
    Manages exemptions/ directory.

    Each exemption is stored as {exemption-id}.yaml
    """

    def __init__(self, agentforge_path: Path):
        self.exemptions_path = agentforge_path / "exemptions"
        self._cache: Dict[str, Exemption] = {}

    def ensure_directory(self) -> None:
        """Create exemptions directory if needed."""
        self.exemptions_path.mkdir(parents=True, exist_ok=True)
        gitkeep = self.exemptions_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def load_all(self) -> List[Exemption]:
        """Load all exemptions from disk."""
        self._cache.clear()
        exemptions = []

        if not self.exemptions_path.exists():
            return exemptions

        for file_path in self.exemptions_path.glob("*.yaml"):
            if file_path.name.startswith("."):
                continue
            exemption = self._load_exemption(file_path)
            if exemption:
                self._cache[exemption.id] = exemption
                exemptions.append(exemption)

        return exemptions

    def _load_exemption(self, file_path: Path) -> Optional[Exemption]:
        """Load exemption from YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return self._dict_to_exemption(data)
        except Exception:
            return None

    def _dict_to_exemption(self, data: Dict) -> Exemption:
        """Convert dictionary to Exemption object."""
        scope_data = data.get("scope", {"type": "global"})
        scope = ExemptionScope(
            type=ExemptionScopeType(scope_data["type"]),
            patterns=scope_data.get("patterns"),
            violation_ids=scope_data.get("violation_ids"),
            lines=(
                (scope_data["lines"]["start"], scope_data["lines"]["end"])
                if scope_data.get("lines") else None
            ),
        )

        return Exemption(
            id=data["id"],
            contract_id=data["contract_id"],
            check_ids=data["check_ids"],
            reason=data["reason"],
            approved_by=data["approved_by"],
            approved_date=date.fromisoformat(data["approved_date"]),
            status=ExemptionStatus(data["status"]),
            scope=scope,
            expires=(
                date.fromisoformat(data["expires"])
                if data.get("expires") else None
            ),
            review_date=(
                date.fromisoformat(data["review_date"])
                if data.get("review_date") else None
            ),
            notes=data.get("notes"),
            ticket=data.get("ticket"),
            tags=data.get("tags"),
        )

    def _exemption_to_dict(self, exemption: Exemption) -> Dict:
        """Convert Exemption to dictionary for YAML."""
        scope_dict = {"type": exemption.scope.type.value}
        if exemption.scope.patterns:
            scope_dict["patterns"] = exemption.scope.patterns
        if exemption.scope.violation_ids:
            scope_dict["violation_ids"] = exemption.scope.violation_ids
        if exemption.scope.lines:
            scope_dict["lines"] = {
                "start": exemption.scope.lines[0],
                "end": exemption.scope.lines[1],
            }

        data = {
            "schema_version": "1.0",
            "id": exemption.id,
            "contract_id": exemption.contract_id,
            "check_ids": exemption.check_ids,
            "reason": exemption.reason,
            "approved_by": exemption.approved_by,
            "approved_date": exemption.approved_date.isoformat(),
            "status": exemption.status.value,
            "scope": scope_dict,
        }

        if exemption.expires:
            data["expires"] = exemption.expires.isoformat()
        if exemption.review_date:
            data["review_date"] = exemption.review_date.isoformat()
        if exemption.notes:
            data["notes"] = exemption.notes
        if exemption.ticket:
            data["ticket"] = exemption.ticket
        if exemption.tags:
            data["tags"] = exemption.tags

        return data

    def get(self, exemption_id: str) -> Optional[Exemption]:
        """Get exemption by ID."""
        return self._cache.get(exemption_id)

    def save(self, exemption: Exemption) -> None:
        """Save exemption to disk atomically."""
        self.ensure_directory()
        file_path = self.exemptions_path / f"{exemption.id}.yaml"
        data = self._exemption_to_dict(exemption)

        with AtomicFileWriter(file_path) as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        self._cache[exemption.id] = exemption

    def delete(self, exemption_id: str) -> bool:
        """Delete exemption file."""
        file_path = self.exemptions_path / f"{exemption_id}.yaml"
        if file_path.exists():
            file_path.unlink()
            self._cache.pop(exemption_id, None)
            return True
        return False

    def find_for_violation(self, violation: Violation) -> Optional[Exemption]:
        """Find exemption that covers a violation."""
        for exemption in self._cache.values():
            if exemption.covers_violation(violation):
                return exemption
        return None

    def get_expired(self) -> List[Exemption]:
        """Get all expired exemptions."""
        return [e for e in self._cache.values() if e.is_expired()]

    def get_active(self) -> List[Exemption]:
        """Get all active exemptions."""
        return [e for e in self._cache.values() if e.is_active()]

    def get_needs_review(self) -> List[Exemption]:
        """Get exemptions that need review."""
        return [e for e in self._cache.values() if e.needs_review()]

    def update_status(self, exemption_id: str, status: ExemptionStatus) -> bool:
        """Update exemption status and save."""
        if exemption_id in self._cache:
            exemption = self._cache[exemption_id]
            exemption.status = status
            self.save(exemption)
            return True
        return False


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

    def get_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[HistorySnapshot]:
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


class ReportStore:
    """Manages conformance_report.yaml persistence."""

    def __init__(self, agentforge_path: Path):
        self.report_path = agentforge_path / "conformance_report.yaml"

    def save(self, report: ConformanceReport) -> None:
        """Save conformance report to disk."""
        data = {
            "schema_version": report.schema_version,
            "generated_at": report.generated_at.isoformat(),
            "run_id": report.run_id,
            "run_type": report.run_type,
            "summary": {
                "total": report.summary.total,
                "passed": report.summary.passed,
                "failed": report.summary.failed,
                "exempted": report.summary.exempted,
                "stale": report.summary.stale,
            },
            "by_severity": report.by_severity,
            "by_contract": report.by_contract,
            "contracts_checked": report.contracts_checked,
            "files_checked": report.files_checked,
        }
        if report.trend:
            data["trend"] = report.trend

        with AtomicFileWriter(self.report_path) as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def load(self) -> Optional[ConformanceReport]:
        """Load existing conformance report."""
        if not self.report_path.exists():
            return None

        try:
            with open(self.report_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            summary_data = data["summary"]
            return ConformanceReport(
                schema_version=data["schema_version"],
                generated_at=datetime.fromisoformat(data["generated_at"]),
                run_id=data["run_id"],
                run_type=data["run_type"],
                summary=ConformanceSummary(
                    total=summary_data["total"],
                    passed=summary_data["passed"],
                    failed=summary_data["failed"],
                    exempted=summary_data["exempted"],
                    stale=summary_data.get("stale", 0),
                ),
                by_severity=data["by_severity"],
                by_contract=data["by_contract"],
                contracts_checked=data["contracts_checked"],
                files_checked=data["files_checked"],
                trend=data.get("trend"),
            )
        except Exception:
            return None
