# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1

"""Shared fixtures for stage integration tests."""

from typing import Any

import pytest

from agentforge.core.pipeline import (
    PipelineController,
    PipelineStateStore,
    StageExecutorRegistry,
)
from agentforge.core.pipeline.stages import register_design_stages


@pytest.fixture
def temp_project_with_code(tmp_path):
    """Create a temporary project with sample code."""
    project = tmp_path / "test_project"
    project.mkdir(parents=True)

    # Create src directory
    src = project / "src"
    src.mkdir()

    # Create sample files
    (src / "main.py").write_text(
        '''"""Main module."""

def main():
    """Entry point."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
    )

    (src / "auth.py").write_text(
        '''"""Authentication module."""

class AuthHandler:
    """Handles authentication."""

    def login(self, username: str, password: str) -> bool:
        """Login user."""
        return True

    def logout(self) -> None:
        """Logout user."""
        pass
'''
    )

    # Create .agentforge directory
    agentforge = project / ".agentforge"
    agentforge.mkdir()

    return project


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client that returns configurable responses."""

    class MockLLMClient:
        def __init__(self):
            self.responses = {}

        def set_response(self, stage: str, response: str, tool_results: list = None):
            """Set the response for a specific stage."""
            self.responses[stage] = {
                "response": response,
                "content": response,
                "tool_results": tool_results or [],
            }

        def get_response(self, stage: str) -> dict[str, Any]:
            """Get the response for a stage."""
            return self.responses.get(stage, {"response": "", "tool_results": []})

    return MockLLMClient()


@pytest.fixture
def pipeline_controller_with_stages(temp_project_with_code):
    """Create a pipeline controller with design stages registered."""
    registry = StageExecutorRegistry()
    register_design_stages(registry)

    state_store = PipelineStateStore(temp_project_with_code)
    controller = PipelineController(
        project_path=temp_project_with_code,
        state_store=state_store,
        registry=registry,
    )

    return controller


# ═══════════════════════════════════════════════════════════════════════════════
# TDD Stage Fixtures (Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_spec_for_tdd():
    """Create a sample specification artifact for TDD tests."""
    return {
        "spec_id": "SPEC-20260102-0001",
        "request_id": "REQ-20260102-0001",
        "title": "Calculator Module",
        "version": "1.0",
        "overview": {
            "purpose": "Create a simple calculator module",
            "scope": "Math operations",
        },
        "components": [
            {
                "name": "Calculator",
                "type": "class",
                "file_path": "src/calculator.py",
                "description": "Simple calculator class",
                "interface": {
                    "methods": [
                        {
                            "signature": "add(a: int, b: int) -> int",
                            "description": "Add two numbers",
                        },
                        {
                            "signature": "subtract(a: int, b: int) -> int",
                            "description": "Subtract two numbers",
                        },
                    ]
                },
            }
        ],
        "test_cases": [
            {
                "id": "TC001",
                "description": "Test addition",
                "component": "Calculator",
                "type": "unit",
                "given": "Two positive integers",
                "when": "add() is called",
                "then": "Returns their sum",
            },
            {
                "id": "TC002",
                "description": "Test subtraction",
                "component": "Calculator",
                "type": "unit",
                "given": "Two integers",
                "when": "subtract() is called",
                "then": "Returns the difference",
            },
        ],
        "acceptance_criteria": [
            {"criterion": "All basic operations work correctly"},
        ],
        "implementation_order": [
            {"step": 1, "description": "Create Calculator class"},
            {"step": 2, "description": "Implement add method"},
            {"step": 3, "description": "Implement subtract method"},
        ],
    }


@pytest.fixture
def sample_red_artifact_for_green():
    """Create a RED phase artifact for GREEN phase testing."""
    return {
        "spec_id": "SPEC-20260102-0001",
        "request_id": "REQ-20260102-0001",
        "test_files": [
            {
                "path": "tests/test_calculator.py",
                "content": '''"""Tests for Calculator."""
import pytest
from src.calculator import Calculator


class TestCalculator:
    """Unit tests for Calculator class."""

    def test_add_positive_numbers(self):
        """TC001: Test addition of positive numbers."""
        calc = Calculator()
        result = calc.add(2, 3)
        assert result == 5

    def test_subtract_numbers(self):
        """TC002: Test subtraction."""
        calc = Calculator()
        result = calc.subtract(5, 3)
        assert result == 2
''',
            }
        ],
        "test_results": {
            "passed": 0,
            "failed": 2,
            "errors": 0,
            "total": 2,
            "exit_code": 1,
            "test_details": [
                {"name": "test_add_positive_numbers", "status": "failed"},
                {"name": "test_subtract_numbers", "status": "failed"},
            ],
        },
        "failing_tests": ["test_add_positive_numbers", "test_subtract_numbers"],
        "unexpected_passes": [],
        "warnings": [],
    }


@pytest.fixture
def temp_project_for_tdd(tmp_path):
    """Create a temporary project for TDD testing."""
    project = tmp_path / "tdd_project"
    project.mkdir(parents=True)

    # Create directories
    (project / "src").mkdir()
    (project / "tests").mkdir()

    # Create __init__.py files
    (project / "src" / "__init__.py").write_text("")
    (project / "tests" / "__init__.py").write_text("")

    # Create .agentforge directory
    (project / ".agentforge").mkdir()

    return project


# ═══════════════════════════════════════════════════════════════════════════════
# REFACTOR & DELIVER Stage Fixtures (Phase 4)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_green_artifact_for_refactor():
    """Create a GREEN phase artifact for REFACTOR testing."""
    return {
        "spec_id": "SPEC-20260102-0001",
        "request_id": "REQ-20260102-0001",
        "implementation_files": [
            "src/calculator.py",
        ],
        "test_files": [
            {
                "path": "tests/test_calculator.py",
                "content": '''"""Tests for Calculator."""
import pytest
from src.calculator import Calculator


class TestCalculator:
    def test_add_positive_numbers(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5

    def test_subtract_numbers(self):
        calc = Calculator()
        assert calc.subtract(5, 3) == 2
''',
            }
        ],
        "test_results": {
            "passed": 2,
            "failed": 0,
            "errors": 0,
            "total": 2,
            "exit_code": 0,
            "test_details": [
                {"name": "test_add_positive_numbers", "status": "passed"},
                {"name": "test_subtract_numbers", "status": "passed"},
            ],
        },
        "passing_tests": 2,
        "iterations": 2,
        "all_tests_pass": True,
        "acceptance_criteria": [
            {"criterion": "All basic operations work correctly"},
        ],
        "clarified_requirements": "Create a simple calculator with add and subtract",
        "original_request": "Create a calculator module",
    }


@pytest.fixture
def sample_refactor_artifact_for_deliver():
    """Create a REFACTOR phase artifact for DELIVER testing."""
    return {
        "spec_id": "SPEC-20260102-0001",
        "request_id": "REQ-20260102-0001",
        "refactored_files": [
            {
                "path": "src/calculator.py",
                "changes": "Added type hints and docstrings",
            }
        ],
        "improvements": [
            {
                "type": "documentation",
                "description": "Added docstrings to all methods",
                "file": "src/calculator.py",
            },
        ],
        "final_files": [
            "src/calculator.py",
            "tests/test_calculator.py",
        ],
        "test_results": {
            "passed": 2,
            "failed": 0,
            "total": 2,
        },
        "conformance_passed": True,
        "remaining_violations": [],
        "clarified_requirements": "Create a simple calculator with add and subtract",
        "original_request": "Create a calculator module",
    }


@pytest.fixture
def temp_project_for_refactor(tmp_path):
    """Create a temporary project for REFACTOR testing with implementation."""
    import subprocess

    project = tmp_path / "refactor_project"
    project.mkdir(parents=True)

    # Create directories
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentforge" / "patches").mkdir(parents=True)

    # Create __init__.py files
    (project / "src" / "__init__.py").write_text("")
    (project / "tests" / "__init__.py").write_text("")

    # Create implementation file
    (project / "src" / "calculator.py").write_text('''"""Calculator module."""


class Calculator:
    """Simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract two numbers."""
        return a - b
''')

    # Create test file
    (project / "tests" / "test_calculator.py").write_text('''"""Tests for Calculator."""
import pytest
from src.calculator import Calculator


class TestCalculator:
    def test_add_positive_numbers(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5

    def test_subtract_numbers(self):
        calc = Calculator()
        assert calc.subtract(5, 3) == 2
''')

    # Initialize git
    try:
        subprocess.run(["git", "init"], cwd=str(project), check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(project), check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(project), check=True, capture_output=True
        )
        subprocess.run(["git", "add", "."], cwd=str(project), check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=str(project), check=True, capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # Git may not be available

    return project
