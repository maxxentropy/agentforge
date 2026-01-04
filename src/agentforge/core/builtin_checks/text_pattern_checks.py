"""
Text Pattern Checks
===================

Checks for text patterns in code files (TODOs, debug statements, secrets).
"""

import re
from pathlib import Path


def check_todo_comments(repo_root: Path, file_paths: list[Path],
                        require_ticket: bool = False,
                        ticket_patterns: list[str] | None = None) -> list[dict]:
    """
    Check for TODO/FIXME comments, optionally requiring ticket references.

    Args:
        require_ticket: If True, TODOs must have a ticket reference
        ticket_patterns: Patterns to match ticket references (e.g., ['AB#\\d+', 'JIRA-\\d+'])
    """
    violations = []
    ticket_patterns = ticket_patterns or [r'AB#\d+', r'[A-Z]+-\d+', r'GH#\d+']
    ticket_regex = re.compile('|'.join(ticket_patterns))

    todo_pattern = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE)

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            match = todo_pattern.search(line)
            if match and require_ticket and not ticket_regex.search(line):
                violations.append({
                    "message": f"{match.group(1)} comment without ticket reference",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "severity": "warning",
                    "fix_hint": "Add ticket reference (e.g., TODO(AB#1234): ...)"
                })

    return violations


def check_debug_statements(repo_root: Path, file_paths: list[Path],
                           patterns: list[str] | None = None) -> list[dict]:
    """
    Check for debug statements that shouldn't be committed.

    This is appropriate for regex since we're looking for specific text patterns
    like console.log, print(), debugger, etc.

    Args:
        patterns: Additional patterns to check for (beyond defaults)
    """
    violations = []

    # Default debug patterns per file type
    default_patterns = {
        '.py': [r'\bprint\s*\(', r'\bbreakpoint\s*\(', r'\bpdb\.set_trace\s*\('],
        '.js': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
        '.jsx': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
        '.ts': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
        '.tsx': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
    }

    for file_path in file_paths:
        suffix = file_path.suffix.lower()
        file_patterns = default_patterns.get(suffix, [])
        if patterns:
            file_patterns = file_patterns + patterns

        if not file_patterns:
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        combined = re.compile('|'.join(file_patterns))

        for line_num, line in enumerate(content.split('\n'), 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith(('#', '//', '/*', '*')):
                continue

            match = combined.search(line)
            if match:
                violations.append({
                    "message": f"Debug statement found: {match.group(0)[:30]}",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "fix_hint": "Remove debug statements before committing"
                })

    return violations


def check_hardcoded_secrets(repo_root: Path, file_paths: list[Path],
                            additional_patterns: list[str] | None = None) -> list[dict]:
    """
    Check for potential hardcoded secrets in code.

    This uses regex patterns to find potential secrets in string literals.
    It's appropriate for regex since we're looking for text patterns.
    """
    violations = []

    # Patterns that might indicate hardcoded secrets
    secret_patterns = [
        # API keys and tokens
        (r'["\'](?:api[_-]?key|apikey)["\']?\s*[=:]\s*["\'][a-zA-Z0-9]{20,}["\']', "API key"),
        (r'["\'](?:secret|token)["\']?\s*[=:]\s*["\'][a-zA-Z0-9]{20,}["\']', "Secret/Token"),
        # Passwords
        (r'(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', "Password"),
        # AWS
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
        (r'[a-zA-Z0-9/+=]{40}', "Potential AWS Secret Key"),
        # Connection strings
        (r'(?:mongodb|postgres|mysql|redis)://[^"\'\s]+', "Database connection string"),
    ]

    if additional_patterns:
        secret_patterns.extend([(p, "Custom pattern") for p in additional_patterns])

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for pattern, secret_type in secret_patterns:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                for match in regex.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    violations.append({
                        "message": f"Potential {secret_type} found",
                        "file": str(file_path.relative_to(repo_root)),
                        "line": line_num,
                        "severity": "error",
                        "fix_hint": "Use environment variables or a secrets manager"
                    })
            except re.error:
                continue

    return violations
