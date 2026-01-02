# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-escalation
# @test_path: tests/unit/pipeline/test_escalation.py

"""
Escalation Handler
==================

Handles human escalation requests during pipeline execution.

Escalations pause the pipeline and wait for human input. Types include:
- APPROVAL_REQUIRED: Human must approve before proceeding
- CLARIFICATION_NEEDED: More information needed from user
- ERROR_RECOVERY: Help needed to recover from error
- CANNOT_PROCEED: Pipeline cannot continue without intervention
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class EscalationType(Enum):
    """Types of escalation requests."""

    APPROVAL_REQUIRED = "approval_required"
    CLARIFICATION_NEEDED = "clarification_needed"
    ERROR_RECOVERY = "error_recovery"
    CANNOT_PROCEED = "cannot_proceed"


class EscalationStatus(Enum):
    """Status of an escalation."""

    PENDING = "pending"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Escalation:
    """
    An escalation request for human intervention.
    """

    escalation_id: str
    pipeline_id: str
    stage_name: str
    type: EscalationType
    message: str
    options: list[str] | None = None
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: EscalationStatus = EscalationStatus.PENDING
    response: str | None = None
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "escalation_id": self.escalation_id,
            "pipeline_id": self.pipeline_id,
            "stage_name": self.stage_name,
            "type": self.type.value,
            "message": self.message,
            "options": self.options,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "response": self.response,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Escalation":
        """Deserialize from dictionary."""
        return cls(
            escalation_id=data["escalation_id"],
            pipeline_id=data["pipeline_id"],
            stage_name=data["stage_name"],
            type=EscalationType(data["type"]),
            message=data["message"],
            options=data.get("options"),
            context=data.get("context", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            status=EscalationStatus(data.get("status", "pending")),
            response=data.get("response"),
            resolved_at=(
                datetime.fromisoformat(data["resolved_at"])
                if data.get("resolved_at")
                else None
            ),
        )


def generate_escalation_id() -> str:
    """Generate a unique escalation ID."""
    return f"ESC-{uuid.uuid4().hex[:8]}"


class EscalationHandler:
    """
    Manages escalation lifecycle.

    Stores escalations in YAML files for persistence.
    """

    def __init__(self, project_path: Path):
        """
        Initialize escalation handler.

        Args:
            project_path: Root path for the project
        """
        self.project_path = Path(project_path)
        self.escalation_dir = self.project_path / ".agentforge" / "escalations"
        self.escalation_dir.mkdir(parents=True, exist_ok=True)

    def _get_escalation_path(self, escalation_id: str) -> Path:
        """Get path to escalation file."""
        return self.escalation_dir / f"{escalation_id}.yaml"

    def create(self, escalation: Escalation) -> str:
        """
        Create an escalation and persist it.

        Args:
            escalation: Escalation to create

        Returns:
            Escalation ID
        """
        if not escalation.escalation_id:
            escalation.escalation_id = generate_escalation_id()

        file_path = self._get_escalation_path(escalation.escalation_id)

        with open(file_path, "w") as f:
            yaml.safe_dump(escalation.to_dict(), f, default_flow_style=False)

        logger.info(
            f"Created escalation {escalation.escalation_id} "
            f"for pipeline {escalation.pipeline_id}"
        )

        return escalation.escalation_id

    def resolve(self, escalation_id: str, response: str) -> None:
        """
        Resolve an escalation with user response.

        Args:
            escalation_id: ID of escalation to resolve
            response: User's response
        """
        escalation = self.get(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation not found: {escalation_id}")

        if escalation.status != EscalationStatus.PENDING:
            raise ValueError(
                f"Cannot resolve escalation in status: {escalation.status.value}"
            )

        escalation.status = EscalationStatus.RESOLVED
        escalation.response = response
        escalation.resolved_at = datetime.now()

        file_path = self._get_escalation_path(escalation_id)
        with open(file_path, "w") as f:
            yaml.safe_dump(escalation.to_dict(), f, default_flow_style=False)

        logger.info(f"Resolved escalation {escalation_id}")

    def reject(self, escalation_id: str, reason: str) -> None:
        """
        Reject an escalation.

        Args:
            escalation_id: ID of escalation to reject
            reason: Rejection reason
        """
        escalation = self.get(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation not found: {escalation_id}")

        escalation.status = EscalationStatus.REJECTED
        escalation.response = reason
        escalation.resolved_at = datetime.now()

        file_path = self._get_escalation_path(escalation_id)
        with open(file_path, "w") as f:
            yaml.safe_dump(escalation.to_dict(), f, default_flow_style=False)

        logger.info(f"Rejected escalation {escalation_id}")

    def get(self, escalation_id: str) -> Escalation | None:
        """
        Get an escalation by ID.

        Args:
            escalation_id: ID of escalation to get

        Returns:
            Escalation if found, None otherwise
        """
        file_path = self._get_escalation_path(escalation_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
                return Escalation.from_dict(data)
        except (yaml.YAMLError, KeyError, ValueError) as e:
            logger.error(f"Failed to load escalation {escalation_id}: {e}")
            return None

    def get_pending(self, pipeline_id: str = None) -> list[Escalation]:
        """
        Get pending escalations.

        Args:
            pipeline_id: Optional filter by pipeline ID

        Returns:
            List of pending escalations
        """
        pending = []
        for file_path in self.escalation_dir.glob("*.yaml"):
            escalation = self._load_from_file(file_path)
            if escalation and escalation.status == EscalationStatus.PENDING:
                if pipeline_id is None or escalation.pipeline_id == pipeline_id:
                    pending.append(escalation)

        # Sort by creation time
        pending.sort(key=lambda e: e.created_at)
        return pending

    def get_for_pipeline(self, pipeline_id: str) -> list[Escalation]:
        """
        Get all escalations for a pipeline.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            List of escalations for the pipeline
        """
        escalations = []
        for file_path in self.escalation_dir.glob("*.yaml"):
            escalation = self._load_from_file(file_path)
            if escalation and escalation.pipeline_id == pipeline_id:
                escalations.append(escalation)

        # Sort by creation time
        escalations.sort(key=lambda e: e.created_at)
        return escalations

    def _load_from_file(self, file_path: Path) -> Escalation | None:
        """Load escalation from file."""
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
                return Escalation.from_dict(data)
        except (yaml.YAMLError, KeyError, ValueError) as e:
            logger.error(f"Failed to load escalation from {file_path}: {e}")
            return None

    def delete(self, escalation_id: str) -> bool:
        """
        Delete an escalation.

        Args:
            escalation_id: ID of escalation to delete

        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_escalation_path(escalation_id)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted escalation {escalation_id}")
            return True
        return False

    def cleanup_resolved(self, days: int = 7) -> int:
        """
        Delete resolved escalations older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of escalations deleted
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted = 0

        for file_path in self.escalation_dir.glob("*.yaml"):
            escalation = self._load_from_file(file_path)
            if (
                escalation
                and escalation.status != EscalationStatus.PENDING
                and escalation.resolved_at
                and escalation.resolved_at.timestamp() < cutoff
            ):
                self.delete(escalation.escalation_id)
                deleted += 1

        logger.info(f"Cleaned up {deleted} old escalations")
        return deleted
