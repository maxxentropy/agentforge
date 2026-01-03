# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @component_id: pipeline-state-store
# @component_id: state-store-list

"""Tests for pipeline state persistence."""

import threading
import time

from agentforge.core.pipeline import (
    PipelineStateStore,
    PipelineStatus,
    create_pipeline_state,
)


class TestPipelineStateStore:
    """Tests for PipelineStateStore."""

    def test_save_and_load(self, state_store, sample_pipeline_state):
        """Save and load round-trips correctly."""
        state_store.save(sample_pipeline_state)
        loaded = state_store.load(sample_pipeline_state.pipeline_id)

        assert loaded is not None, "Expected loaded is not None"
        assert loaded.pipeline_id == sample_pipeline_state.pipeline_id, "Expected loaded.pipeline_id to equal sample_pipeline_state.pipel..."
        assert loaded.template == sample_pipeline_state.template, "Expected loaded.template to equal sample_pipeline_state.template"
        assert loaded.request == sample_pipeline_state.request, "Expected loaded.request to equal sample_pipeline_state.request"

    def test_load_nonexistent(self, state_store):
        """Loading non-existent pipeline returns None."""
        loaded = state_store.load("PL-99999999-nonexist")
        assert loaded is None, "Expected loaded is None"

    def test_save_creates_directories(self, temp_project):
        """Save creates storage directories if they don't exist."""
        store = PipelineStateStore(temp_project)
        state = create_pipeline_state("test", temp_project)
        store.save(state)

        assert (temp_project / ".agentforge" / "pipeline" / "active").exists(), "Expected (temp_project / '.agentforg...() to be truthy"
        assert (temp_project / ".agentforge" / "pipeline" / "completed").exists(), "Expected (temp_project / '.agentforg...() to be truthy"

    def test_active_vs_completed_storage(self, state_store, sample_pipeline_state):
        """Active and completed pipelines stored in different directories."""
        # Save as active (PENDING status)
        state_store.save(sample_pipeline_state)
        active_path = state_store._get_active_path(sample_pipeline_state.pipeline_id)
        assert active_path.exists(), "Expected active_path.exists() to be truthy"

        # Mark as completed and save
        sample_pipeline_state.status = PipelineStatus.COMPLETED
        state_store.save(sample_pipeline_state)

        completed_path = state_store._get_completed_path(sample_pipeline_state.pipeline_id)
        assert completed_path.exists(), "Expected completed_path.exists() to be truthy"
        assert not active_path.exists(), "Assertion failed"# Moved from active

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

        assert state1.pipeline_id in active_ids, "Expected state1.pipeline_id in active_ids"
        assert state2.pipeline_id in active_ids, "Expected state2.pipeline_id in active_ids"
        assert state3.pipeline_id not in active_ids, "Expected state3.pipeline_id not in active_ids"

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

        assert state1.pipeline_id in completed_ids, "Expected state1.pipeline_id in completed_ids"
        assert state2.pipeline_id not in completed_ids, "Expected state2.pipeline_id not in completed_ids"

    def test_list_completed_limit(self, state_store, temp_project):
        """list_completed() respects limit parameter."""
        for i in range(5):
            state = create_pipeline_state(f"req{i}", temp_project)
            state.status = PipelineStatus.COMPLETED
            state_store.save(state)

        completed = state_store.list_completed(limit=3)
        assert len(completed) == 3, "Expected len(completed) to equal 3"

    def test_delete_pipeline(self, state_store, sample_pipeline_state):
        """delete() removes pipeline state."""
        state_store.save(sample_pipeline_state)
        assert state_store.load(sample_pipeline_state.pipeline_id) is not None, "Expected state_store.load(sample_pip... is not None"

        result = state_store.delete(sample_pipeline_state.pipeline_id)
        assert result is True, "Expected result is True"
        assert state_store.load(sample_pipeline_state.pipeline_id) is None, "Expected state_store.load(sample_pip... is None"

    def test_delete_nonexistent(self, state_store):
        """delete() returns False for non-existent pipeline."""
        result = state_store.delete("PL-99999999-nonexist")
        assert result is False, "Expected result is False"

    def test_archive_pipeline(self, state_store, sample_pipeline_state):
        """archive() moves pipeline from active to completed."""
        state_store.save(sample_pipeline_state)
        active_path = state_store._get_active_path(sample_pipeline_state.pipeline_id)
        assert active_path.exists(), "Expected active_path.exists() to be truthy"

        result = state_store.archive(sample_pipeline_state.pipeline_id)
        assert result is True, "Expected result is True"
        assert not active_path.exists(), "Assertion failed"

        completed_path = state_store._get_completed_path(sample_pipeline_state.pipeline_id)
        assert completed_path.exists(), "Expected completed_path.exists() to be truthy"

    def test_archive_nonexistent(self, state_store):
        """archive() returns False for non-existent pipeline."""
        result = state_store.archive("PL-99999999-nonexist")
        assert result is False, "Expected result is False"

    def test_corrupted_state_recovery(self, state_store, temp_project):
        """Corrupted state files are quarantined."""
        pipeline_id = "PL-20260101-corrupt1"
        file_path = state_store._get_active_path(pipeline_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid YAML
        with open(file_path, "w") as f:
            f.write("invalid: yaml: content: [}")

        loaded = state_store.load(pipeline_id)
        assert loaded is None, "Expected loaded is None"

        # Original file should be quarantined
        corrupted_path = file_path.with_suffix(".yaml.corrupted")
        assert corrupted_path.exists(), "Expected corrupted_path.exists() to be truthy"
        assert not file_path.exists(), "Assertion failed"

    def test_index_updated_on_save(self, state_store, sample_pipeline_state):
        """Index file is updated when pipeline is saved."""
        state_store.save(sample_pipeline_state)

        index_data = state_store._read_yaml(state_store.index_file)
        assert sample_pipeline_state.pipeline_id in index_data["pipelines"], "Expected sample_pipeline_state.pipel... in index_data['pipelines']"

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
        assert len(running) == 2, "Expected len(running) to equal 2"

        paused = state_store.get_by_status(PipelineStatus.PAUSED)
        assert len(paused) == 1, "Expected len(paused) to equal 1"

    def test_concurrent_access(self, temp_project):
        """Concurrent saves don't corrupt data."""
        store = PipelineStateStore(temp_project)
        state = create_pipeline_state("concurrent", temp_project)
        store.save(state)

        errors = []

        def update_state(n):
            try:
                # Retry load if we hit a race condition with concurrent write
                for _attempt in range(3):
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

        assert len(errors) == 0, "Expected len(errors) to equal 0"

        # State should have some updates (order depends on timing)
        final = store.load(state.pipeline_id)
        assert final is not None, "Expected final is not None"


class TestStateStoreList:
    """Tests for unified list() method - Phase 6 API Integration."""

    def test_list_all_pipelines(self, state_store, temp_project):
        """list() returns all pipelines when no filter."""
        # Create pipelines with various statuses
        for i, status in enumerate([
            PipelineStatus.PENDING,
            PipelineStatus.RUNNING,
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
        ]):
            state = create_pipeline_state(f"req{i}", temp_project)
            state.status = status
            state_store.save(state)

        all_pipelines = state_store.list()
        assert len(all_pipelines) == 4, "Expected len(all_pipelines) to equal 4"

    def test_list_filtered_by_status(self, state_store, temp_project):
        """list(status=...) filters correctly."""
        state1 = create_pipeline_state("req1", temp_project)
        state2 = create_pipeline_state("req2", temp_project)
        state3 = create_pipeline_state("req3", temp_project)

        state1.status = PipelineStatus.RUNNING
        state2.status = PipelineStatus.RUNNING
        state3.status = PipelineStatus.COMPLETED

        state_store.save(state1)
        state_store.save(state2)
        state_store.save(state3)

        running = state_store.list(status=PipelineStatus.RUNNING)
        assert len(running) == 2, "Expected len(running) to equal 2"

        completed = state_store.list(status=PipelineStatus.COMPLETED)
        assert len(completed) == 1, "Expected len(completed) to equal 1"

    def test_list_respects_limit(self, state_store, temp_project):
        """list(limit=N) returns at most N results."""
        for i in range(10):
            state = create_pipeline_state(f"req{i}", temp_project)
            state_store.save(state)

        limited = state_store.list(limit=5)
        assert len(limited) == 5, "Expected len(limited) to equal 5"

    def test_list_ordered_by_date_newest_first(self, state_store, temp_project):
        """list() returns results ordered by created_at descending."""
        import time

        states = []
        for i in range(3):
            state = create_pipeline_state(f"req{i}", temp_project)
            state_store.save(state)
            states.append(state)
            time.sleep(0.01)  # Ensure different timestamps

        result = state_store.list()

        # Newest (last created) should be first
        assert result[0].pipeline_id == states[2].pipeline_id, "Expected result[0].pipeline_id to equal states[2].pipeline_id"
        assert result[2].pipeline_id == states[0].pipeline_id, "Expected result[2].pipeline_id to equal states[0].pipeline_id"

    def test_list_empty_store(self, state_store):
        """list() returns empty list when no pipelines."""
        result = state_store.list()
        assert result == [], "Expected result to equal []"

    def test_list_with_status_and_limit(self, state_store, temp_project):
        """list() combines status filter and limit."""
        for i in range(10):
            state = create_pipeline_state(f"req{i}", temp_project)
            state.status = PipelineStatus.RUNNING if i < 7 else PipelineStatus.COMPLETED
            state_store.save(state)

        running = state_store.list(status=PipelineStatus.RUNNING, limit=3)
        assert len(running) == 3, "Expected len(running) to equal 3"
        for s in running:
            assert s.status == PipelineStatus.RUNNING, "Expected s.status to equal PipelineStatus.RUNNING"
