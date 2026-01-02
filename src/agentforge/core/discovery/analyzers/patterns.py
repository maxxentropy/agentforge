"""
Pattern Analyzer
================

Detects code patterns through multi-signal analysis.
Combines naming conventions, structural analysis, and AST patterns.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..domain import Detection, DetectionSource, PatternDetection
from ..providers.base import LanguageProvider, Symbol

# Pattern definitions with detection signals
PATTERN_DEFINITIONS = {
    "result_type": {
        "description": "Result<T> or similar error handling pattern",
        "signals": {
            "class_name": {
                # Python and C# Result types
                "patterns": [r"^Result$", r"^Result\[", r"^Result<", r"^Either$", r"^Option$", r"^ErrorOr<"],
                "weight": 0.9,
            },
            "return_type": {
                "patterns": [r"Result\[", r"Result$", r"Result<", r"Either\[", r"Option\[", r"ErrorOr<"],
                "weight": 0.8,
            },
            "import": {
                # Python and C# imports
                "patterns": [r"from.*result.*import", r"from.*returns.*import", r"using.*Result", r"using.*ErrorOr"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.5,
    },
    "mediatr_cqrs": {
        "description": "MediatR CQRS pattern (IRequest/IRequestHandler)",
        "signals": {
            "base_class": {
                "patterns": [r"IRequest<", r"IRequest$", r"IRequestHandler<", r"INotification$", r"INotificationHandler<"],
                "weight": 1.0,
            },
            "class_suffix": {
                "patterns": [r"Command$", r"Query$", r"CommandHandler$", r"QueryHandler$"],
                "weight": 0.8,
            },
            "import": {
                "patterns": [r"using MediatR", r"using.*MediatR"],
                "weight": 0.9,
            },
            "directory": {
                "patterns": [r"Commands?", r"Queries?", r"Handlers?"],
                "weight": 0.6,
            },
        },
        "min_confidence": 0.5,
        # At least one of these signals must be present (not just naming)
        "required_signals": ["base_class", "import"],
    },
    "ddd_entity": {
        "description": "DDD Entity pattern with typed ID",
        "signals": {
            "base_class": {
                "patterns": [r"Entity<", r"Entity$", r"AggregateRoot<", r"AggregateRoot$", r"BaseEntity"],
                "weight": 0.9,
            },
            "property": {
                "patterns": [r"public.*Id\s*{", r"protected.*Id\s*{"],
                "weight": 0.6,
            },
            "directory": {
                "patterns": [r"[Ee]ntities", r"[Dd]omain", r"[Aa]ggregates"],
                "weight": 0.5,
            },
        },
        "min_confidence": 0.5,
    },
    "ddd_value_object": {
        "description": "DDD Value Object pattern (immutable, equality by value)",
        "signals": {
            "base_class": {
                "patterns": [r"ValueObject$", r"ValueObject<"],
                "weight": 0.9,
            },
            "class_suffix": {
                "patterns": [r"Id$", r"Email$", r"Address$", r"Money$", r"Name$"],
                "weight": 0.5,
            },
            "attribute": {
                "patterns": [r"record\s+struct", r"readonly\s+struct"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.5,
    },
    "interface_prefix": {
        "description": "I-prefix interface naming convention",
        "signals": {
            "class_name": {
                "patterns": [r"^I[A-Z][a-zA-Z]+$"],
                "weight": 0.9,
            },
        },
        "min_confidence": 0.7,
    },
    "cqrs": {
        "description": "Command Query Responsibility Segregation",
        "signals": {
            "class_suffix": {
                "patterns": [r"Command$", r"Query$", r"Handler$"],
                "weight": 0.8,
            },
            "directory": {
                "patterns": [r"commands?", r"queries?", r"handlers?"],
                "weight": 0.7,
            },
            "base_class": {
                "patterns": [r"ICommand", r"IQuery", r"IRequest", r"BaseCommand", r"BaseQuery"],
                "weight": 0.9,
            },
        },
        "min_confidence": 0.5,
        # Require actual CQRS base classes, not just naming conventions
        "required_signals": ["base_class"],
    },
    "repository": {
        "description": "Repository pattern for data access abstraction",
        "signals": {
            "class_suffix": {
                "patterns": [r"Repository$", r"Repo$"],
                "weight": 0.9,
            },
            "directory": {
                "patterns": [r"repositories", r"repos", r"persistence"],
                "weight": 0.7,
            },
            "method_names": {
                "patterns": [r"get_by_id", r"find_all", r"save", r"delete", r"add"],
                "weight": 0.6,
            },
            "base_class": {
                "patterns": [r"IRepository", r"BaseRepository", r"Repository"],
                "weight": 0.8,
            },
        },
        "min_confidence": 0.5,
    },
    "dependency_injection": {
        "description": "Dependency Injection pattern",
        "signals": {
            "decorator": {
                "patterns": [r"@inject", r"@Inject", r"@autowired"],
                "weight": 0.9,
            },
            "constructor_params": {
                "patterns": [r"__init__.*:.*"],
                "weight": 0.5,
            },
            "import": {
                "patterns": [r"from.*inject.*import", r"from.*dependency_injector"],
                "weight": 0.8,
            },
        },
        "min_confidence": 0.5,
    },
    "factory": {
        "description": "Factory pattern for object creation",
        "signals": {
            "class_suffix": {
                "patterns": [r"Factory$"],
                "weight": 0.9,
            },
            "method_prefix": {
                "patterns": [r"^create_", r"^build_", r"^make_"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.5,
    },
    "singleton": {
        "description": "Singleton pattern",
        "signals": {
            "method_name": {
                "patterns": [r"get_instance", r"getInstance", r"instance"],
                "weight": 0.8,
            },
            "class_variable": {
                "patterns": [r"_instance", r"__instance"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.6,
    },
    "decorator_pattern": {
        "description": "Decorator pattern (not Python decorators)",
        "signals": {
            "class_suffix": {
                "patterns": [r"Decorator$", r"Wrapper$"],
                "weight": 0.9,
            },
            "wrapped_attribute": {
                "patterns": [r"_wrapped", r"_inner", r"_component"],
                "weight": 0.7,
            },
        },
        "min_confidence": 0.6,
    },
    "strategy": {
        "description": "Strategy pattern for interchangeable algorithms",
        "signals": {
            "class_suffix": {
                "patterns": [r"Strategy$", r"Policy$"],
                "weight": 0.9,
            },
            "base_class": {
                "patterns": [r"Strategy", r"Policy", r"ABC"],
                "weight": 0.6,
            },
        },
        "min_confidence": 0.6,
    },
    "value_object": {
        "description": "Value Object pattern (immutable domain objects)",
        "signals": {
            "decorator": {
                "patterns": [r"@dataclass.*frozen.*True", r"@frozen", r"@value"],
                "weight": 0.9,
            },
            "base_class": {
                "patterns": [r"ValueObject", r"NamedTuple"],
                "weight": 0.8,
            },
            "directory": {
                "patterns": [r"value_objects?", r"domain"],
                "weight": 0.5,
            },
        },
        "min_confidence": 0.5,
    },
    "entity": {
        "description": "Domain Entity pattern (identity-based objects)",
        "signals": {
            "base_class": {
                "patterns": [r"Entity$", r"BaseEntity", r"AggregateRoot"],
                "weight": 0.9,
            },
            "attribute": {
                "patterns": [r"^id$", r"^_id$", r"entity_id"],
                "weight": 0.6,
            },
            "directory": {
                "patterns": [r"entities", r"domain", r"models"],
                "weight": 0.5,
            },
        },
        "min_confidence": 0.5,
    },
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "pytest": {
        "signals": {
            "import": [r"import pytest", r"from pytest"],
            "decorator": [r"@pytest\.", r"@fixture"],
            "function_prefix": [r"^test_"],
            "file_pattern": [r"test_.*\.py$", r".*_test\.py$"],
        },
        "type": "testing",
    },
    "fastapi": {
        "signals": {
            "import": [r"from fastapi", r"import fastapi"],
            "decorator": [r"@app\.(get|post|put|delete|patch)"],
            "class_base": [r"FastAPI"],
        },
        "type": "web",
    },
    "pydantic": {
        "signals": {
            "import": [r"from pydantic", r"import pydantic"],
            "class_base": [r"BaseModel", r"BaseSettings"],
        },
        "type": "validation",
    },
    "sqlalchemy": {
        "signals": {
            "import": [r"from sqlalchemy", r"import sqlalchemy"],
            "class_base": [r"Base", r"DeclarativeBase"],
            "decorator": [r"@mapper_registry"],
        },
        "type": "orm",
    },
    "click": {
        "signals": {
            "import": [r"import click", r"from click"],
            "decorator": [r"@click\.(command|group|option|argument)"],
        },
        "type": "cli",
    },
    "typer": {
        "signals": {
            "import": [r"import typer", r"from typer"],
            "decorator": [r"@app\.command"],
        },
        "type": "cli",
    },
    # .NET Frameworks
    "mediatr": {
        "signals": {
            "import": [r"using MediatR", r"using.*MediatR"],
            "class_base": [r"IRequest<", r"IRequestHandler<", r"INotification"],
        },
        "type": "cqrs",
    },
    "fluentvalidation": {
        "signals": {
            "import": [r"using FluentValidation", r"using.*FluentValidation"],
            "class_base": [r"AbstractValidator<", r"InlineValidator<"],
        },
        "type": "validation",
    },
    "efcore": {
        "signals": {
            "import": [r"using.*EntityFrameworkCore", r"using Microsoft\.EntityFrameworkCore"],
            "class_base": [r"DbContext$", r"DbSet<"],
        },
        "type": "orm",
    },
    "aspnetcore": {
        "signals": {
            "import": [r"using Microsoft\.AspNetCore", r"using.*AspNetCore"],
            "class_base": [r"ControllerBase$", r"Controller$", r"MinimalApiEndpoint"],
            "attribute": [r"\[ApiController\]", r"\[HttpGet", r"\[HttpPost", r"\[Route\("],
        },
        "type": "web",
    },
    "automapper": {
        "signals": {
            "import": [r"using AutoMapper", r"using.*AutoMapper"],
            "class_base": [r"Profile$", r"IMapper"],
        },
        "type": "mapping",
    },
    "serilog": {
        "signals": {
            "import": [r"using Serilog", r"using.*Serilog"],
        },
        "type": "logging",
    },
    "xunit": {
        "signals": {
            "import": [r"using Xunit", r"using.*Xunit"],
            "attribute": [r"\[Fact\]", r"\[Theory\]", r"\[InlineData"],
        },
        "type": "testing",
    },
    "nunit": {
        "signals": {
            "import": [r"using NUnit", r"using.*NUnit"],
            "attribute": [r"\[Test\]", r"\[TestCase\]", r"\[SetUp\]"],
        },
        "type": "testing",
    },
    "moq": {
        "signals": {
            "import": [r"using Moq", r"using.*Moq"],
            "class_usage": [r"Mock<", r"\.Setup\(", r"\.Verify\("],
        },
        "type": "testing",
    },
}


@dataclass
class PatternMatch:
    """A single pattern match instance."""
    pattern_name: str
    file_path: Path
    line_number: int
    signal_type: str
    matched_text: str
    weight: float


@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis."""
    patterns: dict[str, PatternDetection]
    frameworks: dict[str, Detection]
    matches: list[PatternMatch]
    total_files_analyzed: int


class PatternAnalyzer:
    """
    Analyzes code patterns through multi-signal detection.

    Uses weighted scoring across multiple signal types:
    - Class naming patterns
    - Directory structure
    - Base class inheritance
    - Method names
    - Decorators
    - Import statements
    """

    def __init__(self, provider: LanguageProvider):
        self.provider = provider
        self._matches: list[PatternMatch] = []
        self._pattern_scores: dict[str, dict[str, float]] = {}

    def analyze(self, root: Path) -> PatternAnalysisResult:
        """
        Analyze codebase for patterns.

        Args:
            root: Root directory to analyze

        Returns:
            PatternAnalysisResult with detected patterns and frameworks
        """
        self._matches = []
        self._pattern_scores = {name: {} for name in PATTERN_DEFINITIONS}

        source_files = self.provider.get_source_files(root)

        for file_path in source_files:
            self._analyze_file(file_path)

        patterns = self._aggregate_patterns()
        frameworks = self._detect_frameworks(source_files)

        return PatternAnalysisResult(
            patterns=patterns,
            frameworks=frameworks,
            matches=self._matches,
            total_files_analyzed=len(source_files),
        )

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for pattern signals."""
        # Get symbols from provider
        symbols = self.provider.extract_symbols(file_path)
        imports = self.provider.get_imports(file_path)

        # Read file content for text-based matching
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        relative_path = str(file_path)

        # Analyze each pattern
        for pattern_name, pattern_def in PATTERN_DEFINITIONS.items():
            score = 0.0
            signals_found = []

            for signal_type, signal_config in pattern_def["signals"].items():
                signal_score = self._check_signal(
                    signal_type,
                    signal_config,
                    file_path,
                    relative_path,
                    content,
                    symbols,
                    imports,
                    pattern_name,
                )
                if signal_score > 0:
                    score += signal_score
                    signals_found.append(signal_type)

            if score > 0:
                file_key = str(file_path)
                if file_key not in self._pattern_scores[pattern_name]:
                    self._pattern_scores[pattern_name][file_key] = 0.0
                self._pattern_scores[pattern_name][file_key] += score

    def _check_signal(
        self,
        signal_type: str,
        signal_config: dict[str, Any],
        file_path: Path,
        relative_path: str,
        content: str,
        symbols: list[Symbol],
        imports: list,
        pattern_name: str,
    ) -> float:
        """Check for a specific signal type and return weighted score."""
        patterns = signal_config["patterns"]
        weight = signal_config["weight"]
        score = 0.0

        if signal_type == "class_name" or signal_type == "class_suffix":
            for symbol in symbols:
                if symbol.kind == "class":
                    for regex in patterns:
                        if re.search(regex, symbol.name, re.IGNORECASE):
                            self._add_match(pattern_name, file_path, symbol.line_number,
                                          signal_type, symbol.name, weight)
                            score += weight
                            break

        elif signal_type == "method_name" or signal_type == "method_prefix":
            for symbol in symbols:
                if symbol.kind in ("method", "function"):
                    for regex in patterns:
                        if re.search(regex, symbol.name, re.IGNORECASE):
                            self._add_match(pattern_name, file_path, symbol.line_number,
                                          signal_type, symbol.name, weight)
                            score += weight * 0.5  # Lower weight per method
                            break

        elif signal_type == "base_class":
            for symbol in symbols:
                if symbol.kind == "class" and symbol.base_classes:
                    for base in symbol.base_classes:
                        for regex in patterns:
                            if re.search(regex, base, re.IGNORECASE):
                                self._add_match(pattern_name, file_path, symbol.line_number,
                                              signal_type, f"{symbol.name}({base})", weight)
                                score += weight
                                break

        elif signal_type == "decorator":
            for symbol in symbols:
                for decorator in symbol.decorators:
                    for regex in patterns:
                        if re.search(regex, decorator, re.IGNORECASE):
                            self._add_match(pattern_name, file_path, symbol.line_number,
                                          signal_type, f"@{decorator}", weight)
                            score += weight
                            break

        elif signal_type == "directory":
            for regex in patterns:
                if re.search(regex, relative_path, re.IGNORECASE):
                    self._add_match(pattern_name, file_path, 0, signal_type,
                                  relative_path, weight)
                    score += weight
                    break

        elif signal_type == "import":
            for imp in imports:
                imp_str = f"from {imp.module} import {', '.join(imp.names)}"
                for regex in patterns:
                    if re.search(regex, imp_str, re.IGNORECASE):
                        self._add_match(pattern_name, file_path, imp.line_number,
                                      signal_type, imp_str, weight)
                        score += weight
                        break

        elif signal_type == "return_type":
            for symbol in symbols:
                if symbol.return_type:
                    for regex in patterns:
                        if re.search(regex, symbol.return_type, re.IGNORECASE):
                            self._add_match(pattern_name, file_path, symbol.line_number,
                                          signal_type, f"-> {symbol.return_type}", weight)
                            score += weight
                            break

        elif signal_type == "method_names":
            # Check for specific method name patterns
            method_symbols = [s for s in symbols if s.kind in ("method", "function")]
            matched_methods = 0
            for symbol in method_symbols:
                for regex in patterns:
                    if re.search(regex, symbol.name, re.IGNORECASE):
                        matched_methods += 1
                        break
            if matched_methods >= 2:  # Need multiple method matches
                score += weight * min(matched_methods / 4, 1.0)

        return score

    def _add_match(
        self,
        pattern_name: str,
        file_path: Path,
        line_number: int,
        signal_type: str,
        matched_text: str,
        weight: float,
    ) -> None:
        """Record a pattern match."""
        self._matches.append(PatternMatch(
            pattern_name=pattern_name,
            file_path=file_path,
            line_number=line_number,
            signal_type=signal_type,
            matched_text=matched_text,
            weight=weight,
        ))

    def _aggregate_patterns(self) -> dict[str, PatternDetection]:
        """Aggregate pattern matches into pattern detections."""
        patterns = {}

        for pattern_name, file_scores in self._pattern_scores.items():
            if not file_scores:
                continue

            pattern_def = PATTERN_DEFINITIONS[pattern_name]
            min_confidence = pattern_def.get("min_confidence", 0.5)

            # Get all matches for this pattern
            pattern_matches = [m for m in self._matches if m.pattern_name == pattern_name]
            signals = list({m.signal_type for m in pattern_matches})

            # Check required signals - if defined, at least one must be present
            required_signals = pattern_def.get("required_signals", [])
            if required_signals:
                has_required = any(sig in signals for sig in required_signals)
                if not has_required:
                    # Skip this pattern - naming/directory alone isn't enough
                    continue

            # Calculate overall confidence
            total_score = sum(file_scores.values())
            file_count = len(file_scores)

            # Normalize score (more files = higher confidence, but with diminishing returns)
            confidence = min(total_score / (file_count + 2), 1.0)

            if confidence < min_confidence:
                continue

            # Get file locations
            locations = list(file_scores.keys())

            patterns[pattern_name] = PatternDetection(
                pattern_name=pattern_name,
                description=pattern_def.get("description", ""),
                detection=Detection(
                    value=pattern_name,
                    confidence=confidence,
                    source=DetectionSource.AST if "base_class" in signals else DetectionSource.NAMING,
                    signals=signals,
                ),
                locations=locations[:10],  # Limit to 10 examples
                file_count=file_count,
                usage_percentage=0.0,  # Would need total file count
            )

        return patterns

    def _detect_frameworks(self, source_files: list[Path]) -> dict[str, Detection]:
        """Detect frameworks used in the codebase."""
        frameworks = {}

        for fw_name, fw_config in FRAMEWORK_PATTERNS.items():
            signals_found = []
            total_score = 0.0

            for file_path in source_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                except Exception:
                    continue

                # Check import signals
                if "import" in fw_config["signals"]:
                    for pattern in fw_config["signals"]["import"]:
                        if re.search(pattern, content):
                            signals_found.append("import")
                            total_score += 1.0
                            break

                # Check decorator signals
                if "decorator" in fw_config["signals"]:
                    for pattern in fw_config["signals"]["decorator"]:
                        if re.search(pattern, content):
                            signals_found.append("decorator")
                            total_score += 0.8
                            break

                # Check file patterns
                if "file_pattern" in fw_config["signals"]:
                    for pattern in fw_config["signals"]["file_pattern"]:
                        if re.search(pattern, str(file_path)):
                            signals_found.append("file_pattern")
                            total_score += 0.5
                            break

            if total_score > 0:
                confidence = min(total_score / 5, 1.0)  # Cap at 1.0
                frameworks[fw_name] = Detection(
                    value=fw_name,
                    confidence=confidence,
                    source=DetectionSource.EXPLICIT if "import" in signals_found else DetectionSource.NAMING,
                    signals=list(set(signals_found)),
                    metadata={"type": fw_config.get("type", "unknown")},
                )

        return frameworks

    def get_patterns_by_confidence(
        self, min_confidence: float = 0.5
    ) -> list[PatternDetection]:
        """Get patterns above a confidence threshold, sorted by confidence."""
        if not hasattr(self, '_last_result'):
            return []
        return sorted(
            [p for p in self._last_result.patterns.values() if p.detection.confidence >= min_confidence],
            key=lambda p: p.detection.confidence,
            reverse=True,
        )
