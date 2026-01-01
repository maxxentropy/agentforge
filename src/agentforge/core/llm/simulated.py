# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: llm-simulated
# @test_path: tests/unit/llm/test_simulated.py

"""
Simulated LLM Client
====================

Mock LLM client for development and testing without API calls.

Supports multiple response strategies:
- ScriptedResponseStrategy: Follow a predefined sequence
- PatternMatchingStrategy: Match context patterns to responses
- RecordingStrategy: Record real API responses for replay

Usage:
    ```python
    # Simple scripted responses
    client = SimulatedLLMClient(
        strategy=ScriptedResponseStrategy(script_data={
            "responses": [
                {"tool_calls": [{"name": "read_file", "input": {"path": "test.py"}}]},
                {"content": "Done", "tool_calls": [{"name": "complete", "input": {}}]},
            ]
        })
    )

    # Or use factory
    client = LLMClientFactory.create_for_testing(responses=[...])
    ```
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .interface import (
    LLMClient,
    LLMResponse,
    StopReason,
    ThinkingConfig,
    ToolCall,
    ToolDefinition,
)


@dataclass
class SimulatedResponse:
    """
    A pre-configured simulated response.

    Can be used directly or loaded from YAML scripts.
    """
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    thinking: Optional[str] = None
    stop_reason: str = "end_turn"

    def to_llm_response(self, call_index: int = 0) -> LLMResponse:
        """Convert to LLMResponse format."""
        # Determine stop reason
        if self.tool_calls:
            reason = StopReason.TOOL_USE
        else:
            reason = StopReason(self.stop_reason) if self.stop_reason else StopReason.END_TURN

        return LLMResponse(
            content=self.content,
            tool_calls=[
                ToolCall(
                    id=f"sim_{call_index}_{i}",
                    name=tc["name"],
                    input=tc.get("input", tc.get("parameters", {})),
                )
                for i, tc in enumerate(self.tool_calls)
            ],
            thinking=self.thinking,
            stop_reason=reason,
            usage={
                "input_tokens": 100,  # Simulated
                "output_tokens": 50,  # Simulated
                "cache_read_tokens": 0,
                "cache_creation_tokens": 0,
            },
        )


class ResponseStrategy(ABC):
    """
    Strategy for generating simulated responses.

    Implementations determine how responses are selected based on
    the current context and call history.
    """

    @abstractmethod
    def get_response(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        """
        Get the next simulated response.

        Args:
            system: System prompt
            messages: Conversation messages
            tools: Available tools
            context: Additional context (call_count, etc.)

        Returns:
            SimulatedResponse to return
        """
        pass

    def reset(self) -> None:
        """Reset strategy state (e.g., for replaying scripts)."""
        pass


class ScriptedResponseStrategy(ResponseStrategy):
    """
    Returns responses from a predefined script.

    Script format (YAML):
    ```yaml
    metadata:
      name: "Fix Violation - Happy Path"
      task_type: fix_violation

    responses:
      - step: 1
        thinking: "Let me read the file first..."
        tool_calls:
          - name: read_file
            input:
              path: "/src/file.py"

      - step: 2
        content: "Task complete"
        tool_calls:
          - name: complete
            input:
              summary: "Fixed the issue"
    ```
    """

    def __init__(
        self,
        script_path: Optional[Path] = None,
        script_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize with script from file or dict.

        Args:
            script_path: Path to YAML script file
            script_data: Script data as dict
        """
        if script_path:
            self.script = yaml.safe_load(Path(script_path).read_text())
        elif script_data:
            self.script = script_data
        else:
            self.script = {"responses": []}

        self.current_step = 0

    def get_response(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        """Get next scripted response."""
        responses = self.script.get("responses", [])

        if self.current_step >= len(responses):
            # Default: complete the task
            return SimulatedResponse(
                content="No more scripted responses - completing task",
                tool_calls=[{"name": "complete", "input": {"summary": "Script ended"}}],
            )

        response_data = responses[self.current_step]
        self.current_step += 1

        return SimulatedResponse(
            content=response_data.get("content", ""),
            tool_calls=response_data.get("tool_calls", []),
            thinking=response_data.get("thinking"),
            stop_reason=response_data.get(
                "stop_reason",
                "tool_use" if response_data.get("tool_calls") else "end_turn"
            ),
        )

    def reset(self) -> None:
        """Reset to beginning of script."""
        self.current_step = 0

    @property
    def remaining_responses(self) -> int:
        """Get number of remaining scripted responses."""
        return max(0, len(self.script.get("responses", [])) - self.current_step)


class PatternMatchingStrategy(ResponseStrategy):
    """
    Returns responses based on pattern matching against context.

    Useful for testing specific scenarios without full scripts.

    Example:
        ```python
        strategy = PatternMatchingStrategy()

        # Match when message contains "error"
        strategy.add_pattern(
            lambda ctx: "error" in str(ctx.get("messages", [])).lower(),
            SimulatedResponse(
                tool_calls=[{"name": "escalate", "input": {"reason": "Error detected"}}]
            )
        )
        ```
    """

    def __init__(self):
        self.patterns: List[tuple] = []
        self._default_response = SimulatedResponse(
            content="No matching pattern found",
            tool_calls=[{"name": "escalate", "input": {"reason": "No pattern match"}}],
        )

    def add_pattern(
        self,
        matcher: Callable[[Dict[str, Any]], bool],
        response: SimulatedResponse,
    ) -> "PatternMatchingStrategy":
        """
        Add a pattern matcher with its response.

        Args:
            matcher: Function that takes context dict and returns True if pattern matches
            response: Response to return when pattern matches

        Returns:
            Self for chaining
        """
        self.patterns.append((matcher, response))
        return self

    def set_default(self, response: SimulatedResponse) -> "PatternMatchingStrategy":
        """Set the default response when no patterns match."""
        self._default_response = response
        return self

    def get_response(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        """Get response matching first pattern."""
        # Build full context for matchers
        full_context = {
            "system": system,
            "messages": messages,
            "tools": tools,
            **context,
        }

        for matcher, response in self.patterns:
            try:
                if matcher(full_context):
                    return response
            except Exception:
                continue

        return self._default_response


class SequentialStrategy(ResponseStrategy):
    """
    Simple strategy that returns responses in sequence.

    Convenience wrapper around ScriptedResponseStrategy for
    simple test cases.
    """

    def __init__(self, responses: List[SimulatedResponse]):
        """
        Initialize with list of responses.

        Args:
            responses: Responses to return in order
        """
        self.responses = responses
        self.current_index = 0

    def get_response(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        """Get next response in sequence."""
        if self.current_index >= len(self.responses):
            return SimulatedResponse(
                content="Sequence exhausted",
                tool_calls=[{"name": "complete", "input": {"summary": "Done"}}],
            )

        response = self.responses[self.current_index]
        self.current_index += 1
        return response

    def reset(self) -> None:
        """Reset to beginning of sequence."""
        self.current_index = 0


class SimulatedLLMClient(LLMClient):
    """
    LLM client that returns simulated responses.

    Enables development and testing without API calls or token costs.

    Features:
    - Multiple response strategies (scripted, pattern, sequential)
    - Call history tracking for debugging
    - Usage statistics simulation
    - Easy integration with existing tests

    Example:
        ```python
        # For unit tests
        client = SimulatedLLMClient(
            strategy=ScriptedResponseStrategy(script_data={
                "responses": [
                    {"tool_calls": [{"name": "read_file", "input": {"path": "x.py"}}]},
                    {"content": "Done"},
                ]
            })
        )

        response = client.complete(
            system="Test",
            messages=[{"role": "user", "content": "Do task"}],
        )

        assert response.has_tool_calls
        assert response.tool_calls[0].name == "read_file"
        ```
    """

    def __init__(
        self,
        strategy: Optional[ResponseStrategy] = None,
        default_response: Optional[SimulatedResponse] = None,
    ):
        """
        Initialize simulated client.

        Args:
            strategy: Response strategy to use
            default_response: Response when no strategy or strategy returns None
        """
        self.strategy = strategy
        self.default_response = default_response or SimulatedResponse(
            content="Simulated response (no strategy configured)",
            tool_calls=[],
        )

        # Usage tracking
        self._call_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

        # Call history for debugging
        self._call_history: List[Dict[str, Any]] = []

    def complete(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        thinking: Optional[ThinkingConfig] = None,
        tool_choice: str = "auto",
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Make a simulated completion request."""
        self._call_count += 1
        tools = tools or []

        # Build context for strategy
        context = {
            "call_count": self._call_count,
            "thinking_enabled": thinking.enabled if thinking else False,
            "tool_choice": tool_choice,
            "max_tokens": max_tokens,
        }

        # Record the call
        self._call_history.append({
            "call_number": self._call_count,
            "system": system,
            "messages": messages,
            "tools": [t.name for t in tools],
            "thinking": thinking.enabled if thinking else False,
        })

        # Get response from strategy or use default
        if self.strategy:
            sim_response = self.strategy.get_response(
                system, messages, tools, context
            )
        else:
            sim_response = self.default_response

        response = sim_response.to_llm_response(call_index=self._call_count)

        # Track simulated usage
        self._total_input_tokens += response.usage["input_tokens"]
        self._total_output_tokens += response.usage["output_tokens"]

        return response

    def get_usage_stats(self) -> Dict[str, int]:
        """Get cumulative usage statistics."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "cached_tokens": 0,
            "call_count": self._call_count,
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of all calls made (for debugging)."""
        return list(self._call_history)

    def clear_history(self) -> None:
        """Clear call history."""
        self._call_history.clear()

    def reset(self) -> None:
        """Reset client state including strategy."""
        self.reset_usage_stats()
        self.clear_history()
        if self.strategy:
            self.strategy.reset()


def create_simple_client(responses: List[Dict[str, Any]]) -> SimulatedLLMClient:
    """
    Create a simulated client with simple response list.

    Convenience function for tests.

    Args:
        responses: List of response dicts with keys:
            - content: str (optional)
            - tool_calls: List[Dict] (optional)
            - thinking: str (optional)

    Returns:
        Configured SimulatedLLMClient

    Example:
        ```python
        client = create_simple_client([
            {"tool_calls": [{"name": "read_file", "input": {"path": "x.py"}}]},
            {"content": "Done"},
        ])
        ```
    """
    sim_responses = [
        SimulatedResponse(
            content=r.get("content", ""),
            tool_calls=r.get("tool_calls", []),
            thinking=r.get("thinking"),
        )
        for r in responses
    ]

    return SimulatedLLMClient(strategy=SequentialStrategy(sim_responses))
