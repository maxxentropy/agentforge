#!/usr/bin/env python3
"""
Contract Validator Types
========================

Data classes for contract validation.

Extracted from contract_validator.py for modularity.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Severity(Enum):
    """Severity levels for validation checks."""
    BLOCKING = "blocking"
    REQUIRED = "required"
    ADVISORY = "advisory"
    INFORMATIONAL = "informational"


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_id: str
    check_name: str
    passed: bool
    severity: Severity
    message: str
    details: Optional[str] = None


@dataclass
class ContractValidationReport:
    """Complete validation report for a contract."""
    contract_id: str
    contract_version: str
    is_valid: bool
    results: List[ValidationResult] = field(default_factory=list)
    blocking_failures: int = 0
    required_failures: int = 0
    advisory_warnings: int = 0

    def add_result(self, result: ValidationResult):
        """Add a validation result and update failure counts."""
        self.results.append(result)
        if not result.passed:
            if result.severity == Severity.BLOCKING:
                self.blocking_failures += 1
                self.is_valid = False
            elif result.severity == Severity.REQUIRED:
                self.required_failures += 1
            elif result.severity == Severity.ADVISORY:
                self.advisory_warnings += 1
