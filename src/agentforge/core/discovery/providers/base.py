# @spec_file: .agentforge/specs/core-discovery-providers-v1.yaml
# @spec_id: core-discovery-providers-v1
# @component_id: discovery-providers-base
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

"""
Language Provider Abstract Base
===============================

Defines the interface that all language providers must implement.
Each provider handles language-specific parsing, symbol extraction,
and dependency analysis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Symbol:
    """A code symbol (class, function, method, etc.)."""
    name: str
    kind: str  # "class", "function", "method", "property", "variable"
    file_path: Path
    line_number: int
    end_line: int | None = None
    parent: str | None = None  # For methods, the class name
    visibility: str = "public"  # "public", "private", "protected"
    signature: str | None = None
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)
    return_type: str | None = None
    parameters: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Import:
    """An import/using statement."""
    module: str
    names: list[str] = field(default_factory=list)
    alias: str | None = None
    file_path: Path | None = None
    line_number: int = 0
    is_relative: bool = False


@dataclass
class Dependency:
    """An external package dependency."""
    name: str
    version: str | None = None
    version_constraint: str | None = None
    is_dev: bool = False
    source: str = "unknown"  # "pypi", "nuget", "npm"


class LanguageProvider(ABC):
    """
    Abstract base class for language-specific analysis.

    Implementations provide:
    - Project detection and metadata extraction
    - File parsing and AST access
    - Symbol extraction (classes, methods, etc.)
    - Import analysis
    - Dependency extraction
    """

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name (e.g., 'python', 'csharp')."""
        pass

    @property
    @abstractmethod
    def file_extensions(self) -> set[str]:
        """Return supported file extensions (e.g., {'.py', '.pyi'})."""
        pass

    @property
    @abstractmethod
    def project_markers(self) -> set[str]:
        """Return project marker files (e.g., {'pyproject.toml', 'setup.py'})."""
        pass

    @abstractmethod
    def detect_project(self, path: Path) -> dict[str, Any] | None:
        """
        Detect if path contains a project of this language.

        Returns:
            Project info dict if detected, None otherwise.
        """
        pass

    @abstractmethod
    def parse_file(self, path: Path) -> Any | None:
        """
        Parse a source file and return its AST.

        Returns:
            Parsed AST or None if parsing fails
        """
        pass

    @abstractmethod
    def extract_symbols(self, path: Path) -> list[Symbol]:
        """Extract all symbols from a source file."""
        pass

    @abstractmethod
    def get_imports(self, path: Path) -> list[Import]:
        """Extract all imports from a source file."""
        pass

    @abstractmethod
    def get_dependencies(self, project_path: Path) -> list[Dependency]:
        """Extract dependencies from project configuration."""
        pass

    def get_source_files(self, root: Path, exclude_patterns: list[str] = None) -> list[Path]:
        """Find all source files under root."""
        exclude_patterns = exclude_patterns or []
        default_excludes = [
            "node_modules", ".git", "venv", ".venv", "__pycache__",
            "bin", "obj", ".pytest_cache", ".mypy_cache", "dist", "build",
            ".tox", ".eggs", "*.egg-info",
        ]

        files = []
        for ext in self.file_extensions:
            for path in root.rglob(f"*{ext}"):
                skip = False
                path_str = str(path)
                for pattern in default_excludes + exclude_patterns:
                    if pattern in path_str:
                        skip = True
                        break
                if not skip:
                    files.append(path)

        return sorted(files)

    def count_lines(self, path: Path) -> int:
        """Count non-empty, non-comment lines of code."""
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip() and not line.strip().startswith('#'))
        except Exception:
            return 0
