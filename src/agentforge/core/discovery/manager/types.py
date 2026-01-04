"""
Discovery Manager Types
=======================

Data classes and enums for discovery results.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ..domain import (
    CodebaseProfile,
    DiscoveryPhase,
    Interaction,
    Zone,
    ZoneProfile,
)


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
