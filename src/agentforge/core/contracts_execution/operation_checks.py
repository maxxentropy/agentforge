"""
Operation Contract Check Handlers
=================================

Unified operation contract check types:
- code_metric: Function length, complexity checks
- naming_convention: Boolean naming, descriptive names
- safety_pattern: Hardcoded secrets detection
- Advisory checks: Design principles, patterns (documentation only)
"""

import ast

from .types import CheckContext, CheckResult


def execute_code_metric_check(ctx: CheckContext) -> list[CheckResult]:
    """
    Execute code metric checks (function length, complexity, etc.).

    Delegates to the AST check infrastructure with metric-specific config.
    """
    try:
        from ..contracts_ast import execute_ast_check
    except ImportError:
        from contracts_ast import execute_ast_check

    return execute_ast_check(ctx)


# Naming convention constants
_BOOL_PREFIXES = ("is_", "has_", "can_", "should_", "will_", "did_", "was_")
_BAD_NAMES = {"data", "info", "temp", "tmp", "val", "value", "item", "obj", "result", "res"}
_ALLOWED_SHORT = {"i", "j", "k", "x", "y", "z", "e", "f", "n", "_", "id", "db"}


def check_boolean_naming(node, ctx: CheckContext, rel_path: str) -> CheckResult | None:
    """Check if boolean function follows naming convention."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    if not (node.returns and isinstance(node.returns, ast.Name) and node.returns.id == "bool"):
        return None
    name = node.name.lstrip("_")
    if name.startswith(_BOOL_PREFIXES):
        return None
    return CheckResult(
        check_id=ctx.check_id, check_name=ctx.check_name,
        passed=False, severity=ctx.severity,
        message=f"Boolean function '{node.name}' should start with is_/has_/can_/should_",
        file_path=rel_path, line_number=node.lineno,
        fix_hint="Rename to express a yes/no question"
    )


def check_descriptive_naming(node, ctx: CheckContext, rel_path: str) -> list[CheckResult]:
    """Check if function/variable names are descriptive."""
    results = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = node.name
        if not name.startswith("_") and len(name) <= 2 and name not in _ALLOWED_SHORT:
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name,
                passed=False, severity=ctx.severity,
                message=f"Function name '{name}' is too short to be descriptive",
                file_path=rel_path, line_number=node.lineno,
                fix_hint="Use descriptive names that reveal intent"
            ))
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.lower() in _BAD_NAMES:
                results.append(CheckResult(
                    check_id=ctx.check_id, check_name=ctx.check_name,
                    passed=False, severity="info",
                    message=f"Variable name '{target.id}' is generic",
                    file_path=rel_path, line_number=node.lineno,
                    fix_hint="Name should describe what the variable contains"
                ))
    return results


def execute_naming_convention_check(ctx: CheckContext) -> list[CheckResult]:
    """
    Execute naming convention checks (boolean naming, descriptive names, etc.).

    Uses AST to find functions/variables and check naming patterns.
    """
    results = []
    check_id = ctx.check_id

    for file_path in ctx.file_paths:
        if file_path.suffix != ".py":
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, Exception):
            continue

        rel_path = str(file_path.relative_to(ctx.repo_root))

        for node in ast.walk(tree):
            if check_id == "boolean-naming":
                if result := check_boolean_naming(node, ctx, rel_path):
                    results.append(result)
            elif check_id == "descriptive-naming":
                results.extend(check_descriptive_naming(node, ctx, rel_path))

    return results


def execute_safety_pattern_check(ctx: CheckContext) -> list[CheckResult]:
    """
    Execute safety pattern checks (hardcoded secrets, etc.).

    Delegates to builtin safety checks.
    """
    check_id = ctx.check_id

    if check_id == "no-secrets-in-code":
        try:
            from ..builtin_checks import check_hardcoded_secrets
        except ImportError:
            from builtin_checks import check_hardcoded_secrets

        raw_results = check_hardcoded_secrets(ctx.repo_root, ctx.file_paths)
        return [
            CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name,
                passed=False, severity=r.get("severity", ctx.severity),
                message=r.get("message", ""),
                file_path=r.get("file", ""),
                line_number=r.get("line"),
                fix_hint=r.get("fix_hint")
            )
            for r in raw_results
        ]

    # For other safety patterns, return empty (not yet implemented)
    return []


def execute_advisory_check(ctx: CheckContext) -> list[CheckResult]:
    """
    Execute advisory-only checks (design principles, patterns, etc.).

    These checks are not automatable but provide guidance.
    They always pass - the rationale is shown in documentation.
    """
    # Advisory checks don't produce violations programmatically
    # They serve as documentation and guidance for AI agents
    return []
