# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
# @component_id: llm-package
# @test_path: tests/unit/llm/test_package.py

"""
LLM Client Package
==================

Unified LLM client abstraction supporting multiple modes:
- real: Production API calls to Anthropic
- simulated: Mock responses for testing
- record: Capture real sessions for replay
- playback: Replay recorded sessions

Quick Start:
    ```python
    from agentforge.core.llm import LLMClientFactory

    # Auto-detect mode from AGENTFORGE_LLM_MODE env var
    client = LLMClientFactory.create()

    # Or explicit mode
    client = LLMClientFactory.create(mode="simulated")

    # For testing
    client = LLMClientFactory.create_for_testing(responses=[
        {"tool_calls": [{"name": "read_file", "input": {"path": "x.py"}}]},
        {"content": "Done"},
    ])
    ```

Environment Variables:
    AGENTFORGE_LLM_MODE: real|simulated|record|playback
    AGENTFORGE_LLM_SCRIPT: Path to simulation script (simulated mode)
    AGENTFORGE_LLM_RECORDING: Path to recording file (record/playback)
    ANTHROPIC_API_KEY: API key (real/record modes)
"""

# Core interfaces
from .interface import (
    LLMClient,
    LLMResponse,
    StopReason,
    ThinkingConfig,
    ToolCall,
    ToolDefinition,
    ToolExecutor,
    ToolResult,
)

# Factory (main entry point)
from .factory import (
    LLMClientFactory,
    LLMClientMode,
)

# Simulation components
from .simulated import (
    PatternMatchingStrategy,
    ResponseStrategy,
    ScriptedResponseStrategy,
    SequentialStrategy,
    SimulatedLLMClient,
    SimulatedResponse,
    create_simple_client,
)

# Real client (lazy import to avoid anthropic dependency when not needed)
# Use LLMClientFactory.create(mode="real") instead of direct import


__all__ = [
    # Core interfaces
    "LLMClient",
    "LLMResponse",
    "StopReason",
    "ThinkingConfig",
    "ToolCall",
    "ToolDefinition",
    "ToolExecutor",
    "ToolResult",
    # Factory
    "LLMClientFactory",
    "LLMClientMode",
    # Simulation
    "SimulatedLLMClient",
    "SimulatedResponse",
    "ResponseStrategy",
    "ScriptedResponseStrategy",
    "PatternMatchingStrategy",
    "SequentialStrategy",
    "create_simple_client",
]
