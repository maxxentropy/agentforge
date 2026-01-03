# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @component_id: pipeline-artifacts
# @component_id: tdd-artifacts
# @test_path: tests/unit/pipeline/test_artifacts.py

"""Tests for artifact dataclasses."""

from dataclasses import asdict


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

        assert artifact.request_id == "REQ-001", "Expected artifact.request_id to equal 'REQ-001'"
        assert artifact.original_request == "Add a login button", "Expected artifact.original_request to equal 'Add a login button'"
        assert artifact.detected_scope == "feature_addition", "Expected artifact.detected_scope to equal 'feature_addition'"
        assert artifact.priority == "medium", "Expected artifact.priority to equal 'medium'"

    def test_intake_artifact_defaults(self):
        """IntakeArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import IntakeArtifact

        artifact = IntakeArtifact(
            request_id="REQ-001",
            original_request="Test",
            detected_scope="unclear",
            priority="low",
        )

        assert artifact.initial_questions == [], "Expected artifact.initial_questions to equal []"
        assert artifact.detected_components == [], "Expected artifact.detected_components to equal []"
        assert artifact.keywords == [], "Expected artifact.keywords to equal []"
        assert artifact.confidence == 0.5, "Expected artifact.confidence to equal 0.5"
        assert artifact.estimated_complexity == "medium", "Expected artifact.estimated_complexity to equal 'medium'"


class TestClarifyArtifact:
    """Tests for ClarifyArtifact dataclass."""

    def test_clarify_artifact_creation(self):
        """ClarifyArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import ClarifyArtifact

        artifact = ClarifyArtifact(
            request_id="REQ-001",
            clarified_requirements="Add a login button to the header",
        )

        assert artifact.request_id == "REQ-001", "Expected artifact.request_id to equal 'REQ-001'"
        assert artifact.clarified_requirements == "Add a login button to the header", "Expected artifact.clarified_requirem... to equal 'Add a login button to the ..."

    def test_clarify_artifact_defaults(self):
        """ClarifyArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import ClarifyArtifact

        artifact = ClarifyArtifact(
            request_id="REQ-001",
            clarified_requirements="Test",
        )

        assert artifact.scope_confirmed is False, "Expected artifact.scope_confirmed is False"
        assert artifact.answered_questions == [], "Expected artifact.answered_questions to equal []"
        assert artifact.remaining_questions == [], "Expected artifact.remaining_questions to equal []"
        assert artifact.refined_scope is None, "Expected artifact.refined_scope is None"
        assert artifact.ready_for_analysis is False, "Expected artifact.ready_for_analysis is False"


class TestAnalyzeArtifact:
    """Tests for AnalyzeArtifact dataclass."""

    def test_analyze_artifact_creation(self):
        """AnalyzeArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import AnalyzeArtifact

        artifact = AnalyzeArtifact(
            request_id="REQ-001",
            analysis={"summary": "Analysis summary", "complexity": "medium"},
        )

        assert artifact.request_id == "REQ-001", "Expected artifact.request_id to equal 'REQ-001'"
        assert artifact.analysis["summary"] == "Analysis summary", "Expected artifact.analysis['summary'] to equal 'Analysis summary'"

    def test_analyze_artifact_defaults(self):
        """AnalyzeArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import AnalyzeArtifact

        artifact = AnalyzeArtifact(request_id="REQ-001")

        assert artifact.analysis == {}, "Expected artifact.analysis to equal {}"
        assert artifact.affected_files == [], "Expected artifact.affected_files to equal []"
        assert artifact.components == [], "Expected artifact.components to equal []"
        assert artifact.dependencies == [], "Expected artifact.dependencies to equal []"
        assert artifact.risks == [], "Expected artifact.risks to equal []"


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

        assert artifact.spec_id == "SPEC-001", "Expected artifact.spec_id to equal 'SPEC-001'"
        assert artifact.request_id == "REQ-001", "Expected artifact.request_id to equal 'REQ-001'"
        assert artifact.title == "Login Button Feature", "Expected artifact.title to equal 'Login Button Feature'"

    def test_spec_artifact_defaults(self):
        """SpecArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import SpecArtifact

        artifact = SpecArtifact(
            spec_id="SPEC-001",
            request_id="REQ-001",
        )

        assert artifact.title == "", "Expected artifact.title to equal ''"
        assert artifact.version == "1.0", "Expected artifact.version to equal '1.0'"
        assert artifact.overview == {}, "Expected artifact.overview to equal {}"
        assert artifact.components == [], "Expected artifact.components to equal []"
        assert artifact.test_cases == [], "Expected artifact.test_cases to equal []"
        assert artifact.interfaces == [], "Expected artifact.interfaces to equal []"
        assert artifact.data_models == [], "Expected artifact.data_models to equal []"
        assert artifact.implementation_order == [], "Expected artifact.implementation_order to equal []"
        assert artifact.acceptance_criteria == [], "Expected artifact.acceptance_criteria to equal []"


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
        assert data["request_id"] == "REQ-001", "Expected data['request_id'] to equal 'REQ-001'"
        assert data["original_request"] == "Test request", "Expected data['original_request'] to equal 'Test request'"
        assert data["detected_scope"] == "feature_addition", "Expected data['detected_scope'] to equal 'feature_addition'"
        assert data["priority"] == "high", "Expected data['priority'] to equal 'high'"
        assert data["keywords"] == ["test", "feature"], "Expected data['keywords'] to equal ['test', 'feature']"

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
        assert artifact.request_id == "REQ-002", "Expected artifact.request_id to equal 'REQ-002'"
        assert artifact.detected_scope == "bug_fix", "Expected artifact.detected_scope to equal 'bug_fix'"
        assert artifact.priority == "critical", "Expected artifact.priority to equal 'critical'"
        assert len(artifact.initial_questions) == 1, "Expected len(artifact.initial_questi... to equal 1"
        assert artifact.confidence == 0.9, "Expected artifact.confidence to equal 0.9"

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

        assert restored.spec_id == original.spec_id, "Expected restored.spec_id to equal original.spec_id"
        assert restored.title == original.title, "Expected restored.title to equal original.title"
        assert restored.version == original.version, "Expected restored.version to equal original.version"
        assert restored.components == original.components, "Expected restored.components to equal original.components"
        assert restored.test_cases == original.test_cases, "Expected restored.test_cases to equal original.test_cases"
        assert restored.acceptance_criteria == original.acceptance_criteria, "Expected restored.acceptance_criteria to equal original.acceptance_criteria"


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

        assert artifact.spec_id == "SPEC-001", "Expected artifact.spec_id to equal 'SPEC-001'"

    def test_red_artifact_defaults(self):
        """RedArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import RedArtifact

        artifact = RedArtifact(spec_id="SPEC-001")

        assert artifact.request_id == "", "Expected artifact.request_id to equal ''"
        assert artifact.test_files == [], "Expected artifact.test_files to equal []"
        assert artifact.test_results == {}, "Expected artifact.test_results to equal {}"
        assert artifact.failing_tests == [], "Expected artifact.failing_tests to equal []"
        assert artifact.unexpected_passes == [], "Expected artifact.unexpected_passes to equal []"
        assert artifact.warnings == [], "Expected artifact.warnings to equal []"

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

        assert len(artifact.test_files) == 1, "Expected len(artifact.test_files) to equal 1"
        assert artifact.test_results["failed"] == 3, "Expected artifact.test_results['fail... to equal 3"
        assert len(artifact.failing_tests) == 3, "Expected len(artifact.failing_tests) to equal 3"

    def test_red_artifact_to_dict(self):
        """RedArtifact can be converted to dict."""
        from agentforge.core.pipeline.artifacts import RedArtifact

        artifact = RedArtifact(
            spec_id="SPEC-001",
            failing_tests=["test_a", "test_b"],
        )

        data = asdict(artifact)
        assert data["spec_id"] == "SPEC-001", "Expected data['spec_id'] to equal 'SPEC-001'"
        assert data["failing_tests"] == ["test_a", "test_b"], "Expected data['failing_tests'] to equal ['test_a', 'test_b']"


class TestGreenArtifact:
    """Tests for GreenArtifact dataclass."""

    def test_green_artifact_creation(self):
        """GreenArtifact can be created with required fields."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(
            spec_id="SPEC-001",
        )

        assert artifact.spec_id == "SPEC-001", "Expected artifact.spec_id to equal 'SPEC-001'"

    def test_green_artifact_defaults(self):
        """GreenArtifact has correct default values."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(spec_id="SPEC-001")

        assert artifact.request_id == "", "Expected artifact.request_id to equal ''"
        assert artifact.implementation_files == [], "Expected artifact.implementation_files to equal []"
        assert artifact.test_results == {}, "Expected artifact.test_results to equal {}"
        assert artifact.passing_tests == 0, "Expected artifact.passing_tests to equal 0"
        assert artifact.iterations == 0, "Expected artifact.iterations to equal 0"
        assert artifact.all_tests_pass is False, "Expected artifact.all_tests_pass is False"
        assert artifact.error is None, "Expected artifact.error is None"

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

        assert len(artifact.implementation_files) == 2, "Expected len(artifact.implementation... to equal 2"
        assert artifact.passing_tests == 5, "Expected artifact.passing_tests to equal 5"
        assert artifact.iterations == 3, "Expected artifact.iterations to equal 3"
        assert artifact.all_tests_pass is True, "Expected artifact.all_tests_pass is True"

    def test_green_artifact_with_error(self):
        """GreenArtifact can store error state."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(
            spec_id="SPEC-001",
            all_tests_pass=False,
            error="Max iterations reached",
        )

        assert artifact.all_tests_pass is False, "Expected artifact.all_tests_pass is False"
        assert artifact.error == "Max iterations reached", "Expected artifact.error to equal 'Max iterations reached'"

    def test_green_artifact_to_dict(self):
        """GreenArtifact can be converted to dict."""
        from agentforge.core.pipeline.artifacts import GreenArtifact

        artifact = GreenArtifact(
            spec_id="SPEC-001",
            implementation_files=["file.py"],
            all_tests_pass=True,
        )

        data = asdict(artifact)
        assert data["spec_id"] == "SPEC-001", "Expected data['spec_id'] to equal 'SPEC-001'"
        assert data["implementation_files"] == ["file.py"], "Expected data['implementation_files'] to equal ['file.py']"
        assert data["all_tests_pass"] is True, "Expected data['all_tests_pass'] is True"


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

        assert restored.spec_id == original.spec_id, "Expected restored.spec_id to equal original.spec_id"
        assert restored.request_id == original.request_id, "Expected restored.request_id to equal original.request_id"
        assert restored.test_files == original.test_files, "Expected restored.test_files to equal original.test_files"
        assert restored.failing_tests == original.failing_tests, "Expected restored.failing_tests to equal original.failing_tests"
        assert restored.warnings == original.warnings, "Expected restored.warnings to equal original.warnings"

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

        assert restored.spec_id == original.spec_id, "Expected restored.spec_id to equal original.spec_id"
        assert restored.implementation_files == original.implementation_files, "Expected restored.implementation_files to equal original.implementation_files"
        assert restored.passing_tests == original.passing_tests, "Expected restored.passing_tests to equal original.passing_tests"
        assert restored.iterations == original.iterations, "Expected restored.iterations to equal original.iterations"
        assert restored.all_tests_pass == original.all_tests_pass, "Expected restored.all_tests_pass to equal original.all_tests_pass"
