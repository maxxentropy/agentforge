# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: analyze-executor
# @test_path: tests/unit/pipeline/stages/test_analyze.py

"""Tests for AnalyzeExecutor."""

from unittest.mock import patch

from agentforge.core.pipeline import StageContext, StageStatus


class TestAnalyzeExecutor:
    """Tests for AnalyzeExecutor stage."""

    def test_uses_submit_analysis_tool(
        self, tmp_path, sample_clarify_artifact, mock_llm_with_tools
    ):
        """Executor uses submit_analysis for artifact extraction."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="analyze",
            project_path=tmp_path,
            input_artifacts=sample_clarify_artifact,
            request=sample_clarify_artifact.get("original_request", "Test"),
        )

        tool_result = {
            "response": "Analysis complete",
            "tool_results": [
                {
                    "tool_name": "submit_analysis",
                    "input": {
                        "analysis_summary": "OAuth integration analysis",
                        "affected_files": [
                            {
                                "path": "src/auth/oauth.py",
                                "change_type": "create",
                                "reason": "New OAuth handler",
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

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = tool_result
            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED, "Expected result.status to equal StageStatus.COMPLETED"
        assert len(result.artifacts["affected_files"]) > 0, "Expected len(result.artifacts['affec... > 0"
        assert len(result.artifacts["components"]) > 0, "Expected len(result.artifacts['compo... > 0"

    def test_defines_required_tools(self):
        """Executor defines search_code, read_file, find_related, submit_analysis tools."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        tool_names = [t["name"] for t in executor.tools]

        assert "search_code" in tool_names, "Expected 'search_code' in tool_names"
        assert "read_file" in tool_names, "Expected 'read_file' in tool_names"
        assert "find_related" in tool_names, "Expected 'find_related' in tool_names"
        assert "submit_analysis" in tool_names, "Expected 'submit_analysis' in tool_names"

    def test_produces_affected_files_list(
        self, tmp_path, sample_clarify_artifact
    ):
        """Output includes affected files."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="analyze",
            project_path=tmp_path,
            input_artifacts=sample_clarify_artifact,
            request="Test",
        )

        tool_result = {
            "response": "Done",
            "tool_results": [
                {
                    "tool_name": "submit_analysis",
                    "input": {
                        "analysis_summary": "Summary",
                        "affected_files": [
                            {"path": "file1.py", "change_type": "modify", "reason": "Update"}
                        ],
                        "components": [{"name": "Test", "type": "class"}],
                    },
                }
            ],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = tool_result
            result = executor.execute(context)

        assert "affected_files" in result.artifacts, "Expected 'affected_files' in result.artifacts"
        assert len(result.artifacts["affected_files"]) > 0, "Expected len(result.artifacts['affec... > 0"
        assert result.artifacts["affected_files"][0]["path"] == "file1.py", "Expected result.artifacts['affected_... to equal 'file1.py'"

    def test_produces_components_list(self, tmp_path, sample_clarify_artifact):
        """Output includes components list."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="analyze",
            project_path=tmp_path,
            input_artifacts=sample_clarify_artifact,
            request="Test",
        )

        tool_result = {
            "response": "Done",
            "tool_results": [
                {
                    "tool_name": "submit_analysis",
                    "input": {
                        "analysis_summary": "Summary",
                        "affected_files": [],
                        "components": [
                            {
                                "name": "AuthHandler",
                                "type": "class",
                                "description": "Auth component",
                            }
                        ],
                    },
                }
            ],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = tool_result
            result = executor.execute(context)

        assert "components" in result.artifacts, "Expected 'components' in result.artifacts"
        assert len(result.artifacts["components"]) > 0, "Expected len(result.artifacts['compo... > 0"
        assert result.artifacts["components"][0]["name"] == "AuthHandler", "Expected result.artifacts['component... to equal 'AuthHandler'"

    def test_identifies_risks(self, tmp_path, sample_clarify_artifact):
        """Output includes risk assessment."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="analyze",
            project_path=tmp_path,
            input_artifacts=sample_clarify_artifact,
            request="Test",
        )

        tool_result = {
            "response": "Done",
            "tool_results": [
                {
                    "tool_name": "submit_analysis",
                    "input": {
                        "analysis_summary": "Summary",
                        "affected_files": [],
                        "components": [{"name": "Test", "type": "class"}],
                        "risks": [
                            {
                                "description": "Security concern",
                                "severity": "high",
                                "mitigation": "Use encryption",
                            }
                        ],
                    },
                }
            ],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = tool_result
            result = executor.execute(context)

        assert "risks" in result.artifacts, "Expected 'risks' in result.artifacts"
        assert len(result.artifacts["risks"]) > 0, "Expected len(result.artifacts['risks']) > 0"
        assert result.artifacts["risks"][0]["severity"] == "high", "Expected result.artifacts['risks'][0... to equal 'high'"

    def test_handles_missing_tool_call(self, tmp_path, sample_clarify_artifact):
        """Handles case where submit_analysis tool was not called."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="analyze",
            project_path=tmp_path,
            input_artifacts=sample_clarify_artifact,
            request="Test",
        )

        # No submit_analysis call, but has text response
        llm_result = {
            "response": "I analyzed the code but forgot to call the tool.",
            "tool_results": [
                {"tool_name": "search_code", "input": {"pattern": "auth"}, "result": []}
            ],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = llm_result
            result = executor.execute(context)

        # Should fall back to text parsing or return minimal artifact
        assert result.status in [StageStatus.COMPLETED, StageStatus.FAILED], "Expected result.status in [StageStatus.COMPLETED, Sta..."

    def test_fallback_to_text_parsing(self, tmp_path, sample_clarify_artifact):
        """Falls back to text parsing if tool not called."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="analyze",
            project_path=tmp_path,
            input_artifacts=sample_clarify_artifact,
            request="Test",
        )

        # No tool call, but has YAML in response
        llm_result = {
            "response": """Here's the analysis:

```yaml
analysis_summary: "Text-based analysis"
affected_files:
  - path: "src/main.py"
    change_type: "modify"
components:
  - name: "MainModule"
    type: "module"
```""",
            "tool_results": [],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = llm_result
            result = executor.execute(context)

        # Should have parsed something
        assert result.artifacts.get("request_id") is not None, "Expected result.artifacts.get('reque... is not None"

    def test_validates_output_analysis_section(self, tmp_path):
        """Output validation checks for analysis section."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()

        # Missing analysis section
        artifact = {
            "request_id": "REQ-001",
            "affected_files": [],
            "components": [],
        }

        validation = executor.validate_output(artifact)
        assert not validation.valid, "Assertion failed"
        assert any("analysis" in e.lower() for e in validation.errors), "Expected any() to be truthy"

    def test_carries_forward_requirements(
        self, tmp_path, sample_clarify_artifact
    ):
        """Clarified requirements are carried forward."""
        from agentforge.core.pipeline.stages.analyze import AnalyzeExecutor

        executor = AnalyzeExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="analyze",
            project_path=tmp_path,
            input_artifacts=sample_clarify_artifact,
            request="Test",
        )

        tool_result = {
            "response": "Done",
            "tool_results": [
                {
                    "tool_name": "submit_analysis",
                    "input": {
                        "analysis_summary": "Summary",
                        "affected_files": [],
                        "components": [{"name": "Test", "type": "class"}],
                    },
                }
            ],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = tool_result
            result = executor.execute(context)

        # Should carry forward clarified_requirements
        assert "clarified_requirements" in result.artifacts, "Expected 'clarified_requirements' in result.artifacts"


class TestCreateAnalyzeExecutor:
    """Tests for create_analyze_executor factory function."""

    def test_creates_executor_instance(self):
        """Factory creates AnalyzeExecutor instance."""
        from agentforge.core.pipeline.stages.analyze import (
            AnalyzeExecutor,
            create_analyze_executor,
        )

        executor = create_analyze_executor()
        assert isinstance(executor, AnalyzeExecutor), "Expected isinstance() to be truthy"

    def test_accepts_config(self):
        """Factory accepts config parameter."""
        from agentforge.core.pipeline.stages.analyze import create_analyze_executor

        config = {"max_files_to_read": 30}
        executor = create_analyze_executor(config)
        assert executor.config.get("max_files_to_read") == 30, "Expected executor.config.get('max_fi... to equal 30"
