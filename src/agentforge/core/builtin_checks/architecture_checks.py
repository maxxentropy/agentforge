"""
Architecture Checks
===================

Checks for architectural constraints and validation.
"""

from pathlib import Path


def check_minimal_context_validation(
    repo_root: Path,
    file_paths: list[Path],
    **params
) -> list[dict]:
    """
    Check that the Minimal Context Architecture has proper validation in place.

    Validates that key files contain required validation methods:
    1. EnhancedContextBuilder has _validate_context_integrity
    2. Executor has _validate_response_parameters
    3. PhaseMachine has validate_state

    This ensures runtime validation catches issues early.
    """
    violations = []

    required_validations = {
        "enhanced_context_builder.py": {
            "method": "_validate_context_integrity",
            "description": "context integrity validation",
        },
        "executor.py": {
            "method": "_validate_response_parameters",
            "description": "response parameter validation",
        },
        "phase_machine.py": {
            "method": "validate_state",
            "description": "phase state validation",
        },
    }

    for file_path in file_paths:
        filename = file_path.name
        if filename not in required_validations:
            continue

        req = required_validations[filename]

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        if f"def {req['method']}" not in content:
            violations.append({
                "message": f"Missing {req['description']} method: {req['method']}",
                "file": str(file_path.relative_to(repo_root)),
                "severity": "error",
                "fix_hint": f"Add {req['method']} method for runtime validation"
            })

    return violations


def check_layer_imports(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Check that layer imports follow architectural boundaries.

    This is a stub implementation. Future implementation should:
    - Define layer hierarchy (e.g., domain < application < infrastructure)
    - Verify imports don't violate boundaries (e.g., domain shouldn't import infra)

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (layer_detection, layer_rules)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement layer boundary checking
    return []


def check_constructor_injection(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Check that classes use constructor injection for dependencies.

    This is a stub implementation. Future implementation should:
    - Parse class constructors
    - Verify dependencies are injected via __init__
    - Flag direct instantiation of dependencies

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (class_patterns, etc.)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement constructor injection checking
    return []


def check_domain_purity(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Check that domain layer has no external dependencies.

    This is a stub implementation. Future implementation should:
    - Identify domain layer files
    - Verify they don't import infrastructure concerns
    - Flag I/O, HTTP, database imports in domain

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (forbidden_imports, etc.)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement domain purity checking
    return []


def check_circular_imports(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Detect circular import dependencies.

    This is a stub implementation. Future implementation should:
    - Build import graph from AST
    - Detect cycles in the graph
    - Report minimal cycle paths

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (ignore_type_checking, max_depth)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement circular import detection
    return []
