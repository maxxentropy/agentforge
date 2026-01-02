# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @component_id: pipeline-artifacts
# @component_id: tdd-artifacts
# @component_id: phase4-artifacts
# @test_path: tests/unit/pipeline/test_artifacts.py

"""
Pipeline Artifacts
==================

Typed dataclasses for pipeline stage outputs.

Each stage produces a structured artifact that flows to the next stage.
These dataclasses provide:
- Type safety for artifact fields
- Default values for optional fields
- Serialization to/from dict for YAML persistence
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntakeArtifact:
    """
    Artifact produced by INTAKE stage.

    Contains the parsed user request with scope detection,
    priority assessment, and clarifying questions.
    """

    request_id: str
    original_request: str
    detected_scope: str  # bug_fix, feature_addition, refactoring, documentation, testing, unclear
    priority: str  # low, medium, high, critical
    initial_questions: list[dict[str, Any]] = field(default_factory=list)
    detected_components: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    confidence: float = 0.5
    estimated_complexity: str = "medium"


@dataclass
class ClarifyArtifact:
    """
    Artifact produced by CLARIFY stage.

    Contains clarified requirements after Q&A resolution.
    """

    request_id: str
    clarified_requirements: str
    scope_confirmed: bool = False
    answered_questions: list[dict[str, Any]] = field(default_factory=list)
    remaining_questions: list[dict[str, Any]] = field(default_factory=list)
    refined_scope: str | None = None
    ready_for_analysis: bool = False


@dataclass
class AnalyzeArtifact:
    """
    Artifact produced by ANALYZE stage.

    Contains codebase analysis results including affected files,
    components, dependencies, and risks.
    """

    request_id: str
    analysis: dict[str, Any] = field(default_factory=dict)
    affected_files: list[dict[str, Any]] = field(default_factory=list)
    components: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SpecArtifact:
    """
    Artifact produced by SPEC stage.

    Contains the detailed technical specification with components,
    test cases, interfaces, and acceptance criteria.
    """

    spec_id: str
    request_id: str
    title: str = ""
    version: str = "1.0"
    overview: dict[str, Any] = field(default_factory=dict)
    components: list[dict[str, Any]] = field(default_factory=list)
    test_cases: list[dict[str, Any]] = field(default_factory=list)
    interfaces: list[dict[str, Any]] = field(default_factory=list)
    data_models: list[dict[str, Any]] = field(default_factory=list)
    implementation_order: list[dict[str, Any]] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass
class RedArtifact:
    """
    Artifact produced by RED (test-first) stage.

    Contains generated test files and initial test results.
    Tests are expected to fail in RED phase (no implementation yet).
    """

    spec_id: str
    request_id: str = ""
    test_files: list[dict[str, str]] = field(default_factory=list)
    test_results: dict[str, Any] = field(default_factory=dict)
    failing_tests: list[str] = field(default_factory=list)
    unexpected_passes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class GreenArtifact:
    """
    Artifact produced by GREEN (implementation) stage.

    Contains implementation files and test results showing all pass.
    """

    spec_id: str
    request_id: str = ""
    implementation_files: list[str] = field(default_factory=list)
    test_results: dict[str, Any] = field(default_factory=dict)
    passing_tests: int = 0
    iterations: int = 0
    all_tests_pass: bool = False
    error: str | None = None


@dataclass
class RefactorArtifact:
    """
    Artifact produced by REFACTOR stage.

    Contains refactored files and improvement details.
    Tests must continue to pass after refactoring.
    """

    spec_id: str
    request_id: str = ""
    refactored_files: list[dict[str, str]] = field(default_factory=list)
    improvements: list[dict[str, str]] = field(default_factory=list)
    final_files: list[str] = field(default_factory=list)
    test_results: dict[str, Any] = field(default_factory=dict)
    conformance_passed: bool = False
    remaining_violations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DeliverArtifact:
    """
    Artifact produced by DELIVER stage.

    Contains delivery details (commit, PR, files, patch).
    """

    spec_id: str
    request_id: str = ""
    deliverable_type: str = "commit"  # commit, pr, files, patch
    commit_sha: str | None = None
    commit_message: str = ""
    branch_name: str | None = None
    pr_url: str | None = None
    patch_file: str | None = None
    files_modified: list[str] = field(default_factory=list)
    files_staged: list[str] = field(default_factory=list)
    summary: str = ""
    status: str = ""
