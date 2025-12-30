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
from typing import List, Optional, Dict, Any, Set


@dataclass
class Symbol:
    """A code symbol (class, function, method, etc.)."""
    name: str
    kind: str  # "class", "function", "method", "property", "variable"
    file_path: Path
    line_number: int
    end_line: Optional[int] = None
    parent: Optional[str] = None  # For methods, the class name
    visibility: str = "public"  # "public", "private", "protected"
    signature: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class Import:
    """An import/using statement."""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    file_path: Optional[Path] = None
    line_number: int = 0
    is_relative: bool = False


@dataclass
class Dependency:
    """An external package dependency."""
    name: str
    version: Optional[str] = None
    version_constraint: Optional[str] = None
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
    def file_extensions(self) -> Set[str]:
        """Return supported file extensions (e.g., {'.py', '.pyi'})."""
        pass

    @property
    @abstractmethod
    def project_markers(self) -> Set[str]:
        """Return project marker files (e.g., {'pyproject.toml', 'setup.py'})."""
        pass

    @abstractmethod
    def detect_project(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Detect if path contains a project of this language.

        Returns:
            Project info dict if detected, None otherwise.
        """
        pass

    @abstractmethod
    def parse_file(self, path: Path) -> Optional[Any]:
        """
        Parse a source file and return its AST.

        Returns:
            Parsed AST or None if parsing fails
        """
        pass

    @abstractmethod
    def extract_symbols(self, path: Path) -> List[Symbol]:
        """Extract all symbols from a source file."""
        pass

    @abstractmethod
    def get_imports(self, path: Path) -> List[Import]:
        """Extract all imports from a source file."""
        pass

    @abstractmethod
    def get_dependencies(self, project_path: Path) -> List[Dependency]:
        """Extract dependencies from project configuration."""
        pass

    def get_source_files(self, root: Path, exclude_patterns: List[str] = None) -> List[Path]:
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
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip() and not line.strip().startswith('#'))
        except Exception:
            return 0
