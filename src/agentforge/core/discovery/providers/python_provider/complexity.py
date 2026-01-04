"""
Complexity Analysis Classes
===========================

Dataclasses and AST visitor for complexity analysis.
These are standalone classes used by the PythonProvider.
"""

import ast
from dataclasses import dataclass


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
        self.generic_visit(node)
