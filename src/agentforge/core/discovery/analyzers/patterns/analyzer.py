"""
Pattern Analyzer
================

Detects code patterns through multi-signal analysis.
"""

import re
from pathlib import Path
from typing import Any

from ...domain import Detection, DetectionSource, PatternDetection
from ...providers.base import LanguageProvider, Symbol
from .definitions import PATTERN_DEFINITIONS
from .frameworks import FRAMEWORK_PATTERNS
from .types import PatternAnalysisResult, PatternMatch


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

    def _check_class_name_signal(
        self, patterns, weight, symbols, file_path, pattern_name, signal_type
    ) -> float:
        """Check class name/suffix signal."""
        score = 0.0
        for symbol in symbols:
            if symbol.kind == "class":
                for regex in patterns:
                    if re.search(regex, symbol.name, re.IGNORECASE):
                        self._add_match(pattern_name, file_path, symbol.line_number,
                                      signal_type, symbol.name, weight)
                        score += weight
                        break
        return score

    def _check_method_name_signal(
        self, patterns, weight, symbols, file_path, pattern_name, signal_type
    ) -> float:
        """Check method name/prefix signal."""
        score = 0.0
        for symbol in symbols:
            if symbol.kind in ("method", "function"):
                for regex in patterns:
                    if re.search(regex, symbol.name, re.IGNORECASE):
                        self._add_match(pattern_name, file_path, symbol.line_number,
                                      signal_type, symbol.name, weight)
                        score += weight * 0.5
                        break
        return score

    def _check_base_class_signal(
        self, patterns, weight, symbols, file_path, pattern_name, signal_type
    ) -> float:
        """Check base class signal."""
        score = 0.0
        for symbol in symbols:
            if symbol.kind == "class" and symbol.base_classes:
                for base in symbol.base_classes:
                    for regex in patterns:
                        if re.search(regex, base, re.IGNORECASE):
                            self._add_match(pattern_name, file_path, symbol.line_number,
                                          signal_type, f"{symbol.name}({base})", weight)
                            score += weight
                            break
        return score

    def _check_decorator_signal(
        self, patterns, weight, symbols, file_path, pattern_name, signal_type
    ) -> float:
        """Check decorator signal."""
        score = 0.0
        for symbol in symbols:
            for decorator in symbol.decorators:
                for regex in patterns:
                    if re.search(regex, decorator, re.IGNORECASE):
                        self._add_match(pattern_name, file_path, symbol.line_number,
                                      signal_type, f"@{decorator}", weight)
                        score += weight
                        break
        return score

    def _check_directory_signal(
        self, patterns, weight, relative_path, file_path, pattern_name, signal_type
    ) -> float:
        """Check directory signal."""
        for regex in patterns:
            if re.search(regex, relative_path, re.IGNORECASE):
                self._add_match(pattern_name, file_path, 0, signal_type, relative_path, weight)
                return weight
        return 0.0

    def _check_import_signal(
        self, patterns, weight, imports, file_path, pattern_name, signal_type
    ) -> float:
        """Check import signal."""
        score = 0.0
        for imp in imports:
            imp_str = f"from {imp.module} import {', '.join(imp.names)}"
            for regex in patterns:
                if re.search(regex, imp_str, re.IGNORECASE):
                    self._add_match(pattern_name, file_path, imp.line_number,
                                  signal_type, imp_str, weight)
                    score += weight
                    break
        return score

    def _check_return_type_signal(
        self, patterns, weight, symbols, file_path, pattern_name, signal_type
    ) -> float:
        """Check return type signal."""
        score = 0.0
        for symbol in symbols:
            if symbol.return_type:
                for regex in patterns:
                    if re.search(regex, symbol.return_type, re.IGNORECASE):
                        self._add_match(pattern_name, file_path, symbol.line_number,
                                      signal_type, f"-> {symbol.return_type}", weight)
                        score += weight
                        break
        return score

    def _check_method_names_signal(self, patterns, weight, symbols) -> float:
        """Check multiple method names signal."""
        method_symbols = [s for s in symbols if s.kind in ("method", "function")]
        matched_methods = 0
        for symbol in method_symbols:
            for regex in patterns:
                if re.search(regex, symbol.name, re.IGNORECASE):
                    matched_methods += 1
                    break
        if matched_methods >= 2:
            return weight * min(matched_methods / 4, 1.0)
        return 0.0

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

        if signal_type in ("class_name", "class_suffix"):
            return self._check_class_name_signal(
                patterns, weight, symbols, file_path, pattern_name, signal_type
            )
        if signal_type in ("method_name", "method_prefix"):
            return self._check_method_name_signal(
                patterns, weight, symbols, file_path, pattern_name, signal_type
            )
        if signal_type == "base_class":
            return self._check_base_class_signal(
                patterns, weight, symbols, file_path, pattern_name, signal_type
            )
        if signal_type == "decorator":
            return self._check_decorator_signal(
                patterns, weight, symbols, file_path, pattern_name, signal_type
            )
        if signal_type == "directory":
            return self._check_directory_signal(
                patterns, weight, relative_path, file_path, pattern_name, signal_type
            )
        if signal_type == "import":
            return self._check_import_signal(
                patterns, weight, imports, file_path, pattern_name, signal_type
            )
        if signal_type == "return_type":
            return self._check_return_type_signal(
                patterns, weight, symbols, file_path, pattern_name, signal_type
            )
        if signal_type == "method_names":
            return self._check_method_names_signal(patterns, weight, symbols)
        return 0.0

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

            detection = self._build_pattern_detection(pattern_name, file_scores)
            if detection:
                patterns[pattern_name] = detection

        return patterns

    def _build_pattern_detection(
        self, pattern_name: str, file_scores: dict[str, float]
    ) -> PatternDetection | None:
        """Build a pattern detection if it meets requirements."""
        pattern_def = PATTERN_DEFINITIONS[pattern_name]
        signals = self._get_pattern_signals(pattern_name)

        if not self._meets_required_signals(pattern_def, signals):
            return None

        confidence = self._calculate_confidence(file_scores)
        min_confidence = pattern_def.get("min_confidence", 0.5)
        if confidence < min_confidence:
            return None

        return PatternDetection(
            pattern_name=pattern_name,
            description=pattern_def.get("description", ""),
            detection=Detection(
                value=pattern_name,
                confidence=confidence,
                source=DetectionSource.AST if "base_class" in signals else DetectionSource.NAMING,
                signals=signals,
            ),
            locations=list(file_scores.keys())[:10],
            file_count=len(file_scores),
            usage_percentage=0.0,
        )

    def _get_pattern_signals(self, pattern_name: str) -> list[str]:
        """Get unique signal types for a pattern."""
        pattern_matches = [m for m in self._matches if m.pattern_name == pattern_name]
        return list({m.signal_type for m in pattern_matches})

    def _meets_required_signals(self, pattern_def: dict, signals: list[str]) -> bool:
        """Check if required signals are present."""
        required_signals = pattern_def.get("required_signals", [])
        if not required_signals:
            return True
        return any(sig in signals for sig in required_signals)

    def _calculate_confidence(self, file_scores: dict[str, float]) -> float:
        """Calculate confidence from file scores."""
        total_score = sum(file_scores.values())
        file_count = len(file_scores)
        return min(total_score / (file_count + 2), 1.0)

    def _check_framework_signal(
        self, patterns: list, content: str, signal_name: str, score: float
    ) -> tuple[str | None, float]:
        """Check if any pattern matches content for a framework signal."""
        for pattern in patterns:
            if re.search(pattern, content):
                return signal_name, score
        return None, 0.0

    def _scan_file_for_framework(
        self, file_path: Path, fw_config: dict
    ) -> tuple[list[str], float]:
        """Scan a single file for framework signals."""
        signals = fw_config.get("signals", {})
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return [], 0.0

        found_signals = []
        total_score = 0.0

        signal_checks = [
            ("import", signals.get("import", []), content, 1.0),
            ("decorator", signals.get("decorator", []), content, 0.8),
            ("file_pattern", signals.get("file_pattern", []), str(file_path), 0.5),
        ]

        for signal_name, patterns, text, score in signal_checks:
            if patterns:
                sig, sc = self._check_framework_signal(patterns, text, signal_name, score)
                if sig:
                    found_signals.append(sig)
                    total_score += sc

        return found_signals, total_score

    def _detect_frameworks(self, source_files: list[Path]) -> dict[str, Detection]:
        """Detect frameworks used in the codebase."""
        frameworks = {}

        for fw_name, fw_config in FRAMEWORK_PATTERNS.items():
            all_signals = []
            total_score = 0.0

            for file_path in source_files:
                signals, score = self._scan_file_for_framework(file_path, fw_config)
                all_signals.extend(signals)
                total_score += score

            if total_score > 0:
                confidence = min(total_score / 5, 1.0)
                frameworks[fw_name] = Detection(
                    value=fw_name,
                    confidence=confidence,
                    source=DetectionSource.EXPLICIT if "import" in all_signals else DetectionSource.NAMING,
                    signals=list(set(all_signals)),
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
