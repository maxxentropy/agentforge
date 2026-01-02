# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-stage-executor

"""Tests for stage executor interface."""

import pytest

from agentforge.core.pipeline import (
    StageContext,
    StageExecutor,
    StageResult,
    StageStatus,
    PassthroughExecutor,
)


class TestStageContext:
    """Tests for StageContext dataclass."""

    def test_stage_context_creation(self, sample_stage_context):
        """StageContext can be created with required fields."""
        ctx = sample_stage_context

        assert ctx.pipeline_id == "PL-20260101-abc12345"
        assert ctx.stage_name == "intake"
        assert ctx.input_artifacts == {"request": "Test request"}
        assert ctx.config == {"verbose": True}

    def test_get_artifact(self, sample_stage_context):
        """get_artifact() retrieves artifacts with default."""
        ctx = sample_stage_context

        assert ctx.get_artifact("request") == "Test request"
        assert ctx.get_artifact("missing") is None
        assert ctx.get_artifact("missing", "default") == "default"

    def test_has_artifact(self, sample_stage_context):
        """has_artifact() checks for artifact existence."""
        ctx = sample_stage_context

        assert ctx.has_artifact("request") is True
        assert ctx.has_artifact("missing") is False


class TestStageResult:
    """Tests for StageResult dataclass."""

    def test_success_result(self):
        """StageResult.success() creates successful result."""
        result = StageResult.success({"output": "data"})

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts == {"output": "data"}
        assert result.error is None
        assert result.escalation is None
        assert result.is_success() is True
        assert result.is_failed() is False
        assert result.needs_escalation() is False

    def test_failed_result(self):
        """StageResult.failed() creates failed result."""
        result = StageResult.failed("Something went wrong")

        assert result.status == StageStatus.FAILED
        assert result.error == "Something went wrong"
        assert result.is_success() is False
        assert result.is_failed() is True

    def test_skipped_result(self):
        """StageResult.skipped() creates skipped result."""
        result = StageResult.skipped("Not applicable")

        assert result.status == StageStatus.SKIPPED
        assert result.artifacts.get("skip_reason") == "Not applicable"

    def test_escalate_result(self):
        """StageResult.escalate() creates escalation result."""
        result = StageResult.escalate(
            escalation_type="approval_required",
            message="Please approve",
            options=["Yes", "No"],
            context={"reason": "safety"},
        )

        assert result.status == StageStatus.COMPLETED
        assert result.needs_escalation() is True
        assert result.is_success() is False  # Not success if escalating
        assert result.escalation["type"] == "approval_required"
        assert result.escalation["message"] == "Please approve"
        assert result.escalation["options"] == ["Yes", "No"]

    def test_success_with_next_stage(self):
        """Success result can specify next stage override."""
        result = StageResult.success(next_stage="custom_stage")

        assert result.next_stage == "custom_stage"


class TestStageExecutor:
    """Tests for StageExecutor abstract base class."""

    def test_validate_input_with_required(self):
        """validate_input() checks required inputs."""

        class RequiringExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

            def get_required_inputs(self):
                return ["input_a", "input_b"]

        executor = RequiringExecutor()

        # Missing both
        errors = executor.validate_input({})
        assert len(errors) == 2
        assert "input_a" in errors[0]

        # Has both
        errors = executor.validate_input({"input_a": 1, "input_b": 2})
        assert len(errors) == 0

        # Missing one
        errors = executor.validate_input({"input_a": 1})
        assert len(errors) == 1
        assert "input_b" in errors[0]

    def test_stage_name_from_class(self):
        """stage_name property derives from class name."""

        class IntakeExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

        executor = IntakeExecutor()
        assert executor.stage_name == "intake"

        class AnalyzeStageExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

        executor2 = AnalyzeStageExecutor()
        assert executor2.stage_name == "analyzestage"

    def test_default_required_inputs(self):
        """Default get_required_inputs() returns empty list."""

        class SimpleExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

        executor = SimpleExecutor()
        assert executor.get_required_inputs() == []

    def test_default_output_schema(self):
        """Default get_output_schema() returns empty dict."""

        class SimpleExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

        executor = SimpleExecutor()
        assert executor.get_output_schema() == {}


class TestPassthroughExecutor:
    """Tests for PassthroughExecutor."""

    def test_passthrough_returns_input(self, sample_stage_context):
        """PassthroughExecutor returns input artifacts as output."""
        executor = PassthroughExecutor()
        result = executor.execute(sample_stage_context)

        assert result.is_success()
        assert result.artifacts == sample_stage_context.input_artifacts

    def test_passthrough_custom_name(self):
        """PassthroughExecutor can have custom name."""
        executor = PassthroughExecutor(name="my-stage")
        assert executor.stage_name == "my-stage"
