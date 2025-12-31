"""Unit tests for CI/CD domain entities."""

import pytest
from datetime import datetime, timedelta

from tools.cicd.domain import (
    CIMode,
    ExitCode,
    CIViolation,
    BaselineEntry,
    Baseline,
    BaselineComparison,
    CIResult,
    CIConfig,
)


class TestCIMode:
    """Tests for CIMode enum."""

    def test_mode_values(self):
        """Test mode enum values."""
        assert CIMode.FULL.value == "full"
        assert CIMode.INCREMENTAL.value == "incremental"
        assert CIMode.PR.value == "pr"


class TestExitCode:
    """Tests for ExitCode enum."""

    def test_exit_code_values(self):
        """Test exit code integer values."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.VIOLATIONS_FOUND == 1
        assert ExitCode.CONFIG_ERROR == 2
        assert ExitCode.RUNTIME_ERROR == 3
        assert ExitCode.BASELINE_NOT_FOUND == 4

    def test_exit_code_description(self):
        """Test exit code descriptions."""
        assert "Success" in ExitCode.SUCCESS.description
        assert "Violations" in ExitCode.VIOLATIONS_FOUND.description
        assert "Configuration" in ExitCode.CONFIG_ERROR.description


class TestCIViolation:
    """Tests for CIViolation dataclass."""

    @pytest.fixture
    def sample_violation(self):
        """Create sample violation for testing."""
        return CIViolation(
            check_id="naming-check",
            file_path="src/main.py",
            line=42,
            message="Variable name does not match pattern",
            severity="error",
            rule_id="PY001",
            contract_id="python-standards",
            fix_hint="Use snake_case for variable names",
        )

    def test_hash_deterministic(self, sample_violation):
        """Test that hash is deterministic."""
        hash1 = sample_violation.hash
        hash2 = sample_violation.hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated SHA256

    def test_hash_differs_for_different_violations(self, sample_violation):
        """Test that different violations have different hashes."""
        other = CIViolation(
            check_id="other-check",
            file_path="src/main.py",
            line=42,
            message="Different message",
            severity="error",
        )
        assert sample_violation.hash != other.hash

    def test_hash_same_for_equivalent_violations(self):
        """Test that equivalent violations have same hash."""
        v1 = CIViolation(
            check_id="check1",
            file_path="file.py",
            line=10,
            message="msg",
            severity="error",
        )
        v2 = CIViolation(
            check_id="check1",
            file_path="file.py",
            line=10,
            message="msg",
            severity="warning",  # Different severity doesn't affect hash
        )
        assert v1.hash == v2.hash

    def test_to_sarif_result(self, sample_violation):
        """Test SARIF result generation."""
        sarif = sample_violation.to_sarif_result()

        assert sarif["ruleId"] == "PY001"
        assert sarif["level"] == "error"
        assert sarif["message"]["text"] == "Variable name does not match pattern"
        assert len(sarif["locations"]) == 1
        assert sarif["locations"][0]["physicalLocation"]["region"]["startLine"] == 42
        assert "fixes" in sarif  # Has fix hint
        assert "partialFingerprints" in sarif

    def test_to_sarif_result_warning_level(self):
        """Test SARIF level mapping for warning."""
        violation = CIViolation(
            check_id="check",
            file_path="file.py",
            line=1,
            message="msg",
            severity="warning",
        )
        sarif = violation.to_sarif_result()
        assert sarif["level"] == "warning"

    def test_to_sarif_result_info_level(self):
        """Test SARIF level mapping for info."""
        violation = CIViolation(
            check_id="check",
            file_path="file.py",
            line=1,
            message="msg",
            severity="info",
        )
        sarif = violation.to_sarif_result()
        assert sarif["level"] == "note"

    def test_to_junit_testcase(self, sample_violation):
        """Test JUnit testcase generation."""
        testcase = sample_violation.to_junit_testcase("TestSuite")

        assert "naming-check" in testcase["name"]
        assert "src/main.py:42" in testcase["name"]
        assert testcase["classname"] == "TestSuite"
        assert "failure" in testcase
        assert testcase["failure"]["type"] == "error"


class TestBaseline:
    """Tests for Baseline dataclass."""

    @pytest.fixture
    def empty_baseline(self):
        """Create empty baseline for testing."""
        return Baseline.create_empty("abc123")

    @pytest.fixture
    def sample_violation(self):
        """Create sample violation for testing."""
        return CIViolation(
            check_id="check1",
            file_path="file.py",
            line=10,
            message="Test message",
            severity="error",
        )

    def test_create_empty(self, empty_baseline):
        """Test creating empty baseline."""
        assert empty_baseline.schema_version == "1.0"
        assert empty_baseline.commit_sha == "abc123"
        assert len(empty_baseline.entries) == 0

    def test_add_violation(self, empty_baseline, sample_violation):
        """Test adding violation to baseline."""
        empty_baseline.add(sample_violation)

        assert len(empty_baseline.entries) == 1
        assert empty_baseline.contains(sample_violation)

    def test_contains(self, empty_baseline, sample_violation):
        """Test checking if violation is in baseline."""
        assert not empty_baseline.contains(sample_violation)

        empty_baseline.add(sample_violation)
        assert empty_baseline.contains(sample_violation)

    def test_remove(self, empty_baseline, sample_violation):
        """Test removing violation from baseline."""
        empty_baseline.add(sample_violation)
        assert empty_baseline.contains(sample_violation)

        result = empty_baseline.remove(sample_violation.hash)
        assert result is True
        assert not empty_baseline.contains(sample_violation)

    def test_remove_nonexistent(self, empty_baseline):
        """Test removing nonexistent violation."""
        result = empty_baseline.remove("nonexistent-hash")
        assert result is False

    def test_to_dict_from_dict_roundtrip(self, empty_baseline, sample_violation):
        """Test serialization roundtrip."""
        empty_baseline.add(sample_violation)

        data = empty_baseline.to_dict()
        restored = Baseline.from_dict(data)

        assert restored.schema_version == empty_baseline.schema_version
        assert restored.commit_sha == empty_baseline.commit_sha
        assert len(restored.entries) == len(empty_baseline.entries)
        assert restored.contains(sample_violation)


class TestBaselineComparison:
    """Tests for BaselineComparison dataclass."""

    @pytest.fixture
    def baseline_with_violations(self):
        """Create baseline with some violations."""
        baseline = Baseline.create_empty()
        violations = [
            CIViolation(check_id="check1", file_path="file1.py", line=1, message="msg1", severity="error"),
            CIViolation(check_id="check2", file_path="file2.py", line=2, message="msg2", severity="warning"),
            CIViolation(check_id="check3", file_path="file3.py", line=3, message="msg3", severity="error"),
        ]
        for v in violations:
            baseline.add(v)
        return baseline

    def test_compare_no_changes(self, baseline_with_violations):
        """Test comparison when violations unchanged."""
        current = [
            CIViolation(check_id="check1", file_path="file1.py", line=1, message="msg1", severity="error"),
            CIViolation(check_id="check2", file_path="file2.py", line=2, message="msg2", severity="warning"),
            CIViolation(check_id="check3", file_path="file3.py", line=3, message="msg3", severity="error"),
        ]

        comparison = BaselineComparison.compare(current, baseline_with_violations)

        assert len(comparison.new_violations) == 0
        assert len(comparison.fixed_violations) == 0
        assert len(comparison.existing_violations) == 3
        assert comparison.net_change == 0
        assert not comparison.introduces_violations
        assert not comparison.has_improvements

    def test_compare_new_violations(self, baseline_with_violations):
        """Test comparison with new violations."""
        current = [
            CIViolation(check_id="check1", file_path="file1.py", line=1, message="msg1", severity="error"),
            CIViolation(check_id="check2", file_path="file2.py", line=2, message="msg2", severity="warning"),
            CIViolation(check_id="check3", file_path="file3.py", line=3, message="msg3", severity="error"),
            CIViolation(check_id="check4", file_path="file4.py", line=4, message="new violation", severity="error"),
        ]

        comparison = BaselineComparison.compare(current, baseline_with_violations)

        assert len(comparison.new_violations) == 1
        assert comparison.new_violations[0].check_id == "check4"
        assert len(comparison.fixed_violations) == 0
        assert comparison.net_change == 1
        assert comparison.introduces_violations

    def test_compare_fixed_violations(self, baseline_with_violations):
        """Test comparison with fixed violations."""
        current = [
            CIViolation(check_id="check1", file_path="file1.py", line=1, message="msg1", severity="error"),
        ]

        comparison = BaselineComparison.compare(current, baseline_with_violations)

        assert len(comparison.new_violations) == 0
        assert len(comparison.fixed_violations) == 2  # check2 and check3 fixed
        assert len(comparison.existing_violations) == 1
        assert comparison.net_change == -2
        assert comparison.has_improvements

    def test_should_fail_on_new_errors(self, baseline_with_violations):
        """Test should_fail with new errors."""
        current = [
            CIViolation(check_id="new", file_path="new.py", line=1, message="new error", severity="error"),
        ]

        comparison = BaselineComparison.compare(current, baseline_with_violations)

        assert comparison.should_fail(fail_on_new_errors=True, fail_on_new_warnings=False)

    def test_should_fail_on_new_warnings(self, baseline_with_violations):
        """Test should_fail with new warnings when configured."""
        current = [
            CIViolation(check_id="new", file_path="new.py", line=1, message="new warning", severity="warning"),
        ]

        comparison = BaselineComparison.compare(current, baseline_with_violations)

        assert not comparison.should_fail(fail_on_new_errors=True, fail_on_new_warnings=False)
        assert comparison.should_fail(fail_on_new_errors=True, fail_on_new_warnings=True)


class TestCIResult:
    """Tests for CIResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create sample CI result."""
        now = datetime.utcnow()
        return CIResult(
            mode=CIMode.FULL,
            exit_code=ExitCode.SUCCESS,
            violations=[
                CIViolation(check_id="c1", file_path="f1.py", line=1, message="m1", severity="error"),
                CIViolation(check_id="c2", file_path="f1.py", line=2, message="m2", severity="warning"),
                CIViolation(check_id="c3", file_path="f2.py", line=1, message="m3", severity="info"),
            ],
            comparison=None,
            files_checked=10,
            checks_run=5,
            duration_seconds=1.5,
            started_at=now - timedelta(seconds=2),
            completed_at=now,
        )

    def test_violation_counts(self, sample_result):
        """Test violation count properties."""
        assert sample_result.total_violations == 3
        assert sample_result.error_count == 1
        assert sample_result.warning_count == 1
        assert sample_result.info_count == 1

    def test_is_success(self, sample_result):
        """Test is_success property."""
        assert sample_result.is_success

        failed = CIResult(
            mode=CIMode.FULL,
            exit_code=ExitCode.VIOLATIONS_FOUND,
            violations=[],
            comparison=None,
            files_checked=0,
            checks_run=0,
            duration_seconds=0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        assert not failed.is_success

    def test_get_violations_by_file(self, sample_result):
        """Test grouping violations by file."""
        by_file = sample_result.get_violations_by_file()

        assert "f1.py" in by_file
        assert "f2.py" in by_file
        assert len(by_file["f1.py"]) == 2
        assert len(by_file["f2.py"]) == 1

    def test_get_violations_by_check(self, sample_result):
        """Test grouping violations by check."""
        by_check = sample_result.get_violations_by_check()

        assert "c1" in by_check
        assert "c2" in by_check
        assert "c3" in by_check

    def test_to_summary_dict(self, sample_result):
        """Test summary dict generation."""
        summary = sample_result.to_summary_dict()

        assert summary["mode"] == "full"
        assert summary["exit_code"] == 0
        assert summary["total_violations"] == 3
        assert summary["errors"] == 1
        assert summary["warnings"] == 1
        assert summary["files_checked"] == 10
        assert summary["checks_run"] == 5


class TestCIConfig:
    """Tests for CIConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = CIConfig()

        assert config.mode == CIMode.FULL
        assert config.parallel_enabled is True
        assert config.max_workers == 4
        assert config.fail_on_new_errors is True
        assert config.fail_on_new_warnings is False

    def test_for_github_actions(self):
        """Test GitHub Actions preset."""
        config = CIConfig.for_github_actions()

        assert config.mode == CIMode.PR
        assert config.output_sarif is True
        assert config.output_junit is False
        assert config.output_markdown is True

    def test_for_azure_devops(self):
        """Test Azure DevOps preset."""
        config = CIConfig.for_azure_devops()

        assert config.mode == CIMode.PR
        assert config.output_sarif is False
        assert config.output_junit is True
        assert config.output_markdown is True

    def test_to_dict_from_dict_roundtrip(self):
        """Test configuration serialization roundtrip."""
        config = CIConfig(
            mode=CIMode.INCREMENTAL,
            parallel_enabled=False,
            max_workers=2,
            fail_on_new_warnings=True,
        )

        data = config.to_dict()
        restored = CIConfig.from_dict(data)

        assert restored.mode == config.mode
        assert restored.parallel_enabled == config.parallel_enabled
        assert restored.max_workers == config.max_workers
        assert restored.fail_on_new_warnings == config.fail_on_new_warnings
