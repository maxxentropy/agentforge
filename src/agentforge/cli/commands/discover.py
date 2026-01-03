"""Brownfield Discovery command implementation."""

import json
import sys
from pathlib import Path

import click
import yaml


def _handle_discovery_error(e, args):
    """Handle discovery error and exit."""
    click.echo(f"\nError during discovery: {e}")
    if args.verbose:
        import traceback
        traceback.print_exc()
    sys.exit(1)


def _output_final_status(result, success_message: str):
    """Output final status message."""
    click.echo()
    if result.success:
        click.echo(click.style(f"✓ {success_message}", fg='green'))
        if result.profile_path:
            click.echo(f"  Profile saved to: {result.profile_path}")
    else:
        click.echo(click.style("✗ Discovery completed with errors", fg='red'))
        for error in result.errors:
            click.echo(f"  - {error}")
        sys.exit(1)


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

    root_path = Path(args.path).resolve()
    click.echo(f"\nAnalyzing: {root_path}")

    # Progress callback for verbose mode
    def progress_callback(message: str, percentage: float):
        if args.verbose:
            click.echo(f"  [{percentage:5.1f}%] {message}")

    # Check if multi-zone mode
    multi_zone = getattr(args, 'multi_zone', False)

    if multi_zone:
        _run_multi_zone_discovery(args, root_path, progress_callback)
    else:
        _run_single_zone_discovery(args, root_path, progress_callback)


def _get_discovery_phases(args):
    """Get discovery phases based on args."""
    from agentforge.core.discovery import DiscoveryPhase
    if args.phase == 'all':
        return None
    phase_map = {
        'language': [DiscoveryPhase.LANGUAGE],
        'structure': [DiscoveryPhase.STRUCTURE],
        'patterns': [DiscoveryPhase.PATTERNS],
        'architecture': [DiscoveryPhase.ARCHITECTURE],
    }
    return phase_map.get(args.phase)


def _output_by_format(args, result, summary_fn, yaml_fn, json_fn):
    """Output result based on format argument."""
    if args.format == 'summary':
        summary_fn(result, args)
    elif args.format == 'yaml':
        yaml_fn(result)
    elif args.format == 'json':
        json_fn(result)


def _run_single_zone_discovery(args, root_path, progress_callback):
    """Run traditional single-zone discovery."""
    try:
        from agentforge.core.discovery import DiscoveryManager
    except ImportError as e:
        click.echo(f"\nError: Could not import discovery module: {e}")
        sys.exit(1)

    phases = _get_discovery_phases(args)

    manager = DiscoveryManager(
        root_path=root_path,
        verbose=args.verbose,
        progress_callback=progress_callback if args.verbose else None,
    )

    try:
        result = manager.discover(phases=phases, save_profile=not args.no_save)
    except Exception as e:
        _handle_discovery_error(e, args)

    _output_by_format(args, result, _output_summary, _output_yaml, _output_json)
    _output_final_status(result, "Discovery completed successfully")


def _run_multi_zone_discovery(args, root_path, progress_callback):
    """Run multi-zone discovery."""
    try:
        from agentforge.core.discovery import MultiZoneDiscoveryManager
    except ImportError as e:
        click.echo(f"\nError: Could not import multi-zone discovery module: {e}")
        sys.exit(1)

    manager = MultiZoneDiscoveryManager(
        root_path=root_path,
        verbose=args.verbose,
        progress_callback=progress_callback if args.verbose else None,
    )

    # Handle --list-zones flag
    if getattr(args, 'list_zones', False):
        _output_zones_list(manager.list_zones())
        return

    # Run full discovery
    try:
        result = manager.discover(
            zone_name=getattr(args, 'zone', None),
            save_profile=not args.no_save,
        )
    except Exception as e:
        _handle_discovery_error(e, args)

    # Handle --interactions flag
    if getattr(args, 'interactions', False):
        _output_interactions(result.interactions)
        return

    _output_by_format(
        args, result,
        _output_multi_zone_summary, _output_multi_zone_yaml, _output_multi_zone_json
    )
    _output_final_status(result, "Multi-zone discovery completed successfully")


def _output_zones_list(zones):
    """Output list of detected zones."""
    click.echo()
    click.echo("-" * 60)
    click.echo("DETECTED ZONES")
    click.echo("-" * 60)

    if not zones:
        click.echo("\n  No zones detected")
        return

    click.echo(f"\n  Found {len(zones)} zone(s):\n")
    for zone in zones:
        click.echo(f"  • {zone.name}")
        click.echo(f"    Language: {zone.language}")
        click.echo(f"    Path: {zone.path}")
        if zone.marker:
            click.echo(f"    Marker: {zone.marker.name}")
        click.echo(f"    Detection: {zone.detection.value}")
        if zone.purpose:
            click.echo(f"    Purpose: {zone.purpose}")
        click.echo()


def _output_interactions(interactions):
    """Output list of detected interactions."""
    click.echo()
    click.echo("-" * 60)
    click.echo("CROSS-ZONE INTERACTIONS")
    click.echo("-" * 60)

    if not interactions:
        click.echo("\n  No cross-zone interactions detected")
        return

    click.echo(f"\n  Found {len(interactions)} interaction(s):\n")
    for interaction in interactions:
        click.echo(f"  • {interaction.id}")
        click.echo(f"    Type: {interaction.interaction_type.value}")
        if interaction.from_zone and interaction.to_zone:
            click.echo(f"    {interaction.from_zone} → {interaction.to_zone}")
        elif interaction.zones:
            click.echo(f"    Zones: {', '.join(interaction.zones)}")
        if interaction.details:
            for key, value in interaction.details.items():
                click.echo(f"    {key}: {value}")
        click.echo()


def _output_zone_profile(zone_name, profile):
    """Output a single zone's profile summary."""
    click.echo()
    click.echo(f"\n{'='*40}")
    click.echo(f"Zone: {zone_name}")
    click.echo(f"{'='*40}")

    for lang in profile.languages:
        click.echo(f"\n  Language: {lang.name}")
        click.echo(f"  Files: {lang.file_count}, Lines: {lang.line_count}")
        if lang.frameworks:
            click.echo(f"  Frameworks: {', '.join(lang.frameworks)}")

    structure = profile.structure
    click.echo(f"\n  Architecture: {structure.get('style', 'unknown')} ({structure.get('confidence', 0):.0%})")
    layers = structure.get('layers', {})
    if layers:
        click.echo(f"  Layers: {', '.join(layers.keys())}")

    patterns = profile.patterns
    if patterns:
        code_patterns = [k for k in patterns if not k.startswith('framework_')]
        if code_patterns:
            click.echo(f"  Patterns: {', '.join(code_patterns[:5])}")


def _output_cross_zone_interactions(interactions):
    """Output cross-zone interactions summary."""
    if not interactions:
        return
    click.echo()
    click.echo("-" * 40)
    click.echo(f"Cross-Zone Interactions: {len(interactions)}")
    for interaction in interactions:
        if interaction.from_zone and interaction.to_zone:
            click.echo(f"  • {interaction.from_zone} → {interaction.to_zone} ({interaction.interaction_type.value})")
        elif interaction.zones:
            click.echo(f"  • {', '.join(interaction.zones)} ({interaction.interaction_type.value})")


def _output_multi_zone_summary(result, args):
    """Output human-readable multi-zone summary."""
    click.echo()
    click.echo("-" * 60)
    click.echo("MULTI-ZONE DISCOVERY RESULTS")
    click.echo("-" * 60)

    click.echo(f"\nZones Detected: {len(result.zones)}")
    for zone in result.zones:
        click.echo(f"  • {zone.name}: {zone.language} at {zone.path}")

    for zone_name, profile in result.zone_profiles.items():
        _output_zone_profile(zone_name, profile)

    _output_cross_zone_interactions(result.interactions)
    click.echo(f"\nDuration: {result.total_duration_seconds:.2f}s")


def _output_multi_zone_yaml(result):
    """Output multi-zone profile as YAML."""
    if result.profile_path and result.profile_path.exists():
        click.echo(result.profile_path.read_text())
    else:
        click.echo("No profile generated")


def _output_multi_zone_json(result):
    """Output multi-zone profile as JSON."""
    if result.profile_path and result.profile_path.exists():
        profile_data = yaml.safe_load(result.profile_path.read_text())
        click.echo(json.dumps(profile_data, indent=2, default=str))
    else:
        click.echo("{}")


def _output_languages_section(languages):
    """Output languages section."""
    click.echo("\nLanguages:")
    for lang in languages:
        primary = " (primary)" if lang.primary else ""
        click.echo(f"  • {lang.name}{primary}: {lang.file_count} files, {lang.line_count} lines")
        if lang.frameworks:
            click.echo(f"    Frameworks: {', '.join(lang.frameworks)}")


def _output_structure_section(structure):
    """Output structure section."""
    click.echo("\nStructure:")
    click.echo(f"  Architecture style: {structure.get('architecture_style', 'unknown')}")
    click.echo(f"  Confidence: {structure.get('confidence', 0):.0%}")
    layers = structure.get('layers', {})
    if layers:
        click.echo("  Layers detected:")
        for name, layer in layers.items():
            click.echo(f"    • {name}: {layer.get('file_count', 0)} files")


def _output_patterns_section(patterns):
    """Output patterns section."""
    click.echo("\nPatterns:")
    if not patterns:
        click.echo("  No patterns detected")
        return

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


def _output_dependencies_section(dependencies):
    """Output dependencies section."""
    if dependencies:
        click.echo(f"\nDependencies: {len(dependencies)} packages")
        dev_deps = sum(1 for d in dependencies if d.is_dev)
        click.echo(f"  • {len(dependencies) - dev_deps} runtime, {dev_deps} dev")


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

    _output_languages_section(profile.languages)
    _output_structure_section(profile.structure)
    _output_patterns_section(profile.patterns)
    _output_dependencies_section(profile.dependencies)
    click.echo(f"\nDuration: {result.total_duration_seconds:.2f}s")


def _output_yaml(result):
    """Output full profile as YAML."""
    if result.profile:
        from agentforge.core.discovery.generators.profile import ProfileGenerator
        generator = ProfileGenerator(Path("."))
        generator._profile = result.profile
        click.echo(generator.to_yaml())


def _output_json(result):
    """Output full profile as JSON."""
    if result.profile:
        from agentforge.core.discovery.generators.profile import ProfileGenerator
        generator = ProfileGenerator(Path("."))
        generator._profile = result.profile
        data = generator._profile_to_dict(result.profile)
        click.echo(json.dumps(data, indent=2, default=str))
