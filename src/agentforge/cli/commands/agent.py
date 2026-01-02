# @spec_file: .agentforge/specs/cli-commands-v1.yaml
# @spec_id: cli-commands-v1
# @component_id: cli-commands-agent
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Agent Harness Command Implementations
=====================================

Implementation functions for agent CLI commands.
These functions are called by the Click commands in cli/click_commands/agent.py.
"""

from pathlib import Path

import click


def _create_orchestrator():
    """Create and return a configured AgentOrchestrator instance."""
    from agentforge.core.harness.agent_monitor import AgentMonitor
    from agentforge.core.harness.agent_orchestrator import AgentOrchestrator
    from agentforge.core.harness.checkpoint_manager import CheckpointManager
    from agentforge.core.harness.escalation_manager import EscalationManager
    from agentforge.core.harness.memory_manager import MemoryManager
    from agentforge.core.harness.memory_store import MemoryStore
    from agentforge.core.harness.recovery_executor import RecoveryExecutor
    from agentforge.core.harness.session_manager import SessionManager
    from agentforge.core.harness.tool_registry import ToolRegistry
    from agentforge.core.harness.tool_selector import ToolSelector

    # Create components
    session_manager = SessionManager()
    memory_store = MemoryStore()
    memory_manager = MemoryManager(memory_store)
    tool_registry = ToolRegistry()
    tool_selector = ToolSelector(tool_registry)
    agent_monitor = AgentMonitor()
    checkpoint_manager = CheckpointManager()
    recovery_executor = RecoveryExecutor(checkpoint_manager)
    escalation_manager = EscalationManager()

    # Create orchestrator
    orchestrator = AgentOrchestrator(
        session_manager=session_manager,
        memory_manager=memory_manager,
        tool_selector=tool_selector,
        agent_monitor=agent_monitor,
        recovery_executor=recovery_executor,
        escalation_manager=escalation_manager
    )

    return orchestrator


def _get_current_session_id() -> str | None:
    """Get the current active session ID from state file."""
    state_file = Path(".agentforge/harness/current_session.txt")
    if state_file.exists():
        return state_file.read_text().strip()
    return None


def _set_current_session_id(session_id: str) -> None:
    """Store the current session ID."""
    state_dir = Path(".agentforge/harness")
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "current_session.txt").write_text(session_id)


def _clear_current_session() -> None:
    """Clear the current session ID."""
    state_file = Path(".agentforge/harness/current_session.txt")
    if state_file.exists():
        state_file.unlink()


def run_start(task: str, workflow: str, phase: str, token_budget: int, mode: str) -> None:
    """Start a new agent session."""
    from agentforge.core.harness.orchestrator_domain import ExecutionMode

    mode_map = {
        "autonomous": ExecutionMode.AUTONOMOUS,
        "supervised": ExecutionMode.SUPERVISED,
        "interactive": ExecutionMode.INTERACTIVE
    }

    orchestrator = _create_orchestrator()

    click.echo("Starting agent session...")
    click.echo(f"  Task: {task}")
    click.echo(f"  Workflow: {workflow}")
    click.echo(f"  Initial phase: {phase}")
    click.echo(f"  Token budget: {token_budget:,}")
    click.echo(f"  Mode: {mode}")
    click.echo()

    session_id = orchestrator.start_session(
        task_description=task,
        workflow_type=workflow,
        initial_phase=phase,
        token_budget=token_budget,
        execution_mode=mode_map.get(mode)
    )

    _set_current_session_id(session_id)

    click.echo(click.style(f"✓ Session started: {session_id}", fg="green"))
    click.echo()
    click.echo("Next steps:")
    click.echo("  agentforge agent step     # Execute single step")
    click.echo("  agentforge agent run      # Run until completion")
    click.echo("  agentforge agent status   # Check status")


def run_status(session_id: str | None, verbose: bool) -> None:
    """Show session status."""
    if session_id is None:
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No active session. Start one with: agentforge agent start <task>", fg="yellow"))
            return

    orchestrator = _create_orchestrator()
    status = orchestrator.get_status(session_id)

    click.echo(f"Session: {session_id}")
    click.echo(f"  State: {status['state']}")
    click.echo(f"  Iterations: {status['iteration_count']}")
    click.echo(f"  Tokens: {status['tokens_used']:,} / {status['token_budget']:,}")

    if status.get('current_phase'):
        click.echo(f"  Current phase: {status['current_phase']}")

    if status.get('pending_escalations', 0) > 0:
        click.echo(click.style(f"  ⚠ Pending escalations: {status['pending_escalations']}", fg="yellow"))

    health = status.get('health_status')
    if health:
        health_status = getattr(health, 'status', health).name if hasattr(health, 'status') else str(health)
        if health_status == "HEALTHY":
            click.echo(click.style(f"  Health: {health_status}", fg="green"))
        elif health_status == "DEGRADED":
            click.echo(click.style(f"  Health: {health_status}", fg="yellow"))
        else:
            click.echo(click.style(f"  Health: {health_status}", fg="red"))

    if verbose and health and hasattr(health, 'issues') and health.issues:
        click.echo("  Issues:")
        for issue in health.issues:
            click.echo(f"    - {issue}")


def run_resume(session_id: str | None) -> None:
    """Resume a paused session."""
    if session_id is None:
        # Try to find most recent paused session
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No session to resume. Specify --session or start a new one.", fg="yellow"))
            return

    orchestrator = _create_orchestrator()
    success = orchestrator.resume_session(session_id)

    if success:
        _set_current_session_id(session_id)
        click.echo(click.style(f"✓ Session resumed: {session_id}", fg="green"))
    else:
        click.echo(click.style(f"✗ Failed to resume session: {session_id}", fg="red"))


def run_pause(session_id: str | None, reason: str) -> None:
    """Pause the current session."""
    if session_id is None:
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No active session to pause.", fg="yellow"))
            return

    orchestrator = _create_orchestrator()
    success = orchestrator.pause_session(session_id, reason)

    if success:
        click.echo(click.style(f"✓ Session paused: {session_id}", fg="green"))
        click.echo(f"  Reason: {reason}")
    else:
        click.echo(click.style(f"✗ Failed to pause session: {session_id}", fg="red"))


def run_stop(session_id: str | None, force: bool) -> None:
    """Stop and abort the current session."""
    if session_id is None:
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No active session to stop.", fg="yellow"))
            return

    if not force and not click.confirm(f"Stop session {session_id}? This cannot be undone."):
        click.echo("Cancelled.")
        return

    orchestrator = _create_orchestrator()
    success = orchestrator.fail_session(session_id, "User requested stop")

    if success:
        _clear_current_session()
        click.echo(click.style(f"✓ Session stopped: {session_id}", fg="green"))
    else:
        click.echo(click.style(f"✗ Failed to stop session: {session_id}", fg="red"))


def run_step(session_id: str | None) -> None:
    """Execute a single step."""
    if session_id is None:
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No active session. Start one with: agentforge agent start <task>", fg="yellow"))
            return

    orchestrator = _create_orchestrator()

    click.echo(f"Executing step for session {session_id}...")
    result = orchestrator.execute_step(session_id)

    if result.success:
        click.echo(click.style("✓ Step completed", fg="green"))
        click.echo(f"  Task ID: {result.task_id}")
        click.echo(f"  Duration: {result.duration_seconds:.2f}s")
        if result.tools_used:
            click.echo(f"  Tools used: {', '.join(result.tools_used)}")
        if result.output:
            click.echo(f"  Output: {result.output}")
    else:
        click.echo(click.style("✗ Step failed", fg="red"))
        if result.error:
            click.echo(f"  Error: {result.error}")


def run_until_complete(session_id: str | None, max_iterations: int | None) -> None:
    """Run until completion or iteration limit."""
    if session_id is None:
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No active session. Start one with: agentforge agent start <task>", fg="yellow"))
            return

    orchestrator = _create_orchestrator()

    click.echo(f"Running session {session_id}...")
    if max_iterations:
        click.echo(f"  Max iterations: {max_iterations}")

    result = orchestrator.run_until_complete(session_id, max_iterations)

    if result.success:
        click.echo(click.style("✓ Session completed successfully", fg="green"))
    else:
        click.echo(click.style("✗ Session ended with errors", fg="red"))
        if result.error:
            click.echo(f"  Error: {result.error}")

    click.echo(f"  Final task: {result.task_id}")
    click.echo(f"  Duration: {result.duration_seconds:.2f}s")


def run_list(state: str, limit: int) -> None:
    """List agent sessions."""
    from agentforge.core.harness.session_domain import SessionState
    from agentforge.core.harness.session_store import SessionStore

    store = SessionStore()
    session_ids = store.list_sessions()

    if not session_ids:
        click.echo("No sessions found.")
        return

    state_filter = None
    if state != "all":
        state_map = {
            "active": SessionState.ACTIVE,
            "paused": SessionState.PAUSED,
            "completed": SessionState.COMPLETED,
            "aborted": SessionState.ABORTED
        }
        state_filter = state_map.get(state)

    current_session = _get_current_session_id()
    shown = 0

    click.echo("Agent Sessions:")
    click.echo("-" * 60)

    for session_id in session_ids:
        if shown >= limit:
            break

        session = store.load(session_id)
        if session is None:
            continue

        if state_filter and session.state != state_filter:
            continue

        marker = "→ " if session_id == current_session else "  "
        state_color = {
            SessionState.ACTIVE: "green",
            SessionState.PAUSED: "yellow",
            SessionState.COMPLETED: "blue",
            SessionState.ABORTED: "red"
        }.get(session.state, "white")

        click.echo(f"{marker}{session_id}")
        click.echo(f"    State: {click.style(session.state.name, fg=state_color)}")
        click.echo(f"    Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}")
        if session.workflow_type:
            click.echo(f"    Workflow: {session.workflow_type}")

        shown += 1

    click.echo("-" * 60)
    click.echo(f"Showing {shown} of {len(session_ids)} sessions")


def run_history(session_id: str | None, limit: int) -> None:
    """Show execution history."""
    if session_id is None:
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No session specified.", fg="yellow"))
            return

    orchestrator = _create_orchestrator()
    history = orchestrator.get_session_history(session_id)

    if not history:
        click.echo(f"No history for session {session_id}")
        return

    click.echo(f"Execution History for {session_id}:")
    click.echo("-" * 60)

    for i, result in enumerate(history[-limit:], 1):
        status_icon = "✓" if result.success else "✗"
        status_color = "green" if result.success else "red"
        click.echo(f"{i}. {click.style(status_icon, fg=status_color)} {result.task_id}")
        click.echo(f"   Duration: {result.duration_seconds:.2f}s")
        if result.tools_used:
            click.echo(f"   Tools: {', '.join(result.tools_used)}")
        if result.error:
            click.echo(f"   Error: {result.error}")


def run_cleanup(days: int, dry_run: bool) -> None:
    """Clean up old sessions."""
    from agentforge.core.harness.session_manager import SessionManager

    manager = SessionManager()

    if dry_run:
        click.echo(f"Dry run: Would clean sessions older than {days} days")
        count = manager.cleanup_old_sessions(days=days, dry_run=True)
        click.echo(f"Would remove {count} sessions")
    else:
        count = manager.cleanup_old_sessions(days=days, dry_run=False)
        click.echo(click.style(f"✓ Removed {count} old sessions", fg="green"))


# ============================================================================
# Fix Violation Commands
# ============================================================================

def run_fix_violation(
    violation_id: str,
    dry_run: bool = False,
    verbose: bool = False,
    auto_commit: bool = False,
) -> None:
    """
    Fix a single violation using minimal context architecture.

    Args:
        violation_id: Violation ID to fix
        dry_run: Don't make actual changes
        verbose: Show detailed output
        auto_commit: Auto-commit without approval
    """
    import yaml

    from agentforge.core.harness.minimal_context.fix_workflow import (
        create_minimal_fix_workflow,
    )
    from agentforge.core.harness.minimal_context.state_store import Phase

    project_path = Path.cwd()

    click.echo(f"Fixing violation: {violation_id}")
    click.echo(f"Project: {project_path}")
    click.echo("Architecture: Minimal Context (bounded tokens)")
    click.echo()

    # Check violation exists
    if not violation_id.startswith("V-"):
        violation_id = f"V-{violation_id}"

    violation_file = project_path / ".agentforge" / "violations" / f"{violation_id}.yaml"
    if not violation_file.exists():
        click.echo(click.style(f"Violation not found: {violation_id}", fg="red"))
        raise SystemExit(1)

    # Show violation info
    with open(violation_file) as f:
        violation_data = yaml.safe_load(f)

    click.echo("Violation Details:")
    click.echo(f"  Severity: {violation_data.get('severity')}")
    click.echo(f"  File: {violation_data.get('file_path')}")
    click.echo(f"  Check: {violation_data.get('check_id')}")
    click.echo(f"  Message: {violation_data.get('message')}")
    if violation_data.get("fix_hint"):
        click.echo(f"  Hint: {violation_data.get('fix_hint')}")
    click.echo()

    if dry_run:
        click.echo(click.style("DRY RUN - No changes will be made", fg="yellow"))
        click.echo()
        return

    # Create workflow with minimal context architecture
    workflow = create_minimal_fix_workflow(
        project_path=project_path,
        require_commit_approval=not auto_commit,
    )

    # Track steps for verbose output
    step_count = [0]
    total_tokens = [0]

    def on_step(outcome):
        step_count[0] += 1
        total_tokens[0] += outcome.tokens_used
        if verbose:
            click.echo(f"  Step {step_count[0]}: {outcome.action_name}", nl=False)
            click.echo(f" ({outcome.tokens_used} tokens, {outcome.result})")
        else:
            # Show token usage periodically to verify bounded tokens
            if step_count[0] % 3 == 0:
                click.echo(f"  Step {step_count[0]}: {outcome.tokens_used} tokens")

    # Run fix
    click.echo("Starting fix attempt (stateless steps, bounded context)...")
    result = workflow.fix_violation(violation_id, on_step=on_step)

    # Report results
    click.echo()
    click.echo("=" * 60)

    if result.get("success"):
        click.echo(click.style("Fix completed successfully!", fg="green"))
        click.echo(f"  Steps taken: {result.get('steps_taken', 0)}")
        click.echo(f"  Total tokens: {result.get('total_tokens', 0)}")
        if result.get("files_modified"):
            click.echo(f"  Files modified: {', '.join(result.get('files_modified', []))}")

        # Check for pending commit
        pending = workflow.git_tools.get_pending_commit()
        if pending:
            click.echo()
            click.echo("Pending commit:")
            click.echo(f"  Message: {pending.get('message')}")
            click.echo()
            click.echo("Run 'agentforge agent approve-commit' to apply")

    elif result.get("phase") == Phase.FAILED.value:
        click.echo(click.style("Fix failed", fg="red"))
        click.echo(f"  Error: {result.get('error')}")
        click.echo(f"  Steps attempted: {result.get('steps_taken', 0)}")
        click.echo(f"  Total tokens: {result.get('total_tokens', 0)}")

    else:
        click.echo(
            click.style(f"Fix incomplete (phase: {result.get('phase')})", fg="yellow")
        )

    # Task is persisted in state store, show location
    click.echo(f"\nTask state saved: .agentforge/tasks/{result.get('task_id')}/")
    click.echo(f"To resume: agentforge agent resume-task {result.get('task_id')}")


def run_fix_violations_batch(
    limit: int = 5,
    severity: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """
    Fix multiple violations in batch using minimal context architecture.

    Args:
        limit: Maximum violations to attempt
        severity: Filter by severity
        dry_run: Don't make actual changes
        verbose: Show detailed output
    """
    from agentforge.core.harness.minimal_context.fix_workflow import create_minimal_fix_workflow
    from agentforge.core.harness.violation_tools import ViolationTools

    project_path = Path.cwd()
    tools = ViolationTools(project_path)

    # Get violations
    params = {"status": "open", "limit": limit}
    if severity:
        params["severity"] = severity

    result = tools.list_violations("list_violations", params)

    if not result.success:
        click.echo(click.style(f"Error listing violations: {result.error}", fg="red"))
        raise SystemExit(1)

    click.echo("Found violations to fix:")
    click.echo(result.output)
    click.echo()
    click.echo("Architecture: Minimal Context (bounded tokens per step)")
    click.echo()

    if dry_run:
        click.echo(click.style("DRY RUN - Would attempt to fix these violations", fg="yellow"))
        return

    # Parse violation IDs from output and fix each
    violation_ids = []
    for line in result.output.split("\n"):
        line = line.strip()
        if line.startswith("V-"):
            vid = line.split()[0]
            violation_ids.append(vid)

    if not violation_ids:
        click.echo("No violations to fix.")
        return

    click.echo(f"Will attempt to fix {len(violation_ids)} violations...")
    click.echo()

    # Create shared workflow (reuses state store)
    workflow = create_minimal_fix_workflow(
        project_path=project_path,
        require_commit_approval=True,
    )

    fixed = 0
    failed = 0
    total_tokens_all = 0

    for vid in violation_ids:
        click.echo(f"--- Fixing {vid} ---")
        try:
            # Use the workflow directly for efficiency
            result = workflow.fix_violation(vid)
            total_tokens_all += result.get("total_tokens", 0)

            if result.get("success"):
                click.echo(click.style(f"  Fixed! ({result.get('steps_taken')} steps, {result.get('total_tokens')} tokens)", fg="green"))
                fixed += 1
            else:
                click.echo(click.style(f"  Failed: {result.get('error')}", fg="red"))
                failed += 1
        except Exception as e:
            click.echo(click.style(f"Error fixing {vid}: {e}", fg="red"))
            failed += 1

    click.echo()
    click.echo("=" * 60)
    click.echo(f"Fixed: {fixed}, Failed: {failed}")
    click.echo(f"Total tokens used: {total_tokens_all}")
    click.echo()
    click.echo("Task states saved in: .agentforge/tasks/")


def run_approve_commit() -> None:
    """Approve and apply pending commit."""
    from agentforge.core.harness.git_tools import GitTools

    project_path = Path.cwd()
    git_tools = GitTools(project_path)

    pending = git_tools.get_pending_commit()
    if not pending:
        click.echo("No pending commit")
        return

    click.echo("Pending commit:")
    click.echo(f"  Message: {pending.get('message')}")
    click.echo()

    if click.confirm("Apply this commit?"):
        result = git_tools.apply_pending_commit()
        if result.success:
            click.echo(click.style("Committed", fg="green"))
        else:
            click.echo(click.style(f"Failed: {result.error}", fg="red"))
    else:
        click.echo("Commit cancelled")
        git_tools.clear_pending_commit()


def run_list_violations(status: str = "open", severity: str | None = None, limit: int = 20) -> None:
    """List violations that can be fixed."""
    from agentforge.core.harness.violation_tools import ViolationTools

    project_path = Path.cwd()
    tools = ViolationTools(project_path)

    params = {"status": status, "limit": limit}
    if severity:
        params["severity"] = severity

    result = tools.list_violations("list_violations", params)

    if result.success:
        click.echo(result.output)
    else:
        click.echo(click.style(f"Error: {result.error}", fg="red"))
