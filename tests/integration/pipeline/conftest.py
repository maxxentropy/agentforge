# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1

"""Integration test fixtures for pipeline tests."""

import tempfile
from pathlib import Path

import pytest

from agentforge.core.pipeline import (
    PipelineController,
    StageContext,
    StageExecutor,
    StageExecutorRegistry,
    StageResult,
)


@pytest.fixture
def real_project_path():
    """Create a real temporary project directory."""
    with tempfile.TemporaryDirectory() as td:
        project_path = Path(td)
        # Create basic project structure
        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()
        yield project_path


@pytest.fixture
def full_registry():
    """Registry with all pipeline stages registered."""
    registry = StageExecutorRegistry()

    # Design template stages
    registry.register("intake", lambda: IntakeExecutor())
    registry.register("clarify", lambda: ClarifyExecutor())
    registry.register("analyze", lambda: AnalyzeExecutor())
    registry.register("spec", lambda: SpecExecutor())

    # Implement template stages
    registry.register("red", lambda: RedExecutor())
    registry.register("green", lambda: GreenExecutor())
    registry.register("refactor", lambda: RefactorExecutor())
    registry.register("deliver", lambda: DeliverExecutor())

    return registry


@pytest.fixture
def pipeline_controller(real_project_path, full_registry):
    """Create a fully configured pipeline controller."""
    return PipelineController(
        project_path=real_project_path,
        registry=full_registry,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Example Stage Executors
# ─────────────────────────────────────────────────────────────────────────────


class IntakeExecutor(StageExecutor):
    """Intake stage: Parse and understand the request."""

    def execute(self, context: StageContext) -> StageResult:
        # Simulate parsing the request
        return StageResult.success({
            "parsed_request": context.request,
            "request_type": "feature",
            "complexity": "medium",
        })


class ClarifyExecutor(StageExecutor):
    """Clarify stage: Identify ambiguities and clarify requirements."""

    def execute(self, context: StageContext) -> StageResult:
        # Simulate clarification
        return StageResult.success({
            "clarifications": [],
            "assumptions": ["Single file implementation"],
            "scope": "bounded",
        })


class AnalyzeExecutor(StageExecutor):
    """Analyze stage: Analyze codebase for implementation."""

    def execute(self, context: StageContext) -> StageResult:
        # Simulate code analysis
        return StageResult.success({
            "affected_files": ["src/main.py"],
            "dependencies": [],
            "test_files": ["tests/test_main.py"],
        })


class SpecExecutor(StageExecutor):
    """Spec stage: Generate implementation specification."""

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.success({
            "spec": {
                "changes": [
                    {"file": "src/main.py", "action": "add_function"},
                ],
                "tests": [
                    {"file": "tests/test_main.py", "action": "add_test"},
                ],
            },
        })


class RedExecutor(StageExecutor):
    """Red stage: Write failing tests."""

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.success({
            "tests_written": 1,
            "tests_failing": 1,
            "test_file": "tests/test_main.py",
        })


class GreenExecutor(StageExecutor):
    """Green stage: Implement to make tests pass."""

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.success({
            "implementation_file": "src/main.py",
            "tests_passing": 1,
            "tests_failing": 0,
        })


class RefactorExecutor(StageExecutor):
    """Refactor stage: Clean up implementation."""

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.success({
            "refactorings_applied": 0,
            "code_quality": "good",
        })


class DeliverExecutor(StageExecutor):
    """Deliver stage: Finalize and deliver the implementation."""

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.success({
            "deliverables": ["src/main.py", "tests/test_main.py"],
            "summary": "Feature implemented successfully",
        })


class ApprovalRequiredExecutor(StageExecutor):
    """Executor that always requests approval."""

    def __init__(self, message: str = "Please approve this change"):
        self.message = message

    def execute(self, context: StageContext) -> StageResult:
        return StageResult.escalate(
            escalation_type="approval_required",
            message=self.message,
            options=["Approve", "Reject"],
            context={"stage": context.stage_name},
        )


class FailAfterNExecutor(StageExecutor):
    """Executor that succeeds N times then fails."""

    def __init__(self, succeed_count: int = 0, error_message: str = "Intentional failure"):
        self.succeed_count = succeed_count
        self.call_count = 0
        self.error_message = error_message

    def execute(self, context: StageContext) -> StageResult:
        self.call_count += 1
        if self.call_count <= self.succeed_count:
            return StageResult.success({"attempt": self.call_count})
        return StageResult.failed(self.error_message)
