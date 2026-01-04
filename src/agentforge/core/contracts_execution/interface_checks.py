"""
Interface Implementation Check Handlers
======================================

AST-based interface implementation validation.
"""

import re

from .types import CheckContext, CheckResult


# Regex patterns for extracting class definitions with inheritance
_CLASS_WITH_INHERITANCE = {
    # C#: class ClassName : BaseClass, IInterface1, IInterface2
    ".cs": r'(?:public|internal|private|protected)?\s*'
           r'(?:sealed|abstract|static|partial\s+)*'
           r'class\s+(\w+)(?:\s*:\s*([^{]+))?',
    # Python: class ClassName(Base1, Base2)
    ".py": r'class\s+(\w+)\s*(?:\(([^)]*)\))?',
    # TypeScript: class ClassName extends Base implements Interface
    ".ts": r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)'
           r'(?:\s+extends\s+(\w+))?'
           r'(?:\s+implements\s+([^{]+))?',
}


def build_bases_string(match: re.Match, file_suffix: str) -> str:
    """Build inheritance string from regex match based on language."""
    if file_suffix == ".ts":
        # TypeScript has separate extends and implements groups
        bases = []
        if match.lastindex >= 2 and match.group(2):
            bases.append(match.group(2))
        if match.lastindex >= 3 and match.group(3):
            bases.append(match.group(3))
        return ", ".join(bases) if bases else ""
    return match.group(2) if match.lastindex >= 2 else ""


def extract_class_with_bases(content: str, file_suffix: str) -> list[tuple]:
    """
    Extract classes with their base classes/interfaces.

    Returns list of (class_name, bases_string, line_number) tuples.
    """
    pattern_str = _CLASS_WITH_INHERITANCE.get(file_suffix)
    if not pattern_str:
        return []

    classes = []
    try:
        pattern = re.compile(pattern_str, re.MULTILINE)
        for match in pattern.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            class_name = match.group(1)
            bases_str = build_bases_string(match, file_suffix)
            classes.append((class_name, bases_str or "", line_num))
    except re.error:
        pass

    return classes


def parse_inheritance_list(bases_str: str, file_suffix: str) -> list[str]:
    """Parse inheritance string into list of base/interface names."""
    if not bases_str:
        return []

    # Split by comma and clean up
    bases = [b.strip() for b in bases_str.split(",")]

    # Extract just the type name (remove generic parameters like <T>)
    result = []
    for base in bases:
        # Remove generic parameters
        name = re.sub(r'<[^>]*>', '', base).strip()
        # Remove 'where' clauses (C#)
        name = name.split()[0] if name else ""
        if name:
            result.append(name)

    return result


def has_interface(implemented: list[str], interface: str) -> bool:
    """Check if interface is in the implemented list (supports partial matches)."""
    return any(impl == interface or impl.startswith(interface) for impl in implemented)


def check_class_interfaces(
    ctx: CheckContext, class_info: tuple, rel_path: str, suffix: str
) -> list[CheckResult]:
    """Check a single class against interface requirements from ctx.config."""
    class_name, bases_str, line_num = class_info
    implemented = parse_inheritance_list(bases_str, suffix)
    must_impl = ctx.config.get("must_implement", [])
    must_not_impl = ctx.config.get("must_not_implement", [])
    results = []

    for required in must_impl:
        if not has_interface(implemented, required):
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, fix_hint=ctx.fix_hint,
                message=f"Class '{class_name}' must implement '{required}'",
                file_path=rel_path, line_number=line_num
            ))

    for forbidden in must_not_impl:
        if has_interface(implemented, forbidden):
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, fix_hint=ctx.fix_hint,
                message=f"Class '{class_name}' must not implement '{forbidden}'",
                file_path=rel_path, line_number=line_num
            ))

    return results


def execute_ast_interface_check(ctx: CheckContext) -> list[CheckResult]:
    """Execute an AST-based structural check (interface implementation or return type)."""
    # Delegate to return type check if return_pattern is specified
    if ctx.config.get("return_pattern"):
        from .return_type_checks import execute_return_type_check
        return execute_return_type_check(ctx)

    class_pattern_str = ctx.config.get("class_pattern")

    if not class_pattern_str:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message="AST check missing 'class_pattern' or 'return_pattern' in config"
        )]
    try:
        class_pattern = re.compile(class_pattern_str)
    except re.error as e:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message=f"Invalid class pattern: {e}"
        )]

    results = []
    for file_path in ctx.file_paths:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        classes = extract_class_with_bases(content, file_path.suffix)
        rel_path = str(file_path.relative_to(ctx.repo_root))
        for cls in classes:
            if class_pattern.match(cls[0]):
                results.extend(check_class_interfaces(ctx, cls, rel_path, file_path.suffix))
    return results
