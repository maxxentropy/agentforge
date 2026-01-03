# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: operation-contract-tests

"""Tests for operation contracts and loader."""

import pytest
from pathlib import Path

from agentforge.core.contracts.operations import (
    OperationContract,
    OperationRule,
    OperationTrigger,
    OperationGate,
    load_operation_contract,
    load_all_operation_contracts,
    get_builtin_contracts_path,
)
from agentforge.core.contracts.operations.loader import OperationContractManager


class TestOperationRule:
    """Tests for OperationRule."""

    def test_rule_creation(self):
        """Create an operation rule."""
        rule = OperationRule(
            rule_id="read-before-edit",
            description="Must read a file before editing it",
            check_type="sequence_constraint",
            details={"for_tool": "Edit", "requires_prior": "Read"},
            severity="error",
        )

        assert rule.rule_id == "read-before-edit"
        assert rule.check_type == "sequence_constraint"
        assert rule.severity == "error"

    def test_rule_to_dict(self):
        """Serialize rule to dictionary."""
        rule = OperationRule(
            rule_id="test-rule",
            description="Test",
            check_type="tool_preference",
        )

        data = rule.to_dict()

        assert data["id"] == "test-rule"
        assert data["check_type"] == "tool_preference"

    def test_rule_from_dict(self):
        """Deserialize rule from dictionary."""
        data = {
            "id": "test-rule",
            "description": "Test rule",
            "check_type": "command_constraint",
            "severity": "warning",
        }

        rule = OperationRule.from_dict(data)

        assert rule.rule_id == "test-rule"
        assert rule.severity == "warning"


class TestOperationTrigger:
    """Tests for OperationTrigger."""

    def test_trigger_creation(self):
        """Create an operation trigger."""
        trigger = OperationTrigger(
            trigger_id="force-push-requested",
            condition="Force push is needed",
            severity="blocking",
            prompt="Please confirm force push",
        )

        assert trigger.trigger_id == "force-push-requested"
        assert trigger.severity == "blocking"

    def test_trigger_to_dict(self):
        """Serialize trigger to dictionary."""
        trigger = OperationTrigger(
            trigger_id="test-trigger",
            condition="Test condition",
        )

        data = trigger.to_dict()

        assert data["trigger_id"] == "test-trigger"

    def test_trigger_from_dict(self):
        """Deserialize trigger from dictionary."""
        data = {
            "trigger_id": "test-trigger",
            "condition": "Some condition",
            "severity": "advisory",
        }

        trigger = OperationTrigger.from_dict(data)

        assert trigger.trigger_id == "test-trigger"
        assert trigger.severity == "advisory"


class TestOperationGate:
    """Tests for OperationGate."""

    def test_gate_creation(self):
        """Create an operation gate."""
        gate = OperationGate(
            gate_id="pre-commit-check",
            checks=["No uncommitted changes", "Valid commit message"],
            failure_action="escalate",
        )

        assert gate.gate_id == "pre-commit-check"
        assert len(gate.checks) == 2

    def test_gate_to_dict(self):
        """Serialize gate to dictionary."""
        gate = OperationGate(
            gate_id="test-gate",
            checks=["Check 1"],
        )

        data = gate.to_dict()

        assert data["gate_id"] == "test-gate"

    def test_gate_from_dict(self):
        """Deserialize gate from dictionary."""
        data = {
            "gate_id": "test-gate",
            "checks": ["A", "B"],
            "failure_action": "abort",
        }

        gate = OperationGate.from_dict(data)

        assert gate.gate_id == "test-gate"
        assert gate.failure_action == "abort"


class TestOperationContract:
    """Tests for OperationContract."""

    def test_contract_creation(self):
        """Create an operation contract."""
        contract = OperationContract(
            contract_id="operation.test.v1",
            version="1.0",
            description="Test contract",
            rules=[
                OperationRule(
                    rule_id="rule-1",
                    description="Rule 1",
                    check_type="constraint",
                ),
            ],
        )

        assert contract.contract_id == "operation.test.v1"
        assert len(contract.rules) == 1

    def test_contract_to_dict(self):
        """Serialize contract to dictionary."""
        contract = OperationContract(
            contract_id="operation.test.v1",
            version="1.0",
            description="Test",
        )

        data = contract.to_dict()

        assert data["id"] == "operation.test.v1"
        assert data["version"] == "1.0"

    def test_contract_from_dict(self):
        """Deserialize contract from dictionary."""
        data = {
            "id": "operation.test.v1",
            "version": "2.0",
            "description": "Test contract",
            "rules": [
                {
                    "id": "rule-1",
                    "description": "Rule",
                    "check_type": "constraint",
                }
            ],
        }

        contract = OperationContract.from_dict(data)

        assert contract.contract_id == "operation.test.v1"
        assert contract.version == "2.0"
        assert len(contract.rules) == 1

    def test_get_rule(self):
        """Get a specific rule by ID."""
        contract = OperationContract(
            contract_id="test",
            version="1.0",
            description="Test",
            rules=[
                OperationRule("rule-1", "Rule 1", "type1"),
                OperationRule("rule-2", "Rule 2", "type2"),
            ],
        )

        rule = contract.get_rule("rule-2")

        assert rule is not None
        assert rule.rule_id == "rule-2"

    def test_get_rule_nonexistent(self):
        """Get rule returns None for nonexistent ID."""
        contract = OperationContract("test", "1.0", "Test")

        assert contract.get_rule("nonexistent") is None

    def test_get_rules_by_type(self):
        """Get rules filtered by check type."""
        contract = OperationContract(
            contract_id="test",
            version="1.0",
            description="Test",
            rules=[
                OperationRule("r1", "Rule 1", "command_constraint"),
                OperationRule("r2", "Rule 2", "tool_preference"),
                OperationRule("r3", "Rule 3", "command_constraint"),
            ],
        )

        cmd_rules = contract.get_rules_by_type("command_constraint")

        assert len(cmd_rules) == 2
        assert all(r.check_type == "command_constraint" for r in cmd_rules)

    def test_get_rules_by_severity(self):
        """Get rules filtered by severity."""
        contract = OperationContract(
            contract_id="test",
            version="1.0",
            description="Test",
            rules=[
                OperationRule("r1", "Rule 1", "type", severity="error"),
                OperationRule("r2", "Rule 2", "type", severity="warning"),
                OperationRule("r3", "Rule 3", "type", severity="error"),
            ],
        )

        errors = contract.get_rules_by_severity("error")

        assert len(errors) == 2


class TestLoadOperationContract:
    """Tests for loading operation contracts from files."""

    @pytest.fixture
    def temp_contract(self, tmp_path):
        """Create a temporary contract file."""
        contract_yaml = """
id: operation.test.v1
version: "1.0"
description: Test contract

rules:
  - id: test-rule
    description: A test rule
    check_type: test_constraint
    severity: warning

escalation_triggers:
  - trigger_id: test-trigger
    condition: Test condition

quality_gates:
  - gate_id: test-gate
    checks:
      - Check 1
"""
        path = tmp_path / "test.contract.yaml"
        path.write_text(contract_yaml)
        return path

    def test_load_contract_from_file(self, temp_contract):
        """Load a contract from a YAML file."""
        contract = load_operation_contract(temp_contract)

        assert contract.contract_id == "operation.test.v1"
        assert len(contract.rules) == 1
        assert len(contract.escalation_triggers) == 1
        assert len(contract.quality_gates) == 1

    def test_load_contract_preserves_source(self, temp_contract):
        """Loading preserves source path."""
        contract = load_operation_contract(temp_contract)

        assert contract.source_path == temp_contract

    def test_load_contract_file_not_found(self, tmp_path):
        """Load raises for missing file."""
        with pytest.raises(FileNotFoundError):
            load_operation_contract(tmp_path / "nonexistent.yaml")

    def test_load_contract_invalid_structure(self, tmp_path):
        """Load raises for invalid structure."""
        path = tmp_path / "invalid.contract.yaml"
        path.write_text("just a string")

        with pytest.raises(ValueError, match="expected dict"):
            load_operation_contract(path)

    def test_load_contract_missing_id(self, tmp_path):
        """Load raises for missing ID."""
        path = tmp_path / "no-id.contract.yaml"
        path.write_text("description: No ID field")

        with pytest.raises(ValueError, match="missing 'id'"):
            load_operation_contract(path)


class TestLoadAllOperationContracts:
    """Tests for loading all contracts from a directory."""

    @pytest.fixture
    def temp_contracts_dir(self, tmp_path):
        """Create a directory with multiple contracts."""
        contract1 = """
id: operation.one.v1
version: "1.0"
description: Contract one
rules: []
"""
        contract2 = """
id: operation.two.v1
version: "1.0"
description: Contract two
rules: []
"""
        (tmp_path / "one.contract.yaml").write_text(contract1)
        (tmp_path / "two.contract.yaml").write_text(contract2)
        return tmp_path

    def test_load_all_from_directory(self, temp_contracts_dir):
        """Load all contracts from a directory."""
        contracts = load_all_operation_contracts(temp_contracts_dir)

        assert len(contracts) == 2
        assert "operation.one.v1" in contracts
        assert "operation.two.v1" in contracts

    def test_load_builtin_contracts(self):
        """Load built-in operation contracts."""
        contracts = load_all_operation_contracts()

        # We now have 9 operation contracts
        assert len(contracts) >= 9
        # Original 3
        assert "operation.tool-usage.v1" in contracts
        assert "operation.git.v1" in contracts
        assert "operation.safety.v1" in contracts
        # New 6 design/architecture contracts
        assert "operation.code-generation.v1" in contracts
        assert "operation.testing-patterns.v1" in contracts
        assert "operation.error-handling.v1" in contracts
        assert "operation.api-design.v1" in contracts
        assert "operation.async-patterns.v1" in contracts
        assert "operation.observability.v1" in contracts

    def test_load_skips_invalid_contracts(self, tmp_path):
        """Invalid contracts are skipped with warning."""
        valid = """
id: operation.valid.v1
version: "1.0"
description: Valid
"""
        invalid = "not: valid: yaml: [["

        (tmp_path / "valid.contract.yaml").write_text(valid)
        (tmp_path / "invalid.contract.yaml").write_text(invalid)

        contracts = load_all_operation_contracts(tmp_path)

        assert len(contracts) == 1
        assert "operation.valid.v1" in contracts


class TestOperationContractManager:
    """Tests for OperationContractManager."""

    @pytest.fixture
    def manager(self):
        """Create manager with built-in contracts."""
        return OperationContractManager()

    def test_manager_loads_contracts(self, manager):
        """Manager loads contracts on init."""
        assert len(manager.contracts) >= 3

    def test_get_all_rules(self, manager):
        """Get all rules from all contracts."""
        rules = manager.get_all_rules()

        assert len(rules) > 0
        # Each contract has multiple rules
        assert len(rules) > 3

    def test_get_all_triggers(self, manager):
        """Get all triggers from all contracts."""
        triggers = manager.get_all_triggers()

        assert len(triggers) > 0

    def test_get_all_gates(self, manager):
        """Get all gates from all contracts."""
        gates = manager.get_all_gates()

        assert len(gates) > 0

    def test_get_rules_for_check_type(self, manager):
        """Filter rules by check type."""
        cmd_rules = manager.get_rules_for_check_type("command_constraint")

        assert len(cmd_rules) > 0
        assert all(r.check_type == "command_constraint" for r in cmd_rules)

    def test_get_error_rules(self, manager):
        """Get all error-severity rules."""
        errors = manager.get_error_rules()

        assert len(errors) > 0
        assert all(r.severity == "error" for r in errors)

    def test_get_blocking_triggers(self, manager):
        """Get all blocking triggers."""
        blocking = manager.get_blocking_triggers()

        assert len(blocking) > 0
        assert all(t.severity == "blocking" for t in blocking)

    def test_validate_contracts(self, manager):
        """Validate loaded contracts."""
        issues = manager.validate_contracts()

        # Built-in contracts should have no issues
        assert len(issues) == 0

    def test_validate_detects_duplicates(self, tmp_path):
        """Validation detects duplicate IDs."""
        contract = """
id: operation.dup.v1
version: "1.0"
description: Has duplicates
rules:
  - id: same-id
    description: Rule 1
    check_type: test
  - id: same-id
    description: Rule 2
    check_type: test
"""
        (tmp_path / "dup.contract.yaml").write_text(contract)
        manager = OperationContractManager(tmp_path)

        issues = manager.validate_contracts()

        assert any("Duplicate rule ID: same-id" in issue for issue in issues)


class TestBuiltinContracts:
    """Tests for built-in operation contracts."""

    @pytest.fixture
    def manager(self):
        """Load built-in contracts."""
        return OperationContractManager()

    def test_tool_usage_contract(self, manager):
        """Tool usage contract is properly structured."""
        contract = manager.contracts.get("operation.tool-usage.v1")

        assert contract is not None
        assert contract.get_rule("read-before-edit") is not None
        assert contract.get_rule("glob-for-discovery") is not None
        assert contract.get_rule("read-not-cat") is not None

    def test_git_operations_contract(self, manager):
        """Git operations contract is properly structured."""
        contract = manager.contracts.get("operation.git.v1")

        assert contract is not None
        assert contract.get_rule("no-force-push") is not None
        assert contract.get_rule("no-main-direct") is not None
        assert contract.get_rule("commit-message-format") is not None

    def test_safety_rules_contract(self, manager):
        """Safety rules contract is properly structured."""
        contract = manager.contracts.get("operation.safety.v1")

        assert contract is not None
        assert contract.get_rule("no-secrets-in-code") is not None
        assert contract.get_rule("no-destructive-system") is not None
        assert contract.get_rule("no-sudo-without-approval") is not None

    def test_code_generation_contract(self, manager):
        """Code generation contract covers SOLID and design patterns."""
        contract = manager.contracts.get("operation.code-generation.v1")

        assert contract is not None
        # SOLID principles
        assert contract.get_rule("single-responsibility") is not None
        assert contract.get_rule("open-closed") is not None
        assert contract.get_rule("liskov-substitution") is not None
        assert contract.get_rule("interface-segregation") is not None
        assert contract.get_rule("dependency-inversion") is not None
        # Code structure rules
        assert contract.get_rule("function-size-limit") is not None
        assert contract.get_rule("cyclomatic-complexity-limit") is not None
        # Naming conventions
        assert contract.get_rule("descriptive-naming") is not None
        assert contract.get_rule("boolean-naming") is not None

    def test_testing_patterns_contract(self, manager):
        """Testing patterns contract covers test structure and quality."""
        contract = manager.contracts.get("operation.testing-patterns.v1")

        assert contract is not None
        # Test structure
        assert contract.get_rule("arrange-act-assert") is not None
        assert contract.get_rule("one-assertion-concept") is not None
        # Test isolation
        assert contract.get_rule("test-isolation") is not None
        assert contract.get_rule("no-flaky-tests") is not None
        assert contract.get_rule("mock-at-boundaries") is not None
        # Test coverage
        assert contract.get_rule("test-pyramid") is not None
        assert contract.get_rule("coverage-requirements") is not None

    def test_error_handling_contract(self, manager):
        """Error handling contract covers exceptions and Result pattern."""
        contract = manager.contracts.get("operation.error-handling.v1")

        assert contract is not None
        # Exception design
        assert contract.get_rule("custom-exception-hierarchy") is not None
        assert contract.get_rule("exception-information") is not None
        # Exception handling
        assert contract.get_rule("catch-specific-exceptions") is not None
        assert contract.get_rule("no-swallowed-exceptions") is not None
        # Result pattern
        assert contract.get_rule("result-pattern") is not None
        # Validation
        assert contract.get_rule("fail-fast-validation") is not None

    def test_api_design_contract(self, manager):
        """API design contract covers REST conventions."""
        contract = manager.contracts.get("operation.api-design.v1")

        assert contract is not None
        # Resource design
        assert contract.get_rule("resource-naming") is not None
        assert contract.get_rule("http-method-semantics") is not None
        assert contract.get_rule("status-code-usage") is not None
        # Request/response
        assert contract.get_rule("request-validation") is not None
        assert contract.get_rule("error-response-format") is not None
        # Versioning
        assert contract.get_rule("api-versioning") is not None

    def test_async_patterns_contract(self, manager):
        """Async patterns contract covers concurrency."""
        contract = manager.contracts.get("operation.async-patterns.v1")

        assert contract is not None
        # Async basics
        assert contract.get_rule("async-all-the-way") is not None
        assert contract.get_rule("no-fire-and-forget") is not None
        assert contract.get_rule("structured-concurrency") is not None
        # Cancellation and timeouts
        assert contract.get_rule("cancellation-support") is not None
        assert contract.get_rule("timeout-all-io") is not None
        # Concurrency control
        assert contract.get_rule("limit-concurrency") is not None

    def test_observability_contract(self, manager):
        """Observability contract covers logging, metrics, tracing."""
        contract = manager.contracts.get("operation.observability.v1")

        assert contract is not None
        # Logging
        assert contract.get_rule("structured-logging") is not None
        assert contract.get_rule("log-levels") is not None
        assert contract.get_rule("sensitive-data-logging") is not None
        # Metrics
        assert contract.get_rule("metrics-naming") is not None
        assert contract.get_rule("four-golden-signals") is not None
        assert contract.get_rule("histogram-over-average") is not None
        # Tracing
        assert contract.get_rule("trace-all-requests") is not None
        assert contract.get_rule("span-naming") is not None

    def test_all_contracts_have_rationales(self, manager):
        """All rules have rationales for human understanding."""
        for contract in manager.contracts.values():
            for rule in contract.rules:
                assert rule.rationale, f"Rule {rule.rule_id} missing rationale"

    def test_all_blocking_triggers_have_prompts(self, manager):
        """All blocking triggers have prompts for human."""
        for trigger in manager.get_blocking_triggers():
            assert trigger.prompt, f"Trigger {trigger.trigger_id} missing prompt"

    def test_all_contracts_have_quality_gates(self, manager):
        """All contracts should have quality gates defined."""
        for contract_id, contract in manager.contracts.items():
            assert len(contract.quality_gates) > 0, (
                f"Contract {contract_id} missing quality gates"
            )

    def test_all_contracts_have_escalation_triggers(self, manager):
        """All contracts should have escalation triggers defined."""
        for contract_id, contract in manager.contracts.items():
            assert len(contract.escalation_triggers) > 0, (
                f"Contract {contract_id} missing escalation triggers"
            )
