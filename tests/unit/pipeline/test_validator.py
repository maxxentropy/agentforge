# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-validator

"""Tests for artifact validation."""

import pytest

from agentforge.core.pipeline import (
    ArtifactValidator,
    ValidationError,
    validate_artifacts,
)


class TestArtifactValidator:
    """Tests for ArtifactValidator."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_validate_required_fields(self, validator):
        """validate() checks required fields from schema."""
        schema = {
            "required": ["name", "version"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
            },
        }

        # Missing required
        errors = validator.validate({}, schema)
        assert len(errors) == 2
        assert "name" in errors[0] or "name" in errors[1]

        # Has required
        errors = validator.validate({"name": "test", "version": "1.0"}, schema)
        assert len(errors) == 0

    def test_validate_string_type(self, validator):
        """validate() checks string type."""
        schema = {
            "properties": {
                "name": {"type": "string"},
            },
        }

        errors = validator.validate({"name": "valid"}, schema)
        assert len(errors) == 0

        errors = validator.validate({"name": 123}, schema)
        assert len(errors) == 1
        assert "string" in errors[0]

    def test_validate_number_type(self, validator):
        """validate() checks number type."""
        schema = {
            "properties": {
                "count": {"type": "number"},
            },
        }

        errors = validator.validate({"count": 42}, schema)
        assert len(errors) == 0

        errors = validator.validate({"count": 3.14}, schema)
        assert len(errors) == 0

        errors = validator.validate({"count": "42"}, schema)
        assert len(errors) == 1

    def test_validate_array_type(self, validator):
        """validate() checks array type."""
        schema = {
            "properties": {
                "items": {"type": "array"},
            },
        }

        errors = validator.validate({"items": [1, 2, 3]}, schema)
        assert len(errors) == 0

        errors = validator.validate({"items": "not array"}, schema)
        assert len(errors) == 1

    def test_validate_object_type(self, validator):
        """validate() checks object type."""
        schema = {
            "properties": {
                "config": {"type": "object"},
            },
        }

        errors = validator.validate({"config": {"key": "value"}}, schema)
        assert len(errors) == 0

        errors = validator.validate({"config": [1, 2]}, schema)
        assert len(errors) == 1

    def test_validate_boolean_type(self, validator):
        """validate() checks boolean type."""
        schema = {
            "properties": {
                "enabled": {"type": "boolean"},
            },
        }

        errors = validator.validate({"enabled": True}, schema)
        assert len(errors) == 0

        errors = validator.validate({"enabled": "true"}, schema)
        assert len(errors) == 1

    def test_validate_array_items(self, validator):
        """validate() validates array item types."""
        schema = {
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "integer"},
                },
            },
        }

        errors = validator.validate({"numbers": [1, 2, 3]}, schema)
        assert len(errors) == 0

        errors = validator.validate({"numbers": [1, "two", 3]}, schema)
        assert len(errors) == 1
        assert "numbers[1]" in errors[0]


class TestValidateRequired:
    """Tests for validate_required()."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_all_present(self, validator):
        """No errors when all required keys present."""
        errors = validator.validate_required(
            {"a": 1, "b": 2, "c": 3},
            ["a", "b"],
        )
        assert len(errors) == 0

    def test_missing_keys(self, validator):
        """Errors for missing required keys."""
        errors = validator.validate_required(
            {"a": 1},
            ["a", "b", "c"],
        )
        assert len(errors) == 2
        assert any("b" in e for e in errors)
        assert any("c" in e for e in errors)

    def test_none_value(self, validator):
        """Error when required key has None value."""
        errors = validator.validate_required(
            {"a": None},
            ["a"],
        )
        assert len(errors) == 1
        assert "None" in errors[0]


class TestValidateTypes:
    """Tests for validate_types()."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_correct_types(self, validator):
        """No errors when types match."""
        errors = validator.validate_types(
            {"name": "test", "count": 42, "enabled": True},
            {"name": str, "count": int, "enabled": bool},
        )
        assert len(errors) == 0

    def test_wrong_types(self, validator):
        """Errors when types don't match."""
        errors = validator.validate_types(
            {"name": 123, "count": "not int"},
            {"name": str, "count": int},
        )
        assert len(errors) == 2

    def test_tuple_type(self, validator):
        """Multiple acceptable types via tuple."""
        errors = validator.validate_types(
            {"value": 3.14},
            {"value": (int, float)},
        )
        assert len(errors) == 0

        errors = validator.validate_types(
            {"value": "string"},
            {"value": (int, float)},
        )
        assert len(errors) == 1

    def test_missing_key_ignored(self, validator):
        """Missing keys are not type-checked."""
        errors = validator.validate_types(
            {"a": 1},
            {"a": int, "b": str},
        )
        assert len(errors) == 0


class TestValidateAndRaise:
    """Tests for validate_and_raise()."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_no_errors(self, validator):
        """No exception when valid."""
        validator.validate_and_raise(
            {"name": "test"},
            required=["name"],
            types={"name": str},
        )

    def test_raises_validation_error(self, validator):
        """Raises ValidationError when invalid."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_raise(
                {},
                required=["name"],
            )

        assert "name" in str(exc_info.value)
        assert len(exc_info.value.errors) == 1


class TestValidateArtifactsFunction:
    """Tests for validate_artifacts convenience function."""

    def test_with_required(self):
        """Works with required parameter."""
        errors = validate_artifacts(
            {"a": 1},
            required=["a", "b"],
        )
        assert len(errors) == 1
        assert "b" in errors[0]

    def test_with_types(self):
        """Works with types parameter."""
        errors = validate_artifacts(
            {"count": "not int"},
            types={"count": int},
        )
        assert len(errors) == 1

    def test_with_schema(self):
        """Works with schema parameter."""
        schema = {
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        errors = validate_artifacts({}, schema=schema)
        assert len(errors) == 1
