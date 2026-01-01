# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-template-registry
# @test_path: tests/unit/context/test_templates.py

"""
Context Template Registry
=========================

Registry for context templates that map task types to their
phase-specific context definitions.

Usage:
    ```python
    from agentforge.core.context.templates import get_template_for_task

    # Get template for a task type
    template = get_template_for_task("fix_violation")

    # Build context for a phase
    context = template.build_context_dict(
        fingerprint=fingerprint,
        task_spec=task_spec,
        state_spec=state_spec,
        phase="analyze",
        precomputed={...},
        domain_context={...},
    )

    # List available task types
    from agentforge.core.context.templates import list_task_types
    types = list_task_types()  # ["fix_violation", "implement_feature"]
    ```

Extending:
    ```python
    from agentforge.core.context.templates import register_template
    from agentforge.core.context.templates.base import BaseContextTemplate

    class MyCustomTemplate(BaseContextTemplate):
        ...

    register_template("my_custom_task", MyCustomTemplate)
    ```
"""

from typing import Dict, List, Type

from .base import BaseContextTemplate
from .bridge import BridgeTemplate
from .code_review import CodeReviewTemplate
from .discovery import DiscoveryTemplate
from .fix_violation import FixViolationTemplate
from .implement_feature import ImplementFeatureTemplate
from .models import (
    CompactionLevel,
    ContextSection,
    PhaseContextDef,
    TierDefinition,
)
from .refactor import RefactorTemplate
from .write_tests import WriteTestsTemplate

# Registry of all templates
_TEMPLATE_REGISTRY: Dict[str, Type[BaseContextTemplate]] = {
    "fix_violation": FixViolationTemplate,
    "implement_feature": ImplementFeatureTemplate,
    "write_tests": WriteTestsTemplate,
    "discovery": DiscoveryTemplate,
    "bridge": BridgeTemplate,
    "code_review": CodeReviewTemplate,
    "refactor": RefactorTemplate,
}


def get_template_for_task(task_type: str) -> BaseContextTemplate:
    """
    Get the appropriate template for a task type.

    Args:
        task_type: The type of task (e.g., "fix_violation", "implement_feature")

    Returns:
        Instantiated template for the task type

    Raises:
        ValueError: If task type is not registered

    Example:
        >>> template = get_template_for_task("fix_violation")
        >>> template.task_type
        'fix_violation'
    """
    if task_type not in _TEMPLATE_REGISTRY:
        available = ", ".join(sorted(_TEMPLATE_REGISTRY.keys()))
        raise ValueError(f"Unknown task type: {task_type}. Available: {available}")

    return _TEMPLATE_REGISTRY[task_type]()


def register_template(
    task_type: str, template_class: Type[BaseContextTemplate]
) -> None:
    """
    Register a new template type.

    Allows extensions to add custom task types without modifying
    the core registry.

    Args:
        task_type: Unique identifier for this task type
        template_class: Template class (must extend BaseContextTemplate)

    Example:
        >>> class MyTemplate(BaseContextTemplate):
        ...     @property
        ...     def task_type(self) -> str:
        ...         return "my_task"
        ...     # ... implement other abstract methods
        >>> register_template("my_task", MyTemplate)
    """
    _TEMPLATE_REGISTRY[task_type] = template_class


def list_task_types() -> List[str]:
    """
    List all registered task types.

    Returns:
        Sorted list of task type identifiers

    Example:
        >>> list_task_types()
        ['fix_violation', 'implement_feature']
    """
    return sorted(_TEMPLATE_REGISTRY.keys())


def get_template_class(task_type: str) -> Type[BaseContextTemplate]:
    """
    Get the template class (not instance) for a task type.

    Useful for introspection or subclassing.

    Args:
        task_type: The type of task

    Returns:
        Template class

    Raises:
        ValueError: If task type is not registered
    """
    if task_type not in _TEMPLATE_REGISTRY:
        available = ", ".join(sorted(_TEMPLATE_REGISTRY.keys()))
        raise ValueError(f"Unknown task type: {task_type}. Available: {available}")

    return _TEMPLATE_REGISTRY[task_type]


# Public API
__all__ = [
    # Registry functions
    "get_template_for_task",
    "register_template",
    "list_task_types",
    "get_template_class",
    # Base class for extension
    "BaseContextTemplate",
    # Concrete templates
    "FixViolationTemplate",
    "ImplementFeatureTemplate",
    "WriteTestsTemplate",
    "DiscoveryTemplate",
    "BridgeTemplate",
    "CodeReviewTemplate",
    "RefactorTemplate",
    # Models
    "CompactionLevel",
    "ContextSection",
    "TierDefinition",
    "PhaseContextDef",
]
