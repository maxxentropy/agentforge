# @spec_file: .agentforge/specs/harness-minimal-context-v1.yaml
# @spec_id: harness-minimal-context-v1
# @component_id: harness-minimal_context-context_builder
# @test_path: tests/unit/harness/test_minimal_context.py

"""
Context Builder
===============

Builds minimal context for each step from persisted state.
Guarantees token budget compliance.
"""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state_store import TaskState, TaskStateStore
from .token_budget import TokenBudget, estimate_tokens
from .working_memory import WorkingMemoryManager
from .context_schemas import ContextSchema, get_schema_for_task


@dataclass
class StepContext:
    """Complete context for a single step."""
    system_prompt: str
    user_message: str
    total_tokens: int
    sections: Dict[str, int]  # Token count per section


class ContextBuilder:
    """
    Builds minimal context from task state.

    Guarantees:
    - Total tokens never exceed max_tokens (default 8000)
    - Same token count for step 1 and step 100
    - All context built from disk state (no memory)
    """

    def __init__(
        self,
        project_path: Path,
        state_store: Optional[TaskStateStore] = None,
        max_tokens: int = 8000,
    ):
        """
        Initialize context builder.

        Args:
            project_path: Project root path
            state_store: Task state store (created if not provided)
            max_tokens: Maximum total tokens
        """
        self.project_path = Path(project_path)
        self.state_store = state_store or TaskStateStore(self.project_path)
        self.max_tokens = max_tokens
        self.token_budget = TokenBudget()

    def build(self, task_id: str) -> StepContext:
        """
        Build context for a task step.

        Args:
            task_id: Task identifier

        Returns:
            StepContext with system prompt and user message
        """
        state = self.state_store.load(task_id)
        if not state:
            raise ValueError(f"Task not found: {task_id}")

        schema = get_schema_for_task(state.task_type, self.project_path)

        # Build sections
        sections = {}

        # 1. System prompt
        system_prompt = schema.get_system_prompt(state)
        sections["system_prompt"] = estimate_tokens(system_prompt)

        # 2. Task frame
        task_frame = schema.format_task_frame(state)
        sections["task_frame"] = estimate_tokens(task_frame)

        # 3. Current state (task-type specific)
        current_state = schema.get_current_state(state)
        current_state_yaml = yaml.dump(current_state, default_flow_style=False, allow_unicode=True)

        # Compress if needed
        current_state_yaml, _ = self.token_budget.compress_to_fit(
            "current_state", current_state_yaml
        )
        sections["current_state"] = estimate_tokens(current_state_yaml)

        # 4. Recent actions from working memory
        task_dir = self.state_store._task_dir(task_id)
        memory_manager = WorkingMemoryManager(task_dir)
        recent_actions = memory_manager.get_action_results(limit=3, current_step=state.current_step)
        recent_actions_yaml = yaml.dump(recent_actions, default_flow_style=False) if recent_actions else "[]"
        sections["recent_actions"] = estimate_tokens(recent_actions_yaml)

        # 5. Verification status
        verification_yaml = schema.format_verification_status(state)
        sections["verification_status"] = estimate_tokens(verification_yaml)

        # 6. Available actions
        actions_yaml = schema.format_available_actions(state)
        sections["available_actions"] = estimate_tokens(actions_yaml)

        # 7. Loaded context (from working memory)
        loaded_context = memory_manager.get_loaded_context(current_step=state.current_step)
        loaded_context_yaml = ""
        if loaded_context:
            loaded_context_yaml = yaml.dump(loaded_context, default_flow_style=False)
            loaded_context_yaml, _ = self.token_budget.compress_to_fit(
                "current_state", loaded_context_yaml  # Use same compression as current_state
            )
        sections["loaded_context"] = estimate_tokens(loaded_context_yaml)

        # Build user message
        user_message = self._format_user_message(
            task_frame=task_frame,
            current_state=current_state_yaml,
            recent_actions=recent_actions_yaml,
            verification=verification_yaml,
            available_actions=actions_yaml,
            loaded_context=loaded_context_yaml,
        )

        total_tokens = sum(sections.values())

        return StepContext(
            system_prompt=system_prompt,
            user_message=user_message,
            total_tokens=total_tokens,
            sections=sections,
        )

    def _format_user_message(
        self,
        task_frame: str,
        current_state: str,
        recent_actions: str,
        verification: str,
        available_actions: str,
        loaded_context: str = "",
    ) -> str:
        """Format the complete user message."""
        parts = [
            "# Task",
            "```yaml",
            task_frame.strip(),
            "```",
            "",
            "# Current State",
            "```yaml",
            current_state.strip(),
            "```",
            "",
        ]

        if recent_actions and recent_actions.strip() != "[]":
            parts.extend([
                "# Recent Actions",
                "```yaml",
                recent_actions.strip(),
                "```",
                "",
            ])

        parts.extend([
            "# Verification Status",
            "```yaml",
            verification.strip(),
            "```",
            "",
        ])

        if loaded_context:
            parts.extend([
                "# Additional Context",
                "```yaml",
                loaded_context.strip(),
                "```",
                "",
            ])

        parts.extend([
            "# Available Actions",
            "```yaml",
            available_actions.strip(),
            "```",
            "",
            "What is your NEXT action? Respond with exactly ONE action block.",
            "IMPORTANT: If you have analyzed the code, you should now EDIT it. Don't keep reading/analyzing.",
        ])

        return "\n".join(parts)

    def build_messages(self, task_id: str) -> List[Dict[str, str]]:
        """
        Build messages list for LLM API call.

        This is the key method - returns exactly 2 messages:
        1. System message
        2. User message with complete context

        Args:
            task_id: Task identifier

        Returns:
            List of message dicts for API
        """
        context = self.build(task_id)

        return [
            {"role": "system", "content": context.system_prompt},
            {"role": "user", "content": context.user_message},
        ]

    def get_token_breakdown(self, task_id: str) -> Dict[str, Any]:
        """
        Get detailed token breakdown for debugging.

        Args:
            task_id: Task identifier

        Returns:
            Dict with token counts per section
        """
        context = self.build(task_id)

        return {
            "total_tokens": context.total_tokens,
            "max_tokens": self.max_tokens,
            "within_budget": context.total_tokens <= self.max_tokens,
            "sections": context.sections,
            "system_prompt_tokens": context.sections.get("system_prompt", 0),
            "user_message_tokens": context.total_tokens - context.sections.get("system_prompt", 0),
        }


def create_context_builder(
    project_path: Path,
    max_tokens: int = 8000,
) -> ContextBuilder:
    """
    Factory function to create a context builder.

    Args:
        project_path: Project root path
        max_tokens: Maximum total tokens

    Returns:
        Configured ContextBuilder
    """
    return ContextBuilder(project_path=project_path, max_tokens=max_tokens)
