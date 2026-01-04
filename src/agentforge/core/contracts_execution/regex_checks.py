"""
Regex Check Handlers
====================

Pattern matching checks using regular expressions.
"""

import re
from pathlib import Path

from .types import CheckContext, CheckResult


def compile_regex(pattern: str, multiline: bool, case_insensitive: bool):
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


def check_forbid_matches(matches, content: str, ctx: CheckContext,
                         file_path: Path) -> list[CheckResult]:
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


def execute_regex_check(ctx: CheckContext) -> list[CheckResult]:
    """Execute a regex-based check."""
    pattern = ctx.config.get("pattern")
    mode = ctx.config.get("mode", "forbid")

    if not pattern:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity="error", message="Regex check missing 'pattern' in config")]

    regex, error = compile_regex(pattern, ctx.config.get("multiline", False),
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
            results.extend(check_forbid_matches(matches, content, ctx, file_path))
        elif mode == "require" and not matches:
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, message=f"Required pattern not found: '{pattern}'",
                file_path=str(file_path.relative_to(ctx.repo_root)), fix_hint=ctx.fix_hint
            ))

    return results
