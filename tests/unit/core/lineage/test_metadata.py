# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-lineage-metadata

"""
Tests for lineage metadata module.

Tests the core data structures and utilities for embedding and extracting
lineage information from generated source files.
"""

from datetime import datetime

from agentforge.core.lineage.metadata import (
    LineageMetadata,
    generate_lineage_header,
    get_test_path_from_lineage,
    parse_lineage_from_file,
)


class TestLineageMetadata:
    """Tests for LineageMetadata dataclass."""

    def test_to_header_comments_basic(self):
        """Should generate header comments with required fields."""
        metadata = LineageMetadata(
            generated_at=datetime(2026, 1, 2, 12, 0, 0),
            generator="tdflow.red.v1",
            spec_file=".agentforge/specs/core-v1.yaml",
            spec_id="core-v1",
            component_id="core-example",
        )

        header = metadata.to_header_comments()

        assert "# @generated: 2026-01-02T12:00:00" in header, "Expected '# @generated: 2026-01-02T1... in header"
        assert "# @generator: tdflow.red.v1" in header, "Expected '# @generator: tdflow.red.v1' in header"
        assert "# @spec_file: .agentforge/specs/core-v1.yaml" in header, "Expected '# @spec_file: .agentforge/... in header"
        assert "# @spec_id: core-v1" in header, "Expected '# @spec_id: core-v1' in header"
        assert "# @component_id: core-example" in header, "Expected '# @component_id: core-exam... in header"
        assert "═" * 77 in header, "Expected '═' * 77 in header"# Border character

    def test_to_header_comments_with_optional_fields(self):
        """Should include optional fields when present."""
        metadata = LineageMetadata(
            generated_at=datetime(2026, 1, 2, 12, 0, 0),
            generator="tdflow.green.v1",
            spec_file=".agentforge/specs/core-v1.yaml",
            spec_id="core-v1",
            component_id="core-example",
            method_ids=["method_a", "method_b"],
            test_path="tests/unit/test_example.py",
            session_id="sess-123",
        )

        header = metadata.to_header_comments()

        assert "# @method_ids: method_a,method_b" in header, "Expected '# @method_ids: method_a,me... in header"
        assert "# @test_path: tests/unit/test_example.py" in header, "Expected '# @test_path: tests/unit/t... in header"
        assert "# @session_id: sess-123" in header, "Expected '# @session_id: sess-123' in header"

    def test_to_header_comments_with_impl_path(self):
        """Should include impl_path for test files."""
        metadata = LineageMetadata(
            generated_at=datetime(2026, 1, 2, 12, 0, 0),
            generator="tdflow.red.v1",
            spec_file=".agentforge/specs/core-v1.yaml",
            spec_id="core-v1",
            component_id="core-example",
            impl_path="src/agentforge/core/example.py",
        )

        header = metadata.to_header_comments()

        assert "# @impl_path: src/agentforge/core/example.py" in header, "Expected '# @impl_path: src/agentfor... in header"

    def test_to_header_comments_with_different_prefix(self):
        """Should use specified comment prefix."""
        metadata = LineageMetadata(
            generated_at=datetime(2026, 1, 2, 12, 0, 0),
            generator="tdflow.red.v1",
            spec_file=".agentforge/specs/core-v1.yaml",
            spec_id="core-v1",
            component_id="core-example",
        )

        header = metadata.to_header_comments(comment_prefix="//")

        assert "// @generated:" in header, "Expected '// @generated:' in header"
        assert "// @generator:" in header, "Expected '// @generator:' in header"
        assert "// ═" in header, "Expected '// ═' in header"


class TestParseLineageFromFile:
    """Tests for parse_lineage_from_file function."""

    def test_parse_full_lineage(self, tmp_path):
        """Should parse file with complete lineage metadata."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''# ═══════════════════════════════════════════════════════════════════════════════
# LINEAGE METADATA - DO NOT EDIT THIS BLOCK
# ═══════════════════════════════════════════════════════════════════════════════
# @generated: 2026-01-02T12:00:00
# @generator: tdflow.red.v1
# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-example
# @method_ids: test_a,test_b
# @test_path: tests/unit/test_example.py
# @session_id: sess-abc123
# ═══════════════════════════════════════════════════════════════════════════════

def example():
    pass
''')

        metadata = parse_lineage_from_file(file_path)

        assert metadata is not None, "Expected metadata is not None"
        assert metadata.generator == "tdflow.red.v1", "Expected metadata.generator to equal 'tdflow.red.v1'"
        assert metadata.spec_file == ".agentforge/specs/core-v1.yaml", "Expected metadata.spec_file to equal '.agentforge/specs/core-v1...."
        assert metadata.spec_id == "core-v1", "Expected metadata.spec_id to equal 'core-v1'"
        assert metadata.component_id == "core-example", "Expected metadata.component_id to equal 'core-example'"
        assert metadata.method_ids == ["test_a", "test_b"], "Expected metadata.method_ids to equal ['test_a', 'test_b']"
        assert metadata.test_path == "tests/unit/test_example.py", "Expected metadata.test_path to equal 'tests/unit/test_example.py'"
        assert metadata.session_id == "sess-abc123", "Expected metadata.session_id to equal 'sess-abc123'"

    def test_parse_minimal_lineage(self, tmp_path):
        """Should parse file with only required fields."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''# @generated: 2026-01-02T12:00:00
# @generator: tdflow.red.v1
# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-example

def example():
    pass
''')

        metadata = parse_lineage_from_file(file_path)

        assert metadata is not None, "Expected metadata is not None"
        assert metadata.spec_id == "core-v1", "Expected metadata.spec_id to equal 'core-v1'"
        assert metadata.test_path is None, "Expected metadata.test_path is None"
        assert metadata.impl_path is None, "Expected metadata.impl_path is None"
        assert metadata.method_ids == [], "Expected metadata.method_ids to equal []"

    def test_parse_simple_annotations(self, tmp_path):
        """Should parse file with simple @ annotations (no LINEAGE block)."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-example
# @generated: 2026-01-02T12:00:00
# @generator: manual

def example():
    pass
''')

        metadata = parse_lineage_from_file(file_path)

        assert metadata is not None, "Expected metadata is not None"
        assert metadata.spec_id == "core-v1", "Expected metadata.spec_id to equal 'core-v1'"

    def test_parse_no_lineage(self, tmp_path):
        """Should return None for file without lineage metadata."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''"""Example module."""

def example():
    pass
''')

        metadata = parse_lineage_from_file(file_path)

        assert metadata is None, "Expected metadata is None"

    def test_parse_nonexistent_file(self, tmp_path):
        """Should return None for non-existent file."""
        file_path = tmp_path / "does_not_exist.py"

        metadata = parse_lineage_from_file(file_path)

        assert metadata is None, "Expected metadata is None"

    def test_parse_missing_required_fields(self, tmp_path):
        """Should return None if required fields are missing."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''# @spec_id: core-v1
# @component_id: core-example
# Missing: generated_at, generator, spec_file

def example():
    pass
''')

        metadata = parse_lineage_from_file(file_path)

        assert metadata is None, "Expected metadata is None"

    def test_parse_invalid_datetime(self, tmp_path):
        """Should handle invalid datetime gracefully."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''# @generated: not-a-valid-datetime
# @generator: manual
# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-example

def example():
    pass
''')

        metadata = parse_lineage_from_file(file_path)

        assert metadata is not None, "Expected metadata is not None"
        # Should use fallback datetime
        assert metadata.generated_at is not None, "Expected metadata.generated_at is not None"


class TestGenerateLineageHeader:
    """Tests for generate_lineage_header function."""

    def test_generate_with_required_params(self):
        """Should generate header with required parameters."""
        header = generate_lineage_header(
            generator="tdflow.red.v1",
            spec_file=".agentforge/specs/core-v1.yaml",
            spec_id="core-v1",
            component_id="core-example",
        )

        assert "@generator: tdflow.red.v1" in header, "Expected '@generator: tdflow.red.v1' in header"
        assert "@spec_file: .agentforge/specs/core-v1.yaml" in header, "Expected '@spec_file: .agentforge/sp... in header"
        assert "@spec_id: core-v1" in header, "Expected '@spec_id: core-v1' in header"
        assert "@component_id: core-example" in header, "Expected '@component_id: core-example' in header"
        assert "@generated:" in header, "Expected '@generated:' in header"

    def test_generate_with_all_params(self):
        """Should generate header with all parameters."""
        header = generate_lineage_header(
            generator="tdflow.green.v1",
            spec_file=".agentforge/specs/core-v1.yaml",
            spec_id="core-v1",
            component_id="core-example",
            method_ids=["method_a", "method_b"],
            test_path="tests/unit/test_example.py",
            session_id="sess-123",
        )

        assert "@method_ids: method_a,method_b" in header, "Expected '@method_ids: method_a,meth... in header"
        assert "@test_path: tests/unit/test_example.py" in header, "Expected '@test_path: tests/unit/tes... in header"
        assert "@session_id: sess-123" in header, "Expected '@session_id: sess-123' in header"

    def test_generate_with_different_prefix(self):
        """Should use specified comment prefix."""
        header = generate_lineage_header(
            generator="tdflow.red.v1",
            spec_file=".agentforge/specs/core-v1.yaml",
            spec_id="core-v1",
            component_id="core-example",
            comment_prefix="//",
        )

        assert "// @generator:" in header, "Expected '// @generator:' in header"
        assert "// ═" in header, "Expected '// ═' in header"


class TestGetTestPathFromLineage:
    """Tests for get_test_path_from_lineage function."""

    def test_get_test_path_when_present(self, tmp_path):
        """Should return test_path when present in lineage."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''# @generated: 2026-01-02T12:00:00
# @generator: tdflow.green.v1
# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-example
# @test_path: tests/unit/test_example.py

def example():
    pass
''')

        test_path = get_test_path_from_lineage(file_path)

        assert test_path == "tests/unit/test_example.py", "Expected test_path to equal 'tests/unit/test_example.py'"

    def test_get_test_path_when_absent(self, tmp_path):
        """Should return None when test_path not in lineage."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''# @generated: 2026-01-02T12:00:00
# @generator: tdflow.green.v1
# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-example

def example():
    pass
''')

        test_path = get_test_path_from_lineage(file_path)

        assert test_path is None, "Expected test_path is None"

    def test_get_test_path_no_lineage(self, tmp_path):
        """Should return None when file has no lineage."""
        file_path = tmp_path / "example.py"
        file_path.write_text('''def example():
    pass
''')

        test_path = get_test_path_from_lineage(file_path)

        assert test_path is None, "Expected test_path is None"

    def test_get_test_path_nonexistent_file(self, tmp_path):
        """Should return None for non-existent file."""
        file_path = tmp_path / "does_not_exist.py"

        test_path = get_test_path_from_lineage(file_path)

        assert test_path is None, "Expected test_path is None"
