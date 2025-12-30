"""Tests for VerificationRunner class."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml
import sys

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'tools'))

from verification_runner import VerificationRunner
from verification_types import CheckResult, CheckStatus, Severity, VerificationReport


class TestVerificationRunnerInit:
    """Tests for VerificationRunner initialization."""

    def test_init_with_default_config(self, tmp_path: Path):
        """Test initialization with default config path."""
        runner = VerificationRunner(project_root=tmp_path)

        assert runner.project_root == tmp_path
        assert runner.config_path == tmp_path / "config" / "correctness.yaml"
        assert runner.config == {"checks": [], "profiles": {}, "settings": {}}

    def test_init_with_custom_config(self, tmp_path: Path, correctness_config: dict):
        """Test initialization with custom config file."""
        config_path = tmp_path / "custom.yaml"
        config_path.write_text(yaml.dump(correctness_config))

        runner = VerificationRunner(config_path=config_path, project_root=tmp_path)

        assert runner.config_path == config_path
        assert runner.config == correctness_config
        assert len(runner.config["checks"]) == 4

    def test_init_missing_config_returns_empty(self, tmp_path: Path):
        """Test initialization with missing config returns empty structure."""
        runner = VerificationRunner(
            config_path=tmp_path / "nonexistent.yaml",
            project_root=tmp_path
        )

        assert runner.config == {"checks": [], "profiles": {}, "settings": {}}

    def test_lazy_load_pyright_runner(self, tmp_path: Path):
        """Test pyright runner is lazily loaded."""
        runner = VerificationRunner(project_root=tmp_path)

        # Not loaded initially
        assert runner._pyright_runner is None

        # Loaded on first access
        pyright = runner.pyright_runner
        assert pyright is not None
        assert runner._pyright_runner is not None

        # Same instance returned
        assert runner.pyright_runner is pyright

    def test_lazy_load_command_runner(self, tmp_path: Path):
        """Test command runner is lazily loaded."""
        runner = VerificationRunner(project_root=tmp_path)

        assert runner._command_runner is None
        command = runner.command_runner
        assert command is not None
        assert runner.command_runner is command

    def test_lazy_load_ast_checker(self, tmp_path: Path):
        """Test AST checker is lazily loaded."""
        runner = VerificationRunner(project_root=tmp_path)

        assert runner._ast_checker is None
        ast = runner.ast_checker
        assert ast is not None
        assert runner.ast_checker is ast


class TestVariableSubstitution:
    """Tests for variable substitution in templates."""

    def test_substitute_single_variable(self, tmp_path: Path):
        """Test substitution of a single variable."""
        runner = VerificationRunner(project_root=tmp_path)
        runner.set_context(project_path="/path/to/project")

        result = runner._substitute_variables("Build {project_path}")
        assert result == "Build /path/to/project"

    def test_substitute_multiple_variables(self, tmp_path: Path):
        """Test substitution of multiple variables."""
        runner = VerificationRunner(project_root=tmp_path)
        runner.set_context(name="test", version="1.0")

        result = runner._substitute_variables("{name} v{version}")
        assert result == "test v1.0"

    def test_substitute_no_variables(self, tmp_path: Path):
        """Test string without variables is unchanged."""
        runner = VerificationRunner(project_root=tmp_path)

        result = runner._substitute_variables("plain text")
        assert result == "plain text"

    def test_substitute_missing_variable_unchanged(self, tmp_path: Path):
        """Test missing variables are left as placeholders."""
        runner = VerificationRunner(project_root=tmp_path)

        result = runner._substitute_variables("Hello {missing}")
        assert result == "Hello {missing}"

    def test_substitute_none_returns_none(self, tmp_path: Path):
        """Test None input returns None."""
        runner = VerificationRunner(project_root=tmp_path)

        result = runner._substitute_variables(None)
        assert result is None

    def test_substitute_empty_string(self, tmp_path: Path):
        """Test empty string returns empty string."""
        runner = VerificationRunner(project_root=tmp_path)

        result = runner._substitute_variables("")
        assert result == ""


class TestProfileManagement:
    """Tests for profile and check management."""

    def test_get_checks_for_profile_quick(self, verification_runner):
        """Test getting checks for 'quick' profile."""
        checks = verification_runner.get_checks_for_profile("quick")

        assert len(checks) == 1
        assert checks[0]["id"] == "test_command_success"

    def test_get_checks_for_profile_full(self, verification_runner):
        """Test getting checks for 'full' profile."""
        checks = verification_runner.get_checks_for_profile("full")

        assert len(checks) == 3
        check_ids = [c["id"] for c in checks]
        assert "test_command_success" in check_ids
        assert "test_regex_match" in check_ids
        assert "test_file_exists" in check_ids

    def test_get_checks_for_unknown_profile_raises(self, verification_runner):
        """Test unknown profile raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            verification_runner.get_checks_for_profile("nonexistent")

        assert "Unknown profile" in str(exc_info.value)

    def test_get_checks_by_ids(self, verification_runner):
        """Test getting specific checks by ID."""
        checks = verification_runner.get_checks_by_ids(["test_command_success", "test_file_exists"])

        assert len(checks) == 2
        check_ids = [c["id"] for c in checks]
        assert "test_command_success" in check_ids
        assert "test_file_exists" in check_ids

    def test_get_checks_by_ids_missing_ignored(self, verification_runner):
        """Test missing check IDs are silently ignored."""
        checks = verification_runner.get_checks_by_ids(["test_command_success", "nonexistent"])

        assert len(checks) == 1
        assert checks[0]["id"] == "test_command_success"


class TestRunProfile:
    """Tests for running profiles."""

    def test_run_profile_returns_report(self, verification_runner):
        """Test run_profile returns VerificationReport."""
        with patch.object(verification_runner, 'run_check') as mock_run:
            mock_run.return_value = CheckResult(
                check_id="test", check_name="Test", status=CheckStatus.PASSED,
                severity=Severity.ADVISORY, message="Passed"
            )
            report = verification_runner.run_profile("quick")

        assert isinstance(report, VerificationReport)
        assert report.profile == "quick"
        assert report.total_checks == 1

    def test_run_profile_sets_timing(self, verification_runner):
        """Test run_profile sets duration_ms."""
        with patch.object(verification_runner, 'run_check') as mock_run:
            mock_run.return_value = CheckResult(
                check_id="test", check_name="Test", status=CheckStatus.PASSED,
                severity=Severity.ADVISORY, message="Passed"
            )
            report = verification_runner.run_profile("quick")

        assert report.duration_ms >= 0
        assert report.timestamp is not None


class TestRunChecks:
    """Tests for running checks."""

    def test_run_all_checks(self, verification_runner):
        """Test run_checks with all_checks=True."""
        with patch.object(verification_runner, 'run_check') as mock_run:
            mock_run.return_value = CheckResult(
                check_id="test", check_name="Test", status=CheckStatus.PASSED,
                severity=Severity.ADVISORY, message="Passed"
            )
            report = verification_runner.run_checks(all_checks=True)

        assert report.total_checks == 4  # All checks from fixture

    def test_run_specific_checks(self, verification_runner):
        """Test run_checks with specific check IDs."""
        with patch.object(verification_runner, 'run_check') as mock_run:
            mock_run.return_value = CheckResult(
                check_id="test", check_name="Test", status=CheckStatus.PASSED,
                severity=Severity.ADVISORY, message="Passed"
            )
            report = verification_runner.run_checks(check_ids=["test_command_success"])

        assert report.total_checks == 1


class TestDependencyOrdering:
    """Tests for check dependency ordering."""

    def test_depends_on_success_runs_dependent(self, verification_runner):
        """Test dependent check runs when dependency passes."""
        with patch.object(verification_runner, '_run_command_check') as mock_cmd:
            mock_cmd.return_value = CheckResult(
                check_id="test_command_success", check_name="Echo Test",
                status=CheckStatus.PASSED, severity=Severity.ADVISORY, message="Passed"
            )
            report = verification_runner.run_checks(
                check_ids=["test_command_success", "test_depends_on_success"]
            )

        # Both checks should have run
        assert len(report.results) == 2
        assert report.passed == 2

    def test_depends_on_failure_skips_dependent(self, tmp_path: Path):
        """Test dependent check is skipped when dependency fails."""
        config = {
            "checks": [
                {"id": "dep", "type": "command", "command": "false", "severity": "advisory"},
                {"id": "child", "type": "command", "command": "echo ok",
                 "depends_on": ["dep"], "severity": "advisory"}
            ],
            "profiles": {}
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))

        runner = VerificationRunner(config_path=config_path, project_root=tmp_path)

        with patch.object(runner, '_run_command_check') as mock_cmd:
            mock_cmd.return_value = CheckResult(
                check_id="dep", check_name="Dep",
                status=CheckStatus.FAILED, severity=Severity.ADVISORY, message="Failed"
            )
            report = runner.run_checks(all_checks=True)

        assert report.skipped >= 1
        skipped_result = [r for r in report.results if r.check_id == "child"][0]
        assert skipped_result.status == CheckStatus.SKIPPED
        assert "dependencies" in skipped_result.message.lower()


class TestFailFast:
    """Tests for fail-fast behavior."""

    def test_fail_fast_stops_on_blocking_failure(self, tmp_path: Path):
        """Test fail_fast stops execution on blocking failure."""
        config = {
            "settings": {"fail_fast": True},
            "checks": [
                {"id": "first", "type": "command", "command": "false", "severity": "blocking"},
                {"id": "second", "type": "command", "command": "echo ok", "severity": "advisory"}
            ],
            "profiles": {}
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))

        runner = VerificationRunner(config_path=config_path, project_root=tmp_path)

        with patch.object(runner, '_run_command_check') as mock_cmd:
            mock_cmd.return_value = CheckResult(
                check_id="first", check_name="First",
                status=CheckStatus.FAILED, severity=Severity.BLOCKING, message="Failed"
            )
            report = runner.run_checks(all_checks=True)

        assert report.failed == 1
        assert report.skipped >= 1
        assert not report.is_valid

    def test_no_fail_fast_continues_after_failure(self, tmp_path: Path):
        """Test execution continues when fail_fast is disabled."""
        config = {
            "settings": {"fail_fast": False},
            "checks": [
                {"id": "first", "type": "command", "command": "false", "severity": "blocking"},
                {"id": "second", "type": "command", "command": "echo ok", "severity": "advisory"}
            ],
            "profiles": {}
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))

        runner = VerificationRunner(config_path=config_path, project_root=tmp_path)

        call_count = [0]
        def mock_run_check(check, settings):
            call_count[0] += 1
            status = CheckStatus.FAILED if check["id"] == "first" else CheckStatus.PASSED
            return CheckResult(
                check_id=check["id"], check_name=check["id"],
                status=status, severity=Severity.BLOCKING, message="Test"
            )

        with patch.object(runner, '_run_command_check', side_effect=mock_run_check):
            report = runner.run_checks(all_checks=True)

        assert call_count[0] == 2  # Both checks ran


class TestRunCheck:
    """Tests for single check execution."""

    def test_run_check_dispatches_to_handler(self, verification_runner):
        """Test run_check dispatches to correct handler."""
        check = {"id": "test", "name": "Test", "type": "command", "command": "echo hi"}

        with patch.object(verification_runner, '_run_command_check') as mock_cmd:
            mock_cmd.return_value = CheckResult(
                check_id="test", check_name="Test",
                status=CheckStatus.PASSED, severity=Severity.ADVISORY, message="OK"
            )
            result = verification_runner.run_check(check, {})

        mock_cmd.assert_called_once()
        assert result.check_id == "test"

    def test_run_check_unknown_type_returns_error(self, verification_runner):
        """Test unknown check type returns ERROR status."""
        check = {"id": "test", "name": "Test", "type": "unknown_type"}

        result = verification_runner.run_check(check, {})

        assert result.status == CheckStatus.ERROR
        assert "Unknown check type" in result.message

    def test_run_check_exception_returns_error(self, verification_runner):
        """Test exception in handler returns ERROR status."""
        check = {"id": "test", "name": "Test", "type": "command", "command": "echo"}

        with patch.object(verification_runner, '_run_command_check') as mock_cmd:
            mock_cmd.side_effect = RuntimeError("Test exception")
            result = verification_runner.run_check(check, {})

        assert result.status == CheckStatus.ERROR
        assert "exception" in result.message.lower()

    def test_run_check_sets_duration(self, verification_runner):
        """Test run_check sets duration_ms."""
        check = {"id": "test", "name": "Test", "type": "command", "command": "echo"}

        with patch.object(verification_runner, '_run_command_check') as mock_cmd:
            mock_cmd.return_value = CheckResult(
                check_id="test", check_name="Test",
                status=CheckStatus.PASSED, severity=Severity.ADVISORY, message="OK"
            )
            result = verification_runner.run_check(check, {})

        assert result.duration_ms >= 0

    def test_run_check_sets_fix_suggestion(self, verification_runner):
        """Test run_check sets fix_suggestion from check config."""
        check = {
            "id": "test", "name": "Test", "type": "command",
            "command": "echo", "fix_suggestion": "Run the build"
        }

        with patch.object(verification_runner, '_run_command_check') as mock_cmd:
            mock_cmd.return_value = CheckResult(
                check_id="test", check_name="Test",
                status=CheckStatus.PASSED, severity=Severity.ADVISORY, message="OK"
            )
            result = verification_runner.run_check(check, {})

        assert result.fix_suggestion == "Run the build"


class TestReportGeneration:
    """Tests for report generation."""

    def test_report_summary_counts(self, verification_runner):
        """Test report correctly counts pass/fail/skip."""
        results = [
            CheckResult("c1", "C1", CheckStatus.PASSED, Severity.ADVISORY, "OK"),
            CheckResult("c2", "C2", CheckStatus.FAILED, Severity.ADVISORY, "Fail"),
            CheckResult("c3", "C3", CheckStatus.SKIPPED, Severity.ADVISORY, "Skip"),
            CheckResult("c4", "C4", CheckStatus.ERROR, Severity.ADVISORY, "Err"),
        ]

        report = VerificationReport(
            timestamp="2025-01-01T00:00:00Z", profile=None,
            project_path=None, working_dir=".", total_checks=4,
            passed=0, failed=0, skipped=0, errors=0,
            blocking_failures=0, required_failures=0, advisory_warnings=0, duration_ms=0
        )
        for r in results:
            report.add_result(r)

        assert report.passed == 1
        assert report.failed == 1
        assert report.skipped == 1
        assert report.errors == 1

    def test_report_blocking_failure_invalidates(self, verification_runner):
        """Test blocking failure sets is_valid to False."""
        report = VerificationReport(
            timestamp="2025-01-01T00:00:00Z", profile=None,
            project_path=None, working_dir=".", total_checks=1,
            passed=0, failed=0, skipped=0, errors=0,
            blocking_failures=0, required_failures=0, advisory_warnings=0, duration_ms=0
        )

        report.add_result(CheckResult(
            "c1", "C1", CheckStatus.FAILED, Severity.BLOCKING, "Fail"
        ))

        assert not report.is_valid
        assert report.blocking_failures == 1

    def test_report_advisory_does_not_invalidate(self, verification_runner):
        """Test advisory failure does not invalidate report."""
        report = VerificationReport(
            timestamp="2025-01-01T00:00:00Z", profile=None,
            project_path=None, working_dir=".", total_checks=1,
            passed=0, failed=0, skipped=0, errors=0,
            blocking_failures=0, required_failures=0, advisory_warnings=0, duration_ms=0
        )

        report.add_result(CheckResult(
            "c1", "C1", CheckStatus.FAILED, Severity.ADVISORY, "Fail"
        ))

        assert report.is_valid
        assert report.advisory_warnings == 1


class TestCheckHandlerDispatch:
    """Tests for check handler dispatch table."""

    def test_all_check_types_have_handlers(self, verification_runner):
        """Test all documented check types have handlers."""
        handlers = verification_runner._get_check_handlers()

        expected_types = ["command", "regex", "file_exists", "import_check",
                         "custom", "contracts", "lsp_query", "ast_check"]

        for check_type in expected_types:
            assert check_type in handlers, f"Missing handler for {check_type}"

    def test_handler_is_callable(self, verification_runner):
        """Test all handlers are callable."""
        handlers = verification_runner._get_check_handlers()

        for name, handler in handlers.items():
            assert callable(handler), f"Handler {name} is not callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
