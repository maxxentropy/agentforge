# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: operation-contract-loader
# @test_path: tests/unit/contracts/test_operations.py

"""
Operation Contract Loader
=========================

Loads and validates operation contracts from YAML templates.

Operation contracts define universal rules that apply to all requests:
- Tool usage patterns
- Git operations
- Safety constraints

These are loaded at startup and merged with per-request task contracts
for comprehensive enforcement.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class OperationRule:
    """A rule from an operation contract."""

    rule_id: str
    description: str
    check_type: str  # sequence_constraint, tool_preference, command_constraint, etc.
    details: dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # error, warning
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.rule_id,
            "description": self.description,
            "check_type": self.check_type,
            "details": self.details,
            "severity": self.severity,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationRule":
        """Deserialize from dictionary."""
        return cls(
            rule_id=data.get("id", ""),
            description=data.get("description", ""),
            check_type=data.get("check_type", ""),
            details=data.get("details", {}),
            severity=data.get("severity", "error"),
            rationale=data.get("rationale", ""),
        )


@dataclass
class OperationTrigger:
    """An escalation trigger from an operation contract."""

    trigger_id: str
    condition: str
    severity: str = "blocking"  # blocking, advisory
    prompt: str = ""
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "trigger_id": self.trigger_id,
            "condition": self.condition,
            "severity": self.severity,
            "prompt": self.prompt,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationTrigger":
        """Deserialize from dictionary."""
        return cls(
            trigger_id=data.get("trigger_id", ""),
            condition=data.get("condition", ""),
            severity=data.get("severity", "blocking"),
            prompt=data.get("prompt", ""),
            rationale=data.get("rationale", ""),
        )


@dataclass
class OperationGate:
    """A quality gate from an operation contract."""

    gate_id: str
    checks: list[str] = field(default_factory=list)
    failure_action: str = "escalate"  # escalate, abort

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "gate_id": self.gate_id,
            "checks": self.checks,
            "failure_action": self.failure_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationGate":
        """Deserialize from dictionary."""
        return cls(
            gate_id=data.get("gate_id", ""),
            checks=data.get("checks", []),
            failure_action=data.get("failure_action", "escalate"),
        )


@dataclass
class OperationContract:
    """An operation contract loaded from YAML.

    Operation contracts define universal rules that apply regardless
    of the specific task being performed. They encode best practices
    and safety constraints.
    """

    contract_id: str
    version: str
    description: str
    rules: list[OperationRule] = field(default_factory=list)
    escalation_triggers: list[OperationTrigger] = field(default_factory=list)
    quality_gates: list[OperationGate] = field(default_factory=list)

    # Source tracking
    source_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.contract_id,
            "version": self.version,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
            "escalation_triggers": [t.to_dict() for t in self.escalation_triggers],
            "quality_gates": [g.to_dict() for g in self.quality_gates],
        }

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], source_path: Path | None = None
    ) -> "OperationContract":
        """Deserialize from dictionary."""
        return cls(
            contract_id=data.get("id", ""),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            rules=[OperationRule.from_dict(r) for r in data.get("rules", [])],
            escalation_triggers=[
                OperationTrigger.from_dict(t)
                for t in data.get("escalation_triggers", [])
            ],
            quality_gates=[
                OperationGate.from_dict(g) for g in data.get("quality_gates", [])
            ],
            source_path=source_path,
        )

    def get_rule(self, rule_id: str) -> OperationRule | None:
        """Get a specific rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def get_rules_by_type(self, check_type: str) -> list[OperationRule]:
        """Get all rules of a specific type."""
        return [r for r in self.rules if r.check_type == check_type]

    def get_rules_by_severity(self, severity: str) -> list[OperationRule]:
        """Get all rules of a specific severity."""
        return [r for r in self.rules if r.severity == severity]


def get_builtin_contracts_path() -> Path:
    """Get path to built-in operation contracts.

    First checks for unified contracts in contracts/builtin/operations/,
    falls back to legacy location in src/.../operations/.
    """
    # Try unified location first (contracts/builtin/operations/)
    unified_path = Path(__file__).parent.parent.parent.parent.parent.parent / "contracts" / "builtin" / "operations"
    if unified_path.exists() and list(unified_path.glob("*.contract.yaml")):
        return unified_path

    # Fall back to legacy location (this directory)
    return Path(__file__).parent


def load_operation_contract(path: Path) -> OperationContract:
    """Load a single operation contract from a YAML file.

    Supports both legacy format (id, rules) and unified format (contract, checks).

    Args:
        path: Path to the contract YAML file

    Returns:
        Loaded OperationContract

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        ValueError: If contract structure is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid contract structure in {path}: expected dict")

    # Check for unified format (schema_version, contract, checks)
    if "contract" in data and "checks" in data:
        return _load_unified_format(data, path)

    # Legacy format (id, rules)
    if "id" not in data:
        raise ValueError(f"Contract missing 'id' field: {path}")

    return OperationContract.from_dict(data, source_path=path)


def _load_unified_format(data: dict, path: Path) -> OperationContract:
    """Load contract from unified format (contract, checks)."""
    contract_data = data.get("contract", {})
    checks = data.get("checks", [])

    # Convert unified checks to operation rules
    rules = []
    for check in checks:
        rule = OperationRule(
            rule_id=check.get("id", ""),
            description=check.get("description", ""),
            check_type=check.get("type", ""),
            details=check.get("config", {}),
            severity=check.get("severity", "warning"),
            rationale=check.get("rationale", ""),
        )
        rules.append(rule)

    # Convert escalation triggers
    triggers = [
        OperationTrigger.from_dict(t)
        for t in data.get("escalation_triggers", [])
    ]

    # Convert quality gates
    gates = [
        OperationGate.from_dict(g)
        for g in data.get("quality_gates", [])
    ]

    return OperationContract(
        contract_id=f"operation.{contract_data.get('name', 'unknown')}.v1",
        version=contract_data.get("version", "1.0.0"),
        description=contract_data.get("description", ""),
        rules=rules,
        escalation_triggers=triggers,
        quality_gates=gates,
        source_path=path,
    )


def load_all_operation_contracts(
    contracts_dir: Path | None = None,
) -> dict[str, OperationContract]:
    """Load all operation contracts from a directory.

    Args:
        contracts_dir: Directory containing contract YAML files.
                      Defaults to built-in contracts directory.

    Returns:
        Dictionary mapping contract IDs to OperationContract objects
    """
    if contracts_dir is None:
        contracts_dir = get_builtin_contracts_path()

    contracts = {}
    for path in contracts_dir.glob("*.contract.yaml"):
        try:
            contract = load_operation_contract(path)
            contracts[contract.contract_id] = contract
        except (ValueError, yaml.YAMLError) as e:
            # Log warning but continue loading other contracts
            import logging

            logging.warning(f"Failed to load contract {path}: {e}")

    return contracts


class OperationContractManager:
    """Manages loaded operation contracts.

    Provides unified access to all operation contract rules,
    triggers, and gates for enforcement.
    """

    def __init__(self, contracts_dir: Path | None = None):
        """Initialize with contracts from directory.

        Args:
            contracts_dir: Directory containing contracts.
                          Defaults to built-in contracts.
        """
        self.contracts = load_all_operation_contracts(contracts_dir)

    def get_all_rules(self) -> list[OperationRule]:
        """Get all rules from all contracts."""
        rules = []
        for contract in self.contracts.values():
            rules.extend(contract.rules)
        return rules

    def get_all_triggers(self) -> list[OperationTrigger]:
        """Get all escalation triggers from all contracts."""
        triggers = []
        for contract in self.contracts.values():
            triggers.extend(contract.escalation_triggers)
        return triggers

    def get_all_gates(self) -> list[OperationGate]:
        """Get all quality gates from all contracts."""
        gates = []
        for contract in self.contracts.values():
            gates.extend(contract.quality_gates)
        return gates

    def get_rules_for_check_type(self, check_type: str) -> list[OperationRule]:
        """Get all rules matching a specific check type."""
        return [r for r in self.get_all_rules() if r.check_type == check_type]

    def get_error_rules(self) -> list[OperationRule]:
        """Get all rules with error severity."""
        return [r for r in self.get_all_rules() if r.severity == "error"]

    def get_blocking_triggers(self) -> list[OperationTrigger]:
        """Get all blocking escalation triggers."""
        return [t for t in self.get_all_triggers() if t.severity == "blocking"]

    def validate_contracts(self) -> list[str]:
        """Validate all loaded contracts for consistency.

        Returns:
            List of validation warnings/errors
        """
        issues = []

        # Check for duplicate rule IDs
        all_rule_ids = [r.rule_id for r in self.get_all_rules()]
        seen = set()
        for rule_id in all_rule_ids:
            if rule_id in seen:
                issues.append(f"Duplicate rule ID: {rule_id}")
            seen.add(rule_id)

        # Check for duplicate trigger IDs
        all_trigger_ids = [t.trigger_id for t in self.get_all_triggers()]
        seen = set()
        for trigger_id in all_trigger_ids:
            if trigger_id in seen:
                issues.append(f"Duplicate trigger ID: {trigger_id}")
            seen.add(trigger_id)

        # Check for empty rules/descriptions
        for rule in self.get_all_rules():
            if not rule.description:
                issues.append(f"Rule {rule.rule_id} has no description")
            if not rule.check_type:
                issues.append(f"Rule {rule.rule_id} has no check_type")

        return issues
