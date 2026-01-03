# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: llm-stage-executor
# @test_path: tests/unit/pipeline/test_llm_stage_executor.py

"""Tests for LLMStageExecutor and ToolBasedStageExecutor."""

from unittest.mock import patch

from agentforge.core.pipeline import StageContext, StageStatus


class TestLLMStageExecutor:
    """Tests for LLMStageExecutor base class."""

    def test_execute_calls_lifecycle_methods(self, temp_project):
        """Execute calls get_system_prompt, get_user_message, parse_response in order."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        # Track method calls
        calls = []

        class TestLLMExecutor(LLMStageExecutor):
            stage_name = "test"

            def get_system_prompt(self, context):
                calls.append("get_system_prompt")
                return "System prompt"

            def get_user_message(self, context):
                calls.append("get_user_message")
                return "User message"

            def parse_response(self, llm_result, context):
                calls.append("parse_response")
                return {"result": "parsed"}

        executor = TestLLMExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="test",
            project_path=temp_project,
            input_artifacts={},
            request="Test request",
        )

        # Mock the LLM execution
        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = {"response": "LLM response"}
            executor.execute(context)

        assert "get_system_prompt" in calls, "Expected 'get_system_prompt' in calls"
        assert "get_user_message" in calls, "Expected 'get_user_message' in calls"
        assert "parse_response" in calls, "Expected 'parse_response' in calls"
        # Verify order
        assert calls.index("get_system_prompt") < calls.index("parse_response"), "Expected calls.index('get_system_pro... < calls.index('parse_response')"
        assert calls.index("get_user_message") < calls.index("parse_response"), "Expected calls.index('get_user_messa... < calls.index('parse_response')"

    def test_execute_calls_get_prompts_and_parse(self, temp_project):
        """Execute calls get_system_prompt, get_user_message, parse_response."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        class TestLLMExecutor(LLMStageExecutor):
            stage_name = "test"
            get_system_prompt_called = False
            get_user_message_called = False
            parse_response_called = False

            def get_system_prompt(self, context):
                self.get_system_prompt_called = True
                return "System"

            def get_user_message(self, context):
                self.get_user_message_called = True
                return "User"

            def parse_response(self, llm_result, context):
                self.parse_response_called = True
                return {"data": "test"}

        executor = TestLLMExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="test",
            project_path=temp_project,
            input_artifacts={},
            request="Test request",
        )

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = {"response": "test"}
            executor.execute(context)

        assert executor.get_system_prompt_called, "Expected executor.get_system_prompt_... to be truthy"
        assert executor.get_user_message_called, "Expected executor.get_user_message_c... to be truthy"
        assert executor.parse_response_called, "Expected executor.parse_response_called to be truthy"

    def test_failed_parse_returns_failed_result(self, temp_project):
        """When parse_response returns None, result is FAILED."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        class FailingParser(LLMStageExecutor):
            stage_name = "test"

            def get_system_prompt(self, context):
                return "System"

            def get_user_message(self, context):
                return "User"

            def parse_response(self, llm_result, context):
                return None  # Parse fails

        executor = FailingParser()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="test",
            project_path=temp_project,
            input_artifacts={},
            request="Test request",
        )

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = {"response": "unparseable"}
            result = executor.execute(context)

        assert result.status == StageStatus.FAILED, "Expected result.status to equal StageStatus.FAILED"
        assert "parse" in result.error.lower() or "artifact" in result.error.lower(), "Assertion failed"

    def test_extract_yaml_from_code_block(self):
        """YAML in code blocks is extracted correctly."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        class TestExecutor(LLMStageExecutor):
            stage_name = "test"

            def get_system_prompt(self, context):
                return ""

            def get_user_message(self, context):
                return ""

            def parse_response(self, llm_result, context):
                return {}

        executor = TestExecutor()
        response = """Here is the result:

```yaml
key: value
nested:
  item: 123
```

More text after."""

        result = executor.extract_yaml_from_response(response)
        assert result is not None, "Expected result is not None"
        assert result["key"] == "value", "Expected result['key'] to equal 'value'"
        assert result["nested"]["item"] == 123, "Expected result['nested']['item'] to equal 123"

    def test_extract_yaml_from_raw_text(self):
        """Raw YAML without code blocks is parsed correctly."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        class TestExecutor(LLMStageExecutor):
            stage_name = "test"

            def get_system_prompt(self, context):
                return ""

            def get_user_message(self, context):
                return ""

            def parse_response(self, llm_result, context):
                return {}

        executor = TestExecutor()
        response = """key: value
items:
  - one
  - two"""

        result = executor.extract_yaml_from_response(response)
        assert result is not None, "Expected result is not None"
        assert result["key"] == "value", "Expected result['key'] to equal 'value'"
        assert result["items"] == ["one", "two"], "Expected result['items'] to equal ['one', 'two']"

    def test_extract_yaml_handles_invalid(self):
        """Invalid YAML returns None."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        class TestExecutor(LLMStageExecutor):
            stage_name = "test"

            def get_system_prompt(self, context):
                return ""

            def get_user_message(self, context):
                return ""

            def parse_response(self, llm_result, context):
                return {}

        executor = TestExecutor()
        response = "This is not YAML: {{{invalid}}}"

        result = executor.extract_yaml_from_response(response)
        assert result is None, "Expected result is None"

    def test_extract_json_from_code_block(self):
        """JSON in code blocks is extracted correctly."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        class TestExecutor(LLMStageExecutor):
            stage_name = "test"

            def get_system_prompt(self, context):
                return ""

            def get_user_message(self, context):
                return ""

            def parse_response(self, llm_result, context):
                return {}

        executor = TestExecutor()
        response = """Here is the JSON:

```json
{"key": "value", "number": 42}
```
"""

        result = executor.extract_json_from_response(response)
        assert result is not None, "Expected result is not None"
        assert result["key"] == "value", "Expected result['key'] to equal 'value'"
        assert result["number"] == 42, "Expected result['number'] to equal 42"

    def test_extract_json_from_raw_text(self):
        """JSON embedded in text is extracted correctly."""
        from agentforge.core.pipeline.llm_stage_executor import LLMStageExecutor

        class TestExecutor(LLMStageExecutor):
            stage_name = "test"

            def get_system_prompt(self, context):
                return ""

            def get_user_message(self, context):
                return ""

            def parse_response(self, llm_result, context):
                return {}

        executor = TestExecutor()
        response = 'The result is {"data": true, "count": 5} as shown.'

        result = executor.extract_json_from_response(response)
        assert result is not None, "Expected result is not None"
        assert result["data"] is True, "Expected result['data'] is True"
        assert result["count"] == 5, "Expected result['count'] to equal 5"


class TestToolBasedStageExecutor:
    """Tests for ToolBasedStageExecutor."""

    def test_tool_based_executor_extracts_from_tool_call(self, temp_project):
        """ToolBasedStageExecutor extracts artifact from specified tool call."""
        from agentforge.core.pipeline.llm_stage_executor import ToolBasedStageExecutor

        class TestToolExecutor(ToolBasedStageExecutor):
            stage_name = "test"
            artifact_tool_name = "submit_result"

            def get_system_prompt(self, context):
                return "System"

            def get_user_message(self, context):
                return "User"

        executor = TestToolExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="test",
            project_path=temp_project,
            input_artifacts={},
            request="Test request",
        )

        # Simulate tool call result
        llm_result = {
            "response": "Done",
            "tool_results": [
                {
                    "tool_name": "submit_result",
                    "input": {"analysis": "completed", "items": [1, 2, 3]},
                }
            ],
        }

        result = executor.parse_response(llm_result, context)
        assert result is not None, "Expected result is not None"
        assert result["analysis"] == "completed", "Expected result['analysis'] to equal 'completed'"
        assert result["items"] == [1, 2, 3], "Expected result['items'] to equal [1, 2, 3]"

    def test_tool_based_executor_uses_artifact_tool_name(self, temp_project):
        """ToolBasedStageExecutor only extracts from configured tool name."""
        from agentforge.core.pipeline.llm_stage_executor import ToolBasedStageExecutor

        class TestToolExecutor(ToolBasedStageExecutor):
            stage_name = "test"
            artifact_tool_name = "my_tool"

            def get_system_prompt(self, context):
                return "System"

            def get_user_message(self, context):
                return "User"

        executor = TestToolExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="test",
            project_path=temp_project,
            input_artifacts={},
            request="Test request",
        )

        # Wrong tool name - should not extract
        llm_result = {
            "response": "Done",
            "tool_results": [
                {
                    "tool_name": "wrong_tool",
                    "input": {"wrong": "data"},
                }
            ],
        }

        result = executor.parse_response(llm_result, context)
        # Should fall back to final_artifact or None
        assert result is None or result.get("wrong") is None, "Assertion failed"

    def test_tool_based_executor_fallback_to_final_artifact(self, temp_project):
        """ToolBasedStageExecutor falls back to final_artifact if tool not called."""
        from agentforge.core.pipeline.llm_stage_executor import ToolBasedStageExecutor

        class TestToolExecutor(ToolBasedStageExecutor):
            stage_name = "test"
            artifact_tool_name = "submit_result"

            def get_system_prompt(self, context):
                return "System"

            def get_user_message(self, context):
                return "User"

        executor = TestToolExecutor()
        context = StageContext(
            pipeline_id="PL-TEST-001",
            stage_name="test",
            project_path=temp_project,
            input_artifacts={},
            request="Test request",
        )

        # No tool call, but has final_artifact
        llm_result = {
            "response": "Done",
            "tool_results": [],
            "final_artifact": {"fallback": "data"},
        }

        result = executor.parse_response(llm_result, context)
        assert result is not None, "Expected result is not None"
        assert result["fallback"] == "data", "Expected result['fallback'] to equal 'data'"
