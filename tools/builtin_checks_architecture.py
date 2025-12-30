"""
Architecture-related builtin checks for AgentForge contracts.

These checks use AST-based semantic analysis to detect:
- Clean Architecture layer violations
- Constructor injection patterns
- Domain layer purity
- Circular import dependencies

Each function follows the signature:
    func(repo_root: Path, file_paths: List[Path], **params) -> List[Dict]
"""

import ast
import fnmatch
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def check_layer_imports(
    repo_root: Path,
    file_paths: List[Path],
    layer_detection: Dict[str, str],
    layer_rules: Dict[str, Dict]
) -> List[Dict]:
    """
    Detect Clean Architecture layer boundary violations using AST import analysis.

    This check parses Python files and analyzes their imports to detect when
    code in one architectural layer imports from a forbidden layer.

    Args:
        repo_root: Root path of the repository
        file_paths: List of files to check (already filtered by applies_to)
        layer_detection: Maps glob patterns to layer names
                        e.g., {"**/domain/**": "domain", "**/infrastructure/**": "infrastructure"}
        layer_rules: Maps layer names to their import rules
                    e.g., {"domain": {"forbidden": ["infrastructure", "application"]}}

    Returns:
        List of violation dictionaries with file, line, message, and fix_hint
    """
    violations = []

    def get_layer_for_path(file_path: Path) -> Optional[str]:
        """Determine which layer a file belongs to based on its path."""
        try:
            rel_path = str(file_path.relative_to(repo_root))
        except ValueError:
            rel_path = str(file_path)

        # Normalize path separators for consistent matching
        rel_path = rel_path.replace("\\", "/")
        path_parts = rel_path.lower().split("/")

        for pattern, layer in layer_detection.items():
            # Extract layer identifiers from pattern (e.g., "**/domain/**" -> ["domain"])
            # Handle both **/layer/** and layer/** patterns
            pattern_parts = pattern.replace("**/", "").replace("/**", "").replace("*", "").split("/")
            pattern_parts = [p.lower() for p in pattern_parts if p]

            # Check if any pattern part appears in the file path
            for pattern_part in pattern_parts:
                if pattern_part in path_parts:
                    return layer

        return None

    def get_layer_for_import(import_name: str) -> Optional[str]:
        """Determine which layer an import belongs to based on module name."""
        # Split the import into parts
        parts = import_name.split(".")

        # Check each part against layer detection patterns
        for pattern, layer in layer_detection.items():
            # Extract the layer identifier from the pattern
            # e.g., "**/domain/**" -> "domain"
            pattern_parts = pattern.replace("**/", "").replace("/**", "").replace("*", "").split("/")
            pattern_parts = [p for p in pattern_parts if p]

            for part in parts:
                if part.lower() in [pp.lower() for pp in pattern_parts]:
                    return layer

        return None

    def is_stdlib_or_thirdparty(import_name: str) -> bool:
        """Check if import is from standard library or third-party package."""
        first_part = import_name.split(".")[0]
        # Common stdlib modules
        stdlib = {
            "os", "sys", "re", "json", "typing", "collections", "itertools",
            "functools", "pathlib", "datetime", "abc", "dataclasses", "enum",
            "logging", "unittest", "copy", "io", "contextlib", "warnings",
            "importlib", "inspect", "ast", "pickle", "hashlib", "base64",
            "uuid", "random", "math", "statistics", "decimal", "fractions",
            "time", "calendar", "threading", "multiprocessing", "subprocess",
            "shutil", "glob", "fnmatch", "tempfile", "configparser", "argparse",
            "textwrap", "difflib", "csv", "html", "xml", "urllib", "http",
            "email", "mimetypes", "socket", "ssl", "select", "asyncio",
            "concurrent", "queue", "struct", "codecs", "pprint", "traceback",
            "linecache", "dis", "token", "tokenize", "keyword", "operator",
            "weakref", "types", "gc", "atexit", "gettext", "locale", "platform",
        }
        # Common third-party packages
        thirdparty = {
            "pytest", "yaml", "pyyaml", "requests", "httpx", "aiohttp",
            "numpy", "pandas", "sqlalchemy", "flask", "django", "fastapi",
            "pydantic", "click", "rich", "typer", "attrs", "marshmallow",
        }
        return first_part in stdlib or first_part in thirdparty

    for file_path in file_paths:
        source_layer = get_layer_for_path(file_path)
        if not source_layer or source_layer not in layer_rules:
            continue

        rules = layer_rules[source_layer]
        forbidden = set(rules.get("forbidden", []))

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, IOError, UnicodeDecodeError):
            continue

        try:
            rel_file = str(file_path.relative_to(repo_root))
        except ValueError:
            rel_file = str(file_path)

        for node in ast.walk(tree):
            import_names: List[Tuple[str, int]] = []

            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_names.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_names.append((node.module, node.lineno))

            for import_name, lineno in import_names:
                # Skip stdlib and third-party imports
                if is_stdlib_or_thirdparty(import_name):
                    continue

                target_layer = get_layer_for_import(import_name)
                if target_layer and target_layer in forbidden:
                    violations.append({
                        "message": f"{source_layer} layer imports from {target_layer}: {import_name}",
                        "file": rel_file,
                        "line": lineno,
                        "severity": "error",
                        "fix_hint": rules.get("message", "Fix layer dependency violation by using dependency injection")
                    })

    return violations


def check_constructor_injection(
    repo_root: Path,
    file_paths: List[Path],
    class_patterns: List[str],
    forbidden_instantiations: Optional[List[str]] = None,
    check_for_init_params: bool = True
) -> List[Dict]:
    """
    Verify that service classes use constructor injection.

    This check ensures that classes matching certain patterns (e.g., *Service, *Handler)
    receive their dependencies through __init__ parameters rather than instantiating
    them directly.

    Args:
        repo_root: Root path of the repository
        file_paths: List of files to check
        class_patterns: Glob patterns for class names to check (e.g., ["*Service", "*Handler"])
        forbidden_instantiations: Patterns for types that shouldn't be instantiated directly
        check_for_init_params: If True, check that __init__ has parameters (besides self)

    Returns:
        List of violation dictionaries
    """
    violations = []
    forbidden_instantiations = forbidden_instantiations or []

    for file_path in file_paths:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, IOError, UnicodeDecodeError):
            continue

        try:
            rel_file = str(file_path.relative_to(repo_root))
        except ValueError:
            rel_file = str(file_path)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # Check if class matches any pattern
            matches_pattern = any(
                fnmatch.fnmatch(node.name, pattern)
                for pattern in class_patterns
            )

            if not matches_pattern:
                continue

            # Find __init__ method
            init_method = None
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    init_method = item
                    break

            # Check for init parameters (excluding self)
            if check_for_init_params:
                if init_method is None:
                    violations.append({
                        "message": f"Class '{node.name}' has no __init__ method for dependency injection",
                        "file": rel_file,
                        "line": node.lineno,
                        "severity": "warning",
                        "fix_hint": "Add __init__ method with dependencies as parameters"
                    })
                else:
                    params = [
                        arg.arg for arg in init_method.args.args
                        if arg.arg != "self"
                    ]
                    if not params:
                        violations.append({
                            "message": f"Class '{node.name}' has no injected dependencies in __init__",
                            "file": rel_file,
                            "line": node.lineno,
                            "severity": "warning",
                            "fix_hint": "Add dependencies as __init__ parameters"
                        })

            # Check for forbidden instantiations in __init__
            if init_method and forbidden_instantiations:
                for child in ast.walk(init_method):
                    if isinstance(child, ast.Call):
                        # Try to get the call string representation
                        try:
                            if hasattr(ast, 'unparse'):
                                call_str = ast.unparse(child.func)
                            else:
                                # Fallback for Python < 3.9
                                if isinstance(child.func, ast.Name):
                                    call_str = child.func.id
                                elif isinstance(child.func, ast.Attribute):
                                    call_str = child.func.attr
                                else:
                                    call_str = ""
                        except Exception:
                            call_str = ""

                        for forbidden in forbidden_instantiations:
                            forbidden_name = forbidden.rstrip("(")
                            if forbidden_name in call_str:
                                violations.append({
                                    "message": f"Direct instantiation of '{forbidden_name}' in {node.name}.__init__",
                                    "file": rel_file,
                                    "line": child.lineno,
                                    "severity": "warning",
                                    "fix_hint": "Inject this dependency through constructor parameters"
                                })

    return violations


def check_domain_purity(
    repo_root: Path,
    file_paths: List[Path],
    forbidden_imports: Optional[List[str]] = None,
    forbidden_calls: Optional[List[str]] = None
) -> List[Dict]:
    """
    Ensure domain layer contains no I/O operations.

    The domain layer should contain only pure business logic without side effects.
    This check detects imports of I/O libraries and calls to I/O functions.

    Args:
        repo_root: Root path of the repository
        file_paths: List of files to check (should be domain layer files)
        forbidden_imports: Module names that shouldn't be imported in domain
        forbidden_calls: Function/method patterns that shouldn't be called

    Returns:
        List of violation dictionaries
    """
    violations = []

    # Default forbidden imports for domain layer
    default_forbidden_imports = [
        "requests", "httpx", "aiohttp", "urllib.request",
        "sqlite3", "psycopg2", "pymongo", "redis", "sqlalchemy",
        "django.db", "flask_sqlalchemy",
        "boto3", "azure", "google.cloud",
    ]
    forbidden_imports = forbidden_imports or default_forbidden_imports

    # Default forbidden calls
    default_forbidden_calls = [
        "open(", "Path.read", "Path.write", "os.path", "shutil.",
        "subprocess.", "os.system(", "os.popen(",
    ]
    forbidden_calls = forbidden_calls or default_forbidden_calls

    for file_path in file_paths:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, IOError, UnicodeDecodeError):
            continue

        try:
            rel_file = str(file_path.relative_to(repo_root))
        except ValueError:
            rel_file = str(file_path)

        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in forbidden_imports:
                        if alias.name == forbidden or alias.name.startswith(forbidden + "."):
                            violations.append({
                                "message": f"Domain layer imports I/O library: {alias.name}",
                                "file": rel_file,
                                "line": node.lineno,
                                "severity": "error",
                                "fix_hint": "Move I/O operations to infrastructure layer; domain should be pure"
                            })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for forbidden in forbidden_imports:
                        if node.module == forbidden or node.module.startswith(forbidden + "."):
                            violations.append({
                                "message": f"Domain layer imports I/O library: {node.module}",
                                "file": rel_file,
                                "line": node.lineno,
                                "severity": "error",
                                "fix_hint": "Move I/O operations to infrastructure layer; domain should be pure"
                            })

        # Check for forbidden function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                try:
                    if hasattr(ast, 'unparse'):
                        call_str = ast.unparse(node.func)
                    else:
                        if isinstance(node.func, ast.Name):
                            call_str = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            parts = []
                            current = node.func
                            while isinstance(current, ast.Attribute):
                                parts.append(current.attr)
                                current = current.value
                            if isinstance(current, ast.Name):
                                parts.append(current.id)
                            call_str = ".".join(reversed(parts))
                        else:
                            call_str = ""
                except Exception:
                    call_str = ""

                for forbidden in forbidden_calls:
                    forbidden_name = forbidden.rstrip("(")
                    if forbidden_name in call_str:
                        violations.append({
                            "message": f"Domain layer calls I/O function: {call_str}",
                            "file": rel_file,
                            "line": node.lineno,
                            "severity": "error",
                            "fix_hint": "Move I/O operations to infrastructure layer; domain should be pure"
                        })

    return violations


def check_circular_imports(
    repo_root: Path,
    file_paths: List[Path],
    ignore_type_checking: bool = True,
    max_depth: int = 5
) -> List[Dict]:
    """
    Detect circular import dependencies between modules.

    This check builds an import graph from all provided files and detects
    cycles in the dependency graph.

    Args:
        repo_root: Root path of the repository
        file_paths: List of files to analyze
        ignore_type_checking: If True, ignore imports inside TYPE_CHECKING blocks
        max_depth: Maximum cycle length to detect (prevents excessive computation)

    Returns:
        List of violation dictionaries describing detected cycles
    """
    violations = []

    # Build a mapping from module paths to their imports
    import_graph: Dict[str, Set[str]] = defaultdict(set)

    # Convert file paths to module names
    def path_to_module(file_path: Path) -> str:
        try:
            rel_path = file_path.relative_to(repo_root)
        except ValueError:
            rel_path = file_path
        # Convert path to module name
        module = str(rel_path).replace("/", ".").replace("\\", ".")
        if module.endswith(".py"):
            module = module[:-3]
        if module.endswith(".__init__"):
            module = module[:-9]
        return module

    # Build module name to file path mapping
    module_to_path: Dict[str, Path] = {}
    for file_path in file_paths:
        module_name = path_to_module(file_path)
        module_to_path[module_name] = file_path

    # Extract imports from each file
    for file_path in file_paths:
        module_name = path_to_module(file_path)

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, IOError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            # Check for TYPE_CHECKING blocks
            if ignore_type_checking and isinstance(node, ast.If):
                if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
                    # Skip imports in this block
                    continue
                if isinstance(node.test, ast.Attribute):
                    if hasattr(node.test, 'attr') and node.test.attr == "TYPE_CHECKING":
                        continue

            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_graph[module_name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_graph[module_name].add(node.module)

    # Find cycles using DFS
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    detected_cycles: Set[frozenset] = set()

    def find_cycle(module: str, path: List[str]) -> None:
        if len(path) > max_depth:
            return

        if module in rec_stack:
            # Found a cycle
            cycle_start = path.index(module)
            cycle = path[cycle_start:]
            cycle_set = frozenset(cycle)
            if cycle_set not in detected_cycles:
                detected_cycles.add(cycle_set)
                # Report the cycle
                cycle_str = " → ".join(cycle + [module])
                first_module = cycle[0]
                file_path = module_to_path.get(first_module)
                if file_path:
                    try:
                        rel_file = str(file_path.relative_to(repo_root))
                    except ValueError:
                        rel_file = str(file_path)
                else:
                    rel_file = first_module.replace(".", "/") + ".py"

                violations.append({
                    "message": f"Circular import detected: {cycle_str}",
                    "file": rel_file,
                    "line": 1,
                    "severity": "error",
                    "fix_hint": "Break cycle by: 1) Moving shared types to separate module, "
                               "2) Using TYPE_CHECKING guard, 3) Restructuring dependencies"
                })
            return

        if module in visited:
            return

        visited.add(module)
        rec_stack.add(module)

        for imported in import_graph.get(module, []):
            # Only follow imports that are in our module set (local imports)
            if imported in module_to_path or any(
                imported.startswith(m + ".") or m.startswith(imported + ".")
                for m in module_to_path
            ):
                find_cycle(imported, path + [module])

        rec_stack.remove(module)

    # Start DFS from each module
    for module in import_graph:
        if module not in visited:
            find_cycle(module, [])

    return violations
