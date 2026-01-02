# @spec_file: specs/pipeline-controller/implementation/phase-3-tdd-stages.yaml
# @spec_id: pipeline-controller-phase3-v1
# @component_id: red-phase-executor
# @test_path: tests/unit/pipeline/stages/test_red.py

"""Unit tests for RedPhaseExecutor."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch, Mock

import pytest

from agentforge.core.pipeline import StageContext, StageStatus
from agentforge.core.pipeline.stages.red import RedPhaseExecutor, create_red_executor


class TestRedPhaseExecutor:
    """Tests for RedPhaseExecutor class."""

    def test_stage_name_is_red(self):
        """RedPhaseExecutor has stage_name 'red'."""
        executor = RedPhaseExecutor()
        assert executor.stage_name == "red"

    def test_artifact_type_is_test_suite(self):
        """RedPhaseExecutor has artifact_type 'test_suite'."""
        executor = RedPhaseExecutor()
        assert executor.artifact_type == "test_suite"

    def test_required_input_fields(self):
        """RedPhaseExecutor requires spec_id, components, test_cases."""
        executor = RedPhaseExecutor()
        assert "spec_id" in executor.required_input_fields
        assert "components" in executor.required_input_fields
        assert "test_cases" in executor.required_input_fields

    def test_output_fields(self):
        """RedPhaseExecutor outputs spec_id, test_files, test_results."""
        executor = RedPhaseExecutor()
        assert "spec_id" in executor.output_fields
        assert "test_files" in executor.output_fields
        assert "test_results" in executor.output_fields

    def test_generates_test_files_from_spec(
        self,
        sample_spec_artifact,
        sample_llm_test_generation_response,
        temp_project_path,
    ):
        """Generates test files based on spec test_cases."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        # Mock the LLM execution
        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = sample_llm_test_generation_response

            # Mock subprocess for test running
            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(
                    stdout="3 failed",
                    stderr="",
                    returncode=1,
                )

                result = executor.execute(context)

        # Should have generated test files
        assert result.artifacts is not None
        assert "test_files" in result.artifacts

    def test_writes_test_files_to_disk(
        self,
        sample_spec_artifact,
        temp_project_path,
    ):
        """Test files are written to correct locations."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        test_files = [
            {
                "path": "tests/unit/auth/test_example.py",
                "content": "# Test content\ndef test_example():\n    assert True",
            }
        ]

        written = executor._write_test_files(context, test_files)

        assert len(written) == 1
        assert "tests/unit/auth/test_example.py" in written[0]
        assert (temp_project_path / "tests" / "unit" / "auth" / "test_example.py").exists()

    def test_runs_pytest_on_generated_tests(
        self,
        sample_spec_artifact,
        temp_project_path,
        mock_pytest_failing_output,
    ):
        """Runs pytest on generated test files."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout=mock_pytest_failing_output,
                stderr="",
                returncode=1,
            )

            results = executor._run_tests(
                context,
                ["tests/unit/auth/test_oauth_provider.py"]
            )

        assert results["failed"] == 3
        assert results["passed"] == 0

    def test_reports_failing_tests(
        self,
        sample_spec_artifact,
        temp_project_path,
    ):
        """Reports expected failing tests."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        test_results = {
            "passed": 0,
            "failed": 3,
            "total": 3,
            "test_details": [
                {"name": "test_one", "status": "failed"},
                {"name": "test_two", "status": "failed"},
                {"name": "test_three", "status": "failed"},
            ],
        }

        validation = executor._validate_red_results(test_results)

        assert len(validation["failing_tests"]) == 3
        assert "test_one" in validation["failing_tests"]

    def test_warns_on_unexpected_passes(self):
        """Warns when tests pass unexpectedly."""
        executor = RedPhaseExecutor()

        test_results = {
            "passed": 2,
            "failed": 1,
            "total": 3,
            "test_details": [
                {"name": "test_one", "status": "passed"},
                {"name": "test_two", "status": "passed"},
                {"name": "test_three", "status": "failed"},
            ],
        }

        validation = executor._validate_red_results(test_results)

        assert len(validation["unexpected_passes"]) == 2
        assert len(validation["warnings"]) > 0


class TestFileBlockExtraction:
    """Tests for file block extraction from LLM response."""

    def test_extracts_single_file_block(self):
        """Extracts single file from response."""
        executor = RedPhaseExecutor()

        response_text = '''Here is the test file.

### FILE: tests/test_example.py
```python
def test_example():
    assert True
```
'''

        files = executor._extract_file_blocks(response_text)

        assert len(files) == 1
        assert files[0]["path"] == "tests/test_example.py"
        assert "def test_example" in files[0]["content"]

    def test_extracts_multiple_file_blocks(self):
        """Extracts multiple files from response."""
        executor = RedPhaseExecutor()

        response_text = '''I'll generate two test files.

### FILE: tests/test_one.py
```python
def test_one():
    pass
```

### FILE: tests/test_two.py
```python
def test_two():
    pass
```
'''

        files = executor._extract_file_blocks(response_text)

        assert len(files) == 2
        assert files[0]["path"] == "tests/test_one.py"
        assert files[1]["path"] == "tests/test_two.py"

    def test_handles_missing_file_marker(self):
        """Handles response without file markers."""
        executor = RedPhaseExecutor()

        response_text = '''Here is some code:

```python
def test_example():
    pass
```
'''

        files = executor._extract_file_blocks(response_text)

        assert len(files) == 0

    def test_handles_malformed_code_block(self):
        """Handles malformed code block."""
        executor = RedPhaseExecutor()

        response_text = '''### FILE: tests/test.py
This is not a proper code block
```
'''

        files = executor._extract_file_blocks(response_text)

        assert len(files) == 0


class TestPytestOutputParsing:
    """Tests for pytest output parsing."""

    def test_parses_pytest_passed_count(self, mock_pytest_passing_output):
        """Correctly parses passed test count."""
        executor = RedPhaseExecutor()

        results = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "test_details": [],
        }

        executor._parse_pytest_output(mock_pytest_passing_output, results)

        assert results["passed"] == 3
        assert results["failed"] == 0

    def test_parses_pytest_failed_count(self, mock_pytest_failing_output):
        """Correctly parses failed test count."""
        executor = RedPhaseExecutor()

        results = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "test_details": [],
        }

        executor._parse_pytest_output(mock_pytest_failing_output, results)

        assert results["failed"] == 3
        assert results["passed"] == 0

    def test_handles_pytest_timeout(self, sample_spec_artifact, temp_project_path):
        """Handles test execution timeout."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        import subprocess

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired("pytest", 300)

            results = executor._run_tests(context, ["tests/test.py"])

        assert "error" in results

    def test_handles_pytest_error(self, sample_spec_artifact, temp_project_path):
        """Handles pytest execution error."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = Exception("Process error")

            results = executor._run_tests(context, ["tests/test.py"])

        assert "error" in results


class TestRedPhaseValidation:
    """Tests for RED phase artifact validation."""

    def test_validates_test_files_present(self):
        """Validates that test files are present."""
        executor = RedPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "test_files": [],
            "test_results": {},
        }

        validation = executor.validate_output(artifact)

        assert not validation.valid
        assert any("test files" in e.lower() for e in validation.errors)

    def test_validates_red_expects_failures(self):
        """Validates that RED phase expects test failures."""
        executor = RedPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "test_files": [{"path": "test.py", "content": "..."}],
            "test_results": {"total": 3, "failed": 3, "passed": 0},
            "failing_tests": ["test_a", "test_b", "test_c"],
        }

        validation = executor.validate_output(artifact)

        assert validation.valid

    def test_warns_all_tests_passed(self):
        """Warns when all tests pass in RED phase."""
        executor = RedPhaseExecutor()

        test_results = {
            "passed": 3,
            "failed": 0,
            "total": 3,
            "test_details": [
                {"name": "test_a", "status": "passed"},
                {"name": "test_b", "status": "passed"},
                {"name": "test_c", "status": "passed"},
            ],
        }

        validation = executor._validate_red_results(test_results)

        assert len(validation["warnings"]) > 0
        assert any("passed" in w.lower() for w in validation["warnings"])


class TestRedPhaseEdgeCases:
    """Tests for RED phase edge cases."""

    def test_handles_empty_spec_test_cases(self, temp_project_path):
        """Handles spec with no test cases."""
        executor = RedPhaseExecutor()

        spec_artifact = {
            "spec_id": "SPEC-123",
            "components": [{"name": "Component", "type": "class"}],
            "test_cases": [],
        }

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=spec_artifact,
            config={},
        )

        user_message = executor.get_user_message(context)

        # Should still work, just with empty test cases
        assert "SPEC-123" in user_message

    def test_handles_no_components(self, temp_project_path):
        """Handles spec with no components."""
        executor = RedPhaseExecutor()

        spec_artifact = {
            "spec_id": "SPEC-123",
            "components": [],
            "test_cases": [],
        }

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=spec_artifact,
            config={},
        )

        user_message = executor.get_user_message(context)

        assert "SPEC-123" in user_message

    def test_creates_parent_directories(self, temp_project_path):
        """Creates parent directories when writing test files."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts={},
            config={},
        )

        test_files = [
            {
                "path": "tests/new/nested/directory/test_file.py",
                "content": "def test(): pass",
            }
        ]

        written = executor._write_test_files(context, test_files)

        assert len(written) == 1
        assert (temp_project_path / "tests" / "new" / "nested" / "directory" / "test_file.py").exists()


class TestRedPhasePrompts:
    """Tests for RED phase prompt generation."""

    def test_system_prompt_mentions_tdd(self):
        """System prompt mentions TDD and test-first approach."""
        executor = RedPhaseExecutor()

        context = MagicMock()

        prompt = executor.get_system_prompt(context)

        assert "test" in prompt.lower()
        assert "tdd" in prompt.lower() or "fail" in prompt.lower()

    def test_user_message_includes_spec_details(self, sample_spec_artifact, temp_project_path):
        """User message includes spec details."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        message = executor.get_user_message(context)

        assert "SPEC-20260101120000-0001" in message
        assert "OAuthProvider" in message
        assert "TC001" in message

    def test_user_message_includes_test_cases(self, sample_spec_artifact, temp_project_path):
        """User message includes test case details."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_path,
            input_artifacts=sample_spec_artifact,
            config={},
        )

        message = executor.get_user_message(context)

        # Check Given/When/Then
        assert "Given" in message or "given" in message
        assert "When" in message or "when" in message
        assert "Then" in message or "then" in message


class TestCreateRedExecutor:
    """Tests for factory function."""

    def test_creates_executor_instance(self):
        """Factory creates RedPhaseExecutor instance."""
        executor = create_red_executor()

        assert isinstance(executor, RedPhaseExecutor)

    def test_passes_config(self):
        """Factory passes config to executor."""
        config = {"test_runner": "pytest"}

        executor = create_red_executor(config)

        assert executor.test_runner == "pytest"
