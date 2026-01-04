"""
File/Directory Checks
=====================

Checks for file properties (size, line length, whitespace, line endings).
"""

import re
from pathlib import Path


def check_file_size(repo_root: Path, file_paths: list[Path],
                    max_lines: int = 500,
                    max_bytes: int = 50000) -> list[dict]:
    """
    Check that files don't exceed size limits.
    """
    violations = []

    for file_path in file_paths:
        try:
            stat = file_path.stat()
            if stat.st_size > max_bytes:
                violations.append({
                    "message": f"File exceeds size limit ({stat.st_size} bytes > {max_bytes})",
                    "file": str(file_path.relative_to(repo_root)),
                    "severity": "warning",
                    "fix_hint": "Consider splitting into smaller files"
                })
                continue

            content = file_path.read_text(encoding='utf-8', errors='ignore')
            line_count = len(content.split('\n'))
            if line_count > max_lines:
                violations.append({
                    "message": f"File exceeds line limit ({line_count} lines > {max_lines})",
                    "file": str(file_path.relative_to(repo_root)),
                    "severity": "warning",
                    "fix_hint": "Consider splitting into smaller files"
                })
        except Exception:
            continue

    return violations


def check_line_length(repo_root: Path, file_paths: list[Path],
                      max_length: int = 120) -> list[dict]:
    """
    Check that lines don't exceed maximum length.
    """
    violations = []

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            if len(line) > max_length:
                violations.append({
                    "message": f"Line exceeds {max_length} characters ({len(line)} chars)",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "severity": "warning"
                })

    return violations


def check_trailing_whitespace(repo_root: Path, file_paths: list[Path]) -> list[dict]:
    """
    Check for trailing whitespace.
    """
    violations = []

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            if line.rstrip() != line:
                violations.append({
                    "message": "Line has trailing whitespace",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "severity": "info",
                    "fix_hint": "Remove trailing whitespace"
                })

    return violations


def check_mixed_line_endings(repo_root: Path, file_paths: list[Path]) -> list[dict]:
    """
    Check for mixed line endings (CRLF vs LF).
    """
    violations = []

    for file_path in file_paths:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except Exception:
            continue

        has_crlf = b'\r\n' in content
        # Check for LF not preceded by CR
        has_lf = bool(re.search(b'[^\r]\n', content)) or content.startswith(b'\n')

        if has_crlf and has_lf:
            violations.append({
                "message": "File has mixed line endings (CRLF and LF)",
                "file": str(file_path.relative_to(repo_root)),
                "severity": "warning",
                "fix_hint": "Normalize line endings to LF"
            })

    return violations
