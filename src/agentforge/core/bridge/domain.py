# @spec_file: .agentforge/specs/core-bridge-v1.yaml
# @spec_id: core-bridge-v1
# @component_id: core-bridge-domain
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
Bridge Domain Model
====================

Pure domain objects for the Profile-to-Conformance Bridge.
Transforms discovered patterns into enforceable contract checks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class ConfidenceTier(Enum):
    """Confidence tier for determining auto-enablement."""
    HIGH = "high"       # >= 0.9: auto-enable
    MEDIUM = "medium"   # 0.6 - 0.9: disabled, needs review
    LOW = "low"         # 0.3 - 0.6: disabled, suggested only
    UNCERTAIN = "uncertain"  # < 0.3: not generated

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceTier":
        """Convert numeric confidence to tier."""
        if score >= 0.9:
            return cls.HIGH
        elif score >= 0.6:
            return cls.MEDIUM
        elif score >= 0.3:
            return cls.LOW
        else:
            return cls.UNCERTAIN

    @property
    def auto_enable(self) -> bool:
        """Whether checks at this tier should be auto-enabled."""
        return self == ConfidenceTier.HIGH

    @property
    def should_generate(self) -> bool:
        """Whether checks at this tier should be generated."""
        return self != ConfidenceTier.UNCERTAIN

    @property
    def needs_review(self) -> bool:
        """Whether checks at this tier require human review."""
        return self in (ConfidenceTier.MEDIUM, ConfidenceTier.LOW)


class ConflictType(Enum):
    """Types of conflicts between generated and existing contracts."""
    DUPLICATE_ID = "duplicate_id"           # Same check ID exists
    OVERLAPPING_SCOPE = "overlapping_scope" # Same files, similar pattern
    CONTRADICTING = "contradicting"         # Rules contradict each other
    VERSION_MISMATCH = "version_mismatch"   # Older mapping version


class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts."""
    SKIP = "skip"           # Don't generate, keep existing
    RENAME = "rename"       # Rename the generated check ID
    MERGE = "merge"         # Merge with existing
    OVERWRITE = "overwrite" # Replace existing (with --force)
    WARN = "warn"           # Generate but warn user


@dataclass
class CheckTemplate:
    """
    Template for generating a conformance check.

    Templates use placeholders like {zone} that are resolved
    during generation.
    """
    id_template: str                    # e.g., "{zone}-cqrs-command-naming"
    name: str
    description: str
    check_type: str                     # "naming", "ast", "architecture", "regex"
    config: Dict[str, Any]
    severity: str = "warning"           # "error", "warning", "info"
    applies_to_paths: Optional[List[str]] = None
    exclude_paths: Optional[List[str]] = None
    fix_hint: Optional[str] = None
    review_reason: Optional[str] = None  # Why review is needed

    def resolve_id(self, zone_name: str) -> str:
        """Resolve template placeholders in ID."""
        return self.id_template.replace("{zone}", zone_name)


@dataclass
class GeneratedCheck:
    """
    A fully resolved check ready to be written to a contract.
    """
    id: str
    name: str
    description: str
    check_type: str
    enabled: bool
    severity: str
    config: Dict[str, Any]
    applies_to: Dict[str, Any]
    # Generation metadata
    source_pattern: str
    source_confidence: float
    mapping_version: str = "1.0"
    review_required: bool = False
    review_reason: Optional[str] = None
    fix_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.check_type,
            "enabled": self.enabled,
            "severity": self.severity,
            "config": self.config,
            "applies_to": self.applies_to,
            "generation": {
                "source_pattern": self.source_pattern,
                "source_confidence": round(self.source_confidence, 2),
                "mapping_version": self.mapping_version,
            },
        }
        if self.review_required:
            result["generation"]["review_required"] = True
            if self.review_reason:
                result["generation"]["review_reason"] = self.review_reason
        if self.fix_hint:
            result["fix_hint"] = self.fix_hint
        return result


@dataclass
class GenerationMetadata:
    """Provenance tracking for generated contracts."""
    source_profile: str
    source_hash: str
    generated_at: datetime
    generator_version: str
    zone: Optional[str] = None
    confidence_threshold: float = 0.6
    patterns_mapped: Dict[str, float] = field(default_factory=dict)
    regenerate_command: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_profile": self.source_profile,
            "source_hash": self.source_hash,
            "generated_at": self.generated_at.isoformat(),
            "generator_version": self.generator_version,
            "zone": self.zone,
            "confidence_threshold": self.confidence_threshold,
            "patterns_mapped": {
                k: round(v, 2) for k, v in self.patterns_mapped.items()
            },
            "regenerate_command": self.regenerate_command,
        }


@dataclass
class GeneratedContract:
    """
    A complete generated contract for a zone.
    """
    name: str
    zone: Optional[str]
    language: str
    checks: List[GeneratedCheck]
    metadata: GenerationMetadata
    description: Optional[str] = None
    applies_to_paths: Optional[List[str]] = None
    exclude_paths: Optional[List[str]] = None
    tags: List[str] = field(default_factory=list)

    @property
    def enabled_count(self) -> int:
        return sum(1 for c in self.checks if c.enabled)

    @property
    def disabled_count(self) -> int:
        return sum(1 for c in self.checks if not c.enabled)

    @property
    def review_required_count(self) -> int:
        return sum(1 for c in self.checks if c.review_required)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        contract_dict = {
            "name": self.name,
            "type": "patterns",
            "version": "1.0.0-generated",
            "enabled": True,
        }
        if self.description:
            contract_dict["description"] = self.description

        applies_to = {}
        if self.language:
            applies_to["languages"] = [self.language]
        if self.applies_to_paths:
            applies_to["paths"] = self.applies_to_paths
        if self.exclude_paths:
            applies_to["exclude_paths"] = self.exclude_paths
        if applies_to:
            contract_dict["applies_to"] = applies_to

        if self.tags:
            contract_dict["tags"] = self.tags

        return {
            "schema_version": "1.0",
            "contract": contract_dict,
            "generation_metadata": self.metadata.to_dict(),
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass
class Conflict:
    """A detected conflict between generated and existing contracts."""
    conflict_type: ConflictType
    generated_check_id: str
    existing_contract: Optional[str] = None
    existing_check_id: Optional[str] = None
    resolution: ResolutionStrategy = ResolutionStrategy.SKIP
    reason: Optional[str] = None
    new_id: Optional[str] = None  # For rename resolution

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.conflict_type.value,
            "generated_check": self.generated_check_id,
            "resolution": self.resolution.value,
        }
        if self.existing_contract:
            result["existing_contract"] = self.existing_contract
        if self.existing_check_id:
            result["existing_check"] = self.existing_check_id
        if self.reason:
            result["reason"] = self.reason
        if self.new_id:
            result["new_id"] = self.new_id
        return result


@dataclass
class ContractSummary:
    """Summary of a generated contract."""
    path: str
    zone: Optional[str]
    language: str
    total_checks: int
    enabled_checks: int
    disabled_checks: int
    patterns_mapped: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "zone": self.zone,
            "language": self.language,
            "checks": {
                "total": self.total_checks,
                "enabled": self.enabled_checks,
                "disabled": self.disabled_checks,
            },
            "patterns_mapped": self.patterns_mapped,
        }


@dataclass
class ReviewItem:
    """An item requiring human review."""
    contract: str
    check_id: str
    reason: str
    action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.check_id,
            "reason": self.reason,
            "action": self.action,
        }


@dataclass
class GenerationReport:
    """
    Summary report of a bridge generation run.
    """
    schema_version: str = "1.0"
    generated_at: datetime = field(default_factory=datetime.now)
    generator_version: str = "1.0.0"
    # Source info
    profile_path: str = ""
    profile_hash: str = ""
    profile_generated: Optional[str] = None
    # Configuration
    confidence_threshold: float = 0.6
    output_directory: str = "contracts/"
    dry_run: bool = False
    # Summary
    zones_processed: int = 0
    contracts_generated: int = 0
    total_checks: int = 0
    checks_enabled: int = 0
    checks_disabled: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    # Details
    contracts: List[ContractSummary] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)
    review_required: Dict[str, List[ReviewItem]] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "generator_version": self.generator_version,
            "source": {
                "profile_path": self.profile_path,
                "profile_hash": self.profile_hash,
                "profile_generated": self.profile_generated,
            },
            "configuration": {
                "confidence_threshold": self.confidence_threshold,
                "output_directory": self.output_directory,
                "dry_run": self.dry_run,
            },
            "summary": {
                "zones_processed": self.zones_processed,
                "contracts_generated": self.contracts_generated,
                "total_checks_generated": self.total_checks,
                "checks_enabled": self.checks_enabled,
                "checks_disabled": self.checks_disabled,
                "conflicts_detected": self.conflicts_detected,
                "conflicts_resolved": self.conflicts_resolved,
            },
            "contracts": [c.to_dict() for c in self.contracts],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "review_required": {
                contract: [item.to_dict() for item in items]
                for contract, items in self.review_required.items()
            },
            "next_steps": self.next_steps,
        }


@dataclass
class MappingContext:
    """
    Context provided to pattern mappings during generation.

    Contains profile data and helper methods for accessing
    patterns, structure, and zone information.
    """
    zone_name: Optional[str]
    language: str
    patterns: Dict[str, Any]
    structure: Dict[str, Any]
    conventions: Optional[Dict[str, Any]] = None
    frameworks: List[str] = field(default_factory=list)
    zone_paths: Optional[List[str]] = None

    def is_pattern_detected(self, pattern_key: str) -> bool:
        """Check if a pattern was detected."""
        pattern = self.patterns.get(pattern_key, {})
        if isinstance(pattern, dict):
            return pattern.get("detected", False) or pattern.get("confidence", 0) > 0
        return False

    def get_pattern_confidence(self, pattern_key: str) -> float:
        """Get confidence score for a pattern."""
        pattern = self.patterns.get(pattern_key, {})
        if isinstance(pattern, dict):
            return pattern.get("confidence", 0.0)
        return 0.0

    def get_pattern_primary(self, pattern_key: str) -> Optional[str]:
        """Get primary implementation of a pattern (e.g., 'MediatR' for cqrs)."""
        pattern = self.patterns.get(pattern_key, {})
        if isinstance(pattern, dict):
            return pattern.get("primary")
        return None

    def get_pattern_metadata(self, pattern_key: str) -> Dict[str, Any]:
        """Get all metadata for a pattern."""
        pattern = self.patterns.get(pattern_key, {})
        if isinstance(pattern, dict):
            return pattern
        return {}

    def get_layer_paths(self, layer_name: str) -> List[str]:
        """Get paths for a specific architectural layer."""
        layers = self.structure.get("layers", {})
        layer = layers.get(layer_name, {})
        return layer.get("paths", [])

    def has_layer(self, layer_name: str) -> bool:
        """Check if a layer exists in the structure."""
        layers = self.structure.get("layers", {})
        return layer_name in layers

    def get_architecture_style(self) -> Optional[str]:
        """Get the detected architecture style."""
        style = self.structure.get("style") or self.structure.get("architecture_style")
        return style

    def has_framework(self, framework_name: str) -> bool:
        """Check if a framework is present."""
        name_lower = framework_name.lower()
        return any(name_lower in fw.lower() for fw in self.frameworks)
