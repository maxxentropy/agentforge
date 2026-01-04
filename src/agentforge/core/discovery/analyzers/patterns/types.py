"""
Pattern Analysis Types
======================

Data classes for pattern analysis results.
"""

from dataclasses import dataclass
from pathlib import Path

from ...domain import Detection, PatternDetection


@dataclass
class PatternMatch:
    """A single pattern match instance."""
    pattern_name: str
    file_path: Path
    line_number: int
    signal_type: str
    matched_text: str
    weight: float


@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis."""
    patterns: dict[str, PatternDetection]
    frameworks: dict[str, Detection]
    matches: list[PatternMatch]
    total_files_analyzed: int
