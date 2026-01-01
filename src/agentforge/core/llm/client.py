# @spec_file: specs/minimal-context-architecture-specs/specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: llm-client
# @test_path: tests/unit/llm/test_client.py

"""
Anthropic LLM Client
====================

Real LLM client that calls the Anthropic API with native support for:
- Tool calls via the `tools` parameter
- Extended thinking via the `thinking` parameter
- Prompt caching for token efficiency
- Usage statistics tracking

Usage:
    ```python
    client = AnthropicLLMClient(
        api_key="sk-ant-...",
        model="claude-sonnet-4-20250514",
    )

    response = client.complete(
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "Hello"}],
        tools=[read_file_tool],
        thinking=ThinkingConfig(enabled=True, budget_tokens=10000),
    )
    ```
"""

from typing import Any, Dict, List, Optional

import anthropic

from .interface import (
    LLMClient,
    LLMResponse,
    StopReason,
    ThinkingConfig,
    ToolCall,
    ToolDefinition,
)


class AnthropicLLMClient(LLMClient):
    """
    LLM client that uses the Anthropic API.

    Features:
    - Native tool support (no prompt injection needed)
    - Extended thinking for complex reasoning
    - Automatic prompt caching where possible
    - Comprehensive usage tracking

    Environment:
        Requires ANTHROPIC_API_KEY or explicit api_key parameter.
    """

    # Models that support extended thinking
    THINKING_MODELS = {
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
    }

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_retries: int = 3,
        timeout: float = 120.0,
    ):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-sonnet-4-20250514)
            max_retries: Maximum retry attempts for transient errors
            timeout: Request timeout in seconds
        """
        self.model = model
        self._client = anthropic.Anthropic(
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
        )

        # Usage tracking
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._cached_tokens = 0
        self._call_count = 0

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
        Make a completion request to the Anthropic API.

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
        self._call_count += 1

        # Build request parameters
        request_params = self._build_request_params(
            system=system,
            messages=messages,
            tools=tools,
            thinking=thinking,
            tool_choice=tool_choice,
            max_tokens=max_tokens,
        )

        # Make API call
        response = self._client.messages.create(**request_params)

        # Parse and return response
        return self._parse_response(response)

    def _build_request_params(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]],
        thinking: Optional[ThinkingConfig],
        tool_choice: str,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Build parameters for the API request."""
        params: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }

        # Add tools if provided
        if tools:
            params["tools"] = [tool.to_api_format() for tool in tools]

            # Map tool_choice to API format
            if tool_choice == "auto":
                params["tool_choice"] = {"type": "auto"}
            elif tool_choice == "any":
                params["tool_choice"] = {"type": "any"}
            elif tool_choice == "none":
                # Don't send tools if none selected
                del params["tools"]
            elif tool_choice.startswith("tool:"):
                # Specific tool requested
                tool_name = tool_choice[5:]
                params["tool_choice"] = {"type": "tool", "name": tool_name}

        # Add thinking if enabled and model supports it
        if thinking and thinking.enabled:
            if self.model in self.THINKING_MODELS:
                params["thinking"] = thinking.to_api_format()
            # Silently skip thinking for non-supporting models

        return params

    def _parse_response(self, response: anthropic.types.Message) -> LLMResponse:
        """Parse API response into LLMResponse format."""
        content = ""
        tool_calls: List[ToolCall] = []
        thinking_content: Optional[str] = None

        # Process content blocks
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        input=block.input,
                    )
                )
            elif block.type == "thinking":
                thinking_content = block.thinking

        # Map stop reason
        stop_reason = self._map_stop_reason(response.stop_reason)

        # Extract usage
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            "cache_creation_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
        }

        # Update cumulative tracking
        self._total_input_tokens += usage["input_tokens"]
        self._total_output_tokens += usage["output_tokens"]
        self._cached_tokens += usage["cache_read_tokens"]

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            thinking=thinking_content,
            stop_reason=stop_reason,
            usage=usage,
        )

    def _map_stop_reason(self, api_stop_reason: str) -> StopReason:
        """Map API stop reason to our enum."""
        mapping = {
            "end_turn": StopReason.END_TURN,
            "tool_use": StopReason.TOOL_USE,
            "max_tokens": StopReason.MAX_TOKENS,
            "stop_sequence": StopReason.STOP_SEQUENCE,
        }
        return mapping.get(api_stop_reason, StopReason.END_TURN)

    def get_usage_stats(self) -> Dict[str, int]:
        """Get cumulative usage statistics."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "cached_tokens": self._cached_tokens,
            "call_count": self._call_count,
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._cached_tokens = 0
        self._call_count = 0
