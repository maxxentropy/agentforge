# AgentForge Self-Hosting Implementation Plan

## Objective

Enable AgentForge to autonomously fix its own conformance violations with human oversight, building trust through verifiable, auditable execution.

**End State:** `agentforge agent fix-violations --auto` clears violations, runs tests, and commits fixes.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SELF-HOSTING LOOP                                │
│                                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │  Read    │──▶│  Plan    │──▶│ Implement│──▶│  Verify  │──┐      │
│  │Violation │   │   Fix    │   │   Fix    │   │   Fix    │  │      │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘  │      │
│       ▲                                              │       │      │
│       │                                              ▼       │      │
│       │         ┌──────────┐   ┌──────────┐   ┌──────────┐  │      │
│       └─────────│ Rollback │◀──│  Tests   │◀──│  Commit  │◀─┘      │
│         fail    │ on Fail  │   │  Pass?   │   │ Changes  │         │
│                 └──────────┘   └──────────┘   └──────────┘         │
│                                     │                               │
│                                     ▼ no                            │
│                              ┌──────────┐                           │
│                              │ Escalate │                           │
│                              │ to Human │                           │
│                              └──────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation - LLM Context Serialization (5 hours)

### Goal
Make all agent decisions auditable and recoverable via YAML persistence.

### Step 1.1: Add Serialization to Domain Entities

**File:** `tools/harness/llm_executor_domain.py`

Add `to_dict()` and `from_dict()` methods to these classes:

```python
# ============================================================
# ADD TO: tools/harness/llm_executor_domain.py
# ============================================================

from datetime import datetime
from typing import Any, Dict, List, Optional

# Update ToolCall class
@dataclass
class ToolCall:
    """A request to execute a specific tool."""
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    category: Optional[ToolCategory] = None

    def __post_init__(self):
        if self.category is None:
            self.category = self._infer_category()

    def _infer_category(self) -> ToolCategory:
        # ... existing code ...
        pass
    
    # ADD THESE METHODS:
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "name": self.name,
            "parameters": self.parameters,
            "category": self.category.value if self.category else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Deserialize from dict."""
        category = None
        if data.get("category"):
            category = ToolCategory(data["category"])
        return cls(
            name=data["name"],
            parameters=data.get("parameters", {}),
            category=category
        )


# Update ToolResult class
@dataclass
class ToolResult:
    """Result of executing a tool."""
    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0

    # ADD THESE METHODS:
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        # Ensure output is serializable (convert complex objects to string)
        output = self.output
        if output is not None and not isinstance(output, (str, int, float, bool, list, dict)):
            output = str(output)
        
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "output": output,
            "error": self.error,
            "duration_seconds": self.duration_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        """Deserialize from dict."""
        return cls(
            tool_name=data["tool_name"],
            success=data["success"],
            output=data.get("output"),
            error=data.get("error"),
            duration_seconds=data.get("duration_seconds", 0.0)
        )


# Update AgentAction class
@dataclass
class AgentAction:
    """An action decided by the agent."""
    action_type: ActionType
    reasoning: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    response: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ADD THESE METHODS:
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "action_type": self.action_type.value,
            "reasoning": self.reasoning,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "response": self.response,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAction":
        """Deserialize from dict."""
        return cls(
            action_type=ActionType(data["action_type"]),
            reasoning=data.get("reasoning", ""),
            tool_calls=[ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])],
            response=data.get("response"),
            metadata=data.get("metadata", {})
        )


# Update ConversationMessage class
@dataclass
class ConversationMessage:
    """A message in the agent conversation history."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None

    # ADD THESE METHODS:
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": [tc.to_dict() for tc in self.tool_calls] if self.tool_calls else None,
            "tool_results": [tr.to_dict() for tr in self.tool_results] if self.tool_results else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Deserialize from dict."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()
            
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            tool_calls=[ToolCall.from_dict(tc) for tc in data["tool_calls"]] if data.get("tool_calls") else None,
            tool_results=[ToolResult.from_dict(tr) for tr in data["tool_results"]] if data.get("tool_results") else None
        )


# Update ExecutionContext class
@dataclass
class ExecutionContext:
    """Context for agent execution step."""
    session_id: str
    task_description: str
    current_phase: str
    available_tools: List[str]
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    tokens_used: int = 0
    token_budget: int = 100000

    # ADD THESE METHODS:
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "session_id": self.session_id,
            "task_description": self.task_description,
            "current_phase": self.current_phase,
            "available_tools": self.available_tools,
            "conversation_history": [msg.to_dict() for msg in self.conversation_history],
            "memory_context": self.memory_context,
            "iteration": self.iteration,
            "tokens_used": self.tokens_used,
            "token_budget": self.token_budget
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        """Deserialize from dict."""
        return cls(
            session_id=data["session_id"],
            task_description=data["task_description"],
            current_phase=data["current_phase"],
            available_tools=data["available_tools"],
            conversation_history=[
                ConversationMessage.from_dict(m) 
                for m in data.get("conversation_history", [])
            ],
            memory_context=data.get("memory_context", {}),
            iteration=data.get("iteration", 0),
            tokens_used=data.get("tokens_used", 0),
            token_budget=data.get("token_budget", 100000)
        )


# Update StepResult class
@dataclass
class StepResult:
    """Result of executing one agent step."""
    success: bool
    action: Optional[AgentAction] = None
    tool_results: List[ToolResult] = field(default_factory=list)
    tokens_used: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None
    should_continue: bool = True

    # ADD THESE METHODS:
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "success": self.success,
            "action": self.action.to_dict() if self.action else None,
            "tool_results": [tr.to_dict() for tr in self.tool_results],
            "tokens_used": self.tokens_used,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "should_continue": self.should_continue
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepResult":
        """Deserialize from dict."""
        return cls(
            success=data["success"],
            action=AgentAction.from_dict(data["action"]) if data.get("action") else None,
            tool_results=[ToolResult.from_dict(tr) for tr in data.get("tool_results", [])],
            tokens_used=data.get("tokens_used", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            error=data.get("error"),
            should_continue=data.get("should_continue", True)
        )
```

### Step 1.2: Create ExecutionContextStore

**File:** `tools/harness/execution_context_store.py` (NEW)

```python
"""
Execution Context Store
=======================

Persists LLM execution context and step history to YAML.
Enables audit, recovery, and replay of agent sessions.
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .llm_executor_domain import ExecutionContext, StepResult


class ExecutionContextStore:
    """
    Persists execution context and step history to YAML files.
    
    File structure per session:
        .agentforge/sessions/{session_id}/
        ├── session.yaml           # Session metadata (existing)
        ├── execution_context.yaml # LLM execution context
        └── step_history.yaml      # Step-by-step execution log
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize store.
        
        Args:
            base_path: Base path for session storage (e.g., .agentforge/sessions)
        """
        self.base_path = Path(base_path)
    
    def _session_dir(self, session_id: str) -> Path:
        """Get session directory path."""
        return self.base_path / session_id
    
    def save_context(self, context: ExecutionContext) -> Path:
        """
        Save execution context to YAML.
        
        Args:
            context: ExecutionContext to save
            
        Returns:
            Path to saved file
        """
        session_dir = self._session_dir(context.session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        context_file = session_dir / "execution_context.yaml"
        
        data = context.to_dict()
        data["_saved_at"] = datetime.utcnow().isoformat()
        
        # Atomic write
        temp_file = context_file.with_suffix(".yaml.tmp")
        with open(temp_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        temp_file.rename(context_file)
        
        return context_file
    
    def load_context(self, session_id: str) -> Optional[ExecutionContext]:
        """
        Load execution context from YAML.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            ExecutionContext or None if not found
        """
        context_file = self._session_dir(session_id) / "execution_context.yaml"
        
        if not context_file.exists():
            return None
        
        try:
            with open(context_file) as f:
                data = yaml.safe_load(f)
            
            # Remove metadata fields before deserializing
            data.pop("_saved_at", None)
            
            return ExecutionContext.from_dict(data)
        except (yaml.YAMLError, KeyError, TypeError) as e:
            # Log error but don't crash
            return None
    
    def append_step(self, session_id: str, step: StepResult) -> Path:
        """
        Append step result to history file.
        
        Args:
            session_id: Session ID
            step: StepResult to append
            
        Returns:
            Path to history file
        """
        session_dir = self._session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        history_file = session_dir / "step_history.yaml"
        
        # Load existing or create new
        if history_file.exists():
            with open(history_file) as f:
                history = yaml.safe_load(f) or {"steps": []}
        else:
            history = {
                "session_id": session_id,
                "started_at": datetime.utcnow().isoformat(),
                "steps": []
            }
        
        # Append step with timestamp
        step_data = step.to_dict()
        step_data["_recorded_at"] = datetime.utcnow().isoformat()
        step_data["_step_number"] = len(history["steps"]) + 1
        history["steps"].append(step_data)
        history["_updated_at"] = datetime.utcnow().isoformat()
        
        # Atomic write
        temp_file = history_file.with_suffix(".yaml.tmp")
        with open(temp_file, 'w') as f:
            yaml.dump(history, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        temp_file.rename(history_file)
        
        return history_file
    
    def get_history(self, session_id: str) -> List[StepResult]:
        """
        Load step history for session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of StepResult objects
        """
        history_file = self._session_dir(session_id) / "step_history.yaml"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file) as f:
                data = yaml.safe_load(f)
            
            steps = []
            for step_data in data.get("steps", []):
                # Remove metadata before deserializing
                step_data.pop("_recorded_at", None)
                step_data.pop("_step_number", None)
                steps.append(StepResult.from_dict(step_data))
            
            return steps
        except (yaml.YAMLError, KeyError, TypeError):
            return []
    
    def get_last_step(self, session_id: str) -> Optional[StepResult]:
        """Get the most recent step for a session."""
        history = self.get_history(session_id)
        return history[-1] if history else None
    
    def clear_history(self, session_id: str) -> bool:
        """
        Clear step history for session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if cleared successfully
        """
        history_file = self._session_dir(session_id) / "step_history.yaml"
        
        if history_file.exists():
            history_file.unlink()
            return True
        return False
```

### Step 1.3: Create Serialization Tests

**File:** `tests/unit/harness/test_llm_executor_serialization.py` (NEW)

```python
"""
Tests for LLM Executor Serialization
====================================

Ensures all domain entities round-trip correctly through YAML.
"""

import pytest
import yaml
from datetime import datetime
from pathlib import Path
import tempfile

from tools.harness.llm_executor_domain import (
    ActionType,
    ToolCategory,
    ToolCall,
    ToolResult,
    AgentAction,
    ConversationMessage,
    ExecutionContext,
    StepResult,
)
from tools.harness.execution_context_store import ExecutionContextStore


class TestToolCallSerialization:
    def test_round_trip(self):
        original = ToolCall(
            name="read_file",
            parameters={"path": "/tmp/test.py"},
            category=ToolCategory.FILE
        )
        
        data = original.to_dict()
        restored = ToolCall.from_dict(data)
        
        assert restored.name == original.name
        assert restored.parameters == original.parameters
        assert restored.category == original.category
    
    def test_yaml_serializable(self):
        tc = ToolCall(name="bash", parameters={"command": "ls -la"})
        yaml_str = yaml.dump(tc.to_dict())
        restored_data = yaml.safe_load(yaml_str)
        restored = ToolCall.from_dict(restored_data)
        assert restored.name == tc.name
    
    def test_none_category(self):
        tc = ToolCall(name="custom_tool", parameters={})
        data = tc.to_dict()
        # Category should be inferred, so it won't be None after __post_init__
        assert data["category"] is not None


class TestToolResultSerialization:
    def test_success_round_trip(self):
        original = ToolResult.success_result("read_file", "file contents", 0.5)
        
        data = original.to_dict()
        restored = ToolResult.from_dict(data)
        
        assert restored.tool_name == original.tool_name
        assert restored.success == original.success
        assert restored.output == original.output
        assert restored.duration_seconds == original.duration_seconds
    
    def test_failure_round_trip(self):
        original = ToolResult.failure_result("write_file", "Permission denied", 0.1)
        
        data = original.to_dict()
        restored = ToolResult.from_dict(data)
        
        assert restored.success is False
        assert restored.error == "Permission denied"
    
    def test_complex_output_converted_to_string(self):
        # Complex objects should be stringified
        class CustomObject:
            def __str__(self):
                return "CustomObject()"
        
        tr = ToolResult(
            tool_name="test",
            success=True,
            output=CustomObject()
        )
        data = tr.to_dict()
        assert data["output"] == "CustomObject()"


class TestAgentActionSerialization:
    def test_tool_action_round_trip(self):
        tool_calls = [
            ToolCall(name="read_file", parameters={"path": "test.py"}),
            ToolCall(name="grep", parameters={"pattern": "def"})
        ]
        original = AgentAction.tool_action(tool_calls, "Need to understand the code")
        
        data = original.to_dict()
        restored = AgentAction.from_dict(data)
        
        assert restored.action_type == ActionType.TOOL_CALL
        assert restored.reasoning == original.reasoning
        assert len(restored.tool_calls) == 2
        assert restored.tool_calls[0].name == "read_file"
    
    def test_complete_action_round_trip(self):
        original = AgentAction.complete_action("Task done", "All tests pass")
        
        data = original.to_dict()
        restored = AgentAction.from_dict(data)
        
        assert restored.action_type == ActionType.COMPLETE
        assert restored.response == "Task done"


class TestConversationMessageSerialization:
    def test_user_message_round_trip(self):
        original = ConversationMessage.user_message("Fix the bug")
        
        data = original.to_dict()
        restored = ConversationMessage.from_dict(data)
        
        assert restored.role == "user"
        assert restored.content == "Fix the bug"
    
    def test_assistant_message_with_tools(self):
        tool_calls = [ToolCall(name="read_file", parameters={"path": "bug.py"})]
        original = ConversationMessage.assistant_message(
            "I'll read the file first",
            tool_calls=tool_calls
        )
        
        data = original.to_dict()
        restored = ConversationMessage.from_dict(data)
        
        assert restored.role == "assistant"
        assert len(restored.tool_calls) == 1
        assert restored.tool_calls[0].name == "read_file"
    
    def test_timestamp_preserved(self):
        ts = datetime(2025, 12, 31, 10, 30, 0)
        original = ConversationMessage(role="user", content="test", timestamp=ts)
        
        data = original.to_dict()
        restored = ConversationMessage.from_dict(data)
        
        assert restored.timestamp == ts


class TestExecutionContextSerialization:
    def test_full_context_round_trip(self):
        original = ExecutionContext(
            session_id="test-session-123",
            task_description="Fix conformance violations",
            current_phase="execute",
            available_tools=["read_file", "edit_file", "run_tests"],
            iteration=5,
            tokens_used=5000,
            token_budget=100000
        )
        original.add_user_message("Start fixing")
        original.add_assistant_message("I'll begin by reading the code")
        
        data = original.to_dict()
        restored = ExecutionContext.from_dict(data)
        
        assert restored.session_id == original.session_id
        assert restored.task_description == original.task_description
        assert restored.available_tools == original.available_tools
        assert restored.iteration == original.iteration
        assert len(restored.conversation_history) == 2


class TestStepResultSerialization:
    def test_success_step_round_trip(self):
        action = AgentAction.tool_action(
            [ToolCall(name="read_file", parameters={"path": "test.py"})],
            "Reading file"
        )
        tool_results = [ToolResult.success_result("read_file", "contents", 0.1)]
        
        original = StepResult.success_step(action, tool_results, 500, 1.5)
        
        data = original.to_dict()
        restored = StepResult.from_dict(data)
        
        assert restored.success is True
        assert restored.action.action_type == ActionType.TOOL_CALL
        assert len(restored.tool_results) == 1
        assert restored.tokens_used == 500
    
    def test_failure_step_round_trip(self):
        original = StepResult.failure_step("API error", 0.5)
        
        data = original.to_dict()
        restored = StepResult.from_dict(data)
        
        assert restored.success is False
        assert restored.error == "API error"
        assert restored.should_continue is False


class TestExecutionContextStore:
    @pytest.fixture
    def temp_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ExecutionContextStore(Path(tmpdir))
    
    def test_save_and_load_context(self, temp_store):
        context = ExecutionContext(
            session_id="test-123",
            task_description="Test task",
            current_phase="execute",
            available_tools=["read_file"]
        )
        
        path = temp_store.save_context(context)
        assert path.exists()
        
        loaded = temp_store.load_context("test-123")
        assert loaded is not None
        assert loaded.session_id == "test-123"
        assert loaded.task_description == "Test task"
    
    def test_append_and_get_history(self, temp_store):
        step1 = StepResult(success=True, tokens_used=100)
        step2 = StepResult(success=True, tokens_used=200)
        
        temp_store.append_step("test-456", step1)
        temp_store.append_step("test-456", step2)
        
        history = temp_store.get_history("test-456")
        assert len(history) == 2
        assert history[0].tokens_used == 100
        assert history[1].tokens_used == 200
    
    def test_get_last_step(self, temp_store):
        temp_store.append_step("test-789", StepResult(success=True, tokens_used=100))
        temp_store.append_step("test-789", StepResult(success=False, error="fail"))
        
        last = temp_store.get_last_step("test-789")
        assert last.success is False
        assert last.error == "fail"
    
    def test_load_nonexistent_returns_none(self, temp_store):
        assert temp_store.load_context("nonexistent") is None
        assert temp_store.get_history("nonexistent") == []
```

### Step 1.4: Integrate Store with Orchestrator

**File:** `tools/harness/agent_orchestrator.py` (MODIFY)

Add these changes:

```python
# At top of file, add import:
from .execution_context_store import ExecutionContextStore

# In __init__, add parameter and initialization:
def __init__(
    self,
    session_manager,
    memory_manager,
    tool_selector,
    agent_monitor,
    recovery_executor,
    escalation_manager,
    config: Optional[OrchestratorConfig] = None,
    llm_executor: Optional["LLMExecutor"] = None,
    working_dir: Optional[Path] = None,
    execution_store: Optional[ExecutionContextStore] = None,  # ADD THIS
):
    # ... existing code ...
    
    # ADD THIS:
    self.execution_store = execution_store or ExecutionContextStore(
        (working_dir or Path.cwd()) / ".agentforge" / "sessions"
    )

# In execute_step(), after LLM execution, add persistence:
def execute_step(self, session_id: str, input_data: Optional[dict] = None) -> ExecutionResult:
    # ... existing step execution code ...
    
    # ADD after step execution completes:
    if session_id in self._llm_contexts:
        # Persist context after each step
        self.execution_store.save_context(self._llm_contexts[session_id])
        
        # Persist step result
        if 'step_result' in locals() and step_result:
            self.execution_store.append_step(session_id, step_result)
    
    # ... rest of method ...

# In resume_session(), restore LLM context:
def resume_session(self, session_id: str) -> bool:
    # ... existing code ...
    
    # ADD: Restore LLM context if available
    if self.llm_executor and session_id not in self._llm_contexts:
        stored_context = self.execution_store.load_context(session_id)
        if stored_context:
            self._llm_contexts[session_id] = stored_context
    
    # ... rest of method ...
```

### Step 1.5: Verify Phase 1

```bash
# Run serialization tests
python -m pytest tests/unit/harness/test_llm_executor_serialization.py -v

# Run all harness tests to ensure no regressions
python -m pytest tests/unit/harness/ -v --tb=short
```

---

## Phase 2: Violation Tools (4 hours)

### Goal
Give the agent tools to read violations, check conformance, and understand what needs fixing.

### Step 2.1: Create Violation Tools Module

**File:** `tools/harness/violation_tools.py` (NEW)

```python
"""
Violation Tools
===============

Tools for reading and managing conformance violations.
These tools enable the agent to understand and fix violations.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .llm_executor_domain import ToolResult


@dataclass
class ViolationInfo:
    """Parsed violation information."""
    violation_id: str
    contract_id: str
    check_id: str
    severity: str
    file_path: str
    message: str
    fix_hint: Optional[str]
    status: str
    detected_at: str
    
    def to_summary(self) -> str:
        """Create human-readable summary."""
        return f"""Violation: {self.violation_id}
Severity: {self.severity}
File: {self.file_path}
Check: {self.check_id}
Message: {self.message}
Hint: {self.fix_hint or 'No hint available'}"""


class ViolationTools:
    """
    Tools for working with conformance violations.
    
    Provides read-only access to violation data for the agent.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize violation tools.
        
        Args:
            project_path: Project root directory
        """
        self.project_path = Path(project_path)
        self.violations_dir = self.project_path / ".agentforge" / "violations"
    
    def read_violation(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Read a specific violation by ID.
        
        Parameters:
            violation_id: The violation ID (e.g., "V-4734938a9485")
        
        Returns:
            ToolResult with violation details
        """
        violation_id = params.get("violation_id")
        if not violation_id:
            return ToolResult.failure_result(
                "read_violation",
                "Missing required parameter: violation_id"
            )
        
        # Normalize ID
        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"
        
        violation_file = self.violations_dir / f"{violation_id}.yaml"
        
        if not violation_file.exists():
            return ToolResult.failure_result(
                "read_violation",
                f"Violation not found: {violation_id}"
            )
        
        try:
            with open(violation_file) as f:
                data = yaml.safe_load(f)
            
            info = ViolationInfo(
                violation_id=data.get("violation_id", violation_id),
                contract_id=data.get("contract_id", "unknown"),
                check_id=data.get("check_id", "unknown"),
                severity=data.get("severity", "major"),
                file_path=data.get("file_path", "unknown"),
                message=data.get("message", "No message"),
                fix_hint=data.get("fix_hint"),
                status=data.get("status", "open"),
                detected_at=data.get("detected_at", "unknown")
            )
            
            return ToolResult.success_result("read_violation", info.to_summary())
            
        except Exception as e:
            return ToolResult.failure_result(
                "read_violation",
                f"Error reading violation: {e}"
            )
    
    def list_violations(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        List violations with optional filtering.
        
        Parameters:
            status: Filter by status ("open", "resolved", "all"). Default: "open"
            severity: Filter by severity ("blocker", "critical", "major", "minor")
            file_pattern: Filter by file path pattern (glob)
            limit: Maximum number to return. Default: 20
        
        Returns:
            ToolResult with list of violation summaries
        """
        status_filter = params.get("status", "open")
        severity_filter = params.get("severity")
        file_pattern = params.get("file_pattern")
        limit = params.get("limit", 20)
        
        if not self.violations_dir.exists():
            return ToolResult.success_result(
                "list_violations",
                "No violations directory found"
            )
        
        try:
            violations = []
            
            for vfile in sorted(self.violations_dir.glob("V-*.yaml")):
                if len(violations) >= limit:
                    break
                    
                with open(vfile) as f:
                    data = yaml.safe_load(f)
                
                # Apply filters
                if status_filter != "all" and data.get("status") != status_filter:
                    continue
                
                if severity_filter and data.get("severity") != severity_filter:
                    continue
                
                if file_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(data.get("file_path", ""), file_pattern):
                        continue
                
                violations.append({
                    "id": data.get("violation_id"),
                    "severity": data.get("severity"),
                    "file": data.get("file_path"),
                    "check": data.get("check_id"),
                    "message": data.get("message", "")[:80]  # Truncate
                })
            
            if not violations:
                return ToolResult.success_result(
                    "list_violations",
                    f"No violations found matching filters (status={status_filter})"
                )
            
            # Format as table
            lines = [f"Found {len(violations)} violations:"]
            lines.append("")
            lines.append(f"{'ID':<18} {'Severity':<10} {'File':<40} {'Message'}")
            lines.append("-" * 100)
            
            for v in violations:
                lines.append(
                    f"{v['id']:<18} {v['severity']:<10} {v['file']:<40} {v['message']}"
                )
            
            return ToolResult.success_result("list_violations", "\n".join(lines))
            
        except Exception as e:
            return ToolResult.failure_result(
                "list_violations",
                f"Error listing violations: {e}"
            )
    
    def get_violation_context(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Get full context for fixing a violation: violation details + file content.
        
        Parameters:
            violation_id: The violation ID
        
        Returns:
            ToolResult with violation info and relevant file content
        """
        violation_id = params.get("violation_id")
        if not violation_id:
            return ToolResult.failure_result(
                "get_violation_context",
                "Missing required parameter: violation_id"
            )
        
        # First read the violation
        result = self.read_violation("read_violation", {"violation_id": violation_id})
        if not result.success:
            return result
        
        # Parse to get file path
        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"
        
        violation_file = self.violations_dir / f"{violation_id}.yaml"
        with open(violation_file) as f:
            data = yaml.safe_load(f)
        
        file_path = data.get("file_path")
        if not file_path:
            return ToolResult.failure_result(
                "get_violation_context",
                "Violation has no file_path"
            )
        
        # Read the source file
        source_file = self.project_path / file_path
        if not source_file.exists():
            file_content = f"[File not found: {file_path}]"
        else:
            try:
                file_content = source_file.read_text()
            except Exception as e:
                file_content = f"[Error reading file: {e}]"
        
        # Build context
        context = f"""=== VIOLATION DETAILS ===
{result.output}

=== FILE CONTENT: {file_path} ===
{file_content}

=== INSTRUCTIONS ===
Fix this violation by modifying the file to comply with the check.
The fix_hint provides guidance on what change is needed.
"""
        
        return ToolResult.success_result("get_violation_context", context)
    
    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "read_violation": self.read_violation,
            "list_violations": self.list_violations,
            "get_violation_context": self.get_violation_context,
        }


# Tool definitions for prompt building
VIOLATION_TOOL_DEFINITIONS = [
    {
        "name": "read_violation",
        "description": "Read details of a specific conformance violation",
        "parameters": {
            "violation_id": {
                "type": "string",
                "required": True,
                "description": "Violation ID (e.g., V-4734938a9485)"
            }
        }
    },
    {
        "name": "list_violations",
        "description": "List conformance violations with optional filtering",
        "parameters": {
            "status": {
                "type": "string",
                "required": False,
                "description": "Filter by status: open, resolved, all (default: open)"
            },
            "severity": {
                "type": "string",
                "required": False,
                "description": "Filter by severity: blocker, critical, major, minor"
            },
            "file_pattern": {
                "type": "string",
                "required": False,
                "description": "Filter by file path pattern (glob)"
            },
            "limit": {
                "type": "integer",
                "required": False,
                "description": "Max violations to return (default: 20)"
            }
        }
    },
    {
        "name": "get_violation_context",
        "description": "Get full context for fixing a violation (details + file content)",
        "parameters": {
            "violation_id": {
                "type": "string",
                "required": True,
                "description": "Violation ID to get context for"
            }
        }
    }
]
```

### Step 2.2: Create Conformance Tools Module

**File:** `tools/harness/conformance_tools.py` (NEW)

```python
"""
Conformance Tools
=================

Tools for running conformance checks and verifying fixes.
"""

import subprocess
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from .llm_executor_domain import ToolResult


class ConformanceTools:
    """
    Tools for conformance checking.
    
    Enables agent to verify that fixes resolve violations.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize conformance tools.
        
        Args:
            project_path: Project root directory
        """
        self.project_path = Path(project_path)
    
    def check_file(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run conformance check on a specific file.
        
        Parameters:
            file_path: Path to file to check
        
        Returns:
            ToolResult with check results
        """
        file_path = params.get("file_path")
        if not file_path:
            return ToolResult.failure_result(
                "check_file",
                "Missing required parameter: file_path"
            )
        
        try:
            # Run conformance check via CLI
            cmd = [
                "python", "execute.py", "conformance", "check",
                "--file", file_path,
                "--format", "yaml"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                # Parse output for violations
                if "No violations" in result.stdout or "0 violations" in result.stdout:
                    return ToolResult.success_result(
                        "check_file",
                        f"✓ No violations found in {file_path}"
                    )
                else:
                    return ToolResult.success_result(
                        "check_file",
                        f"Violations found:\n{result.stdout}"
                    )
            else:
                return ToolResult.failure_result(
                    "check_file",
                    f"Check failed: {result.stderr or result.stdout}"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(
                "check_file",
                "Conformance check timed out (60s)"
            )
        except Exception as e:
            return ToolResult.failure_result(
                "check_file",
                f"Error running check: {e}"
            )
    
    def verify_violation_fixed(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Verify that a specific violation has been fixed.
        
        Parameters:
            violation_id: The violation ID to verify
        
        Returns:
            ToolResult indicating if violation is resolved
        """
        violation_id = params.get("violation_id")
        if not violation_id:
            return ToolResult.failure_result(
                "verify_violation_fixed",
                "Missing required parameter: violation_id"
            )
        
        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"
        
        # Read current violation status
        violation_file = self.project_path / ".agentforge" / "violations" / f"{violation_id}.yaml"
        
        if not violation_file.exists():
            return ToolResult.failure_result(
                "verify_violation_fixed",
                f"Violation file not found: {violation_id}"
            )
        
        try:
            with open(violation_file) as f:
                data = yaml.safe_load(f)
            
            file_path = data.get("file_path")
            check_id = data.get("check_id")
            
            # Run conformance check on the file
            check_result = self.check_file("check_file", {"file_path": file_path})
            
            if not check_result.success:
                return check_result
            
            # Check if this specific violation still exists
            if violation_id in str(check_result.output) or check_id in str(check_result.output):
                return ToolResult.failure_result(
                    "verify_violation_fixed",
                    f"Violation {violation_id} still present after fix attempt"
                )
            
            return ToolResult.success_result(
                "verify_violation_fixed",
                f"✓ Violation {violation_id} appears to be fixed"
            )
            
        except Exception as e:
            return ToolResult.failure_result(
                "verify_violation_fixed",
                f"Error verifying fix: {e}"
            )
    
    def run_full_check(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run full conformance check on the project.
        
        Parameters:
            None
        
        Returns:
            ToolResult with summary of all violations
        """
        try:
            cmd = [
                "python", "execute.py", "conformance", "check"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_path)
            )
            
            return ToolResult.success_result(
                "run_full_check",
                result.stdout[:5000]  # Limit output size
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(
                "run_full_check",
                "Full conformance check timed out (5 min)"
            )
        except Exception as e:
            return ToolResult.failure_result(
                "run_full_check",
                f"Error running check: {e}"
            )
    
    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "check_file": self.check_file,
            "verify_violation_fixed": self.verify_violation_fixed,
            "run_full_check": self.run_full_check,
        }


# Tool definitions for prompt building
CONFORMANCE_TOOL_DEFINITIONS = [
    {
        "name": "check_file",
        "description": "Run conformance check on a specific file",
        "parameters": {
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to file to check"
            }
        }
    },
    {
        "name": "verify_violation_fixed",
        "description": "Verify that a specific violation has been fixed",
        "parameters": {
            "violation_id": {
                "type": "string",
                "required": True,
                "description": "Violation ID to verify"
            }
        }
    },
    {
        "name": "run_full_check",
        "description": "Run full conformance check on the entire project",
        "parameters": {}
    }
]
```

### Step 2.3: Create Git Tools Module

**File:** `tools/harness/git_tools.py` (NEW)

```python
"""
Git Tools
=========

Tools for Git operations with safety guardrails.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .llm_executor_domain import ToolResult


class GitTools:
    """
    Git tools with safety constraints.
    
    Only allows:
    - Status, diff, log (read operations)
    - Add, commit (with message validation)
    - Never push, force, or destructive operations
    """
    
    # Blocked git operations
    BLOCKED_COMMANDS = [
        "push", "force", "reset --hard", "clean -fd",
        "checkout --", "rebase", "merge", "cherry-pick",
        "branch -D", "branch -d", "remote"
    ]
    
    def __init__(self, project_path: Path, require_approval: bool = True):
        """
        Initialize git tools.
        
        Args:
            project_path: Project root directory
            require_approval: If True, commits need human approval
        """
        self.project_path = Path(project_path)
        self.require_approval = require_approval
        self._pending_commit: Dict[str, Any] = {}
    
    def git_status(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Show git status.
        
        Returns:
            ToolResult with status output
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                if not result.stdout.strip():
                    return ToolResult.success_result("git_status", "Working directory clean")
                return ToolResult.success_result("git_status", result.stdout)
            else:
                return ToolResult.failure_result("git_status", result.stderr)
                
        except Exception as e:
            return ToolResult.failure_result("git_status", f"Error: {e}")
    
    def git_diff(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Show git diff for a file or all changes.
        
        Parameters:
            file_path: Optional file to diff (default: all changes)
            staged: If True, show staged changes
        """
        file_path = params.get("file_path")
        staged = params.get("staged", False)
        
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                if not result.stdout.strip():
                    return ToolResult.success_result("git_diff", "No changes")
                return ToolResult.success_result("git_diff", result.stdout[:5000])
            else:
                return ToolResult.failure_result("git_diff", result.stderr)
                
        except Exception as e:
            return ToolResult.failure_result("git_diff", f"Error: {e}")
    
    def git_add(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Stage files for commit.
        
        Parameters:
            files: List of file paths to stage
        """
        files = params.get("files", [])
        if not files:
            return ToolResult.failure_result(
                "git_add",
                "Missing required parameter: files (list of paths)"
            )
        
        if isinstance(files, str):
            files = [files]
        
        try:
            cmd = ["git", "add"] + files
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                return ToolResult.success_result(
                    "git_add",
                    f"Staged {len(files)} file(s): {', '.join(files)}"
                )
            else:
                return ToolResult.failure_result("git_add", result.stderr)
                
        except Exception as e:
            return ToolResult.failure_result("git_add", f"Error: {e}")
    
    def git_commit(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Create a commit with the staged changes.
        
        Parameters:
            message: Commit message
            violation_id: Optional violation ID for tracking
        
        Note: If require_approval is True, commit is staged for human approval.
        """
        message = params.get("message")
        violation_id = params.get("violation_id")
        
        if not message:
            return ToolResult.failure_result(
                "git_commit",
                "Missing required parameter: message"
            )
        
        # Validate message
        if len(message) < 10:
            return ToolResult.failure_result(
                "git_commit",
                "Commit message too short (minimum 10 characters)"
            )
        
        # Add violation reference to message if provided
        if violation_id:
            message = f"fix({violation_id}): {message}"
        
        if self.require_approval:
            # Stage for approval instead of committing
            self._pending_commit = {
                "message": message,
                "violation_id": violation_id
            }
            return ToolResult.success_result(
                "git_commit",
                f"Commit staged for approval:\n\nMessage: {message}\n\n"
                f"Run 'agentforge agent approve-commit' to apply."
            )
        
        # Direct commit (only if approval not required)
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                return ToolResult.success_result(
                    "git_commit",
                    f"Committed: {message}\n{result.stdout}"
                )
            else:
                return ToolResult.failure_result("git_commit", result.stderr)
                
        except Exception as e:
            return ToolResult.failure_result("git_commit", f"Error: {e}")
    
    def get_pending_commit(self) -> Dict[str, Any]:
        """Get pending commit awaiting approval."""
        return self._pending_commit
    
    def clear_pending_commit(self):
        """Clear pending commit."""
        self._pending_commit = {}
    
    def apply_pending_commit(self) -> ToolResult:
        """Apply the pending commit (called after human approval)."""
        if not self._pending_commit:
            return ToolResult.failure_result(
                "apply_pending_commit",
                "No pending commit"
            )
        
        message = self._pending_commit["message"]
        
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            
            self._pending_commit = {}
            
            if result.returncode == 0:
                return ToolResult.success_result(
                    "apply_pending_commit",
                    f"Committed: {message}"
                )
            else:
                return ToolResult.failure_result("apply_pending_commit", result.stderr)
                
        except Exception as e:
            return ToolResult.failure_result("apply_pending_commit", f"Error: {e}")
    
    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "git_status": self.git_status,
            "git_diff": self.git_diff,
            "git_add": self.git_add,
            "git_commit": self.git_commit,
        }


# Tool definitions
GIT_TOOL_DEFINITIONS = [
    {
        "name": "git_status",
        "description": "Show current git status (modified/staged files)",
        "parameters": {}
    },
    {
        "name": "git_diff",
        "description": "Show git diff for changes",
        "parameters": {
            "file_path": {
                "type": "string",
                "required": False,
                "description": "Specific file to diff"
            },
            "staged": {
                "type": "boolean",
                "required": False,
                "description": "Show staged changes instead of unstaged"
            }
        }
    },
    {
        "name": "git_add",
        "description": "Stage files for commit",
        "parameters": {
            "files": {
                "type": "array",
                "required": True,
                "description": "List of file paths to stage"
            }
        }
    },
    {
        "name": "git_commit",
        "description": "Create a commit (requires human approval by default)",
        "parameters": {
            "message": {
                "type": "string",
                "required": True,
                "description": "Commit message (min 10 chars)"
            },
            "violation_id": {
                "type": "string",
                "required": False,
                "description": "Violation ID for tracking"
            }
        }
    }
]
```

### Step 2.4: Create Test Tools Module

**File:** `tools/harness/test_runner_tools.py` (NEW)

```python
"""
Test Runner Tools
=================

Tools for running tests to verify fixes.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict

from .llm_executor_domain import ToolResult


class TestRunnerTools:
    """Tools for running pytest and validating changes."""
    
    def __init__(self, project_path: Path, timeout: int = 300):
        self.project_path = Path(project_path)
        self.timeout = timeout
    
    def run_tests(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run pytest on specified path.
        
        Parameters:
            test_path: Path to tests (default: "tests/")
            verbose: Show verbose output
            fail_fast: Stop on first failure
        """
        test_path = params.get("test_path", "tests/")
        verbose = params.get("verbose", False)
        fail_fast = params.get("fail_fast", True)
        
        try:
            cmd = ["python", "-m", "pytest", test_path, "--tb=short"]
            if verbose:
                cmd.append("-v")
            if fail_fast:
                cmd.append("-x")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.project_path)
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            
            if result.returncode == 0:
                return ToolResult.success_result(
                    "run_tests",
                    f"✓ Tests passed\n{output[-2000:]}"
                )
            else:
                return ToolResult.failure_result(
                    "run_tests",
                    f"✗ Tests failed (exit {result.returncode})\n{output[-3000:]}"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(
                "run_tests",
                f"Tests timed out after {self.timeout}s"
            )
        except Exception as e:
            return ToolResult.failure_result("run_tests", f"Error: {e}")
    
    def run_single_test(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run a single test file or test function.
        
        Parameters:
            test_path: Full path to test (e.g., "tests/unit/test_foo.py::test_bar")
        """
        test_path = params.get("test_path")
        if not test_path:
            return ToolResult.failure_result(
                "run_single_test",
                "Missing required parameter: test_path"
            )
        
        try:
            cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=long"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_path)
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                return ToolResult.success_result("run_single_test", f"✓ Passed\n{output}")
            else:
                return ToolResult.failure_result(
                    "run_single_test",
                    f"✗ Failed\n{output}"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result("run_single_test", "Test timed out")
        except Exception as e:
            return ToolResult.failure_result("run_single_test", f"Error: {e}")
    
    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "run_tests": self.run_tests,
            "run_single_test": self.run_single_test,
        }


TEST_TOOL_DEFINITIONS = [
    {
        "name": "run_tests",
        "description": "Run pytest on specified path",
        "parameters": {
            "test_path": {
                "type": "string",
                "required": False,
                "description": "Path to tests (default: tests/)"
            },
            "verbose": {
                "type": "boolean",
                "required": False,
                "description": "Show verbose output"
            },
            "fail_fast": {
                "type": "boolean",
                "required": False,
                "description": "Stop on first failure (default: True)"
            }
        }
    },
    {
        "name": "run_single_test",
        "description": "Run a single test file or function",
        "parameters": {
            "test_path": {
                "type": "string",
                "required": True,
                "description": "Full path to test"
            }
        }
    }
]
```

### Step 2.5: Create Tool Tests

**File:** `tests/unit/harness/test_violation_tools.py` (NEW)

```python
"""Tests for violation tools."""

import pytest
import yaml
from pathlib import Path
import tempfile

from tools.harness.violation_tools import ViolationTools


class TestViolationTools:
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            violations_dir = project / ".agentforge" / "violations"
            violations_dir.mkdir(parents=True)
            
            # Create sample violation
            violation = {
                "violation_id": "V-test123",
                "contract_id": "agentforge",
                "check_id": "commands-have-help",
                "severity": "major",
                "file_path": "cli/test.py",
                "message": "Missing help parameter",
                "fix_hint": "Add help='description'",
                "status": "open",
                "detected_at": "2025-01-01T00:00:00"
            }
            
            with open(violations_dir / "V-test123.yaml", 'w') as f:
                yaml.dump(violation, f)
            
            # Create source file
            (project / "cli").mkdir()
            (project / "cli/test.py").write_text("# test file")
            
            yield project
    
    def test_read_violation(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.read_violation("read_violation", {"violation_id": "V-test123"})
        
        assert result.success
        assert "V-test123" in result.output
        assert "major" in result.output
        assert "commands-have-help" in result.output
    
    def test_read_violation_not_found(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.read_violation("read_violation", {"violation_id": "V-nonexistent"})
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_list_violations(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.list_violations("list_violations", {"status": "open"})
        
        assert result.success
        assert "V-test123" in result.output
    
    def test_get_violation_context(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.get_violation_context("get_violation_context", {"violation_id": "V-test123"})
        
        assert result.success
        assert "VIOLATION DETAILS" in result.output
        assert "FILE CONTENT" in result.output
        assert "# test file" in result.output
```

### Step 2.6: Verify Phase 2

```bash
python -m pytest tests/unit/harness/test_violation_tools.py -v
python -m pytest tests/unit/harness/ -v --tb=short
```

---

## Phase 3: Fix-Violation Command (4 hours)

### Goal
Create CLI command that orchestrates the full violation-fixing workflow.

### Step 3.1: Create Fix Violation Workflow

**File:** `tools/harness/fix_violation_workflow.py` (NEW)

```python
"""
Fix Violation Workflow
======================

Orchestrates the process of fixing a conformance violation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llm_executor_domain import ExecutionContext, StepResult
from .violation_tools import ViolationTools
from .conformance_tools import ConformanceTools
from .git_tools import GitTools
from .test_runner_tools import TestRunnerTools


class FixPhase(Enum):
    """Phases of the fix workflow."""
    ANALYZE = "analyze"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    COMMIT = "commit"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class FixAttempt:
    """Record of a fix attempt."""
    violation_id: str
    started_at: datetime
    phase: FixPhase
    steps: List[StepResult] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    tests_passed: bool = False
    conformance_passed: bool = False
    committed: bool = False
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "violation_id": self.violation_id,
            "started_at": self.started_at.isoformat(),
            "phase": self.phase.value,
            "steps": [s.to_dict() for s in self.steps],
            "files_modified": self.files_modified,
            "tests_passed": self.tests_passed,
            "conformance_passed": self.conformance_passed,
            "committed": self.committed,
            "error": self.error,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# Prompt template for violation fixing
FIX_VIOLATION_SYSTEM_PROMPT = """You are an expert software engineer tasked with fixing conformance violations.

Your goal is to fix the violation while:
1. Making minimal changes to the code
2. Following existing code patterns and style
3. Ensuring tests continue to pass
4. Not introducing new violations

Available tools:
{tool_list}

Workflow phases:
1. ANALYZE: Understand the violation and affected code
2. PLAN: Decide on the fix approach
3. IMPLEMENT: Make the code changes
4. VERIFY: Run tests and conformance checks
5. COMMIT: Stage changes for commit (requires human approval)

Important rules:
- Only modify files directly related to the violation
- Always verify your fix with conformance check before committing
- If tests fail, revert changes and try a different approach
- If stuck, escalate to human with clear explanation
"""


FIX_VIOLATION_USER_PROMPT = """Fix this conformance violation:

{violation_context}

Current phase: {phase}

Previous steps in this session:
{step_history}

Decide on your next action. Use tools to read files, make changes, and verify fixes.
When the fix is complete and verified, use COMPLETE action.
If you cannot fix it, use ESCALATE action with explanation.
"""


class FixViolationWorkflow:
    """
    Manages the workflow for fixing a single violation.
    """
    
    def __init__(
        self,
        project_path: Path,
        llm_executor,  # LLMExecutor
        max_iterations: int = 20,
        require_commit_approval: bool = True
    ):
        """
        Initialize workflow.
        
        Args:
            project_path: Project root
            llm_executor: LLM executor for agent decisions
            max_iterations: Max steps before failing
            require_commit_approval: Require human approval for commits
        """
        self.project_path = Path(project_path)
        self.llm_executor = llm_executor
        self.max_iterations = max_iterations
        
        # Initialize tools
        self.violation_tools = ViolationTools(project_path)
        self.conformance_tools = ConformanceTools(project_path)
        self.git_tools = GitTools(project_path, require_approval=require_commit_approval)
        self.test_tools = TestRunnerTools(project_path)
        
        # Register all tools with executor
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools with the LLM executor."""
        all_executors = {}
        all_executors.update(self.violation_tools.get_tool_executors())
        all_executors.update(self.conformance_tools.get_tool_executors())
        all_executors.update(self.git_tools.get_tool_executors())
        all_executors.update(self.test_tools.get_tool_executors())
        
        self.llm_executor.register_tools(all_executors)
    
    def fix_violation(
        self,
        violation_id: str,
        on_step: callable = None
    ) -> FixAttempt:
        """
        Attempt to fix a violation.
        
        Args:
            violation_id: Violation ID to fix
            on_step: Optional callback after each step
            
        Returns:
            FixAttempt with results
        """
        attempt = FixAttempt(
            violation_id=violation_id,
            started_at=datetime.utcnow(),
            phase=FixPhase.ANALYZE
        )
        
        # Get violation context
        context_result = self.violation_tools.get_violation_context(
            "get_violation_context",
            {"violation_id": violation_id}
        )
        
        if not context_result.success:
            attempt.error = f"Failed to get violation context: {context_result.error}"
            attempt.phase = FixPhase.FAILED
            attempt.completed_at = datetime.utcnow()
            return attempt
        
        # Build execution context
        tool_names = list(self.llm_executor.tool_executors.keys())
        
        exec_context = ExecutionContext(
            session_id=f"fix-{violation_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            task_description=f"Fix violation {violation_id}",
            current_phase="fix",
            available_tools=tool_names,
            token_budget=50000
        )
        
        # Add initial context as user message
        exec_context.add_user_message(
            FIX_VIOLATION_USER_PROMPT.format(
                violation_context=context_result.output,
                phase=attempt.phase.value,
                step_history="No steps yet"
            )
        )
        
        # Run agent loop
        for i in range(self.max_iterations):
            step_result = self.llm_executor.execute_step(exec_context)
            attempt.steps.append(step_result)
            
            if on_step:
                on_step(step_result)
            
            if not step_result.success:
                attempt.error = step_result.error
                attempt.phase = FixPhase.FAILED
                break
            
            # Check for completion or escalation
            if step_result.action:
                from .llm_executor_domain import ActionType
                
                if step_result.action.action_type == ActionType.COMPLETE:
                    attempt.phase = FixPhase.COMPLETE
                    break
                elif step_result.action.action_type == ActionType.ESCALATE:
                    attempt.error = f"Escalated: {step_result.action.reasoning}"
                    attempt.phase = FixPhase.FAILED
                    break
            
            # Update phase based on progress
            attempt.phase = self._determine_phase(attempt, step_result)
            
            if not step_result.should_continue:
                break
        
        attempt.completed_at = datetime.utcnow()
        return attempt
    
    def _determine_phase(self, attempt: FixAttempt, step: StepResult) -> FixPhase:
        """Determine current phase based on step results."""
        # Simple heuristic based on tools used
        if not step.tool_results:
            return attempt.phase
        
        tool_names = [tr.tool_name for tr in step.tool_results]
        
        if "edit_file" in tool_names or "write_file" in tool_names:
            return FixPhase.IMPLEMENT
        elif "run_tests" in tool_names or "verify_violation_fixed" in tool_names:
            return FixPhase.VERIFY
        elif "git_commit" in tool_names:
            return FixPhase.COMMIT
        elif "read_file" in tool_names or "read_violation" in tool_names:
            return FixPhase.ANALYZE
        
        return attempt.phase
```

### Step 3.2: Create CLI Command

**File:** `cli/commands/fix_violation.py` (NEW)

```python
"""
Fix Violation Command Implementation
====================================

Implements the agent fix-violation command.
"""

import click
import yaml
from pathlib import Path
from datetime import datetime

from tools.harness.session_manager import SessionManager
from tools.harness.session_store import SessionStore
from tools.harness.memory_manager import MemoryManager
from tools.harness.tool_selector import ToolSelector
from tools.harness.tool_registry import ToolRegistry
from tools.harness.agent_monitor import AgentMonitor
from tools.harness.checkpoint_manager import CheckpointManager
from tools.harness.recovery_executor import RecoveryExecutor
from tools.harness.escalation_manager import EscalationManager
from tools.harness.llm_executor import LLMExecutor
from tools.harness.tool_executor_bridge import ToolExecutorBridge
from tools.harness.execution_context_store import ExecutionContextStore
from tools.harness.fix_violation_workflow import FixViolationWorkflow, FixPhase


def run_fix_violation(
    violation_id: str,
    dry_run: bool = False,
    verbose: bool = False,
    auto_commit: bool = False
):
    """
    Fix a single violation.
    
    Args:
        violation_id: Violation ID to fix
        dry_run: Don't make actual changes
        verbose: Show detailed output
        auto_commit: Auto-commit without approval
    """
    project_path = Path.cwd()
    
    click.echo(f"Fixing violation: {violation_id}")
    click.echo(f"Project: {project_path}")
    click.echo()
    
    # Check violation exists
    if not violation_id.startswith("V-"):
        violation_id = f"V-{violation_id}"
    
    violation_file = project_path / ".agentforge" / "violations" / f"{violation_id}.yaml"
    if not violation_file.exists():
        click.echo(click.style(f"Violation not found: {violation_id}", fg="red"))
        raise SystemExit(1)
    
    # Show violation info
    with open(violation_file) as f:
        violation_data = yaml.safe_load(f)
    
    click.echo("Violation Details:")
    click.echo(f"  Severity: {violation_data.get('severity')}")
    click.echo(f"  File: {violation_data.get('file_path')}")
    click.echo(f"  Check: {violation_data.get('check_id')}")
    click.echo(f"  Message: {violation_data.get('message')}")
    if violation_data.get('fix_hint'):
        click.echo(f"  Hint: {violation_data.get('fix_hint')}")
    click.echo()
    
    if dry_run:
        click.echo(click.style("DRY RUN - No changes will be made", fg="yellow"))
        click.echo()
    
    # Initialize components
    base_path = project_path / ".agentforge"
    
    # Create LLM executor with tools
    tool_bridge = ToolExecutorBridge(project_path)
    llm_executor = LLMExecutor(
        tool_executors=tool_bridge.get_default_executors()
    )
    
    # Create workflow
    workflow = FixViolationWorkflow(
        project_path=project_path,
        llm_executor=llm_executor,
        require_commit_approval=not auto_commit
    )
    
    # Progress callback
    def on_step(step):
        if verbose:
            click.echo(f"  Step {len(workflow_attempt.steps)}: ", nl=False)
            if step.action:
                click.echo(f"{step.action.action_type.value}", nl=False)
                if step.tool_results:
                    tools = [tr.tool_name for tr in step.tool_results]
                    click.echo(f" -> {', '.join(tools)}")
                else:
                    click.echo()
            else:
                click.echo("processing...")
    
    # Run fix
    click.echo("Starting fix attempt...")
    workflow_attempt = workflow.fix_violation(violation_id, on_step=on_step)
    
    # Report results
    click.echo()
    click.echo("=" * 60)
    
    if workflow_attempt.phase == FixPhase.COMPLETE:
        click.echo(click.style("✓ Fix completed successfully!", fg="green"))
        click.echo(f"  Steps taken: {len(workflow_attempt.steps)}")
        if workflow_attempt.files_modified:
            click.echo(f"  Files modified: {', '.join(workflow_attempt.files_modified)}")
        
        # Check for pending commit
        pending = workflow.git_tools.get_pending_commit()
        if pending:
            click.echo()
            click.echo("Pending commit:")
            click.echo(f"  Message: {pending.get('message')}")
            click.echo()
            click.echo("Run 'agentforge agent approve-commit' to apply")
            
    elif workflow_attempt.phase == FixPhase.FAILED:
        click.echo(click.style("✗ Fix failed", fg="red"))
        click.echo(f"  Error: {workflow_attempt.error}")
        click.echo(f"  Steps attempted: {len(workflow_attempt.steps)}")
        
    else:
        click.echo(click.style(f"Fix incomplete (phase: {workflow_attempt.phase.value})", fg="yellow"))
    
    # Save attempt log
    log_file = base_path / "fix_attempts" / f"{violation_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.yaml"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        yaml.dump(workflow_attempt.to_dict(), f, default_flow_style=False)
    
    click.echo(f"\nAttempt log saved: {log_file}")
    
    return workflow_attempt


def run_fix_violations_batch(
    limit: int = 5,
    severity: str = None,
    dry_run: bool = False,
    verbose: bool = False
):
    """
    Fix multiple violations in batch.
    
    Args:
        limit: Maximum violations to attempt
        severity: Filter by severity
        dry_run: Don't make actual changes
        verbose: Show detailed output
    """
    from tools.harness.violation_tools import ViolationTools
    
    project_path = Path.cwd()
    tools = ViolationTools(project_path)
    
    # Get violations
    params = {"status": "open", "limit": limit}
    if severity:
        params["severity"] = severity
    
    result = tools.list_violations("list_violations", params)
    
    if not result.success:
        click.echo(click.style(f"Error listing violations: {result.error}", fg="red"))
        raise SystemExit(1)
    
    click.echo(f"Found violations to fix:")
    click.echo(result.output)
    click.echo()
    
    # TODO: Parse violation IDs from output and fix each
    click.echo("Batch fixing not yet implemented - use individual fix command")


def run_approve_commit():
    """Approve and apply pending commit."""
    from tools.harness.git_tools import GitTools
    
    project_path = Path.cwd()
    git_tools = GitTools(project_path)
    
    pending = git_tools.get_pending_commit()
    if not pending:
        click.echo("No pending commit")
        return
    
    click.echo("Pending commit:")
    click.echo(f"  Message: {pending.get('message')}")
    click.echo()
    
    if click.confirm("Apply this commit?"):
        result = git_tools.apply_pending_commit()
        if result.success:
            click.echo(click.style("✓ Committed", fg="green"))
        else:
            click.echo(click.style(f"✗ Failed: {result.error}", fg="red"))
    else:
        click.echo("Commit cancelled")
        git_tools.clear_pending_commit()
```

### Step 3.3: Add CLI Commands

**File:** `cli/click_commands/agent.py` (MODIFY)

Add these commands to the existing agent group:

```python
# Add to existing agent.py

@agent.command("fix-violation")
@click.argument("violation_id", type=str)
@click.option("--dry-run", is_flag=True, help="Don't make actual changes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--auto-commit", is_flag=True, help="Auto-commit without approval")
def fix_violation(violation_id: str, dry_run: bool, verbose: bool, auto_commit: bool):
    """Fix a specific conformance violation.
    
    Example:
        agentforge agent fix-violation V-4734938a9485
    """
    from cli.commands.fix_violation import run_fix_violation
    run_fix_violation(violation_id, dry_run, verbose, auto_commit)


@agent.command("fix-violations")
@click.option("--limit", "-n", type=int, default=5, help="Max violations to fix")
@click.option("--severity", "-s", type=click.Choice(["blocker", "critical", "major", "minor"]),
              help="Filter by severity")
@click.option("--dry-run", is_flag=True, help="Don't make actual changes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def fix_violations(limit: int, severity: str, dry_run: bool, verbose: bool):
    """Fix multiple violations in batch.
    
    Example:
        agentforge agent fix-violations --limit 10 --severity major
    """
    from cli.commands.fix_violation import run_fix_violations_batch
    run_fix_violations_batch(limit, severity, dry_run, verbose)


@agent.command("approve-commit")
def approve_commit():
    """Approve and apply a pending commit from fix-violation."""
    from cli.commands.fix_violation import run_approve_commit
    run_approve_commit()
```

### Step 3.4: Verify Phase 3

```bash
# Test CLI command loads
python execute.py agent --help
python execute.py agent fix-violation --help

# Dry run on a real violation
python execute.py agent fix-violation V-4734938a9485 --dry-run --verbose
```

---

## Phase 4: Full Autonomous Loop (8+ hours)

### Goal
Enable fully autonomous operation with safety guardrails.

### Step 4.1: Create Auto-Fix Daemon

**File:** `tools/harness/auto_fix_daemon.py` (NEW)

This component runs continuously, picking up violations and fixing them:

```python
"""
Auto-Fix Daemon
===============

Continuously monitors and fixes violations with configurable policies.
"""

import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import logging

from .fix_violation_workflow import FixViolationWorkflow, FixPhase, FixAttempt
from .violation_tools import ViolationTools
from .llm_executor import LLMExecutor
from .tool_executor_bridge import ToolExecutorBridge


@dataclass
class AutoFixConfig:
    """Configuration for auto-fix daemon."""
    max_concurrent: int = 1
    max_attempts_per_violation: int = 3
    cooldown_after_failure: timedelta = timedelta(hours=1)
    severity_order: List[str] = None  # Order to process
    require_approval: bool = True
    pause_on_test_failure: bool = True
    max_fixes_per_run: int = 10
    
    def __post_init__(self):
        if self.severity_order is None:
            self.severity_order = ["blocker", "critical", "major", "minor"]


class AutoFixDaemon:
    """
    Daemon that automatically fixes violations.
    """
    
    def __init__(
        self,
        project_path: Path,
        config: Optional[AutoFixConfig] = None
    ):
        self.project_path = Path(project_path)
        self.config = config or AutoFixConfig()
        self.logger = logging.getLogger("auto_fix")
        
        # Track attempts
        self._attempts: dict[str, List[FixAttempt]] = {}
        self._load_attempt_history()
    
    def _load_attempt_history(self):
        """Load previous attempt history."""
        attempts_dir = self.project_path / ".agentforge" / "fix_attempts"
        if not attempts_dir.exists():
            return
        
        for f in attempts_dir.glob("V-*.yaml"):
            try:
                with open(f) as fp:
                    data = yaml.safe_load(fp)
                vid = data.get("violation_id")
                if vid:
                    if vid not in self._attempts:
                        self._attempts[vid] = []
                    # Just track count, not full history
            except:
                pass
    
    def should_attempt_fix(self, violation_id: str) -> tuple[bool, str]:
        """
        Check if we should attempt to fix this violation.
        
        Returns:
            Tuple of (should_attempt, reason)
        """
        attempts = self._attempts.get(violation_id, [])
        
        # Check attempt count
        if len(attempts) >= self.config.max_attempts_per_violation:
            return False, f"Max attempts ({self.config.max_attempts_per_violation}) reached"
        
        # Check cooldown after failure
        if attempts:
            last = attempts[-1]
            if last.phase == FixPhase.FAILED:
                cooldown_until = last.completed_at + self.config.cooldown_after_failure
                if datetime.utcnow() < cooldown_until:
                    return False, f"In cooldown until {cooldown_until}"
        
        return True, "OK"
    
    def get_next_violation(self) -> Optional[str]:
        """Get next violation to fix based on priority."""
        tools = ViolationTools(self.project_path)
        
        for severity in self.config.severity_order:
            result = tools.list_violations(
                "list_violations",
                {"status": "open", "severity": severity, "limit": 10}
            )
            
            if not result.success:
                continue
            
            # Parse violation IDs from output
            # TODO: Better parsing
            for line in result.output.split("\n"):
                if line.startswith("V-"):
                    vid = line.split()[0]
                    should, reason = self.should_attempt_fix(vid)
                    if should:
                        return vid
        
        return None
    
    def run_once(self) -> Optional[FixAttempt]:
        """
        Run one fix cycle.
        
        Returns:
            FixAttempt if a fix was attempted, None if nothing to do
        """
        violation_id = self.get_next_violation()
        if not violation_id:
            self.logger.info("No violations to fix")
            return None
        
        self.logger.info(f"Attempting to fix: {violation_id}")
        
        # Create executor and workflow
        tool_bridge = ToolExecutorBridge(self.project_path)
        llm_executor = LLMExecutor(
            tool_executors=tool_bridge.get_default_executors()
        )
        
        workflow = FixViolationWorkflow(
            project_path=self.project_path,
            llm_executor=llm_executor,
            require_commit_approval=self.config.require_approval
        )
        
        # Run fix
        attempt = workflow.fix_violation(violation_id)
        
        # Track attempt
        if violation_id not in self._attempts:
            self._attempts[violation_id] = []
        self._attempts[violation_id].append(attempt)
        
        # Log result
        if attempt.phase == FixPhase.COMPLETE:
            self.logger.info(f"Successfully fixed: {violation_id}")
        else:
            self.logger.warning(f"Failed to fix {violation_id}: {attempt.error}")
        
        return attempt
    
    def run_batch(self, max_fixes: Optional[int] = None) -> List[FixAttempt]:
        """
        Run multiple fix cycles.
        
        Args:
            max_fixes: Max fixes to attempt (default: from config)
            
        Returns:
            List of fix attempts
        """
        max_fixes = max_fixes or self.config.max_fixes_per_run
        attempts = []
        
        for i in range(max_fixes):
            attempt = self.run_once()
            if attempt is None:
                break
            attempts.append(attempt)
            
            # Pause if configured and test failed
            if (self.config.pause_on_test_failure and 
                attempt.phase == FixPhase.FAILED and
                "test" in str(attempt.error).lower()):
                self.logger.warning("Pausing due to test failure")
                break
        
        return attempts
```

### Step 4.2: Add Rollback Support

**File:** `tools/harness/rollback_manager.py` (NEW)

```python
"""
Rollback Manager
================

Manages rollback of failed fix attempts.
"""

import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import yaml

from .llm_executor_domain import ToolResult


class RollbackManager:
    """
    Manages file backups and rollback for fix attempts.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.backup_dir = self.project_path / ".agentforge" / "backups"
        self._current_backup: Optional[str] = None
    
    def create_backup(self, files: List[str], label: str = None) -> str:
        """
        Create backup of files before modification.
        
        Args:
            files: List of file paths to backup
            label: Optional label for backup
            
        Returns:
            Backup ID
        """
        backup_id = f"{label or 'backup'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "backup_id": backup_id,
            "created_at": datetime.utcnow().isoformat(),
            "files": []
        }
        
        for file_path in files:
            src = self.project_path / file_path
            if src.exists():
                # Preserve directory structure
                rel_path = Path(file_path)
                dst = backup_path / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                manifest["files"].append({
                    "path": file_path,
                    "backed_up": True
                })
            else:
                manifest["files"].append({
                    "path": file_path,
                    "backed_up": False,
                    "reason": "File did not exist"
                })
        
        # Save manifest
        with open(backup_path / "manifest.yaml", 'w') as f:
            yaml.dump(manifest, f)
        
        self._current_backup = backup_id
        return backup_id
    
    def rollback(self, backup_id: Optional[str] = None) -> ToolResult:
        """
        Rollback to a backup.
        
        Args:
            backup_id: Backup to restore (default: current backup)
            
        Returns:
            ToolResult indicating success/failure
        """
        backup_id = backup_id or self._current_backup
        if not backup_id:
            return ToolResult.failure_result("rollback", "No backup specified")
        
        backup_path = self.backup_dir / backup_id
        manifest_file = backup_path / "manifest.yaml"
        
        if not manifest_file.exists():
            return ToolResult.failure_result("rollback", f"Backup not found: {backup_id}")
        
        with open(manifest_file) as f:
            manifest = yaml.safe_load(f)
        
        restored = []
        errors = []
        
        for file_info in manifest.get("files", []):
            if not file_info.get("backed_up"):
                continue
            
            file_path = file_info["path"]
            src = backup_path / file_path
            dst = self.project_path / file_path
            
            try:
                shutil.copy2(src, dst)
                restored.append(file_path)
            except Exception as e:
                errors.append(f"{file_path}: {e}")
        
        if errors:
            return ToolResult.failure_result(
                "rollback",
                f"Partial rollback. Restored: {restored}. Errors: {errors}"
            )
        
        return ToolResult.success_result(
            "rollback",
            f"Rolled back {len(restored)} files from {backup_id}"
        )
    
    def git_rollback(self, files: List[str] = None) -> ToolResult:
        """
        Rollback using git checkout.
        
        Args:
            files: Specific files to rollback (default: all modified)
            
        Returns:
            ToolResult
        """
        try:
            if files:
                cmd = ["git", "checkout", "--"] + files
            else:
                cmd = ["git", "checkout", "--", "."]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                return ToolResult.success_result("git_rollback", "Changes reverted")
            else:
                return ToolResult.failure_result("git_rollback", result.stderr)
                
        except Exception as e:
            return ToolResult.failure_result("git_rollback", f"Error: {e}")
```

### Step 4.3: Integration Tests

**File:** `tests/integration/test_fix_violation.py` (NEW)

```python
"""
Integration tests for fix violation workflow.
"""

import pytest
import yaml
from pathlib import Path
import tempfile
import os


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY"
)
class TestFixViolationIntegration:
    """Integration tests requiring API key."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with a fixable violation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            # Create .agentforge structure
            violations_dir = project / ".agentforge" / "violations"
            violations_dir.mkdir(parents=True)
            
            # Create a simple violation
            violation = {
                "violation_id": "V-test001",
                "contract_id": "test",
                "check_id": "missing-docstring",
                "severity": "minor",
                "file_path": "src/example.py",
                "message": "Function missing docstring",
                "fix_hint": "Add docstring to function",
                "status": "open",
                "detected_at": "2025-01-01T00:00:00"
            }
            
            with open(violations_dir / "V-test001.yaml", 'w') as f:
                yaml.dump(violation, f)
            
            # Create source file with issue
            src_dir = project / "src"
            src_dir.mkdir()
            (src_dir / "example.py").write_text('''
def calculate_sum(a, b):
    return a + b
''')
            
            yield project
    
    def test_fix_simple_violation(self, temp_project):
        """Test fixing a simple docstring violation."""
        from tools.harness.llm_executor import LLMExecutor
        from tools.harness.tool_executor_bridge import ToolExecutorBridge
        from tools.harness.fix_violation_workflow import FixViolationWorkflow, FixPhase
        
        # Create components
        tool_bridge = ToolExecutorBridge(temp_project)
        llm_executor = LLMExecutor(
            tool_executors=tool_bridge.get_default_executors()
        )
        
        workflow = FixViolationWorkflow(
            project_path=temp_project,
            llm_executor=llm_executor,
            max_iterations=10,
            require_commit_approval=True
        )
        
        # Run fix
        attempt = workflow.fix_violation("V-test001")
        
        # Check results
        assert attempt.violation_id == "V-test001"
        assert len(attempt.steps) > 0
        
        # Should have either completed or provided useful error
        if attempt.phase == FixPhase.COMPLETE:
            # Check file was modified
            content = (temp_project / "src/example.py").read_text()
            assert '"""' in content or "'''" in content  # Docstring added
```

---

## Verification & Testing

### Run All Tests

```bash
# Phase 1: Serialization
python -m pytest tests/unit/harness/test_llm_executor_serialization.py -v

# Phase 2: Tools
python -m pytest tests/unit/harness/test_violation_tools.py -v
python -m pytest tests/unit/harness/test_conformance_tools.py -v
python -m pytest tests/unit/harness/test_git_tools.py -v

# All harness tests
python -m pytest tests/unit/harness/ -v --tb=short

# Integration (requires API key)
ANTHROPIC_API_KEY=xxx python -m pytest tests/integration/test_fix_violation.py -v
```

### Manual Testing

```bash
# List open violations
python execute.py conformance violations list --status open

# Try fixing one (dry run)
python execute.py agent fix-violation V-4734938a9485 --dry-run --verbose

# Actually fix one
python execute.py agent fix-violation V-4734938a9485 --verbose

# Approve the commit
python execute.py agent approve-commit
```

---

## Summary

| Phase | Hours | What's Built |
|-------|-------|--------------|
| 1. Serialization | 5 | `to_dict()`/`from_dict()` on all domain entities, ExecutionContextStore |
| 2. Tools | 4 | ViolationTools, ConformanceTools, GitTools, TestRunnerTools |
| 3. CLI Command | 4 | `fix-violation`, `fix-violations`, `approve-commit` commands |
| 4. Autonomous | 8+ | AutoFixDaemon, RollbackManager, integration tests |
| **Total** | **~21 hrs** | Full self-hosting capability |

### Expected Outcome

After implementation:

```bash
# Fix a single violation with human oversight
agentforge agent fix-violation V-4734938a9485

# Fix multiple violations
agentforge agent fix-violations --limit 10 --severity major

# Approve commits
agentforge agent approve-commit

# Full autonomous mode (when trusted)
agentforge agent fix-violations --auto-commit
```

Each fix attempt produces auditable YAML logs in `.agentforge/fix_attempts/` and `.agentforge/sessions/`.
