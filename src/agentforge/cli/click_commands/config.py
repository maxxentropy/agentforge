"""
Configuration management Click commands.

Commands: config init-global, show, set
"""

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


@click.group(help='Configuration management commands')
@click.pass_context
def config(ctx):
    """Manage AgentForge configuration."""
    pass


@config.command('init-global', help='Initialize global config at ~/.agentforge/')
@click.option('--force', is_flag=True, help='Overwrite existing config')
@click.pass_context
def config_init_global(ctx, force):
    """Initialize global configuration."""
    from agentforge.cli.commands.config import run_config_init_global

    args = Args()
    args.force = force
    run_config_init_global(args)


@config.command('show', help='Show configuration')
@click.option('--tier', type=click.Choice(['global', 'workspace', 'repo', 'effective']),
              help='Configuration tier')
@click.pass_context
def config_show(ctx, tier):
    """Display configuration settings."""
    from agentforge.cli.commands.config import run_config_show

    args = Args()
    args.tier = tier
    run_config_show(args)


@config.command('set', help='Set a configuration value')
@click.argument('key')
@click.argument('value')
@click.option('--global', 'set_global', is_flag=True, help='Set in global config')
@click.option('--workspace', 'set_workspace', is_flag=True, help='Set in workspace config')
@click.option('--repo', 'set_repo', is_flag=True, help='Set in repo config')
@click.pass_context
def config_set(ctx, key, value, set_global, set_workspace, set_repo):
    """Set configuration value."""
    from agentforge.cli.commands.config import run_config_set

    args = Args()
    args.key = key
    args.value = value
    args.set_global = set_global
    args.set_workspace = set_workspace
    args.set_repo = set_repo
    run_config_set(args)
