#!/usr/bin/env python3
"""
AST-based Verification Checks
=============================

Code quality metrics using Python's AST module.

Extracted from VerificationRunner for modularity.
Supports: cyclomatic_complexity, function_length, nesting_depth,
          parameter_count, class_size, import_count
"""

import ast
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from agentforge.core.command_runners import CommandRunner


class ASTChecker:
    """Handles AST-based code quality checks."""

    def __init__(self, command_runner: "CommandRunner" = None):
        self.command_runner = command_runner

    def check_metric(
        self,
        tree: ast.AST,
        source: str,
        metric: str,
        max_value: int,
        file_path: Path
    ) -> List[Dict]:
        """Check a specific AST metric and return violations."""
        metric_handlers = {
            "function_length": self._check_function_length,
            "nesting_depth": self._check_nesting_depth,
            "parameter_count": self._check_parameter_count,
            "class_size": self._check_class_size,
            "import_count": self._check_import_count,
        }

        handler = metric_handlers.get(metric)
        if handler:
            return handler(tree, max_value, file_path)

        if metric == "cyclomatic_complexity" and self.command_runner:
            return self._check_complexity_with_radon(file_path, max_value)

        return []

    def _check_function_length(
        self, tree: ast.AST, max_lines: int, file_path: Path
    ) -> List[Dict]:
        """Check function lengths."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno + 1
                    if length > max_lines:
                        violations.append({
                            "file": str(file_path),
                            "function": node.name,
                            "line": node.lineno,
                            "value": length,
                            "message": f"Function '{node.name}' is {length} lines (max: {max_lines})",
                        })

        return violations

    def _check_nesting_depth(
        self, tree: ast.AST, max_depth: int, file_path: Path
    ) -> List[Dict]:
        """Check nesting depth."""
        violations = []
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)

        def check_depth(node: ast.AST, current_depth: int, parent_func: str):
            new_depth = current_depth
            if isinstance(node, nesting_nodes):
                new_depth = current_depth + 1
                if new_depth > max_depth:
                    violations.append({
                        "file": str(file_path),
                        "function": parent_func,
                        "line": node.lineno,
                        "value": new_depth,
                        "message": f"Nesting depth {new_depth} in '{parent_func}' (max: {max_depth})",
                    })

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    check_depth(child, 0, child.name)
                else:
                    check_depth(child, new_depth, parent_func)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                check_depth(node, 0, node.name)

        return violations

    def _check_parameter_count(
        self, tree: ast.AST, max_params: int, file_path: Path
    ) -> List[Dict]:
        """Check function parameter count."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                param_count = (
                    len(args.args) +
                    len(args.posonlyargs) +
                    len(args.kwonlyargs) +
                    (1 if args.vararg else 0) +
                    (1 if args.kwarg else 0)
                )

                if args.args and args.args[0].arg in ('self', 'cls'):
                    param_count -= 1

                if param_count > max_params:
                    violations.append({
                        "file": str(file_path),
                        "function": node.name,
                        "line": node.lineno,
                        "value": param_count,
                        "message": f"Function '{node.name}' has {param_count} parameters (max: {max_params})",
                    })

        return violations

    def _check_class_size(
        self, tree: ast.AST, max_methods: int, file_path: Path
    ) -> List[Dict]:
        """Check class method count."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(
                    1 for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )

                if method_count > max_methods:
                    violations.append({
                        "file": str(file_path),
                        "function": node.name,
                        "line": node.lineno,
                        "value": method_count,
                        "message": f"Class '{node.name}' has {method_count} methods (max: {max_methods})",
                    })

        return violations

    def _check_import_count(
        self, tree: ast.AST, max_imports: int, file_path: Path
    ) -> List[Dict]:
        """Check module import count."""
        import_count = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        )

        if import_count > max_imports:
            return [{
                "file": str(file_path),
                "function": "<module>",
                "line": 1,
                "value": import_count,
                "message": f"Module has {import_count} imports (max: {max_imports})",
            }]

        return []

    def _check_complexity_with_radon(
        self, file_path: Path, max_complexity: int
    ) -> List[Dict]:
        """Check cyclomatic complexity using radon."""
        if not self.command_runner:
            return []

        violations = []
        result = self.command_runner.run_radon_cc(file_path)

        if not result.parsed_output:
            return violations

        for funcs in result.parsed_output.values():
            for func in funcs:
                complexity = func.get("complexity", 0)
                if complexity > max_complexity:
                    violations.append({
                        "file": str(file_path),
                        "function": func.get("name"),
                        "line": func.get("lineno"),
                        "value": complexity,
                        "message": f"Function '{func.get('name')}' has complexity {complexity} (max: {max_complexity})",
                    })

        return violations
