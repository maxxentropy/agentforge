# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-controller
# @component_id: pipeline-result
# @test_path: tests/unit/pipeline/test_controller.py
# @test_path: tests/unit/pipeline/test_controller_api.py

"""
Pipeline Controller Package
===========================

Main orchestration engine for pipeline execution.

Public API:
    execute(request, template, config) -> PipelineResult  # Create and run
    resume(pipeline_id) -> PipelineResult                 # Resume paused
    approve(pipeline_id) -> bool                          # Approve escalation
    reject(pipeline_id, reason) -> bool                   # Reject escalation
    abort(pipeline_id, reason) -> bool                    # Abort pipeline
    list_pipelines(status, limit) -> List[PipelineState]  # Query history
    provide_feedback(pipeline_id, feedback) -> None       # Store feedback
    get_status(pipeline_id) -> PipelineState              # Get current state
    pause(pipeline_id) -> bool                            # Pause running
"""

from .base import PipelineController
from .exceptions import (
    PipelineError,
    PipelineNotFoundError,
    PipelineStateError,
)
from .result import PipelineResult

__all__ = [
    # Main class
    "PipelineController",
    # Result dataclass
    "PipelineResult",
    # Exceptions
    "PipelineError",
    "PipelineNotFoundError",
    "PipelineStateError",
]
