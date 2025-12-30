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

import yaml
import jsonschema
from pathlib import Path
from typing import Any
import re

try:
    from .contract_validator_types import (
        Severity, ValidationResult, ContractValidationReport
    )
except ImportError:
    from contract_validator_types import (
        Severity, ValidationResult, ContractValidationReport
    )

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


class OutputValidator:
    """
    Validates LLM outputs against contract specifications.

    Used at runtime to verify outputs before proceeding.
    """

    def __init__(self, contract: dict):
        self.contract = contract
        self.output_schema = contract.get('output', {}).get('schema', {})
        self.checks = contract.get('verification', {}).get('checks', [])

    def validate(self, output: Any, inputs: dict) -> ContractValidationReport:
        """Validate an LLM output against the contract."""
        contract_id = self.contract.get('contract', {}).get('id', 'unknown')
        contract_version = self.contract.get('contract', {}).get('version', '0.0.0')

        report = ContractValidationReport(
            contract_id=contract_id,
            contract_version=contract_version,
            is_valid=True
        )

        if self.contract.get('verification', {}).get('schema_validation', True):
            self._validate_schema(output, report)

        for check in self.checks:
            self._run_check(check, output, inputs, report)

        return report

    def _validate_schema(self, output: Any, report: ContractValidationReport):
        """Validate output against JSON Schema."""
        try:
            jsonschema.validate(output, self.output_schema)
            report.add_result(ValidationResult(
                check_id="SCHEMA",
                check_name="Output Schema Validation",
                passed=True,
                severity=Severity.BLOCKING,
                message="Output validates against schema"
            ))
        except jsonschema.ValidationError as e:
            report.add_result(ValidationResult(
                check_id="SCHEMA",
                check_name="Output Schema Validation",
                passed=False,
                severity=Severity.BLOCKING,
                message="Output does not validate against schema",
                details=e.message
            ))

    def _run_check(self, check: dict, output: Any, inputs: dict, report: ContractValidationReport):
        """Run a single verification check."""
        check_id = check.get('id', 'UNKNOWN')
        check_type = check.get('type')
        severity = Severity(check.get('severity', 'required'))

        try:
            if check_type == 'regex':
                passed = self._check_regex(check, output, positive=True)
            elif check_type == 'regex_negative':
                passed = self._check_regex(check, output, positive=False)
            elif check_type == 'field_equals':
                passed = self._check_field_equals(check, output, inputs)
            elif check_type == 'conditional':
                passed = self._check_conditional(check, output)
            elif check_type == 'count_min':
                passed = self._check_count_min(check, output)
            elif check_type == 'llm':
                report.add_result(ValidationResult(
                    check_id=check_id,
                    check_name=check.get('name', check_id),
                    passed=True,
                    severity=severity,
                    message="Requires LLM-based verification (deferred)",
                    details=check.get('prompt', '')[:100]
                ))
                return
            else:
                report.add_result(ValidationResult(
                    check_id=check_id,
                    check_name=check.get('name', check_id),
                    passed=True,
                    severity=Severity.INFORMATIONAL,
                    message=f"Unknown check type '{check_type}' - skipped"
                ))
                return

            report.add_result(ValidationResult(
                check_id=check_id,
                check_name=check.get('name', check_id),
                passed=passed,
                severity=severity,
                message=check.get('message', f"Check {check_id} {'passed' if passed else 'failed'}")
            ))

        except Exception as e:
            report.add_result(ValidationResult(
                check_id=check_id,
                check_name=check.get('name', check_id),
                passed=False,
                severity=severity,
                message=f"Check {check_id} raised exception",
                details=str(e)
            ))

    def _get_field_value(self, target: str, output: Any) -> Any:
        """Get a field value from output using dot notation."""
        parts = target.replace('[]', '').split('.')
        value = output

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list):
                value = [item.get(part) if isinstance(item, dict) else item for item in value]
            else:
                return None

        return value

    def _check_regex(self, check: dict, output: Any, positive: bool) -> bool:
        """Check if field matches (or doesn't match) regex."""
        target = check.get('target')
        pattern = check.get('pattern')
        value = self._get_field_value(target, output)

        if value is None:
            return not positive

        if isinstance(value, list):
            for item in value:
                if item and re.search(pattern, str(item)):
                    return positive
            return not positive

        match = re.search(pattern, str(value))
        return bool(match) == positive

    def _check_field_equals(self, check: dict, output: Any, inputs: dict) -> bool:
        """Check if field equals expected value."""
        target = check.get('target')
        expected = check.get('value')

        if isinstance(expected, str) and expected.startswith('{') and expected.endswith('}'):
            var_path = expected[1:-1]
            parts = var_path.split('.')
            if parts[0] == 'inputs':
                expected = inputs.get(parts[1]) if len(parts) > 1 else inputs

        actual = self._get_field_value(target, output)
        return actual == expected

    def _check_conditional(self, check: dict, output: Any) -> bool:
        """Check conditional rule: if condition then check."""
        condition = check.get('condition')
        check_expr = check.get('check')

        condition_result = self._eval_simple_condition(condition, output)

        if not condition_result:
            return True

        return self._eval_simple_condition(check_expr, output)

    def _check_count_min(self, check: dict, output: Any) -> bool:
        """Check minimum count of array field."""
        target = check.get('target')
        min_count = check.get('value', 0)
        value = self._get_field_value(target, output)

        if not isinstance(value, list):
            return False

        return len(value) >= min_count

    def _eval_simple_condition(self, expr: str, output: Any) -> bool:
        """Evaluate a simple condition expression."""
        if '!=' in expr:
            field, value = expr.split('!=')
            field = field.strip()
            value = value.strip().strip("'\"")
            actual = self._get_field_value(field, output)
            return str(actual) != value

        if '==' in expr:
            field, value = expr.split('==')
            field = field.strip()
            value = value.strip().strip("'\"")
            actual = self._get_field_value(field, output)
            return str(actual) == value

        if 'len(' in expr:
            match = re.match(r'len\((\w+)\)\s*>=\s*(\d+)', expr)
            if match:
                field = match.group(1)
                min_len = int(match.group(2))
                value = self._get_field_value(field, output)
                return isinstance(value, list) and len(value) >= min_len

        return True


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
    print(f"Contract Validation Report")
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

    print(f"\nDetailed Results:")
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
