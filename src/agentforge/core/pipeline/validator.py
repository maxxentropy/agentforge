# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-validator
# @test_path: tests/unit/pipeline/test_validator.py

"""
Artifact Validator
==================

Validates artifacts between pipeline stage transitions.

Provides validation for:
- Required fields
- Type checking
- JSON schema validation
- Language-specific validation (Python, C#, TypeScript)
- Phase transition schema validation

The validation chain ensures artifacts flow correctly:
  INTAKE → CLARIFY → ANALYZE → SPEC → RED → GREEN → REFACTOR → DELIVER
"""

import logging
from typing import TYPE_CHECKING, Any

from .schemas import (
    STAGE_INPUT_REQUIREMENTS,
    get_input_schema,
    get_output_schema,
    validate_transition,
)

if TYPE_CHECKING:
    from .discovery_integration import DiscoveredContext

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when artifact validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class ArtifactValidator:
    """
    Validator for pipeline artifacts.

    Validates artifacts against required fields, types, and JSON schemas.
    """

    def validate(
        self,
        artifacts: dict[str, Any],
        schema: dict[str, Any],
    ) -> list[str]:
        """
        Validate artifacts against a JSON schema.

        Args:
            artifacts: Artifacts to validate
            schema: JSON schema dict

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in artifacts:
                errors.append(f"Missing required field: {field}")

        # Check property types
        properties = schema.get("properties", {})
        for field, prop_schema in properties.items():
            if field in artifacts:
                type_errors = self._validate_type(
                    field, artifacts[field], prop_schema
                )
                errors.extend(type_errors)

        return errors

    def _validate_type(
        self,
        field: str,
        value: Any,
        prop_schema: dict[str, Any],
    ) -> list[str]:
        """Validate a single field against its type schema."""
        errors = []
        expected_type = prop_schema.get("type")

        if expected_type is None:
            return errors

        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        python_type = type_map.get(expected_type)
        if python_type and not isinstance(value, python_type):
            errors.append(
                f"Field '{field}' expected type {expected_type}, "
                f"got {type(value).__name__}"
            )

        # Validate array items if specified
        if expected_type == "array" and isinstance(value, list):
            items_schema = prop_schema.get("items", {})
            if items_schema:
                for i, item in enumerate(value):
                    item_errors = self._validate_type(
                        f"{field}[{i}]", item, items_schema
                    )
                    errors.extend(item_errors)

        return errors

    def validate_required(
        self,
        artifacts: dict[str, Any],
        required: list[str],
    ) -> list[str]:
        """
        Check that required keys are present.

        Args:
            artifacts: Artifacts to check
            required: List of required keys

        Returns:
            List of error messages for missing keys
        """
        errors = []
        for key in required:
            if key not in artifacts:
                errors.append(f"Missing required artifact: {key}")
            elif artifacts[key] is None:
                errors.append(f"Required artifact '{key}' is None")
        return errors

    def validate_types(
        self,
        artifacts: dict[str, Any],
        types: dict[str, type | tuple],
    ) -> list[str]:
        """
        Validate artifact value types.

        Args:
            artifacts: Artifacts to validate
            types: Dict mapping keys to expected types

        Returns:
            List of type mismatch errors
        """
        errors = []
        for key, expected_type in types.items():
            if key in artifacts:
                value = artifacts[key]
                if not isinstance(value, expected_type):
                    if isinstance(expected_type, tuple):
                        type_names = " or ".join(t.__name__ for t in expected_type)
                    else:
                        type_names = expected_type.__name__
                    errors.append(
                        f"Artifact '{key}' expected {type_names}, "
                        f"got {type(value).__name__}"
                    )
        return errors

    def validate_and_raise(
        self,
        artifacts: dict[str, Any],
        schema: dict[str, Any] = None,
        required: list[str] = None,
        types: dict[str, type] = None,
    ) -> None:
        """
        Validate artifacts and raise ValidationError if invalid.

        Args:
            artifacts: Artifacts to validate
            schema: Optional JSON schema
            required: Optional list of required keys
            types: Optional type mapping

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        if schema:
            errors.extend(self.validate(artifacts, schema))

        if required:
            errors.extend(self.validate_required(artifacts, required))

        if types:
            errors.extend(self.validate_types(artifacts, types))

        if errors:
            raise ValidationError(errors)

    # =========================================================================
    # Schema-based Stage Validation
    # =========================================================================

    def validate_stage_input(
        self,
        stage_name: str,
        artifacts: dict[str, Any],
    ) -> list[str]:
        """
        Validate input artifacts for a stage using schema definitions.

        Args:
            stage_name: Name of the stage (intake, clarify, analyze, etc.)
            artifacts: Input artifacts to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        requirements = STAGE_INPUT_REQUIREMENTS.get(stage_name, {})
        required = requirements.get("required", [])
        return self.validate_required(artifacts, required)

    def validate_stage_output(
        self,
        stage_name: str,
        artifacts: dict[str, Any],
    ) -> list[str]:
        """
        Validate output artifacts from a stage using schema definitions.

        Args:
            stage_name: Name of the stage
            artifacts: Output artifacts to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        schema = get_output_schema(stage_name)
        if not schema:
            return []
        return self.validate(artifacts, schema)

    def validate_transition(
        self,
        from_stage: str,
        to_stage: str,
        artifacts: dict[str, Any],
    ) -> list[str]:
        """
        Validate a stage transition with artifact flow.

        Checks that:
        1. The transition is valid
        2. Output from from_stage is valid
        3. Input requirements for to_stage are satisfied

        Args:
            from_stage: Stage we're transitioning from
            to_stage: Stage we're transitioning to
            artifacts: Accumulated artifacts

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check valid transition
        if not validate_transition(from_stage, to_stage):
            errors.append(
                f"Invalid transition: {from_stage} → {to_stage}"
            )
            return errors  # Don't continue if transition is invalid

        # Validate output schema of from_stage
        errors.extend(self.validate_stage_output(from_stage, artifacts))

        # Validate input requirements of to_stage
        errors.extend(self.validate_stage_input(to_stage, artifacts))

        return errors

    def validate_stage_output_for_language(
        self,
        stage_name: str,
        artifacts: dict[str, Any],
        language: str,
    ) -> list[str]:
        """
        Validate stage output with language-specific rules.

        Args:
            stage_name: Name of the stage
            artifacts: Stage output artifacts
            language: Primary language (python, csharp, typescript)

        Returns:
            List of validation error messages (empty if valid)
        """
        # Import here to avoid circular imports
        from .discovery_integration import validate_stage_output_for_language

        return validate_stage_output_for_language(stage_name, artifacts, language)


# Module-level validator instance for convenience
_validator = ArtifactValidator()


def validate_artifacts(
    artifacts: dict[str, Any],
    schema: dict[str, Any] = None,
    required: list[str] = None,
    types: dict[str, type] = None,
) -> list[str]:
    """
    Convenience function to validate artifacts.

    Args:
        artifacts: Artifacts to validate
        schema: Optional JSON schema
        required: Optional list of required keys
        types: Optional type mapping

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if schema:
        errors.extend(_validator.validate(artifacts, schema))

    if required:
        errors.extend(_validator.validate_required(artifacts, required))

    if types:
        errors.extend(_validator.validate_types(artifacts, types))

    return errors
