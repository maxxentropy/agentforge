#!/usr/bin/env python3

# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-context_assembler_types
# @test_path: tests/unit/tools/test_context_retrieval.py

"""
Context Assembler Types
=======================

Data classes for context assembly.

Extracted from context_assembler.py for modularity.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    signature: str | None = None
    docstring: str | None = None
    parent: str | None = None

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
    symbols: list[SymbolInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
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
    examples: list[str] = field(default_factory=list)
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
    files: list[FileContext] = field(default_factory=list)
    symbols: list[SymbolInfo] = field(default_factory=list)
    patterns: list[PatternMatch] = field(default_factory=list)
    total_tokens: int = 0
    retrieval_metadata: dict[str, Any] = field(default_factory=dict)

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

    def _group_files_by_layer(self) -> dict[str, list["FileContext"]]:
        """Group files by architecture layer."""
        by_layer: dict[str, list[FileContext]] = {}
        for f in self.files:
            layer = f.layer or "Unknown"
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(f)
        return by_layer

    def _format_file_section(self, f: "FileContext") -> list[str]:
        """Format a single file for prompt output."""
        lines = [f"### {f.path}", ""]
        if f.symbols:
            lines.append("**Symbols:** " + ", ".join(s.name for s in f.symbols[:5]))
        lines.extend(["", "```" + f.language, f.content, "```", ""])
        return lines

    def _format_patterns_section(self) -> list[str]:
        """Format patterns section for prompt output."""
        if not self.patterns:
            return []
        lines = ["## Detected Patterns", ""]
        for p in self.patterns:
            lines.append(f"- **{p.name}**: {p.description}")
            if p.examples:
                lines.append(f"  Examples: {', '.join(p.examples[:3])}")
        lines.append("")
        return lines

    def to_prompt_text(self) -> str:
        """Format context for LLM consumption."""
        lines = [
            "# Code Context",
            "",
            f"Retrieved {len(self.files)} files, {len(self.symbols)} symbols ({self.total_tokens} tokens)",
            "",
        ]

        by_layer = self._group_files_by_layer()
        layer_order = ["Domain", "Application", "Infrastructure", "Presentation", "Unknown"]

        for layer in layer_order:
            if layer in by_layer:
                lines.extend([f"## {layer} Layer", ""])
                for f in by_layer[layer]:
                    lines.extend(self._format_file_section(f))

        lines.extend(self._format_patterns_section())

        return "\n".join(lines)
