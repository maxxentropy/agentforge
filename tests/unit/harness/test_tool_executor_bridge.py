# @spec_file: .agentforge/specs/harness-v1.yaml
# @spec_id: harness-v1
# @component_id: tools-harness-tool_executor_bridge
# @impl_path: tools/harness/tool_executor_bridge.py

"""Tests for Tool Executor Bridge."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from tools.harness.tool_executor_bridge import ToolExecutorBridge, create_tool_bridge


class TestToolExecutorBridge:
    """Tests for ToolExecutorBridge."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def bridge(self, temp_dir):
        """Create a bridge with temp directory."""
        return ToolExecutorBridge(working_dir=temp_dir)

    def test_init_with_default_working_dir(self):
        """Bridge initializes with current directory by default."""
        bridge = ToolExecutorBridge()
        assert bridge.working_dir == Path.cwd()

    def test_init_with_custom_working_dir(self, temp_dir):
        """Bridge accepts custom working directory."""
        bridge = ToolExecutorBridge(working_dir=temp_dir)
        assert bridge.working_dir == temp_dir

    def test_get_default_executors(self, bridge):
        """Default executors include common tools."""
        executors = bridge.get_default_executors()

        assert "read_file" in executors
        assert "write_file" in executors
        assert "edit_file" in executors
        assert "glob" in executors
        assert "grep" in executors
        assert "bash" in executors
        assert "run_tests" in executors
        assert "list_files" in executors

    def test_register_custom_tool(self, bridge):
        """Register a custom tool executor."""
        def custom_exec(name, params):
            from tools.harness.llm_executor_domain import ToolResult
            return ToolResult.success_result(name, "custom output")

        bridge.register_custom_tool("custom", custom_exec)

        executors = bridge.get_default_executors()
        assert "custom" in executors


class TestReadFile:
    """Tests for read_file tool."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def bridge(self, temp_dir):
        return ToolExecutorBridge(working_dir=temp_dir)

    def test_read_existing_file(self, bridge, temp_dir):
        """Read an existing file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello World")

        result = bridge._execute_read_file("read_file", {"path": str(test_file)})

        assert result.success is True
        assert result.output == "Hello World"

    def test_read_relative_path(self, bridge, temp_dir):
        """Read with relative path."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Content")

        result = bridge._execute_read_file("read_file", {"path": "test.txt"})

        assert result.success is True
        assert result.output == "Content"

    def test_read_nonexistent_file(self, bridge):
        """Read a file that doesn't exist."""
        result = bridge._execute_read_file("read_file", {"path": "nonexistent.txt"})

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_read_missing_path_param(self, bridge):
        """Read without path parameter fails."""
        result = bridge._execute_read_file("read_file", {})

        assert result.success is False
        assert "Missing required parameter" in result.error


class TestWriteFile:
    """Tests for write_file tool."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def bridge(self, temp_dir):
        return ToolExecutorBridge(working_dir=temp_dir)

    def test_write_new_file(self, bridge, temp_dir):
        """Write to a new file."""
        result = bridge._execute_write_file(
            "write_file",
            {"path": "new.txt", "content": "New content"}
        )

        assert result.success is True
        assert (temp_dir / "new.txt").read_text() == "New content"

    def test_write_creates_directories(self, bridge, temp_dir):
        """Write creates parent directories."""
        result = bridge._execute_write_file(
            "write_file",
            {"path": "a/b/c/file.txt", "content": "Deep"}
        )

        assert result.success is True
        assert (temp_dir / "a/b/c/file.txt").read_text() == "Deep"

    def test_write_missing_path(self, bridge):
        """Write without path fails."""
        result = bridge._execute_write_file("write_file", {"content": "test"})
        assert result.success is False

    def test_write_missing_content(self, bridge):
        """Write without content fails."""
        result = bridge._execute_write_file("write_file", {"path": "test.txt"})
        assert result.success is False


class TestEditFile:
    """Tests for edit_file tool."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def bridge(self, temp_dir):
        return ToolExecutorBridge(working_dir=temp_dir)

    def test_edit_replaces_string(self, bridge, temp_dir):
        """Edit replaces a string in file."""
        test_file = temp_dir / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        result = bridge._execute_edit_file(
            "edit_file",
            {"path": str(test_file), "old_string": "pass", "new_string": "return 42"}
        )

        assert result.success is True
        assert test_file.read_text() == "def foo():\n    return 42\n"

    def test_edit_string_not_found(self, bridge, temp_dir):
        """Edit fails when string not found."""
        test_file = temp_dir / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        result = bridge._execute_edit_file(
            "edit_file",
            {"path": str(test_file), "old_string": "nonexistent", "new_string": "x"}
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_edit_nonexistent_file(self, bridge):
        """Edit fails for nonexistent file."""
        result = bridge._execute_edit_file(
            "edit_file",
            {"path": "nope.py", "old_string": "a", "new_string": "b"}
        )
        assert result.success is False


class TestGlob:
    """Tests for glob tool."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def bridge(self, temp_dir):
        return ToolExecutorBridge(working_dir=temp_dir)

    def test_glob_finds_files(self, bridge, temp_dir):
        """Glob finds matching files."""
        (temp_dir / "a.py").write_text("")
        (temp_dir / "b.py").write_text("")
        (temp_dir / "c.txt").write_text("")

        result = bridge._execute_glob("glob", {"pattern": "*.py"})

        assert result.success is True
        assert "a.py" in result.output
        assert "b.py" in result.output
        assert "c.txt" not in result.output

    def test_glob_no_matches(self, bridge, temp_dir):
        """Glob with no matches returns message."""
        result = bridge._execute_glob("glob", {"pattern": "*.xyz"})

        assert result.success is True
        assert "No matches" in result.output

    def test_glob_missing_pattern(self, bridge):
        """Glob without pattern fails."""
        result = bridge._execute_glob("glob", {})
        assert result.success is False


class TestBash:
    """Tests for bash tool."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def bridge(self, temp_dir):
        return ToolExecutorBridge(working_dir=temp_dir)

    def test_bash_executes_command(self, bridge):
        """Bash executes a simple command."""
        result = bridge._execute_bash("bash", {"command": "echo hello"})

        assert result.success is True
        assert "hello" in result.output

    def test_bash_blocks_dangerous_commands(self, bridge):
        """Bash blocks dangerous commands."""
        result = bridge._execute_bash("bash", {"command": "rm -rf /"})

        assert result.success is False
        assert "blocked" in result.error.lower()

    def test_bash_missing_command(self, bridge):
        """Bash without command fails."""
        result = bridge._execute_bash("bash", {})
        assert result.success is False

    def test_bash_failed_command(self, bridge):
        """Bash returns failure for failed commands."""
        result = bridge._execute_bash("bash", {"command": "exit 1"})
        assert result.success is False


class TestListFiles:
    """Tests for list_files tool."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def bridge(self, temp_dir):
        return ToolExecutorBridge(working_dir=temp_dir)

    def test_list_files_returns_entries(self, bridge, temp_dir):
        """List files returns directory contents."""
        (temp_dir / "file.txt").write_text("")
        (temp_dir / "subdir").mkdir()

        result = bridge._execute_list_files("list_files", {"path": "."})

        assert result.success is True
        assert "file.txt" in result.output
        assert "subdir" in result.output

    def test_list_files_marks_directories(self, bridge, temp_dir):
        """List files marks directories with 'd' prefix."""
        (temp_dir / "file.txt").write_text("")
        (temp_dir / "subdir").mkdir()

        result = bridge._execute_list_files("list_files", {"path": "."})

        assert "d subdir" in result.output
        assert "f file.txt" in result.output

    def test_list_nonexistent_dir(self, bridge):
        """List nonexistent directory fails."""
        result = bridge._execute_list_files("list_files", {"path": "nope"})
        assert result.success is False


class TestCreateToolBridge:
    """Tests for factory function."""

    def test_creates_bridge(self):
        """Factory creates bridge."""
        bridge = create_tool_bridge()
        assert isinstance(bridge, ToolExecutorBridge)

    def test_creates_with_working_dir(self):
        """Factory accepts working directory."""
        custom_dir = Path("/tmp")
        bridge = create_tool_bridge(working_dir=custom_dir)
        assert bridge.working_dir == custom_dir
