# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-escalation

"""Tests for escalation handling."""


import pytest

from agentforge.core.pipeline import (
    Escalation,
    EscalationHandler,
    EscalationStatus,
    EscalationType,
    generate_escalation_id,
)


class TestEscalationIdGeneration:
    """Tests for escalation ID generation."""

    def test_format(self):
        """Escalation ID has expected format."""
        esc_id = generate_escalation_id()
        assert esc_id.startswith("ESC-")
        assert len(esc_id) == 12  # ESC- + 8 hex chars

    def test_unique(self):
        """Each ID is unique."""
        ids = [generate_escalation_id() for _ in range(100)]
        assert len(ids) == len(set(ids))


class TestEscalation:
    """Tests for Escalation dataclass."""

    def test_creation(self):
        """Escalation can be created with required fields."""
        esc = Escalation(
            escalation_id="ESC-abc12345",
            pipeline_id="PL-20260101-xyz",
            stage_name="intake",
            type=EscalationType.APPROVAL_REQUIRED,
            message="Please approve",
        )

        assert esc.escalation_id == "ESC-abc12345"
        assert esc.pipeline_id == "PL-20260101-xyz"
        assert esc.type == EscalationType.APPROVAL_REQUIRED
        assert esc.status == EscalationStatus.PENDING
        assert esc.response is None

    def test_serialization(self):
        """Escalation serializes to/from dict."""
        esc = Escalation(
            escalation_id="ESC-abc12345",
            pipeline_id="PL-20260101-xyz",
            stage_name="intake",
            type=EscalationType.CLARIFICATION_NEEDED,
            message="Need more info",
            options=["Option A", "Option B"],
            context={"reason": "ambiguous"},
        )

        data = esc.to_dict()
        restored = Escalation.from_dict(data)

        assert restored.escalation_id == esc.escalation_id
        assert restored.type == esc.type
        assert restored.message == esc.message
        assert restored.options == esc.options
        assert restored.context == esc.context


class TestEscalationTypes:
    """Tests for escalation types."""

    def test_all_types_defined(self):
        """All expected escalation types exist."""
        assert EscalationType.APPROVAL_REQUIRED
        assert EscalationType.CLARIFICATION_NEEDED
        assert EscalationType.ERROR_RECOVERY
        assert EscalationType.CANNOT_PROCEED

    def test_all_statuses_defined(self):
        """All expected statuses exist."""
        assert EscalationStatus.PENDING
        assert EscalationStatus.RESOLVED
        assert EscalationStatus.REJECTED
        assert EscalationStatus.EXPIRED


class TestEscalationHandler:
    """Tests for EscalationHandler."""

    @pytest.fixture
    def handler(self, temp_project):
        return EscalationHandler(temp_project)

    @pytest.fixture
    def sample_escalation(self):
        return Escalation(
            escalation_id=generate_escalation_id(),
            pipeline_id="PL-20260101-xyz",
            stage_name="intake",
            type=EscalationType.APPROVAL_REQUIRED,
            message="Please approve this change",
        )

    def test_create_escalation(self, handler, sample_escalation):
        """create() persists escalation and returns ID."""
        esc_id = handler.create(sample_escalation)

        assert esc_id == sample_escalation.escalation_id

        # Should be retrievable
        loaded = handler.get(esc_id)
        assert loaded is not None
        assert loaded.message == sample_escalation.message

    def test_create_generates_id(self, handler):
        """create() generates ID if not provided."""
        esc = Escalation(
            escalation_id="",  # Empty ID
            pipeline_id="PL-20260101-xyz",
            stage_name="intake",
            type=EscalationType.APPROVAL_REQUIRED,
            message="Test",
        )

        esc_id = handler.create(esc)
        assert esc_id.startswith("ESC-")
        assert esc.escalation_id == esc_id

    def test_resolve_escalation(self, handler, sample_escalation):
        """resolve() updates status and response."""
        handler.create(sample_escalation)

        handler.resolve(sample_escalation.escalation_id, "Approved!")

        loaded = handler.get(sample_escalation.escalation_id)
        assert loaded.status == EscalationStatus.RESOLVED
        assert loaded.response == "Approved!"
        assert loaded.resolved_at is not None

    def test_resolve_nonexistent(self, handler):
        """resolve() raises error for unknown escalation."""
        with pytest.raises(ValueError) as exc_info:
            handler.resolve("ESC-nonexist", "response")

        assert "not found" in str(exc_info.value).lower()

    def test_resolve_already_resolved(self, handler, sample_escalation):
        """resolve() raises error for already resolved escalation."""
        handler.create(sample_escalation)
        handler.resolve(sample_escalation.escalation_id, "First response")

        with pytest.raises(ValueError) as exc_info:
            handler.resolve(sample_escalation.escalation_id, "Second response")

        assert "cannot resolve" in str(exc_info.value).lower()

    def test_reject_escalation(self, handler, sample_escalation):
        """reject() updates status to rejected."""
        handler.create(sample_escalation)

        handler.reject(sample_escalation.escalation_id, "Not acceptable")

        loaded = handler.get(sample_escalation.escalation_id)
        assert loaded.status == EscalationStatus.REJECTED
        assert loaded.response == "Not acceptable"

    def test_get_pending(self, handler, temp_project):
        """get_pending() returns only pending escalations."""
        # Create multiple escalations
        esc1 = Escalation(
            escalation_id=generate_escalation_id(),
            pipeline_id="PL-1",
            stage_name="intake",
            type=EscalationType.APPROVAL_REQUIRED,
            message="Pending 1",
        )
        esc2 = Escalation(
            escalation_id=generate_escalation_id(),
            pipeline_id="PL-2",
            stage_name="clarify",
            type=EscalationType.CLARIFICATION_NEEDED,
            message="Pending 2",
        )
        esc3 = Escalation(
            escalation_id=generate_escalation_id(),
            pipeline_id="PL-1",
            stage_name="analyze",
            type=EscalationType.APPROVAL_REQUIRED,
            message="Will resolve",
        )

        handler.create(esc1)
        handler.create(esc2)
        handler.create(esc3)
        handler.resolve(esc3.escalation_id, "Resolved")

        # All pending
        pending = handler.get_pending()
        assert len(pending) == 2

        # Filter by pipeline
        pending_pl1 = handler.get_pending("PL-1")
        assert len(pending_pl1) == 1
        assert pending_pl1[0].pipeline_id == "PL-1"

    def test_get_for_pipeline(self, handler):
        """get_for_pipeline() returns all escalations for a pipeline."""
        for i in range(3):
            esc = Escalation(
                escalation_id=generate_escalation_id(),
                pipeline_id="PL-target",
                stage_name=f"stage{i}",
                type=EscalationType.APPROVAL_REQUIRED,
                message=f"Message {i}",
            )
            handler.create(esc)

        # Add one for different pipeline
        other = Escalation(
            escalation_id=generate_escalation_id(),
            pipeline_id="PL-other",
            stage_name="stage0",
            type=EscalationType.APPROVAL_REQUIRED,
            message="Other",
        )
        handler.create(other)

        escalations = handler.get_for_pipeline("PL-target")
        assert len(escalations) == 3
        assert all(e.pipeline_id == "PL-target" for e in escalations)

    def test_delete_escalation(self, handler, sample_escalation):
        """delete() removes escalation."""
        handler.create(sample_escalation)
        assert handler.get(sample_escalation.escalation_id) is not None

        result = handler.delete(sample_escalation.escalation_id)
        assert result is True
        assert handler.get(sample_escalation.escalation_id) is None

    def test_delete_nonexistent(self, handler):
        """delete() returns False for unknown escalation."""
        result = handler.delete("ESC-nonexist")
        assert result is False

    def test_get_nonexistent(self, handler):
        """get() returns None for unknown escalation."""
        loaded = handler.get("ESC-nonexist")
        assert loaded is None
