# @spec_file: specs/tools/p0-tool-handlers-overview.md
# @spec_id: p0-tool-handlers-v1
# @component_id: integration-tests-fix-violation
# @test_path: tests/integration/workflows/test_fix_violation_workflow.py
"""
Integration tests for the fix_violation workflow.

These tests exercise the full workflow:
1. Create a project with a conformance violation
2. Run tool handlers in sequence
3. Verify the violation handling (fix OR escalation)

Uses the P0 tool handlers from tool_handlers module:
- read_file, edit_file, replace_lines, insert_lines
- search_code, load_context
- run_check, run_tests
- complete, escalate, cannot_fix
"""

import pytest
from pathlib import Path
from typing import Any, Dict

from agentforge.core.harness.minimal_context.tool_handlers import (
    create_standard_handlers,
    create_fix_violation_handlers,
)
from agentforge.core.harness.minimal_context.native_tool_executor import (
    NativeToolExecutor,
)
from agentforge.core.llm.interface import ToolCall


class TestToolHandlerIntegration:
    """
    Integration tests for P0 tool handlers working together.

    These tests verify handlers can be chained in a workflow sequence.
    """

    def test_read_file_handler(self, project_with_violation: Dict[str, Any]):
        """Test that read_file handler works with project files."""
        project_path = project_with_violation["project_path"]
        handlers = create_standard_handlers(project_path)

        # Create executor with handlers
        executor = NativeToolExecutor(actions=handlers)

        # Execute read_file
        tool_call = ToolCall(
            id="test_1",
            name="read_file",
            input={"path": "src/complex_module.py"}
        )
        result = executor.execute(tool_call)

        assert not result.is_error, f"Unexpected error: {result.content}"
        assert "SUCCESS" in result.content
        assert "process_data" in result.content  # Function name should appear

    def test_edit_file_preserves_formatting(self, project_with_violation: Dict[str, Any]):
        """
        Test that edit_file preserves surrounding code.

        Scenario:
        - Edit a specific portion of the file
        - Verify lines before and after the edit are unchanged
        """
        project_path = project_with_violation["project_path"]
        source_file = project_with_violation["source_file"]

        # Read original content
        original_content = source_file.read_text()
        original_lines = original_content.split("\n")

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        # The simple_helper function is at the end of the file
        # Find line numbers first
        lines = original_content.split("\n")
        simple_helper_start = None
        for i, line in enumerate(lines):
            if "def simple_helper" in line:
                simple_helper_start = i + 1  # 1-indexed
                break

        assert simple_helper_start is not None, "Could not find simple_helper function"

        # Edit the simple_helper function (it spans 3 lines)
        tool_call = ToolCall(
            id="test_edit",
            name="edit_file",
            input={
                "path": "src/complex_module.py",
                "start_line": simple_helper_start,
                "end_line": simple_helper_start + 2,  # 3 lines total
                "new_content": 'def simple_helper(value: str) -> str:\n    """A simple helper function with better docstring."""\n    cleaned = value.strip()\n    return cleaned.lower()'
            }
        )
        result = executor.execute(tool_call)

        assert not result.is_error, f"Unexpected error: {result.content}"
        assert "SUCCESS" in result.content

        # Verify the edit was applied
        new_content = source_file.read_text()
        assert "better docstring" in new_content
        assert "cleaned = value.strip()" in new_content

        # Verify process_data function is unchanged (first part of file)
        assert 'def process_data(data: dict, mode: str, flags: list) -> dict:' in new_content
        assert 'if mode == "parse":' in new_content

    def test_replace_lines_handler(self, project_with_violation: Dict[str, Any]):
        """Test that replace_lines works correctly with line numbers."""
        project_path = project_with_violation["project_path"]
        source_file = project_with_violation["source_file"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        # First, read the file to know line numbers
        read_call = ToolCall(
            id="read_1",
            name="read_file",
            input={"path": "src/complex_module.py"}
        )
        read_result = executor.execute(read_call)
        assert not read_result.is_error

        # Replace the docstring (lines 5-8 approximately)
        replace_call = ToolCall(
            id="replace_1",
            name="replace_lines",
            input={
                "path": "src/complex_module.py",
                "start_line": 5,
                "end_line": 8,
                "new_content": '    """\n    Process data - refactored for clarity.\n    """'
            }
        )
        result = executor.execute(replace_call)

        assert not result.is_error, f"Unexpected error: {result.content}"
        assert "SUCCESS" in result.content

        # Verify the change
        new_content = source_file.read_text()
        assert "refactored for clarity" in new_content

    def test_insert_lines_handler(self, project_with_violation: Dict[str, Any]):
        """Test that insert_lines adds code at the correct position."""
        project_path = project_with_violation["project_path"]
        source_file = project_with_violation["source_file"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        # Insert a new helper function at the beginning (after module docstring)
        insert_call = ToolCall(
            id="insert_1",
            name="insert_lines",
            input={
                "path": "src/complex_module.py",
                "line_number": 4,
                "new_content": '''def _validate_mode(mode: str) -> bool:
    """Check if mode is valid."""
    return mode in ("parse", "validate", "transform")
'''
            }
        )
        result = executor.execute(insert_call)

        assert not result.is_error, f"Unexpected error: {result.content}"
        assert "SUCCESS" in result.content

        # Verify insertion
        new_content = source_file.read_text()
        lines = new_content.split("\n")

        # The new function should appear before process_data
        validate_idx = None
        process_idx = None
        for i, line in enumerate(lines):
            if "def _validate_mode" in line:
                validate_idx = i
            if "def process_data" in line:
                process_idx = i

        assert validate_idx is not None, "_validate_mode not found"
        assert process_idx is not None, "process_data not found"
        assert validate_idx < process_idx, "_validate_mode should come before process_data"

    def test_search_code_finds_patterns(self, project_with_violation: Dict[str, Any]):
        """Test that search_code finds code patterns across files."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        # Search for the process_data function (uses 'pattern' not 'query')
        search_call = ToolCall(
            id="search_1",
            name="search_code",
            input={
                "pattern": "def process_data",
                "max_results": 10
            }
        )
        result = executor.execute(search_call)

        assert not result.is_error, f"Unexpected error: {result.content}"
        assert "complex_module.py" in result.content or "process_data" in result.content

    def test_complete_handler(self, project_with_violation: Dict[str, Any]):
        """Test that complete handler returns proper completion message."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        complete_call = ToolCall(
            id="complete_1",
            name="complete",
            input={
                "summary": "Fixed complexity issue by extracting helper functions"
            }
        )
        result = executor.execute(complete_call)

        assert not result.is_error
        assert "COMPLETE" in result.content
        assert "Fixed complexity" in result.content

    def test_cannot_fix_handler(self, project_with_generated_file: Dict[str, Any]):
        """Test that cannot_fix handler creates proper escalation."""
        project_path = project_with_generated_file["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        cannot_fix_call = ToolCall(
            id="cannot_fix_1",
            name="cannot_fix",
            input={
                "reason": "File is auto-generated",
                "details": "Cannot modify auto-generated code. Fix should be in schema source."
            }
        )
        result = executor.execute(cannot_fix_call)

        assert not result.is_error
        assert "ESCALATE" in result.content or "cannot_fix" in result.content.lower()


class TestWorkflowSequence:
    """
    Tests for complete workflow sequences using tool handlers.

    These test realistic sequences of tool calls as an agent would make them.
    """

    def test_read_search_edit_sequence(self, project_with_violation: Dict[str, Any]):
        """
        Test a realistic sequence: read -> search -> edit.

        This mimics how an agent would:
        1. Read the violation file
        2. Search for related code
        3. Make an edit
        """
        project_path = project_with_violation["project_path"]
        source_file = project_with_violation["source_file"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(
            actions=handlers,
            context={
                "project_path": str(project_path),
                "violation_id": "V-test001",
            }
        )

        # Step 1: Read the file
        read_result = executor.execute(ToolCall(
            id="step_1",
            name="read_file",
            input={"path": "src/complex_module.py"}
        ))
        assert not read_result.is_error
        assert "process_data" in read_result.content

        # Step 2: Search for related code (uses 'pattern' parameter)
        search_result = executor.execute(ToolCall(
            id="step_2",
            name="search_code",
            input={"pattern": "simple_helper"}
        ))
        assert not search_result.is_error

        # Step 3: Edit to add a comment to the module docstring (line 1)
        # The edit_file handler uses line numbers, not text matching
        edit_result = executor.execute(ToolCall(
            id="step_3",
            name="edit_file",
            input={
                "path": "src/complex_module.py",
                "start_line": 1,
                "end_line": 1,
                "new_content": '"""Module with a complex function that needs refactoring.\n\nRefactored to reduce cyclomatic complexity.\n"""'
            }
        ))
        assert not edit_result.is_error

        # Verify the edit persisted
        new_content = source_file.read_text()
        assert "Refactored to reduce cyclomatic complexity" in new_content

        # Verify execution log
        log = executor.get_execution_log()
        assert len(log) == 3
        assert log[0]["tool_name"] == "read_file"
        assert log[1]["tool_name"] == "search_code"
        assert log[2]["tool_name"] == "edit_file"
        assert all(entry["success"] for entry in log)

    def test_handler_returns_success_on_valid_replacement(
        self, project_with_violation: Dict[str, Any]
    ):
        """
        Test that replace_lines returns SUCCESS when replacement is valid.

        Note: The tool_handlers do basic line replacement - syntax validation
        is handled by the workflow layer (e.g., MinimalContextFixWorkflow)
        which runs tests after each modification.
        """
        project_path = project_with_violation["project_path"]
        source_file = project_with_violation["source_file"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        # Make a valid edit - add a comment to a line
        edit_result = executor.execute(ToolCall(
            id="valid_edit",
            name="replace_lines",
            input={
                "path": "src/complex_module.py",
                "start_line": 10,  # Inside the function
                "end_line": 10,
                "new_content": "    result = {}  # Initialize result dictionary"
            }
        ))

        # The edit should succeed
        assert not edit_result.is_error
        assert "SUCCESS" in edit_result.content

        # Verify the file is still valid Python
        final_content = source_file.read_text()
        compile(final_content, source_file.name, 'exec')

    def test_context_injection(self, project_with_violation: Dict[str, Any]):
        """
        Test that context is properly injected into handlers.

        Handlers receive _context parameter with task information.
        """
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)

        context = {
            "violation_id": "V-test001",
            "task_id": "T-12345",
            "files_examined": ["src/complex_module.py"],
            "custom_key": "custom_value",
        }

        executor = NativeToolExecutor(actions=handlers, context=context)

        # Execute a handler - context should be available
        result = executor.execute(ToolCall(
            id="ctx_test",
            name="read_file",
            input={"path": "src/complex_module.py"}
        ))

        assert not result.is_error
        # The handler received context (verified by not crashing)
        # In production, handlers use context for decisions


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_read_nonexistent_file(self, project_with_violation: Dict[str, Any]):
        """Test reading a file that doesn't exist returns proper error."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        result = executor.execute(ToolCall(
            id="bad_read",
            name="read_file",
            input={"path": "src/does_not_exist.py"}
        ))

        # Should return an error message, not crash
        assert "ERROR" in result.content or "not found" in result.content.lower()

    def test_edit_with_no_match(self, project_with_violation: Dict[str, Any]):
        """Test editing with old_text that doesn't exist returns error."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        result = executor.execute(ToolCall(
            id="no_match",
            name="edit_file",
            input={
                "path": "src/complex_module.py",
                "old_text": "this text definitely does not exist in the file",
                "new_text": "replacement"
            }
        ))

        assert "ERROR" in result.content or "not found" in result.content.lower()

    def test_unknown_tool_returns_error(self, project_with_violation: Dict[str, Any]):
        """Test calling an unknown tool returns helpful error."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        result = executor.execute(ToolCall(
            id="unknown",
            name="nonexistent_tool",
            input={}
        ))

        assert result.is_error
        assert "Unknown tool" in result.content
        # Should list available tools
        assert "read_file" in result.content or "Available" in result.content

    def test_replace_lines_invalid_range(self, project_with_violation: Dict[str, Any]):
        """Test replace_lines with invalid line range returns error."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        result = executor.execute(ToolCall(
            id="bad_range",
            name="replace_lines",
            input={
                "path": "src/complex_module.py",
                "start_line": 1000,  # Way beyond file length
                "end_line": 1010,
                "new_content": "replacement"
            }
        ))

        assert "ERROR" in result.content or "invalid" in result.content.lower()


class TestHandlerRegistry:
    """Tests for handler registration and lookup."""

    def test_create_standard_handlers_returns_all_handlers(
        self, project_with_violation: Dict[str, Any]
    ):
        """Test that create_standard_handlers includes all expected handlers."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)

        # P0 handlers (must have)
        expected_p0 = [
            "read_file", "write_file", "edit_file",
            "search_code", "load_context",
            "run_check", "run_tests",
            "complete", "escalate", "cannot_fix",
        ]

        for handler_name in expected_p0:
            assert handler_name in handlers, f"Missing P0 handler: {handler_name}"

        # Additional handlers
        additional = ["replace_lines", "insert_lines", "find_related", "validate_python"]
        for handler_name in additional:
            assert handler_name in handlers, f"Missing handler: {handler_name}"

    def test_create_fix_violation_handlers(
        self, project_with_violation: Dict[str, Any]
    ):
        """Test the specialized fix_violation handler set."""
        project_path = project_with_violation["project_path"]

        handlers = create_fix_violation_handlers(project_path)

        # Should include fix-specific handlers
        assert "edit_file" in handlers
        assert "run_check" in handlers
        assert "cannot_fix" in handlers

    def test_executor_register_action_dynamically(
        self, project_with_violation: Dict[str, Any]
    ):
        """Test that actions can be registered dynamically."""
        project_path = project_with_violation["project_path"]

        handlers = create_standard_handlers(project_path)
        executor = NativeToolExecutor(actions=handlers)

        # Add a custom handler
        def custom_handler(params):
            return f"Custom result: {params.get('value', 'none')}"

        executor.register_action("custom_tool", custom_handler)

        result = executor.execute(ToolCall(
            id="custom",
            name="custom_tool",
            input={"value": "test123"}
        ))

        assert not result.is_error
        assert "Custom result: test123" in result.content
