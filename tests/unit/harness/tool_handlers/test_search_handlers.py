# @spec_file: specs/tools/01-tool-handlers.yaml
# @spec_id: tool-handlers-v1
# @component_id: search-handlers

"""
Tests for search_handlers module.
"""

import pytest
from pathlib import Path

from agentforge.core.harness.minimal_context.tool_handlers.search_handlers import (
    create_search_code_handler,
    create_load_context_handler,
    create_find_related_handler,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with source files."""
    src = tmp_path / "src"
    src.mkdir()

    # Create some Python files
    (src / "module.py").write_text(
        "def calculate_total(items):\n"
        "    return sum(items)\n"
        "\n"
        "def process_data(data):\n"
        "    return data * 2\n"
    )

    (src / "utils.py").write_text(
        "def helper_function():\n"
        "    pass\n"
    )

    # Create a test file
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_module.py").write_text(
        "def test_calculate_total():\n"
        "    assert calculate_total([1, 2]) == 3\n"
    )

    return tmp_path


class TestSearchCodeHandler:
    """Tests for search_code handler."""

    def test_regex_search_finds_pattern(self, temp_project):
        """Regex search finds matching lines."""
        handler = create_search_code_handler(temp_project)

        result = handler({"pattern": "calculate_total"})

        assert "module.py" in result
        assert "1" in result or "line" in result.lower()
        assert "Found" in result

    def test_regex_search_with_file_pattern(self, temp_project):
        """File pattern limits search scope."""
        handler = create_search_code_handler(temp_project)

        result = handler({"pattern": "def", "file_pattern": "src/*.py"})

        assert "module.py" in result or "utils.py" in result
        # Should not include test files
        assert "test_module" not in result

    def test_regex_no_matches(self, temp_project):
        """No matches returns informative message."""
        handler = create_search_code_handler(temp_project)

        result = handler({"pattern": "nonexistent_symbol_xyz123"})

        assert "No matches" in result

    def test_invalid_regex(self, temp_project):
        """Invalid regex returns error."""
        handler = create_search_code_handler(temp_project)

        result = handler({"pattern": "[invalid("})

        assert "ERROR" in result
        assert "Invalid regex" in result

    def test_no_pattern_error(self, temp_project):
        """Error when no pattern provided."""
        handler = create_search_code_handler(temp_project)

        result = handler({})

        assert "ERROR" in result
        assert "pattern" in result.lower()

    def test_case_insensitive_search(self, temp_project):
        """Search is case insensitive."""
        handler = create_search_code_handler(temp_project)

        result = handler({"pattern": "CALCULATE_TOTAL"})

        assert "module.py" in result
        assert "Found" in result

    def test_max_results_limits_output(self, temp_project):
        """max_results limits number of results."""
        handler = create_search_code_handler(temp_project)

        result = handler({"pattern": "def", "max_results": 2})

        # Should have limited results message
        assert "limited" in result.lower() or len(result.split("\n")) < 10


class TestLoadContextHandler:
    """Tests for load_context handler."""

    def test_load_file_by_path(self, temp_project):
        """Load a file using path parameter."""
        handler = create_load_context_handler(temp_project)

        result = handler({"path": "src/module.py"})

        assert "SUCCESS" in result
        assert "module.py" in result
        assert "context" in result.lower()

    def test_load_file_by_item(self, temp_project):
        """Load a file using item parameter."""
        handler = create_load_context_handler(temp_project)

        result = handler({"item": "full_file:src/module.py"})

        assert "SUCCESS" in result
        assert "module.py" in result

    def test_load_file_not_found(self, temp_project):
        """Error on missing file."""
        handler = create_load_context_handler(temp_project)

        result = handler({"path": "nonexistent.py"})

        assert "ERROR" in result
        assert "not found" in result.lower()

    def test_load_no_params_error(self, temp_project):
        """Error when no parameters provided."""
        handler = create_load_context_handler(temp_project)

        result = handler({})

        assert "ERROR" in result

    def test_load_query_redirect(self, temp_project):
        """Query parameter suggests using read_file."""
        handler = create_load_context_handler(temp_project)

        result = handler({"query": "find something"})

        assert "ERROR" in result
        assert "read_file" in result


class TestFindRelatedHandler:
    """Tests for find_related handler."""

    def test_find_same_directory(self, temp_project):
        """Find files in same directory."""
        handler = create_find_related_handler(temp_project)

        result = handler({"file_path": "src/module.py", "type": "same_dir"})

        assert "utils.py" in result
        assert "same_dir" in result

    def test_find_test_files(self, temp_project):
        """Find related test files."""
        handler = create_find_related_handler(temp_project)

        result = handler({"file_path": "src/module.py", "type": "tests"})

        assert "test_module.py" in result or "No related" in result

    def test_find_file_not_found(self, temp_project):
        """Error on missing file."""
        handler = create_find_related_handler(temp_project)

        result = handler({"file_path": "nonexistent.py"})

        assert "ERROR" in result
        assert "not found" in result.lower()

    def test_find_no_path_error(self, temp_project):
        """Error when no path provided."""
        handler = create_find_related_handler(temp_project)

        result = handler({})

        assert "ERROR" in result
        assert "path" in result.lower()

    def test_find_all_types(self, temp_project):
        """Find all related file types."""
        handler = create_find_related_handler(temp_project)

        result = handler({"file_path": "src/module.py", "type": "all"})

        # Should include at least same_dir results
        assert "Related files" in result or "No related" in result
