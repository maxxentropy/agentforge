# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: frame-logger-tests

"""Tests for FrameLogger - contract-aware frame logging."""

import yaml
import pytest

from agentforge.core.audit.frame_logger import FrameLogger
from agentforge.core.audit.context_frame import (
    FrameType,
    ValidationStatus,
)


class TestFrameLogger:
    """Tests for FrameLogger."""

    def test_log_stage_frame(self, tmp_path):
        """Log a complete stage execution frame."""
        logger = FrameLogger(tmp_path, "test-thread")

        # Register a schema
        logger.register_schemas({
            "intake_input": {"required": ["request"]},
            "intake_output": {"required": ["request_id"]},
        })

        frame = logger.log_stage_frame(
            stage_name="intake",
            input_artifacts={"request": "Add login feature"},
            system_prompt="You are an intake processor.",
            user_message="Process this request.",
            raw_response="```yaml\nrequest_id: REQ-001\n```",
            parsed_artifact={"request_id": "REQ-001"},
            pipeline_id="pipeline-001",
            input_schema_id="intake_input",
            output_schema_id="intake_output",
        )

        assert frame.frame_id == "FRAME-0001", "Expected frame.frame_id to equal 'FRAME-0001'"
        assert frame.frame_type == FrameType.STAGE_EXECUTION, "Expected frame.frame_type to equal FrameType.STAGE_EXECUTION"
        assert frame.stage_name == "intake", "Expected frame.stage_name to equal 'intake'"
        assert frame.input_context is not None, "Expected frame.input_context is not None"
        assert frame.input_context.is_valid, "Expected frame.input_context.is_valid to be truthy"
        assert frame.parsed_artifact is not None, "Expected frame.parsed_artifact is not None"
        assert frame.parsed_artifact.is_valid, "Expected frame.parsed_artifact.is_valid to be truthy"

    def test_log_stage_frame_with_validation_failure(self, tmp_path):
        """Log stage frame with input validation failure."""
        logger = FrameLogger(tmp_path, "test-thread")

        logger.register_schemas({
            "intake_input": {"required": ["request"]},
        })

        frame = logger.log_stage_frame(
            stage_name="intake",
            input_artifacts={},  # Missing required field
            system_prompt="...",
            user_message="...",
            raw_response="...",
            parsed_artifact=None,  # Parsing failed
            input_schema_id="intake_input",
        )

        assert not frame.input_context.is_valid, "Assertion failed"
        assert "Missing required field: request" in frame.input_context.validation.errors, "Expected 'Missing required field: re... in frame.input_context.validat..."

    def test_log_agent_step(self, tmp_path):
        """Log an agent step frame."""
        logger = FrameLogger(tmp_path, "test-thread")

        frame = logger.log_agent_step(
            input_context={"task": "fix bug", "file": "main.py"},
            system_prompt="You are a helpful assistant.",
            user_message="Fix the bug in main.py",
            raw_response="```action\nname: read_file\nparams:\n  path: main.py\n```",
            action_name="read_file",
            action_params={"path": "main.py"},
            tokens_input=100,
            tokens_output=50,
            duration_ms=1000,
        )

        assert frame.frame_type == FrameType.AGENT_STEP, "Expected frame.frame_type to equal FrameType.AGENT_STEP"
        assert frame.llm_interaction is not None, "Expected frame.llm_interaction is not None"
        assert frame.parsed_artifact is not None, "Expected frame.parsed_artifact is not None"
        assert frame.parsed_artifact.artifact_data["action"] == "read_file", "Expected frame.parsed_artifact.artif... to equal 'read_file'"

    def test_log_human_interaction(self, tmp_path):
        """Log a human-in-the-loop interaction frame."""
        logger = FrameLogger(tmp_path, "test-thread")

        frame = logger.log_human_interaction(
            prompt="Should we use OAuth or JWT?",
            response="Use JWT for stateless auth.",
            context={"current_auth": "none", "requirements": ["scalable"]},
            duration_ms=30000,
        )

        assert frame.frame_type == FrameType.HUMAN_INTERACTION, "Expected frame.frame_type to equal FrameType.HUMAN_INTERACTION"
        assert frame.input_context.data["current_auth"] == "none", "Expected frame.input_context.data['c... to equal 'none'"
        assert frame.parsed_artifact.artifact_data["response"] == "Use JWT for stateless auth.", "Expected frame.parsed_artifact.artif... to equal 'Use JWT for stateless auth.'"

    def test_log_spawn(self, tmp_path):
        """Log a spawn/delegation frame."""
        logger = FrameLogger(tmp_path, "test-thread")

        frame = logger.log_spawn(
            spawned_thread_id="child-thread-001",
            reason="Delegating security review",
            delegated_context={"task": "security audit", "files": ["auth.py"]},
        )

        assert frame.frame_type == FrameType.SPAWN, "Expected frame.frame_type to equal FrameType.SPAWN"
        assert frame.input_context.data["task"] == "security audit", "Expected frame.input_context.data['t... to equal 'security audit'"
        assert frame.parsed_artifact.artifact_data["spawned_thread_id"] == "child-thread-001", "Expected frame.parsed_artifact.artif... to equal 'child-thread-001'"

    def test_sequential_frame_ids(self, tmp_path):
        """Frames should have sequential IDs."""
        logger = FrameLogger(tmp_path, "test-thread")

        f1 = logger.log_agent_step({}, "...", "...", "...", "action1")
        f2 = logger.log_agent_step({}, "...", "...", "...", "action2")
        f3 = logger.log_agent_step({}, "...", "...", "...", "action3")

        assert f1.frame_id == "FRAME-0001", "Expected f1.frame_id to equal 'FRAME-0001'"
        assert f2.frame_id == "FRAME-0002", "Expected f2.frame_id to equal 'FRAME-0002'"
        assert f3.frame_id == "FRAME-0003", "Expected f3.frame_id to equal 'FRAME-0003'"

    def test_list_frames(self, tmp_path):
        """List all frames in order."""
        logger = FrameLogger(tmp_path, "test-thread")

        logger.log_agent_step({}, "...", "...", "...", "action1")
        logger.log_agent_step({}, "...", "...", "...", "action2")

        frames = logger.list_frames()

        assert frames == ["FRAME-0001", "FRAME-0002"], "Expected frames to equal ['FRAME-0001', 'FRAME-0002']"

    def test_get_frame(self, tmp_path):
        """Retrieve a specific frame."""
        logger = FrameLogger(tmp_path, "test-thread")

        logger.log_agent_step(
            {"task": "test"},
            "System prompt",
            "User message",
            "Response",
            action_name="test_action",
        )

        frame = logger.get_frame("FRAME-0001")

        assert frame is not None, "Expected frame is not None"
        assert frame.frame_id == "FRAME-0001", "Expected frame.frame_id to equal 'FRAME-0001'"

    def test_get_frame_content(self, tmp_path):
        """Get full LLM content for a frame."""
        logger = FrameLogger(tmp_path, "test-thread")

        logger.log_agent_step(
            {},
            "You are helpful.",
            "Do the task.",
            "Task completed.",
        )

        content = logger.get_frame_content("FRAME-0001")

        assert content is not None, "Expected content is not None"
        assert "You are helpful." in content, "Expected 'You are helpful.' in content"
        assert "Do the task." in content, "Expected 'Do the task.' in content"
        assert "Task completed." in content, "Expected 'Task completed.' in content"

    def test_integrity_chain(self, tmp_path):
        """Frames should be linked in integrity chain."""
        logger = FrameLogger(tmp_path, "test-thread")

        f1 = logger.log_agent_step({}, "...", "...", "...")
        f2 = logger.log_agent_step({}, "...", "...", "...")

        assert f1.content_hash is not None, "Expected f1.content_hash is not None"
        assert f2.previous_frame_hash == f1.content_hash, "Expected f2.previous_frame_hash to equal f1.content_hash"

    def test_get_validation_summary(self, tmp_path):
        """Get summary of validation results."""
        logger = FrameLogger(tmp_path, "test-thread")

        logger.register_schemas({
            "intake_input": {"required": ["request"]},
        })

        # Valid frame
        logger.log_stage_frame(
            stage_name="intake",
            input_artifacts={"request": "Add feature"},
            system_prompt="...",
            user_message="...",
            raw_response="...",
            parsed_artifact={"request_id": "REQ-001"},
            input_schema_id="intake_input",
        )

        # Invalid frame (missing required field)
        logger.log_stage_frame(
            stage_name="clarify",
            input_artifacts={},  # Missing request
            system_prompt="...",
            user_message="...",
            raw_response="...",
            parsed_artifact=None,  # Parsing failed
            input_schema_id="intake_input",
        )

        summary = logger.get_validation_summary()

        assert summary["total_frames"] == 2, "Expected summary['total_frames'] to equal 2"
        assert summary["input_validation"]["passed"] == 1, "Expected summary['input_validation']... to equal 1"
        assert summary["input_validation"]["failed"] == 1, "Expected summary['input_validation']... to equal 1"
        assert not summary["all_valid"], "Assertion failed"
        assert len(summary["failures"]) == 2, "Expected len(summary['failures']) to equal 2"# Input and output failures

    def test_persistence_across_instances(self, tmp_path):
        """Frames persist across logger instances."""
        # First instance
        logger1 = FrameLogger(tmp_path, "test-thread")
        logger1.log_agent_step({}, "...", "...", "...")

        # Second instance
        logger2 = FrameLogger(tmp_path, "test-thread")
        f2 = logger2.log_agent_step({}, "...", "...", "...")

        assert f2.frame_id == "FRAME-0002", "Expected f2.frame_id to equal 'FRAME-0002'"
        frames = logger2.list_frames()
        assert len(frames) == 2, "Expected len(frames) to equal 2"


class TestFrameLoggerWithPipelineSchemas:
    """Tests for FrameLogger integration with pipeline schemas."""

    def test_resolves_pipeline_schemas(self, tmp_path):
        """Attempt to resolve schemas from pipeline module."""
        logger = FrameLogger(tmp_path, "test-thread")

        # This should attempt to load from agentforge.core.pipeline.schemas
        frame = logger.log_stage_frame(
            stage_name="intake",
            input_artifacts={"original_request": "Test"},
            system_prompt="...",
            user_message="...",
            raw_response="...",
            parsed_artifact={"request_id": "REQ-001", "detected_scope": "feature", "original_request": "Test"},
            # Don't provide explicit schema - should try to resolve
        )

        # Frame should still be created even if schema not found
        assert frame is not None, "Expected frame is not None"
        assert frame.stage_name == "intake", "Expected frame.stage_name to equal 'intake'"


class TestFrameLoggerEndToEnd:
    """End-to-end tests for frame-based audit trail."""

    def test_complete_pipeline_flow(self, tmp_path):
        """Log a complete pipeline flow with validation."""
        logger = FrameLogger(tmp_path, "pipeline-001")

        # Register schemas
        logger.register_schemas({
            "intake_input": {"required": []},
            "intake_output": {
                "required": ["request_id", "detected_scope"],
                "properties": {
                    "request_id": {"type": "string"},
                    "detected_scope": {"type": "string"},
                },
            },
            "clarify_input": {"required": ["request_id"]},
            "clarify_output": {
                "required": ["request_id", "clarified_requirements"],
            },
        })

        # Intake stage
        intake_frame = logger.log_stage_frame(
            stage_name="intake",
            input_artifacts={"user_request": "Add login feature"},
            system_prompt="You are an intake processor...",
            user_message="Process: Add login feature",
            raw_response="```yaml\nrequest_id: REQ-001\ndetected_scope: feature\n```",
            parsed_artifact={
                "request_id": "REQ-001",
                "detected_scope": "feature",
            },
            input_schema_id="intake_input",
            output_schema_id="intake_output",
            pipeline_id="pipeline-001",
        )

        assert intake_frame.is_valid, "Expected intake_frame.is_valid to be truthy"

        # Clarify stage
        clarify_frame = logger.log_stage_frame(
            stage_name="clarify",
            input_artifacts={"request_id": "REQ-001", "scope": "feature"},
            system_prompt="You are a requirements clarifier...",
            user_message="Clarify the requirements...",
            raw_response="```yaml\nrequest_id: REQ-001\nclarified_requirements: User login with email...\n```",
            parsed_artifact={
                "request_id": "REQ-001",
                "clarified_requirements": "User login with email...",
            },
            input_schema_id="clarify_input",
            output_schema_id="clarify_output",
            pipeline_id="pipeline-001",
        )

        assert clarify_frame.is_valid, "Expected clarify_frame.is_valid to be truthy"

        # Verify chain
        assert clarify_frame.previous_frame_hash == intake_frame.content_hash, "Expected clarify_frame.previous_fram... to equal intake_frame.content_hash"

        # Get validation summary
        summary = logger.get_validation_summary()
        assert summary["all_valid"], "Assertion failed"
        assert summary["total_frames"] == 2, "Expected summary['total_frames'] to equal 2"
