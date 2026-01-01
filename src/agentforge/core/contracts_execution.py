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
    else:
        # Ensure file_paths are Path objects (CLI may pass strings)
        file_paths = [
            f if isinstance(f, Path) else repo_root / f
            for f in file_paths
        ]

    ctx = CheckContext(
        check_id=check_id, check_name=check_name, severity=severity,
        config=config, repo_root=repo_root, file_paths=file_paths, fix_hint=fix_hint
    )

    handlers = {
        "regex": _execute_regex_check,
        "lsp_query": execute_lsp_query_check,
        "ast_check": execute_ast_check,
        "command": _execute_command_check,
        "file_exists": _execute_file_exists_check,
        "custom": _execute_custom_check,
        "naming": _execute_naming_check,
        "ast": _execute_ast_interface_check,
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

    # Global exclusions - internal directories that should never be checked
    global_excludes = [
        ".agentforge/**",  # Internal tracking (violations, logs, backups)
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
        # Check both per-check exclusions and global exclusions
        excluded = any(fnmatch.fnmatch(relative, exc) for exc in exclude_paths)
        if not excluded:
            excluded = any(fnmatch.fnmatch(relative, exc) for exc in global_excludes)
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


# =============================================================================
# Naming Convention Check
# =============================================================================

# Regex patterns for extracting symbol names by language
_SYMBOL_PATTERNS = {
    "class": {
        # C#: class ClassName or public class ClassName : BaseClass, IInterface
        ".cs": r'(?:public|internal|private|protected)?\s*'
               r'(?:sealed|abstract|static|partial\s+)*'
               r'class\s+(\w+)',
        # Python: class ClassName or class ClassName(BaseClass)
        ".py": r'class\s+(\w+)',
        # TypeScript/JavaScript: class ClassName
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


def _get_symbol_pattern(symbol_type: str, file_suffix: str) -> Optional[str]:
    """Get regex pattern for extracting symbols of given type from file."""
    type_patterns = _SYMBOL_PATTERNS.get(symbol_type, {})
    return type_patterns.get(file_suffix)


def _extract_symbols(content: str, symbol_type: str, file_suffix: str) -> List[tuple]:
    """
    Extract symbols from file content.

    Returns list of (name, line_number) tuples.
    """
    pattern_str = _get_symbol_pattern(symbol_type, file_suffix)
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


def _execute_naming_check(ctx: CheckContext) -> List[CheckResult]:
    """
    Execute a naming convention check.

    Config options:
        pattern: Regex pattern that symbol names must match
        symbol_type: Type of symbol to check (class, interface, method)
        mode: 'require' (names must match) or 'forbid' (names must not match)
    """
    pattern_str = ctx.config.get("pattern")
    symbol_type = ctx.config.get("symbol_type", "class")
    mode = ctx.config.get("mode", "require")

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

        symbols = _extract_symbols(content, symbol_type, file_path.suffix)

        for name, line_num in symbols:
            matches = name_pattern.match(name) is not None

            if mode == "require" and not matches:
                results.append(CheckResult(
                    check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                    severity=ctx.severity, fix_hint=ctx.fix_hint,
                    message=f"{symbol_type.capitalize()} '{name}' does not match "
                            f"required pattern '{pattern_str}'",
                    file_path=str(file_path.relative_to(ctx.repo_root)),
                    line_number=line_num
                ))
            elif mode == "forbid" and matches:
                results.append(CheckResult(
                    check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                    severity=ctx.severity, fix_hint=ctx.fix_hint,
                    message=f"{symbol_type.capitalize()} '{name}' matches "
                            f"forbidden pattern '{pattern_str}'",
                    file_path=str(file_path.relative_to(ctx.repo_root)),
                    line_number=line_num
                ))

    return results


# =============================================================================
# AST Interface Implementation Check
# =============================================================================

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


def _extract_class_with_bases(content: str, file_suffix: str) -> List[tuple]:
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

            # Build inheritance string based on language
            if file_suffix == ".ts":
                # TypeScript has separate extends and implements groups
                bases = []
                if match.lastindex >= 2 and match.group(2):
                    bases.append(match.group(2))
                if match.lastindex >= 3 and match.group(3):
                    bases.append(match.group(3))
                bases_str = ", ".join(bases) if bases else ""
            else:
                bases_str = match.group(2) if match.lastindex >= 2 else ""

            classes.append((class_name, bases_str or "", line_num))
    except re.error:
        pass

    return classes


def _parse_inheritance_list(bases_str: str, file_suffix: str) -> List[str]:
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


def _execute_ast_interface_check(ctx: CheckContext) -> List[CheckResult]:
    """
    Execute an AST-based structural check.

    Supports two modes based on config:

    1. Interface implementation check:
        class_pattern: Regex pattern to match class names
        must_implement: List of interfaces/bases that matching classes must have
        must_not_implement: List of interfaces/bases that matching classes must not have

    2. Return type check:
        return_pattern: Regex pattern for required return types (e.g., "Result<|ErrorOr<")
        method_scope: Scope of methods to check (public, all)
        layer: Optional layer hint (application, domain, etc.)
    """
    # Detect which mode based on config
    if ctx.config.get("return_pattern"):
        return _execute_return_type_check(ctx)

    # Interface implementation mode
    class_pattern_str = ctx.config.get("class_pattern")
    must_implement = ctx.config.get("must_implement", [])
    must_not_implement = ctx.config.get("must_not_implement", [])

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

        classes = _extract_class_with_bases(content, file_path.suffix)

        for class_name, bases_str, line_num in classes:
            # Only check classes matching the pattern
            if not class_pattern.match(class_name):
                continue

            implemented = _parse_inheritance_list(bases_str, file_path.suffix)
            relative_path = str(file_path.relative_to(ctx.repo_root))

            # Check must_implement requirements
            for required in must_implement:
                # Support partial matches (e.g., "IRequest" matches "IRequest<T>")
                found = any(
                    impl == required or impl.startswith(required)
                    for impl in implemented
                )
                if not found:
                    results.append(CheckResult(
                        check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                        severity=ctx.severity, fix_hint=ctx.fix_hint,
                        message=f"Class '{class_name}' must implement '{required}'",
                        file_path=relative_path, line_number=line_num
                    ))

            # Check must_not_implement restrictions
            for forbidden in must_not_implement:
                found = any(
                    impl == forbidden or impl.startswith(forbidden)
                    for impl in implemented
                )
                if found:
                    results.append(CheckResult(
                        check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                        severity=ctx.severity, fix_hint=ctx.fix_hint,
                        message=f"Class '{class_name}' must not implement '{forbidden}'",
                        file_path=relative_path, line_number=line_num
                    ))

    return results


# =============================================================================
# Return Type Check
# =============================================================================

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


def _extract_methods_with_return_types(
    content: str, file_suffix: str, scope: str = "public"
) -> List[tuple]:
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

            # Get visibility (default to public for Python)
            try:
                visibility = match.group("visibility") or "public"
            except IndexError:
                visibility = "public"

            # Filter by scope
            if scope == "public" and visibility != "public":
                continue
            if scope == "private" and visibility not in ("private", "protected"):
                continue

            # Skip constructors, property accessors, and common non-methods
            if name in ("get", "set", "init", "if", "while", "for", "foreach",
                       "switch", "catch", "using", "lock", "fixed"):
                continue

            methods.append((name, return_type, line_num, visibility))
    except re.error:
        pass

    return methods


def _execute_return_type_check(ctx: CheckContext) -> List[CheckResult]:
    """
    Execute a return type pattern check.

    Config options:
        return_pattern: Regex pattern for required return types
        method_scope: Scope of methods to check (public, private, all)
        exclude_methods: List of method names to exclude
        exclude_return_types: List of return types to exclude (e.g., void, Task)
    """
    return_pattern_str = ctx.config.get("return_pattern")
    method_scope = ctx.config.get("method_scope", "public")
    exclude_methods = ctx.config.get("exclude_methods", [])
    exclude_return_types = ctx.config.get("exclude_return_types", [
        "void", "Task", "IActionResult", "ActionResult",
    ])

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

        methods = _extract_methods_with_return_types(content, file_path.suffix, method_scope)
        relative_path = str(file_path.relative_to(ctx.repo_root))

        for method_name, return_type, line_num, visibility in methods:
            # Skip excluded methods
            if method_name in exclude_methods:
                continue

            # Skip excluded return types (void, Task without result, etc.)
            should_skip = False
            for excluded in exclude_return_types:
                # Exact match or the return type is just the excluded type
                if return_type == excluded or return_type.startswith(excluded + " "):
                    should_skip = True
                    break
                # Task without generic (just "Task" not "Task<Result>")
                if excluded == "Task" and return_type == "Task":
                    should_skip = True
                    break
            if should_skip:
                continue

            # Check if return type matches the required pattern
            if not return_pattern.search(return_type):
                results.append(CheckResult(
                    check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                    severity=ctx.severity, fix_hint=ctx.fix_hint,
                    message=f"Method '{method_name}' returns '{return_type}', "
                            f"expected pattern '{return_pattern_str}'",
                    file_path=relative_path, line_number=line_num
                ))

    return results
