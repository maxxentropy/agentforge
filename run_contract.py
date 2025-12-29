#!/usr/bin/env python3
"""
AgentForge Contract Runner
==========================

Simple CLI for running prompt contracts with validation.

Usage:
    python run_contract.py intake --request "Add discount codes to orders"
    python run_contract.py clarify --intake-file outputs/intake_record.yaml
    python run_contract.py validate-contract contracts/spec.intake.v1.yaml
"""

import yaml
import json
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import argparse

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent / 'tools'))

# Try to import validation tools - they require jsonschema
ContractValidator = None
OutputValidator = None
ContractValidationReport = None

try:
    from contract_validator import ContractValidator, OutputValidator, ContractValidationReport
except ImportError as e:
    # Show helpful message about missing dependencies
    if 'jsonschema' in str(e):
        print("Note: Install jsonschema for validation: pip install jsonschema")
    elif 'yaml' in str(e):
        print("Note: Install PyYAML for validation: pip install pyyaml")
    else:
        print(f"Note: Validation disabled - {e}")
except Exception as e:
    print(f"Note: Validation disabled - {e}")


class ContractRunner:
    """Run prompt contracts and validate outputs."""
    
    def __init__(self, contracts_dir: Path = None, outputs_dir: Path = None):
        self.contracts_dir = contracts_dir or Path(__file__).parent / 'contracts'
        self.outputs_dir = outputs_dir or Path(__file__).parent / 'outputs'
        self.outputs_dir.mkdir(exist_ok=True)
        
        # Load project context
        self.project_context = self._load_project_context()
    
    def _load_project_context(self) -> str:
        """Load default project context."""
        context_file = Path(__file__).parent / 'sample_data' / 'project_context.yaml'
        if context_file.exists():
            with open(context_file) as f:
                return f.read()
        return "No project context configured."
    
    def load_contract(self, contract_id: str) -> Dict[str, Any]:
        """Load a contract by ID."""
        contract_file = self.contracts_dir / f"{contract_id}.yaml"
        if not contract_file.exists():
            raise FileNotFoundError(f"Contract not found: {contract_file}")
        
        with open(contract_file) as f:
            return yaml.safe_load(f)
    
    def assemble_prompt(self, contract: Dict, inputs: Dict, context: Dict = None) -> Dict:
        """Assemble a prompt from contract and inputs. Returns structured dict."""
        context = context or {}
        
        # Build system message
        system_parts = []
        for section in contract.get('template', {}).get('system', {}).get('sections', []):
            content = section.get('content', '')
            system_parts.append(content)
        
        system_message = '\n'.join(system_parts)
        
        # Build user message with variable substitution
        user_parts = []
        for section in contract.get('template', {}).get('user', {}).get('sections', []):
            # Check condition
            condition = section.get('condition')
            if condition:
                # Simple condition check
                var_name = condition.strip()
                if var_name not in inputs and var_name not in context:
                    continue
                if not inputs.get(var_name) and not context.get(var_name):
                    continue
            
            content = section.get('content', '')
            user_parts.append(content)
        
        user_message = '\n'.join(user_parts)
        
        # Substitute variables
        all_vars = {**inputs, **context, 'project_context': self.project_context}
        
        for key, value in all_vars.items():
            placeholder = f"{{{key}}}"
            if placeholder in user_message:
                if isinstance(value, (dict, list)):
                    replacement = yaml.dump(value, default_flow_style=False)
                else:
                    replacement = str(value)
                user_message = user_message.replace(placeholder, replacement)
        
        # Get execution params from contract
        execution = contract.get('execution', {})
        
        # Return structured prompt
        return {
            'contract_id': contract.get('contract', {}).get('id'),
            'contract_version': contract.get('contract', {}).get('version'),
            'generated_at': datetime.now().isoformat(),
            'inputs_provided': inputs,
            'prompt': {
                'system': system_message,
                'user': user_message,
            },
            'execution': {
                'temperature': execution.get('temperature', 0.0),
                'max_tokens': execution.get('max_tokens', 4096),
            },
            'expected_output': {
                'format': contract.get('output', {}).get('format', 'yaml'),
            },
            'validation_command': f"python run_contract.py validate-output {contract.get('contract', {}).get('id')} outputs/intake_record.yaml"
        }
    
    def validate_output(self, contract: Dict, output: str, inputs: Dict):
        """Validate LLM output against contract."""
        if OutputValidator is None:
            print("Warning: Validation not available")
            return None
        
        # Parse YAML output
        try:
            # Remove markdown code blocks if present
            output_clean = re.sub(r'^```ya?ml?\s*', '', output.strip())
            output_clean = re.sub(r'\s*```$', '', output_clean)
            parsed = yaml.safe_load(output_clean)
        except yaml.YAMLError as e:
            print(f"Error parsing output as YAML: {e}")
            return None
        
        # Validate
        validator = OutputValidator(contract)
        return validator.validate(parsed, inputs)
    
    def save_prompt(self, prompt: Dict, contract_id: str) -> Path:
        """Save assembled prompt to YAML file with readable multiline strings."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{contract_id}_{timestamp}_prompt.yaml"
        filepath = self.outputs_dir / filename
        
        # Custom representer for literal block style on multiline strings
        def str_representer(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)
        
        yaml.add_representer(str, str_representer)
        
        with open(filepath, 'w') as f:
            yaml.dump(prompt, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)
        
        # Reset representer to default
        yaml.add_representer(str, yaml.representer.SafeRepresenter.represent_str)
        
        return filepath
    
    def save_output(self, output: str, contract_id: str) -> Path:
        """Save output to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{contract_id}_{timestamp}_output.yaml"
        filepath = self.outputs_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(output)
        
        return filepath


def run_intake(args):
    """Run INTAKE contract."""
    runner = ContractRunner()
    contract = runner.load_contract('spec.intake.v1')
    
    inputs = {
        'raw_request': args.request,
        'priority': args.priority or 'medium',
    }
    
    if args.constraints:
        inputs['constraints'] = args.constraints
    
    prompt_data = runner.assemble_prompt(contract, inputs)
    
    # Save prompt
    filepath = runner.save_prompt(prompt_data, 'spec.intake.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    
    # Also save copy-paste friendly files
    base = filepath.parent / filepath.stem
    system_file = Path(str(base) + "_SYSTEM.txt")
    user_file = Path(str(base) + "_USER.txt")
    
    with open(system_file, 'w') as f:
        f.write(prompt_data['prompt']['system'])
    with open(user_file, 'w') as f:
        f.write(prompt_data['prompt']['user'])
    
    # Print instructions
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


def run_clarify(args):
    """Run CLARIFY contract."""
    runner = ContractRunner()
    contract = runner.load_contract('spec.clarify.v1')
    
    # Load intake record
    with open(args.intake_file) as f:
        intake_record = yaml.safe_load(f)
    
    # Load conversation history if provided
    conversation_history = []
    if args.history_file and Path(args.history_file).exists():
        with open(args.history_file) as f:
            conversation_history = yaml.safe_load(f) or []
    
    inputs = {
        'intake_record': intake_record,
        'conversation_history': conversation_history,
    }
    
    prompt_data = runner.assemble_prompt(contract, inputs)
    
    # Save prompt
    filepath = runner.save_prompt(prompt_data, 'spec.clarify.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    
    # Also save copy-paste friendly files
    base = filepath.parent / filepath.stem
    system_file = Path(str(base) + "_SYSTEM.txt")
    user_file = Path(str(base) + "_USER.txt")
    
    with open(system_file, 'w') as f:
        f.write(prompt_data['prompt']['system'])
    with open(user_file, 'w') as f:
        f.write(prompt_data['prompt']['user'])
    
    print(f"   Also created: {system_file.name}, {user_file.name}")
    
    if args.print_prompt:
        print(f"\n{'=' * 70}")
        print("SYSTEM MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['system'])
        print(f"\n{'=' * 70}")
        print("USER MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['user'])
        print(f"\n{'=' * 70}")


def run_analyze(args):
    """Run ANALYZE contract."""
    runner = ContractRunner()
    contract = runner.load_contract('spec.analyze.v1')
    
    # Load required inputs
    with open(args.intake_file) as f:
        intake_record = yaml.safe_load(f)
    
    with open(args.clarification_file) as f:
        clarification_log = yaml.safe_load(f)
    
    # Load architecture rules
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
    
    filepath = runner.save_prompt(prompt_data, 'spec.analyze.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    
    # Also save copy-paste friendly files
    base = filepath.parent / filepath.stem
    system_file = Path(str(base) + "_SYSTEM.txt")
    user_file = Path(str(base) + "_USER.txt")
    
    with open(system_file, 'w') as f:
        f.write(prompt_data['prompt']['system'])
    with open(user_file, 'w') as f:
        f.write(prompt_data['prompt']['user'])
    
    print(f"   Also created: {system_file.name}, {user_file.name}")
    
    if args.print_prompt:
        print(f"\n{'=' * 70}")
        print("SYSTEM MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['system'])
        print(f"\n{'=' * 70}")
        print("USER MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['user'])
        print(f"\n{'=' * 70}")


def run_draft(args):
    """Run DRAFT contract."""
    runner = ContractRunner()
    contract = runner.load_contract('spec.draft.v1')
    
    # Load required inputs
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
    
    filepath = runner.save_prompt(prompt_data, 'spec.draft.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    
    # Also save copy-paste friendly files
    base = filepath.parent / filepath.stem
    system_file = Path(str(base) + "_SYSTEM.txt")
    user_file = Path(str(base) + "_USER.txt")
    
    with open(system_file, 'w') as f:
        f.write(prompt_data['prompt']['system'])
    with open(user_file, 'w') as f:
        f.write(prompt_data['prompt']['user'])
    
    print(f"   Also created: {system_file.name}, {user_file.name}")
    
    if args.print_prompt:
        print(f"\n{'=' * 70}")
        print("SYSTEM MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['system'])
        print(f"\n{'=' * 70}")
        print("USER MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['user'])
        print(f"\n{'=' * 70}")


def run_validate(args):
    """Run VALIDATE contract."""
    runner = ContractRunner()
    contract = runner.load_contract('spec.validate.v1')
    
    # Load specification
    with open(args.spec_file) as f:
        specification = f.read()
    
    # Load analysis report
    with open(args.analysis_file) as f:
        analysis_report = yaml.safe_load(f)
    
    # Load architecture rules
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
    
    filepath = runner.save_prompt(prompt_data, 'spec.validate.v1')
    print(f"\n✅ Prompt saved to: {filepath}")
    
    # Also save copy-paste friendly files
    base = filepath.parent / filepath.stem
    system_file = Path(str(base) + "_SYSTEM.txt")
    user_file = Path(str(base) + "_USER.txt")
    
    with open(system_file, 'w') as f:
        f.write(prompt_data['prompt']['system'])
    with open(user_file, 'w') as f:
        f.write(prompt_data['prompt']['user'])
    
    print(f"   Also created: {system_file.name}, {user_file.name}")
    
    if args.print_prompt:
        print(f"\n{'=' * 70}")
        print("SYSTEM MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['system'])
        print(f"\n{'=' * 70}")
        print("USER MESSAGE")
        print(f"{'=' * 70}\n")
        print(prompt_data['prompt']['user'])
        print(f"\n{'=' * 70}")


def validate_contract(args):
    """Validate a contract file."""
    if ContractValidator is None:
        print("Error: Validation requires jsonschema. Install with:")
        print("  pip install jsonschema")
        sys.exit(1)
    
    schema_path = Path(__file__).parent / 'schemas' / 'prompt-contract.schema.yaml'
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    
    validator = ContractValidator(schema_path)
    report = validator.validate_contract(Path(args.contract_file))
    
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


def validate_output(args):
    """Validate an output against a contract."""
    if OutputValidator is None:
        print("Error: Validation requires jsonschema. Install with:")
        print("  pip install jsonschema")
        sys.exit(1)
    
    runner = ContractRunner()
    
    # Load contract
    contract = runner.load_contract(args.contract_id)
    
    # Load output
    with open(args.output_file) as f:
        output = f.read()
    
    # Validate
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


def main():
    parser = argparse.ArgumentParser(
        description='AgentForge Contract Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s intake --request "Add discount codes to orders"
  %(prog)s clarify --intake-file outputs/intake_record.yaml
  %(prog)s validate-contract contracts/spec.intake.v1.yaml
  %(prog)s validate-output spec.intake.v1 outputs/intake_record.yaml
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # INTAKE command
    intake_parser = subparsers.add_parser('intake', help='Run INTAKE contract')
    intake_parser.add_argument('--request', '-r', required=True, help='Feature request text')
    intake_parser.add_argument('--priority', '-p', choices=['critical', 'high', 'medium', 'low'])
    intake_parser.add_argument('--constraints', '-c', help='Known constraints')
    intake_parser.add_argument('--print-prompt', action='store_true', help='Print prompt to stdout')
    intake_parser.set_defaults(func=run_intake)
    
    # CLARIFY command
    clarify_parser = subparsers.add_parser('clarify', help='Run CLARIFY contract')
    clarify_parser.add_argument('--intake-file', required=True, help='Path to intake record YAML')
    clarify_parser.add_argument('--history-file', help='Path to conversation history YAML')
    clarify_parser.add_argument('--print-prompt', action='store_true')
    clarify_parser.set_defaults(func=run_clarify)
    
    # ANALYZE command
    analyze_parser = subparsers.add_parser('analyze', help='Run ANALYZE contract')
    analyze_parser.add_argument('--intake-file', required=True)
    analyze_parser.add_argument('--clarification-file', required=True)
    analyze_parser.add_argument('--architecture-file')
    analyze_parser.add_argument('--code-context', help='Code context string')
    analyze_parser.add_argument('--print-prompt', action='store_true')
    analyze_parser.set_defaults(func=run_analyze)
    
    # DRAFT command
    draft_parser = subparsers.add_parser('draft', help='Run DRAFT contract')
    draft_parser.add_argument('--intake-file', required=True)
    draft_parser.add_argument('--clarification-file', required=True)
    draft_parser.add_argument('--analysis-file', required=True)
    draft_parser.add_argument('--print-prompt', action='store_true')
    draft_parser.set_defaults(func=run_draft)
    
    # VALIDATE (spec) command
    validate_parser = subparsers.add_parser('validate', help='Run VALIDATE contract')
    validate_parser.add_argument('--spec-file', required=True)
    validate_parser.add_argument('--analysis-file', required=True)
    validate_parser.add_argument('--architecture-file')
    validate_parser.add_argument('--print-prompt', action='store_true')
    validate_parser.set_defaults(func=run_validate)
    
    # Validate contract structure
    vc_parser = subparsers.add_parser('validate-contract', help='Validate contract structure')
    vc_parser.add_argument('contract_file', help='Path to contract YAML')
    vc_parser.set_defaults(func=validate_contract)
    
    # Validate output against contract
    vo_parser = subparsers.add_parser('validate-output', help='Validate output against contract')
    vo_parser.add_argument('contract_id', help='Contract ID (e.g., spec.intake.v1)')
    vo_parser.add_argument('output_file', help='Path to output YAML')
    vo_parser.set_defaults(func=validate_output)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
