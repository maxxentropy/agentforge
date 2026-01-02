# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: tool-handler-constants

"""
Tests for tool handler constants.

Verifies that response format constants are properly defined
and have sensible values for runtime operation.
"""



class TestToolHandlerConstants:
    """Tests for tool handler constants."""

    def test_constants_import(self):
        """Verify constants module can be imported."""
        from agentforge.core.harness.minimal_context.tool_handlers.constants import (
            FILE_PREVIEW_MAX_LINES,
            SEARCH_DEFAULT_MAX_RESULTS,
            WORKING_MEMORY_MAX_CONTENT_SIZE,
        )
        assert FILE_PREVIEW_MAX_LINES is not None
        assert SEARCH_DEFAULT_MAX_RESULTS is not None
        assert WORKING_MEMORY_MAX_CONTENT_SIZE is not None

    def test_file_preview_constants(self):
        """File preview constants should have positive values."""
        from agentforge.core.harness.minimal_context.tool_handlers.constants import (
            FILE_PREVIEW_LINE_MAX_CHARS,
            FILE_PREVIEW_MAX_LINES,
        )
        assert isinstance(FILE_PREVIEW_MAX_LINES, int)
        assert FILE_PREVIEW_MAX_LINES > 0
        assert isinstance(FILE_PREVIEW_LINE_MAX_CHARS, int)
        assert FILE_PREVIEW_LINE_MAX_CHARS > 0

    def test_search_constants(self):
        """Search constants should have positive values."""
        from agentforge.core.harness.minimal_context.tool_handlers.constants import (
            SEARCH_DEFAULT_MAX_RESULTS,
            SEARCH_LINE_MAX_CHARS,
        )
        assert isinstance(SEARCH_DEFAULT_MAX_RESULTS, int)
        assert SEARCH_DEFAULT_MAX_RESULTS > 0
        assert isinstance(SEARCH_LINE_MAX_CHARS, int)
        assert SEARCH_LINE_MAX_CHARS > 0

    def test_working_memory_constants(self):
        """Working memory constants should have sensible values."""
        from agentforge.core.harness.minimal_context.tool_handlers.constants import (
            WORKING_MEMORY_EXPIRY_STEPS,
            WORKING_MEMORY_MAX_CONTENT_SIZE,
        )
        assert isinstance(WORKING_MEMORY_MAX_CONTENT_SIZE, int)
        assert WORKING_MEMORY_MAX_CONTENT_SIZE > 0
        assert isinstance(WORKING_MEMORY_EXPIRY_STEPS, int)
        assert WORKING_MEMORY_EXPIRY_STEPS > 0

    def test_timeout_constants(self):
        """Timeout constants should be positive."""
        from agentforge.core.harness.minimal_context.tool_handlers.constants import (
            CONFORMANCE_CHECK_TIMEOUT,
            PYTHON_VALIDATION_TIMEOUT,
            TEST_RUN_TIMEOUT,
        )
        assert CONFORMANCE_CHECK_TIMEOUT > 0
        assert TEST_RUN_TIMEOUT > 0
        assert PYTHON_VALIDATION_TIMEOUT > 0

    def test_output_truncation_constants(self):
        """Output truncation limits should be positive."""
        from agentforge.core.harness.minimal_context.tool_handlers.constants import (
            CHECK_FAILED_OUTPUT_MAX_CHARS,
            CHECK_PASSED_OUTPUT_MAX_CHARS,
            CHECK_STDERR_MAX_CHARS,
        )
        assert CHECK_PASSED_OUTPUT_MAX_CHARS > 0
        assert CHECK_FAILED_OUTPUT_MAX_CHARS > 0
        assert CHECK_STDERR_MAX_CHARS > 0
