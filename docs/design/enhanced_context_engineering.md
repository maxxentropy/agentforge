# Enhanced Context Engineering System - Architectural Design

## Document Information

| Attribute | Value |
|-----------|-------|
| Status | PROPOSED |
| Author | Software Architect |
| Created | 2025-12-31 |
| Target Module | `src/agentforge/core/harness/minimal_context/` |

---

## 1. Executive Summary

This document describes the architectural design for an enhanced context engineering system that replaces the existing semi-structured prose approach with a fully typed, validated system. The design achieves:

- **~50% token reduction** through structured schemas eliminating redundant markup
- **Improved reproducibility** via typed Pydantic models with validation
- **Better loop detection** through semantic analysis and error cycling detection
- **Explicit state management** via a formal phase machine with guards
- **Fact-based understanding** extracting conclusions rather than storing raw outputs

### Design Philosophy

> "The best architecture is the simplest one that will still work in 2 years."

We achieve this by:
1. Building on existing patterns rather than replacing them wholesale
2. Using composition over inheritance for flexibility
3. Keeping the stateless execution model (disk-based persistence)
4. Maintaining backward compatibility with existing workflows

---

## 2. Current System Analysis

### Existing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MinimalContextFixWorkflow                     │
├─────────────────────────────────────────────────────────────────┤
│  fix_violation()                                                 │
│    ├─> create_task (TaskStateStore)                             │
│    ├─> precompute_violation_context()                           │
│    └─> executor.run_until_complete()                            │
│           ├─> context_builder.build_messages()                  │
│           ├─> LLM call                                          │
│           ├─> parse action                                      │
│           ├─> execute action                                    │
│           └─> update state                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Current Strengths (PRESERVE)

1. **Stateless Execution**: Each step loads state fresh from disk
2. **Token Budget**: Hard limits per section (8K total)
3. **Pre-computed Context**: AST analysis before agent starts
4. **Test Verification**: Auto-revert on test regression
5. **Adaptive Budget**: Runaway detection, progress extension

### Current Weaknesses (ADDRESS)

1. **Semi-structured Prose**: YAML strings with inconsistent formats
2. **Raw Tool Output**: Entire outputs stored, wasting tokens
3. **Simple Loop Detection**: Only catches identical repeated failures
4. **Enum-based Phases**: No explicit transitions or guards
5. **Action Menu**: No preconditions or postconditions

---

## 3. Target Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Enhanced Context System                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ context_     │  │ understanding │  │ loop_        │              │
│  │ models.py    │  │ .py          │  │ detector.py  │              │
│  │              │  │              │  │              │              │
│  │ AgentContext │  │ Extractor    │  │ LoopDetector │              │
│  │ TaskSpec     │  │ FactStore    │  │ ErrorCycler  │              │
│  │ ActionDef    │  │ Confidence   │  │ Suggestions  │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └────────┬────────┴────────┬────────┘                       │
│                  ▼                 ▼                                │
│         ┌──────────────────────────────────┐                       │
│         │     context_builder.py (v2)      │                       │
│         │                                  │                       │
│         │  - Builds from Pydantic models   │                       │
│         │  - Validates before API call     │                       │
│         │  - Outputs structured YAML       │                       │
│         └──────────────┬───────────────────┘                       │
│                        │                                            │
│         ┌──────────────┴───────────────────┐                       │
│         │       phase_machine.py           │                       │
│         │                                  │                       │
│         │  - Explicit state transitions    │                       │
│         │  - Guards and preconditions      │                       │
│         │  - Max steps per phase           │                       │
│         └──────────────────────────────────┘                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Designs

### 4.1 Context Models (`context_models.py`)

The foundation of the new system. All context is expressed through typed Pydantic v2 models.

#### Design Principles

1. **Immutability where possible**: Use `frozen=True` for specs
2. **Explicit serialization**: Control YAML output format
3. **Validation at boundaries**: Validate before every LLM call
4. **Composability**: Small models composed into larger ones

#### Class Hierarchy

```python
# context_models.py

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Enums and Literals
# ═══════════════════════════════════════════════════════════════════════════════

class FactCategory(str, Enum):
    """Categories of extracted facts."""
    CODE_STRUCTURE = "code_structure"    # AST-derived facts
    INFERENCE = "inference"              # LLM-derived conclusions
    PATTERN = "pattern"                  # Recognized patterns
    VERIFICATION = "verification"        # Test/check results
    ERROR = "error"                      # Error information


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

    @field_validator('confidence')
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
    parameters: Dict[str, str] = Field(default_factory=dict, description="param -> type hint")
    preconditions: List[str] = Field(default_factory=list, description="When to use")
    postconditions: List[str] = Field(default_factory=list, description="What happens after")
    phases: List[str] = Field(default_factory=list, description="Valid phases")
    value_hints: Dict[str, str] = Field(default_factory=dict, description="param -> hint")
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
    superseded_facts: List[str] = Field(default_factory=list, description="IDs of replaced facts")

    def get_active_facts(self) -> List[Fact]:
        """Get facts that haven't been superseded."""
        return [f for f in self.facts if f.id not in self.superseded_facts]

    def get_by_category(self, category: FactCategory) -> List[Fact]:
        """Get active facts in a category."""
        return [f for f in self.get_active_facts() if f.category == category]

    def get_high_confidence(self, threshold: float = 0.8) -> List[Fact]:
        """Get facts above confidence threshold."""
        return [f for f in self.get_active_facts() if f.confidence >= threshold]


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
    recent_actions: List[ActionRecord] = Field(default_factory=list, max_length=5)
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
    blocked: List[str] = Field(default_factory=list, description="Actions blocked and why")


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

    def to_yaml(self) -> str:
        """Serialize to compact YAML for LLM context."""
        import yaml

        # Build output dict with only non-empty fields
        output = {
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
                {"step": a.step, "action": a.action, "result": a.result.value, "summary": a.summary}
                for a in self.state.recent_actions[-3:]
            ]

        return yaml.dump(output, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _format_understanding(self) -> Dict[str, Any]:
        """Format understanding for context."""
        active_facts = self.state.understanding.get_active_facts()
        if not active_facts:
            return {}

        # Group by category
        by_category = {}
        for fact in active_facts:
            cat = fact.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f"{fact.statement} (conf: {fact.confidence})")

        return by_category

    def _format_actions(self) -> List[Dict[str, str]]:
        """Format available actions for context."""
        return [
            {"name": a.name, "when": "; ".join(a.preconditions) if a.preconditions else a.description}
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
```

#### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Pydantic v2 | Better performance, native Python type hints |
| `frozen=True` for specs | Immutability prevents accidental mutation |
| Facts over raw data | ~50% token reduction, better signal/noise |
| Confidence scores | Enables intelligent fact pruning |
| Action preconditions | Guides agent toward valid actions |

---

### 4.2 Understanding Extractor (`understanding.py`)

Extracts structured facts from tool outputs rather than storing raw results.

#### Design Principles

1. **Conclusions, not data**: Extract "function has complexity 15" not raw AST
2. **Rule-based first**: Deterministic extraction where possible
3. **LLM fallback**: Use LLM only for ambiguous cases
4. **Confidence scoring**: Higher for deterministic, lower for inferred

#### Class Design

```python
# understanding.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable
import re
import uuid

from .context_models import Fact, FactCategory, ActionResult


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
        self.rules: List[ExtractionRule] = []

    def add_rule(self, rule: ExtractionRule) -> "ExtractionRuleSet":
        self.rules.append(rule)
        return self

    def extract(self, output: str, step: int) -> List[Fact]:
        """Apply all rules and return extracted facts."""
        facts = []
        for rule in self.rules:
            if isinstance(rule.pattern, str):
                match = re.search(rule.pattern, output, re.MULTILINE)
                if match:
                    statement = rule.extractor(output, match)
                    facts.append(Fact(
                        id=f"fact_{uuid.uuid4().hex[:8]}",
                        category=rule.category,
                        statement=statement,
                        confidence=rule.confidence,
                        source=f"{self.tool_name}:{rule.name}",
                        step=step,
                    ))
            elif callable(rule.pattern):
                if rule.pattern(output):
                    statement = rule.extractor(output, None)
                    facts.append(Fact(
                        id=f"fact_{uuid.uuid4().hex[:8]}",
                        category=rule.category,
                        statement=statement,
                        confidence=rule.confidence,
                        source=f"{self.tool_name}:{rule.name}",
                        step=step,
                    ))
        return facts


# ═══════════════════════════════════════════════════════════════════════════════
# Built-in Rule Sets
# ═══════════════════════════════════════════════════════════════════════════════

def _build_conformance_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from conformance check output."""
    rules = ExtractionRuleSet("run_check")

    # Check passed
    rules.add_rule(ExtractionRule(
        name="check_passed",
        pattern=r"(Check PASSED|All checks passed|\u2713)",
        category=FactCategory.VERIFICATION,
        confidence=1.0,
        extractor=lambda out, m: "Conformance check passed",
    ))

    # Check failed with complexity
    rules.add_rule(ExtractionRule(
        name="complexity_violation",
        pattern=r"Function '([^']+)' has complexity (\d+)",
        category=FactCategory.VERIFICATION,
        confidence=1.0,
        extractor=lambda out, m: f"Function '{m.group(1)}' has cyclomatic complexity {m.group(2)} (threshold exceeded)",
    ))

    # Check failed with line count
    rules.add_rule(ExtractionRule(
        name="length_violation",
        pattern=r"Function '([^']+)' has (\d+) lines",
        category=FactCategory.VERIFICATION,
        confidence=1.0,
        extractor=lambda out, m: f"Function '{m.group(1)}' has {m.group(2)} lines (threshold exceeded)",
    ))

    # Violation count
    rules.add_rule(ExtractionRule(
        name="violation_count",
        pattern=r"Violations?\s*\((\d+)\)",
        category=FactCategory.VERIFICATION,
        confidence=1.0,
        extractor=lambda out, m: f"Total violations: {m.group(1)}",
    ))

    return rules


def _build_test_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from test output."""
    rules = ExtractionRuleSet("run_tests")

    # All tests passed
    rules.add_rule(ExtractionRule(
        name="tests_passed",
        pattern=r"(\d+) passed",
        category=FactCategory.VERIFICATION,
        confidence=1.0,
        extractor=lambda out, m: f"Tests passed: {m.group(1)}",
    ))

    # Tests failed
    rules.add_rule(ExtractionRule(
        name="tests_failed",
        pattern=r"(\d+) failed",
        category=FactCategory.VERIFICATION,
        confidence=1.0,
        extractor=lambda out, m: f"Tests failed: {m.group(1)}",
    ))

    # Specific test failure
    rules.add_rule(ExtractionRule(
        name="test_failure_detail",
        pattern=r"FAILED\s+([^\s]+)::",
        category=FactCategory.ERROR,
        confidence=0.9,
        extractor=lambda out, m: f"Test failure in: {m.group(1)}",
    ))

    return rules


def _build_edit_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from file edit output."""
    rules = ExtractionRuleSet("edit_file")

    # Edit succeeded
    rules.add_rule(ExtractionRule(
        name="edit_success",
        pattern=r"(Edited|Modified|Updated)\s+([^\s:]+)",
        category=FactCategory.CODE_STRUCTURE,
        confidence=1.0,
        extractor=lambda out, m: f"File modified: {m.group(2)}",
    ))

    # Edit failed - not found
    rules.add_rule(ExtractionRule(
        name="edit_not_found",
        pattern=r"(old_text not found|text to replace not found)",
        category=FactCategory.ERROR,
        confidence=1.0,
        extractor=lambda out, m: "Edit failed: target text not found in file",
    ))

    return rules


def _build_extract_function_rules() -> ExtractionRuleSet:
    """Rules for extracting facts from extract_function output."""
    rules = ExtractionRuleSet("extract_function")

    # Extraction succeeded
    rules.add_rule(ExtractionRule(
        name="extraction_success",
        pattern=r"Extracted.*?'([^']+)'.*?lines?\s*(\d+)-(\d+)",
        category=FactCategory.CODE_STRUCTURE,
        confidence=1.0,
        extractor=lambda out, m: f"Extracted function '{m.group(1)}' from lines {m.group(2)}-{m.group(3)}",
    ))

    # Extraction failed - control flow
    rules.add_rule(ExtractionRule(
        name="extraction_control_flow",
        pattern=r"(cannot extract|control flow|early return|break|continue)",
        category=FactCategory.ERROR,
        confidence=0.95,
        extractor=lambda out, m: "Extraction blocked by control flow (returns/breaks in selection)",
    ))

    # Check passed after extraction
    rules.add_rule(ExtractionRule(
        name="post_extraction_check_passed",
        pattern=r"Check PASSED",
        category=FactCategory.VERIFICATION,
        confidence=1.0,
        extractor=lambda out, m: "Conformance check passed after extraction",
    ))

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

    def __init__(self, llm_extractor: Optional[Callable[[str, str], List[Dict]]] = None):
        """
        Initialize extractor.

        Args:
            llm_extractor: Optional callable for LLM-based extraction
                          Signature: (tool_name, output) -> List[{statement, category, confidence}]
        """
        self.llm_extractor = llm_extractor
        self.rule_sets: Dict[str, ExtractionRuleSet] = {
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
    ) -> List[Fact]:
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
        facts = []

        # 1. Try rule-based extraction
        if tool_name in self.rule_sets:
            facts = self.rule_sets[tool_name].extract(output, step)

        # 2. Add result-based fact if no specific facts extracted
        if not facts:
            facts.append(Fact(
                id=f"fact_{uuid.uuid4().hex[:8]}",
                category=FactCategory.VERIFICATION if result == ActionResult.SUCCESS else FactCategory.ERROR,
                statement=f"{tool_name} {'succeeded' if result == ActionResult.SUCCESS else 'failed'}",
                confidence=0.7,
                source=f"{tool_name}:result",
                step=step,
            ))

        # 3. LLM fallback for complex cases
        if use_llm_fallback and self.llm_extractor and len(facts) < 2:
            llm_facts = self._llm_extract(tool_name, output, step)
            facts.extend(llm_facts)

        return facts

    def _llm_extract(self, tool_name: str, output: str, step: int) -> List[Fact]:
        """Use LLM to extract facts from complex output."""
        if not self.llm_extractor:
            return []

        try:
            raw_facts = self.llm_extractor(tool_name, output)
            facts = []
            for rf in raw_facts:
                facts.append(Fact(
                    id=f"fact_{uuid.uuid4().hex[:8]}",
                    category=FactCategory(rf.get("category", "inference")),
                    statement=rf["statement"],
                    confidence=min(rf.get("confidence", 0.6), 0.8),  # Cap LLM confidence
                    source=f"{tool_name}:llm",
                    step=step,
                ))
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
        self.facts: List[Fact] = []
        self.superseded: set[str] = set()
        self.max_facts = max_facts
        self.compaction_threshold = compaction_threshold

    def add(self, fact: Fact) -> None:
        """Add a fact, potentially superseding existing facts."""
        # Check for supersession
        for existing in self.facts:
            if self._should_supersede(existing, fact):
                self.superseded.add(existing.id)
                fact = Fact(
                    **{**fact.model_dump(), "supersedes": existing.id}
                )

        self.facts.append(fact)

        # Compact if needed
        if len(self.get_active()) > self.compaction_threshold:
            self._compact()

    def add_many(self, facts: List[Fact]) -> None:
        """Add multiple facts."""
        for fact in facts:
            self.add(fact)

    def get_active(self) -> List[Fact]:
        """Get all non-superseded facts."""
        return [f for f in self.facts if f.id not in self.superseded]

    def get_by_category(self, category: FactCategory) -> List[Fact]:
        """Get active facts in a category."""
        return [f for f in self.get_active() if f.category == category]

    def get_recent(self, n: int = 5) -> List[Fact]:
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
        keep_ids = {f.id for _, f in scored[:self.max_facts]}

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

        # Recent facts more valuable
        # (Would need current_step to implement properly)

        return score

    def to_understanding(self) -> "Understanding":
        """Convert to Understanding model."""
        from .context_models import Understanding
        return Understanding(
            facts=self.facts,
            superseded_facts=list(self.superseded),
        )
```

#### Integration Points

| Component | Integration |
|-----------|-------------|
| `executor.py` | After action execution, call `extractor.extract()` |
| `state_store.py` | Persist `FactStore` to disk as `understanding.yaml` |
| `context_builder.py` | Include high-confidence facts in context |

---

### 4.3 Enhanced Loop Detector (`loop_detector.py`)

Detects semantic loops and error cycling, not just repeated identical actions.

#### Design Principles

1. **Semantic detection**: Different actions can constitute a loop if outcome is same
2. **Error cycling**: Detect A->B->A failure patterns
3. **Actionable suggestions**: Don't just detect, help break the loop
4. **Configurable thresholds**: Different tasks have different tolerance

#### Class Design

```python
# loop_detector.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from .context_models import ActionRecord, ActionResult, Fact, FactCategory


class LoopType(str, Enum):
    """Types of loops we can detect."""
    IDENTICAL_ACTION = "identical_action"      # Same action + params repeated
    SEMANTIC_LOOP = "semantic_loop"            # Different actions, same outcome
    ERROR_CYCLE = "error_cycle"                # A fails -> B fails -> A again
    NO_PROGRESS = "no_progress"                # Actions succeed but nothing changes
    OSCILLATION = "oscillation"                # Flip-flopping between states


@dataclass
class LoopDetection:
    """Result of loop detection."""
    detected: bool
    loop_type: Optional[LoopType] = None
    confidence: float = 0.0
    description: str = ""
    suggestions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)


@dataclass
class ActionSignature:
    """
    Semantic signature of an action for comparison.

    Two actions with the same signature are considered "semantically equivalent"
    even if their exact parameters differ.
    """
    action_type: str           # e.g., "edit", "extract", "check"
    target_file: Optional[str] # Normalized file path
    target_entity: Optional[str]  # Function/class name
    outcome: ActionResult
    error_category: Optional[str] = None  # Normalized error type

    def matches(self, other: "ActionSignature", strict: bool = False) -> bool:
        """Check if signatures match."""
        if self.action_type != other.action_type:
            return False
        if self.outcome != other.outcome:
            return False
        if strict:
            return self.target_file == other.target_file and self.target_entity == other.target_entity
        return True


class LoopDetector:
    """
    Detects various types of loops in agent execution.

    Goes beyond simple "same action repeated" to detect:
    - Semantic loops (different actions with same result)
    - Error cycling (A->B->A pattern)
    - No-progress loops (actions succeed but state unchanged)
    - Oscillation (flip-flopping between states)
    """

    def __init__(
        self,
        identical_threshold: int = 3,
        semantic_threshold: int = 4,
        cycle_threshold: int = 2,
        no_progress_threshold: int = 4,
    ):
        """
        Initialize detector with configurable thresholds.

        Args:
            identical_threshold: Consecutive identical actions to trigger
            semantic_threshold: Semantically similar actions to trigger
            cycle_threshold: Error cycles (A->B->A) to trigger
            no_progress_threshold: No-progress steps to trigger
        """
        self.identical_threshold = identical_threshold
        self.semantic_threshold = semantic_threshold
        self.cycle_threshold = cycle_threshold
        self.no_progress_threshold = no_progress_threshold

        # State tracking
        self._action_history: List[ActionSignature] = []
        self._outcome_history: List[str] = []  # Normalized outcomes
        self._progress_markers: Set[str] = set()  # Things that indicate progress

    def check(
        self,
        actions: List[ActionRecord],
        facts: Optional[List[Fact]] = None,
    ) -> LoopDetection:
        """
        Check for loops in recent actions.

        Args:
            actions: Recent action records (most recent last)
            facts: Recent facts for context

        Returns:
            LoopDetection with results and suggestions
        """
        if len(actions) < 2:
            return LoopDetection(detected=False)

        # Extract signatures for comparison
        signatures = [self._to_signature(a) for a in actions]

        # Check each loop type in order of specificity

        # 1. Identical action loop (most specific)
        identical_result = self._check_identical(actions)
        if identical_result.detected:
            return identical_result

        # 2. Error cycle detection
        cycle_result = self._check_error_cycle(signatures)
        if cycle_result.detected:
            return cycle_result

        # 3. Semantic loop (different actions, same outcome)
        semantic_result = self._check_semantic_loop(signatures, facts)
        if semantic_result.detected:
            return semantic_result

        # 4. No-progress loop
        no_progress_result = self._check_no_progress(actions, facts)
        if no_progress_result.detected:
            return no_progress_result

        return LoopDetection(detected=False)

    def _to_signature(self, action: ActionRecord) -> ActionSignature:
        """Convert action record to semantic signature."""
        # Determine action type
        action_type = self._categorize_action(action.action)

        # Extract target info
        target_file = action.target
        target_entity = action.parameters.get("function_name") or action.parameters.get("source_function")

        # Categorize error if present
        error_category = None
        if action.error:
            error_category = self._categorize_error(action.error)

        return ActionSignature(
            action_type=action_type,
            target_file=target_file,
            target_entity=target_entity,
            outcome=action.result,
            error_category=error_category,
        )

    def _categorize_action(self, action_name: str) -> str:
        """Categorize action into semantic groups."""
        categories = {
            "edit": ["edit_file", "replace_lines", "insert_lines", "write_file"],
            "extract": ["extract_function", "simplify_conditional"],
            "check": ["run_check", "run_conformance_check", "run_tests"],
            "read": ["read_file", "load_context"],
            "complete": ["complete", "escalate", "cannot_fix"],
        }
        for category, actions in categories.items():
            if action_name in actions:
                return category
        return action_name

    def _categorize_error(self, error: str) -> str:
        """Categorize error into semantic groups."""
        error_lower = error.lower()
        if "not found" in error_lower:
            return "not_found"
        if "syntax" in error_lower:
            return "syntax_error"
        if "control flow" in error_lower or "cannot extract" in error_lower:
            return "extraction_blocked"
        if "broke tests" in error_lower or "reverted" in error_lower:
            return "test_regression"
        return "other"

    def _check_identical(self, actions: List[ActionRecord]) -> LoopDetection:
        """Check for identical repeated actions."""
        if len(actions) < self.identical_threshold:
            return LoopDetection(detected=False)

        recent = actions[-self.identical_threshold:]

        # All same action name
        if len(set(a.action for a in recent)) != 1:
            return LoopDetection(detected=False)

        # All failures
        if not all(a.result == ActionResult.FAILURE for a in recent):
            return LoopDetection(detected=False)

        # Same parameters (or same error)
        first_params = recent[0].parameters
        first_error = recent[0].error
        all_same = True
        for a in recent[1:]:
            if a.parameters != first_params and a.error != first_error:
                all_same = False
                break

        if not all_same:
            return LoopDetection(detected=False)

        return LoopDetection(
            detected=True,
            loop_type=LoopType.IDENTICAL_ACTION,
            confidence=1.0,
            description=f"Action '{recent[0].action}' has failed {len(recent)} consecutive times with same parameters",
            suggestions=self._suggest_for_identical(recent),
            evidence=[f"Step {a.step}: {a.action} -> {a.result.value}" for a in recent],
        )

    def _check_error_cycle(self, signatures: List[ActionSignature]) -> LoopDetection:
        """Check for A->B->A error cycling patterns."""
        if len(signatures) < 3:
            return LoopDetection(detected=False)

        # Look for cycles in failure sequences
        failures = [s for s in signatures if s.outcome == ActionResult.FAILURE]
        if len(failures) < 3:
            return LoopDetection(detected=False)

        # Check for A->B->A pattern
        cycle_count = 0
        for i in range(len(failures) - 2):
            if (failures[i].action_type == failures[i+2].action_type and
                failures[i].action_type != failures[i+1].action_type):
                cycle_count += 1

        if cycle_count >= self.cycle_threshold:
            return LoopDetection(
                detected=True,
                loop_type=LoopType.ERROR_CYCLE,
                confidence=0.9,
                description=f"Detected error cycling: alternating between failed approaches",
                suggestions=[
                    "Both approaches have failed repeatedly",
                    "Consider a fundamentally different strategy",
                    "The code structure may not support the intended refactoring",
                    "Use 'cannot_fix' if no viable approach exists",
                ],
                evidence=[f"{s.action_type} ({s.error_category})" for s in failures[-5:]],
            )

        return LoopDetection(detected=False)

    def _check_semantic_loop(
        self,
        signatures: List[ActionSignature],
        facts: Optional[List[Fact]],
    ) -> LoopDetection:
        """Check for different actions with same semantic outcome."""
        if len(signatures) < self.semantic_threshold:
            return LoopDetection(detected=False)

        recent = signatures[-self.semantic_threshold:]

        # Different actions but all same outcome
        action_types = set(s.action_type for s in recent)
        if len(action_types) < 2:
            return LoopDetection(detected=False)  # Handled by identical check

        # All failures with same error category
        if all(s.outcome == ActionResult.FAILURE for s in recent):
            error_cats = set(s.error_category for s in recent if s.error_category)
            if len(error_cats) == 1:
                return LoopDetection(
                    detected=True,
                    loop_type=LoopType.SEMANTIC_LOOP,
                    confidence=0.85,
                    description=f"Multiple different approaches all failing with '{error_cats.pop()}' error",
                    suggestions=[
                        "The underlying issue persists across approaches",
                        "Re-examine the root cause before trying more variations",
                        "Consider if the violation is fixable automatically",
                    ],
                    evidence=[f"{s.action_type}: {s.error_category}" for s in recent],
                )

        # Check facts for repeated outcomes
        if facts:
            recent_facts = [f for f in facts if f.category == FactCategory.ERROR]
            error_statements = [f.statement for f in recent_facts[-5:]]
            # Check for similar error messages
            if len(set(error_statements)) == 1 and len(error_statements) >= 3:
                return LoopDetection(
                    detected=True,
                    loop_type=LoopType.SEMANTIC_LOOP,
                    confidence=0.8,
                    description="Different actions producing identical error outcome",
                    suggestions=["Address the common error before continuing"],
                    evidence=error_statements[:3],
                )

        return LoopDetection(detected=False)

    def _check_no_progress(
        self,
        actions: List[ActionRecord],
        facts: Optional[List[Fact]],
    ) -> LoopDetection:
        """Check for successful actions that don't advance the goal."""
        if len(actions) < self.no_progress_threshold:
            return LoopDetection(detected=False)

        recent = actions[-self.no_progress_threshold:]

        # Actions succeeded but all are just reading/checking
        non_mutating = {"read_file", "load_context", "run_check", "run_tests"}
        if all(a.action in non_mutating for a in recent):
            return LoopDetection(
                detected=True,
                loop_type=LoopType.NO_PROGRESS,
                confidence=0.75,
                description=f"Last {len(recent)} actions were read/check operations with no modifications",
                suggestions=[
                    "Analysis phase appears complete",
                    "Make an actual code modification",
                    "Use extract_function or edit_file to fix the violation",
                ],
                evidence=[f"Step {a.step}: {a.action}" for a in recent],
            )

        # Check if verification state hasn't changed
        if facts:
            verification_facts = [
                f for f in facts
                if f.category == FactCategory.VERIFICATION and "check" in f.statement.lower()
            ]
            if len(verification_facts) >= 3:
                # Same check result repeated
                statements = [f.statement for f in verification_facts[-3:]]
                if len(set(statements)) == 1:
                    return LoopDetection(
                        detected=True,
                        loop_type=LoopType.NO_PROGRESS,
                        confidence=0.7,
                        description="Verification status unchanged despite actions",
                        suggestions=["Actions are not affecting the violation"],
                        evidence=statements,
                    )

        return LoopDetection(detected=False)

    def _suggest_for_identical(self, actions: List[ActionRecord]) -> List[str]:
        """Generate suggestions for breaking identical action loops."""
        action = actions[0].action
        error = actions[0].error or ""

        suggestions = []

        if action == "edit_file":
            if "not found" in error.lower():
                suggestions.extend([
                    "The text to replace may have changed - re-read the file",
                    "Use replace_lines with line numbers instead of text matching",
                    "Check for whitespace differences (tabs vs spaces)",
                ])
            else:
                suggestions.append("Try a different edit approach")

        elif action == "extract_function":
            if "control flow" in error.lower():
                suggestions.extend([
                    "The selected lines contain early returns or breaks",
                    "Try simplify_conditional first to restructure the code",
                    "Select a different range that doesn't cross control flow boundaries",
                ])
            else:
                suggestions.extend([
                    "Check that line numbers are still valid (file may have changed)",
                    "Re-analyze the function to get updated extraction suggestions",
                ])

        elif action in ("run_check", "run_tests"):
            suggestions.extend([
                "Repeated checking without modification won't change the result",
                "Make a code change before checking again",
            ])

        # Generic suggestions
        if not suggestions:
            suggestions = [
                "Try a fundamentally different approach",
                "Re-analyze the problem from scratch",
                "Consider using 'escalate' if stuck",
            ]

        return suggestions

    def get_summary(self, actions: List[ActionRecord]) -> Dict[str, any]:
        """Get summary statistics about action patterns."""
        if not actions:
            return {"total": 0}

        by_type = defaultdict(int)
        by_result = defaultdict(int)

        for a in actions:
            by_type[a.action] += 1
            by_result[a.result.value] += 1

        return {
            "total": len(actions),
            "by_action": dict(by_type),
            "by_result": dict(by_result),
            "success_rate": by_result.get("success", 0) / len(actions),
            "most_common": max(by_type.items(), key=lambda x: x[1])[0] if by_type else None,
        }
```

#### Integration with Existing AdaptiveBudget

The `LoopDetector` replaces and extends the existing `_detect_runaway` method in `AdaptiveBudget`:

```python
# In executor.py - Updated AdaptiveBudget

class AdaptiveBudget:
    def __init__(self, ...):
        # ... existing init ...
        self.loop_detector = LoopDetector(
            identical_threshold=3,
            semantic_threshold=4,
            cycle_threshold=2,
            no_progress_threshold=4,
        )

    def check_continue(
        self,
        step_number: int,
        recent_actions: List[Dict[str, Any]],
        facts: Optional[List[Fact]] = None,
    ) -> tuple[bool, str, Optional[LoopDetection]]:
        """
        Determine if execution should continue.

        Returns:
            (should_continue, reason, loop_detection)
        """
        # Convert to ActionRecords
        records = [ActionRecord(**a) for a in recent_actions]

        # Run enhanced loop detection
        loop_result = self.loop_detector.check(records, facts)

        if loop_result.detected:
            return (
                False,
                f"LOOP DETECTED ({loop_result.loop_type.value}): {loop_result.description}",
                loop_result,
            )

        # ... rest of existing budget logic ...
```

---

### 4.4 Phase Machine (`phase_machine.py`)

Replaces the `TaskPhase` enum with an explicit state machine with guards and transitions.

#### Design Principles

1. **Explicit transitions**: Every phase change must go through a defined transition
2. **Guards**: Preconditions that must be true before transition
3. **Max steps**: Hard limits per phase prevent getting stuck
4. **Phase-specific success**: Clear criteria for phase completion

#### Class Design

```python
# phase_machine.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Any


class Phase(str, Enum):
    """Task execution phases."""
    INIT = "init"
    ANALYZE = "analyze"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    COMPLETE = "complete"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class Transition:
    """
    A transition between phases.

    Transitions have:
    - from_phase: Source phase
    - to_phase: Target phase
    - guards: List of conditions that must be true
    - on_transition: Optional callback when transition occurs
    """
    from_phase: Phase
    to_phase: Phase
    guards: List[Callable[["PhaseContext"], bool]] = field(default_factory=list)
    description: str = ""


@dataclass
class PhaseContext:
    """
    Context available to guards and transitions.

    Contains all information needed to evaluate whether a transition
    should be allowed.
    """
    current_phase: Phase
    steps_in_phase: int
    total_steps: int
    verification_passing: bool
    tests_passing: bool
    files_modified: List[str]
    facts: List[Any]  # List[Fact] from context_models
    last_action: Optional[str] = None
    last_action_result: Optional[str] = None

    def has_modifications(self) -> bool:
        return len(self.files_modified) > 0

    def has_fact_of_type(self, category: str) -> bool:
        return any(f.category.value == category for f in self.facts if hasattr(f, 'category'))


@dataclass
class PhaseConfig:
    """Configuration for a single phase."""
    phase: Phase
    max_steps: int
    success_condition: Callable[[PhaseContext], bool]
    failure_condition: Optional[Callable[[PhaseContext], bool]] = None
    description: str = ""


class PhaseMachine:
    """
    State machine for task phase management.

    Provides:
    - Explicit transition definitions
    - Guard evaluation before transitions
    - Max step enforcement per phase
    - Clear success/failure conditions
    """

    def __init__(self):
        self._transitions: Dict[Phase, List[Transition]] = {}
        self._phase_configs: Dict[Phase, PhaseConfig] = {}
        self._current_phase: Phase = Phase.INIT
        self._steps_in_phase: int = 0
        self._phase_history: List[Phase] = []

        # Initialize with default configuration
        self._setup_default_transitions()
        self._setup_default_phase_configs()

    def _setup_default_transitions(self) -> None:
        """Set up default phase transitions for fix_violation tasks."""
        # INIT -> ANALYZE: Can always analyze from init
        self.add_transition(Transition(
            from_phase=Phase.INIT,
            to_phase=Phase.ANALYZE,
            guards=[],
            description="Begin analysis",
        ))

        # INIT -> IMPLEMENT: Can skip to implement if precomputed context is rich
        self.add_transition(Transition(
            from_phase=Phase.INIT,
            to_phase=Phase.IMPLEMENT,
            guards=[lambda ctx: ctx.has_fact_of_type("code_structure")],
            description="Skip to implement when precomputed analysis available",
        ))

        # ANALYZE -> PLAN: After sufficient understanding
        self.add_transition(Transition(
            from_phase=Phase.ANALYZE,
            to_phase=Phase.PLAN,
            guards=[
                lambda ctx: ctx.steps_in_phase >= 1,
                lambda ctx: ctx.has_fact_of_type("code_structure"),
            ],
            description="Move to planning after analysis",
        ))

        # ANALYZE -> IMPLEMENT: Can skip planning
        self.add_transition(Transition(
            from_phase=Phase.ANALYZE,
            to_phase=Phase.IMPLEMENT,
            guards=[lambda ctx: ctx.has_fact_of_type("code_structure")],
            description="Skip to implement for simple cases",
        ))

        # PLAN -> IMPLEMENT: After plan is recorded
        self.add_transition(Transition(
            from_phase=Phase.PLAN,
            to_phase=Phase.IMPLEMENT,
            guards=[],
            description="Begin implementation",
        ))

        # IMPLEMENT -> VERIFY: After modifications made
        self.add_transition(Transition(
            from_phase=Phase.IMPLEMENT,
            to_phase=Phase.VERIFY,
            guards=[lambda ctx: ctx.has_modifications()],
            description="Verify changes after modification",
        ))

        # IMPLEMENT -> IMPLEMENT: Can loop in implement (self-transition)
        # This is implicit - staying in phase

        # VERIFY -> IMPLEMENT: If verification fails, go back
        self.add_transition(Transition(
            from_phase=Phase.VERIFY,
            to_phase=Phase.IMPLEMENT,
            guards=[lambda ctx: not ctx.verification_passing],
            description="Return to implement if verification fails",
        ))

        # VERIFY -> COMPLETE: Success!
        self.add_transition(Transition(
            from_phase=Phase.VERIFY,
            to_phase=Phase.COMPLETE,
            guards=[
                lambda ctx: ctx.verification_passing,
                lambda ctx: ctx.tests_passing,
            ],
            description="Complete when all checks pass",
        ))

        # Any -> FAILED: On fatal error
        for phase in [Phase.INIT, Phase.ANALYZE, Phase.PLAN, Phase.IMPLEMENT, Phase.VERIFY]:
            self.add_transition(Transition(
                from_phase=phase,
                to_phase=Phase.FAILED,
                guards=[lambda ctx: ctx.last_action_result == "fatal"],
                description="Fail on fatal error",
            ))

        # Any -> ESCALATED: When agent requests escalation
        for phase in [Phase.INIT, Phase.ANALYZE, Phase.PLAN, Phase.IMPLEMENT, Phase.VERIFY]:
            self.add_transition(Transition(
                from_phase=phase,
                to_phase=Phase.ESCALATED,
                guards=[lambda ctx: ctx.last_action in ("escalate", "cannot_fix")],
                description="Escalate to human",
            ))

    def _setup_default_phase_configs(self) -> None:
        """Set up default phase configurations."""
        self._phase_configs = {
            Phase.INIT: PhaseConfig(
                phase=Phase.INIT,
                max_steps=2,
                success_condition=lambda ctx: True,  # Always can leave init
                description="Initial setup phase",
            ),
            Phase.ANALYZE: PhaseConfig(
                phase=Phase.ANALYZE,
                max_steps=5,
                success_condition=lambda ctx: ctx.has_fact_of_type("code_structure"),
                description="Understand the code and violation",
            ),
            Phase.PLAN: PhaseConfig(
                phase=Phase.PLAN,
                max_steps=2,
                success_condition=lambda ctx: True,
                description="Plan the fix approach",
            ),
            Phase.IMPLEMENT: PhaseConfig(
                phase=Phase.IMPLEMENT,
                max_steps=15,
                success_condition=lambda ctx: ctx.verification_passing,
                failure_condition=lambda ctx: ctx.steps_in_phase >= 12 and not ctx.has_modifications(),
                description="Make code changes to fix violation",
            ),
            Phase.VERIFY: PhaseConfig(
                phase=Phase.VERIFY,
                max_steps=5,
                success_condition=lambda ctx: ctx.verification_passing and ctx.tests_passing,
                description="Verify fix is complete",
            ),
        }

    def add_transition(self, transition: Transition) -> None:
        """Add a transition to the machine."""
        if transition.from_phase not in self._transitions:
            self._transitions[transition.from_phase] = []
        self._transitions[transition.from_phase].append(transition)

    def configure_phase(self, config: PhaseConfig) -> None:
        """Configure a phase."""
        self._phase_configs[config.phase] = config

    @property
    def current_phase(self) -> Phase:
        return self._current_phase

    @property
    def steps_in_phase(self) -> int:
        return self._steps_in_phase

    def can_transition(self, to_phase: Phase, context: PhaseContext) -> bool:
        """Check if transition to target phase is allowed."""
        transitions = self._transitions.get(self._current_phase, [])

        for t in transitions:
            if t.to_phase == to_phase:
                # Check all guards
                if all(guard(context) for guard in t.guards):
                    return True

        return False

    def get_available_transitions(self, context: PhaseContext) -> List[Transition]:
        """Get all currently valid transitions."""
        transitions = self._transitions.get(self._current_phase, [])
        return [t for t in transitions if all(guard(context) for guard in t.guards)]

    def transition(self, to_phase: Phase, context: PhaseContext) -> bool:
        """
        Attempt to transition to a new phase.

        Args:
            to_phase: Target phase
            context: Current execution context

        Returns:
            True if transition succeeded, False otherwise
        """
        if not self.can_transition(to_phase, context):
            return False

        self._phase_history.append(self._current_phase)
        self._current_phase = to_phase
        self._steps_in_phase = 0

        return True

    def advance_step(self) -> None:
        """Record that a step was taken in current phase."""
        self._steps_in_phase += 1

    def should_auto_transition(self, context: PhaseContext) -> Optional[Phase]:
        """
        Check if we should automatically transition based on conditions.

        Returns target phase if auto-transition should occur, None otherwise.
        """
        config = self._phase_configs.get(self._current_phase)

        if not config:
            return None

        # Check for max steps exceeded
        if self._steps_in_phase >= config.max_steps:
            # Look for any valid transition
            available = self.get_available_transitions(context)
            if available:
                return available[0].to_phase
            # If no valid transitions and max steps hit, consider failure
            return Phase.ESCALATED

        # Check for phase failure condition
        if config.failure_condition and config.failure_condition(context):
            return Phase.FAILED

        # Check for phase success - should we advance?
        if config.success_condition(context):
            available = self.get_available_transitions(context)
            # Return the "forward" transition (not back to same or earlier phase)
            phase_order = [Phase.INIT, Phase.ANALYZE, Phase.PLAN, Phase.IMPLEMENT, Phase.VERIFY, Phase.COMPLETE]
            current_idx = phase_order.index(self._current_phase) if self._current_phase in phase_order else 0

            for t in available:
                if t.to_phase in phase_order:
                    target_idx = phase_order.index(t.to_phase)
                    if target_idx > current_idx:
                        return t.to_phase

        return None

    def get_phase_info(self) -> Dict[str, Any]:
        """Get current phase information for context."""
        config = self._phase_configs.get(self._current_phase)
        return {
            "current": self._current_phase.value,
            "steps_in_phase": self._steps_in_phase,
            "max_steps": config.max_steps if config else 0,
            "description": config.description if config else "",
            "history": [p.value for p in self._phase_history[-5:]],
        }

    def to_state(self) -> "PhaseState":
        """Convert to PhaseState model."""
        from .context_models import PhaseState
        return PhaseState(
            current_phase=self._current_phase.value,
            steps_in_phase=self._steps_in_phase,
            phase_history=[p.value for p in self._phase_history],
        )

    @classmethod
    def from_state(cls, state: "PhaseState") -> "PhaseMachine":
        """Reconstruct from persisted state."""
        machine = cls()
        machine._current_phase = Phase(state.current_phase)
        machine._steps_in_phase = state.steps_in_phase
        machine._phase_history = [Phase(p) for p in state.phase_history]
        return machine
```

#### Phase Diagram

```
                              ┌────────────┐
                              │   INIT     │
                              └─────┬──────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               │
              ┌──────────┐    ┌──────────┐         │
              │ ANALYZE  │───▶│   PLAN   │         │
              └────┬─────┘    └────┬─────┘         │
                   │               │               │
                   └───────┬───────┘               │
                           │                       │
                           ▼                       │
                    ┌──────────┐◄──────────────────┘
                    │IMPLEMENT │◄─────────┐
                    └────┬─────┘          │
                         │                │
                         ▼                │
                    ┌──────────┐          │
                    │  VERIFY  │──────────┘
                    └────┬─────┘     (fails)
                         │
                         ▼ (passes)
                    ┌──────────┐
                    │ COMPLETE │
                    └──────────┘

  [Any phase can transition to FAILED or ESCALATED]
```

---

### 4.5 Updated Context Builder (`context_builder.py` enhancements)

Enhancements to build context from new Pydantic models with validation.

#### Design Changes

1. **Build from models**: Input is typed models, not raw dicts
2. **Validation**: Validate context before every LLM call
3. **Structured output**: Output YAML from model serialization
4. **Token budget integration**: Use new models with existing budget

#### Class Design

```python
# context_builder.py (v2 additions)

from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from .context_models import (
    AgentContext, TaskSpec, StateSpec, ActionsSpec, ActionDef,
    Understanding, PhaseState, VerificationState, ViolationSpec,
)
from .understanding import FactStore
from .phase_machine import PhaseMachine, Phase
from .state_store import TaskState, TaskStateStore
from .token_budget import TokenBudget, estimate_tokens


class EnhancedContextBuilder:
    """
    Builds validated, typed context for agent steps.

    Key improvements over original ContextBuilder:
    - Works with Pydantic models
    - Validates before building
    - Produces reproducible output
    - Integrates with fact store and phase machine
    """

    def __init__(
        self,
        project_path: Path,
        state_store: TaskStateStore,
        max_tokens: int = 6000,
    ):
        self.project_path = Path(project_path)
        self.state_store = state_store
        self.max_tokens = max_tokens
        self.token_budget = TokenBudget()

    def build_context(
        self,
        task_spec: TaskSpec,
        state_spec: StateSpec,
        domain_context: Dict[str, Any],
        precomputed: Dict[str, Any],
        phase_machine: PhaseMachine,
    ) -> AgentContext:
        """
        Build complete agent context.

        Args:
            task_spec: Immutable task specification
            state_spec: Current mutable state
            domain_context: Task-type specific context
            precomputed: Pre-computed analysis
            phase_machine: Current phase machine state

        Returns:
            Validated AgentContext
        """
        # Build actions based on current phase
        actions = self._build_actions(phase_machine.current_phase, state_spec)

        # Update state with phase info
        state_spec.phase = phase_machine.to_state()

        # Build context
        context = AgentContext(
            task=task_spec,
            state=state_spec,
            actions=actions,
            domain_context=domain_context,
            precomputed=precomputed,
        )

        # Validate
        context.model_validate(context.model_dump())

        return context

    def _build_actions(self, phase: Phase, state: StateSpec) -> ActionsSpec:
        """Build available actions for current phase."""
        # Base actions always available
        base_actions = [
            ActionDef(
                name="read_file",
                description="Read file contents",
                parameters={"path": "str"},
                preconditions=["Need to examine code"],
                postconditions=["File content loaded to context"],
                phases=["init", "analyze", "implement"],
                priority=1,
            ),
            ActionDef(
                name="escalate",
                description="Request human assistance",
                parameters={"reason": "str"},
                preconditions=["Stuck or unable to proceed"],
                postconditions=["Task marked as escalated"],
                phases=["init", "analyze", "plan", "implement", "verify"],
                priority=0,
            ),
        ]

        # Phase-specific actions
        phase_actions = self._get_phase_actions(phase)

        # Filter to valid phases
        all_actions = base_actions + phase_actions
        valid_actions = [
            a for a in all_actions
            if not a.phases or phase.value in a.phases
        ]

        # Sort by priority
        valid_actions.sort(key=lambda a: a.priority, reverse=True)

        # Determine recommended action
        recommended = None
        if phase == Phase.IMPLEMENT and not state.files_modified:
            recommended = "extract_function"
        elif phase == Phase.VERIFY:
            recommended = "run_check"

        # Determine blocked actions
        blocked = []
        if phase != Phase.VERIFY or not state.verification.ready_for_completion:
            blocked.append("complete: Verification not yet passing")

        return ActionsSpec(
            available=valid_actions,
            recommended=recommended,
            blocked=blocked,
        )

    def _get_phase_actions(self, phase: Phase) -> List[ActionDef]:
        """Get actions specific to a phase."""
        if phase in (Phase.INIT, Phase.ANALYZE):
            return [
                ActionDef(
                    name="load_context",
                    description="Load additional file context",
                    parameters={"path": "str"},
                    preconditions=["Need more context about a file"],
                    phases=["init", "analyze"],
                ),
            ]

        if phase == Phase.IMPLEMENT:
            return [
                ActionDef(
                    name="extract_function",
                    description="Extract code into helper function (PREFERRED)",
                    parameters={
                        "file_path": "str",
                        "source_function": "str",
                        "start_line": "int",
                        "end_line": "int",
                        "new_function_name": "str",
                    },
                    preconditions=[
                        "Have extraction suggestions available",
                        "Reducing complexity or function length",
                    ],
                    postconditions=[
                        "Code extracted to new function",
                        "Original replaced with call",
                        "Verification auto-runs",
                    ],
                    phases=["implement"],
                    priority=10,
                ),
                ActionDef(
                    name="simplify_conditional",
                    description="Convert if/else to guard clause",
                    parameters={
                        "file_path": "str",
                        "function_name": "str",
                        "if_line": "int",
                    },
                    preconditions=["Code has nested conditionals"],
                    postconditions=["Nesting reduced"],
                    phases=["implement"],
                    priority=8,
                ),
                ActionDef(
                    name="edit_file",
                    description="Text-based file edit (fallback)",
                    parameters={
                        "path": "str",
                        "old_text": "str",
                        "new_text": "str",
                    },
                    preconditions=["Semantic tools cannot help"],
                    phases=["implement"],
                    priority=2,
                ),
                ActionDef(
                    name="replace_lines",
                    description="Replace lines by number",
                    parameters={
                        "file_path": "str",
                        "start_line": "int",
                        "end_line": "int",
                        "new_content": "str",
                    },
                    preconditions=["Need line-based replacement"],
                    phases=["implement"],
                    priority=3,
                ),
                ActionDef(
                    name="write_file",
                    description="Create or overwrite file",
                    parameters={"path": "str", "content": "str"},
                    preconditions=["Creating new file (e.g., conftest.py)"],
                    phases=["implement"],
                    priority=4,
                ),
                ActionDef(
                    name="run_check",
                    description="Run conformance check",
                    parameters={},
                    preconditions=["After making changes"],
                    postconditions=["Verification status updated"],
                    phases=["implement", "verify"],
                    priority=5,
                ),
            ]

        if phase == Phase.VERIFY:
            return [
                ActionDef(
                    name="run_check",
                    description="Run conformance check",
                    parameters={},
                    preconditions=["Verify fix worked"],
                    phases=["verify"],
                    priority=10,
                ),
                ActionDef(
                    name="run_tests",
                    description="Run test suite",
                    parameters={"path": "str (optional)"},
                    preconditions=["Verify tests still pass"],
                    phases=["verify"],
                    priority=9,
                ),
                ActionDef(
                    name="complete",
                    description="Mark task complete",
                    parameters={},
                    preconditions=["All checks passing", "All tests passing"],
                    postconditions=["Task marked complete"],
                    phases=["verify"],
                    priority=11,
                ),
            ]

        return []

    def build_messages(
        self,
        context: AgentContext,
        system_prompt: str,
    ) -> List[Dict[str, str]]:
        """
        Build messages for LLM API call.

        Args:
            context: Built and validated context
            system_prompt: Phase-appropriate system prompt

        Returns:
            List of 2 messages: system + user
        """
        # Convert context to YAML
        context_yaml = context.to_yaml()

        # Check token budget
        context_tokens = estimate_tokens(context_yaml)
        system_tokens = estimate_tokens(system_prompt)

        if context_tokens + system_tokens > self.max_tokens:
            # Compact context
            context_yaml = self._compact_context(context, self.max_tokens - system_tokens)

        # Build user message
        user_message = f"""# Context
```yaml
{context_yaml.strip()}
```

What is your NEXT action? Respond with exactly ONE action block:
```action
name: action_name
parameters:
  key: value
```"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    def _compact_context(self, context: AgentContext, target_tokens: int) -> str:
        """Compact context to fit within token budget."""
        # Priority order for compaction:
        # 1. Remove old facts (keep recent)
        # 2. Truncate precomputed
        # 3. Truncate domain context

        # Start with full context
        output = context.model_dump()

        # Remove old facts
        if context.state.understanding.facts:
            facts = context.state.understanding.get_active_facts()
            # Keep only most recent 5
            output["state"]["understanding"]["facts"] = [
                f.model_dump() for f in sorted(facts, key=lambda f: f.step, reverse=True)[:5]
            ]

        # Truncate precomputed if still too large
        yaml_str = yaml.dump(output, default_flow_style=False)
        if estimate_tokens(yaml_str) > target_tokens:
            if "precomputed" in output and "function_source" in output.get("precomputed", {}):
                # Truncate function source
                source = output["precomputed"]["function_source"]
                lines = source.split("\n")
                if len(lines) > 30:
                    output["precomputed"]["function_source"] = "\n".join(lines[:30]) + "\n... [truncated]"

        return yaml.dump(output, default_flow_style=False, allow_unicode=True)

    def get_token_breakdown(self, context: AgentContext) -> Dict[str, int]:
        """Get token counts per section."""
        yaml_str = context.to_yaml()

        # Parse YAML to get sections
        sections = yaml.safe_load(yaml_str)

        breakdown = {}
        for key, value in sections.items():
            section_yaml = yaml.dump({key: value}, default_flow_style=False)
            breakdown[key] = estimate_tokens(section_yaml)

        breakdown["total"] = estimate_tokens(yaml_str)
        return breakdown


# Backward-compatible factory
def create_enhanced_context_builder(
    project_path: Path,
    max_tokens: int = 6000,
) -> EnhancedContextBuilder:
    """Factory function for EnhancedContextBuilder."""
    state_store = TaskStateStore(project_path)
    return EnhancedContextBuilder(
        project_path=project_path,
        state_store=state_store,
        max_tokens=max_tokens,
    )
```

---

## 5. Integration Plan

### 5.1 Migration Strategy

The migration follows a **strangler fig** pattern - new components wrap and gradually replace old ones.

#### Phase 1: Add New Models (Non-Breaking)

```
Week 1-2:
├── Add context_models.py (new file)
├── Add understanding.py (new file)
├── Add loop_detector.py (new file)
├── Add phase_machine.py (new file)
└── Update __init__.py to export new classes

No changes to existing code yet.
```

#### Phase 2: Integrate Understanding Extraction

```
Week 3:
├── Modify executor.py:
│   ├── Import UnderstandingExtractor
│   ├── After _execute_action(), call extractor.extract()
│   ├── Store facts in working_memory.yaml
│   └── Backward compatible - no schema changes
└── Modify context_builder.py:
    └── Include facts in context (alongside existing format)
```

#### Phase 3: Enhance Loop Detection

```
Week 4:
├── Modify executor.py:
│   ├── Replace _detect_runaway() with LoopDetector
│   ├── Pass facts to check_continue()
│   └── Include loop suggestions in output
└── Test with existing workflows
```

#### Phase 4: Add Phase Machine

```
Week 5:
├── Modify state_store.py:
│   ├── Add phase_state field to TaskState
│   ├── Persist PhaseMachine state
│   └── Backward compatible loading
├── Modify executor.py:
│   ├── Use PhaseMachine for phase transitions
│   ├── Check guards before transitions
│   └── Respect max_steps per phase
└── Modify fix_workflow.py:
    └── Initialize PhaseMachine at task start
```

#### Phase 5: Full Context Builder Migration

```
Week 6:
├── Create EnhancedContextBuilder (new class)
├── Modify fix_workflow.py:
│   ├── Use EnhancedContextBuilder
│   ├── Build from Pydantic models
│   └── Validate before API calls
├── Keep original ContextBuilder for backward compat
└── Feature flag to switch between builders
```

### 5.2 Changes to Existing Files

#### `executor.py`

```python
# New imports
from .understanding import UnderstandingExtractor, FactStore
from .loop_detector import LoopDetector, LoopDetection
from .context_models import ActionResult

class MinimalContextExecutor:
    def __init__(self, ...):
        # ... existing init ...
        self.extractor = UnderstandingExtractor()
        self.fact_store = FactStore()

    def execute_step(self, task_id: str) -> StepOutcome:
        # ... existing code until action execution ...

        # NEW: Extract facts from result
        facts = self.extractor.extract(
            tool_name=action_name,
            output=action_result.get("output", ""),
            result=ActionResult(action_result.get("status", "failure")),
            step=state.current_step,
        )
        self.fact_store.add_many(facts)

        # ... rest of existing code ...
```

#### `state_store.py`

```python
# Add to TaskState dataclass
@dataclass
class TaskState:
    # ... existing fields ...

    # NEW: Understanding and phase state
    understanding_facts: List[Dict[str, Any]] = field(default_factory=list)
    phase_machine_state: Dict[str, Any] = field(default_factory=dict)

    def to_state_dict(self) -> Dict[str, Any]:
        return {
            # ... existing fields ...
            "understanding_facts": self.understanding_facts,
            "phase_machine_state": self.phase_machine_state,
        }
```

#### `fix_workflow.py`

```python
# New imports
from .phase_machine import PhaseMachine, Phase, PhaseContext
from .context_models import TaskSpec, ViolationSpec

class MinimalContextFixWorkflow:
    def fix_violation(self, violation_id: str, ...) -> Dict[str, Any]:
        # ... existing violation loading ...

        # NEW: Initialize phase machine
        phase_machine = PhaseMachine()

        # ... existing task creation ...

        # NEW: Build typed specs
        task_spec = TaskSpec(
            task_id=task_state.task_id,
            task_type="fix_violation",
            goal=f"Fix conformance violation {violation_id}",
            success_criteria=[...],
        )

        # Store in context for later use
        context_data["task_spec"] = task_spec.model_dump()
        context_data["phase_machine_state"] = phase_machine.to_state().model_dump()
```

### 5.3 Testing Strategy

```
Unit Tests:
├── test_context_models.py
│   ├── Test Pydantic validation
│   ├── Test YAML serialization
│   └── Test fact supersession
├── test_understanding.py
│   ├── Test rule-based extraction
│   ├── Test fact store compaction
│   └── Test confidence scoring
├── test_loop_detector.py
│   ├── Test identical action detection
│   ├── Test error cycling
│   ├── Test semantic loops
│   └── Test suggestion generation
└── test_phase_machine.py
    ├── Test transitions
    ├── Test guards
    └── Test max steps

Integration Tests:
├── test_fix_workflow_enhanced.py
│   ├── Test full workflow with new components
│   ├── Test backward compatibility
│   └── Test migration path
└── test_context_builder_v2.py
    ├── Test token budget compliance
    ├── Test context compaction
    └── Test validation
```

### 5.4 Rollback Plan

Each phase is independently deployable and rollbackable:

1. **Feature flags** control new vs old code paths
2. **State format** is backward compatible (new fields are optional)
3. **Original classes** kept alongside new ones
4. **Tests** verify both old and new paths

```python
# In fix_workflow.py
class MinimalContextFixWorkflow:
    def __init__(self, ..., use_enhanced_context: bool = False):
        self.use_enhanced_context = use_enhanced_context

    def fix_violation(self, ...):
        if self.use_enhanced_context:
            return self._fix_violation_enhanced(...)
        return self._fix_violation_legacy(...)
```

---

## 6. Token Budget Analysis

### Current vs Enhanced Comparison

| Component | Current (tokens) | Enhanced (tokens) | Savings |
|-----------|------------------|-------------------|---------|
| Task frame | 500 | 200 | 60% |
| Current state | 4500 | 2000 | 55% |
| Recent actions | 1000 | 400 | 60% |
| Verification | 200 | 100 | 50% |
| Available actions | 800 | 400 | 50% |
| **Total** | **7000** | **3100** | **56%** |

### Why Enhancement Saves Tokens

1. **Facts vs raw output**: "Tests passed: 15" vs full pytest output
2. **Typed actions**: Compact list vs verbose descriptions
3. **Structured YAML**: No redundant markup
4. **Fact supersession**: Only latest verification state

### New Budget Allocation

```python
ENHANCED_TOKEN_LIMITS = {
    "system_prompt": 800,
    "task_frame": 200,
    "understanding": 600,     # Facts, not raw data
    "verification": 100,
    "precomputed": 2000,      # AST analysis (critical)
    "recent_actions": 400,
    "available_actions": 400,
    "domain_context": 500,
    # ─────────────────────────
    # Total: 5000 max (down from 8000)
}
```

---

## 7. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Token reduction | >40% | Compare avg tokens/step |
| Loop detection rate | >90% | Manual review of stuck tasks |
| False positive loops | <5% | Tasks incorrectly stopped |
| Phase transition accuracy | >95% | Correct phase at each step |
| Backward compat | 100% | Existing tests pass |
| Fact extraction coverage | >80% | Facts extracted for tool outputs |

---

## 8. Open Questions

- [ ] Should LLM-based fact extraction be opt-in or default?
- [ ] What confidence threshold for fact inclusion in context?
- [ ] How to handle custom task types with different phases?
- [ ] Should phase machine be configurable per task type?

---

## 9. Related Documents

- ADR-xxx: Context Engineering Approach
- Current implementation: `src/agentforge/core/harness/minimal_context/`
- Research: Context engineering principles from Anthropic

---

## Appendix A: Example Context Output

### Before (Current System)

```yaml
# Task
id: fix-V-abc123
goal: Fix conformance violation V-abc123
step: 5 of 20
steps_remaining: 15
phase: implement
success_criteria:
  - Conformance check passes for the affected file
  - All existing tests continue to pass
  - Minimal changes made to fix the issue
constraints:
  - Only modify files directly related to the violation
  - Follow existing code patterns

# Current State
violation:
  id: V-abc123
  check_id: max-cyclomatic-complexity
  severity: warning
  file_path: src/agentforge/core/harness/minimal_context/fix_workflow.py
  line_number: 145
  message: "Function 'execute' has complexity 15 (max 10)"
  fix_hint: Extract helper functions to reduce complexity
target_function:
  name: execute
  lines: 120-185
  source: |
    def execute(self):
        # 65 lines of code here...

# Recent Actions
- step: 4
  action: read_file
  target: src/agentforge/core/harness/minimal_context/fix_workflow.py
  result: success
  summary: Read 2500 chars from src/agentforge/core/harness/minimal_context/fix_workflow.py
- step: 3
  action: run_check
  result: partial
  summary: "Function 'execute' has complexity 15 (max 10)"

# Verification Status
checks_passing: 0
checks_failing: 1
tests_passing: true
ready_for_completion: false

# Available Actions
- name: extract_function
  description: Extract code into helper function (PREFERRED for complexity)...
- name: simplify_conditional
  description: Convert if/else to guard clause...
# ... 8 more actions with descriptions
```

### After (Enhanced System)

```yaml
task:
  id: fix-V-abc123
  goal: Fix conformance violation V-abc123
  step: "5"
  phase: implement
  success_criteria:
    - Conformance check passes
    - Tests pass
    - Minimal changes

understanding:
  verification:
    - "Function 'execute' has cyclomatic complexity 15 (threshold exceeded) (conf: 1.0)"
  code_structure:
    - "File modified: fix_workflow.py (conf: 1.0)"

verification:
  passing: 0
  failing: 1
  tests_ok: true
  ready: false

analysis:
  violating_function: execute
  function_lines: "120-185"
  extraction_suggestions:
    - start_line: 145
      end_line: 160
      suggested_name: _handle_verification
      reason: "Logical block handling verification"

actions:
  - name: extract_function
    when: Have extraction suggestions available; Reducing complexity
  - name: run_check
    when: After making changes

recent:
  - step: 4
    action: read_file
    result: success
    summary: Read fix_workflow.py
```

**Token comparison**: ~1800 tokens (before) vs ~800 tokens (after) = **55% reduction**