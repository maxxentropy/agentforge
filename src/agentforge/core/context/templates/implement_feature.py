# @spec_file: specs/minimal-context-architecture-specs/specs/minimal-context-architecture/04-context-templates.yaml
# @spec_id: context-templates-v1
# @component_id: context-template-implement-feature
# @test_path: tests/unit/context/test_templates.py

"""
Implement Feature Context Template
==================================

Context template for implement_feature tasks (TDD green phase).

This template supports the "green" phase of TDD where the goal is
to write minimal code to make failing tests pass.

Phases:
- init: Load spec and identify failing tests
- analyze: Understand requirements and test expectations
- implement: Write code to make tests pass
- verify: Confirm all tests pass

Token budget prioritizes:
- implement phase: 2000 tokens (needs tests + interface + examples)
- analyze phase: 1500 tokens (needs requirements + test expectations)
- verify phase: 800 tokens (minimal, just results)
"""

from typing import List, Optional

from .base import BaseContextTemplate
from .models import ContextSection, TierDefinition


class ImplementFeatureTemplate(BaseContextTemplate):
    """Context template for implement_feature tasks (TDD green phase)."""

    @property
    def task_type(self) -> str:
        return "implement_feature"

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

    def get_system_prompt(self, phase: Optional[str] = None) -> str:
        """System prompt for implement_feature tasks."""
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
