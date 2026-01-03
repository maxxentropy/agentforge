# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-cli-start, pipeline-cli-design, pipeline-cli-implement
# @component_id: pipeline-cli-status, pipeline-cli-resume, pipeline-cli-approve
# @component_id: pipeline-cli-reject, pipeline-cli-abort
# @component_id: pipeline-cli-pipelines, pipeline-cli-artifacts
# @test_path: tests/integration/cli/test_pipeline_cli_integration.py

"""Integration tests for pipeline CLI commands.

These tests verify end-to-end behavior of CLI commands with mocked
PipelineController, focusing on command integration and output formatting.
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# =============================================================================
# Command Integration Tests
# =============================================================================


class TestCLICommandIntegration:
    """Integration tests for CLI command registration."""

    def test_cli_has_all_pipeline_commands(self, cli_runner):
        """CLI has all pipeline commands registered."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"

        # Primary commands
        assert "start" in result.output, "Expected 'start' in result.output"
        assert "design" in result.output, "Expected 'design' in result.output"
        assert "implement" in result.output, "Expected 'implement' in result.output"

        # Control commands
        assert "status" in result.output, "Expected 'status' in result.output"
        assert "resume" in result.output, "Expected 'resume' in result.output"
        assert "approve" in result.output, "Expected 'approve' in result.output"
        assert "reject" in result.output, "Expected 'reject' in result.output"
        assert "abort" in result.output, "Expected 'abort' in result.output"

        # List commands
        assert "pipelines" in result.output, "Expected 'pipelines' in result.output"
        assert "artifacts" in result.output, "Expected 'artifacts' in result.output"

    def test_start_help(self, cli_runner):
        """start --help shows usage information."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["start", "--help"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"
        assert "REQUEST" in result.output or "request" in result.output.lower(), "Assertion failed"
        assert "--supervised" in result.output or "-s" in result.output, "Assertion failed"
        assert "--exit-after" in result.output, "Expected '--exit-after' in result.output"
        assert "--delivery-mode" in result.output, "Expected '--delivery-mode' in result.output"

    def test_design_help(self, cli_runner):
        """design --help shows usage information."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["design", "--help"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"
        assert "REQUEST" in result.output or "request" in result.output.lower(), "Assertion failed"
        assert "--iterate" in result.output or "-i" in result.output, "Assertion failed"

    def test_implement_help(self, cli_runner):
        """implement --help shows usage information."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["implement", "--help"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"
        assert "--from-spec" in result.output, "Expected '--from-spec' in result.output"
        assert "--skip-to" in result.output, "Expected '--skip-to' in result.output"
        assert "--delivery-mode" in result.output, "Expected '--delivery-mode' in result.output"

    def test_status_help(self, cli_runner):
        """status --help shows usage information."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["status", "--help"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"
        assert "PIPELINE_ID" in result.output or "pipeline" in result.output.lower(), "Assertion failed"
        assert "--verbose" in result.output or "-v" in result.output, "Assertion failed"

    def test_pipelines_help(self, cli_runner):
        """pipelines --help shows usage information."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["pipelines", "--help"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"
        assert "--status" in result.output or "-s" in result.output, "Assertion failed"
        assert "--limit" in result.output or "-n" in result.output, "Assertion failed"

    def test_artifacts_help(self, cli_runner):
        """artifacts --help shows usage information."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["artifacts", "--help"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"
        assert "PIPELINE_ID" in result.output, "Expected 'PIPELINE_ID' in result.output"
        assert "--stage" in result.output or "-s" in result.output, "Assertion failed"
        assert "--output" in result.output or "-o" in result.output, "Assertion failed"


# =============================================================================
# Pipeline Execution Integration Tests
# =============================================================================


class TestStartIntegration:
    """Integration tests for start command execution."""

    def test_start_full_pipeline(self, cli_runner, mock_pipeline_controller):
        """start executes full pipeline and displays result."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["start", "Add user authentication"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            assert "Starting pipeline" in result.output or "pipeline" in result.output.lower(), "Assertion failed"

    def test_start_with_all_options(self, cli_runner, mock_pipeline_controller):
        """start with all options configured correctly."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, [
                "start", "Add feature",
                "--supervised",
                "--exit-after", "spec",
                "--delivery-mode", "pr",
                "--timeout", "7200",
            ])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"


class TestDesignIntegration:
    """Integration tests for design command execution."""

    def test_design_exits_at_spec(self, cli_runner, mock_pipeline_controller):
        """design creates spec and exits."""
        from agentforge.cli.main import cli

        # Configure mock for design result
        result_mock = MagicMock()
        result_mock.success = True
        result_mock.pipeline_id = "PL-design-001"
        result_mock.stages_completed = ["intake", "clarify", "analyze", "spec"]
        result_mock.total_duration_seconds = 30.0
        result_mock.deliverable = {"spec_id": "SPEC-20260102-0001"}
        result_mock.error = None
        mock_pipeline_controller.execute.return_value = result_mock

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["design", "Design OAuth2 authentication"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show spec info
            assert "SPEC" in result.output or "Design" in result.output, "Assertion failed"


class TestImplementIntegration:
    """Integration tests for implement command execution."""

    def test_implement_from_request(self, cli_runner, mock_pipeline_controller):
        """implement from request runs full pipeline."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["implement", "Add caching layer"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_implement_from_spec_file(self, cli_runner, temp_project_with_spec, mock_pipeline_controller):
        """implement from spec file loads spec and runs."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            with cli_runner.isolated_filesystem():
                # Create spec file
                spec_dir = Path(".agentforge/specs")
                spec_dir.mkdir(parents=True)
                (spec_dir / "SPEC-TEST.yaml").write_text("""
spec_id: SPEC-TEST
overview:
  description: Test implementation
""")

                result = cli_runner.invoke(cli, ["implement", "--from-spec", "SPEC-TEST"])

                # Either succeeds or reports spec not found
                assert result.exit_code == 0 or "not found" in result.output.lower(), "Assertion failed"


# =============================================================================
# Control Command Integration Tests
# =============================================================================


class TestStatusIntegration:
    """Integration tests for status command."""

    def test_status_displays_full_info(self, cli_runner, mock_pipeline_controller):
        """status displays complete pipeline information."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["status", "PL-20260102-int001", "-v"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show pipeline details
            assert "PL-" in result.output or "Pipeline" in result.output, "Assertion failed"

    def test_status_shows_recent_without_id(self, cli_runner, mock_pipeline_controller):
        """status without ID shows most recent pipeline."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["status"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_pipeline_controller.list_pipelines.assert_called()


class TestResumeIntegration:
    """Integration tests for resume command."""

    def test_resume_with_feedback(self, cli_runner, mock_pipeline_controller):
        """resume with feedback provides feedback and continues."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, [
                "resume", "PL-test",
                "--feedback", "Use Google OAuth instead of custom auth"
            ])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_pipeline_controller.provide_feedback.assert_called()
            mock_pipeline_controller.execute.assert_called()


class TestApproveRejectIntegration:
    """Integration tests for approve and reject commands."""

    def test_approve_continues_pipeline(self, cli_runner, mock_pipeline_controller):
        """approve allows pipeline to continue."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["approve", "PL-test"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_pipeline_controller.approve.assert_called_with("PL-test")
            assert "Approved" in result.output or "approved" in result.output.lower(), "Assertion failed"

    def test_reject_with_feedback_revises(self, cli_runner, mock_pipeline_controller):
        """reject with feedback triggers revision."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, [
                "reject", "PL-test",
                "--feedback", "Need more error handling"
            ])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_pipeline_controller.provide_feedback.assert_called()

    def test_reject_with_abort_cancels(self, cli_runner, mock_pipeline_controller):
        """reject with abort cancels pipeline."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["reject", "PL-test", "--abort"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_pipeline_controller.abort.assert_called()


class TestAbortIntegration:
    """Integration tests for abort command."""

    def test_abort_with_reason(self, cli_runner, mock_pipeline_controller):
        """abort with reason cancels pipeline."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, [
                "abort", "PL-test",
                "--reason", "Requirements changed"
            ])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_pipeline_controller.abort.assert_called_with("PL-test", "Requirements changed")


# =============================================================================
# List Command Integration Tests
# =============================================================================


class TestPipelinesIntegration:
    """Integration tests for pipelines command."""

    def test_pipelines_lists_with_format(self, cli_runner, mock_pipeline_controller):
        """pipelines lists in table format."""
        from agentforge.cli.main import cli

        # Setup multiple pipelines
        pipelines = []
        for i, status in enumerate(["running", "completed", "failed"]):
            state = MagicMock()
            state.pipeline_id = f"PL-{i:03d}"
            state.pipeline_type = "implement"
            state.status = MagicMock()
            state.status.value = status
            state.current_stage = "spec"
            state.created_at = datetime(2026, 1, 2, 10, i, 0, tzinfo=UTC)
            pipelines.append(state)

        mock_pipeline_controller.list_pipelines.return_value = pipelines

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["pipelines"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should list all pipelines
            assert "PL-" in result.output, "Expected 'PL-' in result.output"

    def test_pipelines_filter_by_status(self, cli_runner, mock_pipeline_controller):
        """pipelines filters by status."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["pipelines", "--status", "running"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"


class TestArtifactsIntegration:
    """Integration tests for artifacts command."""

    def test_artifacts_lists_all(self, cli_runner):
        """artifacts lists all pipeline artifacts."""
        from agentforge.cli.main import cli

        with cli_runner.isolated_filesystem():
            # Create artifacts
            artifacts_dir = Path(".agentforge/artifacts/PL-int")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "01-intake.yaml").write_text("request_id: REQ-001")
            (artifacts_dir / "02-clarify.yaml").write_text("clarified: true")
            (artifacts_dir / "03-analyze.yaml").write_text("analyzed: true")
            (artifacts_dir / "04-spec.yaml").write_text("spec_id: SPEC-001")

            result = cli_runner.invoke(cli, ["artifacts", "PL-int"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should list artifact files
            assert "yaml" in result.output.lower() or "intake" in result.output.lower(), "Assertion failed"

    def test_artifacts_shows_specific_stage(self, cli_runner):
        """artifacts --stage shows specific artifact content."""
        from agentforge.cli.main import cli

        with cli_runner.isolated_filesystem():
            artifacts_dir = Path(".agentforge/artifacts/PL-int")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "04-spec.yaml").write_text("""
spec_id: SPEC-INT-001
title: Integration Test
components:
  - id: test-comp
""")

            result = cli_runner.invoke(cli, ["artifacts", "PL-int", "--stage", "spec"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show spec content
            assert "spec" in result.output.lower() or "SPEC" in result.output, "Assertion failed"

    def test_artifacts_exports_to_file(self, cli_runner):
        """artifacts --output exports to file."""
        from agentforge.cli.main import cli

        with cli_runner.isolated_filesystem():
            artifacts_dir = Path(".agentforge/artifacts/PL-int")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "04-spec.yaml").write_text("spec_id: SPEC-001")

            result = cli_runner.invoke(cli, [
                "artifacts", "PL-int",
                "--stage", "spec",
                "--output", "exported.yaml"
            ])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            assert Path("exported.yaml").exists(), "Expected Path('exported.yaml').exists() to be truthy"


# =============================================================================
# Error Handling Integration Tests
# =============================================================================


class TestCLIErrorHandling:
    """Integration tests for CLI error handling."""

    def test_invalid_command_shows_help(self, cli_runner):
        """Invalid command shows help message."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"
        assert "Usage" in result.output or "Error" in result.output, "Assertion failed"

    def test_missing_required_argument(self, cli_runner):
        """Missing required argument shows error."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["resume"])  # Missing pipeline_id

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"
        assert "Missing" in result.output or "required" in result.output.lower(), "Assertion failed"

    def test_invalid_option_value(self, cli_runner):
        """Invalid option value shows error."""
        from agentforge.cli.main import cli

        result = cli_runner.invoke(cli, ["start", "Test", "--exit-after", "invalid-stage"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"
        assert "Invalid" in result.output or "invalid" in result.output.lower(), "Assertion failed"

    def test_pipeline_controller_error_handled(self, cli_runner, mock_pipeline_controller):
        """PipelineController errors are handled gracefully."""
        from agentforge.cli.main import cli

        mock_pipeline_controller.execute.side_effect = Exception("Test error")

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["start", "Test"])

            # Should not crash - either catches error or shows it
            # Exit code might be 0 or 1 depending on error handling
            assert "error" in result.output.lower() or result.exit_code != 0, "Assertion failed"


# =============================================================================
# Output Formatting Integration Tests
# =============================================================================


class TestOutputFormatting:
    """Integration tests for CLI output formatting."""

    def test_success_output_formatting(self, cli_runner, mock_pipeline_controller):
        """Success output is properly formatted."""
        from agentforge.cli.main import cli

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["start", "Add feature"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should have formatted output
            assert len(result.output) > 0, "Expected len(result.output) > 0"

    def test_failure_output_formatting(self, cli_runner, mock_pipeline_controller):
        """Failure output shows error clearly."""
        from agentforge.cli.main import cli

        # Configure failure
        fail_result = MagicMock()
        fail_result.success = False
        fail_result.pipeline_id = "PL-fail"
        fail_result.stages_completed = ["intake"]
        fail_result.error = "Analysis failed: missing dependencies"
        fail_result.current_stage = "analyze"
        fail_result.total_duration_seconds = 5.0
        fail_result.deliverable = None
        mock_pipeline_controller.execute.return_value = fail_result

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["start", "Broken feature"])

            # Should show error message
            assert "failed" in result.output.lower() or "error" in result.output.lower(), "Assertion failed"

    def test_table_output_formatting(self, cli_runner, mock_pipeline_controller):
        """Table output is properly aligned."""
        from agentforge.cli.main import cli

        # Setup multiple pipelines
        pipelines = []
        for i in range(3):
            state = MagicMock()
            state.pipeline_id = f"PL-20260102-{i:03d}"
            state.pipeline_type = "implement"
            state.status = MagicMock()
            state.status.value = "completed"
            state.current_stage = "deliver"
            state.created_at = datetime(2026, 1, 2, 10, i, 0, tzinfo=UTC)
            pipelines.append(state)

        mock_pipeline_controller.list_pipelines.return_value = pipelines

        with patch("agentforge.cli.click_commands.pipeline._get_controller") as mock_get:
            mock_get.return_value = mock_pipeline_controller

            result = cli_runner.invoke(cli, ["pipelines"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should have consistent formatting
            lines = result.output.strip().split("\n")
            assert len(lines) >= 3, "Expected len(lines) >= 3"# At least header + separator + data
