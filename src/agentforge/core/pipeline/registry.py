# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-registry
# @test_path: tests/unit/pipeline/test_registry.py

"""
Stage Executor Registry
=======================

Singleton registry for stage executor factories.

Allows registration and retrieval of stage executors by name.
Uses factory pattern to create fresh executor instances.
"""

import logging
from collections.abc import Callable
from typing import Optional

from .stage_executor import StageExecutor

logger = logging.getLogger(__name__)


class StageNotFoundError(Exception):
    """Raised when a requested stage is not registered."""

    pass


class DuplicateStageError(Exception):
    """Raised when attempting to register a stage that already exists."""

    pass


class StageExecutorRegistry:
    """
    Registry for stage executor factories.

    This is a singleton - use get_registry() to get the global instance.
    """

    _instance: Optional["StageExecutorRegistry"] = None

    def __init__(self):
        """Initialize empty registry."""
        self._factories: dict[str, Callable[[], StageExecutor]] = {}

    @classmethod
    def get_instance(cls) -> "StageExecutorRegistry":
        """Get the singleton registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    def register(
        self,
        stage_name: str,
        factory: Callable[[], StageExecutor],
        allow_override: bool = False,
    ) -> None:
        """
        Register a stage executor factory.

        Args:
            stage_name: Name of the stage (e.g., 'intake', 'clarify')
            factory: Callable that returns a StageExecutor instance
            allow_override: If True, allow overwriting existing registration

        Raises:
            DuplicateStageError: If stage already registered and allow_override=False
        """
        if stage_name in self._factories and not allow_override:
            raise DuplicateStageError(
                f"Stage '{stage_name}' is already registered. "
                "Use allow_override=True to replace."
            )

        self._factories[stage_name] = factory
        logger.debug(f"Registered stage executor: {stage_name}")

    def register_class(
        self,
        stage_name: str,
        executor_class: type[StageExecutor],
        allow_override: bool = False,
    ) -> None:
        """
        Register a stage executor class (creates factory automatically).

        Args:
            stage_name: Name of the stage
            executor_class: StageExecutor subclass to instantiate
            allow_override: If True, allow overwriting existing registration
        """
        self.register(stage_name, lambda: executor_class(), allow_override)

    def get(self, stage_name: str) -> StageExecutor:
        """
        Get executor instance for a stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Fresh StageExecutor instance

        Raises:
            StageNotFoundError: If stage is not registered
        """
        if stage_name not in self._factories:
            available = ", ".join(sorted(self._factories.keys())) or "(none)"
            raise StageNotFoundError(
                f"Stage '{stage_name}' is not registered. "
                f"Available stages: {available}"
            )

        return self._factories[stage_name]()

    def list_stages(self) -> list[str]:
        """
        List all registered stage names.

        Returns:
            Sorted list of stage names
        """
        return sorted(self._factories.keys())

    def has_stage(self, stage_name: str) -> bool:
        """
        Check if a stage is registered.

        Args:
            stage_name: Name of the stage

        Returns:
            True if registered, False otherwise
        """
        return stage_name in self._factories

    def unregister(self, stage_name: str) -> bool:
        """
        Remove a stage from the registry.

        Args:
            stage_name: Name of the stage to remove

        Returns:
            True if removed, False if not found
        """
        if stage_name in self._factories:
            del self._factories[stage_name]
            logger.debug(f"Unregistered stage executor: {stage_name}")
            return True
        return False

    def clear(self) -> None:
        """Remove all registered stages."""
        self._factories.clear()
        logger.debug("Cleared all stage executors from registry")


def get_registry() -> StageExecutorRegistry:
    """
    Get the global stage executor registry.

    Returns:
        Singleton StageExecutorRegistry instance
    """
    return StageExecutorRegistry.get_instance()


def register_stage(
    stage_name: str,
    factory: Callable[[], StageExecutor] = None,
    allow_override: bool = False,
):
    """
    Decorator to register a stage executor class.

    Usage:
        @register_stage("intake")
        class IntakeExecutor(StageExecutor):
            ...

    Or with explicit name:
        @register_stage("custom-intake")
        class IntakeExecutor(StageExecutor):
            ...
    """

    def decorator(cls: type[StageExecutor]) -> type[StageExecutor]:
        get_registry().register_class(stage_name, cls, allow_override)
        return cls

    # If used without parentheses, factory is actually the class
    if factory is not None and isinstance(factory, type):
        cls = factory
        get_registry().register_class(stage_name, cls, allow_override)
        return cls

    return decorator
