# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-verification-reports

"""
Tests for verification report generation.

Tests the ReportGenerator class for formatting verification results
in text, YAML, and JSON formats.
"""

import json

import pytest
import yaml

from agentforge.core.verification_reports import ReportGenerator
from agentforge.core.verification_types import (
    CheckResult,
    CheckStatus,
    Severity,
    VerificationReport,
)


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a ReportGenerator instance."""
        return ReportGenerator()

    @pytest.fixture
    def sample_check_result(self):
        """Create a sample check result."""
        return CheckResult(
            check_id="test-001",
            check_name="Test Check",
            status=CheckStatus.PASSED,
            severity=Severity.REQUIRED,
            message="Check passed successfully",
            duration_ms=100,
        )

    @pytest.fixture
    def sample_failed_result(self):
        """Create a sample failed check result."""
        return CheckResult(
            check_id="test-002",
            check_name="Failed Check",
            status=CheckStatus.FAILED,
            severity=Severity.BLOCKING,
            message="Check failed",
            duration_ms=50,
            details="Detailed failure information",
            errors=[{"file": "test.py", "line": 10, "message": "Error here"}],
            fix_suggestion="Fix this by doing X",
        )

    @pytest.fixture
    def sample_report(self, sample_check_result, sample_failed_result):
        """Create a sample verification report."""
        return VerificationReport(
            timestamp="2026-01-02T12:00:00",
            profile="test-profile",
            project_path="/path/to/project",
            working_dir="/path/to/working",
            total_checks=2,
            passed=1,
            failed=1,
            skipped=0,
            errors=0,
            blocking_failures=1,
            required_failures=0,
            advisory_warnings=0,
            duration_ms=150,
            results=[sample_check_result, sample_failed_result],
            is_valid=False,
        )


class TestGenerateReport:
    """Tests for generate_report method."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def sample_report(self):
        return VerificationReport(
            timestamp="2026-01-02T12:00:00",
            profile="test-profile",
            project_path="/path/to/project",
            working_dir="/path/to/working",
            total_checks=1,
            passed=1,
            failed=0,
            skipped=0,
            errors=0,
            blocking_failures=0,
            required_failures=0,
            advisory_warnings=0,
            duration_ms=100,
            results=[
                CheckResult(
                    check_id="test-001",
                    check_name="Test Check",
                    status=CheckStatus.PASSED,
                    severity=Severity.REQUIRED,
                    message="Check passed",
                    duration_ms=100,
                )
            ],
            is_valid=True,
        )

    def test_generate_text_report_default(self, generator, sample_report):
        """Should generate text report by default."""
        report = generator.generate_report(sample_report)

        assert "VERIFICATION REPORT" in report, "Expected 'VERIFICATION REPORT' in report"
        assert "SUMMARY" in report, "Expected 'SUMMARY' in report"
        assert "Total Checks:" in report, "Expected 'Total Checks:' in report"
        assert "VERDICT: PASS" in report, "Expected 'VERDICT: PASS' in report"

    def test_generate_text_report_explicit(self, generator, sample_report):
        """Should generate text report when format='text'."""
        report = generator.generate_report(sample_report, format="text")

        assert "VERIFICATION REPORT" in report, "Expected 'VERIFICATION REPORT' in report"
        assert "DETAILED RESULTS" in report, "Expected 'DETAILED RESULTS' in report"

    def test_generate_yaml_report(self, generator, sample_report):
        """Should generate valid YAML report."""
        report = generator.generate_report(sample_report, format="yaml")

        # Should be valid YAML
        data = yaml.safe_load(report)
        assert "verification_report" in data, "Expected 'verification_report' in data"
        assert data["verification_report"]["summary"]["total_checks"] == 1, "Expected data['verification_report']... to equal 1"
        assert data["verification_report"]["summary"]["is_valid"] is True, "Expected data['verification_report']... is True"

    def test_generate_json_report(self, generator, sample_report):
        """Should generate valid JSON report."""
        report = generator.generate_report(sample_report, format="json")

        # Should be valid JSON
        data = json.loads(report)
        assert "verification_report" in data, "Expected 'verification_report' in data"
        assert data["verification_report"]["summary"]["total_checks"] == 1, "Expected data['verification_report']... to equal 1"
        assert data["verification_report"]["summary"]["is_valid"] is True, "Expected data['verification_report']... is True"


class TestFormatCheckResult:
    """Tests for _format_check_result method."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_format_passed_check(self, generator):
        """Should format passed check with checkmark."""
        result = CheckResult(
            check_id="test-001",
            check_name="Test Check",
            status=CheckStatus.PASSED,
            severity=Severity.REQUIRED,
            message="Check passed",
            duration_ms=50,
        )

        lines = generator._format_check_result(result)

        assert any("✓" in line for line in lines), "Expected any() to be truthy"
        assert any("test-001" in line for line in lines), "Expected any() to be truthy"
        assert any("REQUIRED" in line for line in lines), "Expected any() to be truthy"

    def test_format_failed_check(self, generator):
        """Should format failed check with X mark."""
        result = CheckResult(
            check_id="test-002",
            check_name="Failed Check",
            status=CheckStatus.FAILED,
            severity=Severity.BLOCKING,
            message="Check failed",
            duration_ms=50,
        )

        lines = generator._format_check_result(result)

        assert any("✗" in line for line in lines), "Expected any() to be truthy"
        assert any("BLOCKING" in line for line in lines), "Expected any() to be truthy"

    def test_format_check_with_details(self, generator):
        """Should include details when present."""
        result = CheckResult(
            check_id="test-001",
            check_name="Test Check",
            status=CheckStatus.FAILED,
            severity=Severity.REQUIRED,
            message="Check failed",
            details="More information here",
            duration_ms=50,
        )

        lines = generator._format_check_result(result)

        assert any("Details:" in line for line in lines), "Expected any() to be truthy"
        assert any("More information here" in line for line in lines), "Expected any() to be truthy"

    def test_format_check_with_fix_suggestion(self, generator):
        """Should include fix suggestion for failed checks."""
        result = CheckResult(
            check_id="test-001",
            check_name="Test Check",
            status=CheckStatus.FAILED,
            severity=Severity.REQUIRED,
            message="Check failed",
            fix_suggestion="Try doing X instead",
            duration_ms=50,
        )

        lines = generator._format_check_result(result)

        assert any("Fix:" in line for line in lines), "Expected any() to be truthy"
        assert any("Try doing X instead" in line for line in lines), "Expected any() to be truthy"

    def test_format_check_with_duration(self, generator):
        """Should include duration when non-zero."""
        result = CheckResult(
            check_id="test-001",
            check_name="Test Check",
            status=CheckStatus.PASSED,
            severity=Severity.REQUIRED,
            message="Check passed",
            duration_ms=123,
        )

        lines = generator._format_check_result(result)

        assert any("Duration: 123ms" in line for line in lines), "Expected any() to be truthy"

    def test_format_skipped_check(self, generator):
        """Should format skipped check with circle."""
        result = CheckResult(
            check_id="test-001",
            check_name="Skipped Check",
            status=CheckStatus.SKIPPED,
            severity=Severity.ADVISORY,
            message="Check skipped",
            duration_ms=0,
        )

        lines = generator._format_check_result(result)

        assert any("○" in line for line in lines), "Expected any() to be truthy"


class TestFormatErrorsSection:
    """Tests for _format_errors_section method."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_format_single_error(self, generator):
        """Should format a single error."""
        errors = [{"file": "test.py", "line": 10, "message": "Error"}]

        lines = generator._format_errors_section(errors)

        assert lines[0] == "  Errors (1):", "Expected lines[0] to equal '  Errors (1):'"
        assert any("test.py" in line for line in lines), "Expected any() to be truthy"

    def test_format_multiple_errors(self, generator):
        """Should format multiple errors."""
        errors = [
            {"file": "a.py", "message": "Error A"},
            {"file": "b.py", "message": "Error B"},
        ]

        lines = generator._format_errors_section(errors)

        assert lines[0] == "  Errors (2):", "Expected lines[0] to equal '  Errors (2):'"
        assert any("a.py" in line for line in lines), "Expected any() to be truthy"
        assert any("b.py" in line for line in lines), "Expected any() to be truthy"

    def test_format_errors_truncates_at_five(self, generator):
        """Should truncate after 5 errors with count."""
        errors = [{"file": f"file{i}.py"} for i in range(10)]

        lines = generator._format_errors_section(errors)

        assert lines[0] == "  Errors (10):", "Expected lines[0] to equal '  Errors (10):'"
        assert any("and 5 more" in line for line in lines), "Expected any() to be truthy"

    def test_format_string_errors(self, generator):
        """Should handle string errors (not dicts)."""
        errors = ["Error message 1", "Error message 2"]

        lines = generator._format_errors_section(errors)

        assert any("Error message 1" in line for line in lines), "Expected any() to be truthy"
        assert any("Error message 2" in line for line in lines), "Expected any() to be truthy"


class TestBuildReportData:
    """Tests for _build_report_data method."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_build_report_data_structure(self, generator):
        """Should build correct data structure."""
        report = VerificationReport(
            timestamp="2026-01-02T12:00:00",
            profile="test-profile",
            project_path="/path/to/project",
            working_dir="/working",
            total_checks=1,
            passed=1,
            failed=0,
            skipped=0,
            errors=0,
            blocking_failures=0,
            required_failures=0,
            advisory_warnings=0,
            duration_ms=100,
            results=[],
            is_valid=True,
        )

        data = generator._build_report_data(report)

        assert "verification_report" in data, "Expected 'verification_report' in data"
        vr = data["verification_report"]
        assert vr["timestamp"] == "2026-01-02T12:00:00", "Expected vr['timestamp'] to equal '2026-01-02T12:00:00'"
        assert vr["profile"] == "test-profile", "Expected vr['profile'] to equal 'test-profile'"
        assert vr["summary"]["total_checks"] == 1, "Expected vr['summary']['total_checks'] to equal 1"
        assert vr["summary"]["is_valid"] is True, "Expected vr['summary']['is_valid'] is True"

    def test_build_report_data_with_results(self, generator):
        """Should include check results in data."""
        result = CheckResult(
            check_id="test-001",
            check_name="Test Check",
            status=CheckStatus.PASSED,
            severity=Severity.REQUIRED,
            message="Passed",
            duration_ms=50,
        )
        report = VerificationReport(
            timestamp="2026-01-02T12:00:00",
            profile=None,
            project_path=None,
            working_dir="/working",
            total_checks=1,
            passed=1,
            failed=0,
            skipped=0,
            errors=0,
            blocking_failures=0,
            required_failures=0,
            advisory_warnings=0,
            duration_ms=50,
            results=[result],
            is_valid=True,
        )

        data = generator._build_report_data(report)

        results = data["verification_report"]["results"]
        assert len(results) == 1, "Expected len(results) to equal 1"
        assert results[0]["check_id"] == "test-001", "Expected results[0]['check_id'] to equal 'test-001'"
        assert results[0]["status"] == "passed", "Expected results[0]['status'] to equal 'passed'"
        assert results[0]["severity"] == "required", "Expected results[0]['severity'] to equal 'required'"
