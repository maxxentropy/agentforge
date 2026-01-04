"""
Violation Context Mixin
=======================

Methods for building context tailored to specific violation types.
"""

import ast
from pathlib import Path
from typing import Any

from .complexity import ComplexityVisitor


class ViolationMixin:
    """Violation context building methods for PythonProvider."""

    # Type hints for mixin - provided by main class
    get_function_node: Any
    get_function_location: Any
    analyze_complexity: Any
    _get_annotation_str: Any

    # Violation type to suggestion method and strategy mapping
    _VIOLATION_STRATEGIES = {
        "max-cyclomatic-complexity": (
            "_get_complexity_suggestions",
            "Extract complex logic blocks into helper functions"
        ),
        "max-cognitive-complexity": (
            "_get_complexity_suggestions",
            "Reduce nesting and simplify control flow"
        ),
        "max-function-length": (
            "_get_length_suggestions",
            "Extract logical sections into smaller functions"
        ),
        "max-nesting-depth": (
            "_get_nesting_suggestions",
            "Use early returns and extract nested blocks"
        ),
        "max-parameter-count": (
            "_get_parameter_suggestions",
            "Group related parameters into dataclasses or config objects"
        ),
    }

    def get_violation_context(
        self, path: Path, function_name: str, violation_type: str
    ) -> dict[str, Any]:
        """Get context tailored to a specific violation type."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return {"error": f"Function '{function_name}' not found"}

        context = self._build_base_context(path, function_name)
        self._add_violation_strategy(context, node, violation_type)
        return context

    def _build_base_context(self, path: Path, function_name: str) -> dict[str, Any]:
        """Build base context with metrics and location."""
        metrics = self.analyze_complexity(path, function_name)
        location = self.get_function_location(path, function_name)

        return {
            "function_name": function_name,
            "location": {"start": location[0], "end": location[1]} if location else None,
            "metrics": self._format_metrics(metrics),
        }

    def _format_metrics(self, metrics: Any) -> dict[str, int]:
        """Format complexity metrics into dict."""
        if not metrics:
            return {}
        return {
            "cyclomatic_complexity": metrics.cyclomatic_complexity,
            "cognitive_complexity": metrics.cognitive_complexity,
            "nesting_depth": metrics.nesting_depth,
            "line_count": metrics.line_count,
            "branch_count": metrics.branch_count,
            "loop_count": metrics.loop_count,
        }

    def _add_violation_strategy(
        self, context: dict[str, Any], node: ast.AST, violation_type: str
    ) -> None:
        """Add violation-specific suggestions and strategy to context."""
        method_name, strategy = self._VIOLATION_STRATEGIES.get(
            violation_type,
            ("_get_complexity_suggestions", "Extract code blocks into helper functions"),
        )
        suggestion_getter = getattr(self, method_name)
        context["suggestions"] = suggestion_getter(node)
        context["strategy"] = strategy

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
        return suggestions[:5]

    def _get_length_suggestions(self, node: ast.AST) -> list[dict[str, Any]]:
        """Get extraction suggestions focused on reducing line count."""
        suggestions = []

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.If, ast.Try, ast.With)):
                start = child.lineno
                end = getattr(child, 'end_lineno', start)
                line_count = end - start + 1

                if line_count >= 5:
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
                if depth >= 2:
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
