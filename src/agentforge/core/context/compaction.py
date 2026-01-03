# @spec_file: .agentforge/specs/core-context-v1.yaml
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

    # With LLM summarization (last resort)
    manager = CompactionManager(
        threshold=0.90,
        max_budget=4000,
        summarizer=my_llm_summarizer,
    )
    ```
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

import yaml


class Summarizer(Protocol):
    """Protocol for LLM-based summarization."""

    def summarize(self, content: str, max_tokens: int) -> str:
        """
        Summarize content to fit within token budget.

        Args:
            content: Text content to summarize
            max_tokens: Maximum tokens for the summary

        Returns:
            Summarized text
        """
        ...


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
    param: int | None = None  # Strategy-specific parameter
    priority: int = 0  # Lower = compact first

    def __lt__(self, other: "CompactionRule") -> bool:
        return self.priority < other.priority


# Default compaction rules in priority order
DEFAULT_RULES: list[CompactionRule] = [
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
    rules_applied: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
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

    The SUMMARIZE strategy requires an LLM summarizer to be provided.
    If no summarizer is set, SUMMARIZE rules are skipped.
    """

    def __init__(
        self,
        threshold: float = 0.90,
        max_budget: int = 4000,
        rules: list[CompactionRule] | None = None,
        summarizer: Summarizer | None = None,
    ):
        """
        Initialize compaction manager.

        Args:
            threshold: Trigger compaction when usage exceeds this ratio
            max_budget: Maximum token budget
            rules: Custom compaction rules (uses defaults if not provided)
            summarizer: Optional LLM summarizer for SUMMARIZE strategy
        """
        self.threshold = threshold
        self.max_budget = max_budget
        self.rules = sorted(rules or DEFAULT_RULES, key=lambda r: r.priority)
        self.summarizer = summarizer
        self._summarization_calls = 0  # Track summarization usage

    def estimate_tokens(self, context: dict[str, Any]) -> int:
        """Estimate total tokens in a context dictionary."""
        yaml_str = yaml.dump(context, default_flow_style=False)
        return len(yaml_str) // 4

    def needs_compaction(self, context: dict[str, Any]) -> bool:
        """
        Check if compaction is needed.

        Returns True if estimated tokens exceed threshold * budget.
        """
        tokens = self.estimate_tokens(context)
        return tokens / self.max_budget > self.threshold

    def compact(
        self,
        context: dict[str, Any],
        preserve: list[str] | None = None,
    ) -> tuple[dict[str, Any], CompactionAudit]:
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

        rules_applied: list[dict[str, Any]] = []
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
        return any(section.startswith(p + ".") for p in preserve_set)

    def _navigate_to_section(
        self, context: dict[str, Any], parts: list[str]
    ) -> tuple[dict | None, str | None]:
        """Navigate to section parent and return (parent, key) or (None, None) if not found."""
        parent = context
        for part in parts[:-1]:
            if part not in parent or not isinstance(parent[part], dict):
                return None, None
            parent = parent[part]
        key = parts[-1]
        return (parent, key) if key in parent else (None, None)

    def _create_result_parent(
        self, result: dict[str, Any], parts: list[str]
    ) -> dict[str, Any]:
        """Navigate/create result path and return the parent dict."""
        result_parent = result
        for part in parts[:-1]:
            if part not in result_parent:
                result_parent[part] = {}
            result_parent = result_parent[part]
        return result_parent

    def _apply_truncate(self, value: Any, param: int | None) -> tuple[Any, bool]:
        """Apply truncate strategy."""
        if isinstance(value, str):
            return self._truncate(value, param or 500), True
        return value, False

    def _apply_truncate_middle(self, value: Any, param: int | None) -> tuple[Any, bool]:
        """Apply truncate_middle strategy."""
        if isinstance(value, str):
            return self._truncate_middle(value, param or 500), True
        return value, False

    def _apply_keep_first(self, value: Any, param: int | None) -> tuple[Any, bool]:
        """Apply keep_first strategy."""
        if isinstance(value, list):
            n = param or 5
            if len(value) > n:
                return value[:n], True
        return value, False

    def _apply_keep_last(self, value: Any, param: int | None) -> tuple[Any, bool]:
        """Apply keep_last strategy."""
        if isinstance(value, list):
            n = param or 3
            if len(value) > n:
                return value[-n:], True
        return value, False

    def _apply_summarize(self, value: Any, param: int | None) -> tuple[Any, bool]:
        """Apply summarize strategy."""
        if self.summarizer is None:
            return value, False
        target_tokens = param or 200
        if isinstance(value, str) and len(value) > target_tokens * 4:
            return self._summarize_string(value, target_tokens)
        if isinstance(value, list) and len(value) > 3:
            return self._summarize_list(value, target_tokens)
        return value, False

    def _summarize_string(self, value: str, target_tokens: int) -> tuple[str, bool]:
        """Summarize a string value."""
        try:
            summarized = self.summarizer.summarize(value, target_tokens)
            self._summarization_calls += 1
            return f"[Summarized]\n{summarized}", True
        except Exception:
            return self._truncate(value, target_tokens), True

    def _summarize_list(self, value: list, target_tokens: int) -> tuple[Any, bool]:
        """Summarize a list value."""
        list_text = "\n".join(
            f"- {item}" if isinstance(item, str)
            else f"- {yaml.dump(item, default_flow_style=True).strip()}"
            for item in value
        )
        try:
            summarized = self.summarizer.summarize(list_text, target_tokens)
            self._summarization_calls += 1
            return f"[Summarized from {len(value)} items]\n{summarized}", True
        except Exception:
            return value[:3], True

    def _apply_rule(
        self, context: dict[str, Any], rule: CompactionRule
    ) -> tuple[dict[str, Any], bool]:
        """
        Apply a compaction rule to the context.

        Returns (new_context, was_applied).
        """
        parts = rule.section.split(".")
        parent, key = self._navigate_to_section(context, parts)
        if parent is None:
            return context, False

        value = parent[key]
        result = dict(context)
        result_parent = self._create_result_parent(result, parts)

        # Strategy dispatch
        strategy_handlers = {
            CompactionStrategy.TRUNCATE: self._apply_truncate,
            CompactionStrategy.TRUNCATE_MIDDLE: self._apply_truncate_middle,
            CompactionStrategy.KEEP_FIRST: self._apply_keep_first,
            CompactionStrategy.KEEP_LAST: self._apply_keep_last,
            CompactionStrategy.SUMMARIZE: self._apply_summarize,
        }

        if rule.strategy == CompactionStrategy.REMOVE:
            del result_parent[key]
            return result, True

        handler = strategy_handlers.get(rule.strategy)
        if handler:
            new_value, applied = handler(value, rule.param)
            if applied:
                result_parent[key] = new_value
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

    def get_section_tokens(self, context: dict[str, Any]) -> dict[str, int]:
        """Get token breakdown by top-level section."""
        breakdown: dict[str, int] = {}
        for key, value in context.items():
            section_yaml = yaml.dump({key: value}, default_flow_style=False)
            breakdown[key] = len(section_yaml) // 4
        return breakdown

    def set_summarizer(self, summarizer: Summarizer) -> None:
        """
        Set the LLM summarizer for SUMMARIZE strategy.

        Args:
            summarizer: Object implementing the Summarizer protocol
        """
        self.summarizer = summarizer

    def get_summarization_stats(self) -> dict[str, int]:
        """Get summarization usage statistics."""
        return {
            "summarization_calls": self._summarization_calls,
        }

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self._summarization_calls = 0


class SimpleLLMSummarizer:
    """
    Simple LLM-based summarizer using the AgentForge LLM client.

    This is a reference implementation of the Summarizer protocol.
    For production use, consider caching and rate limiting.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        system_prompt: str | None = None,
    ):
        """
        Initialize the summarizer.

        Args:
            model: Model to use for summarization
            system_prompt: Custom system prompt (uses default if not provided)
        """
        self.model = model
        self.system_prompt = system_prompt or (
            "You are a context summarizer. Your task is to condense the provided "
            "content into a brief summary that preserves the most important information. "
            "Focus on key facts, decisions, and outcomes. Be concise but accurate."
        )
        self._client = None

    def _get_client(self):
        """Lazy-load the LLM client."""
        if self._client is None:
            try:
                from ..llm import LLMClientFactory
                self._client = LLMClientFactory.create(model=self.model)
            except ImportError as e:
                raise RuntimeError(
                    "LLM client not available. Install agentforge with LLM support."
                ) from e
        return self._client

    def summarize(self, content: str, max_tokens: int) -> str:
        """
        Summarize content using an LLM.

        Args:
            content: Text content to summarize
            max_tokens: Maximum tokens for the summary

        Returns:
            Summarized text
        """
        client = self._get_client()

        prompt = (
            f"Summarize the following content in approximately {max_tokens} tokens "
            f"(about {max_tokens * 4} characters). Preserve the most important "
            f"information:\n\n{content}"
        )

        response = client.complete(
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens * 2,  # Allow some buffer
        )

        return response.content or content[:max_tokens * 4]


# Rules that include summarization as a last resort
SUMMARIZE_RULES: list[CompactionRule] = [
    # Phase 1-6: Same as default rules
    *DEFAULT_RULES,
    # Phase 7: Summarize large sections as last resort
    CompactionRule("action_history", CompactionStrategy.SUMMARIZE, 150, priority=11),
    CompactionRule("context_analysis", CompactionStrategy.SUMMARIZE, 200, priority=12),
    CompactionRule("understanding", CompactionStrategy.SUMMARIZE, 100, priority=13),
]
