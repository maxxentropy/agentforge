# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: agent-config-tests

"""
Tests for agent configuration loader.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agentforge.core.context.agent_config import (
    AgentConfig,
    AgentConfigLoader,
    AgentPreferences,
    ProjectConfig,
    TaskDefaults,
)


class TestAgentPreferences:
    """Tests for AgentPreferences model."""

    def test_default_values(self):
        """AgentPreferences should have sensible defaults."""
        prefs = AgentPreferences()

        assert prefs.communication_style == "technical"
        assert prefs.risk_tolerance == "conservative"
        assert prefs.verbosity == "normal"

    def test_valid_values(self):
        """AgentPreferences should accept valid enum values."""
        prefs = AgentPreferences(
            communication_style="concise",
            risk_tolerance="aggressive",
            verbosity="minimal",
        )

        assert prefs.communication_style == "concise"
        assert prefs.risk_tolerance == "aggressive"
        assert prefs.verbosity == "minimal"

    def test_invalid_style_raises(self):
        """AgentPreferences should reject invalid communication_style."""
        with pytest.raises(ValueError, match="Invalid communication_style"):
            AgentPreferences(communication_style="invalid")

    def test_invalid_risk_raises(self):
        """AgentPreferences should reject invalid risk_tolerance."""
        with pytest.raises(ValueError, match="Invalid risk_tolerance"):
            AgentPreferences(risk_tolerance="invalid")

    def test_invalid_verbosity_raises(self):
        """AgentPreferences should reject invalid verbosity."""
        with pytest.raises(ValueError, match="Invalid verbosity"):
            AgentPreferences(verbosity="invalid")


class TestTaskDefaults:
    """Tests for TaskDefaults model."""

    def test_default_values(self):
        """TaskDefaults should have sensible defaults."""
        defaults = TaskDefaults()

        assert defaults.max_steps == 20
        assert defaults.require_tests is True
        assert defaults.auto_commit is False
        assert defaults.thinking_enabled is True
        assert defaults.thinking_budget == 8000

    def test_custom_values(self):
        """TaskDefaults should accept custom values."""
        defaults = TaskDefaults(
            max_steps=50,
            require_tests=False,
            thinking_budget=15000,
        )

        assert defaults.max_steps == 50
        assert defaults.require_tests is False
        assert defaults.thinking_budget == 15000

    def test_max_steps_bounds(self):
        """TaskDefaults should enforce max_steps bounds."""
        with pytest.raises(ValueError):
            TaskDefaults(max_steps=0)

        with pytest.raises(ValueError):
            TaskDefaults(max_steps=200)


class TestProjectConfig:
    """Tests for ProjectConfig model."""

    def test_required_fields(self):
        """ProjectConfig requires name and language."""
        config = ProjectConfig(name="test-project", language="python")

        assert config.name == "test-project"
        assert config.language == "python"
        assert config.test_command == "pytest"

    def test_optional_fields(self):
        """ProjectConfig has optional fields."""
        config = ProjectConfig(
            name="test",
            language="python",
            build_command="python -m build",
            lint_command="ruff check",
        )

        assert config.build_command == "python -m build"
        assert config.lint_command == "ruff check"


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_default_config(self):
        """AgentConfig should have sensible defaults."""
        config = AgentConfig()

        assert config.preferences.communication_style == "technical"
        assert config.defaults.max_steps == 20
        assert config.constraints == []
        assert config.project is None

    def test_with_constraints(self):
        """AgentConfig should store constraints."""
        config = AgentConfig(
            constraints=["Always run tests", "No vendor changes"],
        )

        assert len(config.constraints) == 2
        assert "Always run tests" in config.constraints

    def test_get_constraint_text(self):
        """get_constraint_text should format constraints."""
        config = AgentConfig(
            constraints=["Rule 1", "Rule 2"],
        )

        text = config.get_constraint_text()
        assert "- Rule 1" in text
        assert "- Rule 2" in text

    def test_to_context_dict(self):
        """to_context_dict should produce structured output."""
        config = AgentConfig(
            constraints=["Test must pass", "No vendor changes"],
            patterns={"naming": "snake_case"},
        )

        ctx = config.to_context_dict()

        assert "preferences" in ctx
        assert "defaults" in ctx
        assert "constraints" in ctx
        assert len(ctx["constraints"]) == 2
        assert "patterns" in ctx

    def test_to_context_dict_with_project(self):
        """to_context_dict should include project if set."""
        config = AgentConfig(
            project=ProjectConfig(name="my-project", language="python"),
        )

        ctx = config.to_context_dict()

        assert "project" in ctx
        assert ctx["project"]["name"] == "my-project"


class TestAgentConfigLoader:
    """Tests for AgentConfigLoader."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            (project_path / ".agentforge").mkdir()
            (project_path / ".agentforge" / "tasks").mkdir()
            yield project_path

    @pytest.fixture
    def temp_global(self, monkeypatch):
        """Create a temporary global config."""
        with TemporaryDirectory() as tmpdir:
            global_dir = Path(tmpdir) / ".agentforge"
            global_dir.mkdir()

            monkeypatch.setattr(
                AgentConfigLoader,
                "GLOBAL_PATH",
                global_dir / "AGENT.md",
            )

            yield global_dir / "AGENT.md"

    def test_load_empty_project(self, temp_project):
        """Load from project with no AGENT.md files."""
        loader = AgentConfigLoader(temp_project)
        config = loader.load()

        assert config.preferences.communication_style == "technical"
        assert config.sources == []

    def test_load_global_config(self, temp_project, temp_global):
        """Load global config only."""
        temp_global.write_text(
            """---
preferences:
  communication_style: concise
constraints:
  - "Global constraint"
---

Global instructions here.
"""
        )

        loader = AgentConfigLoader(temp_project)
        config = loader.load()

        assert config.preferences.communication_style == "concise"
        assert "Global constraint" in config.constraints
        assert "Global instructions" in config.instructions
        assert str(temp_global) in config.sources

    def test_project_overrides_global(self, temp_project, temp_global):
        """Project config overrides global."""
        temp_global.write_text(
            """---
preferences:
  communication_style: conversational
  risk_tolerance: aggressive
---
"""
        )

        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text(
            """---
preferences:
  communication_style: concise
project:
  name: test-project
  language: python
---
"""
        )

        loader = AgentConfigLoader(temp_project)
        config = loader.load()

        # Overridden
        assert config.preferences.communication_style == "concise"
        # Preserved from global
        assert config.preferences.risk_tolerance == "aggressive"
        # New from project
        assert config.project.name == "test-project"

    def test_constraints_accumulate(self, temp_project, temp_global):
        """Constraints from all levels accumulate."""
        temp_global.write_text(
            """---
constraints:
  - "Global: always test"
---
"""
        )

        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text(
            """---
constraints:
  - "Project: no vendor changes"
---
"""
        )

        loader = AgentConfigLoader(temp_project)
        config = loader.load()

        assert len(config.constraints) == 2
        assert "Global: always test" in config.constraints
        assert "Project: no vendor changes" in config.constraints

    def test_task_type_override(self, temp_project):
        """Task-type specific config is applied."""
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text(
            """---
defaults:
  max_steps: 20
---
"""
        )

        task_config = temp_project / ".agentforge" / "tasks" / "fix_violation.md"
        task_config.write_text(
            """---
defaults:
  max_steps: 30
constraints:
  - "Fix violations carefully"
---
"""
        )

        loader = AgentConfigLoader(temp_project)

        # Without task type
        config_default = loader.load()
        assert config_default.defaults.max_steps == 20

        # With task type
        loader.invalidate_cache()
        config_fix = loader.load(task_type="fix_violation")
        assert config_fix.defaults.max_steps == 30
        assert "Fix violations carefully" in config_fix.constraints

    def test_caching(self, temp_project):
        """Config is cached after first load."""
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text(
            """---
defaults:
  max_steps: 25
---
"""
        )

        loader = AgentConfigLoader(temp_project)
        config1 = loader.load()
        config2 = loader.load()

        # Same object returned
        assert config1 is config2

        # Modify file
        project_config.write_text(
            """---
defaults:
  max_steps: 50
---
"""
        )

        # Still cached
        config3 = loader.load()
        assert config3.defaults.max_steps == 25

        # Invalidate and reload
        loader.invalidate_cache()
        config4 = loader.load()
        assert config4.defaults.max_steps == 50

    def test_pure_yaml_file(self, temp_project):
        """Load pure YAML file without frontmatter."""
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text(
            """
preferences:
  communication_style: concise
defaults:
  max_steps: 15
"""
        )

        loader = AgentConfigLoader(temp_project)
        config = loader.load()

        assert config.preferences.communication_style == "concise"
        assert config.defaults.max_steps == 15

    def test_pure_markdown_becomes_instructions(self, temp_project):
        """Pure markdown file becomes instructions."""
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text(
            """
# My Project Instructions

Always be careful with database operations.
Check for null values.
"""
        )

        loader = AgentConfigLoader(temp_project)
        config = loader.load()

        assert "database operations" in config.instructions
        assert "null values" in config.instructions

    def test_get_cached_configs(self, temp_project):
        """get_cached_configs returns cached keys."""
        loader = AgentConfigLoader(temp_project)
        loader.load()
        loader.load(task_type="fix_violation")

        cached = loader.get_cached_configs()
        assert len(cached) == 2
