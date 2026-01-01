# @spec_file: specs/minimal-context-architecture-specs/specs/minimal-context-architecture/04-context-templates.yaml
# @spec_id: context-templates-v1
# @component_id: context-template-fix-violation
# @test_path: tests/unit/context/test_templates.py

"""
Fix Violation Context Template
==============================

Context template for fix_violation tasks (code refactoring).

Phases:
- init: Initial violation assessment
- analyze: Deep analysis of code and patterns
- implement: Execute the fix with semantic tools
- verify: Confirm fix resolves the violation

Token budget prioritizes:
- implement phase: 2000 tokens (needs source code + suggestions)
- analyze phase: 1500 tokens (needs patterns + file overview)
- verify phase: 800 tokens (minimal, just results)
"""

from typing import List, Optional

from .base import BaseContextTemplate
from .models import CompactionLevel, ContextSection, TierDefinition


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

    def get_system_prompt(self, phase: Optional[str] = None) -> str:
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
