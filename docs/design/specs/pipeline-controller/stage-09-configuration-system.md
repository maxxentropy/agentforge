# Pipeline Controller Specification - Stage 9: Configuration System

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1-8  
**Estimated Effort:** 3-4 days

---

## 1. Overview

### 1.1 Purpose

The Configuration System provides:

1. **Pipeline Templates**: Pre-defined stage configurations for different goals
2. **Agent Definitions**: Role-specific agent configurations (optional)
3. **Stage Configuration**: Per-stage settings and customization
4. **Global Settings**: Project-wide configuration

### 1.2 Configuration Hierarchy

```
.agentforge/
├── config/
│   ├── settings.yaml           # Global settings
│   └── stages/                  # Stage-specific config
│       ├── intake.yaml
│       ├── analyze.yaml
│       ├── spec.yaml
│       ├── red.yaml
│       ├── green.yaml
│       ├── refactor.yaml
│       └── deliver.yaml
│
├── pipelines/                   # Pipeline templates
│   ├── design.yaml             # Design-only pipeline
│   ├── implement.yaml          # Full implementation
│   ├── test.yaml               # Test-only pipeline
│   ├── fix.yaml                # Violation fix pipeline
│   └── custom/                 # Custom pipelines
│       └── review.yaml
│
└── agents/                      # Agent definitions (optional)
    ├── analyst.yaml
    ├── architect.yaml
    ├── developer.yaml
    └── tester.yaml
```

---

## 2. Pipeline Templates

### 2.1 Template Schema

```yaml
# .agentforge/pipelines/implement.yaml

# Pipeline metadata
name: implement
description: "Full implementation pipeline from request to delivery"
version: "1.0"

# Stage sequence
stages:
  - intake
  - clarify
  - analyze
  - spec
  - red
  - green
  - refactor
  - deliver

# Default configuration
defaults:
  supervised: false
  iteration_enabled: true
  max_iterations_per_stage: 3
  timeout_seconds: 3600

# Stage overrides
stage_config:
  clarify:
    max_iterations: 5
    auto_skip_if_no_questions: true
  
  spec:
    include_tests: true
    require_approval: true
  
  deliver:
    mode: commit
    auto_commit: false

# Exit conditions
exit_conditions:
  on_escalation: pause     # pause, fail, skip
  on_timeout: fail
  max_total_cost_usd: 10.0

# Hooks (optional)
hooks:
  on_stage_complete:
    - notify_slack
  on_pipeline_complete:
    - run_ci
```

### 2.2 Built-in Templates

#### Design Template
```yaml
# .agentforge/pipelines/design.yaml

name: design
description: "Design phase - produces specification without implementation"

stages:
  - intake
  - clarify
  - analyze
  - spec

defaults:
  supervised: true
  exit_after: spec

stage_config:
  spec:
    include_implementation_order: true
    include_test_cases: true
```

#### Test Template
```yaml
# .agentforge/pipelines/test.yaml

name: test
description: "Test generation from existing specification"

stages:
  - red

defaults:
  supervised: false

required_context:
  - spec  # Requires existing specification
```

#### Fix Template
```yaml
# .agentforge/pipelines/fix.yaml

name: fix
description: "Fix conformance violation"

stages:
  - analyze
  - green
  - refactor

defaults:
  supervised: false
  max_iterations_per_stage: 5

required_context:
  - violation  # Requires violation to fix
```

---

## 3. Stage Configuration

### 3.1 Stage Config Schema

```yaml
# .agentforge/config/stages/analyze.yaml

stage: analyze

# Execution settings
execution:
  timeout_seconds: 600
  max_tokens: 50000
  
# Tool configuration
tools:
  search_code:
    max_results: 30
    search_depth: 3
  read_file:
    max_lines: 500
  
# Analysis settings
analysis:
  max_files_to_read: 20
  include_test_files: true
  detect_patterns: true

# Output settings
output:
  save_intermediate: true
  include_reasoning: false
```

### 3.2 Standard Stage Configs

```yaml
# .agentforge/config/stages/spec.yaml

stage: spec

execution:
  timeout_seconds: 900
  
spec_generation:
  include_components: true
  include_interfaces: true
  include_test_cases: true
  include_data_models: true
  include_implementation_order: true
  include_acceptance_criteria: true
  
validation:
  require_components: true
  require_test_cases: true
  min_test_cases: 3
```

```yaml
# .agentforge/config/stages/green.yaml

stage: green

execution:
  max_iterations: 10
  test_timeout_seconds: 120
  
implementation:
  style: minimal  # minimal, comprehensive
  include_docstrings: true
  include_type_hints: true
  
testing:
  run_after_each_change: true
  fail_fast: false
```

---

## 4. Global Settings

### 4.1 Settings Schema

```yaml
# .agentforge/config/settings.yaml

# Version
version: "1.0"

# Project settings
project:
  name: "MyProject"
  language: "python"
  framework: "fastapi"
  
# LLM settings
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  max_tokens: 8000
  temperature: 0.7
  
# Pipeline defaults
pipeline:
  default_type: "implement"
  supervised_by_default: false
  auto_commit: false
  
# Cost controls
cost:
  max_per_pipeline_usd: 10.0
  max_daily_usd: 50.0
  warn_threshold_usd: 5.0
  
# Notifications
notifications:
  on_escalation: true
  on_complete: true
  slack_webhook: "${SLACK_WEBHOOK_URL}"
  
# Integrations
integrations:
  github:
    create_prs: true
    auto_merge: false
  jira:
    update_tickets: false
```

---

## 5. Configuration Loader

### 5.1 Implementation

```python
# src/agentforge/core/pipeline/config.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import yaml

logger = logging.getLogger(__name__)


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
            "stages": ["intake", "clarify", "analyze", "spec", "red", "green", "refactor", "deliver"],
            "defaults": {"supervised": False},
        },
        "design": {
            "stages": ["intake", "clarify", "analyze", "spec"],
            "defaults": {"supervised": True, "exit_after": "spec"},
        },
        "test": {
            "stages": ["red"],
            "required_context": ["spec"],
        },
        "fix": {
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
            with open(settings_file) as f:
                data = yaml.safe_load(f) or {}
            
            self._settings = GlobalSettings(
                project_name=data.get("project", {}).get("name", ""),
                language=data.get("project", {}).get("language", "python"),
                llm_model=data.get("llm", {}).get("model", "claude-sonnet-4-20250514"),
                max_cost_per_pipeline=data.get("cost", {}).get("max_per_pipeline_usd", 10.0),
                supervised_by_default=data.get("pipeline", {}).get("supervised_by_default", False),
                auto_commit=data.get("pipeline", {}).get("auto_commit", False),
            )
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
                **config
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
            description=f"Default {pipeline_type} pipeline",
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


class PipelineTemplateLoader:
    """
    Loader used by PipelineController.
    
    Wraps ConfigurationLoader to provide PipelineConfig objects.
    """
    
    def __init__(self, project_path: Path):
        self.loader = ConfigurationLoader(project_path)
    
    def load(self, pipeline_type: str) -> "PipelineConfig":
        """Load pipeline configuration."""
        from .controller import PipelineConfig
        
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
```

---

## 6. Environment Variable Support

```python
# Environment variable expansion in config

import os
import re

def expand_env_vars(value: str) -> str:
    """Expand ${VAR} patterns in config values."""
    pattern = r'\$\{([^}]+)\}'
    
    def replace(match):
        var_name = match.group(1)
        return os.environ.get(var_name, "")
    
    return re.sub(pattern, replace, value)


# Usage in settings.yaml:
# slack_webhook: "${SLACK_WEBHOOK_URL}"
# api_key: "${ANTHROPIC_API_KEY}"
```

---

## 7. Validation

```python
# src/agentforge/core/pipeline/config_validator.py

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Configuration validation error."""
    path: str
    message: str
    severity: str  # "error", "warning"


class ConfigValidator:
    """Validates pipeline configuration."""
    
    VALID_STAGES = [
        "intake", "clarify", "analyze", "spec",
        "red", "green", "refactor", "deliver"
    ]
    
    def validate_template(self, template: PipelineTemplate) -> List[ValidationError]:
        """Validate a pipeline template."""
        errors = []
        
        # Check stages are valid
        for stage in template.stages:
            if stage not in self.VALID_STAGES:
                errors.append(ValidationError(
                    path=f"stages.{stage}",
                    message=f"Unknown stage: {stage}",
                    severity="error"
                ))
        
        # Check stage order makes sense
        if "green" in template.stages and "red" not in template.stages:
            errors.append(ValidationError(
                path="stages",
                message="GREEN stage requires RED stage",
                severity="warning"
            ))
        
        # Check exit_after is in stages
        exit_after = template.defaults.get("exit_after")
        if exit_after and exit_after not in template.stages:
            errors.append(ValidationError(
                path="defaults.exit_after",
                message=f"exit_after stage '{exit_after}' not in stages",
                severity="error"
            ))
        
        return errors
```

---

## 8. CLI Commands for Config

```python
# cli/click_commands/config.py

@click.group("config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing config")
def config_init(force):
    """Initialize default configuration."""
    from agentforge.core.pipeline.config import ConfigurationLoader
    
    loader = ConfigurationLoader(Path.cwd())
    
    if loader.config_path.exists() and not force:
        click.echo("Configuration already exists. Use --force to overwrite.")
        return
    
    loader.create_default_config()
    click.echo("✅ Configuration initialized.")


@config_group.command("show")
@click.argument("section", required=False)
def config_show(section):
    """Show current configuration."""
    import yaml
    from agentforge.core.pipeline.config import ConfigurationLoader
    
    loader = ConfigurationLoader(Path.cwd())
    
    if section == "settings":
        settings = loader.load_settings()
        click.echo(yaml.dump(settings.__dict__, default_flow_style=False))
    elif section == "pipelines":
        for name in loader.list_available_pipelines():
            click.echo(f"  - {name}")
    else:
        click.echo("Available sections: settings, pipelines")


@config_group.command("validate")
def config_validate():
    """Validate configuration files."""
    from agentforge.core.pipeline.config import ConfigurationLoader
    from agentforge.core.pipeline.config_validator import ConfigValidator
    
    loader = ConfigurationLoader(Path.cwd())
    validator = ConfigValidator()
    
    all_errors = []
    
    for pipeline_type in loader.list_available_pipelines():
        template = loader.load_pipeline_template(pipeline_type)
        errors = validator.validate_template(template)
        
        for error in errors:
            all_errors.append((pipeline_type, error))
    
    if all_errors:
        click.echo("Configuration issues found:")
        for pipeline, error in all_errors:
            icon = "❌" if error.severity == "error" else "⚠️"
            click.echo(f"  {icon} [{pipeline}] {error.path}: {error.message}")
    else:
        click.echo("✅ Configuration is valid.")
```

---

## 9. Test Specification

```python
# tests/unit/pipeline/test_config.py

class TestConfigurationLoader:
    def test_loads_default_settings(self, tmp_path):
        """Loads default settings when no file exists."""
    
    def test_loads_settings_file(self, tmp_path):
        """Loads settings from YAML file."""
    
    def test_loads_pipeline_template(self, tmp_path):
        """Loads pipeline template from file."""
    
    def test_falls_back_to_default_template(self, tmp_path):
        """Uses default template when file missing."""


class TestConfigValidator:
    def test_validates_stage_names(self):
        """Rejects invalid stage names."""
    
    def test_warns_green_without_red(self):
        """Warns when GREEN without RED."""
```

---

## 10. Success Criteria

1. **Configuration Loading:**
   - [ ] Loads settings from YAML
   - [ ] Loads pipeline templates
   - [ ] Loads stage configs
   - [ ] Falls back to defaults

2. **Validation:**
   - [ ] Validates stage names
   - [ ] Validates stage order
   - [ ] Reports errors clearly

3. **CLI:**
   - [ ] `config init` works
   - [ ] `config show` works
   - [ ] `config validate` works

---

## 11. Summary: Full Pipeline Controller Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI LAYER                                       │
│   agentforge start | design | implement | status | approve | pipelines      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE CONTROLLER                                  │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ Configuration   │  │ State           │  │ Stage Executor              │ │
│  │ Loader          │  │ Store           │  │ Registry                    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ Escalation      │  │ Artifact        │  │ Pipeline                    │ │
│  │ Handler         │  │ Validator       │  │ Templates                   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STAGE EXECUTORS                                    │
│                                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────┐                           │
│  │ INTAKE  │→ │ CLARIFY │→ │ ANALYZE │→ │ SPEC │                           │
│  └─────────┘  └─────────┘  └─────────┘  └──────┘                           │
│                                              │                               │
│                                              ▼                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────┐                           │
│  │ DELIVER │← │REFACTOR │← │ GREEN   │← │ RED  │                           │
│  └─────────┘  └─────────┘  └─────────┘  └──────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MINIMAL CONTEXT ARCHITECTURE                            │
│                                                                              │
│  MinimalContextExecutor  │  Tool Handlers  │  LLM Abstraction               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*This completes the Pipeline Controller specification.*
