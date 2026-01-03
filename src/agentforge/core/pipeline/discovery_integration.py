# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-discovery-integration
# @test_path: tests/unit/pipeline/test_discovery_integration.py

"""
Brownfield Discovery Integration
================================

Connects brownfield codebase discovery to pipeline validation and execution.

This module bridges:
1. CodebaseProfile (from discovery) → Pipeline Context
2. Discovered patterns → Validation rules
3. Language detection → Contract selection
4. Test coverage → Red/Green phase guidance

The flow:
  Discovery → CodebaseProfile → PipelineContext → Stage Validation

This enables the pipeline to:
- Know what language(s) the codebase uses
- Understand existing patterns and conventions
- Find related tests for implementations
- Apply language-appropriate validations
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentforge.core.discovery.domain import CodebaseProfile, CoverageGapAnalysis


@dataclass
class DiscoveredContext:
    """
    Context derived from brownfield discovery for pipeline use.

    This is the bridge between discovery and pipeline - it extracts
    the information that pipeline stages need to make decisions.
    """

    # Language information
    primary_language: str | None = None
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)

    # Structure information
    source_directories: list[str] = field(default_factory=list)
    test_directories: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)

    # Pattern information
    detected_patterns: dict[str, Any] = field(default_factory=dict)
    naming_conventions: dict[str, str] = field(default_factory=dict)

    # Test coverage information
    test_framework: str | None = None
    estimated_coverage: float = 0.0
    source_to_test_mapping: dict[str, list[str]] = field(default_factory=dict)

    # Dependency information
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)

    def get_test_path_for_source(self, source_path: str) -> str | None:
        """Get the test file path for a given source file."""
        test_paths = self.source_to_test_mapping.get(source_path, [])
        return test_paths[0] if test_paths else None

    def has_test_for_source(self, source_path: str) -> bool:
        """Check if a source file has associated tests."""
        return source_path in self.source_to_test_mapping

    def get_language_for_file(self, file_path: str) -> str | None:
        """Determine the language for a file based on extension."""
        extension_map = {
            ".py": "python",
            ".cs": "csharp",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
        }
        suffix = Path(file_path).suffix.lower()
        return extension_map.get(suffix)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "primary_language": self.primary_language,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "source_directories": self.source_directories,
            "test_directories": self.test_directories,
            "entry_points": self.entry_points,
            "detected_patterns": self.detected_patterns,
            "naming_conventions": self.naming_conventions,
            "test_framework": self.test_framework,
            "estimated_coverage": self.estimated_coverage,
            "source_to_test_mapping": self.source_to_test_mapping,
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
        }


def _extract_languages(profile: "CodebaseProfile", context: DiscoveredContext) -> None:
    """Extract language and framework information from profile."""
    if not profile.languages:
        return
    for lang_info in profile.languages:
        context.languages.append(lang_info.name.lower())
        if lang_info.primary:
            context.primary_language = lang_info.name.lower()
        if lang_info.frameworks:
            context.frameworks.extend(lang_info.frameworks)


def _extract_structure(profile: "CodebaseProfile", context: DiscoveredContext) -> None:
    """Extract source directory structure from profile."""
    if profile.structure:
        context.source_directories = profile.structure.get("source_dirs", [])
        context.test_directories = profile.structure.get("test_dirs", [])
        context.entry_points = profile.structure.get("entry_points", [])
    if profile.patterns:
        context.detected_patterns = profile.patterns
    if hasattr(profile, "conventions") and profile.conventions:
        for conv in profile.conventions:
            context.naming_conventions[conv.name] = conv.pattern


def _extract_test_info(profile: "CodebaseProfile", context: DiscoveredContext) -> None:
    """Extract test framework and coverage information from profile."""
    if not profile.test_analysis:
        return
    inventory = profile.test_analysis.inventory
    if inventory and inventory.frameworks:
        context.test_framework = inventory.frameworks[0]
    context.estimated_coverage = profile.test_analysis.estimated_coverage or 0.0
    if profile.test_analysis.linkages:
        for linkage in profile.test_analysis.linkages:
            context.source_to_test_mapping[linkage.source_path] = linkage.test_paths


def _extract_dependencies(profile: "CodebaseProfile", context: DiscoveredContext) -> None:
    """Extract dependency information from profile."""
    if not profile.dependencies:
        return
    for dep in profile.dependencies:
        target = context.dev_dependencies if dep.is_dev else context.dependencies
        target.append(dep.name)


def extract_context_from_profile(profile: "CodebaseProfile") -> DiscoveredContext:
    """
    Extract pipeline-relevant context from a CodebaseProfile.

    This is the main entry point for brownfield → pipeline integration.

    Args:
        profile: CodebaseProfile from brownfield discovery

    Returns:
        DiscoveredContext with pipeline-relevant information
    """
    context = DiscoveredContext()
    _extract_languages(profile, context)
    _extract_structure(profile, context)
    _extract_test_info(profile, context)
    _extract_dependencies(profile, context)
    return context


def get_contracts_for_language(language: str) -> list[str]:
    """
    Get the appropriate contracts for a language.

    Args:
        language: Primary language (python, csharp, typescript, etc.)

    Returns:
        List of contract names to apply
    """
    # Base contracts that apply to all languages
    base_contracts = [
        "agentforge-lineage",
        "agentforge-specs",
        "agentforge-structure",
    ]

    # Language-specific contracts
    language_contracts = {
        "python": [
            "_architecture-python",
            "_patterns-python",
            "_security-python",
            "_typing-python",
            "_testing-python",
        ],
        "csharp": [
            "_patterns-csharp",
        ],
        "typescript": [
            "_patterns-typescript",
        ],
        "javascript": [
            "_patterns-typescript",  # Share with TypeScript
        ],
    }

    contracts = base_contracts.copy()
    if language in language_contracts:
        contracts.extend(language_contracts[language])

    return contracts


def create_pipeline_context_from_discovery(
    profile: "CodebaseProfile",
    project_path: Path,
) -> dict[str, Any]:
    """
    Create a pipeline context dictionary from discovery results.

    This context is passed to the INTAKE stage and flows through
    the pipeline, informing each stage about the codebase.

    Args:
        profile: CodebaseProfile from brownfield discovery
        project_path: Path to the project root

    Returns:
        Dictionary suitable for pipeline input_artifacts
    """
    context = extract_context_from_profile(profile)

    return {
        "project_path": str(project_path),
        "codebase_profile": context.to_dict(),
        "primary_language": context.primary_language,
        "languages": context.languages,
        "frameworks": context.frameworks,
        "test_framework": context.test_framework,
        "estimated_coverage": context.estimated_coverage,
        "source_to_test_mapping": context.source_to_test_mapping,
        "detected_patterns": context.detected_patterns,
        # Contracts to apply for this codebase
        "applicable_contracts": get_contracts_for_language(
            context.primary_language or "python"
        ),
    }


# =============================================================================
# Validation Integration
# =============================================================================

def validate_stage_output_for_language(
    stage_name: str,
    artifacts: dict[str, Any],
    language: str,
) -> list[str]:
    """
    Validate stage output with language-specific rules.

    This function only checks language-specific constraints (file extensions,
    naming conventions). Schema validation is done separately via
    ArtifactValidator.validate_stage_output().

    Args:
        stage_name: Name of the stage (spec, red, green, etc.)
        artifacts: Stage output artifacts
        language: Primary language of the codebase

    Returns:
        List of validation error messages
    """
    errors = []

    # Language-specific validations only
    if stage_name == "red":
        errors.extend(_validate_red_output_for_language(artifacts, language))
    elif stage_name == "green":
        errors.extend(_validate_green_output_for_language(artifacts, language))

    return errors


def _validate_red_output_for_language(
    artifacts: dict[str, Any],
    language: str,
) -> list[str]:
    """Validate RED stage output for specific language."""
    errors = []

    test_files = artifacts.get("test_files", [])
    if not test_files:
        return errors

    # Check test file extensions match language
    expected_extensions = {
        "python": [".py"],
        "csharp": [".cs"],
        "typescript": [".ts", ".tsx"],
        "javascript": [".js", ".jsx"],
    }

    expected = expected_extensions.get(language, [])
    for test_file in test_files:
        path = test_file.get("path", "")
        if not any(path.endswith(ext) for ext in expected):
            errors.append(
                f"Test file '{path}' has unexpected extension for {language}"
            )

    return errors


def _validate_green_output_for_language(
    artifacts: dict[str, Any],
    language: str,
) -> list[str]:
    """Validate GREEN stage output for specific language."""
    errors = []

    impl_files = artifacts.get("implementation_files", [])
    if not impl_files:
        return errors

    # Check implementation file extensions match language
    expected_extensions = {
        "python": [".py"],
        "csharp": [".cs"],
        "typescript": [".ts", ".tsx"],
        "javascript": [".js", ".jsx"],
    }

    expected = expected_extensions.get(language, [])
    for impl_file in impl_files:
        path = impl_file.get("path", "")
        if not any(path.endswith(ext) for ext in expected):
            errors.append(
                f"Implementation file '{path}' has unexpected extension for {language}"
            )

    return errors


# =============================================================================
# Test Path Resolution
# =============================================================================

# Language-specific test path conventions
_TEST_CONVENTIONS: dict[str, tuple[str, list[str]]] = {
    # language: (test_name_pattern, default_test_dirs)
    "python": ("test_{stem}.py", ["tests"]),
    "csharp": ("{stem}Tests.cs", ["Tests", "tests"]),
    "typescript": ("{stem}.spec.ts", ["tests", "__tests__"]),
    "javascript": ("{stem}.spec.js", ["tests", "__tests__"]),
}


def _find_test_in_dirs(test_name: str, test_dirs: list[str]) -> str | None:
    """Search for test file in given directories."""
    for test_dir in test_dirs:
        test_path = Path(test_dir) / test_name
        if test_path.exists():
            return str(test_path)
    return None


def resolve_test_path(
    source_path: str,
    context: DiscoveredContext,
    language: str | None = None,
) -> str | None:
    """
    Resolve the test file path for a source file.

    Uses discovered source-to-test mappings first, then falls back
    to language-specific conventions.

    Args:
        source_path: Path to the source file
        context: DiscoveredContext with mappings
        language: Optional language override

    Returns:
        Path to test file, or None if not found
    """
    # Try discovered mapping first
    if context.has_test_for_source(source_path):
        return context.get_test_path_for_source(source_path)

    # Fall back to conventions
    language = language or context.get_language_for_file(source_path)
    if not language or language not in _TEST_CONVENTIONS:
        return None

    source = Path(source_path)
    pattern, default_dirs = _TEST_CONVENTIONS[language]
    test_name = pattern.format(stem=source.stem)
    test_dirs = context.test_directories or default_dirs

    return _find_test_in_dirs(test_name, test_dirs)
