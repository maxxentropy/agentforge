"""
Conformance Tracking System
===========================

Per-repository conformance tracking for AgentForge contracts.

Exports:
    - Domain entities: Violation, Exemption, ConformanceReport, etc.
    - Storage: ViolationStore, ExemptionRegistry, HistoryStore
    - Manager: ConformanceManager for orchestration
"""

from .domain import (
    ConformanceReport,
    ConformanceSummary,
    Exemption,
    ExemptionScope,
    ExemptionScopeType,
    ExemptionStatus,
    HistorySnapshot,
    Severity,
    Violation,
    ViolationStatus,
)

__all__ = [
    "Severity",
    "ViolationStatus",
    "ExemptionStatus",
    "ExemptionScopeType",
    "ExemptionScope",
    "Violation",
    "Exemption",
    "ConformanceSummary",
    "ConformanceReport",
    "HistorySnapshot",
]
