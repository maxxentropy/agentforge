# @spec_file: specs/tools/01-tool-handlers.yaml
# @spec_id: tool-handlers-v1
# @component_id: tool-handler-types
# @test_path: tests/unit/harness/tool_handlers/test_types.py

"""
Tool Handler Types
==================

Type definitions for tool handlers.

All handlers follow the same signature pattern:
    def handler(params: Dict[str, Any]) -> str

Handlers return result strings (not exceptions) so the LLM can understand
and potentially recover from errors.
"""

from typing import Any, Callable, Dict, Protocol, runtime_checkable


# Type alias for action handlers
ActionHandler = Callable[[Dict[str, Any]], str]


@runtime_checkable
class HandlerContext(Protocol):
    """Protocol for handler context injection.

    Handlers can access task context via params["_context"] which
    follows this protocol.
    """

    @property
    def violation_id(self) -> str:
        """The violation being fixed."""
        ...

    @property
    def task_id(self) -> str:
        """Current task ID."""
        ...

    @property
    def files_examined(self) -> list:
        """Files that have been read/analyzed."""
        ...

    @property
    def attempted_approaches(self) -> list:
        """Approaches that have been tried."""
        ...

    @property
    def understanding(self) -> list:
        """Facts learned during execution."""
        ...


class HandlerResult:
    """
    Structured result from a tool handler.

    Provides a standard way to format results for LLM consumption.
    """

    SUCCESS_PREFIX = "SUCCESS:"
    ERROR_PREFIX = "ERROR:"

    def __init__(
        self,
        success: bool,
        message: str,
        details: Dict[str, Any] = None,
    ):
        """
        Initialize handler result.

        Args:
            success: Whether the handler succeeded
            message: Human-readable message
            details: Additional structured details
        """
        self.success = success
        self.message = message
        self.details = details or {}

    def to_string(self) -> str:
        """Convert to string format for tool result."""
        prefix = self.SUCCESS_PREFIX if self.success else self.ERROR_PREFIX
        result = f"{prefix} {self.message}"

        if self.details:
            for key, value in self.details.items():
                result += f"\n  {key}: {value}"

        return result

    @classmethod
    def success(cls, message: str, **details) -> "HandlerResult":
        """Create a success result."""
        return cls(success=True, message=message, details=details)

    @classmethod
    def error(cls, message: str, **details) -> "HandlerResult":
        """Create an error result."""
        return cls(success=False, message=message, details=details)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"HandlerResult(success={self.success}, message={self.message!r})"
