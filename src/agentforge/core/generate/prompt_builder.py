# @spec_file: .agentforge/specs/core-generate-v1.yaml
# @spec_id: core-generate-v1
# @component_id: core-generate-prompt_builder
# @test_path: tests/unit/tools/generate/test_engine.py

"""
Prompt Builder
==============

Assembles LLM prompts from GenerationContext.
Uses XML structure for clear separation of concerns.
"""

from pathlib import Path
from typing import Any

import yaml

from agentforge.core.generate.domain import GenerationContext, GenerationMode, GenerationPhase


class PromptBuilder:
    """
    Builds prompts for LLM code generation.

    Uses XML structure for:
    - Clear section boundaries
    - Easy parsing by LLMs
    - Consistent formatting
    """

    # Phase-specific instructions
    PHASE_INSTRUCTIONS = {
        GenerationPhase.RED: """Generate failing tests for the specification.

Requirements:
1. Use pytest with clear arrange-act-assert structure
2. Tests should FAIL because implementation doesn't exist yet
3. Each test should verify ONE specific behavior from the spec
4. Use descriptive test names: test_{method}_{scenario}_{expected_result}
5. Include both positive and negative test cases
6. Mock external dependencies appropriately

Output format:
- Use ```python:path/to/test_file.py``` markers
- One test file per component
- Include all necessary imports""",

        GenerationPhase.GREEN: """Generate minimal implementation to pass the tests.

Requirements:
1. Implement ONLY what's needed to pass the tests
2. Follow existing project patterns and conventions
3. Use proper type hints
4. Keep implementation simple - no premature optimization
5. Handle edge cases specified in tests
6. Follow the specification's behavioral requirements

Output format:
- Use ```python:path/to/impl_file.py``` markers
- One implementation file per component
- Include all necessary imports""",

        GenerationPhase.REFACTOR: """Improve the code without changing behavior.

Requirements:
1. All existing tests must still pass
2. Extract common patterns into reusable functions
3. Improve naming for clarity
4. Remove code duplication
5. Add appropriate documentation
6. Ensure proper error handling
7. DO NOT add new features or change behavior

Output format:
- Use ```python:path/to/file.py``` markers
- Only output files that have changes
- Explain each refactoring decision""",
    }

    # Mode-specific additions
    MODE_INSTRUCTIONS = {
        GenerationMode.FULL: "",  # No additional instructions
        GenerationMode.INCREMENTAL: """
Additional: This is an incremental update to existing code.
- Only add/modify the specific methods or features requested
- Preserve all existing functionality
- Maintain backwards compatibility""",
        GenerationMode.FIX: """
Additional: This is a fix for failing tests or errors.
- Focus on fixing the specific error described
- Minimize changes to existing code
- Explain what was wrong and how you fixed it""",
    }

    def __init__(self, project_path: Path | None = None):
        """
        Initialize prompt builder.

        Args:
            project_path: Root of the project (for loading context)
        """
        self.project_path = project_path or Path.cwd()

    def build(self, context: GenerationContext) -> str:
        """
        Build prompt from generation context.

        Args:
            context: GenerationContext with spec, phase, patterns, etc.

        Returns:
            Formatted prompt string
        """
        sections = []

        # System instruction
        sections.append(self._build_system_section())

        # Context section
        sections.append(self._build_context_section(context))

        # Instructions section
        sections.append(self._build_instructions_section(context))

        # Output format section
        sections.append(self._build_output_section(context))

        return "\n\n".join(sections)

    def _build_system_section(self) -> str:
        """Build system/role instruction."""
        return """<system>
You are an expert software engineer generating code for a Python project.
You follow clean architecture principles and write high-quality, tested code.
You output code using markdown code blocks with file paths.
</system>"""

    def _build_context_section(self, context: GenerationContext) -> str:
        """Build the context section with all relevant information."""
        parts = ["<context>"]

        # Specification
        parts.append(self._format_specification(context.spec))

        # Phase information
        parts.append(f"""
<phase>{context.phase.value}</phase>
<mode>{context.mode.value}</mode>""")

        # Component focus (if specified)
        if context.component_name:
            parts.append(f"<component>{context.component_name}</component>")

        # Existing code (for GREEN/REFACTOR phases)
        if context.existing_tests:
            parts.append(self._format_existing_code(
                "existing_tests",
                context.existing_tests,
                "Tests that must pass"
            ))

        if context.existing_impl:
            parts.append(self._format_existing_code(
                "existing_implementation",
                context.existing_impl,
                "Current implementation to improve"
            ))

        # Patterns from project
        if context.patterns:
            parts.append(self._format_patterns(context.patterns))

        # Code examples
        if context.examples:
            parts.append(self._format_examples(context.examples))

        # Error context (for FIX mode)
        if context.error_context:
            parts.append(self._format_error_context(context.error_context))

        parts.append("</context>")
        return "\n".join(parts)

    def _format_specification(self, spec: dict[str, Any]) -> str:
        """Format specification as YAML in XML wrapper."""
        spec_yaml = yaml.dump(spec, default_flow_style=False, sort_keys=False)
        return f"""
<specification>
{spec_yaml.strip()}
</specification>"""

    def _format_existing_code(
        self,
        tag: str,
        code: str,
        description: str
    ) -> str:
        """Format existing code section."""
        return f"""
<{tag} description="{description}">
```python
{code.strip()}
```
</{tag}>"""

    def _format_patterns(self, patterns: dict[str, Any]) -> str:
        """Format detected patterns."""
        if not patterns:
            return ""

        pattern_lines = []
        for category, items in patterns.items():
            if isinstance(items, list):
                for item in items:
                    pattern_lines.append(f"  - {category}: {item}")
            else:
                pattern_lines.append(f"  - {category}: {items}")

        return f"""
<patterns description="Detected project patterns to follow">
{chr(10).join(pattern_lines)}
</patterns>"""

    def _format_examples(self, examples: list[dict[str, Any]]) -> str:
        """Format code examples."""
        if not examples:
            return ""

        example_parts = ["<examples description=\"Similar code from project\">"]

        for i, example in enumerate(examples, 1):
            path = example.get("path", f"example_{i}")
            content = example.get("content", "")
            relevance = example.get("relevance", "")

            example_parts.append(f"""
<example path="{path}" relevance="{relevance}">
```python
{content.strip()}
```
</example>""")

        example_parts.append("</examples>")
        return "\n".join(example_parts)

    def _format_error_context(self, error_context: dict[str, Any]) -> str:
        """Format error context for FIX mode."""
        parts = ["<error_context description=\"Error to fix\">"]

        if "error_message" in error_context:
            parts.append(f"  <error_message>{error_context['error_message']}</error_message>")

        if "error_type" in error_context:
            parts.append(f"  <error_type>{error_context['error_type']}</error_type>")

        if "stack_trace" in error_context:
            parts.append(f"""  <stack_trace>
{error_context['stack_trace']}
  </stack_trace>""")

        if "failing_tests" in error_context:
            tests = error_context["failing_tests"]
            if isinstance(tests, list):
                tests = "\n".join(f"    - {t}" for t in tests)
            parts.append(f"  <failing_tests>\n{tests}\n  </failing_tests>")

        parts.append("</error_context>")
        return "\n".join(parts)

    def _build_instructions_section(self, context: GenerationContext) -> str:
        """Build phase-specific instructions."""
        phase_instructions = self.PHASE_INSTRUCTIONS.get(
            context.phase,
            "Generate code according to the specification."
        )
        mode_instructions = self.MODE_INSTRUCTIONS.get(context.mode, "")

        return f"""<instructions>
{phase_instructions}
{mode_instructions}
</instructions>"""

    def _build_output_section(self, context: GenerationContext) -> str:
        """Build output format instructions."""
        # Get paths from spec if available
        component = self._get_component_from_spec(context)

        path_hints = ""
        if component:
            if context.phase == GenerationPhase.RED:
                test_file = component.get("test_file", "tests/unit/test_component.py")
                path_hints = f"\nExpected test file: {test_file}"
            elif context.phase == GenerationPhase.GREEN:
                impl_file = component.get("impl_file", "src/component.py")
                path_hints = f"\nExpected implementation file: {impl_file}"

        return f"""<output_format>
Output your code using markdown code blocks with file paths:

```python:path/to/file.py
# Your code here
```

Important:
- Use the EXACT paths from the specification when provided
- Include ALL necessary imports at the top of each file
- One code block per file
- Add a brief explanation before each code block
{path_hints}
</output_format>"""

    def _get_component_from_spec(
        self,
        context: GenerationContext
    ) -> dict[str, Any] | None:
        """Extract component info from spec."""
        if not context.component_name:
            return None

        components = context.spec.get("components", [])
        for comp in components:
            if comp.get("name") == context.component_name:
                return comp

        return None

    def estimate_tokens(self, prompt: str) -> int:
        """
        Estimate token count for prompt.

        Uses ~4 chars per token approximation.
        """
        return len(prompt) // 4


class PromptTemplates:
    """
    Pre-built prompt templates for common scenarios.

    Use these as starting points or for simple cases.
    """

    @staticmethod
    def simple_test_prompt(
        class_name: str,
        methods: list[dict[str, str]],
        test_file: str,
    ) -> str:
        """Generate a simple test generation prompt."""
        method_specs = "\n".join(
            f"  - {m['name']}: {m.get('behavior', 'implement correctly')}"
            for m in methods
        )

        return f"""Generate pytest tests for the {class_name} class.

Methods to test:
{method_specs}

Output the tests to: {test_file}

Use pytest with clear arrange-act-assert structure.
Each test should verify one specific behavior.
Tests should FAIL initially (no implementation exists).

Output format:
```python:{test_file}
# Your test code here
```"""

    @staticmethod
    def simple_impl_prompt(
        class_name: str,
        test_code: str,
        impl_file: str,
    ) -> str:
        """Generate a simple implementation prompt."""
        return f"""Implement the {class_name} class to pass these tests:

```python
{test_code}
```

Output the implementation to: {impl_file}

Requirements:
- Implement only what's needed to pass the tests
- Use proper type hints
- Follow Python best practices

Output format:
```python:{impl_file}
# Your implementation here
```"""
