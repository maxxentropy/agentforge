# @spec_file: specs/minimal-context-architecture/04-context-templates.yaml
# @spec_id: context-templates-v1
# @component_id: context-templates-base
# @test_path: tests/unit/context/test_templates.py

"""
Base Context Template
=====================

Abstract base class for context templates defining:
- Tier 1: Always present (~800 tokens) - fingerprint, task, phase
- Tier 2: Phase-dependent (~1500 tokens) - varies by task type
- Tier 3: On-demand (~1000 tokens) - understanding, recent actions

Each task type (fix_violation, implement_feature, etc.) extends this
base to define phase-specific tier 2 content.

Usage:
    ```python
    template = get_template_for_task("fix_violation")

    context = template.build_context_dict(
        fingerprint=fingerprint,
        task_spec=task_spec,
        state_spec=state_spec,
        phase="analyze",
        precomputed={...},
        domain_context={...},
    )
    ```
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import yaml

from .models import (
    CompactionLevel,
    ContextSection,
    TierDefinition,
)
from ..fingerprint import ProjectFingerprint


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

    def get_phase_mapping(self) -> Dict[str, str]:
        """
        Map standard PhaseMachine phases to this template's phases.

        The PhaseMachine uses standard phases: init, analyze, plan, implement, verify.
        Templates may use different phase names that carry domain-specific meaning.

        Override this method to provide custom mappings.

        Returns:
            Dict mapping standard phase names to template phase names.

        Example for discovery template:
            {"init": "scan", "analyze": "analyze", "implement": "synthesize", "verify": "synthesize"}
        """
        # Default: identity mapping for standard phases
        return {
            "init": "init" if "init" in self.phases else self.phases[0],
            "analyze": "analyze" if "analyze" in self.phases else (
                self.phases[1] if len(self.phases) > 1 else self.phases[0]
            ),
            "plan": "analyze" if "analyze" in self.phases else self.phases[0],
            "implement": "implement" if "implement" in self.phases else (
                self.phases[-2] if len(self.phases) > 2 else self.phases[-1]
            ),
            "verify": "verify" if "verify" in self.phases else self.phases[-1],
        }

    def translate_phase(self, standard_phase: str) -> str:
        """
        Translate a standard phase name to this template's phase name.

        Args:
            standard_phase: Phase name from PhaseMachine (init, analyze, etc.)

        Returns:
            Corresponding template phase name
        """
        mapping = self.get_phase_mapping()
        template_phase = mapping.get(standard_phase.lower(), self.phases[0])
        # Ensure the returned phase is valid for this template
        if template_phase not in self.phases:
            return self.phases[0]
        return template_phase

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
            self.TIER1_ALWAYS.max_tokens
            + max(self.get_tier2_for_phase(p).max_tokens for p in self.phases)
            + self.TIER3_ON_DEMAND.max_tokens
        )

    def build_context_dict(
        self,
        fingerprint: ProjectFingerprint,
        task_spec: Any,
        state_spec: Any,
        phase: str,
        precomputed: Dict[str, Any],
        domain_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the context dictionary from components.

        This is the main method for context construction.

        Args:
            fingerprint: Project fingerprint
            task_spec: Task specification (TaskSpec from context_models)
            state_spec: Current state (StateSpec from context_models)
            phase: Current phase name
            precomputed: Pre-computed context values
            domain_context: Domain-specific context

        Returns:
            Complete context dictionary ready for LLM
        """
        context: Dict[str, Any] = {}

        # Tier 1: Always present
        context["fingerprint"] = fingerprint.to_context_yaml()
        context["task"] = {
            "id": getattr(task_spec, "task_id", "unknown"),
            "type": getattr(task_spec, "task_type", self.task_type),
            "goal": getattr(task_spec, "goal", ""),
            "success_criteria": getattr(task_spec, "success_criteria", []),
        }
        context["phase"] = {
            "current": phase,
            "step": getattr(state_spec, "current_step", 0),
            "max_steps": getattr(
                getattr(state_spec, "phase", None), "max_steps", 20
            ),
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
        state_spec: Any,
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
            understanding = getattr(state_spec, "understanding", None)
            if understanding and hasattr(understanding, "get_high_confidence"):
                facts = understanding.get_high_confidence(0.7)
                if facts:
                    return [
                        {"statement": f.statement, "confidence": f.confidence}
                        for f in facts[:10]
                    ]

        elif section.source == "recent_actions":
            recent_actions = getattr(state_spec, "recent_actions", None)
            if recent_actions:
                return [
                    {
                        "action": a.action,
                        "result": a.result.value if a.result else "unknown",
                        "summary": getattr(a, "summary", ""),
                    }
                    for a in recent_actions[-3:]
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
            sample = yaml.dump(value[0], default_flow_style=False)
            tokens_per_item = len(sample) // 4
            max_items = max(1, max_tokens // max(1, tokens_per_item))
            return value[:max_items]

        return value

    def estimate_context_tokens(self, context: Dict[str, Any]) -> int:
        """Estimate total tokens in a context dictionary."""
        yaml_str = yaml.dump(context, default_flow_style=False)
        return len(yaml_str) // 4
