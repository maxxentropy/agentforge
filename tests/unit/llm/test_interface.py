# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
# @component_id: llm-interface-tests

"""
Tests for LLM interface data classes and abstractions.
"""

import pytest

from agentforge.core.llm.interface import (
    LLMResponse,
    StopReason,
    ThinkingConfig,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_basic_creation(self):
        """ToolCall should store id, name, and input."""
        tc = ToolCall(
            id="call_123",
            name="read_file",
            input={"path": "/src/main.py"},
        )

        assert tc.id == "call_123"
        assert tc.name == "read_file"
        assert tc.input == {"path": "/src/main.py"}

    def test_repr(self):
        """ToolCall should have informative repr."""
        tc = ToolCall(id="x", name="test", input={})
        repr_str = repr(tc)

        assert "ToolCall" in repr_str
        assert "test" in repr_str


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self):
        """ToolResult should capture successful execution."""
        result = ToolResult(
            tool_use_id="call_123",
            content="File contents here",
            is_error=False,
        )

        assert result.tool_use_id == "call_123"
        assert result.content == "File contents here"
        assert result.is_error is False

    def test_error_result(self):
        """ToolResult should capture error state."""
        result = ToolResult(
            tool_use_id="call_456",
            content="File not found",
            is_error=True,
        )

        assert result.is_error is True

    def test_to_message_content(self):
        """to_message_content should produce Anthropic API format."""
        result = ToolResult(
            tool_use_id="call_789",
            content="Success",
            is_error=False,
        )

        msg = result.to_message_content()

        assert msg["type"] == "tool_result"
        assert msg["tool_use_id"] == "call_789"
        assert msg["content"] == "Success"
        assert msg["is_error"] is False


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_basic_response(self):
        """LLMResponse should store content and metadata."""
        response = LLMResponse(
            content="Hello, world!",
            tool_calls=[],
            stop_reason=StopReason.END_TURN,
        )

        assert response.content == "Hello, world!"
        assert response.tool_calls == []
        assert response.stop_reason == StopReason.END_TURN

    def test_has_tool_calls_true(self):
        """has_tool_calls should return True when tools present."""
        response = LLMResponse(
            content="",
            tool_calls=[
                ToolCall(id="1", name="test", input={}),
            ],
        )

        assert response.has_tool_calls is True

    def test_has_tool_calls_false(self):
        """has_tool_calls should return False when no tools."""
        response = LLMResponse(content="Done", tool_calls=[])

        assert response.has_tool_calls is False

    def test_get_first_tool_call(self):
        """get_first_tool_call should return first tool or None."""
        tc1 = ToolCall(id="1", name="first", input={})
        tc2 = ToolCall(id="2", name="second", input={})

        with_tools = LLMResponse(content="", tool_calls=[tc1, tc2])
        without_tools = LLMResponse(content="", tool_calls=[])

        assert with_tools.get_first_tool_call() == tc1
        assert without_tools.get_first_tool_call() is None

    def test_total_tokens(self):
        """total_tokens should sum input and output tokens."""
        response = LLMResponse(
            content="Test",
            usage={
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_read_tokens": 20,
            },
        )

        assert response.total_tokens == 150

    def test_thinking_storage(self):
        """LLMResponse should store thinking content."""
        response = LLMResponse(
            content="Result",
            thinking="Let me think about this...",
        )

        assert response.thinking == "Let me think about this..."


class TestToolDefinition:
    """Tests for ToolDefinition dataclass."""

    def test_basic_definition(self):
        """ToolDefinition should store name, description, schema."""
        tool = ToolDefinition(
            name="read_file",
            description="Read contents of a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        )

        assert tool.name == "read_file"
        assert tool.description == "Read contents of a file"
        assert "path" in tool.input_schema["properties"]

    def test_to_api_format(self):
        """to_api_format should produce Anthropic API format."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
        )

        api_format = tool.to_api_format()

        assert api_format["name"] == "test_tool"
        assert api_format["description"] == "A test tool"
        assert api_format["input_schema"] == {"type": "object"}


class TestThinkingConfig:
    """Tests for ThinkingConfig dataclass."""

    def test_defaults(self):
        """ThinkingConfig should have sensible defaults."""
        config = ThinkingConfig()

        assert config.enabled is False
        assert config.budget_tokens == 8000

    def test_enabled_config(self):
        """ThinkingConfig should store enabled state and budget."""
        config = ThinkingConfig(enabled=True, budget_tokens=10000)

        assert config.enabled is True
        assert config.budget_tokens == 10000

    def test_to_api_format_disabled(self):
        """to_api_format should return None when disabled."""
        config = ThinkingConfig(enabled=False)

        assert config.to_api_format() is None

    def test_to_api_format_enabled(self):
        """to_api_format should produce API format when enabled."""
        config = ThinkingConfig(enabled=True, budget_tokens=12000)

        api_format = config.to_api_format()

        assert api_format["type"] == "enabled"
        assert api_format["budget_tokens"] == 12000


class TestStopReason:
    """Tests for StopReason enum."""

    def test_enum_values(self):
        """StopReason should have expected values."""
        assert StopReason.END_TURN.value == "end_turn"
        assert StopReason.TOOL_USE.value == "tool_use"
        assert StopReason.MAX_TOKENS.value == "max_tokens"
        assert StopReason.STOP_SEQUENCE.value == "stop_sequence"

    def test_string_subclass(self):
        """StopReason should be usable as string comparison."""
        reason = StopReason.TOOL_USE

        # Can compare directly to string
        assert reason == "tool_use"
        # Value is accessible
        assert reason.value == "tool_use"
