# @spec_file: specs/minimal-context-architecture-specs/specs/minimal-context-architecture/06-compaction.yaml
# @spec_id: compaction-v1
# @component_id: compaction-manager
# @test_path: tests/unit/context/test_compaction.py

"""
Compaction Manager
==================

Progressive context compaction to fit within token budget.
Sacrifices low-value content first, preserves critical context.

Strategy (low value → high value):
1. Truncate precomputed analysis
2. Reduce facts to high-confidence
3. Reduce actions to top N
4. Truncate domain context
5. Reduce recent actions to 1
6. Remove precomputed entirely
7. LLM summarization (last resort)

Usage:
    ```python
    manager = CompactionManager(threshold=0.90, max_budget=4000)

    if manager.needs_compaction(context):
        compacted, audit = manager.compact(
            context,
            preserve=["fingerprint", "task", "phase"],
        )
    ```
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import yaml


class CompactionStrategy(str, Enum):
    """Strategy for compacting a section."""

    TRUNCATE = "truncate"  # Cut to max chars
    TRUNCATE_MIDDLE = "truncate_middle"  # Keep start + end
    KEEP_LAST = "keep_last"  # Keep N most recent
    KEEP_FIRST = "keep_first"  # Keep N highest priority
    REMOVE = "remove"  # Delete entirely
    SUMMARIZE = "summarize"  # LLM summarization (last resort)


@dataclass
class CompactionRule:
    """Rule for compacting a specific section."""

    section: str  # Dot notation: "precomputed.analysis"
    strategy: CompactionStrategy
    param: Optional[int] = None  # Strategy-specific parameter
    priority: int = 0  # Lower = compact first

    def __lt__(self, other: "CompactionRule") -> bool:
        return self.priority < other.priority


# Default compaction rules in priority order
DEFAULT_RULES: List[CompactionRule] = [
    # Phase 1: Truncate precomputed
    CompactionRule("target_source", CompactionStrategy.TRUNCATE_MIDDLE, 800, priority=1),
    CompactionRule("similar_fixes", CompactionStrategy.KEEP_FIRST, 2, priority=2),
    CompactionRule("similar_implementations", CompactionStrategy.KEEP_FIRST, 2, priority=3),
    # Phase 2: Reduce facts
    CompactionRule("understanding", CompactionStrategy.KEEP_FIRST, 10, priority=4),
    # Phase 3: Reduce actions
    CompactionRule("action_hints", CompactionStrategy.TRUNCATE, 100, priority=5),
    # Phase 4: Truncate domain
    CompactionRule("related_patterns", CompactionStrategy.TRUNCATE, 300, priority=6),
    CompactionRule("file_overview", CompactionStrategy.TRUNCATE, 300, priority=7),
    # Phase 5: Reduce recent
    CompactionRule("recent", CompactionStrategy.KEEP_LAST, 1, priority=8),
    # Phase 6: Remove optional sections
    CompactionRule("additional", CompactionStrategy.REMOVE, None, priority=9),
    CompactionRule("related_code", CompactionStrategy.REMOVE, None, priority=10),
]

# Sections that should NEVER be compacted
PRESERVED_SECTIONS = frozenset(["fingerprint", "task", "phase"])


@dataclass
class CompactionAudit:
    """Audit information for a compaction operation."""

    original_tokens: int
    final_tokens: int
    budget: int
    rules_applied: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied": len(self.rules_applied) > 0,
            "original_tokens": self.original_tokens,
            "final_tokens": self.final_tokens,
            "budget": self.budget,
            "rules_applied": self.rules_applied,
            "tokens_saved": self.original_tokens - self.final_tokens,
        }


class CompactionManager:
    """
    Manages progressive context compaction.

    Applies compaction rules in priority order until context fits
    within budget. Preserves critical sections.
    """

    def __init__(
        self,
        threshold: float = 0.90,
        max_budget: int = 4000,
        rules: Optional[List[CompactionRule]] = None,
    ):
        """
        Initialize compaction manager.

        Args:
            threshold: Trigger compaction when usage exceeds this ratio
            max_budget: Maximum token budget
            rules: Custom compaction rules (uses defaults if not provided)
        """
        self.threshold = threshold
        self.max_budget = max_budget
        self.rules = sorted(rules or DEFAULT_RULES, key=lambda r: r.priority)

    def estimate_tokens(self, context: Dict[str, Any]) -> int:
        """Estimate total tokens in a context dictionary."""
        yaml_str = yaml.dump(context, default_flow_style=False)
        return len(yaml_str) // 4

    def needs_compaction(self, context: Dict[str, Any]) -> bool:
        """
        Check if compaction is needed.

        Returns True if estimated tokens exceed threshold * budget.
        """
        tokens = self.estimate_tokens(context)
        return tokens / self.max_budget > self.threshold

    def compact(
        self,
        context: Dict[str, Any],
        preserve: Optional[List[str]] = None,
    ) -> Tuple[Dict[str, Any], CompactionAudit]:
        """
        Compact context to fit within budget.

        Applies rules in priority order until context fits.

        Args:
            context: Context dictionary to compact
            preserve: Additional sections to preserve (added to defaults)

        Returns:
            Tuple of (compacted context, audit info)
        """
        preserve_set = set(preserve or []) | PRESERVED_SECTIONS
        original_tokens = self.estimate_tokens(context)

        rules_applied: List[Dict[str, Any]] = []
        result = dict(context)

        for rule in self.rules:
            # Check if this section should be preserved
            if self._should_preserve(rule.section, preserve_set):
                continue

            # Check if we're under budget
            current_tokens = self.estimate_tokens(result)
            if current_tokens <= self.max_budget:
                break

            # Try to apply the rule
            new_result, applied = self._apply_rule(result, rule)
            if applied:
                tokens_after = self.estimate_tokens(new_result)
                rules_applied.append(
                    {
                        "section": rule.section,
                        "strategy": rule.strategy.value,
                        "param": rule.param,
                        "tokens_after": tokens_after,
                    }
                )
                result = new_result

        final_tokens = self.estimate_tokens(result)
        audit = CompactionAudit(
            original_tokens=original_tokens,
            final_tokens=final_tokens,
            budget=self.max_budget,
            rules_applied=rules_applied,
        )

        return result, audit

    def _should_preserve(self, section: str, preserve_set: set) -> bool:
        """Check if a section should be preserved."""
        # Direct match
        if section in preserve_set:
            return True
        # Check if section starts with any preserved section
        for p in preserve_set:
            if section.startswith(p + "."):
                return True
        return False

    def _apply_rule(
        self, context: Dict[str, Any], rule: CompactionRule
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Apply a compaction rule to the context.

        Returns (new_context, was_applied).
        """
        # Navigate to section (support dot notation)
        parts = rule.section.split(".")
        parent = context
        for part in parts[:-1]:
            if part not in parent or not isinstance(parent[part], dict):
                return context, False
            parent = parent[part]

        key = parts[-1]
        if key not in parent:
            return context, False

        value = parent[key]
        result = dict(context)

        # Navigate to parent in result
        result_parent = result
        for part in parts[:-1]:
            if part not in result_parent:
                result_parent[part] = {}
            result_parent = result_parent[part]

        # Apply strategy
        if rule.strategy == CompactionStrategy.TRUNCATE:
            if isinstance(value, str):
                result_parent[key] = self._truncate(value, rule.param or 500)
                return result, True

        elif rule.strategy == CompactionStrategy.TRUNCATE_MIDDLE:
            if isinstance(value, str):
                result_parent[key] = self._truncate_middle(value, rule.param or 500)
                return result, True

        elif rule.strategy == CompactionStrategy.KEEP_FIRST:
            if isinstance(value, list):
                n = rule.param or 5
                if len(value) > n:
                    result_parent[key] = value[:n]
                    return result, True

        elif rule.strategy == CompactionStrategy.KEEP_LAST:
            if isinstance(value, list):
                n = rule.param or 3
                if len(value) > n:
                    result_parent[key] = value[-n:]
                    return result, True

        elif rule.strategy == CompactionStrategy.REMOVE:
            del result_parent[key]
            return result, True

        return context, False

    def _truncate(self, value: str, max_tokens: int) -> str:
        """Truncate string to fit token budget."""
        max_chars = max_tokens * 4
        if len(value) > max_chars:
            return value[:max_chars] + "... (truncated)"
        return value

    def _truncate_middle(self, value: str, max_tokens: int) -> str:
        """Truncate middle of string, keeping start and end."""
        max_chars = max_tokens * 4
        if len(value) > max_chars:
            keep = max_chars // 2
            return value[:keep] + "\n...(middle truncated)...\n" + value[-keep:]
        return value

    def get_section_tokens(self, context: Dict[str, Any]) -> Dict[str, int]:
        """Get token breakdown by top-level section."""
        breakdown: Dict[str, int] = {}
        for key, value in context.items():
            section_yaml = yaml.dump({key: value}, default_flow_style=False)
            breakdown[key] = len(section_yaml) // 4
        return breakdown
