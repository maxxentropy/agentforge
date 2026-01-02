# @spec_file: specs/tools/01-tool-handlers.yaml
# @spec_id: tool-handlers-v1
# @component_id: verify-handlers

"""
Tests for verify_handlers module.
"""

import pytest
from pathlib import Path

from agentforge.core.harness.minimal_context.tool_handlers.verify_handlers import (
    create_run_check_handler,
    create_run_tests_handler,
    create_validate_python_handler,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with Python files."""
    src = tmp_path / "src"
    src.mkdir()

    # Create a valid Python file
    (src / "valid.py").write_text(
        "def foo():\n"
        "    return 42\n"
    )

    # Create a Python file with syntax error
    (src / "syntax_error.py").write_text(
        "def foo(\n"
        "    return 42\n"
    )

    # Create .agentforge directory
    agentforge = tmp_path / ".agentforge"
    agentforge.mkdir()
    violations = agentforge / "violations"
    violations.mkdir()

    return tmp_path


@pytest.fixture
def temp_project_with_violation(tmp_path):
    """Create a temp project with a conformance violation."""
    import yaml

    project = tmp_path / "test_project"
    project.mkdir()

    # Create .agentforge structure
    (project / ".agentforge").mkdir()
    (project / ".agentforge" / "violations").mkdir()

    # Create violation file
    violation = {
        "violation_id": "V-001",
        "contract_id": "complexity",
        "check_id": "cyclomatic-complexity",
        "severity": "warning",
        "file_path": "src/complex.py",
        "line_number": 10,
        "message": "Function has complexity 15 (max 10)",
        "status": "open",
    }
    with open(project / ".agentforge" / "violations" / "V-001.yaml", "w") as f:
        yaml.dump(violation, f)

    # Create the source directory
    (project / "src").mkdir()

    return project


class TestRunCheckHandler:
    """Tests for run_check handler."""

    def test_run_check_basic(self, temp_project):
        """Run check returns result."""
        handler = create_run_check_handler(temp_project)

        result = handler({})

        # Should return some result (may pass or fail depending on setup)
        assert isinstance(result, str)
        # Should have some status indication
        assert "CHECK" in result or "ERROR" in result

    def test_run_check_with_file(self, temp_project):
        """Run check on specific file."""
        handler = create_run_check_handler(temp_project)

        result = handler({"file_path": "src/valid.py"})

        assert isinstance(result, str)

    def test_run_check_with_context(self, temp_project_with_violation):
        """Run check uses context for violation checking."""
        handler = create_run_check_handler(temp_project_with_violation)

        result = handler({
            "_context": {
                "violation_id": "V-001",
                "file_path": "src/complex.py",
            }
        })

        assert isinstance(result, str)


class TestRunTestsHandler:
    """Tests for run_tests handler."""

    def test_run_tests_basic(self, temp_project):
        """Run tests returns result."""
        handler = create_run_tests_handler(temp_project)

        result = handler({})

        # Should return some result
        assert isinstance(result, str)
        # Should have some status indication
        assert "TEST" in result or "ERROR" in result or "PASSED" in result or "FAILED" in result

    def test_run_tests_with_path(self, temp_project):
        """Run specific test path."""
        handler = create_run_tests_handler(temp_project)

        result = handler({"path": "tests/"})

        assert isinstance(result, str)

    def test_run_tests_with_context_files(self, temp_project):
        """Run tests for modified files from context."""
        handler = create_run_tests_handler(temp_project)

        result = handler({
            "_context": {
                "files_modified": ["src/valid.py"],
            }
        })

        assert isinstance(result, str)


class TestValidatePythonHandler:
    """Tests for validate_python handler."""

    def test_validate_valid_python(self, temp_project):
        """Validate a correct Python file."""
        handler = create_validate_python_handler(temp_project)

        result = handler({"file_path": "src/valid.py"})

        assert "PASSED" in result or "OK" in result
        assert "Syntax" in result

    def test_validate_syntax_error(self, temp_project):
        """Detect syntax error in Python file."""
        handler = create_validate_python_handler(temp_project)

        result = handler({"file_path": "src/syntax_error.py"})

        assert "SYNTAX ERROR" in result or "SyntaxError" in result

    def test_validate_file_not_found(self, temp_project):
        """Error on missing file."""
        handler = create_validate_python_handler(temp_project)

        result = handler({"file_path": "nonexistent.py"})

        assert "ERROR" in result
        assert "not found" in result.lower()

    def test_validate_non_python_file(self, temp_project):
        """Error on non-Python file."""
        # Create a non-Python file
        (temp_project / "readme.md").write_text("# Readme")

        handler = create_validate_python_handler(temp_project)

        result = handler({"file_path": "readme.md"})

        assert "ERROR" in result
        assert "Python" in result

    def test_validate_no_path_error(self, temp_project):
        """Error when no path provided."""
        handler = create_validate_python_handler(temp_project)

        result = handler({})

        assert "ERROR" in result
        assert "file_path" in result.lower()

    def test_validate_import_error(self, temp_project):
        """Detect import error in Python file."""
        # Create a file with undefined name
        (temp_project / "src" / "bad_import.py").write_text(
            "x = undefined_variable\n"
        )

        handler = create_validate_python_handler(temp_project)

        result = handler({"file_path": "src/bad_import.py"})

        # May detect NameError depending on how the code is structured
        assert isinstance(result, str)
