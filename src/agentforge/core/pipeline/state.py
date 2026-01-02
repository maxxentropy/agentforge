# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-state
# @test_path: tests/unit/pipeline/test_state.py

"""
Pipeline State
==============

Core dataclasses for pipeline and stage state management.

The state model supports:
- Pipeline lifecycle tracking (PENDING -> RUNNING -> COMPLETED)
- Stage-level state with artifacts
- Serialization to/from YAML for persistence
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid


class PipelineStatus(Enum):
    """Pipeline lifecycle status."""

    PENDING = "pending"  # Created but not started
    RUNNING = "running"  # Currently executing
    PAUSED = "paused"  # Paused (can be resumed)
    WAITING_APPROVAL = "waiting_approval"  # Waiting for human approval
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"  # Failed with error
    ABORTED = "aborted"  # Manually aborted


class StageStatus(Enum):
    """Stage execution status."""

    PENDING = "pending"  # Not yet executed
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"  # Failed with error
    SKIPPED = "skipped"  # Skipped (conditional flow)


@dataclass
class StageState:
    """
    State for a single pipeline stage.

    Tracks execution status, timing, artifacts produced,
    and any errors that occurred.
    """

    stage_name: str
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for YAML storage."""
        return {
            "stage_name": self.stage_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "artifacts": self.artifacts,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageState":
        """Deserialize from dictionary."""
        return cls(
            stage_name=data["stage_name"],
            status=StageStatus(data["status"]),
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at")
                else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            artifacts=data.get("artifacts", {}),
            error=data.get("error"),
        )

    def mark_running(self) -> None:
        """Mark stage as running."""
        self.status = StageStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, artifacts: Dict[str, Any] = None) -> None:
        """Mark stage as completed with optional artifacts."""
        self.status = StageStatus.COMPLETED
        self.completed_at = datetime.now()
        if artifacts:
            self.artifacts.update(artifacts)

    def mark_failed(self, error: str) -> None:
        """Mark stage as failed with error message."""
        self.status = StageStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def mark_skipped(self, reason: str = None) -> None:
        """Mark stage as skipped."""
        self.status = StageStatus.SKIPPED
        self.completed_at = datetime.now()
        if reason:
            self.artifacts["skip_reason"] = reason


def generate_pipeline_id() -> str:
    """
    Generate a unique pipeline ID.

    Format: PL-{YYYYMMDD}-{uuid8}
    Example: PL-20260102-a1b2c3d4
    """
    date_part = datetime.now().strftime("%Y%m%d")
    uuid_part = uuid.uuid4().hex[:8]
    return f"PL-{date_part}-{uuid_part}"


@dataclass
class PipelineState:
    """
    Complete state for a pipeline execution.

    Tracks:
    - Pipeline identity and configuration
    - Current execution status
    - All stage states
    - Original request and project context
    """

    pipeline_id: str
    template: str
    status: PipelineStatus
    request: str
    project_path: Path
    stages: Dict[str, StageState] = field(default_factory=dict)
    current_stage: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)

    # Stage order for the pipeline template
    stage_order: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for YAML storage."""
        return {
            "schema_version": "1.0",
            "pipeline_id": self.pipeline_id,
            "template": self.template,
            "status": self.status.value,
            "request": self.request,
            "project_path": str(self.project_path),
            "current_stage": self.current_stage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "config": self.config,
            "stage_order": self.stage_order,
            "stages": {
                name: state.to_dict() for name, state in self.stages.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        """Deserialize from dictionary."""
        stages = {
            name: StageState.from_dict(state_data)
            for name, state_data in data.get("stages", {}).items()
        }

        return cls(
            pipeline_id=data["pipeline_id"],
            template=data["template"],
            status=PipelineStatus(data["status"]),
            request=data["request"],
            project_path=Path(data["project_path"]),
            stages=stages,
            current_stage=data.get("current_stage"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            config=data.get("config", {}),
            stage_order=data.get("stage_order", []),
        )

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()

    def get_next_stage(self) -> Optional[str]:
        """Get the next stage to execute based on stage_order."""
        if not self.current_stage:
            # First stage
            return self.stage_order[0] if self.stage_order else None

        try:
            current_idx = self.stage_order.index(self.current_stage)
            if current_idx + 1 < len(self.stage_order):
                return self.stage_order[current_idx + 1]
        except ValueError:
            pass

        return None

    def get_stage(self, stage_name: str) -> StageState:
        """Get or create a stage state."""
        if stage_name not in self.stages:
            self.stages[stage_name] = StageState(stage_name=stage_name)
        return self.stages[stage_name]

    def collect_artifacts(self) -> Dict[str, Any]:
        """Collect all artifacts from completed stages."""
        artifacts = {}
        for stage_name in self.stage_order:
            stage = self.stages.get(stage_name)
            if stage and stage.status == StageStatus.COMPLETED:
                artifacts.update(stage.artifacts)
        return artifacts

    def is_terminal(self) -> bool:
        """Check if pipeline is in a terminal state."""
        return self.status in (
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.ABORTED,
        )

    def can_resume(self) -> bool:
        """Check if pipeline can be resumed."""
        return self.status in (
            PipelineStatus.PAUSED,
            PipelineStatus.WAITING_APPROVAL,
        )


# Default stage orders for common pipeline templates
PIPELINE_TEMPLATES = {
    "design": ["intake", "clarify", "analyze", "spec"],
    "implement": ["intake", "clarify", "analyze", "spec", "red", "green", "refactor", "deliver"],
    "test": ["analyze", "red"],
    "fix": ["analyze", "green", "refactor", "deliver"],
}


def create_pipeline_state(
    request: str,
    project_path: Path,
    template: str = "implement",
    config: Dict[str, Any] = None,
) -> PipelineState:
    """
    Factory function to create a new pipeline state.

    Args:
        request: The original user request
        project_path: Path to the project
        template: Pipeline template name
        config: Optional configuration overrides

    Returns:
        Initialized PipelineState
    """
    stage_order = PIPELINE_TEMPLATES.get(template, PIPELINE_TEMPLATES["implement"])

    state = PipelineState(
        pipeline_id=generate_pipeline_id(),
        template=template,
        status=PipelineStatus.PENDING,
        request=request,
        project_path=project_path,
        stage_order=stage_order,
        config=config or {},
    )

    # Initialize stage states
    for stage_name in stage_order:
        state.stages[stage_name] = StageState(stage_name=stage_name)

    return state
