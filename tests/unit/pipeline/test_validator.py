# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
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


# =============================================================================
# Schema-based Stage Validation Tests
# =============================================================================


class TestStageInputValidation:
    """Tests for schema-based stage input validation."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_intake_stage_no_requirements(self, validator):
        """Intake stage has no required inputs (first stage)."""
        errors = validator.validate_stage_input("intake", {})
        assert len(errors) == 0

    def test_clarify_stage_requires_request_id(self, validator):
        """Clarify stage requires request_id and detected_scope."""
        errors = validator.validate_stage_input("clarify", {})
        assert len(errors) == 2
        assert any("request_id" in e for e in errors)
        assert any("detected_scope" in e for e in errors)

        errors = validator.validate_stage_input("clarify", {
            "request_id": "req-123",
            "detected_scope": "feature",
        })
        assert len(errors) == 0

    def test_spec_stage_requires_analysis(self, validator):
        """Spec stage requires request_id, analysis, and components."""
        errors = validator.validate_stage_input("spec", {})
        assert len(errors) == 3

        errors = validator.validate_stage_input("spec", {
            "request_id": "req-123",
            "analysis": {"summary": "test", "impact": "low"},
            "components": [{"name": "comp1", "path": "/src/comp.py"}],
        })
        assert len(errors) == 0

    def test_red_stage_requires_spec_and_test_cases(self, validator):
        """Red stage requires spec_id, components, and test_cases."""
        errors = validator.validate_stage_input("red", {})
        assert len(errors) == 3

        errors = validator.validate_stage_input("red", {
            "spec_id": "spec-123",
            "components": [],
            "test_cases": [],
        })
        assert len(errors) == 0

    def test_green_stage_requires_tests(self, validator):
        """Green stage requires spec_id, test_files, and failing_tests."""
        errors = validator.validate_stage_input("green", {})
        assert len(errors) == 3

        errors = validator.validate_stage_input("green", {
            "spec_id": "spec-123",
            "test_files": [],
            "failing_tests": ["test_1"],
        })
        assert len(errors) == 0


class TestStageOutputValidation:
    """Tests for schema-based stage output validation."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_intake_output_requires_request_id(self, validator):
        """Intake output requires request_id, detected_scope, original_request."""
        errors = validator.validate_stage_output("intake", {})
        assert len(errors) == 3

        errors = validator.validate_stage_output("intake", {
            "request_id": "req-123",
            "detected_scope": "feature",
            "original_request": "Add a logout button",
        })
        assert len(errors) == 0

    def test_red_output_requires_test_files(self, validator):
        """Red output requires spec_id, test_files, and test_results."""
        errors = validator.validate_stage_output("red", {})
        assert len(errors) == 3

        errors = validator.validate_stage_output("red", {
            "spec_id": "spec-123",
            "test_files": [{"path": "test_foo.py", "content": "def test..."}],
            "test_results": {"passed": 0, "failed": 1, "total": 1},
        })
        assert len(errors) == 0

    def test_green_output_requires_implementation(self, validator):
        """Green output requires spec_id, implementation_files, test_results."""
        errors = validator.validate_stage_output("green", {})
        assert len(errors) == 3

        errors = validator.validate_stage_output("green", {
            "spec_id": "spec-123",
            "implementation_files": [{"path": "foo.py", "content": "class..."}],
            "test_results": {"passed": 1, "failed": 0, "total": 1},
        })
        assert len(errors) == 0


class TestTransitionValidation:
    """Tests for stage transition validation."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_valid_intake_to_clarify(self, validator):
        """Valid intake→clarify transition."""
        artifacts = {
            "request_id": "req-123",
            "detected_scope": "feature",
            "original_request": "Add feature",
        }
        errors = validator.validate_transition("intake", "clarify", artifacts)
        assert len(errors) == 0

    def test_invalid_intake_to_spec(self, validator):
        """Invalid intake→spec transition (skipping clarify)."""
        artifacts = {
            "request_id": "req-123",
            "detected_scope": "feature",
            "original_request": "Add feature",
        }
        errors = validator.validate_transition("intake", "spec", artifacts)
        assert len(errors) == 1
        assert "Invalid transition" in errors[0]

    def test_valid_red_to_green(self, validator):
        """Valid red→green transition."""
        artifacts = {
            "spec_id": "spec-123",
            "test_files": [{"path": "test_foo.py", "content": "..."}],
            "test_results": {"passed": 0, "failed": 1, "total": 1},
            "failing_tests": ["test_foo"],
        }
        errors = validator.validate_transition("red", "green", artifacts)
        assert len(errors) == 0

    def test_transition_missing_required_for_next(self, validator):
        """Transition fails when missing required artifacts for next stage."""
        # Has intake output but missing clarify requirements
        artifacts = {
            "request_id": "req-123",
            "detected_scope": "feature",
            "original_request": "Add feature",
            # Missing clarified_requirements for analyze stage
        }
        errors = validator.validate_transition("clarify", "analyze", artifacts)
        # Should have error for missing clarified_requirements
        assert any("clarified_requirements" in str(e) for e in errors)


class TestLanguageSpecificValidation:
    """Tests for language-specific output validation."""

    @pytest.fixture
    def validator(self):
        return ArtifactValidator()

    def test_python_test_file_extension(self, validator):
        """Python test files should have .py extension."""
        artifacts = {
            "test_files": [{"path": "tests/test_foo.py", "content": "..."}],
        }
        errors = validator.validate_stage_output_for_language(
            "red", artifacts, "python"
        )
        assert len(errors) == 0

        # Wrong extension
        artifacts = {
            "test_files": [{"path": "tests/test_foo.ts", "content": "..."}],
        }
        errors = validator.validate_stage_output_for_language(
            "red", artifacts, "python"
        )
        assert len(errors) == 1
        assert "unexpected extension" in errors[0]

    def test_typescript_test_file_extension(self, validator):
        """TypeScript test files should have .ts or .tsx extension."""
        artifacts = {
            "test_files": [{"path": "tests/foo.spec.ts", "content": "..."}],
        }
        errors = validator.validate_stage_output_for_language(
            "red", artifacts, "typescript"
        )
        assert len(errors) == 0

    def test_csharp_implementation_extension(self, validator):
        """C# implementation files should have .cs extension."""
        artifacts = {
            "implementation_files": [{"path": "src/Foo.cs", "content": "..."}],
        }
        errors = validator.validate_stage_output_for_language(
            "green", artifacts, "csharp"
        )
        assert len(errors) == 0

        # Wrong extension
        artifacts = {
            "implementation_files": [{"path": "src/foo.py", "content": "..."}],
        }
        errors = validator.validate_stage_output_for_language(
            "green", artifacts, "csharp"
        )
        assert len(errors) == 1
