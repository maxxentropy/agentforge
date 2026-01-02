# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-state-store

"""Tests for pipeline state persistence."""

import threading
import time
from pathlib import Path

import pytest
import yaml

from agentforge.core.pipeline import (
    PipelineState,
    PipelineStatus,
    PipelineStateStore,
    create_pipeline_state,
)


class TestPipelineStateStore:
    """Tests for PipelineStateStore."""

    def test_save_and_load(self, state_store, sample_pipeline_state):
        """Save and load round-trips correctly."""
        state_store.save(sample_pipeline_state)
        loaded = state_store.load(sample_pipeline_state.pipeline_id)

        assert loaded is not None
        assert loaded.pipeline_id == sample_pipeline_state.pipeline_id
        assert loaded.template == sample_pipeline_state.template
        assert loaded.request == sample_pipeline_state.request

    def test_load_nonexistent(self, state_store):
        """Loading non-existent pipeline returns None."""
        loaded = state_store.load("PL-99999999-nonexist")
        assert loaded is None

    def test_save_creates_directories(self, temp_project):
        """Save creates storage directories if they don't exist."""
        store = PipelineStateStore(temp_project)
        state = create_pipeline_state("test", temp_project)
        store.save(state)

        assert (temp_project / ".agentforge" / "pipeline" / "active").exists()
        assert (temp_project / ".agentforge" / "pipeline" / "completed").exists()

    def test_active_vs_completed_storage(self, state_store, sample_pipeline_state):
        """Active and completed pipelines stored in different directories."""
        # Save as active (PENDING status)
        state_store.save(sample_pipeline_state)
        active_path = state_store._get_active_path(sample_pipeline_state.pipeline_id)
        assert active_path.exists()

        # Mark as completed and save
        sample_pipeline_state.status = PipelineStatus.COMPLETED
        state_store.save(sample_pipeline_state)

        completed_path = state_store._get_completed_path(sample_pipeline_state.pipeline_id)
        assert completed_path.exists()
        assert not active_path.exists()  # Moved from active

    def test_list_active_pipelines(self, state_store, temp_project):
        """list_active() returns only active pipelines."""
        # Create multiple pipelines
        state1 = create_pipeline_state("req1", temp_project)
        state2 = create_pipeline_state("req2", temp_project)
        state3 = create_pipeline_state("req3", temp_project)

        state1.status = PipelineStatus.RUNNING
        state2.status = PipelineStatus.PAUSED
        state3.status = PipelineStatus.COMPLETED

        state_store.save(state1)
        state_store.save(state2)
        state_store.save(state3)

        active = state_store.list_active()
        active_ids = [s.pipeline_id for s in active]

        assert state1.pipeline_id in active_ids
        assert state2.pipeline_id in active_ids
        assert state3.pipeline_id not in active_ids

    def test_list_completed_pipelines(self, state_store, temp_project):
        """list_completed() returns only completed pipelines."""
        state1 = create_pipeline_state("req1", temp_project)
        state2 = create_pipeline_state("req2", temp_project)

        state1.status = PipelineStatus.COMPLETED
        state2.status = PipelineStatus.RUNNING

        state_store.save(state1)
        state_store.save(state2)

        completed = state_store.list_completed()
        completed_ids = [s.pipeline_id for s in completed]

        assert state1.pipeline_id in completed_ids
        assert state2.pipeline_id not in completed_ids

    def test_list_completed_limit(self, state_store, temp_project):
        """list_completed() respects limit parameter."""
        for i in range(5):
            state = create_pipeline_state(f"req{i}", temp_project)
            state.status = PipelineStatus.COMPLETED
            state_store.save(state)

        completed = state_store.list_completed(limit=3)
        assert len(completed) == 3

    def test_delete_pipeline(self, state_store, sample_pipeline_state):
        """delete() removes pipeline state."""
        state_store.save(sample_pipeline_state)
        assert state_store.load(sample_pipeline_state.pipeline_id) is not None

        result = state_store.delete(sample_pipeline_state.pipeline_id)
        assert result is True
        assert state_store.load(sample_pipeline_state.pipeline_id) is None

    def test_delete_nonexistent(self, state_store):
        """delete() returns False for non-existent pipeline."""
        result = state_store.delete("PL-99999999-nonexist")
        assert result is False

    def test_archive_pipeline(self, state_store, sample_pipeline_state):
        """archive() moves pipeline from active to completed."""
        state_store.save(sample_pipeline_state)
        active_path = state_store._get_active_path(sample_pipeline_state.pipeline_id)
        assert active_path.exists()

        result = state_store.archive(sample_pipeline_state.pipeline_id)
        assert result is True
        assert not active_path.exists()

        completed_path = state_store._get_completed_path(sample_pipeline_state.pipeline_id)
        assert completed_path.exists()

    def test_archive_nonexistent(self, state_store):
        """archive() returns False for non-existent pipeline."""
        result = state_store.archive("PL-99999999-nonexist")
        assert result is False

    def test_corrupted_state_recovery(self, state_store, temp_project):
        """Corrupted state files are quarantined."""
        pipeline_id = "PL-20260101-corrupt1"
        file_path = state_store._get_active_path(pipeline_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid YAML
        with open(file_path, "w") as f:
            f.write("invalid: yaml: content: [}")

        loaded = state_store.load(pipeline_id)
        assert loaded is None

        # Original file should be quarantined
        corrupted_path = file_path.with_suffix(".yaml.corrupted")
        assert corrupted_path.exists()
        assert not file_path.exists()

    def test_index_updated_on_save(self, state_store, sample_pipeline_state):
        """Index file is updated when pipeline is saved."""
        state_store.save(sample_pipeline_state)

        index_data = state_store._read_yaml(state_store.index_file)
        assert sample_pipeline_state.pipeline_id in index_data["pipelines"]

    def test_get_by_status(self, state_store, temp_project):
        """get_by_status() filters pipelines by status."""
        state1 = create_pipeline_state("req1", temp_project)
        state2 = create_pipeline_state("req2", temp_project)
        state3 = create_pipeline_state("req3", temp_project)

        state1.status = PipelineStatus.RUNNING
        state2.status = PipelineStatus.RUNNING
        state3.status = PipelineStatus.PAUSED

        state_store.save(state1)
        state_store.save(state2)
        state_store.save(state3)

        running = state_store.get_by_status(PipelineStatus.RUNNING)
        assert len(running) == 2

        paused = state_store.get_by_status(PipelineStatus.PAUSED)
        assert len(paused) == 1

    def test_concurrent_access(self, temp_project):
        """Concurrent saves don't corrupt data."""
        store = PipelineStateStore(temp_project)
        state = create_pipeline_state("concurrent", temp_project)
        store.save(state)

        errors = []

        def update_state(n):
            try:
                # Retry load if we hit a race condition with concurrent write
                for attempt in range(3):
                    loaded = store.load(state.pipeline_id)
                    if loaded is not None:
                        break
                    time.sleep(0.01)

                if loaded is not None:
                    loaded.config[f"update_{n}"] = n
                    store.save(loaded)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=update_state, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        # State should have some updates (order depends on timing)
        final = store.load(state.pipeline_id)
        assert final is not None
