# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-stage-executor
# @test_path: tests/unit/pipeline/test_stage_executor.py

"""
Stage Executor Interface
========================

Abstract base class for pipeline stage executors.

Each stage in the pipeline (intake, clarify, analyze, etc.) has a concrete
executor that inherits from StageExecutor. The executor:
- Validates input artifacts
- Executes stage logic
- Returns a StageResult with output artifacts or escalation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .state import StageStatus

if TYPE_CHECKING:
    from .state_store import PipelineStateStore


@dataclass
class StageContext:
    """
    Context passed to stage executor.

    Bundles all inputs needed for stage execution.
    """

    pipeline_id: str
    stage_name: str
    project_path: Path
    input_artifacts: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    state_store: Optional["PipelineStateStore"] = None
    request: str = ""  # Original user request

    def get_artifact(self, key: str, default: Any = None) -> Any:
        """Get an artifact by key with optional default."""
        return self.input_artifacts.get(key, default)

    def has_artifact(self, key: str) -> bool:
        """Check if an artifact exists."""
        return key in self.input_artifacts


@dataclass
class StageResult:
    """
    Result from stage execution.

    Captures success/failure, output artifacts, and optional escalation.
    """

    status: StageStatus
    artifacts: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    next_stage: Optional[str] = None  # Override default next stage
    escalation: Optional[Dict[str, Any]] = None  # Escalation request

    @classmethod
    def success(
        cls,
        artifacts: Dict[str, Any] = None,
        next_stage: str = None,
    ) -> "StageResult":
        """Create a successful result."""
        return cls(
            status=StageStatus.COMPLETED,
            artifacts=artifacts or {},
            next_stage=next_stage,
        )

    @classmethod
    def failed(cls, error: str) -> "StageResult":
        """Create a failed result."""
        return cls(
            status=StageStatus.FAILED,
            error=error,
        )

    @classmethod
    def skipped(cls, reason: str) -> "StageResult":
        """Create a skipped result."""
        return cls(
            status=StageStatus.SKIPPED,
            artifacts={"skip_reason": reason},
        )

    @classmethod
    def escalate(
        cls,
        escalation_type: str,
        message: str,
        options: List[str] = None,
        context: Dict[str, Any] = None,
    ) -> "StageResult":
        """Create an escalation result (pauses pipeline for human input)."""
        return cls(
            status=StageStatus.COMPLETED,  # Stage itself completes
            escalation={
                "type": escalation_type,
                "message": message,
                "options": options or [],
                "context": context or {},
            },
        )

    def is_success(self) -> bool:
        """Check if result indicates success."""
        return self.status == StageStatus.COMPLETED and not self.escalation

    def is_failed(self) -> bool:
        """Check if result indicates failure."""
        return self.status == StageStatus.FAILED

    def needs_escalation(self) -> bool:
        """Check if result requires escalation."""
        return self.escalation is not None


class StageExecutor(ABC):
    """
    Abstract base class for stage executors.

    Subclasses implement specific stage logic (intake, clarify, analyze, etc.).
    """

    @abstractmethod
    def execute(self, context: StageContext) -> StageResult:
        """
        Execute the stage.

        Args:
            context: Stage execution context with artifacts and config

        Returns:
            StageResult with output artifacts or error/escalation
        """
        pass

    def validate_input(self, artifacts: Dict[str, Any]) -> List[str]:
        """
        Validate input artifacts.

        Override to implement stage-specific validation.

        Args:
            artifacts: Input artifacts to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        for required in self.get_required_inputs():
            if required not in artifacts:
                errors.append(f"Missing required artifact: {required}")
        return errors

    def get_required_inputs(self) -> List[str]:
        """
        Get list of required input artifact keys.

        Override to specify stage requirements.

        Returns:
            List of required artifact keys
        """
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for output artifacts.

        Override to specify output structure.

        Returns:
            JSON schema dict
        """
        return {}

    @property
    def stage_name(self) -> str:
        """
        Get the name of this stage.

        Defaults to class name in lowercase without 'Executor'.
        """
        name = self.__class__.__name__
        if name.endswith("Executor"):
            name = name[:-8]
        return name.lower()


class PassthroughExecutor(StageExecutor):
    """
    A simple executor that passes through artifacts unchanged.

    Useful for testing or as a placeholder.
    """

    def __init__(self, name: str = "passthrough"):
        self._name = name

    def execute(self, context: StageContext) -> StageResult:
        """Pass through input artifacts as output."""
        return StageResult.success(artifacts=dict(context.input_artifacts))

    @property
    def stage_name(self) -> str:
        return self._name
