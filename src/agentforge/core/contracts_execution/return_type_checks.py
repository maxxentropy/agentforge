"""
Return Type Check Handlers
==========================

Method return type pattern validation.
"""

import re

from .types import CheckContext, CheckResult


# Regex patterns for extracting method signatures with return types
_METHOD_PATTERNS = {
    # C#: public async Task<Result<T>> MethodName(...)
    ".cs": r'(?P<visibility>public|private|protected|internal)\s+'
           r'(?:static\s+)?(?:virtual\s+)?(?:override\s+)?(?:async\s+)?'
           r'(?P<return_type>[\w<>\[\],\s\?]+?)\s+'
           r'(?P<name>\w+)\s*\([^)]*\)',
    # Python: def method_name(...) -> ReturnType:
    ".py": r'def\s+(?P<name>\w+)\s*\([^)]*\)\s*->\s*(?P<return_type>[^:]+):',
    # TypeScript: public async methodName(...): Promise<Result<T>>
    ".ts": r'(?P<visibility>public|private|protected)?\s*(?:async\s+)?'
           r'(?P<name>\w+)\s*\([^)]*\)\s*:\s*(?P<return_type>[^{]+)',
}


# Names that should be skipped (constructors, accessors, keywords)
_SKIP_METHOD_NAMES = frozenset({
    "get", "set", "init", "if", "while", "for", "foreach",
    "switch", "catch", "using", "lock", "fixed"
})


def get_method_visibility(match: re.Match) -> str:
    """Get visibility from regex match, defaulting to public."""
    try:
        return match.group("visibility") or "public"
    except IndexError:
        return "public"


def should_include_method(name: str, visibility: str, scope: str) -> bool:
    """Check if method should be included based on name and scope."""
    if name in _SKIP_METHOD_NAMES:
        return False
    if scope == "public" and visibility != "public":
        return False
    if scope == "private" and visibility not in ("private", "protected"):
        return False
    return True


def extract_methods_with_return_types(
    content: str, file_suffix: str, scope: str = "public"
) -> list[tuple]:
    """
    Extract methods with their return types.

    Returns list of (method_name, return_type, line_number, visibility) tuples.
    """
    pattern_str = _METHOD_PATTERNS.get(file_suffix)
    if not pattern_str:
        return []

    methods = []
    try:
        pattern = re.compile(pattern_str, re.MULTILINE)
        for match in pattern.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            name = match.group("name")
            return_type = match.group("return_type").strip()
            visibility = get_method_visibility(match)

            if should_include_method(name, visibility, scope):
                methods.append((name, return_type, line_num, visibility))
    except re.error:
        pass

    return methods


def is_return_type_excluded(return_type: str, exclude_types: list[str]) -> bool:
    """Check if a return type should be excluded from checking."""
    for excluded in exclude_types:
        if return_type == excluded or return_type.startswith(excluded + " "):
            return True
        if excluded == "Task" and return_type == "Task":
            return True
    return False


def check_method_return_type(
    ctx: CheckContext, method: tuple, pattern: re.Pattern, rel_path: str
) -> CheckResult | None:
    """Check a single method's return type, return violation or None."""
    method_name, return_type, line_num, _ = method
    exclude_methods = ctx.config.get("exclude_methods", [])
    exclude_types = ctx.config.get("exclude_return_types", ["void", "Task", "IActionResult", "ActionResult"])
    if method_name in exclude_methods:
        return None
    if is_return_type_excluded(return_type, exclude_types):
        return None
    if pattern.search(return_type):
        return None
    pattern_str = ctx.config.get("return_pattern", "")
    return CheckResult(
        check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
        severity=ctx.severity, fix_hint=ctx.fix_hint,
        message=f"Method '{method_name}' returns '{return_type}', expected pattern '{pattern_str}'",
        file_path=rel_path, line_number=line_num
    )


def execute_return_type_check(ctx: CheckContext) -> list[CheckResult]:
    """Execute a return type pattern check."""
    return_pattern_str = ctx.config.get("return_pattern")
    method_scope = ctx.config.get("method_scope", "public")

    if not return_pattern_str:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message="Return type check missing 'return_pattern' in config"
        )]
    try:
        return_pattern = re.compile(return_pattern_str)
    except re.error as e:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message=f"Invalid return pattern: {e}"
        )]

    results = []
    for file_path in ctx.file_paths:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        methods = extract_methods_with_return_types(content, file_path.suffix, method_scope)
        rel_path = str(file_path.relative_to(ctx.repo_root))
        for method in methods:
            violation = check_method_return_type(ctx, method, return_pattern, rel_path)
            if violation:
                results.append(violation)
    return results
