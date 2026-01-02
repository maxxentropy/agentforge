"""Unit tests for CI runner."""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from agentforge.core.cicd.domain import (
    Baseline,
    CIConfig,
    CIMode,
    CIViolation,
    ExitCode,
)
from agentforge.core.cicd.runner import CheckCache, CIRunner


class TestCheckCache:
    """Tests for CheckCache."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        return tmp_path / ".agentforge" / "cache"

    @pytest.fixture
    def cache(self, cache_dir):
        """Create cache instance."""
        return CheckCache(cache_dir, ttl_hours=1)

    @pytest.fixture
    def sample_violations(self):
        """Create sample violations for caching."""
        return [
            CIViolation(
                check_id="check1",
                file_path="file1.py",
                line=10,
                message="msg1",
                severity="error",
            ),
        ]

    def test_get_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("nonexistent-key")
        assert result is None

    def test_set_and_get(self, cache, sample_violations):
        """Test setting and getting cached value."""
        cache.set("test-key", sample_violations)
        result = cache.get("test-key")

        assert result is not None
        assert len(result) == 1
        assert result[0].check_id == "check1"

    def test_cache_expiration(self, cache, sample_violations):
        """Test expired cache entries return None."""
        # Set with normal TTL
        cache.set("test-key", sample_violations)

        # Read immediately should work
        assert cache.get("test-key") is not None

        # Mock time passing - need to modify the cached_at in the file
        cache_file = cache.cache_dir / "test-key.json"
        data = json.loads(cache_file.read_text())
        data["cached_at"] = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        cache_file.write_text(json.dumps(data))

        # Now should be expired (TTL is 1 hour, we set cached_at to 2 hours ago)
        result = cache.get("test-key")
        assert result is None

    def test_clear(self, cache, sample_violations):
        """Test clearing cache."""
        cache.set("key1", sample_violations)
        cache.set("key2", sample_violations)

        count = cache.clear()

        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_prune_expired(self, cache, sample_violations):
        """Test pruning expired entries."""
        cache.set("key1", sample_violations)

        # Manually expire one entry
        cache_file = cache.cache_dir / "key1.json"
        data = json.loads(cache_file.read_text())
        data["cached_at"] = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        cache_file.write_text(json.dumps(data))

        count = cache.prune_expired()

        assert count == 1

    def test_clear_empty_cache(self, cache):
        """Test clearing empty cache returns 0."""
        count = cache.clear()
        assert count == 0

    def test_cache_creates_directory(self, cache_dir, sample_violations):
        """Test cache creates directory if it doesn't exist."""
        cache = CheckCache(cache_dir / "subdir")
        cache.set("key", sample_violations)

        assert (cache_dir / "subdir" / "key.json").exists()


class TestCIRunner:
    """Tests for CIRunner."""

    @pytest.fixture
    def repo_root(self, tmp_path):
        """Create temporary repo root."""
        (tmp_path / ".agentforge").mkdir()
        return tmp_path

    @pytest.fixture
    def sample_contracts(self):
        """Create sample contracts for testing."""
        return [
            {
                "id": "test-contract",
                "name": "Test Contract",
                "checks": [
                    {
                        "id": "check1",
                        "type": "regex",
                        "name": "Test Check",
                        "severity": "error",
                        "applies_to": {"paths": ["**/*.py"]},
                        "config": {"pattern": "TODO", "mode": "forbid"},
                    }
                ]
            }
        ]

    @pytest.fixture
    def runner(self, repo_root):
        """Create CI runner."""
        config = CIConfig(mode=CIMode.FULL, cache_enabled=False)
        return CIRunner(repo_root, config)

    def test_runner_init(self, runner, repo_root):
        """Test runner initialization."""
        assert runner.repo_root == repo_root
        assert runner.config.mode == CIMode.FULL

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_run_full_mode(self, mock_execute, runner, sample_contracts):
        """Test running in full mode."""
        mock_execute.return_value = []

        result = runner.run(sample_contracts)

        assert result.mode == CIMode.FULL
        assert result.exit_code == ExitCode.SUCCESS

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_run_with_violations(self, mock_execute, runner, sample_contracts):
        """Test running with violations returns failure."""
        mock_execute.return_value = [
            CIViolation(
                check_id="check1",
                file_path="file.py",
                line=10,
                message="Found TODO",
                severity="error",
            )
        ]

        result = runner.run(sample_contracts)

        assert result.exit_code == ExitCode.VIOLATIONS_FOUND
        assert len(result.violations) == 1

    def test_config_parallel_settings(self, repo_root):
        """Test parallel configuration is respected."""
        config = CIConfig(parallel_enabled=False, max_workers=2)
        runner = CIRunner(repo_root, config)

        assert runner.config.parallel_enabled is False
        assert runner.config.max_workers == 2

    def test_config_fail_thresholds(self, repo_root):
        """Test fail threshold configuration."""
        config = CIConfig(fail_on_new_errors=True, fail_on_new_warnings=True)
        runner = CIRunner(repo_root, config)

        assert runner.config.fail_on_new_errors is True
        assert runner.config.fail_on_new_warnings is True

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    @patch("agentforge.core.cicd.runner.GitHelper.get_changed_files")
    def test_incremental_mode_filters_files(self, mock_git, mock_execute, repo_root, sample_contracts):
        """Test incremental mode filters to changed files."""
        mock_git.return_value = ["changed.py"]
        mock_execute.return_value = []

        config = CIConfig(mode=CIMode.INCREMENTAL, base_ref="origin/main", cache_enabled=False)
        runner = CIRunner(repo_root, config)

        result = runner.run(sample_contracts)

        assert result.mode == CIMode.INCREMENTAL
        mock_git.assert_called_once()

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_pr_mode_uses_baseline(self, mock_execute, repo_root, sample_contracts):
        """Test PR mode compares against baseline."""
        # Create a real baseline file
        baseline_path = repo_root / ".agentforge" / "baseline.json"
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline = Baseline.create_empty()
        baseline_path.write_text(json.dumps(baseline.to_dict()))

        mock_execute.return_value = []

        config = CIConfig(mode=CIMode.PR, cache_enabled=False)
        runner = CIRunner(repo_root, config)

        result = runner.run(sample_contracts)

        assert result.mode == CIMode.PR
        assert result.comparison is not None

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_result_includes_timing(self, mock_execute, runner, sample_contracts):
        """Test result includes timing information."""
        mock_execute.return_value = []

        result = runner.run(sample_contracts)

        assert result.duration_seconds >= 0
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.started_at

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    @patch("agentforge.core.cicd.runner.GitHelper.get_current_sha")
    def test_result_includes_commit_sha(self, mock_sha, mock_execute, runner, sample_contracts):
        """Test result includes commit SHA when available."""
        mock_sha.return_value = "abc123"
        mock_execute.return_value = []

        result = runner.run(sample_contracts)

        assert result.commit_sha == "abc123"

    def test_contract_applies_to_files_matching(self, runner):
        """Test contract pattern matching."""
        # Use patterns compatible with PurePath.match()
        contract = {
            "id": "test",
            "checks": [{
                "id": "check",
                "applies_to": {"paths": ["**/*.py"]}  # Match any .py file
            }]
        }

        assert runner._contract_applies_to_files(contract, {"src/main.py"})
        assert runner._contract_applies_to_files(contract, {"src/sub/file.py"})
        assert runner._contract_applies_to_files(contract, {"test/main.py"})
        assert not runner._contract_applies_to_files(contract, {"test/main.js"})

    def test_contract_applies_excludes(self, runner):
        """Test contract exclusion patterns."""
        contract = {
            "id": "test",
            "checks": [{
                "id": "check",
                "applies_to": {
                    "paths": ["**/*.py"],
                    "exclude_paths": ["tests/**"]
                }
            }]
        }

        assert runner._contract_applies_to_files(contract, {"src/main.py"})
        assert not runner._contract_applies_to_files(contract, {"tests/test_main.py"})

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_exit_code_success_no_violations(self, mock_execute, runner, sample_contracts):
        """Test SUCCESS exit code when no violations."""
        mock_execute.return_value = []

        result = runner.run(sample_contracts)

        assert result.exit_code == ExitCode.SUCCESS

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_exit_code_violations_found(self, mock_execute, runner, sample_contracts):
        """Test VIOLATIONS_FOUND exit code with errors."""
        mock_execute.return_value = [
            CIViolation(check_id="c", file_path="f", line=1, message="m", severity="error")
        ]

        result = runner.run(sample_contracts)

        assert result.exit_code == ExitCode.VIOLATIONS_FOUND

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_warnings_dont_fail_by_default(self, mock_execute, runner, sample_contracts):
        """Test warnings don't cause failure by default."""
        mock_execute.return_value = [
            CIViolation(check_id="c", file_path="f", line=1, message="m", severity="warning")
        ]

        result = runner.run(sample_contracts)

        assert result.exit_code == ExitCode.SUCCESS

    @patch("agentforge.core.cicd.runner.CIRunner._execute_checks")
    def test_warnings_fail_when_configured(self, mock_execute, repo_root, sample_contracts):
        """Test warnings cause failure when configured."""
        config = CIConfig(fail_on_new_warnings=True, cache_enabled=False)
        runner = CIRunner(repo_root, config)

        mock_execute.return_value = [
            CIViolation(check_id="c", file_path="f", line=1, message="m", severity="warning")
        ]

        result = runner.run(sample_contracts)

        assert result.exit_code == ExitCode.VIOLATIONS_FOUND

    def test_error_result_on_baseline_not_found(self, repo_root, sample_contracts):
        """Test BASELINE_NOT_FOUND when baseline missing in PR mode."""
        config = CIConfig(mode=CIMode.PR, cache_enabled=False)
        runner = CIRunner(repo_root, config)

        # No baseline file exists
        with patch("agentforge.core.cicd.runner.CIRunner._execute_checks", return_value=[]):
            result = runner.run(sample_contracts)

        assert result.exit_code == ExitCode.BASELINE_NOT_FOUND
