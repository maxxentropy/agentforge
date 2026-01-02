#!/usr/bin/env python3

# @spec_file: .agentforge/specs/cli-v1.yaml
# @spec_id: cli-v1
# @component_id: agentforge-cli-main
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
AgentForge CLI - Click-based command interface.

This module defines the main CLI entry point using Click.
Commands are organized into groups imported from agentforge.cli.click_commands/.
"""

import sys
import click

from agentforge import __version__

EPILOG = """
Workflow:
  agentforge init           # Initialize a project
  agentforge design "goal"  # Design specifications
  agentforge implement      # Full implementation pipeline
  agentforge status         # Check task status

Examples:
  agentforge init
  agentforge conformance check --full
  agentforge discover --patterns
"""


@click.group(epilog=EPILOG)
@click.version_option(version=__version__, prog_name="AgentForge")
@click.option('--use-api', is_flag=True, help='Use Anthropic API instead of Claude Code CLI')
@click.pass_context
def cli(ctx, use_api):
    """AgentForge - Autonomous AI agent framework with verified execution."""
    ctx.ensure_object(dict)
    ctx.obj['use_api'] = use_api


@cli.command()
@click.option('--name', '-n', help='Project name (defaults to directory name)')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing .agentforge directory')
@click.argument('path', required=False, type=click.Path())
def init(name, force, path):
    """Initialize an AgentForge project.

    Creates the .agentforge directory structure with default agent
    definitions and pipeline configurations.

    \b
    Examples:
        agentforge init                    # Initialize current directory
        agentforge init ./my-project       # Initialize specific directory
        agentforge init -n myproject       # Initialize with custom name
    """
    from pathlib import Path as PathLib
    from agentforge.core.init import initialize_project, is_initialized

    project_path = PathLib(path) if path else PathLib.cwd()

    if is_initialized(project_path) and not force:
        click.echo(f"Project already initialized at {project_path / '.agentforge'}")
        click.echo("Use --force to reinitialize.")
        raise SystemExit(1)

    try:
        agentforge_dir = initialize_project(
            project_path=project_path,
            name=name,
            force=force,
        )
        click.echo(f"Initialized AgentForge project at {agentforge_dir}")
        click.echo("\nCreated:")
        click.echo("  .agentforge/")
        click.echo("  .agentforge/agents/     (default agent definitions)")
        click.echo("  .agentforge/pipelines/  (pipeline configurations)")
        click.echo("  .agentforge/violations/ (conformance tracking)")
        click.echo("  .agentforge/tasks/      (task state)")
        click.echo("  .agentforge/context/    (working context)")
        if (project_path / "repo.yaml").exists():
            click.echo("  repo.yaml               (project configuration)")
        click.echo("\nNext steps:")
        click.echo("  agentforge design 'your feature description'")
    except FileExistsError as e:
        click.echo(str(e), err=True)
        raise SystemExit(1)


# Import and register commands from submodules
from agentforge.cli.click_commands.spec import intake, clarify, analyze, draft, validate_spec, revise
from agentforge.cli.click_commands.utility import context, verify, render_spec
from agentforge.cli.click_commands.workspace import workspace
from agentforge.cli.click_commands.config import config
from agentforge.cli.click_commands.contracts import contracts, exemptions
from agentforge.cli.click_commands.conformance import conformance
from agentforge.cli.click_commands.discover import discover
from agentforge.cli.click_commands.bridge import bridge
from agentforge.cli.click_commands.tdflow import tdflow
from agentforge.cli.click_commands.ci import ci
from agentforge.cli.click_commands.generate import generate
from agentforge.cli.click_commands.agent import agent
from agentforge.cli.click_commands.pipeline import (
    start, design, implement, status, resume, approve, reject, abort,
    pipelines, artifacts
)

# Register spec workflow commands
cli.add_command(intake)
cli.add_command(clarify)
cli.add_command(analyze)
cli.add_command(draft)
cli.add_command(validate_spec, name='validate')
cli.add_command(revise)

# Register utility commands
cli.add_command(context)
cli.add_command(verify)
cli.add_command(render_spec)

# Register command groups
cli.add_command(workspace)
cli.add_command(config)
cli.add_command(contracts)
cli.add_command(exemptions)
cli.add_command(conformance)
cli.add_command(discover)
cli.add_command(bridge)
cli.add_command(tdflow)
cli.add_command(ci)
cli.add_command(generate)
cli.add_command(agent)

# Register pipeline commands
cli.add_command(start)
cli.add_command(design)
cli.add_command(implement)
cli.add_command(status)
cli.add_command(resume)
cli.add_command(approve)
cli.add_command(reject)
cli.add_command(abort)
cli.add_command(pipelines)
cli.add_command(artifacts)


def main():
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
