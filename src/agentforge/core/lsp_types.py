#!/usr/bin/env python3
"""
LSP Data Types
==============

Data classes and enums for LSP communication.

Extracted from lsp_adapter.py for modularity.
"""

from dataclasses import dataclass, field
from enum import IntEnum


@dataclass
class Location:
    """Source code location."""
    file: str
    line: int  # 0-based (LSP convention)
    column: int  # 0-based
    end_line: int | None = None
    end_column: int | None = None

    def to_1based(self) -> 'Location':
        """Convert to 1-based line numbers (editor convention)."""
        return Location(
            file=self.file,
            line=self.line + 1,
            column=self.column + 1,
            end_line=self.end_line + 1 if self.end_line is not None else None,
            end_column=self.end_column + 1 if self.end_column is not None else None,
        )

    def __str__(self):
        loc = self.to_1based()
        return f"{loc.file}:{loc.line}:{loc.column}"


class SymbolKind(IntEnum):
    """LSP Symbol kinds."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26

    @classmethod
    def to_string(cls, kind: int) -> str:
        """Convert numeric kind to string."""
        kind_map = {
            1: "file", 2: "module", 3: "namespace", 4: "package",
            5: "class", 6: "method", 7: "property", 8: "field",
            9: "constructor", 10: "enum", 11: "interface", 12: "function",
            13: "variable", 14: "constant", 15: "string", 16: "number",
            17: "boolean", 18: "array", 19: "object", 20: "key",
            21: "null", 22: "enum_member", 23: "struct", 24: "event",
            25: "operator", 26: "type_parameter",
        }
        return kind_map.get(kind, f"unknown({kind})")


@dataclass
class Symbol:
    """A code symbol (class, method, property, etc.)."""
    name: str
    kind: str  # class, method, property, field, interface, enum, etc.
    location: Location
    container: str | None = None  # Parent class/namespace
    detail: str | None = None  # Type signature
    children: list['Symbol'] = field(default_factory=list)

    def __str__(self):
        if self.container:
            return f"{self.container}.{self.name} ({self.kind})"
        return f"{self.name} ({self.kind})"


@dataclass
class Diagnostic:
    """Compiler error/warning."""
    file: str
    line: int
    column: int
    severity: str  # error, warning, info, hint
    message: str
    code: str | None = None
    source: str | None = None


@dataclass
class HoverInfo:
    """Hover information for a symbol."""
    contents: str  # Markdown formatted
    range: Location | None = None
