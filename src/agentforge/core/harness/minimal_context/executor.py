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

Enhanced with Understanding Extraction for fact-based context.
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

from agentforge.core.generate.provider import LLMProvider, get_provider

from .state_store import TaskStateStore, TaskState, TaskPhase
from .context_builder import ContextBuilder
from .enhanced_context_builder import EnhancedContextBuilder
from .working_memory import WorkingMemoryManager
from .understanding import UnderstandingExtractor
from .context_models import ActionResult, ActionRecord
from .loop_detector import LoopDetector, LoopDetection, LoopType
from .phase_machine import PhaseMachine, Phase, PhaseContext


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
    loop_detected: Optional[LoopDetection] = None  # Enhanced loop detection info

    def to_dict(self) -> Dict[str, Any]:
        result = {
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
        if self.loop_detected and self.loop_detected.detected:
            result["loop_detection"] = {
                "type": self.loop_detected.loop_type.value if self.loop_detected.loop_type else None,
                "description": self.loop_detected.description,
                "confidence": self.loop_detected.confidence,
                "suggestions": self.loop_detected.suggestions,
            }
        return result


# Type alias for action executors
ActionExecutor = Callable[[str, Dict[str, Any], TaskState], Dict[str, Any]]


class AdaptiveBudget:
    """
    Adaptive step budget that prevents runaway while allowing complex tasks.

    Key behaviors:
    1. LOOP DETECTION: Enhanced detection via LoopDetector (Phase 3)
       - Identical action loops
       - Semantic loops (different actions, same outcome)
       - Error cycling (A->B->A patterns)
       - No-progress loops
    2. PROGRESS EXTENSION: Extend budget when making progress
    3. HARD CEILING: Never exceed max_budget (cost control)
    """

    def __init__(
        self,
        base_budget: int = 15,
        max_budget: int = 50,
        runaway_threshold: int = 3,
        no_progress_threshold: int = 3,
        use_enhanced_loop_detection: bool = True,
    ):
        self.base_budget = base_budget
        self.max_budget = max_budget
        self.runaway_threshold = runaway_threshold
        self.no_progress_threshold = no_progress_threshold
        self._progress_count = 0
        self._no_progress_streak = 0
        self._last_violation_count: Optional[int] = None

        # Enhanced loop detection (Phase 3)
        self.use_enhanced_loop_detection = use_enhanced_loop_detection
        self.loop_detector = LoopDetector(
            identical_threshold=runaway_threshold,
            semantic_threshold=runaway_threshold + 1,
            cycle_threshold=2,
            no_progress_threshold=no_progress_threshold,
        ) if use_enhanced_loop_detection else None

        # Store last loop detection for reporting
        self._last_loop_detection: Optional[LoopDetection] = None

    def check_continue(
        self,
        step_number: int,
        recent_actions: List[Dict[str, Any]],
        facts: Optional[List[Any]] = None,
    ) -> tuple[bool, str, Optional[LoopDetection]]:
        """
        Determine if execution should continue.

        Args:
            step_number: Current step number (1-indexed)
            recent_actions: Last N action records (dicts with action, parameters, result, summary)
            facts: Optional list of facts for enhanced loop detection

        Returns:
            (should_continue, reason, loop_detection)
        """
        self._last_loop_detection = None

        # 1. Enhanced loop detection (if enabled)
        if self.use_enhanced_loop_detection and self.loop_detector:
            loop_result = self._check_enhanced_loops(recent_actions, facts)
            if loop_result and loop_result.detected:
                self._last_loop_detection = loop_result
                return (
                    False,
                    f"STOPPED: {loop_result.loop_type.value.upper()} - {loop_result.description}",
                    loop_result,
                )
        else:
            # Fallback to legacy runaway detection
            if self._detect_runaway_legacy(recent_actions):
                return False, "STOPPED: Runaway detected (same action failed 3+ times)", None

        # 2. Update progress tracking
        progress_made = self._update_progress(recent_actions)

        # 3. No-progress detection (legacy, still useful alongside enhanced)
        if not progress_made:
            self._no_progress_streak += 1
            if self._no_progress_streak >= self.no_progress_threshold:
                return False, f"STOPPED: No progress for {self._no_progress_streak} consecutive steps", None
        else:
            self._no_progress_streak = 0

        # 4. Calculate dynamic budget
        dynamic_budget = self._calculate_budget()

        # 5. Check if within budget
        if step_number >= dynamic_budget:
            return False, f"STOPPED: Budget exhausted ({step_number}/{dynamic_budget} steps)", None

        return True, f"Continue (step {step_number}/{dynamic_budget})", None

    def _check_enhanced_loops(
        self,
        recent_actions: List[Dict[str, Any]],
        facts: Optional[List[Any]] = None,
    ) -> Optional[LoopDetection]:
        """
        Use enhanced LoopDetector for semantic loop detection.

        Args:
            recent_actions: Recent action dicts
            facts: Optional facts for context

        Returns:
            LoopDetection result or None
        """
        if not self.loop_detector or not recent_actions:
            return None

        # Convert dicts to ActionRecord models
        action_records = []
        for i, action_dict in enumerate(recent_actions):
            # Map string result to ActionResult enum
            result_str = action_dict.get("result", "success")
            result_enum = {
                "success": ActionResult.SUCCESS,
                "failure": ActionResult.FAILURE,
                "partial": ActionResult.PARTIAL,
            }.get(result_str, ActionResult.SUCCESS)

            record = ActionRecord(
                step=action_dict.get("step", i + 1),
                action=action_dict.get("action", "unknown"),
                target=action_dict.get("target"),
                parameters=action_dict.get("parameters", {}),
                result=result_enum,
                summary=action_dict.get("summary", ""),
                error=action_dict.get("error"),
            )
            action_records.append(record)

        # Run enhanced detection
        return self.loop_detector.check(action_records, facts)

    def _detect_runaway_legacy(self, recent_actions: List[Dict[str, Any]]) -> bool:
        """Legacy runaway detection: repeated identical failures."""
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
                if a.get("error") != last_n[0].get("error"):
                    return False

        return True

    def get_last_loop_detection(self) -> Optional[LoopDetection]:
        """Get the last loop detection result."""
        return self._last_loop_detection

    def get_loop_suggestions(self) -> List[str]:
        """Get suggestions from the last loop detection."""
        if self._last_loop_detection and self._last_loop_detection.detected:
            return self._last_loop_detection.suggestions
        return []

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
        enable_understanding_extraction: bool = True,
        use_phase_machine: bool = True,
        use_enhanced_context_builder: bool = False,
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
            enable_understanding_extraction: Enable fact extraction from actions
            use_phase_machine: Use PhaseMachine for transitions (Phase 4)
            use_enhanced_context_builder: Use EnhancedContextBuilder (Phase 5)
        """
        self.project_path = Path(project_path)
        self.provider = provider or get_provider()
        self.state_store = state_store or TaskStateStore(self.project_path)
        self.action_executors = action_executors or {}
        self.model = model
        self.max_tokens = max_tokens

        # Context builder selection (Phase 5 of Enhanced Context Engineering)
        self.use_enhanced_context_builder = use_enhanced_context_builder
        if use_enhanced_context_builder:
            self.context_builder = EnhancedContextBuilder(self.project_path, self.state_store)
        else:
            self.context_builder = ContextBuilder(self.project_path, self.state_store)

        # Understanding extraction (Phase 2 of Enhanced Context Engineering)
        self.enable_understanding_extraction = enable_understanding_extraction
        self.understanding_extractor = UnderstandingExtractor() if enable_understanding_extraction else None

        # Phase machine (Phase 4 of Enhanced Context Engineering)
        self.use_phase_machine = use_phase_machine

    def register_action(self, name: str, executor: ActionExecutor) -> None:
        """Register an action executor."""
        self.action_executors[name] = executor

    def register_actions(self, executors: Dict[str, ActionExecutor]) -> None:
        """Register multiple action executors."""
        self.action_executors.update(executors)

    def _build_phase_context(
        self,
        machine: PhaseMachine,
        state: TaskState,
        last_action: Optional[str] = None,
        last_action_result: Optional[str] = None,
    ) -> PhaseContext:
        """
        Build PhaseContext for guard evaluation.

        Args:
            machine: Current phase machine
            state: Current task state
            last_action: Most recent action name
            last_action_result: Most recent action result

        Returns:
            PhaseContext for transitions
        """
        # Get facts from working memory
        task_dir = self.state_store._task_dir(state.task_id)
        memory_manager = WorkingMemoryManager(task_dir)
        fact_dicts = memory_manager.get_facts(current_step=state.current_step)

        return PhaseContext(
            current_phase=machine.current_phase,
            steps_in_phase=machine.steps_in_phase,
            total_steps=state.current_step,
            verification_passing=state.verification.checks_failing == 0,
            tests_passing=state.verification.tests_passing,
            files_modified=state.context_data.get("files_modified", []),
            facts=fact_dicts,
            last_action=last_action,
            last_action_result=last_action_result,
        )

    def _handle_phase_transition(
        self,
        task_id: str,
        action_name: str,
        action_result: Dict[str, Any],
        state: TaskState,
    ) -> None:
        """
        Handle phase transitions using PhaseMachine when enabled.

        Args:
            task_id: Task identifier
            action_name: Executed action name
            action_result: Action result dict
            state: Current task state
        """
        if not self.use_phase_machine:
            # Legacy behavior
            if action_name == "complete" and action_result.get("status") == "success":
                self.state_store.update_phase(task_id, TaskPhase.COMPLETE)
            elif action_name == "escalate":
                self.state_store.update_phase(task_id, TaskPhase.ESCALATED)
            elif action_name == "cannot_fix":
                self.state_store.update_phase(task_id, TaskPhase.ESCALATED)
                reason = action_result.get("cannot_fix_reason", "Unknown reason")
                self.state_store.update_context_data(task_id, "cannot_fix_reason", reason)
            elif action_result.get("status") == "failure" and action_result.get("fatal"):
                self.state_store.update_phase(task_id, TaskPhase.FAILED)
                self.state_store.set_error(task_id, action_result.get("error", "Unknown error"))
            return

        # Enhanced behavior with PhaseMachine
        machine = state.get_phase_machine()

        # Build context for guard evaluation
        context = self._build_phase_context(
            machine=machine,
            state=state,
            last_action=action_name,
            last_action_result=action_result.get("status"),
        )

        # Record the step in the phase
        machine.advance_step()

        # Check for explicit action-triggered transitions
        target_phase = None

        if action_name == "complete" and action_result.get("status") == "success":
            target_phase = Phase.COMPLETE
        elif action_name in ("escalate", "cannot_fix"):
            target_phase = Phase.ESCALATED
            if action_name == "cannot_fix":
                reason = action_result.get("cannot_fix_reason", "Unknown reason")
                self.state_store.update_context_data(task_id, "cannot_fix_reason", reason)
        elif action_result.get("status") == "failure" and action_result.get("fatal"):
            target_phase = Phase.FAILED
            self.state_store.set_error(task_id, action_result.get("error", "Unknown error"))
        else:
            # Check for auto-transition based on phase success conditions
            target_phase = machine.should_auto_transition(context)

        # Attempt the transition if we have a target
        if target_phase:
            if machine.can_transition(target_phase, context):
                machine.transition(target_phase, context)
                # Update both legacy phase and phase machine state
                legacy_phase = TaskPhase(target_phase.value)
                self.state_store.update_phase(task_id, legacy_phase)
                self.state_store.update_phase_machine(task_id, machine)
            elif target_phase in (Phase.COMPLETE, Phase.ESCALATED, Phase.FAILED):
                # Terminal transitions should always succeed
                machine._current_phase = target_phase
                machine._steps_in_phase = 0
                legacy_phase = TaskPhase(target_phase.value)
                self.state_store.update_phase(task_id, legacy_phase)
                self.state_store.update_phase_machine(task_id, machine)
        else:
            # Just persist the advanced step count
            self.state_store.update_phase_machine(task_id, machine)

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

            # Extract facts from action result (Enhanced Context Engineering)
            if self.enable_understanding_extraction and self.understanding_extractor:
                self._extract_and_store_facts(
                    action_name=action_name,
                    action_result=action_result,
                    step=step,
                    memory_manager=memory_manager,
                )

            # 7. Determine if we should continue
            should_continue = self._should_continue(action_name, action_result, state)

            # Update phase using PhaseMachine (Phase 4) or legacy logic
            self._handle_phase_transition(task_id, action_name, action_result, state)

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

    def _extract_and_store_facts(
        self,
        action_name: str,
        action_result: Dict[str, Any],
        step: int,
        memory_manager: WorkingMemoryManager,
    ) -> None:
        """
        Extract facts from action result and store in working memory.

        This is part of the Enhanced Context Engineering system - instead of
        storing raw action outputs, we extract typed facts that can be used
        to build more compact context.

        Args:
            action_name: Name of the action that was executed
            action_result: Result dict from action execution
            step: Current step number
            memory_manager: Working memory manager for the task
        """
        if not self.understanding_extractor:
            return

        # Convert status string to ActionResult enum
        status = action_result.get("status", "success")
        result_enum = {
            "success": ActionResult.SUCCESS,
            "failure": ActionResult.FAILURE,
            "partial": ActionResult.PARTIAL,
        }.get(status, ActionResult.SUCCESS)

        # Get the output text (summary + error if present)
        output = action_result.get("summary", "")
        if action_result.get("error"):
            output += f"\nError: {action_result['error']}"

        # Also include raw_output if available (from tool execution)
        if action_result.get("raw_output"):
            output += f"\n{action_result['raw_output']}"

        # Extract facts using the rule-based extractor
        facts = self.understanding_extractor.extract(
            tool_name=action_name,
            output=output,
            result=result_enum,
            step=step,
            use_llm_fallback=False,  # Rule-based only for now
        )

        # Store extracted facts in working memory
        if facts:
            memory_manager.add_facts_from_list(facts, step=step)

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

            # Check adaptive budget with enhanced loop detection
            recent = self.state_store.get_recent_actions(task_id, limit=5)
            recent_dicts = [
                {
                    "step": a.step if hasattr(a, 'step') else i + 1,
                    "action": a.action,
                    "target": a.target if hasattr(a, 'target') else None,
                    "parameters": a.parameters,
                    "result": a.result,
                    "summary": a.summary,
                    "error": a.error,
                }
                for a in recent
            ]

            # Get facts from working memory for enhanced loop detection
            facts = None
            if budget.use_enhanced_loop_detection:
                task_dir = self.state_store._task_dir(task_id)
                memory_manager = WorkingMemoryManager(task_dir)
                state = self.state_store.load(task_id)
                if state:
                    fact_dicts = memory_manager.get_facts(current_step=state.current_step)
                    # Convert to simple objects for loop detector
                    facts = fact_dicts  # Loop detector handles dict format

            should_continue, reason, loop_detection = budget.check_continue(
                i + 1, recent_dicts, facts
            )

            if not should_continue:
                # Log the reason for stopping
                print(f"  {reason}")

                # Add loop detection info to the last outcome
                if loop_detection and loop_detection.detected:
                    # Update the last outcome with loop info
                    last_outcome = outcomes[-1]
                    outcomes[-1] = StepOutcome(
                        success=last_outcome.success,
                        action_name=last_outcome.action_name,
                        action_params=last_outcome.action_params,
                        result=last_outcome.result,
                        summary=last_outcome.summary,
                        should_continue=False,
                        tokens_used=last_outcome.tokens_used,
                        duration_ms=last_outcome.duration_ms,
                        error=last_outcome.error,
                        loop_detected=loop_detection,
                    )

                    # Print suggestions if available
                    if loop_detection.suggestions:
                        print("  Suggestions:")
                        for suggestion in loop_detection.suggestions[:3]:
                            print(f"    - {suggestion}")

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
