"""
Context Models
==============

Pydantic v2 models for structured, validated agent context.

Key principles:
- Immutable specs (frozen=True) for task definitions
- Typed facts instead of raw tool output
- Explicit action definitions with preconditions
- Token-efficient serialization to YAML
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════


class FactCategory(str, Enum):
    """Categories of extracted facts."""

    CODE_STRUCTURE = "code_structure"  # AST-derived facts
    INFERENCE = "inference"  # LLM-derived conclusions
    PATTERN = "pattern"  # Recognized patterns
    VERIFICATION = "verification"  # Test/check results
    ERROR = "error"  # Error information


class ActionResult(str, Enum):
    """Possible action outcomes."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"


# ═══════════════════════════════════════════════════════════════════════════════
# Core Value Objects
# ═══════════════════════════════════════════════════════════════════════════════


class Fact(BaseModel):
    """
    A typed fact extracted from tool output or inference.

    Facts are the primary unit of understanding - conclusions rather than
    raw data. Each fact has a confidence score and category.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Unique fact identifier")
    category: FactCategory
    statement: str = Field(description="The fact itself, as a clear statement")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
    source: str = Field(description="What produced this fact (tool name, inference)")
    step: int = Field(description="Step when fact was established")
    supersedes: Optional[str] = Field(default=None, description="Fact ID this replaces")

    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        return round(v, 2)


class ActionDef(BaseModel):
    """
    Definition of an available action with rich metadata.

    Actions are phase-restricted and have explicit pre/postconditions.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    parameters: Dict[str, str] = Field(
        default_factory=dict, description="param -> type hint"
    )
    preconditions: List[str] = Field(default_factory=list, description="When to use")
    postconditions: List[str] = Field(
        default_factory=list, description="What happens after"
    )
    phases: List[str] = Field(default_factory=list, description="Valid phases")
    value_hints: Dict[str, str] = Field(
        default_factory=dict, description="param -> hint"
    )
    priority: int = Field(default=0, description="Higher = prefer this action")


class ActionRecord(BaseModel):
    """Record of an action that was taken."""

    step: int
    action: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: ActionResult
    summary: str
    facts_produced: List[str] = Field(default_factory=list, description="Fact IDs")
    duration_ms: Optional[int] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Specification Models (Immutable)
# ═══════════════════════════════════════════════════════════════════════════════


class TaskSpec(BaseModel):
    """
    Immutable task specification - the "what" we're trying to do.

    Created once at task start, never modified.
    """

    model_config = ConfigDict(frozen=True)

    task_id: str
    task_type: str
    goal: str
    success_criteria: List[str]
    constraints: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ViolationSpec(BaseModel):
    """Specification for a violation fix task."""

    model_config = ConfigDict(frozen=True)

    violation_id: str
    check_id: str
    file_path: str
    line_number: Optional[int] = None
    severity: str = "warning"
    message: str = ""
    fix_hint: Optional[str] = None
    test_path: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# State Models (Mutable)
# ═══════════════════════════════════════════════════════════════════════════════


class VerificationState(BaseModel):
    """Current verification status."""

    checks_passing: int = 0
    checks_failing: int = 0
    tests_passing: bool = False
    ready_for_completion: bool = False
    last_check_time: Optional[datetime] = None


class Understanding(BaseModel):
    """
    The agent's current understanding - extracted facts, not raw data.

    This is the key innovation: instead of storing tool outputs,
    we store conclusions with confidence scores.
    """

    facts: List[Fact] = Field(default_factory=list)
    superseded_facts: List[str] = Field(
        default_factory=list, description="IDs of replaced facts"
    )

    def get_active_facts(self) -> List[Fact]:
        """Get facts that haven't been superseded."""
        return [f for f in self.facts if f.id not in self.superseded_facts]

    def get_by_category(self, category: FactCategory) -> List[Fact]:
        """Get active facts in a category."""
        return [f for f in self.get_active_facts() if f.category == category]

    def get_high_confidence(self, threshold: float = 0.8) -> List[Fact]:
        """Get facts above confidence threshold."""
        return [f for f in self.get_active_facts() if f.confidence >= threshold]

    def compact(self, max_facts: int = 20) -> "Understanding":
        """
        Compact facts to stay under the maximum threshold.

        Removes low-value facts based on:
        - Confidence score
        - Category importance (VERIFICATION > ERROR > others)
        - Superseded status

        Args:
            max_facts: Maximum number of facts to keep

        Returns:
            New Understanding with compacted facts
        """
        active = self.get_active_facts()

        if len(active) <= max_facts:
            return self

        # Score facts by value
        def score_fact(fact: Fact) -> float:
            score = fact.confidence

            # Verification facts are most valuable
            if fact.category == FactCategory.VERIFICATION:
                score += 0.3

            # Error facts help avoid repeating mistakes
            if fact.category == FactCategory.ERROR:
                score += 0.2

            # Code structure facts are important for context
            if fact.category == FactCategory.CODE_STRUCTURE:
                score += 0.1

            return score

        # Sort by score (highest first) and keep top N
        scored = sorted(active, key=score_fact, reverse=True)
        keep_facts = scored[:max_facts]
        keep_ids = {f.id for f in keep_facts}

        # Mark others as superseded
        new_superseded = list(self.superseded_facts)
        for fact in active:
            if fact.id not in keep_ids:
                new_superseded.append(fact.id)

        return Understanding(
            facts=self.facts,  # Keep all facts for history
            superseded_facts=new_superseded,
        )


class PhaseState(BaseModel):
    """Current phase execution state."""

    current_phase: str = "init"
    steps_in_phase: int = 0
    phase_history: List[str] = Field(default_factory=list)
    blocked_reason: Optional[str] = None


class StateSpec(BaseModel):
    """
    Mutable task state - the "where we are" in execution.
    """

    current_step: int = 0
    phase: PhaseState = Field(default_factory=PhaseState)
    verification: VerificationState = Field(default_factory=VerificationState)
    understanding: Understanding = Field(default_factory=Understanding)
    recent_actions: List[ActionRecord] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Actions Specification
# ═══════════════════════════════════════════════════════════════════════════════


class ActionsSpec(BaseModel):
    """Available actions for current context."""

    available: List[ActionDef]
    recommended: Optional[str] = Field(default=None, description="Suggested next action")
    blocked: List[str] = Field(
        default_factory=list, description="Actions blocked and why"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Top-Level Context Model
# ═══════════════════════════════════════════════════════════════════════════════


class AgentContext(BaseModel):
    """
    Complete context for a single agent step.

    This is the root model that gets serialized to YAML for the LLM.
    All fields are typed and validated.
    """

    task: TaskSpec
    state: StateSpec
    actions: ActionsSpec

    # Task-type specific context (violation details, etc.)
    domain_context: Dict[str, Any] = Field(default_factory=dict)

    # Precomputed analysis (AST-derived, not LLM-derived)
    precomputed: Dict[str, Any] = Field(default_factory=dict)

    def estimate_tokens(self, chars_per_token: int = 4) -> int:
        """
        Estimate token count for this context.

        Uses a conservative chars_per_token estimate. For accurate counts,
        use the provider's tokenizer.

        Args:
            chars_per_token: Characters per token (default 4, conservative)

        Returns:
            Estimated token count
        """
        yaml_output = self.to_yaml()
        return len(yaml_output) // chars_per_token

    def to_yaml(self) -> str:
        """Serialize to compact YAML for LLM context."""
        # Build output dict with only non-empty fields
        output: Dict[str, Any] = {
            "task": {
                "id": self.task.task_id,
                "goal": self.task.goal,
                "step": f"{self.state.current_step}",
                "phase": self.state.phase.current_phase,
                "success_criteria": self.task.success_criteria,
            },
            "understanding": self._format_understanding(),
            "verification": {
                "passing": self.state.verification.checks_passing,
                "failing": self.state.verification.checks_failing,
                "tests_ok": self.state.verification.tests_passing,
                "ready": self.state.verification.ready_for_completion,
            },
            "actions": self._format_actions(),
        }

        # Add domain context if present
        if self.domain_context:
            output["context"] = self.domain_context

        # Add precomputed if present
        if self.precomputed:
            output["analysis"] = self.precomputed

        # Add recent actions if any
        if self.state.recent_actions:
            output["recent"] = [
                {
                    "step": a.step,
                    "action": a.action,
                    "result": a.result.value,
                    "summary": a.summary,
                }
                for a in self.state.recent_actions[-3:]
            ]

        return yaml.dump(output, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _format_understanding(self) -> Dict[str, Any]:
        """Format understanding for context."""
        active_facts = self.state.understanding.get_active_facts()
        if not active_facts:
            return {}

        # Group by category
        by_category: Dict[str, List[str]] = {}
        for fact in active_facts:
            cat = fact.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f"{fact.statement} (conf: {fact.confidence})")

        return by_category

    def _format_actions(self) -> List[Dict[str, str]]:
        """Format available actions for context."""
        return [
            {
                "name": a.name,
                "when": "; ".join(a.preconditions) if a.preconditions else a.description,
            }
            for a in self.actions.available
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# Response Format
# ═══════════════════════════════════════════════════════════════════════════════


class AgentResponse(BaseModel):
    """Expected response format from the agent."""

    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = Field(default=None, description="Brief reasoning if needed")
