"""
Agent Harness Command Implementations
=====================================

Implementation functions for agent CLI commands.
These functions are called by the Click commands in cli/click_commands/agent.py.
"""

import click
from pathlib import Path
from typing import Optional
from datetime import datetime


def _create_orchestrator():
    """Create and return a configured AgentOrchestrator instance."""
    from tools.harness.session_manager import SessionManager
    from tools.harness.memory_manager import MemoryManager
    from tools.harness.memory_store import MemoryStore
    from tools.harness.tool_selector import ToolSelector
    from tools.harness.tool_registry import ToolRegistry
    from tools.harness.agent_monitor import AgentMonitor
    from tools.harness.recovery_executor import RecoveryExecutor
    from tools.harness.checkpoint_manager import CheckpointManager
    from tools.harness.escalation_manager import EscalationManager
    from tools.harness.agent_orchestrator import AgentOrchestrator
    from tools.harness.orchestrator_domain import OrchestratorConfig, ExecutionMode

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


def _get_current_session_id() -> Optional[str]:
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
    from tools.harness.orchestrator_domain import ExecutionMode

    mode_map = {
        "autonomous": ExecutionMode.AUTONOMOUS,
        "supervised": ExecutionMode.SUPERVISED,
        "interactive": ExecutionMode.INTERACTIVE
    }

    orchestrator = _create_orchestrator()

    click.echo(f"Starting agent session...")
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


def run_status(session_id: Optional[str], verbose: bool) -> None:
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

    if verbose and health and hasattr(health, 'issues'):
        if health.issues:
            click.echo("  Issues:")
            for issue in health.issues:
                click.echo(f"    - {issue}")


def run_resume(session_id: Optional[str]) -> None:
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


def run_pause(session_id: Optional[str], reason: str) -> None:
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


def run_stop(session_id: Optional[str], force: bool) -> None:
    """Stop and abort the current session."""
    if session_id is None:
        session_id = _get_current_session_id()
        if session_id is None:
            click.echo(click.style("No active session to stop.", fg="yellow"))
            return

    if not force:
        if not click.confirm(f"Stop session {session_id}? This cannot be undone."):
            click.echo("Cancelled.")
            return

    orchestrator = _create_orchestrator()
    success = orchestrator.fail_session(session_id, "User requested stop")

    if success:
        _clear_current_session()
        click.echo(click.style(f"✓ Session stopped: {session_id}", fg="green"))
    else:
        click.echo(click.style(f"✗ Failed to stop session: {session_id}", fg="red"))


def run_step(session_id: Optional[str]) -> None:
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
        click.echo(click.style(f"✓ Step completed", fg="green"))
        click.echo(f"  Task ID: {result.task_id}")
        click.echo(f"  Duration: {result.duration_seconds:.2f}s")
        if result.tools_used:
            click.echo(f"  Tools used: {', '.join(result.tools_used)}")
        if result.output:
            click.echo(f"  Output: {result.output}")
    else:
        click.echo(click.style(f"✗ Step failed", fg="red"))
        if result.error:
            click.echo(f"  Error: {result.error}")


def run_until_complete(session_id: Optional[str], max_iterations: Optional[int]) -> None:
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
        click.echo(click.style(f"✓ Session completed successfully", fg="green"))
    else:
        click.echo(click.style(f"✗ Session ended with errors", fg="red"))
        if result.error:
            click.echo(f"  Error: {result.error}")

    click.echo(f"  Final task: {result.task_id}")
    click.echo(f"  Duration: {result.duration_seconds:.2f}s")


def run_list(state: str, limit: int) -> None:
    """List agent sessions."""
    from tools.harness.session_store import SessionStore
    from tools.harness.session_domain import SessionState

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


def run_history(session_id: Optional[str], limit: int) -> None:
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
    from tools.harness.session_manager import SessionManager

    manager = SessionManager()

    if dry_run:
        click.echo(f"Dry run: Would clean sessions older than {days} days")
        count = manager.cleanup_old_sessions(days=days, dry_run=True)
        click.echo(f"Would remove {count} sessions")
    else:
        count = manager.cleanup_old_sessions(days=days, dry_run=False)
        click.echo(click.style(f"✓ Removed {count} old sessions", fg="green"))
