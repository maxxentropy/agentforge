# @spec_file: specs/pipeline-controller/implementation/phase-6-configuration.yaml
# @spec_id: pipeline-controller-phase6-v1
# @component_id: config-loader, config-stage-config, config-pipeline-template, config-global-settings

"""Unit tests for ConfigurationLoader and related classes."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


class TestStageConfig:
    """Tests for StageConfig dataclass."""

    def test_stage_config_defaults(self):
        """StageConfig has sensible defaults."""
        from agentforge.core.pipeline.config import StageConfig

        config = StageConfig(name="test")
        assert config.name == "test"
        assert config.enabled is True
        assert config.timeout_seconds == 600
        assert config.max_iterations == 3
        assert config.tools == {}
        assert config.custom == {}

    def test_stage_config_with_values(self):
        """StageConfig accepts custom values."""
        from agentforge.core.pipeline.config import StageConfig

        config = StageConfig(
            name="analyze",
            enabled=False,
            timeout_seconds=300,
            max_iterations=5,
            tools={"search": {"max_results": 10}},
            custom={"include_tests": True},
        )
        assert config.name == "analyze"
        assert config.enabled is False
        assert config.timeout_seconds == 300
        assert config.max_iterations == 5
        assert config.tools == {"search": {"max_results": 10}}
        assert config.custom == {"include_tests": True}


class TestPipelineTemplate:
    """Tests for PipelineTemplate dataclass."""

    def test_pipeline_template_defaults(self):
        """PipelineTemplate has sensible defaults."""
        from agentforge.core.pipeline.config import PipelineTemplate

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["intake", "spec"],
        )
        assert template.name == "test"
        assert template.description == "Test pipeline"
        assert template.stages == ["intake", "spec"]
        assert template.defaults == {}
        assert template.stage_config == {}
        assert template.exit_conditions == {}
        assert template.required_context == []

    def test_pipeline_template_with_all_fields(self):
        """PipelineTemplate accepts all optional fields."""
        from agentforge.core.pipeline.config import PipelineTemplate, StageConfig

        stage_config = {"spec": StageConfig(name="spec", timeout_seconds=900)}
        template = PipelineTemplate(
            name="implement",
            description="Full implementation",
            stages=["intake", "clarify", "analyze", "spec"],
            defaults={"supervised": True, "exit_after": "spec"},
            stage_config=stage_config,
            exit_conditions={"on_timeout": "fail"},
            required_context=["violation"],
        )
        assert template.defaults == {"supervised": True, "exit_after": "spec"}
        assert "spec" in template.stage_config
        assert template.stage_config["spec"].timeout_seconds == 900
        assert template.exit_conditions == {"on_timeout": "fail"}
        assert template.required_context == ["violation"]


class TestGlobalSettings:
    """Tests for GlobalSettings dataclass."""

    def test_global_settings_defaults(self):
        """GlobalSettings has sensible defaults."""
        from agentforge.core.pipeline.config import GlobalSettings

        settings = GlobalSettings()
        assert settings.project_name == ""
        assert settings.language == "python"
        assert settings.llm_model == "claude-sonnet-4-20250514"
        assert settings.max_cost_per_pipeline == 10.0
        assert settings.supervised_by_default is False
        assert settings.auto_commit is False

    def test_global_settings_with_values(self):
        """GlobalSettings accepts custom values."""
        from agentforge.core.pipeline.config import GlobalSettings

        settings = GlobalSettings(
            project_name="MyProject",
            language="typescript",
            llm_model="claude-opus-4-20250514",
            max_cost_per_pipeline=5.0,
            supervised_by_default=True,
            auto_commit=True,
        )
        assert settings.project_name == "MyProject"
        assert settings.language == "typescript"
        assert settings.llm_model == "claude-opus-4-20250514"
        assert settings.max_cost_per_pipeline == 5.0
        assert settings.supervised_by_default is True
        assert settings.auto_commit is True


class TestConfigurationLoader:
    """Tests for ConfigurationLoader class."""

    def test_loads_default_settings(self, tmp_path):
        """Loads default settings when no file exists."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        settings = loader.load_settings()

        assert settings.project_name == ""
        assert settings.language == "python"
        assert settings.supervised_by_default is False

    def test_loads_settings_file(self, tmp_path):
        """Loads settings from YAML file."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        # Create config directory and settings file
        config_dir = tmp_path / ".agentforge" / "config"
        config_dir.mkdir(parents=True)

        settings_content = {
            "project": {
                "name": "TestProject",
                "language": "go",
            },
            "llm": {
                "model": "claude-opus-4-20250514",
            },
            "pipeline": {
                "supervised_by_default": True,
                "auto_commit": True,
            },
            "cost": {
                "max_per_pipeline_usd": 20.0,
            },
        }
        (config_dir / "settings.yaml").write_text(yaml.dump(settings_content))

        loader = ConfigurationLoader(tmp_path)
        settings = loader.load_settings()

        assert settings.project_name == "TestProject"
        assert settings.language == "go"
        assert settings.llm_model == "claude-opus-4-20250514"
        assert settings.supervised_by_default is True
        assert settings.auto_commit is True
        assert settings.max_cost_per_pipeline == 20.0

    def test_settings_cached(self, tmp_path):
        """Settings are cached after first load."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        settings1 = loader.load_settings()
        settings2 = loader.load_settings()

        assert settings1 is settings2  # Same object

    def test_loads_pipeline_template(self, tmp_path):
        """Loads pipeline template from file."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        # Create pipelines directory and template file
        pipelines_dir = tmp_path / ".agentforge" / "pipelines"
        pipelines_dir.mkdir(parents=True)

        template_content = {
            "name": "custom",
            "description": "Custom pipeline template",
            "stages": ["intake", "analyze", "spec"],
            "defaults": {
                "supervised": True,
                "exit_after": "spec",
            },
            "stage_config": {
                "spec": {
                    "timeout_seconds": 1200,
                    "max_iterations": 5,
                }
            },
        }
        (pipelines_dir / "custom.yaml").write_text(yaml.dump(template_content))

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("custom")

        assert template.name == "custom"
        assert template.description == "Custom pipeline template"
        assert template.stages == ["intake", "analyze", "spec"]
        assert template.defaults == {"supervised": True, "exit_after": "spec"}
        assert "spec" in template.stage_config
        assert template.stage_config["spec"].timeout_seconds == 1200
        assert template.stage_config["spec"].max_iterations == 5

    def test_falls_back_to_default_template(self, tmp_path):
        """Uses default template when file missing."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("implement")

        assert template.name == "implement"
        assert "intake" in template.stages
        assert "deliver" in template.stages
        assert len(template.stages) == 8

    def test_template_cached(self, tmp_path):
        """Templates are cached after first load."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        template1 = loader.load_pipeline_template("implement")
        template2 = loader.load_pipeline_template("implement")

        assert template1 is template2  # Same object

    def test_unknown_template_raises_error(self, tmp_path):
        """Raises error for unknown template type."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)

        with pytest.raises(ValueError, match="Unknown pipeline type"):
            loader.load_pipeline_template("nonexistent")

    def test_loads_stage_config(self, tmp_path):
        """Loads stage config from file."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        # Create stages directory and config file
        stages_dir = tmp_path / ".agentforge" / "config" / "stages"
        stages_dir.mkdir(parents=True)

        stage_content = {
            "stage": "analyze",
            "enabled": True,
            "execution": {
                "timeout_seconds": 900,
                "max_iterations": 5,
            },
            "tools": {
                "search_code": {"max_results": 50},
            },
        }
        (stages_dir / "analyze.yaml").write_text(yaml.dump(stage_content))

        loader = ConfigurationLoader(tmp_path)
        config = loader.load_stage_config("analyze")

        assert config.name == "analyze"
        assert config.enabled is True
        assert config.timeout_seconds == 900
        assert config.max_iterations == 5
        assert config.tools == {"search_code": {"max_results": 50}}

    def test_stage_config_defaults(self, tmp_path):
        """Uses defaults when no file exists."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        config = loader.load_stage_config("intake")

        assert config.name == "intake"
        assert config.enabled is True
        assert config.timeout_seconds == 600
        assert config.max_iterations == 3

    def test_stage_config_cached(self, tmp_path):
        """Stage configs are cached after first load."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        config1 = loader.load_stage_config("intake")
        config2 = loader.load_stage_config("intake")

        assert config1 is config2  # Same object

    def test_list_available_pipelines(self, tmp_path):
        """Lists built-in and custom pipelines."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        # Create custom pipeline
        pipelines_dir = tmp_path / ".agentforge" / "pipelines"
        pipelines_dir.mkdir(parents=True)
        (pipelines_dir / "review.yaml").write_text(
            yaml.dump({"name": "review", "stages": ["analyze"]})
        )

        loader = ConfigurationLoader(tmp_path)
        pipelines = loader.list_available_pipelines()

        # Should have built-in pipelines
        assert "implement" in pipelines
        assert "design" in pipelines
        assert "test" in pipelines
        assert "fix" in pipelines
        # And custom pipeline
        assert "review" in pipelines
        # Should be sorted
        assert pipelines == sorted(pipelines)

    def test_create_default_config(self, tmp_path):
        """Creates default configuration files."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        loader.create_default_config()

        config_dir = tmp_path / ".agentforge" / "config"
        assert config_dir.exists()
        assert (config_dir / "settings.yaml").exists()
        assert (config_dir / "stages").exists()

        # Verify settings content
        settings = yaml.safe_load((config_dir / "settings.yaml").read_text())
        assert "project" in settings
        assert "llm" in settings
        assert "pipeline" in settings
        assert "cost" in settings


class TestBuiltInTemplates:
    """Tests for built-in pipeline templates."""

    def test_implement_template(self, tmp_path):
        """Implement template has all 8 stages."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("implement")

        expected_stages = [
            "intake", "clarify", "analyze", "spec",
            "red", "green", "refactor", "deliver"
        ]
        assert template.stages == expected_stages
        assert template.defaults.get("supervised") is False

    def test_design_template(self, tmp_path):
        """Design template exits at spec."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("design")

        assert "spec" in template.stages
        assert "red" not in template.stages
        assert "deliver" not in template.stages
        assert template.defaults.get("supervised") is True
        assert template.defaults.get("exit_after") == "spec"

    def test_test_template(self, tmp_path):
        """Test template requires spec context."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("test")

        assert template.stages == ["red"]
        assert "spec" in template.required_context

    def test_fix_template(self, tmp_path):
        """Fix template requires violation context."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("fix")

        assert "analyze" in template.stages
        assert "green" in template.stages
        assert "refactor" in template.stages
        assert "violation" in template.required_context


class TestExpandEnvVars:
    """Tests for environment variable expansion."""

    def test_expand_env_vars(self):
        """Expands ${VAR} patterns."""
        from agentforge.core.pipeline.config import expand_env_vars

        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = expand_env_vars("prefix_${TEST_VAR}_suffix")
            assert result == "prefix_test_value_suffix"

    def test_expand_multiple_vars(self):
        """Expands multiple ${VAR} patterns."""
        from agentforge.core.pipeline.config import expand_env_vars

        with patch.dict(os.environ, {"VAR1": "one", "VAR2": "two"}):
            result = expand_env_vars("${VAR1} and ${VAR2}")
            assert result == "one and two"

    def test_expand_missing_env_var(self):
        """Returns empty string for missing vars."""
        from agentforge.core.pipeline.config import expand_env_vars

        with patch.dict(os.environ, {}, clear=True):
            # Ensure the var doesn't exist
            os.environ.pop("NONEXISTENT_VAR", None)
            result = expand_env_vars("value_${NONEXISTENT_VAR}_end")
            assert result == "value__end"

    def test_expand_no_vars(self):
        """Returns original string if no vars present."""
        from agentforge.core.pipeline.config import expand_env_vars

        result = expand_env_vars("no variables here")
        assert result == "no variables here"


class TestPipelineTemplateLoader:
    """Tests for PipelineTemplateLoader class."""

    def test_template_loader_returns_pipeline_config(self, tmp_path):
        """Converts template to PipelineConfig."""
        from agentforge.core.pipeline.config import PipelineTemplateLoader, PipelineConfig

        loader = PipelineTemplateLoader(tmp_path)
        config = loader.load("implement")

        assert isinstance(config, PipelineConfig)
        assert config.pipeline_type == "implement"
        assert "intake" in config.stages
        assert "deliver" in config.stages

    def test_template_loader_merges_settings(self, tmp_path):
        """Merges template defaults with global settings."""
        from agentforge.core.pipeline.config import PipelineTemplateLoader

        # Create global settings
        config_dir = tmp_path / ".agentforge" / "config"
        config_dir.mkdir(parents=True)
        settings_content = {
            "pipeline": {
                "supervised_by_default": True,
            },
        }
        (config_dir / "settings.yaml").write_text(yaml.dump(settings_content))

        loader = PipelineTemplateLoader(tmp_path)
        config = loader.load("implement")

        # implement template has supervised: False, but global says True
        # Template takes precedence over global settings
        assert config.supervised is False  # Template default

    def test_template_loader_exit_after(self, tmp_path):
        """Loads exit_after from template."""
        from agentforge.core.pipeline.config import PipelineTemplateLoader

        loader = PipelineTemplateLoader(tmp_path)
        config = loader.load("design")

        assert config.exit_after == "spec"

    def test_template_loader_iteration_enabled(self, tmp_path):
        """Loads iteration_enabled from template."""
        from agentforge.core.pipeline.config import PipelineTemplateLoader

        loader = PipelineTemplateLoader(tmp_path)
        config = loader.load("implement")

        assert config.iteration_enabled is True

    def test_template_loader_custom_template(self, tmp_path):
        """Loads custom template."""
        from agentforge.core.pipeline.config import PipelineTemplateLoader

        # Create custom template
        pipelines_dir = tmp_path / ".agentforge" / "pipelines"
        pipelines_dir.mkdir(parents=True)
        template_content = {
            "name": "review",
            "description": "Code review pipeline",
            "stages": ["analyze", "spec"],
            "defaults": {
                "supervised": True,
                "exit_after": "spec",
                "timeout_seconds": 1800,
            },
        }
        (pipelines_dir / "review.yaml").write_text(yaml.dump(template_content))

        loader = PipelineTemplateLoader(tmp_path)
        config = loader.load("review")

        assert config.pipeline_type == "review"
        assert config.stages == ["analyze", "spec"]
        assert config.supervised is True
        assert config.exit_after == "spec"
        assert config.timeout_seconds == 1800
