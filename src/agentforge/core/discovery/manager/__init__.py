# @spec_file: .agentforge/specs/core-discovery-v1.yaml
# @spec_id: core-discovery-v1
# @component_id: core-discovery-manager
# @test_path: tests/unit/tools/conformance/test_manager.py

"""
Discovery Manager Package
=========================

Orchestrates the brownfield discovery process through multiple phases.

Module Structure:
- types.py: Data classes (PhaseResult, DiscoveryResult, etc.)
- helpers.py: Helper functions
- single_zone.py: DiscoveryManager class
- multi_zone.py: MultiZoneDiscoveryManager class
"""

from .helpers import (
    collect_unique_dependencies,
    get_frameworks_list,
)
from .multi_zone import MultiZoneDiscoveryManager
from .single_zone import DiscoveryManager
from .types import (
    DiscoveryPhaseStatus,
    DiscoveryResult,
    MultiZoneDiscoveryResult,
    PhaseResult,
)

# Backwards-compatible aliases with underscore prefix
_get_frameworks_list = get_frameworks_list
_collect_unique_dependencies = collect_unique_dependencies

__all__ = [
    # Main exports
    "DiscoveryManager",
    "MultiZoneDiscoveryManager",
    # Types
    "DiscoveryPhaseStatus",
    "PhaseResult",
    "DiscoveryResult",
    "MultiZoneDiscoveryResult",
    # Helpers
    "get_frameworks_list",
    "collect_unique_dependencies",
    # Backwards-compatible aliases
    "_get_frameworks_list",
    "_collect_unique_dependencies",
]
