# @spec_file: .agentforge/specs/cli-commands-v1.yaml
# @spec_id: cli-commands-v1
# @component_id: cli-commands-bridge
# @test_path: tests/unit/tools/bridge/test_registry.py

"""Bridge command implementation."""

import sys
import json
import click
from pathlib import Path
from typing import Optional


def _ensure_tools_path():
    """Add tools directory to path for imports."""
    tools_path = str(Path(__file__).parent.parent.parent / 'tools')
    if tools_path not in sys.path:
        sys.path.insert(0, tools_path)


def run_bridge_generate(
    root_path: Path,
    profile_path: Optional[Path] = None,
    output_dir: str = "contracts",
    zone_filter: Optional[str] = None,
    confidence_threshold: float = 0.6,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False,
):
    """
    Generate contracts from codebase profile.
    """
    click.echo()
    click.echo("=" * 60)
    click.echo("PROFILE-TO-CONFORMANCE BRIDGE")
    click.echo("=" * 60)

    _ensure_tools_path()

    try:
        from bridge import BridgeOrchestrator
    except ImportError as e:
        click.echo(f"\nError: Could not import bridge module: {e}")
        sys.exit(1)

    click.echo(f"\nRoot path: {root_path}")
    if zone_filter:
        click.echo(f"Zone filter: {zone_filter}")
    click.echo(f"Confidence threshold: {confidence_threshold}")
    if dry_run:
        click.echo(click.style("DRY RUN - no files will be written", fg="yellow"))

    try:
        orchestrator = BridgeOrchestrator(
            root_path=root_path,
            profile_path=profile_path,
            output_dir=output_dir,
            confidence_threshold=confidence_threshold,
            verbose=verbose,
        )

        contracts, report = orchestrator.generate(
            zone_filter=zone_filter,
            dry_run=dry_run,
            force=force,
        )
    except FileNotFoundError as e:
        click.echo(f"\nError: {e}")
        click.echo("Run 'agentforge discover' first to generate a codebase profile.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nError during generation: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Output results
    _output_generate_results(contracts, report, dry_run, verbose)

    # Write report if not dry run
    if not dry_run and contracts:
        try:
            report_path = orchestrator.write_report(report)
            click.echo(f"\nReport saved to: {report_path}")
        except Exception as e:
            click.echo(f"\nWarning: Could not write report: {e}")

    # Final status
    click.echo()
    if contracts:
        if dry_run:
            click.echo(click.style(f"✓ Would generate {len(contracts)} contract(s)", fg='green'))
        else:
            click.echo(click.style(f"✓ Generated {len(contracts)} contract(s)", fg='green'))
    else:
        click.echo(click.style("⚠ No contracts generated (no patterns matched)", fg='yellow'))

    if report.checks_disabled > 0:
        click.echo(click.style(f"  {report.checks_disabled} check(s) disabled - review required", fg='yellow'))

    if report.conflicts_detected > 0:
        click.echo(f"  {report.conflicts_detected} conflict(s) detected and resolved")


def _output_generate_results(contracts, report, dry_run: bool, verbose: bool):
    """Output generation results."""
    click.echo()
    click.echo("-" * 60)
    click.echo("GENERATION RESULTS" if not dry_run else "PREVIEW RESULTS")
    click.echo("-" * 60)

    if not contracts:
        click.echo("\n  No contracts generated")
        return

    for contract in contracts:
        click.echo(f"\n  {contract.name}.contract.yaml:")
        click.echo(f"    Language: {contract.language}")
        click.echo(f"    Checks: {len(contract.checks)} total")
        click.echo(f"      - Enabled: {contract.enabled_count}")
        click.echo(f"      - Disabled (needs review): {contract.disabled_count}")

        if verbose:
            click.echo("    Checks:")
            for check in contract.checks:
                status = "enabled" if check.enabled else "disabled"
                marker = "✓" if check.enabled else "○"
                click.echo(f"      {marker} {check.id} [{status}]")
                if check.review_reason and not check.enabled:
                    click.echo(f"        → {check.review_reason}")

    # Summary
    click.echo()
    click.echo(f"  Total: {report.total_checks} checks across {len(contracts)} contract(s)")
    click.echo(f"    Enabled: {report.checks_enabled}")
    click.echo(f"    Disabled: {report.checks_disabled}")


def run_bridge_preview(
    root_path: Path,
    profile_path: Optional[Path] = None,
    zone_filter: Optional[str] = None,
    verbose: bool = False,
):
    """Preview what contracts would be generated."""
    run_bridge_generate(
        root_path=root_path,
        profile_path=profile_path,
        zone_filter=zone_filter,
        dry_run=True,
        verbose=verbose,
    )


def run_bridge_mappings(
    pattern_filter: Optional[str] = None,
    output_format: str = "table",
):
    """List available pattern mappings."""
    click.echo()
    click.echo("=" * 60)
    click.echo("PATTERN MAPPINGS")
    click.echo("=" * 60)

    _ensure_tools_path()

    try:
        from bridge import MappingRegistry
        # Import mapping modules to trigger registration via decorators
        from bridge.mappings import cqrs, architecture, repository, conventions  # noqa: F401
    except ImportError as e:
        click.echo(f"\nError: Could not import bridge module: {e}")
        sys.exit(1)

    mapping_info = MappingRegistry.get_mapping_info()

    if pattern_filter:
        mapping_info = [m for m in mapping_info if m["pattern_key"] == pattern_filter]

    if not mapping_info:
        click.echo("\n  No mappings found")
        if pattern_filter:
            click.echo(f"  (filter: {pattern_filter})")
        return

    if output_format == "table":
        click.echo()
        click.echo(f"  {'Pattern Key':<20} {'Languages':<20} {'Min Conf.':<10} {'Version'}")
        click.echo(f"  {'-'*20} {'-'*20} {'-'*10} {'-'*10}")
        for m in mapping_info:
            langs = ", ".join(m["languages"]) if m["languages"] else "all"
            click.echo(f"  {m['pattern_key']:<20} {langs:<20} {m['min_confidence']:<10} {m['version']}")

        click.echo(f"\n  Total: {len(mapping_info)} mapping(s)")

    elif output_format == "yaml":
        import yaml
        click.echo(yaml.dump(mapping_info, default_flow_style=False))

    elif output_format == "json":
        click.echo(json.dumps(mapping_info, indent=2))


def run_bridge_refresh(
    root_path: Path,
    profile_path: Optional[Path] = None,
    zone_filter: Optional[str] = None,
    verbose: bool = False,
):
    """Regenerate contracts from updated profile."""
    run_bridge_generate(
        root_path=root_path,
        profile_path=profile_path,
        zone_filter=zone_filter,
        force=True,
        verbose=verbose,
    )


def run_bridge_diff(
    root_path: Path,
    zone_filter: Optional[str] = None,
):
    """Show diff between generated and existing contracts."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACT DIFF")
    click.echo("=" * 60)

    _ensure_tools_path()

    try:
        from bridge import BridgeOrchestrator
    except ImportError as e:
        click.echo(f"\nError: Could not import bridge module: {e}")
        sys.exit(1)

    try:
        orchestrator = BridgeOrchestrator(root_path=root_path)
        contracts, _ = orchestrator.generate(zone_filter=zone_filter, dry_run=True)
    except FileNotFoundError as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)

    # Compare with existing
    existing_ids = orchestrator.resolver.get_existing_check_ids()

    click.echo()
    for contract in contracts:
        click.echo(f"\n{contract.name}:")

        for check in contract.checks:
            if check.id in existing_ids:
                click.echo(f"  ~ {check.id} (exists)")
            else:
                click.echo(click.style(f"  + {check.id} (new)", fg="green"))

    # Show checks in existing but not in generated
    generated_ids = {c.id for contract in contracts for c in contract.checks}
    removed = existing_ids - generated_ids

    if removed:
        click.echo("\n\nChecks in existing contracts but not generated:")
        for check_id in sorted(removed):
            click.echo(click.style(f"  - {check_id}", fg="red"))
