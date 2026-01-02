# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @test_path: tests/integration/workflows/test_fix_violation_workflow.py
"""
Fixtures for fix_violation workflow integration tests.

Provides:
- project_with_violation: A test project with a complexity violation
- simulated_llm_client: Pre-configured SimulatedLLMClient for testing
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

from agentforge.core.llm.simulated import (
    SequentialStrategy,
    SimulatedLLMClient,
    SimulatedResponse,
)


@pytest.fixture
def project_with_violation(tmp_path: Path) -> dict[str, Any]:
    """
    Create a test project with a cyclomatic complexity violation.

    Structure:
        test_project/
        ├── .agentforge/
        │   └── violations/
        │       └── V-test001.yaml
        ├── src/
        │   └── complex_module.py  # Has cyclomatic complexity > 10
        └── tests/
            └── test_complex.py

    Returns:
        Dict with project_path, violation_id, and file paths
    """
    # Create project structure
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    src_dir = project_path / "src"
    src_dir.mkdir()

    tests_dir = project_path / "tests"
    tests_dir.mkdir()

    agentforge_dir = project_path / ".agentforge"
    agentforge_dir.mkdir()

    violations_dir = agentforge_dir / "violations"
    violations_dir.mkdir()

    # Create complex module with cyclomatic complexity > 10
    complex_module = src_dir / "complex_module.py"
    complex_module.write_text('''"""Module with a complex function that needs refactoring."""


def process_data(data: dict, mode: str, flags: list) -> dict:
    """
    Process data based on mode and flags.

    This function has high cyclomatic complexity (12+) and should be refactored.
    """
    result = {}

    if mode == "parse":
        if "raw" in flags:
            if data.get("format") == "json":
                result["parsed"] = data.get("content", "")
            elif data.get("format") == "xml":
                result["parsed"] = "<parsed>" + data.get("content", "") + "</parsed>"
            else:
                result["parsed"] = str(data.get("content", ""))
        else:
            result["parsed"] = data.get("processed", data.get("content", ""))
    elif mode == "validate":
        if data.get("schema"):
            if "strict" in flags:
                if all(k in data for k in ["id", "name", "type"]):
                    result["valid"] = True
                else:
                    result["valid"] = False
                    result["error"] = "Missing required fields"
            else:
                result["valid"] = "id" in data
        else:
            result["valid"] = len(data) > 0
    elif mode == "transform":
        if "uppercase" in flags:
            result["transformed"] = {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}
        elif "lowercase" in flags:
            result["transformed"] = {k: v.lower() if isinstance(v, str) else v for k, v in data.items()}
        else:
            result["transformed"] = dict(data)
    else:
        result["error"] = f"Unknown mode: {mode}"

    return result


def simple_helper(value: str) -> str:
    """A simple helper function."""
    return value.strip().lower()
''')

    # Create a simple test file
    test_file = tests_dir / "test_complex.py"
    test_file.write_text('''"""Tests for complex_module."""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from complex_module import process_data, simple_helper


def test_parse_json():
    """Test parse mode with JSON format."""
    result = process_data(
        {"format": "json", "content": "hello"},
        mode="parse",
        flags=["raw"]
    )
    assert result["parsed"] == "hello"


def test_validate_strict():
    """Test validate mode with strict flag."""
    result = process_data(
        {"id": "1", "name": "test", "type": "item", "schema": True},
        mode="validate",
        flags=["strict"]
    )
    assert result["valid"] is True


def test_transform_uppercase():
    """Test transform mode with uppercase flag."""
    result = process_data(
        {"key": "value"},
        mode="transform",
        flags=["uppercase"]
    )
    assert result["transformed"]["key"] == "VALUE"


def test_simple_helper():
    """Test the simple helper function."""
    assert simple_helper("  HELLO  ") == "hello"
''')

    # Create violation YAML
    violation_data = {
        "violation_id": "V-test001",
        "check_id": "cyclomatic-complexity",
        "file_path": "src/complex_module.py",
        "line_number": 4,
        "severity": "warning",
        "message": "Function 'process_data' has cyclomatic complexity 12 (max: 10)",
        "fix_hint": "Consider extracting helper functions for each mode branch",
        "contract_id": "agentforge.contract",
        "test_path": "tests/test_complex.py",
        "detected_at": "2025-01-01T00:00:00Z",
        "status": "open",
    }

    violation_file = violations_dir / "V-test001.yaml"
    with open(violation_file, "w") as f:
        yaml.dump(violation_data, f, default_flow_style=False)

    return {
        "project_path": project_path,
        "violation_id": "V-test001",
        "violation_file": violation_file,
        "source_file": complex_module,
        "test_file": test_file,
        "violation_data": violation_data,
    }


@pytest.fixture
def project_with_generated_file(tmp_path: Path) -> dict[str, Any]:
    """
    Create a test project with a violation in an auto-generated file.

    This is used to test the cannot_fix escalation path.
    """
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    src_dir = project_path / "src"
    src_dir.mkdir()

    generated_dir = src_dir / "generated"
    generated_dir.mkdir()

    agentforge_dir = project_path / ".agentforge"
    agentforge_dir.mkdir()

    violations_dir = agentforge_dir / "violations"
    violations_dir.mkdir()

    # Create auto-generated file
    generated_file = generated_dir / "schema_types.py"
    generated_file.write_text('''# AUTO-GENERATED FILE - DO NOT EDIT
# Generated by schema-compiler v1.0.0
# Source: schema/types.graphql

"""Auto-generated type definitions."""


def validate_type(data: dict, type_name: str, strict: bool = False) -> bool:
    """
    Validate data against a type schema.

    This function is auto-generated and has high complexity.
    """
    if type_name == "User":
        if strict:
            if "id" not in data:
                return False
            if "email" not in data:
                return False
            if "name" not in data:
                return False
            return True
        else:
            return "id" in data
    elif type_name == "Product":
        if strict:
            if "sku" not in data:
                return False
            if "price" not in data:
                return False
            return True
        else:
            return "sku" in data
    elif type_name == "Order":
        if strict:
            if "id" not in data:
                return False
            if "items" not in data:
                return False
            if "total" not in data:
                return False
            return True
        else:
            return "id" in data
    else:
        return False
''')

    # Create violation YAML
    violation_data = {
        "violation_id": "V-generated001",
        "check_id": "cyclomatic-complexity",
        "file_path": "src/generated/schema_types.py",
        "line_number": 10,
        "severity": "warning",
        "message": "Function 'validate_type' has cyclomatic complexity 14 (max: 10)",
        "fix_hint": "Consider restructuring the validation logic",
        "contract_id": "agentforge.contract",
        "detected_at": "2025-01-01T00:00:00Z",
        "status": "open",
    }

    violation_file = violations_dir / "V-generated001.yaml"
    with open(violation_file, "w") as f:
        yaml.dump(violation_data, f, default_flow_style=False)

    return {
        "project_path": project_path,
        "violation_id": "V-generated001",
        "violation_file": violation_file,
        "source_file": generated_file,
        "violation_data": violation_data,
    }


@pytest.fixture
def simulated_fix_workflow_responses() -> list[dict[str, Any]]:
    """
    Scripted LLM responses for a successful fix_violation workflow.

    This simulates an agent that:
    1. Reads the file
    2. Analyzes the complexity
    3. Edits to extract helper functions (using line-based editing)
    4. Runs check to verify fix
    5. Completes the task

    Note: The tool_handlers use line-based editing (start_line, end_line, new_content)
    rather than text-based editing (old_text, new_text).
    """
    return [
        # Step 1: Read the violating file
        {
            "thinking": "I need to understand the code before fixing. Let me read the file.",
            "tool_calls": [
                {
                    "name": "read_file",
                    "input": {"path": "src/complex_module.py"}
                }
            ]
        },
        # Step 2: Insert helper function before process_data (line 4)
        {
            "thinking": "I'll first add a helper function before the complex function.",
            "tool_calls": [
                {
                    "name": "insert_lines",
                    "input": {
                        "path": "src/complex_module.py",
                        "line_number": 4,
                        "new_content": '''def _handle_parse(data: dict, flags: list) -> str:
    """Handle parse mode logic."""
    if "raw" in flags:
        fmt = data.get("format")
        if fmt == "json":
            return data.get("content", "")
        elif fmt == "xml":
            return "<parsed>" + data.get("content", "") + "</parsed>"
        else:
            return str(data.get("content", ""))
    return data.get("processed", data.get("content", ""))
'''
                    }
                }
            ]
        },
        # Step 3: Replace the parse branch with call to helper
        # After insert, the original parse branch is now around lines 23-33
        {
            "thinking": "Now I'll simplify the parse branch by calling the helper.",
            "tool_calls": [
                {
                    "name": "replace_lines",
                    "input": {
                        "path": "src/complex_module.py",
                        "start_line": 23,
                        "end_line": 33,
                        "new_content": '''    if mode == "parse":
        result["parsed"] = _handle_parse(data, flags)'''
                    }
                }
            ]
        },
        # Step 4: Run check to verify
        {
            "thinking": "Let me verify the fix reduced complexity.",
            "tool_calls": [
                {
                    "name": "run_check",
                    "input": {"path": "src/complex_module.py"}
                }
            ]
        },
        # Step 5: Complete
        {
            "content": "Successfully reduced cyclomatic complexity by extracting _handle_parse helper.",
            "tool_calls": [
                {
                    "name": "complete",
                    "input": {
                        "summary": "Extracted _handle_parse helper function to reduce cyclomatic complexity from 12 to 8."
                    }
                }
            ]
        }
    ]


@pytest.fixture
def simulated_cannot_fix_responses() -> list[dict[str, Any]]:
    """
    Scripted LLM responses for a cannot_fix escalation.

    This simulates an agent that:
    1. Reads the file
    2. Discovers it's auto-generated
    3. Calls cannot_fix to escalate
    """
    return [
        # Step 1: Read the violating file
        {
            "thinking": "Let me examine the file with the violation.",
            "tool_calls": [
                {
                    "name": "read_file",
                    "input": {"path": "src/generated/schema_types.py"}
                }
            ]
        },
        # Step 2: Recognize auto-generated and escalate
        {
            "thinking": "This file is auto-generated (comment at top). I cannot modify it.",
            "tool_calls": [
                {
                    "name": "cannot_fix",
                    "input": {
                        "reason": "File is auto-generated (header: 'AUTO-GENERATED FILE - DO NOT EDIT')",
                        "details": "The violation is in src/generated/schema_types.py which is auto-generated by schema-compiler. The fix should be applied to the source schema or the generator itself."
                    }
                }
            ]
        }
    ]


@pytest.fixture
def simulated_llm_client(
    simulated_fix_workflow_responses: list[dict[str, Any]]
) -> SimulatedLLMClient:
    """
    Create a SimulatedLLMClient with the fix workflow responses.
    """
    sim_responses = [
        SimulatedResponse(
            content=r.get("content", ""),
            tool_calls=r.get("tool_calls", []),
            thinking=r.get("thinking"),
        )
        for r in simulated_fix_workflow_responses
    ]

    return SimulatedLLMClient(strategy=SequentialStrategy(sim_responses))


@pytest.fixture
def simulated_escalation_client(
    simulated_cannot_fix_responses: list[dict[str, Any]]
) -> SimulatedLLMClient:
    """
    Create a SimulatedLLMClient for the escalation scenario.
    """
    sim_responses = [
        SimulatedResponse(
            content=r.get("content", ""),
            tool_calls=r.get("tool_calls", []),
            thinking=r.get("thinking"),
        )
        for r in simulated_cannot_fix_responses
    ]

    return SimulatedLLMClient(strategy=SequentialStrategy(sim_responses))
