#!/usr/bin/env python3
"""
Vector Search Types
===================

Data classes for vector search.

Extracted from vector_search.py for modularity.
"""

from dataclasses import dataclass, field


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
    errors: list[str] = field(default_factory=list)
