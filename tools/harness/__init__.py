"""
Agent Harness - Autonomous Agent Framework Layer

Provides infrastructure for running autonomous agents with:
- Session management and state persistence
- 4-tier memory hierarchy
- Phase-appropriate tool selection
- Pathology detection and recovery strategies
- Human escalation and oversight

Components:
    session: Session Manager (Phase 1)
    memory: Memory System (Phase 2)
    tools: Tool Selector (Phase 3)
    monitor: Agent Monitor (Phase 4)
    recovery: Recovery Strategies (Phase 5)
    escalation: Human Escalation (Phase 6)
    orchestrator: Agent Orchestrator (Phase 7)
"""

from tools.harness.session_domain import (
    SessionState,
    TokenBudget,
    SessionArtifact,
    SessionHistory,
    SessionContext,
)
from tools.harness.session_store import SessionStore
from tools.harness.session_manager import (
    SessionManager,
    SessionAlreadyActive,
    NoActiveSession,
    InvalidStateTransition,
)

__all__ = [
    "SessionState",
    "TokenBudget",
    "SessionArtifact",
    "SessionHistory",
    "SessionContext",
    "SessionStore",
    "SessionManager",
    "SessionAlreadyActive",
    "NoActiveSession",
    "InvalidStateTransition",
]
