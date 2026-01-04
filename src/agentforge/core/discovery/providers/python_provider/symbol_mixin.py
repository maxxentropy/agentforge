"""
Symbol Extraction Mixin
=======================

Methods for extracting symbols from Python files.
"""

import ast
from pathlib import Path
from typing import Any

from ..base import Symbol


class SymbolMixin:
    """Symbol extraction methods for PythonProvider."""

    # Type hints for mixin - provided by main class
    parse_file: Any

    def extract_symbols(self, path: Path) -> list[Symbol]:
        """Extract all symbols from Python file."""
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
        """Process an ast.ClassDef node into a Symbol."""
        bases = [self._get_attr_name(base) if isinstance(base, ast.Attribute)
                 else getattr(base, 'id', str(base))
                 for base in node.bases]

        methods = [
            {"name": m.name, "visibility": self._get_visibility(m.name)}
            for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        return Symbol(
            name=node.name,
            kind="class",
            file_path=path,
            line_number=node.lineno,
            end_line=getattr(node, 'end_lineno', node.lineno),
            visibility=self._get_visibility(node.name),
            modifiers=["async"] if any(
                isinstance(m, ast.AsyncFunctionDef) for m in node.body
            ) else [],
            parent=None,
            children=[m["name"] for m in methods],
            metadata={
                "bases": bases,
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                "methods": methods,
            },
        )

    def _process_function_node(self, node, path: Path, tree: ast.AST) -> Symbol:
        """Process a function/method node into a Symbol."""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        parent_class = self._find_parent_class(node, tree)

        params = []
        for arg in node.args.args:
            param = {"name": arg.arg}
            if arg.annotation:
                param["type"] = self._get_annotation_str(arg.annotation)
            params.append(param)

        return_type = None
        if node.returns:
            return_type = self._get_annotation_str(node.returns)

        modifiers = []
        if is_async:
            modifiers.append("async")

        for dec in node.decorator_list:
            dec_name = self._get_decorator_name(dec)
            if dec_name in ("staticmethod", "classmethod", "property"):
                modifiers.append(dec_name)

        return Symbol(
            name=node.name,
            kind="method" if parent_class else "function",
            file_path=path,
            line_number=node.lineno,
            end_line=getattr(node, 'end_lineno', node.lineno),
            visibility=self._get_visibility(node.name),
            modifiers=modifiers,
            parent=parent_class,
            children=[],
            metadata={
                "parameters": params,
                "return_type": return_type,
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                "is_async": is_async,
            },
        )

    def _find_parent_class(self, node, tree: ast.AST) -> str | None:
        """Find the parent class of a method."""
        for class_node in ast.walk(tree):
            if isinstance(class_node, ast.ClassDef):
                if node in class_node.body:
                    return class_node.name
        return None

    def _get_visibility(self, name: str) -> str:
        """Determine visibility from name."""
        if name.startswith("__") and not name.endswith("__"):
            return "private"
        elif name.startswith("_"):
            return "protected"
        return "public"

    def _get_decorator_name(self, node) -> str:
        """Get decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attr_name(node)
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return str(node)

    def _get_attr_name(self, node: ast.Attribute) -> str:
        """Get full attribute name (e.g., 'module.Class')."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _get_annotation_str(self, node) -> str:
        """Convert annotation AST node to string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Subscript):
            base = self._get_annotation_str(node.value)
            if isinstance(node.slice, ast.Tuple):
                args = ", ".join(self._get_annotation_str(e) for e in node.slice.elts)
            else:
                args = self._get_annotation_str(node.slice)
            return f"{base}[{args}]"
        elif isinstance(node, ast.Attribute):
            return self._get_attr_name(node)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            left = self._get_annotation_str(node.left)
            right = self._get_annotation_str(node.right)
            return f"{left} | {right}"
        return str(node)
