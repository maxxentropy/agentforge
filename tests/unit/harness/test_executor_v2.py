# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: executor-v2-tests
# @impl_path: src/agentforge/core/harness/minimal_context/executor_v2.py

"""
Tests for MinimalContextExecutorV2.

Covers:
- V2 executor initialization and configuration
- Fingerprint generation
- Native tool integration
- run_task_native method
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
    should_use_native_tools,
)
from agentforge.core.harness.minimal_context.native_tool_executor import (
    NativeToolExecutor,
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


class TestNativeToolIntegration:
    """Tests for native tool integration in executor_v2."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / "src").mkdir()
            (project / ".agentforge").mkdir()
            (project / ".agentforge" / "tasks").mkdir()
            (project / "pyproject.toml").write_text(
                """
[project]
name = "test-project"
requires-python = ">=3.11"
"""
            )
            yield project

    def test_executor_has_native_tool_executor(self, temp_project):
        """Executor initializes with native tool executor."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        assert executor.native_tool_executor is not None
        assert isinstance(executor.native_tool_executor, NativeToolExecutor)

    def test_native_executor_has_standard_handlers(self, temp_project):
        """Native executor has standard handlers registered."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        native = executor.native_tool_executor
        assert native.has_action("read_file")
        assert native.has_action("write_file")
        assert native.has_action("complete")
        assert native.has_action("escalate")

    def test_register_action_adds_to_both_executors(self, temp_project):
        """register_action adds to both base and native executors."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        mock_handler = MagicMock(return_value="result")
        executor.register_action("custom_action", mock_handler)

        # Check both executors have the action
        assert "custom_action" in executor.base_executor.action_executors
        assert executor.native_tool_executor.has_action("custom_action")

    def test_get_native_tool_executor(self, temp_project):
        """Can get native tool executor via accessor."""
        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        native = executor.get_native_tool_executor()
        assert native is executor.native_tool_executor

    def _get_violation_context(self):
        """Get minimal violation context for fix_violation tasks."""
        return {
            "violation": {
                "id": "V-TEST-001",
                "type": "test_violation",
                "description": "Test violation for testing",
                "file": "src/test.py",
                "line": 1,
            }
        }

    def test_run_task_native_with_simulated_client(self, temp_project):
        """run_task_native works with simulated LLM client."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        # Create test file
        test_file = temp_project / "src" / "test.py"
        test_file.write_text("# Test file content")

        # Create simulated client that calls complete
        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "complete", "input": {"summary": "Task done"}}
                ],
            },
        ])

        result = executor.run_task_native(
            task_id="test-task-001",
            domain_context=self._get_violation_context(),
            llm_client=client,
            max_steps=5,
        )

        assert result["status"] == "completed"
        assert result["native_tools"] is True
        assert result["steps"] == 1

    def test_run_task_native_with_file_read(self, temp_project):
        """run_task_native can read files via native tools."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        # Create test file
        test_file = temp_project / "src" / "data.txt"
        test_file.write_text("Hello from test file")

        # Client reads file then completes
        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "read_file", "input": {"path": str(test_file)}}
                ],
            },
            {
                "tool_calls": [
                    {"id": "tc_2", "name": "complete", "input": {"summary": "Read file"}}
                ],
            },
        ])

        result = executor.run_task_native(
            task_id="test-task-002",
            domain_context=self._get_violation_context(),
            llm_client=client,
            max_steps=5,
        )

        assert result["status"] == "completed"
        assert result["steps"] == 2

        # Check first step read the file
        outcomes = result["outcomes"]
        assert outcomes[0]["action_name"] == "read_file"
        assert "Hello from test file" in outcomes[0]["result"]

    def test_run_task_native_escalation(self, temp_project):
        """run_task_native handles escalation."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        # Client escalates
        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "escalate", "input": {"reason": "Need help"}}
                ],
            },
        ])

        result = executor.run_task_native(
            task_id="test-task-003",
            domain_context=self._get_violation_context(),
            llm_client=client,
            max_steps=5,
        )

        assert result["status"] == "escalated"
        assert "ESCALATE" in result["outcomes"][0]["result"]

    def test_run_task_native_step_callback(self, temp_project):
        """run_task_native calls step callback."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "complete", "input": {"summary": "Done"}}
                ],
            },
        ])

        step_outcomes = []

        def on_step(outcome):
            step_outcomes.append(outcome)

        executor.run_task_native(
            task_id="test-task-004",
            domain_context=self._get_violation_context(),
            llm_client=client,
            max_steps=5,
            on_step=on_step,
        )

        assert len(step_outcomes) == 1
        assert step_outcomes[0].action_name == "complete"

    def test_run_task_native_max_steps_limit(self, temp_project):
        """run_task_native respects max_steps limit."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutorV2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        # Create file for reading
        (temp_project / "data.txt").write_text("data")

        # Client just reads files forever (no complete)
        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": f"tc_{i}", "name": "read_file", "input": {"path": str(temp_project / "data.txt")}}
                ],
            }
            for i in range(10)
        ])

        result = executor.run_task_native(
            task_id="test-task-005",
            domain_context=self._get_violation_context(),
            llm_client=client,
            max_steps=3,
        )

        assert result["status"] == "stopped"
        assert result["steps"] == 3


class TestShouldUseNativeTools:
    """Tests for should_use_native_tools function."""

    def test_returns_false_by_default(self):
        """Returns False when env not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AGENTFORGE_NATIVE_TOOLS", None)
            assert should_use_native_tools() is False

    def test_returns_true_when_enabled(self):
        """Returns True when env var is true."""
        with patch.dict(os.environ, {"AGENTFORGE_NATIVE_TOOLS": "true"}):
            assert should_use_native_tools() is True

    def test_returns_true_case_insensitive(self):
        """Returns True with any case."""
        with patch.dict(os.environ, {"AGENTFORGE_NATIVE_TOOLS": "TRUE"}):
            assert should_use_native_tools() is True

        with patch.dict(os.environ, {"AGENTFORGE_NATIVE_TOOLS": "True"}):
            assert should_use_native_tools() is True
