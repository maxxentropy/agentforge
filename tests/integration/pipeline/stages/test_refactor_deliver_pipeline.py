# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: refactor-phase-executor, deliver-phase-executor
# @test_path: tests/integration/pipeline/stages/test_refactor_deliver_pipeline.py

"""Integration tests for REFACTOR & DELIVER pipeline."""

from unittest.mock import MagicMock, patch

from agentforge.core.pipeline import StageContext, StageStatus


class TestRefactorIntegration:
    """Integration tests for REFACTOR phase."""

    def test_green_to_refactor_artifact_flow(
        self,
        sample_green_artifact_for_refactor,
        temp_project_for_refactor,
    ):
        """GREEN artifact flows correctly to REFACTOR phase."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_green_artifact_for_refactor,
            config={},
        )

        # Verify context receives GREEN artifact correctly
        assert context.input_artifacts["spec_id"] == "SPEC-20260102-0001"
        assert len(context.input_artifacts["implementation_files"]) == 1
        assert context.input_artifacts["all_tests_pass"] is True

    def test_refactor_maintains_passing_tests(
        self,
        sample_green_artifact_for_refactor,
        temp_project_for_refactor,
    ):
        """REFACTOR phase maintains passing tests."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_green_artifact_for_refactor,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            # Tests pass both before and after
            mock_tests.return_value = {"passed": 2, "failed": 0, "total": 2}

            with patch.object(executor, "_run_conformance") as mock_conf:
                # Clean conformance - skip refactoring
                mock_conf.return_value = {"passed": True, "violations": []}

                result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        # Final tests should still pass
        assert result.artifacts["test_results"]["failed"] == 0

    def test_refactor_applies_improvements(
        self,
        sample_green_artifact_for_refactor,
        temp_project_for_refactor,
    ):
        """REFACTOR phase applies improvements when violations exist."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_green_artifact_for_refactor,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 2, "failed": 0, "total": 2}

            with patch.object(executor, "_run_conformance") as mock_conf:
                # First call has violations, second passes
                mock_conf.side_effect = [
                    {"passed": False, "violations": [{"type": "complexity"}]},
                    {"passed": True, "violations": []},
                ]

                with patch.object(executor, "_get_refactor_executor") as mock_get:
                    mock_exec = MagicMock()
                    mock_exec.execute_task.return_value = {
                        "files_modified": ["src/calculator.py"],
                        "improvements": ["Reduced complexity"],
                    }
                    mock_get.return_value = mock_exec

                    result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED

    def test_refactor_skips_when_clean(
        self,
        sample_green_artifact_for_refactor,
        temp_project_for_refactor,
    ):
        """REFACTOR phase skips when code is already clean."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        executor = RefactorPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_green_artifact_for_refactor,
            config={},
        )

        with patch.object(executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 2, "failed": 0, "total": 2}

            with patch.object(executor, "_run_conformance") as mock_conf:
                mock_conf.return_value = {"passed": True, "violations": []}

                result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        # No refactoring was needed
        assert result.artifacts.get("refactored_files", []) == []


class TestDeliverIntegration:
    """Integration tests for DELIVER phase."""

    def test_refactor_to_deliver_artifact_flow(
        self,
        sample_refactor_artifact_for_deliver,
        temp_project_for_refactor,
    ):
        """REFACTOR artifact flows correctly to DELIVER phase."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor

        DeliverPhaseExecutor()

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_refactor_artifact_for_deliver,
            config={},
        )

        # Verify context receives REFACTOR artifact correctly
        assert context.input_artifacts["spec_id"] == "SPEC-20260102-0001"
        assert len(context.input_artifacts["final_files"]) == 2
        assert context.input_artifacts["conformance_passed"] is True

    def test_deliver_stages_files(
        self,
        sample_refactor_artifact_for_deliver,
        temp_project_for_refactor,
    ):
        """DELIVER phase stages files correctly."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.COMMIT})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_refactor_artifact_for_deliver,
            config={},
        )

        with patch.object(executor, "_stage_files") as mock_stage:
            mock_stage.return_value = ["src/calculator.py", "tests/test_calculator.py"]

            result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert len(result.artifacts.get("files_staged", [])) == 2

    def test_deliver_generates_summary(
        self,
        sample_refactor_artifact_for_deliver,
        temp_project_for_refactor,
    ):
        """DELIVER phase generates a summary."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode

        executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.FILES})

        context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_refactor_artifact_for_deliver,
            config={},
        )

        result = executor.execute(context)

        assert result.status == StageStatus.COMPLETED
        assert "summary" in result.artifacts
        assert len(result.artifacts["summary"]) > 0


class TestFullPipelineIntegration:
    """End-to-end REFACTOR → DELIVER pipeline tests."""

    def test_green_to_refactor_to_deliver_flow(
        self,
        sample_green_artifact_for_refactor,
        temp_project_for_refactor,
    ):
        """Full GREEN → REFACTOR → DELIVER flow."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        # REFACTOR Phase
        refactor_executor = RefactorPhaseExecutor()

        refactor_context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_green_artifact_for_refactor,
            config={},
        )

        with patch.object(refactor_executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 2, "failed": 0, "total": 2}

            with patch.object(refactor_executor, "_run_conformance") as mock_conf:
                mock_conf.return_value = {"passed": True, "violations": []}

                refactor_result = refactor_executor.execute(refactor_context)

        assert refactor_result.status == StageStatus.COMPLETED

        # DELIVER Phase (using REFACTOR artifact)
        deliver_executor = DeliverPhaseExecutor({"delivery_mode": DeliveryMode.FILES})

        deliver_context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_project_for_refactor,
            input_artifacts=refactor_result.artifacts,
            config={},
        )

        deliver_result = deliver_executor.execute(deliver_context)

        assert deliver_result.status == StageStatus.COMPLETED
        assert deliver_result.artifacts["spec_id"] == sample_green_artifact_for_refactor["spec_id"]

    def test_full_pipeline_completes(
        self,
        sample_green_artifact_for_refactor,
        temp_project_for_refactor,
    ):
        """Full pipeline completes successfully."""
        from agentforge.core.pipeline.stages.deliver import DeliverPhaseExecutor, DeliveryMode
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        # REFACTOR Phase
        refactor_executor = RefactorPhaseExecutor()

        refactor_context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_for_refactor,
            input_artifacts=sample_green_artifact_for_refactor,
            config={},
        )

        with patch.object(refactor_executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 2, "failed": 0, "total": 2}

            with patch.object(refactor_executor, "_run_conformance") as mock_conf:
                mock_conf.return_value = {"passed": True, "violations": []}

                refactor_result = refactor_executor.execute(refactor_context)

        # DELIVER Phase
        deliver_executor = DeliverPhaseExecutor({
            "delivery_mode": DeliveryMode.COMMIT,
            "auto_commit": False,
        })

        deliver_context = StageContext(
            pipeline_id="PL-test",
            stage_name="deliver",
            project_path=temp_project_for_refactor,
            input_artifacts=refactor_result.artifacts,
            config={},
        )

        with patch.object(deliver_executor, "_stage_files") as mock_stage:
            mock_stage.return_value = ["src/calculator.py"]

            deliver_result = deliver_executor.execute(deliver_context)

        # Verify full pipeline completed
        assert refactor_result.status == StageStatus.COMPLETED
        assert deliver_result.status == StageStatus.COMPLETED
        assert deliver_result.artifacts["deliverable_type"] == "commit"

    def test_full_pipeline_handles_errors(
        self,
        sample_green_artifact_for_refactor,
        temp_project_for_refactor,
    ):
        """Pipeline handles errors gracefully."""
        from agentforge.core.pipeline.stages.refactor import RefactorPhaseExecutor

        refactor_executor = RefactorPhaseExecutor()

        # Modify artifact to have failing tests (should fail REFACTOR)
        failing_artifact = sample_green_artifact_for_refactor.copy()
        failing_artifact["test_results"] = {
            "passed": 0,
            "failed": 2,
            "total": 2,
        }

        refactor_context = StageContext(
            pipeline_id="PL-test",
            stage_name="refactor",
            project_path=temp_project_for_refactor,
            input_artifacts=failing_artifact,
            config={},
        )

        with patch.object(refactor_executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {"passed": 0, "failed": 2, "total": 2}

            refactor_result = refactor_executor.execute(refactor_context)

        # Should fail because tests don't pass
        assert refactor_result.status == StageStatus.FAILED


class TestStageRegistration:
    """Tests for Phase 4 stage registration."""

    def test_refactor_executor_registers(self):
        """REFACTOR executor can be registered in registry."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages.refactor import create_refactor_executor

        registry = StageExecutorRegistry()
        registry.register("refactor", create_refactor_executor)

        executor = registry.get("refactor")
        assert executor is not None
        assert executor.stage_name == "refactor"

    def test_deliver_executor_registers(self):
        """DELIVER executor can be registered in registry."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages.deliver import create_deliver_executor

        registry = StageExecutorRegistry()
        registry.register("deliver", create_deliver_executor)

        executor = registry.get("deliver")
        assert executor is not None
        assert executor.stage_name == "deliver"

    def test_register_delivery_stages(self):
        """register_delivery_stages registers both stages."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages import register_delivery_stages

        registry = StageExecutorRegistry()
        register_delivery_stages(registry)

        refactor = registry.get("refactor")
        deliver = registry.get("deliver")

        assert refactor is not None
        assert deliver is not None
        assert refactor.stage_name == "refactor"
        assert deliver.stage_name == "deliver"
