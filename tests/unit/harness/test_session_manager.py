# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: tools-harness-session_store
# @impl_path: tools/harness/session_store.py

"""
Unit tests for SessionManager application service.

Tests for: create, load, pause, resume, complete, abort, advance_phase,
          record_tokens, extend_budget, add_artifact, cleanup_old_sessions
Based on specification acceptance criteria AC-001 through AC-030.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


class TestSessionManagerCreation:
    """Tests for session creation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test isolation."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create SessionManager with temp directory."""
        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore
        store = SessionStore(base_path=temp_dir / "sessions")
        return SessionManager(store=store)

    def test_create_returns_session_with_unique_id(self, manager):
        """AC-001: create() returns session with unique ID and ACTIVE state."""
        from agentforge.core.harness.session_domain import SessionState

        session = manager.create()

        assert session is not None
        assert session.session_id.startswith("session_")
        assert session.state == SessionState.ACTIVE
        assert session.token_budget.total_budget == 100000

    def test_create_with_workflow_and_budget(self, manager):
        """AC-002: create() accepts workflow_type and token_budget."""
        session = manager.create(
            workflow_type="spec",
            token_budget=50000
        )

        assert session.workflow_type == "spec"
        assert session.token_budget.total_budget == 50000

    def test_create_persists_immediately(self, manager):
        """Session should be persisted immediately on creation."""
        session = manager.create()

        # Should be loadable immediately
        loaded = manager.load(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id

    def test_create_when_session_active_returns_error(self, manager):
        """SessionAlreadyActive error when create() called with active session."""
        manager.create()

        # Second create should fail or return error
        with pytest.raises(Exception):  # SessionAlreadyActive
            manager.create()


class TestSessionManagerStateTransitions:
    """Tests for session state transitions."""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore
        store = SessionStore(base_path=temp_dir / "sessions")
        return SessionManager(store=store)

    def test_pause_transitions_to_paused(self, manager):
        """AC-004: pause() transitions ACTIVE to PAUSED."""
        from agentforge.core.harness.session_domain import SessionState

        manager.create()
        session = manager.pause()

        assert session.state == SessionState.PAUSED

    def test_pause_records_history(self, manager):
        """AC-004: pause() records history entry."""
        manager.create()
        initial_history_len = len(manager.current_session.history)

        manager.pause()

        assert len(manager.current_session.history) > initial_history_len

    def test_resume_transitions_to_active(self, manager):
        """AC-005: resume() transitions PAUSED to ACTIVE."""
        from agentforge.core.harness.session_domain import SessionState

        manager.create()
        manager.pause()
        session = manager.resume()

        assert session.state == SessionState.ACTIVE

    def test_resume_records_history(self, manager):
        """AC-005: resume() records history entry."""
        manager.create()
        manager.pause()
        history_before_resume = len(manager.current_session.history)

        manager.resume()

        assert len(manager.current_session.history) > history_before_resume

    def test_complete_transitions_to_completed(self, manager):
        """complete() transitions to COMPLETED (terminal)."""
        from agentforge.core.harness.session_domain import SessionState

        manager.create()
        session = manager.complete()

        assert session.state == SessionState.COMPLETED
        assert session.completed_at is not None

    def test_abort_transitions_to_aborted(self, manager):
        """abort() transitions to ABORTED (terminal)."""
        from agentforge.core.harness.session_domain import SessionState

        manager.create()
        session = manager.abort(reason="Test abort")

        assert session.state == SessionState.ABORTED
        assert session.completed_at is not None

    def test_pause_from_completed_fails(self, manager):
        """AC-006: Cannot transition from COMPLETED state."""
        manager.create()
        manager.complete()

        with pytest.raises(Exception):  # InvalidStateTransition
            manager.pause()

    def test_pause_from_aborted_fails(self, manager):
        """Cannot transition from ABORTED state."""
        manager.create()
        manager.abort()

        with pytest.raises(Exception):  # InvalidStateTransition
            manager.pause()

    def test_no_active_session_returns_error(self, manager):
        """NoActiveSession error when no session exists."""
        with pytest.raises(Exception):  # NoActiveSession
            manager.pause()


class TestSessionManagerPhaseAdvancement:
    """Tests for phase advancement."""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore
        store = SessionStore(base_path=temp_dir / "sessions")
        return SessionManager(store=store)

    def test_advance_phase_updates_current_phase(self, manager):
        """AC-017: advance_phase() updates current_phase."""
        manager.create(initial_phase="analyze")
        session = manager.advance_phase("implement")

        assert session.current_phase == "implement"

    def test_advance_phase_triggers_checkpoint(self, manager):
        """AC-017: advance_phase() triggers auto-checkpoint."""
        manager.create(initial_phase="analyze")
        manager.advance_phase("implement")

        # Should be persisted
        loaded = manager.load(manager.current_session.session_id)
        assert loaded.current_phase == "implement"

    def test_advance_phase_records_history(self, manager):
        """AC-017: advance_phase() records history."""
        manager.create(initial_phase="analyze")
        history_before = len(manager.current_session.history)

        manager.advance_phase("implement")

        assert len(manager.current_session.history) > history_before

    def test_tdflow_phase_transitions(self, manager):
        """AC-018: TDFLOW phase transitions trigger checkpoints."""
        manager.create(workflow_type="tdflow", initial_phase="red")

        manager.advance_phase("green")
        manager.advance_phase("refactor")

        loaded = manager.load(manager.current_session.session_id)
        assert loaded.current_phase == "refactor"


class TestSessionManagerTokenBudget:
    """Tests for token budget management."""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore
        store = SessionStore(base_path=temp_dir / "sessions")
        return SessionManager(store=store)

    def test_record_tokens_updates_usage(self, manager):
        """AC-013: record_tokens() updates token usage."""
        manager.create()
        manager.record_tokens(50000)

        assert manager.current_session.token_budget.tokens_used == 50000
        assert manager.current_session.token_budget.tokens_remaining == 50000

    def test_record_tokens_returns_warning_at_80_percent(self, manager):
        """AC-014: Warning returned at 80% utilization."""
        manager.create()
        manager.record_tokens(80000)

        # Should indicate warning
        assert manager.current_session.token_budget.is_warning is True

    def test_extend_budget_increases_total(self, manager):
        """AC-016: extend_budget() increases total."""
        manager.create()
        manager.record_tokens(100000)  # At limit

        manager.extend_budget(50000)

        assert manager.current_session.token_budget.total_budget == 150000
        assert manager.current_session.token_budget.can_continue(40000) is True


class TestSessionManagerArtifacts:
    """Tests for artifact tracking."""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore
        store = SessionStore(base_path=temp_dir / "sessions")
        return SessionManager(store=store)

    def test_add_artifact_records_file(self, manager):
        """AC-019: add_artifact() records artifact with phase."""
        manager.create(initial_phase="implement")
        manager.add_artifact("src/foo.py", "created")

        artifacts = manager.current_session.artifacts
        assert len(artifacts) == 1
        assert artifacts[0].path == "src/foo.py"
        assert artifacts[0].artifact_type == "created"
        assert artifacts[0].phase == "implement"


class TestSessionManagerCheckpointing:
    """Tests for checkpointing behavior."""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore
        store = SessionStore(base_path=temp_dir / "sessions")
        return SessionManager(store=store)

    def test_checkpoint_session_saves_current_state(self, manager):
        """AC-022: checkpoint_session() saves without phase change."""
        manager.create(initial_phase="analyze")
        manager.record_tokens(5000)

        path = manager.checkpoint_session()

        assert path.exists()
        loaded = manager.load(manager.current_session.session_id)
        assert loaded.token_budget.tokens_used == 5000
        assert loaded.current_phase == "analyze"

    def test_advance_phase_auto_checkpoints(self, manager):
        """AC-021: advance_phase() automatically checkpoints."""
        manager.create(initial_phase="analyze")
        manager.advance_phase("implement")

        # State should be persisted
        loaded = manager.load(manager.current_session.session_id)
        assert loaded.current_phase == "implement"


class TestSessionManagerCleanup:
    """Tests for session cleanup."""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore
        store = SessionStore(base_path=temp_dir / "sessions")
        return SessionManager(store=store)

    def test_cleanup_removes_old_completed_sessions(self, manager):
        """AC-025: cleanup removes old COMPLETED sessions."""
        # Create and complete a session
        manager.create()
        session_id = manager.current_session.session_id
        manager.complete()

        # Reset manager for cleanup (simulating new instance)
        manager._current_session = None

        # Cleanup with 0 days (remove all completed)
        deleted = manager.cleanup_old_sessions(days=0)

        assert session_id in deleted
        assert not manager.store.exists(session_id)

    def test_cleanup_preserves_paused_sessions(self, manager):
        """AC-026: cleanup preserves PAUSED sessions regardless of age."""
        manager.create()
        session_id = manager.current_session.session_id
        manager.pause()

        manager._current_session = None

        deleted = manager.cleanup_old_sessions(days=0)

        assert session_id not in deleted
        assert manager.store.exists(session_id)

    def test_cleanup_preserves_active_sessions(self, manager):
        """Active sessions never deleted by cleanup."""
        manager.create()
        session_id = manager.current_session.session_id

        manager._current_session = None

        deleted = manager.cleanup_old_sessions(days=0)

        assert session_id not in deleted
        assert manager.store.exists(session_id)

    def test_cleanup_dry_run_returns_but_does_not_delete(self, manager):
        """AC-027: dry_run=True previews without deleting."""
        manager.create()
        session_id = manager.current_session.session_id
        manager.complete()

        manager._current_session = None

        # Dry run
        would_delete = manager.cleanup_old_sessions(days=0, dry_run=True)

        assert session_id in would_delete
        assert manager.store.exists(session_id)  # Still exists


class TestSessionManagerTestability:
    """Tests for testability requirements."""

    def test_session_manager_accepts_custom_store(self):
        """AC-030: SessionManager works with custom store path."""
        import tempfile
        from pathlib import Path

        from agentforge.core.harness.session_manager import SessionManager
        from agentforge.core.harness.session_store import SessionStore

        with tempfile.TemporaryDirectory() as temp:
            store = SessionStore(base_path=Path(temp) / "custom_sessions")
            manager = SessionManager(store=store)

            session = manager.create()
            assert session is not None

            loaded = manager.load(session.session_id)
            assert loaded is not None
