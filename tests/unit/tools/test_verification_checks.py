# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-verification_runner

"""Tests for verification check implementations (CheckRunner mixin)."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from agentforge.core.verification_runner import VerificationRunner
from agentforge.core.verification_types import CheckStatus


class TestCommandCheck:
    """Tests for command check execution."""

    def test_command_success_returns_passed(self, tmp_path: Path):
        """Test successful command returns PASSED status."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_cmd",
            "name": "Test Command",
            "type": "command",
            "command": "echo hello",
            "severity": "advisory"
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="hello\n", stderr=""
            )
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED
        assert result.check_id == "test_cmd"

    def test_command_failure_returns_failed(self, tmp_path: Path):
        """Test failed command returns FAILED status."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_cmd",
            "name": "Test Command",
            "type": "command",
            "command": "false",
            "severity": "advisory"
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Error occurred"
            )
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED

    def test_command_timeout_returns_failed(self, tmp_path: Path):
        """Test timed-out command returns ERROR status."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_cmd",
            "name": "Test Command",
            "type": "command",
            "command": "sleep 100",
            "timeout": 1,
            "severity": "advisory"
        }

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=1)
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.ERROR
        assert "timed out" in result.message.lower()

    def test_command_not_found_returns_error(self, tmp_path: Path):
        """Test missing command returns ERROR status."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_cmd",
            "name": "Test Command",
            "type": "command",
            "command": "nonexistent_command_12345",
            "severity": "advisory"
        }

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.ERROR

    def test_command_with_variable_substitution(self, tmp_path: Path):
        """Test command with variable substitution."""
        runner = VerificationRunner(project_root=tmp_path)
        runner.set_context(project_name="MyProject")
        check = {
            "id": "test_cmd",
            "type": "command",
            "command": "echo Building {project_name}",
            "severity": "advisory"
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            runner.run_check(check, {})

        # Check that substitution happened
        call_args = mock_run.call_args[0][0]
        assert "MyProject" in " ".join(call_args)

    def test_command_success_indicator_overrides(self, tmp_path: Path):
        """Test success_indicators can override exit code."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_cmd",
            "type": "command",
            "command": "echo BUILD SUCCEEDED",
            "success_indicators": ["SUCCEEDED"],
            "severity": "advisory"
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,  # Non-zero but has success indicator
                stdout="BUILD SUCCEEDED",
                stderr=""
            )
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_command_failure_indicator_overrides(self, tmp_path: Path):
        """Test failure_indicators can override exit code."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_cmd",
            "type": "command",
            "command": "echo Build failed",
            "failure_indicators": ["failed"],
            "severity": "advisory"
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,  # Zero exit but has failure indicator
                stdout="Build failed",
                stderr=""
            )
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED


class TestRegexCheck:
    """Tests for regex pattern matching check."""

    def test_regex_match_found(self, tmp_path: Path, sample_python_file: Path):
        """Test regex finds matching pattern."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_regex",
            "name": "Find Classes",
            "type": "regex",
            "patterns": [{"name": "class", "pattern": r"class \w+:"}],
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED
        assert "match" in result.message.lower() or "found" in result.message.lower()

    def test_regex_no_match(self, tmp_path: Path, sample_python_file: Path):
        """Test regex with no matches returns FAILED."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_regex",
            "type": "regex",
            "patterns": [{"name": "nonexistent", "pattern": r"ThisPatternDoesNotExist12345"}],
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED

    def test_regex_negative_match_not_found_passes(self, tmp_path: Path, sample_python_file: Path):
        """Test negative match passes when pattern not found."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_regex",
            "type": "regex",
            "patterns": [{"name": "bad", "pattern": r"TODO|FIXME|HACK"}],
            "negative_match": True,
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_regex_negative_match_found_fails(self, tmp_path: Path):
        """Test negative match fails when pattern is found."""
        # Create file with forbidden pattern
        test_file = tmp_path / "bad.py"
        test_file.write_text("# TODO: fix this later")

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_regex",
            "type": "regex",
            "patterns": [{"name": "todo", "pattern": r"TODO"}],
            "negative_match": True,
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED
        assert len(result.errors) > 0

    def test_regex_multiline_pattern(self, tmp_path: Path):
        """Test regex works with multiline patterns."""
        test_file = tmp_path / "multi.py"
        test_file.write_text('def func():\n    """Docstring."""\n    pass')

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_regex",
            "type": "regex",
            "patterns": [{"name": "docstring", "pattern": r'""".*?"""'}],
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED


class TestFileExistsCheck:
    """Tests for file existence check."""

    def test_file_exists_passes(self, tmp_path: Path, sample_python_file: Path):
        """Test file exists check passes for existing file."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_file",
            "type": "file_exists",
            "files": ["sample.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_file_missing_fails(self, tmp_path: Path):
        """Test file exists check fails for missing file."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_file",
            "type": "file_exists",
            "files": ["nonexistent.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED
        assert len(result.errors) > 0

    def test_directory_exists_passes(self, tmp_path: Path):
        """Test directory existence check passes."""
        (tmp_path / "src").mkdir()

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_dir",
            "type": "file_exists",
            "files": ["src"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_multiple_files_all_exist(self, tmp_path: Path):
        """Test multiple files all existing passes."""
        (tmp_path / "a.py").write_text("# a")
        (tmp_path / "b.py").write_text("# b")

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_files",
            "type": "file_exists",
            "files": ["a.py", "b.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_multiple_files_some_missing(self, tmp_path: Path):
        """Test multiple files with some missing fails."""
        (tmp_path / "a.py").write_text("# a")

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_files",
            "type": "file_exists",
            "files": ["a.py", "missing.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED
        assert len(result.errors) == 1

    def test_file_with_custom_message(self, tmp_path: Path):
        """Test file spec with custom error message."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_file",
            "type": "file_exists",
            "files": [
                {"path": "config.yaml", "message": "Config file required for deployment"}
            ],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED
        assert "Config file required" in str(result.errors)


class TestImportCheck:
    """Tests for layer/import dependency check."""

    def test_valid_layer_dependencies_pass(self, sample_clean_architecture: Path):
        """Test valid clean architecture dependencies pass."""
        runner = VerificationRunner(project_root=sample_clean_architecture)
        check = {
            "id": "test_import",
            "type": "import_check",
            "rules": [
                {
                    "source_pattern": "src/domain/**/*.py",
                    "forbidden_imports": ["infrastructure", "application"],
                    "message": "Domain cannot import from outer layers"
                }
            ],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        # Domain only has no imports, so should pass
        assert result.status == CheckStatus.PASSED

    def test_layer_violation_detected(self, sample_layer_violation: Path):
        """Test layer violation is detected."""
        runner = VerificationRunner(project_root=sample_layer_violation)
        check = {
            "id": "test_import",
            "type": "import_check",
            "rules": [
                {
                    "source_pattern": "src/domain/**/*.cs",
                    "forbidden_imports": ["Infrastructure"],
                    "message": "Domain cannot import infrastructure"
                }
            ],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED
        assert len(result.errors) > 0


class TestCustomCheck:
    """Tests for custom Python function check."""

    def test_custom_function_passes(self, tmp_path: Path, custom_check_function: Path):
        """Test custom function that returns success."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_custom",
            "type": "custom",
            "function": "custom_checks.check_always_pass",
            "severity": "advisory"
        }

        # Add custom module to path
        sys.path.insert(0, str(tmp_path))
        try:
            result = runner.run_check(check, {})
            assert result.status == CheckStatus.PASSED
        finally:
            sys.path.remove(str(tmp_path))

    def test_custom_function_fails(self, tmp_path: Path, custom_check_function: Path):
        """Test custom function that returns failure."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_custom",
            "type": "custom",
            "function": "custom_checks.check_always_fail",
            "severity": "advisory"
        }

        sys.path.insert(0, str(tmp_path))
        try:
            result = runner.run_check(check, {})
            assert result.status == CheckStatus.FAILED
        finally:
            sys.path.remove(str(tmp_path))

    def test_custom_function_exception(self, tmp_path: Path, custom_check_function: Path):
        """Test custom function that raises exception."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_custom",
            "type": "custom",
            "function": "custom_checks.check_raises_exception",
            "severity": "advisory"
        }

        sys.path.insert(0, str(tmp_path))
        try:
            result = runner.run_check(check, {})
            assert result.status == CheckStatus.ERROR
            assert "exception" in result.message.lower()
        finally:
            sys.path.remove(str(tmp_path))

    def test_custom_function_returns_bool(self, tmp_path: Path, custom_check_function: Path):
        """Test custom function that returns boolean."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_custom",
            "type": "custom",
            "function": "custom_checks.check_returns_bool",
            "severity": "advisory"
        }

        sys.path.insert(0, str(tmp_path))
        try:
            result = runner.run_check(check, {})
            assert result.status == CheckStatus.PASSED
        finally:
            sys.path.remove(str(tmp_path))

    def test_custom_function_not_found(self, tmp_path: Path):
        """Test error when custom function not found."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_custom",
            "type": "custom",
            "function": "nonexistent_module.nonexistent_func",
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.ERROR


class TestASTCheck:
    """Tests for AST-based code checks."""

    def test_ast_function_length_passes(self, tmp_path: Path, sample_python_file: Path):
        """Test function length check passes for short functions."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_ast",
            "type": "ast_check",
            "config": {"metric": "function_length", "max_value": 50},
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_ast_function_length_fails(self, tmp_path: Path, sample_long_function: Path):
        """Test function length check fails for long functions."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_ast",
            "type": "ast_check",
            "config": {"metric": "function_length", "max_value": 50},
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED
        assert len(result.errors) > 0

    def test_ast_nesting_depth_passes(self, tmp_path: Path, sample_python_file: Path):
        """Test nesting depth check passes for shallow code."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_ast",
            "type": "ast_check",
            "config": {"metric": "nesting_depth", "max_value": 4},
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_ast_nesting_depth_fails(self, tmp_path: Path, sample_deeply_nested: Path):
        """Test nesting depth check fails for deeply nested code."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_ast",
            "type": "ast_check",
            "config": {"metric": "nesting_depth", "max_value": 4},
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED

    def test_ast_cyclomatic_complexity(self, tmp_path: Path):
        """Test cyclomatic complexity check."""
        test_file = tmp_path / "complex.py"
        test_file.write_text('''
def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "big"
            return "medium"
        return "small"
    elif x < 0:
        return "negative"
    else:
        return "zero"
''')

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_ast",
            "type": "ast_check",
            "config": {"metric": "cyclomatic_complexity", "max_value": 3},
            "file_patterns": ["*.py"],
            "severity": "advisory"
        }

        result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED


class TestLSPQueryCheck:
    """Tests for LSP/pyright type checking."""

    def test_lsp_check_valid_file(self, tmp_path: Path, sample_python_file: Path):
        """Test LSP check passes for valid typed file."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_lsp",
            "type": "lsp_query",
            "file_patterns": ["*.py"],
            "severity_filter": ["error"],
            "severity": "advisory"
        }

        # Mock the pyright runner
        with patch.object(runner, '_pyright_runner') as mock_pyright:
            mock_pyright.check_project.return_value = Mock(
                diagnostics=[],
                error_count=0,
                warning_count=0,
                files_analyzed=1
            )
            runner._pyright_runner = mock_pyright
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.PASSED

    def test_lsp_check_type_errors(self, tmp_path: Path, sample_python_with_errors: Path):
        """Test LSP check detects type errors."""
        runner = VerificationRunner(project_root=tmp_path)
        check = {
            "id": "test_lsp",
            "type": "lsp_query",
            "file_patterns": ["*.py"],
            "severity_filter": ["error"],
            "severity": "advisory"
        }

        # Mock pyright with errors
        mock_diag = Mock(
            file=str(sample_python_with_errors),
            line=4, column=12,
            message="Type mismatch",
            rule="reportReturnType",
            severity="error"
        )

        with patch.object(runner, '_pyright_runner') as mock_pyright:
            mock_pyright.check_project.return_value = Mock(
                diagnostics=[mock_diag],
                error_count=1,
                warning_count=0,
                files_analyzed=1
            )
            runner._pyright_runner = mock_pyright
            result = runner.run_check(check, {})

        assert result.status == CheckStatus.FAILED
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
