"""
LLM Generation Component
========================

Provides LLM-powered code generation for AgentForge workflows.

Components:
    domain: Core entities (GeneratedFile, GenerationResult, GenerationContext)
    provider: LLM provider abstraction (ClaudeProvider, ManualProvider)
    prompt_builder: Context-to-prompt assembly
    parser: Response-to-code extraction
    writer: Atomic file writing with rollback
    engine: Main orchestration

Usage:
    from agentforge.core.generate import GenerationEngine, get_provider

    engine = GenerationEngine(provider=get_provider())
    result = await engine.generate(context)
"""

__all__ = [
    # Domain
    "GeneratedFile",
    "GenerationResult",
    "GenerationContext",
    "GenerationError",
    "APIError",
    "ParseError",
    # Provider
    "LLMProvider",
    "ClaudeProvider",
    "ManualProvider",
    "get_provider",
    # Components
    "PromptBuilder",
    "ResponseParser",
    "CodeWriter",
    "GenerationEngine",
]

# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name in ("GeneratedFile", "GenerationResult", "GenerationContext",
                "GenerationError", "APIError", "ParseError"):
        from agentforge.core.generate.domain import (  # noqa: F401
            APIError,
            GeneratedFile,
            GenerationContext,
            GenerationError,
            GenerationResult,
            ParseError,
        )
        return locals()[name]

    if name in ("LLMProvider", "ClaudeProvider", "ManualProvider", "get_provider"):
        from agentforge.core.generate.provider import (  # noqa: F401
            ClaudeProvider,
            LLMProvider,
            ManualProvider,
            get_provider,
        )
        return locals()[name]

    if name == "PromptBuilder":
        from agentforge.core.generate.prompt_builder import PromptBuilder
        return PromptBuilder

    if name == "ResponseParser":
        from agentforge.core.generate.parser import ResponseParser
        return ResponseParser

    if name == "CodeWriter":
        from agentforge.core.generate.writer import CodeWriter
        return CodeWriter

    if name == "GenerationEngine":
        from agentforge.core.generate.engine import GenerationEngine
        return GenerationEngine

    raise AttributeError(f"module 'tools.generate' has no attribute '{name}'")
