"""
Utility Click commands.

Commands: context, verify, render-spec
"""

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


@click.command(help='Test context retrieval for a project')
@click.option('--project', '-p', required=True, type=click.Path(exists=True),
              help='Project root path')
@click.option('--query', '-q', help='Search query for context retrieval')
@click.option('--budget', '-b', type=click.IntRange(1000, 100000), default=6000,
              help='Token budget for context')
@click.option('--check', is_flag=True, help='Check available components')
@click.option('--index', is_flag=True, help='Build/rebuild vector index')
@click.option('--force', is_flag=True, help='Force rebuild index')
@click.option('--provider', type=click.Choice(['local', 'openai', 'voyage']),
              help='Embedding provider')
@click.option('--no-lsp', is_flag=True, help='Disable LSP integration')
@click.option('--no-vector', is_flag=True, help='Disable vector search')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'yaml', 'json']), default='text',
              help='Output format')
@click.pass_context
def context(ctx, project, query, budget, check, index, force, provider,
            no_lsp, no_vector, output_format):
    """Retrieve and display project context."""
    from cli.commands.context import run_context

    args = Args()
    args.project = project
    args.query = query
    args.budget = budget
    args.check = check
    args.index = index
    args.force = force
    args.provider = provider
    args.no_lsp = no_lsp
    args.no_vector = no_vector
    args.format = output_format
    args.use_api = ctx.obj.get('use_api', False)
    run_context(args)


@click.command(help='Run deterministic verification checks')
@click.option('--profile', '-p',
              type=click.Choice(['quick', 'ci', 'full', 'architecture', 'precommit']),
              help='Verification profile to run')
@click.option('--checks', '-c', help='Comma-separated list of check IDs')
@click.option('--project', type=click.Path(exists=True),
              help='Path to project file')
@click.option('--project-root', type=click.Path(exists=True),
              help='Project root directory')
@click.option('--config', type=click.Path(exists=True),
              help='Path to correctness.yaml')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'yaml', 'json']), default='yaml',
              help='Output format')
@click.option('--strict', is_flag=True, help='Fail on warnings too')
@click.pass_context
def verify(ctx, profile, checks, project, project_root, config, output_format, strict):
    """Run deterministic correctness verification."""
    from cli.commands.verify import run_verify

    args = Args()
    args.profile = profile
    args.checks = checks
    args.project = project
    args.project_root = project_root
    args.config = config
    args.format = output_format
    args.strict = strict
    args.use_api = ctx.obj.get('use_api', False)
    run_verify(args)


@click.command('render-spec', help='Render YAML specification to Markdown')
@click.option('--spec-file', default='outputs/specification.yaml',
              type=click.Path(exists=True), help='Path to specification')
@click.option('--output', '-o', default='outputs/specification.md',
              type=click.Path(), help='Output Markdown path')
@click.pass_context
def render_spec(ctx, spec_file, output):
    """Convert specification to human-readable Markdown."""
    from cli.render import run_render_spec

    args = Args()
    args.spec_file = spec_file
    args.output = output
    args.use_api = ctx.obj.get('use_api', False)
    run_render_spec(args)
