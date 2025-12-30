#!/usr/bin/env python3
"""
Output Validator
================

Validates LLM outputs against contract specifications at runtime.

Extracted from contract_validator.py for modularity.
"""

import re
import jsonschema
from typing import Any

try:
    from .contract_validator_types import (
        Severity, ValidationResult, ContractValidationReport
    )
except ImportError:
    from contract_validator_types import (
        Severity, ValidationResult, ContractValidationReport
    )


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
            passed = self._dispatch_check(check, check_type, output, inputs, report)
            if passed is None:
                return  # Check handled its own result

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

    def _dispatch_check(self, check: dict, check_type: str, output: Any,
                        inputs: dict, report: ContractValidationReport):
        """Dispatch to appropriate check handler. Returns passed or None if handled."""
        check_handlers = {
            'regex': lambda: self._check_regex(check, output, positive=True),
            'regex_negative': lambda: self._check_regex(check, output, positive=False),
            'field_equals': lambda: self._check_field_equals(check, output, inputs),
            'conditional': lambda: self._check_conditional(check, output),
            'count_min': lambda: self._check_count_min(check, output),
        }

        if check_type in check_handlers:
            return check_handlers[check_type]()

        return self._handle_special_check_type(check, check_type, report)

    def _handle_special_check_type(self, check: dict, check_type: str,
                                   report: ContractValidationReport):
        """Handle special check types that add their own results."""
        check_id = check.get('id', 'UNKNOWN')
        severity = Severity(check.get('severity', 'required'))

        if check_type == 'llm':
            report.add_result(ValidationResult(
                check_id=check_id, check_name=check.get('name', check_id),
                passed=True, severity=severity,
                message="Requires LLM-based verification (deferred)",
                details=check.get('prompt', '')[:100]
            ))
        else:
            report.add_result(ValidationResult(
                check_id=check_id, check_name=check.get('name', check_id),
                passed=True, severity=Severity.INFORMATIONAL,
                message=f"Unknown check type '{check_type}' - skipped"
            ))
        return None

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
