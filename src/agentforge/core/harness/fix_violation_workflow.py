"""
Fix Violation Workflow
======================

Orchestrates the process of fixing a conformance violation.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .conformance_tools import CONFORMANCE_TOOL_DEFINITIONS, ConformanceTools
from .git_tools import GIT_TOOL_DEFINITIONS, GitTools
from .llm_executor_domain import (
    ActionType,
    ExecutionContext,
    StepResult,
)
from .test_runner_tools import TEST_TOOL_DEFINITIONS, TestRunnerTools
from .violation_tools import VIOLATION_TOOL_DEFINITIONS, ViolationTools


class FixPhase(Enum):
    """Phases of the fix workflow."""

    ANALYZE = "analyze"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    COMMIT = "commit"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class FixAttempt:
    """Record of a fix attempt."""

    violation_id: str
    started_at: datetime
    phase: FixPhase
    steps: list[StepResult] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    tests_passed: bool = False
    conformance_passed: bool = False
    committed: bool = False
    error: str | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "violation_id": self.violation_id,
            "started_at": self.started_at.isoformat(),
            "phase": self.phase.value,
            "steps": [s.to_dict() for s in self.steps],
            "files_modified": self.files_modified,
            "tests_passed": self.tests_passed,
            "conformance_passed": self.conformance_passed,
            "committed": self.committed,
            "error": self.error,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FixAttempt":
        """Deserialize from dict."""
        return cls(
            violation_id=data["violation_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            phase=FixPhase(data["phase"]),
            steps=[StepResult.from_dict(s) for s in data.get("steps", [])],
            files_modified=data.get("files_modified", []),
            tests_passed=data.get("tests_passed", False),
            conformance_passed=data.get("conformance_passed", False),
            committed=data.get("committed", False),
            error=data.get("error"),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
        )


# Prompt template for violation fixing
FIX_VIOLATION_SYSTEM_PROMPT = """You are an expert software engineer tasked with fixing conformance violations.

Your goal is to fix the violation while:
1. Making minimal changes to the code
2. Following existing code patterns and style
3. Ensuring tests continue to pass
4. Not introducing new violations

Available tools:
{tool_list}

Workflow phases:
1. ANALYZE: Understand the violation and affected code
2. PLAN: Decide on the fix approach
3. IMPLEMENT: Make the code changes
4. VERIFY: Run tests and conformance checks
5. COMMIT: Stage changes for commit (requires human approval)

Important rules:
- Only modify files directly related to the violation
- Always verify your fix with conformance check before committing
- If tests fail, revert changes and try a different approach
- If stuck, escalate to human with clear explanation

Output format:
Use XML tags to indicate your action:

<action type="TOOL_CALL">
<reasoning>Why you are taking this action</reasoning>
<tool name="tool_name">
<param name="param_name">value</param>
</tool>
</action>

<action type="COMPLETE">
<reasoning>Summary of what was fixed</reasoning>
<response>Final status message</response>
</action>

<action type="ESCALATE">
<reasoning>Why you cannot fix this and what help you need</reasoning>
</action>
"""


FIX_VIOLATION_USER_PROMPT = """Fix this conformance violation:

{violation_context}

Current phase: {phase}

Previous steps in this session:
{step_history}

Decide on your next action. Use tools to read files, make changes, and verify fixes.
When the fix is complete and verified, use COMPLETE action.
If you cannot fix it, use ESCALATE action with explanation.
"""


class FixViolationWorkflow:
    """
    Manages the workflow for fixing a single violation.
    """

    def __init__(
        self,
        project_path: Path,
        llm_executor,  # LLMExecutor
        max_iterations: int = 20,
        require_commit_approval: bool = True,
    ):
        """
        Initialize workflow.

        Args:
            project_path: Project root
            llm_executor: LLM executor for agent decisions
            max_iterations: Max steps before failing
            require_commit_approval: Require human approval for commits
        """
        self.project_path = Path(project_path)
        self.llm_executor = llm_executor
        self.max_iterations = max_iterations

        # Initialize tools
        self.violation_tools = ViolationTools(project_path)
        self.conformance_tools = ConformanceTools(project_path)
        self.git_tools = GitTools(project_path, require_approval=require_commit_approval)
        self.test_tools = TestRunnerTools(project_path)

        # Register all tools with executor
        self._register_tools()

    def _register_tools(self):
        """Register all tools with the LLM executor."""
        all_executors = {}
        all_executors.update(self.violation_tools.get_tool_executors())
        all_executors.update(self.conformance_tools.get_tool_executors())
        all_executors.update(self.git_tools.get_tool_executors())
        all_executors.update(self.test_tools.get_tool_executors())

        self.llm_executor.register_tools(all_executors)

    def _build_tool_list(self) -> str:
        """Build formatted tool list for prompt."""
        all_defs = (
            VIOLATION_TOOL_DEFINITIONS
            + CONFORMANCE_TOOL_DEFINITIONS
            + GIT_TOOL_DEFINITIONS
            + TEST_TOOL_DEFINITIONS
        )

        lines = []
        for tool in all_defs:
            params_str = ", ".join(
                f"{name}: {info.get('type', 'any')}"
                for name, info in tool.get("parameters", {}).items()
            )
            lines.append(f"- {tool['name']}({params_str}): {tool['description']}")

        return "\n".join(lines)

    def _format_step_history(self, steps: list[StepResult]) -> str:
        """Format step history for prompt."""
        if not steps:
            return "No steps yet"

        lines = []
        for i, step in enumerate(steps[-5:], 1):  # Only show last 5 steps
            action_type = step.action.action_type.value if step.action else "unknown"
            tools_used = [tr.tool_name for tr in step.tool_results] if step.tool_results else []
            status = "success" if step.success else "failed"
            lines.append(f"  {i}. {action_type} -> {', '.join(tools_used) or 'no tools'} ({status})")

        return "\n".join(lines)

    def fix_violation(
        self,
        violation_id: str,
        on_step: Callable[[StepResult], None] | None = None,
    ) -> FixAttempt:
        """
        Attempt to fix a violation.

        Args:
            violation_id: Violation ID to fix
            on_step: Optional callback after each step

        Returns:
            FixAttempt with results
        """
        attempt = FixAttempt(
            violation_id=violation_id,
            started_at=datetime.utcnow(),
            phase=FixPhase.ANALYZE,
        )

        # Get violation context
        context_result = self.violation_tools.get_violation_context(
            "get_violation_context", {"violation_id": violation_id}
        )

        if not context_result.success:
            attempt.error = f"Failed to get violation context: {context_result.error}"
            attempt.phase = FixPhase.FAILED
            attempt.completed_at = datetime.utcnow()
            return attempt

        # Build execution context
        tool_names = list(self.llm_executor.tool_executors.keys())

        exec_context = ExecutionContext(
            session_id=f"fix-{violation_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            task_description=f"Fix violation {violation_id}",
            current_phase="fix",
            available_tools=tool_names,
            token_budget=50000,
        )

        # Build initial user message with context and instructions
        # Note: System prompt is handled by AgentPromptBuilder
        tool_list = self._build_tool_list()
        initial_message = f"""You are fixing a conformance violation. Here are additional tools available for this task:

{tool_list}

{FIX_VIOLATION_USER_PROMPT.format(
    violation_context=context_result.output,
    phase=attempt.phase.value,
    step_history="No steps yet",
)}"""
        exec_context.add_user_message(initial_message)

        # Run agent loop
        for _i in range(self.max_iterations):
            step_result = self.llm_executor.execute_step(exec_context)
            attempt.steps.append(step_result)

            if on_step:
                on_step(step_result)

            if not step_result.success:
                attempt.error = step_result.error
                attempt.phase = FixPhase.FAILED
                break

            # Check for completion or escalation
            if step_result.action:
                if step_result.action.action_type == ActionType.COMPLETE:
                    attempt.phase = FixPhase.COMPLETE
                    break
                elif step_result.action.action_type == ActionType.ESCALATE:
                    attempt.error = f"Escalated: {step_result.action.reasoning}"
                    attempt.phase = FixPhase.FAILED
                    break

            # Track files modified
            if step_result.tool_results:
                for tr in step_result.tool_results:
                    if tr.tool_name in ("edit_file", "write_file") and tr.success:
                        # Try to extract file path from the tool call
                        if step_result.action and step_result.action.tool_calls:
                            for tc in step_result.action.tool_calls:
                                if tc.name == tr.tool_name:
                                    file_path = tc.parameters.get(
                                        "path", tc.parameters.get("file_path")
                                    )
                                    if file_path and file_path not in attempt.files_modified:
                                        attempt.files_modified.append(file_path)

            # Update phase based on progress
            attempt.phase = self._determine_phase(attempt, step_result)

            # Add follow-up prompt for next iteration
            exec_context.add_user_message(
                FIX_VIOLATION_USER_PROMPT.format(
                    violation_context=context_result.output,
                    phase=attempt.phase.value,
                    step_history=self._format_step_history(attempt.steps),
                )
            )

            if not step_result.should_continue:
                break

        attempt.completed_at = datetime.utcnow()
        return attempt

    def _determine_phase(self, attempt: FixAttempt, step: StepResult) -> FixPhase:
        """Determine current phase based on step results."""
        # Simple heuristic based on tools used
        if not step.tool_results:
            return attempt.phase

        tool_names = [tr.tool_name for tr in step.tool_results]

        if "edit_file" in tool_names or "write_file" in tool_names:
            return FixPhase.IMPLEMENT
        elif "run_tests" in tool_names or "verify_violation_fixed" in tool_names:
            # Track test results
            for tr in step.tool_results:
                if tr.tool_name == "run_tests":
                    attempt.tests_passed = tr.success
                elif tr.tool_name == "verify_violation_fixed":
                    attempt.conformance_passed = tr.success
            return FixPhase.VERIFY
        elif "git_commit" in tool_names:
            for tr in step.tool_results:
                if tr.tool_name == "git_commit" and tr.success:
                    attempt.committed = True
            return FixPhase.COMMIT
        elif "read_file" in tool_names or "read_violation" in tool_names:
            return FixPhase.ANALYZE

        return attempt.phase


def create_fix_workflow(
    project_path: Path,
    require_commit_approval: bool = True,
    max_iterations: int = 20,
) -> FixViolationWorkflow:
    """
    Factory function to create a FixViolationWorkflow with default components.

    Args:
        project_path: Project root directory
        require_commit_approval: Require human approval for commits
        max_iterations: Maximum steps per violation fix

    Returns:
        Configured FixViolationWorkflow
    """
    from .llm_executor import LLMExecutor
    from .tool_executor_bridge import ToolExecutorBridge

    # Create executor with default tools
    tool_bridge = ToolExecutorBridge(project_path)
    llm_executor = LLMExecutor(tool_executors=tool_bridge.get_default_executors())

    return FixViolationWorkflow(
        project_path=project_path,
        llm_executor=llm_executor,
        max_iterations=max_iterations,
        require_commit_approval=require_commit_approval,
    )
