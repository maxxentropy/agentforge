# @spec_file: .agentforge/specs/cli-click-commands-v1.yaml
# @spec_id: cli-click-commands-v1
# @component_id: cli-click_commands-tdflow
# @test_path: tests/unit/tools/tdflow/test_session.py

"""
TDFLOW CLI Commands
===================

Commands for the Test-Driven Flow workflow.
"""

from pathlib import Path

import click


@click.group("tdflow", help="Test-Driven Flow workflow commands")
def tdflow():
    """Test-Driven Flow (TDFLOW) commands."""
    pass


@tdflow.command("start")
@click.option(
    "--spec",
    "-s",
    type=click.Path(exists=True),
    required=True,
    help="Path to specification.yaml",
)
@click.option(
    "--framework",
    "-f",
    type=click.Choice(["auto", "xunit", "nunit", "mstest", "pytest"]),
    default="auto",
    help="Test framework (auto-detect by default)",
)
@click.option(
    "--coverage",
    "-c",
    type=float,
    default=80.0,
    help="Coverage threshold percentage",
)
def start(spec: str, framework: str, coverage: float):
    """Start a new TDFLOW session from specification."""
    from agentforge.cli.commands.tdflow import run_start

    # Auto-detect framework if not specified
    if framework == "auto":
        from agentforge.core.tdflow.runners.base import TestRunner
        try:
            runner = TestRunner.detect(Path.cwd())
            # Map runner class to framework name
            from agentforge.core.tdflow.runners.pytest_runner import PytestRunner
            framework = "pytest" if isinstance(runner, PytestRunner) else "xunit"
            click.echo(f"Auto-detected framework: {framework}")
        except ValueError:
            click.echo("Could not auto-detect framework, defaulting to pytest")
            framework = "pytest"

    run_start(Path(spec), framework, coverage)


@tdflow.command("red")
@click.option("--component", "-c", help="Specific component (default: next pending)")
def red(component: str):
    """Execute RED phase: generate failing tests."""
    from agentforge.cli.commands.tdflow import run_red

    run_red(component)


@tdflow.command("green")
@click.option("--component", "-c", help="Specific component")
def green(component: str):
    """Execute GREEN phase: generate implementation."""
    from agentforge.cli.commands.tdflow import run_green

    run_green(component)


@tdflow.command("refactor")
@click.option("--component", "-c", help="Specific component")
def refactor(component: str):
    """Execute REFACTOR phase: clean up implementation."""
    from agentforge.cli.commands.tdflow import run_refactor

    run_refactor(component)


@tdflow.command("verify")
@click.option("--component", "-c", help="Specific component (default: all)")
def verify(component: str):
    """Verify implementation meets specification."""
    from agentforge.cli.commands.tdflow import run_verify

    run_verify(component)


@tdflow.command("status")
def status():
    """Show current session status."""
    from agentforge.cli.commands.tdflow import run_status

    run_status()


@tdflow.command("resume")
def resume():
    """Resume interrupted session."""
    from agentforge.cli.commands.tdflow import run_resume

    run_resume()


@tdflow.command("list")
def list_sessions():
    """List all TDFLOW sessions."""
    from agentforge.cli.commands.tdflow import run_list

    run_list()
