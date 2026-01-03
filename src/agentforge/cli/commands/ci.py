# @spec_file: .agentforge/specs/cli-commands-v1.yaml
# @spec_id: cli-commands-v1
# @component_id: cli-commands-ci
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
CI/CD Integration command handlers.

Implements: ci run, ci baseline save/compare/stats, ci init
"""

import json
import sys
from pathlib import Path
from typing import Any

from agentforge.core.cicd import (
    BaselineError,
    BaselineManager,
    CIConfig,
    CIMode,
    CIRunner,
    ExitCode,
    GitHelper,
)
from agentforge.core.cicd.outputs import write_junit, write_markdown, write_sarif
from agentforge.core.contracts_registry import ContractRegistry


def run_ci_check(args: Any) -> int:
    """
    Run conformance checks in CI mode.

    Returns exit code for CI integration.
    """
    repo_root = Path.cwd()

    # Build configuration
    mode_map = {
        "full": CIMode.FULL,
        "incremental": CIMode.INCREMENTAL,
        "pr": CIMode.PR,
    }
    # Determine fail conditions from min_severity
    min_severity = getattr(args, 'min_severity', 'error')
    severity_order = ['info', 'warning', 'error']
    min_idx = severity_order.index(min_severity)

    # fail_on_new_errors if min_severity is error or lower
    # fail_on_new_warnings if min_severity is warning or lower
    config = CIConfig(
        mode=mode_map.get(args.mode, CIMode.FULL),
        parallel_enabled=args.parallel,
        max_workers=args.workers,
        fail_on_new_errors=(min_idx <= severity_order.index('error')),
        fail_on_new_warnings=(min_idx <= severity_order.index('warning')) or args.fail_on_warnings,
        min_severity=min_severity,
        ratchet_enabled=getattr(args, 'ratchet', False),
        output_sarif=args.output_sarif,
        output_junit=args.output_junit,
        output_markdown=args.output_markdown,
        sarif_path=args.sarif_path,
        junit_path=args.junit_path,
        markdown_path=args.markdown_path,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
    )

    # Load contracts
    registry = ContractRegistry(repo_root)
    registry.discover_contracts()
    contracts = registry.get_all_contracts_data()

    if not contracts:
        print("No contracts found. Run 'agentforge contracts create' first.")
        return ExitCode.CONFIG_ERROR.value

    # Run checks
    runner = CIRunner(repo_root, config)
    result = runner.run(contracts)

    # Generate outputs
    if config.output_sarif:
        write_sarif(result, repo_root / config.sarif_path)
        print(f"SARIF output written to {config.sarif_path}")

    if config.output_junit:
        write_junit(result, repo_root / config.junit_path)
        print(f"JUnit output written to {config.junit_path}")

    if config.output_markdown:
        write_markdown(result, repo_root / config.markdown_path)
        print(f"Markdown output written to {config.markdown_path}")

    # Print summary
    if args.json:
        print(json.dumps(result.to_summary_dict(), indent=2))
    else:
        _print_ci_summary(result, config.ratchet_enabled, config.min_severity)

    return result.exit_code.value


def _print_ci_summary(result, ratchet_enabled: bool = False, min_severity: str = "error"):
    """Print human-readable CI result summary."""
    status = "✅ PASSED" if result.is_success else "❌ FAILED"
    print(f"\n{status}")
    mode_str = result.mode.value
    if ratchet_enabled:
        mode_str += " (ratchet)"
    if min_severity != "error":
        mode_str += f" [min-severity: {min_severity}]"
    print(f"Mode: {mode_str}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"Files checked: {result.files_checked}")
    print(f"Checks run: {result.checks_run}")
    print()
    print(f"Violations: {result.total_violations}")
    print(f"  Errors: {result.error_count}")
    print(f"  Warnings: {result.warning_count}")
    print(f"  Info: {result.info_count}")

    if result.comparison:
        print()
        if ratchet_enabled:
            print("Ratchet Comparison:")
            if result.comparison.net_change > 0:
                print(f"  ❌ Violations INCREASED by {result.comparison.net_change}")
            elif result.comparison.net_change < 0:
                print(f"  ✨ Violations DECREASED by {-result.comparison.net_change}")
            else:
                print(f"  ➡️ Violations unchanged")
        else:
            print("Baseline Comparison:")
        print(f"  New violations: {len(result.comparison.new_violations)}")
        print(f"  Fixed violations: {len(result.comparison.fixed_violations)}")
        print(f"  Existing violations: {len(result.comparison.existing_violations)}")
        print(f"  Net change: {result.comparison.net_change:+d}")

    if result.errors:
        print()
        print("Runtime errors:")
        for error in result.errors:
            print(f"  - {error}")

    print()
    print(f"Exit code: {result.exit_code.value} ({result.exit_code.description})")


def run_baseline_save(args: Any) -> None:
    """Save current violations as baseline."""
    repo_root = Path.cwd()

    baseline_manager = BaselineManager(str(repo_root / ".agentforge/baseline.json"))

    if baseline_manager.exists() and not args.force:
        print("Baseline already exists. Use --force to overwrite.")
        sys.exit(1)

    # Run full check to get current violations
    registry = ContractRegistry(repo_root)
    registry.discover_contracts()
    contracts = registry.get_all_contracts_data()

    if not contracts:
        print("No contracts found.")
        sys.exit(1)

    config = CIConfig(mode=CIMode.FULL)
    runner = CIRunner(repo_root, config)
    result = runner.run(contracts)

    # Save baseline
    try:
        commit_sha = GitHelper.get_current_sha()
    except Exception:
        commit_sha = None

    baseline = baseline_manager.create_from_violations(result.violations, commit_sha)
    baseline_manager.save(baseline)

    print(f"Baseline saved with {len(baseline.entries)} violations")
    if commit_sha:
        print(f"Commit: {commit_sha[:8]}")


def run_baseline_compare(args: Any) -> None:
    """Compare current violations against baseline."""
    repo_root = Path.cwd()

    baseline_manager = BaselineManager(str(repo_root / ".agentforge/baseline.json"))

    if not baseline_manager.exists():
        print("No baseline found. Run 'agentforge ci baseline save' first.")
        sys.exit(1)

    # Run full check
    registry = ContractRegistry(repo_root)
    registry.discover_contracts()
    contracts = registry.get_all_contracts_data()

    if not contracts:
        print("No contracts found.")
        sys.exit(1)

    config = CIConfig(mode=CIMode.FULL)
    runner = CIRunner(repo_root, config)
    result = runner.run(contracts)

    # Compare
    try:
        comparison = baseline_manager.compare(result.violations)
    except BaselineError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.json:
        output = {
            "new_violations": len(comparison.new_violations),
            "fixed_violations": len(comparison.fixed_violations),
            "existing_violations": len(comparison.existing_violations),
            "net_change": comparison.net_change,
            "introduces_violations": comparison.introduces_violations,
            "has_improvements": comparison.has_improvements,
        }
        print(json.dumps(output, indent=2))
    else:
        print("Baseline Comparison")
        print("=" * 40)
        print(f"New violations: {len(comparison.new_violations)}")
        print(f"Fixed violations: {len(comparison.fixed_violations)}")
        print(f"Existing violations: {len(comparison.existing_violations)}")
        print(f"Net change: {comparison.net_change:+d}")
        print()

        if comparison.new_violations:
            print("New violations:")
            for v in comparison.new_violations[:10]:
                print(f"  - [{v.severity}] {v.check_id} in {v.file_path}:{v.line or 0}")
            if len(comparison.new_violations) > 10:
                print(f"  ...and {len(comparison.new_violations) - 10} more")

        if comparison.fixed_violations:
            print("\nFixed violations:")
            for entry in comparison.fixed_violations[:10]:
                print(f"  - {entry.check_id} in {entry.file_path}")
            if len(comparison.fixed_violations) > 10:
                print(f"  ...and {len(comparison.fixed_violations) - 10} more")


def run_baseline_stats(args: Any) -> None:
    """Show baseline statistics."""
    repo_root = Path.cwd()

    baseline_manager = BaselineManager(str(repo_root / ".agentforge/baseline.json"))
    stats = baseline_manager.get_stats()

    if not stats:
        print("No baseline found. Run 'agentforge ci baseline save' first.")
        sys.exit(1)

    print("Baseline Statistics")
    print("=" * 40)
    print(f"Total entries: {stats['total_entries']}")
    print(f"Created: {stats['created_at']}")
    print(f"Updated: {stats['updated_at']}")
    if stats['commit_sha']:
        print(f"Commit: {stats['commit_sha'][:8]}")

    print()
    print("By check:")
    for check_id, count in sorted(stats['by_check'].items(), key=lambda x: -x[1]):
        print(f"  {check_id}: {count}")

    print()
    print("By file (top 10):")
    sorted_files = sorted(stats['by_file'].items(), key=lambda x: -x[1])[:10]
    for file_path, count in sorted_files:
        print(f"  {file_path}: {count}")


def run_ci_init(args: Any) -> None:
    """Generate CI workflow files for a platform."""
    repo_root = Path.cwd()

    if args.platform == "github":
        _init_github_workflow(repo_root, args.force)
    elif args.platform == "azure":
        _init_azure_pipeline(repo_root, args.force)


def _init_github_workflow(repo_root: Path, force: bool) -> None:
    """Generate GitHub Actions workflow."""
    workflow_dir = repo_root / ".github" / "workflows"
    workflow_file = workflow_dir / "agentforge.yml"

    if workflow_file.exists() and not force:
        print(f"Workflow file already exists: {workflow_file}")
        print("Use --force to overwrite.")
        sys.exit(1)

    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Import template
    from agentforge.core.cicd.platforms.github import GITHUB_WORKFLOW_TEMPLATE

    workflow_file.write_text(GITHUB_WORKFLOW_TEMPLATE)
    print(f"Created GitHub Actions workflow: {workflow_file}")
    print()
    print("Next steps:")
    print("1. Review and customize the workflow file")
    print("2. Commit and push to enable CI checks")
    print("3. Run 'agentforge ci baseline save' on main branch")


def _init_azure_pipeline(repo_root: Path, force: bool) -> None:
    """Generate Azure DevOps pipeline."""
    pipeline_file = repo_root / "azure-pipelines" / "agentforge.yml"

    if pipeline_file.exists() and not force:
        print(f"Pipeline file already exists: {pipeline_file}")
        print("Use --force to overwrite.")
        sys.exit(1)

    pipeline_file.parent.mkdir(parents=True, exist_ok=True)

    # Import template
    from agentforge.core.cicd.platforms.azure import AZURE_PIPELINE_TEMPLATE

    pipeline_file.write_text(AZURE_PIPELINE_TEMPLATE)
    print(f"Created Azure DevOps pipeline: {pipeline_file}")
    print()
    print("Next steps:")
    print("1. Review and customize the pipeline file")
    print("2. Add as a pipeline in Azure DevOps")
    print("3. Run 'agentforge ci baseline save' on main branch")


# Pre-commit hook template
PRECOMMIT_HOOK_TEMPLATE = '''#!/bin/bash
# AgentForge Pre-commit Hook
# Generated by: agentforge ci hooks install
# Mode: {mode}
#
# This hook runs conformance checks before each commit.
# {mode_description}

set -e

echo "🔍 Running AgentForge conformance check..."

# Check if baseline exists
if [ ! -f ".agentforge/baseline.json" ]; then
    echo "⚠️  No baseline found. Run 'agentforge ci baseline save' first."
    echo "   Skipping pre-commit check."
    exit 0
fi

# Run the check in {mode} mode
{check_command}
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Conformance check passed"
else
    echo ""
    echo "❌ Conformance check failed"
    echo ""
    echo "Your commit introduces violations. Options:"
    echo "  1. Fix the violations and try again"
    echo "  2. Skip this hook: git commit --no-verify"
    echo "  3. Update baseline: agentforge ci baseline save --force"
    echo ""
fi

exit $EXIT_CODE
'''


def run_hooks_install(args: Any) -> None:
    """Install pre-commit hook for local conformance checking."""
    repo_root = Path.cwd()

    # Check if this is a git repo
    if not GitHelper.is_git_repo():
        print("Error: Not a git repository.")
        sys.exit(1)

    hooks_dir = repo_root / ".git" / "hooks"
    hook_file = hooks_dir / "pre-commit"

    # Check for existing hook
    if hook_file.exists():
        if not args.force:
            # Check if it's our hook
            content = hook_file.read_text()
            if "AgentForge Pre-commit Hook" in content:
                print("AgentForge pre-commit hook already installed.")
                print("Use --force to reinstall.")
            else:
                print("A pre-commit hook already exists (not from AgentForge).")
                print("Use --force to overwrite, or manually integrate.")
            sys.exit(1)

    # Generate hook content based on mode
    if args.mode == "ratchet":
        mode_description = "Ratchet mode: only fails if violations INCREASE from baseline."
        check_command = "agentforge ci run --ratchet --no-output-sarif --no-output-markdown"
    else:
        mode_description = "Strict mode: fails on ANY new violations."
        check_command = "agentforge ci run --mode pr --no-output-sarif --no-output-markdown"

    hook_content = PRECOMMIT_HOOK_TEMPLATE.format(
        mode=args.mode,
        mode_description=mode_description,
        check_command=check_command,
    )

    # Write hook
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file.write_text(hook_content)
    hook_file.chmod(0o755)  # Make executable

    print(f"✅ Pre-commit hook installed: {hook_file}")
    print(f"   Mode: {args.mode}")
    print()
    print("The hook will run conformance checks before each commit.")
    print("To skip the hook for a specific commit: git commit --no-verify")
    print()
    if not (repo_root / ".agentforge" / "baseline.json").exists():
        print("⚠️  No baseline found. Run 'agentforge ci baseline save' to create one.")


def run_hooks_uninstall(args: Any) -> None:
    """Remove the pre-commit hook."""
    repo_root = Path.cwd()

    if not GitHelper.is_git_repo():
        print("Error: Not a git repository.")
        sys.exit(1)

    hook_file = repo_root / ".git" / "hooks" / "pre-commit"

    if not hook_file.exists():
        print("No pre-commit hook found.")
        return

    # Check if it's our hook
    content = hook_file.read_text()
    if "AgentForge Pre-commit Hook" not in content:
        print("The pre-commit hook was not installed by AgentForge.")
        print("Not removing to avoid breaking other tooling.")
        sys.exit(1)

    hook_file.unlink()
    print("✅ Pre-commit hook removed.")
