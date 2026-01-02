#!/usr/bin/env python3
"""
Context Pattern Detection
=========================

Pattern definitions and detection logic for architectural patterns.
Extracted from context_assembler.py for modularity.
"""

import re

try:
    from .context_assembler_types import PatternMatch
except ImportError:
    from context_assembler_types import PatternMatch


# Pattern definitions for detection
PATTERN_DEFS = [
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


def check_pattern_def(pdef: dict, all_content: str, all_symbols: list[str]) -> PatternMatch:
    """Check if a pattern definition matches. Returns PatternMatch or None."""
    content_match = False
    symbol_examples = []

    if "content_pattern" in pdef:
        content_match = bool(re.search(pdef["content_pattern"], all_content))

    if "symbol_filter" in pdef:
        symbol_examples = [s for s in all_symbols if pdef["symbol_filter"](s)][:3]

    if not content_match and not symbol_examples:
        return None

    return PatternMatch(
        name=pdef["name"],
        description=pdef["description"],
        examples=symbol_examples,
        confidence=pdef["confidence"],
    )


def check_cqrs_pattern(all_symbols: list[str]) -> PatternMatch:
    """Check for CQRS pattern. Returns PatternMatch or None."""
    commands = [s for s in all_symbols if s.endswith("Command")]
    queries = [s for s in all_symbols if s.endswith("Query")]

    if not commands and not queries:
        return None

    return PatternMatch(
        name="CQRS Pattern",
        description="Commands and Queries are separate types",
        examples=commands[:2] + queries[:2],
        confidence=0.9,
    )


def detect_patterns(files: list, symbols: list) -> list[PatternMatch]:
    """Detect architectural patterns in assembled context."""
    all_content = "\n".join(f.content for f in files)
    all_symbols = [s.name for s in symbols]

    patterns = []

    for pdef in PATTERN_DEFS:
        match = check_pattern_def(pdef, all_content, all_symbols)
        if match:
            patterns.append(match)

    cqrs = check_cqrs_pattern(all_symbols)
    if cqrs:
        patterns.append(cqrs)

    return patterns
