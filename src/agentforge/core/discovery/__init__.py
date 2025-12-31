"""
Brownfield Discovery
====================

Reverse-engineers codebase artifacts (specs, architecture) from existing code.
Supports gradual onboarding of legacy codebases to AgentForge.

Single-zone usage:
    from agentforge.core.discovery import DiscoveryManager

    manager = DiscoveryManager(root_path=Path("."), verbose=True)
    result = manager.discover()

    if result.success:
        print(f"Profile saved to: {result.profile_path}")

Multi-zone usage:
    from agentforge.core.discovery import MultiZoneDiscoveryManager

    manager = MultiZoneDiscoveryManager(root_path=Path("."), verbose=True)
    result = manager.discover()

    for zone_name, profile in result.zone_profiles.items():
        print(f"{zone_name}: {profile.zone.language}")
"""

from .manager import DiscoveryManager, DiscoveryResult, MultiZoneDiscoveryManager, MultiZoneDiscoveryResult
from .domain import CodebaseProfile, DiscoveryPhase, Zone, Interaction, ZoneProfile

__all__ = [
    "DiscoveryManager",
    "DiscoveryResult",
    "MultiZoneDiscoveryManager",
    "MultiZoneDiscoveryResult",
    "CodebaseProfile",
    "DiscoveryPhase",
    "Zone",
    "Interaction",
    "ZoneProfile",
]
