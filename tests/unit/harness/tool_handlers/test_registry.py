# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: tool-handlers-init

"""
Tests for tool handler registry and factory functions.
"""


import pytest

from agentforge.core.harness.minimal_context.tool_handlers import (
    ToolHandlerRegistry,
    create_fix_violation_handlers,
    create_minimal_handlers,
    create_standard_handlers,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    src = tmp_path / "src"
    src.mkdir()
    return tmp_path


class TestCreateStandardHandlers:
    """Tests for create_standard_handlers factory."""

    def test_returns_dict(self, temp_project):
        """Returns a dictionary of handlers."""
        handlers = create_standard_handlers(temp_project)

        assert isinstance(handlers, dict)
        assert len(handlers) > 0

    def test_includes_file_handlers(self, temp_project):
        """Includes file operation handlers."""
        handlers = create_standard_handlers(temp_project)

        assert "read_file" in handlers
        assert "write_file" in handlers
        assert "edit_file" in handlers

    def test_includes_search_handlers(self, temp_project):
        """Includes search handlers."""
        handlers = create_standard_handlers(temp_project)

        assert "search_code" in handlers
        assert "load_context" in handlers

    def test_includes_verify_handlers(self, temp_project):
        """Includes verification handlers."""
        handlers = create_standard_handlers(temp_project)

        assert "run_check" in handlers
        assert "run_tests" in handlers

    def test_includes_terminal_handlers(self, temp_project):
        """Includes terminal action handlers."""
        handlers = create_standard_handlers(temp_project)

        assert "complete" in handlers
        assert "escalate" in handlers
        assert "cannot_fix" in handlers

    def test_handlers_are_callable(self, temp_project):
        """All handlers are callable."""
        handlers = create_standard_handlers(temp_project)

        for name, handler in handlers.items():
            assert callable(handler), f"Handler '{name}' is not callable"

    def test_handlers_return_strings(self, temp_project):
        """Handlers return string results."""
        handlers = create_standard_handlers(temp_project)

        # Test a simple handler
        complete = handlers["complete"]
        result = complete({"summary": "Test"})

        assert isinstance(result, str)


class TestCreateFixViolationHandlers:
    """Tests for create_fix_violation_handlers factory."""

    def test_returns_handlers(self, temp_project):
        """Returns a dictionary of handlers."""
        handlers = create_fix_violation_handlers(temp_project)

        assert isinstance(handlers, dict)
        assert len(handlers) > 0

    def test_includes_cannot_fix(self, temp_project):
        """Includes cannot_fix handler for violation workflow."""
        handlers = create_fix_violation_handlers(temp_project)

        assert "cannot_fix" in handlers

    def test_includes_run_check(self, temp_project):
        """Includes run_check handler for verification."""
        handlers = create_fix_violation_handlers(temp_project)

        assert "run_check" in handlers


class TestCreateMinimalHandlers:
    """Tests for create_minimal_handlers factory."""

    def test_returns_handlers(self, temp_project):
        """Returns a dictionary of handlers."""
        handlers = create_minimal_handlers(temp_project)

        assert isinstance(handlers, dict)
        assert len(handlers) > 0

    def test_includes_basic_file_ops(self, temp_project):
        """Includes basic file operations."""
        handlers = create_minimal_handlers(temp_project)

        assert "read_file" in handlers
        assert "write_file" in handlers
        assert "edit_file" in handlers

    def test_includes_terminal_actions(self, temp_project):
        """Includes terminal actions."""
        handlers = create_minimal_handlers(temp_project)

        assert "complete" in handlers
        assert "escalate" in handlers

    def test_excludes_advanced_handlers(self, temp_project):
        """Does not include advanced handlers."""
        handlers = create_minimal_handlers(temp_project)

        # Minimal set should be smaller
        assert len(handlers) < len(create_standard_handlers(temp_project))


class TestToolHandlerRegistry:
    """Tests for ToolHandlerRegistry."""

    def test_empty_registry(self, temp_project):
        """Empty registry has no handlers."""
        registry = ToolHandlerRegistry(temp_project)

        handlers = registry.get_handlers()

        assert len(handlers) == 0

    def test_register_single_handler(self, temp_project):
        """Register a single handler."""
        registry = ToolHandlerRegistry(temp_project)

        def my_handler(params):
            return "result"

        registry.register("my_tool", my_handler)
        handlers = registry.get_handlers()

        assert "my_tool" in handlers
        assert handlers["my_tool"]({}) == "result"

    def test_register_multiple_handlers(self, temp_project):
        """Register multiple handlers at once."""
        registry = ToolHandlerRegistry(temp_project)

        def handler_a(params):
            return "a"

        def handler_b(params):
            return "b"

        registry.register_all({"a": handler_a, "b": handler_b})
        handlers = registry.get_handlers()

        assert "a" in handlers
        assert "b" in handlers

    def test_add_file_handlers(self, temp_project):
        """Add file handlers group."""
        registry = ToolHandlerRegistry(temp_project)

        registry.add_file_handlers()
        handlers = registry.get_handlers()

        assert "read_file" in handlers
        assert "write_file" in handlers
        assert "edit_file" in handlers

    def test_add_search_handlers(self, temp_project):
        """Add search handlers group."""
        registry = ToolHandlerRegistry(temp_project)

        registry.add_search_handlers()
        handlers = registry.get_handlers()

        assert "search_code" in handlers
        assert "load_context" in handlers

    def test_add_verify_handlers(self, temp_project):
        """Add verify handlers group."""
        registry = ToolHandlerRegistry(temp_project)

        registry.add_verify_handlers()
        handlers = registry.get_handlers()

        assert "run_check" in handlers
        assert "run_tests" in handlers

    def test_add_terminal_handlers(self, temp_project):
        """Add terminal handlers group."""
        registry = ToolHandlerRegistry(temp_project)

        registry.add_terminal_handlers()
        handlers = registry.get_handlers()

        assert "complete" in handlers
        assert "escalate" in handlers
        assert "cannot_fix" in handlers

    def test_add_all(self, temp_project):
        """Add all handler groups."""
        registry = ToolHandlerRegistry(temp_project)

        registry.add_all()
        handlers = registry.get_handlers()

        # Should have all handlers
        assert "read_file" in handlers
        assert "search_code" in handlers
        assert "run_check" in handlers
        assert "complete" in handlers

    def test_fluent_interface(self, temp_project):
        """Registry supports fluent interface."""
        registry = ToolHandlerRegistry(temp_project)

        handlers = (
            registry
            .add_file_handlers()
            .add_terminal_handlers()
            .get_handlers()
        )

        assert "read_file" in handlers
        assert "complete" in handlers
        assert "search_code" not in handlers

    def test_has_handler(self, temp_project):
        """Check if handler is registered."""
        registry = ToolHandlerRegistry(temp_project)
        registry.add_file_handlers()

        assert registry.has_handler("read_file")
        assert not registry.has_handler("nonexistent")

    def test_list_handlers(self, temp_project):
        """List all registered handler names."""
        registry = ToolHandlerRegistry(temp_project)
        registry.add_file_handlers()

        names = registry.list_handlers()

        assert isinstance(names, list)
        assert "read_file" in names
        assert names == sorted(names)  # Should be sorted

    def test_custom_handler_overrides(self, temp_project):
        """Custom handler can override built-in."""
        registry = ToolHandlerRegistry(temp_project)
        registry.add_file_handlers()

        def custom_read(params):
            return "custom result"

        registry.register("read_file", custom_read)
        handlers = registry.get_handlers()

        assert handlers["read_file"]({}) == "custom result"


class TestHandlerIntegration:
    """Integration tests for handlers working together."""

    def test_write_and_read(self, temp_project):
        """Write then read a file."""
        handlers = create_standard_handlers(temp_project)

        # Write a file
        write_result = handlers["write_file"]({
            "path": "test.txt",
            "content": "Hello World",
        })
        assert "SUCCESS" in write_result

        # Read it back
        read_result = handlers["read_file"]({"path": "test.txt"})
        assert "SUCCESS" in read_result
        assert "Hello World" in read_result

    def test_write_edit_read(self, temp_project):
        """Write, edit, then read a file."""
        handlers = create_standard_handlers(temp_project)

        # Write initial content
        handlers["write_file"]({
            "path": "lines.txt",
            "content": "line1\nline2\nline3\n",
        })

        # Edit middle line
        edit_result = handlers["edit_file"]({
            "path": "lines.txt",
            "start_line": 2,
            "end_line": 2,
            "new_content": "modified",
        })
        assert "SUCCESS" in edit_result

        # Read and verify
        read_result = handlers["read_file"]({"path": "lines.txt"})
        assert "line1" in read_result
        assert "modified" in read_result
        assert "line3" in read_result

    def test_search_after_write(self, temp_project):
        """Search finds newly written content."""
        handlers = create_standard_handlers(temp_project)

        # Create a Python file with function
        (temp_project / "module.py").write_text(
            "def unique_function_name():\n    pass\n"
        )

        # Search for it
        search_result = handlers["search_code"]({
            "pattern": "unique_function_name",
        })
        assert "module.py" in search_result
        assert "Found" in search_result
