# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: audit-module

"""
Unified Audit Trail System
===========================

Complete transparency for autonomous agent execution through:
- Contract-aware context frames with schema validation
- Full LLM conversation capture (prompts + responses)
- Agent delegation tracking (parent-child thread correlation)
- Tamper-evident hash chains
- Human-in-the-loop context recording

Key Components:

Frame-Based Logging (Contract-Aware):
- ContextFrame: Validated snapshot with schema references
- FrameLogger: Logs frames with schema-aware validation
- ValidatedContext: Context wrapped with validation envelope
- ParsedArtifact: LLM output wrapped with parsing/validation info

Transaction Logging (Raw):
- TransactionLogger: Per-thread transaction recording
- TransactionRecord: Complete transaction record

Infrastructure:
- ThreadCorrelator: Agent spawning and parallel execution tracking
- IntegrityChain: SHA-256 hash chain for tamper evidence
- ConversationArchive: Full LLM conversation storage
- AuditManager: Central coordinator

Every autonomous decision is traceable back to its origin
with full contract/schema compliance verification.
"""

from .transaction_logger import TransactionLogger, TransactionRecord
from .thread_correlator import ThreadCorrelator, ThreadInfo, ThreadSpawn
from .integrity_chain import IntegrityChain, ChainBlock
from .conversation_archive import ConversationArchive, ConversationTurn
from .audit_manager import AuditManager
from .context_frame import (
    ContextFrame,
    ContextFrameBuilder,
    FrameType,
    SchemaReference,
    ValidationResult,
    ValidationStatus,
    ValidatedContext,
    LLMInteractionEnvelope,
    ParsedArtifact,
)
from .frame_logger import FrameLogger

__all__ = [
    # Frame-based (contract-aware)
    "ContextFrame",
    "ContextFrameBuilder",
    "FrameType",
    "SchemaReference",
    "ValidationResult",
    "ValidationStatus",
    "ValidatedContext",
    "LLMInteractionEnvelope",
    "ParsedArtifact",
    "FrameLogger",
    # Transaction-based
    "AuditManager",
    "TransactionLogger",
    "TransactionRecord",
    # Infrastructure
    "ThreadCorrelator",
    "ThreadInfo",
    "ThreadSpawn",
    "IntegrityChain",
    "ChainBlock",
    "ConversationArchive",
    "ConversationTurn",
]
