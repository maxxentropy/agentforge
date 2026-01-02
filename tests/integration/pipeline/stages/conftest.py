# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_id: pipeline-controller-phase2-v1

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
