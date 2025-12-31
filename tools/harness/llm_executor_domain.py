"""
LLM Executor Domain Model
=========================

Domain entities for the Agent Harness LLM Executor.
Defines the structures for agent actions, tool calls, and execution context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


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
    parameters: Dict[str, Any] = field(default_factory=dict)
    category: Optional[ToolCategory] = None

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


@dataclass
class ToolResult:
    """Result of executing a tool."""

    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
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


@dataclass
class AgentAction:
    """An action decided by the agent."""

    action_type: ActionType
    reasoning: str = ""  # Agent's reasoning for this action
    tool_calls: List[ToolCall] = field(default_factory=list)
    response: Optional[str] = None  # For RESPOND/ASK_USER types
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def tool_action(cls, tool_calls: List[ToolCall], reasoning: str = "") -> "AgentAction":
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


@dataclass
class ConversationMessage:
    """A message in the agent conversation history."""

    role: str  # "user", "assistant", "tool_result"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None

    @classmethod
    def user_message(cls, content: str) -> "ConversationMessage":
        """Create a user message."""
        return cls(role="user", content=content)

    @classmethod
    def assistant_message(
        cls,
        content: str,
        tool_calls: Optional[List[ToolCall]] = None
    ) -> "ConversationMessage":
        """Create an assistant message."""
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def tool_result_message(cls, results: List[ToolResult]) -> "ConversationMessage":
        """Create a tool result message."""
        content = "\n".join(
            f"[{r.tool_name}]: {'Success' if r.success else 'Error'}: {r.output or r.error}"
            for r in results
        )
        return cls(role="tool_result", content=content, tool_results=results)


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

    @property
    def tokens_remaining(self) -> int:
        """Calculate remaining tokens."""
        return self.token_budget - self.tokens_used

    @property
    def recent_messages(self) -> List[ConversationMessage]:
        """Get recent conversation messages (last 10)."""
        return self.conversation_history[-10:]

    def add_user_message(self, content: str) -> None:
        """Add a user message to history."""
        self.conversation_history.append(ConversationMessage.user_message(content))

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[ToolCall]] = None
    ) -> None:
        """Add an assistant message to history."""
        self.conversation_history.append(
            ConversationMessage.assistant_message(content, tool_calls)
        )

    def add_tool_results(self, results: List[ToolResult]) -> None:
        """Add tool results to history."""
        self.conversation_history.append(
            ConversationMessage.tool_result_message(results)
        )


@dataclass
class StepResult:
    """Result of executing one agent step."""

    success: bool
    action: Optional[AgentAction] = None
    tool_results: List[ToolResult] = field(default_factory=list)
    tokens_used: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None
    should_continue: bool = True  # False if task is complete or failed

    @classmethod
    def success_step(
        cls,
        action: AgentAction,
        tool_results: List[ToolResult],
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


@dataclass
class TokenUsage:
    """Token usage tracking for LLM calls."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.prompt_tokens + self.completion_tokens


# Exceptions

class LLMExecutorError(Exception):
    """Base exception for LLM executor errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ActionParseError(LLMExecutorError):
    """Error parsing agent action from LLM response."""

    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message, {"raw_response": raw_response})
        self.raw_response = raw_response


class ToolExecutionError(LLMExecutorError):
    """Error executing a tool."""

    def __init__(self, message: str, tool_name: str, original_error: Optional[Exception] = None):
        super().__init__(message, {"tool_name": tool_name})
        self.tool_name = tool_name
        self.original_error = original_error
