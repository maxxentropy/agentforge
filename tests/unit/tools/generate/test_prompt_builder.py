"""
Tests for Prompt Builder
========================
"""


import pytest

from agentforge.core.generate.domain import (
    GenerationContext,
    GenerationMode,
    GenerationPhase,
)
from agentforge.core.generate.prompt_builder import PromptBuilder, PromptTemplates

# =============================================================================
# PromptBuilder Tests
# =============================================================================


class TestPromptBuilder:
    """Tests for PromptBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create a PromptBuilder instance."""
        return PromptBuilder()

    @pytest.fixture
    def sample_spec(self):
        """Sample specification for testing."""
        return {
            "name": "SessionManager",
            "description": "Manages session lifecycle",
            "components": [
                {
                    "name": "SessionManager",
                    "impl_file": "tools/harness/session_manager.py",
                    "test_file": "tests/unit/harness/test_session_manager.py",
                    "methods": [
                        {"name": "create", "behavior": "Creates a new session"},
                        {"name": "pause", "behavior": "Pauses the current session"},
                    ],
                }
            ],
        }

    def test_build_returns_string(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_includes_system_section(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert "<system>" in prompt
        assert "</system>" in prompt

    def test_build_includes_context_section(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert "<context>" in prompt
        assert "</context>" in prompt

    def test_build_includes_specification(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert "<specification>" in prompt
        assert "SessionManager" in prompt
        assert "Manages session lifecycle" in prompt

    def test_build_includes_phase(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert "<phase>red</phase>" in prompt

    def test_build_includes_mode(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.GREEN,
            mode=GenerationMode.FIX,
        )
        prompt = builder.build(context)
        assert "<mode>fix</mode>" in prompt

    def test_build_includes_component_name(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.RED,
            component_name="SessionManager",
        )
        prompt = builder.build(context)
        assert "<component>SessionManager</component>" in prompt

    def test_build_includes_instructions(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert "<instructions>" in prompt
        assert "</instructions>" in prompt

    def test_build_includes_output_format(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert "<output_format>" in prompt
        assert "```python:path/to/file.py" in prompt

    def test_red_phase_instructions(self, builder, sample_spec):
        context = GenerationContext(spec=sample_spec, phase=GenerationPhase.RED)
        prompt = builder.build(context)
        assert "failing tests" in prompt.lower()
        assert "pytest" in prompt.lower()

    def test_green_phase_instructions(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.GREEN,
            existing_tests="def test_example(): pass",
        )
        prompt = builder.build(context)
        assert "pass the tests" in prompt.lower()
        assert "minimal implementation" in prompt.lower()

    def test_refactor_phase_instructions(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.REFACTOR,
            existing_impl="class Example: pass",
        )
        prompt = builder.build(context)
        assert "refactor" in prompt.lower()
        assert "tests must still pass" in prompt.lower()

    def test_fix_mode_instructions(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.GREEN,
            mode=GenerationMode.FIX,
            error_context={"error_message": "AssertionError"},
        )
        prompt = builder.build(context)
        assert "fix" in prompt.lower()
        assert "error" in prompt.lower()


class TestPromptBuilderExistingCode:
    """Tests for existing code handling."""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    @pytest.fixture
    def sample_spec(self):
        return {"name": "Test"}

    def test_includes_existing_tests(self, builder, sample_spec):
        test_code = """
def test_example():
    assert 1 + 1 == 2
"""
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.GREEN,
            existing_tests=test_code,
        )
        prompt = builder.build(context)
        assert "<existing_tests" in prompt
        assert "test_example" in prompt

    def test_includes_existing_implementation(self, builder, sample_spec):
        impl_code = """
class Example:
    def method(self):
        return 42
"""
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.REFACTOR,
            existing_impl=impl_code,
        )
        prompt = builder.build(context)
        assert "<existing_implementation" in prompt
        assert "class Example" in prompt


class TestPromptBuilderPatterns:
    """Tests for pattern handling."""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    @pytest.fixture
    def sample_spec(self):
        return {"name": "Test"}

    def test_includes_patterns(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.RED,
            patterns={
                "test_framework": "pytest",
                "naming_convention": "snake_case",
            },
        )
        prompt = builder.build(context)
        assert "<patterns" in prompt
        assert "pytest" in prompt
        assert "snake_case" in prompt

    def test_empty_patterns_not_included(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.RED,
            patterns={},
        )
        prompt = builder.build(context)
        # Empty patterns section should not be in prompt
        assert "<patterns>" not in prompt or "<patterns" not in prompt


class TestPromptBuilderExamples:
    """Tests for code examples handling."""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    @pytest.fixture
    def sample_spec(self):
        return {"name": "Test"}

    def test_includes_examples(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.RED,
            examples=[
                {
                    "path": "tests/unit/test_existing.py",
                    "content": "def test_foo(): pass",
                    "relevance": "similar test file",
                }
            ],
        )
        prompt = builder.build(context)
        assert "<examples" in prompt
        assert "test_existing.py" in prompt
        assert "def test_foo" in prompt

    def test_empty_examples_not_included(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.RED,
            examples=[],
        )
        prompt = builder.build(context)
        assert "<examples>" not in prompt


class TestPromptBuilderErrorContext:
    """Tests for error context handling."""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    @pytest.fixture
    def sample_spec(self):
        return {"name": "Test"}

    def test_includes_error_message(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.GREEN,
            mode=GenerationMode.FIX,
            error_context={
                "error_message": "AssertionError: expected True",
                "error_type": "AssertionError",
            },
        )
        prompt = builder.build(context)
        assert "<error_context" in prompt
        assert "AssertionError: expected True" in prompt

    def test_includes_stack_trace(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.GREEN,
            mode=GenerationMode.FIX,
            error_context={
                "error_message": "Error",
                "stack_trace": "File test.py, line 10\n  assert False",
            },
        )
        prompt = builder.build(context)
        assert "<stack_trace>" in prompt
        assert "line 10" in prompt

    def test_includes_failing_tests(self, builder, sample_spec):
        context = GenerationContext(
            spec=sample_spec,
            phase=GenerationPhase.GREEN,
            mode=GenerationMode.FIX,
            error_context={
                "error_message": "Error",
                "failing_tests": ["test_one", "test_two"],
            },
        )
        prompt = builder.build(context)
        assert "<failing_tests>" in prompt
        assert "test_one" in prompt
        assert "test_two" in prompt


class TestPromptBuilderOutputPaths:
    """Tests for output path hints."""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    def test_red_phase_shows_test_file_hint(self, builder):
        spec = {
            "components": [
                {
                    "name": "MyComponent",
                    "test_file": "tests/unit/test_my_component.py",
                }
            ]
        }
        context = GenerationContext(
            spec=spec,
            phase=GenerationPhase.RED,
            component_name="MyComponent",
        )
        prompt = builder.build(context)
        assert "tests/unit/test_my_component.py" in prompt

    def test_green_phase_shows_impl_file_hint(self, builder):
        spec = {
            "components": [
                {
                    "name": "MyComponent",
                    "impl_file": "src/my_component.py",
                }
            ]
        }
        context = GenerationContext(
            spec=spec,
            phase=GenerationPhase.GREEN,
            component_name="MyComponent",
        )
        prompt = builder.build(context)
        assert "src/my_component.py" in prompt


class TestPromptBuilderTokenEstimation:
    """Tests for token estimation."""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    def test_estimate_tokens(self, builder):
        # 400 chars should be ~100 tokens
        prompt = "a" * 400
        estimate = builder.estimate_tokens(prompt)
        assert estimate == 100

    def test_estimate_tokens_empty(self, builder):
        assert builder.estimate_tokens("") == 0


# =============================================================================
# PromptTemplates Tests
# =============================================================================


class TestPromptTemplates:
    """Tests for PromptTemplates helper class."""

    def test_simple_test_prompt(self):
        prompt = PromptTemplates.simple_test_prompt(
            class_name="Calculator",
            methods=[
                {"name": "add", "behavior": "adds two numbers"},
                {"name": "subtract", "behavior": "subtracts two numbers"},
            ],
            test_file="tests/test_calculator.py",
        )
        assert "Calculator" in prompt
        assert "add" in prompt
        assert "subtract" in prompt
        assert "tests/test_calculator.py" in prompt
        assert "pytest" in prompt.lower()

    def test_simple_impl_prompt(self):
        prompt = PromptTemplates.simple_impl_prompt(
            class_name="Calculator",
            test_code="def test_add(): assert Calculator().add(1, 2) == 3",
            impl_file="src/calculator.py",
        )
        assert "Calculator" in prompt
        assert "test_add" in prompt
        assert "src/calculator.py" in prompt
        assert "pass the tests" in prompt.lower()
