# @spec_file: .agentforge/specs/harness-minimal-context-v1.yaml
# @spec_id: harness-minimal-context-v1
# @component_id: harness-minimal_context-state_store
# @test_path: tests/unit/harness/test_minimal_context.py

"""
Task State Store
================

Manages task state persistence to disk.
All agent state lives here - the agent has no memory except what's in the state store.

Directory structure:
.agentforge/tasks/{task_id}/
├── task.yaml                 # Immutable: goal, success criteria
├── state.yaml                # Mutable: current phase, status, verification
├── actions.yaml              # Append-only: complete log of all actions
├── working_memory.yaml       # Rolling: last N actions for context
└── artifacts/
    ├── inputs/               # Verified inputs (spec, violation, etc.)
    ├── outputs/              # Verified outputs from each phase
    └── snapshots/            # File states before/after changes
"""

import uuid
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskPhase(str, Enum):
    """Task execution phases."""
    INIT = "init"
    ANALYZE = "analyze"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    COMMIT = "commit"
    COMPLETE = "complete"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class ActionRecord:
    """Record of an action taken during execution."""
    step: int
    action: str
    target: Optional[str]
    parameters: Dict[str, Any]
    result: str  # "success", "failure", "partial"
    summary: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action,
            "target": self.target,
            "parameters": self.parameters,
            "result": self.result,
            "summary": self.summary,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionRecord":
        return cls(
            step=data["step"],
            action=data["action"],
            target=data.get("target"),
            parameters=data.get("parameters", {}),
            result=data["result"],
            summary=data["summary"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration_ms=data.get("duration_ms"),
            error=data.get("error"),
        )


@dataclass
class VerificationStatus:
    """Current verification status for a task."""
    checks_passing: int = 0
    checks_failing: int = 0
    tests_passing: bool = False
    ready_for_completion: bool = False
    last_check_time: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checks_passing": self.checks_passing,
            "checks_failing": self.checks_failing,
            "tests_passing": self.tests_passing,
            "ready_for_completion": self.ready_for_completion,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationStatus":
        return cls(
            checks_passing=data.get("checks_passing", 0),
            checks_failing=data.get("checks_failing", 0),
            tests_passing=data.get("tests_passing", False),
            ready_for_completion=data.get("ready_for_completion", False),
            last_check_time=datetime.fromisoformat(data["last_check_time"]) if data.get("last_check_time") else None,
            details=data.get("details", {}),
        )


@dataclass
class TaskState:
    """Complete state for a task."""
    # Immutable (from task.yaml)
    task_id: str
    task_type: str  # "fix_violation", "implement_feature", etc.
    goal: str
    success_criteria: List[str]
    constraints: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Mutable (from state.yaml)
    phase: TaskPhase = TaskPhase.INIT
    current_step: int = 0
    verification: VerificationStatus = field(default_factory=VerificationStatus)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    # Task-type specific data
    context_data: Dict[str, Any] = field(default_factory=dict)

    def to_task_dict(self) -> Dict[str, Any]:
        """Serialize immutable task data."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "goal": self.goal,
            "success_criteria": self.success_criteria,
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
        }

    def to_state_dict(self) -> Dict[str, Any]:
        """Serialize mutable state data."""
        return {
            "phase": self.phase.value,
            "current_step": self.current_step,
            "verification": self.verification.to_dict(),
            "last_updated": self.last_updated.isoformat(),
            "error": self.error,
            "context_data": self.context_data,
        }


class TaskStateStore:
    """
    Manages task state on disk.

    All agent state persists here. The agent has no memory except what's
    loaded from the state store at the start of each step.
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.tasks_dir = self.project_path / ".agentforge" / "tasks"

    def _task_dir(self, task_id: str) -> Path:
        return self.tasks_dir / task_id

    def create_task(
        self,
        task_type: str,
        goal: str,
        success_criteria: List[str],
        constraints: Optional[List[str]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
    ) -> TaskState:
        """
        Create a new task and persist it.

        Args:
            task_type: Type of task (e.g., "fix_violation")
            goal: Single sentence goal description
            success_criteria: List of measurable criteria
            constraints: Optional constraints
            context_data: Task-type specific data
            task_id: Optional specific ID (default: auto-generated)

        Returns:
            Created TaskState
        """
        task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        task_dir = self._task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)

        state = TaskState(
            task_id=task_id,
            task_type=task_type,
            goal=goal,
            success_criteria=success_criteria,
            constraints=constraints or [],
            context_data=context_data or {},
        )

        # Create artifacts directories
        (task_dir / "artifacts" / "inputs").mkdir(parents=True, exist_ok=True)
        (task_dir / "artifacts" / "outputs").mkdir(parents=True, exist_ok=True)
        (task_dir / "artifacts" / "snapshots").mkdir(parents=True, exist_ok=True)

        # Write task.yaml (immutable)
        with open(task_dir / "task.yaml", "w") as f:
            yaml.dump(state.to_task_dict(), f, default_flow_style=False)

        # Write state.yaml (mutable)
        self._save_state(state)

        # Initialize actions.yaml
        with open(task_dir / "actions.yaml", "w") as f:
            yaml.dump({"actions": []}, f, default_flow_style=False)

        # Initialize working_memory.yaml
        with open(task_dir / "working_memory.yaml", "w") as f:
            yaml.dump({"max_items": 5, "items": []}, f, default_flow_style=False)

        return state

    def load(self, task_id: str) -> Optional[TaskState]:
        """
        Load task state from disk.

        Args:
            task_id: Task identifier

        Returns:
            TaskState if exists, None otherwise
        """
        task_dir = self._task_dir(task_id)
        if not task_dir.exists():
            return None

        # Load task.yaml
        with open(task_dir / "task.yaml") as f:
            task_data = yaml.safe_load(f)

        # Load state.yaml
        with open(task_dir / "state.yaml") as f:
            state_data = yaml.safe_load(f)

        return TaskState(
            task_id=task_data["task_id"],
            task_type=task_data["task_type"],
            goal=task_data["goal"],
            success_criteria=task_data["success_criteria"],
            constraints=task_data.get("constraints", []),
            created_at=datetime.fromisoformat(task_data["created_at"]),
            phase=TaskPhase(state_data["phase"]),
            current_step=state_data["current_step"],
            verification=VerificationStatus.from_dict(state_data.get("verification", {})),
            last_updated=datetime.fromisoformat(state_data["last_updated"]),
            error=state_data.get("error"),
            context_data=state_data.get("context_data", {}),
        )

    def _save_state(self, state: TaskState) -> None:
        """Save mutable state to disk."""
        state.last_updated = datetime.utcnow()
        task_dir = self._task_dir(state.task_id)
        with open(task_dir / "state.yaml", "w") as f:
            yaml.dump(state.to_state_dict(), f, default_flow_style=False)

    def update_phase(self, task_id: str, phase: TaskPhase) -> None:
        """Update task phase."""
        state = self.load(task_id)
        if state:
            state.phase = phase
            self._save_state(state)

    def increment_step(self, task_id: str) -> int:
        """Increment step counter and return new value."""
        state = self.load(task_id)
        if state:
            state.current_step += 1
            self._save_state(state)
            return state.current_step
        return 0

    def record_action(
        self,
        task_id: str,
        action: str,
        target: Optional[str],
        parameters: Dict[str, Any],
        result: str,
        summary: str,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> ActionRecord:
        """
        Record an action to the append-only actions log.

        Args:
            task_id: Task identifier
            action: Action name
            target: Target file/resource
            parameters: Action parameters
            result: "success", "failure", or "partial"
            summary: One-line summary
            duration_ms: Execution duration
            error: Error message if failed

        Returns:
            Created ActionRecord
        """
        task_dir = self._task_dir(task_id)
        state = self.load(task_id)
        if not state:
            raise ValueError(f"Task not found: {task_id}")

        record = ActionRecord(
            step=state.current_step,
            action=action,
            target=target,
            parameters=parameters,
            result=result,
            summary=summary,
            duration_ms=duration_ms,
            error=error,
        )

        # Append to actions.yaml
        with open(task_dir / "actions.yaml") as f:
            data = yaml.safe_load(f) or {"actions": []}

        data["actions"].append(record.to_dict())

        with open(task_dir / "actions.yaml", "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        return record

    def get_recent_actions(self, task_id: str, limit: int = 3) -> List[ActionRecord]:
        """Get the most recent actions."""
        task_dir = self._task_dir(task_id)
        actions_file = task_dir / "actions.yaml"

        if not actions_file.exists():
            return []

        with open(actions_file) as f:
            data = yaml.safe_load(f) or {"actions": []}

        actions = data.get("actions", [])[-limit:]
        return [ActionRecord.from_dict(a) for a in actions]

    def update_verification(
        self,
        task_id: str,
        checks_passing: int,
        checks_failing: int,
        tests_passing: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update verification status."""
        state = self.load(task_id)
        if state:
            state.verification = VerificationStatus(
                checks_passing=checks_passing,
                checks_failing=checks_failing,
                tests_passing=tests_passing,
                ready_for_completion=(checks_failing == 0 and tests_passing),
                last_check_time=datetime.utcnow(),
                details=details or {},
            )
            self._save_state(state)

    def update_context_data(self, task_id: str, key: str, value: Any) -> None:
        """Update a specific context data field."""
        state = self.load(task_id)
        if state:
            state.context_data[key] = value
            self._save_state(state)

    def set_error(self, task_id: str, error: str) -> None:
        """Set error and transition to FAILED phase."""
        state = self.load(task_id)
        if state:
            state.error = error
            state.phase = TaskPhase.FAILED
            self._save_state(state)

    def save_artifact(
        self,
        task_id: str,
        artifact_type: str,  # "inputs", "outputs", "snapshots"
        name: str,
        content: str,
    ) -> Path:
        """Save an artifact file."""
        task_dir = self._task_dir(task_id)
        artifact_dir = task_dir / "artifacts" / artifact_type
        artifact_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = artifact_dir / name
        with open(artifact_path, "w") as f:
            f.write(content)

        return artifact_path

    def load_artifact(
        self,
        task_id: str,
        artifact_type: str,
        name: str,
    ) -> Optional[str]:
        """Load an artifact file."""
        artifact_path = self._task_dir(task_id) / "artifacts" / artifact_type / name
        if artifact_path.exists():
            return artifact_path.read_text()
        return None

    def list_tasks(self, status: Optional[str] = None) -> List[str]:
        """List all task IDs, optionally filtered by status."""
        if not self.tasks_dir.exists():
            return []

        task_ids = []
        for task_dir in self.tasks_dir.iterdir():
            if task_dir.is_dir() and (task_dir / "task.yaml").exists():
                if status:
                    state = self.load(task_dir.name)
                    if state and state.phase.value == status:
                        task_ids.append(task_dir.name)
                else:
                    task_ids.append(task_dir.name)

        return sorted(task_ids)

    def delete_task(self, task_id: str) -> bool:
        """Delete a task and all its data."""
        import shutil
        task_dir = self._task_dir(task_id)
        if task_dir.exists():
            shutil.rmtree(task_dir)
            return True
        return False
