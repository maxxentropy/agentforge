# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: file-handlers

"""
Tests for file_handlers module.
"""


import pytest

from agentforge.core.harness.minimal_context.tool_handlers.file_handlers import (
    create_edit_file_handler,
    create_insert_lines_handler,
    create_read_file_handler,
    create_replace_lines_handler,
    create_write_file_handler,
)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test.py"
    file_path.write_text("line1\nline2\nline3\n")
    return file_path


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    src = tmp_path / "src"
    src.mkdir()
    return tmp_path


class TestReadFileHandler:
    """Tests for read_file handler."""

    def test_read_existing_file(self, temp_file):
        """Read an existing file successfully."""
        handler = create_read_file_handler(temp_file.parent)

        result = handler({"path": temp_file.name})

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert "line1" in result, "Expected 'line1' in result"
        assert "line2" in result, "Expected 'line2' in result"
        assert "line3" in result, "Expected 'line3' in result"

    def test_read_file_not_found(self, tmp_path):
        """Error on missing file."""
        handler = create_read_file_handler(tmp_path)

        result = handler({"path": "nonexistent.py"})

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "not found" in result.lower(), "Expected 'not found' in result.lower()"

    def test_read_file_no_path(self, tmp_path):
        """Error when no path provided."""
        handler = create_read_file_handler(tmp_path)

        result = handler({})

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "path" in result.lower(), "Expected 'path' in result.lower()"

    def test_read_file_with_line_numbers(self, temp_file):
        """File content includes line numbers."""
        handler = create_read_file_handler(temp_file.parent)

        result = handler({"path": temp_file.name})

        # Should have line numbers
        assert "1:" in result or "   1:" in result, "Assertion failed"

    def test_read_absolute_path(self, temp_file):
        """Read using absolute path."""
        handler = create_read_file_handler()

        result = handler({"path": str(temp_file)})

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert "line1" in result, "Expected 'line1' in result"


class TestWriteFileHandler:
    """Tests for write_file handler."""

    def test_write_new_file(self, tmp_path):
        """Create a new file."""
        handler = create_write_file_handler(tmp_path)

        result = handler({"path": "new.py", "content": "hello world"})

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert "Created" in result, "Expected 'Created' in result"
        assert (tmp_path / "new.py").read_text() == "hello world", "Expected (tmp_path / 'new.py').read_... to equal 'hello world'"

    def test_write_overwrite_file(self, temp_file):
        """Overwrite existing file."""
        handler = create_write_file_handler(temp_file.parent)

        result = handler({"path": temp_file.name, "content": "new content"})

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert "Wrote" in result, "Expected 'Wrote' in result"
        assert temp_file.read_text() == "new content", "Expected temp_file.read_text() to equal 'new content'"

    def test_write_creates_directories(self, tmp_path):
        """Creates parent directories as needed."""
        handler = create_write_file_handler(tmp_path)

        result = handler({"path": "deep/nested/file.py", "content": "test"})

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert (tmp_path / "deep" / "nested" / "file.py").exists(), "Expected (tmp_path / 'deep' / 'neste...() to be truthy"

    def test_write_no_path(self, tmp_path):
        """Error when no path provided."""
        handler = create_write_file_handler(tmp_path)

        result = handler({"content": "test"})

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "path" in result.lower(), "Expected 'path' in result.lower()"


class TestEditFileHandler:
    """Tests for edit_file handler."""

    def test_replace_single_line(self, temp_file):
        """Replace a single line in the middle of a file."""
        temp_file.write_text("line1\nline2\nline3\n")
        handler = create_edit_file_handler(temp_file.parent)

        result = handler({
            "path": temp_file.name,
            "start_line": 2,
            "end_line": 2,
            "new_content": "replaced",
        })

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert temp_file.read_text() == "line1\nreplaced\nline3\n", "Expected temp_file.read_text() to equal 'line1\nreplaced\nline3\n'"

    def test_replace_multiple_lines(self, temp_file):
        """Replace multiple lines with different count."""
        temp_file.write_text("a\nb\nc\nd\n")
        handler = create_edit_file_handler(temp_file.parent)

        result = handler({
            "path": temp_file.name,
            "start_line": 2,
            "end_line": 3,
            "new_content": "X\nY\nZ",
        })

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert temp_file.read_text() == "a\nX\nY\nZ\nd\n", "Expected temp_file.read_text() to equal 'a\nX\nY\nZ\nd\n'"

    def test_replace_first_line(self, temp_file):
        """Replace the first line."""
        temp_file.write_text("old first\nsecond\n")
        handler = create_edit_file_handler(temp_file.parent)

        result = handler({
            "path": temp_file.name,
            "start_line": 1,
            "end_line": 1,
            "new_content": "new first",
        })

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert temp_file.read_text() == "new first\nsecond\n", "Expected temp_file.read_text() to equal 'new first\nsecond\n'"

    def test_replace_last_line(self, temp_file):
        """Replace the last line."""
        temp_file.write_text("first\nlast\n")
        handler = create_edit_file_handler(temp_file.parent)

        result = handler({
            "path": temp_file.name,
            "start_line": 2,
            "end_line": 2,
            "new_content": "new last",
        })

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        assert temp_file.read_text() == "first\nnew last\n", "Expected temp_file.read_text() to equal 'first\nnew last\n'"

    def test_edit_file_not_found(self, tmp_path):
        """Error on missing file."""
        handler = create_edit_file_handler(tmp_path)

        result = handler({
            "path": "nonexistent.py",
            "start_line": 1,
            "end_line": 1,
            "new_content": "x",
        })

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "not found" in result.lower(), "Expected 'not found' in result.lower()"

    def test_edit_invalid_line_numbers(self, temp_file):
        """Error on invalid line numbers."""
        temp_file.write_text("line\n")
        handler = create_edit_file_handler(temp_file.parent)

        result = handler({
            "path": temp_file.name,
            "start_line": 5,
            "end_line": 3,
            "new_content": "x",
        })

        assert "ERROR" in result, "Expected 'ERROR' in result"

    def test_edit_start_line_beyond_file(self, temp_file):
        """Error when start_line exceeds file length."""
        temp_file.write_text("line\n")
        handler = create_edit_file_handler(temp_file.parent)

        result = handler({
            "path": temp_file.name,
            "start_line": 10,
            "end_line": 10,
            "new_content": "x",
        })

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "exceeds" in result.lower(), "Expected 'exceeds' in result.lower()"

    def test_edit_no_path(self, tmp_path):
        """Error when no path provided."""
        handler = create_edit_file_handler(tmp_path)

        result = handler({
            "start_line": 1,
            "end_line": 1,
            "new_content": "x",
        })

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "path" in result.lower(), "Expected 'path' in result.lower()"


class TestReplaceLinesHandler:
    """Tests for replace_lines handler."""

    def test_replace_with_auto_indent(self, temp_file):
        """Replace lines with auto-indentation."""
        temp_file.write_text("def foo():\n    pass\n    return\n")
        handler = create_replace_lines_handler(temp_file.parent)

        result = handler({
            "file_path": temp_file.name,
            "start_line": 2,
            "end_line": 3,
            "new_content": "x = 1\nreturn x",
        })

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        content = temp_file.read_text()
        # Should have proper indentation
        assert "    x = 1" in content, "Expected '    x = 1' in content"
        assert "    return x" in content, "Expected '    return x' in content"

    def test_replace_invalid_range(self, temp_file):
        """Error on invalid line range."""
        temp_file.write_text("line\n")
        handler = create_replace_lines_handler(temp_file.parent)

        result = handler({
            "file_path": temp_file.name,
            "start_line": 5,
            "end_line": 10,
            "new_content": "x",
        })

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "Invalid" in result, "Expected 'Invalid' in result"


class TestInsertLinesHandler:
    """Tests for insert_lines handler."""

    def test_insert_before_line(self, temp_file):
        """Insert lines before a specific line."""
        temp_file.write_text("first\nsecond\n")
        handler = create_insert_lines_handler(temp_file.parent)

        result = handler({
            "file_path": temp_file.name,
            "line_number": 2,
            "new_content": "inserted",
        })

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        content = temp_file.read_text()
        lines = content.split("\n")
        assert "inserted" in lines[1], "Expected 'inserted' in lines[1]"

    def test_insert_at_beginning(self, temp_file):
        """Insert at the beginning of file."""
        temp_file.write_text("existing\n")
        handler = create_insert_lines_handler(temp_file.parent)

        result = handler({
            "file_path": temp_file.name,
            "line_number": 1,
            "new_content": "# comment",
        })

        assert "SUCCESS" in result, "Expected 'SUCCESS' in result"
        content = temp_file.read_text()
        assert content.startswith("# comment"), "Expected content.startswith() to be truthy"

    def test_insert_file_not_found(self, tmp_path):
        """Error on missing file."""
        handler = create_insert_lines_handler(tmp_path)

        result = handler({
            "file_path": "nonexistent.py",
            "line_number": 1,
            "new_content": "x",
        })

        assert "ERROR" in result, "Expected 'ERROR' in result"
        assert "not found" in result.lower(), "Expected 'not found' in result.lower()"
