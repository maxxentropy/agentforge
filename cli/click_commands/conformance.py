"""
Conformance tracking Click commands.

Commands: conformance init, check, report, history
          conformance violations list, show, resolve, prune
"""

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


@click.group(help='Conformance tracking commands')
@click.pass_context
def conformance(ctx):
    """Track and manage code conformance."""
    pass


@conformance.command('init', help='Initialize conformance tracking')
@click.option('--force', is_flag=True, help='Force reinitialize')
@click.pass_context
def conformance_init(ctx, force):
    """Initialize conformance tracking."""
    from cli.commands.conformance import run_conformance_init

    args = Args()
    args.force = force
    run_conformance_init(args)


@conformance.command('check', help='Run conformance checks')
@click.option('--full', is_flag=True, help='Full scan')
@click.option('--contract', '-c', help='Specific contract')
@click.option('--files', '-F', help='Comma-separated files')
@click.option('--exit-code', is_flag=True, help='Exit 1 if violations')
@click.pass_context
def conformance_check(ctx, full, contract, files, exit_code):
    """Run conformance checks."""
    from cli.commands.conformance import run_conformance_check

    args = Args()
    args.full = full
    args.contract = contract
    args.files = files
    args.exit_code = exit_code
    run_conformance_check(args)


@conformance.command('report', help='Show conformance report')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'json', 'yaml']), default='text',
              help='Output format')
@click.pass_context
def conformance_report(ctx, output_format):
    """Generate conformance report."""
    from cli.commands.conformance import run_conformance_report

    args = Args()
    args.format = output_format
    run_conformance_report(args)


@conformance.command('history', help='Show conformance history')
@click.option('--days', '-d', type=click.IntRange(1, 365), default=30,
              help='Number of days')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['text', 'json', 'yaml']), default='text',
              help='Output format')
@click.pass_context
def conformance_history(ctx, days, output_format):
    """Display conformance history."""
    from cli.commands.conformance import run_conformance_history

    args = Args()
    args.days = days
    args.format = output_format
    run_conformance_history(args)


# =============================================================================
# VIOLATIONS SUBGROUP
# =============================================================================

@conformance.group('violations', help='Manage violations')
@click.pass_context
def violations(ctx):
    """Manage conformance violations."""
    pass


@violations.command('list', help='List violations')
@click.option('--status', '-s',
              type=click.Choice(['open', 'resolved', 'stale', 'exemption_expired']),
              help='Filter by status')
@click.option('--severity',
              type=click.Choice(['blocker', 'critical', 'major', 'minor', 'info']),
              help='Filter by severity')
@click.option('--contract', '-c', help='Filter by contract')
@click.option('--file', '-F', help='Filter by file')
@click.option('--limit', '-n', type=click.IntRange(1, 1000), default=50,
              help='Max results')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['table', 'json', 'yaml']), default='table',
              help='Output format')
@click.pass_context
def violations_list(ctx, status, severity, contract, file, limit, output_format):
    """List violations."""
    from cli.commands.conformance import run_conformance_violations_list

    args = Args()
    args.status = status
    args.severity = severity
    args.contract = contract
    args.file = file
    args.limit = limit
    args.format = output_format
    run_conformance_violations_list(args)


@violations.command('show', help='Show violation details')
@click.argument('violation_id')
@click.pass_context
def violations_show(ctx, violation_id):
    """Display violation information."""
    from cli.commands.conformance import run_conformance_violations_show

    args = Args()
    args.violation_id = violation_id
    run_conformance_violations_show(args)


@violations.command('resolve', help='Mark violation as resolved')
@click.argument('violation_id')
@click.option('--reason', '-r', required=True, help='Resolution reason')
@click.pass_context
def violations_resolve(ctx, violation_id, reason):
    """Resolve a violation."""
    from cli.commands.conformance import run_conformance_violations_resolve

    args = Args()
    args.violation_id = violation_id
    args.reason = reason
    run_conformance_violations_resolve(args)


@violations.command('prune', help='Remove old violations')
@click.option('--days', '-d', type=click.IntRange(1, 365), default=30,
              help='Older than N days')
@click.option('--dry-run', is_flag=True, help='Preview only')
@click.pass_context
def violations_prune(ctx, days, dry_run):
    """Clean up old violations."""
    from cli.commands.conformance import run_conformance_violations_prune

    args = Args()
    args.days = days
    args.dry_run = dry_run
    run_conformance_violations_prune(args)
