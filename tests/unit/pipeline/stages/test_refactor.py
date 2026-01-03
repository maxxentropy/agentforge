# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: refactor-phase-executor
# @test_path: tests/unit/pipeline/stages/test_refactor.py

"""Unit tests for RefactorPhaseExecutor."""

from unittest.mock import MagicMock, Mock, patch

from agentforge.core.pipeline import StageContext, StageStatus


class TestRefactorPhaseExecutor:
    """Tests for RefactorPhaseExecutor class."""

    def test_stage_name_is_refactor(self):
        """RefactorPhaseExecutor has stage_name 'refactor'."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()
        assert executor.stage_name == "refactor", "Expected executor.stage_name to equal 'refactor'"

    def test_artifact_type_is_refactored_code(self):
        """RefactorPhaseExecutor has artifact_type 'refactored_code'."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()
        assert executor.artifact_type == "refactored_code", "Expected executor.artifact_type to equal 'refactored_code'"

    def test_required_input_fields(self):
        """RefactorPhaseExecutor requires spec_id, implementation_files, test_results."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()
        assert "spec_id" in executor.required_input_fields, "Expected 'spec_id' in executor.required_input_fields"
        assert "implementation_files" in executor.required_input_fields, "Expected 'implementation_files' in executor.required_input_fields"
        assert "test_results" in executor.required_input_fields, "Expected 'test_results' in executor.required_input_fields"

    def test_output_fields(self):
        """RefactorPhaseExecutor outputs expected fields."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()
        assert "spec_id" in executor.output_fields, "Expected 'spec_id' in executor.output_fields"
        assert "refactored_files" in executor.output_fields, "Expected 'refactored_files' in executor.output_fields"
        assert "final_files" in executor.output_fields, "Expected 'final_files' in executor.output_fields"

    def test_has_max_iterations_config(self):
        """RefactorPhaseExecutor has max_iterations configuration."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()
        assert hasattr(executor, "max_iterations"), "Expected hasattr() to be truthy"
        assert executor.max_iterations == 10, "Expected executor.max_iterations to equal 10"

    def test_max_iterations_from_config(self):
        """RefactorPhaseExecutor uses max_iterations from config."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor({"max_iterations": 5})
        assert executor.max_iterations == 5, "Expected executor.max_iterations to equal 5"


class TestRefactorPhaseSkipLogic:
    """Tests for REFACTOR phase skip logic."""

    def test_skips_when_no_conformance_violations(
        self,
        sample_green_artifact,
        temp_project_path,
        mock_conformance_passing,
    ):
        """Skips refactoring when conformance passes with no violations."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 3, "failed": 0, "total": 3}

            with patch.object(executor, "_run_conformance") as mock_conf:
                mock_conf.return_value = mock_conformance_passing

                result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED, "Expected result.status to equal StageStatus.COMPLETED"
        # Should be passthrough (no refactoring needed)
        assert result.artifacts.get("refactored_files") == [], "Expected result.artifacts.get('refac... to equal []"

    def test_skips_when_tests_pass_and_conformance_clean(
        self,
        sample_green_artifact,
        temp_project_path,
    ):
        """Skips refactoring when tests pass and conformance is clean."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 3, "failed": 0, "total": 3}

            with patch.object(executor, "_run_conformance") as mock_conf:
                mock_conf.return_value = {"passed": True, "violations": []}

                result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED, "Expected result.status to equal StageStatus.COMPLETED"


class TestRefactorPhaseExecution:
    """Tests for REFACTOR phase execution."""

    def test_applies_refactorings_for_violations(
        self,
        sample_green_artifact,
        temp_project_path,
        mock_conformance_violations,
    ):
        """Applies refactorings when conformance has violations."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            # Initial and final tests pass
            mock_tests.return_value = {"passed": 3, "failed": 0, "total": 3}

            with patch.object(executor, "_run_conformance") as mock_conf:
                # First call has violations, second call passes
                mock_conf.side_effect = [
                    mock_conformance_violations,
                    {"passed": True, "violations": []},
                ]

                with patch.object(executor, "_get_refactor_executor") as mock_get:
                    mock_exec = MagicMock()
                    mock_exec.execute_task.return_value = {
                        "files_modified": ["src/auth/oauth_provider.py"],
                        "improvements": ["Added docstrings"],
                    }
                    mock_get.return_value = mock_exec

                    result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED, "Expected result.status to equal StageStatus.COMPLETED"
        assert result.artifacts is not None, "Expected result.artifacts is not None"

    def test_verifies_tests_still_pass_after_refactoring(
        self,
        sample_green_artifact,
        temp_project_path,
        mock_conformance_violations,
    ):
        """Verifies tests still pass after refactoring."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            # Track call count
            mock_tests.return_value = {"passed": 3, "failed": 0, "total": 3}

            with patch.object(executor, "_run_conformance") as mock_conf:
                mock_conf.side_effect = [
                    mock_conformance_violations,
                    {"passed": True, "violations": []},
                ]

                with patch.object(executor, "_get_refactor_executor") as mock_get:
                    mock_exec = MagicMock()
                    mock_exec.execute_task.return_value = {}
                    mock_get.return_value = mock_exec

                    executor.execute(context)

        # Tests should be run multiple times
        assert mock_tests.call_count >= 2, "Expected mock_tests.call_count >= 2"

    def test_fails_if_tests_break_during_refactoring(
        self,
        sample_green_artifact,
        temp_project_path,
        mock_conformance_violations,
    ):
        """Fails if refactoring breaks tests."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            # Initial tests pass, final tests fail
            mock_tests.side_effect = [
                {"passed": 3, "failed": 0, "total": 3},
                {"passed": 1, "failed": 2, "total": 3},
            ]

            with patch.object(executor, "_run_conformance") as mock_conf:
                mock_conf.return_value = mock_conformance_violations

                with patch.object(executor, "_get_refactor_executor") as mock_get:
                    mock_exec = MagicMock()
                    mock_exec.execute_task.return_value = {}
                    mock_get.return_value = mock_exec

                    result = executor.execute(context)

        assert result.status == StageStatus.FAILED, "Expected result.status to equal StageStatus.FAILED"
        assert "tests" in result.error.lower(), "Expected 'tests' in result.error.lower()"

    def test_fails_if_initial_tests_fail(
        self,
        sample_green_artifact,
        temp_project_path,
    ):
        """Fails if initial tests fail before refactoring."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 0, "failed": 3, "total": 3}

            result = executor.execute(context)

        assert result.status == StageStatus.FAILED, "Expected result.status to equal StageStatus.FAILED"
        assert "must pass" in result.error.lower(), "Expected 'must pass' in result.error.lower()"


class TestRefactorPhaseTestExecution:
    """Tests for REFACTOR phase test execution."""

    def test_runs_tests_returns_results(self, sample_green_artifact, temp_project_path):
        """_run_tests executes pytest and returns results."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout="3 passed, 1 failed PASSED PASSED PASSED FAILED",
                stderr="",
                returncode=1,
            )

            results = executor._run_tests(context)

        assert "passed" in results, "Expected 'passed' in results"
        assert "failed" in results, "Expected 'failed' in results"

    def test_handles_test_timeout(self, sample_green_artifact, temp_project_path):
        """Handles test execution timeout."""
        import subprocess

        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired("pytest", 300)

            results = executor._run_tests(context)

        assert "error" in results, "Expected 'error' in results"

    def test_parses_pytest_output(self, sample_green_artifact, temp_project_path):
        """Parses pytest output correctly."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout="test_one PASSED\ntest_two PASSED\ntest_three PASSED\n3 passed",
                stderr="",
                returncode=0,
            )

            results = executor._run_tests(context)

        assert results["passed"] == 3, "Expected results['passed'] to equal 3"


class TestRefactorPhaseConformance:
    """Tests for REFACTOR phase conformance checks."""

    def test_runs_conformance_checks(self, sample_green_artifact, temp_project_path):
        """_run_conformance executes conformance check."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout='{"passed": true, "violations": []}',
                stderr="",
                returncode=0,
            )

            results = executor._run_conformance(context)

        assert results["passed"] is True, "Expected results['passed'] is True"

    def test_handles_conformance_failure(self, sample_green_artifact, temp_project_path):
        """Handles conformance check execution failure."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = Exception("Process error")

            results = executor._run_conformance(context)

        # Should handle gracefully
        assert "error" in results or results.get("passed", False), "Assertion failed"

    def test_handles_conformance_json_output(self, sample_green_artifact, temp_project_path):
        """Parses JSON conformance output."""
        import json

        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        violations = [{"type": "complexity", "file": "test.py", "line": 10}]

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                stdout=json.dumps({"passed": False, "violations": violations}),
                stderr="",
                returncode=1,
            )

            results = executor._run_conformance(context)

        assert results["passed"] is False, "Expected results['passed'] is False"
        assert len(results["violations"]) == 1, "Expected len(results['violations']) to equal 1"


class TestRefactorPhaseArtifactBuilding:
    """Tests for REFACTOR phase artifact building."""

    def test_creates_passthrough_artifact(self, sample_green_artifact, temp_project_path):
        """Creates passthrough artifact when no refactoring needed."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        test_results = {"passed": 3, "failed": 0, "total": 3}

        artifact = executor._create_passthrough_artifact(context, test_results)

        assert artifact["spec_id"] == sample_green_artifact["spec_id"], "Expected artifact['spec_id'] to equal sample_green_artifact['spec..."
        assert artifact["refactored_files"] == [], "Expected artifact['refactored_files'] to equal []"
        assert artifact["conformance_passed"] is True, "Expected artifact['conformance_passed'] is True"

    def test_builds_refactor_artifact(self, sample_green_artifact, temp_project_path):
        """Builds complete refactor artifact."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        result = {
            "files_modified": ["src/auth/oauth_provider.py"],
            "improvements": ["Added docstrings"],
        }
        test_results = {"passed": 3, "failed": 0, "total": 3}
        conformance = {"passed": True, "violations": []}

        artifact = executor._build_artifact(context, result, test_results, conformance)

        assert artifact["spec_id"] == sample_green_artifact["spec_id"], "Expected artifact['spec_id'] to equal sample_green_artifact['spec..."
        assert "final_files" in artifact, "Expected 'final_files' in artifact"
        assert artifact["conformance_passed"] is True, "Expected artifact['conformance_passed'] is True"

    def test_includes_improvements_in_artifact(self, sample_green_artifact, temp_project_path):
        """Artifact includes improvements from refactoring."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=sample_green_artifact,
            config={},
        )

        result = {
            "files_modified": ["src/auth/oauth_provider.py"],
            "improvements": ["Added docstrings", "Reduced complexity"],
        }
        test_results = {"passed": 3, "failed": 0, "total": 3}
        conformance = {"passed": True, "violations": []}

        artifact = executor._build_artifact(context, result, test_results, conformance)

        assert "improvements" in artifact, "Expected 'improvements' in artifact"
        assert len(artifact["improvements"]) == 2, "Expected len(artifact['improvements']) to equal 2"


class TestRefactorPhaseTaskBuilding:
    """Tests for REFACTOR phase task building."""

    def test_builds_task_with_files(self, sample_green_artifact):
        """Task includes implementation files."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        test_results = {"passed": 3, "failed": 0, "total": 3}
        conformance = {"violations": []}

        task = executor._build_task(sample_green_artifact, test_results, conformance)

        assert "src/auth/oauth_provider.py" in task, "Expected 'src/auth/oauth_provider.py' in task"

    def test_builds_task_with_test_status(self, sample_green_artifact):
        """Task includes test status."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        test_results = {"passed": 3, "failed": 0, "total": 3}
        conformance = {"violations": []}

        task = executor._build_task(sample_green_artifact, test_results, conformance)

        assert "3 passed" in task, "Expected '3 passed' in task"

    def test_builds_task_with_acceptance_criteria(self, sample_green_artifact):
        """Task includes acceptance criteria."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        test_results = {"passed": 3, "failed": 0, "total": 3}
        conformance = {"violations": []}

        task = executor._build_task(sample_green_artifact, test_results, conformance)

        assert "OAuth flow" in task or "criterion" in task.lower(), "Assertion failed"


class TestRefactorPhasePrompts:
    """Tests for REFACTOR phase prompts."""

    def test_system_prompt_mentions_refactor(self):
        """System prompt mentions REFACTOR phase."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        prompt = executor.SYSTEM_PROMPT

        assert "refactor" in prompt.lower(), "Expected 'refactor' in prompt.lower()"
        assert "test" in prompt.lower(), "Expected 'test' in prompt.lower()"
        assert "quality" in prompt.lower(), "Expected 'quality' in prompt.lower()"

    def test_task_template_has_placeholders(self):
        """Task template has required placeholders."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        template = executor.TASK_TEMPLATE

        assert "{implementation_files}" in template, "Expected '{implementation_files}' in template"
        assert "{test_status}" in template, "Expected '{test_status}' in template"
        assert "{acceptance_criteria}" in template, "Expected '{acceptance_criteria}' in template"


class TestRefactorPhaseValidation:
    """Tests for REFACTOR phase artifact validation."""

    def test_validates_final_files_present(self):
        """Validates that final_files is present."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "refactored_files": [],
            "final_files": [],
            "conformance_passed": True,
        }

        validation = executor.validate_output(artifact)

        # Should warn or fail on empty final_files
        assert not validation.valid or len(validation.warnings) > 0, "Assertion failed"

    def test_validates_conformance_status(self):
        """Validates conformance status is present."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "refactored_files": [],
            "final_files": ["file.py"],
            "conformance_passed": True,
        }

        validation = executor.validate_output(artifact)

        # Should be valid when conformance passed
        assert validation.valid, "Expected validation.valid to be truthy"


class TestRefactorPhaseEdgeCases:
    """Tests for REFACTOR phase edge cases."""

    def test_handles_empty_implementation_files(self, temp_project_path):
        """Handles input with empty implementation files."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "implementation_files": [],
            "test_results": {"passed": 0, "failed": 0, "total": 0},
        }

        StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_path,
            input_artifacts=artifact,
            config={},
        )

        test_results = {"passed": 0, "failed": 0, "total": 0}
        conformance = {"violations": []}

        # Should handle gracefully
        task = executor._build_task(artifact, test_results, conformance)
        assert isinstance(task, str), "Expected isinstance() to be truthy"

    def test_handles_no_test_results(self, temp_project_path):
        """Handles input with missing test results."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        artifact = {
            "spec_id": "SPEC-123",
            "implementation_files": ["file.py"],
            "test_results": {},
        }

        test_results = {}
        conformance = {"violations": []}

        # Should handle gracefully
        task = executor._build_task(artifact, test_results, conformance)
        assert isinstance(task, str), "Expected isinstance() to be truthy"


class TestCreateRefactorExecutor:
    """Tests for factory function."""

    def test_creates_executor_instance(self):
        """Factory creates RefactorPhaseExecutor instance."""
        from agentforge.core.pipeline.stages.refactor import (
            RefactorPhaseExecutor,
            create_refactor_executor,
        )

        executor = create_refactor_executor()

        assert isinstance(executor, RefactorPhaseExecutor), "Expected isinstance() to be truthy"

    def test_passes_config(self):
        """Factory passes config to executor."""
        from agentforge.core.pipeline.stages.refactor import create_refactor_executor

        config = {"max_iterations": 5}

        executor = create_refactor_executor(config)

        assert executor.max_iterations == 5, "Expected executor.max_iterations to equal 5"
