# @spec_file: .agentforge/specs/harness-minimal-context-v1.yaml
# @spec_id: harness-minimal-context-v1
# @component_id: harness-minimal_context-executor
# @test_path: tests/unit/harness/test_action_parser.py

"""
Minimal Context Executor
========================

Executes agent steps with stateless, bounded context.
Each step is a fresh conversation with exactly 2 messages.

Key guarantees:
- Step 1 and Step 100 use same token count (±10%)
- No step exceeds 8K tokens
- All state recoverable from disk after crash
- Rate limits never exceeded
"""

import asyncio
import inspect
import re
import time
import yaml
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tools.generate.provider import LLMProvider, get_provider

from .state_store import TaskStateStore, TaskState, TaskPhase
from .context_builder import ContextBuilder
from .working_memory import WorkingMemoryManager


@dataclass
class StepOutcome:
    """Result of executing a single step."""
    success: bool
    action_name: str
    action_params: Dict[str, Any]
    result: str  # "success", "failure", "partial"
    summary: str
    should_continue: bool
    tokens_used: int
    duration_ms: int
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action_name": self.action_name,
            "action_params": self.action_params,
            "result": self.result,
            "summary": self.summary,
            "should_continue": self.should_continue,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


# Type alias for action executors
ActionExecutor = Callable[[str, Dict[str, Any], TaskState], Dict[str, Any]]


class AdaptiveBudget:
    """
    Adaptive step budget that prevents runaway while allowing complex tasks.

    Key behaviors:
    1. RUNAWAY DETECTION: Stop after 3 consecutive identical failures
    2. NO-PROGRESS DETECTION: Stop after 3 steps with zero meaningful progress
    3. PROGRESS EXTENSION: Extend budget when making progress (file mods, violation reduction)
    4. HARD CEILING: Never exceed max_budget (cost control)
    """

    def __init__(
        self,
        base_budget: int = 15,
        max_budget: int = 50,
        runaway_threshold: int = 3,
        no_progress_threshold: int = 3,
    ):
        self.base_budget = base_budget
        self.max_budget = max_budget
        self.runaway_threshold = runaway_threshold
        self.no_progress_threshold = no_progress_threshold
        self._progress_count = 0
        self._no_progress_streak = 0
        self._last_violation_count: Optional[int] = None

    def check_continue(
        self,
        step_number: int,
        recent_actions: List[Dict[str, Any]],
    ) -> tuple[bool, str]:
        """
        Determine if execution should continue.

        Args:
            step_number: Current step number (1-indexed)
            recent_actions: Last N action records (dicts with action, parameters, result, summary)

        Returns:
            (should_continue, reason)
        """
        # 1. Runaway detection: repeated identical failures
        if self._detect_runaway(recent_actions):
            return False, "STOPPED: Runaway detected (same action failed 3+ times)"

        # 2. Update progress tracking
        progress_made = self._update_progress(recent_actions)

        # 3. No-progress detection
        if not progress_made:
            self._no_progress_streak += 1
            if self._no_progress_streak >= self.no_progress_threshold:
                return False, f"STOPPED: No progress for {self._no_progress_streak} consecutive steps"
        else:
            self._no_progress_streak = 0

        # 4. Calculate dynamic budget
        dynamic_budget = self._calculate_budget()

        # 5. Check if within budget
        if step_number >= dynamic_budget:
            return False, f"STOPPED: Budget exhausted ({step_number}/{dynamic_budget} steps)"

        return True, f"Continue (step {step_number}/{dynamic_budget})"

    def _detect_runaway(self, recent_actions: List[Dict[str, Any]]) -> bool:
        """Detect runaway behavior: repeated identical failures."""
        if len(recent_actions) < self.runaway_threshold:
            return False

        last_n = recent_actions[-self.runaway_threshold:]

        # All must be failures
        if not all(a.get("result") == "failure" for a in last_n):
            return False

        # All must have same action
        actions = [a.get("action") for a in last_n]
        if len(set(actions)) != 1:
            return False

        # All must have same parameters (or same error for read failures)
        first_params = last_n[0].get("parameters", {})
        for a in last_n[1:]:
            if a.get("parameters", {}) != first_params:
                # Also check for same error message (catches semantic repetition)
                if a.get("error") != last_n[0].get("error"):
                    return False

        return True

    def _update_progress(self, recent_actions: List[Dict[str, Any]]) -> bool:
        """
        Check if the most recent action made progress.

        Progress indicators:
        - Successful file modification (write_file, edit_file, replace_lines, extract_function)
        - Successful file read (counts as exploration progress)
        - Violation count decreased (parsed from run_check summary)
        - Check passed
        """
        if not recent_actions:
            return False

        latest = recent_actions[-1]
        result = latest.get("result", "failure")
        action = latest.get("action", "")
        summary = latest.get("summary", "")

        # File modification = definite progress
        if result == "success" and action in [
            "write_file", "edit_file", "replace_lines", "insert_lines", "extract_function"
        ]:
            self._progress_count += 1
            return True

        # Check passed = major progress
        if "Check PASSED" in summary or "✓" in summary:
            self._progress_count += 3
            return True

        # Successful file read = exploration progress (doesn't extend budget, but resets no-progress)
        if result == "success" and action in ["read_file", "load_context"]:
            return True  # Counts as activity, not as budget extension

        # Violation count decreased = progress
        if action == "run_check" and "Violations" in summary:
            current_count = self._parse_violation_count(summary)
            if current_count is not None:
                if self._last_violation_count is not None:
                    if current_count < self._last_violation_count:
                        self._progress_count += 2
                        self._last_violation_count = current_count
                        return True
                self._last_violation_count = current_count

        return False

    def _parse_violation_count(self, summary: str) -> Optional[int]:
        """Parse violation count from run_check summary."""
        import re
        # Look for patterns like "Violations (4):" or "4 violations"
        match = re.search(r'Violations?\s*\((\d+)\)', summary)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)\s+violations?', summary, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _calculate_budget(self) -> int:
        """Calculate dynamic budget based on progress."""
        # Extend budget based on progress: +3 steps per progress unit
        extension = self._progress_count * 3
        dynamic_budget = min(self.base_budget + extension, self.max_budget)
        return dynamic_budget


class MinimalContextExecutor:
    """
    Executes agent steps with minimal, stateless context.

    Each step:
    1. Loads current state from disk
    2. Builds minimal context (always 4-8K tokens)
    3. Calls LLM with fresh 2-message conversation
    4. Parses and executes the action
    5. Updates state on disk
    """

    def __init__(
        self,
        project_path: Path,
        provider: Optional[LLMProvider] = None,
        state_store: Optional[TaskStateStore] = None,
        action_executors: Optional[Dict[str, ActionExecutor]] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ):
        """
        Initialize the executor.

        Args:
            project_path: Project root path
            provider: LLM provider (uses default if not provided)
            state_store: Task state store (created if not provided)
            action_executors: Dict mapping action names to executor functions
            model: Model to use for LLM calls
            max_tokens: Maximum tokens for LLM response
        """
        self.project_path = Path(project_path)
        self.provider = provider or get_provider()
        self.state_store = state_store or TaskStateStore(self.project_path)
        self.context_builder = ContextBuilder(self.project_path, self.state_store)
        self.action_executors = action_executors or {}
        self.model = model
        self.max_tokens = max_tokens

    def register_action(self, name: str, executor: ActionExecutor) -> None:
        """Register an action executor."""
        self.action_executors[name] = executor

    def register_actions(self, executors: Dict[str, ActionExecutor]) -> None:
        """Register multiple action executors."""
        self.action_executors.update(executors)

    def execute_step(self, task_id: str) -> StepOutcome:
        """
        Execute one agent step.

        This is stateless - all context is loaded from disk.

        Args:
            task_id: Task identifier

        Returns:
            StepOutcome with action taken and results
        """
        start_time = time.time()
        tokens_used = 0

        try:
            # 1. Load current state from disk
            state = self.state_store.load(task_id)
            if not state:
                return StepOutcome(
                    success=False,
                    action_name="error",
                    action_params={},
                    result="failure",
                    summary=f"Task not found: {task_id}",
                    should_continue=False,
                    tokens_used=0,
                    duration_ms=int((time.time() - start_time) * 1000),
                    error=f"Task not found: {task_id}",
                )

            # Check if task is already complete
            if state.phase in [TaskPhase.COMPLETE, TaskPhase.FAILED, TaskPhase.ESCALATED]:
                return StepOutcome(
                    success=True,
                    action_name="already_complete",
                    action_params={},
                    result="success",
                    summary=f"Task already in {state.phase.value} state",
                    should_continue=False,
                    tokens_used=0,
                    duration_ms=int((time.time() - start_time) * 1000),
                )

            # 2. Build minimal context (always fresh, bounded)
            messages = self.context_builder.build_messages(task_id)
            token_breakdown = self.context_builder.get_token_breakdown(task_id)

            # 3. Call LLM with fresh 2-message conversation
            response_text, tokens_used = self._call_llm(messages)

            # 4. Parse action from response
            action_name, action_params = self._parse_action(response_text)

            # 5. Execute action
            action_result = self._execute_action(action_name, action_params, state)

            # 6. Update state on disk
            step = self.state_store.increment_step(task_id)

            # Record action
            self.state_store.record_action(
                task_id=task_id,
                action=action_name,
                target=action_params.get("path") or action_params.get("file_path"),
                parameters=action_params,
                result=action_result.get("status", "success"),
                summary=action_result.get("summary", ""),
                duration_ms=int((time.time() - start_time) * 1000),
                error=action_result.get("error"),
            )

            # Update working memory
            task_dir = self.state_store._task_dir(task_id)
            memory_manager = WorkingMemoryManager(task_dir)
            memory_manager.add_action_result(
                action=action_name,
                result=action_result.get("status", "success"),
                summary=action_result.get("summary", ""),
                step=step,
                target=action_params.get("path") or action_params.get("file_path"),
            )

            # 7. Determine if we should continue
            should_continue = self._should_continue(action_name, action_result, state)

            # Update phase if needed
            if action_name == "complete" and action_result.get("status") == "success":
                self.state_store.update_phase(task_id, TaskPhase.COMPLETE)
            elif action_name == "escalate":
                self.state_store.update_phase(task_id, TaskPhase.ESCALATED)
            elif action_name == "cannot_fix":
                # Cannot fix is not a failure - it's honest recognition of limitations
                self.state_store.update_phase(task_id, TaskPhase.ESCALATED)
                reason = action_result.get("cannot_fix_reason", "Unknown reason")
                self.state_store.set_context(task_id, "cannot_fix_reason", reason)
            elif action_result.get("status") == "failure" and action_result.get("fatal"):
                self.state_store.update_phase(task_id, TaskPhase.FAILED)
                self.state_store.set_error(task_id, action_result.get("error", "Unknown error"))

            return StepOutcome(
                success=True,
                action_name=action_name,
                action_params=action_params,
                result=action_result.get("status", "success"),
                summary=action_result.get("summary", ""),
                should_continue=should_continue,
                tokens_used=tokens_used,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            return StepOutcome(
                success=False,
                action_name="error",
                action_params={},
                result="failure",
                summary=str(e),
                should_continue=False,
                tokens_used=tokens_used,
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )

    def _call_llm(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Call the LLM provider.

        Args:
            messages: List of message dicts (exactly 2: system + user)

        Returns:
            Tuple of (response_text, tokens_used)
        """
        # Convert to single prompt for provider
        prompt = self._messages_to_prompt(messages)

        # Call provider - handle both sync and async
        result = self.provider.generate(prompt, self.max_tokens)

        # Handle async coroutine if returned
        if inspect.iscoroutine(result):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, result)
                    response = future.result()
            else:
                response = asyncio.run(result)
        else:
            response = result

        # Handle response format - may return (text, TokenUsage) tuple
        if isinstance(response, tuple) and len(response) == 2:
            response_text, token_usage = response
            if hasattr(token_usage, 'prompt_tokens') and hasattr(token_usage, 'completion_tokens'):
                tokens_used = token_usage.prompt_tokens + token_usage.completion_tokens
            else:
                tokens_used = self.provider.count_tokens(prompt) + self.provider.count_tokens(response_text)
        else:
            response_text = response
            tokens_used = self.provider.count_tokens(prompt) + self.provider.count_tokens(response_text)

        return response_text, tokens_used

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to single prompt string."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"<system>\n{content}\n</system>\n")
            elif role == "user":
                parts.append(f"<user>\n{content}\n</user>\n")
        return "\n".join(parts)

    def _parse_action(self, response_text: str) -> tuple:
        """
        Parse action from LLM response.

        Expects format:
        ```action
        name: action_name
        parameters:
          param1: value1
        ```

        Args:
            response_text: LLM response

        Returns:
            Tuple of (action_name, action_params)
        """
        # Look for action block
        action_match = re.search(
            r"```action\s*\n(.*?)```",
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if action_match:
            action_yaml = action_match.group(1).strip()
            try:
                action_data = yaml.safe_load(action_yaml)
                if isinstance(action_data, dict):
                    name = action_data.get("name", "unknown")
                    params = action_data.get("parameters", {}) or {}
                    return name, params
            except yaml.YAMLError:
                pass

        # Fallback: look for simple action pattern
        simple_match = re.search(r"name:\s*(\w+)", response_text)
        if simple_match:
            return simple_match.group(1), {}

        # Default: treat as completion attempt
        if "complete" in response_text.lower():
            return "complete", {}

        return "unknown", {}

    def _execute_action(
        self,
        action_name: str,
        action_params: Dict[str, Any],
        state: TaskState,
    ) -> Dict[str, Any]:
        """
        Execute an action.

        Args:
            action_name: Name of action to execute
            action_params: Action parameters
            state: Current task state

        Returns:
            Dict with status, summary, and optional error
        """
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
                # Agent determined the violation cannot be automatically fixed
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
        action_result: Dict[str, Any],
        state: TaskState,
    ) -> bool:
        """Determine if execution should continue."""
        # Terminal actions
        if action_name in ["complete", "escalate", "cannot_fix"]:
            return False

        # Fatal failures
        if action_result.get("fatal"):
            return False

        # Check phase
        if state.phase in [TaskPhase.COMPLETE, TaskPhase.FAILED, TaskPhase.ESCALATED]:
            return False

        return True

    def run_until_complete(
        self,
        task_id: str,
        max_iterations: int = 50,
        on_step: Optional[Callable[[StepOutcome], None]] = None,
        adaptive_budget: Optional[AdaptiveBudget] = None,
    ) -> List[StepOutcome]:
        """
        Run task until completion or budget exhausted.

        Args:
            task_id: Task identifier
            max_iterations: Hard ceiling (safety limit)
            on_step: Optional callback after each step
            adaptive_budget: Optional adaptive budget for dynamic step limits

        Returns:
            List of all step outcomes
        """
        outcomes = []
        budget = adaptive_budget or AdaptiveBudget(
            base_budget=15,
            max_budget=max_iterations,
        )

        for i in range(max_iterations):
            outcome = self.execute_step(task_id)
            outcomes.append(outcome)

            if on_step:
                on_step(outcome)

            # Check if action signals completion
            if not outcome.should_continue:
                break

            # Check adaptive budget
            recent = self.state_store.get_recent_actions(task_id, limit=5)
            recent_dicts = [
                {
                    "action": a.action,
                    "parameters": a.parameters,
                    "result": a.result,
                    "summary": a.summary,
                    "error": a.error,
                }
                for a in recent
            ]

            should_continue, reason = budget.check_continue(i + 1, recent_dicts)
            if not should_continue:
                # Log the reason for stopping
                print(f"  {reason}")
                break

        return outcomes


def create_minimal_executor(
    project_path: Path,
    action_executors: Optional[Dict[str, ActionExecutor]] = None,
    model: str = "claude-sonnet-4-20250514",
) -> MinimalContextExecutor:
    """
    Factory function to create a minimal context executor.

    Args:
        project_path: Project root path
        action_executors: Optional action executors
        model: Model to use

    Returns:
        Configured MinimalContextExecutor
    """
    return MinimalContextExecutor(
        project_path=project_path,
        action_executors=action_executors or {},
        model=model,
    )
