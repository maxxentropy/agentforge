"""
Contract loading, resolution, and execution for AgentForge.

Contracts define machine-verifiable code correctness rules that can be:
- Inherited from builtin contracts (_base, _patterns-csharp, etc.)
- Defined at global, workspace, or repo level
- Exempted with documented justifications

This module provides the high-level API for contract operations.
For implementation details, see:
- contracts_types.py: Data classes
- contracts_registry.py: Contract discovery and loading
- contracts_execution.py: Check execution
- contracts_ast.py: AST-based checks
- contracts_lsp.py: LSP-based checks
"""

from pathlib import Path
from typing import List, Optional

# Re-export types for backwards compatibility
try:
    from .contracts_types import CheckResult, ContractResult, Exemption, Contract
    from .contracts_registry import ContractRegistry, BUILTIN_CONTRACTS_DIR
    from .contracts_execution import execute_check
except ImportError:
    from contracts_types import CheckResult, ContractResult, Exemption, Contract
    from contracts_registry import ContractRegistry, BUILTIN_CONTRACTS_DIR
    from contracts_execution import execute_check


# ==============================================================================
# High-Level API
# ==============================================================================

def run_contract(contract: Contract, repo_root: Path,
                 registry: ContractRegistry,
                 file_paths: Optional[List[Path]] = None) -> ContractResult:
    """
    Run all checks in a contract.

    Args:
        contract: Contract to run
        repo_root: Repository root directory
        registry: ContractRegistry for exemption lookup
        file_paths: Optional specific files to check

    Returns:
        ContractResult with all check results
    """
    all_results = []

    for check in contract.all_checks():
        if not check.get("enabled", True):
            continue

        effective_check = dict(check)
        if "applies_to" not in effective_check:
            effective_check["applies_to"] = contract.applies_to

        check_results = execute_check(effective_check, repo_root, file_paths)

        for result in check_results:
            if not result.passed:
                exemption = registry.find_exemption(
                    contract.name, result.check_id, result.file_path, result.line_number
                )
                if exemption:
                    result.exempted = True
                    result.exemption_id = exemption.id

        all_results.extend(check_results)

    passed = not any(
        r for r in all_results
        if not r.passed and r.severity == "error" and not r.exempted
    )

    return ContractResult(
        contract_name=contract.name,
        contract_type=contract.type,
        passed=passed,
        check_results=all_results
    )


def run_all_contracts(repo_root: Path,
                      workspace_root: Optional[Path] = None,
                      global_root: Optional[Path] = None,
                      language: Optional[str] = None,
                      repo_type: Optional[str] = None,
                      file_paths: Optional[List[Path]] = None,
                      include_abstract: bool = False) -> List[ContractResult]:
    """
    Run all applicable contracts for a repository.

    By default, only runs CONCRETE contracts (no underscore prefix).
    Abstract contracts (e.g., _base, _patterns-python) are building blocks
    meant to be extended, not run directly. Concrete contracts (e.g., agentforge)
    inherit from abstract contracts and are the entry points for projects.

    Args:
        repo_root: Repository root directory
        workspace_root: Optional workspace contracts directory
        global_root: Optional global contracts directory
        language: Filter by language
        repo_type: Filter by repo type
        file_paths: Optional specific files to check
        include_abstract: If True, also run abstract contracts (not recommended)

    Returns:
        List of ContractResult for each contract
    """
    registry = ContractRegistry(repo_root, workspace_root, global_root)

    if include_abstract:
        contracts = registry.get_enabled_contracts(language, repo_type, include_abstract=True)
    else:
        contracts = registry.get_applicable_contracts(language, repo_type)

    return [run_contract(contract, repo_root, registry, file_paths) for contract in contracts]
