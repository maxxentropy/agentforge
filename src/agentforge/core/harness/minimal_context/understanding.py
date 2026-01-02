# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: understanding-extractor
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Understanding Extractor
=======================

Extracts structured facts from tool outputs rather than storing raw results.

Key principles:
1. Conclusions, not data: Extract "function has complexity 15" not raw AST
2. Rule-based first: Deterministic extraction where possible
3. LLM fallback: Use LLM only for ambiguous cases
4. Confidence scoring: Higher for deterministic, lower for inferred
"""

import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .context_models import ActionResult, Fact, FactCategory, Understanding

# ═══════════════════════════════════════════════════════════════════════════════
# Extraction Rules
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ExtractionRule:
    """
    Rule for extracting facts from tool output.

    Each rule has:
    - pattern: Regex or callable to match
    - category: What kind of fact this produces
    - confidence: How confident we are in rule-based extraction
    - extractor: Function to extract the fact statement
    """

    name: str
    pattern: str | Callable[[str], bool]
    category: FactCategory
    confidence: float
    extractor: Callable[[str, re.Match | None], str]


class ExtractionRuleSet:
    """Collection of extraction rules for a tool type."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.rules: list[ExtractionRule] = []

    def add_rule(self, rule: ExtractionRule) -> "ExtractionRuleSet":
        self.rules.append(rule)
        return self

    def extract(self, output: str, step: int) -> list[Fact]:
        """Apply all rules and return extracted facts."""
        facts = []
        for rule in self.rules:
            if isinstance(rule.pattern, str):
                match = re.search(rule.pattern, output, re.MULTILINE)
                if match:
                    statement = rule.extractor(output, match)
                    facts.append(
                        Fact(
                            id=f"fact_{uuid.uuid4().hex[:8]}",
                            category=rule.category,
                            statement=statement,
                            confidence=rule.confidence,
                            source=f"{self.tool_name}:{rule.name}",
                            step=step,
                        )
                    )
            elif callable(rule.pattern):
                if rule.pattern(output):
                    statement = rule.extractor(output, None)
                    facts.append(
                        Fact(
                            id=f"fact_{uuid.uuid4().hex[:8]}",
                            category=rule.category,
                            statement=statement,
                            confidence=rule.confidence,
                            source=f"{self.tool_name}:{rule.name}",
                            step=step,
                        )
                    )
        return facts


# ═══════════════════════════════════════════════════════════════════════════════
# Built-in Rule Sets
# ═══════════════════════════════════════════════════════════════════════════════


def _build_conformance_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from conformance check output."""
    rules = ExtractionRuleSet("run_check")

    # Check passed
    rules.add_rule(
        ExtractionRule(
            name="check_passed",
            pattern=r"(Check PASSED|All checks passed|\u2713)",
            category=FactCategory.VERIFICATION,
            confidence=1.0,
            extractor=lambda out, m: "Conformance check passed",
        )
    )

    # Check failed with complexity
    rules.add_rule(
        ExtractionRule(
            name="complexity_violation",
            pattern=r"Function '([^']+)' has complexity (\d+)",
            category=FactCategory.VERIFICATION,
            confidence=1.0,
            extractor=lambda out, m: f"Function '{m.group(1)}' has cyclomatic complexity {m.group(2)} (threshold exceeded)"
            if m
            else "Complexity violation detected",
        )
    )

    # Check failed with line count
    rules.add_rule(
        ExtractionRule(
            name="length_violation",
            pattern=r"Function '([^']+)' has (\d+) lines",
            category=FactCategory.VERIFICATION,
            confidence=1.0,
            extractor=lambda out, m: f"Function '{m.group(1)}' has {m.group(2)} lines (threshold exceeded)"
            if m
            else "Length violation detected",
        )
    )

    # Violation count
    rules.add_rule(
        ExtractionRule(
            name="violation_count",
            pattern=r"Violations?\s*\((\d+)\)",
            category=FactCategory.VERIFICATION,
            confidence=1.0,
            extractor=lambda out, m: f"Total violations: {m.group(1)}" if m else "Violations found",
        )
    )

    return rules


def _build_test_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from test output."""
    rules = ExtractionRuleSet("run_tests")

    # All tests passed
    rules.add_rule(
        ExtractionRule(
            name="tests_passed",
            pattern=r"(\d+) passed",
            category=FactCategory.VERIFICATION,
            confidence=1.0,
            extractor=lambda out, m: f"Tests passed: {m.group(1)}" if m else "Tests passed",
        )
    )

    # Tests failed
    rules.add_rule(
        ExtractionRule(
            name="tests_failed",
            pattern=r"(\d+) failed",
            category=FactCategory.VERIFICATION,
            confidence=1.0,
            extractor=lambda out, m: f"Tests failed: {m.group(1)}" if m else "Tests failed",
        )
    )

    # Specific test failure
    rules.add_rule(
        ExtractionRule(
            name="test_failure_detail",
            pattern=r"FAILED\s+([^\s]+)::",
            category=FactCategory.ERROR,
            confidence=0.9,
            extractor=lambda out, m: f"Test failure in: {m.group(1)}" if m else "Test failure detected",
        )
    )

    return rules


def _build_edit_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from file edit output."""
    rules = ExtractionRuleSet("edit_file")

    # Edit succeeded
    rules.add_rule(
        ExtractionRule(
            name="edit_success",
            pattern=r"(Edited|Modified|Updated)\s+([^\s:]+)",
            category=FactCategory.CODE_STRUCTURE,
            confidence=1.0,
            extractor=lambda out, m: f"File modified: {m.group(2)}" if m else "File modified",
        )
    )

    # Edit failed - not found
    rules.add_rule(
        ExtractionRule(
            name="edit_not_found",
            pattern=r"(old_text not found|text to replace not found)",
            category=FactCategory.ERROR,
            confidence=1.0,
            extractor=lambda out, m: "Edit failed: target text not found in file",
        )
    )

    return rules


def _build_extract_function_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from extract_function output."""
    rules = ExtractionRuleSet("extract_function")

    # Extraction succeeded
    rules.add_rule(
        ExtractionRule(
            name="extraction_success",
            pattern=r"Extracted.*?'([^']+)'.*?lines?\s*(\d+)-(\d+)",
            category=FactCategory.CODE_STRUCTURE,
            confidence=1.0,
            extractor=lambda out, m: f"Extracted function '{m.group(1)}' from lines {m.group(2)}-{m.group(3)}"
            if m
            else "Function extracted",
        )
    )

    # Extraction failed - control flow
    rules.add_rule(
        ExtractionRule(
            name="extraction_control_flow",
            pattern=r"(cannot extract|control flow|early return|break|continue)",
            category=FactCategory.ERROR,
            confidence=0.95,
            extractor=lambda out, m: "Extraction blocked by control flow (returns/breaks in selection)",
        )
    )

    # Check passed after extraction
    rules.add_rule(
        ExtractionRule(
            name="post_extraction_check_passed",
            pattern=r"Check PASSED",
            category=FactCategory.VERIFICATION,
            confidence=1.0,
            extractor=lambda out, m: "Conformance check passed after extraction",
        )
    )

    return rules


# ═══════════════════════════════════════════════════════════════════════════════
# Main Extractor
# ═══════════════════════════════════════════════════════════════════════════════


class UnderstandingExtractor:
    """
    Extracts structured facts from tool outputs.

    Uses a two-tier approach:
    1. Rule-based extraction (fast, deterministic, high confidence)
    2. LLM-based extraction (fallback for complex cases)
    """

    def __init__(
        self, llm_extractor: Callable[[str, str], list[dict[str, Any]]] | None = None
    ):
        """
        Initialize extractor.

        Args:
            llm_extractor: Optional callable for LLM-based extraction
                          Signature: (tool_name, output) -> List[{statement, category, confidence}]
        """
        self.llm_extractor = llm_extractor
        self.rule_sets: dict[str, ExtractionRuleSet] = {
            "run_check": _build_conformance_rules(),
            "run_conformance_check": _build_conformance_rules(),
            "run_tests": _build_test_rules(),
            "run_affected_tests": _build_test_rules(),
            "edit_file": _build_edit_rules(),
            "replace_lines": _build_edit_rules(),
            "extract_function": _build_extract_function_rules(),
        }

    def register_rule_set(self, tool_name: str, rule_set: ExtractionRuleSet) -> None:
        """Register a custom rule set for a tool."""
        self.rule_sets[tool_name] = rule_set

    def extract(
        self,
        tool_name: str,
        output: str,
        result: ActionResult,
        step: int,
        use_llm_fallback: bool = False,
    ) -> list[Fact]:
        """
        Extract facts from tool output.

        Args:
            tool_name: Name of the tool that produced output
            output: Raw tool output
            result: Whether tool succeeded/failed
            step: Current step number
            use_llm_fallback: Whether to use LLM if rules don't match

        Returns:
            List of extracted facts
        """
        facts: list[Fact] = []

        # 1. Try rule-based extraction
        if tool_name in self.rule_sets:
            facts = self.rule_sets[tool_name].extract(output, step)

        # 2. Add result-based fact if no specific facts extracted
        if not facts:
            facts.append(
                Fact(
                    id=f"fact_{uuid.uuid4().hex[:8]}",
                    category=FactCategory.VERIFICATION
                    if result == ActionResult.SUCCESS
                    else FactCategory.ERROR,
                    statement=f"{tool_name} {'succeeded' if result == ActionResult.SUCCESS else 'failed'}",
                    confidence=0.7,
                    source=f"{tool_name}:result",
                    step=step,
                )
            )

        # 3. LLM fallback for complex cases
        if use_llm_fallback and self.llm_extractor and len(facts) < 2:
            llm_facts = self._llm_extract(tool_name, output, step)
            facts.extend(llm_facts)

        return facts

    def _llm_extract(self, tool_name: str, output: str, step: int) -> list[Fact]:
        """Use LLM to extract facts from complex output."""
        if not self.llm_extractor:
            return []

        try:
            raw_facts = self.llm_extractor(tool_name, output)
            facts = []
            for rf in raw_facts:
                facts.append(
                    Fact(
                        id=f"fact_{uuid.uuid4().hex[:8]}",
                        category=FactCategory(rf.get("category", "inference")),
                        statement=rf.get("statement", ""),
                        confidence=rf.get("confidence", 0.6),
                        source=f"{tool_name}:llm",
                        step=step,
                    )
                )
            return facts
        except Exception:
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# Fact Store
# ═══════════════════════════════════════════════════════════════════════════════


class FactStore:
    """
    Manages the collection of facts with compaction.

    Handles:
    - Adding new facts
    - Superseding old facts
    - Compacting when too large
    - Retrieving relevant facts
    """

    def __init__(self, max_facts: int = 20, compaction_threshold: int = 15):
        self.facts: list[Fact] = []
        self.superseded: set[str] = set()
        self.max_facts = max_facts
        self.compaction_threshold = compaction_threshold

    def add(self, fact: Fact) -> None:
        """Add a fact, potentially superseding existing facts."""
        # Check for supersession
        for existing in self.facts:
            if self._should_supersede(existing, fact):
                self.superseded.add(existing.id)
                # Create new fact with supersedes link
                fact = Fact(
                    id=fact.id,
                    category=fact.category,
                    statement=fact.statement,
                    confidence=fact.confidence,
                    source=fact.source,
                    step=fact.step,
                    supersedes=existing.id,
                )

        self.facts.append(fact)

        # Compact if needed
        if len(self.get_active()) > self.compaction_threshold:
            self._compact()

    def add_many(self, facts: list[Fact]) -> None:
        """Add multiple facts."""
        for fact in facts:
            self.add(fact)

    def get_active(self) -> list[Fact]:
        """Get all non-superseded facts."""
        return [f for f in self.facts if f.id not in self.superseded]

    def get_by_category(self, category: FactCategory) -> list[Fact]:
        """Get active facts in a category."""
        return [f for f in self.get_active() if f.category == category]

    def get_recent(self, n: int = 5) -> list[Fact]:
        """Get most recent active facts."""
        active = self.get_active()
        return sorted(active, key=lambda f: f.step, reverse=True)[:n]

    def _should_supersede(self, old: Fact, new: Fact) -> bool:
        """Determine if new fact supersedes old fact."""
        # Same category and similar statement
        if old.category != new.category:
            return False

        # For verification facts, newer supersedes older
        if old.category == FactCategory.VERIFICATION:
            # Same type of check result
            if "complexity" in old.statement and "complexity" in new.statement:
                return True
            if "passed" in old.statement.lower() and "passed" in new.statement.lower():
                return True
            if "failed" in old.statement.lower() and "failed" in new.statement.lower():
                return True

        return False

    def _compact(self) -> None:
        """Compact facts by removing low-value ones."""
        active = self.get_active()
        if len(active) <= self.max_facts:
            return

        # Score facts by value
        scored = []
        for fact in active:
            score = self._score_fact(fact)
            scored.append((score, fact))

        # Keep top N facts
        scored.sort(key=lambda x: x[0], reverse=True)
        keep_ids = {f.id for _, f in scored[: self.max_facts]}

        # Mark others as superseded
        for fact in active:
            if fact.id not in keep_ids:
                self.superseded.add(fact.id)

    def _score_fact(self, fact: Fact) -> float:
        """Score a fact's value for retention."""
        score = fact.confidence

        # Verification facts are valuable
        if fact.category == FactCategory.VERIFICATION:
            score += 0.3

        # Error facts help avoid repeating mistakes
        if fact.category == FactCategory.ERROR:
            score += 0.2

        return score

    def to_understanding(self) -> Understanding:
        """Convert to Understanding model."""
        return Understanding(
            facts=self.facts,
            superseded_facts=list(self.superseded),
        )

    def clear(self) -> None:
        """Clear all facts."""
        self.facts = []
        self.superseded = set()

    def from_understanding(self, understanding: Understanding) -> None:
        """Load from Understanding model."""
        self.facts = list(understanding.facts)
        self.superseded = set(understanding.superseded_facts)
