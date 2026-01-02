# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_file: specs/pipeline-controller/implementation/phase-3-tdd-stages.yaml
# @spec_id: pipeline-controller-phase2-v1
# @spec_id: pipeline-controller-phase3-v1
# @component_id: pipeline-artifacts
# @component_id: tdd-artifacts
# @test_path: tests/unit/pipeline/test_artifacts.py

"""Tests for artifact dataclasses."""

from dataclasses import asdict

import pytest


class TestIntakeArtifact:
    """Tests for IntakeArtifact dataclass."""

    def test_intake_artifact_creation(self):
        """IntakeArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import IntakeArtifact

        artifact = IntakeArtifact(
            request_id="REQ-001",
            original_request="Add a login button",
            detected_scope="feature_addition",
            priority="medium",
        )

        assert artifact.request_id == "REQ-001"
        assert artifact.original_request == "Add a login button"
        assert artifact.detected_scope == "feature_addition"
        assert artifact.priority == "medium"

    def test_intake_artifact_defaults(self):
        """IntakeArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import IntakeArtifact

        artifact = IntakeArtifact(
            request_id="REQ-001",
            original_request="Test",
            detected_scope="unclear",
            priority="low",
        )

        assert artifact.initial_questions == []
        assert artifact.detected_components == []
        assert artifact.keywords == []
        assert artifact.confidence == 0.5
        assert artifact.estimated_complexity == "medium"


class TestClarifyArtifact:
    """Tests for ClarifyArtifact dataclass."""

    def test_clarify_artifact_creation(self):
        """ClarifyArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import ClarifyArtifact

        artifact = ClarifyArtifact(
            request_id="REQ-001",
            clarified_requirements="Add a login button to the header",
        )

        assert artifact.request_id == "REQ-001"
        assert artifact.clarified_requirements == "Add a login button to the header"

    def test_clarify_artifact_defaults(self):
        """ClarifyArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import ClarifyArtifact

        artifact = ClarifyArtifact(
            request_id="REQ-001",
            clarified_requirements="Test",
        )

        assert artifact.scope_confirmed is False
        assert artifact.answered_questions == []
        assert artifact.remaining_questions == []
        assert artifact.refined_scope is None
        assert artifact.ready_for_analysis is False


class TestAnalyzeArtifact:
    """Tests for AnalyzeArtifact dataclass."""

    def test_analyze_artifact_creation(self):
        """AnalyzeArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import AnalyzeArtifact

        artifact = AnalyzeArtifact(
            request_id="REQ-001",
            analysis={"summary": "Analysis summary", "complexity": "medium"},
        )

        assert artifact.request_id == "REQ-001"
        assert artifact.analysis["summary"] == "Analysis summary"

    def test_analyze_artifact_defaults(self):
        """AnalyzeArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import AnalyzeArtifact

        artifact = AnalyzeArtifact(request_id="REQ-001")

        assert artifact.analysis == {}
        assert artifact.affected_files == []
        assert artifact.components == []
        assert artifact.dependencies == []
        assert artifact.risks == []


class TestSpecArtifact:
    """Tests for SpecArtifact dataclass."""

    def test_spec_artifact_creation(self):
        """SpecArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import SpecArtifact

        artifact = SpecArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
            title="Login Button Feature",
        )

        assert artifact.spec_id == "SPEC-001"
        assert artifact.request_id == "REQ-001"
        assert artifact.title == "Login Button Feature"

    def test_spec_artifact_defaults(self):
        """SpecArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import SpecArtifact

        artifact = SpecArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
        )

        assert artifact.title == ""
        assert artifact.version == "1.0"
        assert artifact.overview == {}
        assert artifact.components == []
        assert artifact.test_cases == []
        assert artifact.interfaces == []
        assert artifact.data_models == []
        assert artifact.implementation_order == []
        assert artifact.acceptance_criteria == []


class TestArtifactConversion:
    """Tests for artifact to/from dict conversion."""

    def test_artifact_to_dict_conversion(self):
        """Artifacts can be converted to dict."""
        from agentforge.core.pipeline.artifacts import IntakeArtifact

        artifact = IntakeArtifact(
            request_id="REQ-001",
            original_request="Test request",
            detected_scope="feature_addition",
            priority="high",
            keywords=["test", "feature"],
        )

        data = asdict(artifact)
        assert data["request_id"] == "REQ-001"
        assert data["original_request"] == "Test request"
        assert data["detected_scope"] == "feature_addition"
        assert data["priority"] == "high"
        assert data["keywords"] == ["test", "feature"]

    def test_artifact_from_dict_conversion(self):
        """Artifacts can be created from dict."""
        from agentforge.core.pipeline.artifacts import IntakeArtifact

        data = {
            "request_id": "REQ-002",
            "original_request": "Another request",
            "detected_scope": "bug_fix",
            "priority": "critical",
            "initial_questions": [{"question": "What bug?", "priority": "blocking"}],
            "detected_components": ["auth"],
            "keywords": ["bug"],
            "confidence": 0.9,
            "estimated_complexity": "low",
        }

        artifact = IntakeArtifact(**data)
        assert artifact.request_id == "REQ-002"
        assert artifact.detected_scope == "bug_fix"
        assert artifact.priority == "critical"
        assert len(artifact.initial_questions) == 1
        assert artifact.confidence == 0.9

    def test_spec_artifact_full_roundtrip(self):
        """SpecArtifact roundtrips correctly through dict."""
        from agentforge.core.pipeline.artifacts import SpecArtifact

        original = SpecArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
            title="Test Feature",
            version="2.0",
            overview={"description": "Test description"},
            components=[{"name": "Component1", "type": "class"}],
            test_cases=[{"id": "TC001", "description": "Test case 1"}],
            acceptance_criteria=["All tests pass"],
        )

        data = asdict(original)
        restored = SpecArtifact(**data)

        assert restored.spec_id == original.spec_id
        assert restored.title == original.title
        assert restored.version == original.version
        assert restored.components == original.components
        assert restored.test_cases == original.test_cases
        assert restored.acceptance_criteria == original.acceptance_criteria


# ═══════════════════════════════════════════════════════════════════════════════
# TDD Artifact Tests (Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRedArtifact:
    """Tests for RedArtifact dataclass."""

    def test_red_artifact_creation(self):
        """RedArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import RedArtifact

        artifact = RedArtifact(
            spec_id="SPEC-001",
        )

        assert artifact.spec_id == "SPEC-001"

    def test_red_artifact_defaults(self):
        """RedArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import RedArtifact

        artifact = RedArtifact(spec_id="SPEC-001")

        assert artifact.request_id == ""
        assert artifact.test_files == []
        assert artifact.test_results == {}
        assert artifact.failing_tests == []
        assert artifact.unexpected_passes == []
        assert artifact.warnings == []

    def test_red_artifact_with_test_results(self):
        """RedArtifact can store test results."""
        from agentforge.core.pipeline.artifacts import RedArtifact

        artifact = RedArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
            test_files=[{"path": "tests/test.py", "content": "..."}],
            test_results={
                "passed": 0,
                "failed": 3,
                "total": 3,
            },
            failing_tests=["test_one", "test_two", "test_three"],
        )

        assert len(artifact.test_files) == 1
        assert artifact.test_results["failed"] == 3
        assert len(artifact.failing_tests) == 3

    def test_red_artifact_to_dict(self):
        """RedArtifact can be converted to dict."""
        from agentforge.core.pipeline.artifacts import RedArtifact

        artifact = RedArtifact(
            spec_id="SPEC-001",
            failing_tests=["test_a", "test_b"],
        )

        data = asdict(artifact)
        assert data["spec_id"] == "SPEC-001"
        assert data["failing_tests"] == ["test_a", "test_b"]


class TestGreenArtifact:
    """Tests for GreenArtifact dataclass."""

    def test_green_artifact_creation(self):
        """GreenArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(
            spec_id="SPEC-001",
        )

        assert artifact.spec_id == "SPEC-001"

    def test_green_artifact_defaults(self):
        """GreenArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(spec_id="SPEC-001")

        assert artifact.request_id == ""
        assert artifact.implementation_files == []
        assert artifact.test_results == {}
        assert artifact.passing_tests == 0
        assert artifact.iterations == 0
        assert artifact.all_tests_pass is False
        assert artifact.error is None

    def test_green_artifact_with_implementation(self):
        """GreenArtifact can store implementation results."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
            implementation_files=["src/module.py", "src/helper.py"],
            test_results={
                "passed": 5,
                "failed": 0,
                "total": 5,
            },
            passing_tests=5,
            iterations=3,
            all_tests_pass=True,
        )

        assert len(artifact.implementation_files) == 2
        assert artifact.passing_tests == 5
        assert artifact.iterations == 3
        assert artifact.all_tests_pass is True

    def test_green_artifact_with_error(self):
        """GreenArtifact can store error state."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(
            spec_id="SPEC-001",
            all_tests_pass=False,
            error="Max iterations reached",
        )

        assert artifact.all_tests_pass is False
        assert artifact.error == "Max iterations reached"

    def test_green_artifact_to_dict(self):
        """GreenArtifact can be converted to dict."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(
            spec_id="SPEC-001",
            implementation_files=["file.py"],
            all_tests_pass=True,
        )

        data = asdict(artifact)
        assert data["spec_id"] == "SPEC-001"
        assert data["implementation_files"] == ["file.py"]
        assert data["all_tests_pass"] is True


class TestTDDArtifactRoundtrip:
    """Tests for TDD artifact roundtrip conversion."""

    def test_red_artifact_roundtrip(self):
        """RedArtifact roundtrips correctly through dict."""
        from agentforge.core.pipeline.artifacts import RedArtifact

        original = RedArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
            test_files=[{"path": "test.py", "content": "..."}],
            failing_tests=["test_one"],
            warnings=["Some tests passed unexpectedly"],
        )

        data = asdict(original)
        restored = RedArtifact(**data)

        assert restored.spec_id == original.spec_id
        assert restored.request_id == original.request_id
        assert restored.test_files == original.test_files
        assert restored.failing_tests == original.failing_tests
        assert restored.warnings == original.warnings

    def test_green_artifact_roundtrip(self):
        """GreenArtifact roundtrips correctly through dict."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        original = GreenArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
            implementation_files=["src/module.py"],
            passing_tests=5,
            iterations=3,
            all_tests_pass=True,
        )

        data = asdict(original)
        restored = GreenArtifact(**data)

        assert restored.spec_id == original.spec_id
        assert restored.implementation_files == original.implementation_files
        assert restored.passing_tests == original.passing_tests
        assert restored.iterations == original.iterations
        assert restored.all_tests_pass == original.all_tests_pass
