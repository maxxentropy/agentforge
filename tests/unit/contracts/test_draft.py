# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-draft-tests

"""Tests for contract draft data structures."""

import pytest

from agentforge.core.contracts.draft import (
    Assumption,
    ApprovedContracts,
    ContractDraft,
    EscalationTrigger,
    OpenQuestion,
    QualityGate,
    Revision,
    StageContract,
    ValidationRule,
)


class TestValidationRule:
    """Tests for ValidationRule."""

    def test_validation_rule_creation(self):
        """Create a validation rule."""
        rule = ValidationRule(
            rule_id="R-001",
            description="Auth method must be valid",
            check_type="enum_constraint",
            field_path="output.auth_method",
            constraint={"enum": ["jwt", "session", "oauth"]},
            severity="error",
            rationale="Only these auth methods are supported",
        )

        assert rule.rule_id == "R-001"
        assert rule.check_type == "enum_constraint"
        assert rule.severity == "error"

    def test_validation_rule_to_dict(self):
        """Serialize validation rule."""
        rule = ValidationRule(
            rule_id="R-001",
            description="Test rule",
            check_type="required_field",
            field_path="output.request_id",
            constraint={"required": True},
        )

        data = rule.to_dict()

        assert data["rule_id"] == "R-001"
        assert data["check_type"] == "required_field"

    def test_validation_rule_from_dict(self):
        """Deserialize validation rule."""
        data = {
            "rule_id": "R-001",
            "description": "Test rule",
            "check_type": "type_check",
            "field_path": "output.count",
            "constraint": {"type": "integer"},
            "severity": "warning",
        }

        rule = ValidationRule.from_dict(data)

        assert rule.rule_id == "R-001"
        assert rule.severity == "warning"


class TestEscalationTrigger:
    """Tests for EscalationTrigger."""

    def test_trigger_creation(self):
        """Create an escalation trigger."""
        trigger = EscalationTrigger(
            trigger_id="T-001",
            condition="Confidence below 0.7",
            stage="clarify",
            severity="blocking",
            prompt="Clarification needed. Please review.",
            rationale="Low confidence requires human review",
        )

        assert trigger.trigger_id == "T-001"
        assert trigger.stage == "clarify"
        assert trigger.severity == "blocking"

    def test_trigger_to_dict(self):
        """Serialize trigger."""
        trigger = EscalationTrigger(
            trigger_id="T-001",
            condition="Test condition",
        )

        data = trigger.to_dict()

        assert data["trigger_id"] == "T-001"
        assert data["condition"] == "Test condition"

    def test_trigger_from_dict(self):
        """Deserialize trigger."""
        data = {
            "trigger_id": "T-001",
            "condition": "Security concern",
            "severity": "advisory",
        }

        trigger = EscalationTrigger.from_dict(data)

        assert trigger.trigger_id == "T-001"
        assert trigger.severity == "advisory"


class TestQualityGate:
    """Tests for QualityGate."""

    def test_gate_creation(self):
        """Create a quality gate."""
        gate = QualityGate(
            gate_id="G-001",
            stage="spec",
            checks=["All components defined", "Test cases present"],
            failure_action="escalate",
        )

        assert gate.gate_id == "G-001"
        assert len(gate.checks) == 2

    def test_gate_to_dict(self):
        """Serialize gate."""
        gate = QualityGate(
            gate_id="G-001",
            stage="analyze",
            checks=["Impact assessed"],
        )

        data = gate.to_dict()

        assert data["stage"] == "analyze"


class TestStageContract:
    """Tests for StageContract."""

    def test_stage_contract_creation(self):
        """Create a stage contract."""
        contract = StageContract(
            stage_name="intake",
            input_schema={},
            input_requirements=[],
            output_schema={
                "type": "object",
                "required": ["request_id", "detected_scope"],
            },
            output_requirements=["request_id", "detected_scope"],
            validation_rules=[
                ValidationRule(
                    rule_id="R-001",
                    description="Scope must be valid",
                    check_type="enum_constraint",
                    field_path="output.detected_scope",
                    constraint={"enum": ["feature", "bugfix", "refactor"]},
                ),
            ],
            rationale="Intake stage captures initial request analysis",
        )

        assert contract.stage_name == "intake"
        assert len(contract.validation_rules) == 1
        assert "request_id" in contract.output_requirements

    def test_stage_contract_to_dict(self):
        """Serialize stage contract."""
        contract = StageContract(
            stage_name="clarify",
            output_requirements=["clarified_requirements"],
        )

        data = contract.to_dict()

        assert data["stage_name"] == "clarify"
        assert "clarified_requirements" in data["output_requirements"]

    def test_stage_contract_from_dict(self):
        """Deserialize stage contract."""
        data = {
            "stage_name": "analyze",
            "input_requirements": ["request_id"],
            "output_requirements": ["analysis", "components"],
            "validation_rules": [
                {
                    "rule_id": "R-001",
                    "description": "Test",
                    "check_type": "required_field",
                    "field_path": "output.analysis",
                    "constraint": {},
                }
            ],
        }

        contract = StageContract.from_dict(data)

        assert contract.stage_name == "analyze"
        assert len(contract.validation_rules) == 1


class TestContractDraft:
    """Tests for ContractDraft."""

    def test_draft_creation(self):
        """Create a contract draft."""
        draft = ContractDraft(
            draft_id="DRAFT-20240103-120000",
            request_summary="Add user authentication with JWT",
            detected_scope="feature",
            stage_contracts=[
                StageContract(
                    stage_name="intake",
                    output_requirements=["request_id", "auth_type"],
                ),
                StageContract(
                    stage_name="clarify",
                    input_requirements=["request_id"],
                    output_requirements=["clarified_requirements"],
                ),
            ],
            confidence=0.85,
        )

        assert draft.draft_id == "DRAFT-20240103-120000"
        assert len(draft.stage_contracts) == 2
        assert draft.confidence == 0.85

    def test_draft_to_yaml(self):
        """Serialize draft to YAML."""
        draft = ContractDraft(
            draft_id="DRAFT-001",
            request_summary="Test request",
            detected_scope="bugfix",
        )

        yaml_str = draft.to_yaml()

        assert "draft_id: DRAFT-001" in yaml_str
        assert "detected_scope: bugfix" in yaml_str

    def test_draft_from_yaml(self):
        """Deserialize draft from YAML."""
        yaml_str = """
draft_id: DRAFT-001
request_summary: Test request
detected_scope: feature
stage_contracts:
  - stage_name: intake
    output_requirements:
      - request_id
confidence: 0.9
open_questions: []
assumptions: []
revision_history: []
created_at: "2024-01-03T12:00:00Z"
updated_at: "2024-01-03T12:00:00Z"
escalation_triggers: []
quality_gates: []
"""

        draft = ContractDraft.from_yaml(yaml_str)

        assert draft.draft_id == "DRAFT-001"
        assert draft.confidence == 0.9
        assert len(draft.stage_contracts) == 1

    def test_draft_get_stage_contract(self):
        """Get stage contract by name."""
        draft = ContractDraft(
            draft_id="DRAFT-001",
            request_summary="Test",
            detected_scope="feature",
            stage_contracts=[
                StageContract(stage_name="intake"),
                StageContract(stage_name="clarify"),
            ],
        )

        intake = draft.get_stage_contract("intake")
        clarify = draft.get_stage_contract("clarify")
        nonexistent = draft.get_stage_contract("nonexistent")

        assert intake is not None
        assert intake.stage_name == "intake"
        assert clarify is not None
        assert nonexistent is None

    def test_draft_add_revision(self):
        """Add revision to draft."""
        draft = ContractDraft(
            draft_id="DRAFT-001",
            request_summary="Test",
            detected_scope="feature",
        )

        draft.add_revision(
            changes=["Added auth_method field to intake output"],
            reason="User requested explicit auth method tracking",
        )

        assert len(draft.revision_history) == 1
        assert draft.revision_history[0].revision_id == "REV-001"
        assert "auth_method" in draft.revision_history[0].changes[0]

    def test_draft_with_questions_and_assumptions(self):
        """Draft with open questions and assumptions."""
        draft = ContractDraft(
            draft_id="DRAFT-001",
            request_summary="Add authentication",
            detected_scope="feature",
            open_questions=[
                OpenQuestion(
                    question_id="Q-001",
                    question="Should we support OAuth?",
                    priority="high",
                ),
            ],
            assumptions=[
                Assumption(
                    assumption_id="A-001",
                    statement="JWT tokens will be stored in localStorage",
                    confidence=0.7,
                    impact_if_wrong="Security implications if httpOnly cookies preferred",
                ),
            ],
        )

        assert len(draft.open_questions) == 1
        assert len(draft.assumptions) == 1
        assert draft.assumptions[0].confidence == 0.7


class TestApprovedContracts:
    """Tests for ApprovedContracts."""

    def test_approved_creation(self):
        """Create approved contracts."""
        approved = ApprovedContracts(
            contract_set_id="CONTRACT-20240103-120000",
            draft_id="DRAFT-001",
            request_id="REQ-001",
            stage_contracts=[
                StageContract(stage_name="intake"),
            ],
        )

        assert approved.contract_set_id == "CONTRACT-20240103-120000"
        assert approved.approved_by == "human"
        assert approved.version == "1.0"

    def test_approved_from_draft(self):
        """Create approved from draft."""
        draft = ContractDraft(
            draft_id="DRAFT-001",
            request_summary="Test",
            detected_scope="feature",
            stage_contracts=[
                StageContract(stage_name="intake"),
                StageContract(stage_name="clarify"),
            ],
            escalation_triggers=[
                EscalationTrigger(
                    trigger_id="T-001",
                    condition="Confidence below threshold",
                ),
            ],
        )

        approved = ApprovedContracts.from_draft(
            draft,
            contract_set_id="CONTRACT-001",
            request_id="REQ-001",
        )

        assert approved.draft_id == "DRAFT-001"
        assert len(approved.stage_contracts) == 2
        assert len(approved.escalation_triggers) == 1

    def test_approved_to_yaml(self):
        """Serialize approved contracts to YAML."""
        approved = ApprovedContracts(
            contract_set_id="CONTRACT-001",
            draft_id="DRAFT-001",
            request_id="REQ-001",
        )

        yaml_str = approved.to_yaml()

        assert "contract_set_id: CONTRACT-001" in yaml_str

    def test_approved_from_yaml(self):
        """Deserialize approved contracts from YAML."""
        yaml_str = """
contract_set_id: CONTRACT-001
draft_id: DRAFT-001
request_id: REQ-001
stage_contracts:
  - stage_name: intake
    input_schema: {}
    input_requirements: []
    output_schema: {}
    output_requirements:
      - request_id
    validation_rules: []
    escalation_conditions: []
    rationale: ""
escalation_triggers: []
quality_gates: []
approved_at: "2024-01-03T12:00:00Z"
approved_by: human
version: "1.0"
"""

        approved = ApprovedContracts.from_yaml(yaml_str)

        assert approved.contract_set_id == "CONTRACT-001"
        assert len(approved.stage_contracts) == 1

    def test_approved_get_stage_contract(self):
        """Get stage contract from approved."""
        approved = ApprovedContracts(
            contract_set_id="CONTRACT-001",
            draft_id="DRAFT-001",
            request_id="REQ-001",
            stage_contracts=[
                StageContract(stage_name="intake"),
                StageContract(stage_name="spec"),
            ],
        )

        intake = approved.get_stage_contract("intake")
        spec = approved.get_stage_contract("spec")

        assert intake is not None
        assert spec is not None
        assert intake.stage_name == "intake"
