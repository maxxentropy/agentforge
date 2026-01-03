"""
Python Language Provider
========================

Provides Python-specific analysis using the ast module.
Serves as the single source of truth for Python AST analysis,
including symbol extraction, complexity analysis, and refactoring support.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import Dependency, Import, LanguageProvider, Symbol


@dataclass
class ComplexityMetrics:
    """Metrics from complexity analysis."""
    cyclomatic_complexity: int
    cognitive_complexity: int
    nesting_depth: int
    line_count: int
    branch_count: int
    loop_count: int


@dataclass
class ExtractionSuggestion:
    """Suggestion for code extraction to reduce complexity."""
    start_line: int
    end_line: int
    description: str
    estimated_reduction: int
    extractable: bool
    reason: str | None = None


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for calculating complexity metrics."""

    def __init__(self):
        self.complexity = 1  # Start at 1 for the function itself
        self.cognitive = 0
        self.max_nesting = 0
        self.current_nesting = 0
        self.branches = 0
        self.loops = 0

    def _increment_nesting(self):
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)

    def _decrement_nesting(self):
        self.current_nesting -= 1

    def visit_If(self, node):
        self.complexity += 1
        self.branches += 1
        self.cognitive += 1 + self.current_nesting
        self._increment_nesting()
        self.generic_visit(node)
        self._decrement_nesting()

    def visit_For(self, node):
        self.complexity += 1
        self.loops += 1
        self.cognitive += 1 + self.current_nesting
        self._increment_nesting()
        self.generic_visit(node)
        self._decrement_nesting()

    def visit_While(self, node):
        self.complexity += 1
        self.loops += 1
        self.cognitive += 1 + self.current_nesting
        self._increment_nesting()
        self.generic_visit(node)
        self._decrement_nesting()

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.branches += 1
        self.cognitive += 1 + self.current_nesting
        self._increment_nesting()
        self.generic_visit(node)
        self._decrement_nesting()

    def visit_With(self, node):
        self._increment_nesting()
        self.generic_visit(node)
        self._decrement_nesting()

    def visit_BoolOp(self, node):
        # Each 'and' or 'or' adds to complexity
        self.complexity += len(node.values) - 1
        self.cognitive += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        self.loops += 1
        if node.ifs:
            self.complexity += len(node.ifs)
            self.branches += len(node.ifs)
        self.generic_visit(node)


class PythonProvider(LanguageProvider):
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

    def parse_file(self, path: Path) -> ast.AST | None:
        """Parse Python file to AST."""
        try:
            content = path.read_text(encoding='utf-8')
            return ast.parse(content, filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def extract_symbols(self, path: Path) -> list[Symbol]:
        """Extract symbols from Python file."""
        tree = self.parse_file(path)
        if tree is None:
            return []

        symbols = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append(self._process_class_node(node, path))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(self._process_function_node(node, path, tree))

        return symbols

    def _process_class_node(self, node: ast.ClassDef, path: Path) -> Symbol:
        """Process a class definition node into a Symbol."""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(self._get_attr_name(base))

        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        return Symbol(
            name=node.name,
            kind="class",
            file_path=path,
            line_number=node.lineno,
            end_line=getattr(node, 'end_lineno', None),
            visibility=self._get_visibility(node.name),
            docstring=ast.get_docstring(node),
            decorators=decorators,
            base_classes=bases,
        )

    def _process_function_node(self, node, path: Path, tree: ast.AST) -> Symbol:
        """Process a function/method definition node into a Symbol."""
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
        parent = self._find_parent_class(node, tree)
        kind = "method" if parent else "function"

        return Symbol(
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
        )

    def _find_parent_class(self, node, tree: ast.AST) -> str | None:
        """Find the parent class name for a method node."""
        for potential_parent in ast.walk(tree):
            if isinstance(potential_parent, ast.ClassDef):
                for child in ast.iter_child_nodes(potential_parent):
                    if child is node:
                        return potential_parent.name
        return None

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

    # ========================================================================
    # Complexity Analysis Methods
    # ========================================================================

    def get_function_node(self, path: Path, function_name: str) -> ast.AST | None:
        """Get the AST node for a specific function/method."""
        tree = self.parse_file(path)
        if tree is None:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    return node
        return None

    def get_function_source(self, path: Path, function_name: str) -> str | None:
        """Get the source code of a specific function."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return None

        try:
            lines = path.read_text(encoding='utf-8').splitlines()
            start = node.lineno - 1
            end = getattr(node, 'end_lineno', len(lines))
            return '\n'.join(lines[start:end])
        except Exception:
            return None

    def get_function_location(self, path: Path, function_name: str) -> tuple[int, int] | None:
        """Get the start and end line numbers of a function."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return None
        return (node.lineno, getattr(node, 'end_lineno', node.lineno))

    def analyze_complexity(self, path: Path, function_name: str) -> ComplexityMetrics | None:
        """Analyze complexity metrics for a specific function."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return None

        visitor = ComplexityVisitor()
        visitor.visit(node)

        line_count = getattr(node, 'end_lineno', node.lineno) - node.lineno + 1

        return ComplexityMetrics(
            cyclomatic_complexity=visitor.complexity,
            cognitive_complexity=visitor.cognitive,
            nesting_depth=visitor.max_nesting,
            line_count=line_count,
            branch_count=visitor.branches,
            loop_count=visitor.loops,
        )

    def analyze_file_complexity(self, path: Path) -> dict[str, ComplexityMetrics]:
        """Analyze complexity for all functions in a file."""
        tree = self.parse_file(path)
        if tree is None:
            return {}

        results = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visitor = ComplexityVisitor()
                visitor.visit(node)
                line_count = getattr(node, 'end_lineno', node.lineno) - node.lineno + 1
                results[node.name] = ComplexityMetrics(
                    cyclomatic_complexity=visitor.complexity,
                    cognitive_complexity=visitor.cognitive,
                    nesting_depth=visitor.max_nesting,
                    line_count=line_count,
                    branch_count=visitor.branches,
                    loop_count=visitor.loops,
                )
        return results

    # ========================================================================
    # Extraction Suggestions
    # ========================================================================

    def suggest_extractions(self, path: Path, function_name: str) -> list[ExtractionSuggestion]:
        """Suggest code blocks that could be extracted to reduce complexity."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return []

        suggestions = []

        # Look for extractable blocks: loops, large if blocks, try/except
        for child in ast.walk(node):
            if isinstance(child, ast.For):
                suggestion = self._analyze_loop_extraction(child, "for loop")
                if suggestion:
                    suggestions.append(suggestion)

            elif isinstance(child, ast.While):
                suggestion = self._analyze_loop_extraction(child, "while loop")
                if suggestion:
                    suggestions.append(suggestion)

            elif isinstance(child, ast.If):
                suggestion = self._analyze_if_extraction(child)
                if suggestion:
                    suggestions.append(suggestion)

            elif isinstance(child, ast.Try):
                suggestion = self._analyze_try_extraction(child)
                if suggestion:
                    suggestions.append(suggestion)

        # Sort by estimated reduction (highest first)
        suggestions.sort(key=lambda s: s.estimated_reduction, reverse=True)
        return suggestions

    def _analyze_loop_extraction(self, node: ast.AST, loop_type: str) -> ExtractionSuggestion | None:
        """Analyze if a loop is a good extraction candidate."""
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        line_count = end - start + 1

        if line_count < 5:
            return None  # Too small to bother

        # Calculate estimated complexity reduction
        visitor = ComplexityVisitor()
        visitor.visit(node)

        return ExtractionSuggestion(
            start_line=start,
            end_line=end,
            description=f"Extract {loop_type} ({line_count} lines) into helper function",
            estimated_reduction=visitor.complexity,
            extractable=True,
        )

    def _analyze_if_extraction(self, node: ast.If) -> ExtractionSuggestion | None:
        """Analyze if an if-block is a good extraction candidate."""
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        line_count = end - start + 1

        if line_count < 8:
            return None  # Too small

        # Check if this is an elif chain - can't extract these, so don't suggest
        has_elif = any(
            isinstance(child, ast.If)
            for child in node.orelse
            if hasattr(node, 'orelse')
        )

        if has_elif:
            return None  # Don't suggest non-extractable patterns

        visitor = ComplexityVisitor()
        visitor.visit(node)

        return ExtractionSuggestion(
            start_line=start,
            end_line=end,
            description=f"Extract if-block ({line_count} lines) into helper function",
            estimated_reduction=visitor.complexity,
            extractable=True,
        )

    def _analyze_try_extraction(self, node: ast.Try) -> ExtractionSuggestion | None:
        """Analyze if a try block is a good extraction candidate."""
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        line_count = end - start + 1

        if line_count < 10:
            return None

        visitor = ComplexityVisitor()
        visitor.visit(node)

        return ExtractionSuggestion(
            start_line=start,
            end_line=end,
            description=f"Extract try/except block ({line_count} lines) into helper function",
            estimated_reduction=visitor.complexity,
            extractable=True,
        )

    def get_extractable_ranges(self, path: Path, function_name: str) -> list[dict[str, Any]]:
        """Get ranges that can be safely extracted from a function.

        Returns a list of dicts with:
        - start_line: int
        - end_line: int
        - description: str
        - extractable: bool
        - estimated_complexity_reduction: int
        """
        suggestions = self.suggest_extractions(path, function_name)
        return [
            {
                "start_line": s.start_line,
                "end_line": s.end_line,
                "description": s.description,
                "extractable": s.extractable,
                "estimated_complexity_reduction": s.estimated_reduction,
                "reason": s.reason,
            }
            for s in suggestions
        ]

    # ========================================================================
    # Violation-Type-Specific Context
    # ========================================================================

    def get_violation_context(
        self, path: Path, function_name: str, violation_type: str
    ) -> dict[str, Any]:
        """Get context tailored to a specific violation type.

        Args:
            path: Path to the Python file
            function_name: Name of the violating function
            violation_type: Type of violation (e.g., 'max-cyclomatic-complexity',
                          'max-function-length', 'max-nesting-depth', 'max-parameter-count')

        Returns:
            Dict with:
            - metrics: Relevant metrics for this violation
            - suggestions: Extraction suggestions tailored to this violation
            - strategy: Recommended fix strategy
        """
        node = self.get_function_node(path, function_name)
        if node is None:
            return {"error": f"Function '{function_name}' not found"}

        metrics = self.analyze_complexity(path, function_name)
        location = self.get_function_location(path, function_name)

        context = {
            "function_name": function_name,
            "location": {"start": location[0], "end": location[1]} if location else None,
            "metrics": {
                "cyclomatic_complexity": metrics.cyclomatic_complexity if metrics else 0,
                "cognitive_complexity": metrics.cognitive_complexity if metrics else 0,
                "nesting_depth": metrics.nesting_depth if metrics else 0,
                "line_count": metrics.line_count if metrics else 0,
                "branch_count": metrics.branch_count if metrics else 0,
                "loop_count": metrics.loop_count if metrics else 0,
            } if metrics else {},
        }

        # Get violation-specific suggestions
        if violation_type == "max-cyclomatic-complexity":
            context["suggestions"] = self._get_complexity_suggestions(node)
            context["strategy"] = "Extract loops and conditional blocks into helper functions"
        elif violation_type == "max-function-length":
            context["suggestions"] = self._get_length_suggestions(node)
            context["strategy"] = "Extract logical sections into helper functions"
        elif violation_type == "max-nesting-depth":
            context["suggestions"] = self._get_nesting_suggestions(node)
            context["strategy"] = "Use early returns (guard clauses) and extract deeply nested blocks"
        elif violation_type == "max-parameter-count":
            context["suggestions"] = self._get_parameter_suggestions(node)
            context["strategy"] = "Group related parameters into dataclasses or dicts"
        else:
            # Fallback to complexity-based suggestions
            context["suggestions"] = self._get_complexity_suggestions(node)
            context["strategy"] = "Extract code blocks into helper functions"

        return context

    def _get_complexity_suggestions(self, node: ast.AST) -> list[dict[str, Any]]:
        """Get extraction suggestions focused on reducing complexity."""
        suggestions = []

        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                start = child.lineno
                end = getattr(child, 'end_lineno', start)
                line_count = end - start + 1
                if line_count >= 5:
                    visitor = ComplexityVisitor()
                    visitor.visit(child)
                    suggestions.append({
                        "start_line": start,
                        "end_line": end,
                        "description": f"Extract loop ({line_count} lines)",
                        "impact": f"Reduces complexity by ~{visitor.complexity}",
                        "extractable": True,
                    })

            elif isinstance(child, ast.If):
                start = child.lineno
                end = getattr(child, 'end_lineno', start)
                line_count = end - start + 1
                has_elif = any(isinstance(c, ast.If) for c in child.orelse)
                if line_count >= 8 and not has_elif:
                    visitor = ComplexityVisitor()
                    visitor.visit(child)
                    suggestions.append({
                        "start_line": start,
                        "end_line": end,
                        "description": f"Extract if-block ({line_count} lines)",
                        "impact": f"Reduces complexity by ~{visitor.complexity}",
                        "extractable": True,
                    })

            elif isinstance(child, ast.Try):
                start = child.lineno
                end = getattr(child, 'end_lineno', start)
                line_count = end - start + 1
                if line_count >= 10:
                    suggestions.append({
                        "start_line": start,
                        "end_line": end,
                        "description": f"Extract try/except block ({line_count} lines)",
                        "impact": "Reduces complexity and improves readability",
                        "extractable": True,
                    })

        suggestions.sort(key=lambda s: s["end_line"] - s["start_line"], reverse=True)
        return suggestions[:5]  # Top 5 suggestions

    def _get_length_suggestions(self, node: ast.AST) -> list[dict[str, Any]]:
        """Get extraction suggestions focused on reducing line count."""
        suggestions = []

        # For function length, suggest ANY substantial block
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.If, ast.Try, ast.With)):
                start = child.lineno
                end = getattr(child, 'end_lineno', start)
                line_count = end - start + 1

                # Lower threshold for length violations - any block 5+ lines
                if line_count >= 5:
                    # Skip elif chains
                    if isinstance(child, ast.If):
                        has_elif = any(isinstance(c, ast.If) for c in child.orelse)
                        if has_elif:
                            continue

                    block_type = type(child).__name__.lower()
                    suggestions.append({
                        "start_line": start,
                        "end_line": end,
                        "description": f"Extract {block_type} block ({line_count} lines)",
                        "impact": f"Reduces function length by {line_count} lines",
                        "extractable": True,
                    })

        # Sort by line count (largest first) for max impact
        suggestions.sort(key=lambda s: s["end_line"] - s["start_line"], reverse=True)
        return suggestions[:5]

    def _get_nesting_suggestions(self, node: ast.AST) -> list[dict[str, Any]]:
        """Get suggestions for reducing nesting depth."""
        suggestions = []

        def find_deeply_nested(n, depth=0, path=None):
            if path is None:
                path = []

            if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                new_path = path + [(type(n).__name__, n.lineno)]
                if depth >= 2:  # Already nested
                    start = n.lineno
                    end = getattr(n, 'end_lineno', start)
                    suggestions.append({
                        "start_line": start,
                        "end_line": end,
                        "description": f"Extract nested block at depth {depth + 1}",
                        "impact": "Reduces nesting depth",
                        "extractable": not (isinstance(n, ast.If) and
                                          any(isinstance(c, ast.If) for c in n.orelse)),
                        "nesting_path": " > ".join(f"{typ}:{line}" for typ, line in new_path),
                    })

                for child in ast.iter_child_nodes(n):
                    find_deeply_nested(child, depth + 1, new_path)
            else:
                for child in ast.iter_child_nodes(n):
                    find_deeply_nested(child, depth, path)

        find_deeply_nested(node)

        # Filter to only extractable suggestions and sort by depth
        suggestions = [s for s in suggestions if s.get("extractable", True)]
        suggestions.sort(key=lambda s: len(s.get("nesting_path", "")), reverse=True)
        return suggestions[:5]

    def _collect_function_params(self, node) -> list[dict]:
        """Collect all parameters from a function node."""
        all_params = []
        args = node.args

        for arg in args.args:
            if arg.arg != 'self':
                param_type = self._get_annotation_str(arg.annotation) if arg.annotation else None
                all_params.append({"name": arg.arg, "type": param_type})

        for arg in args.kwonlyargs:
            param_type = self._get_annotation_str(arg.annotation) if arg.annotation else None
            all_params.append({"name": arg.arg, "type": param_type})

        return all_params

    def _group_params_by_type(self, all_params: list[dict]) -> list[dict]:
        """Group parameters by type and suggest dataclass groupings."""
        typed_params = [p for p in all_params if p["type"]]
        type_groups = {}
        for p in typed_params:
            base_type = p["type"].split("[")[0]
            if base_type not in type_groups:
                type_groups[base_type] = []
            type_groups[base_type].append(p["name"])

        return [
            {
                "description": f"Group {len(params)} '{type_name}' params into dataclass",
                "params": params,
                "impact": f"Reduces parameter count by {len(params) - 1}",
            }
            for type_name, params in type_groups.items()
            if len(params) >= 2
        ]

    def _group_params_by_prefix(self, all_params: list[dict]) -> list[dict]:
        """Group parameters by name prefix and suggest config groupings."""
        prefix_groups = {}
        for p in all_params:
            parts = p["name"].split("_")
            if len(parts) > 1:
                prefix = parts[0]
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(p["name"])

        return [
            {
                "description": f"Group {len(params)} '{prefix}_*' params into '{prefix}_config' dict",
                "params": params,
                "impact": f"Reduces parameter count by {len(params) - 1}",
            }
            for prefix, params in prefix_groups.items()
            if len(params) >= 2
        ]

    def _get_parameter_suggestions(self, node: ast.AST) -> list[dict[str, Any]]:
        """Get suggestions for reducing parameter count."""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return []

        all_params = self._collect_function_params(node)
        if len(all_params) <= 5:
            return []

        suggestions = self._group_params_by_type(all_params)
        suggestions.extend(self._group_params_by_prefix(all_params))
        return suggestions[:5]

    # ========================================================================
    # Import Analysis
    # ========================================================================

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

    # ========================================================================
    # Dependency Analysis
    # ========================================================================

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
