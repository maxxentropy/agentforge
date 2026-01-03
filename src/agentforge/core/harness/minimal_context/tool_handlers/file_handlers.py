# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: file-handlers
# @test_path: tests/unit/harness/tool_handlers/test_file_handlers.py

"""
File Handlers
=============

Handlers for file operations: read_file, write_file, edit_file.

These handlers follow the factory pattern, returning closures that
capture the project_path for relative path resolution.

Design principles:
- Return strings (not exceptions) so the LLM can understand errors
- Handle relative and absolute paths
- Provide clear success/failure messages with context
"""

import logging
from pathlib import Path
from typing import Any

from .constants import FILE_PREVIEW_MAX_LINES
from .types import ActionHandler, validate_path_security

logger = logging.getLogger(__name__)


def _detect_line_indent(line: str) -> int:
    """Detect indentation level of a line."""
    if line.strip():
        return len(line) - len(line.lstrip())
    return 0


def _detect_content_indent(content_lines: list[str]) -> int:
    """Detect indentation of first non-empty line in content."""
    for line in content_lines:
        if line.strip():
            return len(line) - len(line.lstrip())
    return 0


def _adjust_lines_indentation(
    content_lines: list[str], target_indent: int, source_indent: int
) -> list[str]:
    """Adjust content lines to match target indentation."""
    indent_delta = target_indent - source_indent
    result = []
    for line in content_lines:
        if line.strip():
            current_indent = len(line) - len(line.lstrip())
            new_indent = max(0, current_indent + indent_delta)
            result.append(" " * new_indent + line.lstrip())
        else:
            result.append("")
    return result


def _process_insert_content(content: str, indent_str: str) -> list[str]:
    """Process content for insertion, adding indentation."""
    new_lines = []
    for line in content.split("\n"):
        if line.strip():
            stripped = line.lstrip()
            line_indent = len(line) - len(stripped)
            if line_indent:
                new_lines.append(indent_str + " " * line_indent + stripped)
            else:
                new_lines.append(indent_str + stripped)
        else:
            new_lines.append("")
    if new_lines and new_lines[-1].strip():
        new_lines.append("")
    return new_lines


def _validate_edit_params(
    path: str, start_line: int, end_line: int
) -> str | None:
    """Validate edit operation parameters. Returns error message or None."""
    if not path:
        return "ERROR: path parameter required"
    if start_line < 1:
        return "ERROR: start_line must be >= 1"
    if end_line < start_line:
        return "ERROR: end_line must be >= start_line"
    return None


def _validate_replace_params(
    path: str | None, start_line: int | None, end_line: int | None, new_content: str | None
) -> str | None:
    """Validate replace_lines parameters. Returns error message or None."""
    if not path:
        return "ERROR: path parameter required"
    if start_line is None or end_line is None:
        return "ERROR: start_line and end_line required"
    if new_content is None:
        return "ERROR: new_content required"
    return None


def _validate_insert_params(
    path: str | None, line_number: int | None, new_content: str | None
) -> str | None:
    """Validate insert_lines parameters. Returns error message or None."""
    if not path:
        return "ERROR: path parameter required"
    if line_number is None:
        return "ERROR: line_number parameter required"
    if not new_content:
        return "ERROR: new_content parameter required"
    return None


def _validate_line_range(start_line: int, end_line: int, total_lines: int) -> str | None:
    """Validate line range against file length. Returns error message or None."""
    if start_line < 1 or end_line > total_lines or start_line > end_line:
        return (
            f"ERROR: Invalid line range {start_line}-{end_line} "
            f"(file has {total_lines} lines)"
        )
    return None


def _validate_line_number(line_number: int, total_lines: int) -> str | None:
    """Validate line number for insertion. Returns error message or None."""
    if line_number < 1 or line_number > total_lines + 1:
        return (
            f"ERROR: Invalid line number {line_number} "
            f"(file has {total_lines} lines)"
        )
    return None


def create_read_file_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create a read_file action handler.

    Args:
        project_path: Base path for relative file paths

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        path = params.get("path", "")
        logger.debug("read_file: path=%s", path)
        if not path:
            return "ERROR: path parameter required"

        # Validate path security
        file_path, error = validate_path_security(path, base_path)
        if error:
            return f"ERROR: {error}"

        if not file_path.is_file():
            return f"ERROR: Not a file: {file_path}"

        try:
            content = file_path.read_text()
            lines = content.splitlines()
            line_count = len(lines)

            # Add line numbers for context
            numbered_lines = [f"{i+1:4d}: {line}" for i, line in enumerate(lines[:FILE_PREVIEW_MAX_LINES])]
            preview = "\n".join(numbered_lines)

            if line_count > FILE_PREVIEW_MAX_LINES:
                preview += f"\n... [{line_count - FILE_PREVIEW_MAX_LINES} more lines]"

            return (
                f"SUCCESS: Read {file_path.name}\n"
                f"  Size: {len(content)} chars, {line_count} lines\n"
                f"\n{preview}"
            )

        except PermissionError:
            return f"ERROR: Permission denied: {file_path}"
        except UnicodeDecodeError:
            return f"ERROR: Cannot read binary file: {file_path}"
        except Exception as e:
            return f"ERROR: Failed to read file: {e}"

    return handler


def create_write_file_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create a write_file action handler.

    Args:
        project_path: Base path for relative file paths

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        path = params.get("path", "")
        content = params.get("content", "")
        logger.debug("write_file: path=%s, content_len=%d", path, len(content))

        if not path:
            return "ERROR: path parameter required"

        # Validate path security (allow_create=True for write operations)
        file_path, error = validate_path_security(path, base_path, allow_create=True)
        if error:
            return f"ERROR: {error}"

        try:
            # Track if this is a new file
            is_new = not file_path.exists()

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content)

            action = "Created" if is_new else "Wrote"
            return (
                f"SUCCESS: {action} {file_path.name}\n"
                f"  Path: {file_path}\n"
                f"  Size: {len(content)} bytes"
            )

        except PermissionError:
            return f"ERROR: Permission denied: {file_path}"
        except Exception as e:
            return f"ERROR: Failed to write file: {e}"

    return handler


def create_edit_file_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create an edit_file action handler.

    Replaces lines start_line through end_line (inclusive) with new_content.
    This is more precise than write_file and produces cleaner diffs.

    Args:
        project_path: Base path for relative file paths

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        path = params.get("path", "")
        start_line = params.get("start_line", 0)
        end_line = params.get("end_line", 0)
        new_content = params.get("new_content", "")
        logger.debug("edit_file: path=%s, lines=%d-%d", path, start_line, end_line)

        # Validate parameters
        if error := _validate_edit_params(path, start_line, end_line):
            return error

        # Validate path security
        file_path, error = validate_path_security(path, base_path)
        if error:
            return f"ERROR: {error}"

        if not file_path.is_file():
            return f"ERROR: Not a file: {file_path}"

        try:
            # Read current content
            lines = file_path.read_text().splitlines(keepends=True)
            original_line_count = len(lines)

            # Validate line numbers against file
            if start_line > original_line_count:
                return f"ERROR: start_line {start_line} exceeds file length {original_line_count}"

            # Adjust end_line if beyond file (allow appending)
            effective_end = min(end_line, original_line_count)

            # Build new content
            # Convert 1-indexed to 0-indexed
            before = lines[: start_line - 1]
            after = lines[effective_end:]

            # Ensure new_content ends with newline if it has content
            new_lines = new_content.splitlines(keepends=True)
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"

            # Combine
            result_lines = before + new_lines + after

            # Write back
            file_path.write_text("".join(result_lines))

            # Calculate diff stats
            lines_removed = effective_end - start_line + 1
            lines_added = len(new_lines)

            return (
                f"SUCCESS: Edited {file_path.name}\n"
                f"  Lines {start_line}-{effective_end} replaced "
                f"({lines_removed} lines -> {lines_added} lines)\n"
                f"  File now has {len(result_lines)} lines"
            )

        except PermissionError:
            return f"ERROR: Permission denied: {file_path}"
        except Exception as e:
            return f"ERROR: Failed to edit file: {e}"

    return handler


def create_replace_lines_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create a replace_lines action handler.

    Similar to edit_file but with auto-indentation based on context.

    Args:
        project_path: Base path for relative file paths

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        path = params.get("path") or params.get("file_path")
        start_line = params.get("start_line")
        end_line = params.get("end_line")
        new_content = params.get("new_content")

        # Validate parameters
        if error := _validate_replace_params(path, start_line, end_line, new_content):
            return error

        # Validate path security
        full_path, error = validate_path_security(path, base_path)
        if error:
            return f"ERROR: {error}"

        try:
            original_content = full_path.read_text()
            lines = original_content.split("\n")

            # Validate line range
            if error := _validate_line_range(start_line, end_line, len(lines)):
                return error

            # Detect indentation from the first line being replaced
            original_line = lines[start_line - 1]
            target_indent = _detect_line_indent(original_line)

            # Detect indentation of the new content and adjust
            content_lines = new_content.split("\n")
            source_indent = _detect_content_indent(content_lines)
            new_lines = _adjust_lines_indentation(content_lines, target_indent, source_indent)

            # Replace lines
            result_lines = lines[: start_line - 1] + new_lines + lines[end_line:]
            new_source = "\n".join(result_lines)

            full_path.write_text(new_source)

            return (
                f"SUCCESS: Replaced lines {start_line}-{end_line}\n"
                f"  Added {len(new_lines)} new lines\n"
                f"  Indentation auto-adjusted"
            )

        except Exception as e:
            return f"ERROR: Failed to replace lines: {e}"

    return handler


def create_insert_lines_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create an insert_lines action handler.

    Inserts new lines at a specific line number without removing existing lines.

    Args:
        project_path: Base path for relative file paths

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        path = params.get("path") or params.get("file_path")
        line_number = params.get("line_number") or params.get("before_line")
        new_content = params.get("new_content") or params.get("content")
        indent_level = params.get("indent_level")

        # Validate parameters
        if error := _validate_insert_params(path, line_number, new_content):
            return error

        # Validate path security
        full_path, error = validate_path_security(path, base_path)
        if error:
            return f"ERROR: {error}"

        try:
            lines = full_path.read_text().split("\n")

            # Validate line number
            if error := _validate_line_number(line_number, len(lines)):
                return error

            # Detect indentation from context
            if indent_level is None:
                context_line = lines[line_number - 1] if line_number <= len(lines) else ""
                indent_level = _detect_line_indent(context_line)

            indent_str = " " * indent_level

            # Process new content with indentation
            new_lines = _process_insert_content(new_content, indent_str)

            # Insert lines
            insert_index = line_number - 1
            result_lines = lines[:insert_index] + new_lines + lines[insert_index:]
            new_source = "\n".join(result_lines)

            full_path.write_text(new_source)

            return (
                f"SUCCESS: Inserted {len(new_lines)} lines before line {line_number}\n"
                f"  File now has {len(result_lines)} lines"
            )

        except Exception as e:
            return f"ERROR: Failed to insert lines: {e}"

    return handler
