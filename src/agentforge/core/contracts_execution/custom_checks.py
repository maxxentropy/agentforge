"""
Custom Check Handlers
=====================

Python module-based custom checks.
"""

import importlib
import importlib.util
from pathlib import Path

from .types import CheckContext, CheckResult


def load_custom_module(module_name: str, repo_root: Path):
    """Load a custom check module by name. Returns module or None."""
    # First, try to import builtin_checks as a proper package module
    if module_name == "builtin_checks":
        try:
            return importlib.import_module("agentforge.core.builtin_checks")
        except ImportError:
            pass

    # Search for the module file
    search_paths = [
        repo_root / "contracts" / "checks" / f"{module_name}.py",
        repo_root / ".agentforge" / "checks" / f"{module_name}.py",
        Path(__file__).parent.parent / f"{module_name}.py",
    ]
    module_path = next((p for p in search_paths if p.exists()), None)
    if module_path is None:
        return None

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute_custom_check(ctx: CheckContext) -> list[CheckResult]:
    """Execute a custom Python check."""
    module_name = ctx.config.get("module")
    function_name = ctx.config.get("function")
    params = ctx.config.get("params", {})

    if not module_name or not function_name:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message="Custom check missing 'module' or 'function' in config"
        )]
    try:
        module = load_custom_module(module_name, ctx.repo_root)
        if module is None:
            return [CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity="error", message=f"Custom check module not found: {module_name}"
            )]
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
                severity=v.get("severity", ctx.severity), message=v.get("message", "Custom check violation"),
                file_path=v.get("file"), line_number=v.get("line"), fix_hint=v.get("fix_hint", ctx.fix_hint)
            )
            for v in violations
        ]
    except Exception as e:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message=f"Custom check execution failed: {e}"
        )]
