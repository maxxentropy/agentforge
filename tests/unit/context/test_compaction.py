# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: compaction-tests

"""
Tests for CompactionManager.
"""

import pytest

from agentforge.core.context.compaction import (
    DEFAULT_RULES,
    PRESERVED_SECTIONS,
    CompactionAudit,
    CompactionManager,
    CompactionRule,
    CompactionStrategy,
)


class TestCompactionManager:
    """Tests for CompactionManager."""

    @pytest.fixture
    def manager(self):
        """Create a compaction manager with standard settings."""
        return CompactionManager(threshold=0.90, max_budget=1000)

    @pytest.fixture
    def sample_context(self):
        """Create a sample context that needs compaction."""
        return {
            "fingerprint": "project: test\nlanguage: python",
            "task": {"id": "test-001", "goal": "Fix the bug"},
            "phase": {"current": "implement", "step": 3},
            "target_source": "def foo():\n" + "    pass\n" * 100,  # Long source
            "similar_fixes": [{"name": f"fix{i}"} for i in range(20)],
            "understanding": [{"fact": f"fact{i}"} for i in range(30)],
            "recent": [{"action": f"action{i}"} for i in range(10)],
            "additional": {"extra": "data" * 50},
        }

    def test_estimate_tokens(self, manager):
        """Token estimation works correctly."""
        context = {"key": "value" * 100}
        tokens = manager.estimate_tokens(context)

        # Should be approximately len(yaml_output) / 4
        assert tokens > 0, "Expected tokens > 0"
        assert tokens < 200, "Expected tokens < 200"

    def test_no_compaction_under_threshold(self, manager):
        """No compaction needed when under threshold."""
        # Small context well under budget
        context = {"fingerprint": "small", "task": "test"}
        assert not manager.needs_compaction(context), "Assertion failed"

    def test_compaction_triggers_at_threshold(self, manager):
        """Compaction triggers when over threshold."""
        # Large context over budget
        context = {"data": "x" * 5000}  # ~1250 tokens
        assert manager.needs_compaction(context), "Expected manager.needs_compaction() to be truthy"

    def test_preserved_sections_untouched(self, manager, sample_context):
        """Preserved sections are never compacted."""
        result, audit = manager.compact(sample_context)

        # fingerprint, task, phase should be unchanged
        assert result["fingerprint"] == sample_context["fingerprint"], "Expected result['fingerprint'] to equal sample_context['fingerprint']"
        assert result["task"] == sample_context["task"], "Expected result['task'] to equal sample_context['task']"
        assert result["phase"] == sample_context["phase"], "Expected result['phase'] to equal sample_context['phase']"

    def test_custom_preserve_list(self, manager, sample_context):
        """Custom preserve list is respected."""
        result, audit = manager.compact(
            sample_context,
            preserve=["understanding"],  # Add understanding to preserve
        )

        # understanding should be unchanged
        assert result["understanding"] == sample_context["understanding"], "Expected result['understanding'] to equal sample_context['understandi..."

    def test_rules_applied_in_order(self, manager, sample_context):
        """Rules are applied in priority order."""
        result, audit = manager.compact(sample_context)

        if len(audit.rules_applied) > 1:
            # Check priorities are in order
            for i in range(len(audit.rules_applied) - 1):
                rule_i = next(
                    (r for r in DEFAULT_RULES if r.section == audit.rules_applied[i]["section"]),
                    None,
                )
                rule_j = next(
                    (r for r in DEFAULT_RULES if r.section == audit.rules_applied[i + 1]["section"]),
                    None,
                )
                if rule_i and rule_j:
                    assert rule_i.priority <= rule_j.priority, "Expected rule_i.priority <= rule_j.priority"

    def test_compaction_stops_at_budget(self, manager):
        """Compaction stops once budget is met."""
        # Context slightly over budget
        context = {
            "fingerprint": "x",
            "task": "y",
            "phase": "z",
            "data": ["item"] * 50,  # Will need compaction
        }

        manager_tight = CompactionManager(threshold=0.90, max_budget=500)
        result, audit = manager_tight.compact(context)

        # Should stop once under budget
        assert manager_tight.estimate_tokens(result) <= manager_tight.max_budget, "Expected manager_tight.estimate_toke... <= manager_tight.max_budget"


class TestCompactionStrategies:
    """Tests for individual compaction strategies."""

    @pytest.fixture
    def manager(self):
        return CompactionManager(threshold=0.90, max_budget=100)

    def test_truncate_strategy(self, manager):
        """TRUNCATE cuts string to max chars."""
        long_string = "x" * 5000
        result = manager._truncate(long_string, max_tokens=100)

        assert len(result) < len(long_string), "Expected len(result) < len(long_string)"
        assert result.endswith("... (truncated)"), "Expected result.endswith() to be truthy"

    def test_truncate_no_change_if_under(self, manager):
        """TRUNCATE doesn't change short strings."""
        short_string = "hello"
        result = manager._truncate(short_string, max_tokens=100)

        assert result == short_string, "Expected result to equal short_string"

    def test_truncate_middle_strategy(self, manager):
        """TRUNCATE_MIDDLE keeps start and end."""
        long_string = "START" + "x" * 5000 + "END"
        result = manager._truncate_middle(long_string, max_tokens=100)

        assert "START" in result[:50], "Expected 'START' in result[:50]"
        assert "END" in result[-50:], "Expected 'END' in result[-50:]"
        assert "(middle truncated)" in result, "Expected '(middle truncated)' in result"

    def test_keep_first_strategy(self):
        """KEEP_FIRST keeps first N items."""
        # Use very low budget to ensure compaction triggers
        manager = CompactionManager(
            threshold=0.10,  # Very low threshold
            max_budget=10,   # Very low budget
            rules=[
                CompactionRule("items", CompactionStrategy.KEEP_FIRST, 3, priority=1),
            ],
        )

        # Create a large list to exceed budget
        context = {"items": [{"data": f"item{i}" * 10} for i in range(20)]}
        result, _ = manager.compact(context)

        # Should be truncated to first 3
        assert len(result["items"]) == 3, "Expected len(result['items']) to equal 3"
        assert result["items"][0]["data"].startswith("item0"), "Expected result['items'][0]['data']....() to be truthy"

    def test_keep_last_strategy(self):
        """KEEP_LAST keeps last N items."""
        # Use very low budget to ensure compaction triggers
        manager = CompactionManager(
            threshold=0.10,  # Very low threshold
            max_budget=10,   # Very low budget
            rules=[
                CompactionRule("items", CompactionStrategy.KEEP_LAST, 3, priority=1),
            ],
        )

        # Create a large list to exceed budget
        context = {"items": [{"data": f"item{i}" * 10} for i in range(20)]}
        result, _ = manager.compact(context)

        # Should be truncated to last 3
        assert len(result["items"]) == 3, "Expected len(result['items']) to equal 3"
        assert result["items"][-1]["data"].startswith("item19"), "Expected result['items'][-1]['data']...() to be truthy"

    def test_remove_strategy(self):
        """REMOVE deletes the section entirely."""
        # Use very low budget to ensure compaction triggers
        manager = CompactionManager(
            threshold=0.10,  # Very low threshold
            max_budget=10,   # Very low budget
            rules=[
                CompactionRule("optional", CompactionStrategy.REMOVE, None, priority=1),
            ],
        )

        # Create large context to exceed budget
        context = {"required": "keep", "optional": "x" * 500}
        result, _ = manager.compact(context)

        assert "required" in result, "Expected 'required' in result"
        assert "optional" not in result, "Expected 'optional' not in result"


class TestCompactionAudit:
    """Tests for CompactionAudit."""

    def test_audit_to_dict(self):
        """Audit converts to dictionary correctly."""
        audit = CompactionAudit(
            original_tokens=5000,
            final_tokens=3000,
            budget=4000,
            rules_applied=[
                {"section": "data", "strategy": "truncate", "tokens_after": 3000}
            ],
        )

        result = audit.to_dict()

        assert result["applied"] is True, "Expected result['applied'] is True"
        assert result["original_tokens"] == 5000, "Expected result['original_tokens'] to equal 5000"
        assert result["final_tokens"] == 3000, "Expected result['final_tokens'] to equal 3000"
        assert result["tokens_saved"] == 2000, "Expected result['tokens_saved'] to equal 2000"

    def test_audit_no_rules_applied(self):
        """Audit shows not applied when no rules used."""
        audit = CompactionAudit(
            original_tokens=1000,
            final_tokens=1000,
            budget=4000,
            rules_applied=[],
        )

        result = audit.to_dict()

        assert result["applied"] is False, "Expected result['applied'] is False"
        assert result["tokens_saved"] == 0, "Expected result['tokens_saved'] to equal 0"


class TestCompactionRule:
    """Tests for CompactionRule."""

    def test_rule_ordering(self):
        """Rules sort by priority."""
        rules = [
            CompactionRule("c", CompactionStrategy.REMOVE, None, priority=3),
            CompactionRule("a", CompactionStrategy.REMOVE, None, priority=1),
            CompactionRule("b", CompactionStrategy.REMOVE, None, priority=2),
        ]

        sorted_rules = sorted(rules)

        assert [r.section for r in sorted_rules] == ["a", "b", "c"], "Expected [r.section for r in sorted_... to equal ['a', 'b', 'c']"

    def test_default_rules_exist(self):
        """Default rules are defined."""
        assert len(DEFAULT_RULES) > 0, "Expected len(DEFAULT_RULES) > 0"

        # Check rules have required fields
        for rule in DEFAULT_RULES:
            assert rule.section, "Expected rule.section to be truthy"
            assert rule.strategy, "Expected rule.strategy to be truthy"
            assert rule.priority >= 0, "Expected rule.priority >= 0"


class TestPreservedSections:
    """Tests for preserved section handling."""

    def test_preserved_sections_defined(self):
        """Preserved sections are defined."""
        assert "fingerprint" in PRESERVED_SECTIONS, "Expected 'fingerprint' in PRESERVED_SECTIONS"
        assert "task" in PRESERVED_SECTIONS, "Expected 'task' in PRESERVED_SECTIONS"
        assert "phase" in PRESERVED_SECTIONS, "Expected 'phase' in PRESERVED_SECTIONS"

    def test_nested_section_preserved(self):
        """Nested sections under preserved are protected."""
        manager = CompactionManager(
            threshold=0.50,
            max_budget=50,
            rules=[
                CompactionRule(
                    "fingerprint.identity", CompactionStrategy.REMOVE, None, priority=1
                ),
            ],
        )

        context = {"fingerprint": {"identity": "test", "language": "python"}}
        result, _ = manager.compact(context, preserve=["fingerprint"])

        # Nested section should be preserved
        assert "identity" in result["fingerprint"], "Expected 'identity' in result['fingerprint']"


class TestDotNotation:
    """Tests for dot notation in section paths."""

    def test_nested_section_compaction(self):
        """Nested sections can be compacted."""
        manager = CompactionManager(
            threshold=0.50,
            max_budget=100,
            rules=[
                CompactionRule(
                    "precomputed.analysis", CompactionStrategy.TRUNCATE, 50, priority=1
                ),
            ],
        )

        context = {
            "precomputed": {
                "analysis": "x" * 1000,
                "other": "keep",
            }
        }
        result, audit = manager.compact(context)

        # analysis should be truncated
        assert len(result["precomputed"]["analysis"]) < 1000, "Expected len(result['precomputed']['... < 1000"
        # other should be unchanged
        assert result["precomputed"]["other"] == "keep", "Expected result['precomputed']['other'] to equal 'keep'"

    def test_missing_nested_section_skipped(self):
        """Missing nested sections are skipped gracefully."""
        manager = CompactionManager(
            threshold=0.50,
            max_budget=100,
            rules=[
                CompactionRule(
                    "precomputed.missing", CompactionStrategy.REMOVE, None, priority=1
                ),
            ],
        )

        context = {"precomputed": {"existing": "data"}}
        result, audit = manager.compact(context)

        # Should not fail, should return unchanged
        assert result["precomputed"]["existing"] == "data", "Expected result['precomputed']['exis... to equal 'data'"


class TestSummarizeStrategy:
    """Tests for SUMMARIZE compaction strategy."""

    def test_summarize_without_summarizer_skipped(self):
        """SUMMARIZE is skipped when no summarizer is set."""
        manager = CompactionManager(
            threshold=0.10,
            max_budget=10,
            rules=[
                CompactionRule("content", CompactionStrategy.SUMMARIZE, 50, priority=1),
            ],
            summarizer=None,  # No summarizer
        )

        context = {"content": "x" * 5000}
        result, audit = manager.compact(context)

        # Should be unchanged since no summarizer
        assert result["content"] == context["content"], "Expected result['content'] to equal context['content']"
        assert len(audit.rules_applied) == 0, "Expected len(audit.rules_applied) to equal 0"

    def test_summarize_with_mock_summarizer(self):
        """SUMMARIZE calls summarizer and uses result."""

        class MockSummarizer:
            def summarize(self, content: str, max_tokens: int) -> str:
                return f"Summary of {len(content)} chars"

        manager = CompactionManager(
            threshold=0.10,
            max_budget=10,
            rules=[
                CompactionRule("content", CompactionStrategy.SUMMARIZE, 50, priority=1),
            ],
            summarizer=MockSummarizer(),
        )

        context = {"content": "x" * 5000}
        result, audit = manager.compact(context)

        assert "[Summarized]" in result["content"], "Expected '[Summarized]' in result['content']"
        assert "5000 chars" in result["content"], "Expected '5000 chars' in result['content']"
        assert manager._summarization_calls == 1, "Expected manager._summarization_calls to equal 1"

    def test_summarize_list_content(self):
        """SUMMARIZE handles list content."""

        class MockSummarizer:
            def summarize(self, content: str, max_tokens: int) -> str:
                return "Summarized list items"

        manager = CompactionManager(
            threshold=0.10,
            max_budget=10,
            rules=[
                CompactionRule("items", CompactionStrategy.SUMMARIZE, 50, priority=1),
            ],
            summarizer=MockSummarizer(),
        )

        context = {"items": [f"item{i}" for i in range(20)]}
        result, audit = manager.compact(context)

        assert "[Summarized from 20 items]" in result["items"], "Expected '[Summarized from 20 items]' in result['items']"
        assert "Summarized list items" in result["items"], "Expected 'Summarized list items' in result['items']"

    def test_summarize_fallback_on_error(self):
        """SUMMARIZE falls back to truncation on error."""

        class FailingSummarizer:
            def summarize(self, content: str, max_tokens: int) -> str:
                raise RuntimeError("Summarization failed")

        manager = CompactionManager(
            threshold=0.10,
            max_budget=10,
            rules=[
                CompactionRule("content", CompactionStrategy.SUMMARIZE, 50, priority=1),
            ],
            summarizer=FailingSummarizer(),
        )

        context = {"content": "x" * 5000}
        result, audit = manager.compact(context)

        # Should fall back to truncation
        assert "... (truncated)" in result["content"], "Expected '... (truncated)' in result['content']"
        assert len(result["content"]) < 5000, "Expected len(result['content']) < 5000"

    def test_set_summarizer_method(self):
        """set_summarizer method works correctly."""

        class MockSummarizer:
            def summarize(self, content: str, max_tokens: int) -> str:
                return "summary"

        manager = CompactionManager(threshold=0.90, max_budget=1000)
        assert manager.summarizer is None, "Expected manager.summarizer is None"

        manager.set_summarizer(MockSummarizer())
        assert manager.summarizer is not None, "Expected manager.summarizer is not None"

    def test_get_summarization_stats(self):
        """get_summarization_stats returns correct values."""

        class MockSummarizer:
            def summarize(self, content: str, max_tokens: int) -> str:
                return "summary"

        manager = CompactionManager(
            threshold=0.10,
            max_budget=10,
            rules=[
                CompactionRule("content", CompactionStrategy.SUMMARIZE, 50, priority=1),
            ],
            summarizer=MockSummarizer(),
        )

        # Initial state
        stats = manager.get_summarization_stats()
        assert stats["summarization_calls"] == 0, "Expected stats['summarization_calls'] to equal 0"

        # After compaction
        context = {"content": "x" * 5000}
        manager.compact(context)

        stats = manager.get_summarization_stats()
        assert stats["summarization_calls"] == 1, "Expected stats['summarization_calls'] to equal 1"

    def test_reset_stats(self):
        """reset_stats clears summarization counter."""

        class MockSummarizer:
            def summarize(self, content: str, max_tokens: int) -> str:
                return "summary"

        manager = CompactionManager(
            threshold=0.10,
            max_budget=10,
            rules=[
                CompactionRule("content", CompactionStrategy.SUMMARIZE, 50, priority=1),
            ],
            summarizer=MockSummarizer(),
        )

        context = {"content": "x" * 5000}
        manager.compact(context)
        assert manager._summarization_calls == 1, "Expected manager._summarization_calls to equal 1"

        manager.reset_stats()
        assert manager._summarization_calls == 0, "Expected manager._summarization_calls to equal 0"

    def test_summarize_short_content_not_changed(self):
        """SUMMARIZE doesn't change content under threshold."""

        class MockSummarizer:
            def summarize(self, content: str, max_tokens: int) -> str:
                return "should not be called"

        manager = CompactionManager(
            threshold=0.10,
            max_budget=10,
            rules=[
                CompactionRule("content", CompactionStrategy.SUMMARIZE, 500, priority=1),  # 500 tokens = 2000 chars
            ],
            summarizer=MockSummarizer(),
        )

        # Content is short (100 chars < 2000 char threshold)
        context = {"content": "x" * 100}
        result, audit = manager.compact(context)

        # Should not be summarized
        assert result["content"] == "x" * 100, "Expected result['content'] to equal 'x' * 100"
        assert manager._summarization_calls == 0, "Expected manager._summarization_calls to equal 0"


class TestSummarizeRules:
    """Tests for SUMMARIZE_RULES constant."""

    def test_summarize_rules_includes_defaults(self):
        """SUMMARIZE_RULES includes all default rules."""
        from agentforge.core.context.compaction import DEFAULT_RULES, SUMMARIZE_RULES

        default_sections = {r.section for r in DEFAULT_RULES}
        summarize_sections = {r.section for r in SUMMARIZE_RULES}

        # All default sections should be present
        assert default_sections.issubset(summarize_sections), "Expected default_sections.issubset() to be truthy"

    def test_summarize_rules_has_summarize_strategies(self):
        """SUMMARIZE_RULES includes SUMMARIZE strategy rules."""
        from agentforge.core.context.compaction import SUMMARIZE_RULES

        summarize_rules = [r for r in SUMMARIZE_RULES if r.strategy == CompactionStrategy.SUMMARIZE]

        assert len(summarize_rules) > 0, "Expected len(summarize_rules) > 0"
        # Summarize rules should have lower priority (run later)
        for rule in summarize_rules:
            assert rule.priority > 10, "Expected rule.priority > 10"# After default rules
