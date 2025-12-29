"""
CLI argument parser configuration.

Builds the argparse parser with all subcommands and their handlers.
"""

import argparse

EPILOG = """
Execution Modes:
  DEFAULT: Claude Code CLI (uses your subscription, no extra cost)
  --use-api: Anthropic API (pay-per-token, requires ANTHROPIC_API_KEY)

Workflow:
  intake → clarify → analyze → draft → validate
                                          ↓
                                    [if issues]
                                          ↓
                                       revise → validate → [repeat until approved]
                                          ↓
                                       verify  ← Deterministic correctness checks
                                          ↓
                                     APPROVED (code compiles, tests pass)

Examples:
  python execute.py intake --request "Add discount codes to orders"
  python execute.py clarify --answer "One code per order"
  python execute.py analyze
  python execute.py draft
  python execute.py validate
  python execute.py revise --auto
  python execute.py verify --profile ci
"""


def build_parser(handlers: dict):
    """Build the argument parser with all subcommands.

    Args:
        handlers: Dict mapping command names to handler functions

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description='Execute AgentForge contracts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG
    )
    parser.add_argument('--use-api', action='store_true',
                        help='Use Anthropic API instead of Claude Code CLI')

    subparsers = parser.add_subparsers(dest='command', help='Command')

    _add_spec_commands(subparsers, handlers)
    _add_context_command(subparsers, handlers)
    _add_verify_command(subparsers, handlers)
    _add_render_command(subparsers, handlers)
    ws_parser = _add_workspace_commands(subparsers, handlers)
    cfg_parser = _add_config_commands(subparsers, handlers)
    ct_parser = _add_contracts_commands(subparsers, handlers)
    ex_parser = _add_exemptions_commands(subparsers, handlers)

    return parser, ws_parser, cfg_parser, ct_parser, ex_parser


def _add_spec_commands(subparsers, h):
    """Add SPEC workflow commands."""
    # INTAKE
    p = subparsers.add_parser('intake', help='Run INTAKE')
    p.add_argument('--request', '-r', required=True, help='Feature request')
    p.add_argument('--priority', '-p', choices=['critical', 'high', 'medium', 'low'])
    p.set_defaults(func=h['run_intake'])

    # CLARIFY
    p = subparsers.add_parser('clarify', help='Run CLARIFY')
    p.add_argument('--intake-file', default='outputs/intake_record.yaml')
    p.add_argument('--answer', '-a', help='Answer to previous question')
    p.set_defaults(func=h['run_clarify'])

    # ANALYZE
    p = subparsers.add_parser('analyze', help='Run ANALYZE')
    p.add_argument('--intake-file', default='outputs/intake_record.yaml')
    p.add_argument('--clarification-file', default='outputs/clarification_log.yaml')
    p.add_argument('--code-context', help='Code context to include (manual)')
    p.add_argument('--project-path', help='Project path for automatic context retrieval')
    p.set_defaults(func=h['run_analyze'])

    # DRAFT
    p = subparsers.add_parser('draft', help='Run DRAFT')
    p.add_argument('--intake-file', default='outputs/intake_record.yaml')
    p.add_argument('--clarification-file', default='outputs/clarification_log.yaml')
    p.add_argument('--analysis-file', default='outputs/analysis_report.yaml')
    p.set_defaults(func=h['run_draft'])

    # VALIDATE
    p = subparsers.add_parser('validate', help='Run VALIDATE')
    p.add_argument('--spec-file', default='outputs/specification.yaml')
    p.add_argument('--analysis-file', default='outputs/analysis_report.yaml')
    p.set_defaults(func=h['run_validate'])

    # REVISE
    p = subparsers.add_parser('revise', help='Fix issues from validation')
    p.add_argument('--spec-file', default='outputs/specification.yaml')
    p.add_argument('--validation-file', default='outputs/validation_report.yaml')
    p.add_argument('--auto', action='store_true', help='Autonomous mode - agent makes decisions')
    p.add_argument('--continue', '--resume', dest='resume', action='store_true', help='Continue paused session')
    p.add_argument('--apply', action='store_true', help='Apply all decisions to specification')
    p.add_argument('--status', action='store_true', help='Show revision session status')
    p.add_argument('--force', action='store_true', help='Start fresh session (discard existing)')
    p.set_defaults(func=h['run_revise'])


def _add_context_command(subparsers, h):
    """Add context retrieval command."""
    p = subparsers.add_parser('context', help='Test context retrieval')
    p.add_argument('--project', '-p', required=True, help='Project root path')
    p.add_argument('--query', '-q', help='Search query')
    p.add_argument('--budget', '-b', type=int, default=6000, help='Token budget')
    p.add_argument('--check', action='store_true', help='Check available components')
    p.add_argument('--index', action='store_true', help='Build/rebuild vector index')
    p.add_argument('--force', action='store_true', help='Force rebuild index')
    p.add_argument('--provider', choices=['local', 'openai', 'voyage'], help='Embedding provider')
    p.add_argument('--no-lsp', action='store_true', help='Disable LSP')
    p.add_argument('--no-vector', action='store_true', help='Disable vector search')
    p.add_argument('--format', '-f', choices=['text', 'yaml', 'json'], default='text')
    p.set_defaults(func=h['run_context'])


def _add_verify_command(subparsers, h):
    """Add verify command."""
    p = subparsers.add_parser('verify', help='Run deterministic correctness checks')
    p.add_argument('--profile', '-p', choices=['quick', 'ci', 'full', 'architecture', 'precommit'])
    p.add_argument('--checks', '-c', help='Comma-separated list of check IDs')
    p.add_argument('--project', help='Path to project file (e.g., MyApp.csproj)')
    p.add_argument('--project-root', help='Project root directory')
    p.add_argument('--config', help='Path to correctness.yaml config')
    p.add_argument('--format', '-f', choices=['text', 'yaml', 'json'], default='yaml')
    p.add_argument('--strict', action='store_true', help='Fail on advisory warnings too')
    p.set_defaults(func=h['run_verify'])


def _add_render_command(subparsers, h):
    """Add render-spec command."""
    p = subparsers.add_parser('render-spec', help='Render YAML spec to Markdown')
    p.add_argument('--spec-file', default='outputs/specification.yaml')
    p.add_argument('--output', '-o', default='outputs/specification.md')
    p.set_defaults(func=h['run_render_spec'])


def _add_workspace_commands(subparsers, h):
    """Add workspace management commands."""
    ws = subparsers.add_parser('workspace', help='Workspace management')
    ws.add_argument('--workspace', '-w', help='Path to workspace.yaml')
    ws_sub = ws.add_subparsers(dest='workspace_command', help='Workspace subcommand')

    # init
    p = ws_sub.add_parser('init', help='Initialize a new workspace or single-repo config')
    p.add_argument('--name', '-n', required=True, help='Workspace/repo name')
    p.add_argument('--path', '-p', help='Directory for workspace.yaml')
    p.add_argument('--description', '-d', help='Workspace description')
    p.add_argument('--single-repo', action='store_true', help='Initialize for single-repo mode')
    p.add_argument('--language', '--lang', '-l', choices=['csharp', 'typescript', 'python', 'java', 'go', 'rust'])
    p.add_argument('--type', '-t', choices=['service', 'library', 'application', 'meta', 'tool'], default='service')
    p.add_argument('--force', action='store_true', help='Overwrite existing config')
    p.set_defaults(func=h['run_workspace_init'])

    # status
    p = ws_sub.add_parser('status', help='Show workspace status')
    p.add_argument('--repo', '-r', help='Start discovery from this repo directory')
    p.set_defaults(func=h['run_workspace_status'])

    # add-repo
    p = ws_sub.add_parser('add-repo', help='Add a repository to workspace')
    p.add_argument('--name', '-n', required=True, help='Repository name')
    p.add_argument('--path', '-p', required=True, help='Relative path to repository root')
    p.add_argument('--type', '-t', required=True, choices=['service', 'library', 'application', 'meta'])
    p.add_argument('--language', '--lang', '-l', required=True, choices=['csharp', 'typescript', 'python', 'java', 'go', 'rust', 'yaml'])
    p.add_argument('--framework', '-f', help='Framework (e.g., aspnetcore)')
    p.add_argument('--lsp', choices=['omnisharp', 'csharp-ls', 'typescript-language-server', 'pyright'])
    p.add_argument('--layers', help='Comma-separated architecture layers')
    p.add_argument('--tags', help='Comma-separated tags')
    p.set_defaults(func=h['run_workspace_add_repo'])

    # remove-repo
    p = ws_sub.add_parser('remove-repo', help='Remove a repository')
    p.add_argument('--name', '-n', required=True, help='Repository name to remove')
    p.set_defaults(func=h['run_workspace_remove_repo'])

    # link
    p = ws_sub.add_parser('link', help='Link a repo to a workspace')
    p.add_argument('--workspace', '-w', required=True, help='Path to workspace.yaml')
    p.add_argument('--repo', '-r', help='Repository directory')
    p.set_defaults(func=h['run_workspace_link'])

    # validate
    p = ws_sub.add_parser('validate', help='Validate workspace configuration')
    p.set_defaults(func=h['run_workspace_validate'])

    # list-repos
    p = ws_sub.add_parser('list-repos', help='List repositories')
    p.add_argument('--type', '-t', choices=['service', 'library', 'application', 'meta'])
    p.add_argument('--language', '--lang', '-l', help='Filter by language')
    p.add_argument('--tag', help='Filter by tag')
    p.add_argument('--format', '-f', choices=['table', 'json', 'yaml'], default='table')
    p.set_defaults(func=h['run_workspace_list_repos'])

    # unlink
    p = ws_sub.add_parser('unlink', help='Unlink repo from workspace')
    p.set_defaults(func=h['run_workspace_unlink'])

    ws.set_defaults(func=h['run_workspace'])
    return ws


def _add_config_commands(subparsers, h):
    """Add config management commands."""
    cfg = subparsers.add_parser('config', help='Configuration management')
    cfg_sub = cfg.add_subparsers(dest='config_command', help='Config subcommand')

    # init-global
    p = cfg_sub.add_parser('init-global', help='Initialize global config at ~/.agentforge/')
    p.add_argument('--force', action='store_true', help='Overwrite existing config')
    p.set_defaults(func=h['run_config_init_global'])

    # show
    p = cfg_sub.add_parser('show', help='Show configuration')
    p.add_argument('--tier', choices=['global', 'workspace', 'repo', 'effective'])
    p.set_defaults(func=h['run_config_show'])

    # set
    p = cfg_sub.add_parser('set', help='Set a configuration value')
    p.add_argument('key', help='Config key (dot notation)')
    p.add_argument('value', help='Value to set')
    p.add_argument('--global', dest='set_global', action='store_true')
    p.add_argument('--workspace', dest='set_workspace', action='store_true')
    p.add_argument('--repo', dest='set_repo', action='store_true')
    p.set_defaults(func=h['run_config_set'])

    cfg.set_defaults(func=h['run_config'])
    return cfg


def _add_contracts_commands(subparsers, h):
    """Add contracts management commands."""
    ct = subparsers.add_parser('contracts', help='Contract management')
    ct_sub = ct.add_subparsers(dest='contracts_command', help='Contracts subcommand')

    # list
    p = ct_sub.add_parser('list', help='List all contracts')
    p.add_argument('--language', '--lang', '-l', help='Filter by language')
    p.add_argument('--type', '-t', help='Filter by contract type')
    p.add_argument('--tag', help='Filter by tag')
    p.add_argument('--tier', choices=['builtin', 'global', 'workspace', 'repo'])
    p.add_argument('--format', '-f', choices=['table', 'json', 'yaml'], default='table')
    p.set_defaults(func=h['run_contracts_list'])

    # show
    p = ct_sub.add_parser('show', help='Show contract details')
    p.add_argument('name', help='Contract name')
    p.add_argument('--format', '-f', choices=['yaml', 'json', 'text'], default='yaml')
    p.set_defaults(func=h['run_contracts_show'])

    # check
    p = ct_sub.add_parser('check', help='Run contract checks')
    p.add_argument('--contract', '-c', help='Run specific contract')
    p.add_argument('--check', '-k', help='Run specific check ID')
    p.add_argument('--language', '--lang', '-l', help='Filter by language')
    p.add_argument('--repo-type', '-t', help='Repository type')
    p.add_argument('--files', '-F', help='Comma-separated file paths')
    p.add_argument('--format', '-f', choices=['text', 'yaml', 'json'], default='text')
    p.add_argument('--strict', action='store_true', help='Fail on warnings too')
    p.set_defaults(func=h['run_contracts_check'])

    # init
    p = ct_sub.add_parser('init', help='Initialize contract for repo')
    p.add_argument('--extends', '-e', help='Parent contract to extend')
    p.add_argument('--name', '-n', help='Contract name')
    p.add_argument('--type', '-t', choices=['architecture', 'patterns', 'naming', 'testing', 'documentation', 'security', 'api', 'custom'], default='patterns')
    p.set_defaults(func=h['run_contracts_init'])

    # validate
    p = ct_sub.add_parser('validate', help='Validate contract files')
    p.add_argument('--file', '-f', help='Specific contract file')
    p.set_defaults(func=h['run_contracts_validate'])

    ct.set_defaults(func=h['run_contracts'])
    return ct


def _add_exemptions_commands(subparsers, h):
    """Add exemptions management commands."""
    ex = subparsers.add_parser('exemptions', help='Exemption management')
    ex_sub = ex.add_subparsers(dest='exemptions_command', help='Exemptions subcommand')

    # list
    p = ex_sub.add_parser('list', help='List all exemptions')
    p.add_argument('--contract', '-c', help='Filter by contract')
    p.add_argument('--status', choices=['active', 'expired', 'resolved', 'all'], default='active')
    p.add_argument('--format', '-f', choices=['table', 'json', 'yaml'], default='table')
    p.set_defaults(func=h['run_exemptions_list'])

    # add
    p = ex_sub.add_parser('add', help='Add a new exemption')
    p.add_argument('--contract', '-c', required=True, help='Contract name')
    p.add_argument('--check', '-k', required=True, help='Check ID to exempt')
    p.add_argument('--reason', '-r', required=True, help='Reason for exemption')
    p.add_argument('--approved-by', '-a', required=True, help='Who approved')
    p.add_argument('--files', '-F', help='Comma-separated file patterns')
    p.add_argument('--expires', '-e', help='Expiration date (YYYY-MM-DD)')
    p.add_argument('--ticket', '-t', help='Tracking ticket')
    p.set_defaults(func=h['run_exemptions_add'])

    # audit
    p = ex_sub.add_parser('audit', help='Audit exemptions')
    p.add_argument('--show-expired', action='store_true')
    p.add_argument('--show-unused', action='store_true')
    p.add_argument('--format', '-f', choices=['text', 'yaml', 'json'], default='text')
    p.set_defaults(func=h['run_exemptions_audit'])

    ex.set_defaults(func=h['run_exemptions'])
    return ex
