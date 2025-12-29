#!/usr/bin/env python3
"""
Workspace Management
====================

A workspace is a collection of related repositories that form a logical
product or system. Provides:

- Shared contracts (architectural rules, patterns, naming conventions)
- Cross-repo artifact tracking (shared DTOs, API contracts)
- Unified conformance reporting
- Multi-repo context retrieval

Discovery Priority:
1. --workspace flag (explicit)
2. AGENTFORGE_WORKSPACE environment variable
3. .agentforge/repo.yaml in current or parent directory (workspace_ref)
4. workspace.yaml in current or parent directory
5. agentforge/workspace.yaml in current or parent directory
6. No workspace (single-repo mode)

Usage:
    from tools.workspace import discover_workspace, WorkspaceContext

    ctx = discover_workspace()
    if ctx.is_workspace_mode:
        print(f"Workspace: {ctx.workspace_name}")
        for name, path in ctx.available_repos.items():
            print(f"  - {name}: {path}")
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import yaml


# =============================================================================
# Exceptions
# =============================================================================

class WorkspaceError(Exception):
    """Base exception for workspace errors."""
    pass


class RepoNotFoundError(WorkspaceError):
    """Raised when a referenced repo doesn't exist."""
    pass


class WorkspaceSchemaError(WorkspaceError):
    """Raised when workspace.yaml has invalid schema."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when workspace cannot be found."""
    pass


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RepoConfig:
    """Configuration for a single repository."""
    name: str
    path: str  # Relative path from workspace.yaml
    type: str  # service, library, application, meta
    language: str
    framework: Optional[str] = None
    lsp: Optional[str] = None
    layers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Resolved at runtime
    resolved_path: Optional[Path] = None
    is_available: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'RepoConfig':
        """Create RepoConfig from dictionary."""
        return cls(
            name=data['name'],
            path=data['path'],
            type=data.get('type', 'service'),
            language=data.get('language', 'unknown'),
            framework=data.get('framework'),
            lsp=data.get('lsp'),
            layers=data.get('layers', []),
            tags=data.get('tags', []),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        result = {
            'name': self.name,
            'path': self.path,
            'type': self.type,
            'language': self.language,
        }
        if self.framework:
            result['framework'] = self.framework
        if self.lsp:
            result['lsp'] = self.lsp
        if self.layers:
            result['layers'] = self.layers
        if self.tags:
            result['tags'] = self.tags
        return result


@dataclass
class WorkspaceContext:
    """Resolved workspace context."""

    # Workspace location and config
    workspace_path: Optional[Path] = None
    workspace_config: Optional[dict] = None

    # Current repo context
    current_repo: Optional[str] = None
    current_repo_path: Optional[Path] = None

    # Discovery information
    discovery_method: str = "none"

    # Resolved repos
    repos: Dict[str, RepoConfig] = field(default_factory=dict)
    available_repos: Dict[str, Path] = field(default_factory=dict)
    unavailable_repos: List[str] = field(default_factory=list)

    @property
    def is_workspace_mode(self) -> bool:
        """Check if we're in workspace mode (vs single-repo mode)."""
        return self.discovery_method != "none" and self.workspace_config is not None

    @property
    def workspace_name(self) -> Optional[str]:
        """Get workspace name."""
        if self.workspace_config:
            return self.workspace_config.get('workspace', {}).get('name')
        return None

    @property
    def workspace_description(self) -> Optional[str]:
        """Get workspace description."""
        if self.workspace_config:
            return self.workspace_config.get('workspace', {}).get('description')
        return None

    @property
    def workspace_version(self) -> Optional[str]:
        """Get workspace version."""
        if self.workspace_config:
            return self.workspace_config.get('workspace', {}).get('version')
        return None

    @property
    def workspace_dir(self) -> Optional[Path]:
        """Get workspace directory (parent of workspace.yaml)."""
        if self.workspace_path:
            return self.workspace_path.parent
        return None

    def get_repo(self, name: str) -> Optional[RepoConfig]:
        """Get repo config by name."""
        return self.repos.get(name)

    def get_repo_path(self, name: str) -> Optional[Path]:
        """Get resolved path for a repo."""
        return self.available_repos.get(name)

    def get_repos_by_tag(self, tag: str) -> List[RepoConfig]:
        """Get all repos with a specific tag."""
        return [r for r in self.repos.values() if tag in r.tags]

    def get_repos_by_type(self, repo_type: str) -> List[RepoConfig]:
        """Get all repos of a specific type."""
        return [r for r in self.repos.values() if r.type == repo_type]

    def get_repos_by_language(self, language: str) -> List[RepoConfig]:
        """Get all repos with a specific language."""
        return [r for r in self.repos.values() if r.language == language]


# =============================================================================
# Discovery Functions
# =============================================================================

def find_upward(filename: str, start: Path = None) -> Optional[Path]:
    """
    Search for filename in start directory and all parents.

    Args:
        filename: File or directory name to find
        start: Starting directory (defaults to cwd)

    Returns:
        Path to found file, or None
    """
    current = start or Path.cwd()

    while current != current.parent:
        candidate = current / filename
        if candidate.exists():
            return candidate
        current = current.parent

    # Check root
    candidate = current / filename
    if candidate.exists():
        return candidate

    return None


def resolve_workspace_path(ref_path: str, relative_to: Path) -> Path:
    """
    Resolve a workspace reference path.

    Args:
        ref_path: Path string (absolute or relative)
        relative_to: File that contains the reference

    Returns:
        Resolved absolute Path
    """
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

            # Check for local override first
            local_override = repo_config.get('local_overrides', {}).get('workspace_path')
            if local_override:
                ctx.workspace_path = Path(local_override).resolve()
            else:
                workspace_ref = repo_config.get('workspace_ref')
                if workspace_ref:
                    ctx.workspace_path = resolve_workspace_path(workspace_ref, repo_yaml)

            ctx.current_repo = repo_config.get('repo_name')
            ctx.current_repo_path = repo_yaml.parent.parent  # .agentforge is one level down
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


def _load_workspace(ctx: WorkspaceContext) -> WorkspaceContext:
    """
    Load and validate workspace configuration.

    Args:
        ctx: WorkspaceContext with workspace_path set

    Returns:
        Updated WorkspaceContext with loaded config
    """
    if not ctx.workspace_path:
        return ctx

    if not ctx.workspace_path.exists():
        # Workspace file not found, but don't error - just return empty context
        ctx.discovery_method = "none"
        ctx.workspace_path = None
        return ctx

    # Load config
    try:
        ctx.workspace_config = yaml.safe_load(ctx.workspace_path.read_text())
    except Exception as e:
        raise WorkspaceSchemaError(f"Failed to parse workspace.yaml: {e}")

    # Resolve repo paths and check availability
    workspace_dir = ctx.workspace_path.parent
    for repo_data in ctx.workspace_config.get('repos', []):
        repo = RepoConfig.from_dict(repo_data)
        repo.resolved_path = (workspace_dir / repo.path).resolve()
        repo.is_available = repo.resolved_path.exists()

        ctx.repos[repo.name] = repo

        if repo.is_available:
            ctx.available_repos[repo.name] = repo.resolved_path
        else:
            ctx.unavailable_repos.append(repo.name)

    # Determine current repo if not already set
    if not ctx.current_repo and ctx.current_repo_path:
        for name, path in ctx.available_repos.items():
            try:
                if ctx.current_repo_path.resolve().is_relative_to(path):
                    ctx.current_repo = name
                    ctx.current_repo_path = path
                    break
            except ValueError:
                pass

    return ctx


# =============================================================================
# Workspace Management Functions
# =============================================================================

def init_workspace(
    directory: Path,
    name: str,
    description: str = None,
    force: bool = False
) -> Path:
    """
    Initialize a new workspace in the given directory.

    Args:
        directory: Directory to create workspace in
        name: Workspace name
        description: Optional description
        force: If True, overwrite existing workspace.yaml

    Returns:
        Path to created workspace.yaml
    """
    workspace_dir = directory / 'agentforge'
    workspace_file = workspace_dir / 'workspace.yaml'

    if workspace_file.exists() and not force:
        raise WorkspaceError(f"Workspace already exists: {workspace_file}")

    # Create directory structure (ok if exists)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / 'contracts').mkdir(exist_ok=True)
    (workspace_dir / 'shared').mkdir(exist_ok=True)
    (workspace_dir / 'reports').mkdir(exist_ok=True)

    # Create workspace.yaml
    workspace_config = {
        'schema_version': '1.0',
        'workspace': {
            'name': name,
            'description': description or f'{name} workspace',
            'version': '1.0.0'
        },
        'repos': [],
        'paths': {
            'contracts': './contracts',
            'shared': './shared',
            'reports': './reports'
        },
        'defaults': {
            'context': {
                'budget_tokens': 6000,
                'embedding_provider': None
            },
            'verification': {
                'fail_fast': True,
                'profiles': ['quick']
            }
        }
    }

    workspace_file = workspace_dir / 'workspace.yaml'
    with open(workspace_file, 'w') as f:
        yaml.dump(workspace_config, f, default_flow_style=False, sort_keys=False)

    return workspace_file


def add_repo_to_workspace(
    ctx: WorkspaceContext,
    name: str,
    path: str,
    repo_type: str = 'service',
    language: str = 'csharp',
    framework: str = None,
    lsp: str = None,
    layers: List[str] = None,
    tags: List[str] = None,
    create_repo_yaml: bool = True
) -> RepoConfig:
    """
    Add a repository to the workspace.

    Args:
        ctx: WorkspaceContext
        name: Repo name
        path: Path to repo (absolute or relative to cwd)
        repo_type: service, library, application, or meta
        language: Primary language
        framework: Optional framework
        lsp: Optional LSP server name
        layers: Optional architecture layers
        tags: Optional tags
        create_repo_yaml: Whether to create .agentforge/repo.yaml in target

    Returns:
        Created RepoConfig
    """
    if not ctx.is_workspace_mode:
        raise WorkspaceError("No workspace loaded")

    # Check for duplicate
    if name in ctx.repos:
        raise WorkspaceError(f"Repo '{name}' already exists in workspace")

    # Resolve path
    repo_path = Path(path).resolve()
    workspace_dir = ctx.workspace_path.parent

    # Calculate relative path from workspace.yaml to repo
    try:
        relative_path = os.path.relpath(repo_path, workspace_dir)
    except ValueError:
        # Different drives on Windows
        relative_path = str(repo_path)

    # Build repo entry
    repo = RepoConfig(
        name=name,
        path=relative_path,
        type=repo_type,
        language=language,
        framework=framework,
        lsp=lsp,
        layers=layers or [],
        tags=tags or [],
        resolved_path=repo_path,
        is_available=repo_path.exists()
    )

    # Add to config
    repos_list = ctx.workspace_config.get('repos', [])
    repos_list.append(repo.to_dict())
    ctx.workspace_config['repos'] = repos_list

    # Write updated config
    with open(ctx.workspace_path, 'w') as f:
        yaml.dump(ctx.workspace_config, f, default_flow_style=False, sort_keys=False)

    # Update context
    ctx.repos[name] = repo
    if repo.is_available:
        ctx.available_repos[name] = repo_path
    else:
        ctx.unavailable_repos.append(name)

    # Create repo.yaml in target repo
    if create_repo_yaml and repo_path.exists():
        create_repo_link(repo_path, ctx.workspace_path, name)

    return repo


def remove_repo_from_workspace(ctx: WorkspaceContext, name: str) -> bool:
    """
    Remove a repository from the workspace.

    Args:
        ctx: WorkspaceContext
        name: Repo name to remove

    Returns:
        True if removed, False if not found
    """
    if not ctx.is_workspace_mode:
        raise WorkspaceError("No workspace loaded")

    if name not in ctx.repos:
        return False

    # Remove from config
    repos_list = ctx.workspace_config.get('repos', [])
    repos_list = [r for r in repos_list if r.get('name') != name]
    ctx.workspace_config['repos'] = repos_list

    # Write updated config
    with open(ctx.workspace_path, 'w') as f:
        yaml.dump(ctx.workspace_config, f, default_flow_style=False, sort_keys=False)

    # Update context
    del ctx.repos[name]
    if name in ctx.available_repos:
        del ctx.available_repos[name]
    if name in ctx.unavailable_repos:
        ctx.unavailable_repos.remove(name)

    return True


def create_repo_link(
    repo_path: Path,
    workspace_path: Path,
    repo_name: str
) -> Path:
    """
    Create .agentforge/repo.yaml in a repo to link it to a workspace.

    Args:
        repo_path: Path to the repository
        workspace_path: Path to workspace.yaml
        repo_name: Name of this repo in the workspace

    Returns:
        Path to created repo.yaml
    """
    agentforge_dir = repo_path / '.agentforge'
    agentforge_dir.mkdir(exist_ok=True)

    # Calculate relative path from repo.yaml to workspace.yaml
    workspace_ref = os.path.relpath(workspace_path, agentforge_dir)

    repo_yaml = {
        'schema_version': '1.0',
        'workspace_ref': workspace_ref,
        'repo_name': repo_name
    }

    repo_yaml_path = agentforge_dir / 'repo.yaml'
    with open(repo_yaml_path, 'w') as f:
        yaml.dump(repo_yaml, f, default_flow_style=False, sort_keys=False)

    # Update .gitignore if it exists
    gitignore = repo_path / '.gitignore'
    if gitignore.exists():
        content = gitignore.read_text()
        if '.agentforge/local_overrides.yaml' not in content:
            with open(gitignore, 'a') as f:
                f.write('\n# AgentForge local overrides\n')
                f.write('.agentforge/local_overrides.yaml\n')

    return repo_yaml_path


def validate_workspace(ctx: WorkspaceContext) -> tuple:
    """
    Validate workspace configuration.

    Args:
        ctx: WorkspaceContext

    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []

    if not ctx.is_workspace_mode:
        errors.append("No workspace loaded")
        return errors, warnings

    # Check schema version
    schema_version = ctx.workspace_config.get('schema_version')
    if not schema_version:
        errors.append("Missing 'schema_version'")

    # Check workspace section
    ws = ctx.workspace_config.get('workspace', {})
    if not ws.get('name'):
        errors.append("Missing 'workspace.name'")

    # Check repos
    repos = ctx.workspace_config.get('repos', [])
    if not repos:
        warnings.append("No repos defined")

    seen_names = set()
    for repo in repos:
        name = repo.get('name')
        if not name:
            errors.append("Repo missing 'name'")
            continue

        if name in seen_names:
            errors.append(f"Duplicate repo name: {name}")
        seen_names.add(name)

        if not repo.get('path'):
            errors.append(f"Repo '{name}' missing 'path'")

        if not repo.get('language'):
            errors.append(f"Repo '{name}' missing 'language'")

        # Check if path exists
        if name in ctx.unavailable_repos:
            warnings.append(f"Repo '{name}' path not found")

    # Check that all repo.yaml files match
    for name, path in ctx.available_repos.items():
        repo_yaml = path / '.agentforge' / 'repo.yaml'
        if repo_yaml.exists():
            try:
                repo_config = yaml.safe_load(repo_yaml.read_text())
                if repo_config.get('repo_name') != name:
                    errors.append(
                        f"Repo '{name}': repo.yaml says '{repo_config.get('repo_name')}'"
                    )
            except Exception as e:
                warnings.append(f"Repo '{name}': Failed to parse repo.yaml: {e}")

    return errors, warnings


# =============================================================================
# CLI Support Functions
# =============================================================================

def format_workspace_status(ctx: WorkspaceContext) -> str:
    """
    Format workspace status for CLI output.

    Args:
        ctx: WorkspaceContext

    Returns:
        Formatted string
    """
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
        if repo.is_available:
            status = "✓"
            path = repo.resolved_path
        else:
            status = "✗"
            path = "(not found)"

        current = " (current)" if repo.name == ctx.current_repo else ""
        tags = f" [{', '.join(repo.tags)}]" if repo.tags else ""

        lines.append(f"  {status} {repo.name:20} {repo.language:12} {repo.type:12} {path}{current}{tags}")

    return '\n'.join(lines)


# =============================================================================
# Three-Tier Configuration System
# =============================================================================

@dataclass
class ConfigContext:
    """
    Resolved configuration from all three tiers.

    Tier 1: Global (~/.agentforge/)
    Tier 2: Workspace (workspace.yaml)
    Tier 3: Repository (.agentforge/repo.yaml)
    """

    # Tier 1: Global
    global_path: Optional[Path] = None
    global_config: Optional[Dict] = None
    global_contracts: Dict[str, Any] = field(default_factory=dict)

    # Tier 2: Workspace
    workspace_path: Optional[Path] = None
    workspace_config: Optional[Dict] = None
    workspace_contracts: Dict[str, Any] = field(default_factory=dict)
    available_repos: Dict[str, Path] = field(default_factory=dict)
    unavailable_repos: List[str] = field(default_factory=list)

    # Tier 3: Repo
    repo_path: Optional[Path] = None
    repo_config: Optional[Dict] = None
    repo_contracts: Dict[str, Any] = field(default_factory=dict)
    current_repo_name: Optional[str] = None

    # Local overrides (not checked in)
    local_config: Optional[Dict] = None

    # Merged results
    effective_config: Dict = field(default_factory=dict)
    effective_contracts: Dict[str, Any] = field(default_factory=dict)

    # Discovery metadata
    discovery_log: List[str] = field(default_factory=list)
    mode: str = "unknown"  # single-repo | workspace | no-config

    @property
    def is_workspace_mode(self) -> bool:
        """Check if we're in workspace mode."""
        return self.mode == "workspace"

    @property
    def is_single_repo_mode(self) -> bool:
        """Check if we're in single-repo mode."""
        return self.mode == "single-repo"


def expand_path(path_str: str, relative_to: Path = None) -> Path:
    """Expand a path string, handling ~, env vars, and relative paths."""
    expanded = os.path.expanduser(os.path.expandvars(path_str))
    path = Path(expanded)

    if not path.is_absolute() and relative_to:
        path = (relative_to / path).resolve()

    return path


def load_yaml_file(path: Path) -> Optional[Dict]:
    """Load a YAML file, returning None if it doesn't exist."""
    if path and path.exists():
        try:
            return yaml.safe_load(path.read_text())
        except Exception:
            return None
    return None


def load_contracts_from_dir(contracts_dir: Path) -> Dict[str, Any]:
    """Load all contract files from a directory."""
    contracts = {}
    if contracts_dir and contracts_dir.exists():
        for f in contracts_dir.glob("*.contract.yaml"):
            try:
                contracts[f.stem.replace('.contract', '')] = yaml.safe_load(f.read_text())
            except Exception:
                pass
    return contracts


def discover_config(
    workspace_arg: str = None,
    repo_arg: str = None
) -> ConfigContext:
    """
    Discover configuration from all three tiers.

    Priority for workspace discovery:
    1. --workspace flag (explicit)
    2. AGENTFORGE_WORKSPACE environment variable
    3. .agentforge/local.yaml workspace_ref override
    4. .agentforge/repo.yaml workspace_ref
    5. workspace.yaml in current or parent directory
    6. agentforge/workspace.yaml in current or parent
    7. No workspace (single-repo mode if repo.yaml exists)

    Args:
        workspace_arg: Explicit --workspace argument
        repo_arg: Explicit --repo argument (for workspace mode)

    Returns:
        ConfigContext with all resolved configuration
    """
    ctx = ConfigContext()

    # =========================================
    # TIER 1: Global defaults (always load)
    # =========================================
    ctx.global_path = Path.home() / '.agentforge'
    if ctx.global_path.exists():
        ctx.global_config = load_yaml_file(ctx.global_path / 'config.yaml')
        ctx.global_contracts = load_contracts_from_dir(ctx.global_path / 'contracts')
        ctx.discovery_log.append(f"Global config: {ctx.global_path}")
    else:
        ctx.discovery_log.append("Global config: not found")

    # =========================================
    # TIER 3: Repo config (find from cwd)
    # =========================================
    repo_yaml_path = find_upward('.agentforge/repo.yaml')

    if repo_yaml_path:
        ctx.repo_path = repo_yaml_path.parent.parent  # .agentforge is one level down
        ctx.repo_config = load_yaml_file(repo_yaml_path)
        ctx.repo_contracts = load_contracts_from_dir(repo_yaml_path.parent / 'contracts')
        ctx.current_repo_name = ctx.repo_config.get('repo_name') if ctx.repo_config else None
        ctx.discovery_log.append(f"Repo config: {repo_yaml_path}")

        # Check for local overrides (not checked in)
        local_yaml = repo_yaml_path.parent / 'local.yaml'
        ctx.local_config = load_yaml_file(local_yaml)
        if ctx.local_config:
            ctx.discovery_log.append(f"Local overrides: {local_yaml}")
    else:
        ctx.discovery_log.append("Repo config: not found")

    # =========================================
    # TIER 2: Workspace (multiple discovery paths)
    # =========================================
    workspace_resolved = None

    # Priority 1: Explicit --workspace flag
    if workspace_arg:
        workspace_resolved = expand_path(workspace_arg)
        ctx.discovery_log.append(f"Workspace from --workspace flag: {workspace_resolved}")

    # Priority 2: Environment variable
    elif os.environ.get('AGENTFORGE_WORKSPACE'):
        workspace_resolved = expand_path(os.environ['AGENTFORGE_WORKSPACE'])
        ctx.discovery_log.append(f"Workspace from env var: {workspace_resolved}")

    # Priority 3: Local override
    elif ctx.local_config and ctx.local_config.get('workspace_ref'):
        workspace_resolved = expand_path(
            ctx.local_config['workspace_ref'],
            relative_to=repo_yaml_path.parent if repo_yaml_path else None
        )
        ctx.discovery_log.append(f"Workspace from local.yaml: {workspace_resolved}")

    # Priority 4: repo.yaml workspace_ref
    elif repo_yaml_path and ctx.repo_config:
        workspace_ref = ctx.repo_config.get('workspace_ref')
        if workspace_ref:  # Could be null for single-repo mode
            workspace_resolved = expand_path(
                workspace_ref,
                relative_to=repo_yaml_path.parent
            )
            ctx.discovery_log.append(f"Workspace from repo.yaml: {workspace_resolved}")
        else:
            ctx.discovery_log.append("Workspace ref is null (single-repo mode)")

    # Priority 5: Search upward for workspace.yaml
    if not workspace_resolved:
        ws_yaml = find_upward('workspace.yaml')
        if not ws_yaml:
            ws_yaml = find_upward('agentforge/workspace.yaml')
        if ws_yaml:
            workspace_resolved = ws_yaml
            ctx.discovery_log.append(f"Workspace from upward search: {workspace_resolved}")

    # Load workspace if found
    if workspace_resolved and workspace_resolved.exists():
        ctx.workspace_path = workspace_resolved
        ctx.workspace_config = load_yaml_file(workspace_resolved)
        ctx.workspace_contracts = load_contracts_from_dir(
            workspace_resolved.parent / 'contracts'
        )

        # Resolve repo paths
        workspace_dir = workspace_resolved.parent
        for repo in (ctx.workspace_config or {}).get('repos', []):
            repo_path = expand_path(repo['path'], relative_to=workspace_dir)
            if repo_path.exists():
                ctx.available_repos[repo['name']] = repo_path
            else:
                ctx.unavailable_repos.append(repo['name'])

        ctx.mode = "workspace"
    elif repo_yaml_path:
        ctx.mode = "single-repo"
    else:
        ctx.mode = "no-config"

    # =========================================
    # Merge configuration
    # =========================================
    ctx.effective_config = merge_configs(
        ctx.global_config.get('defaults', {}) if ctx.global_config else {},
        ctx.workspace_config.get('defaults', {}) if ctx.workspace_config else {},
        ctx.repo_config.get('overrides', {}) if ctx.repo_config else {},
        ctx.local_config.get('overrides', {}) if ctx.local_config else {}
    )

    # Get merge strategy
    strategy = 'extend'
    if ctx.global_config:
        strategy = ctx.global_config.get('contracts', {}).get('merge_strategy', 'extend')

    ctx.effective_contracts = merge_contracts(
        ctx.global_contracts,
        ctx.workspace_contracts,
        ctx.repo_contracts,
        strategy=strategy
    )

    return ctx


def merge_configs(*configs: Dict) -> Dict:
    """Merge multiple config dicts, later values override earlier."""
    result = {}
    for config in configs:
        if config:
            deep_merge(result, config)
    return result


def deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge override into base, modifying base in place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def merge_contracts(
    global_contracts: Dict,
    workspace_contracts: Dict,
    repo_contracts: Dict,
    strategy: str = "extend"
) -> Dict:
    """
    Merge contracts according to strategy.

    Args:
        global_contracts: Contracts from ~/.agentforge/contracts/
        workspace_contracts: Contracts from workspace/contracts/
        repo_contracts: Contracts from repo/.agentforge/contracts/
        strategy: override | extend | strict

    Returns:
        Merged contracts dictionary
    """
    if strategy == "override":
        # Most specific wins entirely
        return repo_contracts or workspace_contracts or global_contracts or {}

    elif strategy == "extend":
        # Merge all, more specific wins on conflicts
        result = {}
        for contracts in [global_contracts, workspace_contracts, repo_contracts]:
            for name, contract in (contracts or {}).items():
                if name in result:
                    # Merge checks arrays
                    existing_checks = {c['id']: c for c in result[name].get('checks', [])}
                    for check in contract.get('checks', []):
                        existing_checks[check['id']] = check
                    result[name]['checks'] = list(existing_checks.values())
                    # Merge other top-level keys
                    for key, value in contract.items():
                        if key != 'checks':
                            result[name][key] = value
                else:
                    result[name] = contract
        return result

    else:  # strict
        # Only include if explicitly extends parent
        return merge_contracts(global_contracts, workspace_contracts, repo_contracts, "extend")


# =============================================================================
# Single-Repo Initialization
# =============================================================================

def init_single_repo(
    directory: Path,
    name: str,
    language: str,
    repo_type: str = 'service',
    force: bool = False
) -> Path:
    """
    Initialize a single-repo configuration (no workspace).

    Args:
        directory: Repository directory
        name: Repository name
        language: Primary language
        repo_type: Repository type
        force: If True, overwrite existing config

    Returns:
        Path to created repo.yaml
    """
    agentforge_dir = directory / '.agentforge'
    repo_yaml_path = agentforge_dir / 'repo.yaml'

    if repo_yaml_path.exists() and not force:
        raise WorkspaceError(f"Repo config already exists: {repo_yaml_path}")

    # Create directory structure
    agentforge_dir.mkdir(exist_ok=True)
    (agentforge_dir / 'contracts').mkdir(exist_ok=True)
    (agentforge_dir / 'specs').mkdir(exist_ok=True)

    # Create repo.yaml
    repo_config = {
        'schema_version': '1.0',
        'workspace_ref': None,  # Explicit null for single-repo
        'repo_name': name,
        'language': language,
        'type': repo_type
    }

    with open(repo_yaml_path, 'w') as f:
        yaml.dump(repo_config, f, default_flow_style=False, sort_keys=False)

    # Create .gitignore for local files
    gitignore_path = agentforge_dir / '.gitignore'
    gitignore_content = """# AgentForge local files (not checked in)
local.yaml
*.local.yaml
"""
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content)

    return repo_yaml_path


def init_global_config(force: bool = False) -> Path:
    """
    Initialize global config at ~/.agentforge/.

    Args:
        force: If True, overwrite existing config

    Returns:
        Path to created config.yaml
    """
    global_dir = Path.home() / '.agentforge'
    config_path = global_dir / 'config.yaml'

    if config_path.exists() and not force:
        raise WorkspaceError(f"Global config already exists: {config_path}")

    # Create directory structure
    global_dir.mkdir(exist_ok=True)
    (global_dir / 'contracts').mkdir(exist_ok=True)
    (global_dir / 'workspaces').mkdir(exist_ok=True)

    # Create config.yaml
    config = {
        'schema_version': '1.0',
        'defaults': {
            'context': {
                'budget_tokens': 6000,
                'embedding_provider': 'local'
            },
            'verification': {
                'fail_fast': True,
                'default_profile': 'quick'
            },
            'lsp': {
                'csharp': 'omnisharp',
                'typescript': 'typescript-language-server',
                'python': 'pyright'
            }
        },
        'contracts': {
            'merge_strategy': 'extend'
        },
        'workspaces': {}
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return config_path


def unlink_repo(directory: Path = None) -> bool:
    """
    Convert a workspace-linked repo to single-repo mode.

    Args:
        directory: Repository directory (defaults to cwd)

    Returns:
        True if unlinked successfully
    """
    repo_dir = directory or Path.cwd()
    repo_yaml_path = repo_dir / '.agentforge' / 'repo.yaml'

    if not repo_yaml_path.exists():
        raise WorkspaceError(f"No repo.yaml found: {repo_yaml_path}")

    repo_config = load_yaml_file(repo_yaml_path)
    if not repo_config:
        raise WorkspaceError(f"Could not parse repo.yaml: {repo_yaml_path}")

    if repo_config.get('workspace_ref') is None:
        # Already single-repo mode
        return False

    # Remove workspace reference
    repo_config['workspace_ref'] = None

    # Ensure we have language and type (required for single-repo)
    if 'language' not in repo_config:
        repo_config['language'] = 'unknown'
    if 'type' not in repo_config:
        repo_config['type'] = 'service'

    with open(repo_yaml_path, 'w') as f:
        yaml.dump(repo_config, f, default_flow_style=False, sort_keys=False)

    return True


def format_config_status(ctx: ConfigContext) -> str:
    """
    Format configuration status for CLI output.

    Args:
        ctx: ConfigContext

    Returns:
        Formatted string
    """
    lines = []

    lines.append("=" * 60)
    lines.append("AgentForge Configuration Status")
    lines.append("=" * 60)

    # Discovery log
    lines.append("\nDiscovery:")
    for entry in ctx.discovery_log:
        lines.append(f"  - {entry}")

    lines.append(f"\nMode: {ctx.mode}")

    # Global
    lines.append("\n" + "-" * 40)
    lines.append("TIER 1: Global (~/.agentforge/)")
    if ctx.global_path and ctx.global_path.exists():
        lines.append(f"  Location: {ctx.global_path}")
        lines.append(f"  Contracts: {len(ctx.global_contracts)}")
    else:
        lines.append("  Not configured")
        lines.append("  Run: python execute.py config init-global")

    # Workspace
    lines.append("\n" + "-" * 40)
    lines.append("TIER 2: Workspace")
    if ctx.workspace_path:
        ws = (ctx.workspace_config or {}).get('workspace', {})
        lines.append(f"  Name: {ws.get('name', 'N/A')}")
        lines.append(f"  Location: {ctx.workspace_path}")
        lines.append(f"  Contracts: {len(ctx.workspace_contracts)}")
        lines.append(f"\n  Repositories:")
        for repo in (ctx.workspace_config or {}).get('repos', []):
            name = repo['name']
            if name in ctx.available_repos:
                status = "✓"
                path = ctx.available_repos[name]
            else:
                status = "✗"
                path = "(not found)"
            current = " <- current" if name == ctx.current_repo_name else ""
            lines.append(f"    {status} {name:20} {path}{current}")
    else:
        if ctx.mode == "single-repo":
            lines.append("  N/A (single-repo mode)")
        else:
            lines.append("  Not configured")

    # Repo
    lines.append("\n" + "-" * 40)
    lines.append("TIER 3: Repository")
    if ctx.repo_path:
        lines.append(f"  Name: {ctx.current_repo_name}")
        lines.append(f"  Location: {ctx.repo_path}")
        lines.append(f"  Contracts: {len(ctx.repo_contracts)}")
    else:
        lines.append("  Not in an AgentForge-configured repo")
        lines.append("  Run: python execute.py workspace init --single-repo --name <name> --language <lang>")

    # Effective config summary
    lines.append("\n" + "-" * 40)
    lines.append("Effective Configuration:")
    lines.append(f"  Total contracts: {len(ctx.effective_contracts)}")
    if ctx.effective_contracts:
        for name in list(ctx.effective_contracts.keys())[:5]:
            lines.append(f"    - {name}")
        if len(ctx.effective_contracts) > 5:
            lines.append(f"    ... and {len(ctx.effective_contracts) - 5} more")

    return '\n'.join(lines)


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
