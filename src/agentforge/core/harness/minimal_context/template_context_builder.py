# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: template-context-builder
# @test_path: tests/unit/harness/test_template_context_builder.py

"""
Template Context Builder
========================

Context builder that uses the new template system from core.context.templates.

This replaces the schema-based ContextBuilder with template-driven context
construction that:
- Uses task-type specific templates (fix_violation, discovery, etc.)
- Applies tiered token budgets (Tier1 always, Tier2 phase-specific, Tier3 on-demand)
- Uses template.get_system_prompt() for LLM system prompts
- Integrates with fingerprint generator for project context

Usage:
    ```python
    builder = TemplateContextBuilder(
        project_path=project_path,
        state_store=state_store,
        task_type="fix_violation",
    )

    messages = builder.build_messages(task_id)
    ```
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ...context import (
    FingerprintGenerator,
    get_template_for_task,
)
from .context_models import (
    ActionRecord,
    ActionResult,
    Fact,
    FactCategory,
    PhaseState,
    StateSpec,
    TaskSpec,
    Understanding,
    VerificationState,
)
from .state_store import TaskState, TaskStateStore
from .working_memory import WorkingMemoryManager


@dataclass
class TemplateStepContext:
    """Context built from templates for a single step."""

    system_prompt: str
    user_message: str
    total_tokens: int
    sections: dict[str, int]  # Section name -> token count
    template_name: str
    phase: str


class TemplateContextBuilder:
    """
    Build context using the new template system.

    Key differences from ContextBuilder:
    - Uses templates from core.context.templates instead of context_schemas
    - Template phases drive context structure
    - Fingerprint provides project context
    - Tiered token budgets apply automatically
    """

    def __init__(
        self,
        project_path: Path,
        state_store: TaskStateStore,
        task_type: str = "fix_violation",
        fingerprint_generator: FingerprintGenerator | None = None,
    ):
        """
        Initialize the template context builder.

        Args:
            project_path: Project root path
            state_store: Task state store
            task_type: Task type for template selection
            fingerprint_generator: Optional fingerprint generator (creates one if not provided)
        """
        self.project_path = Path(project_path)
        self.state_store = state_store
        self.task_type = task_type

        # Get template for task type
        try:
            self.template = get_template_for_task(task_type)
        except ValueError:
            # Fall back to fix_violation
            self.template = get_template_for_task("fix_violation")
            self.task_type = "fix_violation"

        # Fingerprint generator for project context
        self.fingerprint_generator = fingerprint_generator or FingerprintGenerator(
            self.project_path
        )

        # Cache for built contexts
        self._last_context: dict[str, Any] | None = None
        self._last_token_breakdown: dict[str, int] | None = None

    def build(self, task_id: str) -> TemplateStepContext:
        """
        Build context for a task step using templates.

        Args:
            task_id: Task identifier

        Returns:
            TemplateStepContext with system prompt and user message
        """
        state = self.state_store.load(task_id)
        if not state:
            raise ValueError(f"Task not found: {task_id}")

        # Determine current phase
        phase = self._get_phase_name(state)

        # Get fingerprint with task context
        fingerprint = self.fingerprint_generator.with_task_context(
            task_type=self.task_type,
            constraints=state.context_data.get("constraints", {}),
            success_criteria=state.context_data.get("success_criteria", []),
        )

        # Build task spec
        task_spec = self._build_task_spec(state)

        # Build state spec
        state_spec = self._build_state_spec(state, task_id)

        # Get precomputed data from working memory
        task_dir = self.state_store._task_dir(task_id)
        memory_manager = WorkingMemoryManager(task_dir)
        precomputed = self._get_precomputed(state, memory_manager)

        # Get domain context from state
        domain_context = self._get_domain_context(state)

        # Build context using template
        context_dict = self.template.build_context_dict(
            fingerprint=fingerprint,
            task_spec=task_spec,
            state_spec=state_spec,
            phase=phase,
            precomputed=precomputed,
            domain_context=domain_context,
        )

        # Cache for token breakdown
        self._last_context = context_dict

        # Get system prompt from template
        system_prompt = self.template.get_system_prompt(phase)

        # Format user message from context dict
        user_message = self._format_user_message(context_dict, state)

        # Calculate token breakdown
        sections = self._calculate_token_breakdown(context_dict, system_prompt)
        self._last_token_breakdown = sections

        total_tokens = sum(sections.values())

        return TemplateStepContext(
            system_prompt=system_prompt,
            user_message=user_message,
            total_tokens=total_tokens,
            sections=sections,
            template_name=self.template.task_type,
            phase=phase,
        )

    def build_messages(self, task_id: str) -> list[dict[str, str]]:
        """
        Build messages list for LLM call (compatible with executor interface).

        Args:
            task_id: Task identifier

        Returns:
            List of message dicts: [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
        """
        context = self.build(task_id)

        return [
            {"role": "system", "content": context.system_prompt},
            {"role": "user", "content": context.user_message},
        ]

    def get_token_breakdown(self, task_id: str) -> dict[str, int]:
        """
        Get token breakdown for last built context.

        Args:
            task_id: Task identifier (triggers build if not cached)

        Returns:
            Dict mapping section names to token counts
        """
        if self._last_token_breakdown is None:
            self.build(task_id)
        return self._last_token_breakdown or {}

    def _get_phase_name(self, state: TaskState) -> str:
        """
        Get current phase name from state, translated to template phases.

        Uses the template's phase mapping to translate from standard PhaseMachine
        phases to template-specific phases.
        """
        # Get standard phase from state
        standard_phase = self._get_standard_phase(state)

        # Translate to template-specific phase using template's mapping
        return self.template.translate_phase(standard_phase)

    def _get_standard_phase(self, state: TaskState) -> str:
        """Get the standard phase name from state."""
        # Try to get from phase machine
        if hasattr(state, 'get_phase_machine'):
            machine = state.get_phase_machine()
            if machine and machine.current_phase:
                # PhaseMachine uses Phase enum with values like "init", "analyze", etc.
                phase_name = machine.current_phase.value if hasattr(machine.current_phase, 'value') else str(machine.current_phase)
                return phase_name.lower()

        # Fall back to Phase enum mapping
        phase_map = {
            "init": "init",
            "analyzing": "analyze",
            "planning": "plan",
            "implementing": "implement",
            "verifying": "verify",
            "complete": "verify",
            "failed": "verify",
            "escalated": "verify",
        }

        phase_value = state.phase.value if hasattr(state.phase, 'value') else str(state.phase)
        return phase_map.get(phase_value.lower(), "init")

    def _build_task_spec(self, state: TaskState) -> TaskSpec:
        """Build TaskSpec from state."""
        return TaskSpec(
            task_id=state.task_id,
            task_type=state.task_type,
            goal=state.goal,
            success_criteria=state.success_criteria,
            constraints=state.constraints,
        )

    def _build_state_spec(self, state: TaskState, task_id: str) -> StateSpec:
        """Build StateSpec from state."""
        # Get working memory for facts and recent actions
        task_dir = self.state_store._task_dir(task_id)
        memory_manager = WorkingMemoryManager(task_dir)

        # Build verification state
        verification = VerificationState(
            checks_passing=state.verification.checks_passing,
            checks_failing=state.verification.checks_failing,
            tests_passing=state.verification.tests_passing,
            ready_for_completion=state.verification.ready_for_completion,
            last_check_time=state.verification.last_check_time,
        )

        # Build understanding from facts
        fact_dicts = memory_manager.get_facts(current_step=state.current_step)
        facts = [
            Fact(
                id=f.get("id", ""),
                category=FactCategory(f.get("category", "inference")),
                statement=f.get("statement", ""),
                confidence=f.get("confidence", 0.5),
                source=f.get("source", "unknown"),
                step=f.get("step", 0),
            )
            for f in fact_dicts
        ]
        understanding = Understanding(facts=facts)

        # Build phase state
        phase = PhaseState(
            current=self._get_phase_name(state),
            step_in_phase=state.current_step,
            max_steps=state.context_data.get("max_steps", 20),
        )

        # Get recent actions
        action_dicts = memory_manager.get_action_results(limit=3, current_step=state.current_step)
        recent_actions = [
            ActionRecord(
                action=a.get("action", ""),
                parameters=a.get("parameters", {}),
                result=ActionResult(a.get("result", "unknown")),
                summary=a.get("summary", ""),
                step=a.get("step", 0),
            )
            for a in action_dicts
        ]

        return StateSpec(
            current_step=state.current_step,
            phase=phase,
            verification=verification,
            understanding=understanding,
            recent_actions=recent_actions,
        )

    # Keys to copy from state.context_data to precomputed
    _PRECOMPUTED_KEYS = frozenset([
        "extraction_suggestions", "similar_fixes", "action_hints",
        "related_patterns", "check_definition", "file_structure",
        "dependency_graph", "pattern_candidates"
    ])

    def _categorize_context_item(
        self, item: dict[str, Any], precomputed: dict[str, Any]
    ) -> None:
        """Categorize a loaded context item into appropriate section."""
        path = item.get("path", "")
        content = item.get("content", "")

        if "target" in path.lower() or item.get("is_target"):
            precomputed["target_source"] = content
        elif "test" in path.lower():
            precomputed["existing_tests"] = content
        else:
            summary = content[:200] + "..." if len(content) > 200 else content
            precomputed.setdefault("file_overview", []).append({"path": path, "summary": summary})

    def _get_precomputed(
        self, state: TaskState, memory_manager: WorkingMemoryManager
    ) -> dict[str, Any]:
        """Get precomputed data from state and working memory."""
        precomputed = {}

        # Get and categorize loaded context files
        loaded_context = memory_manager.get_loaded_context(current_step=state.current_step)
        for item in loaded_context or []:
            if isinstance(item, dict):
                self._categorize_context_item(item, precomputed)

        # Get check results from state
        if state.verification.details.get("last_output"):
            precomputed["check_results"] = state.verification.details["last_output"]

        # Copy precomputed keys from context_data
        for key in self._PRECOMPUTED_KEYS & state.context_data.keys():
            precomputed[key] = state.context_data[key]

        return precomputed

    # Domain context key mappings: (source_key, target_key)
    _DOMAIN_CONTEXT_KEYS = [
        ("violation", "violation"),
        ("spec", "spec"),
        ("spec_requirements", "spec_requirements"),
        ("check_command", "verification_command"),  # renamed
        ("failing_tests", "failing_tests"),
        ("acceptance_criteria", "acceptance_criteria"),
        ("refactor_goal", "refactor_goal"),
        ("target_contracts", "target_contracts"),
        ("diff_summary", "diff_summary"),
        ("full_diff", "full_diff"),
    ]

    def _get_domain_context(self, state: TaskState) -> dict[str, Any]:
        """Get domain-specific context from state."""
        domain_context = {}
        for source_key, target_key in self._DOMAIN_CONTEXT_KEYS:
            if source_key in state.context_data:
                domain_context[target_key] = state.context_data[source_key]
        return domain_context

    # Keys to exclude from tier 2 sections
    _TIER1_AND_TIER3_KEYS = frozenset(["fingerprint", "task", "phase", "understanding", "recent", "additional"])
    _TIER3_KEYS = ["understanding", "recent", "additional"]

    def _format_section(self, key: str, value: Any) -> str:
        """Format a single section with header."""
        header = key.replace('_', ' ').title()
        content = value if isinstance(value, str) else yaml.dump(value, default_flow_style=False)
        return f"# {header}\n{content}"

    def _format_user_message(self, context_dict: dict[str, Any], state: TaskState) -> str:
        """Format the user message from context dict."""
        sections = []

        # Tier 1: fingerprint, task, phase
        if "fingerprint" in context_dict:
            sections.append(f"# Project Fingerprint\n{context_dict['fingerprint']}")
        if "task" in context_dict:
            sections.append(self._format_section("task", context_dict["task"]))
        if "phase" in context_dict:
            sections.append(self._format_section("phase", context_dict["phase"]))

        # Tier 2: phase-specific sections
        for key, value in context_dict.items():
            if key not in self._TIER1_AND_TIER3_KEYS:
                sections.append(self._format_section(key, value))

        # Tier 3: on-demand sections
        for key in self._TIER3_KEYS:
            if context_dict.get(key):
                sections.append(self._format_section(key, context_dict[key]))

        # Add available actions and directive
        sections.append(self._format_available_actions(state))
        sections.append(self._format_directive())

        return "\n\n".join(sections)

    def _format_available_actions(self, state: TaskState) -> str:
        """Format available actions based on current phase."""
        phase = self._get_phase_name(state)

        # Base actions available in all phases
        actions = [
            "- read_file: Read file contents",
            "- escalate: Request human assistance",
        ]

        # Phase-specific actions
        if phase in ["init", "analyze"]:
            actions.extend([
                "- load_context: Load additional file context",
                "- search_code: Search for patterns in codebase",
            ])

        if phase in ["analyze", "implement"]:
            actions.extend([
                "- extract_function: Extract code into new function",
                "- simplify_conditional: Convert to guard clause",
                "- run_check: Run conformance check",
            ])

        if phase == "implement":
            actions.extend([
                "- write_file: Write content to file",
                "- edit_file: Edit specific lines in file",
            ])

        if phase == "verify":
            actions.extend([
                "- run_check: Run conformance check",
                "- run_tests: Run test suite",
                "- complete: Mark task as complete",
            ])

        return "# Available Actions\n" + "\n".join(actions)

    def _format_directive(self) -> str:
        """Format the step directive."""
        return """# Directive
Choose ONE action and respond with:
```yaml
action: action_name
parameters:
  key: value
reasoning: brief explanation
```"""

    def _calculate_token_breakdown(
        self, context_dict: dict[str, Any], system_prompt: str
    ) -> dict[str, int]:
        """Calculate token breakdown by section."""
        breakdown = {
            "system_prompt": len(system_prompt) // 4,
        }

        for key, value in context_dict.items():
            if isinstance(value, str):
                breakdown[key] = len(value) // 4
            else:
                yaml_str = yaml.dump(value, default_flow_style=False)
                breakdown[key] = len(yaml_str) // 4

        return breakdown

    @property
    def phases(self) -> list[str]:
        """Get valid phases from the template."""
        return self.template.phases
