"""
Refactoring Tool Definitions
============================

Tools for fix_violation and refactor tasks.
"""

from ..interface import ToolDefinition

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

# Collection of refactoring tools
REFACTORING_TOOLS: list[ToolDefinition] = [
    EXTRACT_FUNCTION,
    SIMPLIFY_CONDITIONAL,
    RUN_CHECK,
    INLINE_FUNCTION,
    RENAME_SYMBOL,
]
