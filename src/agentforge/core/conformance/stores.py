# @spec_file: .agentforge/specs/core-conformance-v1.yaml
# @spec_id: core-conformance-v1
# @component_id: core-conformance-stores
# @test_path: tests/unit/tools/conformance/test_stores.py

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

import contextlib
import os
import shutil
import tempfile
from datetime import date, datetime
from pathlib import Path

import yaml

from .domain import (
    ConformanceReport,
    ConformanceSummary,
    Exemption,
    ExemptionScope,
    ExemptionScopeType,
    ExemptionStatus,
    Severity,
    Violation,
    ViolationStatus,
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
            with contextlib.suppress(OSError):
                os.unlink(self.temp_path)
        return False


class ViolationStore:
    """
    Manages violations/ directory.

    Each violation is stored as a separate YAML file: V-{hash}.yaml
    This makes Git merges cleaner and allows parallel updates.
    """

    def __init__(self, agentforge_path: Path):
        self.violations_path = agentforge_path / "violations"
        self._cache: dict[str, Violation] = {}

    def ensure_directory(self) -> None:
        """Create violations directory if needed."""
        self.violations_path.mkdir(parents=True, exist_ok=True)
        gitkeep = self.violations_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def load_all(self) -> list[Violation]:
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

    def _load_violation(self, file_path: Path) -> Violation | None:
        """Load a single violation from YAML file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return self._dict_to_violation(data)
        except Exception:
            return None

    def _dict_to_violation(self, data: dict) -> Violation:
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
            test_path=data.get("test_path"),
        )

    def _violation_to_dict(self, violation: Violation) -> dict:
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
        # Test path for verification during fixes (from lineage or convention)
        if violation.test_path:
            data["test_path"] = violation.test_path

        return data

    def get(self, violation_id: str) -> Violation | None:
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

    def find_by_contract(self, contract_id: str) -> list[Violation]:
        """Find violations for a specific contract."""
        return [v for v in self._cache.values() if v.contract_id == contract_id]

    def find_by_status(self, status: ViolationStatus) -> list[Violation]:
        """Find violations by status."""
        return [v for v in self._cache.values() if v.status == status]

    def count_by_status(self) -> dict[ViolationStatus, int]:
        """Count violations by status."""
        counts = dict.fromkeys(ViolationStatus, 0)
        for v in self._cache.values():
            counts[v.status] += 1
        return counts

    def count_by_severity(self) -> dict[Severity, int]:
        """Count violations by severity."""
        counts = dict.fromkeys(Severity, 0)
        for v in self._cache.values():
            if v.status == ViolationStatus.OPEN:
                counts[v.severity] += 1
        return counts

    def mark_stale(
        self,
        except_files: set[str],
        except_contracts: set[str]
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
        self._cache: dict[str, Exemption] = {}

    def ensure_directory(self) -> None:
        """Create exemptions directory if needed."""
        self.exemptions_path.mkdir(parents=True, exist_ok=True)
        gitkeep = self.exemptions_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def load_all(self) -> list[Exemption]:
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

    def _load_exemption(self, file_path: Path) -> Exemption | None:
        """Load exemption from YAML file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return self._dict_to_exemption(data)
        except Exception:
            return None

    def _dict_to_exemption(self, data: dict) -> Exemption:
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

    def _exemption_to_dict(self, exemption: Exemption) -> dict:
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

    def get(self, exemption_id: str) -> Exemption | None:
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

    def find_for_violation(self, violation: Violation) -> Exemption | None:
        """Find exemption that covers a violation."""
        for exemption in self._cache.values():
            if exemption.covers_violation(violation):
                return exemption
        return None

    def get_expired(self) -> list[Exemption]:
        """Get all expired exemptions."""
        return [e for e in self._cache.values() if e.is_expired()]

    def get_active(self) -> list[Exemption]:
        """Get all active exemptions."""
        return [e for e in self._cache.values() if e.is_active()]

    def get_needs_review(self) -> list[Exemption]:
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

    def load(self) -> ConformanceReport | None:
        """Load existing conformance report."""
        if not self.report_path.exists():
            return None

        try:
            with open(self.report_path, encoding='utf-8') as f:
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
