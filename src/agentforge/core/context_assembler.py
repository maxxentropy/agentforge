#!/usr/bin/env python3

# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-context_assembler
# @test_path: tests/unit/tools/test_context_retrieval.py

"""
Context Assembler
=================

Merges structural (LSP) and semantic (Vector) retrieval results.
Enforces token budget with intelligent prioritization.

Strategy:
1. LSP: Get precise structural information (symbols, definitions, references)
2. Vector: Get semantically related code chunks
3. Merge: Combine results, deduplicate, rank by relevance
4. Budget: Truncate to fit token limit with priority ordering

Priority Order:
1. Exact symbol matches from query
2. High-relevance vector results
3. Definitions of referenced symbols
4. Related code from same layer
"""

import fnmatch
from pathlib import Path
from typing import Any

try:
    from .context_assembler_types import (
        ArchitectureLayer,
        CodeContext,
        FileContext,
        PatternMatch,
        SymbolInfo,
    )
    from .context_patterns import detect_patterns
except ImportError:
    from context_assembler_types import (
        ArchitectureLayer,
        CodeContext,
        FileContext,
        PatternMatch,
        SymbolInfo,
    )
    from context_patterns import detect_patterns

# Re-export types for backwards compatibility
__all__ = [
    'ArchitectureLayer', 'SymbolInfo', 'FileContext', 'PatternMatch',
    'CodeContext', 'ContextAssembler'
]


class ContextAssembler:
    """
    Assembles final context from multiple retrieval sources.

    Combines LSP (structural) and Vector (semantic) results,
    manages token budget, and formats for LLM consumption.
    """

    def __init__(self, project_path: str, config: dict = None):
        """
        Initialize assembler.

        Args:
            project_path: Root of the codebase
            config: Optional configuration
        """
        self.project_path = Path(project_path).resolve()
        self.config = config or {}

        # Budget settings
        budget_config = self.config.get("retrieval", {}).get("budget", {})
        self.default_budget = budget_config.get("default_tokens", 6000)
        self.max_budget = budget_config.get("max_tokens", 12000)

        # Layer detection patterns
        self._layer_patterns = self._build_layer_patterns()

    def _build_layer_patterns(self) -> dict[str, list[str]]:
        """Build patterns for detecting architectural layers."""
        layer_config = self.config.get("layer_detection", {}).get("patterns", {})

        default_patterns = {
            "Domain": [
                "**/Domain/**", "**/Entities/**", "**/Core/**",
                "**/Models/**", "**/ValueObjects/**",
            ],
            "Application": [
                "**/Application/**", "**/UseCases/**", "**/Services/**",
                "**/Commands/**", "**/Queries/**", "**/Handlers/**",
            ],
            "Infrastructure": [
                "**/Infrastructure/**", "**/Persistence/**", "**/External/**",
                "**/Data/**", "**/Repositories/**",
            ],
            "Presentation": [
                "**/Presentation/**", "**/Api/**", "**/Controllers/**",
                "**/Web/**", "**/UI/**",
            ],
        }

        # Merge with config
        for layer, patterns in layer_config.items():
            if layer in default_patterns:
                default_patterns[layer].extend(patterns)
            else:
                default_patterns[layer] = patterns

        return default_patterns

    def detect_layer(self, file_path: str) -> str:
        """Detect which architectural layer a file belongs to."""
        try:
            if Path(file_path).is_absolute():
                rel_path = str(Path(file_path).relative_to(self.project_path))
            else:
                rel_path = file_path
        except ValueError:
            rel_path = file_path

        for layer, patterns in self._layer_patterns.items():
            for pattern in patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    return layer

        return "Unknown"

    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".cs": "csharp",
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "text")

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (~4 chars per token)."""
        return len(text) // 4

    def _process_vector_results(
        self, vector_results: list[Any], file_data: dict[str, dict[str, Any]]
    ) -> None:
        """Process vector search results into file_data."""
        if not vector_results:
            return

        for result in vector_results:
            file_path = result.file_path
            if file_path not in file_data:
                file_data[file_path] = {
                    "content": "",
                    "score": 0.0,
                    "symbols": [],
                    "source": "vector",
                }

            file_data[file_path]["score"] = max(
                file_data[file_path]["score"],
                result.score
            )

            if result.chunk not in file_data[file_path]["content"]:
                if file_data[file_path]["content"]:
                    file_data[file_path]["content"] += "\n\n// ...\n\n"
                file_data[file_path]["content"] += result.chunk

    def _process_lsp_symbols(
        self, lsp_symbols: list[Any], query: str, file_data: dict[str, dict[str, Any]]
    ) -> None:
        """Process LSP symbols into file_data."""
        if not lsp_symbols:
            return

        query_lower = query.lower()

        for symbol in lsp_symbols:
            loc = getattr(symbol, 'location', None)
            file_path = getattr(loc, 'file', None) if loc else None
            if not file_path:
                continue

            # Normalize absolute paths to relative
            p = Path(file_path)
            if p.is_absolute() and str(p).startswith(str(self.project_path)):
                file_path = str(p.relative_to(self.project_path))

            file_data.setdefault(file_path, {"content": "", "score": 0.0, "symbols": [], "source": "lsp"})

            symbol_name = getattr(symbol, 'name', '').lower()
            if symbol_name and symbol_name in query_lower:
                file_data[file_path]["score"] += 0.5

            file_data[file_path]["symbols"].append(SymbolInfo(
                name=getattr(symbol, 'name', ''), kind=getattr(symbol, 'kind', ''),
                file_path=file_path, line=getattr(loc, 'line', 0) if loc else 0,
            ))

    def _apply_entry_point_boosts(
        self, entry_points: list[str], file_data: dict[str, dict[str, Any]]
    ) -> None:
        """Boost scores for files matching entry points."""
        if not entry_points:
            return

        for entry in entry_points:
            entry_lower = entry.lower()
            for file_path, data in file_data.items():
                if entry_lower in file_path.lower():
                    data["score"] += 1.0

    def _get_file_content(self, file_path: str, cached_content: str) -> str:
        """Get file content, loading from disk if not cached."""
        if cached_content:
            return cached_content
        try:
            full_path = self.project_path / file_path
            if full_path.exists():
                with open(full_path, encoding='utf-8', errors='replace') as f:
                    return f.read()
        except Exception:
            pass
        return ""

    def _fit_content_to_budget(self, content: str, current_tokens: int, budget: int):
        """Fit content to remaining budget. Returns (content, tokens) or (None, 0) if doesn't fit."""
        tokens = self.estimate_tokens(content)

        if current_tokens + tokens <= budget:
            return content, tokens

        remaining = budget - current_tokens
        if remaining < 200:
            return None, 0

        return self._truncate_content(content, remaining), remaining

    def _build_file_contexts(
        self,
        sorted_files: list[tuple],
        budget: int,
        context: CodeContext
    ) -> int:
        """Build FileContext objects within token budget. Returns tokens used."""
        current_tokens = 0
        seen_symbols: set[str] = set()

        for file_path, data in sorted_files:
            content = self._get_file_content(file_path, data["content"])
            if not content:
                continue

            content, tokens = self._fit_content_to_budget(content, current_tokens, budget)
            if content is None:
                continue

            context.files.append(FileContext(
                path=file_path,
                language=self.detect_language(file_path),
                content=content,
                layer=self.detect_layer(file_path),
                relevance_score=data["score"],
                symbols=data["symbols"],
                token_count=tokens,
            ))
            current_tokens += tokens

            for sym in data["symbols"]:
                if sym.name not in seen_symbols:
                    context.symbols.append(sym)
                    seen_symbols.add(sym.name)

            if current_tokens >= budget:
                break

        return current_tokens

    def assemble(
        self,
        query: str,
        lsp_symbols: list[Any] = None,
        vector_results: list[Any] = None,
        entry_points: list[str] = None,
        budget_tokens: int = None,
    ) -> CodeContext:
        """
        Assemble context from multiple sources.

        Args:
            query: Natural language query
            lsp_symbols: Symbols from LSP adapter
            vector_results: Results from vector search
            entry_points: Specific symbols to include
            budget_tokens: Maximum tokens to return

        Returns:
            Assembled CodeContext
        """
        budget = min(budget_tokens or self.default_budget, self.max_budget)

        context = CodeContext()
        context.retrieval_metadata = {
            "query": query,
            "budget_tokens": budget,
            "lsp_results": len(lsp_symbols) if lsp_symbols else 0,
            "vector_results": len(vector_results) if vector_results else 0,
        }

        file_data: dict[str, dict[str, Any]] = {}
        self._process_vector_results(vector_results, file_data)
        self._process_lsp_symbols(lsp_symbols, query, file_data)
        self._apply_entry_point_boosts(entry_points, file_data)

        sorted_files = sorted(
            file_data.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        current_tokens = self._build_file_contexts(sorted_files, budget, context)

        context.patterns = self._detect_patterns(context)
        context.total_tokens = current_tokens

        return context

    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Truncate content to fit token budget."""
        max_chars = max_tokens * 4
        if len(content) <= max_chars:
            return content

        truncated = content[:max_chars]
        last_newline = truncated.rfind("\n")
        if last_newline > max_chars * 0.8:
            truncated = truncated[:last_newline]

        return truncated + "\n// ... (truncated)"

    def _detect_patterns(self, context: CodeContext) -> list[PatternMatch]:
        """Detect architectural patterns in the assembled context."""
        return detect_patterns(context.files, context.symbols)

    def assemble_from_files(
        self,
        file_paths: list[str],
        budget_tokens: int = None,
    ) -> CodeContext:
        """
        Assemble context from explicit file list.

        Useful when you know exactly which files to include.
        """
        budget = min(budget_tokens or self.default_budget, self.max_budget)
        context = CodeContext()
        current_tokens = 0

        for file_path in file_paths:
            try:
                full_path = self.project_path / file_path
                with open(full_path, encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception:
                continue

            tokens = self.estimate_tokens(content)

            if current_tokens + tokens > budget:
                remaining = budget - current_tokens
                if remaining < 200:
                    continue
                content = self._truncate_content(content, remaining)
                tokens = remaining

            file_ctx = FileContext(
                path=file_path,
                language=self.detect_language(file_path),
                content=content,
                layer=self.detect_layer(file_path),
                token_count=tokens,
            )

            context.files.append(file_ctx)
            current_tokens += tokens

            if current_tokens >= budget:
                break

        context.patterns = self._detect_patterns(context)
        context.total_tokens = current_tokens

        return context


# =============================================================================
# CLI for Testing
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test context assembler")
    parser.add_argument("--project", "-p", required=True, help="Project root path")
    parser.add_argument("--files", "-f", nargs="+", help="Specific files to include")
    parser.add_argument("--budget", "-b", type=int, default=6000, help="Token budget")

    args = parser.parse_args()

    assembler = ContextAssembler(args.project)

    if args.files:
        context = assembler.assemble_from_files(args.files, args.budget)
    else:
        context = CodeContext()
        print("No files specified. Use --files to provide file paths.")
        return

    print(context.to_prompt_text())


if __name__ == "__main__":
    main()
