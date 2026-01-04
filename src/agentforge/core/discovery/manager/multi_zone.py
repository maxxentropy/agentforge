"""
Multi-Zone Discovery Manager
============================

Orchestrates multi-zone brownfield discovery.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..analyzers.interactions import InteractionDetector
from ..analyzers.patterns import PatternAnalyzer
from ..analyzers.structure import StructureAnalyzer
from ..domain import (
    DependencyInfo,
    Detection,
    DetectionSource,
    Interaction,
    LanguageInfo,
    Zone,
    ZoneProfile,
)
from ..providers.dotnet_provider import DotNetProvider
from ..providers.python_provider import PythonProvider
from ..zones.detector import ZoneDetector
from ..zones.merger import ZoneMerger
from .helpers import collect_unique_dependencies, get_frameworks_list
from .single_zone import DiscoveryManager
from .types import MultiZoneDiscoveryResult

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class MultiZoneDiscoveryManager:
    """
    Orchestrates multi-zone brownfield discovery.

    Detects zones, analyzes each zone independently, and
    detects cross-zone interactions.

    Example:
        >>> manager = MultiZoneDiscoveryManager(Path("/my/repo"))
        >>> result = manager.discover()
        >>> for zone_name, profile in result.zone_profiles.items():
        ...     print(f"{zone_name}: {profile.zone.language}")
    """

    PROVIDERS = {
        "python": PythonProvider,
        "csharp": DotNetProvider,
    }

    def __init__(
        self,
        root_path: Path,
        config: dict[str, Any] | None = None,
        verbose: bool = False,
        progress_callback: Callable[[str, float], None] | None = None,
    ):
        """
        Initialize multi-zone discovery manager.

        Args:
            root_path: Root directory to analyze
            config: Optional repo.yaml configuration dict
            verbose: Enable verbose output
            progress_callback: Optional callback for progress updates
        """
        self.root_path = Path(root_path).resolve()
        self.config = config or self._load_config()
        self.verbose = verbose
        self.progress_callback = progress_callback

        self._zones: list[Zone] = []
        self._zone_profiles: dict[str, ZoneProfile] = {}
        self._interactions: list[Interaction] = []

    def _load_config(self) -> dict[str, Any]:
        """Load repo.yaml configuration if it exists."""
        config_path = self.root_path / ".agentforge" / "repo.yaml"
        if config_path.exists() and yaml:
            try:
                return yaml.safe_load(config_path.read_text())
            except Exception:
                pass
        return {}

    def _filter_zones(self, zone_name: str | None) -> tuple[list, str | None]:
        """Filter zones by name, return (zones_to_analyze, error_message)."""
        if not zone_name:
            return self._zones, None
        filtered = [z for z in self._zones if z.name == zone_name]
        if not filtered:
            return [], f"Zone '{zone_name}' not found"
        return filtered, None

    def _analyze_zones(
        self, zones: list, errors: list, warnings: list
    ) -> None:
        """Analyze each zone and populate profiles."""
        for i, zone in enumerate(zones):
            progress = 10 + (i / len(zones)) * 70
            self._report_progress(f"Analyzing zone: {zone.name}...", progress)
            try:
                self._zone_profiles[zone.name] = self._analyze_zone(zone)
            except Exception as e:
                errors.append(f"Zone {zone.name}: {str(e)}")
                warnings.append(f"Zone {zone.name} analysis failed, skipping")

    def _create_error_result(
        self, errors: list, start_time: float
    ) -> MultiZoneDiscoveryResult:
        """Create error result for discovery."""
        return MultiZoneDiscoveryResult(
            success=False,
            zones=self._zones,
            zone_profiles={},
            interactions=[],
            profile_path=None,
            total_duration_seconds=time.time() - start_time,
            errors=errors,
        )

    def discover(
        self,
        zone_name: str | None = None,
        save_profile: bool = True,
    ) -> MultiZoneDiscoveryResult:
        """
        Run multi-zone discovery.

        Args:
            zone_name: Optional specific zone to analyze (None = all zones)
            save_profile: Whether to save profile to disk

        Returns:
            MultiZoneDiscoveryResult with zones, profiles, and interactions
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Phase 1: Detect zones
            self._report_progress("Detecting zones...", 5)
            self._detect_zones()

            if not self._zones:
                self._report_progress("No zones detected, using single-zone mode", 10)
                return self._fallback_single_zone(save_profile)

            if self.verbose:
                print(f"  Detected {len(self._zones)} zone(s)")
                for zone in self._zones:
                    print(f"    - {zone.name}: {zone.language} at {zone.path}")

            # Filter to specific zone if requested
            zones_to_analyze, filter_error = self._filter_zones(zone_name)
            if filter_error:
                errors.append(filter_error)
                return self._create_error_result(errors, start_time)

            # Phase 2: Analyze each zone
            self._analyze_zones(zones_to_analyze, errors, warnings)

            # Phase 3: Detect interactions
            self._report_progress("Detecting cross-zone interactions...", 85)
            try:
                self._detect_interactions()
            except Exception as e:
                warnings.append(f"Interaction detection failed: {str(e)}")

            # Phase 4: Generate multi-zone profile
            self._report_progress("Generating profile...", 95)
            profile_path = None
            if save_profile and self._zone_profiles:
                profile_path = self._generate_multi_zone_profile()

            self._report_progress("Discovery complete", 100)

            return MultiZoneDiscoveryResult(
                success=len(errors) == 0,
                zones=self._zones,
                zone_profiles=self._zone_profiles,
                interactions=self._interactions,
                profile_path=profile_path,
                total_duration_seconds=time.time() - start_time,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            return MultiZoneDiscoveryResult(
                success=False,
                zones=self._zones,
                zone_profiles=self._zone_profiles,
                interactions=[],
                profile_path=None,
                total_duration_seconds=time.time() - start_time,
                errors=[str(e)],
            )

    def list_zones(self) -> list[Zone]:
        """
        Detect and return zones without full analysis.

        Useful for CLI --list-zones flag.
        """
        self._detect_zones()
        return self._zones

    def _detect_zones(self) -> None:
        """Detect and merge zones."""
        # Auto-detect zones
        detector = ZoneDetector(self.root_path)
        auto_zones = detector.detect_zones()

        # Merge with config
        merger = ZoneMerger(self.root_path, self.config)
        self._zones = merger.merge_zones(auto_zones)

    def _build_structure_dict(self, result) -> dict:
        """Build structure dictionary from analysis result."""
        return {
            "style": result.architecture_style,
            "confidence": result.confidence,
            "source_root": str(result.source_root) if result.source_root else None,
            "layers": {
                name: {
                    "paths": info.paths,
                    "file_count": info.file_count,
                    "line_count": info.line_count,
                    "confidence": info.detection.confidence,
                    "signals": info.detection.signals,
                }
                for name, info in result.layers.items()
            },
            "entry_points": [str(ep) for ep in result.entry_points],
            "test_directories": [str(td) for td in result.test_directories],
        }

    def _build_patterns_dict(self, pattern_result) -> dict:
        """Build patterns dictionary from analysis result."""
        patterns = {
            name: {
                "description": pattern.description,
                "confidence": pattern.detection.confidence,
                "source": pattern.detection.source.value,
                "file_count": pattern.file_count,
                "locations": pattern.locations[:5],
                "signals": pattern.detection.signals,
            }
            for name, pattern in pattern_result.patterns.items()
        }
        for name, fw in pattern_result.frameworks.items():
            patterns[f"framework_{name}"] = {
                "description": f"{name} framework detected",
                "confidence": fw.confidence,
                "source": fw.source.value,
                "signals": fw.signals,
                "metadata": fw.metadata,
            }
        return patterns

    def _analyze_zone(self, zone: Zone) -> ZoneProfile:
        """Analyze a single zone."""
        provider_class = self.PROVIDERS.get(zone.language)
        if not provider_class:
            raise ValueError(f"No provider for language: {zone.language}")

        provider = provider_class()
        zone_path = zone.path if zone.path.is_absolute() else (self.root_path / zone.path)

        source_files = provider.get_source_files(zone_path)
        file_count = len(source_files)
        line_count = sum(provider.count_lines(f) for f in source_files)

        deps = provider.get_dependencies(zone_path)
        dependencies = [
            DependencyInfo(name=dep.name, version=dep.version, source=dep.source, is_dev=dep.is_dev)
            for dep in deps
        ]

        project_info = provider.detect_project(zone_path) or {}
        frameworks = get_frameworks_list(project_info)

        lang_info = LanguageInfo(
            name=zone.language,
            version=project_info.get("version"),
            detection=Detection(value=zone.language, confidence=0.9, source=DetectionSource.EXPLICIT),
            file_count=file_count,
            line_count=line_count,
            frameworks=frameworks,
            primary=True,
        )

        structure_result = StructureAnalyzer(provider).analyze(zone_path)
        pattern_result = PatternAnalyzer(provider).analyze(zone_path)

        return ZoneProfile(
            zone=zone,
            languages=[lang_info],
            structure=self._build_structure_dict(structure_result),
            patterns=self._build_patterns_dict(pattern_result),
            frameworks=list(pattern_result.frameworks.keys()) + frameworks,
            dependencies=dependencies,
            file_count=file_count,
            line_count=line_count,
        )

    def _detect_interactions(self) -> None:
        """Detect cross-zone interactions."""
        if len(self._zones) < 2:
            return  # No cross-zone interactions possible

        detector = InteractionDetector(self.root_path, self._zones)
        self._interactions = detector.detect_all()

        if self.verbose and self._interactions:
            print(f"  Detected {len(self._interactions)} cross-zone interaction(s)")
            for interaction in self._interactions:
                if interaction.from_zone and interaction.to_zone:
                    print(f"    - {interaction.from_zone} -> {interaction.to_zone}: {interaction.interaction_type.value}")
                elif interaction.zones:
                    print(f"    - {', '.join(interaction.zones)}: {interaction.interaction_type.value}")

    def _build_discovery_metadata(self, total_files: int) -> dict:
        """Build discovery metadata section."""
        from datetime import datetime
        return {
            "discovery_version": "1.0",
            "run_date": datetime.now().isoformat(),
            "root_path": str(self.root_path),
            "zones_discovered": len(self._zones),
            "detection_mode": self._get_detection_mode(),
            "total_files_analyzed": total_files,
        }

    def _build_languages_list(self, all_languages: list, total_files: int) -> list:
        """Build languages list for profile."""
        return [
            {
                "name": lang.name,
                "percentage": round((lang.file_count / total_files * 100) if total_files else 0, 1),
                "zones": [z.name for z in self._zones if z.language == lang.name],
            }
            for lang in all_languages
        ]

    def _build_dependencies_list(self, all_dependencies: list) -> list:
        """Build dependencies list for profile."""
        return [
            {
                "name": d.name,
                "version": d.version,
                "source": d.source,
                "is_dev": d.is_dev,
                "category": d.category,
            }
            for d in all_dependencies
        ]

    def _generate_multi_zone_profile(self) -> Path:
        """Generate and save multi-zone profile."""
        from datetime import datetime

        all_languages: list[LanguageInfo] = []
        for profile in self._zone_profiles.values():
            all_languages.extend(profile.languages)

        all_dependencies = collect_unique_dependencies(self._zone_profiles)
        total_files = sum(p.file_count for p in self._zone_profiles.values())

        profile_data = {
            "schema_version": "1.1",
            "generated_at": datetime.now().isoformat(),
            "discovery_metadata": self._build_discovery_metadata(total_files),
            "languages": self._build_languages_list(all_languages, total_files),
            "zones": {name: profile.to_dict() for name, profile in self._zone_profiles.items()},
        }

        if self._interactions:
            profile_data["interactions"] = [i.to_dict() for i in self._interactions]

        if all_dependencies:
            profile_data["dependencies"] = self._build_dependencies_list(all_dependencies)

        output_dir = self.root_path / ".agentforge"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "codebase_profile.yaml"

        if yaml:
            output_path.write_text(yaml.dump(profile_data, default_flow_style=False, sort_keys=False))
        else:
            import json
            output_path.write_text(json.dumps(profile_data, indent=2))

        return output_path

    def _get_detection_mode(self) -> str:
        """Get the overall detection mode used."""
        modes = {z.detection for z in self._zones}
        if len(modes) == 1:
            return list(modes)[0].value
        return "hybrid"

    def _fallback_single_zone(self, save_profile: bool) -> MultiZoneDiscoveryResult:
        """Fall back to single-zone discovery when no zones detected."""
        # Use the original DiscoveryManager for single-zone
        manager = DiscoveryManager(
            root_path=self.root_path,
            verbose=self.verbose,
            progress_callback=self.progress_callback,
        )

        result = manager.discover(save_profile=save_profile)

        # Convert to multi-zone result format
        return MultiZoneDiscoveryResult(
            success=result.success,
            zones=[],  # No explicit zones
            zone_profiles={},
            interactions=[],
            profile_path=result.profile_path,
            total_duration_seconds=result.total_duration_seconds,
            errors=result.errors,
            warnings=result.warnings,
        )

    def _report_progress(self, message: str, percentage: float) -> None:
        """Report progress to callback if available."""
        if self.progress_callback:
            self.progress_callback(message, percentage)
        elif self.verbose:
            print(f"[{percentage:.0f}%] {message}")
