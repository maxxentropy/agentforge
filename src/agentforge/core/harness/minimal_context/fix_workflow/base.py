# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Minimal Context Fix Workflow
============================

Fix violation workflow using the minimal context architecture.
Each step is a fresh conversation with bounded context.

Features:
- Template-based context building (TemplateContextBuilder)
- AGENT.md configuration hierarchy
- Dynamic project fingerprints
- Full audit trail with context snapshots
- Progressive compaction for token efficiency

Test verification uses the violation's test_path field, which is computed
at violation detection time from:
1. Lineage metadata embedded in the source file (explicit, auditable)
2. Convention-based detection (fallback for legacy files)
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from ....refactoring.registry import get_refactoring_provider
from ...conformance_tools import ConformanceTools
from ...git_tools import GitTools
from ...python_tools import PythonTools
from ...refactoring_tools import RefactoringTools
from ...test_runner_tools import RunnerTools
from ...violation_tools import ViolationTools
from ..executor import AdaptiveBudget, MinimalContextExecutor, StepOutcome
from ..phase_machine import PhaseMachine
from ..state_store import Phase, TaskState, TaskStateStore
from ..working_memory import WorkingMemoryManager
from .actions_mixin import ActionsMixin
from .context_mixin import ContextMixin
from .testing_mixin import TestingMixin
from .validation_mixin import ValidationMixin


class MinimalContextFixWorkflow(
    ActionsMixin,
    TestingMixin,
    ValidationMixin,
    ContextMixin,
):
    """
    Fix violation workflow using minimal context architecture v2.

    Key differences from FixViolationWorkflow:
    - State persisted to disk, not in memory
    - Each step is a fresh 2-message conversation
    - Token usage bounded regardless of step count
    - Resumable after crashes

    V2 Architecture features (always enabled):
    - TemplateContextBuilder with task-type specific templates
    - AGENT.md configuration hierarchy
    - Dynamic project fingerprinting
    - Full audit trail with context snapshots
    - Progressive compaction for token efficiency
    - PhaseMachine for explicit phase transitions with guards
    - Enhanced loop detection with semantic analysis
    - Fact extraction from tool outputs instead of raw data
    - Targets ~4000 tokens per step
    """

    def __init__(
        self,
        project_path: Path,
        base_iterations: int = 15,
        max_iterations: int = 50,
        require_commit_approval: bool = True,
    ):
        """
        Initialize workflow.

        Args:
            project_path: Project root
            base_iterations: Initial step budget (extends with progress)
            max_iterations: Hard ceiling for steps (cost control)
            require_commit_approval: Require human approval for commits
        """
        self.project_path = Path(project_path)
        self.base_iterations = base_iterations
        self.max_iterations = max_iterations
        self.require_commit_approval = require_commit_approval

        # Initialize state store
        self.state_store = TaskStateStore(project_path)

        # Initialize tools
        self.violation_tools = ViolationTools(project_path)
        self.conformance_tools = ConformanceTools(project_path)
        self.git_tools = GitTools(project_path, require_approval=require_commit_approval)
        self.test_tools = RunnerTools(project_path)
        self.python_tools = PythonTools(project_path)
        self.refactoring_tools = RefactoringTools(project_path)

        # Build action executors
        self.action_executors = self._build_action_executors()

        # Create executor with template-based context building
        self.executor = MinimalContextExecutor(
            project_path=project_path,
            task_type="fix_violation",
            compaction_enabled=True,
            audit_enabled=True,
        )

        # Register action executors with the executor
        self.executor.register_actions(self.action_executors)

        # Share state store between workflow and executor
        self.executor.state_store = self.state_store
        self.executor.context_builder.state_store = self.state_store

    def _build_action_executors(self) -> dict[str, Callable]:
        """Build action executors for all tools."""
        executors = {}

        # Wrap tool executors to match action executor signature
        def wrap_tool_executor(tool_executor):
            def wrapper(action_name: str, params: dict[str, Any], state: TaskState):
                result = tool_executor(action_name, params)
                return {
                    "status": "success" if result.success else "failure",
                    "summary": result.output[:200] if result.output else "",
                    "error": result.error if hasattr(result, "error") else None,
                    "output": result.output,
                }
            return wrapper

        # Register tool executors
        for name, executor in self.violation_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.conformance_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.git_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.test_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.python_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.refactoring_tools.get_tool_executors().items():
            if name == "extract_function":
                # Special handling for extract_function: auto-run check after success
                executors[name] = self._wrap_extract_function(executor)
            else:
                executors[name] = wrap_tool_executor(executor)

        # Add file read/edit actions - WRAPPED with test verification
        executors["read_file"] = self._action_read_file
        executors["edit_file"] = self._with_test_verification(self._action_edit_file)
        executors["replace_lines"] = self._with_test_verification(self._action_replace_lines)
        executors["insert_lines"] = self._with_test_verification(self._action_insert_lines)
        executors["write_file"] = self._with_test_verification(self._action_write_file)
        executors["run_check"] = self._action_run_check
        executors["run_tests"] = self._action_run_tests
        executors["load_context"] = self._action_load_context
        executors["plan_fix"] = self._action_plan_fix

        return executors

    def fix_violation(
        self,
        violation_id: str,
        on_step: Callable[[StepOutcome], None] | None = None,
    ) -> dict[str, Any]:
        """
        Attempt to fix a violation using minimal context architecture.

        Args:
            violation_id: Violation ID to fix
            on_step: Optional callback after each step

        Returns:
            Dict with fix results
        """
        # Normalize violation ID
        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"

        # Read violation data directly from YAML
        violations_dir = self.project_path / ".agentforge" / "violations"
        violation_file = violations_dir / f"{violation_id}.yaml"

        if not violation_file.exists():
            return {
                "success": False,
                "error": f"Violation not found: {violation_id}",
                "violation_id": violation_id,
            }

        try:
            with open(violation_file) as f:
                violation_data = yaml.safe_load(f)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read violation YAML: {e}",
                "violation_id": violation_id,
            }

        # Extract structured context from YAML
        violation_context = {
            "violation_id": violation_data.get("violation_id", violation_id),
            "check_id": violation_data.get("check_id"),
            "file_path": violation_data.get("file_path"),
            "line_number": violation_data.get("line_number"),
            "severity": violation_data.get("severity"),
            "message": violation_data.get("message"),
            "fix_hint": violation_data.get("fix_hint"),
            "contract_id": violation_data.get("contract_id"),
        }

        # Pre-compute rich context using deterministic tools (no LLM)
        precomputed = self._precompute_violation_context(violation_data)

        # Build context_data with both violation info and pre-computed analysis
        context_data = {
            # Basic violation info
            "violation_id": violation_id,
            "check_id": violation_context.get("check_id"),
            "file_path": violation_context.get("file_path"),
            "line_number": violation_context.get("line_number"),
            "severity": violation_context.get("severity"),
            "message": violation_context.get("message"),
            "fix_hint": violation_context.get("fix_hint"),
            "contract_id": violation_context.get("contract_id"),
            # Test path for verification
            "test_path": violation_data.get("test_path"),
            # Pre-computed analysis (from AST, not LLM)
            "precomputed": precomputed,
        }

        # Create task in state store
        task_state = self.state_store.create_task(
            task_type="fix_violation",
            goal=f"Fix conformance violation {violation_id}",
            success_criteria=[
                "Conformance check passes for the affected file",
                "All existing tests continue to pass",
                "Minimal changes made to fix the issue",
            ],
            constraints=[
                "Only modify files directly related to the violation",
                "Follow existing code patterns",
                "Do not introduce new violations",
            ],
            context_data=context_data,
            task_id=f"fix-{violation_id}",
        )

        # Initialize PhaseMachine for enhanced phase transitions
        phase_machine = PhaseMachine()
        task_state.set_phase_machine(phase_machine)
        self.state_store._save_state(task_state)

        # If we have precomputed function_source, seed a CODE_STRUCTURE fact
        if precomputed.get("function_source"):
            task_dir = self.state_store._task_dir(task_state.task_id)
            memory_manager = WorkingMemoryManager(task_dir)
            memory_manager.add_fact(
                fact_id="precomputed_structure",
                category="code_structure",
                statement=f"Function '{precomputed.get('violating_function', 'target')}' analyzed: {precomputed.get('function_lines', 'lines known')}",
                confidence=1.0,
                source="precomputed_analysis",
                step=0,
            )

        # Run until complete with adaptive budget
        budget = AdaptiveBudget(
            base_budget=self.base_iterations,
            max_budget=self.max_iterations,
        )
        outcomes = self.executor.run_until_complete(
            task_id=task_state.task_id,
            max_iterations=self.max_iterations,
            on_step=on_step,
            adaptive_budget=budget,
        )

        # Load final state
        final_state = self.state_store.load(task_state.task_id)

        return {
            "success": final_state.phase == Phase.COMPLETE,
            "violation_id": violation_id,
            "task_id": task_state.task_id,
            "phase": final_state.phase.value,
            "steps_taken": len(outcomes),
            "total_tokens": sum(o.tokens_used for o in outcomes),
            "files_modified": final_state.context_data.get("files_modified", []),
            "tests_passed": final_state.verification.tests_passing,
            "conformance_passed": final_state.verification.checks_failing == 0,
            "error": final_state.error,
        }

    def resume_task(
        self,
        task_id: str,
        on_step: Callable[[StepOutcome], None] | None = None,
    ) -> dict[str, Any]:
        """
        Resume an existing task.

        Args:
            task_id: Task ID to resume
            on_step: Optional callback after each step

        Returns:
            Dict with fix results
        """
        state = self.state_store.load(task_id)
        if not state:
            return {
                "success": False,
                "error": f"Task not found: {task_id}",
            }

        if state.phase in [Phase.COMPLETE, Phase.FAILED, Phase.ESCALATED]:
            return {
                "success": state.phase == Phase.COMPLETE,
                "task_id": task_id,
                "phase": state.phase.value,
                "error": "Task already complete",
            }

        # Continue execution with adaptive budget
        remaining_budget = max(self.base_iterations, self.max_iterations - state.current_step)
        budget = AdaptiveBudget(
            base_budget=self.base_iterations,
            max_budget=remaining_budget,
        )
        outcomes = self.executor.run_until_complete(
            task_id=task_id,
            max_iterations=remaining_budget,
            on_step=on_step,
            adaptive_budget=budget,
        )

        # Load final state
        final_state = self.state_store.load(task_id)

        return {
            "success": final_state.phase == Phase.COMPLETE,
            "task_id": task_id,
            "phase": final_state.phase.value,
            "steps_taken": len(outcomes),
            "total_tokens": sum(o.tokens_used for o in outcomes),
            "files_modified": final_state.context_data.get("files_modified", []),
            "tests_passed": final_state.verification.tests_passing,
            "conformance_passed": final_state.verification.checks_failing == 0,
            "error": final_state.error,
        }


def create_minimal_fix_workflow(
    project_path: Path,
    require_commit_approval: bool = True,
    base_iterations: int = 15,
    max_iterations: int = 50,
) -> MinimalContextFixWorkflow:
    """
    Factory function to create a MinimalContextFixWorkflow using v2 architecture.

    V2 Architecture features are always enabled:
    - TemplateContextBuilder with task-type specific templates
    - AGENT.md configuration hierarchy
    - Dynamic project fingerprinting
    - Full audit trail with context snapshots
    - Progressive compaction for token efficiency
    - PhaseMachine for phase transitions
    - Enhanced loop detection

    Args:
        project_path: Project root directory
        require_commit_approval: Require human approval for commits
        base_iterations: Initial step budget (extends with progress)
        max_iterations: Hard ceiling for steps (cost control)

    Returns:
        Configured MinimalContextFixWorkflow with v2 executor
    """
    return MinimalContextFixWorkflow(
        project_path=project_path,
        base_iterations=base_iterations,
        max_iterations=max_iterations,
        require_commit_approval=require_commit_approval,
    )
