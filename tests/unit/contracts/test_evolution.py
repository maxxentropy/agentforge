# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-evolution-tests

"""Tests for contract evolution handler."""

import pytest

from agentforge.core.contracts.evolution import (
    AssumptionViolation,
    ContractChange,
    ContractEscalation,
    ContractEvolutionHandler,
    EvolutionViolationType,
)
from agentforge.core.contracts.draft import (
    ApprovedContracts,
    Assumption,
    StageContract,
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
            ),
            StageContract(
                stage_name="implement",
                input_requirements=["clarified_requirements"],
                output_requirements=["code_changes"],
            ),
        ],
        version="1.0",
    )


class TestAssumptionViolation:
    """Tests for AssumptionViolation."""

    def test_create_violation(self):
        """Create an assumption violation."""
        violation = AssumptionViolation(
            violation_id="AV-001",
            violation_type=EvolutionViolationType.ASSUMPTION_WRONG,
            actual_situation="JWT storage in localStorage, not cookies",
            discovered_at_stage="implement",
            impact="Security implications",
        )

        assert violation.violation_id == "AV-001"
        assert violation.violation_type == EvolutionViolationType.ASSUMPTION_WRONG

    def test_violation_to_dict(self):
        """Serialize violation to dictionary."""
        violation = AssumptionViolation(
            violation_id="AV-001",
            violation_type=EvolutionViolationType.SCOPE_CHANGE,
            actual_situation="Scope changed",
        )

        data = violation.to_dict()

        assert data["violation_id"] == "AV-001"
        assert data["violation_type"] == "scope_change"


class TestContractChange:
    """Tests for ContractChange."""

    def test_create_change(self):
        """Create a contract change."""
        change = ContractChange(
            change_id="CHG-001",
            change_type="add_rule",
            target="intake",
            description="Add validation for auth_type",
            reason="New constraint discovered",
        )

        assert change.change_id == "CHG-001"
        assert change.change_type == "add_rule"


class TestContractEscalation:
    """Tests for ContractEscalation."""

    def test_create_escalation(self, sample_contracts):
        """Create an escalation."""
        violation = AssumptionViolation(
            violation_id="AV-001",
            violation_type=EvolutionViolationType.ASSUMPTION_WRONG,
            actual_situation="Assumption was wrong",
        )

        escalation = ContractEscalation(
            escalation_id="ESC-001",
            violations=[violation],
            current_contracts=sample_contracts,
            severity="blocking",
        )

        assert escalation.escalation_id == "ESC-001"
        assert len(escalation.violations) == 1
        assert not escalation.resolved


class TestContractEvolutionHandler:
    """Tests for ContractEvolutionHandler."""

    @pytest.fixture
    def handler(self):
        """Create a handler."""
        return ContractEvolutionHandler()

    def test_detect_assumption_wrong(self, handler, sample_contracts):
        """Detect wrong assumption."""
        context = {
            "assumptions": [
                {
                    "id": "A-001",
                    "valid": False,
                    "actual": "JWT stored in localStorage",
                    "impact": "Security implications",
                }
            ]
        }

        violation = handler.detect_assumption_violation(
            "implement", context, sample_contracts
        )

        assert violation is not None
        assert violation.violation_type == EvolutionViolationType.ASSUMPTION_WRONG

    def test_detect_scope_change(self, handler, sample_contracts):
        """Detect scope change."""
        context = {
            "detected_scope": "bugfix",
            "expected_scope": "feature",
        }

        violation = handler.detect_assumption_violation(
            "intake", context, sample_contracts
        )

        assert violation is not None
        assert violation.violation_type == EvolutionViolationType.SCOPE_CHANGE

    def test_detect_incomplete_contract(self, handler, sample_contracts):
        """Detect incomplete contract."""
        context = {
            "missing_outputs": ["new_required_field"],
            "indicates_incomplete_contract": True,
        }

        violation = handler.detect_assumption_violation(
            "implement", context, sample_contracts
        )

        assert violation is not None
        assert violation.violation_type == EvolutionViolationType.CONTRACT_INCOMPLETE

    def test_no_violation_detected(self, handler, sample_contracts):
        """No violation when context is normal."""
        context = {
            "confidence": 0.9,
        }

        violation = handler.detect_assumption_violation(
            "intake", context, sample_contracts
        )

        assert violation is None

    def test_escalate_for_redraft(self, handler, sample_contracts):
        """Create escalation for redraft."""
        violation = AssumptionViolation(
            violation_id="AV-001",
            violation_type=EvolutionViolationType.ASSUMPTION_WRONG,
            actual_situation="JWT in localStorage",
            discovered_at_stage="implement",
        )

        escalation = handler.escalate_for_redraft(violation, sample_contracts)

        assert escalation is not None
        assert len(escalation.violations) == 1
        assert len(escalation.proposed_changes) >= 1
        assert "CONTRACT EVOLUTION REQUIRED" in escalation.prompt

    def test_escalate_generates_prompt(self, handler, sample_contracts):
        """Escalation prompt includes key information."""
        violation = AssumptionViolation(
            violation_id="AV-001",
            violation_type=EvolutionViolationType.SCOPE_CHANGE,
            actual_situation="Scope changed to bugfix",
            discovered_at_stage="intake",
            impact="Contract may not be appropriate",
        )

        escalation = handler.escalate_for_redraft(violation, sample_contracts)

        assert "scope_change" in escalation.prompt.lower()
        assert "Options:" in escalation.prompt

    def test_apply_evolution_modify_stage(self, handler, sample_contracts):
        """Apply evolution that modifies a stage."""
        changes = [
            ContractChange(
                change_id="CHG-001",
                change_type="modify_stage",
                target="intake",
                description="Add new output",
                details={"add_outputs": ["new_field"]},
            )
        ]

        evolved = handler.apply_evolution(sample_contracts, changes)

        assert evolved.version == "1.1"
        assert evolved.contract_set_id != sample_contracts.contract_set_id
        intake = evolved.get_stage_contract("intake")
        assert "new_field" in intake.output_requirements

    def test_apply_evolution_add_trigger(self, handler, sample_contracts):
        """Apply evolution that adds a trigger."""
        changes = [
            ContractChange(
                change_id="CHG-001",
                change_type="add_trigger",
                target="global",
                description="Check for security concern",
                details={"condition": "Security concern detected"},
                reason="Learned from execution",
            )
        ]

        evolved = handler.apply_evolution(sample_contracts, changes)

        assert len(evolved.escalation_triggers) == 1
        assert "T-EVOLVED" in evolved.escalation_triggers[0].trigger_id

    def test_evolution_preserves_data(self, handler, sample_contracts):
        """Evolution preserves original data."""
        changes = []

        evolved = handler.apply_evolution(sample_contracts, changes)

        assert evolved.draft_id == sample_contracts.draft_id
        assert evolved.request_id == sample_contracts.request_id
        assert len(evolved.stage_contracts) == len(sample_contracts.stage_contracts)


class TestEvolutionViolationTypes:
    """Tests for violation types."""

    def test_assumption_wrong(self):
        """ASSUMPTION_WRONG type."""
        vtype = EvolutionViolationType.ASSUMPTION_WRONG
        assert vtype.value == "assumption_wrong"

    def test_scope_change(self):
        """SCOPE_CHANGE type."""
        vtype = EvolutionViolationType.SCOPE_CHANGE
        assert vtype.value == "scope_change"

    def test_new_constraint(self):
        """NEW_CONSTRAINT type."""
        vtype = EvolutionViolationType.NEW_CONSTRAINT
        assert vtype.value == "new_constraint"

    def test_contract_incomplete(self):
        """CONTRACT_INCOMPLETE type."""
        vtype = EvolutionViolationType.CONTRACT_INCOMPLETE
        assert vtype.value == "contract_incomplete"
