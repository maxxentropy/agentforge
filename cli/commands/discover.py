"""Brownfield Discovery command implementation."""

import sys
import json
import click
import yaml
from pathlib import Path


def _ensure_tools_path():
    """Add tools directory to path for imports."""
    tools_path = str(Path(__file__).parent.parent.parent / 'tools')
    if tools_path not in sys.path:
        sys.path.insert(0, tools_path)


def run_discover(args):
    """
    Run brownfield discovery on a codebase.

    Analyzes the codebase to detect languages, frameworks, structure,
    and patterns, then generates a codebase_profile.yaml.
    """
    click.echo()
    click.echo("=" * 60)
    click.echo("BROWNFIELD DISCOVERY")
    click.echo("=" * 60)

    _ensure_tools_path()

    try:
        from discovery import DiscoveryManager, DiscoveryPhase
    except ImportError as e:
        click.echo(f"\nError: Could not import discovery module: {e}")
        sys.exit(1)

    root_path = Path(args.path).resolve()
    click.echo(f"\nAnalyzing: {root_path}")

    # Determine phases to run
    phases = None
    if args.phase != 'all':
        phase_map = {
            'language': [DiscoveryPhase.LANGUAGE_DETECTION],
            'structure': [DiscoveryPhase.STRUCTURE_ANALYSIS],
            'patterns': [DiscoveryPhase.PATTERN_EXTRACTION],
            'architecture': [DiscoveryPhase.ARCHITECTURE_MAPPING],
        }
        phases = phase_map.get(args.phase)

    # Progress callback for verbose mode
    def progress_callback(message: str, percentage: float):
        if args.verbose:
            click.echo(f"  [{percentage:5.1f}%] {message}")

    # Run discovery
    manager = DiscoveryManager(
        root_path=root_path,
        verbose=args.verbose,
        progress_callback=progress_callback if args.verbose else None,
    )

    try:
        result = manager.discover(
            phases=phases,
            save_profile=not args.no_save,
        )
    except Exception as e:
        click.echo(f"\nError during discovery: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Output results based on format
    if args.format == 'summary':
        _output_summary(result, args)
    elif args.format == 'yaml':
        _output_yaml(result)
    elif args.format == 'json':
        _output_json(result)

    # Final status
    click.echo()
    if result.success:
        click.echo(click.style("✓ Discovery completed successfully", fg='green'))
        if result.profile_path:
            click.echo(f"  Profile saved to: {result.profile_path}")
    else:
        click.echo(click.style("✗ Discovery completed with errors", fg='red'))
        for error in result.errors:
            click.echo(f"  - {error}")
        sys.exit(1)


def _output_summary(result, args):
    """Output human-readable summary."""
    click.echo()
    click.echo("-" * 60)
    click.echo("DISCOVERY RESULTS")
    click.echo("-" * 60)

    profile = result.profile
    if not profile:
        click.echo("  No profile generated")
        return

    # Languages
    click.echo("\nLanguages:")
    for lang in profile.languages:
        primary = " (primary)" if lang.primary else ""
        click.echo(f"  • {lang.name}{primary}: {lang.file_count} files, {lang.line_count} lines")
        if lang.frameworks:
            click.echo(f"    Frameworks: {', '.join(lang.frameworks)}")

    # Structure
    click.echo("\nStructure:")
    structure = profile.structure
    click.echo(f"  Architecture style: {structure.get('architecture_style', 'unknown')}")
    click.echo(f"  Confidence: {structure.get('confidence', 0):.0%}")
    layers = structure.get('layers', {})
    if layers:
        click.echo("  Layers detected:")
        for name, layer in layers.items():
            click.echo(f"    • {name}: {layer.get('file_count', 0)} files")

    # Patterns
    click.echo("\nPatterns:")
    patterns = profile.patterns
    if patterns:
        # Separate patterns from frameworks
        code_patterns = {k: v for k, v in patterns.items() if not k.startswith('framework_')}
        frameworks = {k.replace('framework_', ''): v for k, v in patterns.items() if k.startswith('framework_')}

        if code_patterns:
            click.echo("  Code patterns:")
            for name, pattern in sorted(code_patterns.items(), key=lambda x: x[1].get('confidence', 0), reverse=True):
                conf = pattern.get('confidence', 0)
                click.echo(f"    • {name}: {conf:.0%} confidence")

        if frameworks:
            click.echo("  Frameworks:")
            for name, fw in sorted(frameworks.items(), key=lambda x: x[1].get('confidence', 0), reverse=True):
                conf = fw.get('confidence', 0)
                fw_type = fw.get('metadata', {}).get('type', '')
                click.echo(f"    • {name} ({fw_type}): {conf:.0%} confidence")
    else:
        click.echo("  No patterns detected")

    # Dependencies summary
    if profile.dependencies:
        click.echo(f"\nDependencies: {len(profile.dependencies)} packages")
        dev_deps = sum(1 for d in profile.dependencies if d.is_dev)
        click.echo(f"  • {len(profile.dependencies) - dev_deps} runtime, {dev_deps} dev")

    # Timing
    click.echo(f"\nDuration: {result.total_duration_seconds:.2f}s")


def _output_yaml(result):
    """Output full profile as YAML."""
    if result.profile:
        from discovery.generators.profile import ProfileGenerator
        generator = ProfileGenerator(Path("."))
        generator._profile = result.profile
        click.echo(generator.to_yaml())


def _output_json(result):
    """Output full profile as JSON."""
    if result.profile:
        from discovery.generators.profile import ProfileGenerator
        generator = ProfileGenerator(Path("."))
        generator._profile = result.profile
        data = generator._profile_to_dict(result.profile)
        click.echo(json.dumps(data, indent=2, default=str))
