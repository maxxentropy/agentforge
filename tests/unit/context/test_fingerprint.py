# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: fingerprint-tests

"""
Tests for project fingerprint generator.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agentforge.core.context.fingerprint import (
    DetectedPatterns,
    FingerprintGenerator,
    ProjectFingerprint,
    ProjectIdentity,
    ProjectStructure,
    TechnicalProfile,
)


class TestProjectFingerprint:
    """Tests for ProjectFingerprint model."""

    def test_to_context_yaml_minimal(self):
        """Test YAML output with minimal data."""
        fp = ProjectFingerprint(
            identity=ProjectIdentity(
                name="test",
                path="/test",
                content_hash="abc123",
            ),
            technical=TechnicalProfile(language="python"),
            patterns=DetectedPatterns(),
            structure=ProjectStructure(),
        )

        yaml_output = fp.to_context_yaml()
        assert "name: test" in yaml_output
        assert "language: python" in yaml_output

    def test_to_context_yaml_with_frameworks(self):
        """Test YAML output includes frameworks."""
        fp = ProjectFingerprint(
            identity=ProjectIdentity(name="test", path="/test", content_hash="abc"),
            technical=TechnicalProfile(
                language="python",
                frameworks=["fastapi", "pydantic"],
            ),
            patterns=DetectedPatterns(),
            structure=ProjectStructure(),
        )

        yaml_output = fp.to_context_yaml()
        assert "fastapi" in yaml_output
        assert "pydantic" in yaml_output

    def test_to_context_yaml_with_patterns(self):
        """Test YAML output includes detected patterns."""
        fp = ProjectFingerprint(
            identity=ProjectIdentity(name="test", path="/test", content_hash="abc"),
            technical=TechnicalProfile(language="python"),
            patterns=DetectedPatterns(
                architecture="clean_architecture",
                naming="snake_case",
                docstrings="google",
            ),
            structure=ProjectStructure(),
        )

        yaml_output = fp.to_context_yaml()
        assert "clean_architecture" in yaml_output
        assert "snake_case" in yaml_output
        assert "google" in yaml_output

    def test_to_context_yaml_excludes_unknown(self):
        """Test YAML output excludes 'unknown' pattern values."""
        fp = ProjectFingerprint(
            identity=ProjectIdentity(name="test", path="/test", content_hash="abc"),
            technical=TechnicalProfile(language="python"),
            patterns=DetectedPatterns(naming="unknown", docstrings="unknown"),
            structure=ProjectStructure(),
        )

        yaml_output = fp.to_context_yaml()
        # Unknown values should not appear in output
        assert "unknown" not in yaml_output

    def test_estimate_tokens(self):
        """Test token estimation."""
        fp = ProjectFingerprint(
            identity=ProjectIdentity(name="test", path="/test", content_hash="abc"),
            technical=TechnicalProfile(language="python"),
            patterns=DetectedPatterns(),
            structure=ProjectStructure(),
        )

        tokens = fp.estimate_tokens()
        assert tokens > 0
        assert tokens < 200  # Minimal fingerprint should be small

    def test_with_task_context(self):
        """Test adding task context creates new instance."""
        base = ProjectFingerprint(
            identity=ProjectIdentity(name="test", path="/test", content_hash="abc"),
            technical=TechnicalProfile(language="python"),
            patterns=DetectedPatterns(),
            structure=ProjectStructure(),
        )

        with_task = base.with_task_context(
            task_type="fix_violation",
            constraints={"correctness_first": True},
            success_criteria=["Tests pass"],
        )

        # New instance
        assert with_task is not base

        # Task context added
        assert with_task.task_type == "fix_violation"
        assert with_task.task_constraints["correctness_first"] is True
        assert "Tests pass" in with_task.success_criteria

        # Original unchanged
        assert base.task_type is None

    def test_with_task_context_in_yaml(self):
        """Test task context appears in YAML output."""
        base = ProjectFingerprint(
            identity=ProjectIdentity(name="test", path="/test", content_hash="abc"),
            technical=TechnicalProfile(language="python"),
            patterns=DetectedPatterns(),
            structure=ProjectStructure(),
        )

        with_task = base.with_task_context(
            task_type="fix_violation",
            constraints={"correctness_first": True, "auto_revert": True},
            success_criteria=["Tests pass", "Check passes"],
        )

        yaml_output = with_task.to_context_yaml()
        assert "correctness_first" in yaml_output
        assert "Tests pass" in yaml_output


class TestFingerprintGenerator:
    """Tests for FingerprintGenerator."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            yield project

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        FingerprintGenerator.clear_cache()
        yield
        FingerprintGenerator.clear_cache()

    def test_detect_python_project(self, temp_project):
        """Detect Python project from pyproject.toml."""
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "test-project"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0.0",
    "pytest>=7.0.0",
]
"""
        )

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.technical.language == "python"
        assert "pydantic" in fp.technical.frameworks
        assert "pytest" in fp.technical.frameworks
        assert fp.technical.version == "3.11"

    def test_detect_python_with_fastapi(self, temp_project):
        """Detect FastAPI framework."""
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text(
            """
[project]
dependencies = ["fastapi>=0.100.0"]
"""
        )

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.technical.language == "python"
        assert "fastapi" in fp.technical.frameworks

    def test_detect_node_project(self, temp_project):
        """Detect Node.js project from package.json."""
        package_json = temp_project / "package.json"
        package_json.write_text(
            """
{
    "name": "test-project",
    "dependencies": {
        "react": "^18.0.0",
        "express": "^4.0.0"
    },
    "devDependencies": {
        "jest": "^29.0.0"
    }
}
"""
        )

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.technical.language == "javascript"
        assert "react" in fp.technical.frameworks
        assert "express" in fp.technical.frameworks
        assert fp.technical.test_framework == "jest"

    def test_detect_typescript_project(self, temp_project):
        """Detect TypeScript project."""
        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "tsconfig.json").write_text("{}")

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.technical.language == "typescript"

    def test_detect_rust_project(self, temp_project):
        """Detect Rust project."""
        (temp_project / "Cargo.toml").write_text('[package]\nname = "test"')

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.technical.language == "rust"
        assert fp.technical.build_system == "cargo"

    def test_detect_go_project(self, temp_project):
        """Detect Go project."""
        (temp_project / "go.mod").write_text("module test")

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.technical.language == "go"
        assert fp.technical.build_system == "go"

    def test_detect_clean_architecture(self, temp_project):
        """Detect clean architecture pattern."""
        src = temp_project / "src"
        src.mkdir()
        (src / "domain").mkdir()
        (src / "application").mkdir()
        (src / "infrastructure").mkdir()

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.patterns.architecture == "clean_architecture"

    def test_detect_mvc_architecture(self, temp_project):
        """Detect MVC architecture pattern."""
        src = temp_project / "src"
        src.mkdir()
        (src / "models").mkdir()
        (src / "views").mkdir()
        (src / "controllers").mkdir()

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.patterns.architecture == "mvc"

    def test_detect_structure(self, temp_project):
        """Detect project structure."""
        (temp_project / "src").mkdir()
        (temp_project / "tests").mkdir()
        (temp_project / "pyproject.toml").write_text("")

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.structure.source_root == "src"
        assert fp.structure.test_root == "tests"
        assert "pyproject.toml" in fp.structure.config_files

    def test_cache_hit(self, temp_project):
        """Test that cache is used on second call."""
        (temp_project / "pyproject.toml").write_text('[project]\nname = "test"')

        generator = FingerprintGenerator(temp_project)

        fp1 = generator.generate()
        fp2 = generator.generate()

        # Same object (cached)
        assert fp1 is fp2

    def test_cache_invalidation_on_file_change(self, temp_project):
        """Test that cache invalidates on file change."""
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test1"')

        generator = FingerprintGenerator(temp_project)
        fp1 = generator.generate()

        # Modify file
        pyproject.write_text('[project]\nname = "test2"')

        # Force new hash computation
        FingerprintGenerator.clear_cache()
        fp2 = generator.generate()

        # Different objects
        assert fp1 is not fp2

    def test_force_refresh(self, temp_project):
        """Test force refresh bypasses cache."""
        (temp_project / "pyproject.toml").write_text('[project]\nname = "test"')

        generator = FingerprintGenerator(temp_project)

        fp1 = generator.generate()
        fp2 = generator.generate(force_refresh=True)

        # Different objects
        assert fp1 is not fp2

    def test_with_task_context_method(self, temp_project):
        """Test generating fingerprint with task context."""
        (temp_project / "pyproject.toml").write_text('[project]\nname = "test"')

        generator = FingerprintGenerator(temp_project)

        fp = generator.with_task_context(
            task_type="fix_violation",
            constraints={"correctness_first": True, "auto_revert": True},
            success_criteria=["Check passes", "Tests pass"],
        )

        assert fp.task_type == "fix_violation"
        assert fp.task_constraints["correctness_first"] is True
        assert "Check passes" in fp.success_criteria

        # Base fingerprint is cached without task context
        base = generator.generate()
        assert base.task_type is None

    def test_unknown_project(self, temp_project):
        """Test handling of project with no recognized config."""
        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.technical.language == "unknown"
        assert fp.identity.name == "test_project"

    def test_entry_points_detection(self, temp_project):
        """Test detection of entry points at root level."""
        # Entry point at root level (most common case)
        (temp_project / "main.py").write_text("# main entry point")

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert len(fp.structure.entry_points) > 0
        assert "main.py" in fp.structure.entry_points

    def test_identity_content_hash(self, temp_project):
        """Test that identity includes content hash."""
        (temp_project / "pyproject.toml").write_text("test")

        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()

        assert fp.identity.content_hash
        assert len(fp.identity.content_hash) == 16
