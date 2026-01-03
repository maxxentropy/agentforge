# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: intake-executor
# @test_path: tests/unit/pipeline/stages/test_intake.py

"""Tests for IntakeExecutor."""

from unittest.mock import patch

from agentforge.core.pipeline import StageContext, StageStatus


class TestIntakeExecutor:
    """Tests for IntakeExecutor stage."""

    def test_parses_simple_request(self, tmp_path, mock_llm_response):
        """Simple request produces valid IntakeRecord."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="Add a logout button",
        )

        yaml_response = """```yaml
request_id: "REQ-20260101120000-0001"
original_request: "Add a logout button"
detected_scope: "feature_addition"
priority: "medium"
confidence: 0.9
initial_questions: []
detected_components:
  - name: "ui_components"
    confidence: 0.8
keywords:
  - "logout"
  - "button"
estimated_complexity: "low"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED, "Expected result.status to equal StageStatus.COMPLETED"
        assert result.artifacts["request_id"] == "REQ-20260101120000-0001", "Expected result.artifacts['request_id'] to equal 'REQ-20260101120000-0001'"
        assert result.artifacts["detected_scope"] == "feature_addition", "Expected result.artifacts['detected_... to equal 'feature_addition'"

    def test_detects_bug_fix_scope(self, tmp_path, mock_llm_response):
        """Bug fix requests detected correctly."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="Fix the login error on Safari",
        )

        yaml_response = """```yaml
request_id: "REQ-20260101120000-0002"
original_request: "Fix the login error on Safari"
detected_scope: "bug_fix"
priority: "high"
confidence: 0.95
initial_questions:
  - question: "What is the error message?"
    priority: "blocking"
    context: "Need to reproduce the issue"
detected_components:
  - name: "auth"
    confidence: 0.9
keywords:
  - "fix"
  - "error"
  - "login"
estimated_complexity: "medium"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED, "Expected result.status to equal StageStatus.COMPLETED"
        assert result.artifacts["detected_scope"] == "bug_fix", "Expected result.artifacts['detected_... to equal 'bug_fix'"

    def test_detects_feature_addition_scope(self, tmp_path, mock_llm_response):
        """Feature requests detected correctly."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="Add dark mode support",
        )

        yaml_response = """```yaml
request_id: "REQ-001"
original_request: "Add dark mode support"
detected_scope: "feature_addition"
priority: "medium"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.artifacts["detected_scope"] == "feature_addition", "Expected result.artifacts['detected_... to equal 'feature_addition'"

    def test_detects_refactoring_scope(self, tmp_path, mock_llm_response):
        """Refactoring requests detected correctly."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="Refactor the authentication module",
        )

        yaml_response = """```yaml
request_id: "REQ-001"
original_request: "Refactor the authentication module"
detected_scope: "refactoring"
priority: "low"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.artifacts["detected_scope"] == "refactoring", "Expected result.artifacts['detected_... to equal 'refactoring'"

    def test_generates_blocking_questions_for_unclear(
        self, tmp_path, mock_llm_response
    ):
        """Unclear requests generate blocking questions."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="Make it better",
        )

        yaml_response = """```yaml
request_id: "REQ-001"
original_request: "Make it better"
detected_scope: "unclear"
priority: "medium"
initial_questions:
  - question: "What aspect should be improved?"
    priority: "blocking"
    context: "Request is too vague"
  - question: "What is the current problem?"
    priority: "blocking"
    context: "Need baseline for improvement"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.artifacts["detected_scope"] == "unclear", "Expected result.artifacts['detected_... to equal 'unclear'"
        assert len(result.artifacts["initial_questions"]) >= 1, "Expected len(result.artifacts['initi... >= 1"
        blocking = [
            q
            for q in result.artifacts["initial_questions"]
            if q.get("priority") == "blocking"
        ]
        assert len(blocking) >= 1, "Expected len(blocking) >= 1"

    def test_generates_unique_request_ids(self, tmp_path, mock_llm_response):
        """Each execution generates unique request_id."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()

        # First execution
        context1 = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="First request",
        )

        yaml_response1 = """```yaml
request_id: "REQ-20260101120000-0001"
original_request: "First request"
detected_scope: "feature_addition"
priority: "medium"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response1)
            result1 = executor.execute(context1)

        # Second execution
        context2 = StageContext(
            pipeline_id="PL-TEST-002",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="Second request",
        )

        yaml_response2 = """```yaml
request_id: "REQ-20260101120001-0002"
original_request: "Second request"
detected_scope: "bug_fix"
priority: "high"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response2)
            result2 = executor.execute(context2)

        assert result1.artifacts["request_id"] != result2.artifacts["request_id"], "Expected result1.artifacts['request_... to not equal result2.artifacts['request_..."

    def test_validates_output_required_fields(self, tmp_path, mock_llm_response):
        """Output validation catches missing fields."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()

        # Missing request_id should fail validation
        artifact = {
            "detected_scope": "feature_addition",
            "priority": "medium",
        }

        validation = executor.validate_output(artifact)
        assert not validation.valid, "Assertion failed"
        assert any("request_id" in e for e in validation.errors), "Expected any() to be truthy"

    def test_validates_output_scope_values(self, tmp_path):
        """Output validation catches invalid scope values."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()

        artifact = {
            "request_id": "REQ-001",
            "detected_scope": "invalid_scope",
            "priority": "medium",
        }

        validation = executor.validate_output(artifact)
        assert not validation.valid, "Assertion failed"
        assert any("scope" in e.lower() for e in validation.errors), "Expected any() to be truthy"

    def test_validates_output_priority_values(self, tmp_path):
        """Output validation warns on invalid priority values."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()

        artifact = {
            "request_id": "REQ-001",
            "detected_scope": "feature_addition",
            "priority": "invalid_priority",
        }

        validation = executor.validate_output(artifact)
        # Invalid priority is a warning, not an error
        assert len(validation.warnings) >= 1 or not validation.valid, "Assertion failed"

    def test_handles_empty_request(self, tmp_path, mock_llm_response):
        """Empty request is handled gracefully."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={},
            request="",
        )

        yaml_response = """```yaml
request_id: "REQ-001"
original_request: ""
detected_scope: "unclear"
priority: "low"
initial_questions:
  - question: "What would you like to build?"
    priority: "blocking"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED, "Expected result.status to equal StageStatus.COMPLETED"
        assert result.artifacts["detected_scope"] == "unclear", "Expected result.artifacts['detected_... to equal 'unclear'"

    def test_carries_forward_project_context(self, tmp_path, mock_llm_response):
        """Project context from input is included in prompt."""
        from agentforge.core.pipeline.stages.intake import IntakeExecutor

        executor = IntakeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=tmp_path,
            input_artifacts={"project_context": "This is a Python web application"},
            request="Add caching",
        )

        yaml_response = """```yaml
request_id: "REQ-001"
original_request: "Add caching"
detected_scope: "feature_addition"
priority: "medium"
```"""

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response(yaml_response)
            executor.execute(context)

        # Check that get_user_message includes project context
        user_msg = executor.get_user_message(context)
        assert "Python web application" in user_msg, "Expected 'Python web application' in user_msg"


class TestCreateIntakeExecutor:
    """Tests for create_intake_executor factory function."""

    def test_creates_executor_instance(self):
        """Factory creates IntakeExecutor instance."""
        from agentforge.core.pipeline.stages.intake import (
            IntakeExecutor,
            create_intake_executor,
        )

        executor = create_intake_executor()
        assert isinstance(executor, IntakeExecutor), "Expected isinstance() to be truthy"

    def test_accepts_config(self):
        """Factory accepts config parameter."""
        from agentforge.core.pipeline.stages.intake import create_intake_executor

        config = {"custom_setting": True}
        executor = create_intake_executor(config)
        assert executor.config.get("custom_setting") is True, "Expected executor.config.get('custom... is True"
