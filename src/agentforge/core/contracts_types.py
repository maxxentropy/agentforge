#!/usr/bin/env python3
"""
Contract Type Definitions
=========================

Data classes for contracts, exemptions, and check results.

Unified schema supporting both user-defined contracts and
built-in operation contracts (code generation rules).

Check Schema (dict fields):
    id: str - Unique identifier
    name: str - Human-readable name
    description: str - What the check does
    type: str - Check type (ast, custom, lint, code_metric, naming_convention, etc.)
    severity: str - error, warning, info
    enabled: bool - Whether check is active
    config: dict - Type-specific configuration
    applies_to: dict - Path patterns for scoping
    fix_hint: str - How to fix violations
    rationale: str - Why this rule matters (educational)
"""

import fnmatch
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


# =============================================================================
# Escalation and Quality Gates (for AI agent governance)
# =============================================================================

@dataclass
class EscalationTrigger:
    """
    Condition that should trigger human escalation.

    Used by AI agents to know when to pause and ask for guidance.
    """
    trigger_id: str
    condition: str  # Human-readable condition description
    severity: str = "advisory"  # blocking, advisory
    prompt: str = ""  # What to ask the human
    rationale: str = ""  # Why this trigger matters

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "condition": self.condition,
            "severity": self.severity,
            "prompt": self.prompt,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationTrigger":
        return cls(
            trigger_id=data.get("trigger_id", ""),
            condition=data.get("condition", ""),
            severity=data.get("severity", "advisory"),
            prompt=data.get("prompt", ""),
            rationale=data.get("rationale", ""),
        )


@dataclass
class QualityGate:
    """
    Quality checkpoint before proceeding to next stage.

    Used to ensure code meets standards before continuing.
    """
    gate_id: str
    checks: list[str] = field(default_factory=list)  # Check IDs to verify
    failure_action: str = "escalate"  # escalate, abort, warn

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "checks": self.checks,
            "failure_action": self.failure_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityGate":
        return cls(
            gate_id=data.get("gate_id", ""),
            checks=data.get("checks", []),
            failure_action=data.get("failure_action", "escalate"),
        )


# =============================================================================
# Check Results
# =============================================================================

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
    """
    Loaded contract with resolved inheritance.

    Unified contract type supporting both user-defined project contracts
    and built-in operation contracts (code generation rules).
    """
    name: str
    type: str  # patterns, security, testing, operations, etc.
    description: str | None = None
    version: str = "1.0.0"
    enabled: bool = True
    extends: list[str] = field(default_factory=list)
    applies_to: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    source_path: Path | None = None
    tier: str = "repo"  # global, workspace, repo, builtin

    # AI agent governance features (from operation contracts)
    escalation_triggers: list[EscalationTrigger] = field(default_factory=list)
    quality_gates: list[QualityGate] = field(default_factory=list)

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
