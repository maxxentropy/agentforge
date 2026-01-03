# @spec_file: .agentforge/specs/core-cicd-v1.yaml
# @spec_id: core-cicd-v1
# @component_id: tools-cicd-runner
# @impl_path: tools/cicd/runner.py

"""Test Python contract check implementations."""

from pathlib import Path

import pytest

from agentforge.core.command_runner import CommandRunner
from agentforge.core.pyright_runner import PyrightRunner, check_python_types


class TestPyrightRunner:
    """Test pyright integration."""

    def test_pyright_installed(self):
        """Verify pyright is accessible."""
        runner = PyrightRunner()
        # Should not raise
        assert runner is not None, "Expected runner is not None"

    def test_check_valid_file(self, tmp_path: Path):
        """Check a valid Python file."""
        test_file = tmp_path / "valid.py"
        test_file.write_text('''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')

        result = check_python_types(test_file)
        assert result.success, "Expected result.success to be truthy"
        assert result.error_count == 0, "Expected result.error_count to equal 0"

    def test_check_file_with_type_error(self, tmp_path: Path):
        """Check a file with type errors."""
        test_file = tmp_path / "invalid.py"
        test_file.write_text('''
def add(a: int, b: int) -> int:
    return "not an int"  # Type error
''')

        result = check_python_types(test_file)
        assert not result.success, "Assertion failed"
        assert result.error_count > 0, "Expected result.error_count > 0"
        # Pyright should report a return type mismatch
        assert len(result.diagnostics) > 0, "Expected len(result.diagnostics) > 0"


class TestCommandRunner:
    """Test external command execution."""

    def test_run_command(self):
        """Test basic command execution."""
        runner = CommandRunner()
        result = runner.run(["echo", "hello"])

        assert result.success, "Expected result.success to be truthy"
        assert result.return_code == 0, "Expected result.return_code to equal 0"
        assert "hello" in result.stdout, "Expected 'hello' in result.stdout"

    def test_run_missing_command(self):
        """Test handling of missing command."""
        runner = CommandRunner()
        result = runner.run(["nonexistent_command_12345"])

        assert not result.success, "Assertion failed"
        assert "not found" in result.stderr.lower(), "Expected 'not found' in result.stderr.lower()"

    def test_run_radon(self, tmp_path: Path):
        """Test radon execution."""
        test_file = tmp_path / "test.py"
        test_file.write_text('''
def simple():
    return 1

def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "big"
            return "medium"
        return "small"
    return "negative"
''')

        runner = CommandRunner(tmp_path)
        result = runner.run_radon_cc(test_file)

        # Should complete successfully
        assert result.return_code == 0, "Expected result.return_code to equal 0"
        assert result.parsed_output is not None, "Expected result.parsed_output is not None"


class TestVerificationRunner:
    """Test the verification runner integration."""

    def test_ast_check_function_length(self, tmp_path: Path):
        """Test AST check for function length."""
        from agentforge.core.verification_runner import VerificationRunner

        # Create a file with a long function
        test_file = tmp_path / "long_func.py"
        test_file.write_text('\n'.join([
            'def long_function():',
            *[f'    x = {i}' for i in range(60)],
            '    return x'
        ]))

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            'id': 'test-length',
            'name': 'Test Function Length',
            'type': 'ast_check',
            'severity': 'advisory',
            'config': {
                'metric': 'function_length',
                'max_value': 50
            },
            'file_patterns': ['*.py']
        }

        result = runner.run_check(check, {})
        assert result.status.value == 'failed', "Expected result.status.value to equal 'failed'"
        assert len(result.errors) > 0, "Expected len(result.errors) > 0"
        assert result.errors[0]['function'] == 'long_function', "Expected result.errors[0]['function'] to equal 'long_function'"

    def test_ast_check_nesting_depth(self, tmp_path: Path):
        """Test AST check for nesting depth."""
        from agentforge.core.verification_runner import VerificationRunner

        # Create a file with deeply nested code
        test_file = tmp_path / "nested.py"
        test_file.write_text('''
def deep_nesting():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return "too deep"
''')

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            'id': 'test-nesting',
            'name': 'Test Nesting Depth',
            'type': 'ast_check',
            'severity': 'advisory',
            'config': {
                'metric': 'nesting_depth',
                'max_value': 4
            },
            'file_patterns': ['*.py']
        }

        result = runner.run_check(check, {})
        assert result.status.value == 'failed', "Expected result.status.value to equal 'failed'"
        assert any('depth' in str(e.get('message', '')).lower() for e in result.errors), "Expected any() to be truthy"

    def test_lsp_query_check(self, tmp_path: Path):
        """Test LSP query check using pyright."""
        from agentforge.core.verification_runner import VerificationRunner

        # Create a valid Python file
        test_file = tmp_path / "valid.py"
        test_file.write_text('''
def greet(name: str) -> str:
    return f"Hello, {name}"
''')

        runner = VerificationRunner(project_root=tmp_path)
        check = {
            'id': 'test-pyright',
            'name': 'Test Pyright',
            'type': 'lsp_query',
            'severity': 'advisory',
            'file_patterns': ['*.py'],
            'severity_filter': ['error']
        }

        result = runner.run_check(check, {})
        assert result.status.value == 'passed', "Expected result.status.value to equal 'passed'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
