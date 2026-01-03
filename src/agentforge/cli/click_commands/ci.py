# @spec_file: .agentforge/specs/cli-click-commands-v1.yaml
# @spec_id: cli-click-commands-v1
# @component_id: cli-click_commands-ci
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
CI/CD Integration Click commands.

Commands: ci run, ci baseline save/compare/stats, ci init
"""

import sys

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


@click.group(help='CI/CD integration commands')
@click.pass_context
def ci(ctx):
    """CI/CD conformance checking commands."""
    pass


@ci.command('run', help='Run conformance checks in CI mode')
@click.option('--mode', '-m', type=click.Choice(['full', 'incremental', 'pr']),
              default='full', help='Check mode')
@click.option('--base-ref', '-b', help='Base git ref for PR/incremental mode')
@click.option('--head-ref', '-h', 'head_ref', help='Head git ref (default: HEAD)')
@click.option('--parallel/--no-parallel', default=True, help='Enable parallel execution')
@click.option('--workers', '-w', type=click.IntRange(1, 16), default=4,
              help='Number of parallel workers')
@click.option('--output-sarif/--no-output-sarif', default=True, help='Generate SARIF output')
@click.option('--output-junit/--no-output-junit', default=False, help='Generate JUnit output')
@click.option('--output-markdown/--no-output-markdown', default=True, help='Generate Markdown output')
@click.option('--sarif-path', default='.agentforge/results.sarif', help='SARIF output path')
@click.option('--junit-path', default='.agentforge/results.xml', help='JUnit output path')
@click.option('--markdown-path', default='.agentforge/results.md', help='Markdown output path')
@click.option('--fail-on-warnings', is_flag=True, default=False,
              help='Fail on new warnings (not just errors)')
@click.option('--ratchet', is_flag=True, default=False,
              help='Ratchet mode: only fail if violations increase from baseline')
@click.option('--json', 'output_json', is_flag=True, help='Output result as JSON')
@click.pass_context
def ci_run(ctx, mode, base_ref, head_ref, parallel, workers, output_sarif, output_junit,
           output_markdown, sarif_path, junit_path, markdown_path, fail_on_warnings, ratchet, output_json):
    """Run conformance checks in CI mode."""
    from agentforge.cli.commands.ci import run_ci_check

    args = Args()
    args.mode = mode
    args.base_ref = base_ref
    args.head_ref = head_ref
    args.parallel = parallel
    args.workers = workers
    args.output_sarif = output_sarif
    args.output_junit = output_junit
    args.output_markdown = output_markdown
    args.sarif_path = sarif_path
    args.junit_path = junit_path
    args.markdown_path = markdown_path
    args.fail_on_warnings = fail_on_warnings
    args.ratchet = ratchet
    args.json = output_json

    exit_code = run_ci_check(args)
    sys.exit(exit_code)


@ci.group('baseline', help='Baseline management commands')
@click.pass_context
def ci_baseline(ctx):
    """Manage violation baselines."""
    pass


@ci_baseline.command('save', help='Save current violations as baseline')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing baseline')
@click.pass_context
def baseline_save(ctx, force):
    """Save current violations as baseline."""
    from agentforge.cli.commands.ci import run_baseline_save

    args = Args()
    args.force = force
    run_baseline_save(args)


@ci_baseline.command('compare', help='Compare current violations against baseline')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def baseline_compare(ctx, output_json):
    """Compare violations against baseline."""
    from agentforge.cli.commands.ci import run_baseline_compare

    args = Args()
    args.json = output_json
    run_baseline_compare(args)


@ci_baseline.command('stats', help='Show baseline statistics')
@click.pass_context
def baseline_stats(ctx):
    """Show baseline statistics."""
    from agentforge.cli.commands.ci import run_baseline_stats

    args = Args()
    run_baseline_stats(args)


@ci.command('init', help='Initialize CI workflow files')
@click.option('--platform', '-p', type=click.Choice(['github', 'azure']),
              required=True, help='CI platform')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing files')
@click.pass_context
def ci_init(ctx, platform, force):
    """Generate CI workflow files for a platform."""
    from agentforge.cli.commands.ci import run_ci_init

    args = Args()
    args.platform = platform
    args.force = force
    run_ci_init(args)


@ci.group('hooks', help='Git hook management commands')
@click.pass_context
def ci_hooks(ctx):
    """Manage git hooks for local development."""
    pass


@ci_hooks.command('install', help='Install pre-commit hook for local ratcheting')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing hook')
@click.option('--mode', '-m', type=click.Choice(['ratchet', 'strict']),
              default='ratchet', help='Hook mode: ratchet (default) or strict')
@click.pass_context
def hooks_install(ctx, force, mode):
    """Install pre-commit hook for local conformance checking."""
    from agentforge.cli.commands.ci import run_hooks_install

    args = Args()
    args.force = force
    args.mode = mode
    run_hooks_install(args)


@ci_hooks.command('uninstall', help='Remove pre-commit hook')
@click.pass_context
def hooks_uninstall(ctx):
    """Remove the pre-commit hook."""
    from agentforge.cli.commands.ci import run_hooks_uninstall

    args = Args()
    run_hooks_uninstall(args)
