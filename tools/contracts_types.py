#!/usr/bin/env python3
"""
Contract Type Definitions
=========================

Data classes for contracts, exemptions, and check results.

Extracted from contracts.py for modularity.
"""

import fnmatch
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CheckResult:
    """Result of running a single check."""
    check_id: str
    check_name: str
    passed: bool
    severity: str  # error, warning, info
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    fix_hint: Optional[str] = None
    exempted: bool = False
    exemption_id: Optional[str] = None


@dataclass
class ContractResult:
    """Result of running all checks in a contract."""
    contract_name: str
    contract_type: str
    passed: bool
    check_results: List[CheckResult] = field(default_factory=list)

    @property
    def errors(self) -> List[CheckResult]:
        return [r for r in self.check_results if not r.passed and r.severity == "error" and not r.exempted]

    @property
    def warnings(self) -> List[CheckResult]:
        return [r for r in self.check_results if not r.passed and r.severity == "warning" and not r.exempted]

    @property
    def exempted_count(self) -> int:
        return len([r for r in self.check_results if r.exempted])


@dataclass
class Exemption:
    """Loaded exemption with scope information."""
    id: str
    contract: str
    checks: List[str]  # Check IDs covered
    reason: str
    approved_by: str
    scope_files: List[str] = field(default_factory=list)
    scope_functions: List[str] = field(default_factory=list)
    scope_lines: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    scope_global: bool = False
    expires: Optional[date] = None
    ticket: Optional[str] = None
    status: str = "active"

    def is_expired(self) -> bool:
        """Check if exemption has expired."""
        if self.expires is None:
            return False
        return date.today() > self.expires

    def is_active(self) -> bool:
        """Check if exemption is currently active."""
        return self.status == "active" and not self.is_expired()

    def covers_file(self, file_path: str) -> bool:
        """Check if exemption covers a specific file."""
        if self.scope_global:
            return True
        if not self.scope_files:
            return False
        normalized = file_path.replace("\\", "/")
        for pattern in self.scope_files:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        return False

    def covers_line(self, file_path: str, line_number: int) -> bool:
        """Check if exemption covers a specific line in a file."""
        if self.scope_global:
            return True
        if not self.covers_file(file_path):
            return False
        normalized = file_path.replace("\\", "/")
        if normalized not in self.scope_lines:
            return True
        for start, end in self.scope_lines[normalized]:
            if start <= line_number <= end:
                return True
        return False


@dataclass
class Contract:
    """Loaded contract with resolved inheritance."""
    name: str
    type: str
    description: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    extends: List[str] = field(default_factory=list)
    applies_to: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    checks: List[Dict[str, Any]] = field(default_factory=list)
    source_path: Optional[Path] = None
    tier: str = "repo"  # global, workspace, repo, builtin

    # Resolved parent contracts (populated by resolve_inheritance)
    _resolved: bool = False
    _inherited_checks: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_abstract(self) -> bool:
        """
        Check if this is an abstract contract (building block, not run directly).

        Abstract contracts are identified by underscore prefix in their name.
        """
        return self.name.startswith("_")

    def all_checks(self) -> List[Dict[str, Any]]:
        """Get all checks including inherited ones."""
        if not self._resolved:
            return self.checks
        check_ids = set()
        result = []
        for check in self.checks:
            check_ids.add(check.get("id"))
            result.append(check)
        for check in self._inherited_checks:
            if check.get("id") not in check_ids:
                result.append(check)
        return result
