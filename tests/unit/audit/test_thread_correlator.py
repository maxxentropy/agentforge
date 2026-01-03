# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: thread-correlator-tests

"""Tests for ThreadCorrelator - agent delegation and parallel tracking."""

import pytest

from agentforge.core.audit.thread_correlator import (
    SpawnType,
    ThreadCorrelator,
    ThreadInfo,
    ThreadStatus,
)


class TestThreadCorrelator:
    """Tests for ThreadCorrelator."""

    def test_create_root_thread(self, tmp_path):
        """Create a root thread with no parent."""
        correlator = ThreadCorrelator(tmp_path)

        info = correlator.create_thread(
            thread_id="root-001",
            thread_type="pipeline",
            name="Test Pipeline",
            description="A test pipeline",
        )

        assert info.thread_id == "root-001", "Expected info.thread_id to equal 'root-001'"
        assert info.parent_thread_id is None, "Expected info.parent_thread_id is None"
        assert info.root_thread_id is None, "Expected info.root_thread_id is None"# Root has no root reference
        assert info.thread_type == "pipeline", "Expected info.thread_type to equal 'pipeline'"
        assert info.name == "Test Pipeline", "Expected info.name to equal 'Test Pipeline'"
        assert info.status == ThreadStatus.PENDING, "Expected info.status to equal ThreadStatus.PENDING"

    def test_spawn_child_thread(self, tmp_path):
        """Spawn a child thread from parent."""
        correlator = ThreadCorrelator(tmp_path)

        # Create parent
        parent = correlator.create_thread(
            thread_id="parent-001",
            thread_type="pipeline",
            name="Parent",
        )

        # Spawn child
        child = correlator.create_thread(
            thread_id="child-001",
            parent_thread_id="parent-001",
            thread_type="agent",
            name="Child Agent",
            spawn_type=SpawnType.DELEGATION,
            spawn_reason="Delegating security review",
        )

        assert child.parent_thread_id == "parent-001", "Expected child.parent_thread_id to equal 'parent-001'"
        assert child.root_thread_id == "parent-001", "Expected child.root_thread_id to equal 'parent-001'"
        assert child.spawn_type == SpawnType.DELEGATION, "Expected child.spawn_type to equal SpawnType.DELEGATION"
        assert child.spawn_reason == "Delegating security review", "Expected child.spawn_reason to equal 'Delegating security review'"

        # Parent should have child in list
        parent_updated = correlator.get_thread("parent-001")
        assert "child-001" in parent_updated.child_thread_ids, "Expected 'child-001' in parent_updated.child_thread..."

    def test_nested_spawning_tracks_root(self, tmp_path):
        """Nested spawns should track back to root."""
        correlator = ThreadCorrelator(tmp_path)

        # Root -> Child -> Grandchild
        correlator.create_thread(thread_id="root", thread_type="pipeline")
        correlator.create_thread(
            thread_id="child",
            parent_thread_id="root",
            thread_type="agent",
        )
        grandchild = correlator.create_thread(
            thread_id="grandchild",
            parent_thread_id="child",
            thread_type="task",
        )

        # Grandchild should trace back to root
        assert grandchild.parent_thread_id == "child", "Expected grandchild.parent_thread_id to equal 'child'"
        assert grandchild.root_thread_id == "root", "Expected grandchild.root_thread_id to equal 'root'"

    def test_get_children(self, tmp_path):
        """Get direct children of a thread."""
        correlator = ThreadCorrelator(tmp_path)

        correlator.create_thread(thread_id="parent", thread_type="pipeline")
        correlator.create_thread(
            thread_id="child1", parent_thread_id="parent", thread_type="agent"
        )
        correlator.create_thread(
            thread_id="child2", parent_thread_id="parent", thread_type="agent"
        )

        children = correlator.get_children("parent")

        assert len(children) == 2, "Expected len(children) to equal 2"
        child_ids = [c.thread_id for c in children]
        assert "child1" in child_ids, "Expected 'child1' in child_ids"
        assert "child2" in child_ids, "Expected 'child2' in child_ids"

    def test_get_ancestry(self, tmp_path):
        """Get ancestry chain from child to root."""
        correlator = ThreadCorrelator(tmp_path)

        correlator.create_thread(thread_id="root", thread_type="pipeline", name="Root")
        correlator.create_thread(
            thread_id="child", parent_thread_id="root", thread_type="agent", name="Child"
        )
        correlator.create_thread(
            thread_id="grandchild",
            parent_thread_id="child",
            thread_type="task",
            name="Grandchild",
        )

        ancestry = correlator.get_ancestry("grandchild")

        assert len(ancestry) == 3, "Expected len(ancestry) to equal 3"
        assert ancestry[0].thread_id == "grandchild", "Expected ancestry[0].thread_id to equal 'grandchild'"
        assert ancestry[1].thread_id == "child", "Expected ancestry[1].thread_id to equal 'child'"
        assert ancestry[2].thread_id == "root", "Expected ancestry[2].thread_id to equal 'root'"

    def test_thread_tree(self, tmp_path):
        """Build complete thread tree."""
        correlator = ThreadCorrelator(tmp_path)

        correlator.create_thread(thread_id="root", thread_type="pipeline")
        correlator.create_thread(
            thread_id="child1", parent_thread_id="root", thread_type="agent"
        )
        correlator.create_thread(
            thread_id="child2", parent_thread_id="root", thread_type="agent"
        )
        correlator.create_thread(
            thread_id="grandchild", parent_thread_id="child1", thread_type="task"
        )

        tree = correlator.get_thread_tree("root")

        assert tree["thread_id"] == "root", "Expected tree['thread_id'] to equal 'root'"
        assert len(tree["children"]) == 2, "Expected len(tree['children']) to equal 2"

        child1 = next(c for c in tree["children"] if c["thread_id"] == "child1")
        assert len(child1["children"]) == 1, "Expected len(child1['children']) to equal 1"
        assert child1["children"][0]["thread_id"] == "grandchild", "Expected child1['children'][0]['thre... to equal 'grandchild'"

    def test_parallel_group(self, tmp_path):
        """Create and track parallel execution group."""
        correlator = ThreadCorrelator(tmp_path)

        correlator.create_thread(thread_id="parent", thread_type="pipeline")

        tasks = [
            {"thread_id": "p1", "name": "Task 1", "description": "First parallel task"},
            {"thread_id": "p2", "name": "Task 2", "description": "Second parallel task"},
            {"thread_id": "p3", "name": "Task 3", "description": "Third parallel task"},
        ]

        threads = correlator.create_parallel_group(
            parent_thread_id="parent",
            group_id="parallel-test",
            tasks=tasks,
        )

        assert len(threads) == 3, "Expected len(threads) to equal 3"

        # All should have same parallel_group_id
        for i, thread in enumerate(threads):
            assert thread.parallel_group_id == "parallel-test", "Expected thread.parallel_group_id to equal 'parallel-test'"
            assert thread.parallel_index == i, "Expected thread.parallel_index to equal i"
            assert thread.parent_thread_id == "parent", "Expected thread.parent_thread_id to equal 'parent'"

        # Get parallel group
        group = correlator.get_parallel_group("parallel-test")
        assert len(group) == 3, "Expected len(group) to equal 3"
        assert [t.thread_id for t in group] == ["p1", "p2", "p3"], "Expected [t.thread_id for t in group] to equal ['p1', 'p2', 'p3']"

    def test_complete_thread(self, tmp_path):
        """Mark thread as completed with statistics."""
        correlator = ThreadCorrelator(tmp_path)

        correlator.create_thread(thread_id="test", thread_type="pipeline")
        correlator.start_thread("test")

        correlator.complete_thread(
            thread_id="test",
            outcome="success",
            transaction_count=10,
            total_tokens=5000,
            total_duration_ms=30000,
        )

        thread = correlator.get_thread("test")
        assert thread.status == ThreadStatus.COMPLETED, "Expected thread.status to equal ThreadStatus.COMPLETED"
        assert thread.outcome == "success", "Expected thread.outcome to equal 'success'"
        assert thread.transaction_count == 10, "Expected thread.transaction_count to equal 10"
        assert thread.total_tokens == 5000, "Expected thread.total_tokens to equal 5000"
        assert thread.completed_at is not None, "Expected thread.completed_at is not None"

    def test_complete_thread_failure(self, tmp_path):
        """Mark thread as failed."""
        correlator = ThreadCorrelator(tmp_path)

        correlator.create_thread(thread_id="test", thread_type="pipeline")
        correlator.start_thread("test")

        correlator.complete_thread(
            thread_id="test",
            outcome="failed",
            error="Test error message",
        )

        thread = correlator.get_thread("test")
        assert thread.status == ThreadStatus.FAILED, "Expected thread.status to equal ThreadStatus.FAILED"
        assert thread.error == "Test error message", "Expected thread.error to equal 'Test error message'"

    def test_thread_persistence(self, tmp_path):
        """Threads should persist across correlator instances."""
        # Create with first instance
        correlator1 = ThreadCorrelator(tmp_path)
        correlator1.create_thread(
            thread_id="persist-test",
            thread_type="pipeline",
            name="Persistent Thread",
        )

        # Load with second instance
        correlator2 = ThreadCorrelator(tmp_path)
        thread = correlator2.get_thread("persist-test")

        assert thread is not None, "Expected thread is not None"
        assert thread.thread_id == "persist-test", "Expected thread.thread_id to equal 'persist-test'"
        assert thread.name == "Persistent Thread", "Expected thread.name to equal 'Persistent Thread'"


class TestSpawnType:
    """Tests for SpawnType enum."""

    def test_spawn_types(self):
        """All spawn types should be valid."""
        assert SpawnType.DELEGATION.value == "delegation", "Expected SpawnType.DELEGATION.value to equal 'delegation'"
        assert SpawnType.PARALLEL.value == "parallel", "Expected SpawnType.PARALLEL.value to equal 'parallel'"
        assert SpawnType.RETRY.value == "retry", "Expected SpawnType.RETRY.value to equal 'retry'"
        assert SpawnType.ESCALATION.value == "escalation", "Expected SpawnType.ESCALATION.value to equal 'escalation'"
        assert SpawnType.PIPELINE_STAGE.value == "pipeline_stage", "Expected SpawnType.PIPELINE_STAGE.value to equal 'pipeline_stage'"
