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
@click.pass_context
def discover(ctx, verbose, path, output, no_save, output_format, phase):
    """
    Run brownfield discovery on an existing codebase.

    Analyzes the codebase to detect:
    - Languages and frameworks
    - Project structure and architecture style
    - Code patterns (Result<T>, CQRS, Repository, etc.)
    - Layer boundaries

    The result is saved to .agentforge/codebase_profile.yaml
    """
    from cli.commands.discover import run_discover

    args = Args()
    args.verbose = verbose
    args.path = path
    args.output = output
    args.no_save = no_save
    args.format = output_format
    args.phase = phase
    run_discover(args)
