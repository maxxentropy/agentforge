"""
Python Provider Package
=======================

Modular implementation of the Python language provider.

This package decomposes the provider into focused mixins:
- ProjectMixin: Project detection and parsing
- SymbolMixin: Symbol extraction from Python files
- AnalysisMixin: Complexity analysis and extraction suggestions
- ViolationMixin: Violation context building
- ImportMixin: Import and dependency analysis

The main class (PythonProvider) inherits from all mixins,
combining their capabilities while keeping code organized.

Backward Compatibility
----------------------
This package maintains the same public API as the original module.
Existing imports work unchanged:

    from .python_provider import PythonProvider
    from .python_provider import ComplexityMetrics, ExtractionSuggestion
"""

from .base import PythonProvider
from .complexity import ComplexityMetrics, ComplexityVisitor, ExtractionSuggestion

__all__ = [
    "PythonProvider",
    "ComplexityMetrics",
    "ComplexityVisitor",
    "ExtractionSuggestion",
]
