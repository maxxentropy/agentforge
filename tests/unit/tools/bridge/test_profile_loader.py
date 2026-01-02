# @spec_file: .agentforge/specs/core-discovery-generators-v1.yaml
# @spec_id: core-discovery-generators-v1
# @component_id: discovery-generators-profile
# @impl_path: tools/discovery/generators/profile.py

"""Unit tests for profile loader."""


import pytest

from agentforge.core.bridge.profile_loader import ProfileLoader


class TestProfileLoader:
    """Tests for profile loading."""

    @pytest.fixture
    def sample_profile_content(self):
        """Sample profile YAML content."""
        return """
schema_version: '1.0'
generated_at: '2025-01-01T12:00:00'
discovery_metadata:
  discovery_version: '1.0'
  root_path: /test/path
languages:
  - name: csharp
    primary: true
    confidence: 0.95
    frameworks:
      - MediatR
      - EFCore
structure:
  architecture_style: clean-architecture
  confidence: 0.9
  layers:
    domain:
      path: src/Domain
    application:
      path: src/Application
patterns:
  cqrs:
    confidence: 0.92
    primary: MediatR
    description: CQRS pattern detected
  repository:
    confidence: 0.85
    description: Repository pattern
"""

    @pytest.fixture
    def sample_profile(self, tmp_path, sample_profile_content):
        """Create a sample profile file."""
        profile_path = tmp_path / ".agentforge" / "codebase_profile.yaml"
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(sample_profile_content)
        return tmp_path

    def test_load_profile(self, sample_profile):
        """Can load a profile file."""
        loader = ProfileLoader(sample_profile)

        raw_profile = loader.load()

        assert raw_profile is not None
        assert "schema_version" in raw_profile
        assert loader.profile_hash.startswith("sha256:")

    def test_get_zones_returns_zone_names(self, sample_profile):
        """get_zones returns zone names."""
        loader = ProfileLoader(sample_profile)
        loader.load()

        zones = loader.get_zones()

        # Single zone profile returns ['default']
        assert zones == ["default"]

    def test_get_all_contexts(self, sample_profile):
        """get_all_contexts returns MappingContext objects."""
        loader = ProfileLoader(sample_profile)
        loader.load()

        contexts = loader.get_all_contexts()

        assert len(contexts) >= 1
        context = contexts[0]
        assert context.language == "csharp"

    def test_context_has_patterns(self, sample_profile):
        """Context includes detected patterns."""
        loader = ProfileLoader(sample_profile)
        loader.load()

        contexts = loader.get_all_contexts()
        context = contexts[0]

        assert context.is_pattern_detected("cqrs")
        assert context.get_pattern_confidence("cqrs") == 0.92

    def test_context_has_language(self, sample_profile):
        """Context includes language."""
        loader = ProfileLoader(sample_profile)
        loader.load()

        contexts = loader.get_all_contexts()
        context = contexts[0]

        assert context.language == "csharp"

    def test_profile_hash_changes_with_content(self, tmp_path):
        """Profile hash changes when content changes."""
        profile_path = tmp_path / ".agentforge" / "codebase_profile.yaml"
        profile_path.parent.mkdir(parents=True)

        profile_path.write_text("schema_version: '1.0'\npatterns: {}\nlanguages:\n  - name: python")
        loader1 = ProfileLoader(tmp_path)
        loader1.load()
        hash1 = loader1.profile_hash

        profile_path.write_text("schema_version: '1.0'\npatterns: {cqrs: {confidence: 0.9}}\nlanguages:\n  - name: python")
        loader2 = ProfileLoader(tmp_path)
        loader2.load()
        hash2 = loader2.profile_hash

        assert hash1 != hash2


class TestProfileLoaderEdgeCases:
    """Edge case tests for profile loader."""

    def test_raises_when_profile_not_found(self, tmp_path):
        """Raises error when profile doesn't exist."""
        loader = ProfileLoader(tmp_path)

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_handles_empty_patterns(self, tmp_path):
        """Handles profiles with no patterns."""
        profile_content = """
schema_version: '1.0'
languages:
  - name: python
patterns: {}
"""
        profile_path = tmp_path / ".agentforge" / "codebase_profile.yaml"
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(profile_content)

        loader = ProfileLoader(tmp_path)
        loader.load()
        contexts = loader.get_all_contexts()

        assert len(contexts) >= 1
        assert len(contexts[0].patterns) == 0

    def test_handles_missing_optional_fields(self, tmp_path):
        """Handles profiles with minimal fields."""
        profile_content = """
schema_version: '1.0'
languages:
  - name: python
"""
        profile_path = tmp_path / ".agentforge" / "codebase_profile.yaml"
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(profile_content)

        loader = ProfileLoader(tmp_path)
        loader.load()
        contexts = loader.get_all_contexts()

        assert len(contexts) >= 1
        assert contexts[0].language == "python"

    def test_get_primary_language(self, tmp_path):
        """Can get primary language."""
        profile_content = """
schema_version: '1.0'
languages:
  - name: python
    primary: true
  - name: csharp
"""
        profile_path = tmp_path / ".agentforge" / "codebase_profile.yaml"
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(profile_content)

        loader = ProfileLoader(tmp_path)
        loader.load()

        assert loader.get_primary_language() == "python"
