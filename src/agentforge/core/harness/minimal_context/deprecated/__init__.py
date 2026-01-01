# @spec_file: specs/minimal-context-architecture/08-migration.yaml
# @spec_id: migration-v1
# @component_id: deprecated-module

"""
Deprecated Minimal Context Components
=====================================

DEPRECATION NOTICE: These modules are deprecated and will be removed in a future version.

The unified architecture (MinimalContextExecutor) should be used instead:
- Use TemplateContextBuilder instead of EnhancedContextBuilder or ContextBuilder
- Use core.context.compaction instead of token_budget
- Use core.context.templates instead of context_schemas

These files are kept for backwards compatibility with code that still imports
from the legacy modules. New code should NOT import from this package.

Migration Guide:
    # OLD (deprecated)
    from .context_builder import ContextBuilder
    from .enhanced_context_builder import EnhancedContextBuilder
    from .context_schemas import FixViolationSchema

    # NEW (use these instead)
    from .template_context_builder import TemplateContextBuilder
    from ...context.templates import get_template_for_task
"""

import warnings

# Emit deprecation warning when this module is imported
warnings.warn(
    "agentforge.core.harness.minimal_context.deprecated is deprecated. "
    "Use MinimalContextExecutor with TemplateContextBuilder instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export legacy components for backwards compatibility
from .token_budget import (
    TokenBudget,
    TOKEN_BUDGET_LIMITS,
    ENHANCED_TOKEN_LIMITS,
    estimate_tokens,
    compress_file_content,
)
from .context_schemas import (
    ContextSchema,
    FixViolationSchema,
    get_schema_for_task,
)
from .context_builder import (
    ContextBuilder,
    create_context_builder,
)
from .enhanced_context_builder import (
    EnhancedContextBuilder,
    create_enhanced_context_builder,
)

__all__ = [
    # Token Budget (deprecated)
    "TokenBudget",
    "TOKEN_BUDGET_LIMITS",
    "ENHANCED_TOKEN_LIMITS",
    "estimate_tokens",
    "compress_file_content",
    # Context Schemas (deprecated)
    "ContextSchema",
    "FixViolationSchema",
    "get_schema_for_task",
    # Context Builders (deprecated)
    "ContextBuilder",
    "create_context_builder",
    "EnhancedContextBuilder",
    "create_enhanced_context_builder",
]
