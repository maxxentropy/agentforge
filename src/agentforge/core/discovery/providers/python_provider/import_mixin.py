"""
Import Analysis Mixin
=====================

Methods for analyzing imports and dependencies in Python projects.
"""

import ast
import re
from pathlib import Path
from typing import Any

from ..base import Dependency, Import


class ImportMixin:
    """Import and dependency analysis methods for PythonProvider."""

    # Type hints for mixin - provided by main class
    parse_file: Any

    def get_imports(self, path: Path) -> list[Import]:
        """Extract imports from Python file."""
        tree = self.parse_file(path)
        if tree is None:
            return []

        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(Import(
                        module=alias.name,
                        names=[alias.name.split(".")[-1]],
                        alias=alias.asname,
                        file_path=path,
                        line_number=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(Import(
                    module=node.module,
                    names=[alias.name for alias in node.names],
                    file_path=path,
                    line_number=node.lineno,
                    is_relative=node.level > 0,
                ))

        return imports

    def get_dependencies(self, project_path: Path) -> list[Dependency]:
        """Extract dependencies from Python project."""
        dependencies = []

        if project_path.is_file():
            project_path = project_path.parent

        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            dependencies.extend(self._parse_pyproject_deps(pyproject))

        requirements = project_path / "requirements.txt"
        if requirements.exists():
            dependencies.extend(self._parse_requirements_txt(requirements))

        dev_requirements = project_path / "requirements-dev.txt"
        if dev_requirements.exists():
            for dep in self._parse_requirements_txt(dev_requirements):
                dep.is_dev = True
                dependencies.append(dep)

        return dependencies

    def _parse_pyproject_deps(self, path: Path) -> list[Dependency]:
        """Parse dependencies from pyproject.toml."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return []

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            deps = []

            for dep in data.get("project", {}).get("dependencies", []):
                parsed = self._parse_dep_string(dep)
                if parsed:
                    deps.append(parsed)

            for dep in data.get("project", {}).get("optional-dependencies", {}).get("dev", []):
                parsed = self._parse_dep_string(dep)
                if parsed:
                    parsed.is_dev = True
                    deps.append(parsed)

            return deps
        except Exception:
            return []

    def _parse_requirements_txt(self, path: Path) -> list[Dependency]:
        """Parse requirements.txt file."""
        deps = []
        try:
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    parsed = self._parse_dep_string(line)
                    if parsed:
                        deps.append(parsed)
        except Exception:
            pass
        return deps

    def _parse_dep_string(self, dep: str) -> Dependency | None:
        """Parse a dependency specification string."""
        match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*\])?(?:([<>=!]+)(.+))?$', dep.strip())
        if match:
            name, op, version = match.groups()
            return Dependency(
                name=name,
                version=version,
                version_constraint=f"{op}{version}" if op else None,
                source="pypi",
            )
        return None
