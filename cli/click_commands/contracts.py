"""
Contract and exemption management Click commands.

Commands: contracts list, show, check, init, validate
          exemptions list, add, audit
"""

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


# =============================================================================
# CONTRACTS GROUP
# =============================================================================

@click.group(help='Contract management commands')
@click.pass_context
def contracts(ctx):
    """Manage and run contracts."""
    pass


@contracts.command('list', help='List all available contracts')
@click.option('--language', '--lang', '-l', help='Filter by language')
@click.option('--type', '-t', 'contract_type', help='Filter by type')
@click.option('--tag', help='Filter by tag')
@click.option('--tier', type=click.Choice(['builtin', 'global', 'workspace', 'repo']),
              help='Filter by tier')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['table', 'json', 'yaml']), default='table',
              help='Output format')
@click.pass_context
def contracts_list(ctx, language, contract_type, tag, tier, output_format):
    """List contracts with filtering."""
    from cli.commands.contracts import run_contracts_list

    args = Args()
    args.language = language
    args.type = contract_type
    args.tag = tag
    args.tier = tier
    args.format = output_format
    run_contracts_list(args)


@contracts.command('show', help='Show contract details')
@click.argument('name')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['yaml', 'json', 'text']), default='yaml',
              help='Output format')
@click.pass_context
def contracts_show(ctx, name, output_format):
    """Display contract information."""
    from cli.commands.contracts import run_contracts_show

    args = Args()
    args.name = name
    args.format = output_format
    run_contracts_show(args)


@contracts.command('check', help='Run contract checks')
@click.option('--contract', '-c', help='Specific contract')
@click.option('--check', '-k', 'check_id', help='Specific check ID')
@click.option('--language', '--lang', '-l', help='Filter by language')
@click.option('--repo-type', '-t', help='Repository type')
@click.option('--files', '-F', help='Comma-separated files')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'yaml', 'json']), default='text',
              help='Output format')
@click.option('--strict', is_flag=True, help='Fail on warnings')
@click.pass_context
def contracts_check(ctx, contract, check_id, language, repo_type, files, output_format, strict):
    """Execute contract checks."""
    from cli.commands.contracts import run_contracts_check

    args = Args()
    args.contract = contract
    args.check = check_id
    args.language = language
    args.repo_type = repo_type
    args.files = files
    args.format = output_format
    args.strict = strict
    run_contracts_check(args)


@contracts.command('init', help='Initialize contract for repo')
@click.option('--extends', '-e', help='Parent contract')
@click.option('--name', '-n', help='Contract name')
@click.option('--type', '-t', 'contract_type',
              type=click.Choice(['architecture', 'patterns', 'naming', 'testing',
                                 'documentation', 'security', 'api', 'custom']),
              default='patterns', help='Contract type')
@click.pass_context
def contracts_init(ctx, extends, name, contract_type):
    """Create new contract file."""
    from cli.commands.contracts import run_contracts_init

    args = Args()
    args.extends = extends
    args.name = name
    args.type = contract_type
    run_contracts_init(args)


@contracts.command('validate', help='Validate contract files')
@click.option('--file', '-f', 'contract_file', type=click.Path(exists=True),
              help='Specific contract file')
@click.pass_context
def contracts_validate(ctx, contract_file):
    """Validate contract structure."""
    from cli.commands.contracts import run_contracts_validate

    args = Args()
    args.file = contract_file
    run_contracts_validate(args)


# =============================================================================
# EXEMPTIONS GROUP
# =============================================================================

@click.group(help='Exemption management commands')
@click.pass_context
def exemptions(ctx):
    """Manage contract exemptions."""
    pass


@exemptions.command('list', help='List all exemptions')
@click.option('--contract', '-c', help='Filter by contract')
@click.option('--status', type=click.Choice(['active', 'expired', 'resolved', 'all']),
              default='active', help='Filter by status')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['table', 'json', 'yaml']), default='table',
              help='Output format')
@click.pass_context
def exemptions_list(ctx, contract, status, output_format):
    """List exemptions."""
    from cli.commands.contracts import run_exemptions_list

    args = Args()
    args.contract = contract
    args.status = status
    args.format = output_format
    run_exemptions_list(args)


@exemptions.command('add', help='Add a new exemption')
@click.option('--contract', '-c', required=True, help='Contract name')
@click.option('--check', '-k', required=True, help='Check ID')
@click.option('--reason', '-r', required=True, help='Reason')
@click.option('--approved-by', '-a', required=True, help='Approver')
@click.option('--files', '-F', help='File patterns')
@click.option('--expires', '-e', help='Expiration date')
@click.option('--ticket', '-t', help='Ticket reference')
@click.pass_context
def exemptions_add(ctx, contract, check, reason, approved_by, files, expires, ticket):
    """Create new exemption."""
    from cli.commands.contracts import run_exemptions_add

    args = Args()
    args.contract = contract
    args.check = check
    args.reason = reason
    args.approved_by = approved_by
    args.files = files
    args.expires = expires
    args.ticket = ticket
    run_exemptions_add(args)


@exemptions.command('audit', help='Audit exemptions')
@click.option('--show-expired', is_flag=True, help='Include expired')
@click.option('--show-unused', is_flag=True, help='Include unused')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'yaml', 'json']), default='text',
              help='Output format')
@click.pass_context
def exemptions_audit(ctx, show_expired, show_unused, output_format):
    """Audit exemptions."""
    from cli.commands.contracts import run_exemptions_audit

    args = Args()
    args.show_expired = show_expired
    args.show_unused = show_unused
    args.format = output_format
    run_exemptions_audit(args)
