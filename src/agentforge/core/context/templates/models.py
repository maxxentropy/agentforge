# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: context-templates-v1
# @component_id: context-templates-models
# @test_path: tests/unit/context/test_templates.py

"""
Context Template Models
=======================

Data models for defining context templates:
- CompactionLevel: How aggressively a section can be compacted
- ContextSection: Definition of a single context section
- TierDefinition: Definition of a context tier (Tier1, Tier2, Tier3)
- PhaseContextDef: Context definition for a specific phase

Token budget allocation:
- Tier 1 (always): ~800 tokens - fingerprint, task, phase
- Tier 2 (phase): ~1500 tokens - phase-specific content
- Tier 3 (on-demand): ~1000 tokens - understanding, recent actions
"""

from enum import Enum

from pydantic import BaseModel, Field


class CompactionLevel(str, Enum):
    """How aggressively a section can be compacted."""

    NEVER = "never"  # Never compact (fingerprint, task)
    NORMAL = "normal"  # Compact under pressure
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
    sections: list[ContextSection]

    def get_section(self, name: str) -> ContextSection | None:
        """Get a section by name."""
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def get_required_sections(self) -> list[ContextSection]:
        """Get all required sections."""
        return [s for s in self.sections if s.required]

    def get_section_names(self) -> list[str]:
        """Get list of all section names."""
        return [s.name for s in self.sections]


class PhaseContextDef(BaseModel):
    """Context definition for a specific phase."""

    phase: str
    tier2: TierDefinition
    system_prompt_additions: str | None = None
