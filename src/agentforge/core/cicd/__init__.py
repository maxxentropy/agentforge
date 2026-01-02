"""
CI/CD Integration Module
========================

Enables automated conformance checking in CI/CD pipelines with:
- Baseline-based PR checking (new vs existing violations)
- Multiple output formats (SARIF, JUnit, Markdown)
- Parallel check execution for performance
- Incremental checking for PRs
- Platform integrations (GitHub Actions, Azure DevOps)
"""

from agentforge.core.cicd.baseline import BaselineError, BaselineManager, GitError, GitHelper
from agentforge.core.cicd.domain import (
    Baseline,
    BaselineComparison,
    BaselineEntry,
    CIConfig,
    CIMode,
    CIResult,
    CIViolation,
    ExitCode,
)
from agentforge.core.cicd.runner import CheckCache, CIRunner

__all__ = [
    # Domain
    "CIMode",
    "ExitCode",
    "CIViolation",
    "BaselineEntry",
    "Baseline",
    "BaselineComparison",
    "CIResult",
    "CIConfig",
    # Baseline
    "BaselineManager",
    "GitHelper",
    "BaselineError",
    "GitError",
    # Runner
    "CIRunner",
    "CheckCache",
]
