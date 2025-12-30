#!/usr/bin/env python3
"""
Contract Runner Commands
========================

CLI command handlers for run_contract.py.

Extracted from run_contract.py for modularity.
"""

import sys
import yaml
from pathlib import Path


def _save_prompt_files(runner, prompt_data, contract_id: str):
    """Save prompt and copy-paste friendly files. Returns paths."""
    filepath = runner.save_prompt(prompt_data, contract_id)

    base = filepath.parent / filepath.stem
    system_file = Path(str(base) + "_SYSTEM.txt")
    user_file = Path(str(base) + "_USER.txt")

    with open(system_file, 'w') as f:
        f.write(prompt_data['prompt']['system'])
    with open(user_file, 'w') as f:
        f.write(prompt_data['prompt']['user'])

    return filepath, system_file, user_file


def _print_prompt(prompt_data, show_full_instructions: bool = False):
    """Print prompt content to stdout."""
    if show_full_instructions:
        print(f"\n{'=' * 70}")
        print("SYSTEM MESSAGE — Copy everything below until the next ====")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['system'])
        print(f"\n{'=' * 70}")
        print("USER MESSAGE — Copy everything below until the next ====")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['user'])
        print(f"\n{'=' * 70}")
        print("END — Paste the above into Claude, then save response as YAML")
        print(f"{'=' * 70}")
    else:
        print(f"\n{'=' * 70}")
        print("SYSTEM MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['system'])
        print(f"\n{'=' * 70}")
        print("USER MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['user'])
        print(f"\n{'=' * 70}")


def run_intake(args, runner):
    """Run INTAKE contract."""
    contract = runner.load_contract('spec.intake.v1')

    inputs = {
        'raw_request': args.request,
        'priority': args.priority or 'medium',
    }

    if args.constraints:
        inputs['constraints'] = args.constraints

    prompt_data = runner.assemble_prompt(contract, inputs)

    filepath, system_file, user_file = _save_prompt_files(runner, prompt_data, 'spec.intake.v1')
    print(f"\n✅ Prompt saved to: {filepath}")

    print(f"""
{'=' * 70}
USAGE (Claude.ai)
{'=' * 70}

Option 1: Copy from files
  1. Copy contents of: {system_file.name}
     → Paste as System Prompt (or at start of message)
  2. Copy contents of: {user_file.name}
     → Paste as your message
  3. Save Claude's response to: outputs/intake_record.yaml

Option 2: Use --print-prompt flag to see content directly

Then validate: python run_contract.py validate-output spec.intake.v1 outputs/intake_record.yaml
""")

    if args.print_prompt:
        _print_prompt(prompt_data, show_full_instructions=True)


def run_clarify(args, runner):
    """Run CLARIFY contract."""
    contract = runner.load_contract('spec.clarify.v1')

    with open(args.intake_file) as f:
        intake_record = yaml.safe_load(f)

    conversation_history = []
    if args.history_file and Path(args.history_file).exists():
        with open(args.history_file) as f:
            conversation_history = yaml.safe_load(f) or []

    inputs = {
        'intake_record': intake_record,
        'conversation_history': conversation_history,
    }

    prompt_data = runner.assemble_prompt(contract, inputs)

    filepath, system_file, user_file = _save_prompt_files(runner, prompt_data, 'spec.clarify.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    print(f"   Also created: {system_file.name}, {user_file.name}")

    if args.print_prompt:
        _print_prompt(prompt_data)


def run_analyze(args, runner):
    """Run ANALYZE contract."""
    contract = runner.load_contract('spec.analyze.v1')

    with open(args.intake_file) as f:
        intake_record = yaml.safe_load(f)

    with open(args.clarification_file) as f:
        clarification_log = yaml.safe_load(f)

    architecture_rules = "No architecture rules configured."
    if args.architecture_file and Path(args.architecture_file).exists():
        with open(args.architecture_file) as f:
            architecture_rules = f.read()

    inputs = {
        'intake_record': intake_record,
        'clarification_log': clarification_log,
        'architecture_rules': architecture_rules,
        'code_context': args.code_context or "No code context provided.",
    }

    prompt_data = runner.assemble_prompt(contract, inputs)

    filepath, system_file, user_file = _save_prompt_files(runner, prompt_data, 'spec.analyze.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    print(f"   Also created: {system_file.name}, {user_file.name}")

    if args.print_prompt:
        _print_prompt(prompt_data)


def run_draft(args, runner):
    """Run DRAFT contract."""
    contract = runner.load_contract('spec.draft.v1')

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

    prompt_data = runner.assemble_prompt(contract, inputs)

    filepath, system_file, user_file = _save_prompt_files(runner, prompt_data, 'spec.draft.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    print(f"   Also created: {system_file.name}, {user_file.name}")

    if args.print_prompt:
        _print_prompt(prompt_data)


def run_validate(args, runner):
    """Run VALIDATE contract."""
    contract = runner.load_contract('spec.validate.v1')

    with open(args.spec_file) as f:
        specification = f.read()

    with open(args.analysis_file) as f:
        analysis_report = yaml.safe_load(f)

    architecture_rules = ""
    if args.architecture_file and Path(args.architecture_file).exists():
        with open(args.architecture_file) as f:
            architecture_rules = f.read()

    inputs = {
        'specification': specification,
        'analysis_report': analysis_report,
        'architecture_rules': architecture_rules,
    }

    prompt_data = runner.assemble_prompt(contract, inputs)

    filepath, system_file, user_file = _save_prompt_files(runner, prompt_data, 'spec.validate.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    print(f"   Also created: {system_file.name}, {user_file.name}")

    if args.print_prompt:
        _print_prompt(prompt_data)


def validate_contract(args, ContractValidator, ContractValidationReport):
    """Validate a contract file."""
    if ContractValidator is None:
        print("Error: Validation requires jsonschema. Install with:")
        print("  pip install jsonschema")
        sys.exit(1)

    from pathlib import Path as P
    schema_path = P(__file__).parent / 'schemas' / 'prompt-contract.schema.yaml'

    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)

    validator = ContractValidator(schema_path)
    report = validator.validate_contract(P(args.contract_file))

    print(f"\n{'=' * 60}")
    print(f"Contract Validation Report")
    print(f"{'=' * 60}")
    print(f"Contract: {report.contract_id} v{report.contract_version}")
    print(f"Status: {'✅ VALID' if report.is_valid else '❌ INVALID'}")
    print(f"{'=' * 60}")

    for result in report.results:
        status = "✅" if result.passed else "❌"
        print(f"\n{status} [{result.check_id}] {result.check_name}")
        print(f"   {result.message}")
        if result.details and not result.passed:
            print(f"   Details: {result.details[:200]}")

    sys.exit(0 if report.is_valid else 1)


def validate_output(args, runner, OutputValidator):
    """Validate an output against a contract."""
    if OutputValidator is None:
        print("Error: Validation requires jsonschema. Install with:")
        print("  pip install jsonschema")
        sys.exit(1)

    contract = runner.load_contract(args.contract_id)

    with open(args.output_file) as f:
        output = f.read()

    report = runner.validate_output(contract, output, {})

    if report is None:
        print("Validation failed - could not parse output")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"Output Validation Report")
    print(f"{'=' * 60}")
    print(f"Status: {'✅ VALID' if report.is_valid else '❌ INVALID'}")
    print(f"Blocking failures: {report.blocking_failures}")
    print(f"Required failures: {report.required_failures}")
    print(f"{'=' * 60}")

    for result in report.results:
        status = "✅" if result.passed else "❌"
        print(f"\n{status} [{result.check_id}] {result.check_name}")
        print(f"   {result.message}")

    sys.exit(0 if report.is_valid else 1)
