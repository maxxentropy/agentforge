"""
AgentForge Contract Runner
==========================

Runs prompt contracts (YAML templates that define LLM prompts).

NOT to be confused with verification contracts in contracts.py - those are
machine-verifiable code correctness rules. This module handles prompt assembly
for the SPEC workflow (intake, clarify, analyze, draft, validate).

Usage:
    from agentforge.core.contract_runner import ContractRunner

    runner = ContractRunner()
    contract = runner.load_contract('spec.intake.v1')
    prompt_data = runner.assemble_prompt(contract, {'raw_request': 'Add feature X'})
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class ContractRunner:
    """Run prompt contracts and validate outputs."""

    def __init__(self, contracts_dir: Path = None, outputs_dir: Path = None):
        # Default to project root directories
        project_root = Path(__file__).parent.parent.parent.parent
        self.contracts_dir = contracts_dir or project_root / 'contracts'
        self.outputs_dir = outputs_dir or project_root / 'outputs'
        self.outputs_dir.mkdir(exist_ok=True)
        self.project_context = self._load_project_context()

    def _load_project_context(self) -> str:
        """Load default project context."""
        project_root = Path(__file__).parent.parent.parent.parent
        context_file = project_root / 'sample_data' / 'project_context.yaml'
        if context_file.exists():
            with open(context_file) as f:
                return f.read()
        return "No project context configured."

    def load_contract(self, contract_id: str) -> dict[str, Any]:
        """Load a contract by ID."""
        contract_file = self.contracts_dir / f"{contract_id}.yaml"
        if not contract_file.exists():
            raise FileNotFoundError(f"Contract not found: {contract_file}")

        with open(contract_file) as f:
            return yaml.safe_load(f)

    def _build_system_message(self, contract: dict) -> str:
        """Build system message from contract template."""
        sections = contract.get('template', {}).get('system', {}).get('sections', [])
        return '\n'.join(section.get('content', '') for section in sections)

    def _should_include_section(self, section: dict, inputs: dict, context: dict) -> bool:
        """Check if a conditional section should be included."""
        condition = section.get('condition')
        if not condition:
            return True
        var_name = condition.strip()
        return bool(inputs.get(var_name) or context.get(var_name))

    def _build_user_message(self, contract: dict, inputs: dict, context: dict) -> str:
        """Build user message from contract template with conditions."""
        sections = contract.get('template', {}).get('user', {}).get('sections', [])
        parts = [
            section.get('content', '')
            for section in sections
            if self._should_include_section(section, inputs, context)
        ]
        return '\n'.join(parts)

    def _substitute_variables(self, message: str, variables: dict) -> str:
        """Substitute variables in message."""
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                replacement = yaml.dump(value, default_flow_style=False) if isinstance(value, (dict, list)) else str(value)
                message = message.replace(placeholder, replacement)
        return message

    def assemble_prompt(self, contract: dict, inputs: dict, context: dict = None) -> dict:
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

    def validate_output(self, contract: dict, output: str, inputs: dict) -> Any | None:
        """Validate LLM output against contract."""
        # Try to import validation tools - they require jsonschema
        try:
            from agentforge.core.contract_validator import OutputValidator
        except ImportError:
            return None

        try:
            output_clean = re.sub(r'^```ya?ml?\s*', '', output.strip())
            output_clean = re.sub(r'\s*```$', '', output_clean)
            parsed = yaml.safe_load(output_clean)
        except yaml.YAMLError:
            return None

        validator = OutputValidator(contract)
        return validator.validate(parsed, inputs)

    def save_prompt(self, prompt: dict, contract_id: str) -> Path:
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
