# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow

"""
Fix Workflow Package
====================

Modular implementation of the minimal context fix workflow.

This package decomposes the fix workflow into focused mixins:
- ActionsMixin: File operations (read, edit, replace, insert, write)
- TestingMixin: Test verification and auto-revert
- ValidationMixin: Python file validation (syntax, imports)
- ContextMixin: Context pre-computation using AST analysis

The main class (MinimalContextFixWorkflow) inherits from all mixins,
combining their capabilities while keeping code organized.

Backward Compatibility
----------------------
This package maintains the same public API as the original module.
Existing imports work unchanged:

    from .fix_workflow import MinimalContextFixWorkflow
    from .fix_workflow import create_minimal_fix_workflow
"""

from .base import MinimalContextFixWorkflow, create_minimal_fix_workflow

__all__ = [
    "MinimalContextFixWorkflow",
    "create_minimal_fix_workflow",
]
