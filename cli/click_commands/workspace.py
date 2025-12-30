"""
Workspace management Click commands.

Commands: workspace init, status, add-repo, remove-repo, link, validate, list-repos, unlink
"""

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


@click.group(help='Workspace management commands')
@click.option('--workspace', '-w', type=click.Path(), help='Path to workspace.yaml')
@click.pass_context
def workspace(ctx, workspace):
    """Manage multi-repo workspaces."""
    ctx.ensure_object(dict)
    ctx.obj['workspace'] = workspace


@workspace.command('init', help='Initialize a new workspace or single-repo config')
@click.option('--name', '-n', required=True, help='Workspace/repo name')
@click.option('--path', '-p', type=click.Path(), help='Directory for workspace.yaml')
@click.option('--description', '-d', help='Workspace description')
@click.option('--single-repo', is_flag=True, help='Single-repo mode')
@click.option('--language', '--lang', '-l',
              type=click.Choice(['csharp', 'typescript', 'python', 'java', 'go', 'rust']),
              help='Primary language')
@click.option('--type', '-t', 'repo_type',
              type=click.Choice(['service', 'library', 'application', 'meta', 'tool']),
              default='service', help='Repository type')
@click.option('--force', is_flag=True, help='Overwrite existing')
@click.pass_context
def workspace_init(ctx, name, path, description, single_repo, language, repo_type, force):
    """Initialize workspace configuration."""
    from cli.commands.workspace import run_workspace_init

    args = Args()
    args.name = name
    args.path = path
    args.description = description
    args.single_repo = single_repo
    args.language = language
    args.type = repo_type
    args.force = force
    args.workspace = ctx.obj.get('workspace')
    run_workspace_init(args)


@workspace.command('status', help='Show workspace status')
@click.option('--repo', '-r', type=click.Path(exists=True), help='Repo directory')
@click.pass_context
def workspace_status(ctx, repo):
    """Display workspace status."""
    from cli.commands.workspace import run_workspace_status

    args = Args()
    args.repo = repo
    args.workspace = ctx.obj.get('workspace')
    run_workspace_status(args)


@workspace.command('add-repo', help='Add a repository to workspace')
@click.option('--name', '-n', required=True, help='Repository name')
@click.option('--path', '-p', required=True, type=click.Path(), help='Relative path')
@click.option('--type', '-t', 'repo_type', required=True,
              type=click.Choice(['service', 'library', 'application', 'meta']),
              help='Repository type')
@click.option('--language', '--lang', '-l', required=True,
              type=click.Choice(['csharp', 'typescript', 'python', 'java', 'go', 'rust', 'yaml']),
              help='Primary language')
@click.option('--framework', '-f', help='Framework')
@click.option('--lsp', type=click.Choice(['omnisharp', 'csharp-ls', 'typescript-language-server', 'pyright']),
              help='LSP server')
@click.option('--layers', help='Comma-separated layers')
@click.option('--tags', help='Comma-separated tags')
@click.pass_context
def workspace_add_repo(ctx, name, path, repo_type, language, framework, lsp, layers, tags):
    """Add repository to workspace."""
    from cli.commands.workspace import run_workspace_add_repo

    args = Args()
    args.name = name
    args.path = path
    args.type = repo_type
    args.language = language
    args.framework = framework
    args.lsp = lsp
    args.layers = layers
    args.tags = tags
    args.workspace = ctx.obj.get('workspace')
    run_workspace_add_repo(args)


@workspace.command('remove-repo', help='Remove a repository')
@click.option('--name', '-n', required=True, help='Repository name')
@click.pass_context
def workspace_remove_repo(ctx, name):
    """Remove repository from workspace."""
    from cli.commands.workspace import run_workspace_remove_repo

    args = Args()
    args.name = name
    args.workspace = ctx.obj.get('workspace')
    run_workspace_remove_repo(args)


@workspace.command('link', help='Link a repo to a workspace')
@click.option('--workspace', '-w', required=True, type=click.Path(exists=True),
              help='Path to workspace.yaml')
@click.option('--repo', '-r', type=click.Path(exists=True), help='Repository directory')
@click.pass_context
def workspace_link(ctx, workspace, repo):
    """Link repository to workspace."""
    from cli.commands.workspace import run_workspace_link

    args = Args()
    args.workspace = workspace
    args.repo = repo
    run_workspace_link(args)


@workspace.command('validate', help='Validate workspace configuration')
@click.pass_context
def workspace_validate(ctx):
    """Validate workspace.yaml."""
    from cli.commands.workspace import run_workspace_validate

    args = Args()
    args.workspace = ctx.obj.get('workspace')
    run_workspace_validate(args)


@workspace.command('list-repos', help='List repositories')
@click.option('--type', '-t', 'repo_type',
              type=click.Choice(['service', 'library', 'application', 'meta']),
              help='Filter by type')
@click.option('--language', '--lang', '-l', help='Filter by language')
@click.option('--tag', help='Filter by tag')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['table', 'json', 'yaml']), default='table',
              help='Output format')
@click.pass_context
def workspace_list_repos(ctx, repo_type, language, tag, output_format):
    """List all repositories."""
    from cli.commands.workspace import run_workspace_list_repos

    args = Args()
    args.type = repo_type
    args.language = language
    args.tag = tag
    args.format = output_format
    args.workspace = ctx.obj.get('workspace')
    run_workspace_list_repos(args)


@workspace.command('unlink', help='Unlink repo from workspace')
@click.pass_context
def workspace_unlink(ctx):
    """Unlink repository."""
    from cli.commands.workspace import run_workspace_unlink

    args = Args()
    args.workspace = ctx.obj.get('workspace')
    run_workspace_unlink(args)
