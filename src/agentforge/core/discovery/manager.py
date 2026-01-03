# @spec_file: .agentforge/specs/core-discovery-v1.yaml
# @spec_id: core-discovery-v1
# @component_id: core-discovery-manager
# @test_path: tests/unit/tools/conformance/test_manager.py

"""
Discovery Manager
=================

Orchestrates the brownfield discovery process through multiple phases.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .analyzers.interactions import InteractionDetector
from .analyzers.patterns import PatternAnalysisResult, PatternAnalyzer
from .analyzers.structure import StructureAnalysisResult, StructureAnalyzer
from .analyzers.test_linkage import TestLinkageAnalyzer
from .domain import (
    CodebaseProfile,
    DependencyInfo,
    Detection,
    DetectionSource,
    DiscoveryPhase,
    Interaction,
    LanguageInfo,
    CoverageGapAnalysis,
    Zone,
    ZoneProfile,
)
from .generators.as_built_spec import AsBuiltSpecGenerator
from .generators.lineage_embedder import LineageEmbedder
from .generators.profile import ProfileGenerator
from .providers.base import LanguageProvider
from .providers.dotnet_provider import DotNetProvider
from .providers.python_provider import PythonProvider
from .zones.detector import ZoneDetector
from .zones.merger import ZoneMerger

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


# Helper functions to reduce complexity in manager methods
def _get_frameworks_list(project_info: dict[str, Any]) -> list[str]:
    """Extract and normalize frameworks list from project info."""
    frameworks = project_info.get("frameworks", [])
    primary_framework = project_info.get("framework")
    if primary_framework:
        # Ensure primary framework is first, avoid duplicates
        return [primary_framework] + [f for f in frameworks if f != primary_framework]
    return frameworks


def _collect_unique_dependencies(zone_profiles: dict) -> list[DependencyInfo]:
    """Collect unique dependencies across all zone profiles."""
    all_deps: list[DependencyInfo] = []
    seen: set[str] = set()
    for profile in zone_profiles.values():
        for dep in profile.dependencies:
            if dep.name not in seen:
                all_deps.append(dep)
                seen.add(dep.name)
    return all_deps



class DiscoveryPhaseStatus(Enum):
    """Status of a discovery phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result of a single discovery phase."""
    phase: DiscoveryPhase
    status: DiscoveryPhaseStatus
    duration_seconds: float
    result: Any = None
    error: str | None = None


@dataclass
class DiscoveryResult:
    """Complete result of discovery process."""
    success: bool
    profile: CodebaseProfile | None
    profile_path: Path | None
    phases: dict[DiscoveryPhase, PhaseResult]
    total_duration_seconds: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    spec_paths: list[Path] = field(default_factory=list)  # As-built spec files
    lineage_embedded: int = 0  # Number of files with lineage embedded


class DiscoveryManager:
    """
    Orchestrates the brownfield discovery process.

    Runs discovery in phases:
    1. Language Detection - What languages/frameworks?
    2. Structure Analysis - How is it organized?
    3. Pattern Extraction - What patterns are used?
    4. Architecture Mapping - What are the dependencies?
    5. Convention Inference - What naming conventions? (future)
    6. Test Gap Analysis - What's tested? (future)
    """

    # Available language providers
    PROVIDERS = {
        "python": PythonProvider,
        "csharp": DotNetProvider,
    }

    def __init__(
        self,
        root_path: Path,
        verbose: bool = False,
        progress_callback: Callable[[str, float], None] | None = None,
    ):
        """
        Initialize discovery manager.

        Args:
            root_path: Root directory to analyze
            verbose: Enable verbose output
            progress_callback: Optional callback for progress updates (message, percentage)
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.progress_callback = progress_callback

        self._providers: dict[str, LanguageProvider] = {}
        self._phase_results: dict[DiscoveryPhase, PhaseResult] = {}
        self._languages: list[LanguageInfo] = []
        self._dependencies: list[DependencyInfo] = []
        self._structure_result: StructureAnalysisResult | None = None
        self._pattern_result: PatternAnalysisResult | None = None
        self._test_analysis: CoverageGapAnalysis | None = None  # type: ignore

    def _default_phases(self) -> list[DiscoveryPhase]:
        """Return default discovery phases."""
        return [
            DiscoveryPhase.LANGUAGE,
            DiscoveryPhase.STRUCTURE,
            DiscoveryPhase.PATTERNS,
            DiscoveryPhase.ARCHITECTURE,
            DiscoveryPhase.TESTS,
        ]

    def _execute_phase(self, phase: DiscoveryPhase, errors: list[str]) -> None:
        """Execute a single phase and collect errors."""
        try:
            result = self._run_phase(phase)
            self._phase_results[phase] = result
            if result.status == DiscoveryPhaseStatus.FAILED:
                errors.append(f"{phase.value}: {result.error}")
        except Exception as e:
            errors.append(f"{phase.value}: {str(e)}")
            self._phase_results[phase] = PhaseResult(
                phase=phase,
                status=DiscoveryPhaseStatus.FAILED,
                duration_seconds=0,
                error=str(e),
            )

    def discover(
        self,
        phases: list[DiscoveryPhase] | None = None,
        save_profile: bool = True,
        generate_specs: bool = False,
        embed_lineage: bool = False,
    ) -> DiscoveryResult:
        """Run discovery process."""
        start_time = time.time()
        phases = phases or self._default_phases()
        errors: list[str] = []
        warnings: list[str] = []

        # Run each phase
        for i, phase in enumerate(phases):
            self._report_progress(f"Running {phase.value}...", (i / len(phases)) * 100)
            self._execute_phase(phase, errors)

        # Generate profile
        profile, profile_path = None, None
        if not errors or self._has_minimum_results():
            try:
                self._report_progress("Generating profile...", 85)
                profile, profile_path = self._generate_profile(save_profile)
            except Exception as e:
                errors.append(f"Profile generation: {str(e)}")

        # Generate as-built specs
        spec_paths: list[Path] = []
        lineage_embedded = 0
        if generate_specs and self._test_analysis:
            try:
                self._report_progress("Generating as-built specs...", 92)
                spec_paths, lineage_embedded = self._generate_as_built_specs(
                    embed_lineage=embed_lineage
                )
            except Exception as e:
                warnings.append(f"As-built spec generation: {str(e)}")

        self._report_progress("Discovery complete", 100)
        return DiscoveryResult(
            success=len(errors) == 0,
            profile=profile,
            profile_path=profile_path,
            phases=self._phase_results,
            total_duration_seconds=time.time() - start_time,
            errors=errors,
            warnings=warnings,
            spec_paths=spec_paths,
            lineage_embedded=lineage_embedded,
        )

    def _run_phase(self, phase: DiscoveryPhase) -> PhaseResult:
        """Run a single discovery phase."""
        start_time = time.time()

        try:
            if phase == DiscoveryPhase.LANGUAGE:
                result = self._detect_languages()
            elif phase == DiscoveryPhase.STRUCTURE:
                result = self._analyze_structure()
            elif phase == DiscoveryPhase.PATTERNS:
                result = self._extract_patterns()
            elif phase == DiscoveryPhase.ARCHITECTURE:
                result = self._map_architecture()
            elif phase == DiscoveryPhase.TESTS:
                result = self._analyze_tests()
            else:
                return PhaseResult(
                    phase=phase,
                    status=DiscoveryPhaseStatus.SKIPPED,
                    duration_seconds=0,
                )

            duration = time.time() - start_time
            return PhaseResult(
                phase=phase,
                status=DiscoveryPhaseStatus.COMPLETED,
                duration_seconds=duration,
                result=result,
            )

        except Exception as e:
            duration = time.time() - start_time
            return PhaseResult(
                phase=phase,
                status=DiscoveryPhaseStatus.FAILED,
                duration_seconds=duration,
                error=str(e),
            )

    def _detect_languages(self) -> list[LanguageInfo]:
        """Phase 1: Detect languages and frameworks."""
        self._languages = []

        for lang_name, provider_class in self.PROVIDERS.items():
            provider = provider_class()

            # Check for project markers
            project_info = provider.detect_project(self.root_path)
            if project_info:
                self._providers[lang_name] = provider

                # Count files and lines
                source_files = provider.get_source_files(self.root_path)
                file_count = len(source_files)
                line_count = sum(provider.count_lines(f) for f in source_files)

                # Get dependencies
                deps = provider.get_dependencies(self.root_path)
                for dep in deps:
                    self._dependencies.append(DependencyInfo(
                        name=dep.name,
                        version=dep.version,
                        source=dep.source,
                        is_dev=dep.is_dev,
                    ))

                # Create language info
                frameworks = _get_frameworks_list(project_info)

                lang_info = LanguageInfo(
                    name=lang_name,
                    version=project_info.get("version"),
                    detection=Detection(
                        value=lang_name,
                        confidence=0.9 if project_info else 0.5,
                        source=DetectionSource.EXPLICIT,
                        signals=[f"project_file:{project_info.get('project_file', 'unknown')}"],
                    ),
                    file_count=file_count,
                    line_count=line_count,
                    frameworks=frameworks,
                    primary=True,  # First detected is primary
                )
                self._languages.append(lang_info)

                if self.verbose:
                    print(f"  Detected {lang_name}: {file_count} files, {line_count} lines")
                    if frameworks:
                        print(f"    Frameworks: {', '.join(frameworks)}")

        # Mark first language as primary
        if self._languages:
            # Sort by file count, most files = primary
            self._languages.sort(key=lambda lang: lang.file_count, reverse=True)
            for i, lang in enumerate(self._languages):
                lang.primary = (i == 0)

        return self._languages

    def _analyze_structure(self) -> StructureAnalysisResult:
        """Phase 2: Analyze project structure."""
        if not self._providers:
            raise ValueError("No language providers available. Run language detection first.")

        # Use primary language provider
        primary_lang = next((lang for lang in self._languages if lang.primary), None)
        if not primary_lang:
            primary_lang = self._languages[0] if self._languages else None

        if not primary_lang:
            raise ValueError("No languages detected")

        provider = self._providers.get(primary_lang.name)
        if not provider:
            raise ValueError(f"No provider for {primary_lang.name}")

        analyzer = StructureAnalyzer(provider)
        self._structure_result = analyzer.analyze(self.root_path)

        if self.verbose:
            print(f"  Architecture style: {self._structure_result.architecture_style}")
            print(f"  Confidence: {self._structure_result.confidence:.2f}")
            print(f"  Layers detected: {list(self._structure_result.layers.keys())}")

        return self._structure_result

    def _extract_patterns(self) -> PatternAnalysisResult:
        """Phase 3: Extract code patterns."""
        if not self._providers:
            raise ValueError("No language providers available")

        # Use primary language provider
        primary_lang = next((lang for lang in self._languages if lang.primary), None)
        if not primary_lang:
            raise ValueError("No primary language detected")

        provider = self._providers.get(primary_lang.name)
        if not provider:
            raise ValueError(f"No provider for {primary_lang.name}")

        analyzer = PatternAnalyzer(provider)
        self._pattern_result = analyzer.analyze(self.root_path)

        if self.verbose:
            print(f"  Patterns detected: {len(self._pattern_result.patterns)}")
            for name, pattern in self._pattern_result.patterns.items():
                print(f"    - {name}: {pattern.detection.confidence:.2f} confidence")
            print(f"  Frameworks detected: {list(self._pattern_result.frameworks.keys())}")

        return self._pattern_result

    def _map_architecture(self) -> dict[str, Any]:
        """Phase 4: Map architectural dependencies."""
        # This phase uses structure analysis results to map layer dependencies
        if not self._structure_result:
            raise ValueError("Structure analysis not completed")

        # For now, return basic architecture info
        # Full implementation would analyze imports to map dependencies
        architecture = {
            "style": self._structure_result.architecture_style,
            "layers": list(self._structure_result.layers.keys()),
            "dependencies_analyzed": False,  # Not implemented yet
        }

        if self.verbose:
            print(f"  Architecture mapped: {architecture['style']}")

        return architecture

    def _analyze_tests(self) -> CoverageGapAnalysis:
        """Phase 5: Analyze tests and build source-to-test linkage."""
        # Get test directories from structure analysis
        test_dirs = ["tests", "test"]
        source_dirs = ["src", "tools", "lib"]

        if self._structure_result:
            # Use detected test directories
            if self._structure_result.test_directories:
                test_dirs = [
                    str(Path(d).relative_to(self.root_path))
                    if Path(d).is_absolute() else d
                    for d in self._structure_result.test_directories
                ]

        analyzer = TestLinkageAnalyzer(
            root_path=self.root_path,
            test_directories=test_dirs,
            source_directories=source_dirs,
        )

        self._test_analysis = analyzer.analyze()

        if self.verbose:
            print(f"  Test linkage: {len(self._test_analysis.linkages)} source files mapped")
            print(f"  Test files: {self._test_analysis.inventory.total_test_files}")
            print(f"  Coverage estimate: {self._test_analysis.estimated_coverage:.0%}")

        return self._test_analysis

    def _has_minimum_results(self) -> bool:
        """Check if we have minimum results to generate a profile."""
        return (
            len(self._languages) > 0 or
            self._structure_result is not None or
            self._pattern_result is not None
        )

    def _generate_profile(self, save_profile: bool) -> tuple[CodebaseProfile, Path | None]:
        """Generate and optionally save the profile."""
        generator = ProfileGenerator(self.root_path)

        phases_completed = [
            phase.value for phase, result in self._phase_results.items()
            if result.status == DiscoveryPhaseStatus.COMPLETED
        ]

        total_duration = sum(
            result.duration_seconds for result in self._phase_results.values()
        )

        # Ensure we have valid results (use empty defaults if needed)
        structure_result = self._structure_result
        if structure_result is None:
            # Create minimal structure result
            from .analyzers.structure import StructureAnalysisResult
            structure_result = StructureAnalysisResult(
                architecture_style="unknown",
                confidence=0.0,
                layers={},
                directories=[],
                entry_points=[],
                test_directories=[],
            )

        pattern_result = self._pattern_result
        if pattern_result is None:
            # Create minimal pattern result
            from .analyzers.patterns import PatternAnalysisResult
            pattern_result = PatternAnalysisResult(
                patterns={},
                frameworks={},
                matches=[],
                total_files_analyzed=0,
            )

        profile = generator.generate(
            languages=self._languages,
            structure_result=structure_result,
            pattern_result=pattern_result,
            dependencies=self._dependencies,
            phases_completed=phases_completed,
            duration_seconds=total_duration,
            test_analysis=self._test_analysis,
        )

        profile_path = None
        if save_profile:
            profile_path = generator.save()
            if self.verbose:
                print(f"  Profile saved to: {profile_path}")

        return profile, profile_path

    def _generate_as_built_specs(
        self,
        embed_lineage: bool = False,
    ) -> tuple[list[Path], int]:
        """
        Generate as-built specs from test analysis results.

        This implements the Artifact Parity Principle - brownfield code
        gets the same spec structure as greenfield code.

        Args:
            embed_lineage: Whether to embed lineage metadata in source files

        Returns:
            Tuple of (spec_paths, files_with_lineage_embedded)
        """
        if not self._test_analysis or not self._test_analysis.linkages:
            return [], 0

        generator = AsBuiltSpecGenerator(self.root_path)
        specs = generator.generate_from_test_analysis(
            self._test_analysis,
            zone_name="main",
        )

        if not specs:
            return [], 0

        # Save specs to disk
        spec_paths = generator.save_specs(specs)

        if self.verbose:
            print(f"  Generated {len(specs)} as-built spec(s)")
            for path in spec_paths:
                print(f"    - {path.name}")

        # Optionally embed lineage metadata
        files_embedded = 0
        if embed_lineage:
            lineage_updates = generator.generate_lineage_updates(specs)

            embedder = LineageEmbedder(self.root_path)
            results = embedder.embed_all(lineage_updates)

            files_embedded = sum(1 for r in results if r.success and r.action in ("added", "updated"))

            if self.verbose:
                summary = embedder.summary()
                print(f"  Lineage embedded: {summary['added']} added, {summary['updated']} updated")

        return spec_paths, files_embedded

    def _report_progress(self, message: str, percentage: float) -> None:
        """Report progress to callback if available."""
        if self.progress_callback:
            self.progress_callback(message, percentage)
        elif self.verbose:
            print(f"[{percentage:.0f}%] {message}")


@dataclass
class MultiZoneDiscoveryResult:
    """Result of multi-zone discovery process."""
    success: bool
    zones: list[Zone]
    zone_profiles: dict[str, ZoneProfile]
    interactions: list[Interaction]
    profile_path: Path | None
    total_duration_seconds: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


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
                # Fallback to single-zone discovery
                self._report_progress("No zones detected, using single-zone mode", 10)
                return self._fallback_single_zone(save_profile)

            if self.verbose:
                print(f"  Detected {len(self._zones)} zone(s)")
                for zone in self._zones:
                    print(f"    - {zone.name}: {zone.language} at {zone.path}")

            # Filter to specific zone if requested
            zones_to_analyze = self._zones
            if zone_name:
                zones_to_analyze = [z for z in self._zones if z.name == zone_name]
                if not zones_to_analyze:
                    errors.append(f"Zone '{zone_name}' not found")
                    return MultiZoneDiscoveryResult(
                        success=False,
                        zones=self._zones,
                        zone_profiles={},
                        interactions=[],
                        profile_path=None,
                        total_duration_seconds=time.time() - start_time,
                        errors=errors,
                    )

            # Phase 2: Analyze each zone
            for i, zone in enumerate(zones_to_analyze):
                progress = 10 + (i / len(zones_to_analyze)) * 70
                self._report_progress(f"Analyzing zone: {zone.name}...", progress)

                try:
                    profile = self._analyze_zone(zone)
                    self._zone_profiles[zone.name] = profile
                except Exception as e:
                    errors.append(f"Zone {zone.name}: {str(e)}")
                    warnings.append(f"Zone {zone.name} analysis failed, skipping")

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

            total_duration = time.time() - start_time
            self._report_progress("Discovery complete", 100)

            return MultiZoneDiscoveryResult(
                success=len(errors) == 0,
                zones=self._zones,
                zone_profiles=self._zone_profiles,
                interactions=self._interactions,
                profile_path=profile_path,
                total_duration_seconds=total_duration,
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

    def _analyze_zone(self, zone: Zone) -> ZoneProfile:
        """Analyze a single zone."""
        # Get provider for zone's language
        provider_class = self.PROVIDERS.get(zone.language)
        if not provider_class:
            raise ValueError(f"No provider for language: {zone.language}")

        provider = provider_class()
        zone_path = zone.path if zone.path.is_absolute() else (self.root_path / zone.path)

        # Count files and lines
        source_files = provider.get_source_files(zone_path)
        file_count = len(source_files)
        line_count = sum(provider.count_lines(f) for f in source_files)

        # Get dependencies
        deps = provider.get_dependencies(zone_path)
        dependencies = [
            DependencyInfo(
                name=dep.name,
                version=dep.version,
                source=dep.source,
                is_dev=dep.is_dev,
            )
            for dep in deps
        ]

        # Get project info for frameworks
        project_info = provider.detect_project(zone_path) or {}
        frameworks = _get_frameworks_list(project_info)

        # Create language info
        lang_info = LanguageInfo(
            name=zone.language,
            version=project_info.get("version"),
            detection=Detection(
                value=zone.language,
                confidence=0.9,
                source=DetectionSource.EXPLICIT,
            ),
            file_count=file_count,
            line_count=line_count,
            frameworks=frameworks,
            primary=True,
        )

        # Analyze structure
        structure_analyzer = StructureAnalyzer(provider)
        structure_result = structure_analyzer.analyze(zone_path)

        # Analyze patterns
        pattern_analyzer = PatternAnalyzer(provider)
        pattern_result = pattern_analyzer.analyze(zone_path)

        # Build structure dict
        structure = {
            "style": structure_result.architecture_style,
            "confidence": structure_result.confidence,
            "source_root": str(structure_result.source_root) if structure_result.source_root else None,
            "layers": {
                name: {
                    "paths": info.paths,
                    "file_count": info.file_count,
                    "line_count": info.line_count,
                    "confidence": info.detection.confidence,
                    "signals": info.detection.signals,
                }
                for name, info in structure_result.layers.items()
            },
            "entry_points": [str(ep) for ep in structure_result.entry_points],
            "test_directories": [str(td) for td in structure_result.test_directories],
        }

        # Build patterns dict
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

        # Add frameworks to patterns (frameworks are Detection objects, not PatternDetection)
        for name, fw in pattern_result.frameworks.items():
            patterns[f"framework_{name}"] = {
                "description": f"{name} framework detected",
                "confidence": fw.confidence,
                "source": fw.source.value,
                "signals": fw.signals,
                "metadata": fw.metadata,
            }

        return ZoneProfile(
            zone=zone,
            languages=[lang_info],
            structure=structure,
            patterns=patterns,
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

    def _generate_multi_zone_profile(self) -> Path:
        """Generate and save multi-zone profile."""
        from datetime import datetime

        # Aggregate languages across zones
        all_languages: list[LanguageInfo] = []
        for profile in self._zone_profiles.values():
            all_languages.extend(profile.languages)

        # Aggregate dependencies using helper
        all_dependencies = _collect_unique_dependencies(self._zone_profiles)

        # Calculate totals
        total_files = sum(p.file_count for p in self._zone_profiles.values())
        sum(p.line_count for p in self._zone_profiles.values())

        # Build profile dict
        profile_data = {
            "schema_version": "1.1",
            "generated_at": datetime.now().isoformat(),
            "discovery_metadata": {
                "discovery_version": "1.0",
                "run_date": datetime.now().isoformat(),
                "root_path": str(self.root_path),
                "zones_discovered": len(self._zones),
                "detection_mode": self._get_detection_mode(),
                "total_files_analyzed": total_files,
            },
            "languages": [
                {
                    "name": lang.name,
                    "percentage": round((lang.file_count / total_files * 100) if total_files else 0, 1),
                    "zones": [z.name for z in self._zones if z.language == lang.name],
                }
                for lang in all_languages
            ],
            "zones": {
                name: profile.to_dict()
                for name, profile in self._zone_profiles.items()
            },
        }

        # Add interactions
        if self._interactions:
            profile_data["interactions"] = [i.to_dict() for i in self._interactions]

        # Add dependencies
        if all_dependencies:
            profile_data["dependencies"] = [
                {
                    "name": d.name,
                    "version": d.version,
                    "source": d.source,
                    "is_dev": d.is_dev,
                    "category": d.category,
                }
                for d in all_dependencies
            ]

        # Save to file
        output_dir = self.root_path / ".agentforge"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "codebase_profile.yaml"

        if yaml:
            output_path.write_text(yaml.dump(profile_data, default_flow_style=False, sort_keys=False))
        else:
            # Fallback: write as simple YAML-like format
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
