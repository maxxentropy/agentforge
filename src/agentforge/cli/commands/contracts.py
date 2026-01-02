# @spec_file: .agentforge/specs/cli-commands-v1.yaml
# @spec_id: cli-commands-v1
# @component_id: cli-commands-contracts
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

"""Contract management commands - listing, checking, validation, exemptions."""
import click


def run_contracts(args):
    """Fallback for contracts without subcommand."""
    pass


def run_contracts_list(args):
    """List all contracts."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACTS LIST")
    click.echo("=" * 60)

