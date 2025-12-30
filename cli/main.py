#!/usr/bin/env python3
"""
AgentForge CLI - Click-based command interface.

This module defines the main CLI entry point using Click.
Commands are organized into groups imported from cli/click_commands/.
"""

import click

__version__ = "2.0.0"

EPILOG = """
Workflow:
  intake → clarify → analyze → draft → validate → revise → verify

Examples:
  python execute.py intake --request "Add discount codes"
  python execute.py conformance check --full
  python execute.py verify --profile ci
"""


@click.group(epilog=EPILOG)
@click.version_option(version=__version__, prog_name="AgentForge")
@click.option('--use-api', is_flag=True, help='Use Anthropic API instead of Claude Code CLI')
@click.pass_context
def cli(ctx, use_api):
    """AgentForge - Contract-driven specification system."""
    ctx.ensure_object(dict)
    ctx.obj['use_api'] = use_api


# Import and register commands from submodules
from cli.click_commands.spec import intake, clarify, analyze, draft, validate_spec, revise
from cli.click_commands.utility import context, verify, render_spec
from cli.click_commands.workspace import workspace
from cli.click_commands.config import config
from cli.click_commands.contracts import contracts, exemptions
from cli.click_commands.conformance import conformance

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


def main():
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
