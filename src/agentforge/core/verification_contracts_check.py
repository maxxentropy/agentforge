#!/usr/bin/env python3
"""
Verification Contracts Check Helpers
=====================================

Helper functions for running contract-based verification checks.
Extracted from verification_checks.py for modularity.
"""

from pathlib import Path


def get_contract_results(check: dict, project_root: Path) -> tuple[list | None, str | None]:
    """Get contract results based on check config. Returns (results, error_msg)."""
    from contracts import ContractRegistry, run_all_contracts, run_contract

    contract_name = check.get("contract")
    if contract_name:
        registry = ContractRegistry(project_root)
        contract = registry.get_contract(contract_name)
        if not contract:
            return None, f"Contract not found: {contract_name}"
        return [run_contract(contract, project_root, registry)], None

    return run_all_contracts(
        project_root, language=check.get("language"), repo_type=check.get("repo_type")
    ), None


def build_contract_errors(results: list) -> list:
    """Build error details from contract results."""
    errors = []
    for result in results:
        for check_result in result.check_results:
            if not check_result.passed and not check_result.exempted:
                errors.append({
                    "contract": result.contract_name, "check": check_result.check_id,
                    "severity": check_result.severity, "message": check_result.message,
                    "file": check_result.file_path, "line": check_result.line_number,
                })
    return errors


def aggregate_contract_stats(results: list) -> dict:
    """Aggregate statistics from contract results."""
    return {
        "errors": sum(len(r.errors) for r in results),
        "warnings": sum(len(r.warnings) for r in results),
        "exempted": sum(r.exempted_count for r in results),
        "all_passed": all(r.passed for r in results),
    }


def build_contract_message(results: list, stats: dict) -> str:
    """Build summary message for contract check results."""
    message = f"Ran {len(results)} contracts: {stats['errors']} errors, {stats['warnings']} warnings"
    if stats["exempted"] > 0:
        message += f", {stats['exempted']} exempted"
    return message
