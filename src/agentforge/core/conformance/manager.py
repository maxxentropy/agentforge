# @spec_file: .agentforge/specs/core-conformance-v1.yaml
# @spec_id: core-conformance-v1
# @component_id: core-conformance-manager
# @test_path: tests/unit/tools/conformance/test_manager.py

"""
Conformance Manager
===================

Application layer orchestration for conformance operations.
Coordinates between verification engine, stores, and CLI.
"""

import fnmatch
import uuid
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .domain import (
    ConformanceReport,
    ConformanceSummary,
    Exemption,
    ExemptionStatus,
    HistorySnapshot,
    Severity,
    Violation,
    ViolationStatus,
)
from .history_store import HistoryStore
from .stores import ExemptionRegistry, ReportStore, ViolationStore


class ConformanceManager:
    """
    Orchestrates conformance operations.

    This is the main entry point for conformance tracking. It coordinates:
    - Processing verification results into violations
    - Managing exemptions and their effect on violations
    - Tracking history for trend analysis
    - Generating conformance reports
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.agentforge_path = repo_root / ".agentforge"

        self.violation_store = ViolationStore(self.agentforge_path)
        self.exemption_registry = ExemptionRegistry(self.agentforge_path)
        self.history_store = HistoryStore(self.agentforge_path)
        self.report_store = ReportStore(self.agentforge_path)

        self._previous_report: ConformanceReport | None = None

    def is_initialized(self) -> bool:
        """Check if conformance tracking is initialized."""
        return self.agentforge_path.exists() and (
            self.agentforge_path / "conformance_report.yaml"
        ).exists()

    def initialize(self, force: bool = False) -> None:
        """
        Initialize .agentforge/ directory structure.

        Creates:
        - .agentforge/violations/
        - .agentforge/exemptions/
        - .agentforge/history/
        - .agentforge/conformance_report.yaml
        """
        if self.agentforge_path.exists() and not force:
            if (self.agentforge_path / "conformance_report.yaml").exists():
                raise FileExistsError(
                    ".agentforge/ already initialized. Use --force to reinitialize."
                )

        # Create directories
        self.agentforge_path.mkdir(exist_ok=True)
        self.violation_store.ensure_directory()
        self.exemption_registry.ensure_directory()
        self.history_store.ensure_directory()

        # Create initial conformance report
        initial_report = ConformanceReport(
            schema_version="1.0",
            generated_at=datetime.utcnow(),
            run_id=str(uuid.uuid4()),
            run_type="full",
            summary=ConformanceSummary(),
            by_severity={},
            by_contract={},
            contracts_checked=[],
            files_checked=0,
        )
        self.report_store.save(initial_report)

        # Add local.yaml to .gitignore
        gitignore_path = self.repo_root / ".gitignore"
        entry = ".agentforge/local.yaml"
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if entry not in content:
                with open(gitignore_path, 'a') as f:
                    f.write(f"\n# AgentForge local config\n{entry}\n")
        else:
            gitignore_path.write_text(f"# AgentForge local config\n{entry}\n")

    def run_conformance_check(
        self, verification_results: list[dict], contracts_checked: list[str],
        files_checked: int, is_full_run: bool = True, save_history: bool = True
    ) -> ConformanceReport:
        """Process verification results and update conformance state."""
        self.violation_store.load_all()
        self.exemption_registry.load_all()
        self._previous_report = self.report_store.load()

        # Handle expired exemptions
        for exemption in self.exemption_registry.get_expired():
            if exemption.status == ExemptionStatus.ACTIVE:
                self.exemption_registry.update_status(exemption.id, ExemptionStatus.EXPIRED)
                for v in self.violation_store.find_by_contract(exemption.contract_id):
                    if v.exemption_id == exemption.id:
                        v.mark_exemption_expired()
                        self.violation_store.save(v)

        seen_violation_ids: set[str] = set()
        for result in verification_results:
            violation = self._create_or_update_violation(result)
            seen_violation_ids.add(violation.violation_id)
            exemption = self.exemption_registry.find_for_violation(violation)
            violation.exemption_id = exemption.id if exemption else None
            self.violation_store.save(violation)

        # Mark unseen violations (resolved for full run, stale for incremental)
        self._mark_unseen_violations(seen_violation_ids, contracts_checked, resolve=is_full_run)

        # Generate report
        report = self._generate_report(contracts_checked, files_checked, is_full_run)
        self.report_store.save(report)

        # Save history snapshot
        if save_history:
            snapshot = HistorySnapshot(
                schema_version="1.0", date=date.today(), generated_at=datetime.utcnow(),
                summary=report.summary, by_severity=report.by_severity,
                by_contract=report.by_contract, files_analyzed=report.files_checked,
                contracts_checked=report.contracts_checked,
            )
            self.history_store.save_snapshot(snapshot)
            self.history_store.prune_old_snapshots()

        return report

    def _create_or_update_violation(self, result: dict) -> Violation:
        """Create new violation or update existing one."""
        violation_id = Violation.generate_id(
            contract_id=result["contract_id"],
            check_id=result["check_id"],
            file_path=result["file"],
            line_number=result.get("line"),
            rule_id=result.get("rule_id"),
        )

        existing = self.violation_store.get(violation_id)
        now = datetime.utcnow()

        if existing:
            # Update last_seen_at and ensure open status
            existing.last_seen_at = now
            if existing.status in (ViolationStatus.RESOLVED, ViolationStatus.STALE):
                existing.reopen()
            # Update test_path if not set (for existing violations created before this feature)
            if not existing.test_path:
                existing.test_path = Violation.compute_test_path(result["file"], self.repo_root)
            return existing

        # Compute test_path at detection time - this tells fix workflow which tests to run
        test_path = Violation.compute_test_path(result["file"], self.repo_root)

        # Create new violation
        return Violation(
            violation_id=violation_id,
            contract_id=result["contract_id"],
            check_id=result["check_id"],
            severity=Severity.from_contract_severity(result.get("severity", "warning")),
            file_path=result["file"],
            message=result["message"],
            detected_at=now,
            last_seen_at=now,
            status=ViolationStatus.OPEN,
            line_number=result.get("line"),
            column_number=result.get("column"),
            rule_id=result.get("rule_id"),
            fix_hint=result.get("fix_hint"),
            test_path=test_path,
        )

    def _mark_unseen_violations(
        self, seen_ids: set[str], contracts_checked: list[str], resolve: bool
    ) -> None:
        """Mark violations as resolved or stale if not seen in current run."""
        checked = set(contracts_checked)
        for violation in self.violation_store.find_by_status(ViolationStatus.OPEN):
            if violation.contract_id not in checked:
                continue
            if violation.violation_id not in seen_ids:
                if resolve:
                    violation.mark_resolved("No longer detected in full verification run")
                else:
                    violation.mark_stale()
                self.violation_store.save(violation)

    def _categorize_violations(
        self, all_violations: list[Violation]
    ) -> tuple[list[Violation], list[Violation], list[Violation], list[Violation]]:
        """Categorize violations by status. Returns (open, exempted, failed, stale)."""
        open_violations = [v for v in all_violations if v.status == ViolationStatus.OPEN]
        exempted = [v for v in open_violations if v.exemption_id]
        failed = [v for v in open_violations if not v.exemption_id]
        stale = [v for v in all_violations if v.status == ViolationStatus.STALE]
        return open_violations, exempted, failed, stale

    def _count_by_attribute(
        self, violations: list[Violation], attr: str
    ) -> dict[str, int]:
        """Count violations by a given attribute."""
        counts: dict[str, int] = {}
        for v in violations:
            value = getattr(v, attr)
            key = value.value if hasattr(value, 'value') else str(value)
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _calculate_trend(self, summary: ConformanceSummary) -> dict[str, Any] | None:
        """Calculate trend from previous report if available."""
        if not self._previous_report:
            return None
        prev = self._previous_report.summary
        return {
            "passed_delta": summary.passed - prev.passed,
            "failed_delta": summary.failed - prev.failed,
            "exempted_delta": summary.exempted - prev.exempted,
            "previous_run_id": self._previous_report.run_id,
        }

    def _generate_report(
        self,
        contracts_checked: list[str],
        files_checked: int,
        is_full_run: bool
    ) -> ConformanceReport:
        """Generate conformance report from current state."""
        all_violations = self.violation_store.load_all()
        open_violations, exempted, failed, stale = self._categorize_violations(all_violations)

        summary = ConformanceSummary(
            total=len(open_violations) + len(stale),
            passed=0,
            failed=len(failed),
            exempted=len(exempted),
            stale=len(stale),
        )

        return ConformanceReport(
            schema_version="1.0",
            generated_at=datetime.utcnow(),
            run_id=str(uuid.uuid4()),
            run_type="full" if is_full_run else "incremental",
            summary=summary,
            by_severity=self._count_by_attribute(failed, "severity"),
            by_contract=self._count_by_attribute(failed, "contract_id"),
            contracts_checked=contracts_checked,
            files_checked=files_checked,
            trend=self._calculate_trend(summary),
        )

    def get_report(self) -> ConformanceReport | None:
        """Get current conformance report."""
        return self.report_store.load()

    def _build_violation_filters(
        self,
        status: ViolationStatus | None,
        severity: Severity | None,
        contract_id: str | None,
        file_pattern: str | None,
    ) -> list[Callable[[Violation], bool]]:
        """Build list of filter functions for violations."""
        filters: list[Callable[[Violation], bool]] = []
        if status:
            filters.append(lambda v, s=status: v.status == s)
        if severity:
            filters.append(lambda v, s=severity: v.severity == s)
        if contract_id:
            filters.append(lambda v, c=contract_id: v.contract_id == c)
        if file_pattern:
            filters.append(lambda v, p=file_pattern: fnmatch.fnmatch(v.file_path, p))
        return filters

    def list_violations(
        self,
        status: ViolationStatus | None = None,
        severity: Severity | None = None,
        contract_id: str | None = None,
        file_pattern: str | None = None,
        limit: int = 50
    ) -> list[Violation]:
        """List violations with optional filters."""
        violations = self.violation_store.load_all()
        filters = self._build_violation_filters(status, severity, contract_id, file_pattern)

        for filt in filters:
            violations = [v for v in violations if filt(v)]

        # Sort by severity (most severe first), then by file
        violations.sort(key=lambda v: (-v.severity.weight, v.file_path))
        return violations[:limit]

    def get_violation(self, violation_id: str) -> Violation | None:
        """Get a specific violation by ID."""
        self.violation_store.load_all()
        return self.violation_store.get(violation_id)

    def resolve_violation(
        self,
        violation_id: str,
        reason: str,
        resolved_by: str = "user"
    ) -> Violation | None:
        """Mark a violation as resolved."""
        self.violation_store.load_all()
        violation = self.violation_store.get(violation_id)
        if not violation:
            return None

        violation.mark_resolved(reason, resolved_by)
        self.violation_store.save(violation)
        return violation

    def prune_violations(
        self,
        older_than_days: int = 30,
        dry_run: bool = False
    ) -> int:
        """Remove old resolved/stale violations."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)

        violations = self.violation_store.load_all()
        to_prune = [
            v for v in violations
            if v.status in (ViolationStatus.RESOLVED, ViolationStatus.STALE)
            and v.last_seen_at < cutoff
        ]

        if not dry_run:
            for v in to_prune:
                self.violation_store.delete(v.violation_id)

        return len(to_prune)

    def get_history(self, days: int = 30) -> list[HistorySnapshot]:
        """Get conformance history for trend analysis."""
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        return self.history_store.get_range(start_date, end_date)

    def get_exemptions(
        self,
        status: ExemptionStatus | None = None,
        contract_id: str | None = None
    ) -> list[Exemption]:
        """List exemptions with optional filters."""
        exemptions = self.exemption_registry.load_all()

        if status:
            exemptions = [e for e in exemptions if e.status == status]
        if contract_id:
            exemptions = [e for e in exemptions if e.contract_id == contract_id]

        return exemptions

    def get_summary_stats(self) -> dict:
        """Get summary statistics for dashboard display."""
        report = self.get_report()
        if not report:
            return {"initialized": False}

        self.violation_store.load_all()
        self.exemption_registry.load_all()

        return {
            "initialized": True,
            "last_run": report.generated_at.isoformat(),
            "run_type": report.run_type,
            "violations": {
                "open": report.summary.failed,
                "exempted": report.summary.exempted,
                "stale": report.summary.stale,
                "by_severity": report.by_severity,
            },
            "exemptions": {
                "active": len(self.exemption_registry.get_active()),
                "expired": len(self.exemption_registry.get_expired()),
                "needs_review": len(self.exemption_registry.get_needs_review()),
            },
            "contracts_checked": report.contracts_checked,
            "files_checked": report.files_checked,
            "trend": report.trend,
        }
