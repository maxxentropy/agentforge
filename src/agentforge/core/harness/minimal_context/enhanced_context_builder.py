"""
Enhanced Context Builder
========================

Builds validated, typed context for agent steps using Pydantic models.

Key improvements over original ContextBuilder:
- Works with Pydantic models for type safety and validation
- Validates context before building (fails fast on bad data)
- Produces reproducible output with deterministic ordering
- Integrates with fact store and phase machine
- Phase-aware action filtering with priorities

This follows the strangler fig pattern - can be used alongside legacy
ContextBuilder with feature flag to switch between them.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state_store import TaskStateStore, TaskState
from .token_budget import TokenBudget, estimate_tokens
from .working_memory import WorkingMemoryManager
from .phase_machine import PhaseMachine, Phase
from .context_models import (
    TaskSpec,
    StateSpec,
    ActionsSpec,
    ActionDef,
    AgentContext,
    PhaseState,
    VerificationState,
    Understanding,
    ActionRecord,
    Fact,
    FactCategory,
    ActionResult,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Action Definitions
# ═══════════════════════════════════════════════════════════════════════════════


def get_base_actions() -> List[ActionDef]:
    """Get actions available in all phases."""
    return [
        ActionDef(
            name="read_file",
            description="Read file contents",
            parameters={"path": "str"},
            preconditions=["Need to examine code"],
            postconditions=["File content loaded to context"],
            phases=["init", "analyze", "implement", "verify"],
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
        ActionDef(
            name="cannot_fix",
            description="Declare fix beyond current capabilities",
            parameters={"reason": "str"},
            preconditions=["Analyzed the issue", "Determined fix is not possible"],
            postconditions=["Task marked for human review"],
            phases=["analyze", "plan", "implement"],
            priority=0,
        ),
    ]


def get_analyze_actions() -> List[ActionDef]:
    """Get actions for analyze phase."""
    return [
        ActionDef(
            name="load_context",
            description="Load additional file context",
            parameters={"path": "str"},
            preconditions=["Need more context about a file"],
            postconditions=["File content added to context"],
            phases=["init", "analyze"],
            priority=3,
        ),
        ActionDef(
            name="search_code",
            description="Search for patterns in codebase",
            parameters={"pattern": "str", "path": "str (optional)"},
            preconditions=["Need to find related code"],
            postconditions=["Matching files listed"],
            phases=["init", "analyze"],
            priority=2,
        ),
    ]


def get_implement_actions() -> List[ActionDef]:
    """Get actions for implement phase."""
    return [
        ActionDef(
            name="extract_function",
            description="Extract code into helper function (PREFERRED for complexity)",
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
            name="replace_lines",
            description="Replace lines by number (precise edits)",
            parameters={
                "file_path": "str",
                "start_line": "int",
                "end_line": "int",
                "new_content": "str",
            },
            preconditions=["Need line-based replacement"],
            postconditions=["Lines replaced"],
            phases=["implement"],
            priority=5,
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
            postconditions=["File modified"],
            phases=["implement"],
            priority=2,
        ),
        ActionDef(
            name="write_file",
            description="Create or overwrite file",
            parameters={"path": "str", "content": "str"},
            preconditions=["Creating new file or full rewrite needed"],
            postconditions=["File created/overwritten"],
            phases=["implement"],
            priority=1,
        ),
    ]


def get_verify_actions() -> List[ActionDef]:
    """Get actions for verify phase."""
    return [
        ActionDef(
            name="run_check",
            description="Run conformance check on file",
            parameters={"file_path": "str"},
            preconditions=["Made changes to verify"],
            postconditions=["Check results updated"],
            phases=["verify"],
            priority=8,
        ),
        ActionDef(
            name="run_tests",
            description="Run tests to verify changes",
            parameters={"test_path": "str (optional)"},
            preconditions=["Made changes that might affect tests"],
            postconditions=["Test results updated"],
            phases=["verify"],
            priority=7,
        ),
        ActionDef(
            name="complete",
            description="Mark task as complete",
            parameters={"summary": "str"},
            preconditions=[
                "All checks passing",
                "All tests passing",
            ],
            postconditions=["Task marked complete"],
            phases=["verify"],
            priority=10,
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced Context Builder
# ═══════════════════════════════════════════════════════════════════════════════


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
        state_store: Optional[TaskStateStore] = None,
        max_tokens: int = 6000,
    ):
        """
        Initialize the enhanced context builder.

        Args:
            project_path: Project root path
            state_store: Task state store (created if not provided)
            max_tokens: Maximum tokens for context
        """
        self.project_path = Path(project_path)
        self.state_store = state_store or TaskStateStore(self.project_path)
        self.max_tokens = max_tokens
        self.token_budget = TokenBudget()

    def build_from_task_state(self, task_id: str) -> AgentContext:
        """
        Build AgentContext from persisted task state.

        This is the primary entry point - converts legacy TaskState
        to typed Pydantic models.

        Args:
            task_id: Task identifier

        Returns:
            Validated AgentContext
        """
        state = self.state_store.load(task_id)
        if not state:
            raise ValueError(f"Task not found: {task_id}")

        # Get phase machine
        phase_machine = state.get_phase_machine()

        # Build TaskSpec from state
        task_spec = TaskSpec(
            task_id=state.task_id,
            task_type=state.task_type,
            goal=state.goal,
            success_criteria=state.success_criteria,
            constraints=state.constraints,
            created_at=state.created_at,
        )

        # Build StateSpec from state
        state_spec = self._build_state_spec(state, phase_machine)

        # Build domain context
        domain_context = state.context_data.get("violation", {})

        # Build precomputed analysis
        precomputed = state.context_data.get("precomputed", {})

        # Build context
        return self.build_context(
            task_spec=task_spec,
            state_spec=state_spec,
            domain_context=domain_context,
            precomputed=precomputed,
            phase_machine=phase_machine,
        )

    def build_context(
        self,
        task_spec: TaskSpec,
        state_spec: StateSpec,
        domain_context: Dict[str, Any],
        precomputed: Dict[str, Any],
        phase_machine: PhaseMachine,
    ) -> AgentContext:
        """
        Build complete agent context from typed specs.

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
        state_spec = state_spec.model_copy(
            update={"phase": phase_machine.to_state()}
        )

        # Build context
        context = AgentContext(
            task=task_spec,
            state=state_spec,
            actions=actions,
            domain_context=domain_context,
            precomputed=precomputed,
        )

        # Validate (will raise on invalid data)
        context.model_validate(context.model_dump())

        return context

    def _build_state_spec(
        self,
        state: TaskState,
        phase_machine: PhaseMachine,
    ) -> StateSpec:
        """Build StateSpec from TaskState."""
        # Get recent actions from working memory
        task_dir = self.state_store._task_dir(state.task_id)
        memory_manager = WorkingMemoryManager(task_dir)

        recent_action_dicts = memory_manager.get_action_results(
            limit=3,
            current_step=state.current_step,
        )

        # Convert to ActionRecord models
        recent_actions = [
            ActionRecord(
                action=a.get("action", "unknown"),
                result=ActionResult(a.get("result", "failure")),
                summary=a.get("summary", ""),
                step=a.get("step", 0),
                target=a.get("target"),
            )
            for a in recent_action_dicts
        ]

        # Get facts from working memory
        fact_dicts = memory_manager.get_facts(
            current_step=state.current_step,
            min_confidence=0.7,
        )

        # Convert to Fact models
        facts = [
            Fact(
                id=f.get("id", ""),
                category=FactCategory(f.get("category", "inference")),
                statement=f.get("statement", ""),
                confidence=f.get("confidence", 0.5),
                source=f.get("source", "unknown"),
            )
            for f in fact_dicts
        ]

        # Build Understanding
        understanding = Understanding(facts=facts)

        # Build VerificationState
        verification = VerificationState(
            checks_passing=state.verification.checks_passing,
            checks_failing=state.verification.checks_failing,
            tests_passing=state.verification.tests_passing,
            ready_for_completion=state.verification.ready_for_completion,
            last_check_time=state.verification.last_check_time,
        )

        return StateSpec(
            current_step=state.current_step,
            phase=phase_machine.to_state(),
            verification=verification,
            understanding=understanding,
            recent_actions=recent_actions,
            files_modified=state.context_data.get("files_modified", []),
            last_updated=state.last_updated,
            error=state.error,
        )

    def _build_actions(
        self,
        phase: Phase,
        state: StateSpec,
    ) -> ActionsSpec:
        """Build available actions for current phase."""
        # Collect all actions
        all_actions = get_base_actions()

        if phase in (Phase.INIT, Phase.ANALYZE):
            all_actions.extend(get_analyze_actions())
        elif phase == Phase.IMPLEMENT:
            all_actions.extend(get_implement_actions())
        elif phase == Phase.VERIFY:
            all_actions.extend(get_verify_actions())

        # Filter to valid phases
        valid_actions = [
            a for a in all_actions
            if not a.phases or phase.value in a.phases
        ]

        # Sort by priority (highest first)
        valid_actions.sort(key=lambda a: a.priority, reverse=True)

        # Determine recommended action
        recommended = self._get_recommended_action(phase, state, valid_actions)

        # Determine blocked actions
        blocked = self._get_blocked_actions(phase, state)

        return ActionsSpec(
            available=valid_actions,
            recommended=recommended,
            blocked=blocked,
        )

    def _get_recommended_action(
        self,
        phase: Phase,
        state: StateSpec,
        actions: List[ActionDef],
    ) -> Optional[str]:
        """Determine the recommended next action."""
        if phase == Phase.INIT:
            return "read_file"

        if phase == Phase.ANALYZE:
            # If no code_structure facts, recommend read_file
            code_facts = [
                f for f in state.understanding.facts
                if f.category == FactCategory.CODE_STRUCTURE
            ]
            if not code_facts:
                return "read_file"
            return "load_context"

        if phase == Phase.IMPLEMENT:
            # Prefer semantic refactoring tools
            if not state.files_modified:
                return "extract_function"
            return "edit_file"

        if phase == Phase.VERIFY:
            if state.verification.checks_failing > 0:
                return "run_check"
            if not state.verification.tests_passing:
                return "run_tests"
            # All checks passing - can complete
            return "complete"

        return None

    def _get_blocked_actions(
        self,
        phase: Phase,
        state: StateSpec,
    ) -> List[str]:
        """Determine which actions are blocked and why."""
        blocked = []

        # Complete is blocked unless verification passes
        if phase != Phase.VERIFY:
            blocked.append("complete: Not in verify phase")
        elif state.verification.checks_failing > 0:
            blocked.append(
                f"complete: {state.verification.checks_failing} checks failing"
            )
        elif not state.verification.tests_passing:
            blocked.append("complete: Tests not passing")

        # Cannot extract without being in implement phase
        if phase != Phase.IMPLEMENT:
            blocked.append("extract_function: Not in implement phase")

        return blocked

    def build_messages(self, task_id: str) -> List[Dict[str, str]]:
        """
        Build messages list for LLM API call.

        Returns exactly 2 messages:
        1. System message with phase-appropriate instructions
        2. User message with complete context

        Args:
            task_id: Task identifier

        Returns:
            List of message dicts for API
        """
        context = self.build_from_task_state(task_id)
        state = self.state_store.load(task_id)

        # Build system prompt based on phase
        system_prompt = self._build_system_prompt(context)

        # Build user message from context
        user_message = self._build_user_message(context, state)

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build phase-appropriate system prompt."""
        phase = context.state.phase.current_phase

        base_prompt = """You are an expert code refactoring agent.

CRITICAL RULES:
1. Respond with EXACTLY ONE action block in YAML format
2. Do NOT explain your reasoning before the action
3. If you've analyzed the code, you should now EDIT it

Response format:
```yaml
action: <action_name>
parameters:
  <param>: <value>
```
"""

        phase_guidance = {
            "init": """
CURRENT PHASE: INIT
Focus: Load and understand the task context.
Recommended: Use read_file to examine the affected code.
""",
            "analyze": """
CURRENT PHASE: ANALYZE
Focus: Understand the code structure and identify the fix approach.
Recommended: Load more context if needed, then move to implement.
""",
            "implement": """
CURRENT PHASE: IMPLEMENT
Focus: Make the minimal changes needed to fix the violation.
IMPORTANT: Prefer semantic refactoring tools (extract_function) over raw edits.
""",
            "verify": """
CURRENT PHASE: VERIFY
Focus: Confirm the fix works and doesn't break anything.
Run checks and tests. Use 'complete' only when all pass.
""",
        }

        return base_prompt + phase_guidance.get(phase, "")

    def _build_user_message(
        self,
        context: AgentContext,
        state: Optional[TaskState],
    ) -> str:
        """Build user message from context."""
        parts = []

        # Task section
        parts.append("# Task")
        parts.append("```yaml")
        parts.append(f"task_id: {context.task.task_id}")
        parts.append(f"goal: {context.task.goal}")
        parts.append(f"success_criteria:")
        for c in context.task.success_criteria:
            parts.append(f"  - {c}")
        parts.append("```")
        parts.append("")

        # Current state section
        parts.append("# Current State")
        parts.append("```yaml")
        parts.append(f"step: {context.state.current_step}")
        parts.append(f"phase: {context.state.phase.current_phase}")
        parts.append(f"verification:")
        parts.append(f"  checks_passing: {context.state.verification.checks_passing}")
        parts.append(f"  checks_failing: {context.state.verification.checks_failing}")
        parts.append(f"  tests_passing: {context.state.verification.tests_passing}")
        parts.append("```")
        parts.append("")

        # Understanding section (facts)
        if context.state.understanding.facts:
            parts.append("# Understanding")
            parts.append("```yaml")
            for fact in context.state.understanding.facts[:10]:
                parts.append(f"- {fact.statement} (conf: {fact.confidence:.2f})")
            parts.append("```")
            parts.append("")

        # Recent actions section
        if context.state.recent_actions:
            parts.append("# Recent Actions")
            parts.append("```yaml")
            for action in context.state.recent_actions:
                parts.append(f"- step: {action.step}")
                parts.append(f"  action: {action.action}")
                parts.append(f"  result: {action.result.value}")
                parts.append(f"  summary: {action.summary}")
            parts.append("```")
            parts.append("")

        # Domain context (violation details)
        if context.domain_context:
            parts.append("# Violation Details")
            parts.append("```yaml")
            domain_yaml = yaml.dump(
                context.domain_context,
                default_flow_style=False,
                allow_unicode=True,
            )
            parts.append(domain_yaml.strip())
            parts.append("```")
            parts.append("")

        # Precomputed analysis
        if context.precomputed:
            parts.append("# Pre-computed Analysis")
            parts.append("```yaml")
            precomputed_yaml = yaml.dump(
                context.precomputed,
                default_flow_style=False,
                allow_unicode=True,
            )
            # Truncate if too long
            if len(precomputed_yaml) > 2000:
                precomputed_yaml = precomputed_yaml[:2000] + "\n... (truncated)"
            parts.append(precomputed_yaml.strip())
            parts.append("```")
            parts.append("")

        # Available actions section
        parts.append("# Available Actions")
        parts.append("```yaml")
        for action in context.actions.available[:8]:  # Limit to top 8
            parts.append(f"- name: {action.name}")
            parts.append(f"  description: {action.description}")
            if action.parameters:
                parts.append(f"  parameters: {action.parameters}")
            parts.append(f"  priority: {action.priority}")
        parts.append("```")
        parts.append("")

        if context.actions.recommended:
            parts.append(f"**Recommended action:** {context.actions.recommended}")
            parts.append("")

        if context.actions.blocked:
            parts.append("**Blocked actions:**")
            for b in context.actions.blocked[:3]:
                parts.append(f"- {b}")
            parts.append("")

        parts.append("What is your NEXT action? Respond with exactly ONE action block.")
        parts.append("IMPORTANT: If you have analyzed the code, you should now EDIT it.")

        return "\n".join(parts)

    def get_token_breakdown(self, task_id: str) -> Dict[str, Any]:
        """
        Get detailed token breakdown for debugging.

        Args:
            task_id: Task identifier

        Returns:
            Dict with token counts per section
        """
        messages = self.build_messages(task_id)

        system_tokens = estimate_tokens(messages[0]["content"])
        user_tokens = estimate_tokens(messages[1]["content"])

        return {
            "total_tokens": system_tokens + user_tokens,
            "max_tokens": self.max_tokens,
            "within_budget": (system_tokens + user_tokens) <= self.max_tokens,
            "system_prompt_tokens": system_tokens,
            "user_message_tokens": user_tokens,
        }


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
