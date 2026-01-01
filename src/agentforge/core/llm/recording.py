# @spec_file: specs/minimal-context-architecture-specs/specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: llm-recording
# @test_path: tests/unit/llm/test_recording.py

"""
Recording LLM Client
====================

Wraps a real LLM client to record API responses for later playback.

This enables:
- Capturing real API sessions for deterministic replay
- Creating test fixtures from actual behavior
- Debugging production issues with recorded sessions

Usage:
    ```python
    # Record mode
    real_client = AnthropicLLMClient(api_key="...")
    recording_client = RecordingLLMClient(
        real_client=real_client,
        recording_path=Path("session.yaml"),
    )

    # Use normally - responses are recorded
    response = recording_client.complete(system="...", messages=[...])

    # Save recording (auto-saved on exit, or manually)
    recording_client.save()

    # Later, playback with SimulatedLLMClient
    client = LLMClientFactory.create(mode="playback", recording_path="session.yaml")
    ```
"""

import atexit
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .interface import (
    LLMClient,
    LLMResponse,
    ThinkingConfig,
    ToolDefinition,
)


class RecordingLLMClient(LLMClient):
    """
    LLM client wrapper that records responses for later playback.

    Records each API call with:
    - Request parameters (system, messages, tools)
    - Response content (text, tool_calls, thinking)
    - Metadata (timestamp, duration, usage)

    The recording format is compatible with ScriptedResponseStrategy
    for deterministic replay.
    """

    def __init__(
        self,
        real_client: LLMClient,
        recording_path: Path,
        auto_save: bool = True,
    ):
        """
        Initialize recording client.

        Args:
            real_client: The real LLM client to wrap
            recording_path: Where to save the recording
            auto_save: Whether to auto-save on exit (default: True)
        """
        self.real_client = real_client
        self.recording_path = Path(recording_path)
        self.auto_save = auto_save

        # Recording data
        self._recording: Dict[str, Any] = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "description": "Recorded LLM session",
            },
            "responses": [],
        }

        self._call_count = 0

        # Register auto-save on exit
        if auto_save:
            atexit.register(self.save)

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
        Make a completion request and record the response.

        Passes the request to the real client and records both
        request and response for later playback.
        """
        self._call_count += 1
        start_time = datetime.now()

        # Call real client
        response = self.real_client.complete(
            system=system,
            messages=messages,
            tools=tools,
            thinking=thinking,
            tool_choice=tool_choice,
            max_tokens=max_tokens,
        )

        duration = (datetime.now() - start_time).total_seconds()

        # Record the exchange
        self._record_exchange(
            step=self._call_count,
            system=system,
            messages=messages,
            tools=tools,
            thinking=thinking,
            response=response,
            duration=duration,
        )

        return response

    def _record_exchange(
        self,
        step: int,
        system: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]],
        thinking: Optional[ThinkingConfig],
        response: LLMResponse,
        duration: float,
    ) -> None:
        """Record a single request/response exchange."""
        record = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 3),
            # Response data (for playback)
            "content": response.content,
            "tool_calls": [
                {"name": tc.name, "input": tc.input}
                for tc in response.tool_calls
            ],
            "thinking": response.thinking,
            "stop_reason": response.stop_reason.value,
            # Request context (for debugging/verification)
            "_request": {
                "system_preview": system[:200] + "..." if len(system) > 200 else system,
                "message_count": len(messages),
                "last_message_preview": self._preview_message(messages[-1]) if messages else None,
                "tools": [t.name for t in tools] if tools else [],
                "thinking_enabled": thinking.enabled if thinking else False,
            },
            # Usage data
            "usage": response.usage,
        }

        self._recording["responses"].append(record)

    def _preview_message(self, message: Dict[str, Any]) -> str:
        """Create a preview of a message for debugging."""
        content = message.get("content", "")
        if isinstance(content, str):
            return content[:100] + "..." if len(content) > 100 else content
        elif isinstance(content, list):
            return f"[{len(content)} content blocks]"
        return str(content)[:100]

    def save(self) -> None:
        """Save recording to file."""
        if not self._recording["responses"]:
            return  # Don't save empty recordings

        # Update metadata
        self._recording["metadata"]["saved"] = datetime.now().isoformat()
        self._recording["metadata"]["total_calls"] = self._call_count
        self._recording["metadata"]["total_tokens"] = sum(
            r.get("usage", {}).get("input_tokens", 0) +
            r.get("usage", {}).get("output_tokens", 0)
            for r in self._recording["responses"]
        )

        # Ensure directory exists
        self.recording_path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML
        with open(self.recording_path, "w") as f:
            yaml.dump(
                self._recording,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def get_usage_stats(self) -> Dict[str, int]:
        """Get cumulative usage statistics from real client."""
        return self.real_client.get_usage_stats()

    def reset_usage_stats(self) -> None:
        """Reset usage statistics on real client."""
        self.real_client.reset_usage_stats()

    def get_recording(self) -> Dict[str, Any]:
        """Get the current recording data."""
        return dict(self._recording)

    def clear_recording(self) -> None:
        """Clear the current recording."""
        self._recording["responses"] = []
        self._call_count = 0
