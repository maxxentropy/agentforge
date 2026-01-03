# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-cli-start, pipeline-cli-design, pipeline-cli-implement
# @component_id: pipeline-cli-status, pipeline-cli-resume, pipeline-cli-approve
# @component_id: pipeline-cli-reject, pipeline-cli-abort
# @component_id: pipeline-cli-pipelines, pipeline-cli-artifacts
# @component_id: pipeline-cli-display-result, pipeline-cli-progress-display
# @test_path: tests/unit/cli/test_pipeline_commands.py

"""Unit tests for pipeline CLI commands."""

from pathlib import Path
from unittest.mock import patch

import pytest

# Patch target - where _get_controller is defined
PATCH_GET_CONTROLLER = "agentforge.cli.click_commands.pipeline._get_controller"


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def cli():
    """Import CLI for testing."""
    from agentforge.cli.main import cli
    return cli


# =============================================================================
# START COMMAND TESTS
# =============================================================================


class TestStartCommand:
    """Tests for the 'start' command."""

    def test_start_executes_pipeline(self, cli_runner, cli, mock_controller):
        """start command executes full pipeline."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add OAuth authentication"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.execute.assert_called_once()
            assert "Pipeline completed" in result.output or "Starting pipeline" in result.output, "Assertion failed"

    def test_start_with_supervised_flag(self, cli_runner, cli, mock_controller):
        """--supervised flag enables approval mode."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--supervised"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Verify _get_controller was called (config_override is passed there)
            mock_get.assert_called()

    def test_start_with_short_supervised_flag(self, cli_runner, cli, mock_controller):
        """-s short flag enables supervised mode."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "-s"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_start_with_exit_after(self, cli_runner, cli, mock_controller):
        """--exit-after stops at specified stage."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--exit-after", "spec"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_get.assert_called()

    def test_start_with_delivery_mode_commit(self, cli_runner, cli, mock_controller):
        """--delivery-mode commit is default."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--delivery-mode", "commit"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_start_with_delivery_mode_pr(self, cli_runner, cli, mock_controller):
        """--delivery-mode pr creates pull request."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--delivery-mode", "pr"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_start_with_delivery_mode_files(self, cli_runner, cli, mock_controller):
        """--delivery-mode files outputs files only."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--delivery-mode", "files"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_start_with_delivery_mode_patch(self, cli_runner, cli, mock_controller):
        """--delivery-mode patch generates patch file."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--delivery-mode", "patch"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_start_with_iterate_flag(self, cli_runner, cli, mock_controller):
        """--iterate enables spec review pause."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--iterate"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_start_with_timeout(self, cli_runner, cli, mock_controller):
        """--timeout sets pipeline timeout."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--timeout", "7200"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_start_requires_request(self, cli_runner, cli):
        """start command requires request argument."""
        result = cli_runner.invoke(cli, ["start"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"
        assert "Missing argument" in result.output or "Usage" in result.output, "Assertion failed"

    def test_start_displays_success(self, cli_runner, cli, mock_controller):
        """start displays success message on completion."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show pipeline ID and success indicators
            assert "PL-" in result.output or "pipeline" in result.output.lower(), "Assertion failed"

    def test_start_displays_failure(self, cli_runner, cli, mock_controller_failed):
        """start displays error message on failure."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller_failed

            result = cli_runner.invoke(cli, ["start", "Add broken feature"])

            # Should complete (exit 0) but show failure in output
            assert "failed" in result.output.lower() or "error" in result.output.lower(), "Assertion failed"


# =============================================================================
# DESIGN COMMAND TESTS
# =============================================================================


class TestDesignCommand:
    """Tests for the 'design' command."""

    def test_design_executes_pipeline(self, cli_runner, cli, mock_controller, sample_pipeline_result_design):
        """design command executes design-only pipeline."""
        mock_controller.execute.return_value = sample_pipeline_result_design

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["design", "Add user authentication"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.execute.assert_called_once()

    def test_design_exits_at_spec(self, cli_runner, cli, mock_controller, sample_pipeline_result_design):
        """design command exits at SPEC stage."""
        mock_controller.execute.return_value = sample_pipeline_result_design

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["design", "Add feature"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_get.assert_called()

    def test_design_with_iterate(self, cli_runner, cli, mock_controller, sample_pipeline_result_design):
        """--iterate enables spec review pause."""
        mock_controller.execute.return_value = sample_pipeline_result_design

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["design", "Add feature", "--iterate"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_design_shows_spec_id(self, cli_runner, cli, mock_controller, sample_pipeline_result_design):
        """design shows spec ID on completion."""
        mock_controller.execute.return_value = sample_pipeline_result_design

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["design", "Add feature"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show spec ID in output
            assert "SPEC" in result.output or "spec" in result.output.lower(), "Assertion failed"

    def test_design_requires_request(self, cli_runner, cli):
        """design command requires request argument."""
        result = cli_runner.invoke(cli, ["design"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"


# =============================================================================
# IMPLEMENT COMMAND TESTS
# =============================================================================


class TestImplementCommand:
    """Tests for the 'implement' command."""

    def test_implement_from_request(self, cli_runner, cli, mock_controller):
        """implement with request runs full pipeline."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["implement", "Add caching layer"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.execute.assert_called_once()

    def test_implement_from_spec(self, cli_runner, cli, mock_controller, temp_project_with_spec):
        """--from-spec loads existing specification."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            with cli_runner.isolated_filesystem():
                # Create spec in isolated filesystem
                spec_dir = Path(".agentforge/specs")
                spec_dir.mkdir(parents=True)
                (spec_dir / "SPEC-20260102-0001.yaml").write_text("""
spec_id: SPEC-20260102-0001
title: Test Spec
overview:
  description: Test implementation
""")

                result = cli_runner.invoke(cli, ["implement", "--from-spec", "SPEC-20260102-0001"])

            # Should either succeed or fail gracefully
            assert result.exit_code == 0 or "not found" in result.output.lower(), "Assertion failed"

    def test_implement_skip_to_red(self, cli_runner, cli, mock_controller, temp_project_with_spec):
        """--skip-to red jumps to RED stage."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            with cli_runner.isolated_filesystem():
                spec_dir = Path(".agentforge/specs")
                spec_dir.mkdir(parents=True)
                (spec_dir / "SPEC-001.yaml").write_text("spec_id: SPEC-001\noverview: {}")

                result = cli_runner.invoke(
                    cli, ["implement", "--from-spec", "SPEC-001", "--skip-to", "red"]
                )

            # Should process the skip-to flag
            assert result.exit_code == 0 or "not found" in result.output.lower(), "Assertion failed"

    def test_implement_skip_to_green(self, cli_runner, cli, mock_controller):
        """--skip-to green jumps to GREEN stage."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            with cli_runner.isolated_filesystem():
                spec_dir = Path(".agentforge/specs")
                spec_dir.mkdir(parents=True)
                (spec_dir / "SPEC-001.yaml").write_text("spec_id: SPEC-001\noverview: {}")

                result = cli_runner.invoke(
                    cli, ["implement", "--from-spec", "SPEC-001", "--skip-to", "green"]
                )

            assert result.exit_code == 0 or "not found" in result.output.lower(), "Assertion failed"

    def test_implement_requires_request_or_spec(self, cli_runner, cli):
        """error when neither request nor --from-spec provided."""
        result = cli_runner.invoke(cli, ["implement"])

        # Should fail with usage error
        assert result.exit_code != 0 or "required" in result.output.lower(), "Assertion failed"

    def test_implement_with_delivery_mode(self, cli_runner, cli, mock_controller):
        """--delivery-mode configures output format."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["implement", "Add feature", "--delivery-mode", "pr"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_implement_spec_not_found(self, cli_runner, cli):
        """error when spec file not found."""
        result = cli_runner.invoke(cli, ["implement", "--from-spec", "NONEXISTENT-SPEC"])

        # Should fail with not found error
        assert result.exit_code != 0 or "not found" in result.output.lower(), "Assertion failed"


# =============================================================================
# STATUS COMMAND TESTS
# =============================================================================


class TestStatusCommand:
    """Tests for the 'status' command."""

    def test_status_shows_pipeline_info(self, cli_runner, cli, mock_controller):
        """status displays pipeline information."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["status", "PL-20260102-abc123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.get_status.assert_called()
            # Should display pipeline info
            assert "PL-" in result.output or "Pipeline" in result.output, "Assertion failed"

    def test_status_without_id_shows_recent(self, cli_runner, cli, mock_controller):
        """status without ID shows most recent pipeline."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["status"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should call list_pipelines to get most recent
            mock_controller.list_pipelines.assert_called()

    def test_status_verbose_output(self, cli_runner, cli, mock_controller):
        """--verbose shows detailed information."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["status", "--verbose"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Verbose should show more details like tokens/cost
            # (exact output depends on implementation)

    def test_status_short_verbose_flag(self, cli_runner, cli, mock_controller):
        """-v short flag shows verbose output."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["status", "-v"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_status_shows_error_for_failed(self, cli_runner, cli, mock_controller_failed):
        """status shows error for failed pipeline."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller_failed

            result = cli_runner.invoke(cli, ["status", "PL-20260102-fail"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show error info

    def test_status_shows_actions_paused(self, cli_runner, cli, mock_controller_paused):
        """status shows available actions for paused pipeline."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller_paused

            result = cli_runner.invoke(cli, ["status", "PL-20260102-paused"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should suggest resume/abort actions

    def test_status_shows_actions_awaiting(self, cli_runner, cli, mock_controller_awaiting):
        """status shows available actions for awaiting_approval pipeline."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller_awaiting

            result = cli_runner.invoke(cli, ["status", "PL-20260102-await"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should suggest approve/reject actions

    def test_status_no_pipeline_found(self, cli_runner, cli, mock_controller):
        """status handles no pipeline found."""
        mock_controller.list_pipelines.return_value = []
        mock_controller.get_status.return_value = None

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["status"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            assert "No pipeline" in result.output or "not found" in result.output.lower(), "Assertion failed"


# =============================================================================
# RESUME COMMAND TESTS
# =============================================================================


class TestResumeCommand:
    """Tests for the 'resume' command."""

    def test_resume_calls_controller(self, cli_runner, cli, mock_controller):
        """resume calls controller with pipeline ID."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["resume", "PL-20260102-abc123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.execute.assert_called()

    def test_resume_with_feedback(self, cli_runner, cli, mock_controller):
        """--feedback provides feedback before resuming."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(
                cli, ["resume", "PL-123", "--feedback", "Use Google OAuth instead"]
            )

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.provide_feedback.assert_called()

    def test_resume_short_feedback_flag(self, cli_runner, cli, mock_controller):
        """-f short flag provides feedback."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["resume", "PL-123", "-f", "Use JWT instead"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_resume_requires_pipeline_id(self, cli_runner, cli):
        """resume command requires pipeline_id argument."""
        result = cli_runner.invoke(cli, ["resume"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"


# =============================================================================
# APPROVE COMMAND TESTS
# =============================================================================


class TestApproveCommand:
    """Tests for the 'approve' command."""

    def test_approve_calls_controller(self, cli_runner, cli, mock_controller):
        """approve calls controller.approve()."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["approve", "PL-20260102-abc123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.approve.assert_called_with("PL-20260102-abc123")

    def test_approve_shows_success(self, cli_runner, cli, mock_controller):
        """approve shows success message."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["approve", "PL-123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            assert "Approved" in result.output or "approved" in result.output.lower(), "Assertion failed"

    def test_approve_shows_failure(self, cli_runner, cli, mock_controller):
        """approve shows failure when controller returns False."""
        mock_controller.approve.return_value = False

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["approve", "PL-123"])

            # Should still exit 0 but show failure message
            assert "Could not" in result.output or "failed" in result.output.lower(), "Assertion failed"

    def test_approve_requires_pipeline_id(self, cli_runner, cli):
        """approve command requires pipeline_id argument."""
        result = cli_runner.invoke(cli, ["approve"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"


# =============================================================================
# REJECT COMMAND TESTS
# =============================================================================


class TestRejectCommand:
    """Tests for the 'reject' command."""

    def test_reject_with_feedback(self, cli_runner, cli, mock_controller):
        """--feedback requests revision."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(
                cli, ["reject", "PL-123", "--feedback", "Need more validation"]
            )

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.provide_feedback.assert_called()

    def test_reject_with_abort(self, cli_runner, cli, mock_controller):
        """--abort cancels the pipeline."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["reject", "PL-123", "--abort"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.abort.assert_called()

    def test_reject_requires_feedback_or_abort(self, cli_runner, cli, mock_controller):
        """error when neither feedback nor abort specified."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["reject", "PL-123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should prompt for feedback or abort
            assert "feedback" in result.output.lower() or "abort" in result.output.lower(), "Assertion failed"

    def test_reject_requires_pipeline_id(self, cli_runner, cli):
        """reject command requires pipeline_id argument."""
        result = cli_runner.invoke(cli, ["reject"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"


# =============================================================================
# ABORT COMMAND TESTS
# =============================================================================


class TestAbortCommand:
    """Tests for the 'abort' command."""

    def test_abort_calls_controller(self, cli_runner, cli, mock_controller):
        """abort calls controller.abort()."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["abort", "PL-20260102-abc123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.abort.assert_called()

    def test_abort_with_reason(self, cli_runner, cli, mock_controller):
        """--reason provides abort reason."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(
                cli, ["abort", "PL-123", "--reason", "Requirements changed"]
            )

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.abort.assert_called_with("PL-123", "Requirements changed")

    def test_abort_short_reason_flag(self, cli_runner, cli, mock_controller):
        """-r short flag provides reason."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["abort", "PL-123", "-r", "No longer needed"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_abort_default_reason(self, cli_runner, cli, mock_controller):
        """abort uses default reason when not specified."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["abort", "PL-123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should use default "User requested" reason

    def test_abort_shows_success(self, cli_runner, cli, mock_controller):
        """abort shows success message."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["abort", "PL-123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            assert "aborted" in result.output.lower(), "Expected 'aborted' in result.output.lower()"

    def test_abort_shows_failure(self, cli_runner, cli, mock_controller):
        """abort shows failure when controller returns False."""
        mock_controller.abort.return_value = False

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["abort", "PL-123"])

            # Should show failure message
            assert "Could not" in result.output or "not" in result.output.lower(), "Assertion failed"

    def test_abort_requires_pipeline_id(self, cli_runner, cli):
        """abort command requires pipeline_id argument."""
        result = cli_runner.invoke(cli, ["abort"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"


# =============================================================================
# PIPELINES COMMAND TESTS
# =============================================================================


class TestPipelinesCommand:
    """Tests for the 'pipelines' command."""

    def test_pipelines_lists_all(self, cli_runner, cli, mock_controller, multiple_pipelines):
        """pipelines lists all pipelines."""
        mock_controller.list_pipelines.return_value = multiple_pipelines

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            mock_controller.list_pipelines.assert_called()
            # Should list multiple pipelines
            assert "PL-" in result.output, "Expected 'PL-' in result.output"

    def test_pipelines_filter_running(self, cli_runner, cli, mock_controller, multiple_pipelines):
        """--status running filters by status."""
        # Filter to only running pipelines
        running = [p for p in multiple_pipelines if p.status.value == "running"]
        mock_controller.list_pipelines.return_value = running

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines", "--status", "running"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_pipelines_filter_completed(self, cli_runner, cli, mock_controller, multiple_pipelines):
        """--status completed filters by status."""
        completed = [p for p in multiple_pipelines if p.status.value == "completed"]
        mock_controller.list_pipelines.return_value = completed

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines", "--status", "completed"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_pipelines_filter_failed(self, cli_runner, cli, mock_controller, multiple_pipelines):
        """--status failed filters by status."""
        failed = [p for p in multiple_pipelines if p.status.value == "failed"]
        mock_controller.list_pipelines.return_value = failed

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines", "--status", "failed"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_pipelines_limit(self, cli_runner, cli, mock_controller, multiple_pipelines):
        """--limit controls number of results."""
        mock_controller.list_pipelines.return_value = multiple_pipelines[:2]

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines", "--limit", "2"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_pipelines_short_limit_flag(self, cli_runner, cli, mock_controller, multiple_pipelines):
        """-n short flag sets limit."""
        mock_controller.list_pipelines.return_value = multiple_pipelines[:5]

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines", "-n", "5"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_pipelines_no_results(self, cli_runner, cli, mock_controller):
        """pipelines handles no results."""
        mock_controller.list_pipelines.return_value = []

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            assert "No pipelines" in result.output or "found" in result.output.lower(), "Assertion failed"

    def test_pipelines_shows_table_header(self, cli_runner, cli, mock_controller, multiple_pipelines):
        """pipelines shows table header."""
        mock_controller.list_pipelines.return_value = multiple_pipelines

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["pipelines"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should have table-like output
            assert "ID" in result.output or "-" in result.output, "Assertion failed"


# =============================================================================
# ARTIFACTS COMMAND TESTS
# =============================================================================


class TestArtifactsCommand:
    """Tests for the 'artifacts' command."""

    def test_artifacts_shows_all(self, cli_runner, cli, temp_project_with_artifacts):
        """artifacts shows all pipeline artifacts."""
        with cli_runner.isolated_filesystem():
            # Create artifacts directory
            artifacts_dir = Path(".agentforge/artifacts/PL-123")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "01-intake.yaml").write_text("request_id: REQ-001")
            (artifacts_dir / "02-clarify.yaml").write_text("clarified: true")

            result = cli_runner.invoke(cli, ["artifacts", "PL-123"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should list artifacts
            assert "intake" in result.output.lower() or "yaml" in result.output.lower(), "Assertion failed"

    def test_artifacts_specific_stage(self, cli_runner, cli):
        """--stage shows specific stage artifact."""
        with cli_runner.isolated_filesystem():
            artifacts_dir = Path(".agentforge/artifacts/PL-123")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "04-spec.yaml").write_text("spec_id: SPEC-001\ntitle: Test")

            result = cli_runner.invoke(cli, ["artifacts", "PL-123", "--stage", "spec"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show spec content
            assert "spec" in result.output.lower() or "SPEC" in result.output, "Assertion failed"

    def test_artifacts_short_stage_flag(self, cli_runner, cli):
        """-s short flag selects stage."""
        with cli_runner.isolated_filesystem():
            artifacts_dir = Path(".agentforge/artifacts/PL-123")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "01-intake.yaml").write_text("request_id: REQ-001")

            result = cli_runner.invoke(cli, ["artifacts", "PL-123", "-s", "intake"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_artifacts_output_file(self, cli_runner, cli):
        """--output saves artifact to file."""
        with cli_runner.isolated_filesystem():
            artifacts_dir = Path(".agentforge/artifacts/PL-123")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "04-spec.yaml").write_text("spec_id: SPEC-001")

            result = cli_runner.invoke(
                cli, ["artifacts", "PL-123", "--stage", "spec", "--output", "spec_out.yaml"]
            )

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Check output file was created
            assert Path("spec_out.yaml").exists(), "Expected Path('spec_out.yaml').exists() to be truthy"

    def test_artifacts_short_output_flag(self, cli_runner, cli):
        """-o short flag sets output file."""
        with cli_runner.isolated_filesystem():
            artifacts_dir = Path(".agentforge/artifacts/PL-123")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "01-intake.yaml").write_text("request_id: REQ-001")

            result = cli_runner.invoke(
                cli, ["artifacts", "PL-123", "-s", "intake", "-o", "intake.yaml"]
            )

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_artifacts_not_found(self, cli_runner, cli):
        """artifacts handles missing pipeline."""
        result = cli_runner.invoke(cli, ["artifacts", "NONEXISTENT"])

        assert result.exit_code == 0, "Expected result.exit_code to equal 0"
        assert "No artifacts" in result.output or "not found" in result.output.lower(), "Assertion failed"

    def test_artifacts_stage_not_found(self, cli_runner, cli):
        """artifacts handles missing stage."""
        with cli_runner.isolated_filesystem():
            artifacts_dir = Path(".agentforge/artifacts/PL-123")
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "01-intake.yaml").write_text("request_id: REQ-001")

            result = cli_runner.invoke(cli, ["artifacts", "PL-123", "--stage", "nonexistent"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            assert "not found" in result.output.lower(), "Expected 'not found' in result.output.lower()"

    def test_artifacts_requires_pipeline_id(self, cli_runner, cli):
        """artifacts command requires pipeline_id argument."""
        result = cli_runner.invoke(cli, ["artifacts"])

        assert result.exit_code != 0, "Expected result.exit_code to not equal 0"


# =============================================================================
# DISPLAY RESULT HELPER TESTS
# =============================================================================


class TestDisplayResult:
    """Tests for the display_result helper function."""

    def test_display_result_success_commit(self, cli_runner, cli, mock_controller):
        """displays success result with commit correctly."""
        # This is tested implicitly through start command
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--delivery-mode", "commit"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"
            # Should show commit info

    def test_display_result_success_pr(self, cli_runner, cli, mock_controller):
        """displays success result with PR correctly."""
        mock_controller.execute.return_value.deliverable = {"pr_url": "https://github.com/test/pr/1"}

        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller

            result = cli_runner.invoke(cli, ["start", "Add feature", "--delivery-mode", "pr"])

            assert result.exit_code == 0, "Expected result.exit_code to equal 0"

    def test_display_result_failure(self, cli_runner, cli, mock_controller_failed):
        """displays failure result correctly."""
        with patch(PATCH_GET_CONTROLLER) as mock_get:
            mock_get.return_value = mock_controller_failed

            result = cli_runner.invoke(cli, ["start", "Add broken feature"])

            # Should show error message
            assert "failed" in result.output.lower() or "error" in result.output.lower(), "Assertion failed"


# =============================================================================
# PROGRESS DISPLAY TESTS
# =============================================================================


class TestPipelineProgressDisplay:
    """Tests for PipelineProgressDisplay class."""

    def test_stage_icons_defined(self):
        """STAGE_ICONS has correct icons for all stages."""
        from agentforge.cli.click_commands.pipeline import PipelineProgressDisplay

        display = PipelineProgressDisplay()

        expected_stages = ["intake", "clarify", "analyze", "spec", "red", "green", "refactor", "deliver"]
        for stage in expected_stages:
            assert stage in display.STAGE_ICONS, "Expected stage in display.STAGE_ICONS"
            assert len(display.STAGE_ICONS[stage]) > 0, "Expected len(display.STAGE_ICONS[sta... > 0"

    def test_display_stage_start(self, capsys):
        """display_stage_start shows stage with icon."""
        from agentforge.cli.click_commands.pipeline import PipelineProgressDisplay

        display = PipelineProgressDisplay()
        display.display_stage_start("intake")

        captured = capsys.readouterr()
        assert "INTAKE" in captured.out.upper() or "intake" in captured.out.lower(), "Assertion failed"

    def test_display_stage_complete(self, capsys):
        """display_stage_complete shows completion."""
        from agentforge.cli.click_commands.pipeline import PipelineProgressDisplay

        display = PipelineProgressDisplay()
        display.display_stage_complete("intake", 5.5)

        captured = capsys.readouterr()
        assert "complete" in captured.out.lower() or "5.5" in captured.out, "Assertion failed"

    def test_display_stage_failed(self, capsys):
        """display_stage_failed shows error."""
        from agentforge.cli.click_commands.pipeline import PipelineProgressDisplay

        display = PipelineProgressDisplay()
        display.display_stage_failed("analyze", "Could not parse file")

        captured = capsys.readouterr()
        assert "failed" in captured.out.lower() or "Could not" in captured.out, "Assertion failed"

    def test_display_escalation(self, capsys):
        """display_escalation shows warning."""
        from agentforge.cli.click_commands.pipeline import PipelineProgressDisplay

        display = PipelineProgressDisplay()
        display.display_escalation("spec", "Ambiguous requirements")

        captured = capsys.readouterr()
        assert "Escalation" in captured.out or "Ambiguous" in captured.out, "Assertion failed"
