# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: tools-harness-violation_tools
# @impl_path: tools/harness/violation_tools.py

"""
Tests for Self-Hosting Tools
=============================

Tests for violation, git, and test runner tools used in self-hosting workflow.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from agentforge.core.harness.conformance_tools import ConformanceTools
from agentforge.core.harness.git_tools import GitTools
from agentforge.core.harness.test_runner_tools import RunnerTools
from agentforge.core.harness.violation_tools import ViolationInfo, ViolationTools


class TestViolationInfo:
    """Tests for ViolationInfo dataclass."""

    def test_to_summary(self):
        info = ViolationInfo(
            violation_id="V-test123",
            contract_id="agentforge",
            check_id="commands-have-help",
            severity="major",
            file_path="cli/test.py",
            message="Missing help parameter",
            fix_hint="Add help='description'",
            status="open",
            detected_at="2025-01-01T00:00:00",
        )

        summary = info.to_summary()

        assert "V-test123" in summary, "Expected 'V-test123' in summary"
        assert "major" in summary, "Expected 'major' in summary"
        assert "commands-have-help" in summary, "Expected 'commands-have-help' in summary"
        assert "Add help='description'" in summary, "Expected \"Add help='description'\" in summary"

    def test_to_dict_round_trip(self):
        original = ViolationInfo(
            violation_id="V-test123",
            contract_id="agentforge",
            check_id="commands-have-help",
            severity="major",
            file_path="cli/test.py",
            message="Missing help parameter",
            fix_hint="Add help='description'",
            status="open",
            detected_at="2025-01-01T00:00:00",
        )

        data = original.to_dict()
        restored = ViolationInfo.from_dict(data)

        assert restored.violation_id == original.violation_id, "Expected restored.violation_id to equal original.violation_id"
        assert restored.severity == original.severity, "Expected restored.severity to equal original.severity"
        assert restored.fix_hint == original.fix_hint, "Expected restored.fix_hint to equal original.fix_hint"


class TestViolationTools:
    """Tests for ViolationTools."""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            violations_dir = project / ".agentforge" / "violations"
            violations_dir.mkdir(parents=True)

            # Create sample violation
            violation = {
                "violation_id": "V-test123",
                "contract_id": "agentforge",
                "check_id": "commands-have-help",
                "severity": "major",
                "file_path": "cli/test.py",
                "message": "Missing help parameter",
                "fix_hint": "Add help='description'",
                "status": "open",
                "detected_at": "2025-01-01T00:00:00",
            }

            with open(violations_dir / "V-test123.yaml", "w") as f:
                yaml.dump(violation, f)

            # Create source file
            (project / "cli").mkdir()
            (project / "cli/test.py").write_text("# test file\ndef foo(): pass")

            yield project

    def test_read_violation(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.read_violation("read_violation", {"violation_id": "V-test123"})

        assert result.success, "Expected result.success to be truthy"
        assert "V-test123" in result.output, "Expected 'V-test123' in result.output"
        assert "major" in result.output, "Expected 'major' in result.output"
        assert "commands-have-help" in result.output, "Expected 'commands-have-help' in result.output"

    def test_read_violation_without_prefix(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.read_violation("read_violation", {"violation_id": "test123"})

        assert result.success, "Expected result.success to be truthy"
        assert "V-test123" in result.output, "Expected 'V-test123' in result.output"

    def test_read_violation_not_found(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.read_violation(
            "read_violation", {"violation_id": "V-nonexistent"}
        )

        assert not result.success, "Assertion failed"
        assert "not found" in result.error.lower(), "Expected 'not found' in result.error.lower()"

    def test_read_violation_missing_param(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.read_violation("read_violation", {})

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_list_violations(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.list_violations("list_violations", {"status": "open"})

        assert result.success, "Expected result.success to be truthy"
        assert "V-test123" in result.output, "Expected 'V-test123' in result.output"
        assert "1 violations" in result.output, "Expected '1 violations' in result.output"

    def test_list_violations_with_severity_filter(self, temp_project):
        tools = ViolationTools(temp_project)

        # Should find it with major
        result = tools.list_violations(
            "list_violations", {"status": "open", "severity": "major"}
        )
        assert result.success, "Expected result.success to be truthy"
        assert "V-test123" in result.output, "Expected 'V-test123' in result.output"

        # Should not find it with minor
        result = tools.list_violations(
            "list_violations", {"status": "open", "severity": "minor"}
        )
        assert result.success, "Expected result.success to be truthy"
        assert "No violations found" in result.output, "Expected 'No violations found' in result.output"

    def test_list_violations_empty(self, temp_project):
        # Create project without violations
        empty_project = Path(temp_project) / "empty"
        empty_project.mkdir()

        tools = ViolationTools(empty_project)
        result = tools.list_violations("list_violations", {})

        assert result.success, "Expected result.success to be truthy"
        assert "No violations directory" in result.output, "Expected 'No violations directory' in result.output"

    def test_get_violation_context(self, temp_project):
        tools = ViolationTools(temp_project)
        result = tools.get_violation_context(
            "get_violation_context", {"violation_id": "V-test123"}
        )

        assert result.success, "Expected result.success to be truthy"
        assert "VIOLATION DETAILS" in result.output, "Expected 'VIOLATION DETAILS' in result.output"
        assert "FILE CONTENT" in result.output, "Expected 'FILE CONTENT' in result.output"
        assert "# test file" in result.output, "Expected '# test file' in result.output"
        assert "def foo()" in result.output, "Expected 'def foo()' in result.output"

    def test_get_tool_executors(self, temp_project):
        tools = ViolationTools(temp_project)
        executors = tools.get_tool_executors()

        assert "read_violation" in executors, "Expected 'read_violation' in executors"
        assert "list_violations" in executors, "Expected 'list_violations' in executors"
        assert "get_violation_context" in executors, "Expected 'get_violation_context' in executors"
        assert callable(executors["read_violation"]), "Expected callable() to be truthy"


class TestGitTools:
    """Tests for GitTools."""

    @pytest.fixture
    def temp_git_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Initialize git repo
            subprocess.run(
                ["git", "init"], cwd=str(project), capture_output=True, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=str(project),
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=str(project),
                capture_output=True,
            )

            # Create initial commit
            (project / "README.md").write_text("# Test")
            subprocess.run(
                ["git", "add", "."], cwd=str(project), capture_output=True, check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=str(project),
                capture_output=True,
                check=True,
            )

            yield project

    def test_git_status_clean(self, temp_git_repo):
        tools = GitTools(temp_git_repo)
        result = tools.git_status("git_status", {})

        assert result.success, "Expected result.success to be truthy"
        assert "clean" in result.output.lower(), "Expected 'clean' in result.output.lower()"

    def test_git_status_with_changes(self, temp_git_repo):
        # Create a new file
        (temp_git_repo / "new_file.txt").write_text("hello")

        tools = GitTools(temp_git_repo)
        result = tools.git_status("git_status", {})

        assert result.success, "Expected result.success to be truthy"
        assert "new_file.txt" in result.output, "Expected 'new_file.txt' in result.output"

    def test_git_diff_no_changes(self, temp_git_repo):
        tools = GitTools(temp_git_repo)
        result = tools.git_diff("git_diff", {})

        assert result.success, "Expected result.success to be truthy"
        assert "No changes" in result.output, "Expected 'No changes' in result.output"

    def test_git_diff_with_changes(self, temp_git_repo):
        # Modify a file
        (temp_git_repo / "README.md").write_text("# Modified")

        tools = GitTools(temp_git_repo)
        result = tools.git_diff("git_diff", {})

        assert result.success, "Expected result.success to be truthy"
        assert "Modified" in result.output or "-# Test" in result.output, "Assertion failed"

    def test_git_log(self, temp_git_repo):
        tools = GitTools(temp_git_repo)
        result = tools.git_log("git_log", {"count": 5})

        assert result.success, "Expected result.success to be truthy"
        assert "Initial commit" in result.output, "Expected 'Initial commit' in result.output"

    def test_git_add(self, temp_git_repo):
        # Create a new file
        (temp_git_repo / "new_file.txt").write_text("hello")

        tools = GitTools(temp_git_repo)
        result = tools.git_add("git_add", {"files": ["new_file.txt"]})

        assert result.success, "Expected result.success to be truthy"
        assert "Staged" in result.output, "Expected 'Staged' in result.output"
        assert "new_file.txt" in result.output, "Expected 'new_file.txt' in result.output"

    def test_git_add_missing_files_param(self, temp_git_repo):
        tools = GitTools(temp_git_repo)
        result = tools.git_add("git_add", {})

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_git_commit_with_approval(self, temp_git_repo):
        # Create and stage a file
        (temp_git_repo / "new_file.txt").write_text("hello")
        subprocess.run(
            ["git", "add", "new_file.txt"],
            cwd=str(temp_git_repo),
            capture_output=True,
        )

        tools = GitTools(temp_git_repo, require_approval=True)
        result = tools.git_commit(
            "git_commit",
            {"message": "Add new file for testing purposes"},
        )

        assert result.success, "Expected result.success to be truthy"
        assert "staged for approval" in result.output, "Expected 'staged for approval' in result.output"
        assert tools.get_pending_commit() is not None, "Expected tools.get_pending_commit() is not None"

    def test_git_commit_without_approval(self, temp_git_repo):
        # Create and stage a file
        (temp_git_repo / "new_file.txt").write_text("hello")
        subprocess.run(
            ["git", "add", "new_file.txt"],
            cwd=str(temp_git_repo),
            capture_output=True,
        )

        tools = GitTools(temp_git_repo, require_approval=False)
        result = tools.git_commit(
            "git_commit",
            {"message": "Add new file for testing purposes"},
        )

        assert result.success, "Expected result.success to be truthy"
        assert "Committed" in result.output, "Expected 'Committed' in result.output"

    def test_git_commit_with_violation_id(self, temp_git_repo):
        tools = GitTools(temp_git_repo, require_approval=True)
        result = tools.git_commit(
            "git_commit",
            {"message": "Fix missing docstring", "violation_id": "V-test123"},
        )

        assert result.success, "Expected result.success to be truthy"
        pending = tools.get_pending_commit()
        assert "V-test123" in pending["message"], "Expected 'V-test123' in pending['message']"
        assert "fix(V-test123)" in pending["message"], "Expected 'fix(V-test123)' in pending['message']"

    def test_git_commit_message_too_short(self, temp_git_repo):
        tools = GitTools(temp_git_repo)
        result = tools.git_commit("git_commit", {"message": "short"})

        assert not result.success, "Assertion failed"
        assert "too short" in result.error.lower(), "Expected 'too short' in result.error.lower()"

    def test_apply_pending_commit(self, temp_git_repo):
        # Create and stage a file
        (temp_git_repo / "new_file.txt").write_text("hello")
        subprocess.run(
            ["git", "add", "new_file.txt"],
            cwd=str(temp_git_repo),
            capture_output=True,
        )

        tools = GitTools(temp_git_repo, require_approval=True)
        tools.git_commit("git_commit", {"message": "Add new file for testing purposes"})

        # Now apply the pending commit
        result = tools.apply_pending_commit()

        assert result.success, "Expected result.success to be truthy"
        assert "Committed" in result.output, "Expected 'Committed' in result.output"
        assert tools.get_pending_commit() == {}, "Expected tools.get_pending_commit() to equal {}"

    def test_get_tool_executors(self, temp_git_repo):
        tools = GitTools(temp_git_repo)
        executors = tools.get_tool_executors()

        assert "git_status" in executors, "Expected 'git_status' in executors"
        assert "git_diff" in executors, "Expected 'git_diff' in executors"
        assert "git_log" in executors, "Expected 'git_log' in executors"
        assert "git_add" in executors, "Expected 'git_add' in executors"
        assert "git_commit" in executors, "Expected 'git_commit' in executors"


class TestRunnerTools:
    """Tests for RunnerTools."""

    @pytest.fixture
    def temp_test_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            tests_dir = project / "tests"
            tests_dir.mkdir()

            # Create a simple passing test
            (tests_dir / "test_simple.py").write_text(
                """
def test_passes():
    assert True

def test_also_passes():
    assert 1 + 1 == 2
"""
            )

            # Create a failing test
            (tests_dir / "test_failing.py").write_text(
                """
def test_fails():
    assert False, "This test should fail"
"""
            )

            yield project

    def test_run_tests_passing(self, temp_test_project):
        tools = RunnerTools(temp_test_project)
        result = tools.run_tests(
            "run_tests",
            {"test_path": "tests/test_simple.py", "verbose": True},
        )

        assert result.success, "Expected result.success to be truthy"
        assert "passed" in result.output.lower(), "Expected 'passed' in result.output.lower()"

    def test_run_tests_failing(self, temp_test_project):
        tools = RunnerTools(temp_test_project)
        result = tools.run_tests(
            "run_tests",
            {"test_path": "tests/test_failing.py"},
        )

        assert not result.success, "Assertion failed"
        # Error contains the failure message
        assert result.error is not None, "Expected result.error is not None"
        assert "failed" in result.error.lower(), "Expected 'failed' in result.error.lower()"

    def test_run_single_test(self, temp_test_project):
        tools = RunnerTools(temp_test_project)
        result = tools.run_single_test(
            "run_single_test",
            {"test_path": "tests/test_simple.py::test_passes"},
        )

        assert result.success, "Expected result.success to be truthy"
        assert "passed" in result.output.lower(), "Expected 'passed' in result.output.lower()"

    def test_run_single_test_missing_path(self, temp_test_project):
        tools = RunnerTools(temp_test_project)
        result = tools.run_single_test("run_single_test", {})

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_run_affected_tests_no_matches(self, temp_test_project):
        tools = RunnerTools(temp_test_project)
        result = tools.run_affected_tests(
            "run_affected_tests",
            {"changed_files": ["src/some_module.py"]},
        )

        assert result.success, "Expected result.success to be truthy"
        assert "No related tests found" in result.output, "Expected 'No related tests found' in result.output"

    def test_get_tool_executors(self, temp_test_project):
        tools = RunnerTools(temp_test_project)
        executors = tools.get_tool_executors()

        assert "run_tests" in executors, "Expected 'run_tests' in executors"
        assert "run_single_test" in executors, "Expected 'run_single_test' in executors"
        assert "run_affected_tests" in executors, "Expected 'run_affected_tests' in executors"


class TestConformanceTools:
    """Tests for ConformanceTools (mocked)."""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_check_file_missing_param(self, temp_project):
        tools = ConformanceTools(temp_project)
        result = tools.check_file("check_file", {})

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_verify_violation_fixed_missing_param(self, temp_project):
        tools = ConformanceTools(temp_project)
        result = tools.verify_violation_fixed("verify_violation_fixed", {})

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_verify_violation_fixed_not_found(self, temp_project):
        tools = ConformanceTools(temp_project)
        result = tools.verify_violation_fixed(
            "verify_violation_fixed", {"violation_id": "V-nonexistent"}
        )

        assert not result.success, "Assertion failed"
        assert "not found" in result.error.lower(), "Expected 'not found' in result.error.lower()"

    def test_get_tool_executors(self, temp_project):
        tools = ConformanceTools(temp_project)
        executors = tools.get_tool_executors()

        assert "check_file" in executors, "Expected 'check_file' in executors"
        assert "verify_violation_fixed" in executors, "Expected 'verify_violation_fixed' in executors"
        assert "run_full_check" in executors, "Expected 'run_full_check' in executors"

    @patch("subprocess.run")
    def test_check_file_success(self, mock_run, temp_project):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="No violations found",
            stderr="",
        )

        tools = ConformanceTools(temp_project)
        result = tools.check_file("check_file", {"file_path": "test.py"})

        assert result.success, "Expected result.success to be truthy"
        assert "No violations" in result.output, "Expected 'No violations' in result.output"

    @patch("subprocess.run")
    def test_run_full_check_timeout(self, mock_run, temp_project):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)

        tools = ConformanceTools(temp_project)
        result = tools.run_full_check("run_full_check", {})

        assert not result.success, "Assertion failed"
        assert "timed out" in result.error.lower(), "Expected 'timed out' in result.error.lower()"

    def test_get_check_definition_missing_param(self, temp_project):
        """Test get_check_definition with missing parameter."""
        tools = ConformanceTools(temp_project)
        result = tools.get_check_definition("get_check_definition", {})

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_get_check_definition_not_found(self, temp_project):
        """Test get_check_definition with non-existent check."""
        tools = ConformanceTools(temp_project)
        result = tools.get_check_definition(
            "get_check_definition", {"check_id": "nonexistent-check"}
        )

        assert not result.success, "Assertion failed"
        assert "not found" in result.error.lower() or "Check not found" in str(result.output), "Assertion failed"

    def test_run_conformance_check_missing_check_id(self, temp_project):
        """Test run_conformance_check with missing check_id."""
        tools = ConformanceTools(temp_project)
        result = tools.run_conformance_check(
            "run_conformance_check", {"file_path": "test.py"}
        )

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_run_conformance_check_missing_file_path(self, temp_project):
        """Test run_conformance_check with missing file_path."""
        tools = ConformanceTools(temp_project)
        result = tools.run_conformance_check(
            "run_conformance_check", {"check_id": "max-cyclomatic-complexity"}
        )

        assert not result.success, "Assertion failed"
        assert "missing" in result.error.lower(), "Expected 'missing' in result.error.lower()"

    def test_run_conformance_check_file_not_found(self, temp_project):
        """Test run_conformance_check with non-existent file."""
        tools = ConformanceTools(temp_project)
        result = tools.run_conformance_check(
            "run_conformance_check",
            {"check_id": "max-cyclomatic-complexity", "file_path": "nonexistent.py"}
        )

        assert not result.success, "Assertion failed"
        assert "not found" in result.error.lower() or "not found" in str(result.output).lower(), "Assertion failed"

    def test_get_tool_executors_includes_new_tools(self, temp_project):
        """Test that get_tool_executors includes the new domain-specific tools."""
        tools = ConformanceTools(temp_project)
        executors = tools.get_tool_executors()

        # Original tools
        assert "check_file" in executors, "Expected 'check_file' in executors"
        assert "verify_violation_fixed" in executors, "Expected 'verify_violation_fixed' in executors"
        assert "run_full_check" in executors, "Expected 'run_full_check' in executors"
        # New domain-specific tools
        assert "run_conformance_check" in executors, "Expected 'run_conformance_check' in executors"
        assert "get_check_definition" in executors, "Expected 'get_check_definition' in executors"
