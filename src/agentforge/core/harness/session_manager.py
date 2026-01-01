# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: core-harness-session_manager
# @test_path: tests/unit/harness/test_session_manager.py

"""
Session Manager
===============

Application service orchestrating session lifecycle.
Single session per instance.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from agentforge.core.harness.session_domain import SessionContext, SessionState
from agentforge.core.harness.session_store import SessionStore


class SessionAlreadyActive(Exception):
    """Raised when create() called with active session."""
    pass


class NoActiveSession(Exception):
    """Raised when operation requires active session but none exists."""
    pass


class InvalidStateTransition(Exception):
    """Raised when state transition is not allowed."""
    pass


class SessionManager:
    """
    Application service orchestrating session lifecycle.

    Single session per instance. Provides all session management operations.
    """

    # Valid state transitions
    VALID_TRANSITIONS = {
        SessionState.ACTIVE: {SessionState.PAUSED, SessionState.COMPLETED, SessionState.ABORTED},
        SessionState.PAUSED: {SessionState.ACTIVE, SessionState.ABORTED},
        SessionState.COMPLETED: set(),  # Terminal state
        SessionState.ABORTED: set(),    # Terminal state
    }

    def __init__(self, store: Optional[SessionStore] = None):
        """
        Initialize session manager.

        Args:
            store: SessionStore for persistence. Creates default if not provided.
        """
        self.store = store or SessionStore()
        self._current_session: Optional[SessionContext] = None

    @property
    def current_session(self) -> Optional[SessionContext]:
        """Get the current session."""
        return self._current_session

    def create(
        self,
        workflow_type: Optional[str] = None,
        initial_phase: Optional[str] = None,
        token_budget: int = 100000,
    ) -> SessionContext:
        """
        Create a new session with unique ID.

        Args:
            workflow_type: Type of workflow (e.g., 'spec', 'tdflow')
            initial_phase: Initial phase within workflow
            token_budget: Maximum tokens allocated (default 100K)

        Returns:
            New SessionContext

        Raises:
            SessionAlreadyActive: If a session is already active
        """
        if self._current_session is not None:
            raise SessionAlreadyActive(
                "A session is already active. Complete or abort it first."
            )

        session = SessionContext.create(
            workflow_type=workflow_type,
            initial_phase=initial_phase,
            token_budget=token_budget,
        )

        # Persist immediately
        self.store.save(session)
        self._current_session = session

        return session

    def load(self, session_id: str) -> Optional[SessionContext]:
        """
        Load existing session from storage.

        Args:
            session_id: Session identifier

        Returns:
            SessionContext or None if not found
        """
        session = self.store.load(session_id)
        if session:
            self._current_session = session
        return session

    def save(self) -> Path:
        """
        Persist current session state.

        Returns:
            Path to saved session file

        Raises:
            NoActiveSession: If no session is active
        """
        self._require_session()
        return self.store.save(self._current_session)

    def pause(self) -> SessionContext:
        """
        Transition current session to PAUSED state.

        Returns:
            Updated SessionContext

        Raises:
            NoActiveSession: If no session is active
            InvalidStateTransition: If transition not allowed
        """
        self._require_session()
        self._transition_to(SessionState.PAUSED)
        self._current_session.add_history("session_paused")
        self.store.save(self._current_session)
        return self._current_session

    def resume(self) -> SessionContext:
        """
        Transition current session from PAUSED to ACTIVE.

        Returns:
            Updated SessionContext

        Raises:
            NoActiveSession: If no session is active
            InvalidStateTransition: If transition not allowed
        """
        self._require_session()
        self._transition_to(SessionState.ACTIVE)
        self._current_session.add_history("session_resumed")
        self.store.save(self._current_session)
        return self._current_session

    def complete(self) -> SessionContext:
        """
        Transition current session to COMPLETED state.

        Returns:
            Updated SessionContext

        Raises:
            NoActiveSession: If no session is active
            InvalidStateTransition: If transition not allowed
        """
        self._require_session()
        self._transition_to(SessionState.COMPLETED)
        self._current_session.completed_at = datetime.utcnow()
        self._current_session.add_history("session_completed")
        self.store.save(self._current_session)
        return self._current_session

    def abort(self, reason: Optional[str] = None) -> SessionContext:
        """
        Transition current session to ABORTED state.

        Args:
            reason: Optional reason for aborting

        Returns:
            Updated SessionContext

        Raises:
            NoActiveSession: If no session is active
        """
        self._require_session()
        self._transition_to(SessionState.ABORTED)
        self._current_session.completed_at = datetime.utcnow()
        self._current_session.add_history("session_aborted", details=reason)
        self.store.save(self._current_session)
        return self._current_session

    def advance_phase(self, new_phase: str) -> SessionContext:
        """
        Update phase, record history, trigger auto-checkpoint.

        Args:
            new_phase: New phase name

        Returns:
            Updated SessionContext

        Raises:
            NoActiveSession: If no session is active
        """
        self._require_session()

        old_phase = self._current_session.current_phase
        self._current_session.current_phase = new_phase
        self._current_session.updated_at = datetime.utcnow()
        self._current_session.add_history(
            "phase_advanced",
            phase=new_phase,
            details=f"from {old_phase} to {new_phase}",
        )

        # Auto-checkpoint
        self.store.save(self._current_session)

        return self._current_session

    def checkpoint_session(self) -> Path:
        """
        Manual checkpoint - save current state.

        Returns:
            Path to saved session file

        Raises:
            NoActiveSession: If no session is active
        """
        self._require_session()
        self._current_session.add_history("checkpoint")
        return self.store.save(self._current_session)

    def record_tokens(self, tokens: int) -> bool:
        """
        Record token usage, check for budget warning.

        Args:
            tokens: Number of tokens used

        Returns:
            True if budget warning threshold reached

        Raises:
            NoActiveSession: If no session is active
        """
        self._require_session()
        self._current_session.token_budget.record_usage(tokens)
        self._current_session.updated_at = datetime.utcnow()
        return self._current_session.token_budget.is_warning

    def extend_budget(self, additional_tokens: int) -> None:
        """
        Extend token budget for current session.

        Args:
            additional_tokens: Tokens to add to budget

        Raises:
            NoActiveSession: If no session is active
        """
        self._require_session()
        self._current_session.token_budget.extend(additional_tokens)
        self._current_session.add_history(
            "budget_extended",
            details=f"added {additional_tokens} tokens",
        )

    def add_artifact(self, path: str, artifact_type: str) -> None:
        """
        Record artifact for current session and phase.

        Args:
            path: Relative file path
            artifact_type: 'created' or 'modified'

        Raises:
            NoActiveSession: If no session is active
        """
        self._require_session()
        self._current_session.add_artifact(path, artifact_type)

    def cleanup_old_sessions(
        self,
        days: int,
        dry_run: bool = False,
    ) -> List[str]:
        """
        Remove old COMPLETED/ABORTED sessions.

        Args:
            days: Delete sessions older than this many days
            dry_run: If True, return list without deleting

        Returns:
            List of deleted (or would-be deleted) session IDs
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_delete = []

        for session_id in self.store.list_sessions():
            session = self.store.load(session_id)
            if session is None:
                continue

            # Only delete terminal states
            if session.state not in (SessionState.COMPLETED, SessionState.ABORTED):
                continue

            # Check age based on completed_at or updated_at
            session_time = session.completed_at or session.updated_at
            if session_time <= cutoff:
                to_delete.append(session_id)

        if not dry_run:
            for session_id in to_delete:
                self.store.delete(session_id)

        return to_delete

    def _require_session(self) -> None:
        """Raise NoActiveSession if no session is active."""
        if self._current_session is None:
            raise NoActiveSession("No active session. Create or load a session first.")

    def _transition_to(self, target_state: SessionState) -> None:
        """
        Validate and execute state transition.

        Args:
            target_state: State to transition to

        Raises:
            InvalidStateTransition: If transition not allowed
        """
        current = self._current_session.state
        valid_targets = self.VALID_TRANSITIONS.get(current, set())

        if target_state not in valid_targets:
            raise InvalidStateTransition(
                f"Cannot transition from {current.value} to {target_state.value}"
            )

        self._current_session.state = target_state
        self._current_session.updated_at = datetime.utcnow()
