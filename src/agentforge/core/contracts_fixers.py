# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contracts-fixers
# @test_path: tests/unit/contracts/test_fixers.py

"""
Contract Auto-Fixers
====================

Auto-fix implementations for common contract violations.
Fixers use AST manipulation to safely transform code.

Usage:
    agentforge fix --check <check-id> [--dry-run] [files...]
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class FixResult:
    """Result of applying a fix."""

    file_path: str
    fixes_applied: int
    original_content: str
    fixed_content: str
    dry_run: bool = False
    errors: list[str] | None = None


# Type for fixer functions
FixerFunc = Callable[[Path, bool], FixResult | None]

# Registry of fixers by check_id
_FIXERS: dict[str, FixerFunc] = {}


def register_fixer(check_id: str) -> Callable[[FixerFunc], FixerFunc]:
    """Decorator to register a fixer for a check ID."""

    def decorator(func: FixerFunc) -> FixerFunc:
        _FIXERS[check_id] = func
        return func

    return decorator


def get_fixer(check_id: str) -> FixerFunc | None:
    """Get the fixer function for a check ID."""
    return _FIXERS.get(check_id)


def list_fixers() -> list[str]:
    """List all registered fixer check IDs."""
    return list(_FIXERS.keys())


def apply_fix(check_id: str, file_path: Path, dry_run: bool = False) -> FixResult | None:
    """
    Apply a fix for a check to a file.

    Args:
        check_id: The check ID to fix
        file_path: Path to the file to fix
        dry_run: If True, don't write changes

    Returns:
        FixResult with details, or None if fixer doesn't exist
    """
    fixer = get_fixer(check_id)
    if fixer is None:
        return None
    return fixer(file_path, dry_run)


# ============================================================================
# Individual Fixers
# ============================================================================


def _make_error_result(file_path: Path, dry_run: bool, error: str, original: str = "") -> FixResult:
    """Create a FixResult for error cases."""
    return FixResult(
        file_path=str(file_path), fixes_applied=0, original_content=original,
        fixed_content=original, dry_run=dry_run, errors=[error],
    )


def _find_bare_asserts(tree: ast.AST) -> list[tuple[int, int, str]]:
    """Find all assert statements without messages."""
    asserts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and node.msg is None:
            message = _generate_assert_message(node.test)
            asserts.append((node.lineno, node.col_offset, message))
    return asserts


def _apply_assert_fixes(lines: list[str], asserts_to_fix: list[tuple[int, int, str]]) -> int:
    """Apply assert message fixes, return count of fixes applied."""
    fixed_count = 0
    for lineno, col_offset, message in sorted(asserts_to_fix, reverse=True):
        line_idx = lineno - 1
        if line_idx >= len(lines):
            continue
        line = lines[line_idx]
        if _is_single_line_assert(line, col_offset):
            fixed_line = _add_message_to_assert(line, message)
            if fixed_line != line:
                lines[line_idx] = fixed_line
                fixed_count += 1
    return fixed_count


@register_fixer("no-bare-assert")
def fix_bare_assert(file_path: Path, dry_run: bool = False) -> FixResult:
    """
    Fix bare assert statements by adding descriptive messages.

    Transforms:
        assert x == y  ->  assert x == y, "Expected x to equal y"
        assert x in y  ->  assert x in y, "Expected x in y"
        assert x       ->  assert x, "Expected x to be truthy"
    """
    if not file_path.exists():
        return _make_error_result(file_path, dry_run, "File not found")

    original = file_path.read_text(encoding="utf-8", errors="ignore")

    try:
        tree = ast.parse(original, filename=str(file_path))
    except SyntaxError as e:
        return _make_error_result(file_path, dry_run, f"Syntax error: {e}", original)

    asserts_to_fix = _find_bare_asserts(tree)
    if not asserts_to_fix:
        return FixResult(
            file_path=str(file_path), fixes_applied=0,
            original_content=original, fixed_content=original, dry_run=dry_run,
        )

    lines = original.split("\n")
    fixed_count = _apply_assert_fixes(lines, asserts_to_fix)
    fixed_content = "\n".join(lines)

    if not dry_run and fixed_count > 0:
        file_path.write_text(fixed_content, encoding="utf-8")

    return FixResult(
        file_path=str(file_path), fixes_applied=fixed_count,
        original_content=original, fixed_content=fixed_content, dry_run=dry_run,
    )


def _generate_assert_message(test: ast.expr) -> str:
    """Generate a descriptive message for an assert test expression."""
    if isinstance(test, ast.Compare):
        # assert x == y, assert x < y, etc.
        left = _get_node_repr(test.left)
        if len(test.ops) == 1 and len(test.comparators) == 1:
            op = test.ops[0]
            right = _get_node_repr(test.comparators[0])

            op_descriptions = {
                ast.Eq: f"Expected {left} to equal {right}",
                ast.NotEq: f"Expected {left} to not equal {right}",
                ast.Lt: f"Expected {left} < {right}",
                ast.LtE: f"Expected {left} <= {right}",
                ast.Gt: f"Expected {left} > {right}",
                ast.GtE: f"Expected {left} >= {right}",
                ast.Is: f"Expected {left} is {right}",
                ast.IsNot: f"Expected {left} is not {right}",
                ast.In: f"Expected {left} in {right}",
                ast.NotIn: f"Expected {left} not in {right}",
            }
            return op_descriptions.get(type(op), f"Assertion failed: {left}")
        return f"Assertion failed"

    if isinstance(test, ast.BoolOp):
        return "Assertion failed"

    if isinstance(test, ast.Call):
        func_name = _get_node_repr(test.func)
        return f"Expected {func_name}() to be truthy"

    if isinstance(test, ast.Attribute):
        return f"Expected {_get_node_repr(test)} to be truthy"

    if isinstance(test, ast.Name):
        return f"Expected {test.id} to be truthy"

    return "Assertion failed"


def _get_node_repr(node: ast.expr, max_len: int = 30) -> str:
    """Get a short string representation of an AST node."""
    try:
        result = ast.unparse(node)
        if len(result) > max_len:
            result = result[: max_len - 3] + "..."
        return result
    except Exception:
        return "value"


def _is_single_line_assert(line: str, col_offset: int) -> bool:
    """Check if this appears to be a complete single-line assert."""
    # Crude check: line ends without continuation
    stripped = line.rstrip()
    # Not continued if doesn't end with \ or open paren/bracket
    if stripped.endswith("\\"):
        return False
    # Check balanced parens (crude)
    open_count = stripped.count("(") + stripped.count("[")
    close_count = stripped.count(")") + stripped.count("]")
    return open_count <= close_count


def _add_message_to_assert(line: str, message: str) -> str:
    """Add a message to an assert statement on a single line."""
    # Find the assert keyword
    assert_match = re.match(r"^(\s*)(assert\s+)", line)
    if not assert_match:
        return line

    indent = assert_match.group(1)
    assert_kw = assert_match.group(2)
    rest = line[len(assert_match.group(0)):]

    # Parse the test expression, being careful about strings and comments
    # Find the end of the test expression (respecting string literals)
    test_end = _find_expression_end(rest)
    test_expr = rest[:test_end].rstrip()
    trailing = rest[test_end:]

    # Don't add message if one already exists (has comma outside of parens/strings)
    if _has_message_already(test_expr):
        return line

    # Generate a safe message using double quotes to avoid escaping issues
    safe_message = message.replace('"', '\\"')

    return f'{indent}{assert_kw}{test_expr}, "{safe_message}"{trailing}'


def _is_escaped_quote(text: str, i: int) -> bool:
    """Check if char at position is an escaped quote."""
    return i > 0 and text[i - 1] == "\\"


def _handle_string_start(text: str, i: int, char: str) -> tuple[str, int]:
    """Handle start of a string literal, return (string_marker, new_index)."""
    if text[i:i+3] in ('"""', "'''"):
        return text[i:i+3], i + 3
    return char, i + 1


def _handle_quote(text: str, i: int, char: str, in_string: str | None) -> tuple[str | None, int]:
    """Handle quote character, returning (new_in_string, new_index)."""
    if in_string is None:
        return _handle_string_start(text, i, char)
    if in_string == char:
        return None, i + 1
    if len(in_string) == 3 and text[i:i+3] == in_string:
        return None, i + 3
    return in_string, i + 1


def _update_paren_depth(char: str, depth: int) -> int:
    """Update parenthesis depth based on character."""
    if char in "([{":
        return depth + 1
    if char in ")]}":
        return depth - 1
    return depth


def _find_char_at_depth_zero(text: str, target_chars: str) -> int | None:
    """Find first occurrence of any target char at depth 0 outside strings.

    Handles:
    - Single and double quotes (including triple quotes)
    - Escaped quotes
    - Nested parentheses, brackets, braces

    Args:
        text: The text to search
        target_chars: Characters to find (e.g., "#" or ",")

    Returns:
        Index of first target char at depth 0, or None if not found.
    """
    i = 0
    paren_depth = 0
    in_string: str | None = None

    while i < len(text):
        char = text[i]

        # Handle quotes (unescaped only)
        if char in ('"', "'") and not _is_escaped_quote(text, i):
            in_string, i = _handle_quote(text, i, char, in_string)
            continue

        # Skip non-string content processing when inside a string
        if in_string is not None:
            i += 1
            continue

        # Update bracket depth and check for target
        paren_depth = _update_paren_depth(char, paren_depth)
        if char in target_chars and paren_depth == 0:
            return i

        i += 1

    return None


def _find_expression_end(text: str) -> int:
    """Find where the expression ends (accounting for strings and parens)."""
    pos = _find_char_at_depth_zero(text, "#")
    return pos if pos is not None else len(text)


def _has_message_already(test_expr: str) -> bool:
    """Check if assert already has a message (comma at depth 0 outside strings)."""
    return _find_char_at_depth_zero(test_expr, ",") is not None


def _check_logging_setup(lines: list[str]) -> tuple[bool, bool]:
    """Check for existing logging import and logger declaration."""
    has_import = any("import logging" in ln or "from logging import" in ln for ln in lines)
    has_logger = any("logger = " in ln or "logger=" in ln for ln in lines)
    return has_import, has_logger


def _convert_prints_to_logger(lines: list[str]) -> tuple[list[str], int]:
    """Convert print statements to logger.info calls."""
    fixed_lines = []
    fixed_count = 0
    for line in lines:
        match = re.match(r"^(\s*)print\((.+)\)(\s*(?:#.*)?)$", line)
        if match:
            indent, args, trailing = match.group(1), match.group(2), match.group(3)
            fixed_lines.append(f"{indent}logger.info({args}){trailing}")
            fixed_count += 1
        else:
            fixed_lines.append(line)
    return fixed_lines, fixed_count


def _find_import_insert_position(lines: list[str]) -> int:
    """Find position after imports to insert logging setup."""
    insert_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith('"'):
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_idx = i + 1
            else:
                break
    return insert_idx


def _add_logging_header(lines: list[str], has_import: bool, has_logger: bool) -> None:
    """Add logging import and logger declaration if needed."""
    additions = []
    if not has_import:
        additions.append("import logging")
    if not has_logger:
        additions.append("logger = logging.getLogger(__name__)")
    if additions:
        insert_idx = _find_import_insert_position(lines)
        for addition in reversed(additions):
            lines.insert(insert_idx, addition)
        lines.insert(insert_idx + len(additions), "")


@register_fixer("no-print-statements")
def fix_print_statements(file_path: Path, dry_run: bool = False) -> FixResult:
    """
    Fix print statements by converting to logging calls.

    Transforms:
        print("message")  ->  logger.info("message")

    Note: This adds an import and logger if not present.
    """
    if not file_path.exists():
        return FixResult(
            file_path=str(file_path), fixes_applied=0, original_content="",
            fixed_content="", dry_run=dry_run, errors=["File not found"],
        )

    original = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = original.split("\n")

    has_import, has_logger = _check_logging_setup(lines)
    fixed_lines, fixed_count = _convert_prints_to_logger(lines)

    if fixed_count > 0:
        _add_logging_header(fixed_lines, has_import, has_logger)

    fixed_content = "\n".join(fixed_lines)

    if not dry_run and fixed_count > 0:
        file_path.write_text(fixed_content, encoding="utf-8")

    return FixResult(
        file_path=str(file_path), fixes_applied=fixed_count,
        original_content=original, fixed_content=fixed_content, dry_run=dry_run,
    )


@register_fixer("use-click-echo")
def fix_use_click_echo(file_path: Path, dry_run: bool = False) -> FixResult:
    """
    Fix print statements in CLI files by converting to click.echo.

    Transforms:
        print("message")  ->  click.echo("message")
    """
    if not file_path.exists():
        return FixResult(
            file_path=str(file_path),
            fixes_applied=0,
            original_content="",
            fixed_content="",
            dry_run=dry_run,
            errors=["File not found"],
        )

    original = file_path.read_text(encoding="utf-8", errors="ignore")

    # Check if this is a CLI file (has click import)
    if "import click" not in original and "from click" not in original:
        return FixResult(
            file_path=str(file_path),
            fixes_applied=0,
            original_content=original,
            fixed_content=original,
            dry_run=dry_run,
            errors=["Not a click CLI file"],
        )

    # Simple regex replacement
    lines = original.split("\n")
    fixed_lines = []
    fixed_count = 0

    for line in lines:
        # Pattern: print(...) - replace with click.echo(...)
        match = re.match(r"^(\s*)print\((.+)\)(\s*(?:#.*)?)$", line)
        if match:
            indent = match.group(1)
            args = match.group(2)
            trailing = match.group(3)

            fixed_line = f"{indent}click.echo({args}){trailing}"
            fixed_lines.append(fixed_line)
            fixed_count += 1
        else:
            fixed_lines.append(line)

    fixed_content = "\n".join(fixed_lines)

    if not dry_run and fixed_count > 0:
        file_path.write_text(fixed_content, encoding="utf-8")

    return FixResult(
        file_path=str(file_path),
        fixes_applied=fixed_count,
        original_content=original,
        fixed_content=fixed_content,
        dry_run=dry_run,
    )
