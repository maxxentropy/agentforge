# @spec_file: .agentforge/specs/cli-commands-v1.yaml
# @spec_id: cli-commands-v1
# @component_id: cli-commands-context
# @impl_path: src/agentforge/cli/commands/context.py

"""Tests for ContextRetriever class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from agentforge.core.context_assembler import CodeContext, FileContext
from agentforge.core.context_retrieval import ContextRetriever, IndexStats


class TestContextRetrieverInit:
    """Tests for ContextRetriever initialization."""

    def test_init_with_project_path(self, tmp_path: Path):
        """Test initialization with project path."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        assert retriever.project_path == tmp_path.resolve(), "Expected retriever.project_path to equal tmp_path.resolve()"
        assert retriever.config is not None, "Expected retriever.config is not None"

    def test_init_loads_default_config(self, tmp_path: Path):
        """Test initialization loads default config when none exists."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        assert "retrieval" in retriever.config, "Expected 'retrieval' in retriever.config"
        assert "filters" in retriever.config, "Expected 'filters' in retriever.config"

    def test_init_loads_custom_config(self, tmp_path: Path):
        """Test initialization loads custom config file."""
        config_dir = tmp_path / ".agentforge"
        config_dir.mkdir()
        config_file = config_dir / "context_retrieval.yaml"
        config_file.write_text("""
retrieval:
  budget:
    default_tokens: 8000
    max_tokens: 16000
""")

        retriever = ContextRetriever(project_path=str(tmp_path))

        assert retriever.config["retrieval"]["budget"]["default_tokens"] == 8000, "Expected retriever.config['retrieval... to equal 8000"

    def test_init_with_explicit_config_path(self, tmp_path: Path):
        """Test initialization with explicit config path."""
        config_file = tmp_path / "my_config.yaml"
        config_file.write_text("""
retrieval:
  budget:
    default_tokens: 5000
""")

        retriever = ContextRetriever(
            project_path=str(tmp_path),
            config_path=str(config_file)
        )

        assert retriever.config["retrieval"]["budget"]["default_tokens"] == 5000, "Expected retriever.config['retrieval... to equal 5000"

    def test_lazy_load_assembler(self, tmp_path: Path):
        """Test assembler is lazily loaded."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        assert retriever._assembler is None, "Expected retriever._assembler is None"
        assembler = retriever.assembler
        assert assembler is not None, "Expected assembler is not None"
        assert retriever.assembler is assembler, "Expected retriever.assembler is assembler"# Same instance


class TestContextRetrieverLSP:
    """Tests for LSP-related functionality."""

    def test_lsp_adapter_lazy_load(self, tmp_path: Path):
        """Test LSP adapter is lazily loaded."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        assert retriever._lsp_adapter is None, "Expected retriever._lsp_adapter is None"
        assert retriever._lsp_available is None, "Expected retriever._lsp_available is None"

    def test_lsp_adapter_not_available(self, tmp_path: Path):
        """Test graceful degradation when LSP not available."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        with patch('agentforge.core.context_retrieval.ContextRetriever.lsp_adapter', new=None):
            retriever._lsp_available = False
            symbols = retriever._retrieve_lsp_symbols("test query")

        assert symbols == [], "Expected symbols to equal []"

    def test_lsp_adapter_import_error(self, tmp_path: Path):
        """Test graceful handling of LSP import errors."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        # Force the lazy load to fail
        retriever._lsp_available = False
        adapter = retriever.lsp_adapter

        assert adapter is None, "Expected adapter is None"


class TestContextRetrieverVectorSearch:
    """Tests for vector search functionality."""

    def test_vector_search_lazy_load(self, tmp_path: Path):
        """Test vector search is lazily loaded."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        assert retriever._vector_search is None, "Expected retriever._vector_search is None"
        assert retriever._vector_available is None, "Expected retriever._vector_available is None"

    def test_vector_search_not_available(self, tmp_path: Path):
        """Test graceful degradation when vector search not available."""
        retriever = ContextRetriever(project_path=str(tmp_path))
        retriever._vector_available = False

        results = retriever._retrieve_vector_results("test query")

        assert results == [], "Expected results to equal []"


class TestContextRetrieverRetrieve:
    """Tests for the main retrieve method."""

    def test_retrieve_returns_code_context(self, tmp_path: Path):
        """Test retrieve returns CodeContext object."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        # Mock the components
        mock_context = CodeContext(
            files=[], symbols=[], patterns=[],
            total_tokens=0, retrieval_metadata={}
        )

        with patch.object(retriever, '_retrieve_lsp_symbols', return_value=[]):
            with patch.object(retriever, '_retrieve_vector_results', return_value=[]):
                with patch.object(retriever.assembler, 'assemble', return_value=mock_context):
                    context = retriever.retrieve("test query")

        assert isinstance(context, CodeContext), "Expected isinstance() to be truthy"

    def test_retrieve_uses_default_budget(self, tmp_path: Path):
        """Test retrieve uses default token budget from config."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_context = CodeContext(
            files=[], symbols=[], patterns=[],
            total_tokens=0, retrieval_metadata={}
        )

        with patch.object(retriever, '_retrieve_lsp_symbols', return_value=[]):
            with patch.object(retriever, '_retrieve_vector_results', return_value=[]):
                with patch.object(retriever.assembler, 'assemble', return_value=mock_context) as mock_assemble:
                    retriever.retrieve("test query")

        # Check budget was passed to assemble
        call_kwargs = mock_assemble.call_args[1]
        assert call_kwargs["budget_tokens"] == 6000, "Expected call_kwargs['budget_tokens'] to equal 6000"# Default

    def test_retrieve_with_custom_budget(self, tmp_path: Path):
        """Test retrieve with custom token budget."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_context = CodeContext(
            files=[], symbols=[], patterns=[],
            total_tokens=0, retrieval_metadata={}
        )

        with patch.object(retriever, '_retrieve_lsp_symbols', return_value=[]):
            with patch.object(retriever, '_retrieve_vector_results', return_value=[]):
                with patch.object(retriever.assembler, 'assemble', return_value=mock_context) as mock_assemble:
                    retriever.retrieve("test query", budget_tokens=4000)

        call_kwargs = mock_assemble.call_args[1]
        assert call_kwargs["budget_tokens"] == 4000, "Expected call_kwargs['budget_tokens'] to equal 4000"

    def test_retrieve_with_entry_points(self, tmp_path: Path):
        """Test retrieve with entry points."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_context = CodeContext(
            files=[], symbols=[], patterns=[],
            total_tokens=0, retrieval_metadata={}
        )

        with patch.object(retriever, '_retrieve_lsp_symbols', return_value=[]) as mock_lsp:
            with patch.object(retriever, '_retrieve_vector_results', return_value=[]):
                with patch.object(retriever.assembler, 'assemble', return_value=mock_context):
                    retriever.retrieve("test query", entry_points=["OrderService"])

        mock_lsp.assert_called_once_with("test query", ["OrderService"])

    def test_retrieve_without_lsp(self, tmp_path: Path):
        """Test retrieve with LSP disabled."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_context = CodeContext(
            files=[], symbols=[], patterns=[],
            total_tokens=0, retrieval_metadata={}
        )

        with patch.object(retriever, '_retrieve_lsp_symbols') as mock_lsp:
            with patch.object(retriever, '_retrieve_vector_results', return_value=[]):
                with patch.object(retriever.assembler, 'assemble', return_value=mock_context):
                    retriever.retrieve("test query", use_lsp=False)

        mock_lsp.assert_not_called()

    def test_retrieve_without_vector(self, tmp_path: Path):
        """Test retrieve with vector search disabled."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_context = CodeContext(
            files=[], symbols=[], patterns=[],
            total_tokens=0, retrieval_metadata={}
        )

        with patch.object(retriever, '_retrieve_lsp_symbols', return_value=[]):
            with patch.object(retriever, '_retrieve_vector_results') as mock_vector:
                with patch.object(retriever.assembler, 'assemble', return_value=mock_context):
                    retriever.retrieve("test query", use_vector=False)

        mock_vector.assert_not_called()

    def test_retrieve_sets_metadata(self, tmp_path: Path):
        """Test retrieve sets retrieval metadata."""
        retriever = ContextRetriever(project_path=str(tmp_path))
        retriever._lsp_available = True
        retriever._vector_available = True

        mock_context = CodeContext(
            files=[], symbols=[], patterns=[],
            total_tokens=0, retrieval_metadata={}
        )

        with patch.object(retriever, '_retrieve_lsp_symbols', return_value=[]):
            with patch.object(retriever, '_retrieve_vector_results', return_value=[]):
                with patch.object(retriever.assembler, 'assemble', return_value=mock_context):
                    context = retriever.retrieve("test query")

        assert "project_path" in context.retrieval_metadata, "Expected 'project_path' in context.retrieval_metadata"
        assert context.retrieval_metadata["lsp_enabled"], "Assertion failed"
        assert context.retrieval_metadata["vector_enabled"], "Assertion failed"


class TestKeywordExtraction:
    """Tests for keyword extraction from queries."""

    def test_extract_keywords_basic(self, tmp_path: Path):
        """Test basic keyword extraction."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        keywords = retriever._extract_keywords("order discount processing")

        assert "order" in keywords, "Expected 'order' in keywords"
        assert "discount" in keywords, "Expected 'discount' in keywords"
        assert "processing" in keywords, "Expected 'processing' in keywords"

    def test_extract_keywords_filters_stopwords(self, tmp_path: Path):
        """Test stopwords are filtered out."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        keywords = retriever._extract_keywords("the order is processing")

        assert "the" not in keywords, "Expected 'the' not in keywords"
        assert "is" not in keywords, "Expected 'is' not in keywords"
        assert "order" in keywords, "Expected 'order' in keywords"
        assert "processing" in keywords, "Expected 'processing' in keywords"

    def test_extract_keywords_filters_short_words(self, tmp_path: Path):
        """Test short words (<=2 chars) are filtered."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        keywords = retriever._extract_keywords("a to be or")

        assert len(keywords) == 0, "Expected len(keywords) to equal 0"

    def test_extract_keywords_handles_camelcase(self, tmp_path: Path):
        """Test camelCase identifiers are handled."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        keywords = retriever._extract_keywords("OrderService DiscountCalculator")

        assert "OrderService" in keywords, "Expected 'OrderService' in keywords"
        assert "DiscountCalculator" in keywords, "Expected 'DiscountCalculator' in keywords"

    def test_extract_keywords_deduplicates(self, tmp_path: Path):
        """Test duplicate keywords are removed."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        keywords = retriever._extract_keywords("order Order ORDER")

        assert len([k for k in keywords if k.lower() == "order"]) == 1, "Expected len([k for k in keywords if... to equal 1"


class TestSymbolContext:
    """Tests for get_symbol_context method."""

    def test_get_symbol_context_no_lsp(self, tmp_path: Path):
        """Test get_symbol_context returns None when LSP unavailable."""
        retriever = ContextRetriever(project_path=str(tmp_path))
        retriever._lsp_available = False

        result = retriever.get_symbol_context("OrderService")

        assert result is None, "Expected result is None"

    def test_get_symbol_context_symbol_not_found(self, tmp_path: Path):
        """Test get_symbol_context returns None when symbol not found."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_adapter = Mock()
        mock_adapter.get_workspace_symbols.return_value = []
        retriever._lsp_adapter = mock_adapter
        retriever._lsp_available = True

        result = retriever.get_symbol_context("NonexistentSymbol")

        assert result is None, "Expected result is None"


class TestFileContext:
    """Tests for get_file_context method."""

    def test_get_file_context_none_path(self, tmp_path: Path):
        """Test get_file_context with None path."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        result = retriever.get_file_context(None)

        assert result is None, "Expected result is None"

    def test_get_file_context_returns_file_context(self, tmp_path: Path):
        """Test get_file_context returns FileContext."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# Test file")

        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_file_context = FileContext(
            path=str(test_file),
            language="python",
            layer="Unknown",
            content="# Test file",
            token_count=3
        )
        mock_code_context = CodeContext(
            files=[mock_file_context], symbols=[], patterns=[],
            total_tokens=3, retrieval_metadata={}
        )

        with patch.object(retriever.assembler, 'assemble_from_files', return_value=mock_code_context):
            result = retriever.get_file_context(str(test_file))

        assert result is not None, "Expected result is not None"


class TestIndexing:
    """Tests for indexing functionality."""

    def test_index_returns_stats(self, tmp_path: Path):
        """Test index returns IndexStats."""
        retriever = ContextRetriever(project_path=str(tmp_path))
        retriever._vector_available = False

        stats = retriever.index()

        assert isinstance(stats, IndexStats), "Expected isinstance() to be truthy"

    def test_index_without_vector_search(self, tmp_path: Path):
        """Test index works when vector search unavailable."""
        retriever = ContextRetriever(project_path=str(tmp_path))
        retriever._vector_available = False

        stats = retriever.index()

        assert stats.file_count == 0, "Expected stats.file_count to equal 0"
        assert len(stats.errors) == 0, "Expected len(stats.errors) to equal 0"

    def test_index_stats_fields(self, tmp_path: Path):
        """Test IndexStats has expected fields."""
        stats = IndexStats()

        assert stats.file_count == 0, "Expected stats.file_count to equal 0"
        assert stats.chunk_count == 0, "Expected stats.chunk_count to equal 0"
        assert stats.symbol_count == 0, "Expected stats.symbol_count to equal 0"
        assert stats.duration_ms == 0, "Expected stats.duration_ms to equal 0"
        assert stats.errors == [], "Expected stats.errors to equal []"


class TestCheckDependencies:
    """Tests for dependency checking."""

    def test_check_dependencies_returns_status(self, tmp_path: Path):
        """Test check_dependencies returns status dict."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        with patch.dict('sys.modules', {'tools.lsp_adapter': None}):
            status = retriever.check_dependencies()

        assert "lsp" in status, "Expected 'lsp' in status"
        assert "vector" in status, "Expected 'vector' in status"
        assert "available" in status["lsp"], "Expected 'available' in status['lsp']"
        assert "available" in status["vector"], "Expected 'available' in status['vector']"


class TestShutdown:
    """Tests for shutdown and cleanup."""

    def test_shutdown_closes_lsp(self, tmp_path: Path):
        """Test shutdown closes LSP adapter."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_adapter = Mock()
        retriever._lsp_adapter = mock_adapter

        retriever.shutdown()

        mock_adapter.shutdown.assert_called_once()
        assert retriever._lsp_adapter is None, "Expected retriever._lsp_adapter is None"

    def test_shutdown_handles_exception(self, tmp_path: Path):
        """Test shutdown handles adapter exception gracefully."""
        retriever = ContextRetriever(project_path=str(tmp_path))

        mock_adapter = Mock()
        mock_adapter.shutdown.side_effect = RuntimeError("Shutdown error")
        retriever._lsp_adapter = mock_adapter

        # Should not raise
        retriever.shutdown()

        assert retriever._lsp_adapter is None, "Expected retriever._lsp_adapter is None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
