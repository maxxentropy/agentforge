"""
Discovery Manager Helpers
=========================

Helper functions for discovery managers.
"""

from typing import Any

from ..domain import DependencyInfo


def get_frameworks_list(project_info: dict[str, Any]) -> list[str]:
    """Extract and normalize frameworks list from project info."""
    frameworks = project_info.get("frameworks", [])
    primary_framework = project_info.get("framework")
    if primary_framework:
        # Ensure primary framework is first, avoid duplicates
        return [primary_framework] + [f for f in frameworks if f != primary_framework]
    return frameworks


def collect_unique_dependencies(zone_profiles: dict) -> list[DependencyInfo]:
    """Collect unique dependencies across all zone profiles."""
    all_deps: list[DependencyInfo] = []
    seen: set[str] = set()
    for profile in zone_profiles.values():
        for dep in profile.dependencies:
            if dep.name not in seen:
                all_deps.append(dep)
                seen.add(dep.name)
    return all_deps


# Backwards-compatible aliases
_get_frameworks_list = get_frameworks_list
_collect_unique_dependencies = collect_unique_dependencies
