# @spec_file: .agentforge/specs/core-discovery-v1.yaml
# @spec_id: core-discovery-v1
# @component_id: core-discovery-domain-tests

"""
Tests for discovery domain model.

Tests the pure domain objects for brownfield discovery:
- Enums with classification logic
- Dataclasses with to_dict() serialization
- Detection confidence scoring
- Zone containment checks
- TestLinkage and TestAnalysis for fix workflows
"""

from datetime import datetime
from pathlib import Path

import pytest

from agentforge.core.discovery.domain import (
    CodebaseProfile,
    ConfidenceLevel,
    ConventionDetection,
    DependencyInfo,
    Detection,
    DetectionSource,
    DiscoveryMetadata,
    Interaction,
    InteractionType,
    LanguageInfo,
    LayerInfo,
    OnboardingProgress,
    OnboardingStatus,
    PatternDetection,
    TestAnalysis,
    TestInventory,
    TestLinkage,
    Zone,
    ZoneDetectionMode,
)


class TestConfidenceLevel:
    """Tests for ConfidenceLevel enum."""

    def test_from_score_high(self):
        """Should return HIGH for scores >= 0.9."""
        assert ConfidenceLevel.from_score(0.9) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(0.95) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(1.0) == ConfidenceLevel.HIGH

    def test_from_score_medium(self):
        """Should return MEDIUM for scores 0.6-0.9."""
        assert ConfidenceLevel.from_score(0.6) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.75) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.89) == ConfidenceLevel.MEDIUM

    def test_from_score_low(self):
        """Should return LOW for scores 0.3-0.6."""
        assert ConfidenceLevel.from_score(0.3) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_score(0.45) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_score(0.59) == ConfidenceLevel.LOW

    def test_from_score_uncertain(self):
        """Should return UNCERTAIN for scores < 0.3."""
        assert ConfidenceLevel.from_score(0.0) == ConfidenceLevel.UNCERTAIN
        assert ConfidenceLevel.from_score(0.1) == ConfidenceLevel.UNCERTAIN
        assert ConfidenceLevel.from_score(0.29) == ConfidenceLevel.UNCERTAIN


class TestDetection:
    """Tests for Detection dataclass."""

    def test_confidence_level_property(self):
        """Should return correct confidence level from score."""
        detection = Detection(value="test", confidence=0.85)
        assert detection.confidence_level == ConfidenceLevel.MEDIUM

        detection_high = Detection(value="test", confidence=0.95)
        assert detection_high.confidence_level == ConfidenceLevel.HIGH

    def test_to_dict_minimal(self):
        """Should convert minimal detection to dict."""
        detection = Detection(
            value="found_pattern",
            confidence=0.75,
            source=DetectionSource.AUTO_DETECTED
        )

        result = detection.to_dict()

        assert result["value"] == "found_pattern"
        assert result["confidence"] == 0.75
        assert result["source"] == "auto-detected"
        assert "signals" not in result
        assert "metadata" not in result

    def test_to_dict_with_signals(self):
        """Should include signals when present."""
        detection = Detection(
            value="pattern",
            confidence=0.8,
            signals=["signal1", "signal2"]
        )

        result = detection.to_dict()

        assert result["signals"] == ["signal1", "signal2"]

    def test_to_dict_with_metadata(self):
        """Should include metadata when present."""
        detection = Detection(
            value="pattern",
            confidence=0.8,
            metadata={"key": "value"}
        )

        result = detection.to_dict()

        assert result["metadata"] == {"key": "value"}

    def test_confidence_rounding(self):
        """Should round confidence to 2 decimal places."""
        detection = Detection(value="test", confidence=0.123456789)
        result = detection.to_dict()
        assert result["confidence"] == 0.12


class TestLanguageInfo:
    """Tests for LanguageInfo dataclass."""

    def test_to_dict(self):
        """Should convert language info to dict."""
        detection = Detection(value="python", confidence=0.95)
        lang = LanguageInfo(
            name="Python",
            version="3.11",
            detection=detection,
            file_count=100,
            line_count=5000,
            frameworks=["pytest", "flask"],
            primary=True
        )

        result = lang.to_dict()

        assert result["name"] == "Python"
        assert result["version"] == "3.11"
        assert result["confidence"] == 0.95
        assert result["file_count"] == 100
        assert result["line_count"] == 5000
        assert result["frameworks"] == ["pytest", "flask"]
        assert result["primary"] is True


class TestLayerInfo:
    """Tests for LayerInfo dataclass."""

    def test_has_violations_default(self):
        """Should return False for has_violations by default."""
        layer = LayerInfo(name="core", paths=["src/core"])
        assert layer.has_violations is False

    def test_to_dict(self):
        """Should convert layer info to dict."""
        detection = Detection(value="layer", confidence=0.9)
        layer = LayerInfo(
            name="core",
            paths=["src/core", "src/utils"],
            file_count=50,
            line_count=2500,
            detection=detection
        )

        result = layer.to_dict()

        assert result["name"] == "core"
        assert result["paths"] == ["src/core", "src/utils"]
        assert result["file_count"] == 50
        assert result["confidence"] == 0.9


class TestTestLinkage:
    """Tests for TestLinkage dataclass."""

    def test_to_dict(self):
        """Should convert test linkage to dict."""
        linkage = TestLinkage(
            source_path="src/core/module.py",
            test_paths=["tests/unit/test_module.py", "tests/integration/test_module.py"],
            confidence=0.85,
            detection_method="import"
        )

        result = linkage.to_dict()

        assert result["source_path"] == "src/core/module.py"
        assert len(result["test_paths"]) == 2
        assert result["confidence"] == 0.85
        assert result["detection_method"] == "import"


class TestTestAnalysis:
    """Tests for TestAnalysis dataclass."""

    def test_get_test_path_found(self):
        """Should return primary test path when linkage exists."""
        linkage = TestLinkage(
            source_path="src/module.py",
            test_paths=["tests/test_module.py", "tests/test_module_integration.py"],
            confidence=0.9
        )
        analysis = TestAnalysis(linkages=[linkage])

        result = analysis.get_test_path("src/module.py")

        assert result == "tests/test_module.py"

    def test_get_test_path_not_found(self):
        """Should return None when no linkage exists."""
        analysis = TestAnalysis(linkages=[])

        result = analysis.get_test_path("src/unknown.py")

        assert result is None

    def test_get_test_path_empty_test_paths(self):
        """Should return None when linkage has empty test_paths."""
        linkage = TestLinkage(
            source_path="src/module.py",
            test_paths=[],
            confidence=0.5
        )
        analysis = TestAnalysis(linkages=[linkage])

        result = analysis.get_test_path("src/module.py")

        assert result is None

    def test_to_dict(self):
        """Should convert test analysis to dict with linkages."""
        inventory = TestInventory(
            total_test_files=10,
            total_test_methods=50,
            frameworks=["pytest"],
            categories={"unit": 40, "integration": 10}
        )
        linkage = TestLinkage(
            source_path="src/a.py",
            test_paths=["tests/test_a.py"]
        )
        analysis = TestAnalysis(
            inventory=inventory,
            estimated_coverage=0.65,
            linkages=[linkage],
            detection=Detection(value="test_analysis", confidence=0.8)
        )

        result = analysis.to_dict()

        assert result["inventory"]["total_test_files"] == 10
        assert result["inventory"]["frameworks"] == ["pytest"]
        assert result["estimated_coverage"] == 0.65
        assert result["linkages"] == {"src/a.py": ["tests/test_a.py"]}


class TestZone:
    """Tests for Zone dataclass."""

    def test_to_dict(self):
        """Should convert zone to dict."""
        zone = Zone(
            name="backend",
            path=Path("/repo/backend"),
            language="python",
            marker=Path("/repo/backend/pyproject.toml"),
            detection=ZoneDetectionMode.AUTO,
            purpose="API services",
            contracts=["python-standards", "api-contracts"]
        )

        result = zone.to_dict()

        assert result["name"] == "backend"
        assert result["path"] == "/repo/backend"
        assert result["language"] == "python"
        assert result["marker"] == "/repo/backend/pyproject.toml"
        assert result["detection"] == "auto"
        assert result["purpose"] == "API services"
        assert result["contracts"] == ["python-standards", "api-contracts"]

    def test_to_dict_no_marker(self):
        """Should handle None marker."""
        zone = Zone(
            name="root",
            path=Path("/repo"),
            language="python"
        )

        result = zone.to_dict()

        assert result["marker"] is None

    def test_contains_path_inside(self):
        """Should return True for paths inside zone."""
        zone = Zone(
            name="backend",
            path=Path("/repo/backend"),
            language="python"
        )

        assert zone.contains_path(Path("/repo/backend/src")) is True
        assert zone.contains_path(Path("/repo/backend/src/module.py")) is True
        assert zone.contains_path(Path("/repo/backend")) is True

    def test_contains_path_outside(self):
        """Should return False for paths outside zone."""
        zone = Zone(
            name="backend",
            path=Path("/repo/backend"),
            language="python"
        )

        assert zone.contains_path(Path("/repo/frontend")) is False
        assert zone.contains_path(Path("/other/path")) is False


class TestInteraction:
    """Tests for Interaction dataclass."""

    def test_to_dict_directional(self):
        """Should format directional interaction."""
        interaction = Interaction(
            id="http-api-1",
            interaction_type=InteractionType.HTTP_API,
            from_zone="frontend",
            to_zone="backend",
            details={"endpoint": "/api/users"}
        )

        result = interaction.to_dict()

        assert result["id"] == "http-api-1"
        assert result["type"] == "http_api"
        assert result["from_zone"] == "frontend"
        assert result["to_zone"] == "backend"
        assert result["details"]["endpoint"] == "/api/users"

    def test_to_dict_multi_zone(self):
        """Should format multi-zone interaction."""
        interaction = Interaction(
            id="shared-schema-1",
            interaction_type=InteractionType.SHARED_SCHEMA,
            zones=["backend", "worker", "api"]
        )

        result = interaction.to_dict()

        assert result["zones"] == ["backend", "worker", "api"]
        assert "from_zone" not in result
        assert "to_zone" not in result


class TestOnboardingProgress:
    """Tests for OnboardingProgress dataclass."""

    def test_is_complete_true(self):
        """Should return True when status is ANALYZED."""
        progress = OnboardingProgress(status=OnboardingStatus.ANALYZED)
        assert progress.is_complete() is True

    def test_is_complete_false(self):
        """Should return False for other statuses."""
        progress = OnboardingProgress(status=OnboardingStatus.IN_PROGRESS)
        assert progress.is_complete() is False

        progress2 = OnboardingProgress(status=OnboardingStatus.NOT_STARTED)
        assert progress2.is_complete() is False


class TestCodebaseProfile:
    """Tests for CodebaseProfile dataclass."""

    @pytest.fixture
    def sample_profile(self):
        """Create a sample codebase profile."""
        metadata = DiscoveryMetadata(
            discovery_version="1.0.0",
            run_date=datetime(2026, 1, 2, 12, 0, 0),
            root_path="/repo",
            phases_completed=["language", "structure"],
            total_files_analyzed=100,
            duration_seconds=5.5
        )
        language = LanguageInfo(
            name="Python",
            version="3.11",
            detection=Detection(value="python", confidence=0.95),
            file_count=100,
            primary=True
        )
        return CodebaseProfile(
            schema_version="1.0",
            generated_at=datetime(2026, 1, 2, 12, 0, 0),
            discovery_metadata=metadata,
            languages=[language],
            structure={"entry_points": ["main.py"]},
            patterns={"di_framework": "manual"},
        )

    def test_to_dict_minimal(self, sample_profile):
        """Should convert profile to dict with required fields."""
        result = sample_profile.to_dict()

        assert result["schema_version"] == "1.0"
        assert "generated_at" in result
        assert result["discovery_metadata"]["discovery_version"] == "1.0.0"
        assert len(result["languages"]) == 1
        assert result["languages"][0]["name"] == "Python"
        assert result["structure"]["entry_points"] == ["main.py"]

    def test_to_dict_with_test_analysis(self, sample_profile):
        """Should include test analysis when present."""
        sample_profile.test_analysis = TestAnalysis(
            estimated_coverage=0.65,
            detection=Detection(value="tests", confidence=0.8)
        )

        result = sample_profile.to_dict()

        assert "test_analysis" in result
        assert result["test_analysis"]["estimated_coverage"] == 0.65

    def test_to_dict_with_dependencies(self, sample_profile):
        """Should include dependencies when present."""
        sample_profile.dependencies = [
            DependencyInfo(name="pytest", version="7.0", source="pypi", is_dev=True)
        ]

        result = sample_profile.to_dict()

        assert "dependencies" in result
        assert result["dependencies"][0]["name"] == "pytest"
        assert result["dependencies"][0]["is_dev"] is True

    def test_to_dict_with_onboarding(self, sample_profile):
        """Should include onboarding progress when present."""
        sample_profile.onboarding_progress = OnboardingProgress(
            status=OnboardingStatus.IN_PROGRESS,
            modules={"core": OnboardingStatus.ANALYZED, "api": OnboardingStatus.NOT_STARTED}
        )

        result = sample_profile.to_dict()

        assert "onboarding_progress" in result
        assert result["onboarding_progress"]["status"] == "in_progress"
        assert result["onboarding_progress"]["modules"]["core"] == "analyzed"


class TestPatternDetection:
    """Tests for PatternDetection dataclass."""

    def test_to_dict_truncates_locations(self):
        """Should truncate locations to 5 items."""
        detection = Detection(value="pattern", confidence=0.8, source=DetectionSource.AST)
        pattern = PatternDetection(
            pattern_name="repository_pattern",
            description="Repository pattern detected",
            detection=detection,
            locations=[f"file{i}.py" for i in range(10)],
            file_count=10
        )

        result = pattern.to_dict()

        assert len(result["locations"]) == 5


class TestConventionDetection:
    """Tests for ConventionDetection dataclass."""

    def test_to_dict_truncates_exceptions(self):
        """Should truncate exceptions to 10 items."""
        detection = Detection(value="convention", confidence=0.9)
        convention = ConventionDetection(
            name="snake_case",
            pattern=r"^[a-z_]+$",
            detection=detection,
            consistency=0.85,
            exceptions=[f"BadName{i}" for i in range(15)]
        )

        result = convention.to_dict()

        assert len(result["exceptions"]) == 10
