# @spec_file: specs/pipeline-controller/implementation/phase-6-configuration.yaml
# @spec_id: pipeline-controller-phase6-v1
# @component_id: config-loader, config-stage-config, config-pipeline-template, config-global-settings, config-env-expand, config-template-loader
# @test_path: tests/unit/pipeline/test_config.py

"""
Pipeline Configuration System
==============================

Provides flexible configuration for pipeline operations:
- ConfigurationLoader: Loads settings, templates, and stage configs
- PipelineTemplate: Pre-defined stage sequences
- StageConfig: Per-stage settings
- GlobalSettings: Project-wide configuration
"""

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class StageConfig:
    """Configuration for a single stage."""

    name: str
    enabled: bool = True
    timeout_seconds: int = 600
    max_iterations: int = 3
    tools: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineTemplate:
    """Pipeline template definition."""

    name: str
    description: str
    stages: List[str]
    defaults: Dict[str, Any] = field(default_factory=dict)
    stage_config: Dict[str, StageConfig] = field(default_factory=dict)
    exit_conditions: Dict[str, Any] = field(default_factory=dict)
    required_context: List[str] = field(default_factory=list)


@dataclass
class GlobalSettings:
    """Global project settings."""

    project_name: str = ""
    language: str = "python"
    llm_model: str = "claude-sonnet-4-20250514"
    max_cost_per_pipeline: float = 10.0
    supervised_by_default: bool = False
    auto_commit: bool = False


@dataclass
class PipelineConfig:
    """
    Configuration for pipeline execution.

    Used by PipelineController to configure pipeline behavior.
    """

    pipeline_type: str
    stages: List[str]
    exit_after: Optional[str] = None
    supervised: bool = False
    iteration_enabled: bool = True
    max_iterations_per_stage: int = 3
    timeout_seconds: int = 3600


# =============================================================================
# Environment Variable Support
# =============================================================================


def expand_env_vars(value: str) -> str:
    """
    Expand ${VAR} patterns in config values.

    Args:
        value: String that may contain ${VAR} patterns

    Returns:
        String with environment variables expanded
    """
    pattern = r"\$\{([^}]+)\}"

    def replace(match):
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return re.sub(pattern, replace, value)


# =============================================================================
# Configuration Loader
# =============================================================================


class ConfigurationLoader:
    """
    Loads and manages pipeline configuration.

    Configuration sources (in priority order):
    1. Command-line overrides
    2. Environment variables
    3. .agentforge/config/ files
    4. Built-in defaults
    """

    DEFAULT_PIPELINES = {
        "implement": {
            "description": "Full implementation pipeline from request to delivery",
            "stages": [
                "intake",
                "clarify",
                "analyze",
                "spec",
                "red",
                "green",
                "refactor",
                "deliver",
            ],
            "defaults": {"supervised": False, "iteration_enabled": True},
        },
        "design": {
            "description": "Design phase - produces specification without implementation",
            "stages": ["intake", "clarify", "analyze", "spec"],
            "defaults": {"supervised": True, "exit_after": "spec"},
        },
        "test": {
            "description": "Test generation from existing specification",
            "stages": ["red"],
            "required_context": ["spec"],
        },
        "fix": {
            "description": "Fix conformance violation",
            "stages": ["analyze", "green", "refactor"],
            "required_context": ["violation"],
        },
    }

    def __init__(self, project_path: Path):
        """Initialize configuration loader."""
        self.project_path = Path(project_path)
        self.config_path = self.project_path / ".agentforge" / "config"
        self.pipelines_path = self.project_path / ".agentforge" / "pipelines"

        self._settings: Optional[GlobalSettings] = None
        self._templates: Dict[str, PipelineTemplate] = {}
        self._stage_configs: Dict[str, StageConfig] = {}

    def load_settings(self) -> GlobalSettings:
        """Load global settings."""
        if self._settings:
            return self._settings

        settings_file = self.config_path / "settings.yaml"

        if settings_file.exists():
            try:
                with open(settings_file) as f:
                    data = yaml.safe_load(f) or {}

                self._settings = GlobalSettings(
                    project_name=data.get("project", {}).get("name", ""),
                    language=data.get("project", {}).get("language", "python"),
                    llm_model=data.get("llm", {}).get(
                        "model", "claude-sonnet-4-20250514"
                    ),
                    max_cost_per_pipeline=data.get("cost", {}).get(
                        "max_per_pipeline_usd", 10.0
                    ),
                    supervised_by_default=data.get("pipeline", {}).get(
                        "supervised_by_default", False
                    ),
                    auto_commit=data.get("pipeline", {}).get("auto_commit", False),
                )
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse settings.yaml: {e}")
                self._settings = GlobalSettings()
        else:
            self._settings = GlobalSettings()

        return self._settings

    def load_pipeline_template(self, pipeline_type: str) -> PipelineTemplate:
        """Load pipeline template by type."""
        if pipeline_type in self._templates:
            return self._templates[pipeline_type]

        # Try to load from file
        template_file = self.pipelines_path / f"{pipeline_type}.yaml"

        if template_file.exists():
            template = self._load_template_file(template_file)
        elif pipeline_type in self.DEFAULT_PIPELINES:
            template = self._create_default_template(pipeline_type)
        else:
            raise ValueError(f"Unknown pipeline type: {pipeline_type}")

        self._templates[pipeline_type] = template
        return template

    def _load_template_file(self, path: Path) -> PipelineTemplate:
        """Load template from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        # Load stage configs
        stage_configs = {}
        for stage_name, config in data.get("stage_config", {}).items():
            stage_configs[stage_name] = StageConfig(
                name=stage_name,
                enabled=config.get("enabled", True),
                timeout_seconds=config.get("timeout_seconds", 600),
                max_iterations=config.get("max_iterations", 3),
                tools=config.get("tools", {}),
                custom=config,
            )

        return PipelineTemplate(
            name=data.get("name", path.stem),
            description=data.get("description", ""),
            stages=data.get("stages", []),
            defaults=data.get("defaults", {}),
            stage_config=stage_configs,
            exit_conditions=data.get("exit_conditions", {}),
            required_context=data.get("required_context", []),
        )

    def _create_default_template(self, pipeline_type: str) -> PipelineTemplate:
        """Create template from built-in defaults."""
        default = self.DEFAULT_PIPELINES[pipeline_type]

        return PipelineTemplate(
            name=pipeline_type,
            description=default.get("description", f"Default {pipeline_type} pipeline"),
            stages=default.get("stages", []),
            defaults=default.get("defaults", {}),
            required_context=default.get("required_context", []),
        )

    def load_stage_config(self, stage_name: str) -> StageConfig:
        """Load configuration for a specific stage."""
        if stage_name in self._stage_configs:
            return self._stage_configs[stage_name]

        config_file = self.config_path / "stages" / f"{stage_name}.yaml"

        if config_file.exists():
            with open(config_file) as f:
                data = yaml.safe_load(f) or {}

            config = StageConfig(
                name=stage_name,
                enabled=data.get("enabled", True),
                timeout_seconds=data.get("execution", {}).get("timeout_seconds", 600),
                max_iterations=data.get("execution", {}).get("max_iterations", 3),
                tools=data.get("tools", {}),
                custom=data,
            )
        else:
            config = StageConfig(name=stage_name)

        self._stage_configs[stage_name] = config
        return config

    def list_available_pipelines(self) -> List[str]:
        """List all available pipeline types."""
        pipelines = set(self.DEFAULT_PIPELINES.keys())

        if self.pipelines_path.exists():
            for f in self.pipelines_path.glob("*.yaml"):
                pipelines.add(f.stem)

        return sorted(pipelines)

    def create_default_config(self) -> None:
        """Create default configuration files."""
        # Create directories
        self.config_path.mkdir(parents=True, exist_ok=True)
        (self.config_path / "stages").mkdir(exist_ok=True)
        self.pipelines_path.mkdir(parents=True, exist_ok=True)

        # Create settings.yaml
        settings_content = """# AgentForge Configuration
version: "1.0"

project:
  name: ""
  language: "python"

llm:
  model: "claude-sonnet-4-20250514"
  max_tokens: 8000

pipeline:
  default_type: "implement"
  supervised_by_default: false
  auto_commit: false

cost:
  max_per_pipeline_usd: 10.0
  max_daily_usd: 50.0
"""
        (self.config_path / "settings.yaml").write_text(settings_content)

        logger.info(f"Created default configuration at {self.config_path}")


# =============================================================================
# Pipeline Template Loader (for PipelineController)
# =============================================================================


class PipelineTemplateLoader:
    """
    Loader used by PipelineController.

    Wraps ConfigurationLoader to provide PipelineConfig objects.
    """

    def __init__(self, project_path: Path):
        """Initialize with project path."""
        self.loader = ConfigurationLoader(project_path)

    def load(self, pipeline_type: str) -> PipelineConfig:
        """
        Load pipeline configuration.

        Args:
            pipeline_type: Type of pipeline to load

        Returns:
            PipelineConfig ready for use by PipelineController
        """
        template = self.loader.load_pipeline_template(pipeline_type)
        settings = self.loader.load_settings()

        return PipelineConfig(
            pipeline_type=pipeline_type,
            stages=template.stages,
            exit_after=template.defaults.get("exit_after"),
            supervised=template.defaults.get("supervised", settings.supervised_by_default),
            iteration_enabled=template.defaults.get("iteration_enabled", True),
            max_iterations_per_stage=template.defaults.get("max_iterations_per_stage", 3),
            timeout_seconds=template.defaults.get("timeout_seconds", 3600),
        )
