"""
Profile Loader
==============

Loads and parses codebase profiles from discovery output.
Extracts zones, patterns, and creates mapping contexts.
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from bridge.domain import MappingContext

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class ProfileLoader:
    """
    Loads codebase profiles and creates mapping contexts.

    Handles both single-zone and multi-zone profiles.
    """

    DEFAULT_PROFILE_PATH = ".agentforge/codebase_profile.yaml"

    def __init__(self, root_path: Path):
        """
        Initialize profile loader.

        Args:
            root_path: Root path of the repository
        """
        self.root_path = Path(root_path).resolve()
        self._profile: Optional[Dict[str, Any]] = None
        self._profile_path: Optional[Path] = None
        self._profile_hash: Optional[str] = None

    def load(self, profile_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load profile from YAML file.

        Args:
            profile_path: Path to profile file (optional)

        Returns:
            Parsed profile dictionary

        Raises:
            FileNotFoundError: If profile doesn't exist
            ValueError: If profile is invalid
        """
        if yaml is None:
            raise ImportError("PyYAML is required for profile loading")

        if profile_path is None:
            profile_path = self.root_path / self.DEFAULT_PROFILE_PATH

        self._profile_path = Path(profile_path)
        if not self._profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {self._profile_path}")

        content = self._profile_path.read_text()
        self._profile_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

        self._profile = yaml.safe_load(content)
        if not isinstance(self._profile, dict):
            raise ValueError("Profile must be a YAML dictionary")

        return self._profile

    @property
    def profile_path(self) -> Optional[str]:
        """Get relative profile path."""
        if self._profile_path:
            try:
                return str(self._profile_path.relative_to(self.root_path))
            except ValueError:
                return str(self._profile_path)
        return None

    @property
    def profile_hash(self) -> Optional[str]:
        """Get profile content hash."""
        return self._profile_hash

    @property
    def profile_generated_at(self) -> Optional[str]:
        """Get profile generation timestamp."""
        if self._profile:
            return self._profile.get("generated_at")
        return None

    def is_multi_zone(self) -> bool:
        """Check if profile has multiple zones."""
        if not self._profile:
            return False
        # Check for zones key (multi-zone format)
        if "zones" in self._profile and isinstance(self._profile["zones"], dict):
            return len(self._profile["zones"]) > 1
        return False

    def get_zones(self) -> List[str]:
        """
        Get list of zone names from profile.

        Returns:
            List of zone names, or ['default'] for single-zone profiles
        """
        if not self._profile:
            return []

        # Multi-zone format
        if "zones" in self._profile and isinstance(self._profile["zones"], dict):
            return list(self._profile["zones"].keys())

        # Single-zone format - use 'default' zone
        return ["default"]

    def get_languages(self) -> List[Tuple[str, float]]:
        """
        Get detected languages with confidence.

        Returns:
            List of (language, confidence) tuples
        """
        if not self._profile:
            return []

        languages = self._profile.get("languages", [])
        result = []

        for lang in languages:
            if isinstance(lang, dict):
                name = lang.get("name", "")
                confidence = lang.get("confidence", 0.0)
                result.append((name, confidence))
            elif isinstance(lang, str):
                result.append((lang, 1.0))

        return result

    def get_primary_language(self) -> Optional[str]:
        """Get the primary language from profile."""
        if not self._profile:
            return None

        languages = self._profile.get("languages", [])
        for lang in languages:
            if isinstance(lang, dict):
                if lang.get("primary", False):
                    return lang.get("name")

        # Fallback to first language
        if languages:
            first = languages[0]
            if isinstance(first, dict):
                return first.get("name")
            return first

        return None

    def create_context(self, zone_name: Optional[str] = None) -> MappingContext:
        """
        Create a mapping context for a zone.

        Args:
            zone_name: Zone name (optional for single-zone profiles)

        Returns:
            MappingContext with profile data
        """
        if not self._profile:
            raise ValueError("Profile not loaded. Call load() first.")

        # Check if zones exist in profile (even if just 1)
        zones = self._profile.get("zones", {})
        has_zones = isinstance(zones, dict) and len(zones) > 0

        # If zone_name provided and exists in zones, use zone-specific context
        if zone_name and has_zones and zone_name in zones:
            return self._create_zone_context(zone_name)
        else:
            return self._create_single_zone_context()

    def _create_single_zone_context(self) -> MappingContext:
        """Create context for single-zone profile."""
        profile = self._profile or {}

        # Get primary language
        language = self.get_primary_language() or "unknown"

        # Get patterns
        patterns = profile.get("patterns", {})

        # Get structure
        structure = profile.get("structure", {})

        # Get conventions
        conventions = profile.get("conventions")

        # Get frameworks from languages or patterns
        frameworks = self._extract_frameworks(profile)

        return MappingContext(
            zone_name=None,
            language=language,
            patterns=patterns,
            structure=structure,
            conventions=conventions,
            frameworks=frameworks,
        )

    def _create_zone_context(self, zone_name: str) -> MappingContext:
        """Create context for a specific zone in multi-zone profile."""
        profile = self._profile or {}
        zones = profile.get("zones", {})

        if zone_name not in zones:
            raise ValueError(f"Zone not found: {zone_name}")

        zone_data = zones[zone_name]

        # Extract zone-specific data
        language = zone_data.get("language", "unknown")
        patterns = zone_data.get("patterns", {})
        structure = zone_data.get("structure", {})
        conventions = zone_data.get("conventions")
        zone_paths = [zone_data.get("path")] if zone_data.get("path") else None

        # Get frameworks
        frameworks = zone_data.get("frameworks", [])
        if not frameworks:
            frameworks = self._extract_frameworks_from_patterns(patterns)

        return MappingContext(
            zone_name=zone_name,
            language=language,
            patterns=patterns,
            structure=structure,
            conventions=conventions,
            frameworks=frameworks,
            zone_paths=zone_paths,
        )

    def _extract_frameworks(self, profile: Dict[str, Any]) -> List[str]:
        """Extract framework list from profile."""
        frameworks = []

        # From languages
        for lang in profile.get("languages", []):
            if isinstance(lang, dict):
                frameworks.extend(lang.get("frameworks", []))

        # From patterns (framework_* patterns)
        patterns = profile.get("patterns", {})
        frameworks.extend(self._extract_frameworks_from_patterns(patterns))

        return list(set(frameworks))

    def _extract_frameworks_from_patterns(self, patterns: Dict[str, Any]) -> List[str]:
        """Extract framework names from pattern keys."""
        frameworks = []
        for key in patterns.keys():
            if key.startswith("framework_"):
                fw_name = key.replace("framework_", "")
                frameworks.append(fw_name)
        return frameworks

    def get_all_contexts(self) -> List[MappingContext]:
        """
        Get mapping contexts for all zones.

        Returns:
            List of MappingContext objects
        """
        zones = self.get_zones()
        contexts = []

        for zone_name in zones:
            try:
                if zone_name == "default":
                    context = self._create_single_zone_context()
                else:
                    context = self._create_zone_context(zone_name)
                contexts.append(context)
            except Exception:
                # Skip zones that fail to load
                continue

        return contexts


def load_profile(root_path: Path, profile_path: Optional[Path] = None) -> Tuple[ProfileLoader, Dict[str, Any]]:
    """
    Convenience function to load a profile.

    Args:
        root_path: Repository root path
        profile_path: Optional custom profile path

    Returns:
        Tuple of (ProfileLoader, profile dict)
    """
    loader = ProfileLoader(root_path)
    profile = loader.load(profile_path)
    return loader, profile
