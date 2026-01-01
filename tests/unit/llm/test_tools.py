# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: llm-tools
# @impl_path: src/agentforge/core/llm/tools.py

"""
Tests for LLM Tool Definitions
==============================

Tests verify:
- Tool definitions have valid JSON Schema
- get_tools_for_task returns correct tools per task type
- Tool collections are properly organized
- Error handling for invalid inputs
"""

import pytest
from typing import List

from agentforge.core.llm.tools import (
    # Functions
    get_tools_for_task,
    get_tool_by_name,
    get_tools_by_category,
    list_task_types,
    list_all_tools,
    # Collections
    BASE_TOOLS,
    REFACTORING_TOOLS,
    DISCOVERY_TOOLS,
    TESTING_TOOLS,
    REVIEW_TOOLS,
    # Individual tools
    READ_FILE,
    WRITE_FILE,
    EDIT_FILE,
    COMPLETE,
    ESCALATE,
    EXTRACT_FUNCTION,
    RUN_CHECK,
)
from agentforge.core.llm.interface import ToolDefinition


class TestToolDefinitions:
    """Tests for individual tool definitions."""

    def test_read_file_has_valid_schema(self):
        """READ_FILE tool has valid input schema."""
        assert READ_FILE.name == "read_file"
        assert "path" in READ_FILE.input_schema["properties"]
        assert "path" in READ_FILE.input_schema["required"]

    def test_write_file_has_valid_schema(self):
        """WRITE_FILE tool has valid input schema."""
        assert WRITE_FILE.name == "write_file"
        props = WRITE_FILE.input_schema["properties"]
        assert "path" in props
        assert "content" in props
        assert set(WRITE_FILE.input_schema["required"]) == {"path", "content"}

    def test_edit_file_has_valid_schema(self):
        """EDIT_FILE tool has valid input schema."""
        assert EDIT_FILE.name == "edit_file"
        props = EDIT_FILE.input_schema["properties"]
        assert "start_line" in props
        assert "end_line" in props
        assert "new_content" in props

    def test_complete_has_valid_schema(self):
        """COMPLETE tool has valid input schema."""
        assert COMPLETE.name == "complete"
        assert "summary" in COMPLETE.input_schema["properties"]
        assert "summary" in COMPLETE.input_schema["required"]

    def test_escalate_has_valid_schema(self):
        """ESCALATE tool has valid input schema."""
        assert ESCALATE.name == "escalate"
        assert "reason" in ESCALATE.input_schema["properties"]
        assert "reason" in ESCALATE.input_schema["required"]

    def test_extract_function_has_valid_schema(self):
        """EXTRACT_FUNCTION tool has valid input schema."""
        assert EXTRACT_FUNCTION.name == "extract_function"
        props = EXTRACT_FUNCTION.input_schema["properties"]
        assert "file_path" in props
        assert "source_function" in props
        assert "start_line" in props
        assert "end_line" in props
        assert "new_function_name" in props

    def test_run_check_has_valid_schema(self):
        """RUN_CHECK tool has valid input schema."""
        assert RUN_CHECK.name == "run_check"
        # run_check has optional parameters
        assert RUN_CHECK.input_schema.get("required", []) == []

    def test_all_tools_are_tool_definitions(self):
        """All tools in collections are ToolDefinition instances."""
        all_collections = [
            BASE_TOOLS,
            REFACTORING_TOOLS,
            DISCOVERY_TOOLS,
            TESTING_TOOLS,
            REVIEW_TOOLS,
        ]
        for collection in all_collections:
            for tool in collection:
                assert isinstance(tool, ToolDefinition)

    def test_all_tools_have_required_fields(self):
        """All tools have name, description, and input_schema."""
        all_tools = (
            BASE_TOOLS + REFACTORING_TOOLS + DISCOVERY_TOOLS +
            TESTING_TOOLS + REVIEW_TOOLS
        )
        for tool in all_tools:
            assert tool.name, "Tool must have a name"
            assert tool.description, "Tool must have a description"
            assert isinstance(tool.input_schema, dict), "Tool must have input_schema dict"
            assert "type" in tool.input_schema, "Schema must have type"
            assert tool.input_schema["type"] == "object", "Schema type must be object"
            assert "properties" in tool.input_schema, "Schema must have properties"

    def test_tools_can_convert_to_api_format(self):
        """All tools can be converted to API format."""
        for tool in BASE_TOOLS:
            api_format = tool.to_api_format()
            assert "name" in api_format
            assert "description" in api_format
            assert "input_schema" in api_format
            assert api_format["name"] == tool.name


class TestToolCollections:
    """Tests for tool collection constants."""

    def test_base_tools_contains_essential_tools(self):
        """BASE_TOOLS contains essential tools for all tasks."""
        base_names = {t.name for t in BASE_TOOLS}
        assert "read_file" in base_names
        assert "write_file" in base_names
        assert "complete" in base_names
        assert "escalate" in base_names

    def test_refactoring_tools_contains_refactoring_tools(self):
        """REFACTORING_TOOLS contains refactoring-specific tools."""
        refactor_names = {t.name for t in REFACTORING_TOOLS}
        assert "extract_function" in refactor_names
        assert "simplify_conditional" in refactor_names
        assert "run_check" in refactor_names

    def test_discovery_tools_contains_analysis_tools(self):
        """DISCOVERY_TOOLS contains analysis-specific tools."""
        discovery_names = {t.name for t in DISCOVERY_TOOLS}
        assert "analyze_dependencies" in discovery_names
        assert "detect_patterns" in discovery_names
        assert "map_structure" in discovery_names

    def test_testing_tools_contains_test_tools(self):
        """TESTING_TOOLS contains test-specific tools."""
        testing_names = {t.name for t in TESTING_TOOLS}
        assert "generate_test" in testing_names
        assert "run_single_test" in testing_names

    def test_review_tools_contains_review_tools(self):
        """REVIEW_TOOLS contains code review tools."""
        review_names = {t.name for t in REVIEW_TOOLS}
        assert "analyze_diff" in review_names
        assert "add_review_comment" in review_names
        assert "generate_review_summary" in review_names

    def test_no_duplicate_tool_names(self):
        """No duplicate tool names across collections."""
        all_tools = (
            BASE_TOOLS + REFACTORING_TOOLS + DISCOVERY_TOOLS +
            TESTING_TOOLS + REVIEW_TOOLS
        )
        names = [t.name for t in all_tools]
        assert len(names) == len(set(names)), "Duplicate tool names found"


class TestGetToolsForTask:
    """Tests for get_tools_for_task function."""

    def test_fix_violation_includes_base_and_refactoring(self):
        """fix_violation task includes base and refactoring tools."""
        tools = get_tools_for_task("fix_violation")
        names = {t.name for t in tools}
        # Base tools
        assert "read_file" in names
        assert "write_file" in names
        assert "complete" in names
        # Refactoring tools
        assert "extract_function" in names
        assert "run_check" in names

    def test_implement_feature_includes_base_and_testing(self):
        """implement_feature task includes base and testing tools."""
        tools = get_tools_for_task("implement_feature")
        names = {t.name for t in tools}
        # Base tools
        assert "read_file" in names
        assert "write_file" in names
        # Testing tools
        assert "generate_test" in names
        assert "run_single_test" in names
        # Should NOT include refactoring-only tools
        assert "extract_function" not in names

    def test_write_tests_includes_testing_tools(self):
        """write_tests task includes testing-specific tools."""
        tools = get_tools_for_task("write_tests")
        names = {t.name for t in tools}
        assert "generate_test" in names
        assert "run_single_test" in names

    def test_discovery_includes_analysis_tools(self):
        """discovery task includes analysis tools."""
        tools = get_tools_for_task("discovery")
        names = {t.name for t in tools}
        assert "analyze_dependencies" in names
        assert "detect_patterns" in names
        assert "map_structure" in names
        # Discovery is read-only, no write_file
        assert "write_file" not in names

    def test_bridge_includes_discovery_and_mapping(self):
        """bridge task includes discovery and mapping tools."""
        tools = get_tools_for_task("bridge")
        names = {t.name for t in tools}
        assert "analyze_dependencies" in names
        assert "create_mapping" in names

    def test_code_review_includes_review_tools(self):
        """code_review task includes review-specific tools."""
        tools = get_tools_for_task("code_review")
        names = {t.name for t in tools}
        assert "analyze_diff" in names
        assert "add_review_comment" in names
        assert "generate_review_summary" in names
        # Code review is read-only
        assert "write_file" not in names

    def test_refactor_includes_refactoring_tools(self):
        """refactor task includes refactoring tools."""
        tools = get_tools_for_task("refactor")
        names = {t.name for t in tools}
        assert "extract_function" in names
        assert "inline_function" in names
        assert "rename_symbol" in names

    def test_unknown_task_type_raises_error(self):
        """Unknown task type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown task type"):
            get_tools_for_task("unknown_task")

    def test_all_task_types_return_tools(self):
        """All supported task types return non-empty tool lists."""
        for task_type in list_task_types():
            tools = get_tools_for_task(task_type)
            assert len(tools) > 0, f"Task type {task_type} returned no tools"
            for tool in tools:
                assert isinstance(tool, ToolDefinition)

    def test_tools_are_sorted_by_name(self):
        """Tools returned are sorted by name for consistency."""
        for task_type in list_task_types():
            tools = get_tools_for_task(task_type)
            names = [t.name for t in tools]
            assert names == sorted(names), f"Tools for {task_type} not sorted"


class TestGetToolByName:
    """Tests for get_tool_by_name function."""

    def test_get_existing_tool(self):
        """Can retrieve existing tool by name."""
        tool = get_tool_by_name("read_file")
        assert tool.name == "read_file"
        assert isinstance(tool, ToolDefinition)

    def test_get_refactoring_tool(self):
        """Can retrieve refactoring tool by name."""
        tool = get_tool_by_name("extract_function")
        assert tool.name == "extract_function"

    def test_unknown_tool_raises_key_error(self):
        """Unknown tool name raises KeyError."""
        with pytest.raises(KeyError, match="Unknown tool"):
            get_tool_by_name("nonexistent_tool")


class TestGetToolsByCategory:
    """Tests for get_tools_by_category function."""

    def test_get_base_category(self):
        """Can retrieve base category tools."""
        tools = get_tools_by_category("base")
        assert tools == BASE_TOOLS

    def test_get_refactoring_category(self):
        """Can retrieve refactoring category tools."""
        tools = get_tools_by_category("refactoring")
        assert tools == REFACTORING_TOOLS

    def test_get_discovery_category(self):
        """Can retrieve discovery category tools."""
        tools = get_tools_by_category("discovery")
        assert tools == DISCOVERY_TOOLS

    def test_get_testing_category(self):
        """Can retrieve testing category tools."""
        tools = get_tools_by_category("testing")
        assert tools == TESTING_TOOLS

    def test_get_review_category(self):
        """Can retrieve review category tools."""
        tools = get_tools_by_category("review")
        assert tools == REVIEW_TOOLS

    def test_unknown_category_raises_error(self):
        """Unknown category raises ValueError."""
        with pytest.raises(ValueError, match="Unknown category"):
            get_tools_by_category("unknown")


class TestListFunctions:
    """Tests for list_* functions."""

    def test_list_task_types(self):
        """list_task_types returns all supported task types."""
        task_types = list_task_types()
        assert "fix_violation" in task_types
        assert "implement_feature" in task_types
        assert "write_tests" in task_types
        assert "refactor" in task_types
        assert "discovery" in task_types
        assert "bridge" in task_types
        assert "code_review" in task_types

    def test_list_task_types_is_sorted(self):
        """list_task_types returns sorted list."""
        task_types = list_task_types()
        assert task_types == sorted(task_types)

    def test_list_all_tools(self):
        """list_all_tools returns all tool names."""
        tools = list_all_tools()
        assert "read_file" in tools
        assert "extract_function" in tools
        assert "analyze_diff" in tools

    def test_list_all_tools_is_sorted(self):
        """list_all_tools returns sorted list."""
        tools = list_all_tools()
        assert tools == sorted(tools)


class TestToolSchemaValidity:
    """Tests for JSON Schema validity of tool input schemas."""

    @pytest.mark.parametrize("tool", BASE_TOOLS + REFACTORING_TOOLS)
    def test_tool_schema_has_object_type(self, tool: ToolDefinition):
        """Each tool schema has object type."""
        assert tool.input_schema["type"] == "object"

    @pytest.mark.parametrize("tool", BASE_TOOLS + REFACTORING_TOOLS)
    def test_tool_schema_has_properties(self, tool: ToolDefinition):
        """Each tool schema has properties."""
        assert "properties" in tool.input_schema
        assert isinstance(tool.input_schema["properties"], dict)

    @pytest.mark.parametrize("tool", BASE_TOOLS + REFACTORING_TOOLS)
    def test_required_fields_exist_in_properties(self, tool: ToolDefinition):
        """Required fields exist in properties."""
        required = tool.input_schema.get("required", [])
        properties = tool.input_schema["properties"]
        for field in required:
            assert field in properties, f"{tool.name}: required field '{field}' not in properties"


class TestToolIntegration:
    """Integration tests for tool usage with LLM client."""

    def test_tools_work_with_simulated_client(self):
        """Tools can be used with SimulatedLLMClient."""
        from agentforge.core.llm import create_simple_client

        # Get tools for fix_violation
        tools = get_tools_for_task("fix_violation")

        # Create simulated client with response that uses a tool
        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "read_file", "input": {"path": "test.py"}}
                ],
            }
        ])

        response = client.complete(
            system="Test",
            messages=[{"role": "user", "content": "Read a file"}],
            tools=tools,
        )

        assert response.has_tool_calls
        assert response.tool_calls[0].name == "read_file"

    def test_tool_api_format_is_valid(self):
        """Tool API format matches Anthropic expected structure."""
        tool = READ_FILE
        api_format = tool.to_api_format()

        # Check required fields for Anthropic API
        assert "name" in api_format
        assert "description" in api_format
        assert "input_schema" in api_format

        # Name should be lowercase with underscores
        assert api_format["name"] == "read_file"

        # Description should be non-empty
        assert len(api_format["description"]) > 0

        # Input schema should be valid
        schema = api_format["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
