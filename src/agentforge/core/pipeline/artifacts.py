# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_file: specs/pipeline-controller/implementation/phase-3-tdd-stages.yaml
# @spec_file: specs/pipeline-controller/implementation/phase-4-refactor-deliver.yaml
# @spec_id: pipeline-controller-phase2-v1
# @spec_id: pipeline-controller-phase3-v1
# @spec_id: pipeline-controller-phase4-v1
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
from typing import Any, Dict, List, Optional


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
    initial_questions: List[Dict[str, Any]] = field(default_factory=list)
    detected_components: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
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
    answered_questions: List[Dict[str, Any]] = field(default_factory=list)
    remaining_questions: List[Dict[str, Any]] = field(default_factory=list)
    refined_scope: Optional[str] = None
    ready_for_analysis: bool = False


@dataclass
class AnalyzeArtifact:
    """
    Artifact produced by ANALYZE stage.

    Contains codebase analysis results including affected files,
    components, dependencies, and risks.
    """

    request_id: str
    analysis: Dict[str, Any] = field(default_factory=dict)
    affected_files: List[Dict[str, Any]] = field(default_factory=list)
    components: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    risks: List[Dict[str, Any]] = field(default_factory=list)


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
    overview: Dict[str, Any] = field(default_factory=dict)
    components: List[Dict[str, Any]] = field(default_factory=list)
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    data_models: List[Dict[str, Any]] = field(default_factory=list)
    implementation_order: List[Dict[str, Any]] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class RedArtifact:
    """
    Artifact produced by RED (test-first) stage.

    Contains generated test files and initial test results.
    Tests are expected to fail in RED phase (no implementation yet).
    """

    spec_id: str
    request_id: str = ""
    test_files: List[Dict[str, str]] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    failing_tests: List[str] = field(default_factory=list)
    unexpected_passes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class GreenArtifact:
    """
    Artifact produced by GREEN (implementation) stage.

    Contains implementation files and test results showing all pass.
    """

    spec_id: str
    request_id: str = ""
    implementation_files: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    passing_tests: int = 0
    iterations: int = 0
    all_tests_pass: bool = False
    error: Optional[str] = None


@dataclass
class RefactorArtifact:
    """
    Artifact produced by REFACTOR stage.

    Contains refactored files and improvement details.
    Tests must continue to pass after refactoring.
    """

    spec_id: str
    request_id: str = ""
    refactored_files: List[Dict[str, str]] = field(default_factory=list)
    improvements: List[Dict[str, str]] = field(default_factory=list)
    final_files: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    conformance_passed: bool = False
    remaining_violations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DeliverArtifact:
    """
    Artifact produced by DELIVER stage.

    Contains delivery details (commit, PR, files, patch).
    """

    spec_id: str
    request_id: str = ""
    deliverable_type: str = "commit"  # commit, pr, files, patch
    commit_sha: Optional[str] = None
    commit_message: str = ""
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    patch_file: Optional[str] = None
    files_modified: List[str] = field(default_factory=list)
    files_staged: List[str] = field(default_factory=list)
    summary: str = ""
    status: str = ""
