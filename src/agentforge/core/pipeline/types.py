# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-types
# @test_path: tests/unit/pipeline/test_types.py

"""
Pipeline Type Definitions
=========================

Common type aliases and protocols for the pipeline module.

These type definitions improve code clarity and enable better
static type checking across the pipeline codebase.
"""

from typing import Any, TypeAlias

# Configuration dictionary types
StageConfigDict: TypeAlias = dict[str, Any]
"""Configuration dictionary for individual stages."""

PipelineConfigDict: TypeAlias = dict[str, Any]
"""Configuration dictionary for entire pipeline."""

ArtifactDict: TypeAlias = dict[str, Any]
"""Artifact data passed between stages."""

ToolParamsDict: TypeAlias = dict[str, Any]
"""Parameters passed to tool handlers."""

# Result types
ToolResultDict: TypeAlias = dict[str, Any]
"""Result from tool execution."""

TestResultsDict: TypeAlias = dict[str, Any]
"""Test execution results."""

__all__ = [
    "StageConfigDict",
    "PipelineConfigDict",
    "ArtifactDict",
    "ToolParamsDict",
    "ToolResultDict",
    "TestResultsDict",
]
