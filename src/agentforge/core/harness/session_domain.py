# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: core-harness-session_domain
# @test_path: tests/unit/harness/test_agent_orchestrator.py

"""
Session Domain Model
====================

Domain entities for the Agent Harness session management.
Follows patterns from tools/tdflow/domain.py.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid


class SessionState(Enum):
    """Session lifecycle states."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass
class TokenBudget:
    """
    Tracks token consumption against allocated budget.

    Provides budget monitoring and extension capabilities.
    """

    total_budget: int = 100000
    tokens_used: int = 0

    @property
    def tokens_remaining(self) -> int:
        """Calculate remaining tokens."""
        return self.total_budget - self.tokens_used

    @property
    def utilization_percent(self) -> float:
        """Calculate utilization as percentage."""
        if self.total_budget == 0:
            return 0.0
        return (self.tokens_used / self.total_budget) * 100

    @property
    def is_warning(self) -> bool:
        """Check if utilization is at or above 80% warning threshold."""
        return self.utilization_percent >= 80.0

    def can_continue(self, required_tokens: int) -> bool:
        """Check if budget allows operation requiring specified tokens."""
        return self.tokens_remaining >= required_tokens

    def record_usage(self, tokens: int) -> None:
        """Record token usage."""
        self.tokens_used += tokens

    def extend(self, additional_tokens: int) -> None:
        """Extend total budget by additional tokens."""
        self.total_budget += additional_tokens


@dataclass
class SessionArtifact:
    """
    Represents a file created or modified during session execution.
    """

    path: str
    artifact_type: str  # 'created' or 'modified'
    timestamp: datetime
    phase: Optional[str] = None


@dataclass
class SessionHistory:
    """
    A history entry tracking a significant session event.
    """

    timestamp: datetime
    action: str
    phase: Optional[str] = None
    details: Optional[str] = None


@dataclass
class SessionContext:
    """
    Main session entity containing all session state and metadata.

    This is the primary domain object managed by SessionManager.
    """

    session_id: str
    state: SessionState
    created_at: datetime
    updated_at: datetime
    token_budget: TokenBudget = field(default_factory=TokenBudget)
    workflow_type: Optional[str] = None
    current_phase: Optional[str] = None
    attempt_number: int = 1
    completed_at: Optional[datetime] = None
    artifacts: List[SessionArtifact] = field(default_factory=list)
    history: List[SessionHistory] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        workflow_type: Optional[str] = None,
        initial_phase: Optional[str] = None,
        token_budget: int = 100000,
    ) -> "SessionContext":
        """
        Factory method to create a new session with unique ID.

        Args:
            workflow_type: Type of workflow (e.g., 'spec', 'tdflow')
            initial_phase: Initial phase within workflow
            token_budget: Maximum tokens allocated (default 100K)

        Returns:
            New SessionContext instance
        """
        now = datetime.utcnow()
        session_id = f"session_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        session = cls(
            session_id=session_id,
            state=SessionState.ACTIVE,
            created_at=now,
            updated_at=now,
            token_budget=TokenBudget(total_budget=token_budget),
            workflow_type=workflow_type,
            current_phase=initial_phase,
        )

        # Add creation history entry
        session.add_history("session_created")

        return session

    def add_artifact(
        self,
        path: str,
        artifact_type: str,
        phase: Optional[str] = None,
    ) -> None:
        """
        Record an artifact with current timestamp.

        Args:
            path: Relative file path
            artifact_type: 'created' or 'modified'
            phase: Phase that produced the artifact (defaults to current_phase)
        """
        self.artifacts.append(
            SessionArtifact(
                path=path,
                artifact_type=artifact_type,
                timestamp=datetime.utcnow(),
                phase=phase or self.current_phase,
            )
        )
        self.updated_at = datetime.utcnow()

    def get_artifacts(self, phase: Optional[str] = None) -> List[SessionArtifact]:
        """
        Get artifacts, optionally filtered by phase.

        Args:
            phase: Filter by phase (None returns all)

        Returns:
            List of matching artifacts
        """
        if phase is None:
            return list(self.artifacts)
        return [a for a in self.artifacts if a.phase == phase]

    def add_history(
        self,
        action: str,
        phase: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        """
        Record a history entry with current timestamp.

        Args:
            action: Description of the action
            phase: Current phase (defaults to current_phase)
            details: Optional additional context
        """
        self.history.append(
            SessionHistory(
                timestamp=datetime.utcnow(),
                action=action,
                phase=phase or self.current_phase,
                details=details,
            )
        )
        self.updated_at = datetime.utcnow()
