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
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from .vector_types import Chunk, SearchResult, IndexStats
    from .code_chunker import CodeChunker
except ImportError:
    from vector_types import Chunk, SearchResult, IndexStats
    from code_chunker import CodeChunker


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

        self.chunk_size = self.config.get("chunking", {}).get("ast_aware", {}).get("max_chunk_tokens", 500)
        self.chunk_overlap = self.config.get("chunking", {}).get("sliding_window", {}).get("overlap_tokens", 50)

        self._provider_name = provider or self.config.get("semantic", {}).get("embedding_provider")
        self._embedding_provider = None

        index_base = self.config.get("semantic", {}).get("index_path", ".agentforge/vector_index")
        self.index_base = self.project_path / index_base
        self._index_dir = None

        self.chunker = CodeChunker(self.chunk_size, self.chunk_overlap)
        self._index = None
        self._metadata: List[Chunk] = []

        self.include_patterns = self.config.get("include_patterns", ["**/*.cs", "**/*.py", "**/*.ts"])
        self.exclude_patterns = self.config.get("exclude_patterns", [
            "**/bin/**", "**/obj/**", "**/node_modules/**", "**/.git/**"
        ])

    @property
    def embedding_provider(self):
        """Lazy-load embedding provider."""
        if self._embedding_provider is None:
            from agentforge.core.embedding_providers import get_embedding_provider
            provider_config = self.config.get("semantic", {})
            self._embedding_provider = get_embedding_provider(self._provider_name, config=provider_config)
            self._index_dir = self.index_base / self._embedding_provider.name
        return self._embedding_provider

    @property
    def index_dir(self) -> Path:
        """Get index directory (depends on provider)."""
        if self._index_dir is None:
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

        result = []
        for f in all_files:
            if not Path(f).is_file():
                continue
            rel_path = str(Path(f).relative_to(self.project_path))
            excluded = any(fnmatch.fnmatch(rel_path, exc) for exc in self.exclude_patterns)
            if not excluded:
                result.append(Path(f))

        return result

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".cs": "csharp", ".py": "python", ".ts": "typescript", ".tsx": "typescript",
            ".js": "javascript", ".jsx": "javascript", ".java": "java", ".go": "go",
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "text")

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
        """Index or re-index the codebase."""
        import faiss
        import numpy as np

        stats = IndexStats()
        start_time = datetime.now()

        # Compute project hash for cache invalidation
        files = sorted(self._get_files())
        hasher = hashlib.sha256()
        for f in files:
            try:
                stat = f.stat()
                hasher.update(f"{f}:{stat.st_mtime}:{stat.st_size}".encode())
            except Exception:
                continue
        project_hash = hasher.hexdigest()[:16]

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
        """Search for code relevant to query."""
        try:
            import faiss
            import numpy as np
        except ImportError:
            raise ImportError("FAISS not installed. Run: pip install faiss-cpu")

        if not self._load_index():
            print("Index not found. Building...")
            self.index(force_rebuild=True)

        if self._index is None or not self._metadata:
            return []

        query_embedding = self.embedding_provider.embed([query])
        query_embedding = np.array(query_embedding, dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        k = min(top_k, len(self._metadata))
        scores, indices = self._index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            chunk = self._metadata[idx]
            results.append(SearchResult(
                file_path=chunk.file_path, chunk=chunk.content, score=float(score),
                start_line=chunk.start_line, end_line=chunk.end_line,
                surrounding_context=chunk.context,
            ))

        return results

    def is_indexed(self) -> bool:
        """Check if project is already indexed."""
        return self.index_file.exists() and self.metadata_file.exists()


# =============================================================================
# CLI for Testing
# =============================================================================

def _run_index(vs, args):
    """Run index command."""
    print(f"Indexing {args.project}...")
    stats = vs.index(force_rebuild=args.force)
    print(f"\nIndex complete:")
    print(f"  Files: {stats.file_count}")
    print(f"  Chunks: {stats.chunk_count}")
    print(f"  Tokens: {stats.total_tokens}")
    print(f"  Duration: {stats.duration_ms}ms")
    if stats.errors:
        print(f"  Errors: {len(stats.errors)}")


def _run_search(vs, args):
    """Run search command."""
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
        lines = r.chunk.split('\n')[:5]
        for line in lines:
            print(f"   {line[:80]}")
        if len(r.chunk.split('\n')) > 5:
            print("   ...")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Vector search for code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python vector_search.py -p /path/to/project index\n"
               "  python vector_search.py -p /path/to/project search \"discount code validation\""
    )

    parser.add_argument("--project", "-p", required=True, help="Project root path")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--provider", choices=["local", "openai", "voyage"],
                        help="Embedding provider (default: auto-select)")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    idx_parser = subparsers.add_parser("index", help="Index the project")
    idx_parser.add_argument("--force", "-f", action="store_true", help="Force rebuild")

    search_parser = subparsers.add_parser("search", help="Search for code")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-k", "--top-k", type=int, default=10, help="Number of results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    config = {}
    if args.config:
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)

    vs = VectorSearch(args.project, config, provider=args.provider)

    try:
        if args.command == "index":
            _run_index(vs, args)
        elif args.command == "search":
            _run_search(vs, args)
    except ImportError as e:
        print(f"\nError: {e}")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
