# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: thread-correlator
# @test_path: tests/unit/audit/test_thread_correlator.py

"""
Thread Correlator
=================

Tracks agent spawning and thread hierarchy for parallel execution.

When an agent spawns sub-agents to delegate portions of a task,
the ThreadCorrelator maintains the parent-child relationships
enabling complete traceability back to the original request.

Key concepts:
- Thread: A single execution context (pipeline, agent, task)
- Root Thread: The original user-initiated execution
- Parent/Child: Delegation relationship between threads
- Thread Tree: Full hierarchy of spawned threads

Example hierarchy:
    user-request-001 (root)
    ├── analyze-stage-001 (child)
    │   ├── code-review-001 (grandchild, parallel)
    │   └── security-scan-001 (grandchild, parallel)
    └── implement-stage-001 (child)
        └── test-gen-001 (grandchild)
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ThreadStatus(str, Enum):
    """Status of a thread."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SpawnType(str, Enum):
    """Why a thread was spawned."""

    DELEGATION = "delegation"  # Delegating a portion of work
    PARALLEL = "parallel"  # Parallel execution of independent tasks
    RETRY = "retry"  # Retrying a failed operation
    ESCALATION = "escalation"  # Human escalation handling
    PIPELINE_STAGE = "pipeline_stage"  # Pipeline stage execution


@dataclass
class ThreadSpawn:
    """Record of a thread spawn event."""

    parent_thread_id: str
    child_thread_id: str
    spawn_type: SpawnType
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Context passed to child
    delegated_task: str | None = None
    delegated_context: dict[str, Any] | None = None

    # Parallel execution tracking
    parallel_group_id: str | None = None  # Groups parallel spawns
    parallel_index: int | None = None  # Order within parallel group

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "parent_thread_id": self.parent_thread_id,
            "child_thread_id": self.child_thread_id,
            "spawn_type": self.spawn_type.value,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }
        if self.delegated_task:
            data["delegated_task"] = self.delegated_task
        if self.delegated_context:
            data["delegated_context"] = self.delegated_context
        if self.parallel_group_id:
            data["parallel_group"] = {
                "group_id": self.parallel_group_id,
                "index": self.parallel_index,
            }
        return data


@dataclass
class ThreadInfo:
    """Information about a single thread."""

    thread_id: str
    parent_thread_id: str | None = None
    root_thread_id: str | None = None  # Ultimate ancestor

    # Thread metadata
    thread_type: str = "generic"  # pipeline, agent, task, stage
    name: str | None = None
    description: str | None = None

    # Status tracking
    status: ThreadStatus = ThreadStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    started_at: str | None = None
    completed_at: str | None = None

    # Spawn info
    spawn_type: SpawnType | None = None
    spawn_reason: str | None = None

    # Parallel execution
    parallel_group_id: str | None = None
    parallel_index: int | None = None

    # Children
    child_thread_ids: list[str] = field(default_factory=list)

    # Summary (filled on completion)
    outcome: str | None = None
    error: str | None = None
    transaction_count: int = 0
    total_tokens: int = 0
    total_duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "thread_id": self.thread_id,
            "thread_type": self.thread_type,
            "status": self.status.value,
            "created_at": self.created_at,
        }
        for partial in [
            self._identity_fields(),
            self._timing_fields(),
            self._spawn_fields(),
            self._parallel_fields(),
            self._outcome_fields(),
        ]:
            data.update(partial)
        return data

    def _identity_fields(self) -> dict[str, Any]:
        """Optional identity fields."""
        fields: dict[str, Any] = {}
        if self.parent_thread_id:
            fields["parent_thread_id"] = self.parent_thread_id
        if self.root_thread_id:
            fields["root_thread_id"] = self.root_thread_id
        if self.name:
            fields["name"] = self.name
        if self.description:
            fields["description"] = self.description
        if self.child_thread_ids:
            fields["child_thread_ids"] = self.child_thread_ids
        return fields

    def _timing_fields(self) -> dict[str, Any]:
        """Optional timing fields."""
        fields: dict[str, Any] = {}
        if self.started_at:
            fields["started_at"] = self.started_at
        if self.completed_at:
            fields["completed_at"] = self.completed_at
        return fields

    def _spawn_fields(self) -> dict[str, Any]:
        """Optional spawn metadata."""
        if self.spawn_type:
            return {"spawn": {"type": self.spawn_type.value, "reason": self.spawn_reason}}
        return {}

    def _parallel_fields(self) -> dict[str, Any]:
        """Optional parallel group info."""
        if self.parallel_group_id:
            return {"parallel_group": {"group_id": self.parallel_group_id, "index": self.parallel_index}}
        return {}

    def _outcome_fields(self) -> dict[str, Any]:
        """Optional outcome summary."""
        if self.outcome:
            return {"outcome": {
                "status": self.outcome,
                "error": self.error,
                "transaction_count": self.transaction_count,
                "total_tokens": self.total_tokens,
                "total_duration_ms": self.total_duration_ms,
            }}
        return {}


class ThreadCorrelator:
    """
    Tracks thread hierarchy for agent delegation and parallel execution.

    Provides:
    - Thread creation with automatic parent linking
    - Parallel execution group management
    - Thread tree traversal
    - Cross-thread correlation
    """

    def __init__(self, project_path: Path):
        """
        Initialize thread correlator.

        Args:
            project_path: Root project directory
        """
        self.project_path = Path(project_path).resolve()
        self.audit_dir = self.project_path / ".agentforge" / "audit"
        self.threads_dir = self.audit_dir / "threads"
        self.lineage_dir = self.audit_dir / "lineage"
        self.threads_dir.mkdir(parents=True, exist_ok=True)
        self.lineage_dir.mkdir(parents=True, exist_ok=True)

        # Index for quick lookups
        self._index_path = self.audit_dir / "index.yaml"
        self._index: dict[str, Any] | None = None

    def create_thread(
        self,
        thread_id: str,
        parent_thread_id: str | None = None,
        thread_type: str = "generic",
        name: str | None = None,
        description: str | None = None,
        spawn_type: SpawnType | None = None,
        spawn_reason: str | None = None,
        parallel_group_id: str | None = None,
        parallel_index: int | None = None,
    ) -> ThreadInfo:
        """
        Create a new thread record.

        Args:
            thread_id: Unique thread identifier
            parent_thread_id: Parent thread (if spawned)
            thread_type: Type of thread (pipeline, agent, task, stage)
            name: Human-readable name
            description: Description of thread's purpose
            spawn_type: Why this thread was spawned
            spawn_reason: Detailed reason for spawn
            parallel_group_id: Group ID for parallel execution
            parallel_index: Index within parallel group

        Returns:
            Created ThreadInfo
        """
        # Determine root thread
        root_thread_id = thread_id  # Default to self
        if parent_thread_id:
            parent_info = self.get_thread(parent_thread_id)
            if parent_info and parent_info.root_thread_id:
                root_thread_id = parent_info.root_thread_id
            elif parent_info:
                root_thread_id = parent_info.thread_id

            # Update parent's children list
            self._add_child_to_parent(parent_thread_id, thread_id)

        info = ThreadInfo(
            thread_id=thread_id,
            parent_thread_id=parent_thread_id,
            root_thread_id=root_thread_id if parent_thread_id else None,
            thread_type=thread_type,
            name=name,
            description=description,
            status=ThreadStatus.PENDING,
            spawn_type=spawn_type,
            spawn_reason=spawn_reason,
            parallel_group_id=parallel_group_id,
            parallel_index=parallel_index,
        )

        self._save_thread_manifest(info)
        self._update_index(info)

        # Log spawn event if this is a child thread
        if parent_thread_id and spawn_type:
            spawn = ThreadSpawn(
                parent_thread_id=parent_thread_id,
                child_thread_id=thread_id,
                spawn_type=spawn_type,
                reason=spawn_reason or "",
                parallel_group_id=parallel_group_id,
                parallel_index=parallel_index,
            )
            self._log_spawn(spawn)

        return info

    def start_thread(self, thread_id: str) -> None:
        """Mark a thread as started."""
        info = self.get_thread(thread_id)
        if info:
            info.status = ThreadStatus.RUNNING
            info.started_at = datetime.now(UTC).isoformat()
            self._save_thread_manifest(info)

    def complete_thread(
        self,
        thread_id: str,
        outcome: str = "success",
        error: str | None = None,
        transaction_count: int = 0,
        total_tokens: int = 0,
        total_duration_ms: int = 0,
    ) -> None:
        """
        Mark a thread as completed.

        Args:
            thread_id: Thread to complete
            outcome: Outcome status (success, failed, cancelled)
            error: Error message if failed
            transaction_count: Number of transactions in thread
            total_tokens: Total tokens used
            total_duration_ms: Total duration
        """
        info = self.get_thread(thread_id)
        if info:
            info.status = (
                ThreadStatus.COMPLETED
                if outcome == "success"
                else ThreadStatus.FAILED
            )
            info.completed_at = datetime.now(UTC).isoformat()
            info.outcome = outcome
            info.error = error
            info.transaction_count = transaction_count
            info.total_tokens = total_tokens
            info.total_duration_ms = total_duration_ms
            self._save_thread_manifest(info)
            self._update_lineage_tree(info)

    def get_thread(self, thread_id: str) -> ThreadInfo | None:
        """Get thread info by ID."""
        manifest_path = self.threads_dir / thread_id / "manifest.yaml"
        if not manifest_path.exists():
            return None

        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        return self._dict_to_thread_info(data)

    def get_children(self, thread_id: str) -> list[ThreadInfo]:
        """Get all direct children of a thread."""
        info = self.get_thread(thread_id)
        if not info or not info.child_thread_ids:
            return []

        children = []
        for child_id in info.child_thread_ids:
            child = self.get_thread(child_id)
            if child:
                children.append(child)
        return children

    def get_thread_tree(self, root_thread_id: str) -> dict[str, Any]:
        """
        Get complete thread tree from a root.

        Returns nested structure showing all descendants.
        """
        root = self.get_thread(root_thread_id)
        if not root:
            return {}

        return self._build_tree(root)

    def get_parallel_group(self, group_id: str) -> list[ThreadInfo]:
        """Get all threads in a parallel execution group."""
        index = self._load_index()
        thread_ids = index.get("parallel_groups", {}).get(group_id, [])

        threads = []
        for tid in thread_ids:
            thread = self.get_thread(tid)
            if thread:
                threads.append(thread)

        # Sort by parallel_index
        threads.sort(key=lambda t: t.parallel_index or 0)
        return threads

    def create_parallel_group(
        self,
        parent_thread_id: str,
        group_id: str,
        tasks: list[dict[str, Any]],
        spawn_type: SpawnType = SpawnType.PARALLEL,
    ) -> list[ThreadInfo]:
        """
        Create a group of parallel threads.

        Args:
            parent_thread_id: Parent thread spawning the group
            group_id: Unique group identifier
            tasks: List of task definitions with 'thread_id', 'name', 'description'
            spawn_type: Type of spawn

        Returns:
            List of created ThreadInfo objects
        """
        threads = []
        for index, task in enumerate(tasks):
            thread = self.create_thread(
                thread_id=task["thread_id"],
                parent_thread_id=parent_thread_id,
                thread_type="parallel_task",
                name=task.get("name"),
                description=task.get("description"),
                spawn_type=spawn_type,
                spawn_reason=f"Parallel task {index + 1} of {len(tasks)}",
                parallel_group_id=group_id,
                parallel_index=index,
            )
            threads.append(thread)

        # Update index with parallel group
        index = self._load_index()
        if "parallel_groups" not in index:
            index["parallel_groups"] = {}
        index["parallel_groups"][group_id] = [t.thread_id for t in threads]
        self._save_index(index)

        return threads

    def get_ancestry(self, thread_id: str) -> list[ThreadInfo]:
        """
        Get full ancestry from thread to root.

        Returns list from child to root (current thread first).
        """
        ancestry = []
        current_id = thread_id

        while current_id:
            thread = self.get_thread(current_id)
            if not thread:
                break
            ancestry.append(thread)
            current_id = thread.parent_thread_id

        return ancestry

    def _save_thread_manifest(self, info: ThreadInfo) -> None:
        """Save thread manifest."""
        thread_dir = self.threads_dir / info.thread_id
        thread_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = thread_dir / "manifest.yaml"
        manifest_path.write_text(
            yaml.dump(info.to_dict(), default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def _add_child_to_parent(self, parent_id: str, child_id: str) -> None:
        """Add child to parent's children list."""
        parent = self.get_thread(parent_id)
        if parent:
            if child_id not in parent.child_thread_ids:
                parent.child_thread_ids.append(child_id)
                self._save_thread_manifest(parent)

    def _log_spawn(self, spawn: ThreadSpawn) -> None:
        """Log spawn event to parent thread's transactions."""
        parent_dir = self.threads_dir / spawn.parent_thread_id
        spawns_dir = parent_dir / "spawns"
        spawns_dir.mkdir(parents=True, exist_ok=True)

        spawn_path = spawns_dir / f"spawn-{spawn.child_thread_id}.yaml"
        spawn_path.write_text(
            yaml.dump(spawn.to_dict(), default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def _build_tree(self, thread: ThreadInfo) -> dict[str, Any]:
        """Recursively build thread tree."""
        tree = thread.to_dict()
        if thread.child_thread_ids:
            tree["children"] = []
            for child_id in thread.child_thread_ids:
                child = self.get_thread(child_id)
                if child:
                    tree["children"].append(self._build_tree(child))
        return tree

    def _update_index(self, info: ThreadInfo) -> None:
        """Update global index with thread info."""
        index = self._load_index()

        if "threads" not in index:
            index["threads"] = {}

        index["threads"][info.thread_id] = {
            "thread_type": info.thread_type,
            "parent_thread_id": info.parent_thread_id,
            "root_thread_id": info.root_thread_id,
            "status": info.status.value,
            "created_at": info.created_at,
        }

        # Track root threads
        if not info.parent_thread_id:
            if "root_threads" not in index:
                index["root_threads"] = []
            if info.thread_id not in index["root_threads"]:
                index["root_threads"].append(info.thread_id)

        self._save_index(index)

    def _update_lineage_tree(self, info: ThreadInfo) -> None:
        """Update lineage tree file for root thread."""
        root_id = info.root_thread_id or info.thread_id
        lineage_path = self.lineage_dir / f"{root_id}.yaml"

        # Rebuild tree from root
        tree = self.get_thread_tree(root_id)
        lineage_path.write_text(
            yaml.dump(tree, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def _load_index(self) -> dict[str, Any]:
        """Load global index."""
        if self._index is not None:
            return self._index

        if self._index_path.exists():
            self._index = yaml.safe_load(self._index_path.read_text(encoding="utf-8"))
        else:
            self._index = {}

        return self._index

    def _save_index(self, index: dict[str, Any]) -> None:
        """Save global index."""
        self._index = index
        self._index_path.write_text(
            yaml.dump(index, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def _dict_to_thread_info(self, data: dict[str, Any]) -> ThreadInfo:
        """Convert dictionary to ThreadInfo."""
        spawn = data.get("spawn", {})
        parallel = data.get("parallel_group", {})
        outcome = data.get("outcome", {})

        return ThreadInfo(
            thread_id=data.get("thread_id", ""),
            parent_thread_id=data.get("parent_thread_id"),
            root_thread_id=data.get("root_thread_id"),
            thread_type=data.get("thread_type", "generic"),
            name=data.get("name"),
            description=data.get("description"),
            status=ThreadStatus(data.get("status", "pending")),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            spawn_type=SpawnType(spawn["type"]) if spawn.get("type") else None,
            spawn_reason=spawn.get("reason"),
            parallel_group_id=parallel.get("group_id"),
            parallel_index=parallel.get("index"),
            child_thread_ids=data.get("child_thread_ids", []),
            outcome=outcome.get("status"),
            error=outcome.get("error"),
            transaction_count=outcome.get("transaction_count", 0),
            total_tokens=outcome.get("total_tokens", 0),
            total_duration_ms=outcome.get("total_duration_ms", 0),
        )
