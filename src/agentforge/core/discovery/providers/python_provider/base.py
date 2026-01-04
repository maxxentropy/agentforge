"""
Python Language Provider
========================

Provides Python-specific analysis using the ast module.
Serves as the single source of truth for Python AST analysis,
including symbol extraction, complexity analysis, and refactoring support.
"""

import ast
from pathlib import Path
from typing import Any

from ..base import LanguageProvider
from .analysis_mixin import AnalysisMixin
from .import_mixin import ImportMixin
from .project_mixin import ProjectMixin
from .symbol_mixin import SymbolMixin
from .violation_mixin import ViolationMixin


class PythonProvider(
    ProjectMixin,
    SymbolMixin,
    AnalysisMixin,
    ViolationMixin,
    ImportMixin,
    LanguageProvider,
):
    """Python language provider using ast module for analysis."""

    @property
    def language_name(self) -> str:
        return "python"

    @property
    def file_extensions(self) -> set[str]:
        return {".py", ".pyi"}

    @property
    def project_markers(self) -> set[str]:
        return {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"}

    def parse_file(self, path: Path) -> ast.AST | None:
        """Parse Python file to AST."""
        try:
            source = path.read_text()
            return ast.parse(source, filename=str(path))
        except Exception:
            return None

    def get_function_node(self, path: Path, function_name: str) -> ast.AST | None:
        """Get AST node for a specific function."""
        tree = self.parse_file(path)
        if tree is None:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    return node
        return None

    def get_function_source(self, path: Path, function_name: str) -> str | None:
        """Get source code for a specific function."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return None

        try:
            lines = path.read_text().split('\n')
            start = node.lineno - 1
            end = getattr(node, 'end_lineno', start + 1)
            return '\n'.join(lines[start:end])
        except Exception:
            return None

    def get_function_location(self, path: Path, function_name: str) -> tuple[int, int] | None:
        """Get (start_line, end_line) for a function."""
        node = self.get_function_node(path, function_name)
        if node:
            return (node.lineno, getattr(node, 'end_lineno', node.lineno))
        return None
