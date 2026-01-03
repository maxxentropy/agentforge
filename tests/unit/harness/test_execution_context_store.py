# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: tools-harness-execution_context_store
# @impl_path: tools/harness/execution_context_store.py

"""Tests for Execution Context Store."""

import tempfile
from pathlib import Path

import pytest

from agentforge.core.harness.execution_context_store import (
    ExecutionContextStore,
    create_execution_store,
)
from agentforge.core.harness.llm_executor_domain import (
    ActionType,
    AgentAction,
    ConversationMessage,
    ExecutionContext,
    StepResult,
    ToolCall,
    ToolResult,
)


class TestExecutionContextStore:
    """Tests for ExecutionContextStore."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a store with temp directory."""
        return ExecutionContextStore(temp_dir)

    @pytest.fixture
    def sample_context(self):
        """Create a sample execution context."""
        context = ExecutionContext(
            session_id="test-session-001",
            task_description="Fix the authentication bug",
            current_phase="execute",
            available_tools=["read_file", "write_file", "bash"],
            iteration=3,
            tokens_used=5000,
            token_budget=100000
        )
        context.add_user_message("Please fix the auth bug")
        context.add_assistant_message("I'll start by reading the auth file")
        return context

    def test_save_and_load_context(self, store, sample_context):
        """Save and load context round-trip."""
        # Save
        path = store.save_context(sample_context)
        assert path.exists(), "Expected path.exists() to be truthy"

        # Load
        loaded = store.load_context(sample_context.session_id)
        assert loaded is not None, "Expected loaded is not None"
        assert loaded.session_id == sample_context.session_id, "Expected loaded.session_id to equal sample_context.session_id"
        assert loaded.task_description == sample_context.task_description, "Expected loaded.task_description to equal sample_context.task_descrip..."
        assert loaded.current_phase == sample_context.current_phase, "Expected loaded.current_phase to equal sample_context.current_phase"
        assert loaded.available_tools == sample_context.available_tools, "Expected loaded.available_tools to equal sample_context.available_tools"
        assert loaded.iteration == sample_context.iteration, "Expected loaded.iteration to equal sample_context.iteration"
        assert loaded.tokens_used == sample_context.tokens_used, "Expected loaded.tokens_used to equal sample_context.tokens_used"
        assert len(loaded.conversation_history) == 2, "Expected len(loaded.conversation_his... to equal 2"

    def test_load_nonexistent_context(self, store):
        """Load returns None for nonexistent session."""
        loaded = store.load_context("nonexistent-session")
        assert loaded is None, "Expected loaded is None"

    def test_append_step(self, store):
        """Append step results to history."""
        session_id = "test-session-001"

        # Create step results
        step1 = StepResult.success_step(
            action=AgentAction.tool_action(
                [ToolCall(name="read_file", parameters={"path": "/test.py"})],
                "Reading the file"
            ),
            tool_results=[ToolResult.success_result("read_file", "file content")],
            tokens_used=1000,
            duration=0.5
        )

        step2 = StepResult.success_step(
            action=AgentAction.complete_action("Done", "All tests pass"),
            tool_results=[],
            tokens_used=500,
            duration=0.3
        )

        # Append steps
        path1 = store.append_step(session_id, step1)
        path2 = store.append_step(session_id, step2)

        assert path1 == path2, "Expected path1 to equal path2"# Same history file
        assert path1.exists(), "Expected path1.exists() to be truthy"

        # Load history
        history = store.get_history(session_id)
        assert len(history) == 2, "Expected len(history) to equal 2"
        assert history[0].action.action_type == ActionType.TOOL_CALL, "Expected history[0].action.action_type to equal ActionType.TOOL_CALL"
        assert history[1].action.action_type == ActionType.COMPLETE, "Expected history[1].action.action_type to equal ActionType.COMPLETE"

    def test_get_empty_history(self, store):
        """Get history for session with no steps."""
        history = store.get_history("empty-session")
        assert history == [], "Expected history to equal []"

    def test_delete_context(self, store, sample_context):
        """Delete context and history."""
        # Save context and step
        store.save_context(sample_context)
        step = StepResult.failure_step("Test error")
        store.append_step(sample_context.session_id, step)

        # Verify files exist
        context_file = store._get_session_dir(sample_context.session_id) / "execution_context.yaml"
        history_file = store._get_session_dir(sample_context.session_id) / "step_history.yaml"
        assert context_file.exists(), "Expected context_file.exists() to be truthy"
        assert history_file.exists(), "Expected history_file.exists() to be truthy"

        # Delete
        result = store.delete_context(sample_context.session_id)
        assert result is True, "Expected result is True"
        assert not context_file.exists(), "Assertion failed"
        assert not history_file.exists(), "Assertion failed"

    def test_delete_nonexistent_context(self, store):
        """Delete returns False for nonexistent session."""
        result = store.delete_context("nonexistent")
        assert result is False, "Expected result is False"

    def test_list_sessions(self, store):
        """List all sessions with execution context."""
        # Create contexts for multiple sessions
        for i in range(3):
            context = ExecutionContext(
                session_id=f"session-{i}",
                task_description=f"Task {i}",
                current_phase="execute",
                available_tools=[]
            )
            store.save_context(context)

        sessions = store.list_sessions()
        assert len(sessions) == 3, "Expected len(sessions) to equal 3"
        assert "session-0" in sessions, "Expected 'session-0' in sessions"
        assert "session-1" in sessions, "Expected 'session-1' in sessions"
        assert "session-2" in sessions, "Expected 'session-2' in sessions"

    def test_get_step_count(self, store):
        """Get step count for session."""
        session_id = "step-count-test"

        # Initially zero
        assert store.get_step_count(session_id) == 0, "Expected store.get_step_count(sessio... to equal 0"

        # Add steps
        for i in range(5):
            step = StepResult.success_step(
                action=AgentAction.think_action(f"Step {i}"),
                tool_results=[],
                tokens_used=100,
                duration=0.1
            )
            store.append_step(session_id, step)

        assert store.get_step_count(session_id) == 5, "Expected store.get_step_count(sessio... to equal 5"


class TestSerializationRoundTrip:
    """Tests for serialization round-trip of domain entities."""

    def test_tool_call_round_trip(self):
        """ToolCall serializes and deserializes correctly."""
        original = ToolCall(
            name="read_file",
            parameters={"path": "/test.py", "encoding": "utf-8"}
        )

        data = original.to_dict()
        restored = ToolCall.from_dict(data)

        assert restored.name == original.name, "Expected restored.name to equal original.name"
        assert restored.parameters == original.parameters, "Expected restored.parameters to equal original.parameters"
        assert restored.category == original.category, "Expected restored.category to equal original.category"

    def test_tool_result_round_trip(self):
        """ToolResult serializes and deserializes correctly."""
        original = ToolResult.success_result("grep", "Match found at line 42", 0.15)

        data = original.to_dict()
        restored = ToolResult.from_dict(data)

        assert restored.tool_name == original.tool_name, "Expected restored.tool_name to equal original.tool_name"
        assert restored.success == original.success, "Expected restored.success to equal original.success"
        assert restored.output == original.output, "Expected restored.output to equal original.output"
        assert restored.duration_seconds == original.duration_seconds, "Expected restored.duration_seconds to equal original.duration_seconds"

    def test_agent_action_round_trip(self):
        """AgentAction serializes and deserializes correctly."""
        original = AgentAction.tool_action(
            tool_calls=[
                ToolCall(name="read_file", parameters={"path": "/a.py"}),
                ToolCall(name="grep", parameters={"pattern": "def foo"})
            ],
            reasoning="Need to find the function definition"
        )
        original.metadata = {"confidence": 0.9}

        data = original.to_dict()
        restored = AgentAction.from_dict(data)

        assert restored.action_type == original.action_type, "Expected restored.action_type to equal original.action_type"
        assert restored.reasoning == original.reasoning, "Expected restored.reasoning to equal original.reasoning"
        assert len(restored.tool_calls) == 2, "Expected len(restored.tool_calls) to equal 2"
        assert restored.tool_calls[0].name == "read_file", "Expected restored.tool_calls[0].name to equal 'read_file'"
        assert restored.metadata == original.metadata, "Expected restored.metadata to equal original.metadata"

    def test_conversation_message_round_trip(self):
        """ConversationMessage serializes and deserializes correctly."""
        tool_calls = [ToolCall(name="bash", parameters={"command": "ls"})]
        original = ConversationMessage.assistant_message(
            "Running command",
            tool_calls=tool_calls
        )

        data = original.to_dict()
        restored = ConversationMessage.from_dict(data)

        assert restored.role == original.role, "Expected restored.role to equal original.role"
        assert restored.content == original.content, "Expected restored.content to equal original.content"
        assert len(restored.tool_calls) == 1, "Expected len(restored.tool_calls) to equal 1"
        assert restored.tool_calls[0].name == "bash", "Expected restored.tool_calls[0].name to equal 'bash'"
        # Timestamp should be preserved
        assert abs((restored.timestamp - original.timestamp).total_seconds()) < 1, "Expected abs((restored.timestamp - o... < 1"

    def test_execution_context_round_trip(self):
        """ExecutionContext serializes and deserializes correctly."""
        original = ExecutionContext(
            session_id="ctx-test-001",
            task_description="Complex task",
            current_phase="analyze",
            available_tools=["read_file", "write_file", "grep"],
            memory_context={"key": "value", "nested": {"a": 1}},
            iteration=5,
            tokens_used=12000,
            token_budget=100000
        )
        original.add_user_message("Do something")
        original.add_assistant_message("I'll help")
        original.add_tool_results([ToolResult.success_result("test", "ok")])

        data = original.to_dict()
        restored = ExecutionContext.from_dict(data)

        assert restored.session_id == original.session_id, "Expected restored.session_id to equal original.session_id"
        assert restored.task_description == original.task_description, "Expected restored.task_description to equal original.task_description"
        assert restored.current_phase == original.current_phase, "Expected restored.current_phase to equal original.current_phase"
        assert restored.available_tools == original.available_tools, "Expected restored.available_tools to equal original.available_tools"
        assert restored.memory_context == original.memory_context, "Expected restored.memory_context to equal original.memory_context"
        assert restored.iteration == original.iteration, "Expected restored.iteration to equal original.iteration"
        assert restored.tokens_used == original.tokens_used, "Expected restored.tokens_used to equal original.tokens_used"
        assert restored.token_budget == original.token_budget, "Expected restored.token_budget to equal original.token_budget"
        assert len(restored.conversation_history) == 3, "Expected len(restored.conversation_h... to equal 3"

    def test_step_result_round_trip(self):
        """StepResult serializes and deserializes correctly."""
        action = AgentAction.tool_action(
            [ToolCall(name="edit_file", parameters={"path": "/x.py"})],
            "Making changes"
        )
        tool_results = [
            ToolResult.success_result("edit_file", "OK", 0.1),
            ToolResult.failure_result("lint", "Error on line 5", 0.05)
        ]

        original = StepResult.success_step(
            action=action,
            tool_results=tool_results,
            tokens_used=2500,
            duration=1.5
        )

        data = original.to_dict()
        restored = StepResult.from_dict(data)

        assert restored.success == original.success, "Expected restored.success to equal original.success"
        assert restored.tokens_used == original.tokens_used, "Expected restored.tokens_used to equal original.tokens_used"
        assert restored.duration_seconds == original.duration_seconds, "Expected restored.duration_seconds to equal original.duration_seconds"
        assert restored.should_continue == original.should_continue, "Expected restored.should_continue to equal original.should_continue"
        assert restored.action.action_type == ActionType.TOOL_CALL, "Expected restored.action.action_type to equal ActionType.TOOL_CALL"
        assert len(restored.tool_results) == 2, "Expected len(restored.tool_results) to equal 2"


class TestCreateExecutionStore:
    """Tests for factory function."""

    def test_creates_store_with_default_path(self):
        """Factory creates store with default path."""
        store = create_execution_store()
        assert isinstance(store, ExecutionContextStore), "Expected isinstance() to be truthy"
        assert ".agentforge" in str(store.base_path), "Expected '.agentforge' in str(store.base_path)"
        assert "sessions" in str(store.base_path), "Expected 'sessions' in str(store.base_path)"

    def test_creates_store_with_custom_path(self):
        """Factory creates store with custom path."""
        custom_path = Path("/tmp/custom")
        store = create_execution_store(custom_path)
        assert store.base_path == custom_path, "Expected store.base_path to equal custom_path"
