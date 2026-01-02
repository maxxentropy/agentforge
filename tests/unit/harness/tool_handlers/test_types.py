# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: tool-handler-types

"""
Tests for tool handler types and utilities.
"""


import pytest

from agentforge.core.harness.minimal_context.tool_handlers.types import (
    ActionHandler,
    validate_path_security,
)


class TestValidatePathSecurity:
    """Tests for validate_path_security function."""

    def test_valid_relative_path(self, tmp_path):
        """Valid relative path within base directory."""
        # Create a file
        (tmp_path / "src").mkdir()
        test_file = tmp_path / "src" / "module.py"
        test_file.write_text("# test")

        resolved, error = validate_path_security("src/module.py", tmp_path)

        assert error is None
        assert resolved == test_file

    def test_valid_absolute_path(self, tmp_path):
        """Valid absolute path within base directory."""
        test_file = tmp_path / "module.py"
        test_file.write_text("# test")

        resolved, error = validate_path_security(str(test_file), tmp_path)

        assert error is None
        assert resolved == test_file

    def test_path_traversal_rejected(self, tmp_path):
        """Path traversal attempts are rejected."""
        resolved, error = validate_path_security("../../../etc/passwd", tmp_path)

        assert error is not None
        assert "escapes project directory" in error

    def test_path_traversal_with_dots(self, tmp_path):
        """Path with .. components that escape is rejected."""
        (tmp_path / "src").mkdir()

        resolved, error = validate_path_security("src/../../outside.py", tmp_path)

        assert error is not None
        assert "escapes project directory" in error

    def test_file_not_found(self, tmp_path):
        """Non-existent file returns error."""
        resolved, error = validate_path_security("nonexistent.py", tmp_path)

        assert error is not None
        assert "not found" in error.lower()

    def test_allow_create(self, tmp_path):
        """allow_create=True allows non-existent files."""
        resolved, error = validate_path_security(
            "new_file.py", tmp_path, allow_create=True
        )

        assert error is None
        assert resolved == tmp_path / "new_file.py"

    def test_allow_create_with_subdirectory(self, tmp_path):
        """allow_create=True allows non-existent files in subdirs."""
        resolved, error = validate_path_security(
            "new_dir/new_file.py", tmp_path, allow_create=True
        )

        assert error is None
        assert resolved == tmp_path / "new_dir" / "new_file.py"

    def test_symlink_escape_rejected(self, tmp_path):
        """Symlinks that escape base directory are rejected."""
        # Create a symlink pointing outside
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        (outside_dir / "secret.txt").write_text("secret")

        symlink = tmp_path / "escape"
        try:
            symlink.symlink_to(outside_dir)
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")

        resolved, error = validate_path_security("escape/secret.txt", tmp_path)

        assert error is not None
        assert "escapes project directory" in error

    def test_absolute_path_outside_allowed(self, tmp_path):
        """Absolute path outside base directory is allowed (explicit paths trusted).

        Note: Absolute paths are trusted since the caller explicitly provided
        them. The security protection is primarily for relative paths that
        could use .. to escape the project directory.
        """
        # /etc/passwd exists on most Unix systems
        resolved, error = validate_path_security("/etc/passwd", tmp_path)

        # Allowed but file may not exist on all systems
        # If file exists, no error; if not, "not found" error
        if resolved.exists():
            assert error is None
        else:
            assert error is not None
            assert "not found" in error.lower()

    def test_path_with_valid_dots(self, tmp_path):
        """Path with .. that stays inside is allowed."""
        (tmp_path / "src").mkdir()
        (tmp_path / "lib").mkdir()
        test_file = tmp_path / "lib" / "module.py"
        test_file.write_text("# test")

        resolved, error = validate_path_security("src/../lib/module.py", tmp_path)

        assert error is None
        assert resolved == test_file


class TestActionHandler:
    """Tests for ActionHandler type."""

    def test_handler_is_callable_type(self):
        """ActionHandler is a callable type."""
        from typing import Any

        # ActionHandler should accept Dict[str, Any] and return str
        def my_handler(params: dict[str, Any]) -> str:
            return "result"

        # This is a type check - the function should be compatible
        handler: ActionHandler = my_handler
        assert callable(handler)
        assert handler({"key": "value"}) == "result"
