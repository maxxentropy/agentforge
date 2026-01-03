# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: stages-init
# @test_path: tests/unit/pipeline/stages/test_stages_init.py

"""Tests for stages package exports and registration."""



class TestStagesPackageExports:
    """Tests for stages package exports."""

    def test_exports_all_executors(self):
        """Package exports all executor classes."""
        from agentforge.core.pipeline.stages import (
            AnalyzeExecutor,
            ClarifyExecutor,
            IntakeExecutor,
            SpecExecutor,
        )

        assert IntakeExecutor is not None, "Expected IntakeExecutor is not None"
        assert ClarifyExecutor is not None, "Expected ClarifyExecutor is not None"
        assert AnalyzeExecutor is not None, "Expected AnalyzeExecutor is not None"
        assert SpecExecutor is not None, "Expected SpecExecutor is not None"

    def test_exports_factory_functions(self):
        """Package exports factory functions."""
        from agentforge.core.pipeline.stages import (
            create_analyze_executor,
            create_clarify_executor,
            create_intake_executor,
            create_spec_executor,
        )

        assert callable(create_intake_executor), "Expected callable() to be truthy"
        assert callable(create_clarify_executor), "Expected callable() to be truthy"
        assert callable(create_analyze_executor), "Expected callable() to be truthy"
        assert callable(create_spec_executor), "Expected callable() to be truthy"

    def test_factory_functions_return_correct_types(self):
        """Factory functions return correct executor types."""
        from agentforge.core.pipeline.stages import (
            AnalyzeExecutor,
            ClarifyExecutor,
            IntakeExecutor,
            SpecExecutor,
            create_analyze_executor,
            create_clarify_executor,
            create_intake_executor,
            create_spec_executor,
        )

        assert isinstance(create_intake_executor(), IntakeExecutor), "Expected isinstance() to be truthy"
        assert isinstance(create_clarify_executor(), ClarifyExecutor), "Expected isinstance() to be truthy"
        assert isinstance(create_analyze_executor(), AnalyzeExecutor), "Expected isinstance() to be truthy"
        assert isinstance(create_spec_executor(), SpecExecutor), "Expected isinstance() to be truthy"


class TestDesignStagesRegistration:
    """Tests for design stages registration function."""

    def test_register_design_stages(self):
        """register_design_stages registers all design pipeline stages."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages import register_design_stages

        registry = StageExecutorRegistry()
        register_design_stages(registry)

        assert registry.has_stage("intake"), "Expected registry.has_stage() to be truthy"
        assert registry.has_stage("clarify"), "Expected registry.has_stage() to be truthy"
        assert registry.has_stage("analyze"), "Expected registry.has_stage() to be truthy"
        assert registry.has_stage("spec"), "Expected registry.has_stage() to be truthy"

    def test_registered_stages_create_correct_executors(self):
        """Registered stages create correct executor instances."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages import (
            AnalyzeExecutor,
            ClarifyExecutor,
            IntakeExecutor,
            SpecExecutor,
            register_design_stages,
        )

        registry = StageExecutorRegistry()
        register_design_stages(registry)

        assert isinstance(registry.get("intake"), IntakeExecutor), "Expected isinstance() to be truthy"
        assert isinstance(registry.get("clarify"), ClarifyExecutor), "Expected isinstance() to be truthy"
        assert isinstance(registry.get("analyze"), AnalyzeExecutor), "Expected isinstance() to be truthy"
        assert isinstance(registry.get("spec"), SpecExecutor), "Expected isinstance() to be truthy"
