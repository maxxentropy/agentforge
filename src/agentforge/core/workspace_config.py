#!/usr/bin/env python3
"""
Three-Tier Configuration System
===============================

Manages configuration from three tiers:
- Tier 1: Global (~/.agentforge/)
- Tier 2: Workspace (workspace.yaml)
- Tier 3: Repository (.agentforge/repo.yaml)

Extracted from workspace.py for modularity.
"""

import contextlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# Data Classes
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
    global_path: Path | None = None
    global_config: dict | None = None
    global_contracts: dict[str, Any] = field(default_factory=dict)

    # Tier 2: Workspace
    workspace_path: Path | None = None
    workspace_config: dict | None = None
    workspace_contracts: dict[str, Any] = field(default_factory=dict)
    available_repos: dict[str, Path] = field(default_factory=dict)
    unavailable_repos: list[str] = field(default_factory=list)

    # Tier 3: Repo
    repo_path: Path | None = None
    repo_config: dict | None = None
    repo_contracts: dict[str, Any] = field(default_factory=dict)
    current_repo_name: str | None = None

    # Local overrides (not checked in)
    local_config: dict | None = None

    # Merged results
    effective_config: dict = field(default_factory=dict)
    effective_contracts: dict[str, Any] = field(default_factory=dict)

    # Discovery metadata
    discovery_log: list[str] = field(default_factory=list)
    mode: str = "unknown"  # single-repo | workspace | no-config

    @property
    def is_workspace_mode(self) -> bool:
        """Check if we're in workspace mode."""
        return self.mode == "workspace"

    @property
    def is_single_repo_mode(self) -> bool:
        """Check if we're in single-repo mode."""
        return self.mode == "single-repo"


# =============================================================================
# Helper Functions
# =============================================================================

def find_upward(filename: str, start: Path = None) -> Path | None:
    """Search for filename in start directory and all parents."""
    current = start or Path.cwd()
    while current != current.parent:
        candidate = current / filename
        if candidate.exists():
            return candidate
        current = current.parent
    candidate = current / filename
    return candidate if candidate.exists() else None


def expand_path(path_str: str, relative_to: Path = None) -> Path:
    """Expand a path string, handling ~, env vars, and relative paths."""
    expanded = os.path.expanduser(os.path.expandvars(path_str))
    path = Path(expanded)
    if not path.is_absolute() and relative_to:
        path = (relative_to / path).resolve()
    return path


def load_yaml_file(path: Path) -> dict | None:
    """Load a YAML file, returning None if it doesn't exist."""
    if path and path.exists():
        try:
            return yaml.safe_load(path.read_text())
        except Exception:
            return None
    return None


def load_contracts_from_dir(contracts_dir: Path) -> dict[str, Any]:
    """Load all contract files from a directory."""
    contracts = {}
    if contracts_dir and contracts_dir.exists():
        for f in contracts_dir.glob("*.contract.yaml"):
            with contextlib.suppress(Exception):
                contracts[f.stem.replace('.contract', '')] = yaml.safe_load(f.read_text())
    return contracts


# =============================================================================
# Config Merge Functions
# =============================================================================

def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base, modifying base in place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def merge_configs(*configs: dict) -> dict:
    """Merge multiple config dicts, later values override earlier."""
    result = {}
    for config in configs:
        if config:
            deep_merge(result, config)
    return result


def _merge_contract_into(result: dict, name: str, contract: dict):
    """Merge a single contract into result, combining checks arrays."""
    if name not in result:
        result[name] = contract
        return
    existing_checks = {c['id']: c for c in result[name].get('checks', [])}
    for check in contract.get('checks', []):
        existing_checks[check['id']] = check
    result[name]['checks'] = list(existing_checks.values())
    for key, value in contract.items():
        if key != 'checks':
            result[name][key] = value


def merge_contracts(global_contracts: dict, workspace_contracts: dict,
                   repo_contracts: dict, strategy: str = "extend") -> dict:
    """Merge contracts according to strategy (override | extend | strict)."""
    if strategy == "override":
        return repo_contracts or workspace_contracts or global_contracts or {}

    result = {}
    for contracts in [global_contracts, workspace_contracts, repo_contracts]:
        for name, contract in (contracts or {}).items():
            _merge_contract_into(result, name, contract)
    return result


# =============================================================================
# Discovery Helpers
# =============================================================================

def _load_global_config(ctx: ConfigContext) -> None:
    """Load global config from ~/.agentforge (Tier 1)."""
    ctx.global_path = Path.home() / '.agentforge'
    if ctx.global_path.exists():
        ctx.global_config = load_yaml_file(ctx.global_path / 'config.yaml')
        ctx.global_contracts = load_contracts_from_dir(ctx.global_path / 'contracts')
        ctx.discovery_log.append(f"Global config: {ctx.global_path}")
    else:
        ctx.discovery_log.append("Global config: not found")


def _load_repo_config(ctx: ConfigContext) -> Path | None:
    """Load repo config from .agentforge/repo.yaml (Tier 3). Returns repo_yaml_path."""
    repo_yaml_path = find_upward('.agentforge/repo.yaml')
    if not repo_yaml_path:
        ctx.discovery_log.append("Repo config: not found")
        return None

    ctx.repo_path = repo_yaml_path.parent.parent
    ctx.repo_config = load_yaml_file(repo_yaml_path)
    ctx.repo_contracts = load_contracts_from_dir(repo_yaml_path.parent / 'contracts')
    ctx.current_repo_name = ctx.repo_config.get('repo_name') if ctx.repo_config else None
    ctx.discovery_log.append(f"Repo config: {repo_yaml_path}")

    local_yaml = repo_yaml_path.parent / 'local.yaml'
    ctx.local_config = load_yaml_file(local_yaml)
    if ctx.local_config:
        ctx.discovery_log.append(f"Local overrides: {local_yaml}")

    return repo_yaml_path


def _try_workspace_from_config(ctx: ConfigContext, repo_yaml_path: Path | None) -> Path | None:
    """Try to get workspace from local or repo config."""
    if ctx.local_config and ctx.local_config.get('workspace_ref'):
        ws = expand_path(ctx.local_config['workspace_ref'],
                        relative_to=repo_yaml_path.parent if repo_yaml_path else None)
        ctx.discovery_log.append(f"Workspace from local.yaml: {ws}")
        return ws

    if repo_yaml_path and ctx.repo_config:
        workspace_ref = ctx.repo_config.get('workspace_ref')
        if workspace_ref:
            ws = expand_path(workspace_ref, relative_to=repo_yaml_path.parent)
            ctx.discovery_log.append(f"Workspace from repo.yaml: {ws}")
            return ws
        ctx.discovery_log.append("Workspace ref is null (single-repo mode)")
    return None


def _resolve_workspace_path(ctx: ConfigContext, workspace_arg: str, repo_yaml_path: Path | None) -> Path | None:
    """Resolve workspace path from multiple sources (Tier 2)."""
    if workspace_arg:
        ctx.discovery_log.append(f"Workspace from --workspace flag: {workspace_arg}")
        return expand_path(workspace_arg)

    env_ws = os.environ.get('AGENTFORGE_WORKSPACE')
    if env_ws:
        ctx.discovery_log.append(f"Workspace from env var: {env_ws}")
        return expand_path(env_ws)

    ws = _try_workspace_from_config(ctx, repo_yaml_path)
    if ws:
        return ws

    ws_yaml = find_upward('workspace.yaml') or find_upward('agentforge/workspace.yaml')
    if ws_yaml:
        ctx.discovery_log.append(f"Workspace from upward search: {ws_yaml}")
        return ws_yaml

    return None


def _load_workspace_config(ctx: ConfigContext, workspace_resolved: Path | None, repo_yaml_path: Path | None) -> None:
    """Load workspace config and set mode."""
    if workspace_resolved and workspace_resolved.exists():
        ctx.workspace_path = workspace_resolved
        ctx.workspace_config = load_yaml_file(workspace_resolved)
        ctx.workspace_contracts = load_contracts_from_dir(workspace_resolved.parent / 'contracts')

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


def _merge_effective_config(ctx: ConfigContext) -> None:
    """Merge all config tiers into effective config."""
    ctx.effective_config = merge_configs(
        ctx.global_config.get('defaults', {}) if ctx.global_config else {},
        ctx.workspace_config.get('defaults', {}) if ctx.workspace_config else {},
        ctx.repo_config.get('overrides', {}) if ctx.repo_config else {},
        ctx.local_config.get('overrides', {}) if ctx.local_config else {}
    )

    strategy = 'extend'
    if ctx.global_config:
        strategy = ctx.global_config.get('contracts', {}).get('merge_strategy', 'extend')

    ctx.effective_contracts = merge_contracts(
        ctx.global_contracts, ctx.workspace_contracts, ctx.repo_contracts, strategy=strategy
    )


# =============================================================================
# Main Discovery Function
# =============================================================================

def discover_config(workspace_arg: str = None, repo_arg: str = None) -> ConfigContext:
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
    """
    ctx = ConfigContext()

    _load_global_config(ctx)
    repo_yaml_path = _load_repo_config(ctx)
    workspace_resolved = _resolve_workspace_path(ctx, workspace_arg, repo_yaml_path)
    _load_workspace_config(ctx, workspace_resolved, repo_yaml_path)
    _merge_effective_config(ctx)

    return ctx


# =============================================================================
# Formatting
# =============================================================================

def _format_global_section(ctx: ConfigContext, lines: list):
    """Format global tier section."""
    lines.append("\n" + "-" * 40)
    lines.append("TIER 1: Global (~/.agentforge/)")
    if ctx.global_path and ctx.global_path.exists():
        lines.extend([f"  Location: {ctx.global_path}", f"  Contracts: {len(ctx.global_contracts)}"])
    else:
        lines.extend(["  Not configured", "  Run: python execute.py config init-global"])


def _format_workspace_section(ctx: ConfigContext, lines: list):
    """Format workspace tier section."""
    lines.append("\n" + "-" * 40)
    lines.append("TIER 2: Workspace")
    if not ctx.workspace_path:
        lines.append("  N/A (single-repo mode)" if ctx.mode == "single-repo" else "  Not configured")
        return

    ws = (ctx.workspace_config or {}).get('workspace', {})
    lines.extend([f"  Name: {ws.get('name', 'N/A')}", f"  Location: {ctx.workspace_path}",
                  f"  Contracts: {len(ctx.workspace_contracts)}", "\n  Repositories:"])

    for repo in (ctx.workspace_config or {}).get('repos', []):
        name = repo['name']
        status, path = ("✓", ctx.available_repos[name]) if name in ctx.available_repos else ("✗", "(not found)")
        current = " <- current" if name == ctx.current_repo_name else ""
        lines.append(f"    {status} {name:20} {path}{current}")


def _format_repo_section(ctx: ConfigContext, lines: list):
    """Format repository tier section."""
    lines.append("\n" + "-" * 40)
    lines.append("TIER 3: Repository")
    if ctx.repo_path:
        lines.extend([f"  Name: {ctx.current_repo_name}", f"  Location: {ctx.repo_path}",
                      f"  Contracts: {len(ctx.repo_contracts)}"])
    else:
        lines.extend(["  Not in an AgentForge-configured repo",
                      "  Run: python execute.py workspace init --single-repo --name <name> --language <lang>"])


def format_config_status(ctx: ConfigContext) -> str:
    """Format configuration status for CLI output."""
    lines = ["=" * 60, "AgentForge Configuration Status", "=" * 60, "\nDiscovery:"]
    lines.extend(f"  - {entry}" for entry in ctx.discovery_log)
    lines.append(f"\nMode: {ctx.mode}")

    _format_global_section(ctx, lines)
    _format_workspace_section(ctx, lines)
    _format_repo_section(ctx, lines)

    lines.extend(["\n" + "-" * 40, "Effective Configuration:", f"  Total contracts: {len(ctx.effective_contracts)}"])
    if ctx.effective_contracts:
        lines.extend(f"    - {name}" for name in list(ctx.effective_contracts.keys())[:5])
        if len(ctx.effective_contracts) > 5:
            lines.append(f"    ... and {len(ctx.effective_contracts) - 5} more")

    return '\n'.join(lines)
