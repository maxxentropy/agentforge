# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: harness-minimal_context-executor
# @impl_path: tools/harness/minimal_context/executor.py

"""Tests for Action Parser."""

import pytest

from agentforge.core.harness.action_parser import ActionParser
from agentforge.core.harness.llm_executor_domain import (
    ActionParseError,
    ActionType,
)


class TestActionParserBasic:
    """Basic parsing tests."""

    @pytest.fixture
    def parser(self):
        return ActionParser()

    def test_parse_tool_call(self, parser):
        """Parse a valid tool call action."""
        response = """
<thinking>
I need to read the file to understand its contents.
</thinking>

<action type="tool_call">
<tool name="read_file">
<parameter name="path">/src/main.py</parameter>
</tool>
</action>
"""
        action = parser.parse(response)

        assert action.action_type == ActionType.TOOL_CALL, "Expected action.action_type to equal ActionType.TOOL_CALL"
        assert "read the file" in action.reasoning, "Expected 'read the file' in action.reasoning"
        assert len(action.tool_calls) == 1, "Expected len(action.tool_calls) to equal 1"
        assert action.tool_calls[0].name == "read_file", "Expected action.tool_calls[0].name to equal 'read_file'"
        assert action.tool_calls[0].parameters["path"] == "/src/main.py", "Expected action.tool_calls[0].parame... to equal '/src/main.py'"

    def test_parse_multiple_tool_calls(self, parser):
        """Parse multiple tools in one action."""
        response = """
<thinking>
Need to read two files.
</thinking>

<action type="tool_call">
<tool name="read_file">
<parameter name="path">/src/a.py</parameter>
</tool>
<tool name="read_file">
<parameter name="path">/src/b.py</parameter>
</tool>
</action>
"""
        action = parser.parse(response)

        assert action.action_type == ActionType.TOOL_CALL, "Expected action.action_type to equal ActionType.TOOL_CALL"
        assert len(action.tool_calls) == 2, "Expected len(action.tool_calls) to equal 2"
        assert action.tool_calls[0].parameters["path"] == "/src/a.py", "Expected action.tool_calls[0].parame... to equal '/src/a.py'"
        assert action.tool_calls[1].parameters["path"] == "/src/b.py", "Expected action.tool_calls[1].parame... to equal '/src/b.py'"

    def test_parse_complete_action(self, parser):
        """Parse a completion action."""
        response = """
<thinking>
All tests are passing, the task is done.
</thinking>

<action type="complete">
<summary>Successfully implemented the feature with all tests passing.</summary>
</action>
"""
        action = parser.parse(response)

        assert action.action_type == ActionType.COMPLETE, "Expected action.action_type to equal ActionType.COMPLETE"
        assert "tests are passing" in action.reasoning, "Expected 'tests are passing' in action.reasoning"
        assert "Successfully implemented" in action.response, "Expected 'Successfully implemented' in action.response"

    def test_parse_ask_user_action(self, parser):
        """Parse an ask user action."""
        response = """
<thinking>
I need clarification on the requirements.
</thinking>

<action type="ask_user">
<question>Should the API support both JSON and XML formats?</question>
</action>
"""
        action = parser.parse(response)

        assert action.action_type == ActionType.ASK_USER, "Expected action.action_type to equal ActionType.ASK_USER"
        assert "JSON and XML" in action.response, "Expected 'JSON and XML' in action.response"

    def test_parse_escalate_action(self, parser):
        """Parse an escalation action."""
        response = """
<thinking>
I've tried multiple approaches but keep hitting a dead end.
</thinking>

<action type="escalate">
<reason>Unable to resolve the circular dependency after 5 attempts.</reason>
</action>
"""
        action = parser.parse(response)

        assert action.action_type == ActionType.ESCALATE, "Expected action.action_type to equal ActionType.ESCALATE"
        assert "circular dependency" in action.reasoning, "Expected 'circular dependency' in action.reasoning"

    def test_parse_respond_action(self, parser):
        """Parse a response action."""
        response = """
<thinking>
The user asked a question.
</thinking>

<action type="respond">
Here is my detailed answer to your question.
</action>
"""
        action = parser.parse(response)

        assert action.action_type == ActionType.RESPOND, "Expected action.action_type to equal ActionType.RESPOND"
        assert "detailed answer" in action.response, "Expected 'detailed answer' in action.response"


class TestActionParserEdgeCases:
    """Edge case and error handling tests."""

    @pytest.fixture
    def parser(self):
        return ActionParser()

    def test_empty_response_raises(self, parser):
        """Empty response should raise error."""
        with pytest.raises(ActionParseError) as exc_info:
            parser.parse("")
        assert "Empty response" in str(exc_info.value), "Expected 'Empty response' in str(exc_info.value)"

    def test_whitespace_only_raises(self, parser):
        """Whitespace-only response should raise error."""
        with pytest.raises(ActionParseError):
            parser.parse("   \n\t  ")

    def test_missing_action_infers_think(self, parser):
        """Response without action tag but with thinking infers THINK action."""
        response = """
<thinking>
Just thinking here, no action.
</thinking>
"""
        action = parser.parse(response)
        assert action.action_type == ActionType.THINK, "Expected action.action_type to equal ActionType.THINK"
        assert "Just thinking here" in action.reasoning, "Expected 'Just thinking here' in action.reasoning"

    def test_no_structure_raises(self, parser):
        """Response with no recognizable structure should raise error."""
        response = "Just some random text with no XML structure at all."
        with pytest.raises(ActionParseError):
            parser.parse(response)

    def test_invalid_action_type_raises(self, parser):
        """Invalid action type should raise error."""
        response = """
<action type="invalid_type">
content
</action>
"""
        with pytest.raises(ActionParseError) as exc_info:
            parser.parse(response)
        assert "Invalid action type" in str(exc_info.value), "Expected 'Invalid action type' in str(exc_info.value)"

    def test_tool_call_without_tools_raises(self, parser):
        """tool_call action without tools should raise error."""
        response = """
<thinking>
Going to call a tool.
</thinking>

<action type="tool_call">
No tools here.
</action>
"""
        with pytest.raises(ActionParseError) as exc_info:
            parser.parse(response)
        assert "no tools defined" in str(exc_info.value), "Expected 'no tools defined' in str(exc_info.value)"

    def test_missing_thinking_section(self, parser):
        """Response without thinking section should still parse."""
        response = """
<action type="complete">
<summary>Done with the task.</summary>
</action>
"""
        action = parser.parse(response)
        assert action.action_type == ActionType.COMPLETE, "Expected action.action_type to equal ActionType.COMPLETE"
        assert action.reasoning == "", "Expected action.reasoning to equal ''"

    def test_case_insensitive_tags(self, parser):
        """Tags should be case insensitive."""
        response = """
<THINKING>
Case test.
</THINKING>

<ACTION TYPE="complete">
<SUMMARY>Done</SUMMARY>
</ACTION>
"""
        action = parser.parse(response)
        assert action.action_type == ActionType.COMPLETE, "Expected action.action_type to equal ActionType.COMPLETE"

    def test_tool_parameters_empty(self, parser):
        """Tool with no parameters should work."""
        response = """
<thinking>Running tests.</thinking>
<action type="tool_call">
<tool name="run_tests">
</tool>
</action>
"""
        action = parser.parse(response)
        assert len(action.tool_calls) == 1, "Expected len(action.tool_calls) to equal 1"
        assert action.tool_calls[0].name == "run_tests", "Expected action.tool_calls[0].name to equal 'run_tests'"
        assert action.tool_calls[0].parameters == {}, "Expected action.tool_calls[0].parame... to equal {}"

    def test_multiline_parameter_values(self, parser):
        """Parameters can contain multiline values."""
        response = """
<thinking>Writing code.</thinking>
<action type="tool_call">
<tool name="write_file">
<parameter name="path">/test.py</parameter>
<parameter name="content">def hello():
    print("hello")
    return True</parameter>
</tool>
</action>
"""
        action = parser.parse(response)
        assert "def hello():" in action.tool_calls[0].parameters["content"], "Expected 'def hello():' in action.tool_calls[0].parame..."
        assert 'print("hello")' in action.tool_calls[0].parameters["content"], "Expected 'print(\"hello\")' in action.tool_calls[0].parame..."


class TestActionParserLenient:
    """Tests for lenient parsing mode."""

    @pytest.fixture
    def parser(self):
        return ActionParser()

    def test_lenient_parses_valid_normally(self, parser):
        """Lenient mode works for valid input."""
        response = """
<thinking>Test</thinking>
<action type="complete">
<summary>Done</summary>
</action>
"""
        action = parser.parse_lenient(response)
        assert action.action_type == ActionType.COMPLETE, "Expected action.action_type to equal ActionType.COMPLETE"

    def test_lenient_handles_missing_action_tag(self, parser):
        """Lenient mode handles missing action tag."""
        response = """
<thinking>
Just some thinking with nothing else.
</thinking>
"""
        action = parser.parse_lenient(response)
        # Should fall back to THINK action
        assert action.action_type == ActionType.THINK, "Expected action.action_type to equal ActionType.THINK"

    def test_lenient_detects_tool_calls_without_action_tag(self, parser):
        """Lenient mode detects tool calls without action tag."""
        response = """
<thinking>Reading file.</thinking>
<tool name="read_file">
<parameter name="path">/test.py</parameter>
</tool>
"""
        action = parser.parse_lenient(response)
        assert action.action_type == ActionType.TOOL_CALL, "Expected action.action_type to equal ActionType.TOOL_CALL"

    def test_lenient_detects_completion_phrases(self, parser):
        """Lenient mode detects completion from phrases."""
        response = """
I have successfully completed the task. All tests pass.
"""
        action = parser.parse_lenient(response)
        assert action.action_type == ActionType.COMPLETE, "Expected action.action_type to equal ActionType.COMPLETE"

    def test_lenient_fallback_to_thinking(self, parser):
        """Lenient mode falls back to thinking for ambiguous input."""
        response = """
<thinking>
Analyzing the problem. The code looks complex.
Maybe I should approach it differently.
</thinking>
"""
        action = parser.parse_lenient(response)
        assert action.action_type == ActionType.THINK, "Expected action.action_type to equal ActionType.THINK"
        assert "Analyzing the problem" in action.reasoning, "Expected 'Analyzing the problem' in action.reasoning"


class TestExtractElement:
    """Tests for element extraction helpers."""

    @pytest.fixture
    def parser(self):
        return ActionParser()

    def test_extract_summary(self, parser):
        """Extract summary element."""
        content = "<summary>This is the summary</summary>"
        result = parser._extract_element(content, "summary")
        assert result == "This is the summary", "Expected result to equal 'This is the summary'"

    def test_extract_question(self, parser):
        """Extract question element."""
        content = "<question>What should I do?</question>"
        result = parser._extract_element(content, "question")
        assert result == "What should I do?", "Expected result to equal 'What should I do?'"

    def test_extract_missing_element(self, parser):
        """Missing element returns None."""
        content = "<other>content</other>"
        result = parser._extract_element(content, "summary")
        assert result is None, "Expected result is None"

    def test_extract_element_with_whitespace(self, parser):
        """Whitespace is trimmed."""
        content = "<summary>  \n  Trimmed content  \n  </summary>"
        result = parser._extract_element(content, "summary")
        assert result == "Trimmed content", "Expected result to equal 'Trimmed content'"
