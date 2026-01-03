# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: context-frame-tests

"""Tests for ContextFrame and related contract-aware audit structures."""

import pytest

from agentforge.core.audit.context_frame import (
    ContextFrame,
    ContextFrameBuilder,
    FrameType,
    LLMInteractionEnvelope,
    ParsedArtifact,
    SchemaReference,
    ValidatedContext,
    ValidationResult,
    ValidationStatus,
)


class TestSchemaReference:
    """Tests for SchemaReference."""

    def test_schema_reference_to_dict(self):
        """Serialize schema reference."""
        ref = SchemaReference(
            schema_id="INTAKE_OUTPUT_SCHEMA",
            schema_type="json_schema",
            schema_version="1.0",
            schema_location="schemas.py",
        )

        data = ref.to_dict()

        assert data["schema_id"] == "INTAKE_OUTPUT_SCHEMA", "Expected data['schema_id'] to equal 'INTAKE_OUTPUT_SCHEMA'"
        assert data["schema_type"] == "json_schema", "Expected data['schema_type'] to equal 'json_schema'"
        assert data["schema_location"] == "schemas.py", "Expected data['schema_location'] to equal 'schemas.py'"


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_passed_validation(self):
        """Create passed validation result."""
        result = ValidationResult(status=ValidationStatus.PASSED)

        assert result.status == ValidationStatus.PASSED, "Expected result.status to equal ValidationStatus.PASSED"
        assert result.errors == [], "Expected result.errors to equal []"

    def test_failed_validation_with_errors(self):
        """Create failed validation with errors."""
        result = ValidationResult(
            status=ValidationStatus.FAILED,
            errors=["Missing required field: request_id"],
        )

        assert result.status == ValidationStatus.FAILED, "Expected result.status to equal ValidationStatus.FAILED"
        assert len(result.errors) == 1, "Expected len(result.errors) to equal 1"

    def test_to_dict(self):
        """Serialize validation result."""
        ref = SchemaReference(schema_id="test", schema_type="json_schema")
        result = ValidationResult(
            status=ValidationStatus.PASSED,
            schema_ref=ref,
        )

        data = result.to_dict()

        assert data["status"] == "passed", "Expected data['status'] to equal 'passed'"
        assert "schema" in data, "Expected 'schema' in data"
        assert data["schema"]["schema_id"] == "test", "Expected data['schema']['schema_id'] to equal 'test'"


class TestValidatedContext:
    """Tests for ValidatedContext."""

    def test_valid_context(self):
        """Create valid context."""
        context = ValidatedContext(
            data={"request_id": "REQ-001", "scope": "feature"},
            validation=ValidationResult(status=ValidationStatus.PASSED),
            required_fields=["request_id"],
        )

        assert context.is_valid, "Expected context.is_valid to be truthy"
        assert context.data["request_id"] == "REQ-001", "Expected context.data['request_id'] to equal 'REQ-001'"

    def test_invalid_context(self):
        """Create invalid context."""
        context = ValidatedContext(
            data={},
            validation=ValidationResult(
                status=ValidationStatus.FAILED,
                errors=["Missing required field: request_id"],
            ),
            required_fields=["request_id"],
        )

        assert not context.is_valid, "Assertion failed"
        assert len(context.validation.errors) == 1, "Expected len(context.validation.errors) to equal 1"


class TestLLMInteractionEnvelope:
    """Tests for LLMInteractionEnvelope."""

    def test_envelope_creation(self):
        """Create LLM interaction envelope."""
        envelope = LLMInteractionEnvelope(
            system_prompt="You are an expert.",
            user_message="Analyze this code.",
            raw_response="Here is my analysis...",
            model="claude-sonnet-4-20250514",
            thinking="Let me think about this...",
            tokens_input=100,
            tokens_output=50,
            tokens_thinking=30,
            duration_ms=1500,
        )

        assert envelope.model == "claude-sonnet-4-20250514", "Expected envelope.model to equal 'claude-sonnet-4-20250514'"
        assert envelope.tokens_input == 100, "Expected envelope.tokens_input to equal 100"
        assert len(envelope.system_prompt) > 0, "Expected len(envelope.system_prompt) > 0"

    def test_to_dict_stores_lengths(self):
        """to_dict stores content lengths, not full content."""
        envelope = LLMInteractionEnvelope(
            system_prompt="System prompt text",
            user_message="User message text",
            raw_response="Response text",
            model="claude-sonnet-4-20250514",
        )

        data = envelope.to_dict()

        assert "content_lengths" in data, "Expected 'content_lengths' in data"
        assert data["content_lengths"]["system_prompt"] == len("System prompt text"), "Expected data['content_lengths']['sy... to equal len('System prompt text')"
        assert data["content_lengths"]["user_message"] == len("User message text"), "Expected data['content_lengths']['us... to equal len('User message text')"

    def test_to_markdown(self):
        """Format envelope as markdown."""
        envelope = LLMInteractionEnvelope(
            system_prompt="You are an expert.",
            user_message="Analyze this.",
            raw_response="Analysis complete.",
            model="claude-sonnet-4-20250514",
        )

        md = envelope.to_markdown()

        assert "# LLM Interaction" in md, "Expected '# LLM Interaction' in md"
        assert "You are an expert." in md, "Expected 'You are an expert.' in md"
        assert "Analyze this." in md, "Expected 'Analyze this.' in md"
        assert "Analysis complete." in md, "Expected 'Analysis complete.' in md"


class TestParsedArtifact:
    """Tests for ParsedArtifact."""

    def test_valid_parsed_artifact(self):
        """Create valid parsed artifact."""
        artifact = ParsedArtifact(
            artifact_data={"request_id": "REQ-001", "scope": "feature"},
            parse_method="yaml_block",
            validation=ValidationResult(status=ValidationStatus.PASSED),
            artifact_type="IntakeArtifact",
        )

        assert artifact.is_valid, "Expected artifact.is_valid to be truthy"
        assert artifact.artifact_data["request_id"] == "REQ-001", "Expected artifact.artifact_data['req... to equal 'REQ-001'"

    def test_failed_parsing(self):
        """Handle failed parsing."""
        artifact = ParsedArtifact(
            artifact_data=None,
            parse_method="yaml_block",
            validation=ValidationResult(
                status=ValidationStatus.FAILED,
                errors=["Failed to parse artifact from response"],
            ),
        )

        assert not artifact.is_valid, "Assertion failed"
        assert artifact.artifact_data is None, "Expected artifact.artifact_data is None"


class TestContextFrameBuilder:
    """Tests for ContextFrameBuilder."""

    def test_build_stage_frame(self):
        """Build a complete stage execution frame."""
        frame = (
            ContextFrameBuilder("FRAME-0001", "thread-001", 1)
            .with_stage("intake", "pipeline-001")
            .with_input_context(
                data={"request": "Add login feature"},
                schema={"required": ["request"]},
                schema_id="intake_input",
            )
            .with_llm_interaction(
                system_prompt="You are an intake processor.",
                user_message="Process: Add login feature",
                raw_response="```yaml\nrequest_id: REQ-001\n```",
                model="claude-sonnet-4-20250514",
                tokens_input=100,
                tokens_output=50,
            )
            .with_parsed_artifact(
                artifact_data={"request_id": "REQ-001"},
                parse_method="yaml_block",
                schema={"required": ["request_id"]},
                schema_id="intake_output",
            )
            .with_duration(1500)
            .build()
        )

        assert frame.frame_id == "FRAME-0001", "Expected frame.frame_id to equal 'FRAME-0001'"
        assert frame.frame_type == FrameType.STAGE_EXECUTION, "Expected frame.frame_type to equal FrameType.STAGE_EXECUTION"
        assert frame.stage_name == "intake", "Expected frame.stage_name to equal 'intake'"
        assert frame.input_context is not None, "Expected frame.input_context is not None"
        assert frame.input_context.is_valid, "Expected frame.input_context.is_valid to be truthy"
        assert frame.llm_interaction is not None, "Expected frame.llm_interaction is not None"
        assert frame.parsed_artifact is not None, "Expected frame.parsed_artifact is not None"
        assert frame.parsed_artifact.is_valid, "Expected frame.parsed_artifact.is_valid to be truthy"

    def test_build_with_validation_failure(self):
        """Build frame with validation failure."""
        frame = (
            ContextFrameBuilder("FRAME-0001", "thread-001", 1)
            .with_stage("intake")
            .with_input_context(
                data={},  # Missing required field
                schema={"required": ["request"]},
            )
            .build()
        )

        assert frame.input_context is not None, "Expected frame.input_context is not None"
        assert not frame.input_context.is_valid, "Assertion failed"
        assert "Missing required field: request" in frame.input_context.validation.errors, "Expected 'Missing required field: re... in frame.input_context.validat..."

    def test_build_with_type_mismatch(self):
        """Build frame with type validation failure."""
        frame = (
            ContextFrameBuilder("FRAME-0001", "thread-001", 1)
            .with_stage("intake")
            .with_input_context(
                data={"request": 123},  # Should be string
                schema={
                    "required": ["request"],
                    "properties": {"request": {"type": "string"}},
                },
            )
            .build()
        )

        assert not frame.input_context.is_valid, "Assertion failed"
        assert any("expected string" in e for e in frame.input_context.validation.errors), "Expected any() to be truthy"


class TestContextFrame:
    """Tests for ContextFrame."""

    def test_frame_to_dict(self):
        """Serialize frame to dictionary."""
        frame = ContextFrame(
            frame_id="FRAME-0001",
            thread_id="thread-001",
            sequence=1,
            frame_type=FrameType.STAGE_EXECUTION,
            stage_name="intake",
            pipeline_id="pipeline-001",
            duration_ms=1500,
        )

        data = frame.to_dict()

        assert data["frame_id"] == "FRAME-0001", "Expected data['frame_id'] to equal 'FRAME-0001'"
        assert data["frame_type"] == "stage_execution", "Expected data['frame_type'] to equal 'stage_execution'"
        assert data["stage_name"] == "intake", "Expected data['stage_name'] to equal 'intake'"

    def test_frame_is_valid(self):
        """Check frame validity based on component validations."""
        frame = ContextFrame(
            frame_id="FRAME-0001",
            thread_id="thread-001",
            sequence=1,
            frame_type=FrameType.AGENT_STEP,
            input_context=ValidatedContext(
                data={},
                validation=ValidationResult(status=ValidationStatus.PASSED),
            ),
            parsed_artifact=ParsedArtifact(
                artifact_data={"action": "read_file"},
                parse_method="action_block",
                validation=ValidationResult(status=ValidationStatus.PASSED),
            ),
        )

        assert frame.is_valid, "Expected frame.is_valid to be truthy"

    def test_frame_invalid_with_failed_validation(self):
        """Frame is invalid if any validation failed."""
        frame = ContextFrame(
            frame_id="FRAME-0001",
            thread_id="thread-001",
            sequence=1,
            frame_type=FrameType.AGENT_STEP,
            parsed_artifact=ParsedArtifact(
                artifact_data=None,
                parse_method="action_block",
                validation=ValidationResult(status=ValidationStatus.FAILED),
            ),
        )

        assert not frame.is_valid, "Assertion failed"
