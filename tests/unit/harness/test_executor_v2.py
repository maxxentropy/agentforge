# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: executor-v2-tests

"""
Tests for MinimalContextExecutorV2.
"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from agentforge.core.harness.minimal_context.executor_v2 import (
    MinimalContextExecutorV2,
    create_executor_v2,
    should_use_v2,
)


class TestMinimalContextExecutorV2:
    """Tests for MinimalContextExecutorV2."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / "src").mkdir()
            (project / "tests").mkdir()
            (project / ".agentforge").mkdir()
            (project / ".agentforge" / "tasks").mkdir()

            # Create pyproject.toml
            (project / "pyproject.toml").write_text(
                """
[project]
name = "test-project"
requires-python = ">=3.11"
dependencies = ["pytest"]
"""
            )

            yield project

    def test_init_loads_config(self, temp_project):
        """Executor loads config on init."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        assert executor.config is not None
        assert executor.config.defaults.max_steps > 0

    def test_init_loads_fingerprint(self, temp_project):
        """Executor can generate fingerprint."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        fp = executor.get_fingerprint()

        assert fp is not None
        assert fp.technical.language == "python"

    def test_init_loads_template(self, temp_project):
        """Executor loads template for task type."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        assert executor.template is not None
        assert executor.template.task_type == "fix_violation"

    def test_init_with_unknown_task_type_falls_back(self, temp_project):
        """Unknown task type falls back to fix_violation template."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="unknown_type",
        )

        # Should fall back to fix_violation
        assert executor.template.task_type == "fix_violation"

    def test_compaction_disabled(self, temp_project):
        """Compaction can be disabled."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
            compaction_enabled=False,
        )

        assert executor.compaction_manager is None

    def test_compaction_enabled_by_default(self, temp_project):
        """Compaction is enabled by default."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        assert executor.compaction_manager is not None

    def test_audit_disabled_by_env(self, temp_project):
        """Audit can be disabled via environment."""
        with patch.dict(os.environ, {"AGENTFORGE_AUDIT_ENABLED": "false"}):
            executor = MinimalContextExecutorV2(
                project_path=temp_project,
                task_type="fix_violation",
            )

            assert executor.audit_enabled is False

    def test_audit_enabled_by_default(self, temp_project):
        """Audit is enabled by default."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        assert executor.audit_enabled is True

    def test_register_action(self, temp_project):
        """Actions can be registered."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        mock_action = MagicMock()
        executor.register_action("test_action", mock_action)

        assert "test_action" in executor.base_executor.action_executors

    def test_register_actions(self, temp_project):
        """Multiple actions can be registered."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        actions = {
            "action1": MagicMock(),
            "action2": MagicMock(),
        }
        executor.register_actions(actions)

        assert "action1" in executor.base_executor.action_executors
        assert "action2" in executor.base_executor.action_executors


class TestCreateExecutorV2:
    """Tests for create_executor_v2 factory function."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / ".agentforge").mkdir()
            yield project

    def test_creates_executor(self, temp_project):
        """Factory creates executor."""
        executor = create_executor_v2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        assert isinstance(executor, MinimalContextExecutorV2)

    def test_registers_actions(self, temp_project):
        """Factory registers actions."""
        actions = {"test": MagicMock()}
        executor = create_executor_v2(
            project_path=temp_project,
            task_type="fix_violation",
            action_executors=actions,
        )

        assert "test" in executor.base_executor.action_executors


class TestShouldUseV2:
    """Tests for should_use_v2 function."""

    def test_returns_false_by_default(self):
        """Returns False when env not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear the specific var if present
            os.environ.pop("AGENTFORGE_CONTEXT_V2", None)
            assert should_use_v2() is False

    def test_returns_true_when_enabled(self):
        """Returns True when env var is true."""
        with patch.dict(os.environ, {"AGENTFORGE_CONTEXT_V2": "true"}):
            assert should_use_v2() is True

    def test_returns_true_case_insensitive(self):
        """Returns True with any case."""
        with patch.dict(os.environ, {"AGENTFORGE_CONTEXT_V2": "TRUE"}):
            assert should_use_v2() is True

        with patch.dict(os.environ, {"AGENTFORGE_CONTEXT_V2": "True"}):
            assert should_use_v2() is True


class TestFingerprint:
    """Tests for fingerprint functionality."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / ".agentforge").mkdir()
            (project / "pyproject.toml").write_text(
                """
[project]
name = "test"
dependencies = ["pydantic", "fastapi"]
"""
            )
            yield project

    def test_fingerprint_with_constraints(self, temp_project):
        """Fingerprint includes task constraints."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        fp = executor.get_fingerprint(
            constraints={"correctness_first": True},
            success_criteria=["Tests pass"],
        )

        assert fp.task_constraints["correctness_first"] is True
        assert "Tests pass" in fp.success_criteria

    def test_fingerprint_has_project_info(self, temp_project):
        """Fingerprint contains project information."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        fp = executor.get_fingerprint()

        assert fp.technical.language == "python"
        assert "pydantic" in fp.technical.frameworks or "fastapi" in fp.technical.frameworks
