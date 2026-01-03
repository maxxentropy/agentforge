# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: template-context-builder-tests

"""
Tests for TemplateContextBuilder integration.

Tests that the TemplateContextBuilder properly:
- Uses templates to build context
- Translates phases correctly for different task types
- Produces correct messages for executor
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest

from agentforge.core.harness.minimal_context.state_store import (
    TaskStateStore,
)
from agentforge.core.harness.minimal_context.template_context_builder import (
    TemplateContextBuilder,
    TemplateStepContext,
)


def get_required_context_for_task_type(task_type: str) -> dict[str, Any]:
    """Get the minimum required context_data for a task type."""
    contexts = {
        "fix_violation": {
            "violation": {
                "id": "V-001",
                "check_id": "CHECK-001",
                "file": "test.py",
                "message": "Test violation",
            },
        },
        "implement_feature": {
            "spec": {"name": "Test Feature", "description": "Test description"},
            "failing_tests": ["test_example"],
        },
        "write_tests": {
            "target_code": "def example(): pass",
            "test_specification": "Test the example function",
            "spec_requirements": ["Test should cover edge cases"],
        },
        "discovery": {},  # Discovery has no required fields in init phase
        "bridge": {
            "target_contracts": [{"name": "IContract", "methods": ["execute"]}],
        },
        "code_review": {
            "diff_summary": "Added new function",
        },
        "refactor": {
            "target_code": "def old_function(): pass",
            "refactor_goal": "Improve code readability",
        },
    }
    return contexts.get(task_type, {})


class TestTemplateContextBuilder:
    """Tests for TemplateContextBuilder."""

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

    @pytest.fixture
    def state_store(self, temp_project):
        """Create a state store."""
        return TaskStateStore(temp_project)

    @pytest.fixture
    def task_state(self, state_store):
        """Create a test task state with required context."""
        state = state_store.create_task(
            task_type="fix_violation",
            goal="Fix the violation",
            success_criteria=["Violation is resolved"],
            task_id="test-task-001",
            context_data={
                "violation": {
                    "id": "V-001",
                    "check_id": "CHECK-001",
                    "file": "test.py",
                    "message": "Test violation",
                },
            },
        )
        return state

    def test_init_loads_template(self, temp_project, state_store):
        """Builder loads template for task type."""
        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="fix_violation",
        )

        assert builder.template is not None, "Expected builder.template is not None"
        assert builder.template.task_type == "fix_violation", "Expected builder.template.task_type to equal 'fix_violation'"

    def test_init_falls_back_to_fix_violation(self, temp_project, state_store):
        """Builder falls back to fix_violation for unknown type."""
        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="unknown_type",
        )

        assert builder.template.task_type == "fix_violation", "Expected builder.template.task_type to equal 'fix_violation'"

    def test_build_returns_template_step_context(self, temp_project, state_store, task_state):
        """build() returns TemplateStepContext."""
        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="fix_violation",
        )

        context = builder.build(task_state.task_id)

        assert isinstance(context, TemplateStepContext), "Expected isinstance() to be truthy"
        assert context.system_prompt != "", "Expected context.system_prompt to not equal ''"
        assert context.user_message != "", "Expected context.user_message to not equal ''"
        assert context.template_name == "fix_violation", "Expected context.template_name to equal 'fix_violation'"

    def test_build_messages_returns_list(self, temp_project, state_store, task_state):
        """build_messages() returns message list for executor."""
        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="fix_violation",
        )

        messages = builder.build_messages(task_state.task_id)

        assert isinstance(messages, list), "Expected isinstance() to be truthy"
        assert len(messages) == 2, "Expected len(messages) to equal 2"
        assert messages[0]["role"] == "system", "Expected messages[0]['role'] to equal 'system'"
        assert messages[1]["role"] == "user", "Expected messages[1]['role'] to equal 'user'"

    def test_phases_property(self, temp_project, state_store):
        """phases property returns template phases."""
        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="fix_violation",
        )

        assert builder.phases == ["init", "analyze", "implement", "verify"], "Expected builder.phases to equal ['init', 'analyze', 'implem..."


class TestTemplateContextBuilderPhaseTranslation:
    """Tests for phase translation in TemplateContextBuilder."""

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
                '[project]\nname = "test"\n'
            )
            yield project

    @pytest.fixture
    def state_store(self, temp_project):
        return TaskStateStore(temp_project)

    def test_discovery_phase_translation_init(self, temp_project, state_store):
        """Discovery task translates init phase to scan."""
        task_id = "discovery-001"
        state_store.create_task(
            task_type="discovery",
            goal="Discover codebase",
            success_criteria=["Codebase analyzed"],
            task_id=task_id,
            context_data=get_required_context_for_task_type("discovery"),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="discovery",
        )

        context = builder.build(task_id)

        # Phase should be translated from init to scan
        assert context.phase == "scan", "Expected context.phase to equal 'scan'"
        assert context.template_name == "discovery", "Expected context.template_name to equal 'discovery'"

    def test_bridge_phase_translation_init(self, temp_project, state_store):
        """Bridge task translates init phase to analyze."""
        task_id = "bridge-001"
        state_store.create_task(
            task_type="bridge",
            goal="Map contracts",
            success_criteria=["Contracts mapped"],
            task_id=task_id,
            context_data=get_required_context_for_task_type("bridge"),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="bridge",
        )

        context = builder.build(task_id)

        # Phase should be translated from init to analyze
        assert context.phase == "analyze", "Expected context.phase to equal 'analyze'"
        assert context.template_name == "bridge", "Expected context.template_name to equal 'bridge'"

    def test_code_review_phase_translation(self, temp_project, state_store):
        """Code review task uses its own phase names."""
        task_id = "review-001"
        state_store.create_task(
            task_type="code_review",
            goal="Review PR",
            success_criteria=["PR reviewed"],
            task_id=task_id,
            context_data=get_required_context_for_task_type("code_review"),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="code_review",
        )

        context = builder.build(task_id)

        # Init stays as init for code_review
        assert context.phase == "init", "Expected context.phase to equal 'init'"
        assert context.template_name == "code_review", "Expected context.template_name to equal 'code_review'"

    def test_fix_violation_uses_standard_phases(self, temp_project, state_store):
        """fix_violation uses standard phases unchanged."""
        task_id = "fix-001"
        state_store.create_task(
            task_type="fix_violation",
            goal="Fix violation",
            success_criteria=["Violation fixed"],
            task_id=task_id,
            context_data=get_required_context_for_task_type("fix_violation"),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="fix_violation",
        )

        context = builder.build(task_id)

        assert context.phase == "init", "Expected context.phase to equal 'init'"
        assert context.template_name == "fix_violation", "Expected context.template_name to equal 'fix_violation'"


class TestTemplateContextBuilderDifferentTaskTypes:
    """Tests that builder works with all registered task types."""

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
                '[project]\nname = "test"\n'
            )
            yield project

    @pytest.fixture
    def state_store(self, temp_project):
        return TaskStateStore(temp_project)

    @pytest.mark.parametrize("task_type", [
        "fix_violation",
        "implement_feature",
        "write_tests",
        "discovery",
        "bridge",
        "code_review",
        "refactor",
    ])
    def test_builder_works_for_task_type(self, temp_project, state_store, task_type):
        """Builder can build context for all registered task types."""
        task_id = f"{task_type}-001"
        state_store.create_task(
            task_type=task_type,
            goal=f"Test {task_type}",
            success_criteria=[f"{task_type} completed"],
            task_id=task_id,
            context_data=get_required_context_for_task_type(task_type),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type=task_type,
        )

        context = builder.build(task_id)

        assert isinstance(context, TemplateStepContext), "Expected isinstance() to be truthy"
        assert context.template_name == task_type, "Expected context.template_name to equal task_type"
        assert context.phase in builder.phases, "Expected context.phase in builder.phases"

    @pytest.mark.parametrize("task_type", [
        "fix_violation",
        "implement_feature",
        "write_tests",
        "discovery",
        "bridge",
        "code_review",
        "refactor",
    ])
    def test_builder_produces_valid_messages(self, temp_project, state_store, task_type):
        """Builder produces valid messages for all task types."""
        task_id = f"{task_type}-002"
        state_store.create_task(
            task_type=task_type,
            goal=f"Test {task_type}",
            success_criteria=[f"{task_type} completed"],
            task_id=task_id,
            context_data=get_required_context_for_task_type(task_type),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type=task_type,
        )

        messages = builder.build_messages(task_id)

        assert len(messages) == 2, "Expected len(messages) to equal 2"
        assert messages[0]["role"] == "system", "Expected messages[0]['role'] to equal 'system'"
        assert messages[1]["role"] == "user", "Expected messages[1]['role'] to equal 'user'"
        # User message should contain task info
        assert "Task" in messages[1]["content"] or "task" in messages[1]["content"], "Assertion failed"


class TestTemplateContextBuilderTokenTracking:
    """Tests for token breakdown tracking."""

    @pytest.fixture
    def temp_project(self):
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / ".agentforge").mkdir()
            (project / ".agentforge" / "tasks").mkdir()
            (project / "pyproject.toml").write_text('[project]\nname = "test"\n')
            yield project

    @pytest.fixture
    def state_store(self, temp_project):
        return TaskStateStore(temp_project)

    def test_get_token_breakdown(self, temp_project, state_store):
        """get_token_breakdown returns section token counts."""
        task_id = "token-test-001"
        state_store.create_task(
            task_type="fix_violation",
            goal="Test tokens",
            success_criteria=["Tokens counted"],
            task_id=task_id,
            context_data=get_required_context_for_task_type("fix_violation"),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="fix_violation",
        )

        breakdown = builder.get_token_breakdown(task_id)

        assert isinstance(breakdown, dict), "Expected isinstance() to be truthy"
        assert "system_prompt" in breakdown, "Expected 'system_prompt' in breakdown"
        assert breakdown["system_prompt"] > 0, "Expected breakdown['system_prompt'] > 0"

    def test_context_total_tokens(self, temp_project, state_store):
        """Context total_tokens is reasonable."""
        task_id = "token-test-002"
        state_store.create_task(
            task_type="fix_violation",
            goal="Test tokens",
            success_criteria=["Tokens validated"],
            task_id=task_id,
            context_data=get_required_context_for_task_type("fix_violation"),
        )

        builder = TemplateContextBuilder(
            project_path=temp_project,
            state_store=state_store,
            task_type="fix_violation",
        )

        context = builder.build(task_id)

        # Should be under 5000 tokens
        assert context.total_tokens < 5000, "Expected context.total_tokens < 5000"
        # But should be non-trivial
        assert context.total_tokens > 100, "Expected context.total_tokens > 100"
