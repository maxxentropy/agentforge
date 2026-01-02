# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_file: specs/pipeline-controller/implementation/phase-3-tdd-stages.yaml
# @spec_id: pipeline-controller-phase2-v1
# @spec_id: pipeline-controller-phase3-v1

"""Shared fixtures for stage integration tests."""

from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch

import pytest

from agentforge.core.pipeline import (
    PipelineController,
    PipelineStateStore,
    StageExecutorRegistry,
    get_registry,
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

        def get_response(self, stage: str) -> Dict[str, Any]:
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
