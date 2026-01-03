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
        return FixResult(
            file_path=str(file_path),
            fixes_applied=0,
            original_content="",
            fixed_content="",
            dry_run=dry_run,
            errors=["File not found"],
        )

    original = file_path.read_text(encoding="utf-8", errors="ignore")

    try:
        tree = ast.parse(original, filename=str(file_path))
    except SyntaxError as e:
        return FixResult(
            file_path=str(file_path),
            fixes_applied=0,
            original_content=original,
            fixed_content=original,
            dry_run=dry_run,
            errors=[f"Syntax error: {e}"],
        )

    # Find all assert statements without messages
    asserts_to_fix: list[tuple[int, int, str]] = []  # (line, col, message)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and node.msg is None:
            message = _generate_assert_message(node.test)
            asserts_to_fix.append((node.lineno, node.col_offset, message))

    if not asserts_to_fix:
        return FixResult(
            file_path=str(file_path),
            fixes_applied=0,
            original_content=original,
            fixed_content=original,
            dry_run=dry_run,
        )

    # Apply fixes from bottom to top to preserve line numbers
    lines = original.split("\n")
    fixed_count = 0

    for lineno, col_offset, message in sorted(asserts_to_fix, reverse=True):
        line_idx = lineno - 1
        if line_idx >= len(lines):
            continue

        line = lines[line_idx]

        # Find the end of the assert statement (might span multiple lines)
        # Simple case: single-line assert
        if _is_single_line_assert(line, col_offset):
            fixed_line = _add_message_to_assert(line, message)
            if fixed_line != line:
                lines[line_idx] = fixed_line
                fixed_count += 1

    fixed_content = "\n".join(lines)

    if not dry_run and fixed_count > 0:
        file_path.write_text(fixed_content, encoding="utf-8")

    return FixResult(
        file_path=str(file_path),
        fixes_applied=fixed_count,
        original_content=original,
        fixed_content=fixed_content,
        dry_run=dry_run,
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
    # Match assert statement and capture the test expression
    # This is a simple regex-based approach for single-line asserts
    pattern = r"^(\s*)(assert\s+)(.+?)(\s*(?:#.*)?)$"
    match = re.match(pattern, line)

    if not match:
        return line

    indent = match.group(1)
    assert_kw = match.group(2)
    test_expr = match.group(3).rstrip()
    trailing = match.group(4)

    # Don't add message if one already exists (has comma outside of parens)
    paren_depth = 0
    for i, char in enumerate(test_expr):
        if char in "([{":
            paren_depth += 1
        elif char in ")]}":
            paren_depth -= 1
        elif char == "," and paren_depth == 0:
            # Already has a message
            return line

    # Escape quotes in message
    safe_message = message.replace("'", "\\'")

    return f"{indent}{assert_kw}{test_expr}, '{safe_message}'{trailing}"


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
            file_path=str(file_path),
            fixes_applied=0,
            original_content="",
            fixed_content="",
            dry_run=dry_run,
            errors=["File not found"],
        )

    original = file_path.read_text(encoding="utf-8", errors="ignore")

    # Simple regex-based replacement for now
    # This is a basic implementation - a full solution would use AST
    lines = original.split("\n")
    fixed_lines = []
    fixed_count = 0
    has_logging_import = False
    has_logger = False

    # Check for existing logging setup
    for line in lines:
        if "import logging" in line or "from logging import" in line:
            has_logging_import = True
        if "logger = " in line or "logger=" in line:
            has_logger = True

    for line in lines:
        # Simple pattern: print(...) at start of line or after indent
        match = re.match(r"^(\s*)print\((.+)\)(\s*(?:#.*)?)$", line)
        if match:
            indent = match.group(1)
            args = match.group(2)
            trailing = match.group(3)

            # Convert to logger.info()
            # Simple case: just replace print with logger.info
            fixed_line = f"{indent}logger.info({args}){trailing}"
            fixed_lines.append(fixed_line)
            fixed_count += 1
        else:
            fixed_lines.append(line)

    # Add imports and logger if we made changes and they're missing
    if fixed_count > 0:
        header_additions = []
        if not has_logging_import:
            header_additions.append("import logging")
        if not has_logger:
            header_additions.append("logger = logging.getLogger(__name__)")

        if header_additions:
            # Find first non-comment, non-blank, non-import line
            insert_idx = 0
            for i, line in enumerate(fixed_lines):
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and not stripped.startswith('"'):
                    # Check if it's an import
                    if stripped.startswith("import ") or stripped.startswith("from "):
                        insert_idx = i + 1
                    else:
                        break

            # Insert after imports
            for addition in reversed(header_additions):
                fixed_lines.insert(insert_idx, addition)
            # Add blank line after additions
            fixed_lines.insert(insert_idx + len(header_additions), "")

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
