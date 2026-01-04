# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-builtin_checks
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
Built-in check implementations for AgentForge contracts.

These functions provide reusable checks that can be invoked from contracts
using the 'custom' check type. They are specifically designed for tasks
that cannot be done via LSP (text patterns, file operations, etc.).

NOTE: For semantic code analysis (public fields, method naming, etc.),
use `lsp_query` check type instead - it leverages our LSP adapters for
accurate, parser-based analysis.

Each function follows the signature:
    func(repo_root: Path, file_paths: List[Path], **params) -> List[Dict]

Return format:
    [
        {
            "message": "Description of the violation",
            "file": "relative/path/to/file.cs",
            "line": 42,
            "severity": "error",  # Optional, defaults to check's severity
            "fix_hint": "How to fix this"  # Optional
        }
    ]
"""

# Architecture checks
from .architecture_checks import (
    check_circular_imports,
    check_constructor_injection,
    check_domain_purity,
    check_layer_imports,
    check_minimal_context_validation,
)

# File checks
from .file_checks import (
    check_file_size,
    check_line_length,
    check_mixed_line_endings,
    check_trailing_whitespace,
)

# Lineage checks
from .lineage_checks import check_lineage_metadata

# Registry
from .registry import (
    BUILTIN_CHECKS,
    get_builtin_check,
    list_builtin_checks,
)

# Spec checks
from .spec_checks import (
    check_bidirectional_links,
    check_file_structure,
    check_spec_integrity,
)

# Text pattern checks
from .text_pattern_checks import (
    check_debug_statements,
    check_hardcoded_secrets,
    check_todo_comments,
)

__all__ = [
    # Registry
    "BUILTIN_CHECKS",
    "get_builtin_check",
    "list_builtin_checks",
    # Text patterns
    "check_todo_comments",
    "check_debug_statements",
    "check_hardcoded_secrets",
    # File operations
    "check_file_size",
    "check_line_length",
    "check_trailing_whitespace",
    "check_mixed_line_endings",
    # Architecture
    "check_layer_imports",
    "check_constructor_injection",
    "check_domain_purity",
    "check_circular_imports",
    "check_minimal_context_validation",
    # Lineage
    "check_lineage_metadata",
    # Spec integrity
    "check_spec_integrity",
    "check_bidirectional_links",
    "check_file_structure",
]
