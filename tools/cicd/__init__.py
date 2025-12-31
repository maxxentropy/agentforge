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

from tools.cicd.domain import (
    CIMode,
    ExitCode,
    CIViolation,
    BaselineEntry,
    Baseline,
    BaselineComparison,
    CIResult,
    CIConfig,
)
from tools.cicd.baseline import BaselineManager, GitHelper, BaselineError, GitError
from tools.cicd.runner import CIRunner, CheckCache

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
