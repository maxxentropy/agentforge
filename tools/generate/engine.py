# @spec_file: .agentforge/specs/generate-v1.yaml
# @spec_id: generate-v1
# @component_id: tools-generate-engine
# @test_path: tests/unit/tools/generate/test_engine.py

"""
Generation Engine
==================

Main orchestrator for LLM code generation.
Combines provider, prompt builder, parser, and writer.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional

from tools.generate.domain import (
    GenerationContext,
    GenerationResult,
    GeneratedFile,
    TokenUsage,
    GenerationError,
    APIError,
    ParseError,
    WriteError,
)
from tools.generate.provider import LLMProvider, get_provider
from tools.generate.prompt_builder import PromptBuilder
from tools.generate.parser import ResponseParser
from tools.generate.writer import CodeWriter


class GenerationEngine:
    """
    Main engine for LLM code generation.

    Orchestrates the full generation workflow:
    1. Build prompt from context
    2. Call LLM provider
    3. Parse response into files
    4. Write files to disk
    5. Return result

    Handles errors gracefully at each step with appropriate
    recovery strategies.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        parser: Optional[ResponseParser] = None,
        writer: Optional[CodeWriter] = None,
        project_root: Optional[Path] = None,
    ):
        """
        Initialize generation engine.

        Args:
            provider: LLM provider (defaults to auto-detected)
            prompt_builder: Prompt builder (defaults to new instance)
            parser: Response parser (defaults to new instance)
            writer: Code writer (defaults to new instance)
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.provider = provider or get_provider()
        self.prompt_builder = prompt_builder or PromptBuilder(self.project_root)
        self.parser = parser or ResponseParser(validate_syntax=True)
        self.writer = writer or CodeWriter(
            project_root=self.project_root,
            add_header=True,
            atomic_writes=True,
        )

    async def generate(
        self,
        context: GenerationContext,
        dry_run: bool = False,
        max_tokens: int = 8192,
    ) -> GenerationResult:
        """
        Execute full generation workflow.

        Args:
            context: Generation context with spec, phase, etc.
            dry_run: If True, don't write files (just return what would be generated)
            max_tokens: Maximum tokens for LLM response

        Returns:
            GenerationResult with success/failure and generated files
        """
        start_time = time.time()

        # Set writer metadata for headers
        spec_name = context.spec.get("name", "unknown")
        self.writer.set_metadata(
            spec_name=spec_name,
            phase=context.phase.value,
        )

        try:
            # Step 1: Build prompt
            prompt = self.prompt_builder.build(context)

            # Step 2: Call LLM
            response_text, token_usage = await self._call_llm(prompt, max_tokens)

            # Step 3: Parse response
            files, explanation = self._parse_response(response_text)

            # Step 4: Write files (unless dry run)
            if not dry_run:
                self._write_files(files)

            # Step 5: Return success
            return GenerationResult.success_result(
                files=files,
                explanation=explanation,
                model=self.provider.model_name,
                token_usage=token_usage,
                duration_seconds=time.time() - start_time,
                raw_response=response_text,
            )

        except APIError as e:
            return GenerationResult.failure(
                error=f"API error: {e.message}",
                duration_seconds=time.time() - start_time,
            )

        except ParseError as e:
            return GenerationResult.failure(
                error=f"Parse error: {e.message}",
                raw_response=e.raw_response,
                duration_seconds=time.time() - start_time,
            )

        except WriteError as e:
            return GenerationResult.failure(
                error=f"Write error: {e.message}",
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return GenerationResult.failure(
                error=f"Unexpected error: {str(e)}",
                duration_seconds=time.time() - start_time,
            )

    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int,
    ) -> tuple[str, TokenUsage]:
        """
        Call LLM provider with retry handling.

        Args:
            prompt: Prompt to send
            max_tokens: Maximum response tokens

        Returns:
            Tuple of (response text, token usage)

        Raises:
            APIError: If all retries fail
        """
        return await self.provider.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.0,  # Deterministic for code generation
        )

    def _parse_response(
        self,
        response: str,
    ) -> tuple[list[GeneratedFile], str]:
        """
        Parse LLM response into files and explanation.

        Args:
            response: Raw LLM response

        Returns:
            Tuple of (files, explanation)

        Raises:
            ParseError: If parsing fails
        """
        return self.parser.parse_with_explanation(response)

    def _write_files(self, files: list[GeneratedFile]) -> None:
        """
        Write generated files to disk.

        Args:
            files: Files to write

        Raises:
            WriteError: If writing fails (with automatic rollback)
        """
        self.writer.write(files)
        self.writer.clear_history()  # Clear after successful write

    def generate_sync(
        self,
        context: GenerationContext,
        dry_run: bool = False,
        max_tokens: int = 8192,
    ) -> GenerationResult:
        """
        Synchronous wrapper for generate().

        Convenience method for non-async contexts.
        """
        return asyncio.run(self.generate(context, dry_run, max_tokens))


class GenerationSession:
    """
    Manages a multi-step generation session.

    Useful for iterative generation (RED -> GREEN -> REFACTOR)
    with shared context and history.
    """

    def __init__(
        self,
        engine: Optional[GenerationEngine] = None,
        project_root: Optional[Path] = None,
    ):
        """
        Initialize generation session.

        Args:
            engine: Generation engine (creates new if not provided)
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.engine = engine or GenerationEngine(project_root=self.project_root)
        self.results: list[GenerationResult] = []
        self._total_tokens = 0

    async def run_red(
        self,
        context: GenerationContext,
        dry_run: bool = False,
    ) -> GenerationResult:
        """
        Run RED phase (test generation).

        Args:
            context: Generation context (should have phase=RED)
            dry_run: Don't write files if True

        Returns:
            GenerationResult
        """
        result = await self.engine.generate(context, dry_run=dry_run)
        self._record_result(result)
        return result

    async def run_green(
        self,
        context: GenerationContext,
        dry_run: bool = False,
    ) -> GenerationResult:
        """
        Run GREEN phase (implementation).

        Args:
            context: Generation context (should have phase=GREEN)
            dry_run: Don't write files if True

        Returns:
            GenerationResult
        """
        result = await self.engine.generate(context, dry_run=dry_run)
        self._record_result(result)
        return result

    async def run_refactor(
        self,
        context: GenerationContext,
        dry_run: bool = False,
    ) -> GenerationResult:
        """
        Run REFACTOR phase.

        Args:
            context: Generation context (should have phase=REFACTOR)
            dry_run: Don't write files if True

        Returns:
            GenerationResult
        """
        result = await self.engine.generate(context, dry_run=dry_run)
        self._record_result(result)
        return result

    def _record_result(self, result: GenerationResult) -> None:
        """Record result and update totals."""
        self.results.append(result)
        if result.token_usage:
            self._total_tokens += result.token_usage.total_tokens

    @property
    def total_tokens_used(self) -> int:
        """Total tokens used across all generations."""
        return self._total_tokens

    @property
    def total_files_generated(self) -> int:
        """Total files generated across all generations."""
        return sum(r.file_count for r in self.results if r.success)

    @property
    def all_succeeded(self) -> bool:
        """Whether all generation steps succeeded."""
        return all(r.success for r in self.results)

    def summary(self) -> str:
        """Generate session summary."""
        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful

        return (
            f"Generation Session Summary:\n"
            f"  Steps: {len(self.results)} ({successful} succeeded, {failed} failed)\n"
            f"  Files: {self.total_files_generated}\n"
            f"  Tokens: {self.total_tokens_used}\n"
        )


async def generate_code(
    context: GenerationContext,
    dry_run: bool = False,
    project_root: Optional[Path] = None,
) -> GenerationResult:
    """
    Convenience function for one-shot code generation.

    Args:
        context: Generation context
        dry_run: Don't write files if True
        project_root: Project root directory

    Returns:
        GenerationResult
    """
    engine = GenerationEngine(project_root=project_root)
    return await engine.generate(context, dry_run=dry_run)


def generate_code_sync(
    context: GenerationContext,
    dry_run: bool = False,
    project_root: Optional[Path] = None,
) -> GenerationResult:
    """
    Synchronous convenience function for one-shot code generation.

    Args:
        context: Generation context
        dry_run: Don't write files if True
        project_root: Project root directory

    Returns:
        GenerationResult
    """
    return asyncio.run(generate_code(context, dry_run, project_root))
