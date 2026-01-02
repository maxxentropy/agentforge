# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: tool-handlers-init
# @test_path: tests/unit/harness/tool_handlers/test_registry.py

"""
Tool Handlers Module
====================

Provides action handlers for the fix_violation workflow and other agent tasks.

Usage:
    ```python
    from agentforge.core.harness.minimal_context.tool_handlers import (
        create_standard_handlers,
        create_fix_violation_handlers,
    )

    # Create handlers for a project
    handlers = create_standard_handlers(project_path)

    # Register with executor
    executor.register_actions(handlers)
    ```

Handler Categories:
- File handlers: read_file, write_file, edit_file, replace_lines, insert_lines
- Search handlers: search_code, load_context, find_related
- Verify handlers: run_check, run_tests, validate_python
- Terminal handlers: complete, escalate, cannot_fix, plan_fix
"""

from pathlib import Path

from .file_handlers import (
    create_edit_file_handler,
    create_insert_lines_handler,
    create_read_file_handler,
    create_replace_lines_handler,
    create_write_file_handler,
)
from .search_handlers import (
    create_find_related_handler,
    create_load_context_handler,
    create_search_code_handler,
)
from .terminal_handlers import (
    create_cannot_fix_handler,
    create_complete_handler,
    create_escalate_handler,
    create_plan_fix_handler,
    create_request_help_handler,
)
from .types import ActionHandler, HandlerContext
from .verify_handlers import (
    create_run_check_handler,
    create_run_check_handler_v2,
    create_run_tests_handler,
    create_validate_python_handler,
)


def create_standard_handlers(
    project_path: Path | None = None,
) -> dict[str, ActionHandler]:
    """
    Create standard action handlers for all base tools.

    This provides a complete set of handlers suitable for most workflows.

    Args:
        project_path: Base path for file operations

    Returns:
        Dict of action name to handler function
    """
    return {
        # File operations
        "read_file": create_read_file_handler(project_path),
        "write_file": create_write_file_handler(project_path),
        "edit_file": create_edit_file_handler(project_path),
        "replace_lines": create_replace_lines_handler(project_path),
        "insert_lines": create_insert_lines_handler(project_path),
        # Search and context
        "search_code": create_search_code_handler(project_path),
        "load_context": create_load_context_handler(project_path),
        "find_related": create_find_related_handler(project_path),
        # Verification
        "run_check": create_run_check_handler_v2(project_path),
        "run_tests": create_run_tests_handler(project_path),
        "validate_python": create_validate_python_handler(project_path),
        # Terminal actions
        "complete": create_complete_handler(),
        "escalate": create_escalate_handler(),
        "cannot_fix": create_cannot_fix_handler(project_path),
        "request_help": create_request_help_handler(project_path),
        "plan_fix": create_plan_fix_handler(project_path),
    }


def create_fix_violation_handlers(
    project_path: Path | None = None,
) -> dict[str, ActionHandler]:
    """
    Create handlers specifically for the fix_violation workflow.

    This is the recommended set for violation fixing tasks.

    Args:
        project_path: Project root path

    Returns:
        Dict of action name to handler function
    """
    # Start with standard handlers
    handlers = create_standard_handlers(project_path)

    # The fix_violation workflow uses all standard handlers
    # Future: could add specialized handlers here

    return handlers


def create_minimal_handlers(
    project_path: Path | None = None,
) -> dict[str, ActionHandler]:
    """
    Create a minimal set of handlers for simple tasks.

    Includes only file operations and terminal actions.

    Args:
        project_path: Base path for file operations

    Returns:
        Dict of action name to handler function
    """
    return {
        "read_file": create_read_file_handler(project_path),
        "write_file": create_write_file_handler(project_path),
        "edit_file": create_edit_file_handler(project_path),
        "complete": create_complete_handler(),
        "escalate": create_escalate_handler(),
    }


class ToolHandlerRegistry:
    """
    Registry for tool handlers with dynamic registration.

    Provides a fluent interface for building custom handler sets.

    Usage:
        ```python
        registry = ToolHandlerRegistry(project_path)
        registry.add_file_handlers()
        registry.add_verify_handlers()
        registry.register("custom", my_custom_handler)

        handlers = registry.get_handlers()
        ```
    """

    def __init__(self, project_path: Path | None = None):
        """
        Initialize the registry.

        Args:
            project_path: Base path for file operations
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, name: str, handler: ActionHandler) -> "ToolHandlerRegistry":
        """
        Register a single handler.

        Args:
            name: Handler name
            handler: Handler function

        Returns:
            Self for chaining
        """
        self._handlers[name] = handler
        return self

    def register_all(
        self, handlers: dict[str, ActionHandler]
    ) -> "ToolHandlerRegistry":
        """
        Register multiple handlers.

        Args:
            handlers: Dict of name to handler

        Returns:
            Self for chaining
        """
        self._handlers.update(handlers)
        return self

    def add_file_handlers(self) -> "ToolHandlerRegistry":
        """Add file operation handlers."""
        self._handlers.update(
            {
                "read_file": create_read_file_handler(self.project_path),
                "write_file": create_write_file_handler(self.project_path),
                "edit_file": create_edit_file_handler(self.project_path),
                "replace_lines": create_replace_lines_handler(self.project_path),
                "insert_lines": create_insert_lines_handler(self.project_path),
            }
        )
        return self

    def add_search_handlers(self) -> "ToolHandlerRegistry":
        """Add search and context handlers."""
        self._handlers.update(
            {
                "search_code": create_search_code_handler(self.project_path),
                "load_context": create_load_context_handler(self.project_path),
                "find_related": create_find_related_handler(self.project_path),
            }
        )
        return self

    def add_verify_handlers(self) -> "ToolHandlerRegistry":
        """Add verification handlers."""
        self._handlers.update(
            {
                "run_check": create_run_check_handler_v2(self.project_path),
                "run_tests": create_run_tests_handler(self.project_path),
                "validate_python": create_validate_python_handler(self.project_path),
            }
        )
        return self

    def add_terminal_handlers(self) -> "ToolHandlerRegistry":
        """Add terminal action handlers."""
        self._handlers.update(
            {
                "complete": create_complete_handler(),
                "escalate": create_escalate_handler(),
                "cannot_fix": create_cannot_fix_handler(self.project_path),
                "request_help": create_request_help_handler(self.project_path),
                "plan_fix": create_plan_fix_handler(self.project_path),
            }
        )
        return self

    def add_all(self) -> "ToolHandlerRegistry":
        """Add all standard handlers."""
        return (
            self.add_file_handlers()
            .add_search_handlers()
            .add_verify_handlers()
            .add_terminal_handlers()
        )

    def get_handlers(self) -> dict[str, ActionHandler]:
        """Get all registered handlers."""
        return dict(self._handlers)

    def has_handler(self, name: str) -> bool:
        """Check if a handler is registered."""
        return name in self._handlers

    def list_handlers(self) -> list:
        """List all registered handler names."""
        return sorted(self._handlers.keys())


__all__ = [
    # Types
    "ActionHandler",
    "HandlerContext",
    # Registry
    "ToolHandlerRegistry",
    # Factory functions
    "create_standard_handlers",
    "create_fix_violation_handlers",
    "create_minimal_handlers",
    # File handlers
    "create_read_file_handler",
    "create_write_file_handler",
    "create_edit_file_handler",
    "create_replace_lines_handler",
    "create_insert_lines_handler",
    # Search handlers
    "create_search_code_handler",
    "create_load_context_handler",
    "create_find_related_handler",
    # Verify handlers
    "create_run_check_handler",
    "create_run_check_handler_v2",
    "create_run_tests_handler",
    "create_validate_python_handler",
    # Terminal handlers
    "create_complete_handler",
    "create_escalate_handler",
    "create_cannot_fix_handler",
    "create_request_help_handler",
    "create_plan_fix_handler",
]
