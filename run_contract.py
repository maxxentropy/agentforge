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
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent / 'tools'))

# Try to import validation tools - they require jsonschema
ContractValidator = None
OutputValidator = None
ContractValidationReport = None

try:
    from contract_validator import ContractValidator, OutputValidator, ContractValidationReport
except ImportError as e:
    if 'jsonschema' in str(e):
        print("Note: Install jsonschema for validation: pip install jsonschema")
    elif 'yaml' in str(e):
        print("Note: Install PyYAML for validation: pip install pyyaml")
    else:
        print(f"Note: Validation disabled - {e}")
except Exception as e:
    print(f"Note: Validation disabled - {e}")

# Import command handlers
from run_contract_commands import (
    run_intake, run_clarify, run_analyze, run_draft, run_validate,
    validate_contract, validate_output
)


class ContractRunner:
    """Run prompt contracts and validate outputs."""

    def __init__(self, contracts_dir: Path = None, outputs_dir: Path = None):
        self.contracts_dir = contracts_dir or Path(__file__).parent / 'contracts'
        self.outputs_dir = outputs_dir or Path(__file__).parent / 'outputs'
        self.outputs_dir.mkdir(exist_ok=True)
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

    def _build_system_message(self, contract: Dict) -> str:
        """Build system message from contract template."""
        sections = contract.get('template', {}).get('system', {}).get('sections', [])
        return '\n'.join(section.get('content', '') for section in sections)

    def _should_include_section(self, section: dict, inputs: Dict, context: Dict) -> bool:
        """Check if a conditional section should be included."""
        condition = section.get('condition')
        if not condition:
            return True
        var_name = condition.strip()
        return bool(inputs.get(var_name) or context.get(var_name))

    def _build_user_message(self, contract: Dict, inputs: Dict, context: Dict) -> str:
        """Build user message from contract template with conditions."""
        sections = contract.get('template', {}).get('user', {}).get('sections', [])
        parts = [
            section.get('content', '')
            for section in sections
            if self._should_include_section(section, inputs, context)
        ]
        return '\n'.join(parts)

    def _substitute_variables(self, message: str, variables: Dict) -> str:
        """Substitute variables in message."""
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                replacement = yaml.dump(value, default_flow_style=False) if isinstance(value, (dict, list)) else str(value)
                message = message.replace(placeholder, replacement)
        return message

    def assemble_prompt(self, contract: Dict, inputs: Dict, context: Dict = None) -> Dict:
        """Assemble a prompt from contract and inputs. Returns structured dict."""
        context = context or {}

        system_message = self._build_system_message(contract)
        user_message = self._build_user_message(contract, inputs, context)

        all_vars = {**inputs, **context, 'project_context': self.project_context}
        user_message = self._substitute_variables(user_message, all_vars)

        execution = contract.get('execution', {})

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

        try:
            output_clean = re.sub(r'^```ya?ml?\s*', '', output.strip())
            output_clean = re.sub(r'\s*```$', '', output_clean)
            parsed = yaml.safe_load(output_clean)
        except yaml.YAMLError as e:
            print(f"Error parsing output as YAML: {e}")
            return None

        validator = OutputValidator(contract)
        return validator.validate(parsed, inputs)

    def save_prompt(self, prompt: Dict, contract_id: str) -> Path:
        """Save assembled prompt to YAML file with readable multiline strings."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{contract_id}_{timestamp}_prompt.yaml"
        filepath = self.outputs_dir / filename

        def str_representer(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        yaml.add_representer(str, str_representer)

        with open(filepath, 'w') as f:
            yaml.dump(prompt, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)

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


def _build_parser():
    """Build argument parser with all subcommands."""
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

    # CLARIFY command
    clarify_parser = subparsers.add_parser('clarify', help='Run CLARIFY contract')
    clarify_parser.add_argument('--intake-file', required=True, help='Path to intake record YAML')
    clarify_parser.add_argument('--history-file', help='Path to conversation history YAML')
    clarify_parser.add_argument('--print-prompt', action='store_true')

    # ANALYZE command
    analyze_parser = subparsers.add_parser('analyze', help='Run ANALYZE contract')
    analyze_parser.add_argument('--intake-file', required=True)
    analyze_parser.add_argument('--clarification-file', required=True)
    analyze_parser.add_argument('--architecture-file')
    analyze_parser.add_argument('--code-context', help='Code context string')
    analyze_parser.add_argument('--print-prompt', action='store_true')

    # DRAFT command
    draft_parser = subparsers.add_parser('draft', help='Run DRAFT contract')
    draft_parser.add_argument('--intake-file', required=True)
    draft_parser.add_argument('--clarification-file', required=True)
    draft_parser.add_argument('--analysis-file', required=True)
    draft_parser.add_argument('--print-prompt', action='store_true')

    # VALIDATE (spec) command
    validate_parser = subparsers.add_parser('validate', help='Run VALIDATE contract')
    validate_parser.add_argument('--spec-file', required=True)
    validate_parser.add_argument('--analysis-file', required=True)
    validate_parser.add_argument('--architecture-file')
    validate_parser.add_argument('--print-prompt', action='store_true')

    # Validate contract structure
    vc_parser = subparsers.add_parser('validate-contract', help='Validate contract structure')
    vc_parser.add_argument('contract_file', help='Path to contract YAML')

    # Validate output against contract
    vo_parser = subparsers.add_parser('validate-output', help='Validate output against contract')
    vo_parser.add_argument('contract_id', help='Contract ID (e.g., spec.intake.v1)')
    vo_parser.add_argument('output_file', help='Path to output YAML')

    return parser


def _dispatch_command(args, runner):
    """Dispatch to appropriate command handler."""
    handlers = {
        'intake': lambda: run_intake(args, runner),
        'clarify': lambda: run_clarify(args, runner),
        'analyze': lambda: run_analyze(args, runner),
        'draft': lambda: run_draft(args, runner),
        'validate': lambda: run_validate(args, runner),
        'validate-contract': lambda: validate_contract(args, ContractValidator, ContractValidationReport),
        'validate-output': lambda: validate_output(args, runner, OutputValidator),
    }
    handler = handlers.get(args.command)
    if handler:
        handler()


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    runner = ContractRunner()
    _dispatch_command(args, runner)


if __name__ == '__main__':
    main()
