"""
Working Memory Manager
======================

Manages the bounded rolling buffer of recent context items.
Items are automatically evicted (FIFO) when the buffer is full,
unless marked as pinned.

Enhanced with fact storage for the Understanding Extraction system.
"""

import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .context_models import Fact, Understanding


def _utc_now() -> datetime:
    """Get current UTC time (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


@dataclass
class WorkingMemoryItem:
    """Single item in working memory."""
    item_type: str  # "action_result", "loaded_context", "note"
    key: str  # Unique identifier
    content: Any
    added_at: datetime = field(default_factory=_utc_now)
    step: Optional[int] = None
    expires_after_steps: Optional[int] = None
    pinned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.item_type,
            "key": self.key,
            "content": self.content,
            "added_at": self.added_at.isoformat(),
            "step": self.step,
            "expires_after_steps": self.expires_after_steps,
            "pinned": self.pinned,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingMemoryItem":
        return cls(
            item_type=data["type"],
            key=data["key"],
            content=data["content"],
            added_at=datetime.fromisoformat(data["added_at"]),
            step=data.get("step"),
            expires_after_steps=data.get("expires_after_steps"),
            pinned=data.get("pinned", False),
        )

    def is_expired(self, current_step: int) -> bool:
        """Check if item has expired based on step count."""
        if self.expires_after_steps is None or self.step is None:
            return False
        return (current_step - self.step) > self.expires_after_steps


class WorkingMemoryManager:
    """
    Manages a bounded rolling buffer of context items.

    The working memory is persisted to disk and loaded fresh each step.
    Items are automatically evicted when the buffer is full (FIFO),
    unless they are pinned.
    """

    def __init__(self, task_dir: Path, max_items: int = 5):
        """
        Initialize working memory manager.

        Args:
            task_dir: Directory for the task
            max_items: Maximum items to retain
        """
        self.task_dir = Path(task_dir)
        self.max_items = max_items
        self.memory_file = self.task_dir / "working_memory.yaml"

    def _load(self) -> List[WorkingMemoryItem]:
        """Load items from disk."""
        if not self.memory_file.exists():
            return []

        with open(self.memory_file) as f:
            data = yaml.safe_load(f) or {}

        items = data.get("items", [])
        return [WorkingMemoryItem.from_dict(item) for item in items]

    def _save(self, items: List[WorkingMemoryItem]) -> None:
        """Save items to disk."""
        self.task_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "max_items": self.max_items,
            "items": [item.to_dict() for item in items],
        }

        with open(self.memory_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def add(
        self,
        item_type: str,
        key: str,
        content: Any,
        step: Optional[int] = None,
        expires_after_steps: Optional[int] = None,
        pinned: bool = False,
    ) -> None:
        """
        Add an item to working memory.

        Args:
            item_type: Type of item ("action_result", "loaded_context", "note")
            key: Unique identifier for the item
            content: The actual content
            step: Current step number
            expires_after_steps: Auto-remove after N steps
            pinned: If True, won't be evicted by FIFO
        """
        items = self._load()

        # Remove existing item with same key (update)
        items = [i for i in items if i.key != key]

        # Add new item
        new_item = WorkingMemoryItem(
            item_type=item_type,
            key=key,
            content=content,
            step=step,
            expires_after_steps=expires_after_steps,
            pinned=pinned,
        )
        items.append(new_item)

        # Evict old items if over limit
        items = self._evict_if_needed(items)

        self._save(items)

    def add_action_result(
        self,
        action: str,
        result: str,
        summary: str,
        step: int,
        target: Optional[str] = None,
    ) -> None:
        """
        Convenience method to add an action result.

        Args:
            action: Action name
            result: "success", "failure", or "partial"
            summary: One-line summary
            step: Step number
            target: Target file/resource
        """
        key = f"action_step_{step}"
        content = {
            "action": action,
            "result": result,
            "summary": summary,
            "target": target,
        }
        self.add("action_result", key, content, step=step)

    def load_context(
        self,
        context_key: str,
        content: str,
        step: int,
        expires_after_steps: int = 3,
    ) -> None:
        """
        Load additional context (e.g., full file content).

        Args:
            context_key: Key like "full_file:path/to/file.py"
            content: The loaded content
            step: Current step
            expires_after_steps: Auto-expire after N steps
        """
        self.add(
            "loaded_context",
            context_key,
            content,
            step=step,
            expires_after_steps=expires_after_steps,
        )

    def get_items(self, current_step: Optional[int] = None) -> List[WorkingMemoryItem]:
        """
        Get all items, optionally filtering expired ones.

        Args:
            current_step: If provided, filters out expired items

        Returns:
            List of WorkingMemoryItem
        """
        items = self._load()

        if current_step is not None:
            # Filter out expired items
            items = [i for i in items if not i.is_expired(current_step)]
            # Save filtered list
            self._save(items)

        return items

    def get_by_type(
        self,
        item_type: str,
        current_step: Optional[int] = None,
    ) -> List[WorkingMemoryItem]:
        """Get items of a specific type."""
        items = self.get_items(current_step)
        return [i for i in items if i.item_type == item_type]

    def get_action_results(
        self,
        limit: int = 3,
        current_step: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent action results formatted for context.

        Args:
            limit: Maximum results to return
            current_step: For filtering expired items

        Returns:
            List of action result dicts
        """
        items = self.get_by_type("action_result", current_step)

        # Sort by step descending, take most recent
        items = sorted(items, key=lambda x: x.step or 0, reverse=True)[:limit]

        # Reverse to chronological order
        items = list(reversed(items))

        return [
            {
                "step": item.step,
                "action": item.content.get("action"),
                "target": item.content.get("target"),
                "result": item.content.get("result"),
                "summary": item.content.get("summary"),
            }
            for item in items
        ]

    def get_loaded_context(
        self,
        current_step: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Get all loaded context items.

        Args:
            current_step: For filtering expired items

        Returns:
            Dict of context_key -> content
        """
        items = self.get_by_type("loaded_context", current_step)
        return {item.key: item.content for item in items}

    def remove(self, key: str) -> bool:
        """
        Remove an item by key.

        Args:
            key: Item key to remove

        Returns:
            True if item was found and removed
        """
        items = self._load()
        original_count = len(items)
        items = [i for i in items if i.key != key]

        if len(items) < original_count:
            self._save(items)
            return True
        return False

    def clear(self, keep_pinned: bool = True) -> int:
        """
        Clear all items from working memory.

        Args:
            keep_pinned: If True, keeps pinned items

        Returns:
            Number of items cleared
        """
        items = self._load()
        original_count = len(items)

        if keep_pinned:
            items = [i for i in items if i.pinned]
        else:
            items = []

        self._save(items)
        return original_count - len(items)

    def _evict_if_needed(
        self,
        items: List[WorkingMemoryItem],
    ) -> List[WorkingMemoryItem]:
        """
        Evict oldest non-pinned items if over limit.

        Args:
            items: Current items list

        Returns:
            Items list after eviction
        """
        if len(items) <= self.max_items:
            return items

        # Separate pinned and non-pinned
        pinned = [i for i in items if i.pinned]
        unpinned = [i for i in items if not i.pinned]

        # Calculate how many unpinned we can keep
        space_for_unpinned = max(0, self.max_items - len(pinned))

        # Keep most recent unpinned items
        unpinned = sorted(unpinned, key=lambda x: x.added_at, reverse=True)
        unpinned = unpinned[:space_for_unpinned]

        return pinned + unpinned

    def pin(self, key: str) -> bool:
        """
        Pin an item so it won't be evicted.

        Args:
            key: Item key to pin

        Returns:
            True if item was found and pinned
        """
        items = self._load()
        for item in items:
            if item.key == key:
                item.pinned = True
                self._save(items)
                return True
        return False

    def unpin(self, key: str) -> bool:
        """
        Unpin an item.

        Args:
            key: Item key to unpin

        Returns:
            True if item was found and unpinned
        """
        items = self._load()
        for item in items:
            if item.key == key:
                item.pinned = False
                self._save(items)
                return True
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # Fact Storage (Enhanced Context Engineering)
    # ═══════════════════════════════════════════════════════════════════════════

    def add_fact(
        self,
        fact_id: str,
        category: str,
        statement: str,
        confidence: float,
        source: str,
        step: int,
        supersedes: Optional[str] = None,
    ) -> None:
        """
        Add a fact to working memory.

        Facts are stored with item_type="fact" and are used by the
        Understanding Extraction system.

        Args:
            fact_id: Unique identifier for the fact
            category: Fact category (code_structure, inference, pattern, verification, error)
            statement: The fact statement
            confidence: Confidence score 0.0-1.0
            source: What produced this fact
            step: Step when fact was established
            supersedes: ID of fact this replaces (if any)
        """
        content = {
            "id": fact_id,
            "category": category,
            "statement": statement,
            "confidence": confidence,
            "source": source,
            "supersedes": supersedes,
        }
        # Facts don't expire by step count but can be superseded
        self.add(
            item_type="fact",
            key=f"fact:{fact_id}",
            content=content,
            step=step,
            pinned=confidence >= 0.9,  # High-confidence facts are pinned
        )

    def add_facts_from_list(self, facts: List["Fact"], step: int) -> None:
        """
        Add multiple facts from Fact model objects.

        Args:
            facts: List of Fact model objects
            step: Current step number
        """
        for fact in facts:
            self.add_fact(
                fact_id=fact.id,
                category=fact.category.value if hasattr(fact.category, 'value') else str(fact.category),
                statement=fact.statement,
                confidence=fact.confidence,
                source=fact.source,
                step=step,
                supersedes=fact.supersedes,
            )

    def get_facts(
        self,
        current_step: Optional[int] = None,
        category: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Get facts from working memory.

        Args:
            current_step: For filtering expired items
            category: Optional category filter
            min_confidence: Minimum confidence threshold

        Returns:
            List of fact dicts
        """
        items = self.get_by_type("fact", current_step)

        facts = []
        superseded_ids = set()

        # First pass: collect superseded IDs
        for item in items:
            if item.content.get("supersedes"):
                superseded_ids.add(item.content["supersedes"])

        # Second pass: filter facts
        for item in items:
            fact_id = item.content.get("id")
            if fact_id in superseded_ids:
                continue  # Skip superseded facts

            if category and item.content.get("category") != category:
                continue

            if item.content.get("confidence", 0) < min_confidence:
                continue

            facts.append({
                "id": fact_id,
                "category": item.content.get("category"),
                "statement": item.content.get("statement"),
                "confidence": item.content.get("confidence"),
                "source": item.content.get("source"),
                "step": item.step,
            })

        # Sort by step (most recent first) then by confidence
        facts.sort(key=lambda f: (-f.get("step", 0), -f.get("confidence", 0)))

        return facts

    def get_high_confidence_facts(
        self,
        current_step: Optional[int] = None,
        threshold: float = 0.8,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get high-confidence facts for context inclusion.

        Args:
            current_step: For filtering expired items
            threshold: Minimum confidence threshold
            limit: Maximum facts to return

        Returns:
            List of fact dicts sorted by confidence
        """
        facts = self.get_facts(current_step, min_confidence=threshold)
        return facts[:limit]

    def get_facts_for_context(
        self,
        current_step: Optional[int] = None,
    ) -> Dict[str, List[str]]:
        """
        Get facts formatted for context builder.

        Returns facts grouped by category with just the statements.

        Args:
            current_step: For filtering expired items

        Returns:
            Dict mapping category -> list of statements
        """
        facts = self.get_high_confidence_facts(current_step, threshold=0.7, limit=15)

        by_category: Dict[str, List[str]] = {}
        for fact in facts:
            cat = fact.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            statement = fact.get("statement", "")
            conf = fact.get("confidence", 0)
            by_category[cat].append(f"{statement} (conf: {conf:.2f})")

        return by_category

    def clear_facts(self) -> int:
        """
        Clear all facts from working memory.

        Returns:
            Number of facts cleared
        """
        items = self._load()
        original_count = len([i for i in items if i.item_type == "fact"])
        items = [i for i in items if i.item_type != "fact"]
        self._save(items)
        return original_count
