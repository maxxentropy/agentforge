"""
Workspace management commands.

Workspaces provide multi-repository context for code intelligence and
verification. They define relationships between repos that form a logical
product or system.
"""

import sys
import json
import yaml
from pathlib import Path


def _ensure_workspace_tools():
    """Add tools directory to path for workspace imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))


def run_workspace(args):
    """Workspace management commands - subcommand dispatch handled by subparsers."""
    pass


def run_workspace_init(args):
    """Initialize a new workspace or single-repo config."""
    print()
    print("=" * 60)
    if getattr(args, 'single_repo', False):
        print("WORKSPACE INIT (Single-Repo Mode)")
    else:
        print("WORKSPACE INIT")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import init_workspace, init_single_repo
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    if getattr(args, 'single_repo', False):
        _init_single_repo_mode(args, init_single_repo)
    else:
        _init_workspace_mode(args, init_workspace)


def _init_single_repo_mode(args, init_single_repo):
    """Handle single-repo initialization mode."""
    if not getattr(args, 'language', None):
        print("\n❌ Error: --language is required for --single-repo mode")
        sys.exit(1)

    repo_dir = Path(args.path) if args.path else Path.cwd()

    print(f"\n  Location: {repo_dir}")
    print(f"  Name: {args.name}")
    print(f"  Language: {args.language}")
    print(f"  Type: {getattr(args, 'type', 'service') or 'service'}")

    try:
        result = init_single_repo(
            repo_dir, name=args.name, language=args.language,
            repo_type=getattr(args, 'type', 'service') or 'service', force=args.force,
        )
        print(f"\n✅ Single-repo config initialized: {result}")
        print("\nCreated:\n  .agentforge/\n  ├── repo.yaml\n  ├── contracts/\n  └── specs/")
        print("\nNext steps:\n  1. Add contracts to .agentforge/contracts/\n  2. Run verification: python execute.py verify")
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        sys.exit(1)


def _init_workspace_mode(args, init_workspace):
    """Handle full workspace initialization mode."""
    workspace_dir = Path(args.path) if args.path else Path.cwd()

    print(f"\n  Location: {workspace_dir}")
    print(f"  Name: {args.name}")
    if args.description:
        print(f"  Description: {args.description}")

    try:
        result = init_workspace(workspace_dir, name=args.name, description=args.description, force=args.force)
        print(f"\n✅ Workspace initialized: {result}")
        print("\nNext steps:")
        print("  1. Add repositories:")
        print(f"     python execute.py workspace add-repo --name api --path ../my-api --type service --lang csharp")
        print("  2. Validate workspace:")
        print("     python execute.py workspace validate")
    except Exception as e:
        print(f"\n❌ Failed to initialize workspace: {e}")
        sys.exit(1)


def run_workspace_status(args):
    """Show workspace status and configuration."""
    print()
    print("=" * 60)
    print("WORKSPACE STATUS")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import discover_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
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
    print("\n❌ No workspace found.")
    print("\nDiscovery searched:")
    print("  1. --workspace flag\n  2. AGENTFORGE_WORKSPACE env var")
    print("  3. repo.yaml in current directory\n  4. workspace.yaml in current directory")
    print("  5. agentforge/workspace.yaml subdirectory")
    print("\nInitialize with:\n  python execute.py workspace init --name my-workspace")


def _print_workspace_info(ctx):
    """Print basic workspace info."""
    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Root: {ctx.workspace_dir}")
    print(f"  Config: {ctx.workspace_path}")
    if ctx.workspace_description:
        print(f"  Description: {ctx.workspace_description}")
    if ctx.workspace_version:
        print(f"  Version: {ctx.workspace_version}")


def _print_repos_info(ctx):
    """Print repositories info."""
    print()
    print("-" * 60)
    print(f"REPOSITORIES ({len(ctx.repos)})")
    print("-" * 60)

    for repo in ctx.repos.values():
        status = "✓" if repo.is_available else "✗ NOT FOUND"
        print(f"\n  {repo.name} [{status}]")
        print(f"    Path: {repo.path}\n    Type: {repo.type}\n    Language: {repo.language}")
        if repo.framework:
            print(f"    Framework: {repo.framework}")
        if repo.lsp:
            print(f"    LSP: {repo.lsp}")
        if repo.layers:
            print(f"    Layers: {', '.join(repo.layers)}")
        if repo.tags:
            print(f"    Tags: {', '.join(repo.tags)}")


def _print_paths_info(ctx):
    """Print configured paths."""
    paths = ctx.workspace_config.get('paths', {})
    if paths:
        print()
        print("-" * 60)
        print("PATHS")
        print("-" * 60)
        for key, path in paths.items():
            full_path = ctx.workspace_dir / path
            status = "✓" if full_path.exists() else "✗"
            print(f"  {key}: {path} [{status}]")


def _print_defaults_info(ctx):
    """Print default configuration."""
    defaults = ctx.workspace_config.get('defaults', {})
    if defaults:
        print()
        print("-" * 60)
        print("DEFAULTS")
        print("-" * 60)

        context_defaults = defaults.get('context', {})
        if context_defaults:
            print("  Context:")
            print(f"    Budget tokens: {context_defaults.get('budget_tokens', 6000)}")
            provider = context_defaults.get('embedding_provider')
            print(f"    Embedding provider: {provider or 'auto'}")

        verify_defaults = defaults.get('verification', {})
        if verify_defaults:
            print("  Verification:")
            print(f"    Fail fast: {verify_defaults.get('fail_fast', True)}")
            print(f"    Profiles: {', '.join(verify_defaults.get('profiles', ['quick']))}")


def _print_optional_repo_params(args, layers, tags):
    """Print optional repository parameters if set."""
    if args.framework:
        print(f"    Framework: {args.framework}")
    if args.lsp:
        print(f"    LSP: {args.lsp}")
    if layers:
        print(f"    Layers: {', '.join(layers)}")
    if tags:
        print(f"    Tags: {', '.join(tags)}")


def run_workspace_add_repo(args):
    """Add a repository to the workspace."""
    print()
    print("=" * 60)
    print("WORKSPACE ADD-REPO")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import discover_workspace, add_repo_to_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    ctx = discover_workspace(workspace_arg=args.workspace or None)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found. Initialize first:")
        print("  python execute.py workspace init --name my-workspace")
        sys.exit(1)

    layers = args.layers.split(',') if args.layers else None
    tags = args.tags.split(',') if args.tags else None

    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Adding repo: {args.name}")
    print(f"    Path: {args.path}\n    Type: {args.type}\n    Language: {args.language}")
    _print_optional_repo_params(args, layers, tags)

    try:
        add_repo_to_workspace(
            ctx, name=args.name, path=args.path, repo_type=args.type, language=args.language,
            framework=args.framework, lsp=args.lsp, layers=layers, tags=tags,
        )
        print(f"\n✅ Repository added: {args.name}")
        print(f"   Updated: {ctx.workspace_path}")
    except Exception as e:
        print(f"\n❌ Failed to add repository: {e}")
        sys.exit(1)


def run_workspace_remove_repo(args):
    """Remove a repository from the workspace."""
    print()
    print("=" * 60)
    print("WORKSPACE REMOVE-REPO")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import discover_workspace, remove_repo_from_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found.")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Removing repo: {args.name}")

    if args.name not in ctx.repos:
        print(f"\n❌ Repository '{args.name}' not found in workspace.")
        print("Available repos:", ', '.join(ctx.repos.keys()))
        sys.exit(1)

    removed = remove_repo_from_workspace(ctx, args.name)
    if removed:
        print(f"\n✅ Repository removed: {args.name}")
    else:
        print(f"\n❌ Failed to remove repository: {args.name}")


def run_workspace_link(args):
    """Link a repository to a workspace."""
    print()
    print("=" * 60)
    print("WORKSPACE LINK")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import create_repo_link
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    repo_dir = Path(args.repo).resolve() if args.repo else Path.cwd().resolve()
    workspace_path = Path(args.workspace).resolve()

    if not workspace_path.exists():
        print(f"\n❌ Workspace not found: {workspace_path}")
        sys.exit(1)

    print(f"\n  Repository: {repo_dir}")
    print(f"  Linking to: {workspace_path}")

    try:
        repo_name = repo_dir.name.lower().replace('_', '-').replace(' ', '-')
        repo_yaml_path = create_repo_link(repo_dir, workspace_path, repo_name)
        print(f"\n✅ Linked repository to workspace")
        print(f"   Created: {repo_yaml_path}")
    except Exception as e:
        print(f"\n❌ Failed to link repository: {e}")
        sys.exit(1)


def run_workspace_validate(args):
    """Validate workspace configuration."""
    print()
    print("=" * 60)
    print("WORKSPACE VALIDATE")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import discover_workspace, validate_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found.")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Config: {ctx.workspace_path}")
    print()
    print("-" * 60)
    print("VALIDATION")
    print("-" * 60)

    errors, warnings = validate_workspace(ctx)

    if not errors:
        print("\n✅ Workspace configuration is valid!")
    else:
        print("\n❌ Workspace has configuration errors:")
        for error in errors:
            print(f"   • {error}")

    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   • {warning}")

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
    print()
    print("=" * 60)
    print("WORKSPACE LIST-REPOS")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import discover_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    ctx = discover_workspace(workspace_arg=args.workspace or None)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found.")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print()

    repos = _filter_repos(list(ctx.repos.values()), args)
    _output_repos(repos, args.format)
    print(f"\nTotal: {len(repos)} repository(ies)")


def _output_repos(repos, fmt):
    """Output repos in specified format."""
    if fmt == 'json':
        output = [{'name': r.name, 'path': r.path, 'type': r.type, 'language': r.language, 'framework': r.framework, 'tags': r.tags} for r in repos]
        print(json.dumps(output, indent=2))
    elif fmt == 'yaml':
        output = [{'name': r.name, 'path': r.path, 'type': r.type, 'language': r.language, 'framework': r.framework, 'tags': r.tags} for r in repos]
        print(yaml.dump(output, default_flow_style=False))
    else:
        print(f"{'NAME':<20} {'TYPE':<12} {'LANGUAGE':<12} {'PATH'}")
        print("-" * 70)
        for repo in repos:
            print(f"{repo.name:<20} {repo.type:<12} {repo.language:<12} {repo.path}")


def run_workspace_unlink(args):
    """Unlink current repo from workspace (convert to single-repo mode)."""
    print()
    print("=" * 60)
    print("WORKSPACE UNLINK")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import unlink_repo
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    repo_dir = Path.cwd()
    print(f"\n  Repository: {repo_dir}")

    try:
        unlinked = unlink_repo(repo_dir)
        if unlinked:
            print("\n✅ Repository unlinked from workspace")
            print("   Now in single-repo mode (workspace_ref: null)")
        else:
            print("\n⚠️  Repository is already in single-repo mode")
    except Exception as e:
        print(f"\n❌ Failed to unlink: {e}")
        sys.exit(1)
