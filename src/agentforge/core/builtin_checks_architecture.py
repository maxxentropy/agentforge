# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-builtin_checks_architecture
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
Architecture-related builtin checks for AgentForge contracts.

These checks use AST-based semantic analysis to detect:
- Clean Architecture layer violations
- Constructor injection patterns
- Domain layer purity
- Circular import dependencies
"""

import ast
import fnmatch
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    from .builtin_checks_architecture_helpers import (
        is_stdlib_or_thirdparty, get_relative_path, parse_source_safe,
        get_layer_for_path, get_layer_for_import, extract_import_names,
        get_call_string, path_to_module, is_type_checking_block, create_violation,
    )
except ImportError:
    from builtin_checks_architecture_helpers import (
        is_stdlib_or_thirdparty, get_relative_path, parse_source_safe,
        get_layer_for_path, get_layer_for_import, extract_import_names,
        get_call_string, path_to_module, is_type_checking_block, create_violation,
    )


@dataclass
class CycleContext:
    """Context for cycle detection to reduce parameter passing."""
    import_graph: Dict[str, Set[str]]
    module_to_path: Dict[str, Path]
    repo_root: Path
    max_depth: int
    visited: Set[str] = field(default_factory=set)
    rec_stack: Set[str] = field(default_factory=set)
    detected_cycles: Set[frozenset] = field(default_factory=set)


def check_layer_imports(
    repo_root: Path, file_paths: List[Path],
    layer_detection: Dict[str, str], layer_rules: Dict[str, Dict]
) -> List[Dict]:
    """Detect Clean Architecture layer boundary violations using AST import analysis."""
    violations = []

    for file_path in file_paths:
        source_layer = get_layer_for_path(file_path, repo_root, layer_detection)
        if not source_layer or source_layer not in layer_rules:
            continue

        tree = parse_source_safe(file_path)
        if tree is None:
            continue

        rel_file = get_relative_path(file_path, repo_root)
        rules = layer_rules[source_layer]
        forbidden = set(rules.get("forbidden", []))

        for node in ast.walk(tree):
            for import_name, lineno in extract_import_names(node):
                if is_stdlib_or_thirdparty(import_name):
                    continue
                target_layer = get_layer_for_import(import_name, layer_detection)
                if target_layer and target_layer in forbidden:
                    violations.append(create_violation(
                        f"{source_layer} layer imports from {target_layer}: {import_name}",
                        rel_file, lineno, "error",
                        rules.get("message", "Fix layer dependency violation by using dependency injection")
                    ))

    return violations


def _check_class_init(node: ast.ClassDef, rel_file: str, check_for_init_params: bool) -> List[Dict]:
    """Check a single class for __init__ injection issues."""
    violations = []
    init_method = next((item for item in node.body
                        if isinstance(item, ast.FunctionDef) and item.name == "__init__"), None)

    if not check_for_init_params:
        return violations

    if init_method is None:
        violations.append(create_violation(
            f"Class '{node.name}' has no __init__ method for dependency injection",
            rel_file, node.lineno, "warning", "Add __init__ method with dependencies as parameters"))
        return violations

    params = [arg.arg for arg in init_method.args.args if arg.arg != "self"]
    if not params:
        violations.append(create_violation(
            f"Class '{node.name}' has no injected dependencies in __init__",
            rel_file, node.lineno, "warning", "Add dependencies as __init__ parameters"))

    return violations


def _check_forbidden_instantiations(
    init_method: ast.FunctionDef, class_name: str, rel_file: str, forbidden: List[str]
) -> List[Dict]:
    """Check for forbidden instantiations in __init__ method."""
    violations = []
    for child in ast.walk(init_method):
        if not isinstance(child, ast.Call):
            continue
        call_str = get_call_string(child)
        for pattern in forbidden:
            if pattern.rstrip("(") in call_str:
                violations.append(create_violation(
                    f"Direct instantiation of '{pattern.rstrip('(')}' in {class_name}.__init__",
                    rel_file, child.lineno, "warning", "Inject this dependency through constructor parameters"))
    return violations


def _matches_class_pattern(name: str, patterns: List[str]) -> bool:
    """Check if class name matches any pattern."""
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def _get_init_method(node: ast.ClassDef) -> Optional[ast.FunctionDef]:
    """Get __init__ method from class node."""
    return next((item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"), None)


def check_constructor_injection(
    repo_root: Path, file_paths: List[Path], class_patterns: List[str],
    forbidden_instantiations: Optional[List[str]] = None, check_for_init_params: bool = True
) -> List[Dict]:
    """Verify that service classes use constructor injection."""
    violations = []
    forbidden = forbidden_instantiations or []

    for file_path in file_paths:
        tree = parse_source_safe(file_path)
        if tree is None:
            continue
        rel_file = get_relative_path(file_path, repo_root)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not _matches_class_pattern(node.name, class_patterns):
                continue
            violations.extend(_check_class_init(node, rel_file, check_for_init_params))
            init_method = _get_init_method(node)
            if init_method and forbidden:
                violations.extend(_check_forbidden_instantiations(init_method, node.name, rel_file, forbidden))

    return violations


# Default forbidden imports/calls for domain purity
DEFAULT_FORBIDDEN_IMPORTS = [
    "requests", "httpx", "aiohttp", "urllib.request",
    "sqlite3", "psycopg2", "pymongo", "redis", "sqlalchemy",
    "django.db", "flask_sqlalchemy", "boto3", "azure", "google.cloud",
]

DEFAULT_FORBIDDEN_CALLS = [
    "open(", "Path.read", "Path.write", "os.path", "shutil.",
    "subprocess.", "os.system(", "os.popen(",
]


def _is_forbidden_import(name: str, forbidden: List[str]) -> bool:
    """Check if an import name matches any forbidden pattern."""
    return any(name == f or name.startswith(f + ".") for f in forbidden)


def _check_import_purity(node: ast.AST, rel_file: str, forbidden: List[str]) -> List[Dict]:
    """Check a single import node for domain purity violations."""
    names_to_check = []
    if isinstance(node, ast.Import):
        names_to_check = [alias.name for alias in node.names]
    elif isinstance(node, ast.ImportFrom) and node.module:
        names_to_check = [node.module]

    return [create_violation(f"Domain layer imports I/O library: {name}", rel_file, node.lineno, "error",
                             "Move I/O operations to infrastructure layer; domain should be pure")
            for name in names_to_check if _is_forbidden_import(name, forbidden)]


def _check_call_purity(node: ast.Call, rel_file: str, forbidden: List[str]) -> List[Dict]:
    """Check a single call node for domain purity violations."""
    call_str = get_call_string(node)
    for f in forbidden:
        if f.rstrip("(") in call_str:
            return [create_violation(
                f"Domain layer calls I/O function: {call_str}",
                rel_file, node.lineno, "error",
                "Move I/O operations to infrastructure layer; domain should be pure")]
    return []


def check_domain_purity(
    repo_root: Path, file_paths: List[Path],
    forbidden_imports: Optional[List[str]] = None, forbidden_calls: Optional[List[str]] = None
) -> List[Dict]:
    """Ensure domain layer contains no I/O operations."""
    violations = []
    forbidden_imports = forbidden_imports or DEFAULT_FORBIDDEN_IMPORTS
    forbidden_calls = forbidden_calls or DEFAULT_FORBIDDEN_CALLS

    for file_path in file_paths:
        tree = parse_source_safe(file_path)
        if tree is None:
            continue

        rel_file = get_relative_path(file_path, repo_root)

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                violations.extend(_check_import_purity(node, rel_file, forbidden_imports))
            elif isinstance(node, ast.Call):
                violations.extend(_check_call_purity(node, rel_file, forbidden_calls))

    return violations


def _is_local_import(imported: str, module_to_path: Dict[str, Path]) -> bool:
    """Check if an import is from within the project."""
    return imported in module_to_path or any(
        imported.startswith(m + ".") or m.startswith(imported + ".") for m in module_to_path)


def _record_cycle(cycle: List[str], module: str, ctx: CycleContext) -> List[Dict]:
    """Record a detected cycle as a violation."""
    cycle_set = frozenset(cycle)
    if cycle_set in ctx.detected_cycles:
        return []
    ctx.detected_cycles.add(cycle_set)
    cycle_str = " → ".join(cycle + [module])
    file_path = ctx.module_to_path.get(cycle[0])
    rel_file = get_relative_path(file_path, ctx.repo_root) if file_path else f"{cycle[0].replace('.', '/')}.py"
    return [create_violation(
        f"Circular import detected: {cycle_str}", rel_file, 1, "error",
        "Break cycle by: 1) Moving shared types to separate module, "
        "2) Using TYPE_CHECKING guard, 3) Restructuring dependencies")]


def _find_cycles(module: str, path: List[str], ctx: CycleContext) -> List[Dict]:
    """DFS cycle detection helper."""
    if len(path) > ctx.max_depth:
        return []

    # Check for cycle BEFORE checking visited - module in rec_stack means cycle
    if module in ctx.rec_stack:
        return _record_cycle(path[path.index(module):], module, ctx)

    if module in ctx.visited:
        return []

    ctx.visited.add(module)
    ctx.rec_stack.add(module)
    violations = []

    for imported in ctx.import_graph.get(module, []):
        if _is_local_import(imported, ctx.module_to_path):
            violations.extend(_find_cycles(imported, path + [module], ctx))

    ctx.rec_stack.remove(module)
    return violations


def _build_import_graph(
    file_paths: List[Path], repo_root: Path, ignore_type_checking: bool
) -> Dict[str, Set[str]]:
    """Build the import graph from source files."""
    import_graph: Dict[str, Set[str]] = defaultdict(set)
    for file_path in file_paths:
        module_name = path_to_module(file_path, repo_root)
        tree = parse_source_safe(file_path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if ignore_type_checking and isinstance(node, ast.If) and is_type_checking_block(node):
                continue
            for import_name, _ in extract_import_names(node):
                import_graph[module_name].add(import_name)
    return import_graph


def check_circular_imports(
    repo_root: Path, file_paths: List[Path],
    ignore_type_checking: bool = True, max_depth: int = 5
) -> List[Dict]:
    """Detect circular import dependencies between modules."""
    import_graph = _build_import_graph(file_paths, repo_root, ignore_type_checking)
    module_to_path = {path_to_module(fp, repo_root): fp for fp in file_paths}

    ctx = CycleContext(import_graph, module_to_path, repo_root, max_depth)
    violations = []
    for module in import_graph:
        if module not in ctx.visited:
            violations.extend(_find_cycles(module, [], ctx))
    return violations
