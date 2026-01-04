"""
Project Detection Mixin
=======================

Methods for detecting and parsing Python project metadata.
"""

import re
from pathlib import Path
from typing import Any


class ProjectMixin:
    """Project detection and parsing methods for PythonProvider."""

    # Type hints for mixin - provided by main class
    project_markers: set[str]

    def detect_project(self, path: Path) -> dict[str, Any] | None:
        """Detect Python project and extract metadata."""
        if not path.is_dir():
            path = path.parent

        # First check for standard project markers
        for marker in self.project_markers:
            marker_path = path / marker
            if marker_path.exists():
                return self._parse_project_file(marker_path)

        # Fallback: detect Python project by presence of .py files
        py_files = list(path.glob("**/*.py"))
        py_files = [f for f in py_files if not any(
            exclude in str(f) for exclude in
            ["node_modules", ".git", "venv", ".venv", "__pycache__", ".tox"]
        )]

        if len(py_files) >= 3:
            return {
                "name": path.name,
                "version": None,
                "framework": None,
                "project_file": None,
                "detected_by": "python_files",
            }

        return None

    def _parse_project_file(self, path: Path) -> dict[str, Any]:
        """Parse project configuration file."""
        result = {
            "name": path.parent.name,
            "version": None,
            "framework": None,
            "project_file": str(path),
        }

        if path.name == "pyproject.toml":
            result.update(self._parse_pyproject_toml(path))
        elif path.name == "setup.py":
            result.update(self._parse_setup_py(path))
        elif path.name == "requirements.txt":
            frameworks = self._detect_frameworks_from_requirements(path)
            if frameworks:
                result["framework"] = frameworks[0]

        return result

    def _parse_pyproject_toml(self, path: Path) -> dict[str, Any]:
        """Parse pyproject.toml for project metadata."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return {}

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            project = data.get("project", {})
            result = {
                "name": project.get("name", path.parent.name),
                "version": project.get("version"),
            }

            deps = project.get("dependencies", [])
            frameworks = self._detect_frameworks_from_deps(deps)
            if frameworks:
                result["framework"] = frameworks[0]
                result["frameworks"] = frameworks

            return result
        except Exception:
            return {}

    def _parse_setup_py(self, path: Path) -> dict[str, Any]:
        """Parse setup.py for project metadata."""
        try:
            content = path.read_text()
            result = {}

            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                result["name"] = name_match.group(1)

            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                result["version"] = version_match.group(1)

            return result
        except Exception:
            return {}

    def _detect_frameworks_from_requirements(self, path: Path) -> list[str]:
        """Detect frameworks from requirements.txt."""
        try:
            content = path.read_text()
            deps = [line.split("==")[0].split(">=")[0].split("[")[0].strip().lower()
                    for line in content.splitlines() if line.strip() and not line.startswith("#")]
            return self._detect_frameworks_from_deps(deps)
        except Exception:
            return []

    def _detect_frameworks_from_deps(self, deps: list[str]) -> list[str]:
        """Detect frameworks from dependency list."""
        frameworks = []
        deps_lower = [d.lower() if isinstance(d, str) else "" for d in deps]

        framework_markers = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "starlette": "Starlette",
            "pytest": "pytest",
            "sqlalchemy": "SQLAlchemy",
            "pydantic": "Pydantic",
            "click": "Click",
            "typer": "Typer",
        }

        for marker, name in framework_markers.items():
            if any(marker in d for d in deps_lower):
                frameworks.append(name)

        return frameworks
