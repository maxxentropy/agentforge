"""
Conformance Manager
===================

Application layer orchestration for conformance operations.
Coordinates between verification engine, stores, and CLI.
"""

import uuid
import fnmatch
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Set
import yaml

from .domain import (
    Violation, ViolationStatus, Severity,
    Exemption, ExemptionStatus,
    ConformanceReport, ConformanceSummary, HistorySnapshot
)
from .stores import ViolationStore, ExemptionRegistry, AtomicFileWriter, ReportStore
from .history_store import HistoryStore


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

        self._previous_report: Optional[ConformanceReport] = None

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
        self, verification_results: List[Dict], contracts_checked: List[str],
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

        seen_violation_ids: Set[str] = set()
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

    def _create_or_update_violation(self, result: Dict) -> Violation:
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
        self, seen_ids: Set[str], contracts_checked: List[str], resolve: bool
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

    def _generate_report(
        self,
        contracts_checked: List[str],
        files_checked: int,
        is_full_run: bool
    ) -> ConformanceReport:
        """Generate conformance report from current state."""
        all_violations = self.violation_store.load_all()

        # Count by status
        open_violations = [v for v in all_violations if v.status == ViolationStatus.OPEN]
        exempted_violations = [v for v in open_violations if v.exemption_id]
        failed_violations = [v for v in open_violations if not v.exemption_id]
        stale_violations = [v for v in all_violations if v.status == ViolationStatus.STALE]

        # Count by severity (only failed, non-exempted)
        by_severity: Dict[str, int] = {}
        for v in failed_violations:
            severity_name = v.severity.value
            by_severity[severity_name] = by_severity.get(severity_name, 0) + 1

        # Count by contract (only failed, non-exempted)
        by_contract: Dict[str, int] = {}
        for v in failed_violations:
            by_contract[v.contract_id] = by_contract.get(v.contract_id, 0) + 1

        summary = ConformanceSummary(
            total=len(open_violations) + len(stale_violations),
            passed=0,  # Would need check count from verification
            failed=len(failed_violations),
            exempted=len(exempted_violations),
            stale=len(stale_violations),
        )

        # Calculate trend
        trend = None
        if self._previous_report:
            prev = self._previous_report.summary
            trend = {
                "passed_delta": summary.passed - prev.passed,
                "failed_delta": summary.failed - prev.failed,
                "exempted_delta": summary.exempted - prev.exempted,
                "previous_run_id": self._previous_report.run_id,
            }

        return ConformanceReport(
            schema_version="1.0",
            generated_at=datetime.utcnow(),
            run_id=str(uuid.uuid4()),
            run_type="full" if is_full_run else "incremental",
            summary=summary,
            by_severity=by_severity,
            by_contract=by_contract,
            contracts_checked=contracts_checked,
            files_checked=files_checked,
            trend=trend,
        )

    def get_report(self) -> Optional[ConformanceReport]:
        """Get current conformance report."""
        return self.report_store.load()

    def list_violations(
        self,
        status: Optional[ViolationStatus] = None,
        severity: Optional[Severity] = None,
        contract_id: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[Violation]:
        """List violations with optional filters."""
        violations = self.violation_store.load_all()

        if status:
            violations = [v for v in violations if v.status == status]
        if severity:
            violations = [v for v in violations if v.severity == severity]
        if contract_id:
            violations = [v for v in violations if v.contract_id == contract_id]
        if file_pattern:
            violations = [v for v in violations if fnmatch.fnmatch(v.file_path, file_pattern)]

        # Sort by severity (most severe first), then by file
        violations.sort(key=lambda v: (-v.severity.weight, v.file_path))

        return violations[:limit]

    def get_violation(self, violation_id: str) -> Optional[Violation]:
        """Get a specific violation by ID."""
        self.violation_store.load_all()
        return self.violation_store.get(violation_id)

    def resolve_violation(
        self,
        violation_id: str,
        reason: str,
        resolved_by: str = "user"
    ) -> Optional[Violation]:
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

    def get_history(self, days: int = 30) -> List[HistorySnapshot]:
        """Get conformance history for trend analysis."""
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        return self.history_store.get_range(start_date, end_date)

    def get_exemptions(
        self,
        status: Optional[ExemptionStatus] = None,
        contract_id: Optional[str] = None
    ) -> List[Exemption]:
        """List exemptions with optional filters."""
        exemptions = self.exemption_registry.load_all()

        if status:
            exemptions = [e for e in exemptions if e.status == status]
        if contract_id:
            exemptions = [e for e in exemptions if e.contract_id == contract_id]

        return exemptions

    def get_summary_stats(self) -> Dict:
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
