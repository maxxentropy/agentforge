# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: green-phase-executor
# @test_path: tests/unit/pipeline/stages/test_green.py

"""Unit tests for GreenPhaseExecutor."""

from unittest.mock import Mock, patch

from agentforge.core.pipeline import StageContext
from agentforge.core.pipeline.stages.green import GreenPhaseExecutor, create_green_executor


class TestGreenPhaseExecutor:
    """Tests for GreenPhaseExecutor class."""

    def test_stage_name_is_green(self):
        """GreenPhaseExecutor has stage_name 'green'."""
        executor = GreenPhaseExecutor()
        assert executor.stage_name == "green", "Expected executor.stage_name to equal 'green'"

    def test_artifact_type_is_implementation(self):
        """GreenPhaseExecutor has artifact_type 'implementation'."""
        executor = GreenPhaseExecutor()
        assert executor.artifact_type == "implementation", "Expected executor.artifact_type to equal 'implementation'"

    def test_required_input_fields(self):
        """GreenPhaseExecutor requires spec_id, test_files, failing_tests."""
        executor = GreenPhaseExecutor()
        assert "spec_id" in executor.required_input_fields, "Expected 'spec_id' in executor.required_input_fields"
        assert "test_files" in executor.required_input_fields, "Expected 'test_files' in executor.required_input_fields"
        assert "failing_tests" in executor.required_input_fields, "Expected 'failing_tests' in executor.required_input_fields"

    def test_output_fields(self):
        """GreenPhaseExecutor outputs spec_id, implementation_files, test_results."""
        executor = GreenPhaseExecutor()
        assert "spec_id" in executor.output_fields, "Expected 'spec_id' in executor.output_fields"
        assert "implementation_files" in executor.output_fields, "Expected 'implementation_files' in executor.output_fields"
        assert "test_results" in executor.output_fields, "Expected 'test_results' in executor.output_fields"

    def test_has_max_iterations_config(self):
        """GreenPhaseExecutor has max_iterations configuration."""
        executor = GreenPhaseExecutor()
        assert hasattr(executor, "max_iterations"), "Expected hasattr() to be truthy"
        assert executor.max_iterations == 20, "Expected executor.max_iterations to equal 20"

    def test_max_iterations_from_config(self):
        """GreenPhaseExecutor uses max_iterations from config."""
        executor = GreenPhaseExecutor({"max_iterations": 10})
        assert executor.max_iterations == 10, "Expected executor.max_iterations to equal 10"

    def test_has_test_timeout_config(self):
        """GreenPhaseExecutor has test_timeout configuration."""
        executor = GreenPhaseExecutor()
        assert hasattr(executor, "test_timeout"), "Expected hasattr() to be truthy"
        assert executor.test_timeout == 120, "Expected executor.test_timeout to equal 120"


class TestGreenPhaseTools:
    """Tests for GREEN phase tool definitions."""

    def test_defines_read_file_tool(self):
        """Defines read_file tool."""
        executor = GreenPhaseExecutor()

        tool_names = [t["name"] for t in executor.tools]
        assert "read_file" in tool_names, "Expected 'read_file' in tool_names"

    def test_defines_write_file_tool(self):
        """Defines write_file tool."""
        executor = GreenPhaseExecutor()

        tool_names = [t["name"] for t in executor.tools]
        assert "write_file" in tool_names, "Expected 'write_file' in tool_names"

    def test_defines_edit_file_tool(self):
        """Defines edit_file tool."""
        executor = GreenPhaseExecutor()

        tool_names = [t["name"] for t in executor.tools]
        assert "edit_file" in tool_names, "Expected 'edit_file' in tool_names"

    def test_defines_run_tests_tool(self):
        """Defines run_tests tool."""
        executor = GreenPhaseExecutor()

        tool_names = [t["name"] for t in executor.tools]
        assert "run_tests" in tool_names, "Expected 'run_tests' in tool_names"

    def test_defines_complete_implementation_tool(self):
        """Defines complete_implementation tool."""
        executor = GreenPhaseExecutor()

        tool_names = [t["name"] for t in executor.tools]
        assert "complete_implementation" in tool_names, "Expected 'complete_implementation' in tool_names"


class TestGreenPhaseIteration:
    """Tests for GREEN phase iteration logic."""

    def test_builds_user_message_with_failing_tests(
        self,
        sample_red_artifact,
        temp_project_path,
    ):
        """User message includes failing tests."""
        executor = GreenPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=sample_red_artifact,
            config={},
        )

        message = executor._build_user_message(context)

        assert "test_authenticate" in message, "Expected 'test_authenticate' in message"
        assert "test_invalid_code" in message, "Expected 'test_invalid_code' in message"
        assert "test_refresh" in message, "Expected 'test_refresh' in message"

    def test_builds_iteration_message(self):
        """Builds message for subsequent iterations."""
        executor = GreenPhaseExecutor()

        test_results = {
            "passed": 1,
            "failed": 2,
            "total": 3,
            "test_details": [
                {"name": "test_one", "status": "passed"},
                {"name": "test_two", "status": "failed", "message": "AssertionError"},
                {"name": "test_three", "status": "failed", "message": "ImportError"},
            ],
        }

        message = executor._build_iteration_message(test_results, 2)

        assert "Iteration 2" in message, "Expected 'Iteration 2' in message"
        assert "Passed: 1/3" in message, "Expected 'Passed: 1/3' in message"
        assert "Failed: 2/3" in message, "Expected 'Failed: 2/3' in message"

    def test_includes_failure_details(self):
        """Iteration message includes failure details."""
        executor = GreenPhaseExecutor()

        test_results = {
            "passed": 0,
            "failed": 1,
            "total": 1,
            "test_details": [
                {
                    "name": "test_example",
                    "status": "failed",
                    "message": "ModuleNotFoundError: No module named 'mymodule'",
                },
            ],
        }

        message = executor._build_iteration_message(test_results, 1)

        assert "test_example" in message, "Expected 'test_example' in message"
        assert "Error:" in message or "ModuleNotFoundError" in message, "Assertion failed"


class TestGreenPhaseCompletion:
    """Tests for GREEN phase completion detection."""

    def test_detects_completion_signal(self):
        """Detects completion signal from tool call."""
        executor = GreenPhaseExecutor()

        result = {
            "tool_results": [
                {
                    "tool_name": "complete_implementation",
                    "input": {"implementation_files": ["file.py"]},
                    "result": "IMPLEMENTATION_COMPLETE:...",
                }
            ]
        }

        assert executor._check_completion(result), "Expected executor._check_completion() to be truthy"

    def test_no_completion_without_signal(self):
        """Returns False when no completion signal."""
        executor = GreenPhaseExecutor()

        result = {
            "tool_results": [
                {
                    "tool_name": "write_file",
                    "input": {"path": "file.py", "content": "..."},
                    "result": "Success",
                }
            ]
        }

        assert not executor._check_completion(result), "Assertion failed"

    def test_extracts_completion_data(self):
        """Extracts completion data from tool result."""
        executor = GreenPhaseExecutor()

        result = {
            "tool_results": [
                {
                    "tool_name": "complete_implementation",
                    "input": {
                        "implementation_files": ["file1.py", "file2.py"],
                        "summary": "Implemented OAuth",
                    },
                    "result": "Success",
                }
            ]
        }

        data = executor._extract_completion_data(result)

        assert data["implementation_files"] == ["file1.py", "file2.py"], "Expected data['implementation_files'] to equal ['file1.py', 'file2.py']"
        assert data["summary"] == "Implemented OAuth", "Expected data['summary'] to equal 'Implemented OAuth'"

    def test_extracts_written_files(self):
        """Extracts list of files written during iteration."""
        executor = GreenPhaseExecutor()

        result = {
            "tool_results": [
                {
                    "tool_name": "write_file",
                    "input": {"path": "src/auth/oauth.py", "content": "..."},
                    "result": "Success",
                },
                {
                    "tool_name": "write_file",
                    "input": {"path": "src/auth/token.py", "content": "..."},
                    "result": "Success",
                },
                {
                    "tool_name": "read_file",
                    "input": {"path": "tests/test.py"},
                    "result": "...",
                },
            ]
        }

        files = executor._extract_written_files(result)

        assert len(files) == 2, "Expected len(files) to equal 2"
        assert "src/auth/oauth.py" in files, "Expected 'src/auth/oauth.py' in files"
        assert "src/auth/token.py" in files, "Expected 'src/auth/token.py' in files"


class TestGreenPhaseTestExecution:
    """Tests for GREEN phase test execution."""

    def test_runs_all_tests(self, sample_red_artifact, temp_project_path):
        """Runs tests and returns results."""
        executor = GreenPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=sample_red_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout="tests/test.py::test_one PASSED\ntests/test.py::test_two PASSED\n2 passed",
                stderr="",
                returncode=0,
            )

            results = executor._run_all_tests(
                context,
                ["tests/test.py"]
            )

        assert results["passed"] == 2, "Expected results['passed'] to equal 2"
        assert results["failed"] == 0, "Expected results['failed'] to equal 0"

    def test_runs_specific_test(self, sample_red_artifact, temp_project_path):
        """Runs specific test when provided."""
        executor = GreenPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=sample_red_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout="test_specific PASSED\n1 passed",
                stderr="",
                returncode=0,
            )

            executor._run_all_tests(
                context,
                ["tests/test.py"],
                specific_test="test_specific"
            )

            # Check -k flag was used
            call_args = mock_subprocess.call_args[0][0]
            assert "-k" in call_args, "Expected '-k' in call_args"
            assert "test_specific" in call_args, "Expected 'test_specific' in call_args"

    def test_handles_test_timeout(self, sample_red_artifact, temp_project_path):
        """Handles test execution timeout."""
        executor = GreenPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=sample_red_artifact,
            config={},
        )

        import subprocess

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired("pytest", 120)

            results = executor._run_all_tests(context, ["tests/test.py"])

        assert "error" in results, "Expected 'error' in results"


class TestGreenPhasePytestParsing:
    """Tests for GREEN phase pytest output parsing."""

    def test_parses_passed_tests(self, mock_pytest_passing_output):
        """Parses passed test results."""
        executor = GreenPhaseExecutor()

        results = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "test_details": [],
        }

        executor._parse_pytest_output(mock_pytest_passing_output, results)

        assert results["passed"] == 3, "Expected results['passed'] to equal 3"
        assert len([d for d in results["test_details"] if d["status"] == "passed"]) == 3, "Expected len([d for d in results['te... to equal 3"

    def test_parses_failed_tests(self, mock_pytest_failing_output):
        """Parses failed test results."""
        executor = GreenPhaseExecutor()

        results = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "test_details": [],
        }

        executor._parse_pytest_output(mock_pytest_failing_output, results)

        assert results["failed"] == 3, "Expected results['failed'] to equal 3"
        assert len([d for d in results["test_details"] if d["status"] == "failed"]) == 3, "Expected len([d for d in results['te... to equal 3"


class TestGreenPhaseValidation:
    """Tests for GREEN phase artifact validation."""

    def test_validates_implementation_files_present(self):
        """Validates that implementation files are present."""
        executor = GreenPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "implementation_files": [],
            "test_results": {"passed": 3, "failed": 0},
            "all_tests_pass": True,
        }

        validation = executor.validate_output(artifact)

        assert not validation.valid, "Assertion failed"
        assert any("implementation" in e.lower() for e in validation.errors), "Expected any() to be truthy"

    def test_validates_all_tests_pass(self):
        """Validates that all tests pass."""
        executor = GreenPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "implementation_files": ["file.py"],
            "test_results": {"passed": 2, "failed": 1},
            "all_tests_pass": False,
        }

        validation = executor.validate_output(artifact)

        assert not validation.valid, "Assertion failed"
        assert any("failing" in e.lower() or "tests" in e.lower() for e in validation.errors), "Expected any() to be truthy"

    def test_reports_failing_count(self):
        """Reports number of failing tests in validation."""
        executor = GreenPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "implementation_files": ["file.py"],
            "test_results": {"passed": 1, "failed": 5},
            "all_tests_pass": False,
        }

        validation = executor.validate_output(artifact)

        assert any("5" in e for e in validation.errors), "Expected any() to be truthy"


class TestGreenPhaseEdgeCases:
    """Tests for GREEN phase edge cases."""

    def test_handles_no_failing_tests(self, temp_project_path):
        """Handles input with no failing tests."""
        executor = GreenPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "test_files": ["tests/test.py"],
            "failing_tests": [],
        }

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=artifact,
            config={},
        )

        message = executor._build_user_message(context)

        # Should handle gracefully
        assert "SPEC-123" in message, "Expected 'SPEC-123' in message"

    def test_handles_empty_test_files(self, temp_project_path):
        """Handles input with empty test files list."""
        executor = GreenPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "test_files": [],
            "failing_tests": ["test_one"],
        }

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=artifact,
            config={},
        )

        message = executor._build_user_message(context)

        # Should handle gracefully
        assert "test_one" in message, "Expected 'test_one' in message"


class TestGreenPhasePrompts:
    """Tests for GREEN phase prompt generation."""

    def test_system_prompt_mentions_tdd(self):
        """System prompt mentions TDD and GREEN phase."""
        executor = GreenPhaseExecutor()

        prompt = executor.SYSTEM_PROMPT

        assert "green" in prompt.lower() or "tdd" in prompt.lower(), "Assertion failed"
        assert "test" in prompt.lower(), "Expected 'test' in prompt.lower()"
        assert "pass" in prompt.lower(), "Expected 'pass' in prompt.lower()"

    def test_user_message_includes_spec_id(self, sample_red_artifact, temp_project_path):
        """User message includes spec ID."""
        executor = GreenPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=sample_red_artifact,
            config={},
        )

        message = executor._build_user_message(context)

        assert sample_red_artifact["spec_id"] in message, "Expected sample_red_artifact['spec_id'] in message"

    def test_user_message_includes_failing_count(self, sample_red_artifact, temp_project_path):
        """User message includes count of failing tests."""
        executor = GreenPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_path,
            input_artifacts=sample_red_artifact,
            config={},
        )

        message = executor._build_user_message(context)

        # Should include number of failing tests
        assert "3" in message or "FAILING" in message, "Assertion failed"


class TestCreateGreenExecutor:
    """Tests for factory function."""

    def test_creates_executor_instance(self):
        """Factory creates GreenPhaseExecutor instance."""
        executor = create_green_executor()

        assert isinstance(executor, GreenPhaseExecutor), "Expected isinstance() to be truthy"

    def test_passes_config(self):
        """Factory passes config to executor."""
        config = {"max_iterations": 15, "test_timeout": 60}

        executor = create_green_executor(config)

        assert executor.max_iterations == 15, "Expected executor.max_iterations to equal 15"
        assert executor.test_timeout == 60, "Expected executor.test_timeout to equal 60"
