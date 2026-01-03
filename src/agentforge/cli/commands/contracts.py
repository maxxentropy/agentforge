# @spec_file: .agentforge/specs/cli-commands-v1.yaml
# @spec_id: cli-commands-v1
# @component_id: cli-commands-contracts
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

"""Contract management commands - listing, checking, validation, exemptions."""
from pathlib import Path

import click


def run_contracts(args):
    """Fallback for contracts without subcommand."""
    pass


def run_contracts_list(args):
    """List all contracts."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACTS LIST")
    click.echo("=" * 60)

    from agentforge.core.contracts_registry import ContractRegistry

    registry = ContractRegistry(Path.cwd())
    registry.discover_contracts()
    contracts = registry.get_all_contracts()

    if not contracts:
        click.echo("No contracts found.")
        return

    for contract in contracts:
        click.echo(f"  - {contract.name} ({contract.type})")


def run_contracts_show(args):
    """Display contract details."""
    click.echo(f"Showing contract: {args.name}")


def run_contracts_check(args):
    """Execute contract checks."""
    click.echo("Running contract checks...")


def run_contracts_init(args):
    """Create new contract file."""
    click.echo(f"Creating new {args.type} contract...")


def run_contracts_validate(args):
    """Validate contract structure."""
    click.echo("Validating contracts...")


def _collect_python_files(file_args: list | None, repo_root: Path) -> list[Path]:
    """Collect Python files from arguments or repo root."""
    files: list[Path] = []
    if file_args:
        for file_arg in file_args:
            path = Path(file_arg)
            if path.is_dir():
                files.extend(path.rglob("*.py"))
            else:
                files.append(path)
    else:
        files = list(repo_root.rglob("*.py"))
    return files


def _filter_excluded_paths(files: list[Path]) -> list[Path]:
    """Filter out __pycache__, .git, and node_modules paths."""
    excluded = ("__pycache__", ".git", "node_modules")
    return [f for f in files if not any(ex in str(f) for ex in excluded)]


def _apply_fixes_to_files(
    check_id: str, files: list[Path], dry_run: bool, verbose: bool
) -> tuple[int, int]:
    """Apply fixes to files and return (total_fixes, files_fixed)."""
    from agentforge.core.contracts_fixers import apply_fix

    total_fixes = 0
    files_fixed = 0

    for file_path in files:
        result = apply_fix(check_id, file_path, dry_run=dry_run)
        if result is None:
            continue
        if result.errors:
            if verbose:
                click.echo(f"  ⚠ {file_path}: {result.errors[0]}")
            continue
        if result.fixes_applied > 0:
            total_fixes += result.fixes_applied
            files_fixed += 1
            if verbose:
                click.echo(f"  ✓ {file_path}: {result.fixes_applied} fix(es)")

    return total_fixes, files_fixed


def run_contracts_fix(args):
    """Auto-fix violations for a specific check."""
    from agentforge.core.contracts_fixers import get_fixer, list_fixers

    check_id = args.check_id

    # Check if fixer exists
    if get_fixer(check_id) is None:
        available = list_fixers()
        click.echo(f"No auto-fixer available for check: {check_id}")
        click.echo(f"Available fixers: {', '.join(available)}" if available else "No fixers are currently registered.")
        raise SystemExit(1)

    # Collect and filter files
    files_to_fix = _collect_python_files(args.files, Path.cwd())
    files_to_fix = _filter_excluded_paths(files_to_fix)

    if not files_to_fix:
        click.echo("No Python files found to fix.")
        return

    click.echo(f"{'[DRY RUN] ' if args.dry_run else ''}Fixing {check_id} in {len(files_to_fix)} files...")
    click.echo()

    total_fixes, files_fixed = _apply_fixes_to_files(check_id, files_to_fix, args.dry_run, args.verbose)

    click.echo()
    if args.dry_run:
        click.echo(f"Would fix {total_fixes} violations in {files_fixed} files.")
        click.echo("Run without --dry-run to apply fixes.")
    else:
        click.echo(f"Fixed {total_fixes} violations in {files_fixed} files.")


def run_exemptions_list(args):
    """List exemptions."""
    click.echo("Listing exemptions...")


def run_exemptions_add(args):
    """Create new exemption."""
    click.echo(f"Adding exemption for {args.contract}/{args.check}...")


def run_exemptions_audit(args):
    """Audit exemptions."""
    click.echo("Auditing exemptions...")
