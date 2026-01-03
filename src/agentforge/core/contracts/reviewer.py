# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-reviewer
# @test_path: tests/unit/contracts/test_reviewer.py

"""
Contract Reviewer
=================

Manages human review of drafted contracts.

The reviewer presents drafted contracts for human approval and
handles the feedback loop. It supports three modes:
1. CLI prompts (primary, implemented here)
2. YAML file editing (future)
3. Web UI (future)

Key Concepts:
- ReviewSession tracks the state of a review
- ReviewFeedback captures human decisions
- ApprovedContracts are created from approved drafts
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .draft import (
    ApprovedContracts,
    ContractDraft,
    StageContract,
)
from .registry import generate_contract_set_id


class ReviewDecision(str, Enum):
    """Human decision on a draft or stage."""
    APPROVE = "approve"
    MODIFY = "modify"
    REJECT = "reject"
    ASK = "ask"  # Ask for clarification


class OverallDecision(str, Enum):
    """Overall decision on the draft."""
    APPROVE = "approve"
    REFINE = "refine"  # Ask LLM to revise
    REJECT = "reject"  # Reject entirely
    RESTART = "restart"  # Start over


@dataclass
class StageDecision:
    """Human decision on a specific stage contract."""
    stage_name: str
    decision: ReviewDecision
    notes: str = ""
    modifications: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewFeedback:
    """Human feedback on a contract draft."""

    stage_decisions: list[StageDecision] = field(default_factory=list)
    additional_constraints: list[str] = field(default_factory=list)
    questions_for_drafter: list[str] = field(default_factory=list)
    answered_questions: dict[str, str] = field(default_factory=dict)
    validated_assumptions: dict[str, bool] = field(default_factory=dict)
    overall_decision: OverallDecision = OverallDecision.APPROVE
    notes: str = ""

    def get_stage_decision(self, stage_name: str) -> StageDecision | None:
        """Get decision for a specific stage."""
        for sd in self.stage_decisions:
            if sd.stage_name == stage_name:
                return sd
        return None

    def all_stages_approved(self) -> bool:
        """Check if all stages are approved."""
        return all(sd.decision == ReviewDecision.APPROVE for sd in self.stage_decisions)


@dataclass
class ReviewSession:
    """Tracks the state of a contract review."""

    session_id: str
    draft: ContractDraft
    feedback: ReviewFeedback = field(default_factory=ReviewFeedback)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = "pending"  # pending, approved, rejected, refined

    def approve(self, request_id: str) -> ApprovedContracts:
        """Approve the draft and create ApprovedContracts."""
        self.status = "approved"
        return ApprovedContracts.from_draft(
            self.draft,
            contract_set_id=generate_contract_set_id(),
            request_id=request_id,
        )


class ContractReviewer:
    """Manages human review of drafted contracts.

    Provides methods for presenting drafts, collecting feedback,
    and finalizing approved contracts.
    """

    def create_session(self, draft: ContractDraft) -> ReviewSession:
        """Create a new review session for a draft.

        Args:
            draft: The contract draft to review

        Returns:
            ReviewSession for tracking the review
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        session_id = f"REVIEW-{timestamp}"
        return ReviewSession(session_id=session_id, draft=draft)

    def format_for_display(self, draft: ContractDraft) -> str:
        """Format a draft for CLI display.

        Args:
            draft: The draft to format

        Returns:
            Formatted string for CLI display
        """
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append(f"CONTRACT REVIEW: {draft.request_summary}")
        lines.append("=" * 70)
        lines.append("")

        # Metadata
        lines.append(f"Draft ID: {draft.draft_id}")
        lines.append(f"Scope: {draft.detected_scope}")
        lines.append(f"Confidence: {draft.confidence:.0%}")
        lines.append("")

        # Stage contracts
        for stage in draft.stage_contracts:
            lines.append(f"STAGE: {stage.stage_name}")
            lines.append(f"  Input: {', '.join(stage.input_requirements) or '(none)'}")
            lines.append(f"  Output: {', '.join(stage.output_requirements) or '(none)'}")

            if stage.validation_rules:
                lines.append(f"  Validation: {len(stage.validation_rules)} rule(s)")
                for rule in stage.validation_rules[:2]:  # Show first 2
                    lines.append(f"    - {rule.description}")

            if stage.escalation_conditions:
                lines.append(f"  Escalation: {len(stage.escalation_conditions)} condition(s)")

            lines.append("")

        # Escalation triggers
        if draft.escalation_triggers:
            lines.append("ESCALATION TRIGGERS:")
            for trigger in draft.escalation_triggers:
                lines.append(f"  [{trigger.severity}] {trigger.condition}")
            lines.append("")

        # Quality gates
        if draft.quality_gates:
            lines.append("QUALITY GATES:")
            for gate in draft.quality_gates:
                lines.append(f"  After {gate.stage}: {len(gate.checks)} check(s)")
            lines.append("")

        # Open questions
        if draft.open_questions:
            lines.append("OPEN QUESTIONS:")
            for q in draft.open_questions:
                lines.append(f"  [{q.priority}] {q.question}")
                if q.suggested_answers:
                    for ans in q.suggested_answers[:2]:
                        lines.append(f"    -> {ans}")
            lines.append("")

        # Assumptions
        if draft.assumptions:
            lines.append("ASSUMPTIONS:")
            for a in draft.assumptions:
                lines.append(f"  [{a.confidence:.0%}] {a.statement}")
                if a.impact_if_wrong:
                    lines.append(f"    Impact if wrong: {a.impact_if_wrong}")
            lines.append("")

        return "\n".join(lines)

    def format_stage_for_review(self, stage: StageContract) -> str:
        """Format a single stage for detailed review.

        Args:
            stage: The stage contract to format

        Returns:
            Formatted string for review
        """
        lines = []
        lines.append(f"STAGE: {stage.stage_name}")
        lines.append("-" * 40)

        lines.append("Input Requirements:")
        if stage.input_requirements:
            for req in stage.input_requirements:
                lines.append(f"  - {req}")
        else:
            lines.append("  (none - first stage)")

        lines.append("")
        lines.append("Output Requirements:")
        if stage.output_requirements:
            for req in stage.output_requirements:
                lines.append(f"  - {req}")
        else:
            lines.append("  (none specified)")

        if stage.output_schema:
            lines.append("")
            lines.append("Output Schema:")
            if "properties" in stage.output_schema:
                for prop, details in stage.output_schema["properties"].items():
                    type_str = details.get("type", "any")
                    lines.append(f"  - {prop}: {type_str}")

        if stage.validation_rules:
            lines.append("")
            lines.append("Validation Rules:")
            for rule in stage.validation_rules:
                lines.append(f"  [{rule.severity}] {rule.rule_id}: {rule.description}")
                if rule.rationale:
                    lines.append(f"    Rationale: {rule.rationale[:60]}...")

        if stage.escalation_conditions:
            lines.append("")
            lines.append("Escalation Conditions:")
            for cond in stage.escalation_conditions:
                lines.append(f"  - {cond}")

        if stage.rationale:
            lines.append("")
            lines.append(f"Rationale: {stage.rationale}")

        return "\n".join(lines)

    def apply_feedback(
        self,
        session: ReviewSession,
        feedback: ReviewFeedback,
    ) -> ReviewSession:
        """Apply human feedback to a review session.

        Args:
            session: The review session
            feedback: Human feedback to apply

        Returns:
            Updated review session
        """
        session.feedback = feedback

        if feedback.overall_decision == OverallDecision.APPROVE:
            if feedback.all_stages_approved():
                session.status = "approved"
            else:
                session.status = "pending"
        elif feedback.overall_decision == OverallDecision.REJECT:
            session.status = "rejected"
        else:
            session.status = "refined"

        return session

    def finalize(
        self,
        session: ReviewSession,
        request_id: str,
    ) -> ApprovedContracts | None:
        """Finalize an approved session into ApprovedContracts.

        Args:
            session: The review session
            request_id: ID to associate with the contracts

        Returns:
            ApprovedContracts if approved, None otherwise
        """
        if session.status != "approved":
            return None

        return session.approve(request_id)

    def get_summary(self, session: ReviewSession) -> str:
        """Get a summary of the review session state.

        Args:
            session: The review session

        Returns:
            Summary string
        """
        lines = [
            f"Review Session: {session.session_id}",
            f"Draft: {session.draft.draft_id}",
            f"Status: {session.status}",
            f"Stages: {len(session.draft.stage_contracts)}",
        ]

        if session.feedback.stage_decisions:
            approved = sum(
                1 for sd in session.feedback.stage_decisions
                if sd.decision == ReviewDecision.APPROVE
            )
            lines.append(f"Approved stages: {approved}/{len(session.feedback.stage_decisions)}")

        if session.feedback.answered_questions:
            lines.append(f"Questions answered: {len(session.feedback.answered_questions)}")

        if session.feedback.validated_assumptions:
            lines.append(f"Assumptions validated: {len(session.feedback.validated_assumptions)}")

        return "\n".join(lines)
