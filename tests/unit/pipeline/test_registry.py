# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-registry

"""Tests for stage executor registry."""

import pytest

from agentforge.core.pipeline import (
    DuplicateStageError,
    PassthroughExecutor,
    StageExecutor,
    StageExecutorRegistry,
    StageNotFoundError,
    StageResult,
    get_registry,
    register_stage,
)


class TestStageExecutorRegistry:
    """Tests for StageExecutorRegistry."""

    def test_register_and_get(self, fresh_registry):
        """Register and retrieve an executor."""
        fresh_registry.register("intake", lambda: PassthroughExecutor("intake"))

        executor = fresh_registry.get("intake")
        assert executor is not None
        assert executor.stage_name == "intake"

    def test_register_class(self, fresh_registry):
        """register_class() creates factory from class."""

        class TestExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

        fresh_registry.register_class("test", TestExecutor)

        executor = fresh_registry.get("test")
        assert isinstance(executor, TestExecutor)

    def test_get_unknown_stage(self, fresh_registry):
        """get() raises StageNotFoundError for unknown stage."""
        with pytest.raises(StageNotFoundError) as exc_info:
            fresh_registry.get("unknown")

        assert "unknown" in str(exc_info.value)
        assert "Available stages" in str(exc_info.value)

    def test_duplicate_registration(self, fresh_registry):
        """Duplicate registration raises error."""
        fresh_registry.register("stage1", lambda: PassthroughExecutor())

        with pytest.raises(DuplicateStageError):
            fresh_registry.register("stage1", lambda: PassthroughExecutor())

    def test_duplicate_with_override(self, fresh_registry):
        """Duplicate registration allowed with allow_override=True."""
        fresh_registry.register("stage1", lambda: PassthroughExecutor("v1"))
        fresh_registry.register(
            "stage1", lambda: PassthroughExecutor("v2"), allow_override=True
        )

        executor = fresh_registry.get("stage1")
        assert executor.stage_name == "v2"

    def test_list_stages(self, fresh_registry):
        """list_stages() returns all registered stage names."""
        fresh_registry.register("intake", lambda: PassthroughExecutor())
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())

        stages = fresh_registry.list_stages()
        assert stages == ["analyze", "clarify", "intake"]  # Sorted

    def test_has_stage(self, fresh_registry):
        """has_stage() checks for stage existence."""
        fresh_registry.register("intake", lambda: PassthroughExecutor())

        assert fresh_registry.has_stage("intake") is True
        assert fresh_registry.has_stage("unknown") is False

    def test_unregister(self, fresh_registry):
        """unregister() removes a stage."""
        fresh_registry.register("intake", lambda: PassthroughExecutor())
        assert fresh_registry.has_stage("intake") is True

        result = fresh_registry.unregister("intake")
        assert result is True
        assert fresh_registry.has_stage("intake") is False

    def test_unregister_nonexistent(self, fresh_registry):
        """unregister() returns False for non-existent stage."""
        result = fresh_registry.unregister("unknown")
        assert result is False

    def test_clear(self, fresh_registry):
        """clear() removes all stages."""
        fresh_registry.register("intake", lambda: PassthroughExecutor())
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        assert len(fresh_registry.list_stages()) == 2

        fresh_registry.clear()
        assert len(fresh_registry.list_stages()) == 0

    def test_factory_creates_new_instances(self, fresh_registry):
        """get() creates new executor instance each time."""
        call_count = [0]

        def factory():
            call_count[0] += 1
            return PassthroughExecutor()

        fresh_registry.register("stage", factory)

        executor1 = fresh_registry.get("stage")
        executor2 = fresh_registry.get("stage")

        assert call_count[0] == 2
        assert executor1 is not executor2


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_registry_singleton(self):
        """get_registry() returns singleton instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_reset_instance(self):
        """reset_instance() clears the singleton."""
        registry1 = get_registry()
        registry1.register("test", lambda: PassthroughExecutor(), allow_override=True)

        StageExecutorRegistry.reset_instance()

        registry2 = get_registry()
        assert registry1 is not registry2
        assert not registry2.has_stage("test")


class TestRegisterStageDecorator:
    """Tests for @register_stage decorator."""

    def test_decorator_registers_class(self):
        """@register_stage registers the executor class."""
        StageExecutorRegistry.reset_instance()

        @register_stage("decorated")
        class DecoratedExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

        registry = get_registry()
        assert registry.has_stage("decorated")

        executor = registry.get("decorated")
        assert isinstance(executor, DecoratedExecutor)

        # Cleanup
        StageExecutorRegistry.reset_instance()

    def test_decorator_returns_class(self):
        """@register_stage returns the original class."""
        StageExecutorRegistry.reset_instance()

        @register_stage("another")
        class AnotherExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

        # Class should still be usable
        instance = AnotherExecutor()
        assert isinstance(instance, StageExecutor)

        # Cleanup
        StageExecutorRegistry.reset_instance()
