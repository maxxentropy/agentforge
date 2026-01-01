# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-package
# @test_path: tests/unit/context/test_package.py

"""
Context Management Package
==========================

Tools for managing agent context efficiently:
- AgentConfigLoader: Load and merge AGENT.md configuration hierarchy
- FingerprintGenerator: Generate compact project fingerprints (~500 tokens)

Usage:
    ```python
    from agentforge.core.context import AgentConfigLoader, FingerprintGenerator

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

    # Get compact YAML for LLM context
    context_yaml = fingerprint.to_context_yaml()
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

# Project fingerprint
from .fingerprint import (
    DetectedPatterns,
    FingerprintGenerator,
    ProjectFingerprint,
    ProjectIdentity,
    ProjectStructure,
    TechnicalProfile,
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
]
