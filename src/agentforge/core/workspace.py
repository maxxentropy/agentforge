#!/usr/bin/env python3
"""
Workspace Management - A workspace is a collection of related repositories.

Provides shared contracts, cross-repo artifact tracking, unified conformance
reporting, and multi-repo context retrieval.

Discovery order: --workspace flag > AGENTFORGE_WORKSPACE env > repo.yaml
workspace_ref > workspace.yaml in current/parent dir > single-repo mode.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .workspace_types import (
    RepoConfig,
    WorkspaceContext,
    WorkspaceError,
    WorkspaceSchemaError,
)


@dataclass
class RepoMetadata:
    """Metadata for a repository in a workspace."""
    repo_type: str = 'service'
    language: str = 'csharp'
    framework: str | None = None
    lsp: str | None = None
    layers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


from .workspace_config import discover_config, find_upward, format_config_status, load_yaml_file

# =============================================================================
# Discovery Functions
# =============================================================================

def resolve_workspace_path(ref_path: str, relative_to: Path) -> Path:
    """Resolve a workspace reference path."""
    if Path(ref_path).is_absolute():
        return Path(ref_path)
    return (relative_to.parent / ref_path).resolve()


def discover_workspace(workspace_arg: str = None) -> WorkspaceContext:
    """
    Discover workspace configuration.

    Args:
        workspace_arg: Explicit --workspace argument (highest priority)

    Returns:
        WorkspaceContext with resolved paths and config
    """
    ctx = WorkspaceContext()
    ctx.current_repo_path = Path.cwd()

    # Priority 1: Explicit --workspace flag
    if workspace_arg:
        ctx.workspace_path = Path(workspace_arg).resolve()
        ctx.discovery_method = "explicit_flag"
        return _load_workspace(ctx)

    # Priority 2: Environment variable
    env_workspace = os.environ.get('AGENTFORGE_WORKSPACE')
    if env_workspace:
        ctx.workspace_path = Path(env_workspace).resolve()
        ctx.discovery_method = "environment_variable"
        return _load_workspace(ctx)

    # Priority 3: repo.yaml with workspace_ref
    repo_yaml = find_upward('.agentforge/repo.yaml')
    if repo_yaml:
        try:
            repo_config = yaml.safe_load(repo_yaml.read_text())

            local_override = repo_config.get('local_overrides', {}).get('workspace_path')
            if local_override:
                ctx.workspace_path = Path(local_override).resolve()
            else:
                workspace_ref = repo_config.get('workspace_ref')
                if workspace_ref:
                    ctx.workspace_path = resolve_workspace_path(workspace_ref, repo_yaml)

            ctx.current_repo = repo_config.get('repo_name')
            ctx.current_repo_path = repo_yaml.parent.parent
            ctx.discovery_method = "repo_yaml"

            if ctx.workspace_path:
                return _load_workspace(ctx)
        except Exception:
            pass

    # Priority 4: workspace.yaml in current or parent
    ws_yaml = find_upward('workspace.yaml')
    if ws_yaml:
        ctx.workspace_path = ws_yaml
        ctx.discovery_method = "direct_workspace_yaml"
        return _load_workspace(ctx)

    # Priority 5: agentforge/workspace.yaml in current or parent
    ws_yaml = find_upward('agentforge/workspace.yaml')
    if ws_yaml:
        ctx.workspace_path = ws_yaml
        ctx.discovery_method = "agentforge_directory"
        return _load_workspace(ctx)

    # Priority 6: No workspace found
    ctx.discovery_method = "none"
    return ctx


def _load_repos_into_context(ctx: WorkspaceContext, workspace_dir: Path) -> None:
    """Load repo configurations into context."""
    for repo_data in ctx.workspace_config.get('repos', []):
        repo = RepoConfig.from_dict(repo_data)
        repo.resolved_path = (workspace_dir / repo.path).resolve()
        repo.is_available = repo.resolved_path.exists()

        ctx.repos[repo.name] = repo
        if repo.is_available:
            ctx.available_repos[repo.name] = repo.resolved_path
        else:
            ctx.unavailable_repos.append(repo.name)


def _detect_current_repo(ctx: WorkspaceContext) -> None:
    """Detect which repo we're currently in."""
    if ctx.current_repo or not ctx.current_repo_path:
        return
    for name, path in ctx.available_repos.items():
        try:
            if ctx.current_repo_path.resolve().is_relative_to(path):
                ctx.current_repo = name
                ctx.current_repo_path = path
                break
        except ValueError:
            pass


def _load_workspace(ctx: WorkspaceContext) -> WorkspaceContext:
    """Load and validate workspace configuration."""
    if not ctx.workspace_path or not ctx.workspace_path.exists():
        if ctx.workspace_path:
            ctx.discovery_method = "none"
            ctx.workspace_path = None
        return ctx

    try:
        ctx.workspace_config = yaml.safe_load(ctx.workspace_path.read_text())
    except Exception as e:
        raise WorkspaceSchemaError(f"Failed to parse workspace.yaml: {e}")

    _load_repos_into_context(ctx, ctx.workspace_path.parent)
    _detect_current_repo(ctx)

    return ctx


# =============================================================================
# Workspace Management Functions
# =============================================================================

def init_workspace(directory: Path, name: str, description: str = None, force: bool = False) -> Path:
    """Initialize a new workspace in the given directory."""
    workspace_dir = directory / 'agentforge'
    workspace_file = workspace_dir / 'workspace.yaml'

    if workspace_file.exists() and not force:
        raise WorkspaceError(f"Workspace already exists: {workspace_file}")

    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / 'contracts').mkdir(exist_ok=True)
    (workspace_dir / 'shared').mkdir(exist_ok=True)
    (workspace_dir / 'reports').mkdir(exist_ok=True)

    workspace_config = {
        'schema_version': '1.0',
        'workspace': {'name': name, 'description': description or f'{name} workspace', 'version': '1.0.0'},
        'repos': [],
        'paths': {'contracts': './contracts', 'shared': './shared', 'reports': './reports'},
        'defaults': {
            'context': {'budget_tokens': 6000, 'embedding_provider': None},
            'verification': {'fail_fast': True, 'profiles': ['quick']}
        }
    }

    workspace_file = workspace_dir / 'workspace.yaml'
    with open(workspace_file, 'w') as f:
        yaml.dump(workspace_config, f, default_flow_style=False, sort_keys=False)

    return workspace_file


def add_repo_to_workspace(
    ctx: WorkspaceContext, name: str, path: str,
    metadata: RepoMetadata | None = None, create_repo_yaml: bool = True
) -> RepoConfig:
    """Add a repository to the workspace."""
    if not ctx.is_workspace_mode:
        raise WorkspaceError("No workspace loaded")
    if name in ctx.repos:
        raise WorkspaceError(f"Repo '{name}' already exists in workspace")

    meta = metadata or RepoMetadata()
    repo_path = Path(path).resolve()
    workspace_dir = ctx.workspace_path.parent

    try:
        relative_path = os.path.relpath(repo_path, workspace_dir)
    except ValueError:
        relative_path = str(repo_path)

    repo = RepoConfig(
        name=name, path=relative_path, type=meta.repo_type, language=meta.language,
        framework=meta.framework, lsp=meta.lsp, layers=meta.layers, tags=meta.tags,
        resolved_path=repo_path, is_available=repo_path.exists()
    )

    repos_list = ctx.workspace_config.get('repos', [])
    repos_list.append(repo.to_dict())
    ctx.workspace_config['repos'] = repos_list

    with open(ctx.workspace_path, 'w') as f:
        yaml.dump(ctx.workspace_config, f, default_flow_style=False, sort_keys=False)

    ctx.repos[name] = repo
    if repo.is_available:
        ctx.available_repos[name] = repo_path
    else:
        ctx.unavailable_repos.append(name)

    if create_repo_yaml and repo_path.exists():
        create_repo_link(repo_path, ctx.workspace_path, name)

    return repo


def remove_repo_from_workspace(ctx: WorkspaceContext, name: str) -> bool:
    """Remove a repository from the workspace."""
    if not ctx.is_workspace_mode:
        raise WorkspaceError("No workspace loaded")
    if name not in ctx.repos:
        return False

    repos_list = [r for r in ctx.workspace_config.get('repos', []) if r.get('name') != name]
    ctx.workspace_config['repos'] = repos_list

    with open(ctx.workspace_path, 'w') as f:
        yaml.dump(ctx.workspace_config, f, default_flow_style=False, sort_keys=False)

    del ctx.repos[name]
    if name in ctx.available_repos:
        del ctx.available_repos[name]
    if name in ctx.unavailable_repos:
        ctx.unavailable_repos.remove(name)

    return True


def create_repo_link(repo_path: Path, workspace_path: Path, repo_name: str) -> Path:
    """Create .agentforge/repo.yaml in a repo to link it to a workspace."""
    agentforge_dir = repo_path / '.agentforge'
    agentforge_dir.mkdir(exist_ok=True)

    workspace_ref = os.path.relpath(workspace_path, agentforge_dir)
    repo_yaml = {'schema_version': '1.0', 'workspace_ref': workspace_ref, 'repo_name': repo_name}

    repo_yaml_path = agentforge_dir / 'repo.yaml'
    with open(repo_yaml_path, 'w') as f:
        yaml.dump(repo_yaml, f, default_flow_style=False, sort_keys=False)

    gitignore = repo_path / '.gitignore'
    if gitignore.exists():
        content = gitignore.read_text()
        if '.agentforge/local_overrides.yaml' not in content:
            with open(gitignore, 'a') as f:
                f.write('\n# AgentForge local overrides\n.agentforge/local_overrides.yaml\n')

    return repo_yaml_path


# =============================================================================
# Validation
# =============================================================================

def _validate_repo_entry(repo: dict, seen_names: set, ctx: WorkspaceContext, errors: list, warnings: list):
    """Validate a single repo entry."""
    name = repo.get('name')
    if not name:
        errors.append("Repo missing 'name'")
        return
    if name in seen_names:
        errors.append(f"Duplicate repo name: {name}")
    seen_names.add(name)
    if not repo.get('path'):
        errors.append(f"Repo '{name}' missing 'path'")
    if not repo.get('language'):
        errors.append(f"Repo '{name}' missing 'language'")
    if name in ctx.unavailable_repos:
        warnings.append(f"Repo '{name}' path not found")


def _validate_repo_yaml_files(ctx: WorkspaceContext, errors: list, warnings: list):
    """Validate that repo.yaml files match workspace config."""
    for name, path in ctx.available_repos.items():
        repo_yaml = path / '.agentforge' / 'repo.yaml'
        if not repo_yaml.exists():
            continue
        try:
            repo_config = yaml.safe_load(repo_yaml.read_text())
            if repo_config.get('repo_name') != name:
                errors.append(f"Repo '{name}': repo.yaml says '{repo_config.get('repo_name')}'")
        except Exception as e:
            warnings.append(f"Repo '{name}': Failed to parse repo.yaml: {e}")


def validate_workspace(ctx: WorkspaceContext) -> tuple:
    """Validate workspace configuration. Returns (errors, warnings)."""
    errors, warnings = [], []

    if not ctx.is_workspace_mode:
        errors.append("No workspace loaded")
        return errors, warnings

    if not ctx.workspace_config.get('schema_version'):
        errors.append("Missing 'schema_version'")
    if not ctx.workspace_config.get('workspace', {}).get('name'):
        errors.append("Missing 'workspace.name'")

    repos = ctx.workspace_config.get('repos', [])
    if not repos:
        warnings.append("No repos defined")

    seen_names = set()
    for repo in repos:
        _validate_repo_entry(repo, seen_names, ctx, errors, warnings)

    _validate_repo_yaml_files(ctx, errors, warnings)
    return errors, warnings


# =============================================================================
# CLI Support
# =============================================================================

def format_workspace_status(ctx: WorkspaceContext) -> str:
    """Format workspace status for CLI output."""
    if not ctx.is_workspace_mode:
        return "No workspace found."

    lines = []
    ws = ctx.workspace_config.get('workspace', {})
    lines.append(f"Workspace: {ws.get('name', 'unknown')}")
    if ws.get('description'):
        lines.append(f"Description: {ws['description']}")
    if ws.get('version'):
        lines.append(f"Version: {ws['version']}")
    lines.append(f"Location: {ctx.workspace_path}")
    lines.append(f"Discovery: {ctx.discovery_method}")

    if ctx.current_repo:
        lines.append(f"\nCurrent repo: {ctx.current_repo}")

    lines.append(f"\nRepositories ({len(ctx.repos)}):")
    for repo in ctx.repos.values():
        status = "✓" if repo.is_available else "✗"
        path = repo.resolved_path if repo.is_available else "(not found)"
        current = " (current)" if repo.name == ctx.current_repo else ""
        tags = f" [{', '.join(repo.tags)}]" if repo.tags else ""
        lines.append(f"  {status} {repo.name:20} {repo.language:12} {repo.type:12} {path}{current}{tags}")

    return '\n'.join(lines)


# =============================================================================
# Single-Repo Initialization
# =============================================================================

def init_single_repo(directory: Path, name: str, language: str,
                     repo_type: str = 'service', force: bool = False) -> Path:
    """Initialize a single-repo configuration (no workspace)."""
    agentforge_dir = directory / '.agentforge'
    repo_yaml_path = agentforge_dir / 'repo.yaml'

    if repo_yaml_path.exists() and not force:
        raise WorkspaceError(f"Repo config already exists: {repo_yaml_path}")

    agentforge_dir.mkdir(exist_ok=True)
    (agentforge_dir / 'contracts').mkdir(exist_ok=True)
    (agentforge_dir / 'specs').mkdir(exist_ok=True)

    repo_config = {
        'schema_version': '1.0', 'workspace_ref': None,
        'repo_name': name, 'language': language, 'type': repo_type
    }

    with open(repo_yaml_path, 'w') as f:
        yaml.dump(repo_config, f, default_flow_style=False, sort_keys=False)

    gitignore_path = agentforge_dir / '.gitignore'
    with open(gitignore_path, 'w') as f:
        f.write("# AgentForge local files (not checked in)\nlocal.yaml\n*.local.yaml\n")

    return repo_yaml_path


def init_global_config(force: bool = False) -> Path:
    """Initialize global config at ~/.agentforge/."""
    global_dir = Path.home() / '.agentforge'
    config_path = global_dir / 'config.yaml'

    if config_path.exists() and not force:
        raise WorkspaceError(f"Global config already exists: {config_path}")

    global_dir.mkdir(exist_ok=True)
    (global_dir / 'contracts').mkdir(exist_ok=True)
    (global_dir / 'workspaces').mkdir(exist_ok=True)

    config = {
        'schema_version': '1.0',
        'defaults': {
            'context': {'budget_tokens': 6000, 'embedding_provider': 'local'},
            'verification': {'fail_fast': True, 'default_profile': 'quick'},
            'lsp': {'csharp': 'omnisharp', 'typescript': 'typescript-language-server', 'python': 'pyright'}
        },
        'contracts': {'merge_strategy': 'extend'},
        'workspaces': {}
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return config_path


def unlink_repo(directory: Path = None) -> bool:
    """Convert a workspace-linked repo to single-repo mode."""
    repo_dir = directory or Path.cwd()
    repo_yaml_path = repo_dir / '.agentforge' / 'repo.yaml'

    if not repo_yaml_path.exists():
        raise WorkspaceError(f"No repo.yaml found: {repo_yaml_path}")

    repo_config = load_yaml_file(repo_yaml_path)
    if not repo_config:
        raise WorkspaceError(f"Could not parse repo.yaml: {repo_yaml_path}")

    if repo_config.get('workspace_ref') is None:
        return False

    repo_config['workspace_ref'] = None
    if 'language' not in repo_config:
        repo_config['language'] = 'unknown'
    if 'type' not in repo_config:
        repo_config['type'] = 'service'

    with open(repo_yaml_path, 'w') as f:
        yaml.dump(repo_config, f, default_flow_style=False, sort_keys=False)

    return True


# =============================================================================
# Main (for testing)
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Workspace discovery test")
    parser.add_argument('--workspace', '-w', help='Explicit workspace path')
    parser.add_argument('--config', '-c', action='store_true', help='Show full config context')
    args = parser.parse_args()

    if args.config:
        ctx = discover_config(workspace_arg=args.workspace)
        print(format_config_status(ctx))
    else:
        ctx = discover_workspace(args.workspace)
        print(format_workspace_status(ctx))
