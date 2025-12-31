"""
Execution Context Store
=======================

Persists LLM execution context to YAML for auditability and recovery.
Follows the same patterns as other harness stores (session_store, memory_store).
"""

import yaml
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .llm_executor_domain import ExecutionContext, StepResult


class ExecutionContextStore:
    """Stores execution context and step history to YAML.

    Directory structure per session:
        .agentforge/sessions/{session_id}/
        ├── session.yaml              # Existing session state
        ├── execution_context.yaml    # LLM execution context
        └── step_history.yaml         # Step-by-step audit trail
    """

    def __init__(self, base_path: Path):
        """Initialize the store.

        Args:
            base_path: Base path for session storage (e.g., .agentforge/sessions)
        """
        self.base_path = base_path

    def _get_session_dir(self, session_id: str) -> Path:
        """Get the directory for a session."""
        return self.base_path / session_id

    def save_context(self, context: ExecutionContext) -> Path:
        """Save execution context to YAML.

        Args:
            context: ExecutionContext to save

        Returns:
            Path to saved file
        """
        context_dir = self._get_session_dir(context.session_id)
        context_dir.mkdir(parents=True, exist_ok=True)

        context_file = context_dir / "execution_context.yaml"

        # Add metadata
        data = {
            "version": "1.0",
            "saved_at": datetime.utcnow().isoformat(),
            "context": context.to_dict()
        }

        with open(context_file, 'w') as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )

        return context_file

    def load_context(self, session_id: str) -> Optional[ExecutionContext]:
        """Load execution context from YAML.

        Args:
            session_id: Session ID to load

        Returns:
            ExecutionContext or None if not found
        """
        context_file = self._get_session_dir(session_id) / "execution_context.yaml"

        if not context_file.exists():
            return None

        with open(context_file) as f:
            data = yaml.safe_load(f)

        if not data or "context" not in data:
            return None

        return ExecutionContext.from_dict(data["context"])

    def append_step(self, session_id: str, step: StepResult) -> Path:
        """Append step result to history file.

        Args:
            session_id: Session ID
            step: StepResult to append

        Returns:
            Path to history file
        """
        context_dir = self._get_session_dir(session_id)
        context_dir.mkdir(parents=True, exist_ok=True)

        history_file = context_dir / "step_history.yaml"

        # Load existing or create new
        if history_file.exists():
            with open(history_file) as f:
                history = yaml.safe_load(f) or {"version": "1.0", "steps": []}
        else:
            history = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "steps": []
            }

        # Append step with timestamp
        step_entry = {
            "step_number": len(history["steps"]) + 1,
            "timestamp": datetime.utcnow().isoformat(),
            **step.to_dict()
        }
        history["steps"].append(step_entry)
        history["updated_at"] = datetime.utcnow().isoformat()

        # Save
        with open(history_file, 'w') as f:
            yaml.dump(
                history,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )

        return history_file

    def get_history(self, session_id: str) -> List[StepResult]:
        """Load step history for session.

        Args:
            session_id: Session ID to load history for

        Returns:
            List of StepResult objects
        """
        history_file = self._get_session_dir(session_id) / "step_history.yaml"

        if not history_file.exists():
            return []

        with open(history_file) as f:
            data = yaml.safe_load(f)

        if not data or "steps" not in data:
            return []

        # Extract just the StepResult fields (excluding step_number, timestamp metadata)
        results = []
        for step_data in data["steps"]:
            # Remove metadata fields that aren't part of StepResult
            step_fields = {
                k: v for k, v in step_data.items()
                if k not in ("step_number", "timestamp")
            }
            results.append(StepResult.from_dict(step_fields))

        return results

    def delete_context(self, session_id: str) -> bool:
        """Delete execution context and history for a session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        context_dir = self._get_session_dir(session_id)

        if not context_dir.exists():
            return False

        context_file = context_dir / "execution_context.yaml"
        history_file = context_dir / "step_history.yaml"

        deleted = False
        if context_file.exists():
            context_file.unlink()
            deleted = True
        if history_file.exists():
            history_file.unlink()
            deleted = True

        return deleted

    def list_sessions(self) -> List[str]:
        """List all sessions with execution context.

        Returns:
            List of session IDs
        """
        if not self.base_path.exists():
            return []

        sessions = []
        for session_dir in self.base_path.iterdir():
            if session_dir.is_dir():
                context_file = session_dir / "execution_context.yaml"
                if context_file.exists():
                    sessions.append(session_dir.name)

        return sorted(sessions)

    def get_step_count(self, session_id: str) -> int:
        """Get the number of steps executed for a session.

        Args:
            session_id: Session ID

        Returns:
            Number of steps
        """
        history_file = self._get_session_dir(session_id) / "step_history.yaml"

        if not history_file.exists():
            return 0

        with open(history_file) as f:
            data = yaml.safe_load(f)

        if not data or "steps" not in data:
            return 0

        return len(data["steps"])


def create_execution_store(base_path: Optional[Path] = None) -> ExecutionContextStore:
    """Factory function to create an ExecutionContextStore.

    Args:
        base_path: Optional base path (defaults to .agentforge/sessions)

    Returns:
        Configured ExecutionContextStore
    """
    if base_path is None:
        base_path = Path.cwd() / ".agentforge" / "sessions"

    return ExecutionContextStore(base_path)
