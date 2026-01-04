"""
Complexity Analysis Mixin
=========================

Methods for analyzing code complexity and suggesting extractions.
"""

import ast
from pathlib import Path
from typing import Any

from .complexity import ComplexityMetrics, ComplexityVisitor, ExtractionSuggestion


class AnalysisMixin:
    """Complexity analysis methods for PythonProvider."""

    # Type hints for mixin - provided by main class
    parse_file: Any
    get_function_node: Any

    def analyze_complexity(self, path: Path, function_name: str) -> ComplexityMetrics | None:
        """Analyze complexity of a specific function."""
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
        """Analyze complexity of all functions in a file."""
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

    def _analyze_node_for_extraction(self, node: ast.AST) -> ExtractionSuggestion | None:
        """Analyze a node for extraction potential."""
        if isinstance(node, (ast.For, ast.While)):
            return self._analyze_loop_extraction(node, type(node).__name__)
        elif isinstance(node, ast.If):
            return self._analyze_if_extraction(node)
        elif isinstance(node, ast.Try):
            return self._analyze_try_extraction(node)
        return None

    def suggest_extractions(self, path: Path, function_name: str) -> list[ExtractionSuggestion]:
        """Suggest code blocks that could be extracted to reduce complexity."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return []

        suggestions = []
        for child in ast.walk(node):
            suggestion = self._analyze_node_for_extraction(child)
            if suggestion:
                suggestions.append(suggestion)

        suggestions.sort(key=lambda s: s.estimated_reduction, reverse=True)
        return suggestions[:5]

    def _analyze_loop_extraction(self, node: ast.AST, loop_type: str) -> ExtractionSuggestion | None:
        """Analyze a loop for extraction potential."""
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        line_count = end - start + 1

        if line_count < 5:
            return None

        visitor = ComplexityVisitor()
        visitor.visit(node)

        return ExtractionSuggestion(
            start_line=start,
            end_line=end,
            description=f"Extract {loop_type.lower()} loop ({line_count} lines)",
            estimated_reduction=visitor.complexity,
            extractable=True,
        )

    def _analyze_if_extraction(self, node: ast.If) -> ExtractionSuggestion | None:
        """Analyze an if-block for extraction potential."""
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        line_count = end - start + 1

        has_elif = any(isinstance(c, ast.If) for c in node.orelse)
        if line_count < 8 or has_elif:
            return None

        visitor = ComplexityVisitor()
        visitor.visit(node)

        return ExtractionSuggestion(
            start_line=start,
            end_line=end,
            description=f"Extract if-block ({line_count} lines)",
            estimated_reduction=visitor.complexity,
            extractable=True,
        )

    def _analyze_try_extraction(self, node: ast.Try) -> ExtractionSuggestion | None:
        """Analyze a try-except block for extraction potential."""
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        line_count = end - start + 1

        if line_count < 10:
            return None

        return ExtractionSuggestion(
            start_line=start,
            end_line=end,
            description=f"Extract try/except block ({line_count} lines)",
            estimated_reduction=2,
            extractable=True,
        )

    def get_extractable_ranges(self, path: Path, function_name: str) -> list[dict[str, Any]]:
        """Get ranges that can be safely extracted."""
        node = self.get_function_node(path, function_name)
        if node is None:
            return []

        ranges = []

        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While, ast.If, ast.Try, ast.With)):
                start = child.lineno
                end = getattr(child, 'end_lineno', start)
                line_count = end - start + 1

                if line_count < 3:
                    continue

                if isinstance(child, ast.If):
                    has_elif = any(isinstance(c, ast.If) for c in child.orelse)
                    if has_elif:
                        continue

                block_type = type(child).__name__
                ranges.append({
                    "start_line": start,
                    "end_line": end,
                    "type": block_type,
                    "description": f"{block_type} block ({line_count} lines)",
                    "line_count": line_count,
                })

        ranges.sort(key=lambda r: r["line_count"], reverse=True)
        return ranges[:10]
