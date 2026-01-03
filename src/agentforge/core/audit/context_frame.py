# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: context-frame
# @test_path: tests/unit/audit/test_context_frame.py

"""
Context Frame
=============

A Context Frame is a validated snapshot of execution context at a point in time.

Unlike raw conversation logging, frames capture:
- The governing schemas/contracts for input and output
- Validated input context (what was sent to LLM)
- Raw LLM response wrapped in a validation envelope
- Parsed artifact extracted from the response
- Validation results (pass/fail, errors)
- The resulting context state after this frame

Frames enable:
- Complete reproducibility with schema verification
- Contract compliance auditing
- Traceability from free-form LLM text to structured artifacts
- Debugging of validation failures

Frame Lifecycle:
    1. INPUT_CONTEXT validated against input_schema
    2. LLM invoked with validated context
    3. Raw response captured
    4. Response parsed into artifact
    5. Artifact validated against output_schema
    6. OUTPUT_CONTEXT computed as delta from input
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ValidationStatus(str, Enum):
    """Result of schema validation."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Validation not required/applicable


class FrameType(str, Enum):
    """Type of context frame."""

    STAGE_EXECUTION = "stage_execution"  # Pipeline stage execution
    AGENT_STEP = "agent_step"  # Single agent step
    TOOL_CALL = "tool_call"  # Tool invocation
    HUMAN_INTERACTION = "human_interaction"  # HITL escalation
    SPAWN = "spawn"  # Agent delegation/spawn


@dataclass
class SchemaReference:
    """Reference to a schema/contract that governs validation."""

    schema_id: str  # e.g., "INTAKE_OUTPUT_SCHEMA", "spec-artifact-v1"
    schema_type: str  # "json_schema", "contract", "dataclass"
    schema_version: str = "1.0"
    schema_location: str | None = None  # Path to schema definition
    schema_content: dict[str, Any] | None = None  # Inline schema (for audit)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "schema_id": self.schema_id,
            "schema_type": self.schema_type,
            "schema_version": self.schema_version,
        }
        if self.schema_location:
            data["schema_location"] = self.schema_location
        if self.schema_content:
            data["schema_content"] = self.schema_content
        return data


@dataclass
class ValidationResult:
    """Result of validating data against a schema."""

    status: ValidationStatus
    schema_ref: SchemaReference | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "status": self.status.value,
            "validated_at": self.validated_at,
        }
        if self.schema_ref:
            data["schema"] = self.schema_ref.to_dict()
        if self.errors:
            data["errors"] = self.errors
        if self.warnings:
            data["warnings"] = self.warnings
        return data


@dataclass
class ValidatedContext:
    """Context data with validation status.

    Captures the structured data along with its validation result.
    This "wraps" the data in a validation envelope.
    """

    data: dict[str, Any]  # The actual context/artifact data
    validation: ValidationResult  # Validation result

    # For input contexts, what was the governing schema requirement
    required_fields: list[str] = field(default_factory=list)

    # Subset of data that was actually used (for compaction tracking)
    used_fields: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "data": self.data,
            "validation": self.validation.to_dict(),
            "required_fields": self.required_fields,
            "used_fields": self.used_fields,
        }

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.validation.status == ValidationStatus.PASSED


@dataclass
class LLMInteractionEnvelope:
    """Wraps a raw LLM interaction with context.

    This envelope captures the complete LLM interaction
    while keeping the raw response separate from parsed artifacts.
    """

    # Request
    system_prompt: str
    user_message: str
    model: str

    # Raw response
    raw_response: str
    thinking: str | None = None

    # Tokens
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_thinking: int = 0
    tokens_cached: int = 0

    # Timing
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "model": self.model,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "thinking": self.tokens_thinking,
                "cached": self.tokens_cached,
                "total": self.tokens_input + self.tokens_output + self.tokens_thinking,
            },
            # Store lengths, not full content (content in separate files)
            "content_lengths": {
                "system_prompt": len(self.system_prompt),
                "user_message": len(self.user_message),
                "raw_response": len(self.raw_response),
                "thinking": len(self.thinking) if self.thinking else 0,
            },
        }
        return data

    def to_markdown(self) -> str:
        """Format as markdown for archival."""
        parts = [f"# LLM Interaction\n"]
        parts.append(f"**Model:** {self.model}\n")
        parts.append(f"**Timestamp:** {self.timestamp}\n")
        parts.append(f"**Duration:** {self.duration_ms}ms\n")

        parts.append("\n## System Prompt\n```\n")
        parts.append(self.system_prompt)
        parts.append("\n```\n")

        parts.append("\n## User Message\n```\n")
        parts.append(self.user_message)
        parts.append("\n```\n")

        parts.append("\n## Response\n```\n")
        parts.append(self.raw_response)
        parts.append("\n```\n")

        if self.thinking:
            parts.append("\n## Extended Thinking\n")
            parts.append(self.thinking)
            parts.append("\n")

        return "".join(parts)


@dataclass
class ParsedArtifact:
    """Artifact parsed from LLM response with validation.

    Captures:
    - What was extracted from the raw LLM response
    - The schema it was validated against
    - The validation result
    """

    # The extracted artifact data
    artifact_data: dict[str, Any] | None

    # What parsing method was used
    parse_method: str  # "yaml_block", "json_block", "full_yaml", "tool_call", etc.

    # Validation against expected schema
    validation: ValidationResult

    # Artifact type if known
    artifact_type: str | None = None  # "IntakeArtifact", "SpecArtifact", etc.

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "parse_method": self.parse_method,
            "validation": self.validation.to_dict(),
        }
        if self.artifact_data:
            data["artifact_data"] = self.artifact_data
        if self.artifact_type:
            data["artifact_type"] = self.artifact_type
        return data

    @property
    def is_valid(self) -> bool:
        """Check if parsing and validation succeeded."""
        return (
            self.artifact_data is not None
            and self.validation.status == ValidationStatus.PASSED
        )


@dataclass
class ContextFrame:
    """
    A validated snapshot of execution context at a point in time.

    This is the core audit unit that captures:
    - Where we are in the execution (stage, step)
    - What governed the inputs (input schema)
    - The complete input context (validated)
    - The LLM interaction (wrapped)
    - What was parsed from the response (validated)
    - What governs the output (output schema)
    - The resulting context state
    """

    # Identity
    frame_id: str  # Format: FRAME-{sequence:04d}
    thread_id: str
    sequence: int

    # Classification
    frame_type: FrameType
    stage_name: str | None = None
    pipeline_id: str | None = None

    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    duration_ms: int = 0

    # Input context (validated)
    input_context: ValidatedContext | None = None
    input_schema_ref: SchemaReference | None = None

    # LLM interaction (wrapped)
    llm_interaction: LLMInteractionEnvelope | None = None

    # Parsed artifact from response (validated)
    parsed_artifact: ParsedArtifact | None = None
    output_schema_ref: SchemaReference | None = None

    # Output context (result of this frame)
    output_context: ValidatedContext | None = None

    # Context delta (what changed)
    context_delta: dict[str, Any] | None = None  # Keys added/modified/removed

    # Integrity
    previous_frame_hash: str | None = None
    content_hash: str | None = None

    # Optional fields: (attr_name, output_key, needs_to_dict)
    _OPTIONAL_FIELDS = [
        ("stage_name", "stage_name", False),
        ("pipeline_id", "pipeline_id", False),
        ("input_schema_ref", "input_schema", True),
        ("output_schema_ref", "output_schema", True),
        ("input_context", "input_context", True),
        ("output_context", "output_context", True),
        ("llm_interaction", "llm_interaction", True),
        ("parsed_artifact", "parsed_artifact", True),
        ("context_delta", "context_delta", False),
        ("previous_frame_hash", "previous_frame_hash", False),
        ("content_hash", "content_hash", False),
    ]

    def _collect_optional_fields(self) -> dict[str, Any]:
        """Collect optional fields that are set."""
        result = {}
        for attr, key, needs_to_dict in self._OPTIONAL_FIELDS:
            value = getattr(self, attr)
            if value is not None:
                result[key] = value.to_dict() if needs_to_dict else value
        return result

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "frame_id": self.frame_id,
            "thread_id": self.thread_id,
            "sequence": self.sequence,
            "frame_type": self.frame_type.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }
        data.update(self._collect_optional_fields())
        return data

    @property
    def is_valid(self) -> bool:
        """Check if both input and output validated successfully."""
        input_valid = self.input_context is None or self.input_context.is_valid
        artifact_valid = self.parsed_artifact is None or self.parsed_artifact.is_valid
        output_valid = self.output_context is None or self.output_context.is_valid
        return input_valid and artifact_valid and output_valid


class ContextFrameBuilder:
    """Builder for creating validated context frames.

    Provides a fluent interface for constructing frames
    with proper validation at each step.
    """

    def __init__(self, frame_id: str, thread_id: str, sequence: int):
        """Initialize frame builder."""
        self._frame = ContextFrame(
            frame_id=frame_id,
            thread_id=thread_id,
            sequence=sequence,
            frame_type=FrameType.AGENT_STEP,
        )

    def with_type(self, frame_type: FrameType) -> "ContextFrameBuilder":
        """Set frame type."""
        self._frame.frame_type = frame_type
        return self

    def with_stage(
        self, stage_name: str, pipeline_id: str | None = None
    ) -> "ContextFrameBuilder":
        """Set stage context."""
        self._frame.stage_name = stage_name
        self._frame.pipeline_id = pipeline_id
        self._frame.frame_type = FrameType.STAGE_EXECUTION
        return self

    def with_input_context(
        self,
        data: dict[str, Any],
        schema: dict[str, Any] | None = None,
        schema_id: str | None = None,
        required_fields: list[str] | None = None,
    ) -> "ContextFrameBuilder":
        """Set validated input context."""
        from .integrity_chain import compute_hash

        # Create schema reference if schema provided
        schema_ref = None
        if schema_id:
            schema_ref = SchemaReference(
                schema_id=schema_id,
                schema_type="json_schema",
                schema_content=schema,
            )
            self._frame.input_schema_ref = schema_ref

        # Validate against schema
        errors = []
        if schema:
            errors = self._validate_against_schema(data, schema)

        validation = ValidationResult(
            status=ValidationStatus.PASSED if not errors else ValidationStatus.FAILED,
            schema_ref=schema_ref,
            errors=errors,
        )

        self._frame.input_context = ValidatedContext(
            data=data,
            validation=validation,
            required_fields=required_fields or [],
        )
        return self

    def with_llm_interaction(
        self,
        system_prompt: str,
        user_message: str,
        raw_response: str,
        model: str,
        thinking: str | None = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_thinking: int = 0,
        tokens_cached: int = 0,
        duration_ms: int = 0,
    ) -> "ContextFrameBuilder":
        """Set LLM interaction envelope."""
        self._frame.llm_interaction = LLMInteractionEnvelope(
            system_prompt=system_prompt,
            user_message=user_message,
            raw_response=raw_response,
            model=model,
            thinking=thinking,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_thinking=tokens_thinking,
            tokens_cached=tokens_cached,
            duration_ms=duration_ms,
        )
        return self

    def with_parsed_artifact(
        self,
        artifact_data: dict[str, Any] | None,
        parse_method: str,
        schema: dict[str, Any] | None = None,
        schema_id: str | None = None,
        artifact_type: str | None = None,
    ) -> "ContextFrameBuilder":
        """Set parsed artifact with validation."""
        # Create schema reference
        schema_ref = None
        if schema_id:
            schema_ref = SchemaReference(
                schema_id=schema_id,
                schema_type="json_schema",
                schema_content=schema,
            )
            self._frame.output_schema_ref = schema_ref

        # Validate if we have data and schema
        errors = []
        if artifact_data and schema:
            errors = self._validate_against_schema(artifact_data, schema)

        status = ValidationStatus.SKIPPED
        if artifact_data is None:
            status = ValidationStatus.FAILED
            errors.append("Failed to parse artifact from response")
        elif not errors:
            status = ValidationStatus.PASSED
        else:
            status = ValidationStatus.FAILED

        validation = ValidationResult(
            status=status,
            schema_ref=schema_ref,
            errors=errors,
        )

        self._frame.parsed_artifact = ParsedArtifact(
            artifact_data=artifact_data,
            parse_method=parse_method,
            validation=validation,
            artifact_type=artifact_type,
        )
        return self

    def with_output_context(
        self,
        data: dict[str, Any],
        schema: dict[str, Any] | None = None,
        schema_id: str | None = None,
    ) -> "ContextFrameBuilder":
        """Set output context."""
        schema_ref = None
        if schema_id:
            schema_ref = SchemaReference(
                schema_id=schema_id,
                schema_type="json_schema",
                schema_content=schema,
            )

        errors = []
        if schema:
            errors = self._validate_against_schema(data, schema)

        validation = ValidationResult(
            status=ValidationStatus.PASSED if not errors else ValidationStatus.FAILED,
            schema_ref=schema_ref,
            errors=errors,
        )

        self._frame.output_context = ValidatedContext(
            data=data,
            validation=validation,
        )
        return self

    def with_context_delta(self, delta: dict[str, Any]) -> "ContextFrameBuilder":
        """Set context delta."""
        self._frame.context_delta = delta
        return self

    def with_duration(self, duration_ms: int) -> "ContextFrameBuilder":
        """Set frame duration."""
        self._frame.duration_ms = duration_ms
        return self

    def with_integrity(
        self, previous_hash: str | None, content_hash: str
    ) -> "ContextFrameBuilder":
        """Set integrity chain links."""
        self._frame.previous_frame_hash = previous_hash
        self._frame.content_hash = content_hash
        return self

    def build(self) -> ContextFrame:
        """Build and return the frame."""
        return self._frame

    def _validate_against_schema(
        self, data: dict[str, Any], schema: dict[str, Any]
    ) -> list[str]:
        """Validate data against JSON schema."""
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check property types
        properties = schema.get("properties", {})
        for field, prop_schema in properties.items():
            if field in data:
                expected_type = prop_schema.get("type")
                if expected_type:
                    type_map = {
                        "string": str,
                        "integer": int,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }
                    python_type = type_map.get(expected_type)
                    if python_type and not isinstance(data[field], python_type):
                        errors.append(
                            f"Field '{field}' expected {expected_type}, "
                            f"got {type(data[field]).__name__}"
                        )

        return errors
