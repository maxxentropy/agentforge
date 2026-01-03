"""
SPEC workflow commands.

Contains the core SPEC workflow commands: intake, clarify, analyze, draft, validate.
The render-spec command is in cli/render.py.
The revision commands are in cli/commands/revision.py.
"""

import sys
from datetime import datetime
from pathlib import Path

import click
import yaml

from agentforge.cli.core import execute_contract


def run_intake(args):
    """Execute INTAKE contract."""
    click.echo()
    click.echo("=" * 60)
    click.echo("INTAKE")
    click.echo("=" * 60)

    inputs = {
        'raw_request': args.request,
        'priority': args.priority or 'medium',
    }

    result = execute_contract('spec.intake.v1', inputs, args.use_api)

    # Save output
    output_path = Path('outputs/intake_record.yaml')
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    click.echo(f"\nSaved to: {output_path}")
    click.echo()
    click.echo("-" * 60)
    click.echo("RESULT")
    click.echo("-" * 60)
    click.echo(yaml.dump(result, default_flow_style=False, sort_keys=False))

    # Show next step
    if result.get('detected_scope') == 'unclear' or result.get('initial_questions'):
        questions = result.get('initial_questions', [])
        blocking = [q for q in questions if q.get('priority') == 'blocking']

        if blocking:
            click.echo("-" * 60)
            click.echo("BLOCKING QUESTIONS (answer before proceeding)")
            click.echo("-" * 60)
            for i, q in enumerate(blocking, 1):
                click.echo(f"  {i}. {q.get('question', 'N/A')}")
            click.echo()
            click.echo("Next: python execute.py clarify")


def _load_required_file(path: Path, error_hint: str = ""):
    """Load a required YAML file, exit on failure."""
    if not path.exists():
        click.echo(f"Error: {path} not found")
        if error_hint:
            click.echo(error_hint)
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def _load_conversation_history(args) -> list:
    """Load conversation history and optionally append an answer."""
    history_path = Path('outputs/conversation_history.yaml')
    history = []
    if history_path.exists():
        with open(history_path) as f:
            history = yaml.safe_load(f) or []

    if args.answer:
        history.append({
            'question': 'Previous question',
            'answer': args.answer,
            'timestamp': datetime.now().isoformat()
        })
        with open(history_path, 'w') as f:
            yaml.dump(history, f, default_flow_style=False)
    return history


def _handle_clarify_result(result: dict):
    """Handle clarify result based on mode."""
    mode = result.get('mode', 'unknown')
    if mode == 'question':
        question = result.get('question', {})
        click.echo("-" * 60)
        click.echo("QUESTION FOR YOU")
        click.echo("-" * 60)
        click.echo(f"\n  {question.get('text', 'No question')}\n")
        click.echo("Run with your answer:")
        click.echo("  python execute.py clarify --answer \"your answer here\"")
    elif mode == 'complete':
        output_path = Path('outputs/clarification_log.yaml')
        with open(output_path, 'w') as f:
            yaml.dump(result.get('clarification_log', result), f, default_flow_style=False)
        click.echo(f"\nClarification complete! Saved to: {output_path}")
        click.echo()
        click.echo("Next: python execute.py analyze")


def run_clarify(args):
    """Execute CLARIFY contract."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CLARIFY")
    click.echo("=" * 60)

    intake_record = _load_required_file(
        Path(args.intake_file),
        "Run intake first: python execute.py intake --request '...'"
    )
    history = _load_conversation_history(args)

    inputs = {'intake_record': intake_record, 'conversation_history': history}
    result = execute_contract('spec.clarify.v1', inputs, args.use_api)

    click.echo()
    click.echo("-" * 60)
    click.echo("RESULT")
    click.echo("-" * 60)
    click.echo(yaml.dump(result, default_flow_style=False, sort_keys=False))

    _handle_clarify_result(result)


def _retrieve_context(project_path: str, intake_record: dict) -> str | None:
    """Retrieve code context from project. Returns None on failure."""
    click.echo(f"\n  Retrieving context from: {project_path}")
    try:
        from agentforge.core.context_retrieval import ContextRetriever

        retriever = ContextRetriever(project_path)
        query_parts = [intake_record.get('detected_intent', ''), intake_record.get('detected_scope', ''), intake_record.get('original_request', '')]
        query = ' '.join(part for part in query_parts if part)
        context = retriever.retrieve(query, budget_tokens=6000)

        click.echo(f"  Found {len(context.files)} relevant files")
        click.echo(f"  Found {len(context.symbols)} relevant symbols")
        click.echo(f"  Total tokens: {context.total_tokens}")

        result = context.to_prompt_text()
        retriever.shutdown()
        return result
    except ImportError as e:
        click.echo(f"  Warning: Context retrieval not available: {e}")
    except Exception as e:
        click.echo(f"  Warning: Context retrieval failed: {e}")
    return None


def _load_optional_file(path: Path, default: str = "") -> str:
    """Load file content if exists, otherwise return default."""
    return path.read_text() if path.exists() else default


def _get_code_context(args, intake_record: dict) -> str:
    """Get code context from args or retrieval."""
    if args.project_path:
        return _retrieve_context(args.project_path, intake_record) or args.code_context or "No code context provided."
    return args.code_context or "No code context provided."


def run_analyze(args):
    """Execute ANALYZE contract."""
    click.echo()
    click.echo("=" * 60)
    click.echo("ANALYZE")
    click.echo("=" * 60)

    intake_record = _load_required_file(Path(args.intake_file))
    clarification_log = _load_required_file(Path(args.clarification_file))
    architecture_rules = _load_optional_file(Path('config/architecture.yaml'), "No architecture rules configured.")

    inputs = {
        'intake_record': intake_record, 'clarification_log': clarification_log,
        'architecture_rules': architecture_rules,
        'code_context': _get_code_context(args, intake_record),
    }

    result = execute_contract('spec.analyze.v1', inputs, args.use_api)

    output_path = Path('outputs/analysis_report.yaml')
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    click.echo(f"\nSaved to: {output_path}")
    click.echo()
    click.echo("-" * 60)
    click.echo("RESULT")
    click.echo("-" * 60)
    click.echo(yaml.dump(result, default_flow_style=False, sort_keys=False)[:2000])
    click.echo()
    click.echo("Next: python execute.py draft")


def _print_draft_summary(result: dict):
    """Print draft specification summary."""
    metadata = result.get('metadata', {})
    click.echo(f"  Feature: {metadata.get('feature_name', 'Unknown')}")
    click.echo(f"  Version: {metadata.get('version', '1.0')}")
    click.echo(f"  Status: {metadata.get('status', 'draft')}")

    reqs = result.get('requirements', {})
    click.echo(f"  Functional Requirements: {len(reqs.get('functional', []))}")
    click.echo(f"  Non-Functional Requirements: {len(reqs.get('non_functional', []))}")
    click.echo(f"  Entities: {len(result.get('entities', []))}")


def _save_draft_success(result: dict, output_path: Path):
    """Save successful draft result and print summary."""
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    click.echo(f"\nSpecification saved to: {output_path}")
    click.echo()
    click.echo("-" * 60)
    click.echo("SUMMARY")
    click.echo("-" * 60)
    _print_draft_summary(result)
    click.echo()
    click.echo("Validate schema: python tools/validate_schema.py schemas/specification.schema.yaml outputs/specification.yaml")
    click.echo("Render to markdown: python execute.py render-spec")
    click.echo("Next step: python execute.py validate")


def _save_draft_failure(result):
    """Save failed draft result (raw output)."""
    raw_path = Path('outputs/specification_raw.txt')
    raw_content = result.get('_raw', str(result)) if isinstance(result, dict) else str(result)
    with open(raw_path, 'w') as f:
        f.write(raw_content)

    click.echo("\nCould not parse output as YAML")
    click.echo(f"   Raw output saved to: {raw_path}")
    click.echo(f"   Error: {result.get('_parse_error', 'Unknown')}")
    click.echo()
    click.echo("Try re-running the draft step.")


_LOCATION_KEYS = ['affected_files', 'implementation_locations', 'files', 'locations']
_PATH_DICT_KEYS = ['path', 'location', 'file']


def _extract_path_from_item(item) -> str | None:
    """Extract a src/ path from a string or dict item."""
    if isinstance(item, str) and item.startswith('src/'):
        return item
    if isinstance(item, dict):
        for key in _PATH_DICT_KEYS:
            path = item.get(key)
            if path and path.startswith('src/'):
                return path
    return None


def _extract_locations_from_analysis(analysis_report: dict) -> list:
    """Extract target file locations from analysis report."""
    locations = []
    for key in _LOCATION_KEYS:
        items = analysis_report.get(key, [])
        if isinstance(items, list):
            for item in items:
                path = _extract_path_from_item(item)
                if path:
                    locations.append(path)
    return locations


def _analyze_draft_placement(analysis_report: dict, extend_spec: str, new_spec: bool):
    """Analyze where the drafted spec should be placed."""
    from agentforge.core.spec.placement import (
        PlacementAction,
        PlacementDecision,
        SpecPlacementAnalyzer,
    )

    # If --new-spec flag, always create new
    if new_spec:
        return PlacementDecision(
            action=PlacementAction.CREATE,
            reason="Forced new spec creation (--new-spec flag)",
        )

    analyzer = SpecPlacementAnalyzer()

    # Extract locations from analysis
    target_locations = _extract_locations_from_analysis(analysis_report)

    # Analyze placement
    decision = analyzer.analyze(
        feature_description="Greenfield spec draft",
        target_locations=target_locations,
        explicit_spec_id=extend_spec,
    )

    return decision


def _handle_draft_escalation(decision) -> str:
    """Handle ESCALATE decision by asking user to choose."""
    click.echo()
    click.echo("-" * 60)
    click.echo("SPEC PLACEMENT DECISION NEEDED")
    click.echo("-" * 60)
    click.echo(f"\n  {decision.reason}\n")
    click.echo("  Multiple specs could cover this feature:\n")

    for i, opt in enumerate(decision.options, 1):
        click.echo(f"    [{i}] {opt['spec_id']}")
        desc = opt.get('description', 'No description')
        click.echo(f"        {desc[:60]}")

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


def run_draft(args):
    """Execute DRAFT contract."""
    from agentforge.core.spec.placement import PlacementAction

    click.echo()
    click.echo("=" * 60)
    click.echo("DRAFT")
    click.echo("=" * 60)

    intake_record = _load_required_file(Path(args.intake_file))
    clarification_log = _load_required_file(Path(args.clarification_file))
    analysis_report = _load_required_file(Path(args.analysis_file))

    # === SPEC PLACEMENT ANALYSIS ===
    extend_spec = getattr(args, 'extend_spec', None)
    new_spec = getattr(args, 'new_spec', False)

    click.echo("\n" + "-" * 60)
    click.echo("SPEC PLACEMENT ANALYSIS")
    click.echo("-" * 60)

    decision = _analyze_draft_placement(analysis_report, extend_spec, new_spec)

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
        selected = _handle_draft_escalation(decision)
        if selected:
            target_spec_id = selected
            click.echo(f"\n  User selected: EXTEND {target_spec_id}")
        else:
            click.echo("\n  User selected: CREATE new spec")

    # === BUILD INPUTS ===
    inputs = {
        'intake_record': intake_record,
        'clarification_log': clarification_log,
        'analysis_report': analysis_report,
    }

    # Pass placement decision to contract
    if target_spec_id:
        inputs['extend_spec_id'] = target_spec_id
        inputs['placement_action'] = 'extend'
        click.echo(f"\n  Mode: Extending {target_spec_id}")
    else:
        inputs['placement_action'] = 'create'

    # === EXECUTE DRAFT ===
    click.echo("\n" + "-" * 60)
    click.echo("Generating specification...")
    click.echo("-" * 60)

    result = execute_contract('spec.draft.v1', inputs, args.use_api)
    output_path = Path('outputs/specification.yaml')

    if isinstance(result, dict) and '_raw' not in result:
        _save_draft_success(result, output_path)

        # Show placement info
        if target_spec_id:
            click.echo()
            click.echo("-" * 60)
            click.echo("SPEC EXTENSION")
            click.echo("-" * 60)
            click.echo(f"  This feature will extend: {target_spec_id}")
            click.echo("  Components should be added to the existing spec")
            click.echo("  after validation and approval.")
    else:
        _save_draft_failure(result)


def _load_spec_content(spec_path: Path) -> tuple:
    """Load specification content and optional structured data."""
    spec_content = spec_path.read_text()
    specification_data = None

    if spec_path.suffix in ['.yaml', '.yml']:
        try:
            specification_data = yaml.safe_load(spec_content)
            click.echo("  Spec format: YAML (structured)")
        except yaml.YAMLError:
            click.echo("  Spec format: YAML (parse failed, using raw)")
    else:
        click.echo("  Spec format: Markdown")

    return spec_content, specification_data


def _print_verdict(verdict: str):
    """Print verdict message based on validation result."""
    click.echo("-" * 60)
    click.echo(f"VERDICT: {verdict.upper()}")
    click.echo("-" * 60)

    messages = {
        'approved': "\nSpecification approved! Ready for implementation.",
        'approved_with_notes': "\nSpecification approved with conditions.\n   Address approval_conditions before implementation, or run:\n   python execute.py revise",
        'needs_revision': "\nSpecification needs revision. Run:\n   python execute.py revise\n   Then re-validate: python execute.py validate",
    }
    click.echo(messages.get(verdict, "\nSpecification rejected. Major rework needed.\n   Run: python execute.py revise"))


def run_validate(args):
    """Execute VALIDATE contract."""
    click.echo()
    click.echo("=" * 60)
    click.echo("VALIDATE")
    click.echo("=" * 60)

    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        click.echo(f"Error: {spec_path} not found")
        click.echo("Run 'python execute.py draft' first")
        sys.exit(1)

    spec_content, specification_data = _load_spec_content(spec_path)

    with open(args.analysis_file) as f:
        analysis_report = yaml.safe_load(f)

    arch_path = Path('config/architecture.yaml')
    architecture_rules = arch_path.read_text() if arch_path.exists() else ""

    inputs = {
        'specification': spec_content, 'specification_data': specification_data,
        'analysis_report': analysis_report, 'architecture_rules': architecture_rules,
    }

    result = execute_contract('spec.validate.v1', inputs, args.use_api)

    output_path = Path('outputs/validation_report.yaml')
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    click.echo(f"\nSaved to: {output_path}")
    click.echo()
    click.echo("-" * 60)
    click.echo("RESULT")
    click.echo("-" * 60)
    click.echo(yaml.dump(result, default_flow_style=False, sort_keys=False))

    _print_verdict(result.get('overall_verdict', 'unknown'))
