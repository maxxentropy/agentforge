#!/usr/bin/env python3
"""
Vector Search
=============

Semantic code search using embeddings.

Complements LSP's structural queries with "fuzzy" natural language search.
- LSP answers: "where is OrderService defined?"
- Vector answers: "what code is related to discount handling?"

Embedding Providers (auto-selected by priority):
1. LOCAL (default) - sentence-transformers, no API key needed
2. VOYAGE - voyage-code-2, requires VOYAGE_API_KEY
3. OPENAI - text-embedding-3-small, requires OPENAI_API_KEY

Dependencies:
    pip install sentence-transformers faiss-cpu  # Minimal (local embeddings)
    pip install openai                           # Optional (cloud embeddings)
    pip install voyageai                         # Optional (code-optimized)

Usage:
    vs = VectorSearch("/path/to/project")
    vs.index()  # Build index (cached)
    results = vs.search("discount code validation", top_k=10)
"""

import os
import sys
import json
import hashlib
import glob
import fnmatch
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
# Note: pickle removed in favor of JSON for security


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Chunk:
    """A chunk of code for embedding."""
    file_path: str
    content: str
    start_line: int
    end_line: int
    context: str = ""  # Additional context (imports, class name)
    language: str = "text"

    def to_embedding_text(self) -> str:
        """Format chunk for embedding."""
        parts = [f"File: {self.file_path}"]
        if self.context:
            parts.append(f"Context: {self.context}")
        parts.append(self.content)
        return "\n".join(parts)

    @property
    def token_estimate(self) -> int:
        """Rough token estimate."""
        return len(self.to_embedding_text()) // 4

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "context": self.context,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        """Create Chunk from dictionary."""
        return cls(
            file_path=data["file_path"],
            content=data["content"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            context=data.get("context", ""),
            language=data.get("language", "text"),
        )


@dataclass
class SearchResult:
    """A search result from vector search."""
    file_path: str
    chunk: str
    score: float  # Cosine similarity (higher is better)
    start_line: int
    end_line: int
    surrounding_context: str = ""

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "score": round(self.score, 4),
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk": self.chunk,
        }


@dataclass
class IndexStats:
    """Statistics from indexing operation."""
    file_count: int = 0
    chunk_count: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    errors: List[str] = field(default_factory=list)


# =============================================================================
# Code Chunker
# =============================================================================

class CodeChunker:
    """
    Splits code into meaningful chunks for embedding.

    Strategy:
    1. Try to split at function/class boundaries (AST-aware)
    2. Fall back to sliding window for non-parseable files
    3. Include context (imports, class name) with each chunk
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens (~4 chars each)
            overlap: Overlap between chunks in tokens
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunk_size_chars = chunk_size * 4
        self.overlap_chars = overlap * 4

    def chunk_file(self, file_path: str, content: str, language: str = "text") -> List[Chunk]:
        """
        Split file into chunks.

        Args:
            file_path: Path to the file
            content: File content
            language: Programming language

        Returns:
            List of Chunk objects
        """
        # Extract context (imports, namespace, class name)
        context = self._extract_context(content, language)

        # Try AST-aware chunking for known languages
        if language in ("csharp", "python", "typescript", "javascript", "java"):
            chunks = self._chunk_by_structure(file_path, content, context, language)
            if chunks:
                return chunks

        # Fall back to sliding window
        return self._chunk_sliding_window(file_path, content, context, language)

    def _extract_context(self, content: str, language: str) -> str:
        """Extract high-level context from file."""
        context_parts = []

        if language == "csharp":
            # Get namespace
            ns_match = re.search(r"namespace\s+([\w.]+)", content)
            if ns_match:
                context_parts.append(f"Namespace: {ns_match.group(1)}")

            # Get class/interface names
            class_matches = re.findall(r"(?:public|internal)\s+(?:class|interface|record|struct)\s+(\w+)", content)
            if class_matches:
                context_parts.append(f"Types: {', '.join(class_matches[:3])}")

        elif language == "python":
            # Get class names
            class_matches = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
            if class_matches:
                context_parts.append(f"Classes: {', '.join(class_matches[:3])}")

        elif language in ("typescript", "javascript"):
            # Get export names
            export_matches = re.findall(r"export\s+(?:class|interface|function|const)\s+(\w+)", content)
            if export_matches:
                context_parts.append(f"Exports: {', '.join(export_matches[:3])}")

        return "; ".join(context_parts)

    def _chunk_by_structure(
        self,
        file_path: str,
        content: str,
        context: str,
        language: str
    ) -> List[Chunk]:
        """
        Chunk by code structure (functions, classes).

        Uses regex patterns to identify structural boundaries.
        """
        chunks = []
        lines = content.split('\n')

        if language == "csharp":
            # Pattern for method/property/class boundaries
            boundary_pattern = re.compile(
                r"^\s*(?:public|private|protected|internal)?\s*"
                r"(?:static|virtual|override|abstract|async)?\s*"
                r"(?:class|interface|record|struct|enum|\w+(?:<[^>]+>)?)\s+\w+"
            )
        elif language == "python":
            boundary_pattern = re.compile(r"^(?:class|def|async\s+def)\s+\w+")
        elif language in ("typescript", "javascript"):
            boundary_pattern = re.compile(
                r"^(?:export\s+)?(?:class|interface|function|const|let)\s+\w+|"
                r"^\s*(?:async\s+)?(?:function|\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]+)\s*=>)"
            )
        else:
            return []

        # Find boundary lines
        boundaries = [0]
        for i, line in enumerate(lines):
            if boundary_pattern.match(line):
                boundaries.append(i)
        boundaries.append(len(lines))

        # Create chunks from boundaries
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]

            # Extend to include following code until next boundary
            chunk_lines = lines[start:end]
            chunk_content = '\n'.join(chunk_lines)

            # Skip if too small
            if len(chunk_content) < 50:
                continue

            # Split further if too large
            if len(chunk_content) > self.chunk_size_chars * 2:
                sub_chunks = self._chunk_sliding_window(
                    file_path, chunk_content, context, language,
                    start_line_offset=start
                )
                chunks.extend(sub_chunks)
            else:
                chunks.append(Chunk(
                    file_path=file_path,
                    content=chunk_content,
                    start_line=start + 1,  # 1-based
                    end_line=end,
                    context=context,
                    language=language,
                ))

        return chunks

    def _chunk_sliding_window(
        self,
        file_path: str,
        content: str,
        context: str,
        language: str,
        start_line_offset: int = 0
    ) -> List[Chunk]:
        """Chunk using sliding window with overlap."""
        chunks = []
        lines = content.split('\n')

        if len(content) <= self.chunk_size_chars:
            # Small file - single chunk
            return [Chunk(
                file_path=file_path,
                content=content,
                start_line=start_line_offset + 1,
                end_line=start_line_offset + len(lines),
                context=context,
                language=language,
            )]

        # Sliding window by lines
        lines_per_chunk = self.chunk_size_chars // 40  # Rough estimate
        overlap_lines = self.overlap_chars // 40

        i = 0
        while i < len(lines):
            end = min(i + lines_per_chunk, len(lines))
            chunk_lines = lines[i:end]
            chunk_content = '\n'.join(chunk_lines)

            chunks.append(Chunk(
                file_path=file_path,
                content=chunk_content,
                start_line=start_line_offset + i + 1,
                end_line=start_line_offset + end,
                context=context,
                language=language,
            ))

            # Move window
            i += lines_per_chunk - overlap_lines
            if i >= len(lines) - overlap_lines:
                break

        return chunks


# =============================================================================
# Vector Search
# =============================================================================

class VectorSearch:
    """
    Semantic search over codebase using embeddings.

    Uses pluggable embedding providers with local embeddings as default.
    """

    def __init__(self, project_path: str, config: dict = None, provider: str = None):
        """
        Initialize vector search.

        Args:
            project_path: Root of codebase
            config: Optional config with embedding settings, chunk_size, etc.
            provider: Force specific embedding provider ("local", "openai", "voyage")
        """
        self.project_path = Path(project_path).resolve()
        self.config = config or {}

        # Configuration
        self.chunk_size = self.config.get("chunking", {}).get("ast_aware", {}).get("max_chunk_tokens", 500)
        self.chunk_overlap = self.config.get("chunking", {}).get("sliding_window", {}).get("overlap_tokens", 50)

        # Get embedding provider (lazy-loaded on first use)
        self._provider_name = provider or self.config.get("semantic", {}).get("embedding_provider")
        self._embedding_provider = None

        # Index storage - includes provider name (different dimensions need different index)
        index_base = self.config.get("semantic", {}).get("index_path", ".agentforge/vector_index")
        self.index_base = self.project_path / index_base
        self._index_dir = None  # Set when provider is initialized

        # Components
        self.chunker = CodeChunker(self.chunk_size, self.chunk_overlap)
        self._index = None
        self._metadata: List[Chunk] = []

        # File patterns
        self.include_patterns = self.config.get("include_patterns", ["**/*.cs", "**/*.py", "**/*.ts"])
        self.exclude_patterns = self.config.get("exclude_patterns", [
            "**/bin/**", "**/obj/**", "**/node_modules/**", "**/.git/**"
        ])

    @property
    def embedding_provider(self):
        """Lazy-load embedding provider."""
        if self._embedding_provider is None:
            from tools.embedding_providers import get_embedding_provider
            provider_config = self.config.get("semantic", {})
            self._embedding_provider = get_embedding_provider(
                self._provider_name,
                config=provider_config
            )
            # Set index directory based on provider (different dimensions = different index)
            self._index_dir = self.index_base / self._embedding_provider.name
        return self._embedding_provider

    @property
    def index_dir(self) -> Path:
        """Get index directory (depends on provider)."""
        if self._index_dir is None:
            # Initialize provider to get index dir
            _ = self.embedding_provider
        return self._index_dir

    @property
    def index_file(self) -> Path:
        """Path to FAISS index file."""
        return self.index_dir / "index.faiss"

    @property
    def metadata_file(self) -> Path:
        """Path to metadata pickle file."""
        return self.index_dir / "metadata.pkl"

    def _get_files(self) -> List[Path]:
        """Get all files matching include/exclude patterns."""
        all_files = []
        for pattern in self.include_patterns:
            matches = glob.glob(str(self.project_path / pattern), recursive=True)
            all_files.extend(matches)

        # Filter exclusions
        result = []
        for f in all_files:
            if not Path(f).is_file():
                continue

            rel_path = str(Path(f).relative_to(self.project_path))
            excluded = any(
                fnmatch.fnmatch(rel_path, exc)
                for exc in self.exclude_patterns
            )
            if not excluded:
                result.append(Path(f))

        return result

    def _detect_language(self, file_path: str) -> str:
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
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "text")

    def _compute_project_hash(self) -> str:
        """Compute hash of project files for cache invalidation."""
        files = sorted(self._get_files())
        hasher = hashlib.sha256()

        for f in files:
            try:
                stat = f.stat()
                hasher.update(f"{f}:{stat.st_mtime}:{stat.st_size}".encode())
            except Exception:
                continue

        return hasher.hexdigest()[:16]

    def _try_load_cache(self, project_hash: str, stats: IndexStats) -> bool:
        """Try to load index from cache. Returns True if cache was valid."""
        import faiss
        if not self.metadata_file.exists():
            return False
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            if cached.get('project_hash') != project_hash:
                return False
            self._metadata = [Chunk.from_dict(c) for c in cached['chunks']]
            self._index = faiss.read_index(str(self.index_file))
            stats.file_count = cached.get('file_count', 0)
            stats.chunk_count = len(self._metadata)
            stats.duration_ms = 0
            return True
        except Exception:
            return False

    def _chunk_files(self, files: List[Path], stats: IndexStats) -> List[Chunk]:
        """Chunk all files and collect errors."""
        all_chunks = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                language = self._detect_language(str(file_path))
                rel_path = str(file_path.relative_to(self.project_path))
                all_chunks.extend(self.chunker.chunk_file(rel_path, content, language))
            except Exception as e:
                stats.errors.append(f"{file_path}: {e}")
        return all_chunks

    def _build_faiss_index(self, vectors, dimension: int):
        """Build appropriate FAISS index based on dataset size."""
        import faiss
        if len(vectors) < 10000:
            index = faiss.IndexFlatIP(dimension)
        else:
            nlist = min(100, len(vectors) // 10)
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            index.train(vectors)
        index.add(vectors)
        return index

    def _save_index(self, index, chunks: List[Chunk], project_hash: str, file_count: int):
        """Save index and metadata to disk."""
        import faiss
        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.index_file))
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'project_hash': project_hash, 'chunks': [c.to_dict() for c in chunks],
                'file_count': file_count, 'created': datetime.now().isoformat(),
            }, f)

    def index(self, force_rebuild: bool = False) -> IndexStats:
        """Index or re-index the codebase. Creates embeddings for code chunks and stores in FAISS index."""
        import faiss
        import numpy as np

        stats = IndexStats()
        start_time = datetime.now()
        project_hash = self._compute_project_hash()

        if not force_rebuild and self._try_load_cache(project_hash, stats):
            return stats

        files = self._get_files()
        stats.file_count = len(files)
        all_chunks = self._chunk_files(files, stats)
        stats.chunk_count = len(all_chunks)

        if not all_chunks:
            stats.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return stats

        provider = self.embedding_provider
        print(f"  Generating embeddings with '{provider.name}' for {len(all_chunks)} chunks...", file=sys.stderr)
        embeddings = provider.embed([chunk.to_embedding_text() for chunk in all_chunks])

        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        index = self._build_faiss_index(vectors, provider.dimension)

        self._save_index(index, all_chunks, project_hash, stats.file_count)
        self._index = index
        self._metadata = all_chunks

        stats.total_tokens = sum(c.token_estimate for c in all_chunks)
        stats.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return stats

    def _load_index(self) -> bool:
        """Load index from disk if available."""
        if self._index is not None:
            return True

        if not self.index_file.exists():
            return False

        try:
            import faiss
            self._index = faiss.read_index(str(self.index_file))

            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                self._metadata = [Chunk.from_dict(c) for c in cached['chunks']]

            return True

        except Exception:
            return False

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Search for code relevant to query.

        Args:
            query: Natural language query
            top_k: Number of results to return

        Returns:
            List of SearchResult with file, chunk, score, context
        """
        try:
            import faiss
            import numpy as np
        except ImportError:
            raise ImportError("FAISS not installed. Run: pip install faiss-cpu")

        # Load or build index
        if not self._load_index():
            print("Index not found. Building...")
            self.index(force_rebuild=True)

        if self._index is None or not self._metadata:
            return []

        # Get query embedding using same provider
        query_embedding = self.embedding_provider.embed([query])
        query_embedding = np.array(query_embedding, dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        # Search
        k = min(top_k, len(self._metadata))
        scores, indices = self._index.search(query_embedding, k)

        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue

            chunk = self._metadata[idx]
            results.append(SearchResult(
                file_path=chunk.file_path,
                chunk=chunk.content,
                score=float(score),
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                surrounding_context=chunk.context,
            ))

        return results

    def is_indexed(self) -> bool:
        """Check if project is already indexed."""
        return self.index_file.exists() and self.metadata_file.exists()


# =============================================================================
# CLI for Testing
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Vector search for code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a project
  python vector_search.py -p /path/to/project index

  # Search for code
  python vector_search.py -p /path/to/project search "discount code validation"

  # Search with more results
  python vector_search.py -p /path/to/project search "order processing" -k 20
"""
    )

    parser.add_argument("--project", "-p", required=True, help="Project root path")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--provider", choices=["local", "openai", "voyage"],
                        help="Embedding provider (default: auto-select)")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # index command
    idx_parser = subparsers.add_parser("index", help="Index the project")
    idx_parser.add_argument("--force", "-f", action="store_true", help="Force rebuild")

    # search command
    search_parser = subparsers.add_parser("search", help="Search for code")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-k", "--top-k", type=int, default=10, help="Number of results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load config if provided
    config = {}
    if args.config:
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)

    vs = VectorSearch(args.project, config, provider=args.provider)

    try:
        if args.command == "index":
            print(f"Indexing {args.project}...")
            stats = vs.index(force_rebuild=args.force)
            print(f"\nIndex complete:")
            print(f"  Files: {stats.file_count}")
            print(f"  Chunks: {stats.chunk_count}")
            print(f"  Tokens: {stats.total_tokens}")
            print(f"  Duration: {stats.duration_ms}ms")
            if stats.errors:
                print(f"  Errors: {len(stats.errors)}")

        elif args.command == "search":
            if not vs.is_indexed():
                print("Project not indexed. Indexing first...")
                vs.index()

            print(f"Searching: {args.query}")
            results = vs.search(args.query, top_k=args.top_k)

            print(f"\nResults ({len(results)}):")
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r.file_path}:{r.start_line}-{r.end_line} (score: {r.score:.4f})")
                if r.surrounding_context:
                    print(f"   Context: {r.surrounding_context}")
                # Show first few lines
                lines = r.chunk.split('\n')[:5]
                for line in lines:
                    print(f"   {line[:80]}")
                if len(r.chunk.split('\n')) > 5:
                    print("   ...")

    except ImportError as e:
        print(f"\nError: {e}")
        return 1

    except Exception as e:
        print(f"\nError: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
