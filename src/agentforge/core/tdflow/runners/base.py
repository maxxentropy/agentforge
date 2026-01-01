# @spec_file: .agentforge/specs/core-tdflow-runners-v1.yaml
# @spec_id: core-tdflow-runners-v1
# @component_id: tdflow-runners-base
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

"""
Test Runner Base
================

Abstract base class for test runners.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agentforge.core.tdflow.domain import TestResult


class TestRunner(ABC):
    """
    Abstract test runner interface.

    Implementations handle specific frameworks (dotnet, pytest, etc.)
    """

    def __init__(self, project_path: Path):
        """
        Initialize test runner.

        Args:
            project_path: Root path of the project to test
        """
        self.project_path = project_path

    @abstractmethod
    def run_tests(self, filter_pattern: Optional[str] = None) -> "TestResult":
        """
        Run tests and return results.

        Args:
            filter_pattern: Optional filter to run specific tests

        Returns:
            TestResult with pass/fail counts
        """
        pass

    @abstractmethod
    def get_coverage(self) -> float:
        """
        Get test coverage percentage.

        Returns:
            Coverage percentage (0-100)
        """
        pass

    @abstractmethod
    def discover_tests(self) -> List[str]:
        """
        Discover available tests.

        Returns:
            List of test names/identifiers
        """
        pass

    @abstractmethod
    def build(self) -> bool:
        """
        Build the project before running tests.

        Returns:
            True if build succeeded
        """
        pass

    @classmethod
    def detect(cls, project_path: Path) -> "TestRunner":
        """
        Detect appropriate runner for project.

        Examines project files to determine framework.

        Args:
            project_path: Path to project root

        Returns:
            Appropriate TestRunner subclass instance

        Raises:
            ValueError: If no framework detected
        """
        from agentforge.core.tdflow.runners.dotnet import DotNetTestRunner
        from agentforge.core.tdflow.runners.pytest_runner import PytestRunner

        # Check for .NET (solution or project files)
        if list(project_path.glob("**/*.sln")) or list(project_path.glob("**/*.csproj")):
            return DotNetTestRunner(project_path)

        # Check for Python
        if (project_path / "pyproject.toml").exists():
            return PytestRunner(project_path)
        if (project_path / "pytest.ini").exists():
            return PytestRunner(project_path)
        if (project_path / "setup.py").exists():
            return PytestRunner(project_path)
        if list(project_path.glob("**/test_*.py")):
            return PytestRunner(project_path)

        raise ValueError(f"Cannot detect test framework for {project_path}")

    @classmethod
    def for_framework(cls, framework: str, project_path: Path) -> "TestRunner":
        """
        Get runner for specified framework.

        Args:
            framework: Framework name (xunit, nunit, pytest, jest)
            project_path: Path to project root

        Returns:
            Appropriate TestRunner instance

        Raises:
            ValueError: If framework not supported
        """
        from agentforge.core.tdflow.runners.dotnet import DotNetTestRunner
        from agentforge.core.tdflow.runners.pytest_runner import PytestRunner

        framework_map = {
            "xunit": DotNetTestRunner,
            "nunit": DotNetTestRunner,
            "mstest": DotNetTestRunner,
            "pytest": PytestRunner,
        }

        runner_cls = framework_map.get(framework.lower())
        if not runner_cls:
            raise ValueError(f"Unsupported framework: {framework}")

        return runner_cls(project_path)
