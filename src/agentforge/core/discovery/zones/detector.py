"""
Zone Auto-Detection
====================

Automatically detects language zones from project markers.
Each zone represents a coherent area of code with its own
language, patterns, and conventions.

Detection priority:
1. .sln files - defines .NET zone boundary
2. .csproj files - defines .NET project zone (if no parent .sln)
3. pyproject.toml - defines Python zone boundary
4. setup.py - defines Python zone boundary
5. package.json - defines Node.js zone boundary
6. go.mod - defines Go zone boundary
7. Cargo.toml - defines Rust zone boundary
"""

from pathlib import Path

from agentforge.core.discovery.domain import Zone, ZoneDetectionMode

# Marker priority (higher = checked first, takes precedence)
ZONE_MARKERS: list[tuple[str, str, int]] = [
    # (pattern, language, priority)
    ("*.sln", "csharp", 100),        # Solution-level .NET
    ("*.csproj", "csharp", 90),      # Project-level .NET
    ("pyproject.toml", "python", 80),
    ("setup.py", "python", 75),
    ("package.json", "typescript", 70),  # Assume TypeScript, can be overridden
    ("go.mod", "go", 60),
    ("Cargo.toml", "rust", 50),
]

# Directories to skip during zone detection
SKIP_DIRECTORIES = {
    "node_modules",
    "__pycache__",
    ".git",
    ".vs",
    "bin",
    "obj",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    ".tox",
    "packages",
}


class ZoneDetector:
    """
    Detects language zones from project markers.

    Uses a priority-based algorithm to avoid nesting conflicts
    (e.g., a csproj inside a sln area shouldn't create a separate zone).
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def detect_zones(self) -> list[Zone]:
        """
        Auto-detect language zones from project markers.

        Returns zones sorted by path (shortest first, i.e., outer zones first).
        """
        zones: list[Zone] = []

        # Process markers by priority (highest first)
        sorted_markers = sorted(ZONE_MARKERS, key=lambda x: x[2], reverse=True)

        for pattern, language, _priority in sorted_markers:
            for marker_path in self._find_markers(pattern):
                # Skip if already covered by an existing zone
                if self._is_in_existing_zone(marker_path, zones):
                    continue

                zone = self._create_zone_from_marker(marker_path, language)
                if zone:
                    zones.append(zone)

        # Sort by path (outer zones first)
        zones.sort(key=lambda z: len(z.path.parts))

        return zones

    def _find_markers(self, pattern: str) -> list[Path]:
        """Find all marker files matching the pattern."""
        results = []
        for path in self.repo_root.rglob(pattern):
            # Skip excluded directories
            if any(skip in path.parts for skip in SKIP_DIRECTORIES):
                continue
            results.append(path)
        return results

    def _is_in_existing_zone(self, path: Path, zones: list[Zone]) -> bool:
        """Check if path is already covered by an existing zone."""
        return any(zone.contains_path(path.parent) for zone in zones)

    def _create_zone_from_marker(self, marker: Path, language: str) -> Zone | None:
        """Create a zone from a marker file."""
        zone_name = self._derive_zone_name(marker)
        zone_path = self._derive_zone_path(marker)

        return Zone(
            name=zone_name,
            path=zone_path,
            language=language,
            marker=marker,
            detection=ZoneDetectionMode.AUTO,
        )

    def _derive_zone_name(self, marker: Path) -> str:
        """Derive a zone name from marker file."""
        if marker.suffix == ".sln":
            return marker.stem
        if marker.suffix == ".csproj":
            return marker.stem
        # For other markers, use directory name
        return marker.parent.name

    def _derive_zone_path(self, marker: Path) -> Path:
        """Derive zone root path from marker file."""
        # For solution files, the zone is the solution directory
        if marker.suffix == ".sln":
            return marker.parent
        # For project files, the zone is the project directory
        if marker.suffix == ".csproj":
            return marker.parent
        # For other markers, use the directory containing the marker
        return marker.parent


def detect_zones(repo_root: Path) -> list[Zone]:
    """
    Convenience function for zone detection.

    Args:
        repo_root: Path to repository root

    Returns:
        List of detected zones, sorted by path depth

    Example:
        >>> zones = detect_zones(Path("/my/repo"))
        >>> for zone in zones:
        ...     print(f"{zone.name}: {zone.language} at {zone.path}")
    """
    detector = ZoneDetector(repo_root)
    return detector.detect_zones()
