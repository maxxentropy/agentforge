"""
File Existence Check Handlers
=============================

File existence and forbidden file checks.
"""

import subprocess
from pathlib import Path

from .types import CheckContext, CheckResult


def is_gitignored(file_path: Path, repo_root: Path) -> bool:
    """Check if a file is ignored by git."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(file_path)],
            cwd=repo_root,
            capture_output=True,
        )
        return result.returncode == 0  # 0 means ignored
    except Exception:
        return False  # If git fails, assume not ignored


def execute_file_exists_check(ctx: CheckContext) -> list[CheckResult]:
    """Execute a file existence check."""
    required_files = ctx.config.get("required_files", [])
    forbidden_files = ctx.config.get("forbidden_files", [])
    only_tracked = ctx.config.get("only_tracked", True)  # Skip gitignored by default

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
            # Skip gitignored files when only_tracked is True
            if only_tracked and is_gitignored(match, ctx.repo_root):
                continue
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, fix_hint=ctx.fix_hint,
                message=f"Forbidden file exists: '{match.relative_to(ctx.repo_root)}'",
                file_path=str(match.relative_to(ctx.repo_root))
            ))

    return results
