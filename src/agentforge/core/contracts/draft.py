# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-draft
# @test_path: tests/unit/contracts/test_draft.py

"""
Contract Draft Data Structures
==============================

Dataclasses for contract drafts and related structures.

A ContractDraft represents a proposed set of contracts awaiting human approval.
It contains:
- Stage-by-stage contracts with input/output schemas
- Validation rules for each stage
- Escalation triggers for human judgment points
- Quality gates between stages
- Open questions and assumptions for human review

These structures encode human judgment in machine-verifiable form,
enabling trusted autonomous execution.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import yaml


@dataclass
class ValidationRule:
    """A validation rule for contract enforcement.

    Rules define constraints that must be satisfied at stage boundaries.
    """

    rule_id: str
    description: str
    check_type: str  # required_field, type_check, enum_constraint, cross_field, semantic
    field_path: str  # e.g., "output.auth_method"
    constraint: dict[str, Any]  # The actual constraint definition
    severity: str = "error"  # error, warning
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "check_type": self.check_type,
            "field_path": self.field_path,
            "constraint": self.constraint,
            "severity": self.severity,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationRule":
        """Deserialize from dictionary."""
        return cls(
            rule_id=data.get("rule_id", ""),
            description=data.get("description", ""),
            check_type=data.get("check_type", ""),
            field_path=data.get("field_path", ""),
            constraint=data.get("constraint", {}),
            severity=data.get("severity", "error"),
            rationale=data.get("rationale", ""),
        )


@dataclass
class EscalationTrigger:
    """Condition that should trigger human escalation.

    Triggers define when the agent should pause and ask for human input.
    """

    trigger_id: str
    condition: str  # Human-readable condition description
    stage: str | None = None  # Specific stage or None for any
    severity: str = "blocking"  # blocking, advisory
    prompt: str = ""  # What to ask human
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "trigger_id": self.trigger_id,
            "condition": self.condition,
            "stage": self.stage,
            "severity": self.severity,
            "prompt": self.prompt,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationTrigger":
        """Deserialize from dictionary."""
        return cls(
            trigger_id=data.get("trigger_id", ""),
            condition=data.get("condition", ""),
            stage=data.get("stage"),
            severity=data.get("severity", "blocking"),
            prompt=data.get("prompt", ""),
            rationale=data.get("rationale", ""),
        )


@dataclass
class QualityGate:
    """Quality check before proceeding to next stage.

    Gates define checkpoints where quality must be verified.
    """

    gate_id: str
    stage: str  # After which stage this gate applies
    checks: list[str] = field(default_factory=list)  # What to verify
    failure_action: str = "escalate"  # escalate, retry, abort

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "gate_id": self.gate_id,
            "stage": self.stage,
            "checks": self.checks,
            "failure_action": self.failure_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityGate":
        """Deserialize from dictionary."""
        return cls(
            gate_id=data.get("gate_id", ""),
            stage=data.get("stage", ""),
            checks=data.get("checks", []),
            failure_action=data.get("failure_action", "escalate"),
        )


@dataclass
class StageContract:
    """Contract for a single pipeline stage.

    Defines input requirements, output schema, validation rules,
    and stage-specific escalation conditions.
    """

    stage_name: str

    # Input contract
    input_schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema
    input_requirements: list[str] = field(default_factory=list)  # Required artifact keys

    # Output contract
    output_schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema
    output_requirements: list[str] = field(default_factory=list)  # Required output keys

    # Validation rules
    validation_rules: list[ValidationRule] = field(default_factory=list)

    # Stage-specific escalation
    escalation_conditions: list[str] = field(default_factory=list)

    # Rationale for these constraints
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "stage_name": self.stage_name,
            "input_schema": self.input_schema,
            "input_requirements": self.input_requirements,
            "output_schema": self.output_schema,
            "output_requirements": self.output_requirements,
            "validation_rules": [r.to_dict() for r in self.validation_rules],
            "escalation_conditions": self.escalation_conditions,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageContract":
        """Deserialize from dictionary."""
        return cls(
            stage_name=data.get("stage_name", ""),
            input_schema=data.get("input_schema", {}),
            input_requirements=data.get("input_requirements", []),
            output_schema=data.get("output_schema", {}),
            output_requirements=data.get("output_requirements", []),
            validation_rules=[
                ValidationRule.from_dict(r)
                for r in data.get("validation_rules", [])
            ],
            escalation_conditions=data.get("escalation_conditions", []),
            rationale=data.get("rationale", ""),
        )


@dataclass
class OpenQuestion:
    """A question that needs clarification from the human."""

    question_id: str
    question: str
    context: str = ""
    priority: str = "medium"  # low, medium, high
    suggested_answers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "question_id": self.question_id,
            "question": self.question,
            "context": self.context,
            "priority": self.priority,
            "suggested_answers": self.suggested_answers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OpenQuestion":
        """Deserialize from dictionary."""
        return cls(
            question_id=data.get("question_id", ""),
            question=data.get("question", ""),
            context=data.get("context", ""),
            priority=data.get("priority", "medium"),
            suggested_answers=data.get("suggested_answers", []),
        )


@dataclass
class Assumption:
    """An assumption made during contract drafting."""

    assumption_id: str
    statement: str
    confidence: float = 0.5  # 0.0-1.0
    impact_if_wrong: str = ""
    alternative: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "assumption_id": self.assumption_id,
            "statement": self.statement,
            "confidence": self.confidence,
            "impact_if_wrong": self.impact_if_wrong,
            "alternative": self.alternative,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Assumption":
        """Deserialize from dictionary."""
        return cls(
            assumption_id=data.get("assumption_id", ""),
            statement=data.get("statement", ""),
            confidence=data.get("confidence", 0.5),
            impact_if_wrong=data.get("impact_if_wrong", ""),
            alternative=data.get("alternative", ""),
        )


@dataclass
class Revision:
    """A revision to the contract draft."""

    revision_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    changes: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "revision_id": self.revision_id,
            "timestamp": self.timestamp,
            "changes": self.changes,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Revision":
        """Deserialize from dictionary."""
        return cls(
            revision_id=data.get("revision_id", ""),
            timestamp=data.get("timestamp", ""),
            changes=data.get("changes", []),
            reason=data.get("reason", ""),
        )


@dataclass
class ContractDraft:
    """Draft contracts awaiting human approval.

    Contains all proposed contracts for a request, including:
    - Stage-by-stage contracts
    - Escalation triggers
    - Quality gates
    - Open questions and assumptions
    """

    draft_id: str
    request_summary: str
    detected_scope: str  # feature, bugfix, refactor, etc.

    # Stage-by-stage contracts
    stage_contracts: list[StageContract] = field(default_factory=list)

    # Cross-cutting concerns
    escalation_triggers: list[EscalationTrigger] = field(default_factory=list)
    quality_gates: list[QualityGate] = field(default_factory=list)

    # Meta information
    confidence: float = 0.5  # 0.0-1.0
    open_questions: list[OpenQuestion] = field(default_factory=list)
    assumptions: list[Assumption] = field(default_factory=list)

    # Revision tracking
    revision_history: list[Revision] = field(default_factory=list)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "draft_id": self.draft_id,
            "request_summary": self.request_summary,
            "detected_scope": self.detected_scope,
            "stage_contracts": [sc.to_dict() for sc in self.stage_contracts],
            "escalation_triggers": [et.to_dict() for et in self.escalation_triggers],
            "quality_gates": [qg.to_dict() for qg in self.quality_gates],
            "confidence": self.confidence,
            "open_questions": [oq.to_dict() for oq in self.open_questions],
            "assumptions": [a.to_dict() for a in self.assumptions],
            "revision_history": [r.to_dict() for r in self.revision_history],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContractDraft":
        """Deserialize from dictionary."""
        return cls(
            draft_id=data.get("draft_id", ""),
            request_summary=data.get("request_summary", ""),
            detected_scope=data.get("detected_scope", ""),
            stage_contracts=[
                StageContract.from_dict(sc)
                for sc in data.get("stage_contracts", [])
            ],
            escalation_triggers=[
                EscalationTrigger.from_dict(et)
                for et in data.get("escalation_triggers", [])
            ],
            quality_gates=[
                QualityGate.from_dict(qg)
                for qg in data.get("quality_gates", [])
            ],
            confidence=data.get("confidence", 0.5),
            open_questions=[
                OpenQuestion.from_dict(oq)
                for oq in data.get("open_questions", [])
            ],
            assumptions=[
                Assumption.from_dict(a)
                for a in data.get("assumptions", [])
            ],
            revision_history=[
                Revision.from_dict(r)
                for r in data.get("revision_history", [])
            ],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ContractDraft":
        """Deserialize from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    def get_stage_contract(self, stage_name: str) -> StageContract | None:
        """Get contract for a specific stage."""
        for sc in self.stage_contracts:
            if sc.stage_name == stage_name:
                return sc
        return None

    def add_revision(self, changes: list[str], reason: str) -> None:
        """Add a revision to the history."""
        revision_num = len(self.revision_history) + 1
        revision = Revision(
            revision_id=f"REV-{revision_num:03d}",
            changes=changes,
            reason=reason,
        )
        self.revision_history.append(revision)
        self.updated_at = datetime.now(UTC).isoformat()


@dataclass
class ApprovedContracts:
    """Approved contracts ready for execution.

    Created when a ContractDraft is approved by human review.
    """

    contract_set_id: str
    draft_id: str  # Original draft this was created from
    request_id: str  # Associated request

    # The approved contracts
    stage_contracts: list[StageContract] = field(default_factory=list)
    escalation_triggers: list[EscalationTrigger] = field(default_factory=list)
    quality_gates: list[QualityGate] = field(default_factory=list)

    # Approval metadata
    approved_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    approved_by: str = "human"
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "contract_set_id": self.contract_set_id,
            "draft_id": self.draft_id,
            "request_id": self.request_id,
            "stage_contracts": [sc.to_dict() for sc in self.stage_contracts],
            "escalation_triggers": [et.to_dict() for et in self.escalation_triggers],
            "quality_gates": [qg.to_dict() for qg in self.quality_gates],
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovedContracts":
        """Deserialize from dictionary."""
        return cls(
            contract_set_id=data.get("contract_set_id", ""),
            draft_id=data.get("draft_id", ""),
            request_id=data.get("request_id", ""),
            stage_contracts=[
                StageContract.from_dict(sc)
                for sc in data.get("stage_contracts", [])
            ],
            escalation_triggers=[
                EscalationTrigger.from_dict(et)
                for et in data.get("escalation_triggers", [])
            ],
            quality_gates=[
                QualityGate.from_dict(qg)
                for qg in data.get("quality_gates", [])
            ],
            approved_at=data.get("approved_at", ""),
            approved_by=data.get("approved_by", "human"),
            version=data.get("version", "1.0"),
        )

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ApprovedContracts":
        """Deserialize from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    def get_stage_contract(self, stage_name: str) -> StageContract | None:
        """Get contract for a specific stage."""
        for sc in self.stage_contracts:
            if sc.stage_name == stage_name:
                return sc
        return None

    @classmethod
    def from_draft(
        cls,
        draft: ContractDraft,
        contract_set_id: str,
        request_id: str,
    ) -> "ApprovedContracts":
        """Create ApprovedContracts from a draft."""
        return cls(
            contract_set_id=contract_set_id,
            draft_id=draft.draft_id,
            request_id=request_id,
            stage_contracts=draft.stage_contracts.copy(),
            escalation_triggers=draft.escalation_triggers.copy(),
            quality_gates=draft.quality_gates.copy(),
        )
