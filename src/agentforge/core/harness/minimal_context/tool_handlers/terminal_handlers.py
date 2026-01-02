# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: terminal-handlers
# @test_path: tests/unit/harness/tool_handlers/test_terminal_handlers.py

"""
Terminal Handlers
=================

Handlers for terminal actions: complete, escalate, cannot_fix.

These handlers signal the end of a task execution with different outcomes.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .constants import PLAN_DISPLAY_MAX_STEPS, SUMMARY_FIELD_MAX_CHARS
from .types import ActionHandler

logger = logging.getLogger(__name__)


def create_complete_handler() -> ActionHandler:
    """
    Create a complete action handler.

    Signals successful task completion with a summary.

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """

    def handler(params: dict[str, Any]) -> str:
        summary = params.get("summary", "Task completed")
        files_modified = params.get("files_modified", [])
        logger.debug("complete: summary=%s", summary[:50] if len(summary) > 50 else summary)

        # Get context for additional info
        context = params.get("_context", {})
        context_files = context.get("files_modified", [])

        all_files = list(set(files_modified + context_files))

        result_parts = [f"COMPLETE: {summary}"]

        if all_files:
            result_parts.append(f"  Files modified: {', '.join(all_files)}")

        return "\n".join(result_parts)

    return handler


def create_escalate_handler() -> ActionHandler:
    """
    Create an escalate action handler.

    Signals that human intervention is needed for a non-blocking reason.

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """

    def handler(params: dict[str, Any]) -> str:
        reason = params.get("reason", "Unknown reason")
        priority = params.get("priority", "medium")
        suggestions = params.get("suggestions", [])
        logger.debug("escalate: priority=%s, reason=%s", priority, reason[:50])

        result_parts = [f"ESCALATE: {reason}"]
        result_parts.append(f"  Priority: {priority}")

        if suggestions:
            result_parts.append("  Suggestions:")
            for s in suggestions:
                result_parts.append(f"    - {s}")

        return "\n".join(result_parts)

    return handler


def create_cannot_fix_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create a cannot_fix action handler.

    Records the inability to fix a violation with detailed reasoning.
    Creates an escalation record for human review.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        reason = params.get("reason", "")
        constraints = params.get("constraints", [])
        alternatives = params.get("alternatives", [])
        logger.debug("cannot_fix: reason=%s", reason[:50] if reason else "None")

        if not reason:
            return "ERROR: reason parameter required"

        # Get context from working memory
        context = params.get("_context", {})
        violation_id = context.get("violation_id", "unknown")
        task_id = context.get("task_id", "unknown")

        try:
            # Create escalation record
            escalation_dir = base_path / ".agentforge" / "escalations"
            escalation_dir.mkdir(parents=True, exist_ok=True)

            escalation_id = f"ESC-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

            escalation_record = {
                "escalation_id": escalation_id,
                "type": "cannot_fix",
                "violation_id": violation_id,
                "task_id": task_id,
                "created_at": datetime.now(UTC).isoformat(),
                "status": "pending",
                "reason": reason,
                "constraints": constraints,
                "alternatives": alternatives,
                "agent_analysis": {
                    "attempted_approaches": context.get("attempted_approaches", []),
                    "files_examined": context.get("files_examined", []),
                    "understanding": context.get("understanding", []),
                },
            }

            escalation_file = escalation_dir / f"{escalation_id}.yaml"
            with open(escalation_file, "w") as f:
                yaml.dump(escalation_record, f, default_flow_style=False)

            # Update violation status if we have access
            if violation_id != "unknown":
                _update_violation_status(base_path, violation_id, reason)

            # Format response
            response_parts = [
                "CANNOT_FIX: Escalation created",
                f"  Escalation ID: {escalation_id}",
                f"  Violation: {violation_id}",
                f"  Reason: {reason}",
            ]

            if constraints:
                response_parts.append("  Constraints:")
                for c in constraints:
                    response_parts.append(f"    - {c}")

            if alternatives:
                response_parts.append("  Suggested alternatives:")
                for a in alternatives:
                    response_parts.append(f"    - {a}")

            try:
                rel_path = escalation_file.relative_to(base_path)
            except ValueError:
                rel_path = escalation_file
            response_parts.append(f"\n  Escalation file: {rel_path}")

            return "\n".join(response_parts)

        except Exception as e:
            return f"ERROR: Failed to create escalation: {e}"

    def _update_violation_status(
        base_path: Path, violation_id: str, reason: str
    ) -> None:
        """Update violation status to indicate cannot fix."""
        try:
            violation_file = base_path / ".agentforge" / "violations" / f"{violation_id}.yaml"

            if not violation_file.exists():
                return

            with open(violation_file) as f:
                violation = yaml.safe_load(f)

            # Keep status as open but add agent notes
            violation["agent_notes"] = f"Cannot fix: {reason}"
            violation["escalated"] = True

            with open(violation_file, "w") as f:
                yaml.dump(violation, f, default_flow_style=False)

        except Exception:
            pass  # Non-critical if update fails

    return handler


def create_request_help_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create a request_help action handler.

    Requests human assistance for a specific aspect of the task
    without fully escalating.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        question = params.get("question", "")
        options = params.get("options", [])
        context_info = params.get("context", "")

        if not question:
            return "ERROR: question parameter required"

        # Get context
        ctx = params.get("_context", {})
        task_id = ctx.get("task_id", "unknown")
        current_step = ctx.get("current_step", 0)

        try:
            # Create help request record
            help_dir = base_path / ".agentforge" / "help_requests"
            help_dir.mkdir(parents=True, exist_ok=True)

            request_id = f"HELP-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

            request_record = {
                "request_id": request_id,
                "task_id": task_id,
                "step": current_step,
                "created_at": datetime.now(UTC).isoformat(),
                "status": "pending",
                "question": question,
                "options": options,
                "context": context_info,
            }

            request_file = help_dir / f"{request_id}.yaml"
            with open(request_file, "w") as f:
                yaml.dump(request_record, f, default_flow_style=False)

            response_parts = [
                f"HELP_REQUESTED: {request_id}",
                f"  Question: {question}",
            ]

            if options:
                response_parts.append("  Options:")
                for i, opt in enumerate(options, 1):
                    response_parts.append(f"    {i}. {opt}")

            response_parts.append("\n  Waiting for human response...")

            return "\n".join(response_parts)

        except Exception as e:
            return f"ERROR: Failed to create help request: {e}"

    return handler


def create_plan_fix_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create a plan_fix action handler.

    Records a fix plan and advances to the implement phase.
    This is used in workflows with explicit planning phases.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        diagnosis = params.get("diagnosis", "")
        approach = params.get("approach", "")
        steps = params.get("steps", [])

        if not approach:
            return "ERROR: approach parameter required"

        # Get context
        context = params.get("_context", {})
        task_id = context.get("task_id")

        if task_id:
            # Try to update task state
            try:
                from ..state_store import Phase, TaskStateStore

                state_store = TaskStateStore(base_path)
                state_store.update_context_data(task_id, "diagnosis", diagnosis)
                state_store.update_context_data(task_id, "approach", approach)
                state_store.update_context_data(task_id, "planned_steps", steps)
                state_store.update_phase(task_id, Phase.IMPLEMENT)

            except Exception:
                pass  # Non-critical if state update fails

        result_parts = [
            "PLAN_RECORDED",
            f"  Diagnosis: {diagnosis[:SUMMARY_FIELD_MAX_CHARS]}..." if len(diagnosis) > SUMMARY_FIELD_MAX_CHARS else f"  Diagnosis: {diagnosis}",
            f"  Approach: {approach[:SUMMARY_FIELD_MAX_CHARS]}..." if len(approach) > SUMMARY_FIELD_MAX_CHARS else f"  Approach: {approach}",
        ]

        if steps:
            result_parts.append("  Steps:")
            for i, step in enumerate(steps[:PLAN_DISPLAY_MAX_STEPS], 1):
                result_parts.append(f"    {i}. {step}")
            if len(steps) > PLAN_DISPLAY_MAX_STEPS:
                result_parts.append(f"    ... and {len(steps) - PLAN_DISPLAY_MAX_STEPS} more")

        result_parts.append("\n  Ready to implement.")

        return "\n".join(result_parts)

    return handler
