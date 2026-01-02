# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: core-harness-llm_executor_domain
# @test_path: tests/unit/harness/test_action_parser.py

"""
LLM Executor Domain Model
=========================

Domain entities for the Agent Harness LLM Executor.
Defines the structures for agent actions, tool calls, and execution context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ActionType(Enum):
    """Types of actions an agent can take."""

    TOOL_CALL = "tool_call"  # Execute a tool
    THINK = "think"  # Internal reasoning (no external effect)
    RESPOND = "respond"  # Final response to user
    ASK_USER = "ask_user"  # Request user input
    COMPLETE = "complete"  # Mark task as complete
    ESCALATE = "escalate"  # Escalate to human


class ToolCategory(Enum):
    """Categories of tools available to agents."""

    FILE = "file"  # File operations (read, write, edit)
    SEARCH = "search"  # Code search and exploration
    SHELL = "shell"  # Shell command execution
    TEST = "test"  # Test running
    GIT = "git"  # Git operations
    ANALYSIS = "analysis"  # Code analysis
    MEMORY = "memory"  # Memory operations


@dataclass
class ToolCall:
    """A request to execute a specific tool."""

    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    category: ToolCategory | None = None

    def __post_init__(self):
        """Infer category from tool name if not provided."""
        if self.category is None:
            self.category = self._infer_category()

    def _infer_category(self) -> ToolCategory:
        """Infer tool category from name."""
        name_lower = self.name.lower()

        if any(x in name_lower for x in ["read", "write", "edit", "file"]):
            return ToolCategory.FILE
        if any(x in name_lower for x in ["grep", "glob", "search", "find"]):
            return ToolCategory.SEARCH
        if any(x in name_lower for x in ["bash", "shell", "command"]):
            return ToolCategory.SHELL
        if any(x in name_lower for x in ["test", "pytest"]):
            return ToolCategory.TEST
        if any(x in name_lower for x in ["git", "commit", "push"]):
            return ToolCategory.GIT
        if any(x in name_lower for x in ["analyze", "lint", "check"]):
            return ToolCategory.ANALYSIS
        if any(x in name_lower for x in ["memory", "remember", "recall"]):
            return ToolCategory.MEMORY

        return ToolCategory.SHELL  # Default

    def to_dict(self) -> dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "name": self.name,
            "parameters": self.parameters,
            "category": self.category.value if self.category else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCall":
        """Deserialize from dict."""
        category = ToolCategory(data["category"]) if data.get("category") else None
        return cls(
            name=data["name"],
            parameters=data.get("parameters", {}),
            category=category
        )


@dataclass
class ToolResult:
    """Result of executing a tool."""

    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0

    @classmethod
    def success_result(cls, tool_name: str, output: Any, duration: float = 0.0) -> "ToolResult":
        """Create a successful result."""
        return cls(
            tool_name=tool_name,
            success=True,
            output=output,
            duration_seconds=duration,
        )

    @classmethod
    def failure_result(cls, tool_name: str, error: str, duration: float = 0.0) -> "ToolResult":
        """Create a failure result."""
        return cls(
            tool_name=tool_name,
            success=False,
            error=error,
            duration_seconds=duration,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        # Ensure output is serializable (convert to string if needed)
        output_value = self.output
        if output_value is not None and not isinstance(output_value, (str, int, float, bool, list, dict)):
            output_value = str(output_value)
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "output": output_value,
            "error": self.error,
            "duration_seconds": self.duration_seconds
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolResult":
        """Deserialize from dict."""
        return cls(
            tool_name=data["tool_name"],
            success=data["success"],
            output=data.get("output"),
            error=data.get("error"),
            duration_seconds=data.get("duration_seconds", 0.0)
        )


@dataclass
class AgentAction:
    """An action decided by the agent."""

    action_type: ActionType
    reasoning: str = ""  # Agent's reasoning for this action
    tool_calls: list[ToolCall] = field(default_factory=list)
    response: str | None = None  # For RESPOND/ASK_USER types
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def tool_action(cls, tool_calls: list[ToolCall], reasoning: str = "") -> "AgentAction":
        """Create a tool call action."""
        return cls(
            action_type=ActionType.TOOL_CALL,
            tool_calls=tool_calls,
            reasoning=reasoning,
        )

    @classmethod
    def think_action(cls, reasoning: str) -> "AgentAction":
        """Create a thinking action."""
        return cls(
            action_type=ActionType.THINK,
            reasoning=reasoning,
        )

    @classmethod
    def respond_action(cls, response: str, reasoning: str = "") -> "AgentAction":
        """Create a response action."""
        return cls(
            action_type=ActionType.RESPOND,
            response=response,
            reasoning=reasoning,
        )

    @classmethod
    def complete_action(cls, response: str, reasoning: str = "") -> "AgentAction":
        """Create a task completion action."""
        return cls(
            action_type=ActionType.COMPLETE,
            response=response,
            reasoning=reasoning,
        )

    @classmethod
    def escalate_action(cls, reason: str) -> "AgentAction":
        """Create an escalation action."""
        return cls(
            action_type=ActionType.ESCALATE,
            reasoning=reason,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "action_type": self.action_type.value,
            "reasoning": self.reasoning,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "response": self.response,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentAction":
        """Deserialize from dict."""
        return cls(
            action_type=ActionType(data["action_type"]),
            reasoning=data.get("reasoning", ""),
            tool_calls=[ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])],
            response=data.get("response"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationMessage:
    """A message in the agent conversation history."""

    role: str  # "user", "assistant", "tool_result"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: list[ToolCall] | None = None
    tool_results: list[ToolResult] | None = None

    @classmethod
    def user_message(cls, content: str) -> "ConversationMessage":
        """Create a user message."""
        return cls(role="user", content=content)

    @classmethod
    def assistant_message(
        cls,
        content: str,
        tool_calls: list[ToolCall] | None = None
    ) -> "ConversationMessage":
        """Create an assistant message."""
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def tool_result_message(cls, results: list[ToolResult]) -> "ConversationMessage":
        """Create a tool result message."""
        content = "\n".join(
            f"[{r.tool_name}]: {'Success' if r.success else 'Error'}: {r.output or r.error}"
            for r in results
        )
        return cls(role="tool_result", content=content, tool_results=results)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": [tc.to_dict() for tc in self.tool_calls] if self.tool_calls else None,
            "tool_results": [tr.to_dict() for tr in self.tool_results] if self.tool_results else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationMessage":
        """Deserialize from dict."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            tool_calls=[ToolCall.from_dict(tc) for tc in data["tool_calls"]] if data.get("tool_calls") else None,
            tool_results=[ToolResult.from_dict(tr) for tr in data["tool_results"]] if data.get("tool_results") else None
        )


@dataclass
class ExecutionContext:
    """Context for agent execution step."""

    session_id: str
    task_description: str
    current_phase: str
    available_tools: list[str]
    conversation_history: list[ConversationMessage] = field(default_factory=list)
    memory_context: dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    tokens_used: int = 0
    token_budget: int = 100000

    @property
    def tokens_remaining(self) -> int:
        """Calculate remaining tokens."""
        return self.token_budget - self.tokens_used

    @property
    def recent_messages(self) -> list[ConversationMessage]:
        """Get recent conversation messages (last 10)."""
        return self.conversation_history[-10:]

    def add_user_message(self, content: str) -> None:
        """Add a user message to history."""
        self.conversation_history.append(ConversationMessage.user_message(content))

    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[ToolCall] | None = None
    ) -> None:
        """Add an assistant message to history."""
        self.conversation_history.append(
            ConversationMessage.assistant_message(content, tool_calls)
        )

    def add_tool_results(self, results: list[ToolResult]) -> None:
        """Add tool results to history."""
        self.conversation_history.append(
            ConversationMessage.tool_result_message(results)
        )

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionContext":
        """Deserialize from dict."""
        return cls(
            session_id=data["session_id"],
            task_description=data["task_description"],
            current_phase=data["current_phase"],
            available_tools=data["available_tools"],
            conversation_history=[ConversationMessage.from_dict(m) for m in data.get("conversation_history", [])],
            memory_context=data.get("memory_context", {}),
            iteration=data.get("iteration", 0),
            tokens_used=data.get("tokens_used", 0),
            token_budget=data.get("token_budget", 100000)
        )


@dataclass
class StepResult:
    """Result of executing one agent step."""

    success: bool
    action: AgentAction | None = None
    tool_results: list[ToolResult] = field(default_factory=list)
    tokens_used: int = 0
    duration_seconds: float = 0.0
    error: str | None = None
    should_continue: bool = True  # False if task is complete or failed

    @classmethod
    def success_step(
        cls,
        action: AgentAction,
        tool_results: list[ToolResult],
        tokens_used: int,
        duration: float,
    ) -> "StepResult":
        """Create a successful step result."""
        # Check if we should continue
        should_continue = action.action_type not in [
            ActionType.COMPLETE,
            ActionType.RESPOND,
            ActionType.ESCALATE,
        ]

        return cls(
            success=True,
            action=action,
            tool_results=tool_results,
            tokens_used=tokens_used,
            duration_seconds=duration,
            should_continue=should_continue,
        )

    @classmethod
    def failure_step(cls, error: str, duration: float = 0.0) -> "StepResult":
        """Create a failed step result."""
        return cls(
            success=False,
            error=error,
            duration_seconds=duration,
            should_continue=False,
        )

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> "StepResult":
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


@dataclass
class TokenUsage:
    """Token usage tracking for LLM calls."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenUsage":
        """Deserialize from dict."""
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0)
        )


# Exceptions

class LLMExecutorError(Exception):
    """Base exception for LLM executor errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ActionParseError(LLMExecutorError):
    """Error parsing agent action from LLM response."""

    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message, {"raw_response": raw_response})
        self.raw_response = raw_response


class ToolExecutionError(LLMExecutorError):
    """Error executing a tool."""

    def __init__(self, message: str, tool_name: str, original_error: Exception | None = None):
        super().__init__(message, {"tool_name": tool_name})
        self.tool_name = tool_name
        self.original_error = original_error
