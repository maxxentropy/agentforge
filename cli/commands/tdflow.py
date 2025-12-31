"""
TDFLOW Command Handlers
=======================

Implementation of TDFLOW CLI commands.
"""

from pathlib import Path
from typing import Optional

import click


def run_start(spec_file: Path, framework: str, coverage: float) -> None:
    """
    Start a new TDFLOW session.

    Args:
        spec_file: Path to specification.yaml
        framework: Test framework to use
        coverage: Coverage threshold percentage
    """
    from tools.tdflow.orchestrator import TDFlowOrchestrator

    orchestrator = TDFlowOrchestrator()

    try:
        session = orchestrator.start(
            spec_file=spec_file,
            test_framework=framework,
            coverage_threshold=coverage,
        )

        click.echo()
        click.echo("TDFLOW Session Started")
        click.echo("=" * 40)
        click.echo(f"Session ID: {session.session_id}")
        click.echo(f"Spec: {spec_file}")
        click.echo(f"Framework: {framework}")
        click.echo(f"Coverage Target: {coverage}%")
        click.echo()
        click.echo(f"Components: {len(session.components)}")
        for comp in session.components:
            click.echo(f"  - {comp.name}")
        click.echo()
        click.echo("Run 'agentforge tdflow red' to generate tests.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


def run_red(component_name: Optional[str]) -> None:
    """
    Execute RED phase.

    Args:
        component_name: Specific component or None for next pending
    """
    from tools.tdflow.orchestrator import TDFlowOrchestrator

    orchestrator = TDFlowOrchestrator()

    if not orchestrator.session:
        click.echo("No active session. Run 'agentforge tdflow start' first.", err=True)
        return

    click.echo()
    click.echo(f"RED Phase: {component_name or 'next pending'}")
    click.echo("-" * 40)

    result = orchestrator.run_red(component_name)

    if result.success:
        click.echo()
        click.secho(f"[OK] RED phase complete for {result.component}", fg="green")
        if "tests" in result.artifacts:
            click.echo(f"  Tests: {result.artifacts['tests']}")
        if result.test_result:
            click.echo(f"  Status: {result.test_result.failed} failing (expected)")
        click.echo()
        click.echo("Run 'agentforge tdflow green' to implement.")
    else:
        click.echo()
        click.secho(f"[FAILED] RED phase failed", fg="red")
        for error in result.errors:
            click.echo(f"  - {error}")


def run_green(component_name: Optional[str]) -> None:
    """
    Execute GREEN phase.

    Args:
        component_name: Specific component or None for current
    """
    from tools.tdflow.orchestrator import TDFlowOrchestrator

    orchestrator = TDFlowOrchestrator()

    if not orchestrator.session:
        click.echo("No active session. Run 'agentforge tdflow start' first.", err=True)
        return

    click.echo()
    click.echo(f"GREEN Phase: {component_name or 'current'}")
    click.echo("-" * 40)

    result = orchestrator.run_green(component_name)

    if result.success:
        click.echo()
        click.secho(f"[OK] GREEN phase complete for {result.component}", fg="green")
        if "implementation" in result.artifacts:
            click.echo(f"  Implementation: {result.artifacts['implementation']}")
        if result.test_result:
            click.echo(
                f"  Tests: {result.test_result.passed}/{result.test_result.total} passing"
            )
        click.echo()
        click.echo("Run 'agentforge tdflow verify' or 'tdflow refactor'.")
    else:
        click.echo()
        click.secho(f"[FAILED] GREEN phase failed", fg="red")
        for error in result.errors:
            click.echo(f"  - {error}")


def run_refactor(component_name: Optional[str]) -> None:
    """
    Execute REFACTOR phase.

    Args:
        component_name: Specific component or None for current
    """
    from tools.tdflow.orchestrator import TDFlowOrchestrator

    orchestrator = TDFlowOrchestrator()

    if not orchestrator.session:
        click.echo("No active session. Run 'agentforge tdflow start' first.", err=True)
        return

    click.echo()
    click.echo(f"REFACTOR Phase: {component_name or 'current'}")
    click.echo("-" * 40)

    result = orchestrator.run_refactor(component_name)

    if result.success:
        click.echo()
        click.secho(f"[OK] REFACTOR phase complete for {result.component}", fg="green")
        if result.test_result:
            click.echo(
                f"  Tests: {result.test_result.passed}/{result.test_result.total} passing"
            )
        click.echo()
        click.echo("Run 'agentforge tdflow verify' to complete.")
    else:
        click.echo()
        click.secho(f"[FAILED] REFACTOR phase failed", fg="red")
        for error in result.errors:
            click.echo(f"  - {error}")


def run_verify(component_name: Optional[str]) -> None:
    """
    Execute VERIFY phase.

    Args:
        component_name: Specific component or None for all
    """
    from tools.tdflow.orchestrator import TDFlowOrchestrator

    orchestrator = TDFlowOrchestrator()

    if not orchestrator.session:
        click.echo("No active session. Run 'agentforge tdflow start' first.", err=True)
        return

    click.echo()
    click.echo("Verification Report")
    click.echo("=" * 40)

    report = orchestrator.verify(component_name)

    click.echo(f"Component: {report.component}")
    click.echo(f"Tests: {report.tests_passing}/{report.tests_total}")
    click.echo(f"Coverage: {report.coverage:.1f}%")
    click.echo(f"Violations: {report.conformance_violations}")
    click.echo()

    if report.verified:
        click.secho("[OK] Verified successfully", fg="green")
    else:
        click.secho("[FAILED] Not verified", fg="red")


def run_status() -> None:
    """Show current session status."""
    from tools.tdflow.orchestrator import TDFlowOrchestrator

    orchestrator = TDFlowOrchestrator()
    status = orchestrator.get_status()

    if not status.get("active"):
        click.echo("No active session. Run 'agentforge tdflow start' first.")
        return

    click.echo()
    click.echo(f"TDFLOW Session: {status['session_id']}")
    click.echo("=" * 40)
    click.echo(f"Started: {status['started_at']}")
    click.echo(f"Spec: {status['spec_file']}")
    click.echo(f"Phase: {status['current_phase']}")
    if status.get("current_component"):
        click.echo(f"Current: {status['current_component']}")
    click.echo()
    click.echo("Components:")

    status_icons = {
        "pending": "[ ]",
        "red": "[R]",
        "green": "[G]",
        "refactored": "[F]",
        "verified": "[V]",
        "failed": "[X]",
    }

    for comp in status.get("components", []):
        icon = status_icons.get(comp["status"], "[?]")
        coverage = f"{comp['coverage']:.0f}%" if comp["coverage"] > 0 else "-"
        clean = "" if comp["conformance_clean"] else " (violations)"
        click.echo(f"  {icon} {comp['name']}: {comp['status']} ({coverage}){clean}")


def run_resume() -> None:
    """Resume interrupted session."""
    from tools.tdflow.orchestrator import TDFlowOrchestrator

    orchestrator = TDFlowOrchestrator()
    orchestrator.resume()

    if orchestrator.session:
        click.echo(f"Session resumed: {orchestrator.session.session_id}")
        click.echo("Run 'agentforge tdflow status' for current state.")
    else:
        click.echo("No session to resume.")


def run_list() -> None:
    """List all TDFLOW sessions."""
    from tools.tdflow.session import SessionManager

    manager = SessionManager()
    sessions = manager.list_sessions()

    if not sessions:
        click.echo("No TDFLOW sessions found.")
        return

    click.echo()
    click.echo("TDFLOW Sessions")
    click.echo("=" * 60)

    for sess in sessions:
        click.echo(f"  {sess['session_id']}")
        click.echo(f"    Started: {sess['started_at']}")
        click.echo(f"    Spec: {sess['spec_file']}")
        click.echo(f"    Phase: {sess['current_phase']}")
        click.echo(f"    Components: {sess['component_count']}")
        click.echo()
