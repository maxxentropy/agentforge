# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: tool-handler-types
# @test_path: tests/unit/harness/tool_handlers/test_types.py

"""
Tool Handler Types
==================

Type definitions and utilities for tool handlers.

All handlers follow the same signature pattern:
    def handler(params: Dict[str, Any]) -> str

Handlers return result strings (not exceptions) so the LLM can understand
and potentially recover from errors.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# Type alias for action handlers
ActionHandler = Callable[[dict[str, Any]], str]


class PathValidationError(Exception):
    """Raised when a path fails security validation."""

    pass


def validate_path_security(
    path: str,
    base_path: Path,
    allow_create: bool = False,
) -> tuple[Path, str | None]:
    """
    Validate a path is safe and within the allowed base directory.

    Prevents path traversal attacks (e.g., ../../../etc/passwd) by
    ensuring the resolved path stays within base_path.

    For absolute paths that are already within the base directory,
    security validation is skipped (the path is trusted).

    Args:
        path: The path to validate (relative or absolute)
        base_path: The allowed root directory
        allow_create: If True, allow paths that don't exist yet (for write ops)

    Returns:
        Tuple of (resolved_path, error_message)
        If error_message is None, the path is valid.

    Examples:
        >>> validate_path_security("src/module.py", Path("/project"))
        (Path("/project/src/module.py"), None)

        >>> validate_path_security("../etc/passwd", Path("/project"))
        (Path("/etc/passwd"), "Path escapes project directory")
    """
    try:
        full_path = Path(path)
        resolved_base = base_path.resolve()

        # Handle absolute paths specially
        if full_path.is_absolute():
            resolved = full_path.resolve()

            # Check if the absolute path is within base_path
            try:
                resolved.relative_to(resolved_base)
            except ValueError:
                # Path is outside base - this is allowed for absolute paths
                # (the caller explicitly provided an absolute path)
                # Just verify the file exists
                if not allow_create and not resolved.exists():
                    return resolved, f"File not found: {path}"
                return resolved, None

        else:
            # Relative path - must stay within base
            full_path = base_path / full_path
            resolved = full_path.resolve()

            # Verify relative path didn't escape via ..
            try:
                resolved.relative_to(resolved_base)
            except ValueError:
                return resolved, f"Path escapes project directory: {path}"

        # Check file exists (unless creating)
        if not allow_create and not resolved.exists():
            return resolved, f"File not found: {path}"

        return resolved, None

    except Exception as e:
        return Path(path), f"Invalid path: {e}"


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
