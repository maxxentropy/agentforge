# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-template-refactor
# @test_path: tests/unit/context/test_templates.py

"""
Refactor Context Template
=========================

Context template for refactor tasks (general refactoring).

Phases:
- init: Identify refactoring scope and goals
- analyze: Understand code structure and dependencies
- implement: Execute refactoring changes
- verify: Confirm behavior preservation

Token budget prioritizes:
- implement phase: 2000 tokens (needs source code + patterns)
- analyze phase: 1500 tokens (needs structure + dependencies)
- verify phase: 800 tokens (test results)
"""

from typing import List, Optional

from .base import BaseContextTemplate
from .models import CompactionLevel, ContextSection, TierDefinition


class RefactorTemplate(BaseContextTemplate):
    """Context template for refactor tasks (general refactoring)."""

    @property
    def task_type(self) -> str:
        return "refactor"

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
                        name="refactor_goal",
                        source="domain_context",
                        max_tokens=400,
                        required=True,
                    ),
                    ContextSection(
                        name="scope",
                        source="domain_context",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="constraints",
                        source="domain_context",
                        max_tokens=300,
                    ),
                ],
            ),
            "analyze": TierDefinition(
                name="analyze",
                max_tokens=1500,
                sections=[
                    ContextSection(
                        name="target_code",
                        source="precomputed",
                        max_tokens=600,
                        compaction=CompactionLevel.TRUNCATE_MIDDLE,
                        required=True,
                    ),
                    ContextSection(
                        name="dependencies",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="callers",
                        source="precomputed",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="test_coverage",
                        source="precomputed",
                        max_tokens=200,
                    ),
                ],
            ),
            "implement": TierDefinition(
                name="implement",
                max_tokens=2000,
                sections=[
                    ContextSection(
                        name="source_code",
                        source="precomputed",
                        max_tokens=1000,
                        compaction=CompactionLevel.TRUNCATE_MIDDLE,
                        required=True,
                    ),
                    ContextSection(
                        name="refactoring_patterns",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="similar_refactors",
                        source="precomputed",
                        max_tokens=300,
                        compaction=CompactionLevel.AGGRESSIVE,
                    ),
                    ContextSection(
                        name="action_hints",
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
                        name="test_command",
                        source="domain_context",
                        max_tokens=100,
                        required=True,
                    ),
                    ContextSection(
                        name="test_results",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="behavior_diff",
                        source="precomputed",
                        max_tokens=300,
                    ),
                ],
            ),
        }

        return definitions.get(phase, definitions["init"])

    def get_system_prompt(self, phase: Optional[str] = None) -> str:
        """System prompt for refactor tasks."""
        return """You are an expert code refactoring agent.

RULES:
1. Preserve behavior - refactoring must not change functionality
2. Make incremental changes
3. Run tests after each change
4. Prefer semantic refactoring tools

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: refactoring rationale
```"""
