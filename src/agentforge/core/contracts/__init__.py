# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contracts-module

"""
Contract Authoring System
=========================

LLM-assisted contract authoring for trusted autonomous execution.

This module provides:
- Contract drafting from natural language requirements
- Human review workflow for contract approval
- Contract storage and retrieval
- Runtime contract enforcement
- Contract evolution during execution

Key Concepts:

Operation Contracts (Templates):
    Pre-defined contracts that govern common operations:
    - Tool usage patterns
    - Git operations
    - Safety rules

Task Contracts (Per-Request):
    Contracts drafted for specific tasks:
    - Stage schemas
    - Validation rules
    - Escalation triggers
    - Quality gates

Contract Flow:
    1. User provides natural language request
    2. ContractDrafter drafts contracts using LLM
    3. Human reviews and approves contracts
    4. ApprovedContracts registered in ContractRegistry
    5. ContractEnforcer validates execution against contracts
    6. ContractEvolutionHandler handles assumption violations
"""

from .draft import (
    Assumption,
    ApprovedContracts,
    ContractDraft,
    EscalationTrigger,
    OpenQuestion,
    QualityGate,
    Revision,
    StageContract,
    ValidationRule,
)
from .registry import (
    ContractRegistry,
    generate_contract_set_id,
    generate_draft_id,
)
from .drafter import (
    CodebaseContext,
    ContractDrafter,
    DrafterConfig,
)
from .reviewer import (
    ContractReviewer,
    OverallDecision,
    ReviewDecision,
    ReviewFeedback,
    ReviewSession,
    StageDecision,
)
from .enforcer import (
    ContractEnforcer,
    EscalationCheck,
    QualityGateResult,
    ValidationResult,
    Violation,
    ViolationSeverity,
    ViolationType,
)
from .evolution import (
    AssumptionViolation,
    ContractChange,
    ContractEscalation,
    ContractEvolutionHandler,
    EvolutionViolationType,
)

__all__ = [
    # Draft structures
    "ContractDraft",
    "ApprovedContracts",
    "StageContract",
    "ValidationRule",
    "EscalationTrigger",
    "QualityGate",
    "OpenQuestion",
    "Assumption",
    "Revision",
    # Registry
    "ContractRegistry",
    "generate_contract_set_id",
    "generate_draft_id",
    # Drafter
    "ContractDrafter",
    "DrafterConfig",
    "CodebaseContext",
    # Reviewer
    "ContractReviewer",
    "ReviewSession",
    "ReviewFeedback",
    "StageDecision",
    "ReviewDecision",
    "OverallDecision",
    # Enforcer
    "ContractEnforcer",
    "ValidationResult",
    "Violation",
    "ViolationSeverity",
    "ViolationType",
    "QualityGateResult",
    "EscalationCheck",
    # Evolution
    "ContractEvolutionHandler",
    "AssumptionViolation",
    "ContractChange",
    "ContractEscalation",
    "EvolutionViolationType",
]
