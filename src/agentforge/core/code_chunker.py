#!/usr/bin/env python3
"""
Code Chunker
============

Splits code into meaningful chunks for embedding.

Strategy:
1. Try to split at function/class boundaries (AST-aware)
2. Fall back to sliding window for non-parseable files
3. Include context (imports, class name) with each chunk

Extracted from vector_search.py for modularity.
"""

import re
from typing import List

try:
    from .vector_types import Chunk
except ImportError:
    from vector_types import Chunk


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
        context = self._extract_context(content, language)

        if language in ("csharp", "python", "typescript", "javascript", "java"):
            chunks = self._chunk_by_structure(file_path, content, context, language)
            if chunks:
                return chunks

        return self._chunk_sliding_window(file_path, content, context, language)

    def _extract_context(self, content: str, language: str) -> str:
        """Extract high-level context from file."""
        context_parts = []

        if language == "csharp":
            ns_match = re.search(r"namespace\s+([\w.]+)", content)
            if ns_match:
                context_parts.append(f"Namespace: {ns_match.group(1)}")
            class_matches = re.findall(r"(?:public|internal)\s+(?:class|interface|record|struct)\s+(\w+)", content)
            if class_matches:
                context_parts.append(f"Types: {', '.join(class_matches[:3])}")

        elif language == "python":
            class_matches = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
            if class_matches:
                context_parts.append(f"Classes: {', '.join(class_matches[:3])}")

        elif language in ("typescript", "javascript"):
            export_matches = re.findall(r"export\s+(?:class|interface|function|const)\s+(\w+)", content)
            if export_matches:
                context_parts.append(f"Exports: {', '.join(export_matches[:3])}")

        return "; ".join(context_parts)

    def _get_boundary_pattern(self, language: str):
        """Get regex pattern for code structure boundaries."""
        if language == "csharp":
            return re.compile(
                r"^\s*(?:public|private|protected|internal)?\s*"
                r"(?:static|virtual|override|abstract|async)?\s*"
                r"(?:class|interface|record|struct|enum|\w+(?:<[^>]+>)?)\s+\w+"
            )
        elif language == "python":
            return re.compile(r"^(?:class|def|async\s+def)\s+\w+")
        elif language in ("typescript", "javascript"):
            return re.compile(
                r"^(?:export\s+)?(?:class|interface|function|const|let)\s+\w+|"
                r"^\s*(?:async\s+)?(?:function|\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]+)\s*=>)"
            )
        return None

    def _chunk_by_structure(self, file_path: str, content: str, context: str, language: str) -> List[Chunk]:
        """Chunk by code structure (functions, classes)."""
        chunks = []
        lines = content.split('\n')

        boundary_pattern = self._get_boundary_pattern(language)
        if boundary_pattern is None:
            return []

        boundaries = [0]
        for i, line in enumerate(lines):
            if boundary_pattern.match(line):
                boundaries.append(i)
        boundaries.append(len(lines))

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            chunk_lines = lines[start:end]
            chunk_content = '\n'.join(chunk_lines)

            if len(chunk_content) < 50:
                continue

            if len(chunk_content) > self.chunk_size_chars * 2:
                sub_chunks = self._chunk_sliding_window(
                    file_path, chunk_content, context, language, start_line_offset=start
                )
                chunks.extend(sub_chunks)
            else:
                chunks.append(Chunk(
                    file_path=file_path, content=chunk_content,
                    start_line=start + 1, end_line=end,
                    context=context, language=language,
                ))

        return chunks

    def _chunk_sliding_window(self, file_path: str, content: str, context: str,
                               language: str, start_line_offset: int = 0) -> List[Chunk]:
        """Chunk using sliding window with overlap."""
        chunks = []
        lines = content.split('\n')

        if len(content) <= self.chunk_size_chars:
            return [Chunk(
                file_path=file_path, content=content,
                start_line=start_line_offset + 1, end_line=start_line_offset + len(lines),
                context=context, language=language,
            )]

        lines_per_chunk = self.chunk_size_chars // 40
        overlap_lines = self.overlap_chars // 40

        i = 0
        while i < len(lines):
            end = min(i + lines_per_chunk, len(lines))
            chunk_lines = lines[i:end]
            chunk_content = '\n'.join(chunk_lines)

            chunks.append(Chunk(
                file_path=file_path, content=chunk_content,
                start_line=start_line_offset + i + 1, end_line=start_line_offset + end,
                context=context, language=language,
            ))

            i += lines_per_chunk - overlap_lines
            if i >= len(lines) - overlap_lines:
                break

        return chunks
