"""
Brownfield Discovery
====================

Reverse-engineers codebase artifacts (specs, architecture) from existing code.
Supports gradual onboarding of legacy codebases to AgentForge.

Usage:
    from tools.discovery import DiscoveryManager

    manager = DiscoveryManager(root_path=Path("."), verbose=True)
    result = manager.discover()

    if result.success:
        print(f"Profile saved to: {result.profile_path}")
"""

from .manager import DiscoveryManager, DiscoveryResult
from .domain import CodebaseProfile, DiscoveryPhase

__all__ = ["DiscoveryManager", "DiscoveryResult", "CodebaseProfile", "DiscoveryPhase"]
