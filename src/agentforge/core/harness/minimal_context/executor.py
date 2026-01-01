# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
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
- AGENT.md configuration hierarchy
- Dynamic project fingerprinting
- Full audit trail with context snapshots
- Progressive compaction for token efficiency
- Native tool calls (Anthropic tool_use API)
- Enhanced loop detection
- Phase machine for state transitions
- Understanding extraction for fact-based reasoning
"""

import asyncio
import inspect
import os
import re
import time
import yaml
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agentforge.core.generate.provider import LLMProvider, get_provider

from ...context import (
    AgentConfigLoader,
    CompactionManager,
    ContextAuditLogger,
    FingerprintGenerator,
    get_template_for_task,
)
from ...llm import (
    LLMClient,
    LLMClientFactory,
    LLMResponse,
    ThinkingConfig,
    ToolCall,
    get_tools_for_task,
)
from .state_store import TaskStateStore, TaskState, TaskPhase
from .template_context_builder import TemplateContextBuilder
from .working_memory import WorkingMemoryManager
from .understanding import UnderstandingExtractor
from .context_models import ActionResult, ActionRecord, AgentResponse, Fact, FactCategory, ActionDef
from .loop_detector import LoopDetector, LoopDetection, LoopType
from .phase_machine import PhaseMachine, Phase, PhaseContext
from .native_tool_executor import NativeToolExecutor, create_standard_handlers


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
    loop_detected: Optional[LoopDetection] = None

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
    1. LOOP DETECTION: Enhanced detection via LoopDetector
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

        # Enhanced loop detection
        self.use_enhanced_loop_detection = use_enhanced_loop_detection
        self.loop_detector = LoopDetector(
            identical_threshold=runaway_threshold,
            semantic_threshold=runaway_threshold + 1,
            cycle_threshold=2,
            no_progress_threshold=no_progress_threshold,
        ) if use_enhanced_loop_detection else None

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
            recent_actions: Last N action records
            facts: Optional list of facts for enhanced loop detection

        Returns:
            (should_continue, reason, loop_detection)
        """
        self._last_loop_detection = None

        # 1. Enhanced loop detection
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
            if self._detect_runaway_legacy(recent_actions):
                return False, "STOPPED: Runaway detected (same action failed 3+ times)", None

        # 2. Update progress tracking
        progress_made = self._update_progress(recent_actions)

        # 3. No-progress detection
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
        """Use enhanced LoopDetector for semantic loop detection."""
        if not self.loop_detector or not recent_actions:
            return None

        action_records = []
        for i, action_dict in enumerate(recent_actions):
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

        return self.loop_detector.check(action_records, facts)

    def _detect_runaway_legacy(self, recent_actions: List[Dict[str, Any]]) -> bool:
        """Legacy runaway detection: repeated identical failures."""
        if len(recent_actions) < self.runaway_threshold:
            return False

        last_n = recent_actions[-self.runaway_threshold:]

        if not all(a.get("result") == "failure" for a in last_n):
            return False

        actions = [a.get("action") for a in last_n]
        if len(set(actions)) != 1:
            return False

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
        """Check if the most recent action made progress."""
        if not recent_actions:
            return False

        latest = recent_actions[-1]
        result = latest.get("result", "failure")
        action = latest.get("action", "")
        summary = latest.get("summary", "")

        if result == "success" and action in [
            "write_file", "edit_file", "replace_lines", "insert_lines", "extract_function"
        ]:
            self._progress_count += 1
            return True

        if "Check PASSED" in summary or "✓" in summary:
            self._progress_count += 3
            return True

        if result == "success" and action in ["read_file", "load_context"]:
            return True

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
        match = re.search(r'Violations?\s*\((\d+)\)', summary)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)\s+violations?', summary, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _calculate_budget(self) -> int:
        """Calculate dynamic budget based on progress."""
        extension = self._progress_count * 3
        dynamic_budget = min(self.base_budget + extension, self.max_budget)
        return dynamic_budget


class MinimalContextExecutor:
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
    - AGENT.md configuration
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
        provider: Optional[LLMProvider] = None,
        state_store: Optional[TaskStateStore] = None,
        action_executors: Optional[Dict[str, ActionExecutor]] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        config_loader: Optional[AgentConfigLoader] = None,
        fingerprint_generator: Optional[FingerprintGenerator] = None,
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
        self.current_audit_logger: Optional[ContextAuditLogger] = None

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

    def register_actions(self, executors: Dict[str, ActionExecutor]) -> None:
        """Register multiple action executors."""
        self.action_executors.update(executors)
        self.native_tool_executor.register_actions(executors)

    def get_fingerprint(
        self,
        constraints: Optional[Dict[str, Any]] = None,
        success_criteria: Optional[List[str]] = None,
    ):
        """Get project fingerprint with task context."""
        return self.fingerprint_generator.with_task_context(
            task_type=self.task_type,
            constraints=constraints or {},
            success_criteria=success_criteria or [],
        )

    def _build_phase_context(
        self,
        machine: PhaseMachine,
        state: TaskState,
        last_action: Optional[str] = None,
        last_action_result: Optional[str] = None,
    ) -> PhaseContext:
        """Build PhaseContext for guard evaluation."""
        task_dir = self.state_store._task_dir(state.task_id)
        memory_manager = WorkingMemoryManager(task_dir)
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

        return PhaseContext(
            current_phase=machine.current_phase,
            steps_in_phase=machine.steps_in_phase,
            total_steps=state.current_step,
            verification_passing=state.verification.checks_failing == 0,
            tests_passing=state.verification.tests_passing,
            files_modified=state.context_data.get("files_modified", []),
            facts=facts,
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
        """Handle phase transitions using PhaseMachine."""
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

        machine = state.get_phase_machine()
        context = self._build_phase_context(
            machine=machine,
            state=state,
            last_action=action_name,
            last_action_result=action_result.get("status"),
        )

        machine.advance_step()

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
            target_phase = machine.should_auto_transition(context)

        if target_phase:
            if machine.can_transition(target_phase, context):
                machine.transition(target_phase, context)
                legacy_phase = TaskPhase(target_phase.value)
                self.state_store.update_phase(task_id, legacy_phase)
                self.state_store.update_phase_machine(task_id, machine)
            elif target_phase in (Phase.COMPLETE, Phase.ESCALATED, Phase.FAILED):
                machine._current_phase = target_phase
                machine._steps_in_phase = 0
                legacy_phase = TaskPhase(target_phase.value)
                self.state_store.update_phase(task_id, legacy_phase)
                self.state_store.update_phase_machine(task_id, machine)
        else:
            self.state_store.update_phase_machine(task_id, machine)

    def _log_step(self, outcome: StepOutcome, task_id: str) -> None:
        """Log step to audit trail."""
        if not self.current_audit_logger:
            return

        state = self.state_store.load(task_id)
        if not state:
            return

        context = {
            "step": state.current_step,
            "phase": state.phase.value,
            "action": outcome.action_name,
            "action_params": outcome.action_params,
            "result": outcome.result,
        }

        token_breakdown = {
            "action": len(str(outcome.action_params)) // 4,
            "result": len(outcome.summary) // 4,
        }

        self.current_audit_logger.log_step(
            step=state.current_step,
            context=context,
            token_breakdown=token_breakdown,
            response=outcome.summary,
        )

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

            # Extract facts from action result
            if self.understanding_extractor:
                self._extract_and_store_facts(
                    action_name=action_name,
                    action_result=action_result,
                    step=step,
                    memory_manager=memory_manager,
                )

            # 7. Determine if we should continue
            should_continue = self._should_continue(action_name, action_result, state)

            # Update phase using PhaseMachine
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
        """Call the LLM provider."""
        prompt = self._messages_to_prompt(messages)

        result = self.provider.generate(prompt, self.max_tokens)

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
        """Parse and validate action from LLM response."""
        # Look for action block
        action_match = re.search(
            r"```action\s*\n(.*?)```",
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if action_match:
            action_yaml = action_match.group(1).strip()
            result = self._parse_and_validate_yaml(action_yaml, "action")
            if result:
                return result

        # Look for yaml block
        yaml_match = re.search(
            r"```yaml\s*\n(.*?)```",
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if yaml_match:
            yaml_content = yaml_match.group(1).strip()
            result = self._parse_and_validate_yaml(yaml_content, "yaml")
            if result:
                return result

        # Fallback: look for simple action pattern
        simple_match = re.search(r"action:\s*(\w+)", response_text)
        if simple_match:
            return simple_match.group(1), {}

        simple_match = re.search(r"name:\s*(\w+)", response_text)
        if simple_match:
            return simple_match.group(1), {}

        if "complete" in response_text.lower():
            return "complete", {}

        return "unknown", {}

    def _parse_and_validate_yaml(
        self,
        yaml_content: str,
        block_type: str,
    ) -> Optional[tuple]:
        """Parse YAML content and validate against AgentResponse schema."""
        try:
            action_data = yaml.safe_load(yaml_content)
            if not isinstance(action_data, dict):
                return None

            name = action_data.get("name") or action_data.get("action")
            if not name:
                return None

            params = action_data.get("parameters", {}) or {}
            reasoning = action_data.get("reasoning")

            try:
                validated = AgentResponse(
                    action=name,
                    parameters=params,
                    reasoning=reasoning,
                )
                return validated.action, validated.parameters
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Response validation failed: {e}. "
                    f"Action: {name}, Parameters: {params}"
                )
                return name, params

        except yaml.YAMLError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"YAML parsing failed: {e}")
            return None

    def _execute_action(
        self,
        action_name: str,
        action_params: Dict[str, Any],
        state: TaskState,
    ) -> Dict[str, Any]:
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
        action_result: Dict[str, Any],
        state: TaskState,
    ) -> bool:
        """Determine if execution should continue."""
        if action_name in ["complete", "escalate", "cannot_fix"]:
            return False

        if action_result.get("fatal"):
            return False

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
        """Extract facts from action result and store in working memory."""
        if not self.understanding_extractor:
            return

        status = action_result.get("status", "success")
        result_enum = {
            "success": ActionResult.SUCCESS,
            "failure": ActionResult.FAILURE,
            "partial": ActionResult.PARTIAL,
        }.get(status, ActionResult.SUCCESS)

        output = action_result.get("summary", "")
        if action_result.get("error"):
            output += f"\nError: {action_result['error']}"
        if action_result.get("raw_output"):
            output += f"\n{action_result['raw_output']}"

        facts = self.understanding_extractor.extract(
            tool_name=action_name,
            output=output,
            result=result_enum,
            step=step,
            use_llm_fallback=False,
        )

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
        # Initialize audit logger
        if self.audit_enabled:
            self.current_audit_logger = ContextAuditLogger(
                project_path=self.project_path,
                task_id=task_id,
            )

        # Reset compaction tracking
        self._compaction_events = 0
        self._tokens_saved = 0

        outcomes = []
        budget = adaptive_budget or AdaptiveBudget(
            base_budget=15,
            max_budget=max_iterations,
        )

        for i in range(max_iterations):
            outcome = self.execute_step(task_id)
            outcomes.append(outcome)

            # Log step
            self._log_step(outcome, task_id)

            if on_step:
                on_step(outcome)

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

            facts = None
            if budget.use_enhanced_loop_detection:
                task_dir = self.state_store._task_dir(task_id)
                memory_manager = WorkingMemoryManager(task_dir)
                state = self.state_store.load(task_id)
                if state:
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

            should_continue, reason, loop_detection = budget.check_continue(
                i + 1, recent_dicts, facts
            )

            # Allow phase transition even if loop detected
            if not should_continue and loop_detection and loop_detection.detected:
                state = self.state_store.load(task_id)
                if state and self.use_phase_machine:
                    machine = state.get_phase_machine()
                    phase_context = self._build_phase_context(
                        machine=machine,
                        state=state,
                        last_action=outcome.action_name,
                        last_action_result=outcome.result,
                    )
                    target_phase = machine.should_auto_transition(phase_context)
                    if target_phase and target_phase != machine.current_phase:
                        should_continue = True
                        reason = f"Phase transition to {target_phase.value} pending"
                        print(f"  (Loop detected but phase transition to {target_phase.value} is possible)")

            if not should_continue:
                print(f"  {reason}")

                if loop_detection and loop_detection.detected:
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

                    if loop_detection.suggestions:
                        print("  Suggestions:")
                        for suggestion in loop_detection.suggestions[:3]:
                            print(f"    - {suggestion}")

                break

        # Log task summary
        if self.current_audit_logger and outcomes:
            last_outcome = outcomes[-1]
            if last_outcome.action_name == "complete":
                final_status = "completed"
            elif last_outcome.action_name in ("escalate", "cannot_fix"):
                final_status = "escalated"
            elif last_outcome.error:
                final_status = "failed"
            else:
                final_status = "stopped"

            total_tokens = sum(o.tokens_used for o in outcomes)
            self.current_audit_logger.log_task_summary(
                total_steps=len(outcomes),
                final_status=final_status,
                total_tokens=total_tokens,
                cached_tokens=0,
                compaction_events=self._compaction_events,
                tokens_saved=self._tokens_saved,
            )

        return outcomes

    def run_task_native(
        self,
        task_id: str,
        domain_context: Optional[Dict[str, Any]] = None,
        llm_client: Optional[LLMClient] = None,
        max_steps: Optional[int] = None,
        on_step: Optional[Callable[[StepOutcome], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run a complete task using native Anthropic tool calls.

        This method uses the Anthropic API's native tool_use feature
        instead of parsing YAML from text responses.

        Args:
            task_id: Task identifier
            domain_context: Domain-specific context (violation info, etc.)
            llm_client: Optional LLM client (creates one if not provided)
            max_steps: Override max steps (uses config if not provided)
            on_step: Optional callback after each step

        Returns:
            Dict with task results and audit info
        """
        # Initialize audit logger
        if self.audit_enabled:
            self.current_audit_logger = ContextAuditLogger(
                project_path=self.project_path,
                task_id=task_id,
            )

        # Reset compaction tracking
        self._compaction_events = 0
        self._tokens_saved = 0

        effective_max_steps = max_steps or self.config.defaults.max_steps

        tools = get_tools_for_task(self.task_type)
        client = llm_client or LLMClientFactory.create()

        # Initialize state
        state = self.state_store.load(task_id)
        if state is None:
            state = self.state_store.create_task(
                task_type=self.task_type,
                goal="Execute task with native tools",
                success_criteria=["Task completes successfully"],
                context_data=domain_context or {},
                task_id=task_id,
            )
        elif domain_context:
            for key, value in domain_context.items():
                self.state_store.update_context_data(task_id, key, value)

        # Configure thinking if enabled
        thinking_config = None
        if self.config.defaults.thinking_enabled:
            thinking_config = ThinkingConfig(
                enabled=True,
                budget_tokens=self.config.defaults.thinking_budget,
            )

        outcomes: List[StepOutcome] = []
        step_num = 0

        while step_num < effective_max_steps:
            step_num += 1

            context = self.context_builder.build(task_id=task_id)
            system_prompt = context.system_prompt
            messages = [{"role": "user", "content": context.user_message}]

            response = client.complete(
                system=system_prompt,
                messages=messages,
                tools=tools,
                thinking=thinking_config,
            )

            outcome = self._process_native_response(
                response=response,
                task_id=task_id,
                step=step_num,
            )
            outcomes.append(outcome)

            self._log_step(outcome, task_id)

            if on_step:
                on_step(outcome)

            if outcome.action_name in ("complete", "escalate", "cannot_fix"):
                break

            if outcome.error:
                break

            self._update_phase_from_action(task_id, outcome.action_name)

        # Determine final status
        if outcomes:
            last_outcome = outcomes[-1]
            if last_outcome.action_name == "complete":
                final_status = "completed"
            elif last_outcome.action_name in ("escalate", "cannot_fix"):
                final_status = "escalated"
            elif last_outcome.error:
                final_status = "failed"
            else:
                final_status = "stopped"
        else:
            final_status = "no_outcomes"

        # Log task summary
        if self.current_audit_logger:
            total_tokens = sum(o.tokens_used for o in outcomes)
            self.current_audit_logger.log_task_summary(
                total_steps=len(outcomes),
                final_status=final_status,
                total_tokens=total_tokens,
                cached_tokens=0,
                compaction_events=self._compaction_events,
                tokens_saved=self._tokens_saved,
            )

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

    def _update_phase_from_action(self, task_id: str, action_name: str) -> None:
        """Update task phase based on action taken."""
        state = self.state_store.load(task_id)
        if not state:
            return

        phase_map = {
            "read_file": TaskPhase.ANALYZE,
            "analyze_dependencies": TaskPhase.ANALYZE,
            "detect_patterns": TaskPhase.ANALYZE,
            "write_file": TaskPhase.IMPLEMENT,
            "edit_file": TaskPhase.IMPLEMENT,
            "run_check": TaskPhase.VERIFY,
            "run_single_test": TaskPhase.VERIFY,
        }

        new_phase = phase_map.get(action_name)
        if new_phase and new_phase != state.phase:
            self.state_store.update_phase(task_id, new_phase)

    def get_native_tool_executor(self) -> NativeToolExecutor:
        """Get the native tool executor for direct access."""
        return self.native_tool_executor


def create_executor(
    project_path: Path,
    task_type: str = "fix_violation",
    action_executors: Optional[Dict[str, ActionExecutor]] = None,
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
