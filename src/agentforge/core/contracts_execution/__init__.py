#!/usr/bin/env python3

# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-contracts_execution
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

"""
Contract Check Execution
========================

Functions for executing individual contract checks.

Check types:
- regex: Pattern matching
- lsp_query: LSP-based semantic checks
- ast_check: AST-based code metrics
- command: Shell command execution
- file_exists: File existence checks
- custom: Custom Python functions
- naming: Symbol naming conventions
- ast: Interface implementation checks

Operation contract check types:
- code_metric: Function length, complexity
- naming_convention: Boolean naming, descriptive names
- safety_pattern: Hardcoded secrets detection
- Advisory types: Design principles, patterns (documentation only)

Extracted from contracts.py for modularity.
"""

from pathlib import Path
from typing import Any

from .types import CheckContext, CheckResult, normalize_file_paths, get_files_for_check

# Handler imports
from .regex_checks import execute_regex_check
from .command_checks import execute_command_check
from .file_checks import execute_file_exists_check
from .custom_checks import execute_custom_check
from .naming_checks import (
    execute_naming_check,
    extract_symbols,
    get_symbol_pattern,
    check_symbol_naming,
)
from .interface_checks import (
    execute_ast_interface_check,
    extract_class_with_bases,
    parse_inheritance_list,
    build_bases_string,
    has_interface,
    check_class_interfaces,
)
from .operation_checks import (
    execute_code_metric_check,
    execute_naming_convention_check,
    execute_safety_pattern_check,
    execute_advisory_check,
)

# Backwards-compatible aliases (with underscore prefix for internal functions)
_execute_regex_check = execute_regex_check
_execute_command_check = execute_command_check
_execute_file_exists_check = execute_file_exists_check
_execute_custom_check = execute_custom_check
_execute_naming_check = execute_naming_check
_execute_ast_interface_check = execute_ast_interface_check
_extract_symbols = extract_symbols
_get_symbol_pattern = get_symbol_pattern
_check_symbol_naming = check_symbol_naming
_extract_class_with_bases = extract_class_with_bases
_parse_inheritance_list = parse_inheritance_list
_build_bases_string = build_bases_string
_has_interface = has_interface
_check_class_interfaces = check_class_interfaces
_execute_code_metric_check = execute_code_metric_check
_execute_naming_convention_check = execute_naming_convention_check
_execute_safety_pattern_check = execute_safety_pattern_check
_execute_advisory_check = execute_advisory_check


def _get_check_handlers() -> dict:
    """Get check type handlers. Lazy import to avoid circular imports."""
    try:
        from ..contracts_ast import execute_ast_check
        from ..contracts_lsp import execute_lsp_query_check
    except ImportError:
        from contracts_ast import execute_ast_check
        from contracts_lsp import execute_lsp_query_check

    return {
        # Original check types
        "regex": execute_regex_check,
        "lsp_query": execute_lsp_query_check,
        "ast_check": execute_ast_check,
        "command": execute_command_check,
        "file_exists": execute_file_exists_check,
        "custom": execute_custom_check,
        "naming": execute_naming_check,
        "ast": execute_ast_interface_check,
        # Operation contract check types (unified)
        "code_metric": execute_code_metric_check,
        "naming_convention": execute_naming_convention_check,
        "safety_pattern": execute_safety_pattern_check,
        # Advisory-only types (not automatable, always pass)
        "design_principle": execute_advisory_check,
        "design_pattern": execute_advisory_check,
        "code_smell": execute_advisory_check,
        "consistency": execute_advisory_check,
        "change_scope": execute_advisory_check,
        "api_stability": execute_advisory_check,
    }


def execute_check(check: dict[str, Any], repo_root, file_paths: list[Path] | None = None) -> list[CheckResult]:
    """Execute a single check against the repo or specific files."""
    if not isinstance(repo_root, Path):
        repo_root = Path(repo_root)

    check_id, check_name = check.get("id", "unknown"), check.get("name", check.get("id", "unknown"))
    ctx = CheckContext(
        check_id=check_id, check_name=check_name,
        severity=check.get("severity", "error"), config=check.get("config", {}),
        repo_root=repo_root, file_paths=normalize_file_paths(file_paths, check, repo_root),
        fix_hint=check.get("fix_hint")
    )

    handler = _get_check_handlers().get(check.get("type"))
    if handler is None:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity="error", message=f"Unknown check type: {check.get('type')}"
        )]
    return handler(ctx)


# Re-export for backwards compatibility
__all__ = [
    "CheckContext",
    "CheckResult",
    "execute_check",
    "normalize_file_paths",
    "get_files_for_check",
    # Individual check handlers (for direct use if needed)
    "execute_regex_check",
    "execute_command_check",
    "execute_file_exists_check",
    "execute_custom_check",
    "execute_naming_check",
    "execute_ast_interface_check",
    "execute_code_metric_check",
    "execute_naming_convention_check",
    "execute_safety_pattern_check",
    "execute_advisory_check",
]
