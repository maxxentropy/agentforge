#!/usr/bin/env python3
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

    def add_result(self, result: CheckResult):
        self.results.append(result)
        if result.status == CheckStatus.PASSED:
            self.passed += 1
        elif result.status == CheckStatus.FAILED:
            self.failed += 1
            if result.severity == Severity.BLOCKING:
                self.blocking_failures += 1
                self.is_valid = False
            elif result.severity == Severity.REQUIRED:
                self.required_failures += 1
            elif result.severity == Severity.ADVISORY:
                self.advisory_warnings += 1
        elif result.status == CheckStatus.SKIPPED:
            self.skipped += 1
        elif result.status == CheckStatus.ERROR:
            self.errors += 1
            if result.severity == Severity.BLOCKING:
                self.is_valid = False
