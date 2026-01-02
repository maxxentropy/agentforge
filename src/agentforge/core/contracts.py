# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-contracts
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

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

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RegistryOptions:
    """Options for contract registry configuration."""
    workspace_root: Path | None = None
    global_root: Path | None = None
    include_abstract: bool = False


# Re-export types for backwards compatibility
try:
    from .contracts_execution import execute_check
    from .contracts_registry import BUILTIN_CONTRACTS_DIR, ContractRegistry  # noqa: F401
    from .contracts_types import CheckResult, Contract, ContractResult, Exemption  # noqa: F401
except ImportError:
    from contracts_execution import execute_check
    from contracts_registry import ContractRegistry
    from contracts_types import Contract, ContractResult


# ==============================================================================
# High-Level API
# ==============================================================================

def run_contract(contract: Contract, repo_root: Path,
                 registry: ContractRegistry,
                 file_paths: list[Path] | None = None) -> ContractResult:
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


def run_all_contracts(
    repo_root: Path, language: str | None = None, repo_type: str | None = None,
    file_paths: list[Path] | None = None, options: RegistryOptions | None = None
) -> list[ContractResult]:
    """Run all applicable contracts for a repository."""
    opts = options or RegistryOptions()
    registry = ContractRegistry(repo_root, opts.workspace_root, opts.global_root)

    if opts.include_abstract:
        contracts = registry.get_enabled_contracts(language, repo_type, include_abstract=True)
    else:
        contracts = registry.get_applicable_contracts(language, repo_type)

    return [run_contract(contract, repo_root, registry, file_paths) for contract in contracts]
