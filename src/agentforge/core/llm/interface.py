# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
# @component_id: llm-interface
# @test_path: tests/unit/llm/test_interface.py

"""
LLM Client Interface
====================

Abstract interface for LLM clients supporting:
- Native tool calls (Anthropic tools parameter)
- Extended thinking (thinking parameter)
- Usage statistics tracking
- Multiple implementations (real, simulated, record, playback)

This enables cost-free development via simulation while maintaining
full API compatibility for production.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StopReason(str, Enum):
    """Reason why the LLM stopped generating."""
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"


@dataclass
class ToolCall:
    """
    A tool call requested by the LLM.

    Attributes:
        id: Unique identifier for this tool call
        name: Name of the tool to invoke
        input: Parameters for the tool
    """
    id: str
    name: str
    input: Dict[str, Any]

    def __repr__(self) -> str:
        return f"ToolCall(id={self.id!r}, name={self.name!r}, input={self.input!r})"


@dataclass
class ToolResult:
    """
    Result of executing a tool call.

    Attributes:
        tool_use_id: ID of the tool call this is responding to
        content: Result content (string or structured)
        is_error: Whether the tool execution failed
    """
    tool_use_id: str
    content: Any
    is_error: bool = False

    def to_message_content(self) -> Dict[str, Any]:
        """Convert to Anthropic API tool_result format."""
        return {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "content": str(self.content) if not isinstance(self.content, str) else self.content,
            "is_error": self.is_error,
        }


@dataclass
class LLMResponse:
    """
    Standardized response from any LLM client.

    Attributes:
        content: Text content of the response
        tool_calls: List of tool calls requested
        thinking: Extended thinking content (if enabled)
        stop_reason: Why generation stopped
        usage: Token usage statistics
    """
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    thinking: Optional[str] = None
    stop_reason: StopReason = StopReason.END_TURN
    usage: Dict[str, int] = field(default_factory=lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
    })

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0

    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.usage.get("input_tokens", 0) + self.usage.get("output_tokens", 0)

    def get_first_tool_call(self) -> Optional[ToolCall]:
        """Get the first tool call, if any."""
        return self.tool_calls[0] if self.tool_calls else None


@dataclass
class ToolDefinition:
    """
    Definition of a tool for the LLM.

    Attributes:
        name: Tool name (e.g., "read_file")
        description: What the tool does
        input_schema: JSON Schema for tool parameters
    """
    name: str
    description: str
    input_schema: Dict[str, Any]

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ThinkingConfig:
    """
    Configuration for extended thinking.

    When enabled, the LLM will use chain-of-thought reasoning
    before responding, improving quality for complex tasks.

    Attributes:
        enabled: Whether to enable extended thinking
        budget_tokens: Maximum tokens for thinking (1000-50000)
    """
    enabled: bool = False
    budget_tokens: int = 8000

    def to_api_format(self) -> Optional[Dict[str, Any]]:
        """Convert to Anthropic API thinking format."""
        if not self.enabled:
            return None
        return {
            "type": "enabled",
            "budget_tokens": self.budget_tokens,
        }


class LLMClient(ABC):
    """
    Abstract interface for LLM clients.

    Implementations:
    - AnthropicLLMClient: Real Anthropic API
    - SimulatedLLMClient: Mock responses for testing

    Example:
        ```python
        client = LLMClientFactory.create()  # Uses env vars

        response = client.complete(
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": "Hello"}],
            tools=[read_file_tool],
            thinking=ThinkingConfig(enabled=True),
        )

        if response.has_tool_calls:
            tool_call = response.get_first_tool_call()
            # Execute tool...
        ```
    """

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        thinking: Optional[ThinkingConfig] = None,
        tool_choice: str = "auto",
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Make a completion request to the LLM.

        Args:
            system: System prompt
            messages: Conversation messages
            tools: Available tools for the LLM
            thinking: Extended thinking configuration
            tool_choice: Tool selection mode ("auto", "any", "none")
            max_tokens: Maximum response tokens

        Returns:
            LLMResponse with content, tool calls, and usage
        """
        pass

    @abstractmethod
    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get cumulative usage statistics.

        Returns:
            Dict with keys: total_input_tokens, total_output_tokens,
            cached_tokens, call_count
        """
        pass

    @abstractmethod
    def reset_usage_stats(self) -> None:
        """Reset cumulative usage statistics to zero."""
        pass

    def complete_with_tools(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[ToolDefinition],
        tool_executor: "ToolExecutor",
        thinking: Optional[ThinkingConfig] = None,
        max_iterations: int = 10,
    ) -> LLMResponse:
        """
        Complete with automatic tool execution loop.

        Continues calling tools until the LLM stops requesting them
        or max_iterations is reached.

        Args:
            system: System prompt
            messages: Initial conversation messages
            tools: Available tools
            tool_executor: Executor for tool calls
            thinking: Extended thinking configuration
            max_iterations: Maximum tool call iterations

        Returns:
            Final LLMResponse after tool loop completes
        """
        current_messages = list(messages)

        for _ in range(max_iterations):
            response = self.complete(
                system=system,
                messages=current_messages,
                tools=tools,
                thinking=thinking,
            )

            if not response.has_tool_calls:
                return response

            # Add assistant response with tool calls
            assistant_content = []
            if response.content:
                assistant_content.append({"type": "text", "text": response.content})
            for tc in response.tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.input,
                })
            current_messages.append({"role": "assistant", "content": assistant_content})

            # Execute tools and add results
            tool_results = []
            for tc in response.tool_calls:
                result = tool_executor.execute(tc)
                tool_results.append(result.to_message_content())
            current_messages.append({"role": "user", "content": tool_results})

        return response


class ToolExecutor(ABC):
    """
    Abstract interface for executing tool calls.

    Implementations handle the actual tool execution logic.
    """

    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: The tool call to execute

        Returns:
            ToolResult with execution outcome
        """
        pass
