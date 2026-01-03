"""Tests for pytest runner."""

import tempfile
from pathlib import Path

import pytest

from agentforge.core.tdflow.runners.pytest_runner import PytestRunner


class TestPytestRunner:
    """Tests for PytestRunner."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create a minimal pyproject.toml
            (project_path / "pyproject.toml").write_text(
                """[project]
name = "test-project"
version = "0.1.0"
"""
            )
            yield project_path

    @pytest.fixture
    def runner(self, temp_project: Path) -> PytestRunner:
        """Create a test runner."""
        return PytestRunner(temp_project)

    def test_parse_output_success(self, runner: PytestRunner):
        """Parse output correctly identifies passed tests."""
        output = """
============================= test session starts ==============================
collected 5 items

test_example.py .....                                                    [100%]

============================== 5 passed in 0.12s ===============================
"""
        result = runner._parse_output(output, 0)

        assert result.total == 5, "Expected result.total to equal 5"
        assert result.passed == 5, "Expected result.passed to equal 5"
        assert result.failed == 0, "Expected result.failed to equal 0"
        assert result.duration_seconds == 0.12, "Expected result.duration_seconds to equal 0.12"

    def test_parse_output_failures(self, runner: PytestRunner):
        """Parse output correctly identifies failed tests."""
        output = """
============================= test session starts ==============================
collected 5 items

test_example.py ...FF                                                    [100%]

=========================== 3 passed, 2 failed in 0.56s ========================
"""
        result = runner._parse_output(output, 1)

        assert result.total == 5, "Expected result.total to equal 5"
        assert result.passed == 3, "Expected result.passed to equal 3"
        assert result.failed == 2, "Expected result.failed to equal 2"
        assert result.duration_seconds == 0.56, "Expected result.duration_seconds to equal 0.56"

    def test_parse_output_with_errors(self, runner: PytestRunner):
        """Parse output handles errors."""
        output = """
============================= test session starts ==============================
collected 5 items

============================== 3 passed, 1 failed, 1 error in 1.23s ============
"""
        result = runner._parse_output(output, 1)

        assert result.passed == 3, "Expected result.passed to equal 3"
        assert result.failed == 1, "Expected result.failed to equal 1"
        assert result.errors == 1, "Expected result.errors to equal 1"

    def test_parse_output_with_skipped(self, runner: PytestRunner):
        """Parse output handles skipped tests."""
        output = """
============================= test session starts ==============================
collected 5 items

============================= 3 passed, 2 skipped in 0.45s =====================
"""
        result = runner._parse_output(output, 0)

        assert result.total == 5, "Expected result.total to equal 5"
        assert result.passed == 3, "Expected result.passed to equal 3"

    def test_parse_verbose_output(self, runner: PytestRunner):
        """Parse verbose output with PASSED/FAILED markers."""
        output = """
test_example.py::test_one PASSED
test_example.py::test_two PASSED
test_example.py::test_three FAILED
test_example.py::test_four PASSED
"""
        result = runner._parse_output(output, 1)

        # Fallback parsing from verbose output
        assert result.passed == 3, "Expected result.passed to equal 3"
        assert result.failed == 1, "Expected result.failed to equal 1"


class TestTestRunnerDetection:
    """Tests for test runner auto-detection."""

    def test_detect_dotnet(self, tmp_path: Path):
        """Detect .NET project from csproj."""
        from agentforge.core.tdflow.runners.base import TestRunner

        (tmp_path / "Project.csproj").touch()

        runner = TestRunner.detect(tmp_path)

        from agentforge.core.tdflow.runners.dotnet import DotNetTestRunner

        assert isinstance(runner, DotNetTestRunner), "Expected isinstance() to be truthy"

    def test_detect_python(self, tmp_path: Path):
        """Detect Python project from pyproject.toml."""
        from agentforge.core.tdflow.runners.base import TestRunner

        (tmp_path / "pyproject.toml").touch()

        runner = TestRunner.detect(tmp_path)

        assert isinstance(runner, PytestRunner), "Expected isinstance() to be truthy"

    def test_detect_python_from_test_files(self, tmp_path: Path):
        """Detect Python project from test files."""
        from agentforge.core.tdflow.runners.base import TestRunner

        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_example.py").touch()

        runner = TestRunner.detect(tmp_path)

        assert isinstance(runner, PytestRunner), "Expected isinstance() to be truthy"

    def test_detect_fails_unknown(self, tmp_path: Path):
        """Detect fails for unknown project type."""
        from agentforge.core.tdflow.runners.base import TestRunner

        with pytest.raises(ValueError, match="Cannot detect"):
            TestRunner.detect(tmp_path)

    def test_for_framework(self, tmp_path: Path):
        """Get runner for specific framework."""
        from agentforge.core.tdflow.runners.base import TestRunner
        from agentforge.core.tdflow.runners.dotnet import DotNetTestRunner

        runner = TestRunner.for_framework("xunit", tmp_path)

        assert isinstance(runner, DotNetTestRunner), "Expected isinstance() to be truthy"

    def test_for_framework_pytest(self, tmp_path: Path):
        """Get runner for pytest framework."""
        from agentforge.core.tdflow.runners.base import TestRunner

        runner = TestRunner.for_framework("pytest", tmp_path)

        assert isinstance(runner, PytestRunner), "Expected isinstance() to be truthy"

    def test_for_framework_unsupported(self, tmp_path: Path):
        """Get runner fails for unsupported framework."""
        from agentforge.core.tdflow.runners.base import TestRunner

        with pytest.raises(ValueError, match="Unsupported framework"):
            TestRunner.for_framework("unknown", tmp_path)
