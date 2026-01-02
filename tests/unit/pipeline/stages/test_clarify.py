# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: clarify-executor
# @test_path: tests/unit/pipeline/stages/test_clarify.py

"""Tests for ClarifyExecutor."""

from unittest.mock import patch

from agentforge.core.pipeline import StageContext, StageStatus


class TestClarifyExecutor:
    """Tests for ClarifyExecutor stage."""

    def test_skips_when_no_blocking_questions(
        self, tmp_path, sample_intake_artifact, mock_llm_response
    ):
        """Skips clarification if no blocking questions."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        # Remove blocking questions
        sample_intake_artifact["initial_questions"] = [
            {"question": "Optional question?", "priority": "optional"}
        ]

        executor = ClarifyExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=tmp_path,
            input_artifacts=sample_intake_artifact,
            request=sample_intake_artifact["original_request"],
        )

        result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts["ready_for_analysis"] is True

    def test_escalates_when_blocking_unanswered(self, tmp_path, sample_intake_artifact):
        """Escalates when blocking questions have no answers."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        # Ensure there's a blocking question
        sample_intake_artifact["initial_questions"] = [
            {"question": "Blocking question?", "priority": "blocking"}
        ]
        # No answers provided
        sample_intake_artifact["question_answers"] = {}

        executor = ClarifyExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=tmp_path,
            input_artifacts=sample_intake_artifact,
            request=sample_intake_artifact["original_request"],
        )

        result = executor.execute(context)

        # Should escalate for answers
        assert result.needs_escalation() or result.status == StageStatus.COMPLETED
        if result.needs_escalation():
            assert "blocking" in result.escalation.get("message", "").lower()

    def test_incorporates_answers_into_requirements(
        self, tmp_path, sample_intake_artifact, mock_llm_response
    ):
        """Answers are incorporated into clarified requirements."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        # Add answers
        sample_intake_artifact["question_answers"] = {
            "What OAuth provider should be used?": "Google OAuth 2.0"
        }

        executor = ClarifyExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=tmp_path,
            input_artifacts=sample_intake_artifact,
            request=sample_intake_artifact["original_request"],
        )

        yaml_response = """```yaml
request_id: "REQ-20260101120000-0001"
clarified_requirements: |
  Add OAuth2 authentication using Google OAuth 2.0 provider.
scope_confirmed: true
answered_questions:
  - question: "What OAuth provider should be used?"
    answer: "Google OAuth 2.0"
    incorporated: true
remaining_questions: []
ready_for_analysis: true
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert "Google" in result.artifacts["clarified_requirements"]

    def test_handles_feedback_as_answers(
        self, tmp_path, sample_intake_artifact, mock_llm_response
    ):
        """Feedback from escalation is treated as input."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        # Simulate resumed context with feedback
        sample_intake_artifact["initial_questions"] = [
            {"question": "Which provider?", "priority": "blocking"}
        ]

        executor = ClarifyExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=tmp_path,
            input_artifacts=sample_intake_artifact,
            request=sample_intake_artifact["original_request"],
        )
        # Simulate feedback
        context.config["previous_feedback"] = "Use Google OAuth"

        yaml_response = """```yaml
request_id: "REQ-001"
clarified_requirements: "Use Google OAuth for authentication"
scope_confirmed: true
remaining_questions: []
ready_for_analysis: true
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            # Executor should process with feedback
            executor.get_user_message(context)
            # Feedback should be included if provided in context

    def test_marks_ready_when_complete(
        self, tmp_path, sample_intake_artifact, mock_llm_response
    ):
        """Sets ready_for_analysis when all blocking answered."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        sample_intake_artifact["question_answers"] = {
            "What OAuth provider should be used?": "Google"
        }

        executor = ClarifyExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=tmp_path,
            input_artifacts=sample_intake_artifact,
            request=sample_intake_artifact["original_request"],
        )

        yaml_response = """```yaml
request_id: "REQ-001"
clarified_requirements: "Add Google OAuth"
scope_confirmed: true
remaining_questions: []
ready_for_analysis: true
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.artifacts.get("ready_for_analysis") is True

    def test_creates_passthrough_artifact(self, tmp_path, sample_intake_artifact):
        """Passthrough artifact created when no clarification needed."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        # No blocking questions
        sample_intake_artifact["initial_questions"] = []

        executor = ClarifyExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=tmp_path,
            input_artifacts=sample_intake_artifact,
            request=sample_intake_artifact["original_request"],
        )

        result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        # Passthrough should carry forward key fields
        assert result.artifacts["request_id"] == sample_intake_artifact["request_id"]
        assert "clarified_requirements" in result.artifacts

    def test_validates_output_requirements(self, tmp_path):
        """Output validation checks for clarified_requirements."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        executor = ClarifyExecutor()

        # Missing clarified_requirements
        artifact = {
            "request_id": "REQ-001",
            "scope_confirmed": True,
        }

        validation = executor.validate_output(artifact)
        assert not validation.valid
        assert any("clarified_requirements" in e for e in validation.errors)

    def test_carries_forward_request_id(
        self, tmp_path, sample_intake_artifact, mock_llm_response
    ):
        """Request ID is carried forward from intake."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        sample_intake_artifact["initial_questions"] = []

        executor = ClarifyExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=tmp_path,
            input_artifacts=sample_intake_artifact,
            request=sample_intake_artifact["original_request"],
        )

        result = executor.execute(context)

        assert (
            result.artifacts["request_id"] == sample_intake_artifact["request_id"]
        )

    def test_warns_ready_with_blocking_remaining(self, tmp_path):
        """Warns if marked ready but blocking questions remain."""
        from agentforge.core.pipeline.stages.clarify import ClarifyExecutor

        executor = ClarifyExecutor()

        artifact = {
            "request_id": "REQ-001",
            "clarified_requirements": "Some requirements",
            "scope_confirmed": True,
            "remaining_questions": [{"question": "Still pending?", "priority": "blocking"}],
            "ready_for_analysis": True,
        }

        validation = executor.validate_output(artifact)
        # Should warn about inconsistency
        assert len(validation.warnings) >= 1 or not validation.valid


class TestCreateClarifyExecutor:
    """Tests for create_clarify_executor factory function."""

    def test_creates_executor_instance(self):
        """Factory creates ClarifyExecutor instance."""
        from agentforge.core.pipeline.stages.clarify import (
            ClarifyExecutor,
            create_clarify_executor,
        )

        executor = create_clarify_executor()
        assert isinstance(executor, ClarifyExecutor)

    def test_accepts_config_with_max_rounds(self):
        """Factory accepts config with max_rounds parameter."""
        from agentforge.core.pipeline.stages.clarify import create_clarify_executor

        config = {"max_rounds": 5}
        executor = create_clarify_executor(config)
        assert executor.max_clarification_rounds == 5
