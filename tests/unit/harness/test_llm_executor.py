"""Tests for LLM Executor."""

from unittest.mock import Mock, patch

import pytest

from agentforge.core.harness.llm_executor import LLMExecutor, create_default_executor
from agentforge.core.harness.llm_executor_domain import (
    ActionType,
    ExecutionContext,
    ToolCall,
    ToolResult,
)


class TestLLMExecutorInit:
    """Tests for executor initialization."""

    def test_default_initialization(self):
        """Executor initializes with defaults."""
        with patch("agentforge.core.harness.llm_executor.get_provider") as mock_get:
            mock_provider = Mock()
            mock_get.return_value = mock_provider

            executor = LLMExecutor()

            assert executor.provider == mock_provider, "Expected executor.provider to equal mock_provider"
            assert executor.prompt_builder is not None, "Expected executor.prompt_builder is not None"
            assert executor.action_parser is not None, "Expected executor.action_parser is not None"
            assert executor.tool_executors == {}, "Expected executor.tool_executors to equal {}"

    def test_custom_components(self):
        """Executor accepts custom components."""
        mock_provider = Mock()
        mock_builder = Mock()
        mock_parser = Mock()
        tools = {"test": lambda n, p: ToolResult.success_result(n, "ok")}

        executor = LLMExecutor(
            provider=mock_provider,
            prompt_builder=mock_builder,
            action_parser=mock_parser,
            tool_executors=tools,
        )

        assert executor.provider == mock_provider, "Expected executor.provider to equal mock_provider"
        assert executor.prompt_builder == mock_builder, "Expected executor.prompt_builder to equal mock_builder"
        assert executor.action_parser == mock_parser, "Expected executor.action_parser to equal mock_parser"
        assert "test" in executor.tool_executors, "Expected 'test' in executor.tool_executors"


class TestToolRegistration:
    """Tests for tool registration."""

    def test_register_single_tool(self):
        """Register a single tool."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()
            executor.register_tool("my_tool", lambda n, p: ToolResult.success_result(n, "ok"))

            assert "my_tool" in executor.tool_executors, "Expected 'my_tool' in executor.tool_executors"

    def test_register_multiple_tools(self):
        """Register multiple tools at once."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()
            executor.register_tools({
                "tool1": lambda n, p: ToolResult.success_result(n, "1"),
                "tool2": lambda n, p: ToolResult.success_result(n, "2"),
            })

            assert "tool1" in executor.tool_executors, "Expected 'tool1' in executor.tool_executors"
            assert "tool2" in executor.tool_executors, "Expected 'tool2' in executor.tool_executors"


class TestExecuteStep:
    """Tests for single step execution."""

    @pytest.fixture
    def mock_provider(self):
        provider = Mock()
        provider.generate.return_value = """
<thinking>Need to read the file.</thinking>
<action type="tool_call">
<tool name="read_file">
<parameter name="path">/test.py</parameter>
</tool>
</action>
"""
        provider.count_tokens.return_value = 100
        return provider

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            session_id="session-001",
            task_description="Read a file",
            current_phase="execute",
            available_tools=["read_file"],
        )

    def test_execute_step_calls_llm(self, mock_provider, context):
        """Execute step calls the LLM provider."""
        executor = LLMExecutor(provider=mock_provider)
        executor.register_tool("read_file", lambda n, p: ToolResult.success_result(n, "content"))

        result = executor.execute_step(context)

        mock_provider.generate.assert_called_once()
        assert result.success is True, "Expected result.success is True"

    def test_execute_step_parses_action(self, mock_provider, context):
        """Execute step parses the LLM response into action."""
        executor = LLMExecutor(provider=mock_provider)
        executor.register_tool("read_file", lambda n, p: ToolResult.success_result(n, "content"))

        result = executor.execute_step(context)

        assert result.action is not None, "Expected result.action is not None"
        assert result.action.action_type == ActionType.TOOL_CALL, "Expected result.action.action_type to equal ActionType.TOOL_CALL"
        assert len(result.action.tool_calls) == 1, "Expected len(result.action.tool_calls) to equal 1"

    def test_execute_step_runs_tools(self, mock_provider, context):
        """Execute step runs tool calls."""
        executor = LLMExecutor(provider=mock_provider)

        tool_called = []
        def mock_tool(name, params):
            tool_called.append((name, params))
            return ToolResult.success_result(name, "file contents")

        executor.register_tool("read_file", mock_tool)

        result = executor.execute_step(context)

        assert len(tool_called) == 1, "Expected len(tool_called) to equal 1"
        assert tool_called[0][0] == "read_file", "Expected tool_called[0][0] to equal 'read_file'"
        assert tool_called[0][1] == {"path": "/test.py"}, "Expected tool_called[0][1] to equal {'path': '/test.py'}"
        assert len(result.tool_results) == 1, "Expected len(result.tool_results) to equal 1"
        assert result.tool_results[0].success is True, "Expected result.tool_results[0].success is True"

    def test_execute_step_updates_context(self, mock_provider, context):
        """Execute step updates execution context."""
        executor = LLMExecutor(provider=mock_provider)
        executor.register_tool("read_file", lambda n, p: ToolResult.success_result(n, "ok"))

        assert context.iteration == 0, "Expected context.iteration to equal 0"
        assert len(context.conversation_history) == 0, "Expected len(context.conversation_hi... to equal 0"

        executor.execute_step(context)

        assert context.iteration == 1, "Expected context.iteration to equal 1"
        assert context.tokens_used > 0, "Expected context.tokens_used > 0"
        # History should have assistant message + tool result
        assert len(context.conversation_history) == 2, "Expected len(context.conversation_hi... to equal 2"

    def test_execute_step_unknown_tool(self, context):
        """Execute step handles unknown tools gracefully."""
        provider = Mock()
        provider.generate.return_value = """
<thinking>Calling unknown tool.</thinking>
<action type="tool_call">
<tool name="unknown_tool">
</tool>
</action>
"""
        provider.count_tokens.return_value = 50

        executor = LLMExecutor(provider=provider)
        # Don't register any tools

        result = executor.execute_step(context)

        assert result.success is True, "Expected result.success is True"
        assert len(result.tool_results) == 1, "Expected len(result.tool_results) to equal 1"
        assert result.tool_results[0].success is False, "Expected result.tool_results[0].success is False"
        assert "Unknown tool" in result.tool_results[0].error, "Expected 'Unknown tool' in result.tool_results[0].error"

    def test_execute_step_complete_action(self, context):
        """Execute step handles completion action."""
        provider = Mock()
        provider.generate.return_value = """
<thinking>Task is done.</thinking>
<action type="complete">
<summary>Successfully completed the task.</summary>
</action>
"""
        provider.count_tokens.return_value = 50

        executor = LLMExecutor(provider=provider)

        result = executor.execute_step(context)

        assert result.success is True, "Expected result.success is True"
        assert result.action.action_type == ActionType.COMPLETE, "Expected result.action.action_type to equal ActionType.COMPLETE"
        assert result.should_continue is False, "Expected result.should_continue is False"


class TestToolExecution:
    """Tests for tool execution."""

    def test_tool_success(self):
        """Successful tool execution."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()
            executor.register_tool("test", lambda n, p: ToolResult.success_result(n, "done"))

            tool_call = ToolCall(name="test", parameters={})
            result = executor._execute_single_tool(tool_call)

            assert result.success is True, "Expected result.success is True"
            assert result.output == "done", "Expected result.output to equal 'done'"

    def test_tool_failure(self):
        """Failed tool execution."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()
            executor.register_tool("test", lambda n, p: ToolResult.failure_result(n, "failed"))

            tool_call = ToolCall(name="test", parameters={})
            result = executor._execute_single_tool(tool_call)

            assert result.success is False, "Expected result.success is False"
            assert result.error == "failed", "Expected result.error to equal 'failed'"

    def test_tool_exception_caught(self):
        """Tool exceptions are caught and converted to failures."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()

            def bad_tool(name, params):
                raise ValueError("Something broke")

            executor.register_tool("bad", bad_tool)

            tool_call = ToolCall(name="bad", parameters={})
            result = executor._execute_single_tool(tool_call)

            assert result.success is False, "Expected result.success is False"
            assert "Tool execution error" in result.error, "Expected 'Tool execution error' in result.error"
            assert "Something broke" in result.error, "Expected 'Something broke' in result.error"

    def test_tool_returns_non_result(self):
        """Tool returning non-ToolResult is wrapped."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()
            executor.register_tool("raw", lambda n, p: "raw output")

            tool_call = ToolCall(name="raw", parameters={})
            result = executor._execute_single_tool(tool_call)

            assert result.success is True, "Expected result.success is True"
            assert result.output == "raw output", "Expected result.output to equal 'raw output'"


class TestRunUntilComplete:
    """Tests for running until completion."""

    def test_runs_until_complete(self):
        """Executor runs until task completion."""
        responses = [
            """<thinking>Step 1</thinking>
<action type="tool_call">
<tool name="test"><parameter name="step">1</parameter></tool>
</action>""",
            """<thinking>Step 2</thinking>
<action type="complete">
<summary>Done</summary>
</action>""",
        ]

        provider = Mock()
        provider.generate.side_effect = responses
        provider.count_tokens.return_value = 50

        executor = LLMExecutor(provider=provider)
        executor.register_tool("test", lambda n, p: ToolResult.success_result(n, "ok"))

        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="execute",
            available_tools=["test"],
        )

        results = executor.run_until_complete(context, max_iterations=10)

        assert len(results) == 2, "Expected len(results) to equal 2"
        assert results[-1].action.action_type == ActionType.COMPLETE, "Expected results[-1].action.action_type to equal ActionType.COMPLETE"

    def test_respects_max_iterations(self):
        """Executor stops at max iterations."""
        provider = Mock()
        provider.generate.return_value = """
<thinking>Keep going</thinking>
<action type="tool_call">
<tool name="test"></tool>
</action>
"""
        provider.count_tokens.return_value = 50

        executor = LLMExecutor(provider=provider)
        executor.register_tool("test", lambda n, p: ToolResult.success_result(n, "ok"))

        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="execute",
            available_tools=["test"],
        )

        results = executor.run_until_complete(context, max_iterations=3)

        assert len(results) == 3, "Expected len(results) to equal 3"

    def test_stops_on_token_budget(self):
        """Executor stops when token budget exhausted."""
        provider = Mock()
        provider.generate.return_value = """
<thinking>Step</thinking>
<action type="tool_call">
<tool name="test"></tool>
</action>
"""
        provider.count_tokens.return_value = 50000  # Large token usage

        executor = LLMExecutor(provider=provider)
        executor.register_tool("test", lambda n, p: ToolResult.success_result(n, "ok"))

        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="execute",
            available_tools=["test"],
            token_budget=100000,  # Will be exhausted after 2 calls
        )

        results = executor.run_until_complete(context, max_iterations=10)

        # Should stop after tokens exhausted
        assert len(results) <= 3, "Expected len(results) <= 3"
        assert results[-1].error == "Token budget exhausted" or results[-1].should_continue is False, "Assertion failed"

    def test_calls_on_step_callback(self):
        """Callback is called after each step."""
        provider = Mock()
        provider.generate.return_value = """
<thinking>Done</thinking>
<action type="complete"><summary>Done</summary></action>
"""
        provider.count_tokens.return_value = 50

        executor = LLMExecutor(provider=provider)

        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="execute",
            available_tools=[],
        )

        callback_results = []
        executor.run_until_complete(
            context,
            max_iterations=5,
            on_step=lambda r: callback_results.append(r),
        )

        assert len(callback_results) == 1, "Expected len(callback_results) to equal 1"


class TestMessagesToPrompt:
    """Tests for message conversion."""

    def test_system_message_format(self):
        """System messages are formatted correctly."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()

            messages = [{"role": "system", "content": "You are helpful."}]
            result = executor._messages_to_prompt(messages)

            assert "<system>" in result, "Expected '<system>' in result"
            assert "You are helpful." in result, "Expected 'You are helpful.' in result"
            assert "</system>" in result, "Expected '</system>' in result"

    def test_user_message_format(self):
        """User messages are formatted correctly."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()

            messages = [{"role": "user", "content": "Hello"}]
            result = executor._messages_to_prompt(messages)

            assert "<user>" in result, "Expected '<user>' in result"
            assert "Hello" in result, "Expected 'Hello' in result"

    def test_assistant_message_format(self):
        """Assistant messages are formatted correctly."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = LLMExecutor()

            messages = [{"role": "assistant", "content": "Hi there"}]
            result = executor._messages_to_prompt(messages)

            assert "<assistant>" in result, "Expected '<assistant>' in result"
            assert "Hi there" in result, "Expected 'Hi there' in result"


class TestCreateDefaultExecutor:
    """Tests for factory function."""

    def test_creates_executor(self):
        """Factory creates configured executor."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = create_default_executor()
            assert isinstance(executor, LLMExecutor), "Expected isinstance() to be truthy"

    def test_accepts_tools(self):
        """Factory accepts tool executors."""
        tools = {"my_tool": lambda n, p: ToolResult.success_result(n, "ok")}

        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = create_default_executor(tool_executors=tools)
            assert "my_tool" in executor.tool_executors, "Expected 'my_tool' in executor.tool_executors"

    def test_accepts_model(self):
        """Factory accepts model parameter."""
        with patch("agentforge.core.harness.llm_executor.get_provider"):
            executor = create_default_executor(model="claude-opus-4-20250514")
            assert executor.model == "claude-opus-4-20250514", "Expected executor.model to equal 'claude-opus-4-20250514'"
