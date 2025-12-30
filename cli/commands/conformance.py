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
import json
from pathlib import Path
from datetime import date
from typing import Optional


def _get_manager():
    """Get ConformanceManager for current directory."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
    from conformance.manager import ConformanceManager
    return ConformanceManager(Path.cwd())


def _get_contract_runner():
    """Get contract verification runner."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
    from contracts.loader import ContractLoader
    from contracts.engine import ContractVerificationEngine
    return ContractLoader, ContractVerificationEngine


def run_conformance(args):
    """Base conformance command - show help."""
    pass  # Subcommand required, handled by execute.py


def run_conformance_init(args):
    """Initialize conformance tracking."""
    print("\n" + "=" * 60)
    print("CONFORMANCE INIT")
    print("=" * 60)

    manager = _get_manager()

    try:
        manager.initialize(force=getattr(args, 'force', False))
        print(f"\n  Initialized: {manager.agentforge_path}/")
        print("  Created:")
        print("    - violations/")
        print("    - exemptions/")
        print("    - history/")
        print("    - conformance_report.yaml")
        print("\n  Added .agentforge/local.yaml to .gitignore")
        print("\nConformance tracking is ready.")
        print("Run 'agentforge conformance check --full' to analyze your codebase.")
    except FileExistsError as e:
        print(f"\n  Error: {e}")
        sys.exit(1)


def run_conformance_check(args):
    """Run conformance checks."""
    print("\n" + "=" * 60)
    print("CONFORMANCE CHECK")
    print("=" * 60)

    manager = _get_manager()

    if not manager.is_initialized():
        print("\n  Error: Conformance tracking not initialized.")
        print("  Run 'agentforge conformance init' first.")
        sys.exit(1)

    ContractLoader, ContractVerificationEngine = _get_contract_runner()

    is_full = getattr(args, 'full', False)
    print(f"\n  Mode: {'full' if is_full else 'incremental'}")

    loader = ContractLoader(Path.cwd())
    engine = ContractVerificationEngine(loader)

    contracts = loader.get_enabled_contracts()
    if not contracts:
        print("\n  No contracts found. Create a contract first.")
        sys.exit(1)

    print(f"  Contracts: {len(contracts)}")
    print()
    print("-" * 60)

    all_results = []
    contracts_checked = []
    files_checked = set()

    contract_filter = getattr(args, 'contract', None)
    file_filter = getattr(args, 'files', None)
    file_list = [f.strip() for f in file_filter.split(',')] if file_filter else None

    for contract in contracts:
        if contract_filter and contract.id != contract_filter:
            continue

        print(f"\n  Checking: {contract.id}")
        contracts_checked.append(contract.id)

        for check in contract.checks:
            if not check.enabled:
                continue

            result = engine.run_check(check, file_list)
            if result.get('violations'):
                for v in result['violations']:
                    v['contract_id'] = contract.id
                    v['check_id'] = check.id
                    v['severity'] = check.severity
                    all_results.append(v)
                    if v.get('file'):
                        files_checked.add(v['file'])

    print(f"\n  Files analyzed: {len(files_checked)}")
    print(f"  Violations found: {len(all_results)}")

    report = manager.run_conformance_check(
        verification_results=all_results,
        contracts_checked=contracts_checked,
        files_checked=len(files_checked),
        is_full_run=is_full,
    )

    print()
    print("-" * 60)
    _print_report_summary(report)
    print("-" * 60)

    if getattr(args, 'exit_code', False):
        if report.summary.failed > 0:
            print("\nExiting with code 1 (violations found)")
            sys.exit(1)


def run_conformance_report(args):
    """Show current conformance report."""
    print("\n" + "=" * 60)
    print("CONFORMANCE REPORT")
    print("=" * 60)

    manager = _get_manager()

    if not manager.is_initialized():
        print("\n  Error: Conformance tracking not initialized.")
        print("  Run 'agentforge conformance init' first.")
        sys.exit(1)

    report = manager.get_report()
    if not report:
        print("\n  No report found. Run 'agentforge conformance check' first.")
        sys.exit(1)

    fmt = getattr(args, 'format', 'text')

    if fmt == 'json':
        _print_report_json(report)
    elif fmt == 'yaml':
        _print_report_yaml(report)
    else:
        _print_report_text(report)


def _print_report_summary(report):
    """Print brief report summary."""
    s = report.summary
    print(f"\n  Summary:")
    print(f"    Failed:   {s.failed}")
    print(f"    Exempted: {s.exempted}")
    print(f"    Stale:    {s.stale}")

    if report.by_severity:
        print(f"\n  By Severity:")
        for severity, count in report.by_severity.items():
            print(f"    {severity}: {count}")

    if report.trend:
        delta = report.trend.get('failed_delta', 0)
        if delta != 0:
            direction = "↑" if delta > 0 else "↓"
            print(f"\n  Trend: {direction} {abs(delta)} since last run")


def _print_report_text(report):
    """Print full report in text format."""
    print(f"\n  Generated: {report.generated_at.isoformat()}")
    print(f"  Run ID: {report.run_id}")
    print(f"  Run Type: {report.run_type}")
    print()
    print("-" * 60)
    _print_report_summary(report)

    if report.by_contract:
        print(f"\n  By Contract:")
        for contract, count in report.by_contract.items():
            print(f"    {contract}: {count}")

    print(f"\n  Contracts Checked: {len(report.contracts_checked)}")
    for c in report.contracts_checked:
        print(f"    - {c}")

    print(f"\n  Files Checked: {report.files_checked}")


def _print_report_json(report):
    """Print report as JSON."""
    import json
    data = {
        'schema_version': report.schema_version,
        'generated_at': report.generated_at.isoformat(),
        'run_id': report.run_id,
        'run_type': report.run_type,
        'summary': {
            'total': report.summary.total,
            'passed': report.summary.passed,
            'failed': report.summary.failed,
            'exempted': report.summary.exempted,
            'stale': report.summary.stale,
        },
        'by_severity': report.by_severity,
        'by_contract': report.by_contract,
        'contracts_checked': report.contracts_checked,
        'files_checked': report.files_checked,
        'trend': report.trend,
    }
    print(json.dumps(data, indent=2))


def _print_report_yaml(report):
    """Print report as YAML."""
    import yaml
    data = {
        'schema_version': report.schema_version,
        'generated_at': report.generated_at.isoformat(),
        'run_id': report.run_id,
        'run_type': report.run_type,
        'summary': {
            'total': report.summary.total,
            'passed': report.summary.passed,
            'failed': report.summary.failed,
            'exempted': report.summary.exempted,
            'stale': report.summary.stale,
        },
        'by_severity': report.by_severity,
        'by_contract': report.by_contract,
        'contracts_checked': report.contracts_checked,
        'files_checked': report.files_checked,
        'trend': report.trend,
    }
    print(yaml.dump(data, default_flow_style=False, sort_keys=False))


def run_conformance_violations(args):
    """Base violations command - show help."""
    pass  # Subcommand required


def run_conformance_violations_list(args):
    """List violations."""
    manager = _get_manager()

    if not manager.is_initialized():
        print("Error: Conformance tracking not initialized.")
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
        _print_violations_json(violations)
    elif fmt == 'yaml':
        _print_violations_yaml(violations)
    else:
        _print_violations_table(violations)


def _print_violations_table(violations):
    """Print violations as table."""
    if not violations:
        print("\nNo violations found.")
        return

    print(f"\n{'ID':<15} {'Severity':<10} {'Contract':<20} {'File':<30} {'Status':<10}")
    print("-" * 85)

    for v in violations:
        file_display = v.file_path[-28:] if len(v.file_path) > 28 else v.file_path
        print(f"{v.violation_id:<15} {v.severity.value:<10} {v.contract_id:<20} {file_display:<30} {v.status.value:<10}")

    print(f"\nTotal: {len(violations)} violation(s)")


def _print_violations_json(violations):
    """Print violations as JSON."""
    data = []
    for v in violations:
        data.append({
            'violation_id': v.violation_id,
            'contract_id': v.contract_id,
            'check_id': v.check_id,
            'severity': v.severity.value,
            'file_path': v.file_path,
            'line_number': v.line_number,
            'message': v.message,
            'status': v.status.value,
            'detected_at': v.detected_at.isoformat(),
            'exemption_id': v.exemption_id,
        })
    print(json.dumps(data, indent=2))


def _print_violations_yaml(violations):
    """Print violations as YAML."""
    import yaml
    data = []
    for v in violations:
        data.append({
            'violation_id': v.violation_id,
            'contract_id': v.contract_id,
            'check_id': v.check_id,
            'severity': v.severity.value,
            'file_path': v.file_path,
            'line_number': v.line_number,
            'message': v.message,
            'status': v.status.value,
            'detected_at': v.detected_at.isoformat(),
            'exemption_id': v.exemption_id,
        })
    print(yaml.dump(data, default_flow_style=False, sort_keys=False))


def run_conformance_violations_show(args):
    """Show a specific violation."""
    manager = _get_manager()

    if not manager.is_initialized():
        print("Error: Conformance tracking not initialized.")
        sys.exit(1)

    violation_id = args.violation_id
    violation = manager.get_violation(violation_id)

    if not violation:
        print(f"Error: Violation '{violation_id}' not found.")
        sys.exit(1)

    print(f"\nViolation: {violation.violation_id}")
    print("=" * 60)
    print(f"  Contract:  {violation.contract_id}")
    print(f"  Check:     {violation.check_id}")
    print(f"  Severity:  {violation.severity.value}")
    print(f"  Status:    {violation.status.value}")
    print(f"  File:      {violation.file_path}")
    if violation.line_number:
        print(f"  Line:      {violation.line_number}")
    print(f"\n  Message:   {violation.message}")
    if violation.fix_hint:
        print(f"  Fix Hint:  {violation.fix_hint}")
    print(f"\n  Detected:  {violation.detected_at.isoformat()}")
    print(f"  Last Seen: {violation.last_seen_at.isoformat()}")
    if violation.exemption_id:
        print(f"\n  Exemption: {violation.exemption_id}")
    if violation.resolution:
        print(f"\n  Resolution:")
        print(f"    Resolved At: {violation.resolution.get('resolved_at')}")
        print(f"    Resolved By: {violation.resolution.get('resolved_by')}")
        print(f"    Reason: {violation.resolution.get('reason')}")


def run_conformance_violations_resolve(args):
    """Mark a violation as resolved."""
    manager = _get_manager()

    if not manager.is_initialized():
        print("Error: Conformance tracking not initialized.")
        sys.exit(1)

    violation_id = args.violation_id
    reason = args.reason

    violation = manager.resolve_violation(violation_id, reason, resolved_by="user")

    if not violation:
        print(f"Error: Violation '{violation_id}' not found.")
        sys.exit(1)

    print(f"Violation {violation_id} marked as resolved.")
    print(f"  Reason: {reason}")


def run_conformance_violations_prune(args):
    """Remove old resolved/stale violations."""
    manager = _get_manager()

    if not manager.is_initialized():
        print("Error: Conformance tracking not initialized.")
        sys.exit(1)

    days = getattr(args, 'days', 30)
    dry_run = getattr(args, 'dry_run', False)

    count = manager.prune_violations(older_than_days=days, dry_run=dry_run)

    if dry_run:
        print(f"Would prune {count} violation(s) older than {days} days.")
    else:
        print(f"Pruned {count} violation(s) older than {days} days.")


def run_conformance_history(args):
    """Show conformance history."""
    manager = _get_manager()

    if not manager.is_initialized():
        print("Error: Conformance tracking not initialized.")
        sys.exit(1)

    days = getattr(args, 'days', 30)
    snapshots = manager.get_history(days=days)

    if not snapshots:
        print(f"\nNo history found for the last {days} days.")
        return

    fmt = getattr(args, 'format', 'text')

    if fmt == 'json':
        _print_history_json(snapshots)
    elif fmt == 'yaml':
        _print_history_yaml(snapshots)
    else:
        _print_history_text(snapshots)


def _print_history_text(snapshots):
    """Print history as text."""
    print(f"\nConformance History ({len(snapshots)} snapshots)")
    print("=" * 60)
    print(f"{'Date':<12} {'Failed':<8} {'Exempted':<10} {'Stale':<8} {'Files':<8}")
    print("-" * 60)

    for snapshot in snapshots:
        s = snapshot.summary
        print(f"{snapshot.date.isoformat():<12} {s.failed:<8} {s.exempted:<10} {s.stale:<8} {snapshot.files_analyzed:<8}")

    if len(snapshots) >= 2:
        delta = snapshots[-1].delta_from(snapshots[0])
        print()
        print("-" * 60)
        print(f"Change over period:")
        print(f"  Failed:   {delta['failed_delta']:+d}")
        print(f"  Exempted: {delta['exempted_delta']:+d}")


def _print_history_json(snapshots):
    """Print history as JSON."""
    data = []
    for s in snapshots:
        data.append({
            'date': s.date.isoformat(),
            'summary': {
                'total': s.summary.total,
                'passed': s.summary.passed,
                'failed': s.summary.failed,
                'exempted': s.summary.exempted,
                'stale': s.summary.stale,
            },
            'by_severity': s.by_severity,
            'files_analyzed': s.files_analyzed,
        })
    print(json.dumps(data, indent=2))


def _print_history_yaml(snapshots):
    """Print history as YAML."""
    import yaml
    data = []
    for s in snapshots:
        data.append({
            'date': s.date.isoformat(),
            'summary': {
                'total': s.summary.total,
                'passed': s.summary.passed,
                'failed': s.summary.failed,
                'exempted': s.summary.exempted,
                'stale': s.summary.stale,
            },
            'by_severity': s.by_severity,
            'files_analyzed': s.files_analyzed,
        })
    print(yaml.dump(data, default_flow_style=False, sort_keys=False))
