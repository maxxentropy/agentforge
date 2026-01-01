# @spec_file: .agentforge/specs/core-bridge-mappings-v1.yaml
# @spec_id: core-bridge-mappings-v1
# @component_id: bridge-mappings-__init__
# @test_path: tests/unit/tools/bridge/test_registry.py

"""
Pattern Mappings
================

Mappings that transform discovered patterns into conformance checks.

Each mapping:
1. Declares which patterns it handles
2. Implements matches() to determine applicability
3. Implements get_templates() to return check templates

Available mappings are auto-registered via the @MappingRegistry.register decorator.
"""

from .base import PatternMapping
from .registry import MappingRegistry

# Import all mappings to trigger registration
from . import cqrs
from . import architecture
from . import repository
from . import conventions

__all__ = [
    "PatternMapping",
    "MappingRegistry",
]
