"""
Workspace management commands.

Workspaces provide multi-repository context for code intelligence and
verification. They define relationships between repos that form a logical
product or system.
"""

import json
import sys
from pathlib import Path

import click
import yaml


def run_workspace(args):
    """Workspace management commands - subcommand dispatch handled by subparsers."""
    pass


def run_workspace_init(args):
    """Initialize a new workspace or single-repo config."""
    click.echo()
    click.echo("=" * 60)
    if getattr(args, 'single_repo', False):
        click.echo("WORKSPACE INIT (Single-Repo Mode)")
    else:
        click.echo("WORKSPACE INIT")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import init_single_repo, init_workspace
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    if getattr(args, 'single_repo', False):
        _init_single_repo_mode(args, init_single_repo)
    else:
        _init_workspace_mode(args, init_workspace)


def _init_single_repo_mode(args, init_single_repo):
    """Handle single-repo initialization mode."""
    if not getattr(args, 'language', None):
        click.echo("\nError: --language is required for --single-repo mode")
        sys.exit(1)

    repo_dir = Path(args.path) if args.path else Path.cwd()

    click.echo(f"\n  Location: {repo_dir}")
    click.echo(f"  Name: {args.name}")
    click.echo(f"  Language: {args.language}")
    click.echo(f"  Type: {getattr(args, 'type', 'service') or 'service'}")

    try:
        result = init_single_repo(
            repo_dir, name=args.name, language=args.language,
            repo_type=getattr(args, 'type', 'service') or 'service', force=args.force,
        )
        click.echo(f"\nSingle-repo config initialized: {result}")
        click.echo("\nCreated:\n  .agentforge/\n  ├── repo.yaml\n  ├── contracts/\n  └── specs/")
        click.echo("\nNext steps:\n  1. Add contracts to .agentforge/contracts/\n  2. Run verification: python execute.py verify")
    except Exception as e:
        click.echo(f"\nFailed to initialize: {e}")
        sys.exit(1)


def _init_workspace_mode(args, init_workspace):
    """Handle full workspace initialization mode."""
    workspace_dir = Path(args.path) if args.path else Path.cwd()

    click.echo(f"\n  Location: {workspace_dir}")
    click.echo(f"  Name: {args.name}")
    if args.description:
        click.echo(f"  Description: {args.description}")

    try:
        result = init_workspace(workspace_dir, name=args.name, description=args.description, force=args.force)
        click.echo(f"\nWorkspace initialized: {result}")
        click.echo("\nNext steps:")
        click.echo("  1. Add repositories:")
        click.echo("     python execute.py workspace add-repo --name api --path ../my-api --type service --lang csharp")
        click.echo("  2. Validate workspace:")
        click.echo("     python execute.py workspace validate")
    except Exception as e:
        click.echo(f"\nFailed to initialize workspace: {e}")
        sys.exit(1)


def run_workspace_status(args):
    """Show workspace status and configuration."""
    click.echo()
    click.echo("=" * 60)
    click.echo("WORKSPACE STATUS")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import discover_workspace
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        _print_no_workspace_found()
        sys.exit(1)

    _print_workspace_info(ctx)
    _print_repos_info(ctx)
    _print_paths_info(ctx)
    _print_defaults_info(ctx)


def _print_no_workspace_found():
    """Print message when no workspace is found."""
    click.echo("\nNo workspace found.")
    click.echo("\nDiscovery searched:")
    click.echo("  1. --workspace flag\n  2. AGENTFORGE_WORKSPACE env var")
    click.echo("  3. repo.yaml in current directory\n  4. workspace.yaml in current directory")
    click.echo("  5. agentforge/workspace.yaml subdirectory")
    click.echo("\nInitialize with:\n  python execute.py workspace init --name my-workspace")


def _print_workspace_info(ctx):
    """Print basic workspace info."""
    click.echo(f"\n  Workspace: {ctx.workspace_name}")
    click.echo(f"  Root: {ctx.workspace_dir}")
    click.echo(f"  Config: {ctx.workspace_path}")
    if ctx.workspace_description:
        click.echo(f"  Description: {ctx.workspace_description}")
    if ctx.workspace_version:
        click.echo(f"  Version: {ctx.workspace_version}")


def _print_repos_info(ctx):
    """Print repositories info."""
    click.echo()
    click.echo("-" * 60)
    click.echo(f"REPOSITORIES ({len(ctx.repos)})")
    click.echo("-" * 60)

    for repo in ctx.repos.values():
        status = "OK" if repo.is_available else "NOT FOUND"
        click.echo(f"\n  {repo.name} [{status}]")
        click.echo(f"    Path: {repo.path}\n    Type: {repo.type}\n    Language: {repo.language}")
        if repo.framework:
            click.echo(f"    Framework: {repo.framework}")
        if repo.lsp:
            click.echo(f"    LSP: {repo.lsp}")
        if repo.layers:
            click.echo(f"    Layers: {', '.join(repo.layers)}")
        if repo.tags:
            click.echo(f"    Tags: {', '.join(repo.tags)}")


def _print_paths_info(ctx):
    """Print configured paths."""
    paths = ctx.workspace_config.get('paths', {})
    if paths:
        click.echo()
        click.echo("-" * 60)
        click.echo("PATHS")
        click.echo("-" * 60)
        for key, path in paths.items():
            full_path = ctx.workspace_dir / path
            status = "OK" if full_path.exists() else "MISSING"
            click.echo(f"  {key}: {path} [{status}]")


def _print_defaults_info(ctx):
    """Print default configuration."""
    defaults = ctx.workspace_config.get('defaults', {})
    if defaults:
        click.echo()
        click.echo("-" * 60)
        click.echo("DEFAULTS")
        click.echo("-" * 60)

        context_defaults = defaults.get('context', {})
        if context_defaults:
            click.echo("  Context:")
            click.echo(f"    Budget tokens: {context_defaults.get('budget_tokens', 6000)}")
            provider = context_defaults.get('embedding_provider')
            click.echo(f"    Embedding provider: {provider or 'auto'}")

        verify_defaults = defaults.get('verification', {})
        if verify_defaults:
            click.echo("  Verification:")
            click.echo(f"    Fail fast: {verify_defaults.get('fail_fast', True)}")
            click.echo(f"    Profiles: {', '.join(verify_defaults.get('profiles', ['quick']))}")


def _print_optional_repo_params(args, layers, tags):
    """Print optional repository parameters if set."""
    if args.framework:
        click.echo(f"    Framework: {args.framework}")
    if args.lsp:
        click.echo(f"    LSP: {args.lsp}")
    if layers:
        click.echo(f"    Layers: {', '.join(layers)}")
    if tags:
        click.echo(f"    Tags: {', '.join(tags)}")


def run_workspace_add_repo(args):
    """Add a repository to the workspace."""
    click.echo()
    click.echo("=" * 60)
    click.echo("WORKSPACE ADD-REPO")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import add_repo_to_workspace, discover_workspace
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    ctx = discover_workspace(workspace_arg=args.workspace or None)

    if not ctx.is_workspace_mode:
        click.echo("\nNo workspace found. Initialize first:")
        click.echo("  python execute.py workspace init --name my-workspace")
        sys.exit(1)

    layers = args.layers.split(',') if args.layers else None
    tags = args.tags.split(',') if args.tags else None

    click.echo(f"\n  Workspace: {ctx.workspace_name}")
    click.echo(f"  Adding repo: {args.name}")
    click.echo(f"    Path: {args.path}\n    Type: {args.type}\n    Language: {args.language}")
    _print_optional_repo_params(args, layers, tags)

    try:
        from agentforge.core.workspace import RepoMetadata
        metadata = RepoMetadata(
            repo_type=args.type, language=args.language, framework=args.framework,
            lsp=args.lsp, layers=layers, tags=tags
        )
        add_repo_to_workspace(ctx, name=args.name, path=args.path, metadata=metadata)
        click.echo(f"\nRepository added: {args.name}")
        click.echo(f"   Updated: {ctx.workspace_path}")
    except Exception as e:
        click.echo(f"\nFailed to add repository: {e}")
        sys.exit(1)


def run_workspace_remove_repo(args):
    """Remove a repository from the workspace."""
    click.echo()
    click.echo("=" * 60)
    click.echo("WORKSPACE REMOVE-REPO")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import discover_workspace, remove_repo_from_workspace
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        click.echo("\nNo workspace found.")
        sys.exit(1)

    click.echo(f"\n  Workspace: {ctx.workspace_name}")
    click.echo(f"  Removing repo: {args.name}")

    if args.name not in ctx.repos:
        click.echo(f"\nRepository '{args.name}' not found in workspace.")
        click.echo("Available repos: " + ', '.join(ctx.repos.keys()))
        sys.exit(1)

    removed = remove_repo_from_workspace(ctx, args.name)
    if removed:
        click.echo(f"\nRepository removed: {args.name}")
    else:
        click.echo(f"\nFailed to remove repository: {args.name}")


def run_workspace_link(args):
    """Link a repository to a workspace."""
    click.echo()
    click.echo("=" * 60)
    click.echo("WORKSPACE LINK")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import create_repo_link
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    repo_dir = Path(args.repo).resolve() if args.repo else Path.cwd().resolve()
    workspace_path = Path(args.workspace).resolve()

    if not workspace_path.exists():
        click.echo(f"\nWorkspace not found: {workspace_path}")
        sys.exit(1)

    click.echo(f"\n  Repository: {repo_dir}")
    click.echo(f"  Linking to: {workspace_path}")

    try:
        repo_name = repo_dir.name.lower().replace('_', '-').replace(' ', '-')
        repo_yaml_path = create_repo_link(repo_dir, workspace_path, repo_name)
        click.echo("\nLinked repository to workspace")
        click.echo(f"   Created: {repo_yaml_path}")
    except Exception as e:
        click.echo(f"\nFailed to link repository: {e}")
        sys.exit(1)


def run_workspace_validate(args):
    """Validate workspace configuration."""
    click.echo()
    click.echo("=" * 60)
    click.echo("WORKSPACE VALIDATE")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import discover_workspace, validate_workspace
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        click.echo("\nNo workspace found.")
        sys.exit(1)

    click.echo(f"\n  Workspace: {ctx.workspace_name}")
    click.echo(f"  Config: {ctx.workspace_path}")
    click.echo()
    click.echo("-" * 60)
    click.echo("VALIDATION")
    click.echo("-" * 60)

    errors, warnings = validate_workspace(ctx)

    if not errors:
        click.echo("\nWorkspace configuration is valid!")
    else:
        click.echo("\nWorkspace has configuration errors:")
        for error in errors:
            click.echo(f"   - {error}")

    if warnings:
        click.echo("\nWarnings:")
        for warning in warnings:
            click.echo(f"   - {warning}")

    if errors:
        sys.exit(1)


def _filter_repos(repos: list, args) -> list:
    """Filter repos by type, language, and tag."""
    if args.type:
        repos = [r for r in repos if r.type == args.type]
    if args.language:
        repos = [r for r in repos if r.language == args.language]
    if args.tag:
        repos = [r for r in repos if args.tag in (r.tags or [])]
    return repos


def run_workspace_list_repos(args):
    """List repositories in workspace."""
    click.echo()
    click.echo("=" * 60)
    click.echo("WORKSPACE LIST-REPOS")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import discover_workspace
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    ctx = discover_workspace(workspace_arg=args.workspace or None)

    if not ctx.is_workspace_mode:
        click.echo("\nNo workspace found.")
        sys.exit(1)

    click.echo(f"\n  Workspace: {ctx.workspace_name}")
    click.echo()

    repos = _filter_repos(list(ctx.repos.values()), args)
    _output_repos(repos, args.format)
    click.echo(f"\nTotal: {len(repos)} repository(ies)")


def _output_repos(repos, fmt):
    """Output repos in specified format."""
    if fmt == 'json':
        output = [{'name': r.name, 'path': r.path, 'type': r.type, 'language': r.language, 'framework': r.framework, 'tags': r.tags} for r in repos]
        click.echo(json.dumps(output, indent=2))
    elif fmt == 'yaml':
        output = [{'name': r.name, 'path': r.path, 'type': r.type, 'language': r.language, 'framework': r.framework, 'tags': r.tags} for r in repos]
        click.echo(yaml.dump(output, default_flow_style=False))
    else:
        click.echo(f"{'NAME':<20} {'TYPE':<12} {'LANGUAGE':<12} {'PATH'}")
        click.echo("-" * 70)
        for repo in repos:
            click.echo(f"{repo.name:<20} {repo.type:<12} {repo.language:<12} {repo.path}")


def run_workspace_unlink(args):
    """Unlink current repo from workspace (convert to single-repo mode)."""
    click.echo()
    click.echo("=" * 60)
    click.echo("WORKSPACE UNLINK")
    click.echo("=" * 60)


    try:
        from agentforge.core.workspace import unlink_repo
    except ImportError as e:
        click.echo(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    repo_dir = Path.cwd()
    click.echo(f"\n  Repository: {repo_dir}")

    try:
        unlinked = unlink_repo(repo_dir)
        if unlinked:
            click.echo("\nRepository unlinked from workspace")
            click.echo("   Now in single-repo mode (workspace_ref: null)")
        else:
            click.echo("\nRepository is already in single-repo mode")
    except Exception as e:
        click.echo(f"\nFailed to unlink: {e}")
        sys.exit(1)
