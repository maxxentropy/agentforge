# @spec_file: .agentforge/specs/generate-v1.yaml
# @spec_id: generate-v1
# @component_id: tools-generate-provider
# @test_path: tests/unit/tools/generate/test_engine.py

"""
LLM Provider Abstraction
========================

Abstract base class and implementations for LLM providers.
"""

import asyncio
import os
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from tools.generate.domain import APIError, TokenUsage


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implementations handle specific LLM APIs (Claude, OpenAI, etc.)
    or manual fallback modes.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> Tuple[str, TokenUsage]:
        """
        Generate completion from prompt.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            Tuple of (response text, token usage)

        Raises:
            APIError: If the API call fails
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name being used."""
        pass

    @property
    def is_available(self) -> bool:
        """Check if this provider is available for use."""
        return True


class ClaudeProvider(LLMProvider):
    """
    Claude API provider using the Anthropic SDK.

    Features:
    - Async API calls
    - Automatic retry with exponential backoff
    - Token usage tracking
    - Model selection
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_DELAY = 1.0
    BACKOFF_MULTIPLIER = 2.0
    MAX_DELAY = 30.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (defaults to claude-sonnet-4-20250514)
            max_retries: Maximum retry attempts for transient errors
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._model = model or self.DEFAULT_MODEL
        self._max_retries = max_retries
        self._client = None

    def _get_client(self):
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            import anthropic

            if not self._api_key:
                raise APIError(
                    "No API key provided. Set ANTHROPIC_API_KEY environment variable.",
                    retryable=False,
                )
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    @property
    def model_name(self) -> str:
        """Get the model name being used."""
        return self._model

    @property
    def is_available(self) -> bool:
        """Check if API key is available."""
        return bool(self._api_key)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> Tuple[str, TokenUsage]:
        """
        Generate completion using Claude API.

        Implements retry with exponential backoff for transient errors.
        """
        import anthropic

        client = self._get_client()
        last_error = None
        delay = self.INITIAL_DELAY

        for attempt in range(self._max_retries + 1):
            try:
                response = await client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract response text
                text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text += block.text

                # Build token usage
                usage = TokenUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                )

                return text, usage

            except anthropic.RateLimitError as e:
                last_error = APIError(
                    f"Rate limited: {e}",
                    status_code=429,
                    retryable=True,
                )
            except anthropic.APIStatusError as e:
                # 5xx errors are retryable, 4xx (except 429) are not
                retryable = e.status_code >= 500 or e.status_code == 429
                last_error = APIError(
                    f"API error: {e}",
                    status_code=e.status_code,
                    retryable=retryable,
                )
                if not retryable:
                    raise last_error
            except anthropic.APIConnectionError as e:
                last_error = APIError(
                    f"Connection error: {e}",
                    retryable=True,
                )
            except Exception as e:
                last_error = APIError(
                    f"Unexpected error: {e}",
                    retryable=False,
                )
                raise last_error

            # If we get here, error was retryable
            if attempt < self._max_retries:
                await asyncio.sleep(delay)
                delay = min(delay * self.BACKOFF_MULTIPLIER, self.MAX_DELAY)

        # All retries exhausted
        raise last_error

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses a simple approximation (4 chars per token for English).
        For precise counting, use the tokenizer directly.
        """
        # Rough approximation: ~4 characters per token for English
        # This is sufficient for budget estimation
        return len(text) // 4


class ManualProvider(LLMProvider):
    """
    Manual fallback provider for when no API key is available.

    Writes prompt to a file and reads response from a file,
    allowing the user to manually obtain the LLM response.
    """

    def __init__(
        self,
        prompt_file: Optional[Path] = None,
        response_file: Optional[Path] = None,
    ):
        """
        Initialize manual provider.

        Args:
            prompt_file: Path to write prompts (default: .agentforge/generation_prompt.txt)
            response_file: Path to read responses (default: .agentforge/generation_response.txt)
        """
        self._prompt_file = prompt_file or Path(".agentforge/generation_prompt.txt")
        self._response_file = response_file or Path(
            ".agentforge/generation_response.txt"
        )

    @property
    def model_name(self) -> str:
        """Manual mode doesn't use a specific model."""
        return "manual"

    @property
    def is_available(self) -> bool:
        """Manual mode is always available."""
        return True

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> Tuple[str, TokenUsage]:
        """
        Generate completion via manual intervention.

        1. Writes prompt to file
        2. Instructs user to get response
        3. Reads response from file
        """
        # Ensure directory exists
        self._prompt_file.parent.mkdir(parents=True, exist_ok=True)

        # Write prompt to file
        self._prompt_file.write_text(prompt)

        # Print instructions
        print("\n" + "=" * 60)
        print("MANUAL MODE - No API key configured")
        print("=" * 60)
        print(f"\n1. Prompt saved to: {self._prompt_file.absolute()}")
        print("2. Copy the prompt to Claude (claude.ai or API)")
        print(f"3. Save the response to: {self._response_file.absolute()}")
        print("4. Press Enter to continue...")
        print("=" * 60 + "\n")

        # Wait for user
        await asyncio.get_event_loop().run_in_executor(None, input)

        # Read response
        if not self._response_file.exists():
            raise APIError(
                f"Response file not found: {self._response_file}",
                retryable=False,
            )

        response = self._response_file.read_text()

        if not response.strip():
            raise APIError(
                "Response file is empty",
                retryable=False,
            )

        # Estimate tokens (we don't have exact counts in manual mode)
        usage = TokenUsage(
            prompt_tokens=self.count_tokens(prompt),
            completion_tokens=self.count_tokens(response),
        )

        return response, usage

    def count_tokens(self, text: str) -> int:
        """Estimate token count (~4 chars per token)."""
        return len(text) // 4


def _load_dotenv_if_needed() -> None:
    """Load .env file if API key not already in environment."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return  # Already set, don't override

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed, skip


def get_provider(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMProvider:
    """
    Get the appropriate LLM provider.

    Returns ClaudeProvider if API key is available, otherwise ManualProvider.
    Automatically loads .env file if python-dotenv is available.

    Args:
        model: Model to use (for ClaudeProvider)
        api_key: API key (defaults to ANTHROPIC_API_KEY env var)

    Returns:
        Configured LLMProvider instance
    """
    # Try loading from .env if not already set
    _load_dotenv_if_needed()

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    if key:
        return ClaudeProvider(api_key=key, model=model)
    else:
        return ManualProvider()


def get_provider_sync(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMProvider:
    """
    Synchronous version of get_provider.

    Provided for convenience in non-async contexts.
    """
    return get_provider(model=model, api_key=api_key)
