"""Tests for DotNet test runner."""

import pytest
import tempfile
from pathlib import Path

from tools.tdflow.runners.dotnet import DotNetTestRunner
from tools.tdflow.domain import TestResult


class TestDotNetTestRunner:
    """Tests for DotNetTestRunner."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create a minimal csproj file
            (project_path / "Test.csproj").write_text(
                """<Project Sdk="Microsoft.NET.Sdk">
                <PropertyGroup>
                    <TargetFramework>net8.0</TargetFramework>
                </PropertyGroup>
            </Project>"""
            )
            yield project_path

    @pytest.fixture
    def runner(self, temp_project: Path) -> DotNetTestRunner:
        """Create a test runner."""
        return DotNetTestRunner(temp_project)

    def test_parse_output_success(self, runner: DotNetTestRunner):
        """Parse output correctly identifies passed tests."""
        output = """
Starting test execution, please wait...
A total of 1 test files matched the specified pattern.

Passed!  - Failed:     0, Passed:     5, Skipped:     0, Total:     5, Duration: 123 ms
"""
        result = runner._parse_output(output, 0)

        assert result.total == 5
        assert result.passed == 5
        assert result.failed == 0
        assert result.errors == 0

    def test_parse_output_failures(self, runner: DotNetTestRunner):
        """Parse output correctly identifies failed tests."""
        output = """
Starting test execution, please wait...
A total of 1 test files matched the specified pattern.

Failed!  - Failed:     2, Passed:     3, Skipped:     0, Total:     5, Duration: 456 ms
"""
        result = runner._parse_output(output, 1)

        assert result.total == 5
        assert result.passed == 3
        assert result.failed == 2
        assert result.errors == 0

    def test_parse_output_with_duration(self, runner: DotNetTestRunner):
        """Parse output extracts duration."""
        output = """
Passed!  - Failed:     0, Passed:     3, Skipped:     0, Total:     3
Duration: 1.234 s
"""
        result = runner._parse_output(output, 0)

        assert result.duration_seconds == 1.234

    def test_parse_output_no_tests(self, runner: DotNetTestRunner):
        """Parse output handles no tests found."""
        output = """
No test matches the given testcase filter
"""
        result = runner._parse_output(output, 0)

        assert result.total == 0
        assert result.passed == 0
        assert result.failed == 0


class TestTestResultProperties:
    """Tests for TestResult property calculations."""

    def test_all_passed_true(self):
        """All passed when all tests pass."""
        result = TestResult(
            total=5, passed=5, failed=0, errors=0, duration_seconds=1.0, output=""
        )
        assert result.all_passed is True
        assert result.all_failed is False

    def test_all_failed_true(self):
        """All failed when no tests pass."""
        result = TestResult(
            total=5, passed=0, failed=5, errors=0, duration_seconds=1.0, output=""
        )
        assert result.all_failed is True
        assert result.all_passed is False

    def test_partial_pass(self):
        """Partial pass neither all passed nor all failed."""
        result = TestResult(
            total=5, passed=3, failed=2, errors=0, duration_seconds=1.0, output=""
        )
        assert result.all_passed is False
        assert result.all_failed is False
