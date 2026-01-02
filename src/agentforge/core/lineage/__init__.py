"""
Lineage Tracking
================

Provides audit trail linkage between specs, tests, and implementation code.
Every generated artifact embeds metadata about its origin.
"""

from .metadata import LineageMetadata, generate_lineage_header, parse_lineage_from_file

__all__ = [
    "LineageMetadata",
    "parse_lineage_from_file",
    "generate_lineage_header",
]
