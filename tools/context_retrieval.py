#!/usr/bin/env python3

# @spec_file: .agentforge/specs/tools-v1.yaml
# @spec_id: tools-v1
# @component_id: tools-context_retrieval
# @test_path: tests/unit/tools/test_context_retrieval.py

"""
Context Retrieval System
========================

Hybrid LSP + Vector retrieval for code context.
Implements "Correctness is Upstream" - agents need real code to write accurate specs.

This is the main entry point that combines:
- LSP: Compiler-accurate structural information (symbols, definitions, references)
- Vector: Semantic similarity search (related code, concepts)

Usage:
    from tools.context_retrieval import ContextRetriever

    retriever = ContextRetriever(project_path="/path/to/project")
    context = retriever.retrieve(
        query="discount code handling",
        budget_tokens=6000
    )

Dependencies:
    Required: pip install pyyaml
    For vector search: pip install openai faiss-cpu
    For C#: dotnet tool install -g csharp-ls
"""

import os
import sys
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Import components
from tools.context_assembler import (
    ContextAssembler,
    CodeContext,
    FileContext,
    SymbolInfo,
    PatternMatch,
)


@dataclass
class IndexStats:
    """Statistics from indexing operation."""
    file_count: int = 0
    chunk_count: int = 0
    symbol_count: int = 0
    duration_ms: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ContextRetriever:
    """
    Main entry point for context retrieval.

    Combines LSP (structural) and Vector (semantic) search to provide
    comprehensive code context for LLM consumption.

    Example:
        retriever = ContextRetriever("/path/to/dotnet/project")
        context = retriever.retrieve("order discount processing", budget_tokens=6000)
        print(context.to_prompt_text())
    """

    def __init__(self, project_path: str, config_path: str = None, provider: str = None):
        """
        Initialize retriever for a project.

        Args:
            project_path: Root of the codebase to analyze
            config_path: Optional path to context_retrieval.yaml
            provider: Force specific embedding provider ("local", "openai", "voyage")
        """
        self.project_path = Path(project_path).resolve()
        self.config_path = config_path
        self.config = self._load_config()
        self.provider = provider

        # Components (lazy-loaded)
        self._lsp_adapter = None
        self._vector_search = None
        self._assembler = None

        # State
        self._lsp_available = None
        self._vector_available = None

    def _load_config(self) -> Dict[str, Any]:
        """Load retrieval configuration."""
        config_paths = [
            self.config_path,
            self.project_path / ".agentforge" / "context_retrieval.yaml",
            self.project_path / "config" / "context_retrieval.yaml",
            Path(__file__).parent.parent / "config" / "context_retrieval.yaml",
        ]

        for path in config_paths:
            if path and Path(path).exists():
                with open(path) as f:
                    return yaml.safe_load(f)

        return {
            "retrieval": {
                "budget": {
                    "default_tokens": 6000,
                    "max_tokens": 12000,
                },
            },
            "filters": {
                "include_patterns": ["**/*.cs", "**/*.py", "**/*.ts"],
                "exclude_patterns": ["**/bin/**", "**/obj/**", "**/node_modules/**"],
            },
        }

    @property
    def assembler(self) -> ContextAssembler:
        """Get or create context assembler."""
        if self._assembler is None:
            self._assembler = ContextAssembler(str(self.project_path), self.config)
        return self._assembler

    @property
    def lsp_adapter(self):
        """Get or create LSP adapter. Returns None if not available."""
        if self._lsp_adapter is None and self._lsp_available is None:
            try:
                from tools.lsp_adapter import get_adapter_for_project, LSPServerNotFound

                adapter = get_adapter_for_project(str(self.project_path))
                adapter.initialize()
                self._lsp_adapter = adapter
                self._lsp_available = True

            except ImportError:
                self._lsp_available = False

            except Exception as e:
                print(f"LSP initialization failed: {e}", file=sys.stderr)
                self._lsp_available = False

        return self._lsp_adapter

    @property
    def vector_search(self):
        """Get or create vector search. Returns None if not available."""
        if self._vector_search is None and self._vector_available is None:
            try:
                from tools.vector_search import VectorSearch

                self._vector_search = VectorSearch(
                    str(self.project_path),
                    self.config.get("semantic", {}),
                    provider=self.provider
                )
                self._vector_available = True

            except ImportError as e:
                print(f"Vector search not available: {e}", file=sys.stderr)
                self._vector_available = False

        return self._vector_search

    def _retrieve_lsp_symbols(self, query: str, entry_points: List[str] = None) -> list:
        """Retrieve symbols via LSP for query keywords and entry points."""
        if not self.lsp_adapter:
            return []
        try:
            symbols = []
            keywords = self._extract_keywords(query)
            for keyword in keywords[:5]:
                symbols.extend(self.lsp_adapter.get_workspace_symbols(keyword))
            if entry_points:
                for entry in entry_points:
                    symbols.extend(self.lsp_adapter.get_workspace_symbols(entry))
            return symbols
        except Exception as e:
            print(f"LSP query failed: {e}", file=sys.stderr)
            return []

    def _retrieve_vector_results(self, query: str) -> list:
        """Retrieve results via vector search."""
        if not self.vector_search:
            return []
        try:
            if not self.vector_search.is_indexed():
                print("Building vector index (first run)...", file=sys.stderr)
                self.vector_search.index()
            return self.vector_search.search(query, top_k=20)
        except Exception as e:
            print(f"Vector search failed: {e}", file=sys.stderr)
            return []

    def retrieve(
        self,
        query: str,
        budget_tokens: int = None,
        entry_points: List[str] = None,
        use_lsp: bool = True,
        use_vector: bool = True,
    ) -> CodeContext:
        """
        Retrieve relevant code context for a query.

        Args:
            query: Natural language description (e.g., "order processing")
            budget_tokens: Maximum tokens to return
            entry_points: Specific symbols to prioritize
            use_lsp: Whether to use LSP for structural queries
            use_vector: Whether to use vector search for semantic queries

        Returns:
            CodeContext with ranked, relevant code snippets
        """
        budget = budget_tokens or self.config.get("retrieval", {}).get("budget", {}).get("default_tokens", 6000)

        lsp_symbols = self._retrieve_lsp_symbols(query, entry_points) if use_lsp else []
        vector_results = self._retrieve_vector_results(query) if use_vector else []

        context = self.assembler.assemble(
            query=query,
            lsp_symbols=lsp_symbols,
            vector_results=vector_results,
            entry_points=entry_points,
            budget_tokens=budget,
        )

        context.retrieval_metadata.update({
            "project_path": str(self.project_path),
            "lsp_enabled": use_lsp and self._lsp_available,
            "vector_enabled": use_vector and self._vector_available,
        })

        return context

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract searchable keywords from query."""
        import re

        stopwords = {
            "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
            "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
            "be", "been", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must", "can",
            "this", "that", "these", "those", "it", "i", "we", "you",
            "what", "which", "who", "how", "when", "where", "why",
            "add", "create", "make", "get", "set", "update", "delete",
            "new", "feature", "implement", "fix", "change",
        }

        words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]*", query)

        keywords = []
        seen = set()
        for word in words:
            lower = word.lower()
            if lower not in stopwords and lower not in seen and len(word) > 2:
                keywords.append(word)
                seen.add(lower)

        return keywords

    def get_symbol_context(self, symbol_name: str) -> Optional[CodeContext]:
        """Get context for a specific symbol using LSP."""
        if not self.lsp_adapter:
            return None

        try:
            symbols = self.lsp_adapter.get_workspace_symbols(symbol_name)
            if not symbols:
                return None

            symbol = None
            for s in symbols:
                if s.name == symbol_name:
                    symbol = s
                    break

            if not symbol:
                symbol = symbols[0]

            refs = []
            if hasattr(symbol, 'location'):
                refs = self.lsp_adapter.get_references(
                    symbol.location.file,
                    symbol.location.line,
                    symbol.location.column,
                )

            files = [symbol.location.file] if hasattr(symbol, 'location') else []
            files.extend(r.file for r in refs[:5])
            files = list(set(files))

            return self.assembler.assemble_from_files(files, budget_tokens=4000)

        except Exception as e:
            print(f"Symbol context failed: {e}", file=sys.stderr)
            return None

    def get_file_context(self, file_path: str) -> Optional[FileContext]:
        """Get full context for a specific file."""
        return self.assembler.assemble_from_files([file_path]).files[0] if file_path else None

    def index(self, force_rebuild: bool = False) -> IndexStats:
        """Index the codebase for faster retrieval."""
        stats = IndexStats()

        if self.vector_search:
            try:
                vs_stats = self.vector_search.index(force_rebuild)
                stats.file_count = vs_stats.file_count
                stats.chunk_count = vs_stats.chunk_count
                stats.duration_ms = vs_stats.duration_ms
                stats.errors.extend(vs_stats.errors)
            except Exception as e:
                stats.errors.append(f"Vector indexing failed: {e}")

        return stats

    def check_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Check availability of retrieval components."""
        status = {
            "lsp": {"available": False, "server": None, "error": None},
            "vector": {"available": False, "indexed": False, "error": None},
        }

        try:
            from tools.lsp_adapter import get_adapter_for_project

            adapter = get_adapter_for_project(str(self.project_path))
            status["lsp"]["server"] = adapter.SERVER_NAME
            status["lsp"]["install_instructions"] = adapter.INSTALL_INSTRUCTIONS

            adapter.initialize()
            status["lsp"]["available"] = True
            adapter.shutdown()

        except ImportError:
            status["lsp"]["error"] = "lsp_adapter module not found"
        except Exception as e:
            status["lsp"]["error"] = str(e)

        try:
            from tools.vector_search import VectorSearch

            vs = VectorSearch(str(self.project_path))
            status["vector"]["available"] = True
            status["vector"]["indexed"] = vs.is_indexed()

        except ImportError as e:
            status["vector"]["error"] = str(e)
        except Exception as e:
            status["vector"]["error"] = str(e)

        return status

    def shutdown(self):
        """Clean up resources."""
        if self._lsp_adapter:
            try:
                self._lsp_adapter.shutdown()
            except Exception:
                pass
            self._lsp_adapter = None


# CLI entry point
if __name__ == "__main__":
    from context_retrieval_cli import main
    sys.exit(main())
