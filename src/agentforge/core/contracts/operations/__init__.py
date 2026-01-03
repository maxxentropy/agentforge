# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: operation-contracts

"""
Operation Contracts
===================

Pre-defined contracts that govern common operations.
These encode universal judgment that applies to ALL requests.

Contract Types:
- tool-usage: When and how to use specific tools
- git-operations: Safe git practices
- safety-rules: Security and safety constraints

These templates are loaded at startup and enforced
alongside per-request task contracts.
"""

from .loader import (
    OperationContract,
    OperationRule,
    OperationTrigger,
    OperationGate,
    OperationContractManager,
    load_operation_contract,
    load_all_operation_contracts,
    get_builtin_contracts_path,
)
from .verifier import (
    OperationContractVerifier,
    Violation,
    VerificationReport,
    verify_operations,
)

__all__ = [
    # Loader
    "OperationContract",
    "OperationRule",
    "OperationTrigger",
    "OperationGate",
    "OperationContractManager",
    "load_operation_contract",
    "load_all_operation_contracts",
    "get_builtin_contracts_path",
    # Verifier
    "OperationContractVerifier",
    "Violation",
    "VerificationReport",
    "verify_operations",
]
