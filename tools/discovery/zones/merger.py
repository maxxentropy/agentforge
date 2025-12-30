"""
Zone Configuration Merger
=========================

Merges auto-detected zones with manual configuration from repo.yaml.
Manual configuration can:
- Override auto-detected zone properties
- Add zones that weren't auto-detected
- Exclude directories from zone detection
- Associate contracts with zones
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from tools.discovery.domain import Zone, ZoneDetectionMode


class ZoneMerger:
    """
    Merges auto-detected zones with manual configuration.

    Supports three discovery modes:
    - auto: Use only auto-detected zones
    - manual: Use only manually configured zones
    - hybrid: Merge auto-detected with manual overrides (default)
    """

    def __init__(self, repo_root: Path, config: Optional[Dict[str, Any]] = None):
        self.repo_root = repo_root
        self.config = config or {}
        self.discovery_config = self.config.get("discovery", {})
        self.zones_config = self.config.get("zones", {})

    @property
    def discovery_mode(self) -> str:
        """Get the discovery mode from config (default: hybrid)."""
        return self.discovery_config.get("mode", "hybrid")

    def merge_zones(self, auto_zones: List[Zone]) -> List[Zone]:
        """
        Merge auto-detected zones with manual configuration.

        Args:
            auto_zones: List of auto-detected zones

        Returns:
            Merged list of zones based on discovery mode
        """
        mode = self.discovery_mode

        if mode == "manual":
            return self._get_manual_zones()
        elif mode == "auto":
            return auto_zones
        else:  # hybrid
            return self._merge_hybrid(auto_zones)

    def _merge_hybrid(self, auto_zones: List[Zone]) -> List[Zone]:
        """Merge auto-detected zones with manual overrides."""
        result: List[Zone] = []

        # Process auto-detected zones with potential overrides
        for auto_zone in auto_zones:
            if auto_zone.name in self.zones_config:
                manual = self.zones_config[auto_zone.name]

                # Check for exclusion
                if manual.get("exclude"):
                    continue

                # Merge: manual overrides auto
                merged = Zone(
                    name=auto_zone.name,
                    path=Path(manual.get("path", str(auto_zone.path))),
                    language=manual.get("language", auto_zone.language),
                    marker=auto_zone.marker,
                    detection=ZoneDetectionMode.HYBRID,
                    purpose=manual.get("purpose"),
                    contracts=manual.get("contracts", []),
                )
                result.append(merged)
            else:
                result.append(auto_zone)

        # Add manual-only zones
        for name, zone_config in self.zones_config.items():
            # Skip if already processed or excluded
            if any(z.name == name for z in result):
                continue
            if zone_config.get("exclude"):
                continue

            # Require path and language for manual zones
            if "path" not in zone_config or "language" not in zone_config:
                continue

            manual_zone = Zone(
                name=name,
                path=self.repo_root / zone_config["path"],
                language=zone_config["language"],
                marker=None,
                detection=ZoneDetectionMode.MANUAL,
                purpose=zone_config.get("purpose"),
                contracts=zone_config.get("contracts", []),
            )
            result.append(manual_zone)

        return result

    def _get_manual_zones(self) -> List[Zone]:
        """Get zones from manual configuration only."""
        result: List[Zone] = []

        for name, zone_config in self.zones_config.items():
            if zone_config.get("exclude"):
                continue

            # Require path and language for manual zones
            if "path" not in zone_config or "language" not in zone_config:
                continue

            zone = Zone(
                name=name,
                path=self.repo_root / zone_config["path"],
                language=zone_config["language"],
                marker=None,
                detection=ZoneDetectionMode.MANUAL,
                purpose=zone_config.get("purpose"),
                contracts=zone_config.get("contracts", []),
            )
            result.append(zone)

        return result


def merge_zones(
    auto_zones: List[Zone],
    repo_root: Path,
    config: Optional[Dict[str, Any]] = None
) -> List[Zone]:
    """
    Convenience function for zone merging.

    Args:
        auto_zones: List of auto-detected zones
        repo_root: Path to repository root
        config: Optional repo.yaml configuration dict

    Returns:
        Merged list of zones

    Example:
        >>> auto_zones = detect_zones(repo_root)
        >>> config = yaml.safe_load(open(".agentforge/repo.yaml"))
        >>> zones = merge_zones(auto_zones, repo_root, config)
    """
    merger = ZoneMerger(repo_root, config)
    return merger.merge_zones(auto_zones)
