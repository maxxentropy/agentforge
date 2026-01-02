# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_id: pipeline-controller-phase2-v1
# @component_id: stages-init
# @test_path: tests/unit/pipeline/stages/test_stages_init.py

"""Tests for stages package exports and registration."""

import pytest


class TestStagesPackageExports:
    """Tests for stages package exports."""

    def test_exports_all_executors(self):
        """Package exports all executor classes."""
        from agentforge.core.pipeline.stages import (
            IntakeExecutor,
            ClarifyExecutor,
            AnalyzeExecutor,
            SpecExecutor,
        )

        assert IntakeExecutor is not None
        assert ClarifyExecutor is not None
        assert AnalyzeExecutor is not None
        assert SpecExecutor is not None

    def test_exports_factory_functions(self):
        """Package exports factory functions."""
        from agentforge.core.pipeline.stages import (
            create_intake_executor,
            create_clarify_executor,
            create_analyze_executor,
            create_spec_executor,
        )

        assert callable(create_intake_executor)
        assert callable(create_clarify_executor)
        assert callable(create_analyze_executor)
        assert callable(create_spec_executor)

    def test_factory_functions_return_correct_types(self):
        """Factory functions return correct executor types."""
        from agentforge.core.pipeline.stages import (
            IntakeExecutor,
            ClarifyExecutor,
            AnalyzeExecutor,
            SpecExecutor,
            create_intake_executor,
            create_clarify_executor,
            create_analyze_executor,
            create_spec_executor,
        )

        assert isinstance(create_intake_executor(), IntakeExecutor)
        assert isinstance(create_clarify_executor(), ClarifyExecutor)
        assert isinstance(create_analyze_executor(), AnalyzeExecutor)
        assert isinstance(create_spec_executor(), SpecExecutor)


class TestDesignStagesRegistration:
    """Tests for design stages registration function."""

    def test_register_design_stages(self):
        """register_design_stages registers all design pipeline stages."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages import register_design_stages

        registry = StageExecutorRegistry()
        register_design_stages(registry)

        assert registry.has_stage("intake")
        assert registry.has_stage("clarify")
        assert registry.has_stage("analyze")
        assert registry.has_stage("spec")

    def test_registered_stages_create_correct_executors(self):
        """Registered stages create correct executor instances."""
        from agentforge.core.pipeline import StageExecutorRegistry
        from agentforge.core.pipeline.stages import (
            IntakeExecutor,
            ClarifyExecutor,
            AnalyzeExecutor,
            SpecExecutor,
            register_design_stages,
        )

        registry = StageExecutorRegistry()
        register_design_stages(registry)

        assert isinstance(registry.get("intake"), IntakeExecutor)
        assert isinstance(registry.get("clarify"), ClarifyExecutor)
        assert isinstance(registry.get("analyze"), AnalyzeExecutor)
        assert isinstance(registry.get("spec"), SpecExecutor)
