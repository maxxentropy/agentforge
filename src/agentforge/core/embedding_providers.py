#!/usr/bin/env python3
"""
Embedding Providers
===================

Pluggable embedding providers for vector search.
Local provider is default (no API key needed).

Usage:
    provider = get_embedding_provider()  # Auto-selects based on available keys
    provider = get_embedding_provider("local")  # Force local
    provider = get_embedding_provider("openai")  # Force OpenAI

    embeddings = provider.embed(["code chunk 1", "code chunk 2"])

Providers:
    1. LOCAL (default) - sentence-transformers
       - No API key needed
       - Code stays on machine
       - Works offline
       - Good quality (~80MB model download on first use)

    2. OPENAI (optional) - text-embedding-3-small
       - Requires OPENAI_API_KEY
       - Excellent quality
       - ~$0.02/1M tokens

    3. VOYAGE (optional) - voyage-code-2
       - Requires VOYAGE_API_KEY
       - Anthropic's recommended partner
       - Optimized for code
       - ~$0.02/1M tokens
"""

import os
from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    name: str
    dimension: int  # Output embedding dimension

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text chunks to embed

        Returns:
            numpy array of shape (len(texts), dimension)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (dependencies installed, API key set)."""
        pass

    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        pass

    @property
    def install_instructions(self) -> str:
        """Instructions for installing this provider."""
        return ""


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embeddings using sentence-transformers.

    No API key required. Code stays on your machine.

    Models (in order of speed vs quality tradeoff):
    - all-MiniLM-L6-v2: 80MB, fast, good quality (default)
    - all-mpnet-base-v2: 420MB, slower, better quality
    - codeparrot/codebert-base: 420MB, optimized for code
    """

    name = "local"
    dimension = 384  # for all-MiniLM-L6-v2
    requires_api_key = False
    install_instructions = "pip install sentence-transformers"

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model = None

    def _load_model(self):
        """Lazy load model on first use."""
        if self._model is None:
            try:
                import sys

                from sentence_transformers import SentenceTransformer
                print(f"Loading embedding model: {self.model_name}", file=sys.stderr)
                self._model = SentenceTransformer(self.model_name)
                self.dimension = self._model.get_sentence_embedding_dimension()
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers not installed. "
                    f"Install with: {self.install_instructions}"
                ) from e
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        model = self._load_model()
        # show_progress_bar for large batches
        embeddings = model.encode(
            texts,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        return embeddings

    def is_available(self) -> bool:
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            return False


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embeddings using text-embedding-3-small.

    Requires OPENAI_API_KEY environment variable.
    Excellent quality, ~$0.02 per 1M tokens.
    """

    name = "openai"
    dimension = 1536
    requires_api_key = True
    install_instructions = "pip install openai && export OPENAI_API_KEY=your-key"

    MODEL = "text-embedding-3-small"

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI()  # Uses OPENAI_API_KEY env var
            except ImportError as e:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                ) from e
        return self._client

    def embed(self, texts: list[str]) -> np.ndarray:
        client = self._get_client()

        # OpenAI has a limit of 8191 tokens per request, batch if needed
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                model=self.MODEL,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return np.array(all_embeddings)

    def is_available(self) -> bool:
        if not os.environ.get("OPENAI_API_KEY"):
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False


class VoyageEmbeddingProvider(EmbeddingProvider):
    """
    Voyage AI embeddings using voyage-code-2.

    Requires VOYAGE_API_KEY environment variable.
    Anthropic's recommended embedding partner, optimized for code.
    """

    name = "voyage"
    dimension = 1024
    requires_api_key = True
    install_instructions = "pip install voyageai && export VOYAGE_API_KEY=your-key"

    MODEL = "voyage-code-2"

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import voyageai
                self._client = voyageai.Client()  # Uses VOYAGE_API_KEY env var
            except ImportError as e:
                raise ImportError(
                    "voyageai package not installed. "
                    "Install with: pip install voyageai"
                ) from e
        return self._client

    def embed(self, texts: list[str]) -> np.ndarray:
        client = self._get_client()

        # Voyage has batch limits too
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = client.embed(batch, model=self.MODEL)
            all_embeddings.extend(result.embeddings)

        return np.array(all_embeddings)

    def is_available(self) -> bool:
        if not os.environ.get("VOYAGE_API_KEY"):
            return False
        try:
            import voyageai  # noqa: F401
            return True
        except ImportError:
            return False


# Provider registry
PROVIDERS = {
    "local": LocalEmbeddingProvider,
    "openai": OpenAIEmbeddingProvider,
    "voyage": VoyageEmbeddingProvider,
}


def get_embedding_provider(provider_name: str = None, config: dict = None) -> EmbeddingProvider:
    """
    Get an embedding provider.

    Args:
        provider_name: Specific provider to use ("local", "openai", "voyage")
                      If None, auto-selects based on availability.
        config: Optional config dict with provider-specific settings

    Returns:
        EmbeddingProvider instance

    Auto-selection priority:
    1. If VOYAGE_API_KEY set → Voyage (best for code)
    2. If OPENAI_API_KEY set → OpenAI
    3. Otherwise → Local (no API key needed)
    """
    config = config or {}

    if provider_name:
        if provider_name not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}")

        # Create provider with config
        if provider_name == "local":
            model_name = config.get("local", {}).get("model")
            provider = LocalEmbeddingProvider(model_name)
        else:
            provider = PROVIDERS[provider_name]()

        if not provider.is_available():
            raise RuntimeError(
                f"Provider '{provider_name}' is not available.\n"
                f"Install with: {provider.install_instructions}"
            )
        return provider

    # Auto-select based on availability
    # Prefer cloud providers if API key is set (better quality for code)
    import sys
    for name in ["voyage", "openai", "local"]:
        if name == "local":
            model_name = config.get("local", {}).get("model")
            provider = LocalEmbeddingProvider(model_name)
        else:
            provider = PROVIDERS[name]()

        if provider.is_available():
            print(f"Using embedding provider: {name}", file=sys.stderr)
            return provider

    raise RuntimeError(
        "No embedding provider available.\n"
        "Install sentence-transformers for local embeddings:\n"
        "  pip install sentence-transformers"
    )


def list_providers() -> list[dict]:
    """
    List all embedding providers with their status.

    Returns:
        List of dicts with provider info and availability
    """
    result = []
    for name, cls in PROVIDERS.items():
        provider = cls() if name != "local" else LocalEmbeddingProvider()
        result.append({
            "name": name,
            "available": provider.is_available(),
            "requires_api_key": provider.requires_api_key,
            "dimension": provider.dimension,
            "install_instructions": provider.install_instructions,
        })
    return result


def get_available_providers() -> list[str]:
    """List names of all available embedding providers."""
    available = []
    for name, cls in PROVIDERS.items():
        provider = cls() if name != "local" else LocalEmbeddingProvider()
        if provider.is_available():
            available.append(name)
    return available
