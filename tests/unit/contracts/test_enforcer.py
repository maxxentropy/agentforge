# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-enforcer-tests

"""Tests for contract enforcer."""

import pytest

from agentforge.core.contracts.enforcer import (
    ContractEnforcer,
    EscalationCheck,
    QualityGateResult,
    ValidationResult,
    Violation,
    ViolationSeverity,
    ViolationType,
)
from agentforge.core.contracts.draft import (
    ApprovedContracts,
    EscalationTrigger,
    QualityGate,
    StageContract,
    ValidationRule,
)


@pytest.fixture
def sample_contracts():
    """Create sample approved contracts."""
    return ApprovedContracts(
        contract_set_id="CONTRACT-TEST",
        draft_id="DRAFT-001",
        request_id="REQ-001",
        stage_contracts=[
            StageContract(
                stage_name="intake",
                output_requirements=["request_id", "auth_type"],
                output_schema={
                    "type": "object",
                    "required": ["request_id", "auth_type"],
                    "properties": {
                        "request_id": {"type": "string"},
                        "auth_type": {"type": "string", "enum": ["jwt", "session", "oauth"]},
                    },
                },
                validation_rules=[
                    ValidationRule(
                        rule_id="R-001",
                        description="Auth type must be valid",
                        check_type="enum_constraint",
                        field_path="output.auth_type",
                        constraint={"enum": ["jwt", "session", "oauth"]},
                        severity="error",
                        rationale="Only these auth methods are supported",
                    ),
                ],
            ),
            StageContract(
                stage_name="clarify",
                input_requirements=["request_id"],
                output_requirements=["clarified_requirements"],
            ),
        ],
        escalation_triggers=[
            EscalationTrigger(
                trigger_id="T-001",
                condition="Confidence below 0.7",
                severity="blocking",
            ),
        ],
        quality_gates=[
            QualityGate(
                gate_id="G-001",
                stage="spec",
                checks=["All components defined", "Security review completed"],
                failure_action="escalate",
            ),
        ],
    )


class TestViolation:
    """Tests for Violation."""

    def test_create_violation(self):
        """Create a violation."""
        violation = Violation(
            violation_id="V-001",
            violation_type=ViolationType.MISSING_REQUIRED,
            severity=ViolationSeverity.ERROR,
            message="Missing required field: auth_type",
            field_path="output.auth_type",
        )

        assert violation.violation_id == "V-001", "Expected violation.violation_id to equal 'V-001'"
        assert violation.severity == ViolationSeverity.ERROR, "Expected violation.severity to equal ViolationSeverity.ERROR"

    def test_violation_to_dict(self):
        """Serialize violation."""
        violation = Violation(
            violation_id="V-001",
            violation_type=ViolationType.ENUM_VIOLATION,
            severity=ViolationSeverity.ERROR,
            message="Invalid value",
            expected=["jwt", "session"],
            actual="invalid",
        )

        data = violation.to_dict()

        assert data["violation_type"] == "enum_violation", "Expected data['violation_type'] to equal 'enum_violation'"
        assert data["severity"] == "error", "Expected data['severity'] to equal 'error'"


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_empty_result_is_valid(self):
        """Empty result is valid."""
        result = ValidationResult(valid=True)

        assert result.valid, "Expected result.valid to be truthy"
        assert result.error_count == 0, "Expected result.error_count to equal 0"
        assert result.warning_count == 0, "Expected result.warning_count to equal 0"

    def test_add_error_violation(self):
        """Adding error makes result invalid."""
        result = ValidationResult(valid=True)
        result.add_violation(Violation(
            violation_id="V-001",
            violation_type=ViolationType.MISSING_REQUIRED,
            severity=ViolationSeverity.ERROR,
            message="Missing field",
        ))

        assert not result.valid, "Assertion failed"
        assert result.error_count == 1, "Expected result.error_count to equal 1"

    def test_add_warning_keeps_valid(self):
        """Adding warning keeps result valid."""
        result = ValidationResult(valid=True)
        result.add_violation(Violation(
            violation_id="V-001",
            violation_type=ViolationType.TYPE_MISMATCH,
            severity=ViolationSeverity.WARNING,
            message="Type mismatch",
        ))

        assert result.valid, "Expected result.valid to be truthy"
        assert result.warning_count == 1, "Expected result.warning_count to equal 1"

    def test_merge_results(self):
        """Merge multiple results."""
        result1 = ValidationResult(valid=True)
        result1.add_violation(Violation(
            "V-001", ViolationType.MISSING_REQUIRED, ViolationSeverity.ERROR, "Error 1"
        ))

        result2 = ValidationResult(valid=True)
        result2.add_violation(Violation(
            "V-002", ViolationType.TYPE_MISMATCH, ViolationSeverity.WARNING, "Warning 1"
        ))

        merged = result1.merge(result2)

        assert not merged.valid, "Assertion failed"
        assert merged.error_count == 1, "Expected merged.error_count to equal 1"
        assert merged.warning_count == 1, "Expected merged.warning_count to equal 1"


class TestContractEnforcer:
    """Tests for ContractEnforcer."""

    @pytest.fixture
    def enforcer(self, sample_contracts):
        """Create an enforcer."""
        return ContractEnforcer(sample_contracts)

    def test_create_enforcer(self, sample_contracts):
        """Create enforcer with contracts."""
        enforcer = ContractEnforcer(sample_contracts)

        assert enforcer.contracts is sample_contracts, "Expected enforcer.contracts is sample_contracts"

    def test_validate_input_passes(self, enforcer):
        """Validate passing input."""
        result = enforcer.validate_stage_input(
            "clarify",
            {"request_id": "REQ-001"},
        )

        assert result.valid, "Expected result.valid to be truthy"
        assert result.error_count == 0, "Expected result.error_count to equal 0"

    def test_validate_input_missing_required(self, enforcer):
        """Validate input with missing required field."""
        result = enforcer.validate_stage_input(
            "clarify",
            {},  # Missing request_id
        )

        assert not result.valid, "Assertion failed"
        assert result.error_count == 1, "Expected result.error_count to equal 1"
        assert "request_id" in result.violations[0].message, "Expected 'request_id' in result.violations[0].message"

    def test_validate_output_passes(self, enforcer):
        """Validate passing output."""
        result = enforcer.validate_stage_output(
            "intake",
            {"request_id": "REQ-001", "auth_type": "jwt"},
        )

        assert result.valid, "Expected result.valid to be truthy"
        assert result.error_count == 0, "Expected result.error_count to equal 0"

    def test_validate_output_missing_required(self, enforcer):
        """Validate output with missing required field."""
        result = enforcer.validate_stage_output(
            "intake",
            {"request_id": "REQ-001"},  # Missing auth_type
        )

        assert not result.valid, "Assertion failed"
        assert any("auth_type" in v.message for v in result.violations), "Expected any() to be truthy"

    def test_validate_output_enum_violation(self, enforcer):
        """Validate output with invalid enum value."""
        result = enforcer.validate_stage_output(
            "intake",
            {"request_id": "REQ-001", "auth_type": "invalid"},
        )

        assert not result.valid, "Assertion failed"
        assert any(v.violation_type == ViolationType.ENUM_VIOLATION for v in result.violations), "Expected any() to be truthy"

    def test_validate_output_type_mismatch(self, enforcer):
        """Validate output with type mismatch."""
        result = enforcer.validate_stage_output(
            "intake",
            {"request_id": 123, "auth_type": "jwt"},  # request_id should be string
        )

        assert not result.valid, "Assertion failed"
        assert any(v.violation_type == ViolationType.TYPE_MISMATCH for v in result.violations), "Expected any() to be truthy"

    def test_validate_unknown_stage(self, enforcer):
        """Validate unknown stage passes (no contract)."""
        result = enforcer.validate_stage_output(
            "unknown_stage",
            {"anything": "goes"},
        )

        assert result.valid, "Expected result.valid to be truthy"

    def test_check_escalation_trigger_not_met(self, enforcer):
        """Escalation trigger not met."""
        checks = enforcer.check_escalation_triggers(
            "intake",
            {"confidence": 0.9},  # Above 0.7 threshold
        )

        triggered = [c for c in checks if c.triggered]
        assert len(triggered) == 0, "Expected len(triggered) to equal 0"

    def test_check_escalation_trigger_met(self, enforcer):
        """Escalation trigger met."""
        checks = enforcer.check_escalation_triggers(
            "intake",
            {"confidence": 0.5},  # Below 0.7 threshold
        )

        triggered = [c for c in checks if c.triggered]
        assert len(triggered) == 1, "Expected len(triggered) to equal 1"
        assert triggered[0].trigger.trigger_id == "T-001", "Expected triggered[0].trigger.trigge... to equal 'T-001'"

    def test_check_quality_gate_pass(self, enforcer):
        """Quality gate passes."""
        result = enforcer.check_quality_gate(
            "G-001",
            {"components": ["A", "B"]},
            {"security_approved": True},
        )

        assert result.passed, "Expected result.passed to be truthy"
        assert len(result.failed_checks) == 0, "Expected len(result.failed_checks) to equal 0"

    def test_check_quality_gate_fail(self, enforcer):
        """Quality gate fails."""
        result = enforcer.check_quality_gate(
            "G-001",
            {"components": ["A", "B"]},
            {"security_approved": False},  # Security not approved
        )

        assert not result.passed, "Assertion failed"
        assert len(result.failed_checks) > 0, "Expected len(result.failed_checks) > 0"
        assert result.action == "escalate", "Expected result.action to equal 'escalate'"

    def test_check_quality_gate_not_found(self, enforcer):
        """Unknown gate passes by default."""
        result = enforcer.check_quality_gate(
            "G-UNKNOWN",
            {},
        )

        assert result.passed, "Expected result.passed to be truthy"

    def test_get_summary(self, enforcer):
        """Get summary of multiple results."""
        result1 = enforcer.validate_stage_output(
            "intake",
            {"request_id": "REQ", "auth_type": "jwt"},
        )
        result2 = enforcer.validate_stage_input(
            "clarify",
            {},  # Missing request_id
        )

        summary = enforcer.get_summary([result1, result2])

        assert not summary["valid"], "Assertion failed"
        assert summary["total_errors"] >= 1, "Expected summary['total_errors'] >= 1"
        assert summary["stages_checked"] == 2, "Expected summary['stages_checked'] to equal 2"


class TestEnforcerWithEmptyContracts:
    """Tests with minimal contracts."""

    def test_empty_stage_contracts(self):
        """Enforcer handles empty stage contracts."""
        contracts = ApprovedContracts(
            contract_set_id="CONTRACT-EMPTY",
            draft_id="DRAFT",
            request_id="REQ",
        )
        enforcer = ContractEnforcer(contracts)

        result = enforcer.validate_stage_output("any", {"data": "value"})

        assert result.valid, "Expected result.valid to be truthy"
