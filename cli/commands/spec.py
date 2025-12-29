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


def run_clarify(args):
    """Execute CLARIFY contract."""
    print()
    print("=" * 60)
    print("CLARIFY")
    print("=" * 60)

    # Load intake record
    intake_path = Path(args.intake_file)
    if not intake_path.exists():
        print(f"Error: {intake_path} not found")
        print("Run intake first: python execute.py intake --request '...'")
        sys.exit(1)

    with open(intake_path) as f:
        intake_record = yaml.safe_load(f)

    # Load history if exists
    history = []
    history_path = Path('outputs/conversation_history.yaml')
    if history_path.exists():
        with open(history_path) as f:
            history = yaml.safe_load(f) or []

    # Add answer to history if provided
    if args.answer:
        history.append({
            'question': 'Previous question',
            'answer': args.answer,
            'timestamp': datetime.now().isoformat()
        })
        with open(history_path, 'w') as f:
            yaml.dump(history, f, default_flow_style=False)

    inputs = {
        'intake_record': intake_record,
        'conversation_history': history,
    }

    result = execute_contract('spec.clarify.v1', inputs, args.use_api)

    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))

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


def run_analyze(args):
    """Execute ANALYZE contract."""
    print()
    print("=" * 60)
    print("ANALYZE")
    print("=" * 60)

    # Load required files
    intake_path = Path(args.intake_file)
    clarify_path = Path(args.clarification_file)

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

    # Load architecture if exists
    arch_path = Path('config/architecture.yaml')
    architecture_rules = ""
    if arch_path.exists():
        with open(arch_path) as f:
            architecture_rules = f.read()

    # Get code context if project path provided
    code_context = args.code_context or "No code context provided."

    if args.project_path:
        print(f"\n  Retrieving context from: {args.project_path}")
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
            from context_retrieval import ContextRetriever

            retriever = ContextRetriever(args.project_path)

            # Build query from intake record
            query_parts = [
                intake_record.get('detected_intent', ''),
                intake_record.get('detected_scope', ''),
                intake_record.get('original_request', ''),
            ]
            query = ' '.join(part for part in query_parts if part)

            context = retriever.retrieve(query, budget_tokens=6000)

            print(f"  Found {len(context.files)} relevant files")
            print(f"  Found {len(context.symbols)} relevant symbols")
            print(f"  Total tokens: {context.total_tokens}")

            # Format for LLM consumption
            code_context = context.to_prompt_text()

            retriever.shutdown()

        except ImportError as e:
            print(f"  Warning: Context retrieval not available: {e}")
        except Exception as e:
            print(f"  Warning: Context retrieval failed: {e}")

    inputs = {
        'intake_record': intake_record,
        'clarification_log': clarification_log,
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


def run_draft(args):
    """Execute DRAFT contract."""
    print()
    print("=" * 60)
    print("DRAFT")
    print("=" * 60)

    # Load required files
    with open(args.intake_file) as f:
        intake_record = yaml.safe_load(f)
    with open(args.clarification_file) as f:
        clarification_log = yaml.safe_load(f)
    with open(args.analysis_file) as f:
        analysis_report = yaml.safe_load(f)

    inputs = {
        'intake_record': intake_record,
        'clarification_log': clarification_log,
        'analysis_report': analysis_report,
    }

    result = execute_contract('spec.draft.v1', inputs, args.use_api)

    # Draft output is now YAML (specification.schema.yaml)
    output_path = Path('outputs/specification.yaml')

    if isinstance(result, dict) and '_raw' not in result:
        # Successfully parsed as YAML - save it
        with open(output_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"\n✅ Specification saved to: {output_path}")
        print()
        print("-" * 60)
        print("SUMMARY")
        print("-" * 60)

        # Show summary
        metadata = result.get('metadata', {})
        print(f"  Feature: {metadata.get('feature_name', 'Unknown')}")
        print(f"  Version: {metadata.get('version', '1.0')}")
        print(f"  Status: {metadata.get('status', 'draft')}")

        reqs = result.get('requirements', {})
        fr_count = len(reqs.get('functional', []))
        nfr_count = len(reqs.get('non_functional', []))
        entity_count = len(result.get('entities', []))

        print(f"  Functional Requirements: {fr_count}")
        print(f"  Non-Functional Requirements: {nfr_count}")
        print(f"  Entities: {entity_count}")

        print()
        print("Validate schema: python tools/validate_schema.py schemas/specification.schema.yaml outputs/specification.yaml")
        print("Render to markdown: python execute.py render-spec")
        print("Next step: python execute.py validate")

    else:
        # Couldn't parse as YAML - save raw and warn
        raw_path = Path('outputs/specification_raw.txt')
        raw_content = result.get('_raw', str(result)) if isinstance(result, dict) else str(result)
        with open(raw_path, 'w') as f:
            f.write(raw_content)

        print(f"\n⚠️  Could not parse output as YAML")
        print(f"   Raw output saved to: {raw_path}")
        print(f"   Error: {result.get('_parse_error', 'Unknown')}")
        print()
        print("Try re-running the draft step.")


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

    # Load specification - handle both YAML and markdown
    with open(spec_path) as f:
        spec_content = f.read()

    # If YAML, also load as structured data for better validation
    specification_data = None
    if spec_path.suffix in ['.yaml', '.yml']:
        try:
            specification_data = yaml.safe_load(spec_content)
            print(f"  Spec format: YAML (structured)")
        except yaml.YAMLError:
            print(f"  Spec format: YAML (parse failed, using raw)")
    else:
        print(f"  Spec format: Markdown")

    with open(args.analysis_file) as f:
        analysis_report = yaml.safe_load(f)

    arch_path = Path('config/architecture.yaml')
    architecture_rules = ""
    if arch_path.exists():
        with open(arch_path) as f:
            architecture_rules = f.read()

    # Pass both raw content and structured data if available
    inputs = {
        'specification': spec_content,
        'specification_data': specification_data,  # Structured YAML if available
        'analysis_report': analysis_report,
        'architecture_rules': architecture_rules,
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

    verdict = result.get('overall_verdict', 'unknown')
    print("-" * 60)
    print(f"VERDICT: {verdict.upper()}")
    print("-" * 60)

    if verdict == 'approved':
        print("\n✅ Specification approved! Ready for implementation.")
    elif verdict == 'approved_with_notes':
        print("\n✅ Specification approved with conditions.")
        print("   Address approval_conditions before implementation, or run:")
        print("   python execute.py revise")
    elif verdict == 'needs_revision':
        print("\n⚠️  Specification needs revision. Run:")
        print("   python execute.py revise")
        print("   Then re-validate: python execute.py validate")
    else:
        print("\n❌ Specification rejected. Major rework needed.")
        print("   Run: python execute.py revise")
