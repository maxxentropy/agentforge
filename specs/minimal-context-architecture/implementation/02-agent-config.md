# Implementation Spec Part 2: Agent Configuration

## 3. Agent Configuration Implementation

### 3.1 File Structure

```
src/agentforge/core/context/
├── __init__.py
├── agent_config.py          # This section
├── fingerprint.py           # Next section
└── ...
```

### 3.2 Models

```python
# src/agentforge/core/context/agent_config.py

from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import yaml
import re


class AgentPreferences(BaseModel):
    """User communication preferences."""
    
    communication_style: str = Field(
        default="technical",
        description="Style: technical|conversational|concise"
    )
    risk_tolerance: str = Field(
        default="conservative",
        description="Risk level: conservative|moderate|aggressive"
    )
    verbosity: str = Field(
        default="normal",
        description="Output verbosity: minimal|normal|verbose"
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
        result = {
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
```

### 3.3 Loader Implementation

```python
# src/agentforge/core/context/agent_config.py (continued)

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
        content = path.read_text(encoding='utf-8')
        
        # Try to extract YAML frontmatter
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n?(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            yaml_content = match.group(1)
            markdown_body = match.group(2).strip()
            
            try:
                data = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {path}: {e}")
            
            # Add markdown body as instructions if not already set
            if markdown_body and 'instructions' not in data:
                data['instructions'] = markdown_body
            
            return data
        
        # No frontmatter - try parsing entire file as YAML
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return data
        except yaml.YAMLError:
            pass
        
        # Treat entire content as instructions
        return {'instructions': content.strip()}
    
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
```

### 3.4 Tests

```python
# tests/unit/context/test_agent_config.py

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import os

from agentforge.core.context.agent_config import (
    AgentConfig,
    AgentConfigLoader,
    AgentPreferences,
    TaskDefaults,
    ProjectConfig,
)


class TestAgentPreferences:
    """Tests for AgentPreferences model."""
    
    def test_default_values(self):
        prefs = AgentPreferences()
        assert prefs.communication_style == "technical"
        assert prefs.risk_tolerance == "conservative"
        assert prefs.verbosity == "normal"
    
    def test_valid_values(self):
        prefs = AgentPreferences(
            communication_style="concise",
            risk_tolerance="aggressive",
            verbosity="minimal",
        )
        assert prefs.communication_style == "concise"
    
    def test_invalid_style_raises(self):
        with pytest.raises(ValueError, match="Invalid communication_style"):
            AgentPreferences(communication_style="invalid")


class TestAgentConfig:
    """Tests for AgentConfig model."""
    
    def test_default_config(self):
        config = AgentConfig()
        assert config.preferences.communication_style == "technical"
        assert config.defaults.max_steps == 20
        assert config.constraints == []
    
    def test_to_context_dict(self):
        config = AgentConfig(
            constraints=["Test must pass", "No vendor changes"],
            patterns={"naming": "snake_case"},
        )
        ctx = config.to_context_dict()
        
        assert "preferences" in ctx
        assert "constraints" in ctx
        assert len(ctx["constraints"]) == 2


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
            
            # Monkeypatch home directory
            monkeypatch.setattr(
                AgentConfigLoader, 
                'GLOBAL_PATH', 
                global_dir / "AGENT.md"
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
        temp_global.write_text("""---
preferences:
  communication_style: concise
constraints:
  - "Global constraint"
---
Global instructions here.
""")
        
        loader = AgentConfigLoader(temp_project)
        config = loader.load()
        
        assert config.preferences.communication_style == "concise"
        assert "Global constraint" in config.constraints
        assert "Global instructions" in config.instructions
        assert str(temp_global) in config.sources
    
    def test_project_overrides_global(self, temp_project, temp_global):
        """Project config overrides global."""
        temp_global.write_text("""---
preferences:
  communication_style: verbose
  risk_tolerance: aggressive
---
""")
        
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text("""---
preferences:
  communication_style: concise
project:
  name: test-project
  language: python
---
""")
        
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
        temp_global.write_text("""---
constraints:
  - "Global: always test"
---
""")
        
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text("""---
constraints:
  - "Project: no vendor changes"
---
""")
        
        loader = AgentConfigLoader(temp_project)
        config = loader.load()
        
        assert len(config.constraints) == 2
        assert "Global: always test" in config.constraints
        assert "Project: no vendor changes" in config.constraints
    
    def test_task_type_override(self, temp_project):
        """Task-type specific config is applied."""
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text("""---
defaults:
  max_steps: 20
---
""")
        
        task_config = temp_project / ".agentforge" / "tasks" / "fix_violation.md"
        task_config.write_text("""---
defaults:
  max_steps: 30
constraints:
  - "Fix violations carefully"
---
""")
        
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
        project_config.write_text("""---
defaults:
  max_steps: 25
---
""")
        
        loader = AgentConfigLoader(temp_project)
        config1 = loader.load()
        config2 = loader.load()
        
        # Same object returned
        assert config1 is config2
        
        # Modify file
        project_config.write_text("""---
defaults:
  max_steps: 50
---
""")
        
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
        project_config.write_text("""
preferences:
  communication_style: concise
defaults:
  max_steps: 15
""")
        
        loader = AgentConfigLoader(temp_project)
        config = loader.load()
        
        assert config.preferences.communication_style == "concise"
        assert config.defaults.max_steps == 15
    
    def test_pure_markdown_becomes_instructions(self, temp_project):
        """Pure markdown file becomes instructions."""
        project_config = temp_project / ".agentforge" / "AGENT.md"
        project_config.write_text("""
# My Project Instructions

Always be careful with database operations.
Check for null values.
""")
        
        loader = AgentConfigLoader(temp_project)
        config = loader.load()
        
        assert "database operations" in config.instructions
        assert "null values" in config.instructions
```

### 3.5 Integration Points

```python
# Usage in executor

class MinimalContextExecutor:
    def __init__(
        self,
        project_path: Path,
        task_type: str = "fix_violation",
        llm_client: Optional[LLMClient] = None,
    ):
        self.project_path = Path(project_path)
        self.task_type = task_type
        
        # Load configuration
        self.config_loader = AgentConfigLoader(project_path)
        self.config = self.config_loader.load(task_type)
        
        # Apply config to execution
        self.max_steps = self.config.defaults.max_steps
        self.thinking_enabled = self.config.defaults.thinking_enabled
        self.thinking_budget = self.config.defaults.thinking_budget
        
        # Use factory (respects AGENTFORGE_LLM_MODE env var)
        self.llm_client = llm_client or LLMClientFactory.create()
```

---

**[Saved Part 2 - Agent Config Implementation]**

*Continue to Part 3: Fingerprint Implementation...*
