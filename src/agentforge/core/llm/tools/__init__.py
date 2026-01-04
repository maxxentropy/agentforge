# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
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

# Base tools
from .base_tools import (
    BASE_TOOLS,
    CANNOT_FIX,
    COMPLETE,
    EDIT_FILE,
    ESCALATE,
    LOAD_CONTEXT,
    READ_FILE,
    RUN_TESTS,
    SEARCH_CODE,
    WRITE_FILE,
)

# Discovery tools
from .discovery_tools import (
    ANALYZE_DEPENDENCIES,
    CREATE_MAPPING,
    DETECT_PATTERNS,
    DISCOVERY_TOOLS,
    MAP_STRUCTURE,
)

# Refactoring tools
from .refactoring_tools import (
    EXTRACT_FUNCTION,
    INLINE_FUNCTION,
    REFACTORING_TOOLS,
    RENAME_SYMBOL,
    RUN_CHECK,
    SIMPLIFY_CONDITIONAL,
)

# Registry functions
from .registry import (
    get_tool_by_name,
    get_tools_by_category,
    get_tools_for_task,
    list_all_tools,
    list_task_types,
)

# Review tools
from .review_tools import (
    ADD_REVIEW_COMMENT,
    ANALYZE_DIFF,
    GENERATE_REVIEW_SUMMARY,
    REVIEW_TOOLS,
)

# Testing tools
from .testing_tools import (
    GENERATE_TEST,
    RUN_SINGLE_TEST,
    TESTING_TOOLS,
)

__all__ = [
    # Base tools
    "READ_FILE",
    "WRITE_FILE",
    "EDIT_FILE",
    "SEARCH_CODE",
    "LOAD_CONTEXT",
    "RUN_TESTS",
    "COMPLETE",
    "ESCALATE",
    "CANNOT_FIX",
    "BASE_TOOLS",
    # Refactoring tools
    "EXTRACT_FUNCTION",
    "SIMPLIFY_CONDITIONAL",
    "RUN_CHECK",
    "INLINE_FUNCTION",
    "RENAME_SYMBOL",
    "REFACTORING_TOOLS",
    # Discovery tools
    "ANALYZE_DEPENDENCIES",
    "DETECT_PATTERNS",
    "MAP_STRUCTURE",
    "CREATE_MAPPING",
    "DISCOVERY_TOOLS",
    # Testing tools
    "GENERATE_TEST",
    "RUN_SINGLE_TEST",
    "TESTING_TOOLS",
    # Review tools
    "ANALYZE_DIFF",
    "ADD_REVIEW_COMMENT",
    "GENERATE_REVIEW_SUMMARY",
    "REVIEW_TOOLS",
    # Registry functions
    "get_tools_for_task",
    "get_tool_by_name",
    "list_task_types",
    "list_all_tools",
    "get_tools_by_category",
]
