# Pipeline Controller Specification - Stage 1: Core Architecture

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Estimated Effort:** 5-7 days

---

## 1. Overview

### 1.1 Purpose

The Pipeline Controller Core is the central orchestration engine that manages the execution of multi-stage development workflows. It coordinates stage execution, manages state transitions, handles escalations, and ensures artifact validation between stages.

### 1.2 Position in Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│   agentforge start | design | implement | status | approve      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PIPELINE CONTROLLER CORE                       │  ◄── THIS SPEC
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ PipelineState │  │ StageRouter  │  │ ArtifactValidator    │  │
│  │    Machine    │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Escalation   │  │ Pipeline     │  │ StageExecutor        │  │
│  │ Handler      │  │ StateStore   │  │ Registry             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Stage Executors                             │
│   IntakeExecutor | AnalyzeExecutor | SpecExecutor | ...         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Minimal Context Architecture                     │
│   MinimalContextExecutor | Tool Handlers | LLM Abstraction      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Design Principles

1. **Single Entry Point**: All pipeline execution flows through `PipelineController.execute()`
2. **State Persistence**: Pipeline state survives process restarts
3. **Artifact-Driven**: Stages communicate via validated artifacts
4. **Fail-Safe**: Escalation on any unrecoverable error
5. **Extensible**: New stages and pipelines via configuration

---

## 2. Core Components

### 2.1 PipelineController

The main orchestrator class.

```python
# src/agentforge/core/pipeline/controller.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Overall pipeline execution status."""
    PENDING = "pending"           # Created but not started
    RUNNING = "running"           # Currently executing
    PAUSED = "paused"             # Waiting for human input
    AWAITING_APPROVAL = "awaiting_approval"  # Stage complete, needs approval
    COMPLETED = "completed"       # Successfully finished
    FAILED = "failed"             # Unrecoverable error
    ABORTED = "aborted"           # User cancelled


class StageStatus(Enum):
    """Individual stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result from executing a single stage."""
    stage_name: str
    status: StageStatus
    artifact: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    escalation_reason: Optional[str] = None
    duration_seconds: float = 0.0
    
    @property
    def success(self) -> bool:
        return self.status == StageStatus.COMPLETED
    
    @property
    def escalated(self) -> bool:
        return self.escalation_reason is not None


@dataclass
class PipelineResult:
    """Final result of pipeline execution."""
    success: bool
    pipeline_id: str
    status: PipelineStatus
    current_stage: Optional[str] = None
    deliverable: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    stages_completed: List[str] = field(default_factory=list)
    total_duration_seconds: float = 0.0


@dataclass
class PipelineConfig:
    """Configuration for a pipeline execution."""
    pipeline_type: str              # "design", "implement", "fix", "test"
    stages: List[str]               # Ordered list of stage names
    exit_after: Optional[str] = None  # Early exit after this stage
    supervised: bool = False        # Pause for approval between stages
    iteration_enabled: bool = True  # Allow feedback/revision cycles
    max_iterations_per_stage: int = 3
    timeout_seconds: int = 3600     # 1 hour default


class PipelineController:
    """
    Orchestrates full request→delivery lifecycle.
    
    This is THE entry point for all autonomous development workflows.
    Human intervention only occurs on escalation or in supervised mode.
    
    Usage:
        controller = PipelineController(project_path)
        result = controller.execute(
            user_request="Add OAuth2 authentication",
            pipeline_type="implement"
        )
    """
    
    def __init__(
        self,
        project_path: Path,
        escalation_handler: Optional["EscalationHandler"] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the pipeline controller.
        
        Args:
            project_path: Root path of the project
            escalation_handler: Handler for human escalations
            config_override: Override default configuration values
        """
        self.project_path = Path(project_path)
        self.escalation_handler = escalation_handler or DefaultEscalationHandler()
        self.config_override = config_override or {}
        
        # Initialize subsystems
        self.state_store = PipelineStateStore(
            self.project_path / ".agentforge" / "pipeline"
        )
        self.stage_registry = StageExecutorRegistry()
        self.artifact_validator = ArtifactValidator()
        self.pipeline_templates = PipelineTemplateLoader(self.project_path)
        
        # Register default stages (can be overridden)
        self._register_default_stages()
    
    def execute(
        self,
        user_request: str,
        pipeline_type: str = "implement",
        context: Optional[Dict[str, Any]] = None,
        resume_pipeline_id: Optional[str] = None,
    ) -> PipelineResult:
        """
        Execute a full pipeline from request to delivery.
        
        This is THE primary entry point for all pipeline execution.
        
        Args:
            user_request: Natural language description of what to build
            pipeline_type: Type of pipeline ("design", "implement", "fix", "test")
            context: Additional context (e.g., existing spec, target files)
            resume_pipeline_id: Resume a paused pipeline instead of starting new
            
        Returns:
            PipelineResult with success status and deliverable
        """
        start_time = datetime.now(timezone.utc)
        
        # Resume existing or create new pipeline
        if resume_pipeline_id:
            pipeline_state = self.state_store.load(resume_pipeline_id)
            if not pipeline_state:
                return PipelineResult(
                    success=False,
                    pipeline_id=resume_pipeline_id,
                    status=PipelineStatus.FAILED,
                    error=f"Pipeline {resume_pipeline_id} not found"
                )
            logger.info(f"Resuming pipeline {resume_pipeline_id}")
        else:
            pipeline_state = self._create_pipeline(
                user_request=user_request,
                pipeline_type=pipeline_type,
                context=context or {}
            )
            logger.info(f"Created pipeline {pipeline_state.pipeline_id}")
        
        # Execute pipeline stages
        try:
            result = self._execute_pipeline(pipeline_state)
        except Exception as e:
            logger.exception(f"Pipeline execution failed: {e}")
            pipeline_state.status = PipelineStatus.FAILED
            pipeline_state.error = str(e)
            self.state_store.save(pipeline_state)
            
            result = PipelineResult(
                success=False,
                pipeline_id=pipeline_state.pipeline_id,
                status=PipelineStatus.FAILED,
                error=str(e),
                stages_completed=pipeline_state.completed_stages
            )
        
        # Record duration
        result.total_duration_seconds = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        
        return result
    
    def _create_pipeline(
        self,
        user_request: str,
        pipeline_type: str,
        context: Dict[str, Any],
    ) -> "PipelineState":
        """Create a new pipeline instance."""
        # Load pipeline template
        config = self.pipeline_templates.load(pipeline_type)
        
        # Apply overrides
        if self.config_override:
            config = self._apply_config_override(config, self.config_override)
        
        # Create state
        pipeline_state = PipelineState(
            pipeline_id=self._generate_pipeline_id(),
            pipeline_type=pipeline_type,
            config=config,
            user_request=user_request,
            context=context,
            status=PipelineStatus.PENDING,
            current_stage_index=0,
            created_at=datetime.now(timezone.utc),
        )
        
        # Persist
        self.state_store.save(pipeline_state)
        
        return pipeline_state
    
    def _execute_pipeline(self, state: "PipelineState") -> PipelineResult:
        """Execute pipeline stages in sequence."""
        state.status = PipelineStatus.RUNNING
        self.state_store.save(state)
        
        stages = state.config.stages
        current_artifact = {"original_request": state.user_request, **state.context}
        
        # Resume from current stage if resuming
        start_index = state.current_stage_index
        
        for i in range(start_index, len(stages)):
            stage_name = stages[i]
            state.current_stage_index = i
            state.current_stage = stage_name
            self.state_store.save(state)
            
            logger.info(f"Executing stage: {stage_name} ({i+1}/{len(stages)})")
            
            # Execute stage with retry/escalation logic
            stage_result = self._execute_stage_with_recovery(
                state=state,
                stage_name=stage_name,
                input_artifact=current_artifact
            )
            
            # Handle escalation
            if stage_result.escalated:
                resolution = self._handle_escalation(state, stage_result)
                
                if resolution.abort:
                    state.status = PipelineStatus.ABORTED
                    self.state_store.save(state)
                    return PipelineResult(
                        success=False,
                        pipeline_id=state.pipeline_id,
                        status=PipelineStatus.ABORTED,
                        current_stage=stage_name,
                        error="User aborted after escalation"
                    )
                
                # Retry with resolution context
                current_artifact["_resolution"] = resolution.context
                stage_result = self._execute_stage_with_recovery(
                    state=state,
                    stage_name=stage_name,
                    input_artifact=current_artifact
                )
            
            # Handle failure
            if not stage_result.success:
                state.status = PipelineStatus.FAILED
                state.error = stage_result.error
                self.state_store.save(state)
                
                return PipelineResult(
                    success=False,
                    pipeline_id=state.pipeline_id,
                    status=PipelineStatus.FAILED,
                    current_stage=stage_name,
                    error=stage_result.error,
                    stages_completed=state.completed_stages
                )
            
            # Validate artifact for next stage
            if i < len(stages) - 1:
                next_stage = stages[i + 1]
                validation = self.artifact_validator.validate_transition(
                    from_stage=stage_name,
                    to_stage=next_stage,
                    artifact=stage_result.artifact
                )
                
                if not validation.valid:
                    # Attempt self-healing
                    healed = self._attempt_artifact_healing(
                        state, stage_name, stage_result.artifact, validation
                    )
                    if not healed:
                        state.status = PipelineStatus.FAILED
                        state.error = f"Artifact validation failed: {validation.errors}"
                        self.state_store.save(state)
                        
                        return PipelineResult(
                            success=False,
                            pipeline_id=state.pipeline_id,
                            status=PipelineStatus.FAILED,
                            current_stage=stage_name,
                            error=f"Artifact validation failed: {validation.errors}"
                        )
            
            # Supervised mode: pause for approval
            if state.config.supervised and i < len(stages) - 1:
                state.status = PipelineStatus.AWAITING_APPROVAL
                state.pending_artifact = stage_result.artifact
                self.state_store.save(state)
                
                approval = self.escalation_handler.request_approval(
                    pipeline_id=state.pipeline_id,
                    stage=stage_name,
                    artifact=stage_result.artifact
                )
                
                if not approval.approved:
                    if approval.feedback:
                        # Iterate with feedback
                        current_artifact["_feedback"] = approval.feedback
                        continue  # Re-run same stage
                    else:
                        state.status = PipelineStatus.ABORTED
                        self.state_store.save(state)
                        return PipelineResult(
                            success=False,
                            pipeline_id=state.pipeline_id,
                            status=PipelineStatus.ABORTED,
                            error="User rejected stage output"
                        )
                
                state.status = PipelineStatus.RUNNING
            
            # Record completion
            state.completed_stages.append(stage_name)
            state.stage_artifacts[stage_name] = stage_result.artifact
            current_artifact = stage_result.artifact
            self.state_store.save(state)
            
            # Early exit check
            if state.config.exit_after == stage_name:
                logger.info(f"Early exit after {stage_name} as configured")
                break
        
        # Pipeline complete
        state.status = PipelineStatus.COMPLETED
        state.completed_at = datetime.now(timezone.utc)
        self.state_store.save(state)
        
        return PipelineResult(
            success=True,
            pipeline_id=state.pipeline_id,
            status=PipelineStatus.COMPLETED,
            deliverable=current_artifact,
            stages_completed=state.completed_stages
        )
    
    def _execute_stage_with_recovery(
        self,
        state: "PipelineState",
        stage_name: str,
        input_artifact: Dict[str, Any],
    ) -> StageResult:
        """Execute a stage with retry and recovery logic."""
        executor = self.stage_registry.get(stage_name)
        if not executor:
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error=f"No executor registered for stage: {stage_name}"
            )
        
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                start = datetime.now(timezone.utc)
                result = executor.execute(
                    input_artifact=input_artifact,
                    pipeline_state=state,
                    project_path=self.project_path
                )
                result.duration_seconds = (
                    datetime.now(timezone.utc) - start
                ).total_seconds()
                
                if result.success or result.escalated:
                    return result
                
                last_error = result.error
                logger.warning(
                    f"Stage {stage_name} attempt {attempt + 1} failed: {last_error}"
                )
                
            except Exception as e:
                last_error = str(e)
                logger.exception(
                    f"Stage {stage_name} attempt {attempt + 1} exception: {e}"
                )
        
        return StageResult(
            stage_name=stage_name,
            status=StageStatus.FAILED,
            error=f"Stage failed after {max_retries + 1} attempts: {last_error}"
        )
    
    def _handle_escalation(
        self,
        state: "PipelineState",
        stage_result: StageResult,
    ) -> "EscalationResolution":
        """Handle stage escalation by requesting human input."""
        state.status = PipelineStatus.PAUSED
        self.state_store.save(state)
        
        return self.escalation_handler.wait_for_resolution(
            pipeline_id=state.pipeline_id,
            stage=stage_result.stage_name,
            issue=stage_result.escalation_reason,
            context=stage_result.artifact
        )
    
    def _attempt_artifact_healing(
        self,
        state: "PipelineState",
        stage_name: str,
        artifact: Dict[str, Any],
        validation: "ValidationResult",
    ) -> bool:
        """Attempt to fix artifact validation errors."""
        # TODO: Implement artifact healing via LLM
        # For now, just log and fail
        logger.error(
            f"Artifact healing not implemented. "
            f"Stage {stage_name} produced invalid artifact: {validation.errors}"
        )
        return False
    
    def _apply_config_override(
        self,
        config: PipelineConfig,
        overrides: Dict[str, Any],
    ) -> PipelineConfig:
        """Apply configuration overrides."""
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    
    def _generate_pipeline_id(self) -> str:
        """Generate unique pipeline ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        import uuid
        short_uuid = uuid.uuid4().hex[:8]
        return f"PL-{timestamp}-{short_uuid}"
    
    def _register_default_stages(self) -> None:
        """Register default stage executors."""
        # These will be implemented in subsequent specs
        # For now, register placeholders
        pass
    
    # --- Public API for external control ---
    
    def get_status(self, pipeline_id: str) -> Optional["PipelineState"]:
        """Get current status of a pipeline."""
        return self.state_store.load(pipeline_id)
    
    def list_pipelines(
        self,
        status: Optional[PipelineStatus] = None,
        limit: int = 20,
    ) -> List["PipelineState"]:
        """List pipelines, optionally filtered by status."""
        return self.state_store.list(status=status, limit=limit)
    
    def abort(self, pipeline_id: str, reason: str = "User requested") -> bool:
        """Abort a running or paused pipeline."""
        state = self.state_store.load(pipeline_id)
        if not state:
            return False
        
        if state.status in (PipelineStatus.COMPLETED, PipelineStatus.ABORTED):
            return False
        
        state.status = PipelineStatus.ABORTED
        state.error = reason
        state.completed_at = datetime.now(timezone.utc)
        self.state_store.save(state)
        return True
    
    def provide_feedback(
        self,
        pipeline_id: str,
        feedback: str,
    ) -> bool:
        """Provide feedback to a paused pipeline."""
        state = self.state_store.load(pipeline_id)
        if not state or state.status != PipelineStatus.AWAITING_APPROVAL:
            return False
        
        state.pending_feedback = feedback
        self.state_store.save(state)
        return True
    
    def approve(self, pipeline_id: str) -> bool:
        """Approve current stage and continue pipeline."""
        state = self.state_store.load(pipeline_id)
        if not state or state.status != PipelineStatus.AWAITING_APPROVAL:
            return False
        
        state.status = PipelineStatus.RUNNING
        state.approved_stages.append(state.current_stage)
        self.state_store.save(state)
        
        # Resume execution
        self.execute(
            user_request=state.user_request,
            resume_pipeline_id=pipeline_id
        )
        return True
```

### 2.2 PipelineState

State object persisted between executions.

```python
# src/agentforge/core/pipeline/state.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .controller import PipelineStatus, PipelineConfig


@dataclass
class PipelineState:
    """
    Complete state of a pipeline execution.
    
    This is persisted to disk and can be loaded to resume execution.
    """
    # Identity
    pipeline_id: str
    pipeline_type: str
    
    # Configuration
    config: PipelineConfig
    
    # Request
    user_request: str
    context: Dict[str, Any]
    
    # Status
    status: PipelineStatus
    current_stage_index: int
    current_stage: Optional[str] = None
    error: Optional[str] = None
    
    # Progress
    completed_stages: List[str] = field(default_factory=list)
    approved_stages: List[str] = field(default_factory=list)
    stage_artifacts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Iteration
    iteration_count: Dict[str, int] = field(default_factory=dict)
    pending_feedback: Optional[str] = None
    pending_artifact: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metrics
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            "pipeline_id": self.pipeline_id,
            "pipeline_type": self.pipeline_type,
            "config": {
                "pipeline_type": self.config.pipeline_type,
                "stages": self.config.stages,
                "exit_after": self.config.exit_after,
                "supervised": self.config.supervised,
                "iteration_enabled": self.config.iteration_enabled,
                "max_iterations_per_stage": self.config.max_iterations_per_stage,
                "timeout_seconds": self.config.timeout_seconds,
            },
            "user_request": self.user_request,
            "context": self.context,
            "status": self.status.value,
            "current_stage_index": self.current_stage_index,
            "current_stage": self.current_stage,
            "error": self.error,
            "completed_stages": self.completed_stages,
            "approved_stages": self.approved_stages,
            "stage_artifacts": self.stage_artifacts,
            "iteration_count": self.iteration_count,
            "pending_feedback": self.pending_feedback,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": self.total_cost_usd,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        """Deserialize from dictionary."""
        config_data = data["config"]
        config = PipelineConfig(
            pipeline_type=config_data["pipeline_type"],
            stages=config_data["stages"],
            exit_after=config_data.get("exit_after"),
            supervised=config_data.get("supervised", False),
            iteration_enabled=config_data.get("iteration_enabled", True),
            max_iterations_per_stage=config_data.get("max_iterations_per_stage", 3),
            timeout_seconds=config_data.get("timeout_seconds", 3600),
        )
        
        return cls(
            pipeline_id=data["pipeline_id"],
            pipeline_type=data["pipeline_type"],
            config=config,
            user_request=data["user_request"],
            context=data.get("context", {}),
            status=PipelineStatus(data["status"]),
            current_stage_index=data["current_stage_index"],
            current_stage=data.get("current_stage"),
            error=data.get("error"),
            completed_stages=data.get("completed_stages", []),
            approved_stages=data.get("approved_stages", []),
            stage_artifacts=data.get("stage_artifacts", {}),
            iteration_count=data.get("iteration_count", {}),
            pending_feedback=data.get("pending_feedback"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            total_tokens_used=data.get("total_tokens_used", 0),
            total_cost_usd=data.get("total_cost_usd", 0.0),
        )
```

### 2.3 PipelineStateStore

Persistence layer for pipeline state.

```python
# src/agentforge/core/pipeline/state_store.py

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml

from .controller import PipelineStatus
from .state import PipelineState

logger = logging.getLogger(__name__)


class PipelineStateStore:
    """
    Persists pipeline state to disk.
    
    Storage structure:
        .agentforge/pipeline/
        ├── active/
        │   └── PL-20260102-abc123.yaml
        ├── completed/
        │   └── PL-20260101-def456.yaml
        └── index.yaml
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize state store.
        
        Args:
            base_path: Base directory for pipeline state storage
        """
        self.base_path = Path(base_path)
        self.active_path = self.base_path / "active"
        self.completed_path = self.base_path / "completed"
        self.index_path = self.base_path / "index.yaml"
        
        # Ensure directories exist
        self.active_path.mkdir(parents=True, exist_ok=True)
        self.completed_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, state: PipelineState) -> None:
        """Save pipeline state to disk."""
        state.updated_at = datetime.now(timezone.utc)
        
        # Determine storage location based on status
        if state.status in (PipelineStatus.COMPLETED, PipelineStatus.ABORTED, PipelineStatus.FAILED):
            storage_path = self.completed_path
        else:
            storage_path = self.active_path
        
        file_path = storage_path / f"{state.pipeline_id}.yaml"
        
        with open(file_path, "w") as f:
            yaml.dump(state.to_dict(), f, default_flow_style=False, sort_keys=False)
        
        # Update index
        self._update_index(state)
        
        logger.debug(f"Saved pipeline state: {state.pipeline_id}")
    
    def load(self, pipeline_id: str) -> Optional[PipelineState]:
        """Load pipeline state from disk."""
        # Check active first, then completed
        for storage_path in [self.active_path, self.completed_path]:
            file_path = storage_path / f"{pipeline_id}.yaml"
            if file_path.exists():
                with open(file_path) as f:
                    data = yaml.safe_load(f)
                return PipelineState.from_dict(data)
        
        return None
    
    def delete(self, pipeline_id: str) -> bool:
        """Delete pipeline state."""
        for storage_path in [self.active_path, self.completed_path]:
            file_path = storage_path / f"{pipeline_id}.yaml"
            if file_path.exists():
                file_path.unlink()
                self._remove_from_index(pipeline_id)
                return True
        return False
    
    def list(
        self,
        status: Optional[PipelineStatus] = None,
        limit: int = 20,
    ) -> List[PipelineState]:
        """List pipelines, optionally filtered by status."""
        pipelines = []
        
        # Load from active and completed
        for storage_path in [self.active_path, self.completed_path]:
            for file_path in storage_path.glob("*.yaml"):
                try:
                    with open(file_path) as f:
                        data = yaml.safe_load(f)
                    state = PipelineState.from_dict(data)
                    
                    if status is None or state.status == status:
                        pipelines.append(state)
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
        
        # Sort by created_at descending
        pipelines.sort(key=lambda p: p.created_at, reverse=True)
        
        return pipelines[:limit]
    
    def get_active_count(self) -> int:
        """Get count of active (non-terminal) pipelines."""
        return len(list(self.active_path.glob("*.yaml")))
    
    def _update_index(self, state: PipelineState) -> None:
        """Update the index file with pipeline metadata."""
        index = self._load_index()
        
        index[state.pipeline_id] = {
            "status": state.status.value,
            "pipeline_type": state.pipeline_type,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
            "current_stage": state.current_stage,
        }
        
        with open(self.index_path, "w") as f:
            yaml.dump(index, f, default_flow_style=False)
    
    def _remove_from_index(self, pipeline_id: str) -> None:
        """Remove pipeline from index."""
        index = self._load_index()
        index.pop(pipeline_id, None)
        
        with open(self.index_path, "w") as f:
            yaml.dump(index, f, default_flow_style=False)
    
    def _load_index(self) -> dict:
        """Load index file."""
        if self.index_path.exists():
            with open(self.index_path) as f:
                return yaml.safe_load(f) or {}
        return {}
```

---

## 3. Supporting Components

### 3.1 StageExecutorRegistry

Registry for stage executors.

```python
# src/agentforge/core/pipeline/registry.py

from typing import Callable, Dict, Optional, Type
import logging

logger = logging.getLogger(__name__)


class StageExecutorRegistry:
    """
    Registry for stage executors.
    
    Allows dynamic registration of stage implementations.
    """
    
    def __init__(self):
        self._executors: Dict[str, "StageExecutor"] = {}
        self._factories: Dict[str, Callable[[], "StageExecutor"]] = {}
    
    def register(
        self,
        stage_name: str,
        executor: "StageExecutor",
    ) -> None:
        """Register a stage executor instance."""
        self._executors[stage_name] = executor
        logger.debug(f"Registered executor for stage: {stage_name}")
    
    def register_factory(
        self,
        stage_name: str,
        factory: Callable[[], "StageExecutor"],
    ) -> None:
        """Register a factory for lazy executor creation."""
        self._factories[stage_name] = factory
        logger.debug(f"Registered factory for stage: {stage_name}")
    
    def get(self, stage_name: str) -> Optional["StageExecutor"]:
        """Get executor for a stage."""
        # Check direct registration first
        if stage_name in self._executors:
            return self._executors[stage_name]
        
        # Try factory
        if stage_name in self._factories:
            executor = self._factories[stage_name]()
            self._executors[stage_name] = executor
            return executor
        
        return None
    
    def list_stages(self) -> list:
        """List all registered stage names."""
        return sorted(set(self._executors.keys()) | set(self._factories.keys()))
    
    def has_stage(self, stage_name: str) -> bool:
        """Check if a stage is registered."""
        return stage_name in self._executors or stage_name in self._factories
```

### 3.2 EscalationHandler

Interface for handling escalations.

```python
# src/agentforge/core/pipeline/escalation.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class EscalationResolution:
    """Resolution from human for an escalation."""
    abort: bool = False
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class ApprovalResult:
    """Result of approval request."""
    approved: bool
    feedback: Optional[str] = None


class EscalationHandler(ABC):
    """
    Abstract base for handling escalations.
    
    Implementations may be CLI-based, web-based, or queue-based.
    """
    
    @abstractmethod
    def wait_for_resolution(
        self,
        pipeline_id: str,
        stage: str,
        issue: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EscalationResolution:
        """
        Wait for human to resolve an escalation.
        
        This may block indefinitely or return a default after timeout.
        """
        pass
    
    @abstractmethod
    def request_approval(
        self,
        pipeline_id: str,
        stage: str,
        artifact: Dict[str, Any],
    ) -> ApprovalResult:
        """
        Request human approval for stage output.
        
        Used in supervised mode.
        """
        pass


class DefaultEscalationHandler(EscalationHandler):
    """
    Default escalation handler that writes to files.
    
    For CLI usage, escalations are written to .agentforge/escalations/
    and the process waits for a resolution file.
    """
    
    def __init__(self, timeout_seconds: int = 86400):
        self.timeout_seconds = timeout_seconds
    
    def wait_for_resolution(
        self,
        pipeline_id: str,
        stage: str,
        issue: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EscalationResolution:
        """Write escalation and wait for resolution file."""
        import time
        import yaml
        from pathlib import Path
        from datetime import datetime, timezone
        
        escalation_dir = Path(".agentforge/escalations")
        escalation_dir.mkdir(parents=True, exist_ok=True)
        
        escalation_id = f"ESC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        escalation_file = escalation_dir / f"{escalation_id}.yaml"
        resolution_file = escalation_dir / f"{escalation_id}.resolution.yaml"
        
        # Write escalation
        with open(escalation_file, "w") as f:
            yaml.dump({
                "escalation_id": escalation_id,
                "pipeline_id": pipeline_id,
                "stage": stage,
                "issue": issue,
                "context": context,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending",
            }, f, default_flow_style=False)
        
        print(f"\n⚠️  ESCALATION REQUIRED")
        print(f"   Pipeline: {pipeline_id}")
        print(f"   Stage: {stage}")
        print(f"   Issue: {issue}")
        print(f"\n   To resolve, create: {resolution_file}")
        print(f"   With: abort: false/true and context: {{...}}")
        
        # Wait for resolution
        start = time.time()
        while time.time() - start < self.timeout_seconds:
            if resolution_file.exists():
                with open(resolution_file) as f:
                    resolution = yaml.safe_load(f)
                return EscalationResolution(
                    abort=resolution.get("abort", False),
                    context=resolution.get("context", {})
                )
            time.sleep(5)
        
        # Timeout - abort
        return EscalationResolution(abort=True)
    
    def request_approval(
        self,
        pipeline_id: str,
        stage: str,
        artifact: Dict[str, Any],
    ) -> ApprovalResult:
        """Request approval via CLI prompt."""
        import yaml
        
        print(f"\n📋 APPROVAL REQUIRED")
        print(f"   Pipeline: {pipeline_id}")
        print(f"   Stage: {stage}")
        print(f"\n   Artifact preview:")
        print(yaml.dump(artifact, default_flow_style=False)[:500])
        
        response = input("\n   Approve? [y/n/feedback]: ").strip().lower()
        
        if response == "y":
            return ApprovalResult(approved=True)
        elif response == "n":
            return ApprovalResult(approved=False)
        else:
            return ApprovalResult(approved=False, feedback=response)
```

### 3.3 ArtifactValidator

Validates artifacts between stages.

```python
# src/agentforge/core/pipeline/validator.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of artifact validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ArtifactValidator:
    """
    Validates artifacts meet stage transition requirements.
    
    Each stage-to-stage transition has required fields and optional
    schema validation.
    """
    
    # Required fields for each transition
    TRANSITION_REQUIREMENTS = {
        ("intake", "clarify"): ["request_id", "detected_scope", "initial_questions"],
        ("intake", "analyze"): ["request_id", "detected_scope"],
        ("clarify", "analyze"): ["request_id", "clarified_requirements"],
        ("analyze", "spec"): ["request_id", "analysis", "components"],
        ("spec", "red"): ["spec_id", "components", "test_cases"],
        ("red", "green"): ["spec_id", "test_files", "test_results"],
        ("green", "refactor"): ["spec_id", "implementation_files"],
        ("refactor", "deliver"): ["spec_id", "final_files"],
    }
    
    def validate_transition(
        self,
        from_stage: str,
        to_stage: str,
        artifact: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate artifact for stage transition.
        
        Args:
            from_stage: Source stage name
            to_stage: Target stage name
            artifact: Artifact to validate
            
        Returns:
            ValidationResult with valid flag and any errors
        """
        errors = []
        warnings = []
        
        # Check required fields
        key = (from_stage, to_stage)
        required_fields = self.TRANSITION_REQUIREMENTS.get(key, [])
        
        for field_name in required_fields:
            if field_name not in artifact:
                errors.append(f"Missing required field: {field_name}")
            elif artifact[field_name] is None:
                warnings.append(f"Field {field_name} is None")
        
        # Stage-specific validation
        if from_stage == "spec":
            spec_errors = self._validate_spec_artifact(artifact)
            errors.extend(spec_errors)
        
        if from_stage == "red":
            test_errors = self._validate_test_artifact(artifact)
            errors.extend(test_errors)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_spec_artifact(self, artifact: Dict[str, Any]) -> List[str]:
        """Validate specification artifact."""
        errors = []
        
        components = artifact.get("components", [])
        if not components:
            errors.append("Spec must have at least one component")
        
        for i, comp in enumerate(components):
            if "name" not in comp:
                errors.append(f"Component {i} missing 'name'")
            if "type" not in comp:
                errors.append(f"Component {i} missing 'type'")
        
        return errors
    
    def _validate_test_artifact(self, artifact: Dict[str, Any]) -> List[str]:
        """Validate test (RED phase) artifact."""
        errors = []
        
        test_files = artifact.get("test_files", [])
        if not test_files:
            errors.append("RED phase must produce at least one test file")
        
        test_results = artifact.get("test_results", {})
        if test_results.get("passed", 0) > 0:
            errors.append("RED phase tests should fail initially")
        
        return errors
```

---

## 4. Directory Structure

```
src/agentforge/core/pipeline/
├── __init__.py
├── controller.py          # PipelineController, PipelineConfig, results
├── state.py               # PipelineState
├── state_store.py         # PipelineStateStore
├── registry.py            # StageExecutorRegistry
├── escalation.py          # EscalationHandler, DefaultEscalationHandler
├── validator.py           # ArtifactValidator
└── templates.py           # PipelineTemplateLoader (Stage 9)
```

---

## 5. Test Specification

### 5.1 Unit Tests

```python
# tests/unit/pipeline/test_controller.py

class TestPipelineController:
    """Unit tests for PipelineController."""
    
    def test_create_pipeline_generates_unique_id(self, tmp_path):
        """Pipeline IDs should be unique."""
        
    def test_execute_runs_all_stages_in_order(self, tmp_path, mock_stages):
        """Stages execute in configured order."""
        
    def test_execute_stops_on_stage_failure(self, tmp_path, failing_stage):
        """Pipeline stops when a stage fails."""
        
    def test_execute_handles_escalation(self, tmp_path, escalating_stage):
        """Escalation triggers handler and can resume."""
        
    def test_resume_continues_from_current_stage(self, tmp_path):
        """Resuming a paused pipeline continues from correct stage."""
        
    def test_supervised_mode_pauses_between_stages(self, tmp_path):
        """Supervised mode requests approval between stages."""
        
    def test_early_exit_stops_at_configured_stage(self, tmp_path):
        """exit_after config stops pipeline at specified stage."""
        
    def test_abort_terminates_running_pipeline(self, tmp_path):
        """abort() terminates and records reason."""


class TestPipelineState:
    """Unit tests for PipelineState."""
    
    def test_to_dict_serializes_all_fields(self):
        """to_dict produces complete serialization."""
        
    def test_from_dict_deserializes_correctly(self):
        """from_dict restores state exactly."""
        
    def test_round_trip_preserves_state(self):
        """to_dict -> from_dict preserves all data."""


class TestPipelineStateStore:
    """Unit tests for PipelineStateStore."""
    
    def test_save_creates_file(self, tmp_path):
        """save() creates YAML file."""
        
    def test_load_returns_saved_state(self, tmp_path):
        """load() returns previously saved state."""
        
    def test_list_returns_pipelines_by_status(self, tmp_path):
        """list() filters by status correctly."""
        
    def test_completed_pipelines_move_to_completed_dir(self, tmp_path):
        """Completed pipelines are moved to completed/ directory."""


class TestArtifactValidator:
    """Unit tests for ArtifactValidator."""
    
    def test_validates_required_fields(self):
        """Missing required fields produce errors."""
        
    def test_spec_artifact_requires_components(self):
        """Spec artifacts must have components."""
        
    def test_red_artifact_requires_failing_tests(self):
        """RED phase artifacts should have failing tests."""
```

### 5.2 Integration Tests

```python
# tests/integration/pipeline/test_pipeline_execution.py

class TestPipelineExecution:
    """Integration tests for full pipeline execution."""
    
    def test_simple_pipeline_completes(self, tmp_path, mock_llm):
        """A simple 2-stage pipeline completes successfully."""
        
    def test_pipeline_persists_across_restart(self, tmp_path):
        """Pipeline state survives process restart."""
        
    def test_escalation_workflow(self, tmp_path):
        """Full escalation -> resolution -> resume workflow."""
```

---

## 6. Success Criteria

1. **Functional:**
   - [ ] PipelineController.execute() runs stages in order
   - [ ] State persists to disk and survives restart
   - [ ] Resume continues from correct stage
   - [ ] Escalation pauses and can be resolved
   - [ ] Supervised mode requests approval

2. **Quality:**
   - [ ] 90%+ test coverage for core module
   - [ ] All state transitions logged
   - [ ] Clear error messages for failures

3. **Performance:**
   - [ ] State save/load < 100ms
   - [ ] No memory leaks in long-running pipelines

---

## 7. Dependencies

- **Existing:** None (new module)
- **Future:** Stage executors (Stage 2-7), CLI commands (Stage 8), Configuration (Stage 9)

---

## 8. Open Questions

1. Should pipeline state include full artifact history or just latest?
2. How to handle very large artifacts (>1MB)?
3. Should escalation timeout be configurable per-stage?

---

*Next: Stage 2 - Stage Executor Interface*
