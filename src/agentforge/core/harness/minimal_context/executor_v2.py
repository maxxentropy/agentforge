# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: executor-v2
# @test_path: tests/unit/harness/test_executor_v2.py

"""
Minimal Context Executor V2
===========================

Enhanced executor with full context management integration:
- AGENT.md configuration hierarchy
- Dynamic project fingerprints
- Task-type specific context templates
- Progressive compaction
- Full audit trail

This is a new implementation that wraps the core MinimalContextExecutor
and adds the context management layer.

Usage:
    ```python
    from agentforge.core.harness.minimal_context.executor_v2 import (
        MinimalContextExecutorV2,
        create_executor_v2,
    )

    # Create executor with v2 features
    executor = create_executor_v2(
        project_path=project_path,
        task_type="fix_violation",
    )

    # Run task
    results = executor.run_task(
        task_id="fix-V-001",
        domain_context={"violation": violation_data},
    )
    ```

Environment Variables:
    AGENTFORGE_CONTEXT_V2: Set to "true" to enable v2 by default
    AGENTFORGE_AUDIT_ENABLED: Set to "false" to disable audit logging
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...context import (
    AgentConfigLoader,
    CompactionManager,
    ContextAuditLogger,
    FingerprintGenerator,
    get_template_for_task,
)
from .executor import MinimalContextExecutor, StepOutcome, AdaptiveBudget
from .state_store import TaskStateStore
from .working_memory import WorkingMemoryManager


class MinimalContextExecutorV2:
    """
    Enhanced executor with full context management.

    Wraps the core MinimalContextExecutor and adds:
    - Configuration from AGENT.md chain
    - Project fingerprinting
    - Context templates
    - Progressive compaction
    - Audit logging
    """

    def __init__(
        self,
        project_path: Path,
        task_type: str = "fix_violation",
        config_loader: Optional[AgentConfigLoader] = None,
        fingerprint_generator: Optional[FingerprintGenerator] = None,
        compaction_enabled: bool = True,
        audit_enabled: bool = True,
        **executor_kwargs,
    ):
        """
        Initialize the v2 executor.

        Args:
            project_path: Root path of the project
            task_type: Type of task (fix_violation, implement_feature, etc.)
            config_loader: Optional custom config loader
            fingerprint_generator: Optional custom fingerprint generator
            compaction_enabled: Enable progressive compaction
            audit_enabled: Enable audit logging
            **executor_kwargs: Additional args for base executor
        """
        self.project_path = Path(project_path).resolve()
        self.task_type = task_type

        # Initialize context management components
        self.config_loader = config_loader or AgentConfigLoader(self.project_path)
        self.config = self.config_loader.load(task_type=task_type)

        self.fingerprint_generator = fingerprint_generator or FingerprintGenerator(
            self.project_path
        )

        # Get template for task type
        try:
            self.template = get_template_for_task(task_type)
        except ValueError:
            # Fall back to fix_violation if task type not found
            self.template = get_template_for_task("fix_violation")

        # Initialize compaction manager
        self.compaction_enabled = compaction_enabled
        if compaction_enabled:
            self.compaction_manager = CompactionManager(
                threshold=0.90,
                max_budget=self.config.defaults.token_budget
                if hasattr(self.config.defaults, "token_budget")
                else 4000,
            )
        else:
            self.compaction_manager = None

        # Audit logging
        self.audit_enabled = audit_enabled and os.environ.get(
            "AGENTFORGE_AUDIT_ENABLED", "true"
        ).lower() != "false"
        self.current_audit_logger: Optional[ContextAuditLogger] = None

        # Tracking
        self._compaction_events = 0
        self._tokens_saved = 0

        # Initialize base executor with config-derived settings
        executor_kwargs.setdefault("model", "claude-sonnet-4-20250514")
        executor_kwargs.setdefault(
            "max_tokens",
            self.config.defaults.thinking_budget
            if self.config.defaults.thinking_enabled
            else 4096,
        )

        self.base_executor = MinimalContextExecutor(
            project_path=self.project_path,
            **executor_kwargs,
        )

    def get_fingerprint(
        self,
        constraints: Optional[Dict[str, Any]] = None,
        success_criteria: Optional[List[str]] = None,
    ):
        """
        Get project fingerprint with task context.

        Args:
            constraints: Task-specific constraints
            success_criteria: Success criteria for the task

        Returns:
            ProjectFingerprint with task context
        """
        return self.fingerprint_generator.with_task_context(
            task_type=self.task_type,
            constraints=constraints or {},
            success_criteria=success_criteria or [],
        )

    def run_task(
        self,
        task_id: str,
        domain_context: Optional[Dict[str, Any]] = None,
        precomputed: Optional[Dict[str, Any]] = None,
        max_steps: Optional[int] = None,
        on_step: Optional[Callable[[StepOutcome], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run a complete task with full context management.

        Args:
            task_id: Task identifier
            domain_context: Domain-specific context (violation info, etc.)
            precomputed: Pre-computed analysis data
            max_steps: Override max steps (uses config if not provided)
            on_step: Optional callback after each step

        Returns:
            Dict with task results and audit info
        """
        # Initialize audit logger for this task
        if self.audit_enabled:
            self.current_audit_logger = ContextAuditLogger(
                project_path=self.project_path,
                task_id=task_id,
            )

        # Reset compaction tracking
        self._compaction_events = 0
        self._tokens_saved = 0

        # Get max steps from config or override
        effective_max_steps = max_steps or self.config.defaults.max_steps

        # Create adaptive budget
        adaptive_budget = AdaptiveBudget(
            base_budget=effective_max_steps // 2,
            max_budget=effective_max_steps,
        )

        # Run with step callback that includes audit logging
        def step_callback(outcome: StepOutcome):
            self._log_step(outcome, task_id)
            if on_step:
                on_step(outcome)

        # Execute using base executor
        outcomes = self.base_executor.run_until_complete(
            task_id=task_id,
            max_iterations=effective_max_steps,
            on_step=step_callback,
            adaptive_budget=adaptive_budget,
        )

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
                cached_tokens=0,  # TODO: Track from actual API responses
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
        }

    def _log_step(self, outcome: StepOutcome, task_id: str) -> None:
        """Log step to audit trail."""
        if not self.current_audit_logger:
            return

        # Get context from base executor's state store
        state = self.base_executor.state_store.load(task_id)
        if not state:
            return

        # Build simplified context dict for audit
        context = {
            "step": state.current_step,
            "phase": state.phase.value,
            "action": outcome.action_name,
            "action_params": outcome.action_params,
            "result": outcome.result,
        }

        # Estimate tokens
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

    def register_action(self, name: str, executor: Callable) -> None:
        """Register an action executor."""
        self.base_executor.register_action(name, executor)

    def register_actions(self, executors: Dict[str, Callable]) -> None:
        """Register multiple action executors."""
        self.base_executor.register_actions(executors)


def create_executor_v2(
    project_path: Path,
    task_type: str = "fix_violation",
    action_executors: Optional[Dict[str, Callable]] = None,
    **kwargs,
) -> MinimalContextExecutorV2:
    """
    Factory function to create a v2 executor.

    Args:
        project_path: Project root path
        task_type: Task type
        action_executors: Optional action executors
        **kwargs: Additional executor options

    Returns:
        Configured MinimalContextExecutorV2
    """
    executor = MinimalContextExecutorV2(
        project_path=project_path,
        task_type=task_type,
        **kwargs,
    )

    if action_executors:
        executor.register_actions(action_executors)

    return executor


def should_use_v2() -> bool:
    """
    Check if v2 should be used based on environment.

    Returns True if AGENTFORGE_CONTEXT_V2=true
    """
    return os.environ.get("AGENTFORGE_CONTEXT_V2", "false").lower() == "true"
