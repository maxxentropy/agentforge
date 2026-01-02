# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1

"""Shared fixtures for pipeline unit tests."""

from unittest.mock import MagicMock

import pytest

from agentforge.core.pipeline import (
    PipelineStateStore,
    StageContext,
    StageExecutor,
    StageExecutorRegistry,
    StageResult,
    create_pipeline_state,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project_path = tmp_path / "test_project"
    project_path.mkdir(parents=True)
    return project_path


@pytest.fixture
def state_store(temp_project):
    """Create a PipelineStateStore for testing."""
    return PipelineStateStore(temp_project)


@pytest.fixture
def sample_pipeline_state(temp_project):
    """Create a sample pipeline state for testing."""
    return create_pipeline_state(
        request="Add a logout button",
        project_path=temp_project,
        template="implement",
    )


@pytest.fixture
def sample_stage_context(temp_project):
    """Create a sample stage context for testing."""
    return StageContext(
        pipeline_id="PL-20260101-abc12345",
        stage_name="intake",
        project_path=temp_project,
        input_artifacts={"request": "Test request"},
        config={"verbose": True},
        request="Add a logout button",
    )


@pytest.fixture
def mock_state_store():
    """Create a mock state store."""
    mock = MagicMock(spec=PipelineStateStore)
    mock.load.return_value = None
    mock.save.return_value = None
    return mock


@pytest.fixture
def mock_registry():
    """Create a mock stage executor registry."""
    mock = MagicMock(spec=StageExecutorRegistry)
    return mock


@pytest.fixture
def fresh_registry():
    """Create a fresh registry instance (not singleton)."""
    registry = StageExecutorRegistry()
    return registry


class TestExecutor(StageExecutor):
    """A test executor that returns configurable results."""

    def __init__(
        self,
        name: str = "test",
        result: StageResult = None,
        required_inputs: list = None,
    ):
        self._name = name
        self._result = result or StageResult.success({"output": "test"})
        self._required_inputs = required_inputs or []

    def execute(self, context: StageContext) -> StageResult:
        return self._result

    def get_required_inputs(self) -> list:
        return self._required_inputs

    @property
    def stage_name(self) -> str:
        return self._name


class FailingExecutor(StageExecutor):
    """An executor that always fails."""

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.failed("Intentional failure")


class EscalatingExecutor(StageExecutor):
    """An executor that always escalates."""

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.escalate(
            escalation_type="approval_required",
            message="Please approve this action",
            options=["Approve", "Reject"],
        )


@pytest.fixture
def test_executor():
    """Create a test executor."""
    return TestExecutor()


@pytest.fixture
def failing_executor():
    """Create a failing executor."""
    return FailingExecutor()


@pytest.fixture
def escalating_executor():
    """Create an escalating executor."""
    return EscalatingExecutor()


@pytest.fixture
def full_registry():
    """Create a registry with all stages registered."""
    from agentforge.core.pipeline import PassthroughExecutor

    registry = StageExecutorRegistry()
    stages = [
        "intake", "clarify", "analyze", "spec",
        "red", "green", "refactor", "deliver"
    ]
    for stage in stages:
        registry.register(stage, lambda s=stage: PassthroughExecutor(s))
    return registry


@pytest.fixture
def controller(temp_project, full_registry):
    """Create a PipelineController with full registry."""
    from agentforge.core.pipeline import PipelineController

    return PipelineController(
        project_path=temp_project,
        registry=full_registry,
    )
