"""Tests for ContextAssembler class."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'tools'))

from context_assembler import ContextAssembler, CodeContext, FileContext
from context_assembler_types import SymbolInfo, PatternMatch, ArchitectureLayer


class TestContextAssemblerInit:
    """Tests for ContextAssembler initialization."""

    def test_init_with_project_path(self, tmp_path: Path):
        """Test initialization with project path."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.project_path == tmp_path.resolve()

    def test_init_with_default_config(self, tmp_path: Path):
        """Test initialization with default config."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.default_budget == 6000
        assert assembler.max_budget == 12000

    def test_init_with_custom_config(self, tmp_path: Path):
        """Test initialization with custom config."""
        config = {
            "retrieval": {
                "budget": {
                    "default_tokens": 8000,
                    "max_tokens": 16000
                }
            }
        }

        assembler = ContextAssembler(str(tmp_path), config=config)

        assert assembler.default_budget == 8000
        assert assembler.max_budget == 16000


class TestLayerDetection:
    """Tests for architectural layer detection."""

    def test_detect_domain_layer(self, tmp_path: Path):
        """Test detection of Domain layer."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_layer("src/Domain/Order.cs") == "Domain"
        assert assembler.detect_layer("src/Entities/User.cs") == "Domain"
        assert assembler.detect_layer("src/Core/Product.cs") == "Domain"

    def test_detect_application_layer(self, tmp_path: Path):
        """Test detection of Application layer."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_layer("src/Application/OrderService.cs") == "Application"
        assert assembler.detect_layer("src/UseCases/CreateOrder.cs") == "Application"
        assert assembler.detect_layer("src/Handlers/OrderHandler.cs") == "Application"

    def test_detect_infrastructure_layer(self, tmp_path: Path):
        """Test detection of Infrastructure layer."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_layer("src/Infrastructure/Database.cs") == "Infrastructure"
        assert assembler.detect_layer("src/Persistence/OrderRepository.cs") == "Infrastructure"
        assert assembler.detect_layer("src/Repositories/UserRepository.cs") == "Infrastructure"

    def test_detect_presentation_layer(self, tmp_path: Path):
        """Test detection of Presentation layer."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_layer("src/Api/OrderController.cs") == "Presentation"
        assert assembler.detect_layer("src/Controllers/UserController.cs") == "Presentation"
        assert assembler.detect_layer("src/Web/Index.cs") == "Presentation"

    def test_detect_unknown_layer(self, tmp_path: Path):
        """Test Unknown layer for unrecognized paths."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_layer("src/Utils/Helper.cs") == "Unknown"
        assert assembler.detect_layer("lib/external.cs") == "Unknown"

    def test_detect_layer_with_absolute_path(self, tmp_path: Path):
        """Test layer detection with absolute paths."""
        assembler = ContextAssembler(str(tmp_path))

        absolute_path = str(tmp_path / "src" / "Domain" / "Order.cs")
        assert assembler.detect_layer(absolute_path) == "Domain"

    def test_custom_layer_patterns(self, tmp_path: Path):
        """Test custom layer patterns from config."""
        config = {
            "layer_detection": {
                "patterns": {
                    "Domain": ["**/Aggregates/**", "**/DomainModels/**"],
                    "CustomLayer": ["**/Custom/**"]
                }
            }
        }

        assembler = ContextAssembler(str(tmp_path), config=config)

        assert assembler.detect_layer("src/Aggregates/Order.cs") == "Domain"
        assert assembler.detect_layer("src/Custom/Thing.cs") == "CustomLayer"


class TestLanguageDetection:
    """Tests for programming language detection."""

    def test_detect_csharp(self, tmp_path: Path):
        """Test C# detection."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_language("file.cs") == "csharp"

    def test_detect_python(self, tmp_path: Path):
        """Test Python detection."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_language("file.py") == "python"

    def test_detect_typescript(self, tmp_path: Path):
        """Test TypeScript detection."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_language("file.ts") == "typescript"
        assert assembler.detect_language("file.tsx") == "typescript"

    def test_detect_javascript(self, tmp_path: Path):
        """Test JavaScript detection."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_language("file.js") == "javascript"
        assert assembler.detect_language("file.jsx") == "javascript"

    def test_detect_go(self, tmp_path: Path):
        """Test Go detection."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_language("file.go") == "go"

    def test_detect_rust(self, tmp_path: Path):
        """Test Rust detection."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_language("file.rs") == "rust"

    def test_detect_unknown_extension(self, tmp_path: Path):
        """Test unknown extension defaults to text."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.detect_language("file.xyz") == "text"
        assert assembler.detect_language("file") == "text"


class TestTokenEstimation:
    """Tests for token estimation."""

    def test_estimate_tokens_short_text(self, tmp_path: Path):
        """Test token estimation for short text."""
        assembler = ContextAssembler(str(tmp_path))

        # ~4 chars per token
        assert assembler.estimate_tokens("hello") == 1
        assert assembler.estimate_tokens("hello world") == 2

    def test_estimate_tokens_code(self, tmp_path: Path):
        """Test token estimation for code."""
        assembler = ContextAssembler(str(tmp_path))

        code = """
def hello():
    print("Hello, World!")
"""
        tokens = assembler.estimate_tokens(code)
        assert tokens > 0
        assert tokens == len(code) // 4

    def test_estimate_tokens_empty_string(self, tmp_path: Path):
        """Test token estimation for empty string."""
        assembler = ContextAssembler(str(tmp_path))

        assert assembler.estimate_tokens("") == 0


class TestCodeContext:
    """Tests for CodeContext data class."""

    def test_code_context_creation(self):
        """Test CodeContext creation with required fields."""
        context = CodeContext(
            files=[],
            symbols=[],
            patterns=[],
            total_tokens=0,
            retrieval_metadata={}
        )

        assert context.files == []
        assert context.symbols == []
        assert context.patterns == []
        assert context.total_tokens == 0

    def test_code_context_with_files(self, tmp_path: Path):
        """Test CodeContext with file contexts."""
        file_ctx = FileContext(
            path="test.py",
            language="python",
            layer="Unknown",
            content="# test",
            token_count=1
        )

        context = CodeContext(
            files=[file_ctx],
            symbols=[],
            patterns=[],
            total_tokens=1,
            retrieval_metadata={}
        )

        assert len(context.files) == 1
        assert context.files[0].path == "test.py"


class TestFileContext:
    """Tests for FileContext data class."""

    def test_file_context_creation(self):
        """Test FileContext creation."""
        ctx = FileContext(
            path="src/domain/order.py",
            language="python",
            layer="Domain",
            content="class Order:\n    pass",
            token_count=5
        )

        assert ctx.path == "src/domain/order.py"
        assert ctx.language == "python"
        assert ctx.layer == "Domain"
        assert ctx.token_count == 5


class TestSymbolInfo:
    """Tests for SymbolInfo data class."""

    def test_symbol_info_creation(self):
        """Test SymbolInfo creation."""
        symbol = SymbolInfo(
            name="OrderService",
            kind="class",
            file_path="src/application/order_service.py",
            line=10,
            signature="class OrderService:"
        )

        assert symbol.name == "OrderService"
        assert symbol.kind == "class"
        assert symbol.line == 10


class TestPatternMatch:
    """Tests for PatternMatch data class."""

    def test_pattern_match_creation(self):
        """Test PatternMatch creation."""
        match = PatternMatch(
            name="command_handler",
            description="Command Handler Pattern",
            examples=["src/handlers/order_handler.py"],
            confidence=0.9
        )

        assert match.name == "command_handler"
        assert match.description == "Command Handler Pattern"


class TestArchitectureLayer:
    """Tests for ArchitectureLayer enum."""

    def test_layer_values(self):
        """Test ArchitectureLayer has expected values."""
        assert ArchitectureLayer.DOMAIN.value == "Domain"
        assert ArchitectureLayer.APPLICATION.value == "Application"
        assert ArchitectureLayer.INFRASTRUCTURE.value == "Infrastructure"
        assert ArchitectureLayer.PRESENTATION.value == "Presentation"
        assert ArchitectureLayer.UNKNOWN.value == "Unknown"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_config(self, tmp_path: Path):
        """Test assembler with empty config."""
        assembler = ContextAssembler(str(tmp_path), config={})

        assert assembler.default_budget == 6000  # Uses built-in default
        assert assembler.max_budget == 12000

    def test_file_path_with_special_characters(self, tmp_path: Path):
        """Test file path with special characters."""
        assembler = ContextAssembler(str(tmp_path))

        # Should not raise
        layer = assembler.detect_layer("src/Domain/file with spaces.cs")
        assert layer is not None

    def test_unicode_content_token_estimation(self, tmp_path: Path):
        """Test token estimation with unicode content."""
        assembler = ContextAssembler(str(tmp_path))

        # Unicode characters still counted by length
        tokens = assembler.estimate_tokens("你好世界")
        assert tokens >= 0


class TestAssemblyMethods:
    """Tests for core assembly functionality."""

    def test_assemble_empty_results(self, tmp_path: Path):
        """Test assemble with no results."""
        assembler = ContextAssembler(str(tmp_path))
        context = assembler.assemble("test query")

        assert context.files == []
        assert context.symbols == []
        assert context.total_tokens == 0
        assert "query" in context.retrieval_metadata

    def test_assemble_with_budget(self, tmp_path: Path):
        """Test assemble respects token budget."""
        assembler = ContextAssembler(str(tmp_path))
        context = assembler.assemble("test query", budget_tokens=1000)

        assert context.retrieval_metadata["budget_tokens"] == 1000

    def test_assemble_with_max_budget_cap(self, tmp_path: Path):
        """Test assemble caps budget at max_budget."""
        assembler = ContextAssembler(str(tmp_path))
        context = assembler.assemble("test query", budget_tokens=100000)

        # Should be capped at max_budget (12000)
        assert context.retrieval_metadata["budget_tokens"] == 12000

    def test_assemble_from_files_reads_content(self, tmp_path: Path):
        """Test assemble_from_files reads actual file content."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    return 'world'")

        assembler = ContextAssembler(str(tmp_path))
        context = assembler.assemble_from_files(["test.py"])

        assert len(context.files) == 1
        assert "def hello" in context.files[0].content
        assert context.files[0].language == "python"

    def test_assemble_from_files_missing_file(self, tmp_path: Path):
        """Test assemble_from_files handles missing files."""
        assembler = ContextAssembler(str(tmp_path))
        context = assembler.assemble_from_files(["nonexistent.py"])

        assert len(context.files) == 0

    def test_assemble_from_files_respects_budget(self, tmp_path: Path):
        """Test assemble_from_files truncates to budget."""
        # Create a large file
        large_content = "x" * 10000
        test_file = tmp_path / "large.py"
        test_file.write_text(large_content)

        assembler = ContextAssembler(str(tmp_path))
        # Budget of 500 tokens (~2000 chars) should truncate 10000 char file
        context = assembler.assemble_from_files(["large.py"], budget_tokens=500)

        # Content should be truncated
        assert len(context.files) == 1
        assert len(context.files[0].content) < len(large_content)

    def test_truncate_content_preserves_newlines(self, tmp_path: Path):
        """Test content truncation tries to preserve line boundaries."""
        assembler = ContextAssembler(str(tmp_path))
        content = "line1\nline2\nline3\nline4\nline5\n" * 100

        truncated = assembler._truncate_content(content, 50)

        assert "truncated" in truncated.lower()


class TestProcessingMethods:
    """Tests for internal processing methods."""

    def test_process_vector_results_empty(self, tmp_path: Path):
        """Test processing empty vector results."""
        assembler = ContextAssembler(str(tmp_path))
        file_data = {}

        assembler._process_vector_results(None, file_data)
        assert file_data == {}

        assembler._process_vector_results([], file_data)
        assert file_data == {}

    def test_process_vector_results_adds_to_file_data(self, tmp_path: Path):
        """Test processing vector results populates file_data."""
        assembler = ContextAssembler(str(tmp_path))
        file_data = {}

        # Mock vector result
        mock_result = Mock()
        mock_result.file_path = "src/test.py"
        mock_result.score = 0.95
        mock_result.chunk = "def test_function(): pass"

        assembler._process_vector_results([mock_result], file_data)

        assert "src/test.py" in file_data
        assert file_data["src/test.py"]["score"] == 0.95
        assert "def test_function" in file_data["src/test.py"]["content"]

    def test_process_lsp_symbols_empty(self, tmp_path: Path):
        """Test processing empty LSP symbols."""
        assembler = ContextAssembler(str(tmp_path))
        file_data = {}

        assembler._process_lsp_symbols(None, "query", file_data)
        assert file_data == {}

        assembler._process_lsp_symbols([], "query", file_data)
        assert file_data == {}

    def test_process_lsp_symbols_adds_symbols(self, tmp_path: Path):
        """Test processing LSP symbols adds to file_data."""
        assembler = ContextAssembler(str(tmp_path))
        file_data = {}

        # Mock symbol
        mock_location = Mock()
        mock_location.file = "src/service.py"
        mock_location.line = 10

        mock_symbol = Mock()
        mock_symbol.name = "OrderService"
        mock_symbol.kind = "class"
        mock_symbol.location = mock_location

        assembler._process_lsp_symbols([mock_symbol], "order", file_data)

        assert "src/service.py" in file_data
        assert len(file_data["src/service.py"]["symbols"]) == 1

    def test_apply_entry_point_boosts_empty(self, tmp_path: Path):
        """Test entry point boosts with empty inputs."""
        assembler = ContextAssembler(str(tmp_path))
        file_data = {"test.py": {"score": 0.5}}

        assembler._apply_entry_point_boosts(None, file_data)
        assert file_data["test.py"]["score"] == 0.5

        assembler._apply_entry_point_boosts([], file_data)
        assert file_data["test.py"]["score"] == 0.5

    def test_apply_entry_point_boosts_increases_score(self, tmp_path: Path):
        """Test entry point boosts increase matching file scores."""
        assembler = ContextAssembler(str(tmp_path))
        file_data = {
            "order_service.py": {"score": 0.5},
            "user_service.py": {"score": 0.5}
        }

        assembler._apply_entry_point_boosts(["order"], file_data)

        assert file_data["order_service.py"]["score"] == 1.5  # boosted
        assert file_data["user_service.py"]["score"] == 0.5  # not boosted

    def test_get_file_content_cached(self, tmp_path: Path):
        """Test get_file_content returns cached content."""
        assembler = ContextAssembler(str(tmp_path))

        result = assembler._get_file_content("test.py", "cached content")
        assert result == "cached content"

    def test_get_file_content_from_disk(self, tmp_path: Path):
        """Test get_file_content reads from disk when not cached."""
        test_file = tmp_path / "test.py"
        test_file.write_text("file content from disk")

        assembler = ContextAssembler(str(tmp_path))
        result = assembler._get_file_content("test.py", "")

        assert result == "file content from disk"

    def test_get_file_content_missing_file(self, tmp_path: Path):
        """Test get_file_content returns empty for missing file."""
        assembler = ContextAssembler(str(tmp_path))
        result = assembler._get_file_content("nonexistent.py", "")

        assert result == ""

    def test_fit_content_to_budget_fits(self, tmp_path: Path):
        """Test fit_content_to_budget when content fits."""
        assembler = ContextAssembler(str(tmp_path))
        content = "short content"

        result_content, result_tokens = assembler._fit_content_to_budget(
            content, current_tokens=0, budget=1000
        )

        assert result_content == content
        assert result_tokens == assembler.estimate_tokens(content)

    def test_fit_content_to_budget_truncates(self, tmp_path: Path):
        """Test fit_content_to_budget truncates when over budget."""
        assembler = ContextAssembler(str(tmp_path))
        content = "x" * 10000  # Large content

        result_content, result_tokens = assembler._fit_content_to_budget(
            content, current_tokens=0, budget=500
        )

        assert len(result_content) < len(content)
        assert result_tokens == 500

    def test_fit_content_to_budget_returns_none_when_no_room(self, tmp_path: Path):
        """Test fit_content_to_budget returns None when insufficient room (<200 tokens)."""
        assembler = ContextAssembler(str(tmp_path))

        # When remaining budget < 200 tokens, skip the file
        result_content, result_tokens = assembler._fit_content_to_budget(
            "x" * 1000,  # Large content
            current_tokens=900,  # Only 100 tokens remaining (< 200 threshold)
            budget=1000
        )

        assert result_content is None
        assert result_tokens == 0


class TestCodeContextMethods:
    """Tests for CodeContext output methods."""

    def test_code_context_to_dict(self, tmp_path: Path):
        """Test CodeContext.to_dict output format."""
        file_ctx = FileContext(
            path="test.py",
            language="python",
            content="# test",
            layer="Domain"
        )
        context = CodeContext(
            files=[file_ctx],
            total_tokens=100
        )

        result = context.to_dict()

        assert "summary" in result
        assert result["summary"]["total_files"] == 1
        assert result["summary"]["total_tokens"] == 100
        assert "files" in result

    def test_code_context_to_prompt_text(self, tmp_path: Path):
        """Test CodeContext.to_prompt_text formatting."""
        file_ctx = FileContext(
            path="test.py",
            language="python",
            content="def test(): pass",
            layer="Domain"
        )
        context = CodeContext(
            files=[file_ctx],
            total_tokens=10
        )

        result = context.to_prompt_text()

        assert "# Code Context" in result
        assert "Domain Layer" in result
        assert "```python" in result
        assert "def test(): pass" in result

    def test_code_context_groups_files_by_layer(self, tmp_path: Path):
        """Test files are grouped by architectural layer in prompt."""
        files = [
            FileContext(path="domain.py", language="python", content="a", layer="Domain"),
            FileContext(path="infra.py", language="python", content="b", layer="Infrastructure"),
            FileContext(path="app.py", language="python", content="c", layer="Application"),
        ]
        context = CodeContext(files=files, total_tokens=30)

        result = context.to_prompt_text()

        # Check layers appear in order
        domain_pos = result.find("Domain Layer")
        app_pos = result.find("Application Layer")
        infra_pos = result.find("Infrastructure Layer")

        assert domain_pos < app_pos < infra_pos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
