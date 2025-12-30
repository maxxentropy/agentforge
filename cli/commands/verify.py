"""
Deterministic verification command.

Runs actual verification checks instead of LLM-based validation:
- Does the code compile?
- Do tests pass?
- Do architecture rules hold?

This implements the "Correctness is Upstream" philosophy.
"""

import sys
import click
from pathlib import Path


def _ensure_verify_tools():
    """Add tools directory to path for verification imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))


def run_verify(args):
    """Run deterministic verification checks."""
    click.echo()
    click.echo("=" * 60)
    click.echo("VERIFY - Deterministic Correctness Checks")
    click.echo("=" * 60)

    _ensure_verify_tools()

    try:
        from verification_runner import VerificationRunner
    except ImportError as e:
        click.echo(f"\nError: Could not import verification_runner: {e}")
        click.echo("Ensure tools/verification_runner.py exists.")
        sys.exit(1)

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    config_path = Path(args.config) if args.config else None

    runner = VerificationRunner(config_path=config_path, project_root=project_root)

    context = {'project_root': str(project_root)}
    if args.project:
        context['project_path'] = args.project
    runner.set_context(**context)

    _print_verify_header(project_root, args, runner)

    report = _run_verification(runner, args)

    _print_and_save_results(runner, report, args)

    _exit_with_status(report, args)


def _print_verify_header(project_root, args, runner):
    """Print verification header info."""
    click.echo(f"\n  Project Root: {project_root}")
    if args.project:
        click.echo(f"  Project File: {args.project}")
    click.echo(f"  Config: {runner.config_path}")


def _run_verification(runner, args):
    """Run the appropriate verification based on args."""
    if args.profile:
        return _run_profile(runner, args.profile)
    elif args.checks:
        return _run_specific_checks(runner, args.checks)
    else:
        return _run_default(runner)


def _run_profile(runner, profile_name):
    """Run a verification profile."""
    click.echo(f"  Profile: {profile_name}")
    click.echo()
    click.echo("-" * 60)
    click.echo(f"Running '{profile_name}' profile...")
    click.echo("-" * 60)

    try:
        return runner.run_profile(profile_name)
    except ValueError as e:
        click.echo(f"\nError: {e}")
        available = list(runner.config.get('profiles', {}).keys())
        click.echo(f"Available profiles: {', '.join(available)}")
        sys.exit(1)


def _run_specific_checks(runner, checks_str):
    """Run specific checks."""
    check_ids = [c.strip() for c in checks_str.split(',')]
    click.echo(f"  Checks: {', '.join(check_ids)}")
    click.echo()
    click.echo("-" * 60)
    click.echo(f"Running {len(check_ids)} check(s)...")
    click.echo("-" * 60)
    return runner.run_checks(check_ids=check_ids)


def _run_default(runner):
    """Run default verification."""
    profiles = runner.config.get('profiles', {})
    if 'quick' in profiles:
        click.echo("  Profile: quick (default)")
        click.echo()
        click.echo("-" * 60)
        click.echo("Running 'quick' profile...")
        click.echo("-" * 60)
        return runner.run_profile('quick')
    else:
        click.echo("  Running: all checks")
        click.echo()
        click.echo("-" * 60)
        click.echo("Running all checks...")
        click.echo("-" * 60)
        return runner.run_checks(all_checks=True)


def _print_and_save_results(runner, report, args):
    """Print results and save report."""
    output = runner.generate_report(report, format='text')
    click.echo(output)

    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)

    fmt = args.format if args.format != 'text' else 'yaml'
    report_content = runner.generate_report(report, format=fmt)
    ext = 'json' if fmt == 'json' else 'yaml'
    report_path = output_dir / f'verification_report.{ext}'

    with open(report_path, 'w') as f:
        f.write(report_content)

    click.echo(f"\nReport saved to: {report_path}")
    click.echo()
    click.echo("-" * 60)

    if report.is_valid:
        _print_pass_summary(report)
    else:
        _print_fail_summary(report)


def _print_pass_summary(report):
    """Print summary for passing verification."""
    click.echo("RESULT: PASS")
    click.echo("-" * 60)
    click.echo("\nAll blocking checks passed!")

    if report.required_failures > 0:
        click.echo(f"\nNote: {report.required_failures} required check(s) failed (non-blocking).")
        click.echo("Consider addressing these before proceeding.")

    if report.advisory_warnings > 0:
        click.echo(f"\nAdvisory: {report.advisory_warnings} warning(s) - review recommended.")


def _print_fail_summary(report):
    """Print summary for failing verification."""
    click.echo("RESULT: FAIL")
    click.echo("-" * 60)
    click.echo(f"\n{report.blocking_failures} blocking check(s) failed!")
    click.echo("\nBlocking failures must be fixed before proceeding:")

    for result in report.results:
        if result.is_blocking_failure:
            click.echo(f"\n  {result.check_id}: {result.check_name}")
            click.echo(f"    {result.message}")
            if result.fix_suggestion:
                click.echo(f"    Fix: {result.fix_suggestion}")
            if result.errors:
                _print_error_details(result.errors[:3])

    click.echo()
    click.echo("Fix the issues and re-run:")
    click.echo("  python execute.py verify")


def _print_error_details(errors):
    """Print error details."""
    for err in errors:
        if isinstance(err, dict):
            file_info = err.get('file', '')
            line_info = err.get('line', '')
            msg = err.get('message', err.get('match', ''))
            if file_info:
                click.echo(f"      - {file_info}:{line_info}: {msg[:60]}")
            else:
                click.echo(f"      - {msg[:80]}")


def _exit_with_status(report, args):
    """Exit with appropriate status code."""
    if not report.is_valid:
        sys.exit(1)
    elif args.strict and (report.required_failures > 0 or report.advisory_warnings > 0):
        click.echo("\n--strict mode: Failing due to non-blocking issues.")
        sys.exit(1)
