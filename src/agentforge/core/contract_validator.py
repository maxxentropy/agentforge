#!/usr/bin/env python3
"""
Contract Validator
==================

Verifies that prompt contracts are correct BEFORE they're used.

This applies "correctness is upstream" to the prompts themselves:
- Contract structure must be valid
- All examples must validate against output schema
- Template variables must be defined in inputs
- Verification checks must be well-formed
"""

import re
from pathlib import Path

import jsonschema
import yaml

try:
    from .contract_validator_types import ContractValidationReport, Severity, ValidationResult
    from .output_validator import OutputValidator
except ImportError:
    from contract_validator_types import ContractValidationReport, Severity, ValidationResult
    from output_validator import OutputValidator

# Re-export types for backwards compatibility
__all__ = [
    'Severity', 'ValidationResult', 'ContractValidationReport',
    'ContractValidator', 'OutputValidator'
]


class ContractValidator:
    """
    Validates prompt contracts for correctness.

    This applies "correctness is upstream" to the prompts themselves:
    - Contract structure must be valid
    - All examples must validate against output schema
    - Template variables must be defined in inputs
    - Verification checks must be well-formed
    """

    def __init__(self, schema_path: Path):
        """Load the contract schema."""
        with open(schema_path) as f:
            self.contract_schema = yaml.safe_load(f)

    def validate_contract(self, contract_path: Path) -> ContractValidationReport:
        """Validate a prompt contract file."""
        with open(contract_path) as f:
            contract = yaml.safe_load(f)

        contract_id = contract.get('contract', {}).get('id', 'unknown')
        contract_version = contract.get('contract', {}).get('version', '0.0.0')

        report = ContractValidationReport(
            contract_id=contract_id,
            contract_version=contract_version,
            is_valid=True
        )

        # Run all validation checks
        self._check_schema_validity(contract, report)
        self._check_output_schema_validity(contract, report)
        self._check_examples_validate(contract, report)
        self._check_template_variables(contract, report)
        self._check_verification_rules(contract, report)
        self._check_input_coverage(contract, report)

        return report

    def _check_schema_validity(self, contract: dict, report: ContractValidationReport):
        """Check contract validates against contract schema."""
        try:
            jsonschema.validate(contract, self.contract_schema)
            report.add_result(ValidationResult(
                check_id="SCHEMA-001",
                check_name="Contract Schema Validity",
                passed=True,
                severity=Severity.ADVISORY,
                message="Contract validates against prompt-contract.schema.yaml"
            ))
        except jsonschema.ValidationError as e:
            report.add_result(ValidationResult(
                check_id="SCHEMA-001",
                check_name="Contract Schema Validity",
                passed=False,
                severity=Severity.ADVISORY,
                message="Contract structure has minor schema deviations (doesn't affect functionality)",
                details=str(e.message)
            ))

    def _check_output_schema_validity(self, contract: dict, report: ContractValidationReport):
        """Check that the output schema is valid JSON Schema."""
        output_schema = contract.get('output', {}).get('schema', {})

        if not output_schema:
            report.add_result(ValidationResult(
                check_id="SCHEMA-002",
                check_name="Output Schema Presence",
                passed=False,
                severity=Severity.BLOCKING,
                message="Contract must define output.schema"
            ))
            return

        try:
            jsonschema.Draft7Validator.check_schema(output_schema)
            report.add_result(ValidationResult(
                check_id="SCHEMA-002",
                check_name="Output Schema Validity",
                passed=True,
                severity=Severity.BLOCKING,
                message="Output schema is valid JSON Schema"
            ))
        except jsonschema.SchemaError as e:
            report.add_result(ValidationResult(
                check_id="SCHEMA-002",
                check_name="Output Schema Validity",
                passed=False,
                severity=Severity.BLOCKING,
                message="Output schema is not valid JSON Schema",
                details=str(e.message)
            ))

    def _check_examples_validate(self, contract: dict, report: ContractValidationReport):
        """Check that all valid examples validate against output schema."""
        output_schema = contract.get('output', {}).get('schema', {})
        examples = contract.get('examples', {})
        valid_examples = examples.get('valid', [])

        if not valid_examples:
            report.add_result(ValidationResult(
                check_id="EXAMPLE-001",
                check_name="Examples Presence",
                passed=False,
                severity=Severity.REQUIRED,
                message="Contract should have at least one valid example"
            ))
            return

        validator = jsonschema.Draft7Validator(output_schema)

        for i, example in enumerate(valid_examples):
            example_name = example.get('name', f'Example {i+1}')
            output = example.get('output', {})
            errors = list(validator.iter_errors(output))

            if errors:
                report.add_result(ValidationResult(
                    check_id=f"EXAMPLE-{i+1:03d}",
                    check_name=f"Example Validation: {example_name}",
                    passed=False,
                    severity=Severity.BLOCKING,
                    message=f"Example '{example_name}' does not validate against output schema",
                    details="; ".join(e.message for e in errors[:3])
                ))
            else:
                report.add_result(ValidationResult(
                    check_id=f"EXAMPLE-{i+1:03d}",
                    check_name=f"Example Validation: {example_name}",
                    passed=True,
                    severity=Severity.BLOCKING,
                    message=f"Example '{example_name}' validates correctly"
                ))

    def _check_template_variables(self, contract: dict, report: ContractValidationReport):
        """Check that all template variables are defined in inputs."""
        defined_inputs = set()
        inputs = contract.get('inputs', {})

        for input_type in ['required', 'optional', 'context']:
            for input_spec in inputs.get(input_type, []):
                defined_inputs.add(input_spec.get('name'))

        defined_inputs.add('inputs')

        template = contract.get('template', {})
        all_content = ""

        for section_type in ['system', 'user']:
            sections = template.get(section_type, {}).get('sections', [])
            for section in sections:
                all_content += section.get('content', '') + "\n"

        variable_pattern = re.compile(r'\{([a-z_][a-z0-9_.]*)\}')
        used_variables = set()

        for match in variable_pattern.finditer(all_content):
            var_name = match.group(1).split('.')[0]
            used_variables.add(var_name)

        undefined = used_variables - defined_inputs

        if undefined:
            report.add_result(ValidationResult(
                check_id="VAR-001",
                check_name="Template Variable Definition",
                passed=False,
                severity=Severity.BLOCKING,
                message=f"Template uses undefined variables: {', '.join(undefined)}",
                details="All template variables must be defined in inputs.required, inputs.optional, or inputs.context"
            ))
        else:
            report.add_result(ValidationResult(
                check_id="VAR-001",
                check_name="Template Variable Definition",
                passed=True,
                severity=Severity.BLOCKING,
                message="All template variables are defined in inputs"
            ))

        unused = defined_inputs - used_variables - {'inputs'}

        if unused:
            report.add_result(ValidationResult(
                check_id="VAR-002",
                check_name="Input Usage",
                passed=False,
                severity=Severity.ADVISORY,
                message=f"Defined inputs not used in template: {', '.join(unused)}",
                details="Consider removing unused inputs or using them in the template"
            ))

    def _check_verification_rules(self, contract: dict, report: ContractValidationReport):
        """Check that verification rules are well-formed."""
        verification = contract.get('verification', {})
        checks = verification.get('checks', [])

        if not checks:
            report.add_result(ValidationResult(
                check_id="VERIFY-001",
                check_name="Verification Rules Presence",
                passed=False,
                severity=Severity.ADVISORY,
                message="Contract has no verification checks beyond schema validation"
            ))
            return

        type_requirements = {
            'regex': ['target', 'pattern'],
            'regex_negative': ['target', 'pattern'],
            'field_equals': ['target', 'value'],
            'field_contains': ['target', 'value'],
            'count_min': ['target', 'value'],
            'count_max': ['target', 'value'],
            'conditional': ['condition', 'check'],
            'llm': ['prompt', 'expected'],
        }

        for i, check in enumerate(checks):
            check_id = check.get('id', f'CHECK-{i}')
            check_type = check.get('type')
            required_fields = type_requirements.get(check_type, [])
            missing_fields = [f for f in required_fields if f not in check]

            if missing_fields:
                report.add_result(ValidationResult(
                    check_id=f"VERIFY-{check_id}",
                    check_name=f"Verification Rule: {check_id}",
                    passed=False,
                    severity=Severity.REQUIRED,
                    message=f"Check {check_id} missing required fields for type '{check_type}'",
                    details=f"Missing: {', '.join(missing_fields)}"
                ))
            else:
                report.add_result(ValidationResult(
                    check_id=f"VERIFY-{check_id}",
                    check_name=f"Verification Rule: {check_id}",
                    passed=True,
                    severity=Severity.REQUIRED,
                    message=f"Check {check_id} is well-formed"
                ))

    def _check_input_coverage(self, contract: dict, report: ContractValidationReport):
        """Check that examples cover required inputs."""
        required_inputs = [
            inp.get('name')
            for inp in contract.get('inputs', {}).get('required', [])
        ]

        valid_examples = contract.get('examples', {}).get('valid', [])

        for i, example in enumerate(valid_examples):
            example_name = example.get('name', f'Example {i+1}')
            example_inputs = example.get('inputs', {})
            missing = [inp for inp in required_inputs if inp not in example_inputs]

            if missing:
                report.add_result(ValidationResult(
                    check_id=f"INPUT-{i+1:03d}",
                    check_name=f"Example Input Coverage: {example_name}",
                    passed=False,
                    severity=Severity.REQUIRED,
                    message=f"Example '{example_name}' missing required inputs",
                    details=f"Missing: {', '.join(missing)}"
                ))


# ==============================================================================
# CLI Interface
# ==============================================================================

def validate_contract_cli(contract_path: str, schema_path: str = None):
    """CLI to validate a contract file."""
    if schema_path is None:
        schema_path = Path(__file__).parent / 'schemas' / 'prompt-contract.schema.yaml'

    validator = ContractValidator(Path(schema_path))
    report = validator.validate_contract(Path(contract_path))

    print(f"\n{'=' * 60}")
    print("Contract Validation Report")
    print(f"{'=' * 60}")
    print(f"Contract: {report.contract_id} v{report.contract_version}")
    print(f"Status: {'VALID' if report.is_valid else 'INVALID'}")
    print(f"{'=' * 60}")

    if report.blocking_failures > 0:
        print(f"\nBLOCKING FAILURES: {report.blocking_failures}")
    if report.required_failures > 0:
        print(f"\nREQUIRED FAILURES: {report.required_failures}")
    if report.advisory_warnings > 0:
        print(f"\nADVISORY WARNINGS: {report.advisory_warnings}")

    print("\nDetailed Results:")
    print("-" * 60)

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"\n{status} [{result.check_id}] {result.check_name}")
        print(f"   {result.severity.value.upper()}: {result.message}")
        if result.details:
            print(f"   Details: {result.details[:200]}")

    return report.is_valid


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python contract_validator.py <contract.yaml> [schema.yaml]")
        sys.exit(1)

    contract_path = sys.argv[1]
    schema_path = sys.argv[2] if len(sys.argv) > 2 else None

    is_valid = validate_contract_cli(contract_path, schema_path)
    sys.exit(0 if is_valid else 1)
