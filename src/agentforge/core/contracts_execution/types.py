"""
Check Execution Types
=====================

Common types and utilities for check execution.
"""

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from ..contracts_types import CheckResult
except ImportError:
    from contracts_types import CheckResult


@dataclass
class CheckContext:
    """Context object for check execution, grouping common parameters."""
    check_id: str
    check_name: str
    severity: str
    config: dict[str, Any]
    repo_root: Path
    file_paths: list[Path]
    fix_hint: str | None = None


def normalize_file_paths(file_paths: list | None, check: dict, repo_root: Path) -> list[Path]:
    """Normalize file paths list, resolving strings to Paths."""
    if file_paths is None:
        return get_files_for_check(check, repo_root)
    return [f if isinstance(f, Path) else repo_root / f for f in file_paths]


def get_files_for_check(check: dict[str, Any], repo_root: Path) -> list[Path]:
    """Get list of files this check should run against."""
    applies_to = check.get("applies_to", {})
    paths = applies_to.get("paths", ["**/*"])
    exclude_paths = applies_to.get("exclude_paths", [])

    # Global exclusions - internal directories that should never be checked
    global_excludes = [
        ".agentforge/**",
        ".git/**",
        "__pycache__/**",
        "*.pyc",
        ".venv/**",
        "venv/**",
        "node_modules/**",
    ]

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
            excluded = any(fnmatch.fnmatch(relative, exc) for exc in global_excludes)
        if not excluded:
            result.append(f)

    return result


# Re-export CheckResult for convenience
__all__ = ["CheckContext", "CheckResult", "normalize_file_paths", "get_files_for_check"]
