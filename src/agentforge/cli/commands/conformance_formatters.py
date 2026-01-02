"""
Output formatters for conformance commands.

Separated from main conformance module to keep file sizes manageable.
"""

import json

import click


def print_report_summary(report):
    """Print brief report summary."""
    s = report.summary
    click.echo("\n  Summary:")
    click.echo(f"    Failed:   {s.failed}")
    click.echo(f"    Exempted: {s.exempted}")
    click.echo(f"    Stale:    {s.stale}")

    if report.by_severity:
        click.echo("\n  By Severity:")
        for severity, count in report.by_severity.items():
            click.echo(f"    {severity}: {count}")

    if report.trend:
        delta = report.trend.get('failed_delta', 0)
        if delta != 0:
            direction = "↑" if delta > 0 else "↓"
            click.echo(f"\n  Trend: {direction} {abs(delta)} since last run")


def print_report_text(report):
    """Print full report in text format."""
    click.echo(f"\n  Generated: {report.generated_at.isoformat()}")
    click.echo(f"  Run ID: {report.run_id}")
    click.echo(f"  Run Type: {report.run_type}")
    click.echo()
    click.echo("-" * 60)
    print_report_summary(report)

    if report.by_contract:
        click.echo("\n  By Contract:")
        for contract, count in report.by_contract.items():
            click.echo(f"    {contract}: {count}")

    click.echo(f"\n  Contracts Checked: {len(report.contracts_checked)}")
    for c in report.contracts_checked:
        click.echo(f"    - {c}")

    click.echo(f"\n  Files Checked: {report.files_checked}")


def _report_to_dict(report):
    """Convert report to dict for serialization."""
    return {
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


def print_report_json(report):
    """Print report as JSON."""
    click.echo(json.dumps(_report_to_dict(report), indent=2))


def print_report_yaml(report):
    """Print report as YAML."""
    import yaml
    click.echo(yaml.dump(_report_to_dict(report), default_flow_style=False, sort_keys=False))


def print_violations_table(violations):
    """Print violations as table."""
    if not violations:
        click.echo("\nNo violations found.")
        return

    click.echo(f"\n{'ID':<15} {'Severity':<10} {'Contract':<20} {'File':<30} {'Status':<10}")
    click.echo("-" * 85)

    for v in violations:
        file_display = v.file_path[-28:] if len(v.file_path) > 28 else v.file_path
        click.echo(f"{v.violation_id:<15} {v.severity.value:<10} {v.contract_id:<20} {file_display:<30} {v.status.value:<10}")

    click.echo(f"\nTotal: {len(violations)} violation(s)")


def _violations_to_list(violations):
    """Convert violations to list of dicts for serialization."""
    return [{
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
    } for v in violations]


def print_violations_json(violations):
    """Print violations as JSON."""
    click.echo(json.dumps(_violations_to_list(violations), indent=2))


def print_violations_yaml(violations):
    """Print violations as YAML."""
    import yaml
    click.echo(yaml.dump(_violations_to_list(violations), default_flow_style=False, sort_keys=False))


def print_history_text(snapshots):
    """Print history as text."""
    click.echo(f"\nConformance History ({len(snapshots)} snapshots)")
    click.echo("=" * 60)
    click.echo(f"{'Date':<12} {'Failed':<8} {'Exempted':<10} {'Stale':<8} {'Files':<8}")
    click.echo("-" * 60)

    for snapshot in snapshots:
        s = snapshot.summary
        click.echo(f"{snapshot.date.isoformat():<12} {s.failed:<8} {s.exempted:<10} {s.stale:<8} {snapshot.files_analyzed:<8}")

    if len(snapshots) >= 2:
        delta = snapshots[-1].delta_from(snapshots[0])
        click.echo()
        click.echo("-" * 60)
        click.echo("Change over period:")
        click.echo(f"  Failed:   {delta['failed_delta']:+d}")
        click.echo(f"  Exempted: {delta['exempted_delta']:+d}")


def _history_to_list(snapshots):
    """Convert history snapshots to list of dicts for serialization."""
    return [{
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
    } for s in snapshots]


def print_history_json(snapshots):
    """Print history as JSON."""
    click.echo(json.dumps(_history_to_list(snapshots), indent=2))


def print_history_yaml(snapshots):
    """Print history as YAML."""
    import yaml
    click.echo(yaml.dump(_history_to_list(snapshots), default_flow_style=False, sort_keys=False))
