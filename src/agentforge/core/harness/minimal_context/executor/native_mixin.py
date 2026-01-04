"""
Native Tool Execution Mixin
===========================

Native Anthropic tool call execution for the executor.
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ....llm import (
    LLMClient,
    LLMClientFactory,
    LLMResponse,
    ThinkingConfig,
    get_tools_for_task,
)
from ..state_store import Phase
from .helpers import determine_final_status
from .step_outcome import StepOutcome

if TYPE_CHECKING:
    from ..native_tool_executor import NativeToolExecutor
    from ..state_store import TaskStateStore
    from ..template_context_builder import TemplateContextBuilder


class NativeMixin:
    """
    Mixin for native tool execution in executor.

    Handles native Anthropic tool calls and task execution.
    """

    # Type hints for attributes from main class
    project_path: Path
    task_type: str
    state_store: "TaskStateStore"
    context_builder: "TemplateContextBuilder"
    config: Any
    native_tool_executor: "NativeToolExecutor"
    _compaction_events: int
    _tokens_saved: int

    # Methods from other mixins
    _initialize_run: Callable
    _log_step: Callable
    _log_run_summary: Callable
    _update_phase_from_action: Callable

    def _initialize_task_state(self, task_id: str, domain_context: dict[str, Any] | None):
        """Initialize or update task state with domain context."""
        state = self.state_store.load(task_id)
        if state is None:
            self.state_store.create_task(
                task_type=self.task_type,
                goal="Execute task with native tools",
                success_criteria=["Task completes successfully"],
                context_data=domain_context or {},
                task_id=task_id,
            )
        elif domain_context:
            for key, value in domain_context.items():
                self.state_store.update_context_data(task_id, key, value)

    def _get_thinking_config(self) -> ThinkingConfig | None:
        """Get thinking configuration if enabled."""
        if self.config.defaults.thinking_enabled:
            return ThinkingConfig(
                enabled=True,
                budget_tokens=self.config.defaults.thinking_budget,
            )
        return None

    def _should_stop_native(self, outcome: StepOutcome) -> bool:
        """Check if native execution should stop."""
        if outcome.action_name in ("complete", "escalate", "cannot_fix"):
            return True
        return bool(outcome.error)

    def _build_native_result(self, task_id: str, outcomes: list[StepOutcome]) -> dict[str, Any]:
        """Build result dictionary for native task execution."""
        final_status = determine_final_status(outcomes)
        self._log_run_summary(outcomes)
        return {
            "task_id": task_id,
            "status": final_status,
            "steps": len(outcomes),
            "outcomes": [o.to_dict() for o in outcomes],
            "compaction_events": self._compaction_events,
            "tokens_saved": self._tokens_saved,
            "native_tools": True,
        }

    def _process_native_response(
        self,
        response: LLMResponse,
        task_id: str,
        step: int,
    ) -> StepOutcome:
        """Process LLM response with native tool calls."""
        tokens_used = response.total_tokens

        if not response.has_tool_calls:
            return StepOutcome(
                success=True,
                action_name="unknown",
                action_params={},
                result=response.content or "",
                summary=response.content[:200] if response.content else "No response",
                should_continue=False,
                tokens_used=tokens_used,
                duration_ms=0,
                error=None,
            )

        tool_call = response.get_first_tool_call()
        if not tool_call:
            return StepOutcome(
                success=False,
                action_name="unknown",
                action_params={},
                result="No tool call found",
                summary="No tool call found",
                should_continue=False,
                tokens_used=tokens_used,
                duration_ms=0,
                error="No tool call found",
            )

        tool_result = self.native_tool_executor.execute(tool_call)
        is_terminal = tool_call.name in ("complete", "escalate", "cannot_fix")

        return StepOutcome(
            success=not tool_result.is_error,
            action_name=tool_call.name,
            action_params=tool_call.input,
            result=tool_result.content or "",
            summary=tool_result.content[:200] if tool_result.content else "",
            should_continue=not is_terminal and not tool_result.is_error,
            tokens_used=tokens_used,
            duration_ms=0,
            error=tool_result.content if tool_result.is_error else None,
        )

    def run_task_native(
        self,
        task_id: str,
        domain_context: dict[str, Any] | None = None,
        llm_client: LLMClient | None = None,
        max_steps: int | None = None,
        on_step: Callable[[StepOutcome], None] | None = None,
    ) -> dict[str, Any]:
        """Run a complete task using native Anthropic tool calls."""
        self._initialize_run(task_id)

        effective_max_steps = max_steps or self.config.defaults.max_steps
        tools = get_tools_for_task(self.task_type)
        client = llm_client or LLMClientFactory.create()

        self._initialize_task_state(task_id, domain_context)
        thinking_config = self._get_thinking_config()

        outcomes: list[StepOutcome] = []
        step_num = 0

        while step_num < effective_max_steps:
            step_num += 1

            context = self.context_builder.build(task_id=task_id)
            messages = [{"role": "user", "content": context.user_message}]

            response = client.complete(
                system=context.system_prompt,
                messages=messages,
                tools=tools,
                thinking=thinking_config,
            )

            outcome = self._process_native_response(response=response, task_id=task_id, step=step_num)
            outcomes.append(outcome)
            self._log_step(outcome, task_id)

            if on_step:
                on_step(outcome)

            if self._should_stop_native(outcome):
                break

            self._update_phase_from_action(task_id, outcome.action_name)

        return self._build_native_result(task_id, outcomes)

    def get_native_tool_executor(self) -> "NativeToolExecutor":
        """Get the native tool executor for direct access."""
        return self.native_tool_executor
