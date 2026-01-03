# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-enforcer
# @test_path: tests/unit/contracts/test_enforcer.py

"""
Contract Enforcer
=================

Runtime enforcement of approved contracts.

The enforcer validates:
- Stage inputs meet contract requirements
- Stage outputs satisfy schemas and rules
- Escalation triggers are checked
- Quality gates are evaluated

Key Design:
- Validation produces results, not exceptions
- Multiple violations can be detected in one pass
- Violations include context for human understanding
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .draft import (
    ApprovedContracts,
    EscalationTrigger,
    QualityGate,
    StageContract,
    ValidationRule,
)
from .operations.loader import OperationContract, OperationContractManager, OperationRule


class ViolationSeverity(str, Enum):
    """Severity of a contract violation."""
    ERROR = "error"  # Must be fixed
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Informational


class ViolationType(str, Enum):
    """Type of contract violation."""
    MISSING_REQUIRED = "missing_required"
    TYPE_MISMATCH = "type_mismatch"
    ENUM_VIOLATION = "enum_violation"
    CONSTRAINT_VIOLATION = "constraint_violation"
    SCHEMA_VIOLATION = "schema_violation"
    OPERATION_RULE = "operation_rule"


@dataclass
class Violation:
    """A contract violation."""

    violation_id: str
    violation_type: ViolationType
    severity: ViolationSeverity
    message: str
    field_path: str = ""
    expected: Any = None
    actual: Any = None
    rule_id: str = ""
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "field_path": self.field_path,
            "expected": str(self.expected) if self.expected else None,
            "actual": str(self.actual) if self.actual else None,
            "rule_id": self.rule_id,
            "rationale": self.rationale,
        }


@dataclass
class ValidationResult:
    """Result of contract validation."""

    valid: bool
    violations: list[Violation] = field(default_factory=list)
    warnings: list[Violation] = field(default_factory=list)
    stage_name: str = ""
    context: str = ""  # input or output

    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return len([v for v in self.violations if v.severity == ViolationSeverity.ERROR])

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return len(self.warnings)

    def add_violation(self, violation: Violation) -> None:
        """Add a violation to the result."""
        if violation.severity == ViolationSeverity.WARNING:
            self.warnings.append(violation)
        else:
            self.violations.append(violation)
            self.valid = False

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another result into this one."""
        self.violations.extend(other.violations)
        self.warnings.extend(other.warnings)
        if not other.valid:
            self.valid = False
        return self


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation."""

    passed: bool
    gate_id: str
    failed_checks: list[str] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    action: str = ""  # What to do if failed


@dataclass
class EscalationCheck:
    """Result of checking escalation triggers."""

    triggered: bool
    trigger: EscalationTrigger | None = None
    context: dict[str, Any] = field(default_factory=dict)


class ContractEnforcer:
    """Enforces contracts during pipeline execution.

    Validates stage inputs and outputs against approved contracts,
    checks escalation triggers, and evaluates quality gates.
    """

    def __init__(
        self,
        contracts: ApprovedContracts,
        operation_manager: OperationContractManager | None = None,
    ):
        """Initialize enforcer with approved contracts.

        Args:
            contracts: The approved contracts to enforce
            operation_manager: Manager for operation contracts
        """
        self.contracts = contracts
        self.operation_manager = operation_manager or OperationContractManager()
        self._violation_counter = 0

    def _next_violation_id(self) -> str:
        """Generate next violation ID."""
        self._violation_counter += 1
        return f"V-{self._violation_counter:03d}"

    def validate_stage_input(
        self,
        stage_name: str,
        artifacts: dict[str, Any],
    ) -> ValidationResult:
        """Validate stage input against contract.

        Args:
            stage_name: Name of the stage
            artifacts: Input artifacts to validate

        Returns:
            ValidationResult with any violations
        """
        result = ValidationResult(valid=True, stage_name=stage_name, context="input")

        stage_contract = self.contracts.get_stage_contract(stage_name)
        if stage_contract is None:
            return result  # No contract means no validation

        # Check required inputs
        for req in stage_contract.input_requirements:
            if req not in artifacts:
                result.add_violation(Violation(
                    violation_id=self._next_violation_id(),
                    violation_type=ViolationType.MISSING_REQUIRED,
                    severity=ViolationSeverity.ERROR,
                    message=f"Missing required input: {req}",
                    field_path=f"input.{req}",
                    rule_id="input-required",
                ))

        # Validate against schema if provided
        if stage_contract.input_schema:
            schema_result = self._validate_schema(
                artifacts, stage_contract.input_schema, "input"
            )
            result.merge(schema_result)

        return result

    def validate_stage_output(
        self,
        stage_name: str,
        artifacts: dict[str, Any],
    ) -> ValidationResult:
        """Validate stage output against contract.

        Args:
            stage_name: Name of the stage
            artifacts: Output artifacts to validate

        Returns:
            ValidationResult with any violations
        """
        result = ValidationResult(valid=True, stage_name=stage_name, context="output")

        stage_contract = self.contracts.get_stage_contract(stage_name)
        if stage_contract is None:
            return result  # No contract means no validation

        # Check required outputs
        for req in stage_contract.output_requirements:
            if req not in artifacts:
                result.add_violation(Violation(
                    violation_id=self._next_violation_id(),
                    violation_type=ViolationType.MISSING_REQUIRED,
                    severity=ViolationSeverity.ERROR,
                    message=f"Missing required output: {req}",
                    field_path=f"output.{req}",
                    rule_id="output-required",
                ))

        # Validate against schema if provided
        if stage_contract.output_schema:
            schema_result = self._validate_schema(
                artifacts, stage_contract.output_schema, "output"
            )
            result.merge(schema_result)

        # Apply validation rules
        for rule in stage_contract.validation_rules:
            rule_result = self._apply_validation_rule(rule, artifacts)
            result.merge(rule_result)

        return result

    def _validate_schema(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
        context: str,
    ) -> ValidationResult:
        """Validate data against a JSON schema.

        Args:
            data: Data to validate
            schema: JSON Schema
            context: Context for error messages

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True, context=context)

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                result.add_violation(Violation(
                    violation_id=self._next_violation_id(),
                    violation_type=ViolationType.MISSING_REQUIRED,
                    severity=ViolationSeverity.ERROR,
                    message=f"Missing required field: {field}",
                    field_path=f"{context}.{field}",
                    rule_id="schema-required",
                ))

        # Check property types
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                value = data[prop_name]
                expected_type = prop_schema.get("type")
                if expected_type and not self._check_type(value, expected_type):
                    result.add_violation(Violation(
                        violation_id=self._next_violation_id(),
                        violation_type=ViolationType.TYPE_MISMATCH,
                        severity=ViolationSeverity.ERROR,
                        message=f"Type mismatch for {prop_name}: expected {expected_type}",
                        field_path=f"{context}.{prop_name}",
                        expected=expected_type,
                        actual=type(value).__name__,
                        rule_id="schema-type",
                    ))

                # Check enum constraints
                enum_values = prop_schema.get("enum")
                if enum_values and value not in enum_values:
                    result.add_violation(Violation(
                        violation_id=self._next_violation_id(),
                        violation_type=ViolationType.ENUM_VIOLATION,
                        severity=ViolationSeverity.ERROR,
                        message=f"Invalid value for {prop_name}: {value}",
                        field_path=f"{context}.{prop_name}",
                        expected=enum_values,
                        actual=value,
                        rule_id="schema-enum",
                    ))

        return result

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON Schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, allow
        return isinstance(value, expected)

    def _get_severity(self, rule: ValidationRule) -> ViolationSeverity:
        """Get violation severity from rule."""
        return ViolationSeverity.ERROR if rule.severity == "error" else ViolationSeverity.WARNING

    def _validate_required_field(
        self, rule: ValidationRule, value: Any, severity: ViolationSeverity
    ) -> Violation | None:
        """Check required field constraint."""
        if value is None:
            return Violation(
                violation_id=self._next_violation_id(),
                violation_type=ViolationType.MISSING_REQUIRED,
                severity=severity,
                message=rule.description,
                field_path=rule.field_path,
                rule_id=rule.rule_id,
                rationale=rule.rationale,
            )
        return None

    def _validate_type_check(
        self, rule: ValidationRule, value: Any, severity: ViolationSeverity
    ) -> Violation | None:
        """Check type constraint."""
        expected_type = rule.constraint.get("type")
        if value is not None and expected_type and not self._check_type(value, expected_type):
            return Violation(
                violation_id=self._next_violation_id(),
                violation_type=ViolationType.TYPE_MISMATCH,
                severity=severity,
                message=rule.description,
                field_path=rule.field_path,
                expected=expected_type,
                actual=type(value).__name__,
                rule_id=rule.rule_id,
                rationale=rule.rationale,
            )
        return None

    def _validate_enum_constraint(
        self, rule: ValidationRule, value: Any, severity: ViolationSeverity
    ) -> Violation | None:
        """Check enum constraint."""
        enum_values = rule.constraint.get("enum", [])
        if value is not None and value not in enum_values:
            return Violation(
                violation_id=self._next_violation_id(),
                violation_type=ViolationType.ENUM_VIOLATION,
                severity=severity,
                message=rule.description,
                field_path=rule.field_path,
                expected=enum_values,
                actual=value,
                rule_id=rule.rule_id,
                rationale=rule.rationale,
            )
        return None

    def _apply_validation_rule(
        self,
        rule: ValidationRule,
        artifacts: dict[str, Any],
    ) -> ValidationResult:
        """Apply a validation rule to artifacts."""
        result = ValidationResult(valid=True)
        severity = self._get_severity(rule)
        value = self._get_field_value(artifacts, rule.field_path)

        # Dispatch to appropriate validator
        validators = {
            "required_field": self._validate_required_field,
            "type_check": self._validate_type_check,
            "enum_constraint": self._validate_enum_constraint,
        }

        validator = validators.get(rule.check_type)
        if validator:
            violation = validator(rule, value, severity)
            if violation:
                result.add_violation(violation)

        return result

    def _get_field_value(self, data: dict[str, Any], field_path: str) -> Any:
        """Get value from nested dict using dot notation path.

        Args:
            data: Dictionary to search
            field_path: Path like "output.auth_method"

        Returns:
            Value at path or None if not found
        """
        parts = field_path.split(".")
        # Skip 'output' or 'input' prefix
        if parts and parts[0] in ("output", "input"):
            parts = parts[1:]

        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def check_escalation_triggers(
        self,
        stage_name: str,
        context: dict[str, Any],
    ) -> list[EscalationCheck]:
        """Check if any escalation triggers are met.

        Args:
            stage_name: Current stage name
            context: Context data for evaluation

        Returns:
            List of triggered escalations
        """
        triggered = []

        for trigger in self.contracts.escalation_triggers:
            # Check if trigger applies to this stage
            if trigger.stage and trigger.stage != stage_name:
                continue

            # Simple condition checking (could be extended with expression eval)
            if self._evaluate_trigger_condition(trigger, context):
                triggered.append(EscalationCheck(
                    triggered=True,
                    trigger=trigger,
                    context=context,
                ))

        return triggered

    def _evaluate_trigger_condition(
        self,
        trigger: EscalationTrigger,
        context: dict[str, Any],
    ) -> bool:
        """Evaluate a trigger condition.

        Currently supports simple keyword matching. Could be extended
        with expression evaluation.
        """
        condition = trigger.condition.lower()

        # Check for confidence threshold
        if "confidence" in condition and "below" in condition:
            confidence = context.get("confidence", 1.0)
            # Extract threshold from condition like "Confidence below 0.7"
            parts = condition.split()
            for i, part in enumerate(parts):
                if part == "below" and i + 1 < len(parts):
                    try:
                        threshold = float(parts[i + 1])
                        return confidence < threshold
                    except ValueError:
                        pass

        # Check for error conditions
        if "error" in condition or "fail" in condition:
            return context.get("has_errors", False)

        return False

    def _find_gate(self, gate_id: str):
        """Find a quality gate by ID."""
        for g in self.contracts.quality_gates:
            if g.gate_id == gate_id:
                return g
        return None

    def _evaluate_check(
        self, check: str, artifacts: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Evaluate a single quality gate check."""
        check_lower = check.lower()
        if "defined" in check_lower or "present" in check_lower:
            return bool(artifacts)
        if "test" in check_lower or "coverage" in check_lower:
            return context.get("tests_passed", True)
        if "security" in check_lower or "review" in check_lower:
            return context.get("security_approved", False)
        return True  # Default to passed for unrecognized checks

    def check_quality_gate(
        self,
        gate_id: str,
        artifacts: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> QualityGateResult:
        """Evaluate a quality gate.

        Args:
            gate_id: ID of the gate to check
            artifacts: Artifacts to check
            context: Additional context

        Returns:
            QualityGateResult
        """
        context = context or {}
        gate = self._find_gate(gate_id)

        if gate is None:
            return QualityGateResult(
                passed=True, gate_id=gate_id,
                passed_checks=["Gate not found - passing by default"],
            )

        passed_checks = []
        failed_checks = []
        for check in gate.checks:
            if self._evaluate_check(check, artifacts, context):
                passed_checks.append(check)
            else:
                failed_checks.append(check)

        return QualityGateResult(
            passed=len(failed_checks) == 0,
            gate_id=gate_id,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            action=gate.failure_action if failed_checks else "",
        )

    def validate_operation(
        self,
        operation_type: str,
        operation_context: dict[str, Any],
    ) -> ValidationResult:
        """Validate an operation against operation contracts.

        Args:
            operation_type: Type of operation (e.g., "tool_call", "git")
            operation_context: Context of the operation

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True, context=operation_type)

        # Get relevant rules from operation contracts
        rules = self.operation_manager.get_rules_for_check_type(operation_type)

        for rule in rules:
            if self._check_operation_rule(rule, operation_context):
                severity = (
                    ViolationSeverity.ERROR
                    if rule.severity == "error"
                    else ViolationSeverity.WARNING
                )
                result.add_violation(Violation(
                    violation_id=self._next_violation_id(),
                    violation_type=ViolationType.OPERATION_RULE,
                    severity=severity,
                    message=rule.description,
                    rule_id=rule.rule_id,
                    rationale=rule.rationale,
                ))

        return result

    def _check_operation_rule(
        self,
        rule: OperationRule,
        context: dict[str, Any],
    ) -> bool:
        """Check if an operation rule is violated.

        Returns True if the rule IS violated.
        """
        # Implementation depends on rule type
        # This is a placeholder for actual rule checking logic
        return False

    def get_summary(self, results: list[ValidationResult]) -> dict[str, Any]:
        """Get summary of validation results.

        Args:
            results: List of validation results

        Returns:
            Summary dictionary
        """
        total_errors = sum(r.error_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        all_valid = all(r.valid for r in results)

        return {
            "valid": all_valid,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "stages_checked": len(results),
            "results": [
                {
                    "stage": r.stage_name,
                    "context": r.context,
                    "valid": r.valid,
                    "errors": r.error_count,
                    "warnings": r.warning_count,
                }
                for r in results
            ],
        }
