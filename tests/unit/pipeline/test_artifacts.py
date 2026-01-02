# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_id: pipeline-controller-phase2-v1
# @component_id: pipeline-artifacts
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
