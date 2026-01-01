# @spec_file: .agentforge/specs/discovery-v1.yaml
# @spec_id: discovery-v1
# @component_id: tools-discovery-domain
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
from typing import List, Optional, Dict, Any


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
    signals: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_score(self.confidence)

    def to_dict(self) -> Dict[str, Any]:
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
    version: Optional[str]
    detection: Detection
    file_count: int = 0
    line_count: int = 0
    frameworks: List[str] = field(default_factory=list)
    primary: bool = False

    def to_dict(self) -> Dict[str, Any]:
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
    framework: Optional[str] = None
    references: List[str] = field(default_factory=list)
    packages: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class LayerInfo:
    """Detected architectural layer."""
    name: str
    paths: List[str] = field(default_factory=list)
    file_count: int = 0
    line_count: int = 0
    detection: Detection = field(default_factory=lambda: Detection(
        value="unknown", confidence=0.0, source=DetectionSource.AUTO_DETECTED
    ))

    @property
    def has_violations(self) -> bool:
        """Check if layer has dependency violations."""
        return False  # Violations tracked separately

    def to_dict(self) -> Dict[str, Any]:
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
    from_project: Optional[str] = None
    to_project: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    import_statement: Optional[str] = None
    severity: str = "major"


@dataclass
class PatternDetection:
    """A detected coding pattern."""
    pattern_name: str
    description: str
    detection: Detection
    locations: List[str] = field(default_factory=list)
    file_count: int = 0
    usage_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
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
    exceptions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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
    frameworks: List[str] = field(default_factory=list)
    categories: Dict[str, int] = field(default_factory=dict)


@dataclass
class TestGap:
    """An identified gap in test coverage."""
    gap_type: str  # "untested_project", "untested_class", "untested_method"
    location: str
    note: Optional[str] = None


@dataclass
class TestAnalysis:
    """Results of test gap analysis."""
    inventory: TestInventory = field(default_factory=TestInventory)
    estimated_coverage: float = 0.0
    gaps: List[TestGap] = field(default_factory=list)
    detection: Detection = field(default_factory=lambda: Detection(
        value="test_analysis", confidence=0.0, source=DetectionSource.AUTO_DETECTED
    ))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inventory": {
                "total_test_files": self.inventory.total_test_files,
                "total_test_methods": self.inventory.total_test_methods,
                "frameworks": self.inventory.frameworks,
                "categories": self.inventory.categories,
            },
            "estimated_coverage": round(self.estimated_coverage, 2),
            "confidence": round(self.detection.confidence, 2),
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
    marker: Optional[Path] = None  # The file that triggered detection (e.g., pyproject.toml)
    detection: ZoneDetectionMode = ZoneDetectionMode.AUTO
    purpose: Optional[str] = None
    contracts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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
    from_zone: Optional[str] = None
    to_zone: Optional[str] = None
    # For multi-zone interactions (e.g., shared schema used by multiple zones)
    zones: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
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
    languages: List[LanguageInfo] = field(default_factory=list)
    structure: Dict[str, Any] = field(default_factory=dict)
    patterns: Dict[str, Any] = field(default_factory=dict)
    conventions: Optional[Dict[str, Any]] = None
    frameworks: List[str] = field(default_factory=list)
    dependencies: List["DependencyInfo"] = field(default_factory=list)
    file_count: int = 0
    line_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
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
    version: Optional[str] = None
    source: str = "unknown"  # "nuget", "pypi", "npm"
    is_dev: bool = False
    category: Optional[str] = None
    license: Optional[str] = None


@dataclass
class DiscoveryMetadata:
    """Metadata about a discovery run."""
    discovery_version: str
    run_date: datetime
    root_path: str
    phases_completed: List[str]
    total_files_analyzed: int = 0
    duration_seconds: float = 0.0


@dataclass
class OnboardingProgress:
    """Tracks incremental onboarding progress."""
    status: OnboardingStatus
    modules: Dict[str, OnboardingStatus] = field(default_factory=dict)

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
    languages: List[LanguageInfo]

    # Structure
    structure: Dict[str, Any]

    # Patterns
    patterns: Dict[str, Any]

    # Architecture
    architecture: Optional[Dict[str, Any]] = None

    # Conventions
    conventions: Optional[Dict[str, Any]] = None

    # Tests
    test_analysis: Optional[TestAnalysis] = None

    # Dependencies
    dependencies: List[DependencyInfo] = field(default_factory=list)

    # Onboarding
    onboarding_progress: Optional[OnboardingProgress] = None

    def to_dict(self) -> Dict[str, Any]:
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
