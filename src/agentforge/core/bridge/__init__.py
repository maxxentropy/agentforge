"""
Profile-to-Conformance Bridge
=============================

Transforms discovered patterns from Chunk 4 (Brownfield Discovery)
into enforceable contracts for Chunk 3 (Conformance Tracking).

Usage:
    from agentforge.core.bridge import BridgeOrchestrator

    orchestrator = BridgeOrchestrator(root_path=Path("."))
    contracts, report = orchestrator.generate()

    for contract in contracts:
        print(f"{contract.name}: {len(contract.checks)} checks")

CLI:
    agentforge bridge generate [--zone NAME] [--dry-run]
    agentforge bridge preview
    agentforge bridge mappings
    agentforge bridge refresh
"""

from .orchestrator import BridgeOrchestrator
from .domain import (
    ConfidenceTier,
    ConflictType,
    ResolutionStrategy,
    CheckTemplate,
    GeneratedCheck,
    GeneratedContract,
    GenerationMetadata,
    Conflict,
    GenerationReport,
    MappingContext,
)
from .mappings import PatternMapping, MappingRegistry
from .profile_loader import ProfileLoader
from .conflict_resolver import ConflictResolver
from .contract_builder import ContractBuilder

__all__ = [
    # Main orchestrator
    "BridgeOrchestrator",
    # Domain entities
    "ConfidenceTier",
    "ConflictType",
    "ResolutionStrategy",
    "CheckTemplate",
    "GeneratedCheck",
    "GeneratedContract",
    "GenerationMetadata",
    "Conflict",
    "GenerationReport",
    "MappingContext",
    # Mapping infrastructure
    "PatternMapping",
    "MappingRegistry",
    # Components
    "ProfileLoader",
    "ConflictResolver",
    "ContractBuilder",
]
