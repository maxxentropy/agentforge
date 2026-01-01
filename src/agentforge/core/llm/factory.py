# @spec_file: specs/minimal-context-architecture-specs/specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: llm-factory
# @test_path: tests/unit/llm/test_factory.py

"""
LLM Client Factory
==================

Factory for creating LLM clients based on configuration and environment.

Supports four modes:
- real: Use Anthropic API (requires ANTHROPIC_API_KEY)
- simulated: Use mock responses (no API calls)
- record: Use real API and record responses for later replay
- playback: Replay recorded responses

Environment Variables:
- AGENTFORGE_LLM_MODE: real|simulated|record|playback
- AGENTFORGE_LLM_SCRIPT: Path to simulation script (for simulated mode)
- AGENTFORGE_LLM_RECORDING: Path to recording file (for record/playback)
- ANTHROPIC_API_KEY: API key (for real/record modes)

Usage:
    ```python
    # Use environment variables
    client = LLMClientFactory.create()

    # Explicit mode
    client = LLMClientFactory.create(mode="simulated")

    # For testing
    client = LLMClientFactory.create_for_testing(responses=[...])
    ```
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .interface import LLMClient
from .simulated import (
    ScriptedResponseStrategy,
    SimulatedLLMClient,
    SimulatedResponse,
    SequentialStrategy,
)


class LLMClientMode(str, Enum):
    """LLM client operating modes."""
    REAL = "real"           # Use real Anthropic API
    SIMULATED = "simulated" # Use simulated responses
    RECORD = "record"       # Use real API but record responses
    PLAYBACK = "playback"   # Playback recorded responses


class LLMClientFactory:
    """
    Factory for creating LLM clients based on configuration.

    The factory reads environment variables to determine which client
    implementation to use, enabling seamless switching between
    development (simulated) and production (real) modes.

    Environment Variables:
        AGENTFORGE_LLM_MODE: Operating mode (default: real)
        AGENTFORGE_LLM_SCRIPT: Path to simulation script
        AGENTFORGE_LLM_RECORDING: Path to recording file
        ANTHROPIC_API_KEY: API key for real mode
    """

    # Environment variable names
    ENV_MODE = "AGENTFORGE_LLM_MODE"
    ENV_SCRIPT = "AGENTFORGE_LLM_SCRIPT"
    ENV_RECORDING = "AGENTFORGE_LLM_RECORDING"
    ENV_API_KEY = "ANTHROPIC_API_KEY"

    @classmethod
    def create(
        cls,
        mode: Optional[str] = None,
        script_path: Optional[Path] = None,
        recording_path: Optional[Path] = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> LLMClient:
        """
        Create an LLM client based on mode.

        Args:
            mode: Operating mode (defaults to env var or 'real')
            script_path: Path to simulation script
            recording_path: Path for recording/playback
            model: Model to use for real API
            **kwargs: Additional arguments for client

        Returns:
            Configured LLMClient

        Raises:
            ValueError: If mode is invalid or required config missing
        """
        # Determine mode
        mode_str = mode or os.environ.get(cls.ENV_MODE, LLMClientMode.REAL.value)
        try:
            client_mode = LLMClientMode(mode_str.lower())
        except ValueError:
            valid_modes = ", ".join(m.value for m in LLMClientMode)
            raise ValueError(f"Invalid LLM mode: {mode_str}. Valid: {valid_modes}")

        # Create appropriate client
        if client_mode == LLMClientMode.REAL:
            return cls._create_real_client(model=model, **kwargs)

        elif client_mode == LLMClientMode.SIMULATED:
            return cls._create_simulated_client(script_path=script_path)

        elif client_mode == LLMClientMode.PLAYBACK:
            return cls._create_playback_client(recording_path=recording_path)

        elif client_mode == LLMClientMode.RECORD:
            return cls._create_recording_client(
                recording_path=recording_path,
                model=model,
                **kwargs,
            )

        raise ValueError(f"Unhandled mode: {client_mode}")

    @classmethod
    def _create_real_client(cls, model: str, **kwargs) -> LLMClient:
        """Create real Anthropic API client."""
        # Import here to avoid dependency when not needed
        from .client import AnthropicLLMClient

        api_key = kwargs.pop("api_key", None) or os.environ.get(cls.ENV_API_KEY)
        if not api_key:
            raise ValueError(
                f"No API key found. Set {cls.ENV_API_KEY} environment variable "
                f"or pass api_key parameter."
            )

        return AnthropicLLMClient(api_key=api_key, model=model, **kwargs)

    @classmethod
    def _create_simulated_client(
        cls,
        script_path: Optional[Path] = None,
    ) -> SimulatedLLMClient:
        """Create simulated client with optional script."""
        script_path = script_path or os.environ.get(cls.ENV_SCRIPT)

        if script_path:
            path = Path(script_path)
            if not path.exists():
                raise ValueError(f"Simulation script not found: {path}")
            strategy = ScriptedResponseStrategy(script_path=path)
        else:
            strategy = None

        return SimulatedLLMClient(strategy=strategy)

    @classmethod
    def _create_playback_client(
        cls,
        recording_path: Optional[Path] = None,
    ) -> SimulatedLLMClient:
        """Create client that plays back recorded responses."""
        recording_path = recording_path or os.environ.get(cls.ENV_RECORDING)

        if not recording_path:
            raise ValueError(
                f"{cls.ENV_RECORDING} required for playback mode"
            )

        path = Path(recording_path)
        if not path.exists():
            raise ValueError(f"Recording file not found: {path}")

        strategy = ScriptedResponseStrategy(script_path=path)
        return SimulatedLLMClient(strategy=strategy)

    @classmethod
    def _create_recording_client(
        cls,
        recording_path: Optional[Path] = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> LLMClient:
        """Create client that records real API responses."""
        from .client import AnthropicLLMClient
        from .recording import RecordingLLMClient

        recording_path = recording_path or os.environ.get(cls.ENV_RECORDING)

        if not recording_path:
            raise ValueError(
                f"{cls.ENV_RECORDING} required for record mode"
            )

        api_key = kwargs.pop("api_key", None) or os.environ.get(cls.ENV_API_KEY)
        if not api_key:
            raise ValueError(
                f"No API key found for recording. Set {cls.ENV_API_KEY}."
            )

        real_client = AnthropicLLMClient(api_key=api_key, model=model, **kwargs)
        return RecordingLLMClient(
            real_client=real_client,
            recording_path=Path(recording_path),
        )

    @classmethod
    def create_for_testing(
        cls,
        responses: Optional[List[Dict[str, Any]]] = None,
        script_data: Optional[Dict[str, Any]] = None,
    ) -> SimulatedLLMClient:
        """
        Create a simulated client specifically for testing.

        Convenience method that doesn't require environment variables.

        Args:
            responses: List of response dicts (simple format)
            script_data: Full script dict (with metadata)

        Returns:
            SimulatedLLMClient configured for testing

        Example:
            ```python
            # Simple list of responses
            client = LLMClientFactory.create_for_testing(responses=[
                {"tool_calls": [{"name": "read_file", "input": {"path": "x.py"}}]},
                {"content": "Done"},
            ])

            # Full script format
            client = LLMClientFactory.create_for_testing(script_data={
                "metadata": {"name": "Test Script"},
                "responses": [
                    {"step": 1, "tool_calls": [...]},
                    {"step": 2, "content": "Done"},
                ]
            })
            ```
        """
        if responses:
            # Convert simple format to SimulatedResponse objects
            sim_responses = [
                SimulatedResponse(
                    content=r.get("content", ""),
                    tool_calls=r.get("tool_calls", []),
                    thinking=r.get("thinking"),
                )
                for r in responses
            ]
            strategy = SequentialStrategy(sim_responses)

        elif script_data:
            strategy = ScriptedResponseStrategy(script_data=script_data)

        else:
            strategy = None

        return SimulatedLLMClient(strategy=strategy)

    @classmethod
    def get_current_mode(cls) -> str:
        """Get the current LLM mode from environment."""
        return os.environ.get(cls.ENV_MODE, LLMClientMode.REAL.value)

    @classmethod
    def is_simulated(cls) -> bool:
        """Check if currently in simulated mode."""
        mode = cls.get_current_mode()
        return mode in (LLMClientMode.SIMULATED.value, LLMClientMode.PLAYBACK.value)
