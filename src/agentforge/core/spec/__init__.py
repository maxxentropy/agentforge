# @spec_file: .agentforge/specs/core-spec-v1.yaml
# @spec_id: core-spec-v1
# @component_id: core-spec-init
# @test_path: tests/unit/core/spec/test_init.py

"""
Spec management utilities.

Provides tools for analyzing and managing the spec space:
- SpecPlacementAnalyzer: Determines where new features belong
- Spec loading and indexing
"""

from agentforge.core.spec.placement import (
    PlacementAction,
    PlacementDecision,
    SpecPlacementAnalyzer,
)

__all__ = [
    'SpecPlacementAnalyzer',
    'PlacementDecision',
    'PlacementAction',
]
