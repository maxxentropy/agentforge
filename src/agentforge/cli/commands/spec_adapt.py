# @spec_file: .agentforge/specs/cli-v1.yaml
# @spec_id: cli-v1
# @component_id: cli-spec-adapt
# @test_path: tests/unit/cli/test_spec_adapt.py

"""
SPEC.ADAPT command implementation.

Adapts external specifications to AgentForge codebase conventions.
This is the ON-RAMP for external specs - it transforms them into
canonical format compatible with VALIDATE → REVISE → TDFLOW.

Includes spec placement analysis to prevent fragmentation:
- Analyzes existing spec space before creating new specs
- Recommends extending existing specs when appropriate
- Escalates to user when multiple valid options exist
"""

from pathlib import Path
from typing import Any

import click
import yaml

from agentforge.cli.core import execute_contract
from agentforge.core.spec.placement import (
    PlacementAction,
    PlacementDecision,
    SpecPlacementAnalyzer,
)


def _load_external_spec(input_file: str) -> str:
    """Load external specification content."""
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"External spec not found: {path}")
    return path.read_text()


def _load_codebase_profile(profile_path: str) -> dict[str, Any]:
    """Load codebase profile for context. Returns empty dict if not found."""
    path = Path(profile_path)
    if not path.exists():
        click.echo(f"  Note: Codebase profile not found at {path}")
        click.echo("  Run 'agentforge discover' first for better adaptation")
        return {}

    with open(path) as f:
        return yaml.safe_load(f) or {}


def _get_existing_spec_ids() -> list[str]:
    """Get list of existing spec IDs to ensure uniqueness."""
    specs_dir = Path('.agentforge/specs')
    if not specs_dir.exists():
        return []

    spec_ids = []
    for spec_file in specs_dir.glob('*.yaml'):
        try:
            with open(spec_file) as f:
                spec = yaml.safe_load(f)
                if spec and 'spec_id' in spec:
                    spec_ids.append(spec['spec_id'])
        except (OSError, yaml.YAMLError):
            continue

    return spec_ids


def _build_adapt_inputs(
    external_spec: str,
    profile: dict[str, Any],
    existing_spec_ids: list[str],
    original_file: str,
) -> dict[str, Any]:
    """Build inputs for the adapt contract."""
    return {
        'external_spec_content': external_spec,
        'codebase_profile': yaml.dump(profile, default_flow_style=False) if profile else "No codebase profile available.",
        'existing_spec_ids': ', '.join(existing_spec_ids) if existing_spec_ids else "No existing specs.",
        'original_file_path': original_file,
    }


def _save_adapted_spec(result: dict[str, Any], output_path: Path) -> bool:
    """Save adapted specification. Returns True on success."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if result is valid
    if isinstance(result, dict) and '_raw' not in result:
        with open(output_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return True

    # Save raw output for debugging
    raw_path = output_path.with_suffix('.raw.txt')
    raw_content = result.get('_raw', str(result)) if isinstance(result, dict) else str(result)
    with open(raw_path, 'w') as f:
        f.write(raw_content)

    click.echo("\nCould not parse adapted spec as YAML")
    click.echo(f"Raw output saved to: {raw_path}")
    return False


def _extract_target_locations(external_spec: str) -> list[str]:
    """
    Extract target locations from external spec content.

    Looks for patterns like:
    - Location: src/agentforge/...
    - location: src/...
    - File: src/...
    """
    import re
    locations = []

    # Pattern for explicit location declarations
    patterns = [
        r'[Ll]ocation:\s*(src/[^\s\n]+)',
        r'[Ff]ile:\s*(src/[^\s\n]+)',
        r'`(src/agentforge/[^`]+\.py)`',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, external_spec)
        locations.extend(matches)

    return list(set(locations))


def _analyze_placement(
    external_spec: str,
    extend_spec: str | None,
    new_spec: bool,
) -> PlacementDecision:
    """
    Analyze where this feature should be placed in the spec space.

    Args:
        external_spec: External spec content
        extend_spec: Explicit spec to extend (from --extend-spec flag)
        new_spec: Force new spec creation (from --new-spec flag)

    Returns:
        PlacementDecision indicating what to do
    """
    analyzer = SpecPlacementAnalyzer()

    # Extract target locations from spec
    target_locations = _extract_target_locations(external_spec)

    # If --new-spec flag, always create new
    if new_spec:
        return PlacementDecision(
            action=PlacementAction.CREATE,
            reason="Forced new spec creation (--new-spec flag)",
            suggested_spec_id=None,
        )

    # Analyze placement
    decision = analyzer.analyze(
        feature_description="External spec adaptation",
        target_locations=target_locations,
        explicit_spec_id=extend_spec,
    )

    return decision


def _handle_escalation(decision: PlacementDecision) -> str | None:
    """
    Handle ESCALATE decision by asking user to choose.

    Returns:
        Selected spec_id or None if user wants new spec
    """
    click.echo()
    click.echo("-" * 60)
    click.echo("SPEC PLACEMENT DECISION NEEDED")
    click.echo("-" * 60)
    click.echo(f"\n  {decision.reason}\n")
    click.echo("  Multiple specs could cover this feature:\n")

    for i, opt in enumerate(decision.options, 1):
        click.echo(f"    [{i}] {opt['spec_id']}")
        click.echo(f"        {opt.get('description', 'No description')[:60]}")

    click.echo("    [N] Create NEW spec")
    click.echo()

    while True:
        choice = click.prompt("  Select option", type=str)

        if choice.upper() == 'N':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(decision.options):
                return decision.options[idx]['spec_id']
        except ValueError:
            pass

        click.echo("  Invalid choice. Try again.")


def _print_adaptation_summary(result: dict[str, Any], input_file: str):
    """Print summary of the adaptation."""
    metadata = result.get('metadata', {})
    components = result.get('components', [])
    requirements = result.get('requirements', {})

    click.echo()
    click.echo("-" * 60)
    click.echo("ADAPTATION SUMMARY")
    click.echo("-" * 60)
    click.echo(f"  Source: {input_file}")
    click.echo(f"  Feature: {metadata.get('feature_name', 'Unknown')}")
    click.echo(f"  Spec ID: {result.get('spec_id', 'Unknown')}")
    click.echo()
    click.echo(f"  Components: {len(components)}")
    for comp in components[:5]:  # Show first 5
        click.echo(f"    - {comp.get('name', 'Unknown')} → {comp.get('location', 'Unknown')}")
    if len(components) > 5:
        click.echo(f"    ... and {len(components) - 5} more")
    click.echo()
    click.echo(f"  Functional Requirements: {len(requirements.get('functional', []))}")
    click.echo(f"  Non-Functional Requirements: {len(requirements.get('non_functional', []))}")


def run_adapt(args):
    """
    Execute ADAPT phase - transform external spec to AgentForge format.

    This is the ON-RAMP for external specifications. It:
    - Takes a rich external spec as PRIMARY INPUT
    - Analyzes spec space to prevent fragmentation
    - Uses SA agent (via contract) to map concepts to codebase reality
    - Produces a canonical draft compatible with VALIDATE/REVISE/TDFLOW
    """
    click.echo()
    click.echo("=" * 60)
    click.echo("ADAPT - External Spec On-Ramp")
    click.echo("=" * 60)

    # Load inputs
    click.echo(f"\n  Loading external spec: {args.input_file}")
    external_spec = _load_external_spec(args.input_file)
    click.echo(f"  Spec size: {len(external_spec)} characters")

    # === SPEC PLACEMENT ANALYSIS ===
    click.echo("\n" + "-" * 60)
    click.echo("SPEC PLACEMENT ANALYSIS")
    click.echo("-" * 60)

    extend_spec = getattr(args, 'extend_spec', None)
    new_spec = getattr(args, 'new_spec', False)

    decision = _analyze_placement(external_spec, extend_spec, new_spec)

    target_spec_id = None
    if decision.action == PlacementAction.EXTEND:
        click.echo("\n  Decision: EXTEND existing spec")
        click.echo(f"  Spec: {decision.spec_id}")
        click.echo(f"  Reason: {decision.reason}")
        target_spec_id = decision.spec_id

    elif decision.action == PlacementAction.CREATE:
        click.echo("\n  Decision: CREATE new spec")
        if decision.suggested_spec_id:
            click.echo(f"  Suggested ID: {decision.suggested_spec_id}")
        click.echo(f"  Reason: {decision.reason}")

    elif decision.action == PlacementAction.ESCALATE:
        # Ask user to decide
        selected = _handle_escalation(decision)
        if selected:
            target_spec_id = selected
            click.echo(f"\n  User selected: EXTEND {target_spec_id}")
        else:
            click.echo("\n  User selected: CREATE new spec")

    # === LOAD CONTEXT ===
    click.echo(f"\n  Loading codebase profile: {args.profile}")
    profile = _load_codebase_profile(args.profile)
    if profile:
        click.echo(f"  Profile loaded: {len(profile)} sections")

    click.echo("\n  Checking existing specs for ID uniqueness...")
    existing_spec_ids = _get_existing_spec_ids()
    click.echo(f"  Found {len(existing_spec_ids)} existing specs")

    # Build contract inputs
    inputs = _build_adapt_inputs(
        external_spec=external_spec,
        profile=profile,
        existing_spec_ids=existing_spec_ids,
        original_file=args.input_file,
    )

    # Pass placement decision to contract
    if target_spec_id:
        inputs['extend_spec_id'] = target_spec_id
        inputs['placement_action'] = 'extend'
        click.echo(f"\n  Mode: Extending {target_spec_id}")
    else:
        inputs['placement_action'] = 'create'

    # Override spec_id if provided via old flag (backwards compat)
    if args.spec_id:
        inputs['override_spec_id'] = args.spec_id
        click.echo(f"\n  Using override spec_id: {args.spec_id}")

    # Skip review note
    if args.skip_review:
        click.echo("\n  Note: SA review skipped (--skip-review flag)")
        inputs['skip_review'] = True

    # === EXECUTE ADAPTATION ===
    click.echo("\n" + "-" * 60)
    click.echo("Adapting external spec to AgentForge format...")
    click.echo("-" * 60)

    result = execute_contract('spec.adapt.v1', inputs, args.use_api)

    # Save output
    output_path = Path(args.output)
    if _save_adapted_spec(result, output_path):
        click.echo(f"\nAdapted specification saved to: {output_path}")
        _print_adaptation_summary(result, args.input_file)

        # Show placement info
        if target_spec_id:
            click.echo()
            click.echo("-" * 60)
            click.echo("SPEC EXTENSION")
            click.echo("-" * 60)
            click.echo(f"  This feature will extend: {target_spec_id}")
            click.echo("  Components should be added to the existing spec")
            click.echo("  after validation and approval.")

        # Show next steps
        click.echo()
        click.echo("-" * 60)
        click.echo("NEXT STEPS")
        click.echo("-" * 60)
        click.echo("  1. Review the adapted spec:")
        click.echo(f"     cat {output_path}")
        click.echo()
        click.echo("  2. Validate the spec:")
        click.echo(f"     agentforge validate --spec-file {output_path}")
        click.echo()
        click.echo("  3. Revise if needed:")
        click.echo(f"     agentforge revise --spec-file {output_path}")
        click.echo()
        click.echo("  4. Implement with TDFLOW:")
        click.echo(f"     agentforge tdflow start --spec {output_path}")
    else:
        click.echo("\nAdaptation failed. Check the raw output for details.")
        raise SystemExit(1)
