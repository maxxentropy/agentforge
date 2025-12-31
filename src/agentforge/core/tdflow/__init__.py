"""
TDFLOW - Test-Driven Implementation Workflow
=============================================

Implements a test-driven development workflow where the agent:
1. Writes failing tests from specification (RED)
2. Implements code to pass tests (GREEN)
3. Refactors while maintaining passing tests (REFACTOR)
4. Verifies implementation meets specification (VERIFY)

Workflow:
    specification.yaml → RED → GREEN → REFACTOR → verified code
"""

from agentforge.core.tdflow.domain import (
    TDFlowPhase,
    ComponentStatus,
    TestCase,
    TestFile,
    ImplementationFile,
    ComponentProgress,
    TestResult,
    PhaseResult,
    VerificationReport,
    SessionHistory,
    TDFlowSession,
)
from agentforge.core.tdflow.session import SessionManager
from agentforge.core.tdflow.orchestrator import TDFlowOrchestrator

__all__ = [
    # Domain entities
    "TDFlowPhase",
    "ComponentStatus",
    "TestCase",
    "TestFile",
    "ImplementationFile",
    "ComponentProgress",
    "TestResult",
    "PhaseResult",
    "VerificationReport",
    "SessionHistory",
    "TDFlowSession",
    # Core classes
    "SessionManager",
    "TDFlowOrchestrator",
]
