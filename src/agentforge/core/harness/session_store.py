# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: core-harness-session_store
# @test_path: tests/unit/harness/test_session_manager.py

"""
Session Store
=============

Persistence layer for SessionContext using atomic YAML writes.
Follows patterns from tools/tdflow/session.py.
"""

import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from agentforge.core.harness.session_domain import (
    SessionArtifact,
    SessionContext,
    SessionHistory,
    SessionState,
    TokenBudget,
)


class SessionStore:
    """
    Persistence layer for SessionContext.

    Handles serialization to/from YAML files using atomic writes
    for crash safety.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize session store.

        Args:
            base_path: Base directory for session storage.
                      Defaults to .agentforge/sessions
        """
        self.base_path = base_path or Path(".agentforge/sessions")

    def ensure_directory(self) -> None:
        """Create base directory with .gitkeep if needed."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        gitkeep = self.base_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def save(self, session: SessionContext) -> Path:
        """
        Persist session to YAML using atomic write.

        Args:
            session: Session to save

        Returns:
            Path to saved session file
        """
        self.ensure_directory()

        session_dir = self.base_path / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / "session.yaml"

        # Serialize session
        data = self._serialize(session)

        # Atomic write: write to temp file, then rename
        fd, temp_path = tempfile.mkstemp(
            suffix=".yaml",
            dir=session_dir,
        )
        try:
            with os.fdopen(fd, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            # Atomic rename
            shutil.move(temp_path, session_file)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        return session_file

    def load(self, session_id: str) -> Optional[SessionContext]:
        """
        Load session from YAML.

        Args:
            session_id: Session identifier

        Returns:
            SessionContext or None if not found
        """
        session_file = self.base_path / session_id / "session.yaml"

        if not session_file.exists():
            return None

        try:
            with open(session_file) as f:
                data = yaml.safe_load(f)
            return self._deserialize(data)
        except (yaml.YAMLError, KeyError, TypeError):
            # Corrupted file - return None or could raise specific error
            return None

    def exists(self, session_id: str) -> bool:
        """
        Check if session file exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists
        """
        session_file = self.base_path / session_id / "session.yaml"
        return session_file.exists()

    def list_sessions(self) -> List[str]:
        """
        Get list of all session IDs in storage.

        Returns:
            List of session IDs
        """
        if not self.base_path.exists():
            return []

        sessions = []
        for path in self.base_path.iterdir():
            if path.is_dir() and (path / "session.yaml").exists():
                sessions.append(path.name)
        return sessions

    def delete(self, session_id: str) -> bool:
        """
        Remove session directory.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        session_dir = self.base_path / session_id

        if not session_dir.exists():
            return False

        shutil.rmtree(session_dir)
        return True

    def _serialize(self, session: SessionContext) -> Dict[str, Any]:
        """
        Serialize session to dictionary for YAML.

        Args:
            session: Session to serialize

        Returns:
            Dictionary representation
        """
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "workflow_type": session.workflow_type,
            "current_phase": session.current_phase,
            "attempt_number": session.attempt_number,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "token_budget": {
                "total_budget": session.token_budget.total_budget,
                "tokens_used": session.token_budget.tokens_used,
            },
            "artifacts": [
                {
                    "path": a.path,
                    "artifact_type": a.artifact_type,
                    "timestamp": a.timestamp.isoformat(),
                    "phase": a.phase,
                }
                for a in session.artifacts
            ],
            "history": [
                {
                    "timestamp": h.timestamp.isoformat(),
                    "action": h.action,
                    "phase": h.phase,
                    "details": h.details,
                }
                for h in session.history
            ],
        }

    def _deserialize(self, data: Dict[str, Any]) -> SessionContext:
        """
        Deserialize dictionary to SessionContext.

        Args:
            data: Dictionary from YAML

        Returns:
            SessionContext instance
        """
        token_data = data.get("token_budget", {})
        token_budget = TokenBudget(
            total_budget=token_data.get("total_budget", 100000),
            tokens_used=token_data.get("tokens_used", 0),
        )

        artifacts = [
            SessionArtifact(
                path=a["path"],
                artifact_type=a["artifact_type"],
                timestamp=datetime.fromisoformat(a["timestamp"]),
                phase=a.get("phase"),
            )
            for a in data.get("artifacts", [])
        ]

        history = [
            SessionHistory(
                timestamp=datetime.fromisoformat(h["timestamp"]),
                action=h["action"],
                phase=h.get("phase"),
                details=h.get("details"),
            )
            for h in data.get("history", [])
        ]

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return SessionContext(
            session_id=data["session_id"],
            state=SessionState(data["state"]),
            workflow_type=data.get("workflow_type"),
            current_phase=data.get("current_phase"),
            attempt_number=data.get("attempt_number", 1),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=completed_at,
            token_budget=token_budget,
            artifacts=artifacts,
            history=history,
        )
