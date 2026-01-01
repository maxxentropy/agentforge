#!/usr/bin/env python3

# @spec_file: .agentforge/specs/tools-v1.yaml
# @spec_id: tools-v1
# @component_id: tools-verification_types
# @test_path: tests/unit/tools/test_verification_checks.py

"""
Verification Types
==================

Data classes and enums for the verification system.

Extracted from verification_runner.py for modularity.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class Severity(Enum):
    BLOCKING = "blocking"
    REQUIRED = "required"
    ADVISORY = "advisory"
    INFORMATIONAL = "informational"


class CheckStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class CheckResult:
    """Result of a single verification check."""
    check_id: str
    check_name: str
    status: CheckStatus
    severity: Severity
    message: str
    duration_ms: int = 0
    details: Optional[str] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    output: Optional[str] = None
    fix_suggestion: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASSED

    @property
    def is_blocking_failure(self) -> bool:
        return not self.passed and self.severity == Severity.BLOCKING


@dataclass
class VerificationReport:
    """Complete verification report with all check results."""
    timestamp: str
    profile: Optional[str]
    project_path: Optional[str]
    working_dir: str
    total_checks: int
    passed: int
    failed: int
    skipped: int
    errors: int
    blocking_failures: int
    required_failures: int
    advisory_warnings: int
    duration_ms: int
    results: List[CheckResult] = field(default_factory=list)
    is_valid: bool = True

    def _update_failure_counts(self, result: CheckResult):
        """Update failure-related counters based on severity."""
        if result.severity == Severity.BLOCKING:
            self.blocking_failures += 1
            self.is_valid = False
        elif result.severity == Severity.REQUIRED:
            self.required_failures += 1
        elif result.severity == Severity.ADVISORY:
            self.advisory_warnings += 1

    def add_result(self, result: CheckResult):
        """Add a check result and update counters."""
        self.results.append(result)
        status_handlers = {
            CheckStatus.PASSED: lambda: setattr(self, 'passed', self.passed + 1),
            CheckStatus.SKIPPED: lambda: setattr(self, 'skipped', self.skipped + 1),
            CheckStatus.ERROR: lambda: self._handle_error_result(result),
            CheckStatus.FAILED: lambda: self._handle_failed_result(result),
        }
        handler = status_handlers.get(result.status)
        if handler:
            handler()

    def _handle_failed_result(self, result: CheckResult):
        """Handle a failed check result."""
        self.failed += 1
        self._update_failure_counts(result)

    def _handle_error_result(self, result: CheckResult):
        """Handle an error check result."""
        self.errors += 1
        if result.severity == Severity.BLOCKING:
            self.is_valid = False
