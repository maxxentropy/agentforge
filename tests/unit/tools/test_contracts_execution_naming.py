# @spec_file: .agentforge/specs/core-refactoring-v1.yaml
# @spec_id: core-refactoring-v1
# @component_id: tools-refactoring-base
# @impl_path: tools/refactoring/base.py

"""Tests for naming and AST interface check handlers in contracts_execution.py."""

from pathlib import Path

import pytest

from agentforge.core.contracts_execution import (
    CheckContext,
    _execute_ast_interface_check,
    _execute_naming_check,
    _extract_class_with_bases,
    _extract_symbols,
    _parse_inheritance_list,
)


class TestExtractSymbols:
    """Tests for symbol extraction from source code."""

    def test_extract_csharp_class(self):
        """Extract C# class names."""
        content = """
namespace MyApp {
    public class MyService {
    }
    internal class Helper {
    }
}
"""
        symbols = _extract_symbols(content, "class", ".cs")
        names = [s[0] for s in symbols]
        assert "MyService" in names
        assert "Helper" in names

    def test_extract_csharp_sealed_class(self):
        """Extract C# sealed class."""
        content = """public sealed class SealedService { }"""
        symbols = _extract_symbols(content, "class", ".cs")
        assert symbols[0][0] == "SealedService"

    def test_extract_csharp_abstract_class(self):
        """Extract C# abstract class."""
        content = """public abstract class BaseHandler { }"""
        symbols = _extract_symbols(content, "class", ".cs")
        assert symbols[0][0] == "BaseHandler"

    def test_extract_csharp_partial_class(self):
        """Extract C# partial class."""
        content = """public partial class PartialCommand { }"""
        symbols = _extract_symbols(content, "class", ".cs")
        assert symbols[0][0] == "PartialCommand"

    def test_extract_csharp_interface(self):
        """Extract C# interface names."""
        content = """
public interface IRepository { }
internal interface IService { }
"""
        symbols = _extract_symbols(content, "interface", ".cs")
        names = [s[0] for s in symbols]
        assert "IRepository" in names
        assert "IService" in names

    def test_extract_python_class(self):
        """Extract Python class names."""
        content = """
class MyHandler:
    pass

class AnotherClass(BaseClass):
    pass
"""
        symbols = _extract_symbols(content, "class", ".py")
        names = [s[0] for s in symbols]
        assert "MyHandler" in names
        assert "AnotherClass" in names

    def test_extract_typescript_class(self):
        """Extract TypeScript class names."""
        content = """
export class UserService {
}
abstract class BaseRepository {
}
"""
        symbols = _extract_symbols(content, "class", ".ts")
        names = [s[0] for s in symbols]
        assert "UserService" in names
        assert "BaseRepository" in names

    def test_extract_unsupported_language(self):
        """Return empty for unsupported file type."""
        symbols = _extract_symbols("class Foo", "class", ".rb")
        assert symbols == []

    def test_line_numbers_correct(self):
        """Verify line numbers are correct."""
        content = """line1
line2
public class MyClass {
}
"""
        symbols = _extract_symbols(content, "class", ".cs")
        assert symbols[0][1] == 3  # Line 3


class TestExtractClassWithBases:
    """Tests for extracting classes with inheritance."""

    def test_csharp_class_with_interface(self):
        """Extract C# class with interface."""
        content = """public class CreateCommand : IRequest<Response> { }"""
        classes = _extract_class_with_bases(content, ".cs")
        assert len(classes) == 1
        assert classes[0][0] == "CreateCommand"
        assert "IRequest<Response>" in classes[0][1]

    def test_csharp_class_multiple_interfaces(self):
        """Extract C# class with multiple interfaces."""
        content = """public class Handler : BaseHandler, IRequestHandler<Cmd, Resp>, IDisposable { }"""
        classes = _extract_class_with_bases(content, ".cs")
        assert len(classes) == 1
        name, bases, _ = classes[0]
        assert name == "Handler"
        assert "BaseHandler" in bases
        assert "IRequestHandler<Cmd, Resp>" in bases
        assert "IDisposable" in bases

    def test_csharp_class_no_inheritance(self):
        """Extract C# class without inheritance."""
        content = """public class SimpleClass { }"""
        classes = _extract_class_with_bases(content, ".cs")
        assert len(classes) == 1
        assert classes[0][0] == "SimpleClass"
        assert classes[0][1] == ""

    def test_python_class_with_bases(self):
        """Extract Python class with base classes."""
        content = """class MyHandler(BaseHandler, Mixin):
    pass"""
        classes = _extract_class_with_bases(content, ".py")
        assert len(classes) == 1
        name, bases, _ = classes[0]
        assert name == "MyHandler"
        assert "BaseHandler" in bases
        assert "Mixin" in bases


class TestParseInheritanceList:
    """Tests for parsing inheritance strings."""

    def test_simple_list(self):
        """Parse simple comma-separated list."""
        bases = _parse_inheritance_list("IFoo, IBar, IBaz", ".cs")
        assert bases == ["IFoo", "IBar", "IBaz"]

    def test_generic_types(self):
        """Remove generic parameters."""
        bases = _parse_inheritance_list("IRequest<TResponse>, IDisposable", ".cs")
        assert "IRequest" in bases
        assert "IDisposable" in bases

    def test_where_clause(self):
        """Handle where clause in C#."""
        bases = _parse_inheritance_list("IHandler where T : class", ".cs")
        assert bases == ["IHandler"]

    def test_empty_string(self):
        """Return empty for empty string."""
        bases = _parse_inheritance_list("", ".cs")
        assert bases == []


class TestNamingCheck:
    """Tests for the naming convention check handler."""

    @pytest.fixture
    def temp_cs_file(self, tmp_path: Path) -> Path:
        """Create a temporary C# file."""
        cs_file = tmp_path / "src" / "Commands" / "CreateUserCommand.cs"
        cs_file.parent.mkdir(parents=True)
        cs_file.write_text("""
namespace App.Commands {
    public class CreateUserCommand : IRequest<Result> { }
    public class UpdateUserCommand : IRequest<Result> { }
    public class Helper { }
}
""")
        return cs_file

    def test_naming_match_passes(self, tmp_path: Path, temp_cs_file: Path):
        """Classes matching pattern produce no violations."""
        ctx = CheckContext(
            check_id="test-naming",
            check_name="Command Naming",
            severity="minor",
            config={"pattern": ".*Command$", "symbol_type": "class"},
            repo_root=tmp_path,
            file_paths=[temp_cs_file],
        )
        results = _execute_naming_check(ctx)
        # Helper doesn't match, but CreateUserCommand and UpdateUserCommand do
        violations = [r for r in results if not r.passed]
        assert len(violations) == 1  # Only Helper
        assert "Helper" in violations[0].message

    def test_naming_forbid_mode(self, tmp_path: Path):
        """Forbid mode catches matching names."""
        test_file = tmp_path / "Test.cs"
        test_file.write_text("public class ForbiddenClass { }")

        ctx = CheckContext(
            check_id="test-forbid",
            check_name="Forbid Test",
            severity="warning",
            config={"pattern": ".*Forbidden.*", "symbol_type": "class", "mode": "forbid"},
            repo_root=tmp_path,
            file_paths=[test_file],
        )
        results = _execute_naming_check(ctx)
        assert len(results) == 1
        assert "forbidden pattern" in results[0].message.lower()

    def test_naming_missing_pattern_error(self, tmp_path: Path):
        """Missing pattern in config produces error."""
        ctx = CheckContext(
            check_id="test-error",
            check_name="Error Test",
            severity="error",
            config={"symbol_type": "class"},  # No pattern!
            repo_root=tmp_path,
            file_paths=[],
        )
        results = _execute_naming_check(ctx)
        assert len(results) == 1
        assert "missing 'pattern'" in results[0].message.lower()

    def test_naming_invalid_pattern_error(self, tmp_path: Path):
        """Invalid regex pattern produces error."""
        ctx = CheckContext(
            check_id="test-invalid",
            check_name="Invalid Regex",
            severity="error",
            config={"pattern": "[invalid(", "symbol_type": "class"},
            repo_root=tmp_path,
            file_paths=[],
        )
        results = _execute_naming_check(ctx)
        assert len(results) == 1
        assert "invalid" in results[0].message.lower()


class TestAstInterfaceCheck:
    """Tests for the AST interface implementation check handler."""

    @pytest.fixture
    def temp_command_file(self, tmp_path: Path) -> Path:
        """Create a temp C# file with commands."""
        cs_file = tmp_path / "src" / "Commands" / "Commands.cs"
        cs_file.parent.mkdir(parents=True)
        cs_file.write_text("""
namespace App.Commands {
    public class CreateUserCommand : IRequest<UserDto> { }
    public class DeleteUserCommand : IRequest<bool>, IValidatable { }
    public class BadCommand { }
}
""")
        return cs_file

    def test_must_implement_satisfied(self, tmp_path: Path, temp_command_file: Path):
        """No violation when interface is implemented."""
        ctx = CheckContext(
            check_id="test-impl",
            check_name="Commands implement IRequest",
            severity="warning",
            config={
                "class_pattern": "CreateUserCommand",
                "must_implement": ["IRequest"],
            },
            repo_root=tmp_path,
            file_paths=[temp_command_file],
        )
        results = _execute_ast_interface_check(ctx)
        # CreateUserCommand implements IRequest<UserDto>, which starts with IRequest
        assert len(results) == 0

    def test_must_implement_violated(self, tmp_path: Path, temp_command_file: Path):
        """Violation when required interface is missing."""
        ctx = CheckContext(
            check_id="test-missing",
            check_name="Commands implement IRequest",
            severity="warning",
            config={
                "class_pattern": "BadCommand",
                "must_implement": ["IRequest"],
            },
            repo_root=tmp_path,
            file_paths=[temp_command_file],
        )
        results = _execute_ast_interface_check(ctx)
        assert len(results) == 1
        assert "must implement 'IRequest'" in results[0].message

    def test_must_implement_pattern_match(self, tmp_path: Path, temp_command_file: Path):
        """Pattern matching selects correct classes."""
        ctx = CheckContext(
            check_id="test-pattern",
            check_name="All Commands implement IRequest",
            severity="warning",
            config={
                "class_pattern": ".*Command$",
                "must_implement": ["IRequest"],
            },
            repo_root=tmp_path,
            file_paths=[temp_command_file],
        )
        results = _execute_ast_interface_check(ctx)
        # Only BadCommand should fail - CreateUserCommand and DeleteUserCommand have IRequest
        assert len(results) == 1
        assert "BadCommand" in results[0].message

    def test_must_not_implement(self, tmp_path: Path, temp_command_file: Path):
        """Violation when forbidden interface is implemented."""
        ctx = CheckContext(
            check_id="test-forbid",
            check_name="Commands must not be Validatable",
            severity="minor",
            config={
                "class_pattern": ".*Command$",
                "must_not_implement": ["IValidatable"],
            },
            repo_root=tmp_path,
            file_paths=[temp_command_file],
        )
        results = _execute_ast_interface_check(ctx)
        assert len(results) == 1
        assert "DeleteUserCommand" in results[0].message
        assert "must not implement" in results[0].message

    def test_missing_class_pattern_error(self, tmp_path: Path):
        """Missing class_pattern produces error."""
        ctx = CheckContext(
            check_id="test-error",
            check_name="Error",
            severity="error",
            config={"must_implement": ["IFoo"]},
            repo_root=tmp_path,
            file_paths=[],
        )
        results = _execute_ast_interface_check(ctx)
        assert len(results) == 1
        assert "missing 'class_pattern'" in results[0].message.lower()

    def test_invalid_class_pattern_error(self, tmp_path: Path):
        """Invalid class pattern regex produces error."""
        ctx = CheckContext(
            check_id="test-invalid",
            check_name="Invalid",
            severity="error",
            config={"class_pattern": "[bad(", "must_implement": []},
            repo_root=tmp_path,
            file_paths=[],
        )
        results = _execute_ast_interface_check(ctx)
        assert len(results) == 1
        assert "invalid" in results[0].message.lower()


class TestIntegration:
    """Integration tests with execute_check."""

    def test_naming_check_type_registered(self, tmp_path: Path):
        """Verify 'naming' check type is in dispatch table."""
        from agentforge.core.contracts_execution import execute_check

        test_file = tmp_path / "Test.cs"
        test_file.write_text("public class TestHandler { }")

        check = {
            "id": "int-test",
            "name": "Integration Test",
            "type": "naming",
            "severity": "minor",
            "config": {"pattern": ".*Handler$", "symbol_type": "class"},
            "applies_to": {"paths": ["*.cs"]},
        }
        results = execute_check(check, tmp_path, [test_file])
        # Should not return "Unknown check type"
        assert not any("unknown check type" in r.message.lower() for r in results)

    def test_ast_check_type_registered(self, tmp_path: Path):
        """Verify 'ast' check type is in dispatch table."""
        from agentforge.core.contracts_execution import execute_check

        test_file = tmp_path / "Test.cs"
        test_file.write_text("public class TestCommand : IRequest<bool> { }")

        check = {
            "id": "int-test",
            "name": "Integration Test",
            "type": "ast",
            "severity": "warning",
            "config": {
                "class_pattern": ".*Command$",
                "must_implement": ["IRequest"],
            },
            "applies_to": {"paths": ["*.cs"]},
        }
        results = execute_check(check, tmp_path, [test_file])
        # Should not return "Unknown check type"
        assert not any("unknown check type" in r.message.lower() for r in results)
