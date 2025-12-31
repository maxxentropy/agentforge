"""
Token Budget Enforcement
========================

Enforces hard token limits for each context component.
Ensures total context never exceeds 8K tokens.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# Hard limits for each context section (legacy)
TOKEN_BUDGET_LIMITS = {
    "system_prompt": 1000,
    "task_frame": 500,
    "current_state": 4500,  # Largest allocation
    "recent_actions": 1000,
    "verification_status": 200,
    "available_actions": 800,
    # ─────────────────────────
    # Total: 8000 max
}

# Enhanced token budget (Phase 6) - 40% reduction via fact-based context
ENHANCED_TOKEN_LIMITS = {
    "system_prompt": 800,       # Reduced - more focused prompts
    "task_frame": 200,          # Reduced - typed specs are compact
    "understanding": 600,       # NEW - facts, not raw data
    "verification": 100,        # Reduced - just status
    "precomputed": 2000,        # AST analysis (critical for refactoring)
    "recent_actions": 400,      # Reduced - typed ActionRecords
    "available_actions": 400,   # Reduced - phase-filtered
    "domain_context": 500,      # Task-specific context
    # ─────────────────────────
    # Total: 5000 max (down from 8000)
}

# Approximate tokens per character (conservative estimate)
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses a conservative 4 chars/token estimate.
    For accurate counts, use the provider's tokenizer.
    """
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


@dataclass
class BudgetAllocation:
    """Token allocation for a content section."""
    section: str
    content: str
    estimated_tokens: int
    budget: int
    over_budget: bool
    compressed: bool = False


class TokenBudget:
    """
    Enforces token budget limits with compression strategies.
    """

    def __init__(self, limits: Optional[Dict[str, int]] = None):
        """
        Initialize with optional custom limits.

        Args:
            limits: Custom token limits by section
        """
        self.limits = limits or TOKEN_BUDGET_LIMITS.copy()
        self.total_limit = sum(self.limits.values())

    def check_allocation(self, section: str, content: str) -> BudgetAllocation:
        """
        Check if content fits within section budget.

        Args:
            section: Section name
            content: Content to check

        Returns:
            BudgetAllocation with status
        """
        budget = self.limits.get(section, 500)
        tokens = estimate_tokens(content)

        return BudgetAllocation(
            section=section,
            content=content,
            estimated_tokens=tokens,
            budget=budget,
            over_budget=tokens > budget,
        )

    def compress_to_fit(self, section: str, content: str) -> Tuple[str, bool]:
        """
        Compress content to fit within budget.

        Args:
            section: Section name
            content: Content to compress

        Returns:
            Tuple of (compressed_content, was_compressed)
        """
        budget = self.limits.get(section, 500)
        tokens = estimate_tokens(content)

        if tokens <= budget:
            return content, False

        # Apply compression strategy based on section
        strategy = COMPRESSION_STRATEGIES.get(section, truncate_with_ellipsis)
        compressed = strategy(content, budget)

        return compressed, True

    def allocate_all(self, sections: Dict[str, str]) -> Dict[str, BudgetAllocation]:
        """
        Allocate and compress all sections.

        Args:
            sections: Dict of section name -> content

        Returns:
            Dict of section name -> BudgetAllocation
        """
        allocations = {}

        for section, content in sections.items():
            compressed, was_compressed = self.compress_to_fit(section, content)
            tokens = estimate_tokens(compressed)
            budget = self.limits.get(section, 500)

            allocations[section] = BudgetAllocation(
                section=section,
                content=compressed,
                estimated_tokens=tokens,
                budget=budget,
                over_budget=tokens > budget,
                compressed=was_compressed,
            )

        return allocations

    def get_total_tokens(self, allocations: Dict[str, BudgetAllocation]) -> int:
        """Get total estimated tokens across all allocations."""
        return sum(a.estimated_tokens for a in allocations.values())

    def is_within_budget(self, allocations: Dict[str, BudgetAllocation]) -> bool:
        """Check if total is within overall budget."""
        return self.get_total_tokens(allocations) <= self.total_limit


# ═══════════════════════════════════════════════════════════════════════════════
# Compression Strategies
# ═══════════════════════════════════════════════════════════════════════════════


def truncate_with_ellipsis(content: str, budget_tokens: int) -> str:
    """Simple truncation with ellipsis."""
    max_chars = budget_tokens * CHARS_PER_TOKEN
    if len(content) <= max_chars:
        return content
    return content[:max_chars - 20] + "\n... [truncated]"


def compress_file_content(content: str, budget_tokens: int) -> str:
    """
    Compress file content, keeping first/last lines.

    Shows first N lines, middle replaced with omission marker, last M lines.
    """
    max_chars = budget_tokens * CHARS_PER_TOKEN
    if len(content) <= max_chars:
        return content

    lines = content.split("\n")
    total_lines = len(lines)

    if total_lines <= 10:
        return truncate_with_ellipsis(content, budget_tokens)

    # Keep 40% at start, 40% at end
    keep_ratio = 0.4
    target_chars = max_chars - 50  # Reserve space for omission marker
    chars_per_section = target_chars // 2

    # Build start section
    start_lines = []
    start_chars = 0
    for line in lines:
        if start_chars + len(line) > chars_per_section:
            break
        start_lines.append(line)
        start_chars += len(line) + 1

    # Build end section
    end_lines = []
    end_chars = 0
    for line in reversed(lines):
        if end_chars + len(line) > chars_per_section:
            break
        end_lines.insert(0, line)
        end_chars += len(line) + 1

    omitted = total_lines - len(start_lines) - len(end_lines)
    omission_marker = f"\n# ... [{omitted} lines omitted] ...\n"

    return "\n".join(start_lines) + omission_marker + "\n".join(end_lines)


def compress_recent_actions(content: str, budget_tokens: int) -> str:
    """
    Compress action list by keeping only most recent.

    Parses YAML-like action entries and keeps the last N that fit.
    """
    max_chars = budget_tokens * CHARS_PER_TOKEN
    if len(content) <= max_chars:
        return content

    # Split by action entry markers
    entries = content.split("- step:")
    if len(entries) <= 2:
        return truncate_with_ellipsis(content, budget_tokens)

    # Keep as many recent entries as fit
    result_entries = []
    current_chars = 0

    for entry in reversed(entries[1:]):  # Skip first empty split
        entry_text = "- step:" + entry
        if current_chars + len(entry_text) > max_chars:
            break
        result_entries.insert(0, entry_text)
        current_chars += len(entry_text)

    if len(result_entries) < len(entries) - 1:
        omitted = len(entries) - 1 - len(result_entries)
        header = f"# [{omitted} earlier actions omitted]\n\n"
        return header + "\n".join(result_entries)

    return "\n".join(result_entries)


def compress_error_message(content: str, budget_tokens: int) -> str:
    """Compress error messages to first 500 chars."""
    max_chars = min(budget_tokens * CHARS_PER_TOKEN, 500)
    if len(content) <= max_chars:
        return content

    # Keep first line and beginning of trace
    lines = content.split("\n")
    if lines:
        first_line = lines[0][:200]
        remaining = content[len(lines[0]):max_chars - len(first_line) - 20]
        return first_line + remaining + "\n... [truncated]"

    return content[:max_chars - 20] + "\n... [truncated]"


def compress_list_items(content: str, budget_tokens: int) -> str:
    """
    Compress list by keeping first N items.

    Detects YAML list format (- item) and keeps items that fit.
    """
    max_chars = budget_tokens * CHARS_PER_TOKEN
    if len(content) <= max_chars:
        return content

    lines = content.split("\n")
    result_lines = []
    current_chars = 0
    item_count = 0
    total_items = sum(1 for line in lines if line.strip().startswith("-"))

    for line in lines:
        if current_chars + len(line) > max_chars - 50:
            break
        result_lines.append(line)
        current_chars += len(line) + 1
        if line.strip().startswith("-"):
            item_count += 1

    if item_count < total_items:
        remaining = total_items - item_count
        result_lines.append(f"# ... and {remaining} more items")

    return "\n".join(result_lines)


# Mapping of sections to compression strategies
COMPRESSION_STRATEGIES = {
    "system_prompt": truncate_with_ellipsis,
    "task_frame": truncate_with_ellipsis,
    "current_state": compress_file_content,
    "recent_actions": compress_recent_actions,
    "verification_status": truncate_with_ellipsis,
    "available_actions": compress_list_items,
    "file_content": compress_file_content,
    "error_details": compress_error_message,
}
