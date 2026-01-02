# @spec_file: .agentforge/specs/core-discovery-v1.yaml
# @spec_id: core-discovery-v1
# @component_id: core-discovery-domain
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
Brownfield Discovery Domain Model
=================================

Pure domain objects for discovery operations. No I/O operations.
These entities represent detected patterns, conventions, and structure.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class DetectionSource(Enum):
    """How a value was determined."""
    AUTO_DETECTED = "auto-detected"
    HUMAN_CURATED = "human-curated"
    INFERRED = "inferred"
    EXPLICIT = "explicit"
    STRUCTURAL = "structural"
    NAMING = "naming"
    AST = "ast"
    STATISTICAL = "statistical"


class ConfidenceLevel(Enum):
    """Confidence classification for detections."""
    HIGH = "high"       # >= 0.9
    MEDIUM = "medium"   # 0.6 - 0.9
    LOW = "low"         # 0.3 - 0.6
    UNCERTAIN = "uncertain"  # < 0.3

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        """Convert numeric score to confidence level."""
        if score >= 0.9:
            return cls.HIGH
        elif score >= 0.6:
            return cls.MEDIUM
        elif score >= 0.3:
            return cls.LOW
        else:
            return cls.UNCERTAIN


class DiscoveryPhase(Enum):
    """Phases of discovery process."""
    LANGUAGE = "language"
    STRUCTURE = "structure"
    PATTERNS = "patterns"
    ARCHITECTURE = "architecture"
    CONVENTIONS = "conventions"
    TESTS = "tests"


class OnboardingStatus(Enum):
    """Status of module onboarding."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ANALYZED = "analyzed"
    FAILED = "failed"


class ZoneDetectionMode(Enum):
    """How zone was detected."""
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


class InteractionType(Enum):
    """Types of cross-zone interactions."""
    HTTP_API = "http_api"
    GRPC = "grpc"
    MESSAGE_QUEUE = "message_queue"
    SHARED_SCHEMA = "shared_schema"
    SHARED_LIBRARY = "shared_library"
    DOCKER_COMPOSE = "docker_compose"
    FILE_SYSTEM = "file_system"


@dataclass
class Detection:
    """A detection with confidence and evidence tracking."""
    value: Any
    confidence: float
    source: DetectionSource = DetectionSource.AUTO_DETECTED
    signals: list[str] = field(default_factory=list)
    metadata: dict[str, Any] | None = None

    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_score(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "value": self.value,
            "confidence": round(self.confidence, 2),
            "source": self.source.value,
        }
        if self.signals:
            result["signals"] = self.signals
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class LanguageInfo:
    """Detected programming language."""
    name: str
    version: str | None
    detection: Detection
    file_count: int = 0
    line_count: int = 0
    frameworks: list[str] = field(default_factory=list)
    primary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "confidence": round(self.detection.confidence, 2),
            "file_count": self.file_count,
            "line_count": self.line_count,
            "frameworks": self.frameworks,
            "primary": self.primary,
        }


@dataclass
class ProjectInfo:
    """Information about a detected project."""
    path: Path
    name: str
    language: str
    project_type: str  # "library", "executable", "web", "test"
    framework: str | None = None
    references: list[str] = field(default_factory=list)
    packages: list[dict[str, str]] = field(default_factory=list)


@dataclass
class LayerInfo:
    """Detected architectural layer."""
    name: str
    paths: list[str] = field(default_factory=list)
    file_count: int = 0
    line_count: int = 0
    detection: Detection = field(default_factory=lambda: Detection(
        value="unknown", confidence=0.0, source=DetectionSource.AUTO_DETECTED
    ))

    @property
    def has_violations(self) -> bool:
        """Check if layer has dependency violations."""
        return False  # Violations tracked separately

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "paths": self.paths,
            "file_count": self.file_count,
            "line_count": self.line_count,
            "confidence": round(self.detection.confidence, 2),
        }


@dataclass
class ArchitectureViolation:
    """A detected architecture layer violation."""
    from_layer: str
    to_layer: str
    from_project: str | None = None
    to_project: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    import_statement: str | None = None
    severity: str = "major"


@dataclass
class PatternDetection:
    """A detected coding pattern."""
    pattern_name: str
    description: str
    detection: Detection
    locations: list[str] = field(default_factory=list)
    file_count: int = 0
    usage_percentage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "description": self.description,
            "confidence": round(self.detection.confidence, 2),
            "source": self.detection.source.value,
            "file_count": self.file_count,
            "locations": self.locations[:5],
        }


@dataclass
class ConventionDetection:
    """A detected naming or organization convention."""
    name: str
    pattern: str
    detection: Detection
    consistency: float = 0.0
    exceptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern": self.pattern,
            "consistency": round(self.consistency, 2),
            "confidence": round(self.detection.confidence, 2),
            "exceptions": self.exceptions[:10],
        }


@dataclass
class TestInventory:
    """Inventory of tests in the codebase."""
    total_test_files: int = 0
    total_test_methods: int = 0
    frameworks: list[str] = field(default_factory=list)
    categories: dict[str, int] = field(default_factory=dict)


@dataclass
class TestGap:
    """An identified gap in test coverage."""
    gap_type: str  # "untested_project", "untested_class", "untested_method"
    location: str
    note: str | None = None


@dataclass
class TestLinkage:
    """
    Links a source file to its test file(s).

    This is the critical data structure for the fix workflow - it tells
    exactly which tests verify a given source file. Generated by brownfield
    discovery through import analysis and naming conventions.
    """
    source_path: str  # Relative path to source file
    test_paths: list[str] = field(default_factory=list)  # Test files that cover this source
    confidence: float = 0.0  # How confident we are in the linkage
    detection_method: str = "unknown"  # "import", "naming", "ast", "explicit"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "test_paths": self.test_paths,
            "confidence": round(self.confidence, 2),
            "detection_method": self.detection_method,
        }


@dataclass
class TestAnalysis:
    """Results of test gap analysis."""
    inventory: TestInventory = field(default_factory=TestInventory)
    estimated_coverage: float = 0.0
    gaps: list[TestGap] = field(default_factory=list)
    # NEW: Source-to-test mapping for fix verification
    linkages: list[TestLinkage] = field(default_factory=list)
    detection: Detection = field(default_factory=lambda: Detection(
        value="test_analysis", confidence=0.0, source=DetectionSource.AUTO_DETECTED
    ))

    def get_test_path(self, source_path: str) -> str | None:
        """Get the primary test path for a source file."""
        for linkage in self.linkages:
            if linkage.source_path == source_path and linkage.test_paths:
                return linkage.test_paths[0]
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory": {
                "total_test_files": self.inventory.total_test_files,
                "total_test_methods": self.inventory.total_test_methods,
                "frameworks": self.inventory.frameworks,
                "categories": self.inventory.categories,
            },
            "estimated_coverage": round(self.estimated_coverage, 2),
            "confidence": round(self.detection.confidence, 2),
            "linkages": {l.source_path: l.test_paths for l in self.linkages},
        }


@dataclass
class Zone:
    """
    A coherent area of code with its own language, patterns, and conventions.

    Zones enable multi-language repository support. Each zone is independently
    analyzed and can have its own conformance contracts.
    """
    name: str
    path: Path
    language: str
    marker: Path | None = None  # The file that triggered detection (e.g., pyproject.toml)
    detection: ZoneDetectionMode = ZoneDetectionMode.AUTO
    purpose: str | None = None
    contracts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "language": self.language,
            "marker": str(self.marker) if self.marker else None,
            "detection": self.detection.value,
            "purpose": self.purpose,
            "contracts": self.contracts,
        }

    def contains_path(self, path: Path) -> bool:
        """Check if a path is within this zone."""
        try:
            path.relative_to(self.path)
            return True
        except ValueError:
            return False


@dataclass
class Interaction:
    """
    A detected cross-zone interaction.

    Interactions capture how different zones communicate - through HTTP APIs,
    shared schemas, docker-compose orchestration, etc.
    """
    id: str
    interaction_type: InteractionType
    # For directional interactions (from_zone -> to_zone)
    from_zone: str | None = None
    to_zone: str | None = None
    # For multi-zone interactions (e.g., shared schema used by multiple zones)
    zones: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "type": self.interaction_type.value,
        }
        if self.from_zone and self.to_zone:
            result["from_zone"] = self.from_zone
            result["to_zone"] = self.to_zone
        if self.zones:
            result["zones"] = self.zones
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class ZoneProfile:
    """
    Per-zone discovery results.

    Each zone gets its own profile with language-specific patterns,
    structure, and conventions. This enables different analysis
    strategies per zone.
    """
    zone: Zone
    languages: list[LanguageInfo] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)
    patterns: dict[str, Any] = field(default_factory=dict)
    conventions: dict[str, Any] | None = None
    frameworks: list[str] = field(default_factory=list)
    dependencies: list["DependencyInfo"] = field(default_factory=list)
    file_count: int = 0
    line_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        result = {
            "language": self.zone.language,
            "path": str(self.zone.path),
            "marker": str(self.zone.marker) if self.zone.marker else None,
            "detection": self.zone.detection.value,
            "purpose": self.zone.purpose,
            "structure": self.structure,
            "patterns": self.patterns,
            "frameworks": self.frameworks,
            "contracts": self.zone.contracts,
        }
        if self.conventions:
            result["conventions"] = self.conventions
        return result


@dataclass
class DependencyInfo:
    """Information about an external dependency."""
    name: str
    version: str | None = None
    source: str = "unknown"  # "nuget", "pypi", "npm"
    is_dev: bool = False
    category: str | None = None
    license: str | None = None


@dataclass
class DiscoveryMetadata:
    """Metadata about a discovery run."""
    discovery_version: str
    run_date: datetime
    root_path: str
    phases_completed: list[str]
    total_files_analyzed: int = 0
    duration_seconds: float = 0.0


@dataclass
class OnboardingProgress:
    """Tracks incremental onboarding progress."""
    status: OnboardingStatus
    modules: dict[str, OnboardingStatus] = field(default_factory=dict)

    def is_complete(self) -> bool:
        return self.status == OnboardingStatus.ANALYZED


@dataclass
class CodebaseProfile:
    """
    Complete profile of a discovered codebase.

    This is the primary output of brownfield discovery.
    """
    schema_version: str
    generated_at: datetime
    discovery_metadata: DiscoveryMetadata

    # Language & Framework
    languages: list[LanguageInfo]

    # Structure
    structure: dict[str, Any]

    # Patterns
    patterns: dict[str, Any]

    # Architecture
    architecture: dict[str, Any] | None = None

    # Conventions
    conventions: dict[str, Any] | None = None

    # Tests
    test_analysis: TestAnalysis | None = None

    # Dependencies
    dependencies: list[DependencyInfo] = field(default_factory=list)

    # Onboarding
    onboarding_progress: OnboardingProgress | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "discovery_metadata": {
                "discovery_version": self.discovery_metadata.discovery_version,
                "run_date": self.discovery_metadata.run_date.isoformat(),
                "root_path": self.discovery_metadata.root_path,
                "phases_completed": self.discovery_metadata.phases_completed,
                "total_files_analyzed": self.discovery_metadata.total_files_analyzed,
                "duration_seconds": round(self.discovery_metadata.duration_seconds, 2),
            },
            "languages": [lang.to_dict() for lang in self.languages],
            "structure": self.structure,
            "patterns": self.patterns,
        }

        if self.architecture:
            result["architecture"] = self.architecture
        if self.conventions:
            result["conventions"] = self.conventions
        if self.test_analysis:
            result["test_analysis"] = self.test_analysis.to_dict()
        if self.dependencies:
            result["dependencies"] = [
                {"name": d.name, "version": d.version, "source": d.source, "is_dev": d.is_dev}
                for d in self.dependencies
            ]
        if self.onboarding_progress:
            result["onboarding_progress"] = {
                "status": self.onboarding_progress.status.value,
                "modules": {
                    k: v.value for k, v in self.onboarding_progress.modules.items()
                },
            }

        return result
