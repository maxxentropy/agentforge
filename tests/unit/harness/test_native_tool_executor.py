# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: llm-integration-v1
# @component_id: native-tool-executor
# @impl_path: src/agentforge/core/harness/minimal_context/native_tool_executor.py

"""
Tests for Native Tool Executor
==============================

Tests verify:
- Tool execution via registered handlers
- Error handling for unknown tools
- Handler exception handling
- Execution logging

Note: Handler-specific tests (read_file, write_file, etc.) are in
tests/unit/harness/tool_handlers/ directory.
"""


from agentforge.core.harness.minimal_context.native_tool_executor import NativeToolExecutor
from agentforge.core.llm.interface import ToolCall


class TestNativeToolExecutor:
    """Tests for NativeToolExecutor class."""

    def test_execute_registered_action(self):
        """Execute a registered action successfully."""
        executor = NativeToolExecutor()
        executor.register_action("greet", lambda p: f"Hello, {p['name']}!")

        tool_call = ToolCall(id="tc_1", name="greet", input={"name": "World"})
        result = executor.execute(tool_call)

        assert result.tool_use_id == "tc_1"
        assert result.content == "Hello, World!"
        assert not result.is_error

    def test_execute_unknown_action_returns_error(self):
        """Unknown action returns error result."""
        executor = NativeToolExecutor()

        tool_call = ToolCall(id="tc_1", name="unknown", input={})
        result = executor.execute(tool_call)

        assert result.tool_use_id == "tc_1"
        assert result.is_error
        assert "Unknown tool: unknown" in result.content

    def test_handler_exception_returns_error(self):
        """Handler exception is caught and returned as error."""
        def failing_handler(params):
            raise ValueError("Something went wrong")

        executor = NativeToolExecutor()
        executor.register_action("fail", failing_handler)

        tool_call = ToolCall(id="tc_1", name="fail", input={})
        result = executor.execute(tool_call)

        assert result.is_error
        assert "Tool execution failed" in result.content
        assert "Something went wrong" in result.content

    def test_none_result_returns_success(self):
        """Handler returning None results in 'Success' message."""
        executor = NativeToolExecutor()
        executor.register_action("noop", lambda p: None)

        tool_call = ToolCall(id="tc_1", name="noop", input={})
        result = executor.execute(tool_call)

        assert not result.is_error
        assert result.content == "Success"

    def test_dict_result_returns_json(self):
        """Handler returning dict is serialized to JSON."""
        executor = NativeToolExecutor()
        executor.register_action("data", lambda p: {"key": "value", "count": 42})

        tool_call = ToolCall(id="tc_1", name="data", input={})
        result = executor.execute(tool_call)

        assert not result.is_error
        assert '"key": "value"' in result.content
        assert '"count": 42' in result.content

    def test_register_actions_bulk(self):
        """Register multiple actions at once."""
        executor = NativeToolExecutor()
        executor.register_actions({
            "action1": lambda p: "result1",
            "action2": lambda p: "result2",
        })

        assert executor.has_action("action1")
        assert executor.has_action("action2")

    def test_list_actions(self):
        """List registered actions."""
        executor = NativeToolExecutor()
        executor.register_actions({
            "c_action": lambda p: "",
            "a_action": lambda p: "",
            "b_action": lambda p: "",
        })

        actions = executor.list_actions()
        assert actions == ["a_action", "b_action", "c_action"]

    def test_has_action(self):
        """Check if action is registered."""
        executor = NativeToolExecutor()
        executor.register_action("exists", lambda p: "")

        assert executor.has_action("exists")
        assert not executor.has_action("not_exists")

    def test_context_passed_to_handler(self):
        """Shared context is passed to handler."""
        context = {"project_path": "/test/path"}
        executor = NativeToolExecutor(context=context)

        received_context = {}

        def handler(params):
            nonlocal received_context
            received_context = params.get("_context", {})
            return "done"

        executor.register_action("check", handler)

        tool_call = ToolCall(id="tc_1", name="check", input={"arg": "value"})
        executor.execute(tool_call)

        assert received_context == context


class TestExecutionLogging:
    """Tests for execution logging."""

    def test_successful_execution_logged(self):
        """Successful execution is logged."""
        executor = NativeToolExecutor()
        executor.register_action("test", lambda p: "result")

        tool_call = ToolCall(id="tc_1", name="test", input={"param": "value"})
        executor.execute(tool_call)

        log = executor.get_execution_log()
        assert len(log) == 1
        assert log[0]["tool_id"] == "tc_1"
        assert log[0]["tool_name"] == "test"
        assert log[0]["input"] == {"param": "value"}
        assert log[0]["result"] == "result"
        assert log[0]["success"] is True
        assert log[0]["error"] is None

    def test_failed_execution_logged(self):
        """Failed execution is logged with error."""
        executor = NativeToolExecutor()
        executor.register_action("fail", lambda p: 1 / 0)

        tool_call = ToolCall(id="tc_1", name="fail", input={})
        executor.execute(tool_call)

        log = executor.get_execution_log()
        assert len(log) == 1
        assert log[0]["success"] is False
        assert log[0]["error"] is not None
        assert "division by zero" in log[0]["error"]

    def test_unknown_action_logged(self):
        """Unknown action attempt is logged."""
        executor = NativeToolExecutor()

        tool_call = ToolCall(id="tc_1", name="unknown", input={})
        executor.execute(tool_call)

        log = executor.get_execution_log()
        assert len(log) == 1
        assert log[0]["success"] is False
        assert "Unknown tool" in log[0]["error"]

    def test_clear_execution_log(self):
        """Execution log can be cleared."""
        executor = NativeToolExecutor()
        executor.register_action("test", lambda p: "")

        tool_call = ToolCall(id="tc_1", name="test", input={})
        executor.execute(tool_call)

        assert len(executor.get_execution_log()) == 1

        executor.clear_execution_log()
        assert len(executor.get_execution_log()) == 0

    def test_multiple_executions_logged(self):
        """Multiple executions are logged in order."""
        executor = NativeToolExecutor()
        executor.register_action("test", lambda p: p.get("n", 0))

        for i in range(3):
            tool_call = ToolCall(id=f"tc_{i}", name="test", input={"n": i})
            executor.execute(tool_call)

        log = executor.get_execution_log()
        assert len(log) == 3
        assert [e["tool_id"] for e in log] == ["tc_0", "tc_1", "tc_2"]


class TestIntegrationWithToolHandlers:
    """Integration tests with actual tool handlers."""

    def test_executor_with_standard_handlers(self, tmp_path):
        """NativeToolExecutor works with standard handlers."""
        from agentforge.core.harness.minimal_context.tool_handlers import (
            create_standard_handlers,
        )

        # Set up executor with handlers
        handlers = create_standard_handlers(tmp_path)
        executor = NativeToolExecutor(actions=handlers)

        # Create test file
        test_file = tmp_path / "source.txt"
        test_file.write_text("Source content")

        # Execute read_file
        read_call = ToolCall(
            id="tc_1",
            name="read_file",
            input={"path": str(test_file)},
        )
        result = executor.execute(read_call)

        assert not result.is_error
        assert "SUCCESS" in result.content
        assert "Source content" in result.content

    def test_complete_handler_integration(self, tmp_path):
        """Complete handler works through executor."""
        from agentforge.core.harness.minimal_context.tool_handlers import (
            create_standard_handlers,
        )

        handlers = create_standard_handlers(tmp_path)
        executor = NativeToolExecutor(actions=handlers)

        complete_call = ToolCall(
            id="tc_1",
            name="complete",
            input={"summary": "Task finished successfully"},
        )
        result = executor.execute(complete_call)

        assert not result.is_error
        assert "COMPLETE" in result.content
        assert "Task finished successfully" in result.content

    def test_escalate_handler_integration(self, tmp_path):
        """Escalate handler works through executor."""
        from agentforge.core.harness.minimal_context.tool_handlers import (
            create_standard_handlers,
        )

        handlers = create_standard_handlers(tmp_path)
        executor = NativeToolExecutor(actions=handlers)

        escalate_call = ToolCall(
            id="tc_1",
            name="escalate",
            input={"reason": "Need human review"},
        )
        result = executor.execute(escalate_call)

        assert not result.is_error
        assert "ESCALATE" in result.content
        assert "Need human review" in result.content
