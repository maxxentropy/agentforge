# @spec_file: specs/tools/01-tool-handlers.yaml
# @spec_id: tool-handlers-v1
# @component_id: tool-handlers-integration

"""
Integration tests for context injection through NativeToolExecutor.

These tests verify that:
1. Context is properly injected into handlers via _context
2. Handlers can read and use context data
3. The complete tool execution flow works with context
"""

import pytest
from pathlib import Path

from agentforge.core.harness.minimal_context.native_tool_executor import (
    NativeToolExecutor,
)
from agentforge.core.harness.minimal_context.tool_handlers import (
    create_standard_handlers,
    create_complete_handler,
    create_escalate_handler,
    create_cannot_fix_handler,
)
from agentforge.core.llm.interface import ToolCall


class TestContextInjection:
    """Integration tests for context injection into handlers."""

    @pytest.fixture
    def executor_with_context(self, tmp_path):
        """Create an executor with context configured."""
        handlers = create_standard_handlers(tmp_path)
        context = {
            "violation_id": "V-001",
            "task_id": "T-123",
            "files_examined": ["src/a.py", "src/b.py"],
            "attempted_approaches": ["approach1"],
            "understanding": ["fact1", "fact2"],
            "files_modified": ["src/fixed.py"],
        }
        return NativeToolExecutor(actions=handlers, context=context)

    def test_complete_receives_context(self, executor_with_context):
        """Complete handler receives and uses context data."""
        tool_call = ToolCall(
            id="tool_1",
            name="complete",
            input={"summary": "Fixed the violation"},
        )

        result = executor_with_context.execute(tool_call)

        assert not result.is_error
        assert "COMPLETE" in result.content
        # Should include files from context
        assert "src/fixed.py" in result.content

    def test_complete_merges_files_modified(self, executor_with_context):
        """Complete handler merges files_modified from params and context."""
        tool_call = ToolCall(
            id="tool_1",
            name="complete",
            input={
                "summary": "Done",
                "files_modified": ["src/another.py"],
            },
        )

        result = executor_with_context.execute(tool_call)

        assert not result.is_error
        # Should have files from both context and params
        assert "src/fixed.py" in result.content or "src/another.py" in result.content

    def test_escalate_handler_with_context(self, executor_with_context):
        """Escalate handler works with injected context."""
        tool_call = ToolCall(
            id="tool_2",
            name="escalate",
            input={
                "reason": "Need human review",
                "priority": "high",
            },
        )

        result = executor_with_context.execute(tool_call)

        assert not result.is_error
        assert "ESCALATE" in result.content
        assert "high" in result.content

    def test_cannot_fix_receives_violation_id(self, tmp_path):
        """Cannot_fix handler receives violation_id from context."""
        handlers = {"cannot_fix": create_cannot_fix_handler(tmp_path)}
        context = {
            "violation_id": "V-TEST-123",
            "task_id": "T-456",
            "attempted_approaches": ["try1", "try2"],
            "files_examined": ["module.py"],
            "understanding": ["root cause found"],
        }
        executor = NativeToolExecutor(actions=handlers, context=context)

        tool_call = ToolCall(
            id="tool_3",
            name="cannot_fix",
            input={
                "reason": "Cannot fix without breaking changes",
                "constraints": ["backwards compatibility"],
                "alternatives": ["manual fix recommended"],
            },
        )

        result = executor.execute(tool_call)

        assert not result.is_error
        assert "CANNOT_FIX" in result.content
        assert "V-TEST-123" in result.content

    def test_context_persists_across_calls(self, executor_with_context):
        """Context remains available across multiple tool calls."""
        # First call
        call1 = ToolCall(
            id="tool_1",
            name="complete",
            input={"summary": "Step 1"},
        )
        result1 = executor_with_context.execute(call1)
        assert not result1.is_error

        # Second call should still have context
        call2 = ToolCall(
            id="tool_2",
            name="complete",
            input={"summary": "Step 2"},
        )
        result2 = executor_with_context.execute(call2)
        assert not result2.is_error
        assert "src/fixed.py" in result2.content


class TestExecutorWithHandlers:
    """Integration tests for executor with standard handlers."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with files."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def hello():\n    return 'world'\n")
        return tmp_path

    @pytest.fixture
    def executor(self, temp_project):
        """Create an executor with standard handlers."""
        handlers = create_standard_handlers(temp_project)
        return NativeToolExecutor(actions=handlers)

    def test_read_write_edit_workflow(self, executor, temp_project):
        """Complete read-write-edit workflow through executor."""
        # Read original file
        read_call = ToolCall(
            id="read_1",
            name="read_file",
            input={"path": "src/module.py"},
        )
        read_result = executor.execute(read_call)
        assert not read_result.is_error
        assert "hello" in read_result.content

        # Write a new file
        write_call = ToolCall(
            id="write_1",
            name="write_file",
            input={
                "path": "src/new_module.py",
                "content": "# New module\n",
            },
        )
        write_result = executor.execute(write_call)
        assert not write_result.is_error
        assert "SUCCESS" in write_result.content

        # Edit the original file
        edit_call = ToolCall(
            id="edit_1",
            name="edit_file",
            input={
                "path": "src/module.py",
                "start_line": 2,
                "end_line": 2,
                "new_content": "    return 'modified'\n",
            },
        )
        edit_result = executor.execute(edit_call)
        assert not edit_result.is_error

        # Verify edit
        verify_read = ToolCall(
            id="read_2",
            name="read_file",
            input={"path": "src/module.py"},
        )
        verify_result = executor.execute(verify_read)
        assert "modified" in verify_result.content

    def test_search_finds_content(self, executor, temp_project):
        """Search handler finds content in files."""
        search_call = ToolCall(
            id="search_1",
            name="search_code",
            input={"pattern": "hello"},
        )

        result = executor.execute(search_call)

        assert not result.is_error
        assert "module.py" in result.content

    def test_execution_log_tracks_calls(self, executor, temp_project):
        """Execution log records all tool calls."""
        # Make a few calls
        executor.execute(ToolCall(
            id="log_1",
            name="read_file",
            input={"path": "src/module.py"},
        ))
        executor.execute(ToolCall(
            id="log_2",
            name="complete",
            input={"summary": "Done"},
        ))

        log = executor.get_execution_log()

        assert len(log) == 2
        assert log[0]["tool_name"] == "read_file"
        assert log[0]["success"] is True
        assert log[1]["tool_name"] == "complete"

    def test_unknown_tool_error(self, executor):
        """Unknown tool returns an error result."""
        call = ToolCall(
            id="unknown_1",
            name="nonexistent_tool",
            input={},
        )

        result = executor.execute(call)

        assert result.is_error
        assert "Unknown tool" in result.content


class TestContextFromParams:
    """Tests for context passed directly in params."""

    def test_handler_receives_context_in_params(self, tmp_path):
        """Handler can access _context from params."""
        received_context = {}

        def custom_handler(params):
            nonlocal received_context
            received_context = params.get("_context", {})
            return "OK"

        executor = NativeToolExecutor(
            actions={"custom": custom_handler},
            context={"key": "value", "task_id": "T-1"},
        )

        call = ToolCall(id="c1", name="custom", input={"arg": "test"})
        executor.execute(call)

        assert received_context.get("key") == "value"
        assert received_context.get("task_id") == "T-1"
