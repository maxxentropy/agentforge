"""
Tool Registry
=============

Task-to-tool mapping and lookup functions.
"""

from ..interface import ToolDefinition
from .base_tools import BASE_TOOLS
from .discovery_tools import DISCOVERY_TOOLS
from .refactoring_tools import REFACTORING_TOOLS
from .review_tools import REVIEW_TOOLS
from .testing_tools import TESTING_TOOLS

# Task Type to Tools Mapping
_TASK_TOOLS: dict[str, set[str]] = {
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
_ALL_TOOLS: dict[str, ToolDefinition] = {
    tool.name: tool
    for tool in (
        BASE_TOOLS + REFACTORING_TOOLS + DISCOVERY_TOOLS +
        TESTING_TOOLS + REVIEW_TOOLS
    )
}

# Category to tools mapping
_CATEGORIES: dict[str, list[ToolDefinition]] = {
    "base": BASE_TOOLS,
    "refactoring": REFACTORING_TOOLS,
    "discovery": DISCOVERY_TOOLS,
    "testing": TESTING_TOOLS,
    "review": REVIEW_TOOLS,
}


def get_tools_for_task(task_type: str) -> list[ToolDefinition]:
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


def list_task_types() -> list[str]:
    """
    List all supported task types.

    Returns:
        Sorted list of task type names
    """
    return sorted(_TASK_TOOLS.keys())


def list_all_tools() -> list[str]:
    """
    List all available tool names.

    Returns:
        Sorted list of tool names
    """
    return sorted(_ALL_TOOLS.keys())


def get_tools_by_category(category: str) -> list[ToolDefinition]:
    """
    Get tools by category.

    Args:
        category: Category name (base, refactoring, discovery, testing, review)

    Returns:
        List of tools in the category

    Raises:
        ValueError: If category is not recognized
    """
    if category not in _CATEGORIES:
        valid = ", ".join(sorted(_CATEGORIES.keys()))
        raise ValueError(f"Unknown category: {category}. Valid: {valid}")

    return _CATEGORIES[category]
