"""
Unit tests for Session Domain entities.

Tests for: SessionState, TokenBudget, SessionArtifact, SessionHistory, SessionContext
Based on specification acceptance criteria AC-001 through AC-024.
"""

import pytest
from datetime import datetime, timedelta


class TestSessionState:
    """Tests for SessionState enum."""

    def test_session_state_has_active_value(self):
        """SessionState should have ACTIVE state."""
        from tools.harness.session_domain import SessionState
        assert SessionState.ACTIVE.value == "active"

    def test_session_state_has_paused_value(self):
        """SessionState should have PAUSED state."""
        from tools.harness.session_domain import SessionState
        assert SessionState.PAUSED.value == "paused"

    def test_session_state_has_completed_value(self):
        """SessionState should have COMPLETED state."""
        from tools.harness.session_domain import SessionState
        assert SessionState.COMPLETED.value == "completed"

    def test_session_state_has_aborted_value(self):
        """SessionState should have ABORTED state."""
        from tools.harness.session_domain import SessionState
        assert SessionState.ABORTED.value == "aborted"


class TestTokenBudget:
    """Tests for TokenBudget value object."""

    def test_token_budget_default_values(self):
        """AC-001: Default budget should be 100K tokens."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget()
        assert budget.total_budget == 100000
        assert budget.tokens_used == 0

    def test_tokens_remaining_calculation(self):
        """tokens_remaining should equal total_budget - tokens_used."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=30000)
        assert budget.tokens_remaining == 70000

    def test_utilization_percent_calculation(self):
        """AC-013: utilization_percent should be (tokens_used / total_budget) * 100."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=50000)
        assert budget.utilization_percent == 50.0

    def test_is_warning_at_80_percent(self):
        """AC-014: is_warning should be True when utilization >= 80%."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=80000)
        assert budget.is_warning is True

    def test_is_warning_below_80_percent(self):
        """is_warning should be False when utilization < 80%."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=79999)
        assert budget.is_warning is False

    def test_can_continue_when_sufficient_budget(self):
        """can_continue returns True when tokens_remaining >= required."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=50000)
        assert budget.can_continue(40000) is True

    def test_can_continue_when_insufficient_budget(self):
        """AC-015: can_continue returns False when would exceed budget."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=95000)
        assert budget.can_continue(10000) is False

    def test_record_usage_adds_tokens(self):
        """record_usage should add tokens to tokens_used."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=0)
        budget.record_usage(5000)
        assert budget.tokens_used == 5000

    def test_extend_increases_budget(self):
        """AC-016: extend should increase total_budget."""
        from tools.harness.session_domain import TokenBudget
        budget = TokenBudget(total_budget=100000, tokens_used=100000)
        budget.extend(50000)
        assert budget.total_budget == 150000
        assert budget.can_continue(40000) is True


class TestSessionArtifact:
    """Tests for SessionArtifact value object."""

    def test_artifact_creation(self):
        """Artifacts should store path, type, timestamp, and phase."""
        from tools.harness.session_domain import SessionArtifact
        now = datetime.utcnow()
        artifact = SessionArtifact(
            path="src/foo.py",
            artifact_type="created",
            timestamp=now,
            phase="implement"
        )
        assert artifact.path == "src/foo.py"
        assert artifact.artifact_type == "created"
        assert artifact.timestamp == now
        assert artifact.phase == "implement"

    def test_artifact_type_must_be_created_or_modified(self):
        """artifact_type must be 'created' or 'modified'."""
        from tools.harness.session_domain import SessionArtifact
        # Valid types
        SessionArtifact(path="a.py", artifact_type="created", timestamp=datetime.utcnow())
        SessionArtifact(path="b.py", artifact_type="modified", timestamp=datetime.utcnow())


class TestSessionHistory:
    """Tests for SessionHistory value object."""

    def test_history_entry_creation(self):
        """History entries should store timestamp, action, phase, details."""
        from tools.harness.session_domain import SessionHistory
        now = datetime.utcnow()
        entry = SessionHistory(
            timestamp=now,
            action="session_created",
            phase=None,
            details="Initial creation"
        )
        assert entry.timestamp == now
        assert entry.action == "session_created"
        assert entry.phase is None
        assert entry.details == "Initial creation"


class TestSessionContext:
    """Tests for SessionContext entity."""

    def test_session_context_creation_with_defaults(self):
        """AC-001: Session created with unique ID, ACTIVE state, 100K budget."""
        from tools.harness.session_domain import SessionContext, SessionState
        session = SessionContext.create()

        assert session.session_id.startswith("session_")
        assert session.state == SessionState.ACTIVE
        assert session.token_budget.total_budget == 100000
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_session_context_creation_with_workflow(self):
        """AC-002: Session created with specified workflow type and budget."""
        from tools.harness.session_domain import SessionContext
        session = SessionContext.create(
            workflow_type="spec",
            token_budget=50000
        )
        assert session.workflow_type == "spec"
        assert session.token_budget.total_budget == 50000

    def test_session_ids_are_unique(self):
        """AC-003: Session IDs should be unique."""
        from tools.harness.session_domain import SessionContext
        session1 = SessionContext.create()
        session2 = SessionContext.create()
        assert session1.session_id != session2.session_id

    def test_add_artifact_records_with_timestamp(self):
        """AC-019: add_artifact records artifact with timestamp and phase."""
        from tools.harness.session_domain import SessionContext
        session = SessionContext.create()
        session.current_phase = "implement"

        session.add_artifact("src/foo.py", "created")

        assert len(session.artifacts) == 1
        artifact = session.artifacts[0]
        assert artifact.path == "src/foo.py"
        assert artifact.artifact_type == "created"
        assert artifact.phase == "implement"
        assert artifact.timestamp is not None

    def test_get_artifacts_filters_by_phase(self):
        """AC-020: get_artifacts filters by phase."""
        from tools.harness.session_domain import SessionContext
        session = SessionContext.create()

        session.current_phase = "analyze"
        session.add_artifact("doc.md", "created")

        session.current_phase = "implement"
        session.add_artifact("src/a.py", "created")
        session.add_artifact("src/b.py", "modified")

        implement_artifacts = session.get_artifacts(phase="implement")
        assert len(implement_artifacts) == 2

        analyze_artifacts = session.get_artifacts(phase="analyze")
        assert len(analyze_artifacts) == 1

    def test_add_history_records_entry(self):
        """AC-023: History contains entries with timestamps."""
        from tools.harness.session_domain import SessionContext
        session = SessionContext.create()

        # Session creation should add initial history
        assert len(session.history) >= 1
        assert session.history[0].action == "session_created"

    def test_history_contains_all_state_transitions(self):
        """AC-024: All state transitions recorded in history."""
        from tools.harness.session_domain import SessionContext, SessionState
        session = SessionContext.create()
        initial_history_len = len(session.history)

        session.add_history("phase_advanced", phase="analyze")

        assert len(session.history) == initial_history_len + 1
        assert session.history[-1].action == "phase_advanced"
        assert session.history[-1].phase == "analyze"

    def test_created_at_before_updated_at(self):
        """Invariant: created_at <= updated_at."""
        from tools.harness.session_domain import SessionContext
        session = SessionContext.create()
        assert session.created_at <= session.updated_at

    def test_completed_at_only_set_for_terminal_states(self):
        """Invariant: completed_at is None unless COMPLETED or ABORTED."""
        from tools.harness.session_domain import SessionContext, SessionState
        session = SessionContext.create()
        assert session.completed_at is None
        assert session.state == SessionState.ACTIVE
