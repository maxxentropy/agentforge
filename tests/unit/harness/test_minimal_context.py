# @spec_file: .agentforge/specs/harness-minimal-context-v1.yaml
# @spec_id: harness-minimal-context-v1
# @component_id: harness-minimal_context-__init__
# @impl_path: tools/harness/minimal_context/__init__.py

"""
Tests for Minimal Context Architecture
======================================

Tests the stateless step execution with bounded context.
"""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from tools.harness.minimal_context import (
    TaskStateStore,
    TaskState,
    TaskPhase,
    TokenBudget,
    TOKEN_BUDGET_LIMITS,
    WorkingMemoryManager,
    WorkingMemoryItem,
    ContextSchema,
    FixViolationSchema,
    get_schema_for_task,
    ContextBuilder,
    MinimalContextExecutor,
    StepOutcome,
)
from tools.harness.minimal_context.token_budget import (
    estimate_tokens,
    compress_file_content,
    compress_recent_actions,
)


class TestTokenBudget:
    """Tests for token budget enforcement."""

    def test_estimate_tokens(self):
        """Test token estimation."""
        # ~4 chars per token
        text = "hello world"  # 11 chars
        tokens = estimate_tokens(text)
        assert tokens == 2  # 11 // 4 = 2

    def test_estimate_tokens_empty(self):
        """Test empty string."""
        assert estimate_tokens("") == 0

    def test_budget_limits_exist(self):
        """Test default limits are defined."""
        assert "system_prompt" in TOKEN_BUDGET_LIMITS
        assert "current_state" in TOKEN_BUDGET_LIMITS
        assert TOKEN_BUDGET_LIMITS["current_state"] == 4500

    def test_check_allocation_under_budget(self):
        """Test allocation check for content under budget."""
        budget = TokenBudget()
        content = "short content"
        alloc = budget.check_allocation("system_prompt", content)

        assert not alloc.over_budget
        assert alloc.estimated_tokens < alloc.budget

    def test_check_allocation_over_budget(self):
        """Test allocation check for content over budget."""
        budget = TokenBudget()
        # Create content larger than budget
        content = "x" * (TOKEN_BUDGET_LIMITS["system_prompt"] * 8)
        alloc = budget.check_allocation("system_prompt", content)

        assert alloc.over_budget

    def test_compress_to_fit(self):
        """Test compression to fit budget."""
        budget = TokenBudget()
        # Large content
        content = "line\n" * 1000
        compressed, was_compressed = budget.compress_to_fit("system_prompt", content)

        assert was_compressed
        assert estimate_tokens(compressed) <= TOKEN_BUDGET_LIMITS["system_prompt"]

    def test_compress_file_content(self):
        """Test file content compression."""
        content = "\n".join([f"line {i}" for i in range(1000)])
        compressed = compress_file_content(content, budget_tokens=500)

        assert "lines omitted" in compressed
        assert estimate_tokens(compressed) <= 500

    def test_compress_recent_actions(self):
        """Test action list compression keeps most recent."""
        content = "\n".join([f"- step: {i}\n  action: test" for i in range(50)])
        compressed = compress_recent_actions(content, budget_tokens=300)

        # Should compress and include omission message
        assert "omitted" in compressed or "step: 49" in compressed
        # Should keep recent actions
        assert "step: 49" in compressed

    def test_allocate_all(self):
        """Test allocating all sections."""
        budget = TokenBudget()
        sections = {
            "system_prompt": "You are a helpful assistant.",
            "task_frame": "Task: Fix a bug",
            "current_state": "File content here",
        }

        allocations = budget.allocate_all(sections)

        assert "system_prompt" in allocations
        assert "task_frame" in allocations
        assert budget.is_within_budget(allocations)


class TestWorkingMemory:
    """Tests for working memory manager."""

    @pytest.fixture
    def temp_task_dir(self):
        """Create temporary task directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_add_and_get_items(self, temp_task_dir):
        """Test adding and retrieving items."""
        manager = WorkingMemoryManager(temp_task_dir)

        manager.add("action_result", "action_1", {"action": "test"}, step=1)
        items = manager.get_items()

        assert len(items) == 1
        assert items[0].key == "action_1"

    def test_add_action_result(self, temp_task_dir):
        """Test convenience method for action results."""
        manager = WorkingMemoryManager(temp_task_dir)

        manager.add_action_result(
            action="edit_file",
            result="success",
            summary="Edited file.py",
            step=5,
            target="file.py",
        )

        results = manager.get_action_results()
        assert len(results) == 1
        assert results[0]["action"] == "edit_file"
        assert results[0]["step"] == 5

    def test_load_context(self, temp_task_dir):
        """Test loading additional context."""
        manager = WorkingMemoryManager(temp_task_dir)

        manager.load_context(
            "full_file:test.py",
            "def hello(): pass",
            step=1,
            expires_after_steps=3,
        )

        context = manager.get_loaded_context(current_step=2)
        assert "full_file:test.py" in context

        # Should expire after 3 steps
        context = manager.get_loaded_context(current_step=5)
        assert "full_file:test.py" not in context

    def test_fifo_eviction(self, temp_task_dir):
        """Test FIFO eviction when over limit."""
        manager = WorkingMemoryManager(temp_task_dir, max_items=3)

        for i in range(5):
            manager.add("action_result", f"action_{i}", {"n": i}, step=i)

        items = manager.get_items()
        assert len(items) == 3

        # Should have kept most recent
        keys = [i.key for i in items]
        assert "action_4" in keys
        assert "action_0" not in keys

    def test_pinned_items_not_evicted(self, temp_task_dir):
        """Test pinned items are not evicted."""
        manager = WorkingMemoryManager(temp_task_dir, max_items=3)

        # Add pinned item
        manager.add("note", "important", "critical info", pinned=True)

        # Add more items
        for i in range(4):
            manager.add("action_result", f"action_{i}", {"n": i}, step=i)

        items = manager.get_items()

        # Pinned item should still be there
        keys = [i.key for i in items]
        assert "important" in keys

    def test_remove(self, temp_task_dir):
        """Test removing items."""
        manager = WorkingMemoryManager(temp_task_dir)

        manager.add("action_result", "to_remove", {})
        manager.add("action_result", "to_keep", {})

        removed = manager.remove("to_remove")
        assert removed

        items = manager.get_items()
        assert len(items) == 1
        assert items[0].key == "to_keep"

    def test_clear(self, temp_task_dir):
        """Test clearing all items."""
        manager = WorkingMemoryManager(temp_task_dir)

        manager.add("action_result", "a1", {})
        manager.add("action_result", "a2", {}, pinned=True)
        manager.add("action_result", "a3", {})

        cleared = manager.clear(keep_pinned=True)
        assert cleared == 2

        items = manager.get_items()
        assert len(items) == 1
        assert items[0].key == "a2"


class TestTaskStateStore:
    """Tests for task state persistence."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_task(self, temp_project):
        """Test creating a task."""
        store = TaskStateStore(temp_project)

        state = store.create_task(
            task_type="fix_violation",
            goal="Fix the bug",
            success_criteria=["Tests pass", "Check passes"],
        )

        assert state.task_id.startswith("task_")
        assert state.task_type == "fix_violation"
        assert state.phase == TaskPhase.INIT

    def test_load_task(self, temp_project):
        """Test loading a task."""
        store = TaskStateStore(temp_project)

        created = store.create_task(
            task_type="fix_violation",
            goal="Fix the bug",
            success_criteria=["Tests pass"],
            task_id="test-task-1",
        )

        loaded = store.load("test-task-1")

        assert loaded is not None
        assert loaded.task_id == "test-task-1"
        assert loaded.goal == "Fix the bug"

    def test_update_phase(self, temp_project):
        """Test updating task phase."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            task_id="test-task-2",
        )

        store.update_phase("test-task-2", TaskPhase.IMPLEMENT)

        loaded = store.load("test-task-2")
        assert loaded.phase == TaskPhase.IMPLEMENT

    def test_increment_step(self, temp_project):
        """Test incrementing step counter."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            task_id="test-task-3",
        )

        step1 = store.increment_step("test-task-3")
        step2 = store.increment_step("test-task-3")

        assert step1 == 1
        assert step2 == 2

    def test_record_action(self, temp_project):
        """Test recording actions."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            task_id="test-task-4",
        )

        record = store.record_action(
            task_id="test-task-4",
            action="read_file",
            target="test.py",
            parameters={"path": "test.py"},
            result="success",
            summary="Read file",
        )

        assert record.action == "read_file"
        assert record.step == 0

        recent = store.get_recent_actions("test-task-4")
        assert len(recent) == 1

    def test_update_verification(self, temp_project):
        """Test updating verification status."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            task_id="test-task-5",
        )

        store.update_verification(
            "test-task-5",
            checks_passing=3,
            checks_failing=1,
            tests_passing=True,
        )

        loaded = store.load("test-task-5")
        assert loaded.verification.checks_passing == 3
        assert loaded.verification.tests_passing
        assert not loaded.verification.ready_for_completion

    def test_save_and_load_artifact(self, temp_project):
        """Test artifact persistence."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            task_id="test-task-6",
        )

        store.save_artifact("test-task-6", "inputs", "violation.yaml", "id: V-001")
        content = store.load_artifact("test-task-6", "inputs", "violation.yaml")

        assert content == "id: V-001"

    def test_list_tasks(self, temp_project):
        """Test listing tasks."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix 1",
            success_criteria=["Pass"],
            task_id="task-a",
        )
        store.create_task(
            task_type="fix_violation",
            goal="Fix 2",
            success_criteria=["Pass"],
            task_id="task-b",
        )

        tasks = store.list_tasks()
        assert len(tasks) == 2
        assert "task-a" in tasks
        assert "task-b" in tasks

    def test_delete_task(self, temp_project):
        """Test deleting tasks."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            task_id="task-to-delete",
        )

        deleted = store.delete_task("task-to-delete")
        assert deleted

        loaded = store.load("task-to-delete")
        assert loaded is None


class TestContextSchema:
    """Tests for context schemas."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_get_schema_for_task(self, temp_project):
        """Test getting schema by task type."""
        schema = get_schema_for_task("fix_violation", temp_project)
        assert isinstance(schema, FixViolationSchema)

    def test_fix_violation_schema(self, temp_project):
        """Test fix violation schema."""
        schema = FixViolationSchema(temp_project)

        state = TaskState(
            task_id="test",
            task_type="fix_violation",
            goal="Fix bug",
            success_criteria=["Pass"],
            context_data={
                "violation_id": "V-001",
                "check_id": "check-test",
                "file_path": "test.py",
                "message": "Missing docstring",
            },
        )

        current_state = schema.get_current_state(state)
        assert "violation" in current_state
        assert current_state["violation"]["id"] == "V-001"

    def test_available_actions(self, temp_project):
        """Test getting available actions."""
        schema = FixViolationSchema(temp_project)

        state = TaskState(
            task_id="test",
            task_type="fix_violation",
            goal="Fix bug",
            success_criteria=["Pass"],
            phase=TaskPhase.IMPLEMENT,
        )

        actions = schema.get_available_actions(state)
        action_names = [a.name for a in actions]

        assert "read_file" in action_names
        assert "edit_file" in action_names
        assert "run_check" in action_names

    def test_system_prompt(self, temp_project):
        """Test getting system prompt."""
        schema = FixViolationSchema(temp_project)

        state = TaskState(
            task_id="test",
            task_type="fix_violation",
            goal="Fix bug",
            success_criteria=["Pass"],
        )

        prompt = schema.get_system_prompt(state)
        assert "conformance violation" in prompt.lower()


class TestContextBuilder:
    """Tests for context building."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_build_context(self, temp_project):
        """Test building context for a task."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix the bug",
            success_criteria=["Tests pass", "Check passes"],
            context_data={
                "violation_id": "V-001",
                "check_id": "check-test",
                "file_path": "test.py",
                "message": "Error",
            },
            task_id="build-test",
        )

        builder = ContextBuilder(temp_project, store)
        context = builder.build("build-test")

        assert context.system_prompt
        assert context.user_message
        assert context.total_tokens > 0

    def test_build_messages(self, temp_project):
        """Test building messages for API call."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix the bug",
            success_criteria=["Tests pass"],
            context_data={
                "violation_id": "V-001",
            },
            task_id="msg-test",
        )

        builder = ContextBuilder(temp_project, store)
        messages = builder.build_messages("msg-test")

        # Should always be exactly 2 messages
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_token_breakdown(self, temp_project):
        """Test token breakdown analysis."""
        store = TaskStateStore(temp_project)

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            task_id="breakdown-test",
        )

        builder = ContextBuilder(temp_project, store)
        breakdown = builder.get_token_breakdown("breakdown-test")

        assert "total_tokens" in breakdown
        assert "sections" in breakdown
        assert breakdown["within_budget"]

    def test_context_bounded(self, temp_project):
        """Test that context stays within budget."""
        store = TaskStateStore(temp_project)

        # Create task with lots of context data
        large_context = {
            "violation_id": "V-001",
            "file_content": "x" * 10000,  # Large content
        }

        store.create_task(
            task_type="fix_violation",
            goal="Fix",
            success_criteria=["Pass"],
            context_data=large_context,
            task_id="bounded-test",
        )

        builder = ContextBuilder(temp_project, store, max_tokens=8000)
        context = builder.build("bounded-test")

        # Should be compressed to fit
        assert context.total_tokens <= 8000


class TestMinimalContextExecutor:
    """Tests for the minimal context executor."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_executor_creation(self, temp_project):
        """Test creating an executor."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            action_executors={},
        )

        assert executor is not None

    def test_register_action(self, temp_project):
        """Test registering actions."""
        executor = MinimalContextExecutor(project_path=temp_project)

        def my_action(name, params, state):
            return {"status": "success", "summary": "Done"}

        executor.register_action("my_action", my_action)
        assert "my_action" in executor.action_executors

    def test_step_outcome_to_dict(self):
        """Test StepOutcome serialization."""
        outcome = StepOutcome(
            success=True,
            action_name="read_file",
            action_params={"path": "test.py"},
            result="success",
            summary="Read file",
            should_continue=True,
            tokens_used=1000,
            duration_ms=500,
        )

        d = outcome.to_dict()
        assert d["success"]
        assert d["action_name"] == "read_file"
        assert d["tokens_used"] == 1000
