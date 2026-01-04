# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: minimal-context-executor
# @test_path: tests/unit/harness/test_minimal_context.py

"""
Minimal Context Executor
========================

Executes agent steps with stateless, bounded context.
Each step is a fresh conversation with exactly 2 messages.

Key guarantees:
- Step 1 and Step 100 use same token count (±10%)
- No step exceeds ~4K tokens
- All state recoverable from disk after crash
- Rate limits never exceeded

Features:
- Template-based context building (TemplateContextBuilder)
- AGENT.MD configuration hierarchy
- Dynamic project fingerprinting
- Full audit trail with context snapshots
- Progressive compaction for token efficiency
- Native tool calls (Anthropic tool_use API)
- Enhanced loop detection
- Phase machine for state transitions
- Understanding extraction for fact-based reasoning
"""

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agentforge.core.generate.provider import LLMProvider, get_provider

from ....context import (
    AgentConfigLoader,
    CompactionManager,
    FingerprintGenerator,
    get_template_for_task,
)
from ..native_tool_executor import NativeToolExecutor
from ..state_store import Phase, TaskState, TaskStateStore
from ..template_context_builder import TemplateContextBuilder
from ..tool_handlers import create_standard_handlers
from ..understanding import UnderstandingExtractor
from ..working_memory import WorkingMemoryManager
from .llm_mixin import LLMMixin
from .native_mixin import NativeMixin
from .phase_mixin import PhaseMixin
from .run_mixin import RunMixin
from .step_outcome import StepOutcome

# Type alias for action executors
ActionExecutor = Callable[[str, dict[str, Any], TaskState], dict[str, Any]]


class MinimalContextExecutor(
    PhaseMixin,
    LLMMixin,
    RunMixin,
    NativeMixin,
):
    """
    Executes agent steps with minimal, stateless context.

    Each step:
    1. Loads current state from disk
    2. Builds minimal context via templates (~4K tokens)
    3. Calls LLM with fresh 2-message conversation
    4. Parses and executes the action
    5. Updates state on disk
    6. Logs to audit trail

    Features:
    - Template-based context building
    - AGENT.MD configuration
    - Dynamic fingerprinting
    - Audit logging
    - Progressive compaction
    - Native tool support
    - Enhanced loop detection
    - Phase machine integration
    """

    def __init__(
        self,
        project_path: Path,
        task_type: str = "fix_violation",
        provider: LLMProvider | None = None,
        state_store: TaskStateStore | None = None,
        action_executors: dict[str, ActionExecutor] | None = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        config_loader: AgentConfigLoader | None = None,
        fingerprint_generator: FingerprintGenerator | None = None,
        compaction_enabled: bool = True,
        audit_enabled: bool = True,
    ):
        """
        Initialize the executor.

        Args:
            project_path: Project root path
            task_type: Type of task (fix_violation, implement_feature, etc.)
            provider: LLM provider (uses default if not provided)
            state_store: Task state store (created if not provided)
            action_executors: Dict mapping action names to executor functions
            model: Model to use for LLM calls
            max_tokens: Maximum tokens for LLM response
            config_loader: Optional custom config loader
            fingerprint_generator: Optional custom fingerprint generator
            compaction_enabled: Enable progressive compaction
            audit_enabled: Enable audit logging
        """
        self.project_path = Path(project_path).resolve()
        self.task_type = task_type
        self.provider = provider or get_provider()
        self.state_store = state_store or TaskStateStore(self.project_path)
        self.action_executors = action_executors or {}
        self.model = model
        self.max_tokens = max_tokens

        # Configuration
        self.config_loader = config_loader or AgentConfigLoader(self.project_path)
        self.config = self.config_loader.load(task_type=task_type)

        # Fingerprinting
        self.fingerprint_generator = fingerprint_generator or FingerprintGenerator(
            self.project_path
        )

        # Get template for task type
        try:
            self.template = get_template_for_task(task_type)
        except ValueError:
            self.template = get_template_for_task("fix_violation")

        # Template-based context builder
        self.context_builder = TemplateContextBuilder(
            project_path=self.project_path,
            state_store=self.state_store,
            task_type=task_type,
            fingerprint_generator=self.fingerprint_generator,
        )

        # Compaction
        self.compaction_enabled = compaction_enabled
        if compaction_enabled:
            self.compaction_manager = CompactionManager(
                threshold=0.90,
                max_budget=getattr(self.config.defaults, "token_budget", 4000),
            )
        else:
            self.compaction_manager = None

        # Audit logging
        self.audit_enabled = audit_enabled and os.environ.get(
            "AGENTFORGE_AUDIT_ENABLED", "true"
        ).lower() != "false"
        self.current_audit_logger = None

        # Compaction tracking
        self._compaction_events = 0
        self._tokens_saved = 0

        # Understanding extraction
        self.understanding_extractor = UnderstandingExtractor()

        # Phase machine enabled by default
        self.use_phase_machine = True

        # Native tool executor
        self.native_tool_executor = NativeToolExecutor(
            actions=create_standard_handlers(self.project_path),
            context={"project_path": str(self.project_path)},
        )

    def register_action(self, name: str, executor: ActionExecutor) -> None:
        """Register an action executor."""
        self.action_executors[name] = executor
        # Also register with native tool executor using compatible wrapper
        self.native_tool_executor.register_action(name, executor)

    def register_actions(self, executors: dict[str, ActionExecutor]) -> None:
        """Register multiple action executors."""
        self.action_executors.update(executors)
        self.native_tool_executor.register_actions(executors)

    def _outcome(self, success: bool, action: str, params: dict, result: str,
                 summary: str, should_continue: bool, tokens: int,
                 start_time: float, error: str | None = None) -> StepOutcome:
        """Create a StepOutcome with computed duration."""
        return StepOutcome(
            success=success, action_name=action, action_params=params,
            result=result, summary=summary, should_continue=should_continue,
            tokens_used=tokens, duration_ms=int((time.time() - start_time) * 1000),
            error=error)

    def get_fingerprint(
        self,
        constraints: dict[str, Any] | None = None,
        success_criteria: list[str] | None = None,
    ):
        """Get project fingerprint with task context."""
        return self.fingerprint_generator.with_task_context(
            task_type=self.task_type,
            constraints=constraints or {},
            success_criteria=success_criteria or [],
        )

    def execute_step(self, task_id: str) -> StepOutcome:
        """Execute one agent step. Stateless - all context loaded from disk."""
        start_time = time.time()
        tokens_used = 0

        try:
            # 1. Load and validate state
            state = self.state_store.load(task_id)
            if not state:
                return self._outcome(False, "error", {}, "failure",
                    f"Task not found: {task_id}", False, 0, start_time, f"Task not found: {task_id}")
            if state.phase in [Phase.COMPLETE, Phase.FAILED, Phase.ESCALATED]:
                return self._outcome(True, "already_complete", {}, "success",
                    f"Task already in {state.phase.value} state", False, 0, start_time)

            # 2. Build context and call LLM
            messages = self.context_builder.build_messages(task_id)
            self.context_builder.get_token_breakdown(task_id)
            response_text, tokens_used = self._call_llm(messages)

            # 3. Parse and execute action
            action_name, action_params = self._parse_action(response_text)
            action_result = self._execute_action(action_name, action_params, state)

            # 4. Record step and update memory
            self._record_step(task_id, action_name, action_params, action_result, start_time)

            # 5. Determine continuation and update phase
            should_continue = self._should_continue(action_name, action_result, state)
            self._handle_phase_transition(task_id, action_name, action_result, state)

            return self._outcome(True, action_name, action_params,
                action_result.get("status", "success"), action_result.get("summary", ""),
                should_continue, tokens_used, start_time)

        except Exception as e:
            return self._outcome(False, "error", {}, "failure", str(e), False, tokens_used, start_time, str(e))

    def _record_step(self, task_id: str, action_name: str, action_params: dict,
                     action_result: dict, start_time: float) -> None:
        """Record action in state store and working memory."""
        step = self.state_store.increment_step(task_id)
        target = action_params.get("path") or action_params.get("file_path")

        self.state_store.record_action(
            task_id=task_id, action=action_name, target=target, parameters=action_params,
            result=action_result.get("status", "success"), summary=action_result.get("summary", ""),
            duration_ms=int((time.time() - start_time) * 1000), error=action_result.get("error"))

        task_dir = self.state_store._task_dir(task_id)
        memory_manager = WorkingMemoryManager(task_dir)
        memory_manager.add_action_result(
            action=action_name, result=action_result.get("status", "success"),
            summary=action_result.get("summary", ""), step=step, target=target)

        if self.understanding_extractor:
            self._extract_and_store_facts(action_name, action_result, step, memory_manager)

    def _execute_action(
        self,
        action_name: str,
        action_params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Execute an action."""
        executor = self.action_executors.get(action_name)

        if not executor:
            # Handle built-in actions
            if action_name == "complete":
                if state.verification.ready_for_completion:
                    return {
                        "status": "success",
                        "summary": "Task marked complete",
                    }
                else:
                    return {
                        "status": "failure",
                        "summary": "Cannot complete - verification not passing",
                        "error": "Verification not passing",
                    }

            if action_name == "escalate":
                return {
                    "status": "success",
                    "summary": "Escalated to human",
                }

            if action_name == "cannot_fix":
                reason = action_params.get("reason", "No reason provided")
                return {
                    "status": "success",
                    "summary": f"Cannot fix automatically: {reason}",
                    "cannot_fix_reason": reason,
                }

            return {
                "status": "failure",
                "summary": f"Unknown action: {action_name}",
                "error": f"No executor registered for: {action_name}",
            }

        try:
            result = executor(action_name, action_params, state)
            if isinstance(result, dict):
                return result
            return {
                "status": "success",
                "summary": str(result),
            }
        except Exception as e:
            return {
                "status": "failure",
                "summary": f"Action failed: {e}",
                "error": str(e),
            }

    def _should_continue(
        self,
        action_name: str,
        action_result: dict[str, Any],
        state: TaskState,
    ) -> bool:
        """Determine if execution should continue."""
        if action_name in ["complete", "escalate", "cannot_fix"]:
            return False

        if action_result.get("fatal"):
            return False

        return state.phase not in [Phase.COMPLETE, Phase.FAILED, Phase.ESCALATED]


def create_executor(
    project_path: Path,
    task_type: str = "fix_violation",
    action_executors: dict[str, ActionExecutor] | None = None,
    **kwargs,
) -> MinimalContextExecutor:
    """
    Factory function to create an executor.

    Args:
        project_path: Project root path
        task_type: Task type
        action_executors: Optional action executors
        **kwargs: Additional executor options

    Returns:
        Configured MinimalContextExecutor
    """
    executor = MinimalContextExecutor(
        project_path=project_path,
        task_type=task_type,
        **kwargs,
    )

    if action_executors:
        executor.register_actions(action_executors)

    return executor


def should_use_native_tools() -> bool:
    """
    Check if native tools should be used based on environment.

    Returns True if AGENTFORGE_NATIVE_TOOLS=true
    """
    return os.environ.get("AGENTFORGE_NATIVE_TOOLS", "false").lower() == "true"
