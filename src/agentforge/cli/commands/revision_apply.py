"""
Revision apply logic.

Contains the apply_revision_session function for applying revision decisions to specifications.
"""

import shutil
from datetime import datetime
from pathlib import Path

import click
import yaml

from agentforge.cli.commands.revision import save_revision_session
from agentforge.cli.core import call_anthropic_api, call_claude_code, extract_yaml_from_response


def apply_revision_session(args):
    """Apply all decisions from revision session to specification."""
    click.echo("\n" + "=" * 60)
    click.echo("REVISE - Apply Decisions")
    click.echo("=" * 60)

    session_path = Path('outputs/revision_session.yaml')
    if not session_path.exists():
        click.echo("\nNo revision session found. Start with: python execute.py revise")
        return

    with open(session_path) as f:
        session = yaml.safe_load(f)

    # Check status
    if session['status'] == 'pending_human':
        click.echo("\nSome issues need human review first.")
        click.echo("Run: python execute.py revise --continue")
        return
    if session['status'] == 'applied':
        click.echo("\nSession already applied.")
        return

    # Check for unresolved issues
    unresolved = [i for i in session['issues'] if not i.get('decision') or i['decision'].get('requires_human')]
    if unresolved:
        click.echo(f"\n{len(unresolved)} issue(s) still need decisions.")
        click.echo("Run: python execute.py revise --continue")
        return

    _print_summary(session)

    # Build revision instructions from decisions
    to_apply, to_defer = _build_revision_lists(session)

    click.echo(f"\n  Will apply {len(to_apply)} change(s), defer {len(to_defer)}.")

    if not to_apply:
        click.echo("\nNo changes to apply (all deferred).")
        session['status'] = 'applied'
        save_revision_session(session)
        return

    # Confirm
    click.echo()
    confirm = input("Apply these changes to specification? (y/n): ").strip().lower()
    if confirm != 'y':
        click.echo("\nAborted. Session preserved.")
        return

    _execute_apply(session, to_apply, to_defer, args)


def _build_revision_lists(session: dict) -> tuple:
    """Build lists of changes to apply and defer."""
    to_apply = []
    to_defer = []

    for issue in session['issues']:
        decision = issue['decision']
        if decision['selected_option'] == 'skip':
            to_defer.append({
                'issue_id': issue['id'],
                'reason': decision.get('rationale', 'Deferred'),
            })
        else:
            resolution = decision.get('custom_resolution') or next(
                (o['resolution'] for o in issue['options'] if o['id'] == decision['selected_option']),
                decision.get('rationale', '')
            )
            to_apply.append({
                'issue_id': issue['id'],
                'location': issue['location'],
                'resolution': resolution,
                'decided_by': decision['decided_by'],
                'rationale': decision.get('rationale', ''),
            })

    return to_apply, to_defer


def _build_revision_notes(session: dict, to_apply: list, to_defer: list) -> dict:
    """Build revision notes to embed in the spec."""
    return {
        'revision_version': _increment_version(session['spec_version']),
        'session_id': session['session_id'],
        'previous_verdict': session['validation_verdict'],
        'issues_addressed': [
            {'id': r['issue_id'], 'action': r['resolution'][:50], 'decided_by': r['decided_by']}
            for r in to_apply
        ],
        'issues_deferred': [
            {'id': d['issue_id'], 'reason': d['reason']}
            for d in to_defer
        ],
    }


def _save_apply_success(result: dict, spec_path: Path, session: dict, to_apply: list, to_defer: list):
    """Save successful apply result and update session."""
    backup_path = spec_path.with_suffix('.yaml.bak')
    shutil.copy(spec_path, backup_path)
    click.echo(f"\n  Backed up: {backup_path}")

    result['_revision_notes'] = _build_revision_notes(session, to_apply, to_defer)

    with open(spec_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    session['status'] = 'applied'
    session['apply_log'].append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': 'applied',
        'changes': len(to_apply),
        'deferred': len(to_defer),
    })
    save_revision_session(session)

    click.echo(f"\nSpecification updated: {spec_path}")
    click.echo("\n" + "-" * 60)
    click.echo("NEXT STEPS")
    click.echo("-" * 60)
    click.echo(f"  1. Review: diff {backup_path} {spec_path}")
    click.echo("  2. Re-validate: python execute.py validate")


def _execute_apply(session: dict, to_apply: list, to_defer: list, args):
    """Execute the application of revisions."""
    spec_path = Path(session['spec_file'])
    with open(spec_path) as f:
        specification = yaml.safe_load(f)

    revision_text = _build_apply_instructions(to_apply, to_defer)

    click.echo("\n" + "-" * 60)
    click.echo("APPLYING CHANGES")
    click.echo("-" * 60)
    click.echo("  Mode:", "Anthropic API" if args.use_api else "Claude Code CLI")

    result = _execute_apply_revision(
        yaml.dump(specification, default_flow_style=False, sort_keys=False),
        revision_text,
        args.use_api
    )

    if isinstance(result, dict) and '_raw' not in result:
        _save_apply_success(result, spec_path, session, to_apply, to_defer)
    else:
        click.echo("\nFailed to apply changes.")
        click.echo("   Session preserved. Try again or apply manually.")


def _build_apply_instructions(to_apply: list, to_defer: list) -> str:
    """Build instructions for applying revisions."""
    lines = ["# Revision Instructions", "", "Apply these specific changes to the specification:", ""]

    for r in to_apply:
        lines.append(f"## {r['issue_id']} at {r['location']}")
        lines.append(f"Resolution: {r['resolution']}")
        lines.append(f"Rationale: {r['rationale']}")
        lines.append("")

    if to_defer:
        lines.append("## Deferred (no changes):")
        for d in to_defer:
            lines.append(f"- {d['issue_id']}: {d['reason']}")
        lines.append("")

    lines.extend([
        "# Rules",
        "- Apply ONLY the changes listed",
        "- Preserve all other content",
        "- Use literal blocks (|) for multiline",
        "- Output complete YAML starting with 'metadata:'",
    ])

    return '\n'.join(lines)


def _execute_apply_revision(spec_yaml: str, instructions: str, use_api: bool) -> dict:
    """Execute the revision application."""
    system = """Apply the requested changes to the specification.
Output the complete revised specification as valid YAML.
Start with "metadata:" - no preamble or explanation."""

    user = f"""# Current Specification

```yaml
{spec_yaml}
```

{instructions}

Output the complete revised YAML specification:"""

    if use_api:
        response = call_anthropic_api(system, user, max_tokens=12000, temperature=0.0)
    else:
        response = call_claude_code(system, user)

    yaml_content = extract_yaml_from_response(response)

    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        return {"_raw": response}


def _increment_version(version: str) -> str:
    """Increment patch version."""
    parts = version.split('.')
    if len(parts) >= 2:
        parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)


def _print_summary(session: dict):
    """Print session summary."""
    s = session.get('summary', {})
    click.echo(f"\n  Summary: {s.get('resolved', 0)} resolved, {s.get('deferred', 0)} deferred, {s.get('pending_human', 0)} pending")
