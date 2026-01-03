# @spec_file: .agentforge/specs/cli-v1.yaml
# @spec_id: cli-v1
# @component_id: cli-spec-adapt

"""
Tests for spec adapt command.

Tests the external spec adaptation workflow that transforms
external specifications into canonical AgentForge format.
"""


import pytest
import yaml


class TestSpecAdaptImports:
    """Tests for spec adapt module imports."""

    def test_run_adapt_import(self):
        """Verify run_adapt can be imported."""
        from agentforge.cli.commands.spec_adapt import run_adapt
        assert run_adapt is not None, "Expected run_adapt is not None"

    def test_adapt_click_command_import(self):
        """Verify adapt click command can be imported."""
        from agentforge.cli.click_commands.spec import adapt
        assert adapt is not None, "Expected adapt is not None"


class TestLoadExternalSpec:
    """Tests for external spec loading."""

    def test_load_external_spec_success(self, tmp_path):
        """Should load external spec content."""
        from agentforge.cli.commands.spec_adapt import _load_external_spec

        spec_file = tmp_path / "test_spec.md"
        spec_file.write_text("# Test Spec\n\nSome content")

        content = _load_external_spec(str(spec_file))
        assert "# Test Spec" in content, "Expected '# Test Spec' in content"
        assert "Some content" in content, "Expected 'Some content' in content"

    def test_load_external_spec_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        from agentforge.cli.commands.spec_adapt import _load_external_spec

        with pytest.raises(FileNotFoundError):
            _load_external_spec("/nonexistent/path/spec.md")


class TestLoadCodebaseProfile:
    """Tests for codebase profile loading."""

    def test_load_profile_success(self, tmp_path):
        """Should load codebase profile when it exists."""
        from agentforge.cli.commands.spec_adapt import _load_codebase_profile

        profile_file = tmp_path / "profile.yaml"
        profile_data = {"language": "python", "patterns": ["mvc"]}
        profile_file.write_text(yaml.dump(profile_data))

        profile = _load_codebase_profile(str(profile_file))
        assert profile["language"] == "python", "Expected profile['language'] to equal 'python'"
        assert "mvc" in profile["patterns"], "Expected 'mvc' in profile['patterns']"

    def test_load_profile_not_found(self, tmp_path):
        """Should return empty dict when profile doesn't exist."""
        from agentforge.cli.commands.spec_adapt import _load_codebase_profile

        profile = _load_codebase_profile(str(tmp_path / "nonexistent.yaml"))
        assert profile == {}, "Expected profile to equal {}"


class TestGetExistingSpecIds:
    """Tests for existing spec ID retrieval."""

    def test_get_existing_spec_ids_empty(self, tmp_path, monkeypatch):
        """Should return empty list when no specs exist."""
        from agentforge.cli.commands.spec_adapt import _get_existing_spec_ids

        monkeypatch.chdir(tmp_path)
        spec_ids = _get_existing_spec_ids()
        assert spec_ids == [], "Expected spec_ids to equal []"

    def test_get_existing_spec_ids_with_specs(self, tmp_path, monkeypatch):
        """Should return spec IDs from existing specs."""
        from agentforge.cli.commands.spec_adapt import _get_existing_spec_ids

        monkeypatch.chdir(tmp_path)
        specs_dir = tmp_path / ".agentforge" / "specs"
        specs_dir.mkdir(parents=True)

        # Create test specs
        spec1 = {"spec_id": "core-feature-v1", "name": "feature"}
        spec2 = {"spec_id": "cli-v1", "name": "cli"}

        (specs_dir / "spec1.yaml").write_text(yaml.dump(spec1))
        (specs_dir / "spec2.yaml").write_text(yaml.dump(spec2))

        spec_ids = _get_existing_spec_ids()
        assert "core-feature-v1" in spec_ids, "Expected 'core-feature-v1' in spec_ids"
        assert "cli-v1" in spec_ids, "Expected 'cli-v1' in spec_ids"


class TestBuildAdaptInputs:
    """Tests for adapt input building."""

    def test_build_adapt_inputs(self):
        """Should build correct input structure."""
        from agentforge.cli.commands.spec_adapt import _build_adapt_inputs

        inputs = _build_adapt_inputs(
            external_spec="# Test Spec",
            profile={"language": "python"},
            existing_spec_ids=["spec-1", "spec-2"],
            original_file="test.md",
        )

        assert inputs["external_spec_content"] == "# Test Spec", "Expected inputs['external_spec_conte... to equal '# Test Spec'"
        assert "python" in inputs["codebase_profile"], "Expected 'python' in inputs['codebase_profile']"
        assert "spec-1" in inputs["existing_spec_ids"], "Expected 'spec-1' in inputs['existing_spec_ids']"
        assert inputs["original_file_path"] == "test.md", "Expected inputs['original_file_path'] to equal 'test.md'"

    def test_build_adapt_inputs_empty_profile(self):
        """Should handle empty profile gracefully."""
        from agentforge.cli.commands.spec_adapt import _build_adapt_inputs

        inputs = _build_adapt_inputs(
            external_spec="# Test",
            profile={},
            existing_spec_ids=[],
            original_file="test.md",
        )

        assert "No codebase profile" in inputs["codebase_profile"], "Expected 'No codebase profile' in inputs['codebase_profile']"
        assert "No existing specs" in inputs["existing_spec_ids"], "Expected 'No existing specs' in inputs['existing_spec_ids']"


class TestSaveAdaptedSpec:
    """Tests for saving adapted specifications."""

    def test_save_adapted_spec_success(self, tmp_path):
        """Should save valid spec and return True."""
        from agentforge.cli.commands.spec_adapt import _save_adapted_spec

        output_path = tmp_path / "output" / "spec.yaml"
        result = {"metadata": {"version": "1.0"}, "spec_id": "test-v1"}

        success = _save_adapted_spec(result, output_path)

        assert success is True, "Expected success is True"
        assert output_path.exists(), "Expected output_path.exists() to be truthy"
        saved = yaml.safe_load(output_path.read_text())
        assert saved["spec_id"] == "test-v1", "Expected saved['spec_id'] to equal 'test-v1'"

    def test_save_adapted_spec_with_raw(self, tmp_path):
        """Should save raw output and return False when parsing failed."""
        from agentforge.cli.commands.spec_adapt import _save_adapted_spec

        output_path = tmp_path / "spec.yaml"
        result = {"_raw": "unparseable content", "_parse_error": "bad yaml"}

        success = _save_adapted_spec(result, output_path)

        assert success is False, "Expected success is False"
        raw_path = output_path.with_suffix(".raw.txt")
        assert raw_path.exists(), "Expected raw_path.exists() to be truthy"
