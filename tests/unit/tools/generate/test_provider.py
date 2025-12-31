"""
Tests for LLM Provider Abstraction
==================================
"""

import asyncio
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Configure pytest-asyncio mode
pytest_plugins = ("pytest_asyncio",)

from tools.generate.provider import (
    LLMProvider,
    ClaudeProvider,
    ManualProvider,
    get_provider,
)
from tools.generate.domain import APIError, TokenUsage


# =============================================================================
# ClaudeProvider Tests
# =============================================================================


class TestClaudeProvider:
    """Tests for ClaudeProvider."""

    def test_default_model(self):
        provider = ClaudeProvider(api_key="test-key")
        assert provider.model_name == "claude-sonnet-4-20250514"

    def test_custom_model(self):
        provider = ClaudeProvider(api_key="test-key", model="claude-3-5-haiku-20241022")
        assert provider.model_name == "claude-3-5-haiku-20241022"

    def test_is_available_with_key(self):
        provider = ClaudeProvider(api_key="test-key")
        assert provider.is_available is True

    def test_is_available_without_key(self):
        provider = ClaudeProvider(api_key=None)
        assert provider.is_available is False

    def test_reads_api_key_from_env(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            provider = ClaudeProvider()
            assert provider._api_key == "env-key"

    def test_count_tokens_approximation(self):
        provider = ClaudeProvider(api_key="test-key")
        # ~4 chars per token
        text = "a" * 400
        assert provider.count_tokens(text) == 100

    @pytest.mark.asyncio
    async def test_generate_success(self):
        provider = ClaudeProvider(api_key="test-key")

        # Mock the Anthropic client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated code here")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            text, usage = await provider.generate("Test prompt")

        assert text == "Generated code here"
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50

    @pytest.mark.asyncio
    async def test_generate_no_api_key_raises(self):
        provider = ClaudeProvider(api_key=None)

        with patch.dict(os.environ, {}, clear=True):
            # Remove ANTHROPIC_API_KEY if present
            os.environ.pop("ANTHROPIC_API_KEY", None)

            with pytest.raises(APIError) as exc_info:
                await provider.generate("Test prompt")

            assert "No API key" in str(exc_info.value)
            assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_generate_retries_on_rate_limit(self):
        import anthropic

        provider = ClaudeProvider(api_key="test-key", max_retries=2)

        # First call raises rate limit, second succeeds
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Success")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                anthropic.RateLimitError(
                    message="Rate limited",
                    response=MagicMock(status_code=429),
                    body=None,
                ),
                mock_response,
            ]
        )

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                text, usage = await provider.generate("Test prompt")

        assert text == "Success"
        assert mock_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_fails_on_auth_error(self):
        import anthropic

        provider = ClaudeProvider(api_key="bad-key", max_retries=3)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIStatusError(
                message="Unauthorized",
                response=MagicMock(status_code=401),
                body=None,
            )
        )

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            with pytest.raises(APIError) as exc_info:
                await provider.generate("Test prompt")

            # Should not retry 401 errors
            assert mock_client.messages.create.call_count == 1
            assert exc_info.value.status_code == 401
            assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_generate_retries_on_server_error(self):
        import anthropic

        provider = ClaudeProvider(api_key="test-key", max_retries=2)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIStatusError(
                message="Server error",
                response=MagicMock(status_code=500),
                body=None,
            )
        )

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(APIError) as exc_info:
                    await provider.generate("Test prompt")

        # Should retry on 500 errors
        assert mock_client.messages.create.call_count == 3  # 1 + 2 retries
        assert exc_info.value.retryable is True


# =============================================================================
# ManualProvider Tests
# =============================================================================


class TestManualProvider:
    """Tests for ManualProvider."""

    def test_model_name_is_manual(self):
        provider = ManualProvider()
        assert provider.model_name == "manual"

    def test_is_available_always_true(self):
        provider = ManualProvider()
        assert provider.is_available is True

    def test_count_tokens_approximation(self):
        provider = ManualProvider()
        text = "a" * 400
        assert provider.count_tokens(text) == 100

    def test_default_file_paths(self):
        provider = ManualProvider()
        assert provider._prompt_file == Path(".agentforge/generation_prompt.txt")
        assert provider._response_file == Path(".agentforge/generation_response.txt")

    def test_custom_file_paths(self):
        provider = ManualProvider(
            prompt_file=Path("/custom/prompt.txt"),
            response_file=Path("/custom/response.txt"),
        )
        assert provider._prompt_file == Path("/custom/prompt.txt")
        assert provider._response_file == Path("/custom/response.txt")

    @pytest.mark.asyncio
    async def test_generate_writes_prompt_file(self, tmp_path):
        prompt_file = tmp_path / "prompt.txt"
        response_file = tmp_path / "response.txt"

        provider = ManualProvider(
            prompt_file=prompt_file,
            response_file=response_file,
        )

        # Pre-create response file
        response_file.write_text("Generated response")

        # Mock input() to not block
        with patch("builtins.input", return_value=""):
            text, usage = await provider.generate("Test prompt content")

        assert prompt_file.read_text() == "Test prompt content"
        assert text == "Generated response"

    @pytest.mark.asyncio
    async def test_generate_raises_if_no_response_file(self, tmp_path):
        prompt_file = tmp_path / "prompt.txt"
        response_file = tmp_path / "response.txt"

        provider = ManualProvider(
            prompt_file=prompt_file,
            response_file=response_file,
        )

        # Don't create response file

        with patch("builtins.input", return_value=""):
            with pytest.raises(APIError) as exc_info:
                await provider.generate("Test prompt")

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_raises_if_response_empty(self, tmp_path):
        prompt_file = tmp_path / "prompt.txt"
        response_file = tmp_path / "response.txt"

        provider = ManualProvider(
            prompt_file=prompt_file,
            response_file=response_file,
        )

        # Create empty response file
        response_file.write_text("")

        with patch("builtins.input", return_value=""):
            with pytest.raises(APIError) as exc_info:
                await provider.generate("Test prompt")

            assert "empty" in str(exc_info.value).lower()


# =============================================================================
# get_provider Tests
# =============================================================================


class TestGetProvider:
    """Tests for get_provider factory function."""

    def test_returns_claude_provider_with_api_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            provider = get_provider()
            assert isinstance(provider, ClaudeProvider)

    def test_returns_manual_provider_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("tools.generate.provider._load_dotenv_if_needed"):
                provider = get_provider()
                assert isinstance(provider, ManualProvider)

    def test_explicit_api_key_overrides_env(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            provider = get_provider(api_key="explicit-key")
            assert isinstance(provider, ClaudeProvider)
            assert provider._api_key == "explicit-key"

    def test_passes_model_to_claude_provider(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            provider = get_provider(model="claude-3-5-haiku-20241022")
            assert isinstance(provider, ClaudeProvider)
            assert provider.model_name == "claude-3-5-haiku-20241022"
