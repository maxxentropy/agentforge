# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-package
# @test_path: tests/unit/context/

"""
Context Management Package
==========================

Tools for managing agent context efficiently:
- AgentConfigLoader: Load and merge AGENT.md configuration hierarchy
- FingerprintGenerator: Generate compact project fingerprints (~500 tokens)
- Context Templates: Task-type specific context definitions

Usage:
    ```python
    from agentforge.core.context import (
        AgentConfigLoader,
        FingerprintGenerator,
        get_template_for_task,
    )

    # Load configuration
    config_loader = AgentConfigLoader(project_path)
    config = config_loader.load(task_type="fix_violation")

    # Generate fingerprint
    fingerprint_gen = FingerprintGenerator(project_path)
    fingerprint = fingerprint_gen.with_task_context(
        task_type="fix_violation",
        constraints={"correctness_first": True},
        success_criteria=["Tests pass"],
    )

    # Get template for task type
    template = get_template_for_task("fix_violation")
    context = template.build_context_dict(
        fingerprint=fingerprint,
        task_spec=task_spec,
        state_spec=state_spec,
        phase="analyze",
        precomputed={...},
        domain_context={...},
    )
    ```
"""

# Agent configuration
from .agent_config import (
    AgentConfig,
    AgentConfigLoader,
    AgentPreferences,
    ProjectConfig,
    TaskDefaults,
)

# Audit
from .audit import ContextAuditLogger

# Compaction
from .compaction import (
    CompactionAudit,
    CompactionManager,
    CompactionRule,
    CompactionStrategy,
)

# Project fingerprint
from .fingerprint import (
    DetectedPatterns,
    FingerprintGenerator,
    ProjectFingerprint,
    ProjectIdentity,
    ProjectStructure,
    TechnicalProfile,
)

# Context templates
from .templates import (
    BaseContextTemplate,
    CompactionLevel,
    ContextSection,
    FixViolationTemplate,
    ImplementFeatureTemplate,
    PhaseContextDef,
    TierDefinition,
    get_template_class,
    get_template_for_task,
    list_task_types,
    register_template,
)

__all__ = [
    # Agent config
    "AgentConfig",
    "AgentConfigLoader",
    "AgentPreferences",
    "ProjectConfig",
    "TaskDefaults",
    # Fingerprint
    "FingerprintGenerator",
    "ProjectFingerprint",
    "ProjectIdentity",
    "TechnicalProfile",
    "DetectedPatterns",
    "ProjectStructure",
    # Templates
    "BaseContextTemplate",
    "FixViolationTemplate",
    "ImplementFeatureTemplate",
    "CompactionLevel",
    "ContextSection",
    "TierDefinition",
    "PhaseContextDef",
    "get_template_for_task",
    "get_template_class",
    "register_template",
    "list_task_types",
    # Compaction
    "CompactionManager",
    "CompactionRule",
    "CompactionStrategy",
    "CompactionAudit",
    # Audit
    "ContextAuditLogger",
]
