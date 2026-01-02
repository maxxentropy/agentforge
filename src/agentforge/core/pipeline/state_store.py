# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
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

import fcntl
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .state import PipelineState, PipelineStatus

logger = logging.getLogger(__name__)


class PipelineStateStore:
    """
    YAML-based storage for pipeline states.

    Storage structure:
        .agentforge/pipeline/
        ├── active/
        │   └── {pipeline_id}.yaml
        ├── completed/
        │   └── {pipeline_id}.yaml
        └── index.yaml
    """

    def __init__(self, project_path: Path):
        """
        Initialize the state store.

        Args:
            project_path: Root path for the project
        """
        self.project_path = Path(project_path)
        self.root = self.project_path / ".agentforge" / "pipeline"
        self.active_dir = self.root / "active"
        self.completed_dir = self.root / "completed"
        self.index_file = self.root / "index.yaml"

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

    def load(self, pipeline_id: str) -> Optional[PipelineState]:
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

    def _load_from_file(self, file_path: Path) -> Optional[PipelineState]:
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

    def list_active(self) -> List[PipelineState]:
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

    def list_completed(self, limit: int = 20) -> List[PipelineState]:
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

    def _write_yaml(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write YAML with file locking."""
        with open(file_path, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _read_yaml(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read YAML with file locking."""
        try:
            with open(file_path, "r") as f:
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

    def get_by_status(self, status: PipelineStatus) -> List[PipelineState]:
        """
        Get all pipelines with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of matching pipeline states
        """
        all_states = self.list_active() + self.list_completed()
        return [s for s in all_states if s.status == status]

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
