"""
Zone Detection Module
=====================

Provides zone detection and configuration merging for
multi-language repository support.
"""

from .detector import ZoneDetector, detect_zones
from .merger import ZoneMerger, merge_zones

__all__ = [
    "ZoneDetector",
    "detect_zones",
    "ZoneMerger",
    "merge_zones",
]
