# Implementation Spec Part 4: Context Templates

## 5. Context Template Implementation

### 5.1 Purpose

Task-type specific templates defining:
- What context sections are needed per phase
- Token budgets per section
- Compaction priorities
- System prompt content

### 5.2 Base Models

```python
# src/agentforge/core/context/templates/models.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CompactionLevel(str, Enum):
    """How aggressively a section can be compacted."""
    NEVER = "never"          # Never compact (fingerprint, task)
    NORMAL = "normal"        # Compact under pressure
    AGGRESSIVE = "aggressive"  # Compact first
    TRUNCATE_MIDDLE = "truncate_middle"  # Special: keep start+end


class ContextSection(BaseModel):
    """Definition of a single context section."""
    
    name: str = Field(description="Section name in context dict")
    source: str = Field(description="Where to get the data")
    max_tokens: int = Field(description="Token budget for this section")
    compaction: CompactionLevel = CompactionLevel.NORMAL
    required: bool = Field(default=False, description="Error if missing")
    
    def __hash__(self):
        return hash(self.name)


class TierDefinition(BaseModel):
    """Definition of a context tier."""
    
    name: str
    max_tokens: int
    sections: List[ContextSection]
    
    def get_section(self, name: str) -> Optional[ContextSection]:
        """Get a section by name."""
        for section in self.sections:
            if section.name == name:
                return section
        return None


class PhaseContextDef(BaseModel):
    """Context definition for a specific phase."""
    
    phase: str
    tier2: TierDefinition
    system_prompt_additions: Optional[str] = None
```

### 5.3 Base Template

```python
# src/agentforge/core/context/templates/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from .models import (
    ContextSection,
    TierDefinition,
    PhaseContextDef,
    CompactionLevel,
)
from ..fingerprint import ProjectFingerprint
from ...harness.minimal_context.context_models import (
    TaskSpec, StateSpec, ActionsSpec, AgentContext, Understanding
)


class BaseContextTemplate(ABC):
    """
    Abstract base class for context templates.
    
    Defines the tiered context structure:
    - Tier 1: Always present (~800 tokens)
    - Tier 2: Phase-dependent (~1500 tokens)
    - Tier 3: On-demand (~1000 tokens)
    """
    
    # Tier 1: Always present (same for all task types)
    TIER1_ALWAYS = TierDefinition(
        name="always",
        max_tokens=800,
        sections=[
            ContextSection(
                name="fingerprint",
                source="project_fingerprint",
                max_tokens=500,
                compaction=CompactionLevel.NEVER,
                required=True,
            ),
            ContextSection(
                name="task",
                source="task_definition",
                max_tokens=200,
                compaction=CompactionLevel.NEVER,
                required=True,
            ),
            ContextSection(
                name="phase",
                source="phase_machine",
                max_tokens=100,
                compaction=CompactionLevel.NEVER,
                required=True,
            ),
        ],
    )
    
    # Tier 3: On-demand (same for all task types)
    TIER3_ON_DEMAND = TierDefinition(
        name="on_demand",
        max_tokens=1000,
        sections=[
            ContextSection(
                name="understanding",
                source="fact_store",
                max_tokens=500,
                compaction=CompactionLevel.AGGRESSIVE,
            ),
            ContextSection(
                name="recent",
                source="recent_actions",
                max_tokens=300,
                compaction=CompactionLevel.AGGRESSIVE,
            ),
            ContextSection(
                name="additional",
                source="on_demand_fetch",
                max_tokens=200,
                compaction=CompactionLevel.AGGRESSIVE,
            ),
        ],
    )
    
    # Base system prompt (~150 tokens, cacheable)
    BASE_SYSTEM_PROMPT = """You are an expert software development agent.

RULES:
1. One action per response
2. Use semantic tools when available
3. Verify changes before completion

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: brief explanation
```"""
    
    @property
    @abstractmethod
    def task_type(self) -> str:
        """Return the task type this template handles."""
        pass
    
    @property
    @abstractmethod
    def phases(self) -> List[str]:
        """Return the valid phases for this task type."""
        pass
    
    @abstractmethod
    def get_tier2_for_phase(self, phase: str) -> TierDefinition:
        """Get tier 2 definition for a specific phase."""
        pass
    
    def get_system_prompt(self, phase: Optional[str] = None) -> str:
        """
        Get the system prompt for this task type.
        
        Override to add task-specific instructions.
        """
        return self.BASE_SYSTEM_PROMPT
    
    def get_all_tiers(self, phase: str) -> List[TierDefinition]:
        """Get all tier definitions for a phase."""
        return [
            self.TIER1_ALWAYS,
            self.get_tier2_for_phase(phase),
            self.TIER3_ON_DEMAND,
        ]
    
    def get_total_budget(self) -> int:
        """Get total token budget across all tiers."""
        return (
            self.TIER1_ALWAYS.max_tokens +
            max(self.get_tier2_for_phase(p).max_tokens for p in self.phases) +
            self.TIER3_ON_DEMAND.max_tokens
        )
    
    def build_context_dict(
        self,
        fingerprint: ProjectFingerprint,
        task_spec: TaskSpec,
        state_spec: StateSpec,
        phase: str,
        precomputed: Dict[str, Any],
        domain_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the context dictionary from components.
        
        This is the main method for context construction.
        """
        context = {}
        
        # Tier 1: Always present
        context["fingerprint"] = fingerprint.to_context_yaml()
        context["task"] = {
            "id": task_spec.task_id,
            "type": task_spec.task_type,
            "goal": task_spec.goal,
            "success_criteria": task_spec.success_criteria,
        }
        context["phase"] = {
            "current": phase,
            "step": state_spec.current_step,
            "max_steps": state_spec.phase.max_steps if state_spec.phase else 20,
        }
        
        # Tier 2: Phase-specific
        tier2 = self.get_tier2_for_phase(phase)
        for section in tier2.sections:
            value = self._get_section_value(
                section,
                precomputed=precomputed,
                domain_context=domain_context,
                state_spec=state_spec,
            )
            if value is not None:
                context[section.name] = self._truncate_to_budget(
                    value, section.max_tokens
                )
            elif section.required:
                raise ValueError(f"Required section missing: {section.name}")
        
        # Tier 3: On-demand
        for section in self.TIER3_ON_DEMAND.sections:
            value = self._get_section_value(
                section,
                precomputed=precomputed,
                domain_context=domain_context,
                state_spec=state_spec,
            )
            if value is not None:
                context[section.name] = self._truncate_to_budget(
                    value, section.max_tokens
                )
        
        return context
    
    def _get_section_value(
        self,
        section: ContextSection,
        precomputed: Dict[str, Any],
        domain_context: Dict[str, Any],
        state_spec: StateSpec,
    ) -> Optional[Any]:
        """Get the value for a section based on its source."""
        
        # Check precomputed first
        if section.name in precomputed:
            return precomputed[section.name]
        
        # Check domain_context
        if section.name in domain_context:
            return domain_context[section.name]
        
        # Special handling for specific sources
        if section.source == "fact_store":
            facts = state_spec.understanding.get_high_confidence(0.7)
            if facts:
                return [
                    {"statement": f.statement, "confidence": f.confidence}
                    for f in facts[:10]
                ]
        
        elif section.source == "recent_actions":
            if state_spec.recent_actions:
                return [
                    {
                        "action": a.action,
                        "result": a.result.value if a.result else "unknown",
                        "summary": a.summary,
                    }
                    for a in state_spec.recent_actions[-3:]
                ]
        
        return None
    
    def _truncate_to_budget(self, value: Any, max_tokens: int) -> Any:
        """Truncate a value to fit within token budget."""
        if isinstance(value, str):
            max_chars = max_tokens * 4
            if len(value) > max_chars:
                return value[:max_chars] + "... (truncated)"
        elif isinstance(value, list):
            # Estimate tokens per item
            if len(value) == 0:
                return value
            import yaml
            sample = yaml.dump(value[0], default_flow_style=False)
            tokens_per_item = len(sample) // 4
            max_items = max(1, max_tokens // max(1, tokens_per_item))
            return value[:max_items]
        
        return value
```

### 5.4 Fix Violation Template

```python
# src/agentforge/core/context/templates/fix_violation.py

from typing import List
from .base import BaseContextTemplate
from .models import TierDefinition, ContextSection, CompactionLevel


class FixViolationTemplate(BaseContextTemplate):
    """Context template for fix_violation tasks."""
    
    @property
    def task_type(self) -> str:
        return "fix_violation"
    
    @property
    def phases(self) -> List[str]:
        return ["init", "analyze", "implement", "verify"]
    
    def get_tier2_for_phase(self, phase: str) -> TierDefinition:
        """Get phase-specific tier 2 definition."""
        
        definitions = {
            "init": TierDefinition(
                name="init",
                max_tokens=1000,
                sections=[
                    ContextSection(
                        name="violation",
                        source="domain_context",
                        max_tokens=400,
                        required=True,
                    ),
                    ContextSection(
                        name="overview",
                        source="precomputed",
                        max_tokens=600,
                    ),
                ],
            ),
            
            "analyze": TierDefinition(
                name="analyze",
                max_tokens=1500,
                sections=[
                    ContextSection(
                        name="violation",
                        source="domain_context",
                        max_tokens=300,
                        required=True,
                    ),
                    ContextSection(
                        name="check_definition",
                        source="precomputed",
                        max_tokens=200,
                    ),
                    ContextSection(
                        name="file_overview",
                        source="precomputed",
                        max_tokens=500,
                    ),
                    ContextSection(
                        name="related_patterns",
                        source="precomputed",
                        max_tokens=500,
                    ),
                ],
            ),
            
            "implement": TierDefinition(
                name="implement",
                max_tokens=2000,
                sections=[
                    ContextSection(
                        name="target_source",
                        source="precomputed",
                        max_tokens=1000,
                        compaction=CompactionLevel.TRUNCATE_MIDDLE,
                        required=True,
                    ),
                    ContextSection(
                        name="extraction_suggestions",
                        source="precomputed",
                        max_tokens=500,
                        required=True,
                    ),
                    ContextSection(
                        name="action_hints",
                        source="precomputed",
                        max_tokens=200,
                    ),
                    ContextSection(
                        name="similar_fixes",
                        source="precomputed",
                        max_tokens=300,
                    ),
                ],
            ),
            
            "verify": TierDefinition(
                name="verify",
                max_tokens=800,
                sections=[
                    ContextSection(
                        name="verification_command",
                        source="domain_context",
                        max_tokens=100,
                        required=True,
                    ),
                    ContextSection(
                        name="check_results",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="remaining_issues",
                        source="precomputed",
                        max_tokens=300,
                    ),
                ],
            ),
        }
        
        return definitions.get(phase, definitions["init"])
    
    def get_system_prompt(self, phase: str = None) -> str:
        """System prompt for fix_violation tasks."""
        return """You are an expert code refactoring agent.

RULES:
1. One action per response
2. Prefer semantic tools (extract_function) over text edits
3. If check passes → 'complete'. If stuck → 'escalate'.

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: why this action
```"""
```

### 5.5 Implement Feature Template

```python
# src/agentforge/core/context/templates/implement_feature.py

from typing import List
from .base import BaseContextTemplate
from .models import TierDefinition, ContextSection, CompactionLevel


class ImplementFeatureTemplate(BaseContextTemplate):
    """Context template for implement_feature tasks (TDD green phase)."""
    
    @property
    def task_type(self) -> str:
        return "implement_feature"
    
    @property
    def phases(self) -> List[str]:
        return ["init", "analyze", "implement", "verify"]
    
    def get_tier2_for_phase(self, phase: str) -> TierDefinition:
        definitions = {
            "init": TierDefinition(
                name="init",
                max_tokens=1000,
                sections=[
                    ContextSection(
                        name="spec",
                        source="domain_context",
                        max_tokens=500,
                        required=True,
                    ),
                    ContextSection(
                        name="failing_tests",
                        source="precomputed",
                        max_tokens=500,
                        required=True,
                    ),
                ],
            ),
            
            "analyze": TierDefinition(
                name="analyze",
                max_tokens=1500,
                sections=[
                    ContextSection(
                        name="spec_requirements",
                        source="domain_context",
                        max_tokens=400,
                        required=True,
                    ),
                    ContextSection(
                        name="acceptance_criteria",
                        source="domain_context",
                        max_tokens=300,
                        required=True,
                    ),
                    ContextSection(
                        name="test_expectations",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="related_code",
                        source="precomputed",
                        max_tokens=400,
                    ),
                ],
            ),
            
            "implement": TierDefinition(
                name="implement",
                max_tokens=2000,
                sections=[
                    ContextSection(
                        name="failing_tests",
                        source="precomputed",
                        max_tokens=600,
                        required=True,
                    ),
                    ContextSection(
                        name="target_location",
                        source="precomputed",
                        max_tokens=200,
                    ),
                    ContextSection(
                        name="interface_definition",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="similar_implementations",
                        source="precomputed",
                        max_tokens=500,
                    ),
                ],
            ),
            
            "verify": TierDefinition(
                name="verify",
                max_tokens=800,
                sections=[
                    ContextSection(
                        name="test_results",
                        source="precomputed",
                        max_tokens=400,
                        required=True,
                    ),
                    ContextSection(
                        name="coverage_delta",
                        source="precomputed",
                        max_tokens=200,
                    ),
                    ContextSection(
                        name="remaining_failures",
                        source="precomputed",
                        max_tokens=200,
                    ),
                ],
            ),
        }
        
        return definitions.get(phase, definitions["init"])
    
    def get_system_prompt(self, phase: str = None) -> str:
        return """You are an expert implementation agent (TDD green phase).

GOAL: Make the failing tests pass with minimal, correct code.

RULES:
1. Focus on making tests pass, not gold-plating
2. Follow existing code patterns
3. One action per response

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: why this makes the test pass
```"""
```

### 5.6 Template Registry

```python
# src/agentforge/core/context/templates/__init__.py

from typing import Dict, Type
from .base import BaseContextTemplate
from .fix_violation import FixViolationTemplate
from .implement_feature import ImplementFeatureTemplate
# Import others as implemented


# Registry of all templates
_TEMPLATE_REGISTRY: Dict[str, Type[BaseContextTemplate]] = {
    "fix_violation": FixViolationTemplate,
    "implement_feature": ImplementFeatureTemplate,
    # Add others here
}


def get_template_for_task(task_type: str) -> BaseContextTemplate:
    """
    Get the appropriate template for a task type.
    
    Args:
        task_type: The type of task
        
    Returns:
        Instantiated template
        
    Raises:
        ValueError: If task type is unknown
    """
    if task_type not in _TEMPLATE_REGISTRY:
        available = ", ".join(_TEMPLATE_REGISTRY.keys())
        raise ValueError(
            f"Unknown task type: {task_type}. Available: {available}"
        )
    
    return _TEMPLATE_REGISTRY[task_type]()


def register_template(task_type: str, template_class: Type[BaseContextTemplate]) -> None:
    """
    Register a new template type.
    
    Allows extensions to add custom task types.
    """
    _TEMPLATE_REGISTRY[task_type] = template_class


def list_task_types() -> list:
    """List all registered task types."""
    return list(_TEMPLATE_REGISTRY.keys())
```

### 5.7 Tests

```python
# tests/unit/context/test_templates.py

import pytest
from agentforge.core.context.templates import (
    get_template_for_task,
    list_task_types,
    BaseContextTemplate,
)
from agentforge.core.context.templates.fix_violation import FixViolationTemplate
from agentforge.core.context.templates.models import CompactionLevel


class TestTemplateRegistry:
    def test_get_fix_violation_template(self):
        template = get_template_for_task("fix_violation")
        assert isinstance(template, FixViolationTemplate)
        assert template.task_type == "fix_violation"
    
    def test_unknown_task_type_raises(self):
        with pytest.raises(ValueError, match="Unknown task type"):
            get_template_for_task("nonexistent")
    
    def test_list_task_types(self):
        types = list_task_types()
        assert "fix_violation" in types


class TestFixViolationTemplate:
    @pytest.fixture
    def template(self):
        return FixViolationTemplate()
    
    def test_phases(self, template):
        assert template.phases == ["init", "analyze", "implement", "verify"]
    
    def test_tier2_analyze_phase(self, template):
        tier2 = template.get_tier2_for_phase("analyze")
        
        assert tier2.name == "analyze"
        section_names = [s.name for s in tier2.sections]
        assert "violation" in section_names
        assert "file_overview" in section_names
    
    def test_tier2_implement_phase(self, template):
        tier2 = template.get_tier2_for_phase("implement")
        
        section_names = [s.name for s in tier2.sections]
        assert "target_source" in section_names
        assert "extraction_suggestions" in section_names
        
        # Check compaction level
        target_source = tier2.get_section("target_source")
        assert target_source.compaction == CompactionLevel.TRUNCATE_MIDDLE
    
    def test_required_sections(self, template):
        tier2 = template.get_tier2_for_phase("implement")
        
        required = [s for s in tier2.sections if s.required]
        required_names = [s.name for s in required]
        
        assert "target_source" in required_names
        assert "extraction_suggestions" in required_names
    
    def test_system_prompt_is_small(self, template):
        prompt = template.get_system_prompt()
        tokens = len(prompt) // 4
        
        assert tokens < 200  # Must be cacheable


class TestBaseContextTemplate:
    def test_tier1_always_present(self):
        tier1 = BaseContextTemplate.TIER1_ALWAYS
        
        section_names = [s.name for s in tier1.sections]
        assert "fingerprint" in section_names
        assert "task" in section_names
        assert "phase" in section_names
        
        # All tier1 sections are required
        for section in tier1.sections:
            assert section.compaction == CompactionLevel.NEVER
    
    def test_total_budget(self):
        template = FixViolationTemplate()
        budget = template.get_total_budget()
        
        # Should be reasonable (< 5000 tokens)
        assert 2000 < budget < 5000
```

---

**[Saved Part 4 - Context Templates Implementation]**

*Continue to Part 5: Integration and Testing Strategy...*
