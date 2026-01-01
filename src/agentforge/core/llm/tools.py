# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: llm-tools
# @test_path: tests/unit/llm/test_tools.py

"""
LLM Tool Definitions
====================

Native Anthropic API tool definitions organized by task type.

Tool Categories:
- Base Tools: Available to all task types (read_file, write_file, etc.)
- Refactoring Tools: For fix_violation, refactor tasks
- Discovery Tools: For discovery, bridge tasks
- Testing Tools: For write_tests, implement_feature tasks
- Review Tools: For code_review tasks

Usage:
    ```python
    from agentforge.core.llm.tools import get_tools_for_task

    # Get tools for a specific task type
    tools = get_tools_for_task("fix_violation")

    # Use with LLM client
    response = client.complete(
        system=system,
        messages=messages,
        tools=tools,
    )
    ```
"""

from typing import Dict, List, Set

from .interface import ToolDefinition


# =============================================================================
# Base Tools (all task types)
# =============================================================================

READ_FILE = ToolDefinition(
    name="read_file",
    description="Read the contents of a file. Use this to examine source code, configuration, or any text file.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read (relative to project root)",
            },
            "start_line": {
                "type": "integer",
                "description": "Optional starting line number (1-indexed)",
            },
            "end_line": {
                "type": "integer",
                "description": "Optional ending line number (1-indexed)",
            },
        },
        "required": ["path"],
    },
)

WRITE_FILE = ToolDefinition(
    name="write_file",
    description="Write content to a file, creating it if it doesn't exist or overwriting if it does.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write (relative to project root)",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
        "required": ["path", "content"],
    },
)

EDIT_FILE = ToolDefinition(
    name="edit_file",
    description="Edit specific lines in a file. Replaces lines between start_line and end_line with new content.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit",
            },
            "start_line": {
                "type": "integer",
                "description": "Starting line number to replace (1-indexed)",
            },
            "end_line": {
                "type": "integer",
                "description": "Ending line number to replace (1-indexed, inclusive)",
            },
            "new_content": {
                "type": "string",
                "description": "The new content to insert",
            },
        },
        "required": ["path", "start_line", "end_line", "new_content"],
    },
)

SEARCH_CODE = ToolDefinition(
    name="search_code",
    description="Search for patterns in the codebase. Returns matching file paths and line numbers.",
    input_schema={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regular expression pattern to search for",
            },
            "file_pattern": {
                "type": "string",
                "description": "Glob pattern to filter files (e.g., '*.py', 'src/**/*.ts')",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 20)",
            },
        },
        "required": ["pattern"],
    },
)

LOAD_CONTEXT = ToolDefinition(
    name="load_context",
    description="Load additional file context into working memory for analysis.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to load",
            },
            "purpose": {
                "type": "string",
                "description": "Why this file is being loaded (for audit)",
            },
        },
        "required": ["path"],
    },
)

RUN_TESTS = ToolDefinition(
    name="run_tests",
    description="Execute the project's test suite or specific tests.",
    input_schema={
        "type": "object",
        "properties": {
            "test_path": {
                "type": "string",
                "description": "Specific test file or directory to run (optional)",
            },
            "test_name": {
                "type": "string",
                "description": "Specific test name pattern to run (optional)",
            },
        },
        "required": [],
    },
)

COMPLETE = ToolDefinition(
    name="complete",
    description="Mark the task as successfully completed. Only use when all success criteria are met.",
    input_schema={
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Brief summary of what was accomplished",
            },
            "changes_made": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of changes made during the task",
            },
        },
        "required": ["summary"],
    },
)

ESCALATE = ToolDefinition(
    name="escalate",
    description="Request human assistance when the task cannot be completed autonomously.",
    input_schema={
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why the task cannot be completed autonomously",
            },
            "attempted": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of approaches that were attempted",
            },
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Suggestions for human intervention",
            },
        },
        "required": ["reason"],
    },
)

CANNOT_FIX = ToolDefinition(
    name="cannot_fix",
    description="Indicate that the issue cannot be fixed with the current approach or constraints.",
    input_schema={
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why the fix is not possible",
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Constraints preventing the fix",
            },
            "alternatives": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Alternative approaches that might work",
            },
        },
        "required": ["reason"],
    },
)


# =============================================================================
# Refactoring Tools (fix_violation, refactor)
# =============================================================================

EXTRACT_FUNCTION = ToolDefinition(
    name="extract_function",
    description="Extract a block of code into a new helper function to reduce complexity.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file containing the code",
            },
            "source_function": {
                "type": "string",
                "description": "Name of the function containing the code to extract",
            },
            "start_line": {
                "type": "integer",
                "description": "Starting line of code to extract (1-indexed)",
            },
            "end_line": {
                "type": "integer",
                "description": "Ending line of code to extract (1-indexed)",
            },
            "new_function_name": {
                "type": "string",
                "description": "Name for the new extracted function",
            },
            "parameters": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Parameters the new function should accept",
            },
        },
        "required": ["file_path", "source_function", "start_line", "end_line", "new_function_name"],
    },
)

SIMPLIFY_CONDITIONAL = ToolDefinition(
    name="simplify_conditional",
    description="Simplify conditional logic by converting to guard clauses or early returns.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file",
            },
            "function_name": {
                "type": "string",
                "description": "Name of the function to simplify",
            },
            "strategy": {
                "type": "string",
                "enum": ["guard_clause", "early_return", "invert_condition", "extract_condition"],
                "description": "Simplification strategy to apply",
            },
            "target_line": {
                "type": "integer",
                "description": "Line number of the conditional to simplify",
            },
        },
        "required": ["file_path", "function_name", "strategy"],
    },
)

RUN_CHECK = ToolDefinition(
    name="run_check",
    description="Run a conformance check to verify the fix. Returns pass/fail and details.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to check (optional, checks all if not specified)",
            },
            "check_type": {
                "type": "string",
                "description": "Type of check to run (e.g., 'complexity', 'style', 'type')",
            },
        },
        "required": [],
    },
)

INLINE_FUNCTION = ToolDefinition(
    name="inline_function",
    description="Inline a function call, replacing it with the function body.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file",
            },
            "function_name": {
                "type": "string",
                "description": "Name of the function to inline",
            },
            "call_line": {
                "type": "integer",
                "description": "Line number of the function call to inline",
            },
        },
        "required": ["file_path", "function_name", "call_line"],
    },
)

RENAME_SYMBOL = ToolDefinition(
    name="rename_symbol",
    description="Rename a symbol (variable, function, class) across all references.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file containing the symbol definition",
            },
            "old_name": {
                "type": "string",
                "description": "Current name of the symbol",
            },
            "new_name": {
                "type": "string",
                "description": "New name for the symbol",
            },
            "symbol_type": {
                "type": "string",
                "enum": ["variable", "function", "class", "method", "parameter"],
                "description": "Type of symbol being renamed",
            },
        },
        "required": ["file_path", "old_name", "new_name"],
    },
)


# =============================================================================
# Discovery Tools (discovery, bridge)
# =============================================================================

ANALYZE_DEPENDENCIES = ToolDefinition(
    name="analyze_dependencies",
    description="Map the import/dependency graph for a file or module.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to file or directory to analyze",
            },
            "depth": {
                "type": "integer",
                "description": "Maximum depth of dependency traversal (default: 3)",
            },
            "include_external": {
                "type": "boolean",
                "description": "Include external/third-party dependencies",
            },
        },
        "required": ["path"],
    },
)

DETECT_PATTERNS = ToolDefinition(
    name="detect_patterns",
    description="Detect architectural patterns and code structures in the codebase.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to analyze (file or directory)",
            },
            "patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific patterns to look for (e.g., 'singleton', 'factory', 'mvc')",
            },
        },
        "required": ["path"],
    },
)

MAP_STRUCTURE = ToolDefinition(
    name="map_structure",
    description="Analyze and map the project structure, identifying key directories and files.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Root path to analyze (default: project root)",
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Include hidden files and directories",
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum directory depth to traverse",
            },
        },
        "required": [],
    },
)

CREATE_MAPPING = ToolDefinition(
    name="create_mapping",
    description="Create a mapping between code elements and contracts/specifications.",
    input_schema={
        "type": "object",
        "properties": {
            "source_element": {
                "type": "string",
                "description": "Source code element (e.g., class name, function)",
            },
            "target_contract": {
                "type": "string",
                "description": "Target contract or specification ID",
            },
            "mapping_type": {
                "type": "string",
                "enum": ["implements", "uses", "extends", "validates"],
                "description": "Type of relationship",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score for the mapping (0.0-1.0)",
            },
        },
        "required": ["source_element", "target_contract", "mapping_type"],
    },
)


# =============================================================================
# Testing Tools (write_tests, implement_feature)
# =============================================================================

GENERATE_TEST = ToolDefinition(
    name="generate_test",
    description="Generate a test case for a function or class.",
    input_schema={
        "type": "object",
        "properties": {
            "target_path": {
                "type": "string",
                "description": "Path to the file containing the code to test",
            },
            "target_name": {
                "type": "string",
                "description": "Name of the function/class to test",
            },
            "test_type": {
                "type": "string",
                "enum": ["unit", "integration", "property", "snapshot"],
                "description": "Type of test to generate",
            },
            "scenarios": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific scenarios to test",
            },
        },
        "required": ["target_path", "target_name"],
    },
)

RUN_SINGLE_TEST = ToolDefinition(
    name="run_single_test",
    description="Run a specific test and return detailed results.",
    input_schema={
        "type": "object",
        "properties": {
            "test_path": {
                "type": "string",
                "description": "Path to the test file",
            },
            "test_name": {
                "type": "string",
                "description": "Specific test function/method name",
            },
            "verbose": {
                "type": "boolean",
                "description": "Include verbose output",
            },
        },
        "required": ["test_path", "test_name"],
    },
)


# =============================================================================
# Review Tools (code_review)
# =============================================================================

ANALYZE_DIFF = ToolDefinition(
    name="analyze_diff",
    description="Analyze a code diff for potential issues, style violations, and improvements.",
    input_schema={
        "type": "object",
        "properties": {
            "diff_content": {
                "type": "string",
                "description": "The diff content to analyze (unified diff format)",
            },
            "focus_areas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific areas to focus on (e.g., 'security', 'performance', 'style')",
            },
        },
        "required": ["diff_content"],
    },
)

ADD_REVIEW_COMMENT = ToolDefinition(
    name="add_review_comment",
    description="Add a review comment on a specific line or range in the diff.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file being commented on",
            },
            "line_number": {
                "type": "integer",
                "description": "Line number in the new version",
            },
            "comment": {
                "type": "string",
                "description": "The review comment",
            },
            "severity": {
                "type": "string",
                "enum": ["critical", "warning", "suggestion", "nitpick"],
                "description": "Severity of the issue",
            },
            "category": {
                "type": "string",
                "enum": ["bug", "security", "performance", "style", "documentation", "design"],
                "description": "Category of the comment",
            },
        },
        "required": ["file_path", "line_number", "comment", "severity"],
    },
)

GENERATE_REVIEW_SUMMARY = ToolDefinition(
    name="generate_review_summary",
    description="Generate an overall summary of the code review findings.",
    input_schema={
        "type": "object",
        "properties": {
            "include_stats": {
                "type": "boolean",
                "description": "Include statistics about changes",
            },
            "recommendation": {
                "type": "string",
                "enum": ["approve", "request_changes", "comment"],
                "description": "Overall recommendation for the review",
            },
        },
        "required": ["recommendation"],
    },
)


# =============================================================================
# Tool Collections by Category
# =============================================================================

BASE_TOOLS: List[ToolDefinition] = [
    READ_FILE,
    WRITE_FILE,
    EDIT_FILE,
    SEARCH_CODE,
    LOAD_CONTEXT,
    RUN_TESTS,
    COMPLETE,
    ESCALATE,
    CANNOT_FIX,
]

REFACTORING_TOOLS: List[ToolDefinition] = [
    EXTRACT_FUNCTION,
    SIMPLIFY_CONDITIONAL,
    RUN_CHECK,
    INLINE_FUNCTION,
    RENAME_SYMBOL,
]

DISCOVERY_TOOLS: List[ToolDefinition] = [
    ANALYZE_DEPENDENCIES,
    DETECT_PATTERNS,
    MAP_STRUCTURE,
    CREATE_MAPPING,
]

TESTING_TOOLS: List[ToolDefinition] = [
    GENERATE_TEST,
    RUN_SINGLE_TEST,
]

REVIEW_TOOLS: List[ToolDefinition] = [
    ANALYZE_DIFF,
    ADD_REVIEW_COMMENT,
    GENERATE_REVIEW_SUMMARY,
]


# =============================================================================
# Task Type to Tools Mapping
# =============================================================================

_TASK_TOOLS: Dict[str, Set[str]] = {
    "fix_violation": {
        # Base
        "read_file", "write_file", "edit_file", "search_code", "load_context",
        "run_tests", "complete", "escalate", "cannot_fix",
        # Refactoring
        "extract_function", "simplify_conditional", "run_check",
        "inline_function", "rename_symbol",
    },
    "implement_feature": {
        # Base
        "read_file", "write_file", "edit_file", "search_code", "load_context",
        "run_tests", "complete", "escalate",
        # Testing
        "generate_test", "run_single_test",
    },
    "write_tests": {
        # Base
        "read_file", "write_file", "edit_file", "search_code", "load_context",
        "run_tests", "complete", "escalate",
        # Testing
        "generate_test", "run_single_test",
    },
    "refactor": {
        # Base
        "read_file", "write_file", "edit_file", "search_code", "load_context",
        "run_tests", "complete", "escalate", "cannot_fix",
        # Refactoring
        "extract_function", "simplify_conditional", "run_check",
        "inline_function", "rename_symbol",
    },
    "discovery": {
        # Base (subset)
        "read_file", "search_code", "load_context", "complete", "escalate",
        # Discovery
        "analyze_dependencies", "detect_patterns", "map_structure",
    },
    "bridge": {
        # Base (subset)
        "read_file", "search_code", "load_context", "complete", "escalate",
        # Discovery
        "analyze_dependencies", "detect_patterns", "map_structure",
        "create_mapping",
    },
    "code_review": {
        # Base (subset)
        "read_file", "search_code", "complete", "escalate",
        # Review
        "analyze_diff", "add_review_comment", "generate_review_summary",
    },
}

# Build a lookup from tool name to definition
_ALL_TOOLS: Dict[str, ToolDefinition] = {
    tool.name: tool
    for tool in (
        BASE_TOOLS + REFACTORING_TOOLS + DISCOVERY_TOOLS +
        TESTING_TOOLS + REVIEW_TOOLS
    )
}


def get_tools_for_task(task_type: str) -> List[ToolDefinition]:
    """
    Get the list of tools available for a specific task type.

    Args:
        task_type: Type of task (e.g., "fix_violation", "implement_feature")

    Returns:
        List of ToolDefinition objects for the task type

    Raises:
        ValueError: If task_type is not recognized

    Example:
        ```python
        tools = get_tools_for_task("fix_violation")
        # Returns: [READ_FILE, WRITE_FILE, ..., EXTRACT_FUNCTION, ...]
        ```
    """
    if task_type not in _TASK_TOOLS:
        valid_types = ", ".join(sorted(_TASK_TOOLS.keys()))
        raise ValueError(
            f"Unknown task type: {task_type}. Valid types: {valid_types}"
        )

    tool_names = _TASK_TOOLS[task_type]
    return [_ALL_TOOLS[name] for name in sorted(tool_names)]


def get_tool_by_name(name: str) -> ToolDefinition:
    """
    Get a specific tool definition by name.

    Args:
        name: Tool name (e.g., "read_file", "extract_function")

    Returns:
        ToolDefinition for the tool

    Raises:
        KeyError: If tool name is not recognized
    """
    if name not in _ALL_TOOLS:
        valid_names = ", ".join(sorted(_ALL_TOOLS.keys()))
        raise KeyError(f"Unknown tool: {name}. Valid tools: {valid_names}")
    return _ALL_TOOLS[name]


def list_task_types() -> List[str]:
    """
    List all supported task types.

    Returns:
        Sorted list of task type names
    """
    return sorted(_TASK_TOOLS.keys())


def list_all_tools() -> List[str]:
    """
    List all available tool names.

    Returns:
        Sorted list of tool names
    """
    return sorted(_ALL_TOOLS.keys())


def get_tools_by_category(category: str) -> List[ToolDefinition]:
    """
    Get tools by category.

    Args:
        category: Category name (base, refactoring, discovery, testing, review)

    Returns:
        List of tools in the category

    Raises:
        ValueError: If category is not recognized
    """
    categories = {
        "base": BASE_TOOLS,
        "refactoring": REFACTORING_TOOLS,
        "discovery": DISCOVERY_TOOLS,
        "testing": TESTING_TOOLS,
        "review": REVIEW_TOOLS,
    }

    if category not in categories:
        valid = ", ".join(sorted(categories.keys()))
        raise ValueError(f"Unknown category: {category}. Valid: {valid}")

    return categories[category]
