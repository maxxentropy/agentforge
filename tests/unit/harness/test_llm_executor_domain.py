"""Tests for LLM Executor Domain entities."""

from datetime import datetime

from agentforge.core.harness.llm_executor_domain import (
    ActionParseError,
    ActionType,
    AgentAction,
    ConversationMessage,
    ExecutionContext,
    LLMExecutorError,
    StepResult,
    TokenUsage,
    ToolCall,
    ToolCategory,
    ToolExecutionError,
    ToolResult,
)


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_types_exist(self):
        """All expected action types should exist."""
        assert ActionType.TOOL_CALL.value == "tool_call", "Expected ActionType.TOOL_CALL.value to equal 'tool_call'"
        assert ActionType.THINK.value == "think", "Expected ActionType.THINK.value to equal 'think'"
        assert ActionType.RESPOND.value == "respond", "Expected ActionType.RESPOND.value to equal 'respond'"
        assert ActionType.ASK_USER.value == "ask_user", "Expected ActionType.ASK_USER.value to equal 'ask_user'"
        assert ActionType.COMPLETE.value == "complete", "Expected ActionType.COMPLETE.value to equal 'complete'"
        assert ActionType.ESCALATE.value == "escalate", "Expected ActionType.ESCALATE.value to equal 'escalate'"


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_categories_exist(self):
        """All expected tool categories should exist."""
        assert ToolCategory.FILE.value == "file", "Expected ToolCategory.FILE.value to equal 'file'"
        assert ToolCategory.SEARCH.value == "search", "Expected ToolCategory.SEARCH.value to equal 'search'"
        assert ToolCategory.SHELL.value == "shell", "Expected ToolCategory.SHELL.value to equal 'shell'"
        assert ToolCategory.TEST.value == "test", "Expected ToolCategory.TEST.value to equal 'test'"
        assert ToolCategory.GIT.value == "git", "Expected ToolCategory.GIT.value to equal 'git'"
        assert ToolCategory.ANALYSIS.value == "analysis", "Expected ToolCategory.ANALYSIS.value to equal 'analysis'"
        assert ToolCategory.MEMORY.value == "memory", "Expected ToolCategory.MEMORY.value to equal 'memory'"


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_create_basic(self):
        """Create basic tool call."""
        tool = ToolCall(name="read_file", parameters={"path": "/test.py"})
        assert tool.name == "read_file", "Expected tool.name to equal 'read_file'"
        assert tool.parameters == {"path": "/test.py"}, "Expected tool.parameters to equal {'path': '/test.py'}"

    def test_category_inference_file(self):
        """File tools should infer FILE category."""
        tool = ToolCall(name="read_file", parameters={})
        assert tool.category == ToolCategory.FILE, "Expected tool.category to equal ToolCategory.FILE"

        tool = ToolCall(name="write_file", parameters={})
        assert tool.category == ToolCategory.FILE, "Expected tool.category to equal ToolCategory.FILE"

        tool = ToolCall(name="edit_file", parameters={})
        assert tool.category == ToolCategory.FILE, "Expected tool.category to equal ToolCategory.FILE"

    def test_category_inference_search(self):
        """Search tools should infer SEARCH category."""
        tool = ToolCall(name="grep", parameters={})
        assert tool.category == ToolCategory.SEARCH, "Expected tool.category to equal ToolCategory.SEARCH"

        tool = ToolCall(name="glob", parameters={})
        assert tool.category == ToolCategory.SEARCH, "Expected tool.category to equal ToolCategory.SEARCH"

    def test_category_inference_shell(self):
        """Shell tools should infer SHELL category."""
        tool = ToolCall(name="bash", parameters={})
        assert tool.category == ToolCategory.SHELL, "Expected tool.category to equal ToolCategory.SHELL"

    def test_category_inference_test(self):
        """Test tools should infer TEST category."""
        tool = ToolCall(name="run_tests", parameters={})
        assert tool.category == ToolCategory.TEST, "Expected tool.category to equal ToolCategory.TEST"

        tool = ToolCall(name="pytest", parameters={})
        assert tool.category == ToolCategory.TEST, "Expected tool.category to equal ToolCategory.TEST"

    def test_category_inference_git(self):
        """Git tools should infer GIT category."""
        tool = ToolCall(name="git_status", parameters={})
        assert tool.category == ToolCategory.GIT, "Expected tool.category to equal ToolCategory.GIT"

    def test_explicit_category_overrides(self):
        """Explicit category should override inference."""
        tool = ToolCall(name="read_file", parameters={}, category=ToolCategory.ANALYSIS)
        assert tool.category == ToolCategory.ANALYSIS, "Expected tool.category to equal ToolCategory.ANALYSIS"


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self):
        """Create successful result."""
        result = ToolResult.success_result("read_file", "file content", 0.5)
        assert result.success is True, "Expected result.success is True"
        assert result.tool_name == "read_file", "Expected result.tool_name to equal 'read_file'"
        assert result.output == "file content", "Expected result.output to equal 'file content'"
        assert result.error is None, "Expected result.error is None"
        assert result.duration_seconds == 0.5, "Expected result.duration_seconds to equal 0.5"

    def test_failure_result(self):
        """Create failed result."""
        result = ToolResult.failure_result("write_file", "Permission denied", 0.1)
        assert result.success is False, "Expected result.success is False"
        assert result.tool_name == "write_file", "Expected result.tool_name to equal 'write_file'"
        assert result.output is None, "Expected result.output is None"
        assert result.error == "Permission denied", "Expected result.error to equal 'Permission denied'"


class TestAgentAction:
    """Tests for AgentAction dataclass."""

    def test_tool_action(self):
        """Create tool call action."""
        tools = [ToolCall(name="read_file", parameters={"path": "/test.py"})]
        action = AgentAction.tool_action(tools, "Reading file first")

        assert action.action_type == ActionType.TOOL_CALL, "Expected action.action_type to equal ActionType.TOOL_CALL"
        assert len(action.tool_calls) == 1, "Expected len(action.tool_calls) to equal 1"
        assert action.reasoning == "Reading file first", "Expected action.reasoning to equal 'Reading file first'"

    def test_think_action(self):
        """Create thinking action."""
        action = AgentAction.think_action("Need to analyze the codebase")

        assert action.action_type == ActionType.THINK, "Expected action.action_type to equal ActionType.THINK"
        assert action.reasoning == "Need to analyze the codebase", "Expected action.reasoning to equal 'Need to analyze the codebase'"

    def test_respond_action(self):
        """Create response action."""
        action = AgentAction.respond_action("Here's my answer", "Thinking through")

        assert action.action_type == ActionType.RESPOND, "Expected action.action_type to equal ActionType.RESPOND"
        assert action.response == "Here's my answer", "Expected action.response to equal \"Here's my answer\""
        assert action.reasoning == "Thinking through", "Expected action.reasoning to equal 'Thinking through'"

    def test_complete_action(self):
        """Create completion action."""
        action = AgentAction.complete_action("Task done", "All tests pass")

        assert action.action_type == ActionType.COMPLETE, "Expected action.action_type to equal ActionType.COMPLETE"
        assert action.response == "Task done", "Expected action.response to equal 'Task done'"
        assert action.reasoning == "All tests pass", "Expected action.reasoning to equal 'All tests pass'"

    def test_escalate_action(self):
        """Create escalation action."""
        action = AgentAction.escalate_action("Need human guidance")

        assert action.action_type == ActionType.ESCALATE, "Expected action.action_type to equal ActionType.ESCALATE"
        assert action.reasoning == "Need human guidance", "Expected action.reasoning to equal 'Need human guidance'"


class TestConversationMessage:
    """Tests for ConversationMessage dataclass."""

    def test_user_message(self):
        """Create user message."""
        msg = ConversationMessage.user_message("Hello")
        assert msg.role == "user", "Expected msg.role to equal 'user'"
        assert msg.content == "Hello", "Expected msg.content to equal 'Hello'"
        assert isinstance(msg.timestamp, datetime), "Expected isinstance() to be truthy"

    def test_assistant_message(self):
        """Create assistant message."""
        tools = [ToolCall(name="grep", parameters={"pattern": "test"})]
        msg = ConversationMessage.assistant_message("Searching...", tools)

        assert msg.role == "assistant", "Expected msg.role to equal 'assistant'"
        assert msg.content == "Searching...", "Expected msg.content to equal 'Searching...'"
        assert msg.tool_calls == tools, "Expected msg.tool_calls to equal tools"

    def test_tool_result_message(self):
        """Create tool result message."""
        results = [
            ToolResult.success_result("read_file", "content"),
            ToolResult.failure_result("write_file", "error"),
        ]
        msg = ConversationMessage.tool_result_message(results)

        assert msg.role == "tool_result", "Expected msg.role to equal 'tool_result'"
        assert "[read_file]: Success" in msg.content, "Expected '[read_file]: Success' in msg.content"
        assert "[write_file]: Error" in msg.content, "Expected '[write_file]: Error' in msg.content"
        assert msg.tool_results == results, "Expected msg.tool_results to equal results"


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""

    def test_create_context(self):
        """Create execution context."""
        context = ExecutionContext(
            session_id="sess-001",
            task_description="Fix the bug",
            current_phase="execute",
            available_tools=["read_file", "write_file"],
        )

        assert context.session_id == "sess-001", "Expected context.session_id to equal 'sess-001'"
        assert context.task_description == "Fix the bug", "Expected context.task_description to equal 'Fix the bug'"
        assert context.iteration == 0, "Expected context.iteration to equal 0"
        assert context.tokens_used == 0, "Expected context.tokens_used to equal 0"
        assert context.token_budget == 100000, "Expected context.token_budget to equal 100000"

    def test_tokens_remaining(self):
        """Calculate remaining tokens."""
        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="p1",
            available_tools=[],
            tokens_used=25000,
            token_budget=100000,
        )
        assert context.tokens_remaining == 75000, "Expected context.tokens_remaining to equal 75000"

    def test_recent_messages(self):
        """Get recent messages (last 10)."""
        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="p1",
            available_tools=[],
        )

        # Add 15 messages
        for i in range(15):
            context.add_user_message(f"Message {i}")

        recent = context.recent_messages
        assert len(recent) == 10, "Expected len(recent) to equal 10"
        assert recent[0].content == "Message 5", "Expected recent[0].content to equal 'Message 5'"# First of last 10
        assert recent[-1].content == "Message 14", "Expected recent[-1].content to equal 'Message 14'"# Last

    def test_add_messages(self):
        """Add different message types."""
        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="p1",
            available_tools=[],
        )

        context.add_user_message("User says hi")
        context.add_assistant_message("Assistant responds")
        context.add_tool_results([ToolResult.success_result("test", "ok")])

        assert len(context.conversation_history) == 3, "Expected len(context.conversation_hi... to equal 3"
        assert context.conversation_history[0].role == "user", "Expected context.conversation_histor... to equal 'user'"
        assert context.conversation_history[1].role == "assistant", "Expected context.conversation_histor... to equal 'assistant'"
        assert context.conversation_history[2].role == "tool_result", "Expected context.conversation_histor... to equal 'tool_result'"


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_success_step_with_tool_call(self):
        """Successful step with tool call continues."""
        action = AgentAction.tool_action([ToolCall(name="test", parameters={})], "")
        result = StepResult.success_step(action, [], 100, 0.5)

        assert result.success is True, "Expected result.success is True"
        assert result.should_continue is True, "Expected result.should_continue is True"# Tool calls continue

    def test_success_step_with_complete(self):
        """Successful step with complete action stops."""
        action = AgentAction.complete_action("Done", "")
        result = StepResult.success_step(action, [], 100, 0.5)

        assert result.success is True, "Expected result.success is True"
        assert result.should_continue is False, "Expected result.should_continue is False"# Complete stops

    def test_success_step_with_escalate(self):
        """Escalation stops execution."""
        action = AgentAction.escalate_action("Help needed")
        result = StepResult.success_step(action, [], 100, 0.5)

        assert result.success is True, "Expected result.success is True"
        assert result.should_continue is False, "Expected result.should_continue is False"

    def test_failure_step(self):
        """Failed step stops execution."""
        result = StepResult.failure_step("Something broke", 0.1)

        assert result.success is False, "Expected result.success is False"
        assert result.error == "Something broke", "Expected result.error to equal 'Something broke'"
        assert result.should_continue is False, "Expected result.should_continue is False"


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_total_tokens(self):
        """Calculate total tokens."""
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        assert usage.total_tokens == 1500, "Expected usage.total_tokens to equal 1500"


class TestExceptions:
    """Tests for custom exceptions."""

    def test_llm_executor_error(self):
        """Base error with details."""
        error = LLMExecutorError("Test error", {"key": "value"})
        assert str(error) == "Test error", "Expected str(error) to equal 'Test error'"
        assert error.details == {"key": "value"}, "Expected error.details to equal {'key': 'value'}"

    def test_action_parse_error(self):
        """Parse error with raw response."""
        error = ActionParseError("Invalid XML", "<bad>xml")
        assert "Invalid XML" in str(error), "Expected 'Invalid XML' in str(error)"
        assert error.raw_response == "<bad>xml", "Expected error.raw_response to equal '<bad>xml'"

    def test_tool_execution_error(self):
        """Tool error with details."""
        original = ValueError("Bad value")
        error = ToolExecutionError("Tool failed", "read_file", original)
        assert error.tool_name == "read_file", "Expected error.tool_name to equal 'read_file'"
        assert error.original_error == original, "Expected error.original_error to equal original"
