"""
Revision workflow commands.

Contains the revision workflow for addressing specification issues.
Apply logic is in revision_apply.py.
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime
import uuid
import re

from cli.core import execute_contract, call_claude_code, call_anthropic_api, extract_yaml_from_response


def run_revise(args):
    """
    Revision workflow with session management.

    Modes:
      - Interactive (default): Human makes decisions one by one
      - Autonomous (--auto): Agent makes decisions, flags uncertain ones
      - Continue (--continue): Resume paused session
      - Apply (--apply): Apply all decisions to spec
      - Status (--status): Show session status
    """
    if args.status:
        return show_revision_status()

    if args.apply:
        from cli.commands.revision_apply import apply_revision_session
        return apply_revision_session(args)

    if args.resume:
        return continue_revision_session(args)

    # Check for existing session
    session_path = Path('outputs/revision_session.yaml')
    if session_path.exists() and not args.force:
        _show_existing_session(session_path)
        return

    # Create new session
    session = create_revision_session(args)
    if session is None:
        return

    save_revision_session(session)

    if args.auto:
        run_autonomous_revision(session, args)
    else:
        run_interactive_revision(session, args)


def _show_existing_session(session_path: Path):
    """Show info about existing session."""
    print("\n⚠️  Existing revision session found.\n")
    with open(session_path) as f:
        session = yaml.safe_load(f)
    print(f"  Status: {session.get('status', 'unknown')}")
    print(f"  Issues: {session.get('summary', {}).get('total_issues', '?')}")
    print(f"  Resolved: {session.get('summary', {}).get('resolved', '?')}")
    print("\nOptions:")
    print("  python execute.py revise --continue   # Resume session")
    print("  python execute.py revise --status     # View details")
    print("  python execute.py revise --apply      # Apply decisions")
    print("  python execute.py revise --force      # Start fresh")


def create_revision_session(args) -> dict | None:
    """Create a new revision session from validation report."""
    print("\n" + "=" * 60)
    print("REVISE - Creating Session")
    print("=" * 60)

    spec_path = Path(args.spec_file)
    validation_path = Path(args.validation_file)

    if not spec_path.exists():
        print(f"Error: {spec_path} not found")
        return None
    if not validation_path.exists():
        print(f"Error: {validation_path} not found\nRun 'python execute.py validate' first")
        return None

    with open(spec_path) as f:
        specification = yaml.safe_load(f)
    with open(validation_path) as f:
        validation_report = yaml.safe_load(f)

    issues = _build_issues_list(validation_report)
    if not issues:
        print("\n✅ No issues to address! Specification is clean.")
        return None

    session = {
        'session_id': str(uuid.uuid4())[:8],
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'spec_file': str(spec_path),
        'spec_version': specification.get('metadata', {}).get('version', '1.0'),
        'validation_file': str(validation_path),
        'validation_verdict': validation_report.get('overall_verdict', 'unknown'),
        'mode': 'autonomous' if args.auto else 'interactive',
        'status': 'in_progress',
        'issues': issues,
        'summary': {'total_issues': len(issues), 'resolved': 0, 'deferred': 0, 'pending_human': 0},
        'apply_log': [],
    }

    print(f"\n  Session ID: {session['session_id']}")
    print(f"  Previous verdict: {session['validation_verdict']}")
    print(f"  Total issues: {len(issues)}")
    print(f"  Mode: {'Autonomous' if args.auto else 'Interactive'}")

    return session


def _build_issues_list(validation_report: dict) -> list:
    """Build issues list from validation report."""
    issues = []

    for item in validation_report.get('blocking_issues', []):
        issues.append(_build_issue_entry(item, 'BLOCKING', 'issue_id'))

    for item in validation_report.get('warnings', []):
        issues.append(_build_issue_entry(item, 'WARNING', 'warning_id'))

    for i, cond in enumerate(validation_report.get('approval_conditions', [])):
        cond_str = cond if isinstance(cond, str) else str(cond)
        issues.append({
            'id': f'COND-{i+1}', 'type': 'CONDITION', 'location': 'Approval Conditions',
            'description': cond_str, 'recommendation': '',
            'options': _generate_options('', cond_str), 'decision': None,
        })

    return issues


def _build_issue_entry(item: dict, issue_type: str, id_field: str) -> dict:
    """Build a structured issue entry."""
    return {
        'id': item.get(id_field, item.get('id', f'{issue_type[0]}?')),
        'type': issue_type,
        'location': item.get('location', 'Unknown'),
        'description': item.get('description', ''),
        'recommendation': item.get('recommendation', ''),
        'options': _generate_options(item.get('recommendation', ''), item.get('description', '')),
        'decision': None,
    }


def _generate_options(recommendation: str, description: str) -> list:
    """Generate options for an issue."""
    options = []

    if recommendation:
        # Look for action patterns
        actions = re.findall(r'(?:Add|Use|Set|Change|Include)\s+([^.,]+)', recommendation, re.IGNORECASE)
        for action in actions[:2]:
            action = action.strip()
            if action and len(action) > 5:
                options.append({'id': str(len(options) + 1), 'label': action[:60], 'resolution': action})

    if not options:
        main_text = recommendation[:200] if recommendation else f'Fix: {description[:100]}'
        options.append({'id': '1', 'label': 'Apply fix', 'resolution': main_text})

    options.append({'id': 'skip', 'label': 'Skip - defer to implementation', 'resolution': 'Deferred'})
    options.append({'id': 'custom', 'label': 'Custom resolution...', 'resolution': None})

    return options


def save_revision_session(session: dict):
    """Save revision session to file."""
    session['updated_at'] = datetime.utcnow().isoformat() + 'Z'

    resolved = sum(1 for i in session['issues'] if i.get('decision') and i['decision'].get('selected_option') not in [None, 'skip'])
    deferred = sum(1 for i in session['issues'] if i.get('decision') and i['decision'].get('selected_option') == 'skip')
    pending = sum(1 for i in session['issues'] if i.get('decision') and i['decision'].get('requires_human'))

    session['summary'] = {'total_issues': len(session['issues']), 'resolved': resolved, 'deferred': deferred, 'pending_human': pending}

    with open(Path('outputs/revision_session.yaml'), 'w') as f:
        yaml.dump(session, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def run_interactive_revision(session: dict, args):
    """Interactive mode - human makes decisions."""
    print("\n" + "-" * 60)
    print("INTERACTIVE MODE")
    print("-" * 60)
    print("You will decide how to resolve each issue. Type 'q' to save & quit.\n")

    for idx, issue in enumerate(session['issues']):
        if issue.get('decision') and not issue['decision'].get('requires_human'):
            continue

        if not _handle_issue_interactive(issue, idx, len(session['issues']), session):
            return

    session['status'] = 'ready_to_apply'
    save_revision_session(session)
    _print_summary(session)
    print("\nAll issues addressed! Apply with: python execute.py revise --apply")


def _handle_issue_interactive(issue: dict, idx: int, total: int, session: dict) -> bool:
    """Handle a single issue interactively. Returns False if user quit."""
    _display_issue(issue, idx, total)

    while True:
        try:
            choice = input("Your choice (or 'q' to save & quit): ").strip()
            if choice.lower() == 'q':
                save_revision_session(session)
                print(f"\n✅ Session saved. Resume with: python execute.py revise --continue")
                return False

            selected = next((o for o in issue['options'] if o['id'] == choice), None)
            if selected:
                break
            print(f"Invalid choice. Enter one of: {', '.join(o['id'] for o in issue['options'])}")
        except (EOFError, KeyboardInterrupt):
            save_revision_session(session)
            print(f"\n✅ Session saved. Resume with: python execute.py revise --continue")
            return False

    resolution = selected['resolution']
    if selected['id'] == 'custom':
        print("\nEnter your custom resolution:")
        resolution = input().strip()

    rationale = input("\nBrief rationale (optional): ").strip() or f"Selected: {selected['label']}"

    issue['decision'] = {
        'selected_option': selected['id'], 'decided_by': 'human', 'rationale': rationale,
        'custom_resolution': resolution if selected['id'] == 'custom' else None,
        'requires_human': False, 'timestamp': datetime.utcnow().isoformat() + 'Z',
    }
    print(f"\n  ✓ Recorded: {selected['label']}")
    save_revision_session(session)
    return True


def _display_issue(issue: dict, idx: int, total: int, show_agent_flag: bool = False):
    """Display an issue for user review."""
    print(f"\nIssue {idx + 1} of {total}: {issue['id']} [{issue['type']}]")
    print("━" * 60)

    if show_agent_flag and issue.get('decision', {}).get('requires_human'):
        print(f"\n⚠️  Agent flagged: {issue['decision'].get('human_prompt', 'Needs review')}")

    print(f"\nLocation: {issue['location']}\n")
    print("Problem:")
    for line in issue['description'].strip().split('\n'):
        print(f"  {line}")

    if issue.get('recommendation'):
        print("\nRecommendation:")
        for line in issue['recommendation'].strip().split('\n'):
            print(f"  {line}")

    print("\nOptions:")
    for opt in issue['options']:
        print(f"  [{opt['id']}] {opt['label']}")
    print()


def run_autonomous_revision(session: dict, args):
    """Autonomous mode - agent makes decisions."""
    print("\n" + "-" * 60)
    print("AUTONOMOUS MODE")
    print("-" * 60)
    print("Agent will evaluate each issue. Uncertain decisions flagged for human review.\n")

    for idx, issue in enumerate(session['issues']):
        if issue.get('decision'):
            continue

        print(f"Evaluating {idx + 1}/{len(session['issues'])}: {issue['id']}...", end=' ', flush=True)
        decision = _evaluate_autonomously(issue, args.use_api)
        issue['decision'] = decision

        if decision.get('requires_human'):
            print("⚠️  FLAGGED FOR HUMAN")
        elif decision.get('selected_option') == 'skip':
            print("→ Deferred")
        else:
            print(f"✓ {decision.get('selected_option')}")

        save_revision_session(session)

    pending = [i for i in session['issues'] if i.get('decision', {}).get('requires_human')]

    if pending:
        session['status'] = 'pending_human'
        save_revision_session(session)
        print(f"\n{'=' * 60}\nHUMAN REVIEW REQUIRED\n{'=' * 60}")
        print(f"\n{len(pending)} issue(s) need human review:")
        for issue in pending:
            print(f"  • {issue['id']}: {issue['decision'].get('human_prompt', 'Needs review')[:60]}")
        print("\nReview with: python execute.py revise --continue")
    else:
        session['status'] = 'ready_to_apply'
        save_revision_session(session)
        _print_summary(session)
        print("\nAll resolved! Apply with: python execute.py revise --apply")


def _evaluate_autonomously(issue: dict, use_api: bool) -> dict:
    """Use agent to evaluate an issue."""
    options_text = "\n".join([f"- {o['id']}: {o['label']}" for o in issue['options']])

    system = """Evaluate the specification issue. Output YAML only:
selected_option: "id"
rationale: "reason"
requires_human: true/false
human_prompt: "why needs human (if flagged)"

Flag for human if: architectural decision, ambiguous, or needs domain expertise."""

    user = f"""Issue: {issue['id']} ({issue['type']})
Location: {issue['location']}
Problem: {issue['description']}
Recommendation: {issue.get('recommendation', 'None')}
Options:
{options_text}"""

    try:
        response = call_anthropic_api(system, user, 300, 0.0) if use_api else call_claude_code(system, user)
        decision = yaml.safe_load(extract_yaml_from_response(response))
        if decision:
            decision['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            decision['decided_by'] = 'agent'
            return decision
    except Exception:
        pass

    return {'selected_option': None, 'rationale': 'Failed to evaluate', 'requires_human': True,
            'human_prompt': 'Agent could not evaluate.', 'timestamp': datetime.utcnow().isoformat() + 'Z'}


def continue_revision_session(args):
    """Continue a paused revision session."""
    print("\n" + "=" * 60)
    print("REVISE - Continue Session")
    print("=" * 60)

    session_path = Path('outputs/revision_session.yaml')
    if not session_path.exists():
        print("\nNo session found. Start with: python execute.py revise")
        return

    with open(session_path) as f:
        session = yaml.safe_load(f)

    print(f"\n  Session ID: {session['session_id']}")
    print(f"  Status: {session['status']}")
    _print_summary(session)

    pending = [i for i in session['issues'] if not i.get('decision') or i['decision'].get('requires_human')]

    if not pending:
        session['status'] = 'ready_to_apply'
        save_revision_session(session)
        print("\nAll resolved! Apply with: python execute.py revise --apply")
        return

    print(f"\n{len(pending)} issue(s) need your input:\n")
    session['mode'] = 'interactive'

    for idx, issue in enumerate(pending):
        _display_issue(issue, idx, len(pending), show_agent_flag=True)

        if not _handle_issue_interactive(issue, idx, len(pending), session):
            return

    session['status'] = 'ready_to_apply'
    save_revision_session(session)
    _print_summary(session)
    print("\nAll addressed! Apply with: python execute.py revise --apply")


def show_revision_status():
    """Show current revision session status."""
    print("\n" + "=" * 60)
    print("REVISION SESSION STATUS")
    print("=" * 60)

    session_path = Path('outputs/revision_session.yaml')
    if not session_path.exists():
        print("\nNo active session. Start with: python execute.py revise")
        return

    with open(session_path) as f:
        session = yaml.safe_load(f)

    print(f"\n  Session ID: {session['session_id']}")
    print(f"  Status: {session['status']}")
    print(f"  Mode: {session['mode']}")
    print(f"  Spec: {session['spec_file']} v{session['spec_version']}")
    _print_summary(session)

    print("\n  Issues:")
    for issue in session['issues']:
        d = issue.get('decision', {})
        if d.get('requires_human'):
            status = "⚠️  NEEDS HUMAN"
        elif d.get('selected_option') == 'skip':
            status = "→ Deferred"
        elif d.get('selected_option'):
            status = f"✓ {d['selected_option']}"
        else:
            status = "○ Pending"
        print(f"    {issue['id']}: {status}")

    print("\nCommands:")
    if session['status'] == 'ready_to_apply':
        print("  python execute.py revise --apply")
    else:
        print("  python execute.py revise --continue")


def _print_summary(session: dict):
    """Print session summary."""
    s = session.get('summary', {})
    print(f"\n  Summary: {s.get('resolved', 0)} resolved, {s.get('deferred', 0)} deferred, {s.get('pending_human', 0)} pending")
