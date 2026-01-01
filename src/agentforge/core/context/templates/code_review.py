# @spec_file: specs/minimal-context-architecture/04-context-templates.yaml
# @spec_id: context-templates-v1
# @component_id: context-template-code-review
# @test_path: tests/unit/context/test_templates.py

"""
Code Review Context Template
============================

Context template for code_review tasks.

Phases:
- init: Initial diff and context gathering
- analyze: Deep analysis of changes and impacts
- report: Generate review findings and suggestions

Token budget prioritizes:
- analyze phase: 2000 tokens (needs full diff context)
- init phase: 1000 tokens (overview)
- report phase: 1200 tokens (findings + suggestions)
"""

from typing import Dict, List, Optional

from .base import BaseContextTemplate
from .models import CompactionLevel, ContextSection, TierDefinition


class CodeReviewTemplate(BaseContextTemplate):
    """Context template for code_review tasks."""

    @property
    def task_type(self) -> str:
        return "code_review"

    @property
    def phases(self) -> List[str]:
        return ["init", "analyze", "report"]

    def get_phase_mapping(self) -> Dict[str, str]:
        """Map standard phases to code_review phases."""
        return {
            "init": "init",
            "analyze": "analyze",
            "plan": "analyze",
            "implement": "report",
            "verify": "report",
        }

    def get_tier2_for_phase(self, phase: str) -> TierDefinition:
        """Get phase-specific tier 2 definition."""
        definitions = {
            "init": TierDefinition(
                name="init",
                max_tokens=1000,
                sections=[
                    ContextSection(
                        name="diff_summary",
                        source="domain_context",
                        max_tokens=400,
                        required=True,
                    ),
                    ContextSection(
                        name="changed_files",
                        source="domain_context",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="pr_context",
                        source="domain_context",
                        max_tokens=300,
                    ),
                ],
            ),
            "analyze": TierDefinition(
                name="analyze",
                max_tokens=2000,
                sections=[
                    ContextSection(
                        name="full_diff",
                        source="domain_context",
                        max_tokens=800,
                        compaction=CompactionLevel.TRUNCATE_MIDDLE,
                        required=True,
                    ),
                    ContextSection(
                        name="affected_functions",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="test_coverage",
                        source="precomputed",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="related_code",
                        source="precomputed",
                        max_tokens=500,
                        compaction=CompactionLevel.AGGRESSIVE,
                    ),
                ],
            ),
            "report": TierDefinition(
                name="report",
                max_tokens=1200,
                sections=[
                    ContextSection(
                        name="findings",
                        source="precomputed",
                        max_tokens=500,
                        required=True,
                    ),
                    ContextSection(
                        name="suggestions",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="security_concerns",
                        source="precomputed",
                        max_tokens=300,
                    ),
                ],
            ),
        }

        return definitions.get(phase, definitions["init"])

    def get_system_prompt(self, phase: Optional[str] = None) -> str:
        """System prompt for code_review tasks."""
        return """You are an expert code reviewer.

RULES:
1. Focus on correctness, security, and maintainability
2. Provide specific, actionable feedback
3. Reference line numbers when possible
4. Distinguish blocking issues from suggestions

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: review rationale
```"""
