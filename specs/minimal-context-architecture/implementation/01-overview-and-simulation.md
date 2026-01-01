# Minimal Context Architecture - Implementation Specification

**Document:** Implementation Spec  
**Version:** 1.0  
**Status:** Ready for Development  
**Date:** January 2025

---

## 1. Overview

### 1.1 Purpose

This document provides the detailed implementation specification for the Minimal Context Architecture. It includes:
- Component interfaces and contracts
- Implementation details with code examples
- Test strategies including **LLM simulation for development**
- Integration points with existing code

### 1.2 Key Implementation Principle

> **Develop and test without LLM invocation**

All components must be testable with simulated LLM responses. This:
- Eliminates token costs during development
- Enables deterministic testing
- Allows rapid iteration
- Supports CI/CD without API keys

### 1.3 Document Structure

| Section | Content | Status |
|---------|---------|--------|
| 1. Overview | This section | ✅ |
| 2. LLM Simulation | Mock LLM for development | ✅ |
| 3. Agent Config | AGENT.md implementation | Pending |
| 4. Fingerprint | Project fingerprint impl | Pending |
| 5. Context Templates | Template implementation | Pending |
| 6. LLM Client | Native API client | Pending |
| 7. Compaction | Compaction manager impl | Pending |
| 8. Audit | Transparency logging impl | Pending |
| 9. Integration | Executor integration | Pending |
| 10. Testing | Test strategy | Pending |

---

## 2. LLM Simulation System

### 2.1 Design Goals

```yaml
goals:
  - Run full workflows without API calls
  - Deterministic responses for testing
  - Simulate success, failure, and edge cases
  - Record interactions for debugging
  - Easy switch between simulation and real API
```

### 2.2 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ LLM Client Interface (Abstract)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐           ┌──────────────────┐            │
│  │ AnthropicClient  │           │ SimulatedClient  │            │
│  │ (Real API)       │           │ (Mock/Playback)  │            │
│  └────────┬─────────┘           └────────┬─────────┘            │
│           │                              │                       │
│           └──────────┬───────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│           ┌──────────────────┐                                  │
│           │ LLMClientFactory │                                  │
│           │ (selects based   │                                  │
│           │  on config)      │                                  │
│           └──────────────────┘                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 LLM Client Interface

```python
# src/agentforge/core/llm/interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass
from enum import Enum


class StopReason(str, Enum):
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"


@dataclass
class ToolCall:
    """A tool call from the LLM."""
    id: str
    name: str
    input: Dict[str, Any]


@dataclass
class LLMResponse:
    """Standardized response from any LLM client."""
    content: str
    tool_calls: List[ToolCall]
    thinking: Optional[str]
    stop_reason: StopReason
    usage: Dict[str, int]
    
    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


@dataclass
class ToolDefinition:
    """Definition of a tool for the LLM."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class ThinkingConfig:
    """Configuration for extended thinking."""
    enabled: bool = False
    budget_tokens: int = 8000


class LLMClient(ABC):
    """Abstract interface for LLM clients."""
    
    @abstractmethod
    def complete(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        thinking: Optional[ThinkingConfig] = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        """Make a completion request."""
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> Dict[str, int]:
        """Get cumulative usage statistics."""
        pass
    
    @abstractmethod
    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        pass
```

### 2.4 Simulated LLM Client

```python
# src/agentforge/core/llm/simulated.py

from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import yaml
import re
from dataclasses import dataclass, field

from .interface import (
    LLMClient, LLMResponse, ToolCall, ToolDefinition,
    ThinkingConfig, StopReason
)


@dataclass
class SimulatedResponse:
    """A pre-configured simulated response."""
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    thinking: Optional[str] = None
    stop_reason: str = "end_turn"
    
    def to_llm_response(self) -> LLMResponse:
        return LLMResponse(
            content=self.content,
            tool_calls=[
                ToolCall(
                    id=f"sim_{i}",
                    name=tc["name"],
                    input=tc.get("input", tc.get("parameters", {})),
                )
                for i, tc in enumerate(self.tool_calls)
            ],
            thinking=self.thinking,
            stop_reason=StopReason(self.stop_reason),
            usage={"input_tokens": 100, "output_tokens": 50},  # Simulated
        )


class ResponseStrategy(ABC):
    """Strategy for generating simulated responses."""
    
    @abstractmethod
    def get_response(
        self,
        system: str,
        messages: List[Dict],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        pass


class ScriptedResponseStrategy(ResponseStrategy):
    """
    Returns responses from a predefined script.
    
    Script format (YAML):
    ```yaml
    responses:
      - step: 1
        tool_calls:
          - name: read_file
            input:
              path: "/src/file.py"
      - step: 2
        tool_calls:
          - name: extract_function
            input:
              file_path: "/src/file.py"
              start_line: 42
              end_line: 65
              new_function_name: "_handle_error"
      - step: 3
        content: "Task complete"
        tool_calls:
          - name: complete
            input:
              summary: "Extracted function to reduce complexity"
    ```
    """
    
    def __init__(self, script_path: Optional[Path] = None, script_data: Optional[Dict] = None):
        if script_path:
            self.script = yaml.safe_load(script_path.read_text())
        elif script_data:
            self.script = script_data
        else:
            self.script = {"responses": []}
        
        self.current_step = 0
    
    def get_response(
        self,
        system: str,
        messages: List[Dict],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        responses = self.script.get("responses", [])
        
        if self.current_step >= len(responses):
            # Default: complete the task
            return SimulatedResponse(
                content="No more scripted responses",
                tool_calls=[{"name": "complete", "input": {"summary": "Script ended"}}],
            )
        
        response_data = responses[self.current_step]
        self.current_step += 1
        
        return SimulatedResponse(
            content=response_data.get("content", ""),
            tool_calls=response_data.get("tool_calls", []),
            thinking=response_data.get("thinking"),
            stop_reason=response_data.get("stop_reason", "tool_use" if response_data.get("tool_calls") else "end_turn"),
        )
    
    def reset(self) -> None:
        """Reset to beginning of script."""
        self.current_step = 0


class PatternMatchingStrategy(ResponseStrategy):
    """
    Returns responses based on pattern matching against context.
    
    Useful for testing specific scenarios without full scripts.
    """
    
    def __init__(self):
        self.patterns: List[tuple] = []  # (pattern_func, response)
    
    def add_pattern(
        self,
        matcher: Callable[[Dict], bool],
        response: SimulatedResponse,
    ) -> None:
        """Add a pattern matcher with its response."""
        self.patterns.append((matcher, response))
    
    def get_response(
        self,
        system: str,
        messages: List[Dict],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        for matcher, response in self.patterns:
            if matcher(context):
                return response
        
        # Default response
        return SimulatedResponse(
            content="No matching pattern found",
            tool_calls=[{"name": "escalate", "input": {"reason": "No pattern match"}}],
        )


class RecordingStrategy(ResponseStrategy):
    """
    Records real API responses for later playback.
    
    Usage:
    1. Run with real API, recording enabled
    2. Save recordings
    3. Use recordings for future test runs
    """
    
    def __init__(self, real_client: LLMClient, record_path: Path):
        self.real_client = real_client
        self.record_path = record_path
        self.recordings: List[Dict] = []
    
    def get_response(
        self,
        system: str,
        messages: List[Dict],
        tools: List[ToolDefinition],
        context: Dict[str, Any],
    ) -> SimulatedResponse:
        # Get real response
        response = self.real_client.complete(
            system=system,
            messages=messages,
            tools=tools,
        )
        
        # Record it
        recording = {
            "request": {
                "system": system,
                "messages": messages,
                "tools": [{"name": t.name} for t in tools],
            },
            "response": {
                "content": response.content,
                "tool_calls": [
                    {"name": tc.name, "input": tc.input}
                    for tc in response.tool_calls
                ],
                "thinking": response.thinking,
                "stop_reason": response.stop_reason.value,
            },
        }
        self.recordings.append(recording)
        
        return SimulatedResponse(
            content=response.content,
            tool_calls=[{"name": tc.name, "input": tc.input} for tc in response.tool_calls],
            thinking=response.thinking,
            stop_reason=response.stop_reason.value,
        )
    
    def save_recordings(self) -> None:
        """Save recordings to file."""
        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.record_path, 'w') as f:
            yaml.dump({"responses": [r["response"] for r in self.recordings]}, f)


class SimulatedLLMClient(LLMClient):
    """
    LLM client that returns simulated responses.
    
    Supports multiple strategies:
    - Scripted: Follow a predefined sequence
    - Pattern: Match context patterns to responses
    - Recording: Record real responses for playback
    """
    
    def __init__(
        self,
        strategy: Optional[ResponseStrategy] = None,
        default_response: Optional[SimulatedResponse] = None,
    ):
        self.strategy = strategy
        self.default_response = default_response or SimulatedResponse(
            content="Simulated response",
            tool_calls=[],
        )
        
        self._call_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_history: List[Dict] = []
    
    def complete(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        thinking: Optional[ThinkingConfig] = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        self._call_count += 1
        
        # Build context for strategy
        context = {
            "system": system,
            "messages": messages,
            "tools": tools or [],
            "thinking": thinking,
            "call_count": self._call_count,
        }
        
        # Record the call
        self._call_history.append({
            "system": system,
            "messages": messages,
            "tools": [t.name for t in (tools or [])],
        })
        
        # Get response from strategy or use default
        if self.strategy:
            sim_response = self.strategy.get_response(
                system, messages, tools or [], context
            )
        else:
            sim_response = self.default_response
        
        response = sim_response.to_llm_response()
        
        # Track simulated usage
        self._total_input_tokens += response.usage["input_tokens"]
        self._total_output_tokens += response.usage["output_tokens"]
        
        return response
    
    def get_usage_stats(self) -> Dict[str, int]:
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "cached_tokens": 0,
            "call_count": self._call_count,
        }
    
    def reset_usage_stats(self) -> None:
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0
    
    def get_call_history(self) -> List[Dict]:
        """Get history of all calls made (for debugging)."""
        return list(self._call_history)
    
    def clear_history(self) -> None:
        """Clear call history."""
        self._call_history.clear()
```

### 2.5 LLM Client Factory

```python
# src/agentforge/core/llm/factory.py

from typing import Optional
from pathlib import Path
import os

from .interface import LLMClient
from .simulated import (
    SimulatedLLMClient,
    ScriptedResponseStrategy,
    SimulatedResponse,
)


class LLMClientMode:
    """LLM client operating modes."""
    REAL = "real"           # Use real Anthropic API
    SIMULATED = "simulated" # Use simulated responses
    RECORD = "record"       # Use real API but record responses
    PLAYBACK = "playback"   # Playback recorded responses


class LLMClientFactory:
    """
    Factory for creating LLM clients based on configuration.
    
    Environment variables:
    - AGENTFORGE_LLM_MODE: real|simulated|record|playback
    - AGENTFORGE_LLM_SCRIPT: Path to simulation script
    - AGENTFORGE_LLM_RECORDING: Path to recording file
    - ANTHROPIC_API_KEY: API key (for real mode)
    """
    
    @classmethod
    def create(
        cls,
        mode: Optional[str] = None,
        script_path: Optional[Path] = None,
        recording_path: Optional[Path] = None,
        **kwargs,
    ) -> LLMClient:
        """
        Create an LLM client based on mode.
        
        Args:
            mode: Operating mode (defaults to env var or 'real')
            script_path: Path to simulation script
            recording_path: Path for recording/playback
            **kwargs: Additional arguments for client
            
        Returns:
            Configured LLMClient
        """
        mode = mode or os.environ.get("AGENTFORGE_LLM_MODE", LLMClientMode.REAL)
        
        if mode == LLMClientMode.REAL:
            from .client import AnthropicLLMClient
            return AnthropicLLMClient(**kwargs)
        
        elif mode == LLMClientMode.SIMULATED:
            script_path = script_path or os.environ.get("AGENTFORGE_LLM_SCRIPT")
            if script_path:
                strategy = ScriptedResponseStrategy(Path(script_path))
            else:
                strategy = None
            return SimulatedLLMClient(strategy=strategy)
        
        elif mode == LLMClientMode.PLAYBACK:
            recording_path = recording_path or os.environ.get("AGENTFORGE_LLM_RECORDING")
            if not recording_path:
                raise ValueError("AGENTFORGE_LLM_RECORDING required for playback mode")
            strategy = ScriptedResponseStrategy(Path(recording_path))
            return SimulatedLLMClient(strategy=strategy)
        
        elif mode == LLMClientMode.RECORD:
            from .client import AnthropicLLMClient
            from .simulated import RecordingStrategy
            
            recording_path = recording_path or os.environ.get("AGENTFORGE_LLM_RECORDING")
            if not recording_path:
                raise ValueError("AGENTFORGE_LLM_RECORDING required for record mode")
            
            real_client = AnthropicLLMClient(**kwargs)
            strategy = RecordingStrategy(real_client, Path(recording_path))
            return SimulatedLLMClient(strategy=strategy)
        
        else:
            raise ValueError(f"Unknown LLM mode: {mode}")
    
    @classmethod
    def create_for_testing(
        cls,
        responses: Optional[list] = None,
        script_data: Optional[dict] = None,
    ) -> SimulatedLLMClient:
        """
        Create a simulated client specifically for testing.
        
        Args:
            responses: List of response dicts
            script_data: Full script dict
            
        Returns:
            SimulatedLLMClient configured for testing
        """
        if responses:
            script_data = {"responses": responses}
        
        if script_data:
            strategy = ScriptedResponseStrategy(script_data=script_data)
        else:
            strategy = None
        
        return SimulatedLLMClient(strategy=strategy)
```

### 2.6 Example Simulation Scripts

```yaml
# tests/fixtures/llm_scripts/fix_violation_success.yaml
# Simulates a successful fix_violation workflow

metadata:
  name: "Fix Violation - Success Path"
  description: "Simulates successful complexity reduction via extract_function"
  task_type: fix_violation

responses:
  # Step 1: Read the target file
  - step: 1
    thinking: |
      The task is to reduce complexity of the 'execute' function.
      First, I should read the file to understand the code structure.
    tool_calls:
      - name: read_file
        input:
          path: "src/agentforge/core/executor.py"
  
  # Step 2: Extract error handling block
  - step: 2
    thinking: |
      Looking at the code, lines 67-78 handle error cases.
      This is a good extraction candidate that will reduce complexity by 4.
    tool_calls:
      - name: extract_function
        input:
          file_path: "src/agentforge/core/executor.py"
          source_function: "execute"
          start_line: 67
          end_line: 78
          new_function_name: "_handle_execution_error"
  
  # Step 3: Run verification
  - step: 3
    thinking: |
      The extraction succeeded. Now I need to verify:
      1. The conformance check passes
      2. All tests still pass
    tool_calls:
      - name: run_check
        input:
          file_path: "src/agentforge/core/executor.py"
  
  # Step 4: Complete
  - step: 4
    thinking: |
      Check passed - complexity is now 10 (was 15).
      Tests still pass. Task complete.
    content: "Successfully reduced complexity from 15 to 10"
    tool_calls:
      - name: complete
        input:
          summary: "Extracted _handle_execution_error to reduce cyclomatic complexity"
```

```yaml
# tests/fixtures/llm_scripts/fix_violation_escalate.yaml
# Simulates an escalation scenario

metadata:
  name: "Fix Violation - Escalation"
  description: "Simulates workflow that requires human intervention"

responses:
  - step: 1
    tool_calls:
      - name: read_file
        input:
          path: "src/complex_file.py"
  
  - step: 2
    thinking: |
      This function has deeply nested conditionals with complex business logic.
      The extraction candidates don't seem safe - they would change behavior.
      I should escalate for human review.
    tool_calls:
      - name: escalate
        input:
          reason: "Complex business logic - extraction may change behavior. Human review needed."
```

### 2.7 Usage Examples

```python
# Example 1: Unit test with simulated responses
def test_executor_calls_read_file_first():
    client = LLMClientFactory.create_for_testing(responses=[
        {
            "tool_calls": [{"name": "read_file", "input": {"path": "/test.py"}}]
        }
    ])
    
    executor = MinimalContextExecutor(
        project_path=Path("/tmp/test"),
        llm_client=client,  # Inject simulated client
    )
    
    result = executor.execute_step(...)
    
    # Verify the right tool was called
    assert client.get_call_history()[0]["tools"]
    assert result.action == "read_file"


# Example 2: Integration test with full script
def test_full_fix_workflow():
    script_path = Path("tests/fixtures/llm_scripts/fix_violation_success.yaml")
    client = LLMClientFactory.create(
        mode=LLMClientMode.SIMULATED,
        script_path=script_path,
    )
    
    executor = MinimalContextExecutor(
        project_path=test_project,
        llm_client=client,
    )
    
    result = executor.run_to_completion(task)
    
    assert result.status == "completed"
    assert "extract" in result.summary.lower()


# Example 3: Record real interactions for later playback
def record_real_execution():
    client = LLMClientFactory.create(
        mode=LLMClientMode.RECORD,
        recording_path=Path("recordings/session_001.yaml"),
    )
    
    executor = MinimalContextExecutor(
        project_path=real_project,
        llm_client=client,
    )
    
    result = executor.run_to_completion(task)
    
    # Save the recording
    client.strategy.save_recordings()


# Example 4: Environment-based configuration
# In CI/CD: AGENTFORGE_LLM_MODE=simulated
# In development: AGENTFORGE_LLM_MODE=real
def run_workflow():
    client = LLMClientFactory.create()  # Uses env vars
    executor = MinimalContextExecutor(
        project_path=project,
        llm_client=client,
    )
    return executor.run_to_completion(task)
```

---

**[Saved Part 1 - LLM Simulation System]**

*Continue to Part 2: Agent Config Implementation...*
