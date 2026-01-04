"""
Built-in Checks Registry
========================

Registry of all built-in check functions.
"""

from .architecture_checks import (
    check_circular_imports,
    check_constructor_injection,
    check_domain_purity,
    check_layer_imports,
    check_minimal_context_validation,
)
from .file_checks import (
    check_file_size,
    check_line_length,
    check_mixed_line_endings,
    check_trailing_whitespace,
)
from .lineage_checks import check_lineage_metadata
from .spec_checks import (
    check_bidirectional_links,
    check_file_structure,
    check_spec_integrity,
)
from .text_pattern_checks import (
    check_debug_statements,
    check_hardcoded_secrets,
    check_todo_comments,
)

# Registry of built-in checks
BUILTIN_CHECKS = {
    # Text patterns
    "todo_comments": check_todo_comments,
    "debug_statements": check_debug_statements,
    "hardcoded_secrets": check_hardcoded_secrets,

    # File operations
    "file_size": check_file_size,
    "line_length": check_line_length,
    "trailing_whitespace": check_trailing_whitespace,
    "mixed_line_endings": check_mixed_line_endings,

    # Architecture checks (AST-based)
    "layer_imports": check_layer_imports,
    "constructor_injection": check_constructor_injection,
    "domain_purity": check_domain_purity,
    "circular_imports": check_circular_imports,

    # Lineage/Audit trail
    "lineage_metadata": check_lineage_metadata,

    # Spec integrity and traceability
    "spec_integrity": check_spec_integrity,
    "bidirectional_links": check_bidirectional_links,
    "file_structure": check_file_structure,

    # Minimal Context Architecture
    "minimal_context_validation": check_minimal_context_validation,
}


def get_builtin_check(name: str):
    """Get a built-in check function by name."""
    return BUILTIN_CHECKS.get(name)


def list_builtin_checks() -> list[str]:
    """List all available built-in checks."""
    return list(BUILTIN_CHECKS.keys())
