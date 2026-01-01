# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-template-bridge
# @test_path: tests/unit/context/test_templates.py

"""
Bridge Context Template
=======================

Context template for bridge tasks (contract mapping).

Phases:
- analyze: Understand existing code structure and target contracts
- map: Create mappings between code and contracts
- validate: Verify mapping coverage and correctness

Token budget prioritizes:
- map phase: 2000 tokens (needs candidate mappings + transformation hints)
- analyze phase: 1500 tokens (needs structure + contracts)
- validate phase: 800 tokens (coverage + results)
"""

from typing import List, Optional

from .base import BaseContextTemplate
from .models import CompactionLevel, ContextSection, TierDefinition


class BridgeTemplate(BaseContextTemplate):
    """Context template for bridge tasks (contract mapping)."""

    @property
    def task_type(self) -> str:
        return "bridge"

    @property
    def phases(self) -> List[str]:
        return ["analyze", "map", "validate"]

    def get_tier2_for_phase(self, phase: str) -> TierDefinition:
        """Get phase-specific tier 2 definition."""
        definitions = {
            "analyze": TierDefinition(
                name="analyze",
                max_tokens=1500,
                sections=[
                    ContextSection(
                        name="existing_code_structure",
                        source="precomputed",
                        max_tokens=600,
                        compaction=CompactionLevel.NORMAL,
                    ),
                    ContextSection(
                        name="target_contracts",
                        source="domain_context",
                        max_tokens=400,
                        required=True,
                    ),
                    ContextSection(
                        name="mapping_rules",
                        source="precomputed",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="existing_mappings",
                        source="precomputed",
                        max_tokens=200,
                    ),
                ],
            ),
            "map": TierDefinition(
                name="map",
                max_tokens=2000,
                sections=[
                    ContextSection(
                        name="candidate_mappings",
                        source="precomputed",
                        max_tokens=700,
                        required=True,
                    ),
                    ContextSection(
                        name="conflict_analysis",
                        source="precomputed",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="transformation_hints",
                        source="precomputed",
                        max_tokens=500,
                    ),
                    ContextSection(
                        name="related_mappings",
                        source="precomputed",
                        max_tokens=500,
                        compaction=CompactionLevel.AGGRESSIVE,
                    ),
                ],
            ),
            "validate": TierDefinition(
                name="validate",
                max_tokens=800,
                sections=[
                    ContextSection(
                        name="mapping_coverage",
                        source="precomputed",
                        max_tokens=300,
                        required=True,
                    ),
                    ContextSection(
                        name="unmapped_elements",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="validation_results",
                        source="precomputed",
                        max_tokens=300,
                    ),
                ],
            ),
        }

        return definitions.get(phase, definitions["analyze"])

    def get_system_prompt(self, phase: Optional[str] = None) -> str:
        """System prompt for bridge tasks."""
        return """You are an expert contract mapping agent.

RULES:
1. Analyze code structure before mapping
2. Follow established mapping rules
3. Flag conflicts and ambiguities
4. Ensure complete coverage

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: mapping rationale
```"""
