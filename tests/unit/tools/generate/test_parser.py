# @spec_file: .agentforge/specs/core-generate-v1.yaml
# @spec_id: core-generate-v1
# @component_id: tools-generate-parser
# @impl_path: tools/generate/parser.py

"""
Tests for Response Parser
=========================
"""

from pathlib import Path

import pytest

from agentforge.core.generate.domain import FileAction, ParseError
from agentforge.core.generate.parser import (
    MultiLanguageParser,
    ResponseParser,
    parse_response,
)

# =============================================================================
# ResponseParser Tests
# =============================================================================


class TestResponseParserBasic:
    """Basic parsing tests."""

    @pytest.fixture
    def parser(self):
        return ResponseParser()

    def test_parse_single_file(self, parser):
        response = '''Here's the implementation:

```python:src/calculator.py
def add(a, b):
    return a + b
```
'''
        files = parser.parse(response)
        assert len(files) == 1
        assert files[0].path == Path("src/calculator.py")
        assert "def add" in files[0].content

    def test_parse_multiple_files(self, parser):
        response = '''Creating test and implementation:

```python:tests/test_calc.py
def test_add():
    assert add(1, 2) == 3
```

And the implementation:

```python:src/calc.py
def add(a, b):
    return a + b
```
'''
        files = parser.parse(response)
        assert len(files) == 2
        assert files[0].path == Path("tests/test_calc.py")
        assert files[1].path == Path("src/calc.py")

    def test_parse_py_shorthand(self, parser):
        response = '''```py:src/module.py
x = 1
```'''
        files = parser.parse(response)
        assert len(files) == 1
        assert files[0].path == Path("src/module.py")

    def test_file_action_is_create(self, parser):
        response = '''```python:src/new_file.py
pass
```'''
        files = parser.parse(response)
        assert files[0].action == FileAction.CREATE

    def test_no_files_raises_parse_error(self, parser):
        response = "Here's some text without any code blocks."
        with pytest.raises(ParseError) as exc_info:
            parser.parse(response)
        assert "No code files found" in str(exc_info.value)

    def test_parse_error_includes_raw_response(self, parser):
        response = "No code here"
        with pytest.raises(ParseError) as exc_info:
            parser.parse(response)
        assert exc_info.value.raw_response == "No code here"


class TestResponseParserContentCleaning:
    """Tests for content cleaning."""

    @pytest.fixture
    def parser(self):
        return ResponseParser()

    def test_strips_trailing_whitespace(self, parser):
        response = '''```python:test.py
def foo():
    pass
```'''
        files = parser.parse(response)
        # Lines should not have trailing spaces
        assert "   \n" not in files[0].content

    def test_removes_leading_blank_lines(self, parser):
        response = '''```python:test.py

def foo():
    pass
```'''
        files = parser.parse(response)
        assert files[0].content.startswith("def foo")

    def test_removes_trailing_blank_lines(self, parser):
        response = '''```python:test.py
def foo():
    pass

```'''
        files = parser.parse(response)
        assert files[0].content.rstrip() == "def foo():\n    pass"

    def test_preserves_internal_blank_lines(self, parser):
        response = '''```python:test.py
def foo():
    pass

def bar():
    pass
```'''
        files = parser.parse(response)
        assert "\n\n" in files[0].content

    def test_adds_trailing_newline(self, parser):
        response = '''```python:test.py
x = 1```'''
        files = parser.parse(response)
        assert files[0].content.endswith("\n")


class TestResponseParserSyntaxValidation:
    """Tests for Python syntax validation."""

    @pytest.fixture
    def parser(self):
        return ResponseParser(validate_syntax=True)

    @pytest.fixture
    def no_validate_parser(self):
        return ResponseParser(validate_syntax=False)

    def test_valid_syntax_passes(self, parser):
        response = '''```python:test.py
def foo():
    return 42
```'''
        files = parser.parse(response)
        assert len(files) == 1

    def test_invalid_syntax_raises(self, parser):
        response = '''```python:test.py
def foo(
    # missing closing paren
```'''
        with pytest.raises(ParseError) as exc_info:
            parser.parse(response)
        assert "Invalid Python syntax" in str(exc_info.value)
        assert "test.py" in str(exc_info.value)

    def test_validation_disabled(self, no_validate_parser):
        response = '''```python:test.py
def foo(
    # this is invalid but should pass
```'''
        files = no_validate_parser.parse(response)
        assert len(files) == 1

    def test_parse_error_includes_line_number(self, parser):
        response = '''```python:test.py
def foo():
    pass
def bar(
```'''
        with pytest.raises(ParseError) as exc_info:
            parser.parse(response)
        assert exc_info.value.position is not None


class TestResponseParserImplicitPaths:
    """Tests for implicit path inference."""

    @pytest.fixture
    def parser(self):
        return ResponseParser()

    def test_infers_path_from_text(self, parser):
        response = '''I'll create the file: tests/test_example.py

```python
def test_foo():
    pass
```'''
        files = parser.parse(response)
        assert len(files) == 1
        assert files[0].path == Path("tests/test_example.py")

    def test_infers_path_from_output_to(self, parser):
        response = '''Output to: src/module.py

```python
x = 1
```'''
        files = parser.parse(response)
        assert files[0].path == Path("src/module.py")

    def test_infers_path_with_backticks(self, parser):
        response = '''Write to `src/util.py`:

```python
def helper():
    pass
```'''
        files = parser.parse(response)
        assert files[0].path == Path("src/util.py")

    def test_no_path_found_raises(self, parser):
        response = '''Here's some code:

```python
x = 1
```'''
        with pytest.raises(ParseError):
            parser.parse(response)


class TestResponseParserExplanation:
    """Tests for explanation extraction."""

    @pytest.fixture
    def parser(self):
        return ResponseParser()

    def test_extract_explanation(self, parser):
        response = '''Here's the implementation:

```python:src/module.py
x = 1
```

This creates a simple variable.'''

        explanation = parser.extract_explanation(response)
        assert "Here's the implementation" in explanation
        assert "creates a simple variable" in explanation
        assert "x = 1" not in explanation

    def test_extract_explanation_removes_code_blocks(self, parser):
        response = '''Before code.

```python:test.py
code
```

After code.'''

        explanation = parser.extract_explanation(response)
        assert "code" not in explanation or "Before" in explanation

    def test_parse_with_explanation(self, parser):
        response = '''Creating module:

```python:src/mod.py
x = 1
```

Done!'''

        files, explanation = parser.parse_with_explanation(response)
        assert len(files) == 1
        assert "Creating module" in explanation
        assert "Done" in explanation


# =============================================================================
# MultiLanguageParser Tests
# =============================================================================


class TestMultiLanguageParser:
    """Tests for multi-language support."""

    @pytest.fixture
    def parser(self):
        return MultiLanguageParser()

    def test_parse_typescript(self, parser):
        response = '''```typescript:src/index.ts
const x: number = 1;
```'''
        files = parser.parse(response)
        assert len(files) == 1
        assert files[0].path == Path("src/index.ts")

    def test_parse_csharp(self, parser):
        response = '''```csharp:src/Program.cs
class Program { }
```'''
        files = parser.parse(response)
        assert files[0].path == Path("src/Program.cs")

    def test_parse_mixed_languages(self, parser):
        response = '''```python:src/main.py
print("hello")
```

```typescript:src/client.ts
console.log("hello");
```'''
        files = parser.parse(response)
        assert len(files) == 2
        assert files[0].path.suffix == ".py"
        assert files[1].path.suffix == ".ts"

    def test_validates_python_only(self, parser):
        # Invalid Python should raise
        response = '''```python:test.py
def foo(
```'''
        with pytest.raises(ParseError):
            parser.parse(response)

        # Invalid TypeScript should NOT raise (no TS validation)
        response = '''```typescript:test.ts
const x: = 1; // invalid TS
```'''
        files = parser.parse(response)
        assert len(files) == 1

    def test_falls_back_to_python_parser(self, parser):
        # Standard python:path format should still work
        response = '''```python:src/mod.py
x = 1
```'''
        files = parser.parse(response)
        assert len(files) == 1


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestParseResponseFunction:
    """Tests for the parse_response convenience function."""

    def test_basic_usage(self):
        response = '''```python:test.py
x = 1
```'''
        files = parse_response(response)
        assert len(files) == 1

    def test_with_validation_disabled(self):
        response = '''```python:test.py
def bad(
```'''
        files = parse_response(response, validate_syntax=False)
        assert len(files) == 1

    def test_with_validation_enabled(self):
        response = '''```python:test.py
def bad(
```'''
        with pytest.raises(ParseError):
            parse_response(response, validate_syntax=True)


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def parser(self):
        return ResponseParser()

    def test_empty_response(self, parser):
        with pytest.raises(ParseError):
            parser.parse("")

    def test_only_whitespace(self, parser):
        with pytest.raises(ParseError):
            parser.parse("   \n\n   ")

    def test_unclosed_code_block(self, parser):
        response = '''```python:test.py
x = 1
# no closing backticks'''
        with pytest.raises(ParseError):
            parser.parse(response)

    def test_path_with_spaces_in_dir(self, parser):
        response = '''```python:src/my module/test.py
x = 1
```'''
        files = parser.parse(response)
        assert "my module" in str(files[0].path)

    def test_deeply_nested_path(self, parser):
        response = '''```python:src/a/b/c/d/e/test.py
x = 1
```'''
        files = parser.parse(response)
        assert files[0].path == Path("src/a/b/c/d/e/test.py")

    def test_relative_path_with_dots(self, parser):
        response = '''```python:../tests/test.py
x = 1
```'''
        files = parser.parse(response)
        assert ".." in str(files[0].path)

    def test_preserves_indentation(self, parser):
        response = '''```python:test.py
class Foo:
    def bar(self):
        if True:
            return 1
```'''
        files = parser.parse(response)
        content = files[0].content
        assert "    def bar" in content
        assert "        if True" in content
        assert "            return" in content

    def test_handles_triple_quotes_in_code(self, parser):
        response = '''```python:test.py
"""Docstring"""
x = 1
```'''
        files = parser.parse(response)
        assert '"""Docstring"""' in files[0].content

    def test_handles_backticks_in_strings(self, parser):
        response = '''```python:test.py
x = "contains `backticks`"
```'''
        files = parser.parse(response)
        assert "`backticks`" in files[0].content
