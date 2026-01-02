# @spec_file: .agentforge/specs/cli-click-commands-v1.yaml
# @spec_id: cli-click-commands-v1
# @component_id: cli-click_commands-agent
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Agent Harness CLI Commands
==========================

Commands for managing agent sessions in the Agent Harness.
"""


import click


@click.group("agent", help="Agent Harness session management commands")
def agent():
    """Agent Harness commands for autonomous task execution."""
    pass


@agent.command("start")
@click.argument("task", type=str)
@click.option(
    "--workflow",
    "-w",
    type=click.Choice(["agent", "spec", "tdflow"]),
    default="agent",
    help="Workflow type (default: agent)",
)
@click.option(
    "--phase",
    "-p",
    type=str,
    default="execute",
    help="Initial phase (default: execute)",
)
@click.option(
    "--token-budget",
    "-t",
    type=int,
    default=100000,
    help="Token budget for session (default: 100000)",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["autonomous", "supervised", "interactive"]),
    default="autonomous",
    help="Execution mode (default: autonomous)",
)
def start(task: str, workflow: str, phase: str, token_budget: int, mode: str):
    """Start a new agent session with the given TASK description.

    Example:
        agentforge agent start "Implement user authentication"
    """
    from agentforge.cli.commands.agent import run_start

    run_start(task, workflow, phase, token_budget, mode)


@agent.command("status")
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Session ID (default: current session)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed status information",
)
def status(session: str, verbose: bool):
    """Show current agent session status."""
    from agentforge.cli.commands.agent import run_status

    run_status(session, verbose)


@agent.command("resume")
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Session ID to resume (default: most recent paused)",
)
def resume(session: str):
    """Resume a paused agent session."""
    from agentforge.cli.commands.agent import run_resume

    run_resume(session)


@agent.command("pause")
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Session ID to pause (default: current)",
)
@click.option(
    "--reason",
    "-r",
    type=str,
    default="User requested",
    help="Reason for pausing",
)
def pause(session: str, reason: str):
    """Pause the current agent session."""
    from agentforge.cli.commands.agent import run_pause

    run_pause(session, reason)


@agent.command("stop")
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Session ID to stop (default: current)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force stop without confirmation",
)
def stop(session: str, force: bool):
    """Stop and abort the current agent session."""
    from agentforge.cli.commands.agent import run_stop

    run_stop(session, force)


@agent.command("step")
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Session ID (default: current)",
)
def step(session: str):
    """Execute a single step in the agent session."""
    from agentforge.cli.commands.agent import run_step

    run_step(session)


@agent.command("run")
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Session ID (default: current)",
)
@click.option(
    "--max-iterations",
    "-n",
    type=int,
    default=None,
    help="Maximum iterations (default: from config)",
)
def run(session: str, max_iterations: int):
    """Run agent until completion or iteration limit."""
    from agentforge.cli.commands.agent import run_until_complete

    run_until_complete(session, max_iterations)


@agent.command("list")
@click.option(
    "--state",
    "-s",
    type=click.Choice(["all", "active", "paused", "completed", "aborted"]),
    default="all",
    help="Filter by session state",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Maximum sessions to show",
)
def list_sessions(state: str, limit: int):
    """List agent sessions."""
    from agentforge.cli.commands.agent import run_list

    run_list(state, limit)


@agent.command("history")
@click.option(
    "--session",
    "-s",
    type=str,
    default=None,
    help="Session ID (default: current)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=20,
    help="Maximum history entries to show",
)
def history(session: str, limit: int):
    """Show execution history for a session."""
    from agentforge.cli.commands.agent import run_history

    run_history(session, limit)


@agent.command("cleanup")
@click.option(
    "--days",
    "-d",
    type=int,
    default=30,
    help="Remove sessions older than N days",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be cleaned without deleting",
)
def cleanup(days: int, dry_run: bool):
    """Clean up old agent sessions."""
    from agentforge.cli.commands.agent import run_cleanup

    run_cleanup(days, dry_run)


# ============================================================================
# Fix Violation Commands
# ============================================================================


@agent.command("fix-violation")
@click.argument("violation_id", type=str)
@click.option("--dry-run", is_flag=True, help="Don't make actual changes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--auto-commit", is_flag=True, help="Auto-commit without approval")
def fix_violation(violation_id: str, dry_run: bool, verbose: bool, auto_commit: bool):
    """Fix a specific conformance violation.

    Example:
        agentforge agent fix-violation V-4734938a9485
    """
    from agentforge.cli.commands.agent import run_fix_violation

    run_fix_violation(violation_id, dry_run, verbose, auto_commit)


@agent.command("fix-violations")
@click.option("--limit", "-n", type=int, default=5, help="Max violations to fix")
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["blocker", "critical", "major", "minor"]),
    help="Filter by severity",
)
@click.option("--dry-run", is_flag=True, help="Don't make actual changes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def fix_violations(limit: int, severity: str, dry_run: bool, verbose: bool):
    """Fix multiple violations in batch.

    Example:
        agentforge agent fix-violations --limit 10 --severity major
    """
    from agentforge.cli.commands.agent import run_fix_violations_batch

    run_fix_violations_batch(limit, severity, dry_run, verbose)


@agent.command("approve-commit")
def approve_commit():
    """Approve and apply a pending commit from fix-violation."""
    from agentforge.cli.commands.agent import run_approve_commit

    run_approve_commit()


@agent.command("list-violations")
@click.option(
    "--status",
    "-s",
    type=click.Choice(["open", "resolved", "all"]),
    default="open",
    help="Filter by status (default: open)",
)
@click.option(
    "--severity",
    type=click.Choice(["blocker", "critical", "major", "minor"]),
    help="Filter by severity",
)
@click.option("--limit", "-l", type=int, default=20, help="Max violations to show")
def list_violations(status: str, severity: str, limit: int):
    """List conformance violations that can be fixed.

    Example:
        agentforge agent list-violations --severity major
    """
    from agentforge.cli.commands.agent import run_list_violations

    run_list_violations(status, severity, limit)
