# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-reviewer-tests

"""Tests for contract reviewer."""

import pytest

from agentforge.core.contracts.reviewer import (
    ContractReviewer,
    OverallDecision,
    ReviewDecision,
    ReviewFeedback,
    ReviewSession,
    StageDecision,
)
from agentforge.core.contracts.draft import (
    Assumption,
    ContractDraft,
    EscalationTrigger,
    OpenQuestion,
    QualityGate,
    StageContract,
    ValidationRule,
)


@pytest.fixture
def sample_draft():
    """Create a sample draft for testing."""
    return ContractDraft(
        draft_id="DRAFT-20240103-120000",
        request_summary="Add user authentication with JWT",
        detected_scope="feature",
        confidence=0.85,
        stage_contracts=[
            StageContract(
                stage_name="intake",
                output_requirements=["request_id", "auth_type"],
                validation_rules=[
                    ValidationRule(
                        rule_id="R-001",
                        description="Auth type must be valid",
                        check_type="enum_constraint",
                        field_path="output.auth_type",
                        constraint={"enum": ["jwt", "session", "oauth"]},
                        severity="error",
                        rationale="Only these auth methods are supported",
                    )
                ],
            ),
            StageContract(
                stage_name="clarify",
                input_requirements=["request_id"],
                output_requirements=["clarified_requirements"],
            ),
            StageContract(
                stage_name="implement",
                input_requirements=["clarified_requirements"],
                output_requirements=["code_changes"],
            ),
        ],
        escalation_triggers=[
            EscalationTrigger(
                trigger_id="T-001",
                condition="Confidence below 0.7",
                severity="blocking",
            )
        ],
        quality_gates=[
            QualityGate(
                gate_id="G-001",
                stage="spec",
                checks=["All components defined"],
            )
        ],
        open_questions=[
            OpenQuestion(
                question_id="Q-001",
                question="Should we support refresh tokens?",
                priority="high",
                suggested_answers=["Yes", "No"],
            )
        ],
        assumptions=[
            Assumption(
                assumption_id="A-001",
                statement="JWT tokens stored in httpOnly cookies",
                confidence=0.7,
                impact_if_wrong="Security implications",
            )
        ],
    )


class TestStageDecision:
    """Tests for StageDecision."""

    def test_create_approval(self):
        """Create an approval decision."""
        decision = StageDecision(
            stage_name="intake",
            decision=ReviewDecision.APPROVE,
        )

        assert decision.stage_name == "intake"
        assert decision.decision == ReviewDecision.APPROVE

    def test_create_modification(self):
        """Create a modification decision."""
        decision = StageDecision(
            stage_name="clarify",
            decision=ReviewDecision.MODIFY,
            notes="Need to add password policy",
            modifications={"output_requirements": ["clarified_requirements", "password_policy"]},
        )

        assert decision.decision == ReviewDecision.MODIFY
        assert "password policy" in decision.notes


class TestReviewFeedback:
    """Tests for ReviewFeedback."""

    def test_empty_feedback(self):
        """Empty feedback has sensible defaults."""
        feedback = ReviewFeedback()

        assert len(feedback.stage_decisions) == 0
        assert feedback.overall_decision == OverallDecision.APPROVE

    def test_get_stage_decision(self):
        """Get decision for specific stage."""
        feedback = ReviewFeedback(
            stage_decisions=[
                StageDecision("intake", ReviewDecision.APPROVE),
                StageDecision("clarify", ReviewDecision.MODIFY),
            ]
        )

        intake = feedback.get_stage_decision("intake")
        clarify = feedback.get_stage_decision("clarify")
        missing = feedback.get_stage_decision("nonexistent")

        assert intake is not None
        assert intake.decision == ReviewDecision.APPROVE
        assert clarify.decision == ReviewDecision.MODIFY
        assert missing is None

    def test_all_stages_approved_true(self):
        """All stages approved returns True."""
        feedback = ReviewFeedback(
            stage_decisions=[
                StageDecision("intake", ReviewDecision.APPROVE),
                StageDecision("clarify", ReviewDecision.APPROVE),
            ]
        )

        assert feedback.all_stages_approved() is True

    def test_all_stages_approved_false(self):
        """Not all stages approved returns False."""
        feedback = ReviewFeedback(
            stage_decisions=[
                StageDecision("intake", ReviewDecision.APPROVE),
                StageDecision("clarify", ReviewDecision.MODIFY),
            ]
        )

        assert feedback.all_stages_approved() is False


class TestReviewSession:
    """Tests for ReviewSession."""

    def test_create_session(self, sample_draft):
        """Create a review session."""
        session = ReviewSession(
            session_id="REVIEW-001",
            draft=sample_draft,
        )

        assert session.session_id == "REVIEW-001"
        assert session.status == "pending"
        assert session.draft is sample_draft

    def test_approve_session(self, sample_draft):
        """Approve a session."""
        session = ReviewSession(
            session_id="REVIEW-001",
            draft=sample_draft,
        )

        approved = session.approve("REQ-001")

        assert session.status == "approved"
        assert approved is not None
        assert approved.draft_id == sample_draft.draft_id
        assert approved.request_id == "REQ-001"


class TestContractReviewer:
    """Tests for ContractReviewer."""

    @pytest.fixture
    def reviewer(self):
        """Create a reviewer."""
        return ContractReviewer()

    def test_create_session(self, reviewer, sample_draft):
        """Create a review session."""
        session = reviewer.create_session(sample_draft)

        assert session.session_id.startswith("REVIEW-")
        assert session.draft is sample_draft
        assert session.status == "pending"

    def test_format_for_display(self, reviewer, sample_draft):
        """Format draft for CLI display."""
        output = reviewer.format_for_display(sample_draft)

        assert "CONTRACT REVIEW" in output
        assert "Add user authentication" in output
        assert "STAGE: intake" in output
        assert "STAGE: clarify" in output
        assert "ESCALATION TRIGGERS" in output
        assert "OPEN QUESTIONS" in output
        assert "ASSUMPTIONS" in output

    def test_format_includes_confidence(self, reviewer, sample_draft):
        """Display includes confidence level."""
        output = reviewer.format_for_display(sample_draft)

        assert "85%" in output or "0.85" in output

    def test_format_includes_validation_rules(self, reviewer, sample_draft):
        """Display includes validation rules."""
        output = reviewer.format_for_display(sample_draft)

        assert "Validation" in output

    def test_format_stage_for_review(self, reviewer, sample_draft):
        """Format single stage for detailed review."""
        stage = sample_draft.stage_contracts[0]
        output = reviewer.format_stage_for_review(stage)

        assert "STAGE: intake" in output
        assert "Output Requirements" in output
        assert "request_id" in output
        assert "Validation Rules" in output
        assert "R-001" in output

    def test_apply_feedback_approve(self, reviewer, sample_draft):
        """Apply approval feedback."""
        session = reviewer.create_session(sample_draft)
        feedback = ReviewFeedback(
            stage_decisions=[
                StageDecision("intake", ReviewDecision.APPROVE),
                StageDecision("clarify", ReviewDecision.APPROVE),
                StageDecision("implement", ReviewDecision.APPROVE),
            ],
            overall_decision=OverallDecision.APPROVE,
        )

        updated = reviewer.apply_feedback(session, feedback)

        assert updated.status == "approved"
        assert updated.feedback is feedback

    def test_apply_feedback_refine(self, reviewer, sample_draft):
        """Apply refinement feedback."""
        session = reviewer.create_session(sample_draft)
        feedback = ReviewFeedback(
            overall_decision=OverallDecision.REFINE,
            questions_for_drafter=["Add more validation rules"],
        )

        updated = reviewer.apply_feedback(session, feedback)

        assert updated.status == "refined"

    def test_apply_feedback_partial_approval(self, reviewer, sample_draft):
        """Partial approval keeps status pending."""
        session = reviewer.create_session(sample_draft)
        feedback = ReviewFeedback(
            stage_decisions=[
                StageDecision("intake", ReviewDecision.APPROVE),
                StageDecision("clarify", ReviewDecision.MODIFY),
            ],
            overall_decision=OverallDecision.APPROVE,
        )

        updated = reviewer.apply_feedback(session, feedback)

        # Partial approval means still pending
        assert updated.status == "pending"

    def test_finalize_approved(self, reviewer, sample_draft):
        """Finalize an approved session."""
        session = reviewer.create_session(sample_draft)
        session.status = "approved"

        approved = reviewer.finalize(session, "REQ-001")

        assert approved is not None
        assert approved.request_id == "REQ-001"
        assert len(approved.stage_contracts) == len(sample_draft.stage_contracts)

    def test_finalize_not_approved(self, reviewer, sample_draft):
        """Finalize returns None for non-approved session."""
        session = reviewer.create_session(sample_draft)
        session.status = "pending"

        result = reviewer.finalize(session, "REQ-001")

        assert result is None

    def test_get_summary(self, reviewer, sample_draft):
        """Get session summary."""
        session = reviewer.create_session(sample_draft)
        session.feedback = ReviewFeedback(
            stage_decisions=[
                StageDecision("intake", ReviewDecision.APPROVE),
                StageDecision("clarify", ReviewDecision.APPROVE),
            ],
            answered_questions={"Q-001": "Yes, support refresh tokens"},
            validated_assumptions={"A-001": True},
        )

        summary = reviewer.get_summary(session)

        assert session.session_id in summary
        assert "Status: pending" in summary
        assert "Approved stages: 2/2" in summary


class TestReviewerWithEmptyDraft:
    """Tests with minimal/empty drafts."""

    @pytest.fixture
    def empty_draft(self):
        """Create an empty draft."""
        return ContractDraft(
            draft_id="DRAFT-EMPTY",
            request_summary="Simple request",
            detected_scope="bugfix",
        )

    def test_format_empty_draft(self, empty_draft):
        """Format draft with no stages."""
        reviewer = ContractReviewer()
        output = reviewer.format_for_display(empty_draft)

        assert "CONTRACT REVIEW" in output
        assert "Simple request" in output

    def test_session_with_empty_draft(self, empty_draft):
        """Create session with empty draft."""
        reviewer = ContractReviewer()
        session = reviewer.create_session(empty_draft)

        assert session is not None
        assert len(session.draft.stage_contracts) == 0
