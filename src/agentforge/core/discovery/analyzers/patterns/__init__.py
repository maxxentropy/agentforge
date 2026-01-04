"""
Pattern Analyzer
================

Detects code patterns through multi-signal analysis.
Combines naming conventions, structural analysis, and AST patterns.
"""

from .analyzer import PatternAnalyzer
from .definitions import PATTERN_DEFINITIONS
from .frameworks import FRAMEWORK_PATTERNS
from .types import PatternAnalysisResult, PatternMatch

__all__ = [
    # Main analyzer
    "PatternAnalyzer",
    # Types
    "PatternAnalysisResult",
    "PatternMatch",
    # Pattern definitions
    "PATTERN_DEFINITIONS",
    "FRAMEWORK_PATTERNS",
]
