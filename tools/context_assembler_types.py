#!/usr/bin/env python3
"""
Context Assembler Types
=======================

Data classes for context assembly.

Extracted from context_assembler.py for modularity.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


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
