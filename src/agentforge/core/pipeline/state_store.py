# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-state-store
# @test_path: tests/unit/pipeline/test_state_store.py

"""
Pipeline State Store
====================

YAML-based persistence for pipeline state.

Manages storage of pipeline states with:
- Separate directories for active and completed pipelines
- File locking for concurrent access safety
- Automatic archival on completion
"""

import atexit
import fcntl
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Generator

import yaml

from .state import PipelineState, PipelineStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Deferred Write Manager
# =============================================================================


class DeferredWriteManager:
    """
    Manages deferred/batched writes for state persistence.

    Buffers writes and flushes them either:
    - After a configurable delay (debouncing rapid saves)
    - When flush() is explicitly called
    - On shutdown

    This reduces I/O overhead during rapid iteration phases like GREEN.

    Thread-safe: writes are processed by a background thread.
    """

    # Default debounce delay in seconds
    DEFAULT_DEBOUNCE_SECONDS = 0.5

    def __init__(
        self,
        write_func: callable,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
    ):
        """
        Initialize the deferred write manager.

        Args:
            write_func: Function to call for actual write (path, data) -> None
            debounce_seconds: Delay before flushing buffered writes
        """
        self._write_func = write_func
        self._debounce_seconds = debounce_seconds

        # Pending writes: path -> (data, timestamp)
        self._pending: dict[Path, tuple[dict[str, Any], float]] = {}
        self._lock = threading.Lock()

        # Background thread for flushing
        self._queue: Queue = Queue()
        self._shutdown = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

        # Register shutdown handler
        atexit.register(self.shutdown)

    def schedule_write(self, path: Path, data: dict[str, Any]) -> None:
        """
        Schedule a write operation.

        If a write for this path is already pending, it's replaced.
        The write will be executed after the debounce delay.

        Args:
            path: File path to write to
            data: Data to write (YAML-serializable dict)
        """
        with self._lock:
            self._pending[path] = (data, time.time())
            # Signal the worker to check for pending writes
            self._queue.put(("check", None))

    def flush(self, path: Path | None = None) -> None:
        """
        Flush pending writes immediately.

        Args:
            path: Specific path to flush, or None for all pending writes
        """
        with self._lock:
            if path is not None:
                # Flush specific path
                if path in self._pending:
                    data, _ = self._pending.pop(path)
                    self._write_func(path, data)
            else:
                # Flush all
                for p, (data, _) in list(self._pending.items()):
                    self._write_func(p, data)
                self._pending.clear()

    def flush_blocking(self) -> None:
        """Flush all pending writes and wait for completion."""
        self._queue.put(("flush_all", None))
        # Wait for the flush to complete
        self._queue.join()

    def _worker_loop(self) -> None:
        """Background worker that processes the write queue."""
        while not self._shutdown.is_set():
            try:
                # Wait for a signal with timeout for periodic checks
                cmd, _ = self._queue.get(timeout=0.1)

                if cmd == "check":
                    self._process_pending()
                elif cmd == "flush_all":
                    self.flush()

                self._queue.task_done()

            except Empty:
                # Timeout - check for expired pending writes
                self._process_pending()

    def _process_pending(self) -> None:
        """Process pending writes that have passed the debounce delay."""
        now = time.time()
        with self._lock:
            expired = []
            for path, (data, timestamp) in self._pending.items():
                if now - timestamp >= self._debounce_seconds:
                    expired.append((path, data))

            for path, data in expired:
                del self._pending[path]
                try:
                    self._write_func(path, data)
                except Exception as e:
                    logger.error(f"Deferred write failed for {path}: {e}")

    def shutdown(self) -> None:
        """Shutdown the manager, flushing all pending writes."""
        self._shutdown.set()
        self.flush()
        if self._worker.is_alive():
            self._worker.join(timeout=2.0)

    @property
    def pending_count(self) -> int:
        """Number of pending writes."""
        with self._lock:
            return len(self._pending)


class PipelineStateStore:
    """
    YAML-based storage for pipeline states.

    Storage structure:
        .agentforge/pipeline/
        ├── active/
        │   └── {pipeline_id}.yaml
        ├── completed/
        │   └── {pipeline_id}.yaml
        ├── locks/
        │   └── {pipeline_id}.lock
        └── index.yaml

    Supports two write modes:
        - Immediate (default): Writes to disk immediately
        - Deferred: Buffers writes and flushes after debounce delay

    Use deferred mode for rapid iteration scenarios (e.g., GREEN phase)
    where frequent saves would cause I/O overhead.
    """

    # Default debounce delay for deferred writes
    DEFAULT_DEBOUNCE_SECONDS = 0.5

    def __init__(
        self,
        project_path: Path,
        deferred: bool = False,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
    ):
        """
        Initialize the state store.

        Args:
            project_path: Root path for the project
            deferred: Enable deferred/batched writes (reduces I/O for rapid saves)
            debounce_seconds: Delay before flushing deferred writes (default: 0.5s)
        """
        self.project_path = Path(project_path)
        self.root = self.project_path / ".agentforge" / "pipeline"
        self.active_dir = self.root / "active"
        self.completed_dir = self.root / "completed"
        self.index_file = self.root / "index.yaml"

        # Deferred write support
        self._deferred_mode = deferred
        self._deferred_manager: DeferredWriteManager | None = None
        if deferred:
            self._deferred_manager = DeferredWriteManager(
                write_func=self._write_yaml,
                debounce_seconds=debounce_seconds,
            )

        # Ensure directories exist
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Create storage directories if they don't exist."""
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

    def _get_active_path(self, pipeline_id: str) -> Path:
        """Get path to active pipeline state file."""
        return self.active_dir / f"{pipeline_id}.yaml"

    def _get_completed_path(self, pipeline_id: str) -> Path:
        """Get path to completed pipeline state file."""
        return self.completed_dir / f"{pipeline_id}.yaml"

    def _get_lock_path(self, pipeline_id: str) -> Path:
        """Get path to lock file for a pipeline."""
        return self.root / "locks" / f"{pipeline_id}.lock"

    @contextmanager
    def transaction(self, pipeline_id: str) -> Generator[None, None, None]:
        """
        Context manager for atomic pipeline operations.

        Acquires an exclusive lock on the pipeline for the duration of the
        context. Use this when you need to load, modify, and save a pipeline
        atomically to prevent race conditions.

        Usage:
            with state_store.transaction(pipeline_id):
                state = state_store.load(pipeline_id)
                state.status = PipelineStatus.RUNNING
                state_store.save(state)

        Args:
            pipeline_id: Pipeline ID to lock

        Yields:
            None (lock is held for duration of context)
        """
        lock_dir = self.root / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)

        lock_path = self._get_lock_path(pipeline_id)
        lock_path.touch(exist_ok=True)

        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def save(self, state: PipelineState) -> None:
        """
        Save pipeline state to YAML file.

        Uses file locking for concurrent access safety.

        Args:
            state: Pipeline state to save
        """
        # Update timestamp
        state.touch()

        # Determine target path based on status
        if state.is_terminal():
            file_path = self._get_completed_path(state.pipeline_id)
            # Remove from active if exists
            active_path = self._get_active_path(state.pipeline_id)
            if active_path.exists():
                active_path.unlink()
        else:
            file_path = self._get_active_path(state.pipeline_id)

        # Serialize to YAML
        data = state.to_dict()

        # Write with file locking
        self._write_yaml(file_path, data)

        # Update index
        self._update_index(state)

        logger.debug(f"Saved pipeline state: {state.pipeline_id} -> {file_path}")

    def save_deferred(self, state: PipelineState) -> None:
        """
        Save pipeline state using deferred write mode.

        In deferred mode: buffers the write and flushes after debounce delay.
        In immediate mode: behaves exactly like save().

        Use this for non-critical saves during rapid iteration phases
        (e.g., progress updates during GREEN phase).

        For critical state changes (status transitions, completions),
        use save() instead to ensure immediate persistence.

        Args:
            state: Pipeline state to save
        """
        if not self._deferred_mode or self._deferred_manager is None:
            # Fall back to immediate save
            self.save(state)
            return

        # Update timestamp
        state.touch()

        # Determine target path based on status
        if state.is_terminal():
            # Terminal states should be saved immediately
            self.save(state)
            return

        file_path = self._get_active_path(state.pipeline_id)

        # Serialize and schedule deferred write
        data = state.to_dict()
        self._deferred_manager.schedule_write(file_path, data)

        # Index update is still immediate (small file)
        self._update_index(state)

        logger.debug(f"Scheduled deferred save: {state.pipeline_id}")

    def flush(self, pipeline_id: str | None = None) -> None:
        """
        Flush pending deferred writes.

        Args:
            pipeline_id: Specific pipeline to flush, or None for all

        Note:
            No-op if not in deferred mode.
        """
        if self._deferred_manager is None:
            return

        if pipeline_id:
            # Flush specific pipeline
            path = self._get_active_path(pipeline_id)
            self._deferred_manager.flush(path)
        else:
            # Flush all
            self._deferred_manager.flush()

    def flush_all_blocking(self) -> None:
        """
        Flush all pending writes and block until complete.

        Call this before shutdown or when you need to ensure
        all state is persisted.
        """
        if self._deferred_manager:
            self._deferred_manager.flush_blocking()

    @property
    def pending_writes(self) -> int:
        """Number of pending deferred writes."""
        if self._deferred_manager:
            return self._deferred_manager.pending_count
        return 0

    @property
    def deferred_mode(self) -> bool:
        """Whether deferred write mode is enabled."""
        return self._deferred_mode

    def load(self, pipeline_id: str) -> PipelineState | None:
        """
        Load pipeline state by ID.

        Checks both active and completed directories.

        Args:
            pipeline_id: Pipeline ID to load

        Returns:
            PipelineState if found, None otherwise
        """
        # Check active first
        active_path = self._get_active_path(pipeline_id)
        if active_path.exists():
            return self._load_from_file(active_path)

        # Check completed
        completed_path = self._get_completed_path(pipeline_id)
        if completed_path.exists():
            return self._load_from_file(completed_path)

        logger.debug(f"Pipeline not found: {pipeline_id}")
        return None

    def _load_from_file(self, file_path: Path) -> PipelineState | None:
        """Load state from a specific file with error recovery."""
        try:
            data = self._read_yaml(file_path)
            if data is None:
                return None
            return PipelineState.from_dict(data)
        except (yaml.YAMLError, KeyError, ValueError) as e:
            logger.error(f"Failed to load pipeline state from {file_path}: {e}")
            # Move corrupted file to .corrupted
            self._quarantine_corrupted(file_path)
            return None

    def _quarantine_corrupted(self, file_path: Path) -> None:
        """Move corrupted file to a .corrupted backup."""
        corrupted_path = file_path.with_suffix(".yaml.corrupted")
        try:
            file_path.rename(corrupted_path)
            logger.warning(f"Quarantined corrupted state: {corrupted_path}")
        except OSError as e:
            logger.error(f"Failed to quarantine corrupted file: {e}")

    def list_active(self) -> list[PipelineState]:
        """
        List all active (non-completed) pipelines.

        Returns:
            List of active pipeline states, sorted by updated_at descending
        """
        states = []
        for file_path in self.active_dir.glob("*.yaml"):
            state = self._load_from_file(file_path)
            if state:
                states.append(state)

        # Sort by updated_at descending
        states.sort(key=lambda s: s.updated_at, reverse=True)
        return states

    def list_completed(self, limit: int = 20) -> list[PipelineState]:
        """
        List recent completed pipelines.

        Args:
            limit: Maximum number of pipelines to return

        Returns:
            List of completed pipeline states, sorted by updated_at descending
        """
        states = []
        for file_path in self.completed_dir.glob("*.yaml"):
            state = self._load_from_file(file_path)
            if state:
                states.append(state)

        # Sort by updated_at descending
        states.sort(key=lambda s: s.updated_at, reverse=True)
        return states[:limit]

    def delete(self, pipeline_id: str) -> bool:
        """
        Delete a pipeline state.

        Args:
            pipeline_id: Pipeline ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Check active
        active_path = self._get_active_path(pipeline_id)
        if active_path.exists():
            active_path.unlink()
            self._remove_from_index(pipeline_id)
            logger.info(f"Deleted active pipeline: {pipeline_id}")
            return True

        # Check completed
        completed_path = self._get_completed_path(pipeline_id)
        if completed_path.exists():
            completed_path.unlink()
            self._remove_from_index(pipeline_id)
            logger.info(f"Deleted completed pipeline: {pipeline_id}")
            return True

        logger.debug(f"Pipeline not found for deletion: {pipeline_id}")
        return False

    def archive(self, pipeline_id: str) -> bool:
        """
        Move pipeline from active to completed directory.

        Args:
            pipeline_id: Pipeline ID to archive

        Returns:
            True if archived, False if not found or already completed
        """
        active_path = self._get_active_path(pipeline_id)
        if not active_path.exists():
            logger.debug(f"Pipeline not in active: {pipeline_id}")
            return False

        completed_path = self._get_completed_path(pipeline_id)
        active_path.rename(completed_path)
        logger.info(f"Archived pipeline: {pipeline_id}")
        return True

    def _write_yaml(self, file_path: Path, data: dict[str, Any]) -> None:
        """Write YAML with file locking."""
        with open(file_path, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _read_yaml(self, file_path: Path) -> dict[str, Any] | None:
        """Read YAML with file locking."""
        try:
            with open(file_path) as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    return yaml.safe_load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except FileNotFoundError:
            return None

    def _update_index(self, state: PipelineState) -> None:
        """Update the index file with pipeline metadata."""
        index = self._read_yaml(self.index_file) or {"pipelines": {}}

        index["pipelines"][state.pipeline_id] = {
            "template": state.template,
            "status": state.status.value,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "current_stage": state.current_stage,
        }

        self._write_yaml(self.index_file, index)

    def _remove_from_index(self, pipeline_id: str) -> None:
        """Remove pipeline from index."""
        index = self._read_yaml(self.index_file)
        if index and pipeline_id in index.get("pipelines", {}):
            del index["pipelines"][pipeline_id]
            self._write_yaml(self.index_file, index)

    def get_by_status(self, status: PipelineStatus) -> list[PipelineState]:
        """
        Get all pipelines with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of matching pipeline states
        """
        all_states = self.list_active() + self.list_completed()
        return [s for s in all_states if s.status == status]

    def list(
        self,
        status: PipelineStatus | None = None,
        limit: int = 10,
    ) -> list[PipelineState]:
        """
        List pipelines with optional filtering.

        Unified method combining active and completed pipelines.

        Args:
            status: Filter by status (None = all)
            limit: Maximum number to return (default: 10)

        Returns:
            List of PipelineState objects, newest first (by created_at)
        """
        # Gather all pipelines
        all_states = self.list_active() + self.list_completed(limit=1000)

        # Filter by status if specified
        if status is not None:
            all_states = [s for s in all_states if s.status == status]

        # Sort by created_at descending (newest first)
        all_states.sort(key=lambda s: s.created_at, reverse=True)

        # Apply limit
        return all_states[:limit]

    def cleanup_old_completed(self, days: int = 30) -> int:
        """
        Remove completed pipelines older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of pipelines removed
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        removed = 0

        for file_path in self.completed_dir.glob("*.yaml"):
            if file_path.stat().st_mtime < cutoff:
                state = self._load_from_file(file_path)
                if state:
                    self.delete(state.pipeline_id)
                    removed += 1

        logger.info(f"Cleaned up {removed} old completed pipelines")
        return removed
