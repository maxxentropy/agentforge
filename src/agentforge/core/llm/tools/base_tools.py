"""
Base Tool Definitions
=====================

Core tools available to all task types.
"""

from ..interface import ToolDefinition

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

# Collection of all base tools
BASE_TOOLS: list[ToolDefinition] = [
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
