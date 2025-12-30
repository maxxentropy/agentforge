"""
SPEC workflow commands.

Contains the core SPEC workflow commands: intake, clarify, analyze, draft, validate.
The render-spec command is in cli/render.py.
The revision commands are in cli/commands/revision.py.
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

from cli.core import execute_contract


def run_intake(args):
    """Execute INTAKE contract."""
    print()
    print("=" * 60)
    print("INTAKE")
    print("=" * 60)

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

    print(f"\n✅ Saved to: {output_path}")
    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))

    # Show next step
    if result.get('detected_scope') == 'unclear' or result.get('initial_questions'):
        questions = result.get('initial_questions', [])
        blocking = [q for q in questions if q.get('priority') == 'blocking']

        if blocking:
            print("-" * 60)
            print("BLOCKING QUESTIONS (answer before proceeding)")
            print("-" * 60)
            for i, q in enumerate(blocking, 1):
                print(f"  {i}. {q.get('question', 'N/A')}")
            print()
            print("Next: python execute.py clarify")


def _load_required_file(path: Path, error_hint: str = ""):
    """Load a required YAML file, exit on failure."""
    if not path.exists():
        print(f"Error: {path} not found")
        if error_hint:
            print(error_hint)
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
        print("-" * 60)
        print("QUESTION FOR YOU")
        print("-" * 60)
        print(f"\n  {question.get('text', 'No question')}\n")
        print("Run with your answer:")
        print(f"  python execute.py clarify --answer \"your answer here\"")
    elif mode == 'complete':
        output_path = Path('outputs/clarification_log.yaml')
        with open(output_path, 'w') as f:
            yaml.dump(result.get('clarification_log', result), f, default_flow_style=False)
        print(f"\n✅ Clarification complete! Saved to: {output_path}")
        print()
        print("Next: python execute.py analyze")


def run_clarify(args):
    """Execute CLARIFY contract."""
    print()
    print("=" * 60)
    print("CLARIFY")
    print("=" * 60)

    intake_record = _load_required_file(
        Path(args.intake_file),
        "Run intake first: python execute.py intake --request '...'"
    )
    history = _load_conversation_history(args)

    inputs = {'intake_record': intake_record, 'conversation_history': history}
    result = execute_contract('spec.clarify.v1', inputs, args.use_api)

    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))

    _handle_clarify_result(result)


def _retrieve_context(project_path: str, intake_record: dict) -> str | None:
    """Retrieve code context from project. Returns None on failure."""
    print(f"\n  Retrieving context from: {project_path}")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
        from context_retrieval import ContextRetriever

        retriever = ContextRetriever(project_path)
        query_parts = [intake_record.get('detected_intent', ''), intake_record.get('detected_scope', ''), intake_record.get('original_request', '')]
        query = ' '.join(part for part in query_parts if part)
        context = retriever.retrieve(query, budget_tokens=6000)

        print(f"  Found {len(context.files)} relevant files")
        print(f"  Found {len(context.symbols)} relevant symbols")
        print(f"  Total tokens: {context.total_tokens}")

        result = context.to_prompt_text()
        retriever.shutdown()
        return result
    except ImportError as e:
        print(f"  Warning: Context retrieval not available: {e}")
    except Exception as e:
        print(f"  Warning: Context retrieval failed: {e}")
    return None


def run_analyze(args):
    """Execute ANALYZE contract."""
    print()
    print("=" * 60)
    print("ANALYZE")
    print("=" * 60)

    intake_path, clarify_path = Path(args.intake_file), Path(args.clarification_file)
    if not intake_path.exists():
        print(f"Error: {intake_path} not found")
        sys.exit(1)
    if not clarify_path.exists():
        print(f"Error: {clarify_path} not found")
        sys.exit(1)

    with open(intake_path) as f:
        intake_record = yaml.safe_load(f)
    with open(clarify_path) as f:
        clarification_log = yaml.safe_load(f)

    arch_path = Path('config/architecture.yaml')
    architecture_rules = arch_path.read_text() if arch_path.exists() else ""

    code_context = args.code_context or "No code context provided."
    if args.project_path:
        code_context = _retrieve_context(args.project_path, intake_record) or code_context

    inputs = {
        'intake_record': intake_record, 'clarification_log': clarification_log,
        'architecture_rules': architecture_rules or "No architecture rules configured.",
        'code_context': code_context,
    }

    result = execute_contract('spec.analyze.v1', inputs, args.use_api)

    output_path = Path('outputs/analysis_report.yaml')
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Saved to: {output_path}")
    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False)[:2000])
    print()
    print("Next: python execute.py draft")


def _print_draft_summary(result: dict):
    """Print draft specification summary."""
    metadata = result.get('metadata', {})
    print(f"  Feature: {metadata.get('feature_name', 'Unknown')}")
    print(f"  Version: {metadata.get('version', '1.0')}")
    print(f"  Status: {metadata.get('status', 'draft')}")

    reqs = result.get('requirements', {})
    print(f"  Functional Requirements: {len(reqs.get('functional', []))}")
    print(f"  Non-Functional Requirements: {len(reqs.get('non_functional', []))}")
    print(f"  Entities: {len(result.get('entities', []))}")


def _save_draft_success(result: dict, output_path: Path):
    """Save successful draft result and print summary."""
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\n✅ Specification saved to: {output_path}")
    print()
    print("-" * 60)
    print("SUMMARY")
    print("-" * 60)
    _print_draft_summary(result)
    print()
    print("Validate schema: python tools/validate_schema.py schemas/specification.schema.yaml outputs/specification.yaml")
    print("Render to markdown: python execute.py render-spec")
    print("Next step: python execute.py validate")


def _save_draft_failure(result):
    """Save failed draft result (raw output)."""
    raw_path = Path('outputs/specification_raw.txt')
    raw_content = result.get('_raw', str(result)) if isinstance(result, dict) else str(result)
    with open(raw_path, 'w') as f:
        f.write(raw_content)

    print(f"\n⚠️  Could not parse output as YAML")
    print(f"   Raw output saved to: {raw_path}")
    print(f"   Error: {result.get('_parse_error', 'Unknown')}")
    print()
    print("Try re-running the draft step.")


def run_draft(args):
    """Execute DRAFT contract."""
    print()
    print("=" * 60)
    print("DRAFT")
    print("=" * 60)

    inputs = {
        'intake_record': _load_required_file(Path(args.intake_file)),
        'clarification_log': _load_required_file(Path(args.clarification_file)),
        'analysis_report': _load_required_file(Path(args.analysis_file)),
    }

    result = execute_contract('spec.draft.v1', inputs, args.use_api)
    output_path = Path('outputs/specification.yaml')

    if isinstance(result, dict) and '_raw' not in result:
        _save_draft_success(result, output_path)
    else:
        _save_draft_failure(result)


def _load_spec_content(spec_path: Path) -> tuple:
    """Load specification content and optional structured data."""
    spec_content = spec_path.read_text()
    specification_data = None

    if spec_path.suffix in ['.yaml', '.yml']:
        try:
            specification_data = yaml.safe_load(spec_content)
            print(f"  Spec format: YAML (structured)")
        except yaml.YAMLError:
            print(f"  Spec format: YAML (parse failed, using raw)")
    else:
        print(f"  Spec format: Markdown")

    return spec_content, specification_data


def _print_verdict(verdict: str):
    """Print verdict message based on validation result."""
    print("-" * 60)
    print(f"VERDICT: {verdict.upper()}")
    print("-" * 60)

    messages = {
        'approved': "\n✅ Specification approved! Ready for implementation.",
        'approved_with_notes': "\n✅ Specification approved with conditions.\n   Address approval_conditions before implementation, or run:\n   python execute.py revise",
        'needs_revision': "\n⚠️  Specification needs revision. Run:\n   python execute.py revise\n   Then re-validate: python execute.py validate",
    }
    print(messages.get(verdict, "\n❌ Specification rejected. Major rework needed.\n   Run: python execute.py revise"))


def run_validate(args):
    """Execute VALIDATE contract."""
    print()
    print("=" * 60)
    print("VALIDATE")
    print("=" * 60)

    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"Error: {spec_path} not found")
        print("Run 'python execute.py draft' first")
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

    print(f"\n✅ Saved to: {output_path}")
    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))

    _print_verdict(result.get('overall_verdict', 'unknown'))
