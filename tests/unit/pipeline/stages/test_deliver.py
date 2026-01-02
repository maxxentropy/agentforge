# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: deliver-phase-executor
# @test_path: tests/unit/pipeline/stages/test_deliver.py

"""Unit tests for DeliverPhaseExecutor."""

from pathlib import Path
from unittest.mock import Mock, patch

from agentforge.core.pipeline import StageContext, StageStatus


class TestDeliveryMode:
    """Tests for DeliveryMode enum-like class."""

    def test_delivery_mode_commit_value(self):
        """DeliveryMode.COMMIT has correct value."""
        from agentforge.core.pipeline.stages.deliver import DeliveryMode

        assert DeliveryMode.COMMIT == "commit"

    def test_delivery_mode_pr_value(self):
        """DeliveryMode.PR has correct value."""
        from agentforge.core.pipeline.stages.deliver import DeliveryMode

        assert DeliveryMode.PR == "pr"

    def test_delivery_mode_files_value(self):
        """DeliveryMode.FILES has correct value."""
        from agentforge.core.pipeline.stages.deliver import DeliveryMode

        assert DeliveryMode.FILES == "files"

    def test_delivery_mode_patch_value(self):
        """DeliveryMode.PATCH has correct value."""
        from agentforge.core.pipeline.stages.deliver import DeliveryMode

        assert DeliveryMode.PATCH == "patch"


class TestDeliverPhaseExecutor:
    """Tests for DeliverPhaseExecutor class."""

    def test_stage_name_is_deliver(self):
        """DeliverPhaseExecutor has stage_name 'deliver'."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()
        assert executor.stage_name == "deliver"

    def test_artifact_type_is_deliverable(self):
        """DeliverPhaseExecutor has artifact_type 'deliverable'."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()
        assert executor.artifact_type == "deliverable"

    def test_required_input_fields(self):
        """DeliverPhaseExecutor requires spec_id, final_files."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()
        assert "spec_id" in executor.required_input_fields
        assert "final_files" in executor.required_input_fields

    def test_output_fields(self):
        """DeliverPhaseExecutor outputs expected fields."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()
        assert "spec_id" in executor.output_fields
        assert "deliverable_type" in executor.output_fields


class TestDeliverPhaseConfiguration:
    """Tests for DELIVER phase configuration."""

    def test_default_delivery_mode_is_commit(self):
        """Default delivery mode is commit."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor()
        assert executor.delivery_mode == DeliveryMode.COMMIT

    def test_delivery_mode_from_config(self):
        """Delivery mode can be set from config."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.PR})
        assert executor.delivery_mode == DeliveryMode.PR

    def test_auto_commit_default_false(self):
        """Auto commit defaults to False."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()
        assert executor.auto_commit is False

    def test_auto_commit_from_config(self):
        """Auto commit can be set from config."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor({"auto_commit": True})
        assert executor.auto_commit is True

    def test_branch_prefix_from_config(self):
        """Branch prefix can be set from config."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor({"branch_prefix": "fix/"})
        assert executor.branch_prefix == "fix/"


class TestDeliverPhaseDeliveryModes:
    """Tests for DELIVER phase delivery modes."""

    def test_delivers_as_commit(self, sample_refactor_artifact, temp_git_project):
        """Delivers as git commit."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.COMMIT})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_stage_files") as mock_stage:
            mock_stage.return_value = ["src/auth/oauth_provider.py"]

            with patch.object(executor, "_create_commit") as mock_commit:
                mock_commit.return_value = None  # auto_commit is False

                result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts["deliverable_type"] == "commit"

    def test_delivers_as_pr(self, sample_refactor_artifact, temp_git_project):
        """Delivers as pull request."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.PR})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_create_branch") as mock_branch:
            mock_branch.return_value = True

            with patch.object(executor, "_stage_files") as mock_stage:
                mock_stage.return_value = ["file.py"]

                with patch.object(executor, "_create_commit") as mock_commit:
                    mock_commit.return_value = "abc123"

                    with patch.object(executor, "_create_pull_request") as mock_pr:
                        mock_pr.return_value = "https://github.com/test/pr/1"

                        result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts["deliverable_type"] == "pr"
        assert result.artifacts["pr_url"] == "https://github.com/test/pr/1"

    def test_delivers_as_files(self, sample_refactor_artifact, temp_git_project):
        """Delivers as files only."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.FILES})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts["deliverable_type"] == "files"

    def test_delivers_as_patch(self, sample_refactor_artifact, temp_git_project):
        """Delivers as patch file."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.PATCH})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_generate_patch") as mock_patch:
            mock_patch.return_value = "diff --git a/file.py b/file.py\n..."

            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts["deliverable_type"] == "patch"
        assert "patch_file" in result.artifacts

    def test_fails_on_unknown_delivery_mode(self, sample_refactor_artifact, temp_git_project):
        """Fails on unknown delivery mode."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()
        executor.delivery_mode = "unknown_mode"

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        result = executor.execute(context)

        assert result.status == StageStatus.FAILED
        assert "unknown" in result.error.lower()


class TestDeliverPhaseCommitDelivery:
    """Tests for DELIVER phase commit delivery."""

    def test_generates_commit_message(self, sample_refactor_artifact):
        """Generates commit message from artifact."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        message = executor._generate_commit_message(sample_refactor_artifact)

        assert "feat:" in message
        assert sample_refactor_artifact["spec_id"] in message

    def test_commit_message_includes_spec_id(self, sample_refactor_artifact):
        """Commit message includes spec ID."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        message = executor._generate_commit_message(sample_refactor_artifact)

        assert "SPEC-" in message

    def test_commit_message_includes_files(self, sample_refactor_artifact):
        """Commit message includes modified files."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        message = executor._generate_commit_message(sample_refactor_artifact)

        assert "Files modified" in message or "file" in message.lower()

    def test_commit_message_truncates_long_title(self):
        """Commit message truncates long title."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "original_request": "A" * 100,  # Very long request
            "final_files": [],
        }

        message = executor._generate_commit_message(artifact)

        # Title line should be reasonable length
        first_line = message.split("\n")[0]
        assert len(first_line) < 60

    def test_stages_files_for_commit(self, sample_refactor_artifact, temp_git_project):
        """Stages files for commit."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        # Create a file to stage
        (temp_git_project / "src" / "auth" / "oauth_provider.py").write_text("# test")

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)

            staged = executor._stage_files(context, ["src/auth/oauth_provider.py"])

        assert len(staged) == 1

    def test_creates_commit_when_auto_commit(self, sample_refactor_artifact, temp_git_project):
        """Creates commit when auto_commit is enabled."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({
            "delivery_mode": DeliveryMode.COMMIT,
            "auto_commit": True,
        })

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_stage_files") as mock_stage:
            mock_stage.return_value = ["file.py"]

            with patch.object(executor, "_create_commit") as mock_commit:
                mock_commit.return_value = "abc123"

                result = executor.execute(context)

        assert mock_commit.called
        assert result.artifacts["commit_sha"] == "abc123"

    def test_skips_commit_when_no_auto_commit(self, sample_refactor_artifact, temp_git_project):
        """Skips commit when auto_commit is disabled."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({
            "delivery_mode": DeliveryMode.COMMIT,
            "auto_commit": False,
        })

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_stage_files") as mock_stage:
            mock_stage.return_value = ["file.py"]

            result = executor.execute(context)

        assert result.artifacts["commit_sha"] is None
        assert result.artifacts["status"] == "staged"

    def test_handles_no_changes_to_commit(self, sample_refactor_artifact, temp_git_project):
        """Handles case with no changes to commit."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.COMMIT})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_stage_files") as mock_stage:
            mock_stage.return_value = []  # No files staged

            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert result.artifacts["status"] == "no_changes"


class TestDeliverPhasePRDelivery:
    """Tests for DELIVER phase PR delivery."""

    def test_creates_feature_branch(self, sample_refactor_artifact, temp_git_project):
        """Creates feature branch."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor({"branch_prefix": "feature/"})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)

            result = executor._create_branch(context, "feature/test-branch")

        assert result is True

    def test_pushes_branch_to_remote(self, sample_refactor_artifact, temp_git_project):
        """Pushes branch to remote in _create_pull_request."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout="https://github.com/test/pr/1",
            )

            executor._create_pull_request(context, "feature/test", sample_refactor_artifact)

        # Should have called git push
        push_calls = [c for c in mock_subprocess.call_args_list if "push" in str(c)]
        assert len(push_calls) >= 1

    def test_creates_pull_request(self, sample_refactor_artifact, temp_git_project):
        """Creates pull request via gh CLI."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout="https://github.com/test/pr/1",
            )

            pr_url = executor._create_pull_request(context, "feature/test", sample_refactor_artifact)

        assert pr_url == "https://github.com/test/pr/1"

    def test_handles_pr_creation_failure(self, sample_refactor_artifact, temp_git_project):
        """Handles PR creation failure gracefully."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = Exception("gh not found")

            pr_url = executor._create_pull_request(context, "feature/test", sample_refactor_artifact)

        assert pr_url is None


class TestDeliverPhasePatchDelivery:
    """Tests for DELIVER phase patch delivery."""

    def test_generates_patch_content(self, sample_refactor_artifact, temp_git_project):
        """Generates patch content."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout="diff --git a/file.py b/file.py\n+test",
            )

            patch_content = executor._generate_patch(context)

        assert "diff" in patch_content

    def test_saves_patch_file(self, sample_refactor_artifact, temp_git_project):
        """Saves patch to file."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.PATCH})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_generate_patch") as mock_patch:
            mock_patch.return_value = "diff --git a/file.py b/file.py"

            result = executor.execute(context)

        assert "patch_file" in result.artifacts
        assert Path(result.artifacts["patch_file"]).exists()

    def test_patch_file_uses_spec_id(self, sample_refactor_artifact, temp_git_project):
        """Patch file name uses spec ID."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.PATCH})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch.object(executor, "_generate_patch") as mock_patch:
            mock_patch.return_value = "diff"

            result = executor.execute(context)

        patch_file = result.artifacts["patch_file"]
        assert "SPEC-" in patch_file.upper() or "spec" in patch_file.lower()


class TestDeliverPhaseFilesDelivery:
    """Tests for DELIVER phase files delivery."""

    def test_files_mode_no_git_operations(self, sample_refactor_artifact, temp_git_project):
        """Files mode performs no git operations."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.FILES})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            result = executor.execute(context)

        # Should not call any subprocess (git) commands
        mock_subprocess.assert_not_called()
        assert result.status == StageStatus.COMPLETED

    def test_files_mode_returns_file_list(self, sample_refactor_artifact, temp_git_project):
        """Files mode returns file list."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.FILES})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        result = executor.execute(context)

        assert "files_modified" in result.artifacts
        assert len(result.artifacts["files_modified"]) > 0


class TestDeliverPhaseSummaryGeneration:
    """Tests for DELIVER phase summary generation."""

    def test_generates_summary(self, sample_refactor_artifact):
        """Generates human-readable summary."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        summary = executor._generate_summary(sample_refactor_artifact)

        assert "Delivery Summary" in summary or "##" in summary

    def test_summary_includes_spec_id(self, sample_refactor_artifact):
        """Summary includes spec ID."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        summary = executor._generate_summary(sample_refactor_artifact)

        assert sample_refactor_artifact["spec_id"] in summary

    def test_summary_includes_file_count(self, sample_refactor_artifact):
        """Summary includes file count."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        summary = executor._generate_summary(sample_refactor_artifact)

        assert "Files" in summary or "file" in summary.lower()

    def test_summary_includes_test_results(self, sample_refactor_artifact):
        """Summary includes test results."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        summary = executor._generate_summary(sample_refactor_artifact)

        assert "Test" in summary or "passed" in summary.lower()


class TestDeliverPhaseGitOperations:
    """Tests for DELIVER phase git operations."""

    def test_stages_multiple_files(self, sample_refactor_artifact, temp_git_project):
        """Stages multiple files for commit."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        # Create files to stage
        (temp_git_project / "src" / "auth" / "oauth_provider.py").write_text("# test1")
        (temp_git_project / "src" / "auth" / "token_manager.py").write_text("# test2")

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)

            files = [
                "src/auth/oauth_provider.py",
                "src/auth/token_manager.py",
            ]
            staged = executor._stage_files(context, files)

        assert len(staged) == 2

    def test_handles_staging_failure(self, sample_refactor_artifact, temp_git_project):
        """Handles file staging failure."""
        import subprocess

        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = subprocess.CalledProcessError(1, "git add")

            staged = executor._stage_files(context, ["nonexistent.py"])

        # Should handle gracefully and return empty list
        assert staged == []

    def test_gets_commit_sha(self, sample_refactor_artifact, temp_git_project):
        """Gets commit SHA after creating commit."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = [
                Mock(returncode=0),  # git commit
                Mock(returncode=0, stdout="abc123def456\n"),  # git rev-parse
            ]

            sha = executor._create_commit(context, "Test commit")

        assert sha == "abc123def456"


class TestDeliverPhaseValidation:
    """Tests for DELIVER phase artifact validation."""

    def test_validates_deliverable_type_present(self):
        """Validates that deliverable_type is present."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "files_modified": ["file.py"],
            "summary": "Test summary",
            # Missing deliverable_type
        }

        validation = executor.validate_output(artifact)

        assert not validation.valid

    def test_validates_files_modified_present(self):
        """Validates that files_modified is present."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "deliverable_type": "commit",
            "summary": "Test summary",
            # Missing files_modified
        }

        validation = executor.validate_output(artifact)

        # Should fail or warn
        assert not validation.valid or len(validation.warnings) > 0


class TestDeliverPhaseEdgeCases:
    """Tests for DELIVER phase edge cases."""

    def test_handles_empty_final_files(self, temp_git_project):
        """Handles input with empty final files."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.FILES})

        artifact = {
            "spec_id": "SPEC-123",
            "final_files": [],
        }

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=artifact,
            config={},
        )

        result = executor.execute(context)

        # Should handle gracefully
        assert result.status == StageStatus.COMPLETED

    def test_handles_dict_file_entries(self, sample_refactor_artifact, temp_git_project):
        """Handles file entries that are dicts with 'path' key."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "final_files": [
                {"path": "file1.py", "content": "..."},
                {"path": "file2.py", "content": "..."},
            ],
        }

        StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_git_project,
            input_artifacts=artifact,
            config={},
        )

        summary = executor._generate_summary(artifact)

        # Should handle dict entries
        assert "file1.py" in summary or "Files" in summary

    def test_handles_git_not_available(self, sample_refactor_artifact, temp_project_path):
        """Handles case where git is not available."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        executor = DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_project_path,
            input_artifacts=sample_refactor_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError("git not found")

            staged = executor._stage_files(context, ["file.py"])

        # Should handle gracefully
        assert staged == []


class TestCreateDeliverExecutor:
    """Tests for factory function."""

    def test_creates_executor_instance(self):
        """Factory creates DeliverPhaseExecutor instance."""
        from agentforge.core.pipeline.stages.deliver import (
            DeliverPhaseExecutor,
            create_deliver_executor,
        )

        executor = create_deliver_executor()

        assert isinstance(executor, DeliverPhaseExecutor)

    def test_passes_config(self):
        """Factory passes config to executor."""
        from agentforge.core.pipeline.stages.deliver import (
            DeliveryMode,
            create_deliver_executor,
        )

        config = {"delivery_mode": DeliveryMode.PR, "auto_commit": True}

        executor = create_deliver_executor(config)

        assert executor.delivery_mode == DeliveryMode.PR
        assert executor.auto_commit is True
