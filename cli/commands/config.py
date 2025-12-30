"""
Configuration management commands.

Handles configuration initialization, display, and modification
across the three-tier config system (global, workspace, repo).
"""

import sys
import yaml
from pathlib import Path


def _ensure_workspace_tools():
    """Add tools directory to path for workspace imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))


def run_config(args):
    """Configuration management commands - subcommand dispatch handled by subparsers."""
    pass


def run_config_init_global(args):
    """Initialize global config at ~/.agentforge/"""
    print()
    print("=" * 60)
    print("CONFIG INIT-GLOBAL")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import init_global_config
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    print(f"\n  Location: ~/.agentforge/")

    try:
        result = init_global_config(force=getattr(args, 'force', False))
        print(f"\n✅ Global config initialized: {result}")
        print("\nCreated:")
        print("  ~/.agentforge/")
        print("  ├── config.yaml")
        print("  ├── contracts/")
        print("  └── workspaces/")
        print("\nEdit config.yaml to set your default preferences.")
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        sys.exit(1)


def run_config_show(args):
    """Show configuration at specified tier or effective."""
    print()
    print("=" * 60)
    print("CONFIG SHOW")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import discover_config, format_config_status
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    ctx = discover_config()
    tier = getattr(args, 'tier', None)

    if tier == 'global':
        _show_global_config(ctx)
    elif tier == 'workspace':
        _show_workspace_config(ctx)
    elif tier == 'repo':
        _show_repo_config(ctx)
    else:
        print(format_config_status(ctx))


def _show_global_config(ctx):
    """Show global configuration."""
    print("\nGlobal Configuration (~/.agentforge/config.yaml):")
    print("-" * 50)
    if ctx.global_config:
        print(yaml.dump(ctx.global_config, default_flow_style=False))
    else:
        print("Not configured. Run: python execute.py config init-global")


def _show_workspace_config(ctx):
    """Show workspace configuration."""
    print("\nWorkspace Configuration:")
    print("-" * 50)
    if ctx.workspace_config:
        defaults = ctx.workspace_config.get('defaults', {})
        if defaults:
            print(yaml.dump(defaults, default_flow_style=False))
        else:
            print("No defaults configured in workspace")
    else:
        print("No workspace found")


def _show_repo_config(ctx):
    """Show repository configuration."""
    print("\nRepository Configuration:")
    print("-" * 50)
    if ctx.repo_config:
        overrides = ctx.repo_config.get('overrides', {})
        if overrides:
            print(yaml.dump(overrides, default_flow_style=False))
        else:
            print("No overrides configured in repo")
    else:
        print("No repo config found")


def run_config_set(args):
    """Set a configuration value."""
    print()
    print("=" * 60)
    print("CONFIG SET")
    print("=" * 60)

    _ensure_workspace_tools()

    try:
        from workspace import find_upward
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    key = args.key
    value = args.value

    config_path, tier = _determine_config_file(args, find_upward)
    if config_path is None:
        return

    if not config_path.exists():
        print(f"\n❌ Config file not found: {config_path}")
        sys.exit(1)

    print(f"\n  Tier: {tier}")
    print(f"  File: {config_path}")
    print(f"  Key: {key}")
    print(f"  Value: {value}")

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    parsed_value = _parse_config_value(value)
    _set_config_value(config, key, parsed_value, tier)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Configuration updated")


def _determine_config_file(args, find_upward):
    """Determine which config file to update based on flags."""
    if getattr(args, 'set_global', False):
        return Path.home() / '.agentforge' / 'config.yaml', 'global'
    elif getattr(args, 'set_workspace', False):
        ws_yaml = find_upward('workspace.yaml') or find_upward('agentforge/workspace.yaml')
        if not ws_yaml:
            print("\n❌ No workspace found")
            sys.exit(1)
        return ws_yaml, 'workspace'
    else:
        return Path.cwd() / '.agentforge' / 'repo.yaml', 'repo'


def _try_parse_float(value: str):
    """Try to parse value as float, return original string if not possible."""
    try:
        return float(value)
    except ValueError:
        return value


def _parse_config_value(value: str):
    """Parse a config value string to appropriate type."""
    if not isinstance(value, str):
        return value
    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    if lowered in ('null', 'none'):
        return None
    if value.isdigit():
        return int(value)
    return _try_parse_float(value)


def _get_tier_section(config: dict, keys: list, tier: str) -> dict:
    """Get the appropriate config section based on tier."""
    section_map = {
        'repo': ('overrides', keys[0] != 'overrides'),
        'workspace': ('defaults', keys[0] != 'defaults'),
        'global': ('defaults', keys[0] != 'defaults'),
    }

    if tier in section_map:
        section_name, should_use_section = section_map[tier]
        if should_use_section:
            if section_name not in config:
                config[section_name] = {}
            return config[section_name]
    return config


def _set_config_value(config: dict, key: str, value, tier: str):
    """Set a value in the config dict using dot notation."""
    keys = key.split('.')
    target = _get_tier_section(config, keys, tier)

    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    target[keys[-1]] = value
