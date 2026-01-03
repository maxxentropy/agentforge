# @spec_file: .agentforge/specs/core-generate-v1.yaml
# @spec_id: core-generate-v1
# @component_id: tools-generate-writer
# @impl_path: tools/generate/writer.py

"""
Tests for Generation Engine
============================
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentforge.core.generate.domain import (
    APIError,
    GenerationContext,
    GenerationPhase,
    TokenUsage,
)
from agentforge.core.generate.engine import (
    GenerationEngine,
    GenerationSession,
    generate_code,
)
from agentforge.core.generate.prompt_builder import PromptBuilder
from agentforge.core.generate.provider import LLMProvider

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    provider = MagicMock(spec=LLMProvider)
    provider.model_name = "test-model"
    provider.is_available = True

    # Default successful response
    response = '''Here's the implementation:

```python:src/module.py
def hello():
    return "world"
```
'''
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
    provider.generate = AsyncMock(return_value=(response, usage))

    return provider


@pytest.fixture
def mock_prompt_builder():
    """Create a mock prompt builder."""
    builder = MagicMock(spec=PromptBuilder)
    builder.build.return_value = "Mock prompt content"
    return builder


@pytest.fixture
def sample_context():
    """Create a sample generation context."""
    return GenerationContext(
        spec={"name": "TestComponent", "methods": []},
        phase=GenerationPhase.RED,
    )


# =============================================================================
# GenerationEngine Basic Tests
# =============================================================================


class TestGenerationEngineBasic:
    """Basic engine tests."""

    @pytest.fixture
    def engine(self, mock_provider, tmp_path):
        return GenerationEngine(
            provider=mock_provider,
            project_root=tmp_path,
        )

    @pytest.mark.asyncio
    async def test_generate_success(self, engine, sample_context, tmp_path):
        result = await engine.generate(sample_context)

        assert result.success is True, "Expected result.success is True"
        assert result.file_count == 1, "Expected result.file_count to equal 1"
        assert result.model == "test-model", "Expected result.model to equal 'test-model'"
        assert (tmp_path / "src/module.py").exists(), "Expected (tmp_path / 'src/module.py'...() to be truthy"

    @pytest.mark.asyncio
    async def test_generate_dry_run(self, engine, sample_context, tmp_path):
        result = await engine.generate(sample_context, dry_run=True)

        assert result.success is True, "Expected result.success is True"
        assert result.file_count == 1, "Expected result.file_count to equal 1"
        # File should NOT be written in dry run
        assert not (tmp_path / "src/module.py").exists(), "Assertion failed"

    @pytest.mark.asyncio
    async def test_generate_records_token_usage(self, engine, sample_context):
        result = await engine.generate(sample_context, dry_run=True)

        assert result.tokens_used == 150, "Expected result.tokens_used to equal 150"
        assert result.prompt_tokens == 100, "Expected result.prompt_tokens to equal 100"
        assert result.completion_tokens == 50, "Expected result.completion_tokens to equal 50"

    @pytest.mark.asyncio
    async def test_generate_records_duration(self, engine, sample_context):
        result = await engine.generate(sample_context, dry_run=True)

        assert result.duration_seconds > 0, "Expected result.duration_seconds > 0"

    @pytest.mark.asyncio
    async def test_generate_includes_explanation(
        self, mock_provider, sample_context, tmp_path
    ):
        # Response with explanation text
        response = '''Here's the test file:

```python:tests/test_module.py
def test_example():
    pass
```

This creates a basic test.'''
        mock_provider.generate = AsyncMock(
            return_value=(response, TokenUsage(100, 50))
        )

        engine = GenerationEngine(provider=mock_provider, project_root=tmp_path)
        result = await engine.generate(sample_context, dry_run=True)

        assert "Here's the test file" in result.explanation, "Expected \"Here's the test file\" in result.explanation"
        assert "creates a basic test" in result.explanation, "Expected 'creates a basic test' in result.explanation"


class TestGenerationEngineErrors:
    """Error handling tests."""

    @pytest.mark.asyncio
    async def test_api_error_returns_failure(self, sample_context, tmp_path):
        provider = MagicMock(spec=LLMProvider)
        provider.model_name = "test-model"
        provider.generate = AsyncMock(
            side_effect=APIError("Rate limited", status_code=429)
        )

        engine = GenerationEngine(provider=provider, project_root=tmp_path)
        result = await engine.generate(sample_context)

        assert result.success is False, "Expected result.success is False"
        assert "API error" in result.error, "Expected 'API error' in result.error"
        assert "Rate limited" in result.error, "Expected 'Rate limited' in result.error"

    @pytest.mark.asyncio
    async def test_parse_error_returns_failure(self, sample_context, tmp_path):
        provider = MagicMock(spec=LLMProvider)
        provider.model_name = "test-model"
        # Response with no code blocks
        provider.generate = AsyncMock(
            return_value=("No code here", TokenUsage(100, 50))
        )

        engine = GenerationEngine(provider=provider, project_root=tmp_path)
        result = await engine.generate(sample_context)

        assert result.success is False, "Expected result.success is False"
        assert "Parse error" in result.error, "Expected 'Parse error' in result.error"

    @pytest.mark.asyncio
    async def test_write_error_returns_failure(
        self, mock_provider, sample_context, tmp_path
    ):
        # Create a directory where we'll try to write a file
        (tmp_path / "src").mkdir()
        (tmp_path / "src/module.py").mkdir()  # Make it a directory

        engine = GenerationEngine(provider=mock_provider, project_root=tmp_path)
        result = await engine.generate(sample_context)

        assert result.success is False, "Expected result.success is False"
        assert "Write error" in result.error, "Expected 'Write error' in result.error"

    @pytest.mark.asyncio
    async def test_parse_error_includes_raw_response(self, sample_context, tmp_path):
        provider = MagicMock(spec=LLMProvider)
        provider.model_name = "test-model"
        provider.generate = AsyncMock(
            return_value=("Invalid response without code", TokenUsage(100, 50))
        )

        engine = GenerationEngine(provider=provider, project_root=tmp_path)
        result = await engine.generate(sample_context)

        assert result.raw_response is not None, "Expected result.raw_response is not None"


class TestGenerationEngineSync:
    """Synchronous interface tests."""

    def test_generate_sync(self, mock_provider, sample_context, tmp_path):
        engine = GenerationEngine(provider=mock_provider, project_root=tmp_path)
        result = engine.generate_sync(sample_context, dry_run=True)

        assert result.success is True, "Expected result.success is True"
        assert result.file_count == 1, "Expected result.file_count to equal 1"


# =============================================================================
# GenerationSession Tests
# =============================================================================


class TestGenerationSession:
    """Session management tests."""

    @pytest.fixture
    def mock_engine(self, mock_provider, tmp_path):
        return GenerationEngine(provider=mock_provider, project_root=tmp_path)

    @pytest.mark.asyncio
    async def test_run_red(self, mock_engine, sample_context):
        session = GenerationSession(engine=mock_engine)
        result = await session.run_red(sample_context, dry_run=True)

        assert result.success is True, "Expected result.success is True"
        assert len(session.results) == 1, "Expected len(session.results) to equal 1"

    @pytest.mark.asyncio
    async def test_run_green(self, mock_engine):
        context = GenerationContext(
            spec={"name": "Test"},
            phase=GenerationPhase.GREEN,
            existing_tests="def test_foo(): pass",
        )
        session = GenerationSession(engine=mock_engine)
        result = await session.run_green(context, dry_run=True)

        assert result.success is True, "Expected result.success is True"

    @pytest.mark.asyncio
    async def test_run_refactor(self, mock_engine):
        context = GenerationContext(
            spec={"name": "Test"},
            phase=GenerationPhase.REFACTOR,
            existing_impl="class Foo: pass",
        )
        session = GenerationSession(engine=mock_engine)
        result = await session.run_refactor(context, dry_run=True)

        assert result.success is True, "Expected result.success is True"

    @pytest.mark.asyncio
    async def test_tracks_total_tokens(self, mock_engine, sample_context):
        session = GenerationSession(engine=mock_engine)

        await session.run_red(sample_context, dry_run=True)
        await session.run_green(sample_context, dry_run=True)

        # Each call uses 150 tokens (100 + 50)
        assert session.total_tokens_used == 300, "Expected session.total_tokens_used to equal 300"

    @pytest.mark.asyncio
    async def test_tracks_total_files(self, mock_engine, sample_context):
        session = GenerationSession(engine=mock_engine)

        await session.run_red(sample_context, dry_run=True)
        await session.run_green(sample_context, dry_run=True)

        # Each call generates 1 file
        assert session.total_files_generated == 2, "Expected session.total_files_generated to equal 2"

    @pytest.mark.asyncio
    async def test_all_succeeded_true(self, mock_engine, sample_context):
        session = GenerationSession(engine=mock_engine)

        await session.run_red(sample_context, dry_run=True)
        await session.run_green(sample_context, dry_run=True)

        assert session.all_succeeded is True, "Expected session.all_succeeded is True"

    @pytest.mark.asyncio
    async def test_all_succeeded_false_on_failure(self, sample_context, tmp_path):
        # Engine that fails
        provider = MagicMock(spec=LLMProvider)
        provider.model_name = "test"
        provider.generate = AsyncMock(
            return_value=("no code", TokenUsage(10, 5))
        )
        engine = GenerationEngine(provider=provider, project_root=tmp_path)

        session = GenerationSession(engine=engine)
        await session.run_red(sample_context, dry_run=True)

        assert session.all_succeeded is False, "Expected session.all_succeeded is False"

    @pytest.mark.asyncio
    async def test_summary(self, mock_engine, sample_context):
        session = GenerationSession(engine=mock_engine)

        await session.run_red(sample_context, dry_run=True)
        await session.run_green(sample_context, dry_run=True)

        summary = session.summary()
        assert "2" in summary, "Expected '2' in summary"# 2 steps
        assert "succeeded" in summary, "Expected 'succeeded' in summary"
        assert "Files" in summary, "Expected 'Files' in summary"
        assert "Tokens" in summary, "Expected 'Tokens' in summary"


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_generate_code(self, mock_provider, sample_context, tmp_path):
        with patch("agentforge.core.generate.engine.get_provider", return_value=mock_provider):
            result = await generate_code(
                sample_context,
                dry_run=True,
                project_root=tmp_path,
            )

        assert result.success is True, "Expected result.success is True"


# =============================================================================
# Integration Tests
# =============================================================================


class TestEngineIntegration:
    """Integration tests with real components (except provider)."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        # Create a mock provider with realistic response
        provider = MagicMock(spec=LLMProvider)
        provider.model_name = "claude-test"
        provider.generate = AsyncMock(
            return_value=(
                '''I'll create the test file:

```python:tests/test_calculator.py
import pytest

def test_add():
    """Test addition."""
    assert 1 + 1 == 2

def test_subtract():
    """Test subtraction."""
    assert 5 - 3 == 2
```

These tests verify basic arithmetic operations.''',
                TokenUsage(prompt_tokens=500, completion_tokens=100),
            )
        )

        # Create engine with real components
        engine = GenerationEngine(provider=provider, project_root=tmp_path)

        # Run generation
        context = GenerationContext.for_red(
            spec={
                "name": "Calculator",
                "components": [
                    {
                        "name": "Calculator",
                        "test_file": "tests/test_calculator.py",
                        "methods": [
                            {"name": "add", "behavior": "adds numbers"},
                            {"name": "subtract", "behavior": "subtracts numbers"},
                        ],
                    }
                ],
            },
            component_name="Calculator",
        )

        result = await engine.generate(context)

        # Verify success
        assert result.success is True, "Expected result.success is True"
        assert result.file_count == 1, "Expected result.file_count to equal 1"
        assert result.tokens_used == 600, "Expected result.tokens_used to equal 600"

        # Verify file was written
        test_file = tmp_path / "tests/test_calculator.py"
        assert test_file.exists(), "Expected test_file.exists() to be truthy"

        content = test_file.read_text()
        assert "test_add" in content, "Expected 'test_add' in content"
        assert "test_subtract" in content, "Expected 'test_subtract' in content"

    @pytest.mark.asyncio
    async def test_multi_file_generation(self, tmp_path):
        provider = MagicMock(spec=LLMProvider)
        provider.model_name = "claude-test"
        provider.generate = AsyncMock(
            return_value=(
                '''Creating both test and implementation:

```python:tests/test_greeter.py
def test_greet():
    from src.greeter import greet
    assert greet("World") == "Hello, World!"
```

```python:src/greeter.py
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

Done!''',
                TokenUsage(200, 100),
            )
        )

        engine = GenerationEngine(provider=provider, project_root=tmp_path)
        context = GenerationContext(
            spec={"name": "Greeter"},
            phase=GenerationPhase.GREEN,
        )

        result = await engine.generate(context)

        assert result.success is True, "Expected result.success is True"
        assert result.file_count == 2, "Expected result.file_count to equal 2"
        assert (tmp_path / "tests/test_greeter.py").exists(), "Expected (tmp_path / 'tests/test_gre...() to be truthy"
        assert (tmp_path / "src/greeter.py").exists(), "Expected (tmp_path / 'src/greeter.py...() to be truthy"
