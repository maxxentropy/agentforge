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
from typing import Any, Dict, List, Optional

import yaml

from ...context import (
    FingerprintGenerator,
    get_template_for_task,
)
from ...context.templates.base import BaseContextTemplate
from .state_store import TaskStateStore, TaskState
from .working_memory import WorkingMemoryManager
from .context_models import (
    TaskSpec,
    StateSpec,
    PhaseState,
    VerificationState,
    Understanding,
    ActionRecord,
    Fact,
    FactCategory,
    ActionResult,
)


@dataclass
class TemplateStepContext:
    """Context built from templates for a single step."""

    system_prompt: str
    user_message: str
    total_tokens: int
    sections: Dict[str, int]  # Section name -> token count
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
        fingerprint_generator: Optional[FingerprintGenerator] = None,
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
        self._last_context: Optional[Dict[str, Any]] = None
        self._last_token_breakdown: Optional[Dict[str, int]] = None

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

    def build_messages(self, task_id: str) -> List[Dict[str, str]]:
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

    def get_token_breakdown(self, task_id: str) -> Dict[str, int]:
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

        # Fall back to TaskPhase enum mapping
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

    def _get_precomputed(
        self, state: TaskState, memory_manager: WorkingMemoryManager
    ) -> Dict[str, Any]:
        """Get precomputed data from state and working memory."""
        precomputed = {}

        # Get loaded context files
        loaded_context = memory_manager.get_loaded_context(current_step=state.current_step)
        if loaded_context:
            # Map loaded files to appropriate sections
            for item in loaded_context:
                if isinstance(item, dict):
                    path = item.get("path", "")
                    content = item.get("content", "")
                    if "target" in path.lower() or item.get("is_target"):
                        precomputed["target_source"] = content
                    elif "test" in path.lower():
                        precomputed["existing_tests"] = content
                    else:
                        precomputed.setdefault("file_overview", []).append({
                            "path": path,
                            "summary": content[:200] + "..." if len(content) > 200 else content
                        })

        # Get check results from state (stored in details dict)
        if state.verification.details.get("last_output"):
            precomputed["check_results"] = state.verification.details["last_output"]

        # Get any precomputed data stored in context_data
        for key in ["extraction_suggestions", "similar_fixes", "action_hints",
                    "related_patterns", "check_definition", "file_structure",
                    "dependency_graph", "pattern_candidates"]:
            if key in state.context_data:
                precomputed[key] = state.context_data[key]

        return precomputed

    def _get_domain_context(self, state: TaskState) -> Dict[str, Any]:
        """Get domain-specific context from state."""
        domain_context = {}

        # Get violation info if present
        if "violation" in state.context_data:
            domain_context["violation"] = state.context_data["violation"]

        # Get spec/requirements if present
        if "spec" in state.context_data:
            domain_context["spec"] = state.context_data["spec"]
        if "spec_requirements" in state.context_data:
            domain_context["spec_requirements"] = state.context_data["spec_requirements"]

        # Get verification command
        if "check_command" in state.context_data:
            domain_context["verification_command"] = state.context_data["check_command"]

        # Get failing tests for implement_feature
        if "failing_tests" in state.context_data:
            domain_context["failing_tests"] = state.context_data["failing_tests"]

        # Get acceptance criteria
        if "acceptance_criteria" in state.context_data:
            domain_context["acceptance_criteria"] = state.context_data["acceptance_criteria"]

        # Get refactor goal for refactor tasks
        if "refactor_goal" in state.context_data:
            domain_context["refactor_goal"] = state.context_data["refactor_goal"]

        # Get target contracts for bridge tasks
        if "target_contracts" in state.context_data:
            domain_context["target_contracts"] = state.context_data["target_contracts"]

        # Get diff for code review
        if "diff_summary" in state.context_data:
            domain_context["diff_summary"] = state.context_data["diff_summary"]
        if "full_diff" in state.context_data:
            domain_context["full_diff"] = state.context_data["full_diff"]

        return domain_context

    def _format_user_message(self, context_dict: Dict[str, Any], state: TaskState) -> str:
        """Format the user message from context dict."""
        # Format as YAML with clear sections
        sections = []

        # Always include fingerprint, task, phase (Tier 1)
        if "fingerprint" in context_dict:
            sections.append(f"# Project Fingerprint\n{context_dict['fingerprint']}")

        if "task" in context_dict:
            task_yaml = yaml.dump(context_dict["task"], default_flow_style=False)
            sections.append(f"# Task\n{task_yaml}")

        if "phase" in context_dict:
            phase_yaml = yaml.dump(context_dict["phase"], default_flow_style=False)
            sections.append(f"# Phase\n{phase_yaml}")

        # Add tier 2 sections (phase-specific)
        tier2_keys = [k for k in context_dict.keys()
                      if k not in ["fingerprint", "task", "phase", "understanding", "recent", "additional"]]
        for key in tier2_keys:
            value = context_dict[key]
            if isinstance(value, str):
                sections.append(f"# {key.replace('_', ' ').title()}\n{value}")
            else:
                value_yaml = yaml.dump(value, default_flow_style=False)
                sections.append(f"# {key.replace('_', ' ').title()}\n{value_yaml}")

        # Add tier 3 sections (on-demand)
        for key in ["understanding", "recent", "additional"]:
            if key in context_dict and context_dict[key]:
                value = context_dict[key]
                if isinstance(value, str):
                    sections.append(f"# {key.replace('_', ' ').title()}\n{value}")
                else:
                    value_yaml = yaml.dump(value, default_flow_style=False)
                    sections.append(f"# {key.replace('_', ' ').title()}\n{value_yaml}")

        # Add available actions
        sections.append(self._format_available_actions(state))

        # Add directive
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

        return f"# Available Actions\n" + "\n".join(actions)

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
        self, context_dict: Dict[str, Any], system_prompt: str
    ) -> Dict[str, int]:
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
    def phases(self) -> List[str]:
        """Get valid phases from the template."""
        return self.template.phases
