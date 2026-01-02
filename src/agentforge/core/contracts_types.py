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
from typing import Any


@dataclass
class CheckResult:
    """Result of running a single check."""
    check_id: str
    check_name: str
    passed: bool
    severity: str  # error, warning, info
    message: str
    file_path: str | None = None
    line_number: int | None = None
    column: int | None = None
    fix_hint: str | None = None
    exempted: bool = False
    exemption_id: str | None = None


@dataclass
class ContractResult:
    """Result of running all checks in a contract."""
    contract_name: str
    contract_type: str
    passed: bool
    check_results: list[CheckResult] = field(default_factory=list)

    @property
    def errors(self) -> list[CheckResult]:
        return [r for r in self.check_results if not r.passed and r.severity == "error" and not r.exempted]

    @property
    def warnings(self) -> list[CheckResult]:
        return [r for r in self.check_results if not r.passed and r.severity == "warning" and not r.exempted]

    @property
    def exempted_count(self) -> int:
        return len([r for r in self.check_results if r.exempted])


@dataclass
class Exemption:
    """Loaded exemption with scope information."""
    id: str
    contract: str
    checks: list[str]  # Check IDs covered
    reason: str
    approved_by: str
    scope_files: list[str] = field(default_factory=list)
    scope_functions: list[str] = field(default_factory=list)
    scope_lines: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    scope_global: bool = False
    expires: date | None = None
    ticket: str | None = None
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
        return any(fnmatch.fnmatch(normalized, pattern) for pattern in self.scope_files)

    def covers_line(self, file_path: str, line_number: int) -> bool:
        """Check if exemption covers a specific line in a file."""
        if self.scope_global:
            return True
        if not self.covers_file(file_path):
            return False
        normalized = file_path.replace("\\", "/")
        if normalized not in self.scope_lines:
            return True
        return any(start <= line_number <= end for start, end in self.scope_lines[normalized])


@dataclass
class Contract:
    """Loaded contract with resolved inheritance."""
    name: str
    type: str
    description: str | None = None
    version: str = "1.0.0"
    enabled: bool = True
    extends: list[str] = field(default_factory=list)
    applies_to: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    source_path: Path | None = None
    tier: str = "repo"  # global, workspace, repo, builtin

    # Resolved parent contracts (populated by resolve_inheritance)
    _resolved: bool = False
    _inherited_checks: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_abstract(self) -> bool:
        """
        Check if this is an abstract contract (building block, not run directly).

        Abstract contracts are identified by underscore prefix in their name.
        """
        return self.name.startswith("_")

    def all_checks(self) -> list[dict[str, Any]]:
        """Get all checks including inherited ones, with proper merging.

        Child check definitions override specific fields from parent definitions
        while inheriting the rest. This allows contracts to override just
        `enabled` or `severity` without needing to redefine the full check.
        """
        if not self._resolved:
            return self.checks

        # Build lookup of inherited checks by ID
        inherited_by_id: dict[str, dict[str, Any]] = {}
        for check in self._inherited_checks:
            check_id = check.get("id")
            if check_id:
                inherited_by_id[check_id] = check

        result = []
        processed_ids = set()

        # Process child checks, merging with inherited definitions
        for check in self.checks:
            check_id = check.get("id")
            if check_id and check_id in inherited_by_id:
                # Merge: start with inherited, override with child's fields
                merged = inherited_by_id[check_id].copy()
                merged.update(check)
                result.append(merged)
            else:
                # New check defined only in child
                result.append(check)
            if check_id:
                processed_ids.add(check_id)

        # Add inherited checks not overridden by child
        for check in self._inherited_checks:
            if check.get("id") not in processed_ids:
                result.append(check)

        return result
