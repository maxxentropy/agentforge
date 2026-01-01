# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-template-discovery
# @test_path: tests/unit/context/test_templates.py

"""
Discovery Context Template
==========================

Context template for discovery tasks (codebase analysis).

Phases:
- scan: Initial file structure and entry point scanning
- analyze: Deep analysis of dependencies and patterns
- synthesize: Generate discoveries and recommendations

Token budget prioritizes:
- analyze phase: 2000 tokens (needs dependency graphs + pattern candidates)
- scan phase: 1500 tokens (needs file structure)
- synthesize phase: 1000 tokens (consolidation)
"""

from typing import List, Optional

from .base import BaseContextTemplate
from .models import CompactionLevel, ContextSection, TierDefinition


class DiscoveryTemplate(BaseContextTemplate):
    """Context template for discovery tasks (codebase analysis)."""

    @property
    def task_type(self) -> str:
        return "discovery"

    @property
    def phases(self) -> List[str]:
        return ["scan", "analyze", "synthesize"]

    def get_tier2_for_phase(self, phase: str) -> TierDefinition:
        """Get phase-specific tier 2 definition."""
        definitions = {
            "scan": TierDefinition(
                name="scan",
                max_tokens=1500,
                sections=[
                    ContextSection(
                        name="file_structure",
                        source="precomputed",
                        max_tokens=800,
                        compaction=CompactionLevel.NORMAL,
                    ),
                    ContextSection(
                        name="entry_points",
                        source="precomputed",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="config_files",
                        source="precomputed",
                        max_tokens=400,
                    ),
                ],
            ),
            "analyze": TierDefinition(
                name="analyze",
                max_tokens=2000,
                sections=[
                    ContextSection(
                        name="dependency_graph",
                        source="precomputed",
                        max_tokens=600,
                        compaction=CompactionLevel.TRUNCATE_MIDDLE,
                    ),
                    ContextSection(
                        name="pattern_candidates",
                        source="precomputed",
                        max_tokens=500,
                    ),
                    ContextSection(
                        name="architecture_hints",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="zone_detection",
                        source="precomputed",
                        max_tokens=500,
                    ),
                ],
            ),
            "synthesize": TierDefinition(
                name="synthesize",
                max_tokens=1000,
                sections=[
                    ContextSection(
                        name="discovered_patterns",
                        source="precomputed",
                        max_tokens=500,
                        required=True,
                    ),
                    ContextSection(
                        name="zone_boundaries",
                        source="precomputed",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="recommendations",
                        source="precomputed",
                        max_tokens=200,
                    ),
                ],
            ),
        }

        return definitions.get(phase, definitions["scan"])

    def get_system_prompt(self, phase: Optional[str] = None) -> str:
        """System prompt for discovery tasks."""
        return """You are an expert codebase analyst.

RULES:
1. Map structure before analyzing patterns
2. Identify architectural boundaries (zones)
3. Document dependencies accurately
4. Synthesize findings into actionable insights

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: what this reveals
```"""
