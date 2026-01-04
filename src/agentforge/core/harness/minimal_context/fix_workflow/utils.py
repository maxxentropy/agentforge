# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow-utils

"""
Fix Workflow Utilities
======================

Helper functions for fix workflow operations.
"""

import re


def detect_source_indent(content_lines: list[str]) -> int:
    """Detect indentation of first non-empty line in content."""
    for line in content_lines:
        if line.strip():
            return len(line) - len(line.lstrip())
    return 0


def adjust_content_indentation(
    content_lines: list[str], target_indent: int, source_indent: int
) -> list[str]:
    """Adjust content lines to match target indentation."""
    indent_delta = target_indent - source_indent
    result = []
    for line in content_lines:
        if line.strip():
            current_indent = len(line) - len(line.lstrip())
            new_indent = max(0, current_indent + indent_delta)
            result.append(' ' * new_indent + line.lstrip())
        else:
            result.append('')
    return result


def validate_replace_params(
    file_path: str | None, start_line: int | None, end_line: int | None, new_content: str | None
) -> str | None:
    """Validate replace_lines parameters. Returns error message or None."""
    if not file_path:
        return "Missing file_path"
    if start_line is None or end_line is None:
        return "Missing start_line or end_line"
    if new_content is None:
        return "Missing new_content"
    return None


def validate_insert_params(
    file_path: str | None, line_number: int | None, new_content: str | None
) -> str | None:
    """Validate insert_lines parameters. Returns error message or None."""
    if not file_path:
        return "Missing file_path"
    if line_number is None:
        return "Missing line_number"
    if new_content is None:
        return "Missing new_content"
    return None


def extract_function_name_from_output(output: str) -> str | None:
    """Extract function name from check output using known patterns."""
    patterns = [
        r"Function '([^']+)' has complexity \d+",
        r"Function '([^']+)' has \d+ lines",
        r"Function '([^']+)' has nesting depth \d+",
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return None
