"""
Pipeline Result
===============

Result object returned by pipeline execution.
"""

import time
from dataclasses import dataclass, field
from typing import Any

from ..state import (
    PipelineState,
    PipelineStatus,
    StageStatus,
)


@dataclass
class PipelineResult:
    """
    Result object returned by execute() and resume().

    Provides consistent interface for CLI to consume.
    """

    success: bool
    pipeline_id: str
    stages_completed: list[str] = field(default_factory=list)
    current_stage: str | None = None
    deliverable: dict[str, Any] | None = None
    error: str | None = None
    total_duration_seconds: float = 0.0

    @classmethod
    def from_state(cls, state: PipelineState, start_time: float) -> "PipelineResult":
        """Create PipelineResult from PipelineState."""
        completed_stages = [
            name for name, stage in state.stages.items()
            if stage.status == StageStatus.COMPLETED
        ]

        # Get deliverable from deliver stage if completed
        deliverable = None
        if "deliver" in state.stages:
            deliver_stage = state.stages["deliver"]
            if deliver_stage.status == StageStatus.COMPLETED:
                deliverable = deliver_stage.artifacts

        # Determine error message
        error = None
        if state.status == PipelineStatus.FAILED:
            for _name, stage in state.stages.items():
                if stage.status == StageStatus.FAILED and stage.error:
                    error = stage.error
                    break

        return cls(
            success=state.status == PipelineStatus.COMPLETED,
            pipeline_id=state.pipeline_id,
            stages_completed=completed_stages,
            current_stage=state.current_stage,
            deliverable=deliverable,
            error=error,
            total_duration_seconds=time.time() - start_time,
        )
