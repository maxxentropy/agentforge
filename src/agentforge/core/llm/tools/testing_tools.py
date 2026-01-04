"""
Testing Tool Definitions
========================

Tools for write_tests and implement_feature tasks.
"""

from ..interface import ToolDefinition

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

# Collection of testing tools
TESTING_TOOLS: list[ToolDefinition] = [
    GENERATE_TEST,
    RUN_SINGLE_TEST,
]
