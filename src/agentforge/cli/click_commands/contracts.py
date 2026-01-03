# @spec_file: .agentforge/specs/cli-click-commands-v1.yaml
# @spec_id: cli-click-commands-v1
# @component_id: cli-click_commands-contracts
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

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
    from agentforge.cli.commands.contracts import run_contracts_list

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
    from agentforge.cli.commands.contracts import run_contracts_show

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
    from agentforge.cli.commands.contracts import run_contracts_check

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
    from agentforge.cli.commands.contracts import run_contracts_init

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
    from agentforge.cli.commands.contracts import run_contracts_validate

    args = Args()
    args.file = contract_file
    run_contracts_validate(args)


@contracts.command('fix', help='Auto-fix contract violations')
@click.option('--check', '-c', 'check_id', required=True,
              help='Check ID to fix (e.g., no-bare-assert)')
@click.option('--dry-run', '-n', is_flag=True, help='Show what would be fixed without making changes')
@click.option('--verbose', '-v', is_flag=True, help='Show details of each fix')
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.pass_context
def contracts_fix(ctx, check_id, dry_run, verbose, files):
    """Auto-fix violations for a specific check.

    Examples:
        agentforge contracts fix --check no-bare-assert
        agentforge contracts fix --check no-bare-assert --dry-run tests/
        agentforge contracts fix -c no-print-statements src/
    """
    from agentforge.cli.commands.contracts import run_contracts_fix

    args = Args()
    args.check_id = check_id
    args.dry_run = dry_run
    args.verbose = verbose
    args.files = files if files else None
    run_contracts_fix(args)


@contracts.command('verify-ops', help='Verify code against operation contracts')
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--contract', '-c', 'contract_ids', multiple=True,
              help='Specific operation contract(s) to check')
@click.option('--rule', '-r', 'rule_id', help='Specific rule ID to check')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'json', 'yaml']), default='text',
              help='Output format')
@click.option('--strict', is_flag=True, help='Fail on any violation')
@click.option('--verbose', '-v', is_flag=True, help='Show all checked files')
@click.pass_context
def contracts_verify_ops(ctx, path, contract_ids, rule_id, output_format, strict, verbose):
    """Verify code against operation contract rules."""
    from pathlib import Path as PathLib
    from agentforge.core.contracts.operations import OperationContractVerifier

    path, repo_root = PathLib(path), PathLib.cwd()
    _print_verify_header(path, rule_id, contract_ids)

    verifier = OperationContractVerifier(repo_root=repo_root)
    report = (verifier.verify_rule(rule_id, path) if rule_id
              else verifier.verify(path, contract_ids=list(contract_ids) if contract_ids else None))

    click.echo(f"\n  {report.summary()}\n")
    click.echo("-" * 60)
    _output_report(report, output_format, verbose)
    click.echo("-" * 60)
    _print_result(report)
    click.echo("-" * 60)

    if (strict and report.violations) or report.error_count > 0:
        raise SystemExit(1)


def _print_verify_header(path, rule_id, contract_ids):
    """Print verification header."""
    click.echo("\n" + "=" * 60 + "\nOPERATION CONTRACT VERIFICATION\n" + "=" * 60)
    click.echo(f"\n  Path: {path}")
    if rule_id:
        click.echo(f"  Rule: {rule_id}")
    elif contract_ids:
        click.echo(f"  Contracts: {', '.join(contract_ids)}")


def _output_report(report, output_format: str, verbose: bool):
    """Output report in the specified format."""
    if output_format == 'text':
        _print_verification_results(report, verbose)
    elif output_format == 'json':
        import json
        click.echo(json.dumps(_report_to_dict(report), indent=2))
    elif output_format == 'yaml':
        import yaml
        click.echo(yaml.dump(_report_to_dict(report), default_flow_style=False))


def _print_result(report):
    """Print final result message."""
    if not report.violations:
        click.secho("RESULT: PASS", fg='green', bold=True)
    elif report.error_count > 0:
        click.secho(f"RESULT: FAIL ({report.error_count} errors)", fg='red', bold=True)
    else:
        click.secho(f"RESULT: PASS with warnings ({report.warning_count})", fg='yellow')


def _print_verification_results(report, verbose: bool):
    """Print verification results in text format."""
    if not report.violations:
        click.echo("No violations found.\n")
        return

    # Group by file
    by_file = report.violations_by_file()

    for file_path, violations in sorted(by_file.items()):
        click.echo(f"\n{file_path}:")
        for v in sorted(violations, key=lambda x: x.line_number or 0):
            severity_color = {
                'error': 'red',
                'warning': 'yellow',
                'info': 'blue',
            }.get(v.severity, 'white')

            line_info = f":{v.line_number}" if v.line_number else ""
            click.echo(f"  {line_info} ", nl=False)
            click.secho(f"[{v.severity.upper()}]", fg=severity_color, nl=False)
            click.echo(f" {v.message}")

            if verbose and v.fix_hint:
                hint_preview = v.fix_hint.split('\n')[0][:60]
                click.echo(f"         → {hint_preview}")

    click.echo()


def _report_to_dict(report) -> dict:
    """Convert report to dictionary for JSON/YAML output."""
    return {
        'summary': {
            'contracts_checked': report.contracts_checked,
            'rules_checked': report.rules_checked,
            'files_scanned': report.files_scanned,
            'violations': len(report.violations),
            'errors': report.error_count,
            'warnings': report.warning_count,
            'info': report.info_count,
            'passed': report.is_passed,
        },
        'violations': [
            {
                'rule_id': v.rule_id,
                'contract_id': v.contract_id,
                'file': v.file_path,
                'line': v.line_number,
                'message': v.message,
                'severity': v.severity,
            }
            for v in report.violations
        ],
    }


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
    from agentforge.cli.commands.contracts import run_exemptions_list

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
    from agentforge.cli.commands.contracts import run_exemptions_add

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
    from agentforge.cli.commands.contracts import run_exemptions_audit

    args = Args()
    args.show_expired = show_expired
    args.show_unused = show_unused
    args.format = output_format
    run_exemptions_audit(args)
