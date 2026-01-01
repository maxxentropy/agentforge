# @spec_file: specs/minimal-context-architecture-specs/specs/minimal-context-architecture/02-agent-config.yaml
# @spec_id: agent-config-v1
# @component_id: agent-config-loader
# @test_path: tests/unit/context/test_agent_config.py

"""
Agent Configuration Loader
==========================

Loads and merges AGENT.md configuration from a hierarchy:
1. ~/.agentforge/AGENT.md (global user preferences)
2. {project}/.agentforge/AGENT.md (project-specific)
3. {project}/.agentforge/tasks/{task_type}.md (task-specific)

File format: Markdown with YAML frontmatter
```markdown
---
preferences:
  communication_style: concise
constraints:
  - "Always run tests"
---

# Additional Instructions

Free-form markdown becomes the `instructions` field.
```

Usage:
    ```python
    loader = AgentConfigLoader(project_path)
    config = loader.load(task_type="fix_violation")

    # Access configuration
    print(config.defaults.max_steps)
    print(config.preferences.communication_style)
    print(config.constraints)
    ```
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class AgentPreferences(BaseModel):
    """User communication preferences."""

    communication_style: str = Field(
        default="technical",
        description="Style: technical|conversational|concise",
    )
    risk_tolerance: str = Field(
        default="conservative",
        description="Risk level: conservative|moderate|aggressive",
    )
    verbosity: str = Field(
        default="normal",
        description="Output verbosity: minimal|normal|verbose",
    )

    def model_post_init(self, __context) -> None:
        """Validate enum-like fields."""
        valid_styles = {"technical", "conversational", "concise"}
        valid_risks = {"conservative", "moderate", "aggressive"}
        valid_verbosity = {"minimal", "normal", "verbose"}

        if self.communication_style not in valid_styles:
            raise ValueError(f"Invalid communication_style: {self.communication_style}")
        if self.risk_tolerance not in valid_risks:
            raise ValueError(f"Invalid risk_tolerance: {self.risk_tolerance}")
        if self.verbosity not in valid_verbosity:
            raise ValueError(f"Invalid verbosity: {self.verbosity}")


class TaskDefaults(BaseModel):
    """Default values for task execution."""

    max_steps: int = Field(default=20, ge=1, le=100)
    require_tests: bool = True
    auto_commit: bool = False
    thinking_enabled: bool = True
    thinking_budget: int = Field(default=8000, ge=1000, le=50000)
    token_budget: int = Field(default=4000, ge=1000, le=100000)


class ProjectConfig(BaseModel):
    """Project-specific configuration."""

    name: str
    language: str
    test_command: str = "pytest"
    build_command: Optional[str] = None
    lint_command: Optional[str] = None
    source_root: str = "src"
    test_root: str = "tests"


class AgentConfig(BaseModel):
    """
    Complete agent configuration merged from AGENT.md chain.

    Hierarchy (later overrides earlier):
    1. Built-in defaults
    2. ~/.agentforge/AGENT.md (global)
    3. {project}/.agentforge/AGENT.md (project)
    4. {project}/.agentforge/tasks/{task_type}.md (task-specific)
    """

    preferences: AgentPreferences = Field(default_factory=AgentPreferences)
    defaults: TaskDefaults = Field(default_factory=TaskDefaults)
    project: Optional[ProjectConfig] = None
    patterns: Dict[str, str] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    instructions: Optional[str] = None

    # Metadata
    sources: List[str] = Field(default_factory=list)
    loaded_at: datetime = Field(default_factory=datetime.utcnow)

    def get_constraint_text(self) -> str:
        """Get constraints as formatted text for context."""
        if not self.constraints:
            return ""
        return "\n".join(f"- {c}" for c in self.constraints)

    def get_instructions_text(self) -> str:
        """Get instructions for context."""
        return self.instructions or ""

    def to_context_dict(self) -> Dict[str, Any]:
        """Convert to dict for context inclusion."""
        result: Dict[str, Any] = {
            "preferences": {
                "style": self.preferences.communication_style,
                "risk": self.preferences.risk_tolerance,
            },
            "defaults": {
                "max_steps": self.defaults.max_steps,
                "require_tests": self.defaults.require_tests,
            },
        }

        if self.project:
            result["project"] = {
                "name": self.project.name,
                "language": self.project.language,
            }

        if self.patterns:
            result["patterns"] = self.patterns

        if self.constraints:
            result["constraints"] = self.constraints

        return result


class AgentConfigLoader:
    """
    Loads and merges AGENT.md configuration from hierarchy.

    File format: Markdown with YAML frontmatter
    ```markdown
    ---
    preferences:
      communication_style: concise
    constraints:
      - "Always run tests"
    ---

    # Additional Instructions

    Free-form markdown becomes the `instructions` field.
    ```
    """

    GLOBAL_PATH = Path.home() / ".agentforge" / "AGENT.md"
    PROJECT_SUBPATH = ".agentforge/AGENT.md"
    TASK_SUBPATH_TEMPLATE = ".agentforge/tasks/{task_type}.md"

    def __init__(self, project_path: Path):
        """
        Initialize loader for a project.

        Args:
            project_path: Root path of the project
        """
        self.project_path = Path(project_path).resolve()
        self._cache: Dict[str, AgentConfig] = {}

    def load(self, task_type: Optional[str] = None) -> AgentConfig:
        """
        Load merged configuration for a task.

        Args:
            task_type: Optional task type for task-specific overrides

        Returns:
            Merged AgentConfig
        """
        cache_key = f"{self.project_path}:{task_type or 'default'}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        config = AgentConfig()

        # Layer 1: Global user config
        if self.GLOBAL_PATH.exists():
            global_data = self._load_file(self.GLOBAL_PATH)
            config = self._merge(config, global_data)
            config.sources.append(str(self.GLOBAL_PATH))

        # Layer 2: Project config
        project_config_path = self.project_path / self.PROJECT_SUBPATH
        if project_config_path.exists():
            project_data = self._load_file(project_config_path)
            config = self._merge(config, project_data)
            config.sources.append(str(project_config_path))

        # Layer 3: Task-type config
        if task_type:
            task_path = self.project_path / self.TASK_SUBPATH_TEMPLATE.format(
                task_type=task_type
            )
            if task_path.exists():
                task_data = self._load_file(task_path)
                config = self._merge(config, task_data)
                config.sources.append(str(task_path))

        # Update metadata
        config.loaded_at = datetime.utcnow()

        # Cache and return
        self._cache[cache_key] = config
        return config

    def _load_file(self, path: Path) -> Dict[str, Any]:
        """
        Load configuration from a markdown file with YAML frontmatter.

        Supports:
        - YAML frontmatter between --- markers
        - Markdown body becomes `instructions` field
        - Pure YAML files (no frontmatter)
        """
        content = path.read_text(encoding="utf-8")

        # Try to extract YAML frontmatter
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n?(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            yaml_content = match.group(1)
            markdown_body = match.group(2).strip()

            try:
                data = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {path}: {e}")

            # Add markdown body as instructions if not already set
            if markdown_body and "instructions" not in data:
                data["instructions"] = markdown_body

            return data

        # No frontmatter - try parsing entire file as YAML
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return data
        except yaml.YAMLError:
            pass

        # Treat entire content as instructions
        return {"instructions": content.strip()}

    def _merge(self, base: AgentConfig, override: Dict[str, Any]) -> AgentConfig:
        """
        Merge override dict into base config.

        Rules:
        - Scalars: override replaces
        - Dicts: deep merge (override wins per key)
        - Lists: concatenate (accumulate)
        """
        base_dict = base.model_dump()

        for key, value in override.items():
            if key not in base_dict:
                base_dict[key] = value
                continue

            base_value = base_dict[key]

            if isinstance(base_value, dict) and isinstance(value, dict):
                # Deep merge dicts
                base_dict[key] = self._deep_merge_dict(base_value, value)
            elif isinstance(base_value, list) and isinstance(value, list):
                # Concatenate lists (constraints accumulate)
                base_dict[key] = base_value + value
            else:
                # Override scalar
                base_dict[key] = value

        return AgentConfig(**base_dict)

    def _deep_merge_dict(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dicts."""
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        return result

    def invalidate_cache(self, task_type: Optional[str] = None) -> None:
        """
        Clear cached configuration.

        Args:
            task_type: Specific task type to invalidate, or None for all
        """
        if task_type:
            cache_key = f"{self.project_path}:{task_type}"
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()

    def get_cached_configs(self) -> List[str]:
        """Get list of cached config keys."""
        return list(self._cache.keys())
