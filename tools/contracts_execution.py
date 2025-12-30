#!/usr/bin/env python3
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

Extracted from contracts.py for modularity.
"""

import fnmatch
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .contracts_types import CheckResult
except ImportError:
    from contracts_types import CheckResult


@dataclass
class CheckContext:
    """Context object for check execution, grouping common parameters."""
    check_id: str
    check_name: str
    severity: str
    config: Dict[str, Any]
    repo_root: Path
    file_paths: List[Path]
    fix_hint: Optional[str] = None


def execute_check(check: Dict[str, Any], repo_root,
                  file_paths: Optional[List[Path]] = None) -> List[CheckResult]:
    """
    Execute a single check against the repo or specific files.

    Args:
        check: Check configuration from contract
        repo_root: Repository root directory (Path or str)
        file_paths: Optional list of specific files to check

    Returns:
        List of CheckResult for any violations found
    """
    # Ensure repo_root is a Path
    if not isinstance(repo_root, Path):
        repo_root = Path(repo_root)

    # Lazy import to avoid circular imports
    try:
        from .contracts_ast import execute_ast_check
        from .contracts_lsp import execute_lsp_query_check
    except ImportError:
        from contracts_ast import execute_ast_check
        from contracts_lsp import execute_lsp_query_check

    check_type = check.get("type")
    check_id = check.get("id", "unknown")
    check_name = check.get("name", check_id)
    severity = check.get("severity", "error")
    config = check.get("config", {})
    fix_hint = check.get("fix_hint")

    if file_paths is None:
        file_paths = _get_files_for_check(check, repo_root)

    ctx = CheckContext(
        check_id=check_id, check_name=check_name, severity=severity,
        config=config, repo_root=repo_root, file_paths=file_paths, fix_hint=fix_hint
    )

    handlers = {
        "regex": _execute_regex_check,
        "lsp_query": lambda c: execute_lsp_query_check(
            c.check_id, c.check_name, c.severity, c.config, c.repo_root, c.file_paths, c.fix_hint),
        "ast_check": lambda c: execute_ast_check(
            c.check_id, c.check_name, c.severity, c.config, c.repo_root, c.file_paths, c.fix_hint),
        "command": _execute_command_check,
        "file_exists": _execute_file_exists_check,
        "custom": _execute_custom_check,
    }

    handler = handlers.get(check_type)
    if handler is None:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity="error", message=f"Unknown check type: {check_type}"
        )]

    return handler(ctx)


def _get_files_for_check(check: Dict[str, Any], repo_root: Path) -> List[Path]:
    """Get list of files this check should run against."""
    applies_to = check.get("applies_to", {})
    paths = applies_to.get("paths", ["**/*"])
    exclude_paths = applies_to.get("exclude_paths", [])

    all_files = []
    for pattern in paths:
        all_files.extend(repo_root.glob(pattern))

    result = []
    for f in all_files:
        if not f.is_file():
            continue
        relative = str(f.relative_to(repo_root))
        excluded = any(fnmatch.fnmatch(relative, exc) for exc in exclude_paths)
        if not excluded:
            result.append(f)

    return result


# =============================================================================
# Regex Check
# =============================================================================

def _compile_regex(pattern: str, multiline: bool, case_insensitive: bool):
    """Compile regex with flags. Returns (regex, error_message)."""
    flags = 0
    if multiline:
        flags |= re.MULTILINE | re.DOTALL
    if case_insensitive:
        flags |= re.IGNORECASE
    try:
        return re.compile(pattern, flags), None
    except re.error as e:
        return None, str(e)


def _check_forbid_matches(matches, content: str, ctx: CheckContext,
                          file_path: Path) -> List[CheckResult]:
    """Generate results for forbidden pattern matches."""
    results = []
    for match in matches:
        line_num = content[:match.start()].count("\n") + 1
        results.append(CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity=ctx.severity, message=f"Forbidden pattern found: '{match.group()}'",
            file_path=str(file_path.relative_to(ctx.repo_root)), line_number=line_num,
            fix_hint=ctx.fix_hint
        ))
    return results


def _execute_regex_check(ctx: CheckContext) -> List[CheckResult]:
    """Execute a regex-based check."""
    pattern = ctx.config.get("pattern")
    mode = ctx.config.get("mode", "forbid")

    if not pattern:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity="error", message="Regex check missing 'pattern' in config")]

    regex, error = _compile_regex(pattern, ctx.config.get("multiline", False),
                                   ctx.config.get("case_insensitive", False))
    if error:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity="error", message=f"Invalid regex pattern: {error}")]

    results = []
    for file_path in ctx.file_paths:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        matches = list(regex.finditer(content))

        if mode == "forbid":
            results.extend(_check_forbid_matches(matches, content, ctx, file_path))
        elif mode == "require" and not matches:
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, message=f"Required pattern not found: '{pattern}'",
                file_path=str(file_path.relative_to(ctx.repo_root)), fix_hint=ctx.fix_hint
            ))

    return results


# =============================================================================
# Command Check
# =============================================================================

def _execute_command_check(ctx: CheckContext) -> List[CheckResult]:
    """Execute a command-based check."""
    command = ctx.config.get("command")
    args = ctx.config.get("args", [])
    working_dir = ctx.config.get("working_dir")
    timeout = ctx.config.get("timeout", 60)
    expected_exit_code = ctx.config.get("expected_exit_code", 0)

    if not command:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message="Command check missing 'command' in config"
        )]

    cwd = ctx.repo_root / working_dir if working_dir else ctx.repo_root

    try:
        result = subprocess.run(
            [command] + args, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != expected_exit_code:
            return [CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, fix_hint=ctx.fix_hint,
                message=f"Command failed with exit code {result.returncode}: {result.stderr or result.stdout}"
            )]

        return []

    except subprocess.TimeoutExpired:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity=ctx.severity, message=f"Command timed out after {timeout}s")]
    except FileNotFoundError:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity=ctx.severity, message=f"Command not found: {command}")]
    except Exception as e:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity="error", message=f"Command execution failed: {e}")]


# =============================================================================
# File Exists Check
# =============================================================================

def _execute_file_exists_check(ctx: CheckContext) -> List[CheckResult]:
    """Execute a file existence check."""
    required_files = ctx.config.get("required_files", [])
    forbidden_files = ctx.config.get("forbidden_files", [])

    results = []

    for pattern in required_files:
        matches = list(ctx.repo_root.glob(pattern))
        if not matches:
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, message=f"Required file not found: '{pattern}'",
                fix_hint=ctx.fix_hint
            ))

    for pattern in forbidden_files:
        for match in ctx.repo_root.glob(pattern):
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, fix_hint=ctx.fix_hint,
                message=f"Forbidden file exists: '{match.relative_to(ctx.repo_root)}'",
                file_path=str(match.relative_to(ctx.repo_root))
            ))

    return results


# =============================================================================
# Custom Check
# =============================================================================

def _execute_custom_check(ctx: CheckContext) -> List[CheckResult]:
    """Execute a custom Python check."""
    import importlib.util

    module_name = ctx.config.get("module")
    function_name = ctx.config.get("function")
    params = ctx.config.get("params", {})

    if not module_name or not function_name:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message="Custom check missing 'module' or 'function' in config"
        )]

    try:
        search_paths = [
            ctx.repo_root / "contracts" / "checks" / f"{module_name}.py",
            ctx.repo_root / ".agentforge" / "checks" / f"{module_name}.py",
            Path(__file__).parent / f"{module_name}.py",
        ]

        module_path = next((p for p in search_paths if p.exists()), None)
        if module_path is None:
            return [CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity="error", message=f"Custom check module not found: {module_name}"
            )]

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        func = getattr(module, function_name, None)
        if func is None:
            return [CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity="error", message=f"Function '{function_name}' not found in {module_name}"
            )]

        violations = func(ctx.repo_root, ctx.file_paths, **params)

        return [
            CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=v.get("severity", ctx.severity),
                message=v.get("message", "Custom check violation"),
                file_path=v.get("file"), line_number=v.get("line"),
                fix_hint=v.get("fix_hint", ctx.fix_hint)
            )
            for v in violations
        ]

    except Exception as e:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message=f"Custom check execution failed: {e}"
        )]
