"""
Discovery Manager
=================

Orchestrates the brownfield discovery process through multiple phases.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from enum import Enum

from .domain import (
    CodebaseProfile, DiscoveryPhase, Detection, DetectionSource,
    LanguageInfo, DependencyInfo, OnboardingProgress, OnboardingStatus,
)
from .providers.base import LanguageProvider
from .providers.python_provider import PythonProvider
from .analyzers.structure import StructureAnalyzer, StructureAnalysisResult
from .analyzers.patterns import PatternAnalyzer, PatternAnalysisResult
from .generators.profile import ProfileGenerator


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
    error: Optional[str] = None


@dataclass
class DiscoveryResult:
    """Complete result of discovery process."""
    success: bool
    profile: Optional[CodebaseProfile]
    profile_path: Optional[Path]
    phases: Dict[DiscoveryPhase, PhaseResult]
    total_duration_seconds: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


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
    }

    def __init__(
        self,
        root_path: Path,
        verbose: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
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

        self._providers: Dict[str, LanguageProvider] = {}
        self._phase_results: Dict[DiscoveryPhase, PhaseResult] = {}
        self._languages: List[LanguageInfo] = []
        self._dependencies: List[DependencyInfo] = []
        self._structure_result: Optional[StructureAnalysisResult] = None
        self._pattern_result: Optional[PatternAnalysisResult] = None

    def discover(
        self,
        phases: Optional[List[DiscoveryPhase]] = None,
        save_profile: bool = True,
    ) -> DiscoveryResult:
        """
        Run discovery process.

        Args:
            phases: Specific phases to run, or None for all phases
            save_profile: Whether to save profile to disk

        Returns:
            DiscoveryResult with profile and phase results
        """
        start_time = time.time()

        # Default to all implemented phases
        if phases is None:
            phases = [
                DiscoveryPhase.LANGUAGE,
                DiscoveryPhase.STRUCTURE,
                DiscoveryPhase.PATTERNS,
                DiscoveryPhase.ARCHITECTURE,
            ]

        errors = []
        warnings = []

        # Run each phase
        for i, phase in enumerate(phases):
            progress = (i / len(phases)) * 100
            self._report_progress(f"Running {phase.value}...", progress)

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

        # Generate profile
        profile = None
        profile_path = None

        if not errors or self._has_minimum_results():
            try:
                self._report_progress("Generating profile...", 90)
                profile, profile_path = self._generate_profile(save_profile)
            except Exception as e:
                errors.append(f"Profile generation: {str(e)}")

        total_duration = time.time() - start_time
        self._report_progress("Discovery complete", 100)

        return DiscoveryResult(
            success=len(errors) == 0,
            profile=profile,
            profile_path=profile_path,
            phases=self._phase_results,
            total_duration_seconds=total_duration,
            errors=errors,
            warnings=warnings,
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

    def _detect_languages(self) -> List[LanguageInfo]:
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
                frameworks = project_info.get("frameworks", [])
                if project_info.get("framework"):
                    frameworks = [project_info["framework"]] + [f for f in frameworks if f != project_info["framework"]]

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
            self._languages.sort(key=lambda l: l.file_count, reverse=True)
            for i, lang in enumerate(self._languages):
                lang.primary = (i == 0)

        return self._languages

    def _analyze_structure(self) -> StructureAnalysisResult:
        """Phase 2: Analyze project structure."""
        if not self._providers:
            raise ValueError("No language providers available. Run language detection first.")

        # Use primary language provider
        primary_lang = next((l for l in self._languages if l.primary), None)
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
        primary_lang = next((l for l in self._languages if l.primary), None)
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

    def _map_architecture(self) -> Dict[str, Any]:
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

    def _has_minimum_results(self) -> bool:
        """Check if we have minimum results to generate a profile."""
        return (
            len(self._languages) > 0 or
            self._structure_result is not None or
            self._pattern_result is not None
        )

    def _generate_profile(self, save_profile: bool) -> tuple[CodebaseProfile, Optional[Path]]:
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
        )

        profile_path = None
        if save_profile:
            profile_path = generator.save()
            if self.verbose:
                print(f"  Profile saved to: {profile_path}")

        return profile, profile_path

    def _report_progress(self, message: str, percentage: float) -> None:
        """Report progress to callback if available."""
        if self.progress_callback:
            self.progress_callback(message, percentage)
        elif self.verbose:
            print(f"[{percentage:.0f}%] {message}")
