# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-builtin_checks_architecture_helpers
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
Helper functions for architecture checks.

Extracted from builtin_checks_architecture.py to reduce complexity and file length.
"""

import ast
from pathlib import Path

# Standard library modules (for import classification)
STDLIB_MODULES = {
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
THIRDPARTY_MODULES = {
    "pytest", "yaml", "pyyaml", "requests", "httpx", "aiohttp",
    "numpy", "pandas", "sqlalchemy", "flask", "django", "fastapi",
    "pydantic", "click", "rich", "typer", "attrs", "marshmallow",
}


def is_stdlib_or_thirdparty(import_name: str) -> bool:
    """Check if import is from standard library or third-party package."""
    first_part = import_name.split(".")[0]
    return first_part in STDLIB_MODULES or first_part in THIRDPARTY_MODULES


def get_relative_path(file_path: Path, repo_root: Path) -> str:
    """Get relative path string from file path."""
    try:
        return str(file_path.relative_to(repo_root))
    except ValueError:
        return str(file_path)


def parse_source_safe(file_path: Path) -> ast.Module | None:
    """Parse a Python file, returning None on error."""
    try:
        source = file_path.read_text(encoding="utf-8")
        return ast.parse(source)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def get_layer_for_path(file_path: Path, repo_root: Path, layer_detection: dict[str, str]) -> str | None:
    """Determine which layer a file belongs to based on its path."""
    rel_path = get_relative_path(file_path, repo_root).replace("\\", "/")
    path_parts = rel_path.lower().split("/")

    for pattern, layer in layer_detection.items():
        pattern_parts = pattern.replace("**/", "").replace("/**", "").replace("*", "").split("/")
        pattern_parts = [p.lower() for p in pattern_parts if p]
        for pattern_part in pattern_parts:
            if pattern_part in path_parts:
                return layer
    return None


def get_layer_for_import(import_name: str, layer_detection: dict[str, str]) -> str | None:
    """Determine which layer an import belongs to based on module name."""
    parts = import_name.split(".")
    for pattern, layer in layer_detection.items():
        pattern_parts = pattern.replace("**/", "").replace("/**", "").replace("*", "").split("/")
        pattern_parts = [p for p in pattern_parts if p]
        for part in parts:
            if part.lower() in [pp.lower() for pp in pattern_parts]:
                return layer
    return None


def extract_import_names(node: ast.AST) -> list[tuple[str, int]]:
    """Extract import names and line numbers from an AST node."""
    if isinstance(node, ast.Import):
        return [(alias.name, node.lineno) for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [(node.module, node.lineno)]
    return []


def get_call_string(node: ast.Call) -> str:
    """Get string representation of a function call."""
    try:
        if hasattr(ast, 'unparse'):
            return ast.unparse(node.func)
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
    except Exception:
        pass
    return ""


def path_to_module(file_path: Path, repo_root: Path) -> str:
    """Convert a file path to a module name."""
    rel_path = get_relative_path(file_path, repo_root)
    module = rel_path.replace("/", ".").replace("\\", ".")
    if module.endswith(".py"):
        module = module[:-3]
    if module.endswith(".__init__"):
        module = module[:-9]
    return module


def is_type_checking_block(node: ast.If) -> bool:
    """Check if an If node is a TYPE_CHECKING guard."""
    if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
        return True
    return bool(isinstance(node.test, ast.Attribute) and getattr(node.test, 'attr', '') == "TYPE_CHECKING")


def create_violation(message: str, file: str, line: int, severity: str, fix_hint: str) -> dict:
    """Create a standardized violation dictionary."""
    return {"message": message, "file": file, "line": line, "severity": severity, "fix_hint": fix_hint}
