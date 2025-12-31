"""
Brownfield Discovery Click commands.

Commands: discover (main), discover show, discover phases
"""

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


@click.command('discover', help='Run brownfield discovery on codebase')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--path', '-p', type=click.Path(exists=True), default='.',
              help='Root path to analyze (default: current directory)')
@click.option('--output', '-o', type=click.Path(), help='Custom output path for profile')
@click.option('--no-save', is_flag=True, help='Do not save profile to disk')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['yaml', 'json', 'summary']), default='summary',
              help='Output format')
@click.option('--phase', type=click.Choice([
    'language', 'structure', 'patterns', 'architecture', 'all'
]), default='all', help='Run specific phase only')
@click.option('--zone', '-z', type=str, help='Analyze specific zone only')
@click.option('--list-zones', is_flag=True, help='List detected zones without analysis')
@click.option('--interactions', is_flag=True, help='Show detected cross-zone interactions')
@click.option('--multi-zone', is_flag=True, help='Enable multi-zone discovery mode')
@click.pass_context
def discover(ctx, verbose, path, output, no_save, output_format, phase, zone, list_zones, interactions, multi_zone):
    """
    Run brownfield discovery on an existing codebase.

    Analyzes the codebase to detect:
    - Languages and frameworks
    - Project structure and architecture style
    - Code patterns (Result<T>, CQRS, Repository, etc.)
    - Layer boundaries
    - Zones (in multi-zone mode)
    - Cross-zone interactions

    The result is saved to .agentforge/codebase_profile.yaml

    Examples:
      agentforge discover                    # Single-zone discovery
      agentforge discover --multi-zone       # Multi-zone discovery
      agentforge discover --list-zones       # List detected zones
      agentforge discover --zone core-api    # Analyze specific zone
      agentforge discover --interactions     # Show zone interactions
    """
    from agentforge.cli.commands.discover import run_discover

    args = Args()
    args.verbose = verbose
    args.path = path
    args.output = output
    args.no_save = no_save
    args.format = output_format
    args.phase = phase
    args.zone = zone
    args.list_zones = list_zones
    args.interactions = interactions
    args.multi_zone = multi_zone or zone is not None or list_zones or interactions
    run_discover(args)
