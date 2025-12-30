"""
CLI helper functions.

Contains miscellaneous helper functions used by command handlers:
- Output formatting
- Result building
- Text display utilities
"""

import click
from typing import Any


def build_contracts_output(
    results: list,
    all_passed: bool,
    total_errors: int,
    total_warnings: int,
    total_exempted: int
) -> dict:
    """Build structured output dict for contract results."""
    output = {
        'summary': {
            'passed': all_passed,
            'contracts_checked': len(results),
            'errors': total_errors,
            'warnings': total_warnings,
            'exempted': total_exempted
        },
        'results': []
    }
    for result in results:
        output['results'].append({
            'contract': result.contract_name,
            'type': result.contract_type,
            'passed': result.passed,
            'violations': [
                {
                    'check_id': r.check_id,
                    'check_name': r.check_name,
                    'severity': r.severity,
                    'message': r.message,
                    'file': r.file_path,
                    'line': r.line_number,
                    'exempted': r.exempted,
                    'exemption_id': r.exemption_id
                }
                for r in result.check_results if not r.passed
            ]
        })
    return output


def _get_severity_icon(check_result) -> str:
    """Get icon for check result based on status."""
    if check_result.exempted:
        return '[EX]'
    return {'error': '[ERR]', 'warning': '[WRN]'}.get(check_result.severity, '[INF]')


def _print_failed_check(check_result) -> None:
    """Print a failed check result."""
    icon = _get_severity_icon(check_result)
    click.echo(f"      {icon} {check_result.check_name}: {check_result.message}")
    if check_result.file_path:
        click.echo(f"         at {check_result.file_path}:{check_result.line_number}")
    if check_result.fix_hint:
        click.echo(f"         fix: {check_result.fix_hint}")


def print_contracts_text(
    results: list,
    total_errors: int,
    total_warnings: int,
    total_exempted: int
) -> None:
    """Print contract results in text format."""
    click.echo(f"\n  Ran {len(results)} contracts\n")

    for result in results:
        status = '[OK]' if result.passed else '[FAIL]'
        click.echo(f"  {status} {result.contract_name} ({result.contract_type})")
        for check_result in result.check_results:
            if not check_result.passed:
                _print_failed_check(check_result)

    click.echo(f"\n  Summary:")
    click.echo(f"    Errors: {total_errors}")
    click.echo(f"    Warnings: {total_warnings}")
    click.echo(f"    Exempted: {total_exempted}")


def print_banner(title: str, char: str = "=", width: int = 60) -> None:
    """Print a banner with a title."""
    click.echo()
    click.echo(char * width)
    click.echo(title)
    click.echo(char * width)


def print_section(title: str, char: str = "-", width: int = 60) -> None:
    """Print a section divider with a title."""
    click.echo()
    click.echo(char * width)
    click.echo(title)
    click.echo(char * width)


def format_check_result(result: Any, show_details: bool = True) -> str:
    """Format a check result for display."""
    status = '[OK]' if result.passed else '[FAIL]'
    line = f"{status} {result.check_name}"

    if not result.passed and show_details:
        line += f": {result.message}"
        if result.file_path:
            line += f" ({result.file_path}:{result.line_number})"

    return line
