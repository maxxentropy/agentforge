# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: minimal-context-tests

"""
Tests for minimal context components.

This file covers:
- Executor (minimal context executor)
- TaskStateStore (state persistence)
- WorkingMemoryManager (context window management)

TODO: Add comprehensive tests for each component.
"""



class TestMinimalContextExecutor:
    """Tests for MinimalContextExecutor."""

    def test_executor_import(self):
        """Verify executor can be imported."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor
        assert MinimalContextExecutor is not None


class TestTaskStateStore:
    """Tests for TaskStateStore."""

    def test_state_store_import(self):
        """Verify TaskStateStore can be imported."""
        from agentforge.core.harness.minimal_context.state_store import TaskStateStore
        assert TaskStateStore is not None


class TestWorkingMemoryManager:
    """Tests for WorkingMemoryManager."""

    def test_working_memory_import(self):
        """Verify WorkingMemoryManager can be imported."""
        from agentforge.core.harness.minimal_context.working_memory import WorkingMemoryManager
        assert WorkingMemoryManager is not None
