# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: tool-handler-constants
# @test_path: tests/unit/harness/tool_handlers/test_constants.py

"""
Tool Handler Constants
======================

Magic numbers and configuration values extracted for maintainability.

These values control behavior across handlers and can be adjusted
for different environments or requirements.
"""

# ==============================================================================
# FILE HANDLERS
# ==============================================================================

# Maximum lines to show in file read preview
FILE_PREVIEW_MAX_LINES = 100

# Maximum characters to show per line in preview
FILE_PREVIEW_LINE_MAX_CHARS = 100

# ==============================================================================
# SEARCH HANDLERS
# ==============================================================================

# Default maximum search results to return
SEARCH_DEFAULT_MAX_RESULTS = 20

# Maximum characters per line in search results
SEARCH_LINE_MAX_CHARS = 100

# Maximum content size to store in working memory (chars)
WORKING_MEMORY_MAX_CONTENT_SIZE = 5000

# Number of steps before loaded context expires
WORKING_MEMORY_EXPIRY_STEPS = 3

# Maximum related files to show
FIND_RELATED_MAX_FILES = 10

# Maximum test file patterns to try
FIND_RELATED_MAX_PATTERNS = 5

# ==============================================================================
# VERIFY HANDLERS
# ==============================================================================

# Timeouts (in seconds)
CONFORMANCE_CHECK_TIMEOUT = 120
TEST_RUN_TIMEOUT = 300
PYTHON_VALIDATION_TIMEOUT = 10

# Output truncation for results (chars)
CHECK_PASSED_OUTPUT_MAX_CHARS = 500
CHECK_FAILED_OUTPUT_MAX_CHARS = 800
CHECK_STDERR_MAX_CHARS = 300

# ==============================================================================
# TERMINAL HANDLERS
# ==============================================================================

# Maximum characters for summary fields
SUMMARY_FIELD_MAX_CHARS = 100

# Maximum plan steps to display
PLAN_DISPLAY_MAX_STEPS = 5
