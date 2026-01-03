# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: frame-logger
# @test_path: tests/unit/audit/test_frame_logger.py

"""
Frame Logger
============

Logs context frames with schema-aware validation.

The FrameLogger bridges the contract/schema system with the audit trail,
ensuring that every logged frame captures:
- The governing schemas for input and output
- Validated context at each step
- Raw LLM responses wrapped with parsed artifacts
- Validation status for contract compliance auditing

Integration with Pipeline:
    The FrameLogger can be injected into stage executors to automatically
    capture frames at each stage transition, with schema references
    resolved from the pipeline's schema registry.

Usage:
    ```python
    logger = FrameLogger(project_path, thread_id)

    # Log a stage execution frame
    logger.log_stage_frame(
        stage_name="intake",
        input_artifacts={"request": "Add login feature"},
        system_prompt="You are an intake processor...",
        user_message="Process this request: ...",
        raw_response="```yaml\\nrequest_id: REQ-001...",
        parsed_artifact={"request_id": "REQ-001", ...},
        pipeline_id="pipeline-001",
    )
    ```
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .context_frame import (
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
from .integrity_chain import IntegrityChain, compute_hash


class FrameLogger:
    """
    Logs context frames with schema-aware validation.

    Each frame captures a complete, validated snapshot of execution state,
    enabling contract compliance auditing and full reproducibility.
    """

    def __init__(self, project_path: Path, thread_id: str):
        """
        Initialize frame logger for a thread.

        Args:
            project_path: Root project directory
            thread_id: Unique thread identifier
        """
        self.project_path = Path(project_path).resolve()
        self.thread_id = thread_id

        self.thread_dir = self.project_path / ".agentforge" / "audit" / "threads" / thread_id
        self.frames_dir = self.thread_dir / "frames"
        self.frames_dir.mkdir(parents=True, exist_ok=True)

        self._sequence = self._get_next_sequence()
        self._integrity_chain = IntegrityChain(self.thread_dir)
        self._last_hash: str | None = self._integrity_chain.get_last_hash()

        # Schema registry for resolving schema references
        self._schema_registry: dict[str, dict[str, Any]] = {}

    def register_schemas(self, schemas: dict[str, dict[str, Any]]) -> None:
        """
        Register schemas for validation.

        Args:
            schemas: Mapping of schema_id to schema definition
        """
        self._schema_registry.update(schemas)

    def get_schema(self, schema_id: str) -> dict[str, Any] | None:
        """Get a registered schema by ID."""
        return self._schema_registry.get(schema_id)

    def log_stage_frame(
        self,
        stage_name: str,
        input_artifacts: dict[str, Any],
        system_prompt: str,
        user_message: str,
        raw_response: str,
        parsed_artifact: dict[str, Any] | None,
        model: str = "claude-sonnet-4-20250514",
        thinking: str | None = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_thinking: int = 0,
        tokens_cached: int = 0,
        duration_ms: int = 0,
        pipeline_id: str | None = None,
        parse_method: str = "yaml_block",
        input_schema_id: str | None = None,
        output_schema_id: str | None = None,
    ) -> ContextFrame:
        """
        Log a pipeline stage execution frame.

        Args:
            stage_name: Name of the stage (intake, clarify, etc.)
            input_artifacts: Input artifacts for this stage
            system_prompt: System prompt sent to LLM
            user_message: User message sent to LLM
            raw_response: Complete LLM response
            parsed_artifact: Artifact parsed from response (or None if parsing failed)
            model: LLM model used
            thinking: Extended thinking content
            tokens_*: Token usage breakdown
            duration_ms: Execution duration
            pipeline_id: Pipeline ID if applicable
            parse_method: How the artifact was parsed
            input_schema_id: Schema ID for input validation
            output_schema_id: Schema ID for output validation

        Returns:
            The created ContextFrame
        """
        frame_id = f"FRAME-{self._sequence:04d}"
        self._sequence += 1

        # Resolve schemas
        input_schema = self._resolve_schema(input_schema_id, f"{stage_name}_input")
        output_schema = self._resolve_schema(output_schema_id, f"{stage_name}_output")

        # Build frame
        builder = ContextFrameBuilder(frame_id, self.thread_id, self._sequence - 1)
        builder.with_stage(stage_name, pipeline_id)

        # Input context with validation
        builder.with_input_context(
            data=input_artifacts,
            schema=input_schema,
            schema_id=input_schema_id or f"{stage_name}_input",
            required_fields=self._get_required_fields(input_schema),
        )

        # LLM interaction
        builder.with_llm_interaction(
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

        # Parsed artifact with validation
        builder.with_parsed_artifact(
            artifact_data=parsed_artifact,
            parse_method=parse_method,
            schema=output_schema,
            schema_id=output_schema_id or f"{stage_name}_output",
            artifact_type=f"{stage_name.capitalize()}Artifact",
        )

        builder.with_duration(duration_ms)

        frame = builder.build()

        # Persist the frame
        self._persist_frame(frame)

        return frame

    def log_agent_step(
        self,
        input_context: dict[str, Any],
        system_prompt: str,
        user_message: str,
        raw_response: str,
        action_name: str | None = None,
        action_params: dict[str, Any] | None = None,
        model: str = "claude-sonnet-4-20250514",
        thinking: str | None = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_thinking: int = 0,
        duration_ms: int = 0,
    ) -> ContextFrame:
        """
        Log a single agent step frame.

        Args:
            input_context: Context provided to the agent
            system_prompt: System prompt
            user_message: User message
            raw_response: LLM response
            action_name: Parsed action name
            action_params: Parsed action parameters
            model: Model used
            thinking: Extended thinking
            tokens_*: Token usage
            duration_ms: Step duration

        Returns:
            The created ContextFrame
        """
        frame_id = f"FRAME-{self._sequence:04d}"
        self._sequence += 1

        builder = ContextFrameBuilder(frame_id, self.thread_id, self._sequence - 1)
        builder.with_type(FrameType.AGENT_STEP)

        # Input context
        builder.with_input_context(data=input_context)

        # LLM interaction
        builder.with_llm_interaction(
            system_prompt=system_prompt,
            user_message=user_message,
            raw_response=raw_response,
            model=model,
            thinking=thinking,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_thinking=tokens_thinking,
            duration_ms=duration_ms,
        )

        # Parsed artifact (action)
        if action_name:
            builder.with_parsed_artifact(
                artifact_data={"action": action_name, "params": action_params},
                parse_method="action_block",
            )

        builder.with_duration(duration_ms)

        frame = builder.build()
        self._persist_frame(frame)

        return frame

    def log_human_interaction(
        self,
        prompt: str,
        response: str | None,
        context: dict[str, Any],
        duration_ms: int = 0,
    ) -> ContextFrame:
        """
        Log a human-in-the-loop interaction frame.

        Args:
            prompt: Question shown to human
            response: Human's response
            context: Full context at time of escalation
            duration_ms: Time human took to respond

        Returns:
            The created ContextFrame
        """
        frame_id = f"FRAME-{self._sequence:04d}"
        self._sequence += 1

        builder = ContextFrameBuilder(frame_id, self.thread_id, self._sequence - 1)
        builder.with_type(FrameType.HUMAN_INTERACTION)

        # Full context at escalation
        builder.with_input_context(data=context)

        # Capture as a special LLM-like interaction
        builder.with_llm_interaction(
            system_prompt="[Human Escalation]",
            user_message=prompt,
            raw_response=response or "[No response]",
            model="human",
            duration_ms=duration_ms,
        )

        # The "artifact" is the human decision
        builder.with_parsed_artifact(
            artifact_data={"prompt": prompt, "response": response},
            parse_method="human_input",
        )

        builder.with_duration(duration_ms)

        frame = builder.build()
        self._persist_frame(frame)

        return frame

    def log_spawn(
        self,
        spawned_thread_id: str,
        reason: str,
        delegated_context: dict[str, Any] | None = None,
    ) -> ContextFrame:
        """
        Log a spawn/delegation frame.

        Args:
            spawned_thread_id: ID of spawned child thread
            reason: Why spawn occurred
            delegated_context: Context passed to child

        Returns:
            The created ContextFrame
        """
        frame_id = f"FRAME-{self._sequence:04d}"
        self._sequence += 1

        builder = ContextFrameBuilder(frame_id, self.thread_id, self._sequence - 1)
        builder.with_type(FrameType.SPAWN)

        # Context being delegated
        builder.with_input_context(data=delegated_context or {})

        # The spawn action
        builder.with_parsed_artifact(
            artifact_data={
                "spawned_thread_id": spawned_thread_id,
                "reason": reason,
            },
            parse_method="spawn_action",
        )

        frame = builder.build()
        self._persist_frame(frame)

        return frame

    def get_frame(self, frame_id: str) -> ContextFrame | None:
        """Get a frame by ID."""
        frame_path = self.frames_dir / f"{frame_id}.yaml"
        if not frame_path.exists():
            return None

        data = yaml.safe_load(frame_path.read_text(encoding="utf-8"))
        return self._dict_to_frame(data)

    def list_frames(self) -> list[str]:
        """List all frame IDs in order."""
        frames = []
        for path in sorted(self.frames_dir.glob("FRAME-*.yaml")):
            frames.append(path.stem)
        return frames

    def get_frame_content(self, frame_id: str) -> str | None:
        """Get full LLM content for a frame."""
        content_path = self.frames_dir / f"{frame_id}-llm.md"
        if content_path.exists():
            return content_path.read_text(encoding="utf-8")
        return None

    def get_validation_summary(self) -> dict[str, Any]:
        """Get summary of validation results across all frames."""
        frames = self.list_frames()
        summary = {
            "total_frames": len(frames),
            "input_validation": {"passed": 0, "failed": 0, "skipped": 0},
            "output_validation": {"passed": 0, "failed": 0, "skipped": 0},
            "all_valid": True,
            "failures": [],
        }

        for frame_id in frames:
            frame = self.get_frame(frame_id)
            if frame:
                # Check input validation
                if frame.input_context:
                    status = frame.input_context.validation.status.value
                    summary["input_validation"][status] += 1
                    if status == "failed":
                        summary["all_valid"] = False
                        summary["failures"].append({
                            "frame_id": frame_id,
                            "type": "input",
                            "errors": frame.input_context.validation.errors,
                        })

                # Check output validation
                if frame.parsed_artifact:
                    status = frame.parsed_artifact.validation.status.value
                    summary["output_validation"][status] += 1
                    if status == "failed":
                        summary["all_valid"] = False
                        summary["failures"].append({
                            "frame_id": frame_id,
                            "type": "output",
                            "errors": frame.parsed_artifact.validation.errors,
                        })

        return summary

    def _persist_frame(self, frame: ContextFrame) -> Path:
        """Persist a frame to disk."""
        # Compute content hash and link to chain
        frame_data = frame.to_dict()
        block = self._integrity_chain.append(frame.frame_id, frame_data)

        frame.previous_frame_hash = block.previous_hash
        frame.content_hash = block.content_hash
        self._last_hash = block.content_hash

        # Save frame metadata
        frame_path = self.frames_dir / f"{frame.frame_id}.yaml"
        frame_path.write_text(
            yaml.dump(frame.to_dict(), default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        # Save full LLM content separately
        if frame.llm_interaction:
            llm_path = self.frames_dir / f"{frame.frame_id}-llm.md"
            llm_path.write_text(frame.llm_interaction.to_markdown(), encoding="utf-8")

        # Save thinking if large
        if frame.llm_interaction and frame.llm_interaction.thinking:
            if len(frame.llm_interaction.thinking) > 1000:
                thinking_path = self.frames_dir / f"{frame.frame_id}-thinking.md"
                thinking_path.write_text(
                    f"# Frame {frame.frame_id} Thinking\n\n{frame.llm_interaction.thinking}",
                    encoding="utf-8",
                )

        return frame_path

    def _resolve_schema(
        self, schema_id: str | None, default_id: str
    ) -> dict[str, Any] | None:
        """Resolve a schema by ID or default.

        Only resolves schemas from the registry or pipeline if an explicit
        schema_id is provided. When schema_id is None, returns None to skip
        validation.
        """
        if not schema_id:
            return None

        if schema_id in self._schema_registry:
            return self._schema_registry[schema_id]

        # Try to load from pipeline schemas only if explicitly requested
        try:
            from agentforge.core.pipeline.schemas import STAGE_OUTPUT_SCHEMAS

            stage_name = default_id.replace("_input", "").replace("_output", "")
            if stage_name in STAGE_OUTPUT_SCHEMAS:
                return STAGE_OUTPUT_SCHEMAS[stage_name]
        except ImportError:
            pass

        return None

    def _get_required_fields(self, schema: dict[str, Any] | None) -> list[str]:
        """Extract required fields from schema."""
        if schema:
            return schema.get("required", [])
        return []

    def _get_next_sequence(self) -> int:
        """Get next frame sequence number."""
        existing = list(self.frames_dir.glob("FRAME-*.yaml"))
        if not existing:
            return 1
        max_seq = 0
        for path in existing:
            try:
                seq = int(path.stem.split("-")[1])
                max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                pass
        return max_seq + 1

    def _dict_to_frame(self, data: dict[str, Any]) -> ContextFrame:
        """Convert dictionary to ContextFrame with full nested object reconstruction."""
        # Reconstruct input_context if present
        input_context = None
        if "input_context" in data:
            input_context = self._dict_to_validated_context(data["input_context"])

        # Reconstruct parsed_artifact if present
        parsed_artifact = None
        if "parsed_artifact" in data:
            parsed_artifact = self._dict_to_parsed_artifact(data["parsed_artifact"])

        return ContextFrame(
            frame_id=data.get("frame_id", ""),
            thread_id=data.get("thread_id", self.thread_id),
            sequence=data.get("sequence", 0),
            frame_type=FrameType(data.get("frame_type", "agent_step")),
            stage_name=data.get("stage_name"),
            pipeline_id=data.get("pipeline_id"),
            timestamp=data.get("timestamp", ""),
            duration_ms=data.get("duration_ms", 0),
            previous_frame_hash=data.get("previous_frame_hash"),
            content_hash=data.get("content_hash"),
            input_context=input_context,
            parsed_artifact=parsed_artifact,
        )

    def _dict_to_validation_result(self, data: dict[str, Any]) -> ValidationResult:
        """Convert dictionary to ValidationResult."""
        status_str = data.get("status", "skipped")
        status = ValidationStatus(status_str)

        schema_ref = None
        if "schema" in data:
            schema_data = data["schema"]
            schema_ref = SchemaReference(
                schema_id=schema_data.get("schema_id", ""),
                schema_type=schema_data.get("schema_type", "json_schema"),
                schema_version=schema_data.get("schema_version", "1.0"),
                schema_location=schema_data.get("schema_location"),
                schema_content=schema_data.get("schema_content"),
            )

        return ValidationResult(
            status=status,
            schema_ref=schema_ref,
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            validated_at=data.get("validated_at", ""),
        )

    def _dict_to_validated_context(self, data: dict[str, Any]) -> ValidatedContext:
        """Convert dictionary to ValidatedContext."""
        validation = self._dict_to_validation_result(data.get("validation", {}))

        return ValidatedContext(
            data=data.get("data", {}),
            validation=validation,
            required_fields=data.get("required_fields", []),
            used_fields=data.get("used_fields"),
        )

    def _dict_to_parsed_artifact(self, data: dict[str, Any]) -> ParsedArtifact:
        """Convert dictionary to ParsedArtifact."""
        validation = self._dict_to_validation_result(data.get("validation", {}))

        return ParsedArtifact(
            artifact_data=data.get("artifact_data"),
            parse_method=data.get("parse_method", "unknown"),
            validation=validation,
            artifact_type=data.get("artifact_type"),
        )
