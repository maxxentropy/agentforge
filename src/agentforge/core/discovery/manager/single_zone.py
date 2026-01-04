# @spec_file: .agentforge/specs/core-discovery-v1.yaml
# @spec_id: core-discovery-v1
# @component_id: core-discovery-manager
# @test_path: tests/unit/tools/conformance/test_manager.py

"""
Single-Zone Discovery Manager
=============================

Orchestrates the brownfield discovery process through multiple phases.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..analyzers.patterns import PatternAnalysisResult, PatternAnalyzer
from ..analyzers.structure import StructureAnalysisResult, StructureAnalyzer
from ..analyzers.test_linkage import TestLinkageAnalyzer
from ..domain import (
    CodebaseProfile,
    DependencyInfo,
    Detection,
    DetectionSource,
    DiscoveryPhase,
    LanguageInfo,
    CoverageGapAnalysis,
)
from ..generators.as_built_spec import AsBuiltSpecGenerator
from ..generators.lineage_embedder import LineageEmbedder
from ..generators.profile import ProfileGenerator
from ..providers.base import LanguageProvider
from ..providers.dotnet_provider import DotNetProvider
from ..providers.python_provider import PythonProvider
from .helpers import get_frameworks_list
from .types import DiscoveryPhaseStatus, DiscoveryResult, PhaseResult


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
                frameworks = get_frameworks_list(project_info)

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
            from ..analyzers.structure import StructureAnalysisResult
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
            from ..analyzers.patterns import PatternAnalysisResult
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

    def _embed_lineage_metadata(self, generator, specs) -> int:
        """Embed lineage metadata in source files and return count."""
        lineage_updates = generator.generate_lineage_updates(specs)
        embedder = LineageEmbedder(self.root_path)
        results = embedder.embed_all(lineage_updates)
        files_embedded = sum(1 for r in results if r.success and r.action in ("added", "updated"))
        if self.verbose:
            summary = embedder.summary()
            print(f"  Lineage embedded: {summary['added']} added, {summary['updated']} updated")
        return files_embedded

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
        specs = generator.generate_from_test_analysis(self._test_analysis, zone_name="main")

        if not specs:
            return [], 0

        spec_paths = generator.save_specs(specs)
        if self.verbose:
            print(f"  Generated {len(specs)} as-built spec(s)")
            for path in spec_paths:
                print(f"    - {path.name}")

        files_embedded = self._embed_lineage_metadata(generator, specs) if embed_lineage else 0
        return spec_paths, files_embedded

    def _report_progress(self, message: str, percentage: float) -> None:
        """Report progress to callback if available."""
        if self.progress_callback:
            self.progress_callback(message, percentage)
        elif self.verbose:
            print(f"[{percentage:.0f}%] {message}")
