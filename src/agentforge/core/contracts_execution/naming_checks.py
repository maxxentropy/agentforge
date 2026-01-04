"""
Naming Convention Check Handlers
================================

Symbol naming pattern checks.
"""

import re

from .types import CheckContext, CheckResult

# Regex patterns for extracting symbol names by language
_SYMBOL_PATTERNS = {
    "class": {
        ".cs": r'(?:public|internal|private|protected)?\s*'
               r'(?:sealed|abstract|static|partial\s+)*'
               r'class\s+(\w+)',
        ".py": r'class\s+(\w+)',
        ".ts": r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)',
        ".js": r'class\s+(\w+)',
    },
    "interface": {
        ".cs": r'(?:public|internal|private|protected)?\s*'
               r'(?:partial\s+)?interface\s+(\w+)',
        ".ts": r'(?:export\s+)?interface\s+(\w+)',
    },
    "method": {
        ".cs": r'(?:public|internal|private|protected)\s+'
               r'(?:static\s+)?(?:virtual\s+)?(?:override\s+)?(?:async\s+)?'
               r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(',
        ".py": r'def\s+(\w+)\s*\(',
        ".ts": r'(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*[:{]',
    },
}


def get_symbol_pattern(symbol_type: str, file_suffix: str) -> str | None:
    """Get regex pattern for extracting symbols of given type from file."""
    type_patterns = _SYMBOL_PATTERNS.get(symbol_type, {})
    return type_patterns.get(file_suffix)


def extract_symbols(content: str, symbol_type: str, file_suffix: str) -> list[tuple]:
    """Extract symbols from file content. Returns list of (name, line_number) tuples."""
    pattern_str = get_symbol_pattern(symbol_type, file_suffix)
    if not pattern_str:
        return []

    symbols = []
    try:
        pattern = re.compile(pattern_str, re.MULTILINE)
        for match in pattern.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            symbols.append((match.group(1), line_num))
    except re.error:
        pass

    return symbols


def check_symbol_naming(
    ctx: CheckContext, symbol: tuple, pattern: re.Pattern, rel_path: str
) -> CheckResult | None:
    """Check if a symbol name violates the naming convention from ctx.config."""
    name, line_num = symbol
    symbol_type = ctx.config.get("symbol_type", "class")
    pattern_str = ctx.config.get("pattern", "")
    mode = ctx.config.get("mode", "require")
    is_match = pattern.match(name) is not None

    if mode == "require" and not is_match:
        return CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity=ctx.severity, fix_hint=ctx.fix_hint,
            message=f"{symbol_type.capitalize()} '{name}' does not match required pattern '{pattern_str}'",
            file_path=rel_path, line_number=line_num
        )
    if mode == "forbid" and is_match:
        return CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity=ctx.severity, fix_hint=ctx.fix_hint,
            message=f"{symbol_type.capitalize()} '{name}' matches forbidden pattern '{pattern_str}'",
            file_path=rel_path, line_number=line_num
        )
    return None


def execute_naming_check(ctx: CheckContext) -> list[CheckResult]:
    """Execute a naming convention check (pattern matching on symbol names)."""
    pattern_str = ctx.config.get("pattern")
    symbol_type = ctx.config.get("symbol_type", "class")

    if not pattern_str:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message="Naming check missing 'pattern' in config"
        )]
    try:
        name_pattern = re.compile(pattern_str)
    except re.error as e:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message=f"Invalid naming pattern: {e}"
        )]

    results = []
    for file_path in ctx.file_paths:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        symbols = extract_symbols(content, symbol_type, file_path.suffix)
        rel_path = str(file_path.relative_to(ctx.repo_root))
        for symbol in symbols:
            violation = check_symbol_naming(ctx, symbol, name_pattern, rel_path)
            if violation:
                results.append(violation)
    return results
