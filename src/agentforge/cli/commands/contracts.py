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


def run_contracts_fix(args):
    """Auto-fix violations for a specific check."""
    from agentforge.core.contracts_fixers import apply_fix, get_fixer, list_fixers

    check_id = args.check_id
    dry_run = args.dry_run
    verbose = args.verbose
    file_args = args.files

    # Check if fixer exists
    if get_fixer(check_id) is None:
        available = list_fixers()
        click.echo(f"No auto-fixer available for check: {check_id}")
        if available:
            click.echo(f"Available fixers: {', '.join(available)}")
        else:
            click.echo("No fixers are currently registered.")
        raise SystemExit(1)

    # Collect files to fix
    repo_root = Path.cwd()
    files_to_fix: list[Path] = []

    if file_args:
        for file_arg in file_args:
            path = Path(file_arg)
            if path.is_dir():
                files_to_fix.extend(path.rglob("*.py"))
            else:
                files_to_fix.append(path)
    else:
        # Default to all Python files in repo
        files_to_fix = list(repo_root.rglob("*.py"))

    # Filter out __pycache__ and other unwanted paths
    files_to_fix = [
        f for f in files_to_fix
        if "__pycache__" not in str(f)
        and ".git" not in str(f)
        and "node_modules" not in str(f)
    ]

    if not files_to_fix:
        click.echo("No Python files found to fix.")
        return

    click.echo(f"{'[DRY RUN] ' if dry_run else ''}Fixing {check_id} in {len(files_to_fix)} files...")
    click.echo()

    total_fixes = 0
    files_fixed = 0

    for file_path in files_to_fix:
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

    click.echo()
    if dry_run:
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
