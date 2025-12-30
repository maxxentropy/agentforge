#!/usr/bin/env python3
"""
Verification Report Generation
==============================

Report formatting for verification results.

Formats: text, yaml, json

Extracted from verification_runner.py for modularity.
"""

import json
import yaml
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .verification_types import VerificationReport, CheckResult, CheckStatus


class ReportGenerator:
    """Mixin class providing report generation for VerificationRunner."""

    def generate_report(self, report: "VerificationReport", format: str = "text") -> str:
        """Generate formatted report."""
        if format == "yaml":
            return self._generate_yaml_report(report)
        elif format == "json":
            return self._generate_json_report(report)
        else:
            return self._generate_text_report(report)

    def _format_errors_section(self, errors: list) -> list:
        """Format errors section for a check result."""
        lines = [f"  Errors ({len(errors)}):"]
        for err in errors[:5]:
            err_str = ", ".join(f"{k}: {v}" for k, v in err.items()) if isinstance(err, dict) else str(err)
            lines.append(f"    - {err_str}")
        if len(errors) > 5:
            lines.append(f"    ... and {len(errors) - 5} more")
        return lines

    def _format_check_result(self, result: "CheckResult") -> list:
        """Format a single check result for text report."""
        try:
            from .verification_types import CheckStatus
        except ImportError:
            from verification_types import CheckStatus

        status_icons = {CheckStatus.PASSED: "✓", CheckStatus.FAILED: "✗", CheckStatus.SKIPPED: "○", CheckStatus.ERROR: "!"}
        lines = [
            f"\n{status_icons.get(result.status, '?')} {result.check_id}: {result.check_name} [{result.severity.value.upper()}]",
            f"  {result.message}"
        ]
        if result.details:
            lines.append(f"  Details: {result.details}")
        if result.errors:
            lines.extend(self._format_errors_section(result.errors))
        if result.fix_suggestion and not result.passed:
            lines.append(f"  Fix: {result.fix_suggestion}")
        if result.duration_ms > 0:
            lines.append(f"  Duration: {result.duration_ms}ms")
        return lines

    def _generate_text_report(self, report: "VerificationReport") -> str:
        """Generate human-readable text report."""
        lines = [
            "", "=" * 70, "VERIFICATION REPORT", "=" * 70,
            f"  Timestamp: {report.timestamp}",
            f"  Profile: {report.profile or 'custom'}",
            f"  Project: {report.project_path or 'N/A'}",
            f"  Duration: {report.duration_ms}ms",
            "", "-" * 70, "SUMMARY", "-" * 70,
            f"  Total Checks:      {report.total_checks}",
            f"  Passed:            {report.passed}",
            f"  Failed:            {report.failed}",
            f"  Skipped:           {report.skipped}",
            f"  Errors:            {report.errors}",
            "",
            f"  Blocking Failures: {report.blocking_failures}",
            f"  Required Failures: {report.required_failures}",
            f"  Advisory Warnings: {report.advisory_warnings}",
            "",
            f"  VERDICT: {'PASS' if report.is_valid else 'FAIL'}",
            "", "-" * 70, "DETAILED RESULTS", "-" * 70,
        ]

        for result in report.results:
            lines.extend(self._format_check_result(result))

        lines.extend(["", "=" * 70])
        return "\n".join(lines)

    def _build_report_data(self, report: "VerificationReport") -> dict:
        """Build report data dictionary for YAML/JSON export."""
        return {
            "verification_report": {
                "timestamp": report.timestamp,
                "profile": report.profile,
                "project_path": report.project_path,
                "working_dir": report.working_dir,
                "duration_ms": report.duration_ms,
                "summary": {
                    "total_checks": report.total_checks,
                    "passed": report.passed,
                    "failed": report.failed,
                    "skipped": report.skipped,
                    "errors": report.errors,
                    "blocking_failures": report.blocking_failures,
                    "required_failures": report.required_failures,
                    "advisory_warnings": report.advisory_warnings,
                    "is_valid": report.is_valid,
                },
                "results": [
                    {
                        "check_id": r.check_id,
                        "check_name": r.check_name,
                        "status": r.status.value,
                        "severity": r.severity.value,
                        "message": r.message,
                        "duration_ms": r.duration_ms,
                        "details": r.details,
                        "errors": r.errors if r.errors else None,
                        "fix_suggestion": r.fix_suggestion,
                    }
                    for r in report.results
                ],
            }
        }

    def _generate_yaml_report(self, report: "VerificationReport") -> str:
        """Generate YAML report."""
        data = self._build_report_data(report)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def _generate_json_report(self, report: "VerificationReport") -> str:
        """Generate JSON report."""
        data = self._build_report_data(report)
        return json.dumps(data, indent=2)
