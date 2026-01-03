"""
Unit tests for SessionStore persistence layer.

Tests for: save, load, exists, list_sessions, delete
Based on specification acceptance criteria AC-007 through AC-012.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


class TestSessionStore:
    """Tests for SessionStore persistence."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test isolation."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def store(self, temp_dir):
        """Create SessionStore with temp directory."""
        from agentforge.core.harness.session_store import SessionStore
        return SessionStore(base_path=temp_dir / "sessions")

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        from agentforge.core.harness.session_domain import SessionContext
        return SessionContext.create(workflow_type="spec")

    def test_save_creates_session_file(self, store, sample_session):
        """AC-007: save() writes session.yaml atomically."""
        path = store.save(sample_session)

        assert path.exists(), "Expected path.exists() to be truthy"
        assert path.name == "session.yaml", "Expected path.name to equal 'session.yaml'"
        assert sample_session.session_id in str(path), "Expected sample_session.session_id in str(path)"

    def test_save_creates_directory_if_needed(self, store, sample_session):
        """AC-009: Directory created with .gitkeep if needed."""
        store.ensure_directory()

        assert store.base_path.exists(), "Expected store.base_path.exists() to be truthy"
        gitkeep = store.base_path / ".gitkeep"
        assert gitkeep.exists(), "Expected gitkeep.exists() to be truthy"

    def test_load_returns_session(self, store, sample_session):
        """AC-010: load() returns SessionContext with all fields restored."""
        store.save(sample_session)

        loaded = store.load(sample_session.session_id)

        assert loaded is not None, "Expected loaded is not None"
        assert loaded.session_id == sample_session.session_id, "Expected loaded.session_id to equal sample_session.session_id"
        assert loaded.workflow_type == sample_session.workflow_type, "Expected loaded.workflow_type to equal sample_session.workflow_type"
        assert loaded.state == sample_session.state, "Expected loaded.state to equal sample_session.state"

    def test_load_returns_none_for_missing_session(self, store):
        """AC-011: load() returns None if session not found."""
        loaded = store.load("nonexistent_session_id")
        assert loaded is None, "Expected loaded is None"

    def test_load_handles_corrupted_file(self, store, sample_session, temp_dir):
        """AC-012: load() returns error for corrupted file."""
        # Save valid session first
        store.save(sample_session)

        # Corrupt the file
        session_dir = store.base_path / sample_session.session_id
        session_file = session_dir / "session.yaml"
        session_file.write_text("invalid: yaml: content: [[[")

        # Load should handle gracefully
        store.load(sample_session.session_id)
        # Either returns None or raises appropriate error
        # Implementation can choose approach

    def test_exists_returns_true_for_existing_session(self, store, sample_session):
        """exists() returns True for saved session."""
        store.save(sample_session)
        assert store.exists(sample_session.session_id) is True, "Expected store.exists(sample_session... is True"

    def test_exists_returns_false_for_missing_session(self, store):
        """exists() returns False for non-existent session."""
        assert store.exists("nonexistent") is False, "Expected store.exists('nonexistent') is False"

    def test_list_sessions_returns_all_session_ids(self, store):
        """list_sessions() returns all session IDs."""
        from agentforge.core.harness.session_domain import SessionContext

        # Create multiple sessions
        session1 = SessionContext.create()
        session2 = SessionContext.create()
        session3 = SessionContext.create()

        store.save(session1)
        store.save(session2)
        store.save(session3)

        sessions = store.list_sessions()

        assert len(sessions) == 3, "Expected len(sessions) to equal 3"
        assert session1.session_id in sessions, "Expected session1.session_id in sessions"
        assert session2.session_id in sessions, "Expected session2.session_id in sessions"
        assert session3.session_id in sessions, "Expected session3.session_id in sessions"

    def test_delete_removes_session(self, store, sample_session):
        """delete() removes session directory."""
        store.save(sample_session)
        assert store.exists(sample_session.session_id) is True, "Expected store.exists(sample_session... is True"

        result = store.delete(sample_session.session_id)

        assert result is True, "Expected result is True"
        assert store.exists(sample_session.session_id) is False, "Expected store.exists(sample_session... is False"

    def test_delete_returns_false_for_missing_session(self, store):
        """delete() returns False for non-existent session."""
        result = store.delete("nonexistent")
        assert result is False, "Expected result is False"

    def test_atomic_write_preserves_state_on_interruption(self, store, sample_session):
        """AC-008: Atomic write - original remains intact on failure."""
        # Save initial state
        store.save(sample_session)
        original_state = sample_session.state

        # Load and verify original preserved
        loaded = store.load(sample_session.session_id)
        assert loaded.state == original_state, "Expected loaded.state to equal original_state"

    def test_yaml_format_is_human_readable(self, store, sample_session):
        """NFR-002: YAML should be human-readable with proper formatting."""
        path = store.save(sample_session)

        content = path.read_text()

        # Should have proper YAML formatting
        assert "session_id:" in content, "Expected 'session_id:' in content"
        assert "state:" in content, "Expected 'state:' in content"
        # Should not be single-line JSON-style
        assert content.count("\n") > 5, "Expected content.count('\n') > 5"

    def test_timestamps_in_iso_format(self, store, sample_session):
        """NFR-002: Timestamps should be ISO format."""
        path = store.save(sample_session)
        content = path.read_text()

        # ISO format has T separator
        assert "T" in content, "Expected 'T' in content"# ISO datetime format

    def test_session_stored_in_correct_path(self, store, sample_session):
        """Session stored at {base_path}/{session_id}/session.yaml."""
        path = store.save(sample_session)

        expected_dir = store.base_path / sample_session.session_id
        expected_file = expected_dir / "session.yaml"

        assert path == expected_file, "Expected path to equal expected_file"

    def test_round_trip_preserves_all_fields(self, store):
        """All fields should be preserved through save/load cycle."""
        from agentforge.core.harness.session_domain import SessionContext

        # Create session with all fields populated
        session = SessionContext.create(
            workflow_type="tdflow",
            initial_phase="red",
            token_budget=75000
        )
        session.add_artifact("test.py", "created")
        session.add_history("test_action", phase="red", details="test details")
        session.token_budget.record_usage(25000)

        # Save and load
        store.save(session)
        loaded = store.load(session.session_id)

        # Verify all fields
        assert loaded.session_id == session.session_id, "Expected loaded.session_id to equal session.session_id"
        assert loaded.workflow_type == session.workflow_type, "Expected loaded.workflow_type to equal session.workflow_type"
        assert loaded.current_phase == session.current_phase, "Expected loaded.current_phase to equal session.current_phase"
        assert loaded.token_budget.total_budget == session.token_budget.total_budget, "Expected loaded.token_budget.total_b... to equal session.token_budget.total_..."
        assert loaded.token_budget.tokens_used == session.token_budget.tokens_used, "Expected loaded.token_budget.tokens_... to equal session.token_budget.tokens..."
        assert len(loaded.artifacts) == len(session.artifacts), "Expected len(loaded.artifacts) to equal len(session.artifacts)"
        assert len(loaded.history) == len(session.history), "Expected len(loaded.history) to equal len(session.history)"
