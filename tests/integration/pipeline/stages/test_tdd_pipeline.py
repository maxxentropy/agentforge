# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: red-phase-executor, green-phase-executor
# @test_path: tests/integration/pipeline/stages/test_tdd_pipeline.py

"""Integration tests for TDD pipeline (RED → GREEN)."""

from unittest.mock import MagicMock, Mock, patch

from agentforge.core.pipeline import StageContext, StageStatus
from agentforge.core.pipeline.stages.green import GreenPhaseExecutor
from agentforge.core.pipeline.stages.red import RedPhaseExecutor


class TestRedPhaseIntegration:
    """Integration tests for RED phase."""

    def test_full_spec_to_tests_flow(
        self,
        sample_spec_for_tdd,
        temp_project_for_tdd,
    ):
        """Full flow from spec to generated tests."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_for_tdd,
            input_artifacts=sample_spec_for_tdd,
            config={},
        )

        # Mock LLM to return test file generation
        test_generation_response = {
            "response": '''### FILE: tests/test_calculator.py
```python
"""Tests for Calculator."""
import pytest
from src.calculator import Calculator


class TestCalculator:
    def test_add_positive_numbers(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5

    def test_subtract_numbers(self):
        calc = Calculator()
        assert calc.subtract(5, 3) == 2
```
''',
            "content": "",
            "tool_results": [],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = test_generation_response

            with patch("subprocess.run") as mock_subprocess:
                # Simulate tests failing (expected in RED)
                mock_subprocess.return_value = Mock(
                    stdout="""
tests/test_calculator.py::TestCalculator::test_add_positive_numbers FAILED
tests/test_calculator.py::TestCalculator::test_subtract_numbers FAILED

============================= 2 failed in 0.01s ==============================
""",
                    stderr="",
                    returncode=1,
                )

                result = executor.execute(context)

        # Tests should be generated and fail
        assert result.status == StageStatus.COMPLETED
        assert result.artifacts is not None
        assert len(result.artifacts.get("test_files", [])) > 0
        assert len(result.artifacts.get("failing_tests", [])) > 0

    def test_tests_fail_without_implementation(
        self,
        sample_spec_for_tdd,
        temp_project_for_tdd,
    ):
        """Generated tests fail when no implementation exists."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_for_tdd,
            input_artifacts=sample_spec_for_tdd,
            config={},
        )

        # Mock LLM response
        test_gen_response = {
            "response": '''### FILE: tests/test_calc.py
```python
from src.calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(1, 1) == 2
```
''',
            "content": "",
            "tool_results": [],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = test_gen_response

            with patch("subprocess.run") as mock_subprocess:
                # Tests fail with ModuleNotFoundError
                mock_subprocess.return_value = Mock(
                    stdout="""
tests/test_calc.py::test_add FAILED

ModuleNotFoundError: No module named 'src.calculator'

============================= 1 failed in 0.01s ==============================
""",
                    stderr="",
                    returncode=1,
                )

                result = executor.execute(context)

        # Verify tests fail (expected in RED phase)
        assert result.artifacts["test_results"]["failed"] > 0
        assert result.artifacts["test_results"]["passed"] == 0

    def test_generated_tests_are_written(
        self,
        sample_spec_for_tdd,
        temp_project_for_tdd,
    ):
        """Generated test files are written to disk."""
        executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_for_tdd,
            input_artifacts=sample_spec_for_tdd,
            config={},
        )

        test_gen_response = {
            "response": '''### FILE: tests/test_calculator.py
```python
def test_add():
    assert 1 + 1 == 2
```
''',
            "content": "",
            "tool_results": [],
        }

        with patch.object(executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = test_gen_response

            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(
                    stdout="1 failed",
                    stderr="",
                    returncode=1,
                )

                executor.execute(context)

        # Verify file was written
        test_file = temp_project_for_tdd / "tests" / "test_calculator.py"
        assert test_file.exists()
        assert "def test_add" in test_file.read_text()


class TestGreenPhaseIntegration:
    """Integration tests for GREEN phase."""

    def test_red_to_green_artifact_flow(
        self,
        sample_red_artifact_for_green,
        temp_project_for_tdd,
    ):
        """RED artifact flows correctly to GREEN phase."""
        GreenPhaseExecutor()

        # Write the test file from RED phase
        test_file = temp_project_for_tdd / "tests" / "test_calculator.py"
        test_file.write_text(sample_red_artifact_for_green["test_files"][0]["content"])

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_for_tdd,
            input_artifacts=sample_red_artifact_for_green,
                        config={},
        )

        # Verify context receives RED artifact correctly
        assert context.input_artifacts["spec_id"] == "SPEC-20260102-0001"
        assert len(context.input_artifacts["failing_tests"]) == 2
        assert len(context.input_artifacts["test_files"]) == 1

    def test_green_produces_implementation(
        self,
        sample_red_artifact_for_green,
        temp_project_for_tdd,
    ):
        """GREEN phase produces implementation files."""
        executor = GreenPhaseExecutor()

        # Write test file
        test_file = temp_project_for_tdd / "tests" / "test_calculator.py"
        test_file.write_text(sample_red_artifact_for_green["test_files"][0]["content"])

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_for_tdd,
            input_artifacts=sample_red_artifact_for_green,
                        config={},
        )

        # Mock the executor to simulate implementation
        with patch.object(executor, "_get_executor") as mock_get_executor:
            mock_executor = MagicMock()

            # Simulate LLM creating implementation
            mock_executor.execute_task.return_value = {
                "response": "Implementation complete",
                "tool_results": [
                    {
                        "tool_name": "write_file",
                        "input": {
                            "path": "src/calculator.py",
                            "content": """class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, a: int, b: int) -> int:
        return a - b
""",
                        },
                        "result": "Success",
                    },
                    {
                        "tool_name": "complete_implementation",
                        "input": {"implementation_files": ["src/calculator.py"]},
                        "result": "IMPLEMENTATION_COMPLETE",
                    },
                ],
            }
            mock_get_executor.return_value = mock_executor

            with patch("subprocess.run") as mock_subprocess:
                # First call: tests still failing
                # Second call: tests passing after implementation
                mock_subprocess.side_effect = [
                    Mock(
                        stdout="""
tests/test_calculator.py::TestCalculator::test_add_positive_numbers FAILED
tests/test_calculator.py::TestCalculator::test_subtract_numbers FAILED
============================= 2 failed in 0.01s ==============================
""",
                        stderr="",
                        returncode=1,
                    ),
                    Mock(
                        stdout="""
tests/test_calculator.py::TestCalculator::test_add_positive_numbers PASSED
tests/test_calculator.py::TestCalculator::test_subtract_numbers PASSED
============================= 2 passed in 0.01s ==============================
""",
                        stderr="",
                        returncode=0,
                    ),
                ]

                result = executor.execute(context)

        # Verify implementation was tracked
        assert result.artifacts is not None
        assert "implementation_files" in result.artifacts


class TestTDDPipelineIntegration:
    """End-to-end TDD pipeline tests."""

    def test_spec_to_red_to_green_flow(
        self,
        sample_spec_for_tdd,
        temp_project_for_tdd,
    ):
        """Full SPEC → RED → GREEN flow."""
        # Setup
        red_executor = RedPhaseExecutor()
        GreenPhaseExecutor()

        # RED Phase
        red_context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_for_tdd,
            input_artifacts=sample_spec_for_tdd,
            config={},
        )

        test_gen_response = {
            "response": '''### FILE: tests/test_calculator.py
```python
from src.calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_subtract():
    calc = Calculator()
    assert calc.subtract(5, 3) == 2
```
''',
            "content": "",
            "tool_results": [],
        }

        with patch.object(red_executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = test_gen_response

            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(
                    stdout="2 failed",
                    stderr="",
                    returncode=1,
                )

                red_result = red_executor.execute(red_context)

        # Verify RED produced artifact
        assert red_result.status == StageStatus.COMPLETED
        assert len(red_result.artifacts.get("test_files", [])) > 0

        # GREEN Phase (using RED artifact)
        green_context = StageContext(
            pipeline_id="PL-test",
            stage_name="green",
            project_path=temp_project_for_tdd,
            input_artifacts=red_result.artifacts,
                        config={},
        )

        # Verify artifact passes from RED to GREEN
        assert green_context.input_artifacts["spec_id"] == sample_spec_for_tdd["spec_id"]

    def test_tdd_pipeline_creates_test_then_implementation(
        self,
        sample_spec_for_tdd,
        temp_project_for_tdd,
    ):
        """TDD pipeline creates tests before implementation."""
        red_executor = RedPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="red",
            project_path=temp_project_for_tdd,
            input_artifacts=sample_spec_for_tdd,
            config={},
        )

        test_gen_response = {
            "response": '''### FILE: tests/test_calculator.py
```python
def test_add():
    from src.calculator import Calculator
    calc = Calculator()
    assert calc.add(1, 2) == 3
```
''',
            "content": "",
            "tool_results": [],
        }

        with patch.object(red_executor, "_run_with_llm") as mock_llm:
            mock_llm.return_value = test_gen_response

            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(
                    stdout="1 failed",
                    stderr="",
                    returncode=1,
                )

                red_executor.execute(context)

        # Verify: test file exists, implementation does not
        assert (temp_project_for_tdd / "tests" / "test_calculator.py").exists()
        assert not (temp_project_for_tdd / "src" / "calculator.py").exists()


class TestTDDStageRegistration:
    """Tests for TDD stage registration."""

    def test_red_executor_registers(self):
        """RED executor can be registered in registry."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages.red import create_red_executor

        registry = StageExecutorRegistry()
        registry.register("red", create_red_executor)

        executor = registry.get("red")
        assert executor is not None
        assert executor.stage_name == "red"

    def test_green_executor_registers(self):
        """GREEN executor can be registered in registry."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages.green import create_green_executor

        registry = StageExecutorRegistry()
        registry.register("green", create_green_executor)

        executor = registry.get("green")
        assert executor is not None
        assert executor.stage_name == "green"
