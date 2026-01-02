# @spec_file: .agentforge/specs/core-cicd-v1.yaml
# @spec_id: core-cicd-v1
# @component_id: tools-cicd-baseline
# @impl_path: tools/cicd/baseline.py

"""Unit tests for baseline management."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentforge.core.cicd.baseline import BaselineError, BaselineManager, GitError, GitHelper
from agentforge.core.cicd.domain import CIViolation


class TestBaselineManager:
    """Tests for BaselineManager."""

    @pytest.fixture
    def temp_baseline_dir(self, tmp_path):
        """Create temporary directory for baseline files."""
        return tmp_path

    @pytest.fixture
    def manager(self, temp_baseline_dir):
        """Create baseline manager with temp directory."""
        baseline_path = temp_baseline_dir / ".agentforge" / "baseline.json"
        return BaselineManager(str(baseline_path))

    @pytest.fixture
    def sample_violations(self):
        """Create sample violations for testing."""
        return [
            CIViolation(check_id="check1", file_path="file1.py", line=10, message="msg1", severity="error"),
            CIViolation(check_id="check2", file_path="file2.py", line=20, message="msg2", severity="warning"),
        ]

    def test_load_nonexistent(self, manager):
        """Test loading nonexistent baseline returns None."""
        result = manager.load()
        assert result is None

    def test_exists_false_when_no_file(self, manager):
        """Test exists returns False when no baseline file."""
        assert manager.exists() is False

    def test_save_and_load(self, manager, sample_violations):
        """Test saving and loading baseline."""
        baseline = manager.create_from_violations(sample_violations, "abc123")
        manager.save(baseline)

        assert manager.exists()

        loaded = manager.load()
        assert loaded is not None
        assert loaded.commit_sha == "abc123"
        assert len(loaded.entries) == 2

    def test_create_from_violations(self, manager, sample_violations):
        """Test creating baseline from violations."""
        baseline = manager.create_from_violations(sample_violations, "sha123")

        assert len(baseline.entries) == 2
        assert baseline.commit_sha == "sha123"
        for violation in sample_violations:
            assert baseline.contains(violation)

    def test_compare_success(self, manager, sample_violations):
        """Test comparing violations against baseline."""
        # Save initial baseline
        baseline = manager.create_from_violations(sample_violations, "sha123")
        manager.save(baseline)

        # Compare with same violations
        comparison = manager.compare(sample_violations)

        assert len(comparison.new_violations) == 0
        assert len(comparison.fixed_violations) == 0
        assert len(comparison.existing_violations) == 2

    def test_compare_with_new_violation(self, manager, sample_violations):
        """Test comparing with a new violation."""
        # Save initial baseline
        baseline = manager.create_from_violations(sample_violations, "sha123")
        manager.save(baseline)

        # Add new violation
        new_violations = sample_violations + [
            CIViolation(check_id="check3", file_path="file3.py", line=30, message="new", severity="error"),
        ]

        comparison = manager.compare(new_violations)

        assert len(comparison.new_violations) == 1
        assert comparison.new_violations[0].check_id == "check3"

    def test_compare_no_baseline_raises(self, manager, sample_violations):
        """Test comparing when baseline doesn't exist raises error."""
        with pytest.raises(BaselineError, match="Baseline not found"):
            manager.compare(sample_violations)

    def test_update_adds_new_violations(self, manager, sample_violations):
        """Test update adds new violations."""
        # Save initial baseline
        baseline = manager.create_from_violations(sample_violations[:1], "sha1")
        manager.save(baseline)

        # Update with more violations
        updated, added, removed = manager.update(sample_violations, "sha2")

        assert added == 1
        assert removed == 0
        assert len(updated.entries) == 2

    def test_update_removes_fixed(self, manager, sample_violations):
        """Test update removes fixed violations."""
        # Save initial baseline
        baseline = manager.create_from_violations(sample_violations, "sha1")
        manager.save(baseline)

        # Update with fewer violations
        updated, added, removed = manager.update([sample_violations[0]], "sha2")

        assert added == 0
        assert removed == 1
        assert len(updated.entries) == 1

    def test_get_stats(self, manager, sample_violations):
        """Test getting baseline statistics."""
        baseline = manager.create_from_violations(sample_violations, "sha123")
        manager.save(baseline)

        stats = manager.get_stats()

        assert stats is not None
        assert stats["total_entries"] == 2
        assert stats["commit_sha"] == "sha123"
        assert "by_check" in stats
        assert "by_file" in stats

    def test_get_stats_no_baseline(self, manager):
        """Test get_stats returns None when no baseline."""
        stats = manager.get_stats()
        assert stats is None

    def test_load_corrupted_baseline(self, manager, temp_baseline_dir):
        """Test loading corrupted baseline raises error."""
        # Create invalid JSON file
        baseline_path = temp_baseline_dir / ".agentforge" / "baseline.json"
        baseline_path.parent.mkdir(parents=True)
        baseline_path.write_text("not valid json")

        with pytest.raises(BaselineError, match="Failed to load baseline"):
            manager.load()


class TestGitHelper:
    """Tests for GitHelper."""

    @patch("subprocess.run")
    def test_get_changed_files(self, mock_run):
        """Test getting changed files from git."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="file1.py\nfile2.py\ndir/file3.py\n"
        )

        files = GitHelper.get_changed_files("origin/main", "HEAD")

        assert files == ["file1.py", "file2.py", "dir/file3.py"]
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_get_changed_files_empty(self, mock_run):
        """Test getting changed files when none changed."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=""
        )

        files = GitHelper.get_changed_files("origin/main", "HEAD")

        assert files == []

    @patch("subprocess.run")
    def test_get_changed_files_error(self, mock_run):
        """Test git error handling."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "git", stderr="error message")

        with pytest.raises(GitError, match="Failed to get changed files"):
            GitHelper.get_changed_files("origin/main", "HEAD")

    @patch("subprocess.run")
    def test_get_current_sha(self, mock_run):
        """Test getting current commit SHA."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def456\n"
        )

        sha = GitHelper.get_current_sha()

        assert sha == "abc123def456"

    @patch("subprocess.run")
    def test_get_current_branch(self, mock_run):
        """Test getting current branch name."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="feature/my-branch\n"
        )

        branch = GitHelper.get_current_branch()

        assert branch == "feature/my-branch"

    @patch("subprocess.run")
    def test_is_git_repo_true(self, mock_run):
        """Test is_git_repo returns True for git repos."""
        mock_run.return_value = MagicMock(returncode=0)

        assert GitHelper.is_git_repo() is True

    @patch("subprocess.run")
    def test_is_git_repo_false(self, mock_run):
        """Test is_git_repo returns False for non-repos."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "git")

        assert GitHelper.is_git_repo() is False

    @patch("subprocess.run")
    def test_get_merge_base(self, mock_run):
        """Test getting merge base."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="deadbeef123\n"
        )

        result = GitHelper.get_merge_base("origin/main", "HEAD")

        assert result == "deadbeef123"

    @patch("subprocess.run")
    def test_get_repo_root(self, mock_run):
        """Test getting repo root."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/path/to/repo\n"
        )

        root = GitHelper.get_repo_root()

        assert root == Path("/path/to/repo")

    @patch("subprocess.run")
    def test_file_exists_at_ref_true(self, mock_run):
        """Test file existence check at ref."""
        mock_run.return_value = MagicMock(returncode=0)

        assert GitHelper.file_exists_at_ref("file.py", "HEAD") is True

    @patch("subprocess.run")
    def test_file_exists_at_ref_false(self, mock_run):
        """Test file doesn't exist at ref."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "git")

        assert GitHelper.file_exists_at_ref("file.py", "HEAD") is False
