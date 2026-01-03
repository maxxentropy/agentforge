"""
Tests for LLM Generation Domain Model
======================================
"""

from datetime import datetime
from pathlib import Path

import pytest

from agentforge.core.generate.domain import (
    APIError,
    FileAction,
    GeneratedFile,
    GenerationContext,
    GenerationError,
    GenerationMode,
    GenerationPhase,
    GenerationResult,
    ParseError,
    TokenUsage,
    WriteError,
)

# =============================================================================
# Enum Tests
# =============================================================================


class TestGenerationPhase:
    """Tests for GenerationPhase enum."""

    def test_has_red_phase(self):
        assert GenerationPhase.RED.value == "red", "Expected GenerationPhase.RED.value to equal 'red'"

    def test_has_green_phase(self):
        assert GenerationPhase.GREEN.value == "green", "Expected GenerationPhase.GREEN.value to equal 'green'"

    def test_has_refactor_phase(self):
        assert GenerationPhase.REFACTOR.value == "refactor", "Expected GenerationPhase.REFACTOR.value to equal 'refactor'"


class TestGenerationMode:
    """Tests for GenerationMode enum."""

    def test_has_full_mode(self):
        assert GenerationMode.FULL.value == "full", "Expected GenerationMode.FULL.value to equal 'full'"

    def test_has_incremental_mode(self):
        assert GenerationMode.INCREMENTAL.value == "incremental", "Expected GenerationMode.INCREMENTAL.... to equal 'incremental'"

    def test_has_fix_mode(self):
        assert GenerationMode.FIX.value == "fix", "Expected GenerationMode.FIX.value to equal 'fix'"


class TestFileAction:
    """Tests for FileAction enum."""

    def test_has_create_action(self):
        assert FileAction.CREATE.value == "create", "Expected FileAction.CREATE.value to equal 'create'"

    def test_has_modify_action(self):
        assert FileAction.MODIFY.value == "modify", "Expected FileAction.MODIFY.value to equal 'modify'"

    def test_has_delete_action(self):
        assert FileAction.DELETE.value == "delete", "Expected FileAction.DELETE.value to equal 'delete'"


# =============================================================================
# Exception Tests
# =============================================================================


class TestGenerationError:
    """Tests for GenerationError exception."""

    def test_message_captured(self):
        error = GenerationError("test error")
        assert str(error) == "test error", "Expected str(error) to equal 'test error'"
        assert error.message == "test error", "Expected error.message to equal 'test error'"

    def test_details_default_empty(self):
        error = GenerationError("test")
        assert error.details == {}, "Expected error.details to equal {}"

    def test_details_captured(self):
        error = GenerationError("test", {"key": "value"})
        assert error.details == {"key": "value"}, "Expected error.details to equal {'key': 'value'}"


class TestAPIError:
    """Tests for APIError exception."""

    def test_captures_status_code(self):
        error = APIError("API failed", status_code=429)
        assert error.status_code == 429, "Expected error.status_code to equal 429"

    def test_captures_response(self):
        error = APIError("API failed", response="Rate limited")
        assert error.response == "Rate limited", "Expected error.response to equal 'Rate limited'"

    def test_retryable_default_true(self):
        error = APIError("API failed")
        assert error.retryable is True, "Expected error.retryable is True"

    def test_retryable_can_be_false(self):
        error = APIError("Invalid key", retryable=False)
        assert error.retryable is False, "Expected error.retryable is False"


class TestParseError:
    """Tests for ParseError exception."""

    def test_captures_raw_response(self):
        error = ParseError("Parse failed", raw_response="invalid json")
        assert error.raw_response == "invalid json", "Expected error.raw_response to equal 'invalid json'"

    def test_captures_position(self):
        error = ParseError("Parse failed", position=42)
        assert error.position == 42, "Expected error.position to equal 42"


class TestWriteError:
    """Tests for WriteError exception."""

    def test_captures_path(self):
        error = WriteError("Write failed", path=Path("/test/file.py"))
        assert error.path == Path("/test/file.py"), "Expected error.path to equal Path('/test/file.py')"

    def test_captures_original_error(self):
        original = OSError("disk full")
        error = WriteError("Write failed", original_error=original)
        assert error.original_error is original, "Expected error.original_error is original"


# =============================================================================
# TokenUsage Tests
# =============================================================================


class TestTokenUsage:
    """Tests for TokenUsage value object."""

    def test_total_tokens_calculation(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        assert usage.total_tokens == 150, "Expected usage.total_tokens to equal 150"

    def test_cost_estimate_calculation(self):
        # 1000 prompt tokens + 1000 completion tokens
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=1000)
        # Cost: (1000/1M * $3) + (1000/1M * $15) = $0.003 + $0.015 = $0.018
        assert abs(usage.cost_estimate - 0.018) < 0.0001, "Expected abs(usage.cost_estimate - 0... < 0.0001"

    def test_frozen_immutable(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        with pytest.raises(AttributeError):
            usage.prompt_tokens = 200


# =============================================================================
# GeneratedFile Tests
# =============================================================================


class TestGeneratedFile:
    """Tests for GeneratedFile entity."""

    def test_creation_with_path_string(self):
        file = GeneratedFile(path="src/test.py", content="# test")
        assert file.path == Path("src/test.py"), "Expected file.path to equal Path('src/test.py')"
        assert file.content == "# test", "Expected file.content to equal '# test'"

    def test_creation_with_path_object(self):
        file = GeneratedFile(path=Path("src/test.py"), content="# test")
        assert file.path == Path("src/test.py"), "Expected file.path to equal Path('src/test.py')"

    def test_default_action_is_create(self):
        file = GeneratedFile(path="test.py", content="")
        assert file.action == FileAction.CREATE, "Expected file.action to equal FileAction.CREATE"

    def test_is_new_for_create(self):
        file = GeneratedFile(path="test.py", content="", action=FileAction.CREATE)
        assert file.is_new is True, "Expected file.is_new is True"
        assert file.is_modification is False, "Expected file.is_modification is False"

    def test_is_modification_for_modify(self):
        file = GeneratedFile(path="test.py", content="", action=FileAction.MODIFY)
        assert file.is_new is False, "Expected file.is_new is False"
        assert file.is_modification is True, "Expected file.is_modification is True"

    def test_line_count(self):
        content = "line1\nline2\nline3"
        file = GeneratedFile(path="test.py", content=content)
        assert file.line_count == 3, "Expected file.line_count to equal 3"

    def test_line_count_empty_file(self):
        file = GeneratedFile(path="test.py", content="")
        assert file.line_count == 0, "Expected file.line_count to equal 0"

    def test_diff_summary_new_file(self):
        file = GeneratedFile(path="test.py", content="line1\nline2")
        assert file.diff_summary() == "New file: 2 lines", "Expected file.diff_summary() to equal 'New file: 2 lines'"

    def test_diff_summary_modification(self):
        file = GeneratedFile(
            path="test.py",
            content="line1\nline2\nline3",
            action=FileAction.MODIFY,
            original_content="line1",
        )
        assert file.diff_summary() == "Modified: 1 → 3 lines (+2)", "Expected file.diff_summary() to equal 'Modified: 1 → 3 lines (+2)'"

    def test_diff_summary_modification_reduction(self):
        file = GeneratedFile(
            path="test.py",
            content="line1",
            action=FileAction.MODIFY,
            original_content="line1\nline2\nline3",
        )
        assert file.diff_summary() == "Modified: 3 → 1 lines (-2)", "Expected file.diff_summary() to equal 'Modified: 3 → 1 lines (-2)'"


# =============================================================================
# GenerationContext Tests
# =============================================================================


class TestGenerationContext:
    """Tests for GenerationContext entity."""

    def test_basic_creation(self):
        spec = {"name": "test"}
        ctx = GenerationContext(spec=spec, phase=GenerationPhase.RED)
        assert ctx.spec == spec, "Expected ctx.spec to equal spec"
        assert ctx.phase == GenerationPhase.RED, "Expected ctx.phase to equal GenerationPhase.RED"

    def test_default_mode_is_full(self):
        ctx = GenerationContext(spec={}, phase=GenerationPhase.RED)
        assert ctx.mode == GenerationMode.FULL, "Expected ctx.mode to equal GenerationMode.FULL"

    def test_patterns_default_empty(self):
        ctx = GenerationContext(spec={}, phase=GenerationPhase.RED)
        assert ctx.patterns == {}, "Expected ctx.patterns to equal {}"

    def test_examples_default_empty(self):
        ctx = GenerationContext(spec={}, phase=GenerationPhase.RED)
        assert ctx.examples == [], "Expected ctx.examples to equal []"

    def test_for_red_factory(self):
        spec = {"name": "TestComponent"}
        ctx = GenerationContext.for_red(
            spec=spec,
            component_name="TestComponent",
            patterns={"test_pattern": "pytest"},
        )
        assert ctx.phase == GenerationPhase.RED, "Expected ctx.phase to equal GenerationPhase.RED"
        assert ctx.mode == GenerationMode.FULL, "Expected ctx.mode to equal GenerationMode.FULL"
        assert ctx.component_name == "TestComponent", "Expected ctx.component_name to equal 'TestComponent'"
        assert ctx.patterns == {"test_pattern": "pytest"}, "Expected ctx.patterns to equal {'test_pattern': 'pytest'}"

    def test_for_green_factory(self):
        spec = {"name": "TestComponent"}
        ctx = GenerationContext.for_green(
            spec=spec,
            existing_tests="def test_foo(): pass",
            component_name="TestComponent",
        )
        assert ctx.phase == GenerationPhase.GREEN, "Expected ctx.phase to equal GenerationPhase.GREEN"
        assert ctx.mode == GenerationMode.FULL, "Expected ctx.mode to equal GenerationMode.FULL"
        assert ctx.existing_tests == "def test_foo(): pass", "Expected ctx.existing_tests to equal 'def test_foo(): pass'"

    def test_for_fix_factory(self):
        spec = {"name": "TestComponent"}
        error_ctx = {"test_error": "assertion failed"}
        ctx = GenerationContext.for_fix(
            spec=spec,
            error_context=error_ctx,
            existing_tests="test code",
            existing_impl="impl code",
        )
        assert ctx.phase == GenerationPhase.GREEN, "Expected ctx.phase to equal GenerationPhase.GREEN"
        assert ctx.mode == GenerationMode.FIX, "Expected ctx.mode to equal GenerationMode.FIX"
        assert ctx.error_context == error_ctx, "Expected ctx.error_context to equal error_ctx"


# =============================================================================
# GenerationResult Tests
# =============================================================================


class TestGenerationResult:
    """Tests for GenerationResult entity."""

    def test_success_creation(self):
        result = GenerationResult(
            success=True,
            files=[GeneratedFile(path="test.py", content="# test")],
            explanation="Generated test file",
            model="claude-sonnet-4-20250514",
        )
        assert result.success is True, "Expected result.success is True"
        assert result.file_count == 1, "Expected result.file_count to equal 1"

    def test_failure_creation(self):
        result = GenerationResult(success=False, error="API timeout")
        assert result.success is False, "Expected result.success is False"
        assert result.error == "API timeout", "Expected result.error to equal 'API timeout'"

    def test_tokens_used_with_usage(self):
        result = GenerationResult(
            success=True,
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
        )
        assert result.tokens_used == 150, "Expected result.tokens_used to equal 150"
        assert result.prompt_tokens == 100, "Expected result.prompt_tokens to equal 100"
        assert result.completion_tokens == 50, "Expected result.completion_tokens to equal 50"

    def test_tokens_used_without_usage(self):
        result = GenerationResult(success=True)
        assert result.tokens_used == 0, "Expected result.tokens_used to equal 0"
        assert result.prompt_tokens == 0, "Expected result.prompt_tokens to equal 0"
        assert result.completion_tokens == 0, "Expected result.completion_tokens to equal 0"

    def test_total_lines(self):
        result = GenerationResult(
            success=True,
            files=[
                GeneratedFile(path="a.py", content="line1\nline2"),
                GeneratedFile(path="b.py", content="line1\nline2\nline3"),
            ],
        )
        assert result.total_lines == 5, "Expected result.total_lines to equal 5"

    def test_failure_factory(self):
        result = GenerationResult.failure(
            error="Parse failed",
            raw_response="invalid",
            duration_seconds=1.5,
        )
        assert result.success is False, "Expected result.success is False"
        assert result.error == "Parse failed", "Expected result.error to equal 'Parse failed'"
        assert result.raw_response == "invalid", "Expected result.raw_response to equal 'invalid'"
        assert result.duration_seconds == 1.5, "Expected result.duration_seconds to equal 1.5"

    def test_success_factory(self):
        files = [GeneratedFile(path="test.py", content="# test")]
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        result = GenerationResult.success_result(
            files=files,
            explanation="Done",
            model="claude-sonnet-4-20250514",
            token_usage=usage,
            duration_seconds=2.5,
        )
        assert result.success is True, "Expected result.success is True"
        assert result.files == files, "Expected result.files to equal files"
        assert result.explanation == "Done", "Expected result.explanation to equal 'Done'"
        assert result.model == "claude-sonnet-4-20250514", "Expected result.model to equal 'claude-sonnet-4-20250514'"
        assert result.token_usage == usage, "Expected result.token_usage to equal usage"

    def test_summary_success(self):
        result = GenerationResult(
            success=True,
            files=[GeneratedFile(path="test.py", content="line1\nline2")],
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
            duration_seconds=1.5,
        )
        summary = result.summary()
        assert "1 files" in summary, "Expected '1 files' in summary"
        assert "2 lines" in summary, "Expected '2 lines' in summary"
        assert "150 tokens" in summary, "Expected '150 tokens' in summary"
        assert "1.5s" in summary, "Expected '1.5s' in summary"

    def test_summary_failure(self):
        result = GenerationResult.failure(error="API timeout")
        assert "failed" in result.summary().lower(), "Expected 'failed' in result.summary().lower()"
        assert "API timeout" in result.summary(), "Expected 'API timeout' in result.summary()"

    def test_timestamp_default(self):
        before = datetime.utcnow()
        result = GenerationResult(success=True)
        after = datetime.utcnow()
        assert before <= result.timestamp <= after, "Assertion failed"
