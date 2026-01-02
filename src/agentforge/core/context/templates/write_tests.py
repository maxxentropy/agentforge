# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: context-templates-v1
# @component_id: context-template-write-tests
# @test_path: tests/unit/context/test_templates.py

"""
Write Tests Context Template
============================

Context template for write_tests tasks (TDD red phase).

Phases:
- init: Initial test requirements assessment
- analyze: Understand testable interface and coverage gaps
- implement: Write failing tests
- verify: Ensure tests fail for the right reasons

Token budget prioritizes:
- implement phase: 2000 tokens (needs test patterns + fixtures)
- analyze phase: 1500 tokens (needs interface + coverage info)
- verify phase: 600 tokens (minimal, just failure reasons)
"""


from .base import BaseContextTemplate
from .models import CompactionLevel, ContextSection, TierDefinition


class WriteTestsTemplate(BaseContextTemplate):
    """Context template for write_tests tasks (TDD red phase)."""

    @property
    def task_type(self) -> str:
        return "write_tests"

    @property
    def phases(self) -> list[str]:
        return ["init", "analyze", "implement", "verify"]

    def get_tier2_for_phase(self, phase: str) -> TierDefinition:
        """Get phase-specific tier 2 definition."""
        definitions = {
            "init": TierDefinition(
                name="init",
                max_tokens=1000,
                sections=[
                    ContextSection(
                        name="spec_requirements",
                        source="domain_context",
                        max_tokens=500,
                        required=True,
                    ),
                    ContextSection(
                        name="existing_tests",
                        source="precomputed",
                        max_tokens=500,
                    ),
                ],
            ),
            "analyze": TierDefinition(
                name="analyze",
                max_tokens=1500,
                sections=[
                    ContextSection(
                        name="acceptance_criteria",
                        source="domain_context",
                        max_tokens=400,
                        required=True,
                    ),
                    ContextSection(
                        name="testable_interface",
                        source="precomputed",
                        max_tokens=300,
                        required=True,
                    ),
                    ContextSection(
                        name="existing_test_patterns",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="coverage_gaps",
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
                        name="test_template",
                        source="precomputed",
                        max_tokens=500,
                    ),
                    ContextSection(
                        name="assertion_hints",
                        source="precomputed",
                        max_tokens=300,
                    ),
                    ContextSection(
                        name="fixture_examples",
                        source="precomputed",
                        max_tokens=400,
                        compaction=CompactionLevel.NORMAL,
                    ),
                    ContextSection(
                        name="edge_cases",
                        source="precomputed",
                        max_tokens=400,
                    ),
                    ContextSection(
                        name="target_interface",
                        source="precomputed",
                        max_tokens=400,
                        required=True,
                    ),
                ],
            ),
            "verify": TierDefinition(
                name="verify",
                max_tokens=600,
                sections=[
                    ContextSection(
                        name="tests_must_fail",
                        source="domain_context",
                        max_tokens=300,
                        required=True,
                    ),
                    ContextSection(
                        name="failure_reasons",
                        source="precomputed",
                        max_tokens=300,
                    ),
                ],
            ),
        }

        return definitions.get(phase, definitions["init"])

    def get_system_prompt(self, phase: str | None = None) -> str:
        """System prompt for write_tests tasks."""
        return """You are an expert test-driven development agent.

RULES:
1. Write tests BEFORE implementation (TDD red phase)
2. Tests MUST fail initially - that's the goal
3. One test file per action
4. Use existing patterns from the codebase

FORMAT:
```yaml
action: action_name
parameters:
  key: value
reasoning: why this test
```"""
