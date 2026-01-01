# @spec_file: .agentforge/specs/cli-commands-v1.yaml
# @spec_id: cli-commands-v1
# @component_id: cli-commands-conformance
# @test_path: tests/unit/tools/conformance/test_domain.py

"""
Conformance tracking CLI commands.

Provides commands for managing per-repository conformance state:
- init: Initialize .agentforge/ directory
- check: Run conformance checks
- report: Show current conformance report
- violations: List, show, resolve, prune violations
- history: Show historical trends
- exemptions: Manage exemptions (redirect to existing exemptions command)
"""

import sys
import click
from pathlib import Path

from agentforge.cli.commands.conformance_formatters import (
    print_report_summary,
    print_report_text,
    print_report_json,
    print_report_yaml,
    print_violations_table,
    print_violations_json,
    print_violations_yaml,
    print_history_text,
    print_history_json,
    print_history_yaml,
)


def _get_manager():
    """Get ConformanceManager for current directory."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
    from conformance.manager import ConformanceManager
    return ConformanceManager(Path.cwd())


def _ensure_tools():
    """Add tools directory to path."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))


def run_conformance(args):
    """Base conformance command - show help."""
    pass  # Subcommand required, handled by execute.py


def run_conformance_init(args):
    """Initialize conformance tracking."""
    click.echo("\n" + "=" * 60)
    click.echo("CONFORMANCE INIT")
    click.echo("=" * 60)

    manager = _get_manager()

    try:
        manager.initialize(force=getattr(args, 'force', False))
        click.echo(f"\n  Initialized: {manager.agentforge_path}/")
        click.echo("  Created:")
        click.echo("    - violations/")
        click.echo("    - exemptions/")
        click.echo("    - history/")
        click.echo("    - conformance_report.yaml")
        click.echo("\n  Added .agentforge/local.yaml to .gitignore")
        click.echo("\nConformance tracking is ready.")
        click.echo("Run 'agentforge conformance check --full' to analyze your codebase.")
    except FileExistsError as e:
        click.echo(f"\n  Error: {e}")
        sys.exit(1)


def _run_contract_checks(registry, repo_root, contract_filter, file_list):
    """Run contract checks and return results."""
    from contracts import run_contract, run_all_contracts

    if contract_filter:
        contract = registry.get_contract(contract_filter)
        if not contract:
            click.echo(f"\n  Error: Contract not found: {contract_filter}")
            sys.exit(1)
        return [run_contract(contract, repo_root, registry, file_list)]
    return run_all_contracts(repo_root, file_paths=file_list)


def _results_to_violations(results):
    """Convert contract results to violation format."""
    violations = []
    contracts_checked = []
    files_checked = set()

    for result in results:
        contract_id = result.contract_name
        contracts_checked.append(contract_id)
        click.echo(f"\n  Checked: {contract_id}")

        for check_result in result.check_results:
            if check_result.passed:
                continue
            violations.append({
                'contract_id': contract_id,
                'check_id': check_result.check_id,
                'file': check_result.file_path or '',
                'line': check_result.line_number,
                'message': check_result.message,
                'severity': check_result.severity,
                'fix_hint': check_result.fix_hint,
            })
            if check_result.file_path:
                files_checked.add(check_result.file_path)

    return violations, contracts_checked, files_checked


def run_conformance_check(args):
    """Run conformance checks."""
    click.echo("\n" + "=" * 60)
    click.echo("CONFORMANCE CHECK")
    click.echo("=" * 60)

    manager = _get_manager()
    if not manager.is_initialized():
        click.echo("\n  Error: Conformance tracking not initialized.")
        click.echo("  Run 'agentforge conformance init' first.")
        sys.exit(1)

    _ensure_tools()
    from contracts import ContractRegistry

    is_full = getattr(args, 'full', False)
    click.echo(f"\n  Mode: {'full' if is_full else 'incremental'}")

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)

    if not registry.discover_contracts():
        click.echo("\n  No contracts found. Create a contract first.")
        sys.exit(1)

    contract_filter = getattr(args, 'contract', None)
    file_filter = getattr(args, 'files', None)
    file_list = [f.strip() for f in file_filter.split(',')] if file_filter else None

    results = _run_contract_checks(registry, repo_root, contract_filter, file_list)
    click.echo(f"  Contracts: {len(results)}")
    click.echo()
    click.echo("-" * 60)

    violations, contracts_checked, files_checked = _results_to_violations(results)
    click.echo(f"\n  Files analyzed: {len(files_checked)}")
    click.echo(f"  Violations found: {len(violations)}")

    report = manager.run_conformance_check(
        verification_results=violations,
        contracts_checked=contracts_checked,
        files_checked=len(files_checked),
        is_full_run=is_full,
    )

    click.echo()
    click.echo("-" * 60)
    print_report_summary(report)
    click.echo("-" * 60)

    if getattr(args, 'exit_code', False) and report.summary.failed > 0:
        click.echo("\nExiting with code 1 (violations found)")
        sys.exit(1)


def run_conformance_report(args):
    """Show current conformance report."""
    click.echo("\n" + "=" * 60)
    click.echo("CONFORMANCE REPORT")
    click.echo("=" * 60)

    manager = _get_manager()

    if not manager.is_initialized():
        click.echo("\n  Error: Conformance tracking not initialized.")
        click.echo("  Run 'agentforge conformance init' first.")
        sys.exit(1)

    report = manager.get_report()
    if not report:
        click.echo("\n  No report found. Run 'agentforge conformance check' first.")
        sys.exit(1)

    fmt = getattr(args, 'format', 'text')

    if fmt == 'json':
        print_report_json(report)
    elif fmt == 'yaml':
        print_report_yaml(report)
    else:
        print_report_text(report)


def run_conformance_violations(args):
    """Base violations command - show help."""
    pass  # Subcommand required


def run_conformance_violations_list(args):
    """List violations."""
    manager = _get_manager()

    if not manager.is_initialized():
        click.echo("Error: Conformance tracking not initialized.")
        sys.exit(1)

    from conformance.domain import ViolationStatus, Severity

    status = None
    if getattr(args, 'status', None):
        try:
            status = ViolationStatus(args.status)
        except ValueError:
            pass

    severity = None
    if getattr(args, 'severity', None):
        try:
            severity = Severity(args.severity)
        except ValueError:
            pass

    violations = manager.list_violations(
        status=status,
        severity=severity,
        contract_id=getattr(args, 'contract', None),
        file_pattern=getattr(args, 'file', None),
        limit=getattr(args, 'limit', 50),
    )

    fmt = getattr(args, 'format', 'table')

    if fmt == 'json':
        print_violations_json(violations)
    elif fmt == 'yaml':
        print_violations_yaml(violations)
    else:
        print_violations_table(violations)


def run_conformance_violations_show(args):
    """Show a specific violation."""
    manager = _get_manager()

    if not manager.is_initialized():
        click.echo("Error: Conformance tracking not initialized.")
        sys.exit(1)

    violation_id = args.violation_id
    violation = manager.get_violation(violation_id)

    if not violation:
        click.echo(f"Error: Violation '{violation_id}' not found.")
        sys.exit(1)

    click.echo(f"\nViolation: {violation.violation_id}")
    click.echo("=" * 60)
    click.echo(f"  Contract:  {violation.contract_id}")
    click.echo(f"  Check:     {violation.check_id}")
    click.echo(f"  Severity:  {violation.severity.value}")
    click.echo(f"  Status:    {violation.status.value}")
    click.echo(f"  File:      {violation.file_path}")
    if violation.line_number:
        click.echo(f"  Line:      {violation.line_number}")
    click.echo(f"\n  Message:   {violation.message}")
    if violation.fix_hint:
        click.echo(f"  Fix Hint:  {violation.fix_hint}")
    click.echo(f"\n  Detected:  {violation.detected_at.isoformat()}")
    click.echo(f"  Last Seen: {violation.last_seen_at.isoformat()}")
    if violation.exemption_id:
        click.echo(f"\n  Exemption: {violation.exemption_id}")
    if violation.resolution:
        click.echo(f"\n  Resolution:")
        click.echo(f"    Resolved At: {violation.resolution.get('resolved_at')}")
        click.echo(f"    Resolved By: {violation.resolution.get('resolved_by')}")
        click.echo(f"    Reason: {violation.resolution.get('reason')}")


def run_conformance_violations_resolve(args):
    """Mark a violation as resolved."""
    manager = _get_manager()

    if not manager.is_initialized():
        click.echo("Error: Conformance tracking not initialized.")
        sys.exit(1)

    violation_id = args.violation_id
    reason = args.reason

    violation = manager.resolve_violation(violation_id, reason, resolved_by="user")

    if not violation:
        click.echo(f"Error: Violation '{violation_id}' not found.")
        sys.exit(1)

    click.echo(f"Violation {violation_id} marked as resolved.")
    click.echo(f"  Reason: {reason}")


def run_conformance_violations_prune(args):
    """Remove old resolved/stale violations."""
    manager = _get_manager()

    if not manager.is_initialized():
        click.echo("Error: Conformance tracking not initialized.")
        sys.exit(1)

    days = getattr(args, 'days', 30)
    dry_run = getattr(args, 'dry_run', False)

    count = manager.prune_violations(older_than_days=days, dry_run=dry_run)

    if dry_run:
        click.echo(f"Would prune {count} violation(s) older than {days} days.")
    else:
        click.echo(f"Pruned {count} violation(s) older than {days} days.")


def run_conformance_history(args):
    """Show conformance history."""
    manager = _get_manager()

    if not manager.is_initialized():
        click.echo("Error: Conformance tracking not initialized.")
        sys.exit(1)

    days = getattr(args, 'days', 30)
    snapshots = manager.get_history(days=days)

    if not snapshots:
        click.echo(f"\nNo history found for the last {days} days.")
        return

    fmt = getattr(args, 'format', 'text')

    if fmt == 'json':
        print_history_json(snapshots)
    elif fmt == 'yaml':
        print_history_yaml(snapshots)
    else:
        print_history_text(snapshots)
