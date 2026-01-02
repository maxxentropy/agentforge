# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1

"""
Integration tests for the design pipeline.

Tests the full INTAKE → CLARIFY → ANALYZE → SPEC flow.
"""

from unittest.mock import patch

from agentforge.core.pipeline import (
    StageContext,
    StageExecutorRegistry,
    StageStatus,
)
from agentforge.core.pipeline.stages import (
    AnalyzeExecutor,
    ClarifyExecutor,
    IntakeExecutor,
    SpecExecutor,
    register_design_stages,
)


class TestDesignPipelineFlow:
    """Integration tests for design pipeline flow."""

    def test_design_pipeline_intake_to_spec(self, temp_project_with_code):
        """Design pipeline executes INTAKE → CLARIFY → ANALYZE → SPEC."""
        registry = StageExecutorRegistry()
        register_design_stages(registry)

        # Verify all stages are registered
        assert registry.has_stage("intake")
        assert registry.has_stage("clarify")
        assert registry.has_stage("analyze")
        assert registry.has_stage("spec")

        # Create executors
        intake = registry.get("intake")
        clarify = registry.get("clarify")
        analyze = registry.get("analyze")
        spec = registry.get("spec")

        # Verify executor types
        assert isinstance(intake, IntakeExecutor)
        assert isinstance(clarify, ClarifyExecutor)
        assert isinstance(analyze, AnalyzeExecutor)
        assert isinstance(spec, SpecExecutor)

    def test_intake_artifact_flows_to_clarify(self, temp_project_with_code):
        """Intake artifact flows correctly to Clarify stage."""
        # Create intake executor
        intake = IntakeExecutor()

        # Mock LLM response for intake
        intake_response = {
            "response": """```yaml
request_id: "REQ-20260101120000-0001"
original_request: "Add OAuth authentication"
detected_scope: "feature_addition"
priority: "high"
confidence: 0.9
initial_questions: []
detected_components:
  - name: "auth"
    confidence: 0.9
keywords:
  - "oauth"
  - "authentication"
estimated_complexity: "medium"
```""",
            "tool_results": [],
        }

        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="intake",
            project_path=temp_project_with_code,
            input_artifacts={},
            request="Add OAuth authentication",
        )

        with patch.object(intake, "_run_with_llm") as mock_llm:
            mock_llm.return_value = intake_response
            intake_result = intake.execute(context)

        assert intake_result.status == StageStatus.COMPLETED
        assert intake_result.artifacts["request_id"] == "REQ-20260101120000-0001"
        assert intake_result.artifacts["detected_scope"] == "feature_addition"

        # Now pass to clarify
        clarify = ClarifyExecutor()
        clarify_context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="clarify",
            project_path=temp_project_with_code,
            input_artifacts=intake_result.artifacts,
            request="Add OAuth authentication",
        )

        # No blocking questions, should pass through
        clarify_result = clarify.execute(clarify_context)

        assert clarify_result.status == StageStatus.COMPLETED
        assert clarify_result.artifacts["request_id"] == "REQ-20260101120000-0001"
        assert clarify_result.artifacts["ready_for_analysis"] is True

    def test_design_pipeline_with_clarification(self, temp_project_with_code):
        """Design pipeline handles clarification with blocking questions."""
        intake = IntakeExecutor()

        # Intake with blocking questions
        intake_response = {
            "response": """```yaml
request_id: "REQ-20260101120000-0002"
original_request: "Add authentication"
detected_scope: "unclear"
priority: "medium"
initial_questions:
  - question: "What authentication method?"
    priority: "blocking"
    context: "Need to know provider"
```""",
            "tool_results": [],
        }

        context = StageContext(
            pipeline_id="PL-TEST-002",
            stage_name="intake",
            project_path=temp_project_with_code,
            input_artifacts={},
            request="Add authentication",
        )

        with patch.object(intake, "_run_with_llm") as mock_llm:
            mock_llm.return_value = intake_response
            intake_result = intake.execute(context)

        # Now clarify should escalate
        clarify = ClarifyExecutor()
        clarify_context = StageContext(
            pipeline_id="PL-TEST-002",
            stage_name="clarify",
            project_path=temp_project_with_code,
            input_artifacts=intake_result.artifacts,
            request="Add authentication",
        )

        clarify_result = clarify.execute(clarify_context)

        # Should escalate for answers
        assert clarify_result.needs_escalation()
        assert "blocking" in clarify_result.escalation.get("message", "").lower()

    def test_analyze_produces_component_list(self, temp_project_with_code):
        """Analyze stage produces component and file list."""
        analyze = AnalyzeExecutor()

        analyze_input = {
            "request_id": "REQ-001",
            "clarified_requirements": "Add OAuth2 authentication using Google",
            "priority": "high",
            "keywords": ["oauth", "google", "auth"],
        }

        context = StageContext(
            pipeline_id="PL-TEST-003",
            stage_name="analyze",
            project_path=temp_project_with_code,
            input_artifacts=analyze_input,
            request="Add OAuth authentication",
        )

        # Mock tool call result
        analyze_response = {
            "response": "Analysis complete",
            "tool_results": [
                {
                    "tool_name": "submit_analysis",
                    "input": {
                        "analysis_summary": "OAuth integration requires auth module changes",
                        "affected_files": [
                            {
                                "path": "src/auth.py",
                                "change_type": "modify",
                                "reason": "Add OAuth handler",
                            }
                        ],
                        "components": [
                            {
                                "name": "OAuthHandler",
                                "type": "class",
                                "description": "Handles OAuth flow",
                            }
                        ],
                        "risks": [],
                        "complexity": "medium",
                    },
                }
            ],
        }

        with patch.object(analyze, "_run_with_llm") as mock_llm:
            mock_llm.return_value = analyze_response
            result = analyze.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert len(result.artifacts["affected_files"]) > 0
        assert len(result.artifacts["components"]) > 0
        assert result.artifacts["affected_files"][0]["path"] == "src/auth.py"

    def test_spec_generates_test_cases(self, temp_project_with_code):
        """Spec stage generates component and test specifications."""
        spec = SpecExecutor()

        spec_input = {
            "request_id": "REQ-001",
            "clarified_requirements": "Add OAuth2 authentication",
            "analysis": {
                "summary": "OAuth integration",
                "complexity": "medium",
            },
            "affected_files": [
                {"path": "src/auth.py", "change_type": "modify"}
            ],
            "components": [
                {"name": "OAuthHandler", "type": "class"}
            ],
        }

        context = StageContext(
            pipeline_id="PL-TEST-004",
            stage_name="spec",
            project_path=temp_project_with_code,
            input_artifacts=spec_input,
            request="Add OAuth authentication",
        )

        spec_response = {
            "response": """```yaml
spec_id: "SPEC-20260101120000-0001"
request_id: "REQ-001"
title: "OAuth Authentication"
version: "1.0"

components:
  - name: "OAuthHandler"
    type: "class"
    file_path: "src/auth/oauth.py"
    description: "Handles OAuth authentication flow"

test_cases:
  - id: "TC001"
    component: "OAuthHandler"
    type: "unit"
    description: "Test login flow"
    given: "Valid credentials"
    when: "User initiates OAuth"
    then: "Token returned"
    priority: "high"

acceptance_criteria:
  - criterion: "All tests pass"
    measurable: true
```""",
            "tool_results": [],
        }

        with patch.object(spec, "_run_with_llm") as mock_llm:
            mock_llm.return_value = spec_response
            result = spec.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts["spec_id"].startswith("SPEC-")
        assert len(result.artifacts["components"]) > 0
        assert len(result.artifacts["test_cases"]) > 0

    def test_full_design_pipeline_with_mocked_llm(self, temp_project_with_code):
        """Full design pipeline flow with mocked LLM responses."""
        # Stage 1: Intake
        intake = IntakeExecutor()
        intake_ctx = StageContext(
            pipeline_id="PL-FULL-001",
            stage_name="intake",
            project_path=temp_project_with_code,
            input_artifacts={},
            request="Add user logout functionality",
        )

        intake_resp = {
            "response": """```yaml
request_id: "REQ-FULL-001"
original_request: "Add user logout functionality"
detected_scope: "feature_addition"
priority: "medium"
initial_questions: []
detected_components:
  - name: "auth"
    confidence: 0.95
keywords: ["logout", "user", "session"]
```""",
            "tool_results": [],
        }

        with patch.object(intake, "_run_with_llm", return_value=intake_resp):
            intake_result = intake.execute(intake_ctx)

        assert intake_result.status == StageStatus.COMPLETED

        # Stage 2: Clarify (passthrough - no blocking questions)
        clarify = ClarifyExecutor()
        clarify_ctx = StageContext(
            pipeline_id="PL-FULL-001",
            stage_name="clarify",
            project_path=temp_project_with_code,
            input_artifacts=intake_result.artifacts,
            request="Add user logout functionality",
        )

        clarify_result = clarify.execute(clarify_ctx)
        assert clarify_result.status == StageStatus.COMPLETED
        assert clarify_result.artifacts["ready_for_analysis"]

        # Stage 3: Analyze
        analyze = AnalyzeExecutor()
        analyze_ctx = StageContext(
            pipeline_id="PL-FULL-001",
            stage_name="analyze",
            project_path=temp_project_with_code,
            input_artifacts=clarify_result.artifacts,
            request="Add user logout functionality",
        )

        analyze_resp = {
            "response": "Done",
            "tool_results": [
                {
                    "tool_name": "submit_analysis",
                    "input": {
                        "analysis_summary": "Add logout method to AuthHandler",
                        "affected_files": [
                            {"path": "src/auth.py", "change_type": "modify", "reason": "Add logout"}
                        ],
                        "components": [
                            {"name": "AuthHandler", "type": "class", "description": "Auth handler"}
                        ],
                        "complexity": "low",
                    },
                }
            ],
        }

        with patch.object(analyze, "_run_with_llm", return_value=analyze_resp):
            analyze_result = analyze.execute(analyze_ctx)

        assert analyze_result.status == StageStatus.COMPLETED

        # Stage 4: Spec
        spec = SpecExecutor()
        spec_ctx = StageContext(
            pipeline_id="PL-FULL-001",
            stage_name="spec",
            project_path=temp_project_with_code,
            input_artifacts=analyze_result.artifacts,
            request="Add user logout functionality",
        )

        spec_resp = {
            "response": """```yaml
spec_id: "SPEC-FULL-001"
request_id: "REQ-FULL-001"
title: "User Logout"
components:
  - name: "AuthHandler.logout"
    type: "method"
    file_path: "src/auth.py"
test_cases:
  - id: "TC001"
    description: "Test logout clears session"
acceptance_criteria:
  - criterion: "Logout clears user session"
```""",
            "tool_results": [],
        }

        with patch.object(spec, "_run_with_llm", return_value=spec_resp):
            spec_result = spec.execute(spec_ctx)

        assert spec_result.status == StageStatus.COMPLETED
        assert spec_result.artifacts["spec_id"] == "SPEC-FULL-001"

        # Verify pipeline completed all stages
        assert intake_result.is_success()
        assert clarify_result.is_success()
        assert analyze_result.is_success()
        assert spec_result.is_success()
