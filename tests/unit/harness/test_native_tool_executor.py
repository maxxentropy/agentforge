# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
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
- Standard handler factories
"""

import pytest
import tempfile
from pathlib import Path
from typing import Any, Dict

from agentforge.core.llm.interface import ToolCall, ToolResult
from agentforge.core.harness.minimal_context.native_tool_executor import (
    NativeToolExecutor,
    ActionResult,
    create_read_file_handler,
    create_write_file_handler,
    create_complete_handler,
    create_escalate_handler,
    create_standard_handlers,
)


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


class TestActionResult:
    """Tests for ActionResult class."""

    def test_success_result_to_string(self):
        """Successful result converts to string."""
        result = ActionResult(success=True, data="file content")
        assert result.to_string() == "file content"

    def test_success_with_dict_data(self):
        """Successful result with dict data serializes to JSON."""
        result = ActionResult(success=True, data={"lines": 42})
        output = result.to_string()
        assert '"lines": 42' in output

    def test_success_with_message_only(self):
        """Successful result with message only."""
        result = ActionResult(success=True, message="Done")
        assert result.to_string() == "Done"

    def test_success_no_data_no_message(self):
        """Successful result defaults to 'Success'."""
        result = ActionResult(success=True)
        assert result.to_string() == "Success"

    def test_error_result_to_string(self):
        """Error result includes error prefix."""
        result = ActionResult(success=False, message="File not found")
        assert result.to_string() == "Error: File not found"

    def test_repr(self):
        """ActionResult has useful repr."""
        result = ActionResult(success=True, message="Done")
        assert "success=True" in repr(result)
        assert "Done" in repr(result)


class TestReadFileHandler:
    """Tests for read_file handler factory."""

    def test_read_existing_file(self, tmp_path):
        """Read existing file contents."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        handler = create_read_file_handler(tmp_path)
        result = handler({"path": "test.txt"})

        assert result == "Hello, World!"

    def test_read_absolute_path(self, tmp_path):
        """Read file with absolute path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        handler = create_read_file_handler()
        result = handler({"path": str(test_file)})

        assert result == "Content"

    def test_read_missing_file_raises(self, tmp_path):
        """Reading missing file raises FileNotFoundError."""
        handler = create_read_file_handler(tmp_path)

        with pytest.raises(FileNotFoundError, match="not found"):
            handler({"path": "nonexistent.txt"})

    def test_read_missing_path_param_raises(self, tmp_path):
        """Missing path parameter raises ValueError."""
        handler = create_read_file_handler(tmp_path)

        with pytest.raises(ValueError, match="path parameter required"):
            handler({})


class TestWriteFileHandler:
    """Tests for write_file handler factory."""

    def test_write_new_file(self, tmp_path):
        """Write to new file."""
        handler = create_write_file_handler(tmp_path)
        result = handler({"path": "new.txt", "content": "New content"})

        assert (tmp_path / "new.txt").read_text() == "New content"
        assert "11 bytes" in result

    def test_write_creates_directories(self, tmp_path):
        """Write creates parent directories."""
        handler = create_write_file_handler(tmp_path)
        handler({"path": "deep/nested/file.txt", "content": "Deep"})

        assert (tmp_path / "deep" / "nested" / "file.txt").read_text() == "Deep"

    def test_write_absolute_path(self, tmp_path):
        """Write with absolute path."""
        test_file = tmp_path / "abs.txt"
        handler = create_write_file_handler()
        handler({"path": str(test_file), "content": "Absolute"})

        assert test_file.read_text() == "Absolute"

    def test_write_missing_path_raises(self, tmp_path):
        """Missing path parameter raises ValueError."""
        handler = create_write_file_handler(tmp_path)

        with pytest.raises(ValueError, match="path parameter required"):
            handler({"content": "no path"})


class TestCompleteHandler:
    """Tests for complete handler factory."""

    def test_complete_with_summary(self):
        """Complete includes summary in result."""
        handler = create_complete_handler()
        result = handler({"summary": "Fixed the bug"})

        assert "COMPLETE" in result
        assert "Fixed the bug" in result

    def test_complete_default_summary(self):
        """Complete has default summary."""
        handler = create_complete_handler()
        result = handler({})

        assert "COMPLETE" in result
        assert "Task completed" in result


class TestEscalateHandler:
    """Tests for escalate handler factory."""

    def test_escalate_with_reason(self):
        """Escalate includes reason in result."""
        handler = create_escalate_handler()
        result = handler({"reason": "Need human review"})

        assert "ESCALATE" in result
        assert "Need human review" in result

    def test_escalate_default_reason(self):
        """Escalate has default reason."""
        handler = create_escalate_handler()
        result = handler({})

        assert "ESCALATE" in result
        assert "Unknown reason" in result


class TestStandardHandlers:
    """Tests for create_standard_handlers factory."""

    def test_creates_all_standard_handlers(self, tmp_path):
        """Creates all standard handlers."""
        handlers = create_standard_handlers(tmp_path)

        assert "read_file" in handlers
        assert "write_file" in handlers
        assert "complete" in handlers
        assert "escalate" in handlers

    def test_handlers_work_with_executor(self, tmp_path):
        """Standard handlers work with executor."""
        handlers = create_standard_handlers(tmp_path)
        executor = NativeToolExecutor(actions=handlers)

        # Write a file
        write_call = ToolCall(
            id="tc_1",
            name="write_file",
            input={"path": "test.txt", "content": "Test content"},
        )
        write_result = executor.execute(write_call)
        assert not write_result.is_error

        # Read it back
        read_call = ToolCall(
            id="tc_2",
            name="read_file",
            input={"path": "test.txt"},
        )
        read_result = executor.execute(read_call)
        assert not read_result.is_error
        assert read_result.content == "Test content"

        # Complete
        complete_call = ToolCall(
            id="tc_3",
            name="complete",
            input={"summary": "Done"},
        )
        complete_result = executor.execute(complete_call)
        assert "COMPLETE" in complete_result.content


class TestIntegrationWithLLMClient:
    """Integration tests with simulated LLM client."""

    def test_executor_with_simulated_client(self, tmp_path):
        """NativeToolExecutor works with SimulatedLLMClient."""
        from agentforge.core.llm import create_simple_client
        from agentforge.core.llm.tools import READ_FILE, WRITE_FILE, COMPLETE

        # Set up executor with handlers
        handlers = create_standard_handlers(tmp_path)
        tool_executor = NativeToolExecutor(actions=handlers)

        # Create test file
        test_file = tmp_path / "source.txt"
        test_file.write_text("Source content")

        # Create simulated client that requests read_file then complete
        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "read_file", "input": {"path": str(test_file)}}
                ],
            },
            {
                "content": "I read the file.",
                "tool_calls": [
                    {"id": "tc_2", "name": "complete", "input": {"summary": "Read file"}}
                ],
            },
        ])

        # Execute first call
        response1 = client.complete(
            system="Test",
            messages=[{"role": "user", "content": "Read source.txt"}],
            tools=[READ_FILE, WRITE_FILE, COMPLETE],
        )

        assert response1.has_tool_calls
        result1 = tool_executor.execute(response1.tool_calls[0])
        assert result1.content == "Source content"

    def test_complete_with_tools_loop(self, tmp_path):
        """complete_with_tools handles full tool loop."""
        from agentforge.core.llm import create_simple_client
        from agentforge.core.llm.tools import READ_FILE, COMPLETE

        # Set up executor
        handlers = create_standard_handlers(tmp_path)
        tool_executor = NativeToolExecutor(actions=handlers)

        # Create test file
        test_file = tmp_path / "data.txt"
        test_file.write_text("Important data")

        # Simulated responses: read file, then return final answer
        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "read_file", "input": {"path": str(test_file)}}
                ],
            },
            {
                "content": "The file contains: Important data",
            },
        ])

        # Use complete_with_tools
        final_response = client.complete_with_tools(
            system="You are a file reader",
            messages=[{"role": "user", "content": "What's in data.txt?"}],
            tools=[READ_FILE, COMPLETE],
            tool_executor=tool_executor,
        )

        # Should have completed the loop
        assert "Important data" in final_response.content
        assert not final_response.has_tool_calls

        # Check execution log
        log = tool_executor.get_execution_log()
        assert len(log) == 1
        assert log[0]["tool_name"] == "read_file"
        assert log[0]["success"] is True
