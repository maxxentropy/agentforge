# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: tools-harness-agent_prompt_builder
# @impl_path: tools/harness/agent_prompt_builder.py

"""Tests for Agent Prompt Builder."""

import pytest

from agentforge.core.harness.agent_prompt_builder import AgentPromptBuilder
from agentforge.core.harness.llm_executor_domain import (
    ConversationMessage,
    ExecutionContext,
    ToolResult,
)


class TestAgentPromptBuilder:
    """Tests for prompt building."""

    @pytest.fixture
    def builder(self):
        return AgentPromptBuilder()

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            session_id="session-001",
            task_description="Fix the bug in user authentication",
            current_phase="execute",
            available_tools=["read_file", "write_file", "grep", "bash"],
            tokens_used=5000,
            token_budget=100000,
        )

    def test_build_system_prompt_includes_base_prompt(self, builder, context):
        """System prompt includes base instructions."""
        result = builder.build_system_prompt(context)
        assert "autonomous software engineering agent" in result, "Expected 'autonomous software engine... in result"
        assert "tool_call" in result, "Expected 'tool_call' in result"
        assert "complete" in result, "Expected 'complete' in result"
        assert "ask_user" in result, "Expected 'ask_user' in result"

    def test_build_system_prompt_includes_tools(self, builder, context):
        """System prompt includes available tools."""
        result = builder.build_system_prompt(context)
        assert "Available Tools" in result, "Expected 'Available Tools' in result"
        assert "read_file" in result, "Expected 'read_file' in result"
        assert "write_file" in result, "Expected 'write_file' in result"
        assert "grep" in result, "Expected 'grep' in result"
        assert "bash" in result, "Expected 'bash' in result"

    def test_build_user_prompt_includes_task(self, builder, context):
        """User prompt includes task description."""
        result = builder.build_user_prompt(context)
        assert "<task>" in result, "Expected '<task>' in result"
        assert "Fix the bug in user authentication" in result, "Expected 'Fix the bug in user authen... in result"
        assert "<phase>execute</phase>" in result, "Expected '<phase>execute</phase>' in result"

    def test_build_user_prompt_includes_status(self, builder, context):
        """User prompt includes current status."""
        result = builder.build_user_prompt(context)
        assert "<status>" in result, "Expected '<status>' in result"
        assert "<tokens_used>5000</tokens_used>" in result, "Expected '<tokens_used>5000</tokens_... in result"
        assert "<tokens_remaining>95000</tokens_remaining>" in result, "Expected '<tokens_remaining>95000</t... in result"

    def test_build_user_prompt_includes_memory_context(self, builder, context):
        """User prompt includes memory context if present."""
        context.memory_context = {
            "key_findings": ["Bug is in auth.py"],
            "approach": "Fix the token validation",
        }
        result = builder.build_user_prompt(context)
        assert "<memory_context>" in result, "Expected '<memory_context>' in result"
        assert "key_findings" in result, "Expected 'key_findings' in result"
        assert "Bug is in auth.py" in result, "Expected 'Bug is in auth.py' in result"

    def test_build_messages_basic(self, builder, context):
        """Build messages returns correct structure."""
        messages = builder.build_messages(context)

        assert len(messages) >= 2, "Expected len(messages) >= 2"# System + user
        assert messages[0]["role"] == "system", "Expected messages[0]['role'] to equal 'system'"
        assert messages[-1]["role"] == "user", "Expected messages[-1]['role'] to equal 'user'"

    def test_build_messages_includes_conversation_history(self, builder, context):
        """Build messages includes conversation history."""
        context.add_user_message("What files exist?")
        context.add_assistant_message("Let me search for files.")
        context.add_tool_results([ToolResult.success_result("glob", "file1.py\nfile2.py")])

        messages = builder.build_messages(context)

        # Should have system + 3 history messages
        assert len(messages) == 4, "Expected len(messages) to equal 4"
        assert messages[1]["content"] == "What files exist?", "Expected messages[1]['content'] to equal 'What files exist?'"
        assert messages[2]["content"] == "Let me search for files.", "Expected messages[2]['content'] to equal 'Let me search for files.'"
        assert "Tool Results" in messages[3]["content"], "Expected 'Tool Results' in messages[3]['content']"

    def test_build_messages_first_message_has_task(self, builder, context):
        """First message (no history) includes full task prompt."""
        messages = builder.build_messages(context)

        # System + user with task
        assert len(messages) == 2, "Expected len(messages) to equal 2"
        user_content = messages[1]["content"]
        assert "<task>" in user_content, "Expected '<task>' in user_content"
        assert "Fix the bug" in user_content, "Expected 'Fix the bug' in user_content"


class TestToolsSection:
    """Tests for tools section building."""

    @pytest.fixture
    def builder(self):
        return AgentPromptBuilder()

    def test_no_tools_available(self, builder):
        """Empty tools list shows no tools message."""
        result = builder._build_tools_section([])
        assert "No tools available" in result, "Expected 'No tools available' in result"

    def test_tools_listed(self, builder):
        """Tools are listed in markdown format."""
        result = builder._build_tools_section(["read_file", "write_file"])
        assert "- read_file" in result, "Expected '- read_file' in result"
        assert "- write_file" in result, "Expected '- write_file' in result"

    def test_tool_descriptions_included(self, builder):
        """Tool descriptions are included."""
        result = builder._build_tools_section(["read_file"])
        assert "Tool Descriptions" in result, "Expected 'Tool Descriptions' in result"
        assert "read_file" in result, "Expected 'read_file' in result"
        assert "Read contents of a file" in result, "Expected 'Read contents of a file' in result"


class TestHistorySection:
    """Tests for conversation history section."""

    @pytest.fixture
    def builder(self):
        return AgentPromptBuilder()

    def test_empty_history(self, builder):
        """Empty history returns empty string."""
        result = builder._build_history_section([])
        assert result == "", "Expected result to equal ''"

    def test_user_message_formatted(self, builder):
        """User messages are formatted correctly."""
        messages = [ConversationMessage.user_message("Hello")]
        result = builder._build_history_section(messages)
        assert "<user_message>" in result, "Expected '<user_message>' in result"
        assert "Hello" in result, "Expected 'Hello' in result"
        assert "</user_message>" in result, "Expected '</user_message>' in result"

    def test_assistant_message_formatted(self, builder):
        """Assistant messages are formatted correctly."""
        messages = [ConversationMessage.assistant_message("Hi there")]
        result = builder._build_history_section(messages)
        assert "<assistant_message>" in result, "Expected '<assistant_message>' in result"
        assert "Hi there" in result, "Expected 'Hi there' in result"

    def test_tool_result_formatted(self, builder):
        """Tool results are formatted correctly."""
        results = [ToolResult.success_result("read_file", "content")]
        messages = [ConversationMessage.tool_result_message(results)]
        result = builder._build_history_section(messages)
        assert "<tool_results>" in result, "Expected '<tool_results>' in result"
        assert "read_file" in result, "Expected 'read_file' in result"


class TestFormatToolResults:
    """Tests for tool result formatting."""

    @pytest.fixture
    def builder(self):
        return AgentPromptBuilder()

    def test_format_success_result(self, builder):
        """Success results formatted correctly."""
        results = [ToolResult.success_result("grep", "Match found: line 42")]
        formatted = builder.format_tool_results(results)
        assert "[grep] SUCCESS" in formatted, "Expected '[grep] SUCCESS' in formatted"
        assert "Match found: line 42" in formatted, "Expected 'Match found: line 42' in formatted"

    def test_format_failure_result(self, builder):
        """Failure results formatted correctly."""
        results = [ToolResult.failure_result("bash", "Command not found")]
        formatted = builder.format_tool_results(results)
        assert "[bash] ERROR" in formatted, "Expected '[bash] ERROR' in formatted"
        assert "Command not found" in formatted, "Expected 'Command not found' in formatted"

    def test_format_multiple_results(self, builder):
        """Multiple results separated correctly."""
        results = [
            ToolResult.success_result("read_file", "content1"),
            ToolResult.failure_result("write_file", "permission denied"),
        ]
        formatted = builder.format_tool_results(results)
        assert "[read_file] SUCCESS" in formatted, "Expected '[read_file] SUCCESS' in formatted"
        assert "[write_file] ERROR" in formatted, "Expected '[write_file] ERROR' in formatted"
        assert "content1" in formatted, "Expected 'content1' in formatted"
        assert "permission denied" in formatted, "Expected 'permission denied' in formatted"


class TestCustomSystemPrompt:
    """Tests for custom system prompt."""

    def test_custom_prompt_used(self):
        """Custom system prompt replaces default."""
        custom = "You are a test assistant."
        builder = AgentPromptBuilder(system_prompt=custom)

        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="p1",
            available_tools=[],
        )

        result = builder.build_system_prompt(context)
        assert "You are a test assistant" in result, "Expected 'You are a test assistant' in result"
        assert "autonomous software engineering agent" not in result, "Expected 'autonomous software engine... not in result"

    def test_default_prompt_when_none(self):
        """Default prompt used when None provided."""
        builder = AgentPromptBuilder(system_prompt=None)

        context = ExecutionContext(
            session_id="s1",
            task_description="task",
            current_phase="p1",
            available_tools=[],
        )

        result = builder.build_system_prompt(context)
        assert "autonomous software engineering agent" in result, "Expected 'autonomous software engine... in result"
