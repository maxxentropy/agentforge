# @deprecated: Moved from native_tool_executor.py on 2025-01-01
# @reason: Handlers consolidated into tool_handlers module
# @replacement: agentforge.core.harness.minimal_context.tool_handlers

"""
Legacy Action Handlers (DEPRECATED)
===================================

These handlers were originally in native_tool_executor.py.
They have been replaced by the tool_handlers module which provides
a more complete and tested implementation.

Use instead:
    from agentforge.core.harness.minimal_context.tool_handlers import (
        create_standard_handlers,
        create_read_file_handler,
        create_write_file_handler,
        create_complete_handler,
        create_escalate_handler,
    )
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

ActionHandler = Callable[[Dict[str, Any]], Any]


def create_read_file_handler(project_path: Optional[Path] = None) -> ActionHandler:
    """
    Create a read_file action handler.

    DEPRECATED: Use tool_handlers.create_read_file_handler instead.
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: Dict[str, Any]) -> str:
        path = params.get("path", "")
        if not path:
            return "ERROR: path parameter required"

        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = base_path / file_path

        if not file_path.exists():
            return f"ERROR: File not found: {file_path}"

        try:
            content = file_path.read_text()
            return f"SUCCESS: Read {file_path}\n\n{content[:2000]}"
        except Exception as e:
            return f"ERROR: Failed to read file: {e}"

    return handler


def create_write_file_handler(project_path: Optional[Path] = None) -> ActionHandler:
    """
    Create a write_file action handler.

    DEPRECATED: Use tool_handlers.create_write_file_handler instead.
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: Dict[str, Any]) -> str:
        path = params.get("path", "")
        content = params.get("content", "")

        if not path:
            return "ERROR: path parameter required"

        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = base_path / file_path

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return f"SUCCESS: Wrote {len(content)} bytes to {file_path}"
        except Exception as e:
            return f"ERROR: Failed to write file: {e}"

    return handler


def create_complete_handler() -> ActionHandler:
    """
    Create a complete action handler.

    DEPRECATED: Use tool_handlers.create_complete_handler instead.
    """

    def handler(params: Dict[str, Any]) -> str:
        summary = params.get("summary", "Task completed")
        return f"COMPLETE: {summary}"

    return handler


def create_escalate_handler() -> ActionHandler:
    """
    Create an escalate action handler.

    DEPRECATED: Use tool_handlers.create_escalate_handler instead.
    """

    def handler(params: Dict[str, Any]) -> str:
        reason = params.get("reason", "Unknown reason")
        return f"ESCALATE: {reason}"

    return handler


def create_standard_handlers(project_path: Optional[Path] = None) -> Dict[str, ActionHandler]:
    """
    Create standard action handlers for common tools.

    DEPRECATED: Use tool_handlers.create_standard_handlers instead.
    """
    return {
        "read_file": create_read_file_handler(project_path),
        "write_file": create_write_file_handler(project_path),
        "complete": create_complete_handler(),
        "escalate": create_escalate_handler(),
    }
