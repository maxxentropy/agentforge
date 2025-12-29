#!/usr/bin/env python3
"""
AgentForge CLI entry point.

This is the main executable for the AgentForge contract system.
All command implementations are in the cli/ package.
"""

import sys

# Import all command handlers from cli package
from cli.commands.spec import (
    run_intake,
    run_clarify,
    run_analyze,
    run_draft,
    run_validate,
)
from cli.commands.revision import run_revise
from cli.commands.context import run_context
from cli.commands.verify import run_verify
from cli.render import run_render_spec
from cli.commands.workspace import (
    run_workspace,
    run_workspace_init,
    run_workspace_status,
    run_workspace_add_repo,
    run_workspace_remove_repo,
    run_workspace_link,
    run_workspace_validate,
    run_workspace_list_repos,
    run_workspace_unlink,
)
from cli.commands.config import (
    run_config,
    run_config_init_global,
    run_config_show,
    run_config_set,
)
from cli.commands.contracts import (
    run_contracts,
    run_contracts_list,
    run_contracts_show,
    run_contracts_check,
    run_contracts_init,
    run_contracts_validate,
    run_exemptions,
    run_exemptions_list,
    run_exemptions_add,
    run_exemptions_audit,
)
from cli.parser import build_parser

# Handler mapping - maps parser defaults to command functions
HANDLERS = {
    'run_intake': run_intake, 'run_clarify': run_clarify, 'run_analyze': run_analyze,
    'run_draft': run_draft, 'run_validate': run_validate, 'run_revise': run_revise,
    'run_context': run_context, 'run_verify': run_verify, 'run_render_spec': run_render_spec,
    'run_workspace': run_workspace, 'run_workspace_init': run_workspace_init,
    'run_workspace_status': run_workspace_status, 'run_workspace_add_repo': run_workspace_add_repo,
    'run_workspace_remove_repo': run_workspace_remove_repo, 'run_workspace_link': run_workspace_link,
    'run_workspace_validate': run_workspace_validate, 'run_workspace_list_repos': run_workspace_list_repos,
    'run_workspace_unlink': run_workspace_unlink, 'run_config': run_config,
    'run_config_init_global': run_config_init_global, 'run_config_show': run_config_show,
    'run_config_set': run_config_set, 'run_contracts': run_contracts,
    'run_contracts_list': run_contracts_list, 'run_contracts_show': run_contracts_show,
    'run_contracts_check': run_contracts_check, 'run_contracts_init': run_contracts_init,
    'run_contracts_validate': run_contracts_validate, 'run_exemptions': run_exemptions,
    'run_exemptions_list': run_exemptions_list, 'run_exemptions_add': run_exemptions_add,
    'run_exemptions_audit': run_exemptions_audit,
}

# Commands that require subcommands
SUBCOMMAND_REQUIRED = {
    'workspace': 'workspace_command',
    'config': 'config_command',
    'contracts': 'contracts_command',
    'exemptions': 'exemptions_command',
}


def _check_subcommand(args, command: str, attr: str, subparser) -> bool:
    """Check if subcommand is required but missing. Returns True if should exit."""
    if args.command != command:
        return False
    if not hasattr(args, attr) or getattr(args, attr) is None:
        subparser.print_help()
        return True
    return False


def main():
    """Main entry point."""
    parser, ws_parser, cfg_parser, ct_parser, ex_parser = build_parser(HANDLERS)
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Check subcommand requirements
    subparsers = {'workspace': ws_parser, 'config': cfg_parser, 'contracts': ct_parser, 'exemptions': ex_parser}
    for cmd, attr in SUBCOMMAND_REQUIRED.items():
        if _check_subcommand(args, cmd, attr, subparsers[cmd]):
            sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
