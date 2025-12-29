#!/usr/bin/env python3
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

import re
import fnmatch
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum


# =============================================================================
# Data Classes
# =============================================================================

class ArchitectureLayer(Enum):
    """Clean Architecture layers."""
    DOMAIN = "Domain"
    APPLICATION = "Application"
    INFRASTRUCTURE = "Infrastructure"
    PRESENTATION = "Presentation"
    UNKNOWN = "Unknown"


@dataclass
class SymbolInfo:
    """Information about a code symbol."""
    name: str
    kind: str
    file_path: str
    line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "location": f"{self.file_path}:{self.line}",
        }


@dataclass
class FileContext:
    """Context for a single file."""
    path: str
    language: str
    content: str
    layer: str = "Unknown"
    relevance_score: float = 0.0
    symbols: List[SymbolInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    token_count: int = 0

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "layer": self.layer,
            "relevance_score": round(self.relevance_score, 3),
            "content": self.content,
            "symbols": [{"name": s.name, "kind": s.kind} for s in self.symbols],
        }


@dataclass
class PatternMatch:
    """Detected architectural pattern."""
    name: str
    description: str
    examples: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "examples": self.examples[:3],
        }


@dataclass
class CodeContext:
    """Complete assembled context for LLM consumption."""
    files: List[FileContext] = field(default_factory=list)
    symbols: List[SymbolInfo] = field(default_factory=list)
    patterns: List[PatternMatch] = field(default_factory=list)
    total_tokens: int = 0
    retrieval_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "summary": {
                "total_files": len(self.files),
                "total_symbols": len(self.symbols),
                "total_tokens": self.total_tokens,
            },
            "files": [f.to_dict() for f in self.files],
            "patterns_detected": [p.to_dict() for p in self.patterns],
        }

    def to_yaml(self) -> str:
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def to_prompt_text(self) -> str:
        """Format context for LLM consumption."""
        lines = [
            "# Code Context",
            "",
            f"Retrieved {len(self.files)} files, {len(self.symbols)} symbols ({self.total_tokens} tokens)",
            "",
        ]

        # Group by layer
        by_layer: Dict[str, List[FileContext]] = {}
        for f in self.files:
            layer = f.layer or "Unknown"
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(f)

        # Output in architecture order
        layer_order = ["Domain", "Application", "Infrastructure", "Presentation", "Unknown"]
        for layer in layer_order:
            if layer in by_layer:
                lines.append(f"## {layer} Layer")
                lines.append("")
                for f in by_layer[layer]:
                    lines.append(f"### {f.path}")
                    lines.append("")
                    if f.symbols:
                        lines.append("**Symbols:** " + ", ".join(s.name for s in f.symbols[:5]))
                    lines.append("")
                    lines.append("```" + f.language)
                    lines.append(f.content)
                    lines.append("```")
                    lines.append("")

        # Patterns
        if self.patterns:
            lines.append("## Detected Patterns")
            lines.append("")
            for p in self.patterns:
                lines.append(f"- **{p.name}**: {p.description}")
                if p.examples:
                    lines.append(f"  Examples: {', '.join(p.examples[:3])}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# Context Assembler
# =============================================================================

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

    def _build_layer_patterns(self) -> Dict[str, List[str]]:
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
        # Handle both absolute and relative paths
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
        self, vector_results: List[Any], file_data: Dict[str, Dict[str, Any]]
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

            # Use highest score for file
            file_data[file_path]["score"] = max(
                file_data[file_path]["score"],
                result.score
            )

            # Accumulate content (avoiding duplicates)
            if result.chunk not in file_data[file_path]["content"]:
                if file_data[file_path]["content"]:
                    file_data[file_path]["content"] += "\n\n// ...\n\n"
                file_data[file_path]["content"] += result.chunk

    def _process_lsp_symbols(
        self, lsp_symbols: List[Any], query: str, file_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Process LSP symbols into file_data."""
        if not lsp_symbols:
            return

        query_lower = query.lower()

        for symbol in lsp_symbols:
            file_path = symbol.location.file if hasattr(symbol, 'location') else None
            if not file_path:
                continue

            # Normalize path
            try:
                if Path(file_path).is_absolute():
                    file_path = str(Path(file_path).relative_to(self.project_path))
            except ValueError:
                pass

            if file_path not in file_data:
                file_data[file_path] = {
                    "content": "",
                    "score": 0.0,
                    "symbols": [],
                    "source": "lsp",
                }

            # Boost score for exact symbol matches
            symbol_name = symbol.name.lower() if hasattr(symbol, 'name') else ""
            if symbol_name in query_lower:
                file_data[file_path]["score"] += 0.5

            # Add symbol info
            file_data[file_path]["symbols"].append(SymbolInfo(
                name=symbol.name,
                kind=symbol.kind,
                file_path=file_path,
                line=symbol.location.line if hasattr(symbol.location, 'line') else 0,
            ))

    def _apply_entry_point_boosts(
        self, entry_points: List[str], file_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Boost scores for files matching entry points."""
        if not entry_points:
            return

        for entry in entry_points:
            entry_lower = entry.lower()
            for file_path, data in file_data.items():
                if entry_lower in file_path.lower():
                    data["score"] += 1.0

    def _build_file_contexts(
        self,
        sorted_files: List[tuple],
        budget: int,
        context: CodeContext
    ) -> int:
        """Build FileContext objects within token budget. Returns tokens used."""
        current_tokens = 0
        seen_symbols: Set[str] = set()

        for file_path, data in sorted_files:
            content = data["content"]

            # If no content from vector, try to read file
            if not content:
                try:
                    full_path = self.project_path / file_path
                    if full_path.exists():
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                except Exception:
                    continue

            if not content:
                continue

            tokens = self.estimate_tokens(content)

            # Truncate if needed
            if current_tokens + tokens > budget:
                remaining = budget - current_tokens
                if remaining < 200:
                    continue
                content = self._truncate_content(content, remaining)
                tokens = remaining

            # Create file context
            file_ctx = FileContext(
                path=file_path,
                language=self.detect_language(file_path),
                content=content,
                layer=self.detect_layer(file_path),
                relevance_score=data["score"],
                symbols=data["symbols"],
                token_count=tokens,
            )

            context.files.append(file_ctx)
            current_tokens += tokens

            # Track symbols
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
        lsp_symbols: List[Any] = None,
        vector_results: List[Any] = None,
        entry_points: List[str] = None,
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

        # Phase 1: Collect file data from all sources
        file_data: Dict[str, Dict[str, Any]] = {}
        self._process_vector_results(vector_results, file_data)
        self._process_lsp_symbols(lsp_symbols, query, file_data)
        self._apply_entry_point_boosts(entry_points, file_data)

        # Phase 2: Sort by relevance score
        sorted_files = sorted(
            file_data.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        # Phase 3: Build file contexts within budget
        current_tokens = self._build_file_contexts(sorted_files, budget, context)

        # Phase 4: Detect patterns and finalize
        context.patterns = self._detect_patterns(context)
        context.total_tokens = current_tokens

        return context

    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Truncate content to fit token budget."""
        max_chars = max_tokens * 4
        if len(content) <= max_chars:
            return content

        # Try to truncate at a natural boundary
        truncated = content[:max_chars]
        last_newline = truncated.rfind("\n")
        if last_newline > max_chars * 0.8:
            truncated = truncated[:last_newline]

        return truncated + "\n// ... (truncated)"

    # Pattern definitions for detection
    _PATTERN_DEFS = [
        {
            "name": "Result<T> Pattern",
            "description": "Methods return Result<T> instead of throwing exceptions",
            "content_pattern": r"Result<\w+>|Result\.\w+\(",
            "symbol_filter": lambda s: "Result" in s,
            "confidence": 0.8,
        },
        {
            "name": "Repository Pattern",
            "description": "Data access abstracted through repository interfaces",
            "symbol_filter": lambda s: "Repository" in s,
            "confidence": 0.85,
        },
        {
            "name": "Value Objects",
            "description": "Immutable objects identified by their values",
            "content_pattern": r":\s*ValueObject|record\s+struct|readonly\s+struct",
            "confidence": 0.7,
        },
        {
            "name": "Entity/Aggregate Pattern",
            "description": "Domain entities with identity and lifecycle",
            "content_pattern": r":\s*(?:Entity|AggregateRoot)|class\s+\w+\s*:\s*\w*Entity",
            "symbol_filter": lambda s: bool(re.search(r"Entity$|Aggregate", s)),
            "confidence": 0.8,
        },
        {
            "name": "Mediator/Handler Pattern",
            "description": "Request handlers via MediatR or similar",
            "content_pattern": r"IRequestHandler|INotificationHandler",
            "symbol_filter": lambda s: "Handler" in s,
            "confidence": 0.85,
        },
        {
            "name": "Specification Pattern",
            "description": "Business rules encapsulated in specification objects",
            "content_pattern": r"Specification<|ISpecification",
            "symbol_filter": lambda s: "Specification" in s or "Spec" in s,
            "confidence": 0.8,
        },
    ]

    def _detect_patterns(self, context: CodeContext) -> List[PatternMatch]:
        """Detect architectural patterns in the assembled context."""
        all_content = "\n".join(f.content for f in context.files)
        all_symbols = [s.name for s in context.symbols]

        patterns = []

        # Check each pattern definition
        for pdef in self._PATTERN_DEFS:
            content_match = False
            symbol_examples = []

            # Check content pattern if defined
            if "content_pattern" in pdef:
                content_match = bool(re.search(pdef["content_pattern"], all_content))

            # Check symbol filter if defined
            if "symbol_filter" in pdef:
                symbol_examples = [s for s in all_symbols if pdef["symbol_filter"](s)][:3]

            # Pattern matches if content matches OR symbols found
            if content_match or symbol_examples:
                patterns.append(PatternMatch(
                    name=pdef["name"],
                    description=pdef["description"],
                    examples=symbol_examples,
                    confidence=pdef["confidence"],
                ))

        # Special case: CQRS (needs both commands and queries check)
        commands = [s for s in all_symbols if s.endswith("Command")]
        queries = [s for s in all_symbols if s.endswith("Query")]
        if commands or queries:
            patterns.append(PatternMatch(
                name="CQRS Pattern",
                description="Commands and Queries are separate types",
                examples=commands[:2] + queries[:2],
                confidence=0.9,
            ))

        return patterns

    def assemble_from_files(
        self,
        file_paths: List[str],
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
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
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
    import yaml

    parser = argparse.ArgumentParser(description="Test context assembler")
    parser.add_argument("--project", "-p", required=True, help="Project root path")
    parser.add_argument("--files", "-f", nargs="+", help="Specific files to include")
    parser.add_argument("--budget", "-b", type=int, default=6000, help="Token budget")

    args = parser.parse_args()

    assembler = ContextAssembler(args.project)

    if args.files:
        context = assembler.assemble_from_files(args.files, args.budget)
    else:
        # Demo with no input
        context = CodeContext()
        print("No files specified. Use --files to provide file paths.")
        return

    print(context.to_prompt_text())


if __name__ == "__main__":
    main()
