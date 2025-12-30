"""
Built-in check implementations for AgentForge contracts.

These functions provide reusable checks that can be invoked from contracts
using the 'custom' check type. They are specifically designed for tasks
that cannot be done via LSP (text patterns, file operations, etc.).

NOTE: For semantic code analysis (public fields, method naming, etc.),
use `lsp_query` check type instead - it leverages our LSP adapters for
accurate, parser-based analysis.

Each function follows the signature:
    func(repo_root: Path, file_paths: List[Path], **params) -> List[Dict]

Return format:
    [
        {
            "message": "Description of the violation",
            "file": "relative/path/to/file.cs",
            "line": 42,
            "severity": "error",  # Optional, defaults to check's severity
            "fix_hint": "How to fix this"  # Optional
        }
    ]
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


# ==============================================================================
# Text Pattern Checks (appropriate for regex)
# ==============================================================================

def check_todo_comments(repo_root: Path, file_paths: List[Path],
                        require_ticket: bool = False,
                        ticket_patterns: Optional[List[str]] = None) -> List[Dict]:
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
            if match:
                if require_ticket and not ticket_regex.search(line):
                    violations.append({
                        "message": f"{match.group(1)} comment without ticket reference",
                        "file": str(file_path.relative_to(repo_root)),
                        "line": line_num,
                        "severity": "warning",
                        "fix_hint": "Add ticket reference (e.g., TODO(AB#1234): ...)"
                    })

    return violations


def check_debug_statements(repo_root: Path, file_paths: List[Path],
                           patterns: Optional[List[str]] = None) -> List[Dict]:
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


# ==============================================================================
# File/Directory Checks
# ==============================================================================

def check_file_size(repo_root: Path, file_paths: List[Path],
                    max_lines: int = 500,
                    max_bytes: int = 50000) -> List[Dict]:
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


def check_line_length(repo_root: Path, file_paths: List[Path],
                      max_length: int = 120) -> List[Dict]:
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


def check_trailing_whitespace(repo_root: Path, file_paths: List[Path]) -> List[Dict]:
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


def check_mixed_line_endings(repo_root: Path, file_paths: List[Path]) -> List[Dict]:
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


# ==============================================================================
# Security Pattern Checks (appropriate for regex)
# ==============================================================================

def check_hardcoded_secrets(repo_root: Path, file_paths: List[Path],
                            additional_patterns: Optional[List[str]] = None) -> List[Dict]:
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


# ==============================================================================
# Architecture Checks (AST-based semantic analysis)
# ==============================================================================
# These are imported from a separate module to keep file size manageable

from builtin_checks_architecture import (
    check_layer_imports,
    check_constructor_injection,
    check_domain_purity,
    check_circular_imports,
)

# ==============================================================================
# Registry of built-in checks
# ==============================================================================

BUILTIN_CHECKS = {
    # Text patterns
    "todo_comments": check_todo_comments,
    "debug_statements": check_debug_statements,
    "hardcoded_secrets": check_hardcoded_secrets,

    # File operations
    "file_size": check_file_size,
    "line_length": check_line_length,
    "trailing_whitespace": check_trailing_whitespace,
    "mixed_line_endings": check_mixed_line_endings,

    # Architecture checks (AST-based)
    "layer_imports": check_layer_imports,
    "constructor_injection": check_constructor_injection,
    "domain_purity": check_domain_purity,
    "circular_imports": check_circular_imports,
}


def get_builtin_check(name: str):
    """Get a built-in check function by name."""
    return BUILTIN_CHECKS.get(name)


def list_builtin_checks() -> List[str]:
    """List all available built-in checks."""
    return list(BUILTIN_CHECKS.keys())
