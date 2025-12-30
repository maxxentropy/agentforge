"""
Python Language Provider
========================

Provides Python-specific analysis using the ast module.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from .base import LanguageProvider, Symbol, Import, Dependency


class PythonProvider(LanguageProvider):
    """Python language provider using ast module for analysis."""

    @property
    def language_name(self) -> str:
        return "python"

    @property
    def file_extensions(self) -> Set[str]:
        return {".py", ".pyi"}

    @property
    def project_markers(self) -> Set[str]:
        return {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"}

    def detect_project(self, path: Path) -> Optional[Dict[str, Any]]:
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
        # Exclude common non-project directories
        py_files = [f for f in py_files if not any(
            exclude in str(f) for exclude in
            ["node_modules", ".git", "venv", ".venv", "__pycache__", ".tox"]
        )]

        if len(py_files) >= 3:  # At least 3 Python files suggests a project
            return {
                "name": path.name,
                "version": None,
                "framework": None,
                "project_file": None,
                "detected_by": "python_files",
            }

        return None

    def _parse_project_file(self, path: Path) -> Dict[str, Any]:
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

    def _parse_pyproject_toml(self, path: Path) -> Dict[str, Any]:
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

    def _parse_setup_py(self, path: Path) -> Dict[str, Any]:
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

    def _detect_frameworks_from_requirements(self, path: Path) -> List[str]:
        """Detect frameworks from requirements.txt."""
        try:
            content = path.read_text()
            deps = [line.split("==")[0].split(">=")[0].split("[")[0].strip().lower()
                    for line in content.splitlines() if line.strip() and not line.startswith("#")]
            return self._detect_frameworks_from_deps(deps)
        except Exception:
            return []

    def _detect_frameworks_from_deps(self, deps: List[str]) -> List[str]:
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

    def parse_file(self, path: Path) -> Optional[ast.AST]:
        """Parse Python file to AST."""
        try:
            content = path.read_text(encoding='utf-8')
            return ast.parse(content, filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def extract_symbols(self, path: Path) -> List[Symbol]:
        """Extract symbols from Python file."""
        tree = self.parse_file(path)
        if tree is None:
            return []

        symbols = []
        current_class = None

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(self._get_attr_name(base))

                decorators = [self._get_decorator_name(d) for d in node.decorator_list]

                symbols.append(Symbol(
                    name=node.name,
                    kind="class",
                    file_path=path,
                    line_number=node.lineno,
                    end_line=getattr(node, 'end_lineno', None),
                    visibility=self._get_visibility(node.name),
                    docstring=ast.get_docstring(node),
                    decorators=decorators,
                    base_classes=bases,
                ))

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]

                return_type = None
                if node.returns:
                    return_type = self._get_annotation_str(node.returns)

                params = []
                for arg in node.args.args:
                    param = {"name": arg.arg}
                    if arg.annotation:
                        param["type"] = self._get_annotation_str(arg.annotation)
                    params.append(param)

                is_async = isinstance(node, ast.AsyncFunctionDef)
                param_strs = [p["name"] for p in params]
                signature = f"{'async ' if is_async else ''}def {node.name}({', '.join(param_strs)})"
                if return_type:
                    signature += f" -> {return_type}"

                # Determine if this is a method or function
                parent = None
                for potential_parent in ast.walk(tree):
                    if isinstance(potential_parent, ast.ClassDef):
                        for child in ast.iter_child_nodes(potential_parent):
                            if child is node:
                                parent = potential_parent.name
                                break

                kind = "method" if parent else "function"

                symbols.append(Symbol(
                    name=node.name,
                    kind=kind,
                    file_path=path,
                    line_number=node.lineno,
                    end_line=getattr(node, 'end_lineno', None),
                    parent=parent,
                    visibility=self._get_visibility(node.name),
                    signature=signature,
                    docstring=ast.get_docstring(node),
                    decorators=decorators,
                    return_type=return_type,
                    parameters=params,
                ))

        return symbols

    def _get_visibility(self, name: str) -> str:
        if name.startswith("__") and not name.endswith("__"):
            return "private"
        elif name.startswith("_"):
            return "protected"
        return "public"

    def _get_decorator_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attr_name(node)
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "unknown"

    def _get_attr_name(self, node: ast.Attribute) -> str:
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))

    def _get_annotation_str(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attr_name(node)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation_str(node.value)
            if isinstance(node.slice, ast.Tuple):
                slices = ", ".join(self._get_annotation_str(e) for e in node.slice.elts)
            else:
                slices = self._get_annotation_str(node.slice)
            return f"{value}[{slices}]"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        return "Any"

    def get_imports(self, path: Path) -> List[Import]:
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
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(Import(
                        module=node.module,
                        names=[alias.name for alias in node.names],
                        file_path=path,
                        line_number=node.lineno,
                        is_relative=node.level > 0,
                    ))

        return imports

    def get_dependencies(self, project_path: Path) -> List[Dependency]:
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

    def _parse_pyproject_deps(self, path: Path) -> List[Dependency]:
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

    def _parse_requirements_txt(self, path: Path) -> List[Dependency]:
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

    def _parse_dep_string(self, dep: str) -> Optional[Dependency]:
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
