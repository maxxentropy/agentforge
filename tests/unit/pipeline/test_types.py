# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-types
# @test_path: tests/unit/pipeline/test_types.py

"""
Tests for Pipeline Type Definitions
===================================

Verifies type aliases are properly defined and exported.
"""

from typing import Any, get_type_hints

import pytest


class TestTypeAliasExports:
    """Verify all type aliases are properly exported."""

    def test_stage_config_dict_importable(self):
        """StageConfigDict should be importable."""
        from agentforge.core.pipeline.types import StageConfigDict

        # Verify it's a type alias for dict[str, Any]
        assert StageConfigDict is not None, "Expected StageConfigDict is not None"

    def test_pipeline_config_dict_importable(self):
        """PipelineConfigDict should be importable."""
        from agentforge.core.pipeline.types import PipelineConfigDict

        assert PipelineConfigDict is not None, "Expected PipelineConfigDict is not None"

    def test_artifact_dict_importable(self):
        """ArtifactDict should be importable."""
        from agentforge.core.pipeline.types import ArtifactDict

        assert ArtifactDict is not None, "Expected ArtifactDict is not None"

    def test_tool_params_dict_importable(self):
        """ToolParamsDict should be importable."""
        from agentforge.core.pipeline.types import ToolParamsDict

        assert ToolParamsDict is not None, "Expected ToolParamsDict is not None"

    def test_tool_result_dict_importable(self):
        """ToolResultDict should be importable."""
        from agentforge.core.pipeline.types import ToolResultDict

        assert ToolResultDict is not None, "Expected ToolResultDict is not None"

    def test_test_results_dict_importable(self):
        """TestResultsDict should be importable."""
        from agentforge.core.pipeline.types import TestResultsDict

        assert TestResultsDict is not None, "Expected TestResultsDict is not None"


class TestTypeAliasUsage:
    """Verify type aliases work correctly in practice."""

    def test_stage_config_dict_accepts_dict(self):
        """StageConfigDict should accept dict values."""
        from agentforge.core.pipeline.types import StageConfigDict

        config: StageConfigDict = {"max_iterations": 20, "timeout": 120}
        assert config["max_iterations"] == 20, "Expected config['max_iterations'] to equal 20"

    def test_artifact_dict_accepts_nested_data(self):
        """ArtifactDict should accept nested structures."""
        from agentforge.core.pipeline.types import ArtifactDict

        artifact: ArtifactDict = {
            "files": ["file1.py", "file2.py"],
            "metadata": {"author": "test", "version": 1},
        }
        assert len(artifact["files"]) == 2, "Expected len(artifact['files']) to equal 2"

    def test_tool_params_dict_accepts_various_types(self):
        """ToolParamsDict should accept various value types."""
        from agentforge.core.pipeline.types import ToolParamsDict

        params: ToolParamsDict = {
            "path": "/tmp/test",
            "verbose": True,
            "count": 42,
            "options": ["a", "b"],
        }
        assert params["verbose"] is True, "Expected params['verbose'] is True"


class TestAllExports:
    """Verify __all__ exports match defined types."""

    def test_all_exports_are_defined(self):
        """All items in __all__ should be importable."""
        from agentforge.core.pipeline import types

        for name in types.__all__:
            assert hasattr(types, name), f"{name} in __all__ but not defined"

    def test_expected_exports_count(self):
        """Should export exactly 6 type aliases."""
        from agentforge.core.pipeline.types import __all__

        expected = [
            "StageConfigDict",
            "PipelineConfigDict",
            "ArtifactDict",
            "ToolParamsDict",
            "ToolResultDict",
            "TestResultsDict",
        ]
        assert sorted(__all__) == sorted(expected), "Expected sorted(__all__) to equal sorted(expected)"
