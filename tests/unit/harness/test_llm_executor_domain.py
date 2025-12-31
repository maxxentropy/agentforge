"""Tests for LLM Executor Domain entities."""

import pytest
from datetime import datetime

from tools.harness.llm_executor_domain import (
    ActionType,
    ToolCategory,
    ToolCall,
    ToolResult,
    AgentAction,
    ConversationMessage,
    ExecutionContext,
    StepResult,
    TokenUsage,
    LLMExecutorError,
    ActionParseError,
    ToolExecutionError,
)


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_types_exist(self):
        """All expected action types should exist."""
        assert ActionType.TOOL_CALL.value == "tool_call"
        assert ActionType.THINK.value == "think"
        assert ActionType.RESPOND.value == "respond"
        assert ActionType.ASK_USER.value == "ask_user"
        assert ActionType.COMPLETE.value == "complete"
        assert ActionType.ESCALATE.value == "escalate"


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_categories_exist(self):
        """All expected tool categories should exist."""
        assert ToolCategory.FILE.value == "file"
        assert ToolCategory.SEARCH.value == "search"
        assert ToolCategory.SHELL.value == "shell"
        assert ToolCategory.TEST.value == "test"
        assert ToolCategory.GIT.value == "git"
        assert ToolCategory.ANALYSIS.value == "analysis"
        assert ToolCategory.MEMORY.value == "memory"


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_create_basic(self):
        """Create basic tool call."""
        tool = ToolCall(name="read_file", parameters={"path": "/test.py"})
        assert tool.name == "read_file"
        assert tool.parameters == {"path": "/test.py"}

    def test_category_inference_file(self):
        """File tools should infer FILE category."""
        tool = ToolCall(name="read_file", parameters={})
        assert tool.category == ToolCategory.FILE

        tool = ToolCall(name="write_file", parameters={})
        assert tool.category == ToolCategory.FILE

        tool = ToolCall(name="edit_file", parameters={})
        assert tool.category == ToolCategory.FILE

    def test_category_inference_search(self):
        """Search tools should infer SEARCH category."""
        tool = ToolCall(name="grep", parameters={})
        assert tool.category == ToolCategory.SEARCH

        tool = ToolCall(name="glob", parameters={})
        assert tool.category == ToolCategory.SEARCH

    def test_category_inference_shell(self):
        """Shell tools should infer SHELL category."""
        tool = ToolCall(name="bash", parameters={})
        assert tool.category == ToolCategory.SHELL

    def test_category_inference_test(self):
        """Test tools should infer TEST category."""
        tool = ToolCall(name="run_tests", parameters={})
        assert tool.category == ToolCategory.TEST

        tool = ToolCall(name="pytest", parameters={})
        assert tool.category == ToolCategory.TEST

    def test_category_inference_git(self):
        """Git tools should infer GIT category."""
        tool = ToolCall(name="git_status", parameters={})
        assert tool.category == ToolCategory.GIT

    def test_explicit_category_overrides(self):
        """Explicit category should override inference."""
        tool = ToolCall(name="read_file", parameters={}, category=ToolCategory.ANALYSIS)
        assert tool.category == ToolCategory.ANALYSIS


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self):
        """Create successful result."""
        result = ToolResult.success_result("read_file", "file content", 0.5)
        assert result.success is True
        assert result.tool_name == "read_file"
        assert result.output == "file content"
        assert result.error is None
        assert result.duration_seconds == 0.5

    def test_failure_result(self):
        """Create failed result."""
        result = ToolResult.failure_result("write_file", "Permission denied", 0.1)
        assert result.success is False
        assert result.tool_name == "write_file"
        assert result.output is None
        assert result.error == "Permission denied"


class TestAgentAction:
    """Tests for AgentAction dataclass."""

    def test_tool_action(self):
        """Create tool call action."""
        tools = [ToolCall(name="read_file", parameters={"path": "/test.py"})]
        action = AgentAction.tool_action(tools, "Reading file first")

        assert action.action_type == ActionType.TOOL_CALL
        assert len(action.tool_calls) == 1
        assert action.reasoning == "Reading file first"

    def test_think_action(self):
        """Create thinking action."""
        action = AgentAction.think_action("Need to analyze the codebase")

        assert action.action_type == ActionType.THINK
        assert action.reasoning == "Need to analyze the codebase"

    def test_respond_action(self):
        """Create response action."""
        action = AgentAction.respond_action("Here's my answer", "Thinking through")

        assert action.action_type == ActionType.RESPOND
        assert action.response == "Here's my answer"
        assert action.reasoning == "Thinking through"

    def test_complete_action(self):
        """Create completion action."""
        action = AgentAction.complete_action("Task done", "All tests pass")

        assert action.action_type == ActionType.COMPLETE
        assert action.response == "Task done"
        assert action.reasoning == "All tests pass"

    def test_escalate_action(self):
        """Create escalation action."""
        action = AgentAction.escalate_action("Need human guidance")

        assert action.action_type == ActionType.ESCALATE
        assert action.reasoning == "Need human guidance"


class TestConversationMessage:
    """Tests for ConversationMessage dataclass."""

    def test_user_message(self):
        """Create user message."""
        msg = ConversationMessage.user_message("Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)

    def test_assistant_message(self):
        """Create assistant message."""
        tools = [ToolCall(name="grep", parameters={"pattern": "test"})]
        msg = ConversationMessage.assistant_message("Searching...", tools)

        assert msg.role == "assistant"
        assert msg.content == "Searching..."
        assert msg.tool_calls == tools

    def test_tool_result_message(self):
        """Create tool result message."""
        results = [
            ToolResult.success_result("read_file", "content"),
            ToolResult.failure_result("write_file", "error"),
        ]
        msg = ConversationMessage.tool_result_message(results)

        assert msg.role == "tool_result"
        assert "[read_file]: Success" in msg.content
        assert "[write_file]: Error" in msg.content
        assert msg.tool_results == results


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

        assert context.session_id == "sess-001"
        assert context.task_description == "Fix the bug"
        assert context.iteration == 0
        assert context.tokens_used == 0
        assert context.token_budget == 100000

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
        assert context.tokens_remaining == 75000

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
        assert len(recent) == 10
        assert recent[0].content == "Message 5"  # First of last 10
        assert recent[-1].content == "Message 14"  # Last

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

        assert len(context.conversation_history) == 3
        assert context.conversation_history[0].role == "user"
        assert context.conversation_history[1].role == "assistant"
        assert context.conversation_history[2].role == "tool_result"


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_success_step_with_tool_call(self):
        """Successful step with tool call continues."""
        action = AgentAction.tool_action([ToolCall(name="test", parameters={})], "")
        result = StepResult.success_step(action, [], 100, 0.5)

        assert result.success is True
        assert result.should_continue is True  # Tool calls continue

    def test_success_step_with_complete(self):
        """Successful step with complete action stops."""
        action = AgentAction.complete_action("Done", "")
        result = StepResult.success_step(action, [], 100, 0.5)

        assert result.success is True
        assert result.should_continue is False  # Complete stops

    def test_success_step_with_escalate(self):
        """Escalation stops execution."""
        action = AgentAction.escalate_action("Help needed")
        result = StepResult.success_step(action, [], 100, 0.5)

        assert result.success is True
        assert result.should_continue is False

    def test_failure_step(self):
        """Failed step stops execution."""
        result = StepResult.failure_step("Something broke", 0.1)

        assert result.success is False
        assert result.error == "Something broke"
        assert result.should_continue is False


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_total_tokens(self):
        """Calculate total tokens."""
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        assert usage.total_tokens == 1500


class TestExceptions:
    """Tests for custom exceptions."""

    def test_llm_executor_error(self):
        """Base error with details."""
        error = LLMExecutorError("Test error", {"key": "value"})
        assert str(error) == "Test error"
        assert error.details == {"key": "value"}

    def test_action_parse_error(self):
        """Parse error with raw response."""
        error = ActionParseError("Invalid XML", "<bad>xml")
        assert "Invalid XML" in str(error)
        assert error.raw_response == "<bad>xml"

    def test_tool_execution_error(self):
        """Tool error with details."""
        original = ValueError("Bad value")
        error = ToolExecutionError("Tool failed", "read_file", original)
        assert error.tool_name == "read_file"
        assert error.original_error == original
