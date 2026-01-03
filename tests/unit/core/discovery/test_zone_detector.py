# @spec_file: .agentforge/specs/core-discovery-v1.yaml
# @spec_id: core-discovery-v1
# @component_id: core-discovery-zones-detector-tests

"""
Tests for zone auto-detection.

Tests the ZoneDetector class which finds language zones
from project markers like pyproject.toml, *.csproj, *.sln, etc.
"""


import pytest

from agentforge.core.discovery.domain import ZoneDetectionMode
from agentforge.core.discovery.zones.detector import (
    SKIP_DIRECTORIES,
    ZONE_MARKERS,
    ZoneDetector,
    detect_zones,
)


class TestZoneMarkerConfig:
    """Tests for zone marker configuration."""

    def test_zone_markers_have_correct_structure(self):
        """Should have (pattern, language, priority) tuples."""
        for marker in ZONE_MARKERS:
            assert len(marker) == 3, "Expected len(marker) to equal 3"
            pattern, language, priority = marker
            assert isinstance(pattern, str), "Expected isinstance() to be truthy"
            assert isinstance(language, str), "Expected isinstance() to be truthy"
            assert isinstance(priority, int), "Expected isinstance() to be truthy"

    def test_sln_has_highest_priority(self):
        """Solution files should have highest priority."""
        sln_entry = next(m for m in ZONE_MARKERS if m[0] == "*.sln")
        assert sln_entry[2] == 100, "Expected sln_entry[2] to equal 100"

    def test_skip_directories_configured(self):
        """Should have common build/cache directories."""
        assert "node_modules" in SKIP_DIRECTORIES, "Expected 'node_modules' in SKIP_DIRECTORIES"
        assert "__pycache__" in SKIP_DIRECTORIES, "Expected '__pycache__' in SKIP_DIRECTORIES"
        assert ".git" in SKIP_DIRECTORIES, "Expected '.git' in SKIP_DIRECTORIES"
        assert "venv" in SKIP_DIRECTORIES, "Expected 'venv' in SKIP_DIRECTORIES"


class TestZoneDetector:
    """Tests for ZoneDetector class."""

    @pytest.fixture
    def repo_root(self, tmp_path):
        """Create a temporary repository root."""
        return tmp_path

    def test_detect_empty_repo(self, repo_root):
        """Should return empty list for repo without markers."""
        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()
        assert zones == [], "Expected zones to equal []"

    def test_detect_single_python_zone(self, repo_root):
        """Should detect Python zone from pyproject.toml."""
        (repo_root / "pyproject.toml").write_text("[project]\nname='test'")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "python", "Expected zones[0].language to equal 'python'"
        assert zones[0].path == repo_root, "Expected zones[0].path to equal repo_root"
        assert zones[0].marker == repo_root / "pyproject.toml", "Expected zones[0].marker to equal repo_root / 'pyproject.toml'"
        assert zones[0].detection == ZoneDetectionMode.AUTO, "Expected zones[0].detection to equal ZoneDetectionMode.AUTO"

    def test_detect_python_zone_from_setup_py(self, repo_root):
        """Should detect Python zone from setup.py."""
        (repo_root / "setup.py").write_text("from setuptools import setup")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "python", "Expected zones[0].language to equal 'python'"

    def test_detect_single_csharp_zone(self, repo_root):
        """Should detect C# zone from .csproj."""
        project_dir = repo_root / "MyProject"
        project_dir.mkdir()
        (project_dir / "MyProject.csproj").write_text("<Project></Project>")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "csharp", "Expected zones[0].language to equal 'csharp'"
        assert zones[0].name == "MyProject", "Expected zones[0].name to equal 'MyProject'"
        assert zones[0].path == project_dir, "Expected zones[0].path to equal project_dir"

    def test_detect_solution_zone(self, repo_root):
        """Should detect solution-level zone from .sln."""
        (repo_root / "Solution.sln").write_text("Microsoft Visual Studio Solution")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "csharp", "Expected zones[0].language to equal 'csharp'"
        assert zones[0].name == "Solution", "Expected zones[0].name to equal 'Solution'"

    def test_detect_typescript_zone(self, repo_root):
        """Should detect TypeScript zone from package.json."""
        (repo_root / "package.json").write_text('{"name": "frontend"}')

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "typescript", "Expected zones[0].language to equal 'typescript'"

    def test_detect_go_zone(self, repo_root):
        """Should detect Go zone from go.mod."""
        (repo_root / "go.mod").write_text("module example.com/project")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "go", "Expected zones[0].language to equal 'go'"

    def test_detect_rust_zone(self, repo_root):
        """Should detect Rust zone from Cargo.toml."""
        (repo_root / "Cargo.toml").write_text('[package]\nname = "test"')

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "rust", "Expected zones[0].language to equal 'rust'"

    def test_detect_multiple_independent_zones(self, repo_root):
        """Should detect multiple non-nested zones."""
        backend = repo_root / "backend"
        frontend = repo_root / "frontend"
        backend.mkdir()
        frontend.mkdir()

        (backend / "pyproject.toml").write_text("[project]")
        (frontend / "package.json").write_text("{}")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 2, "Expected len(zones) to equal 2"
        languages = {z.language for z in zones}
        assert languages == {"python", "typescript"}, "Expected languages to equal {'python', 'typescript'}"

    def test_solution_takes_precedence_over_csproj(self, repo_root):
        """Solution should subsume nested csproj files."""
        (repo_root / "App.sln").write_text("Microsoft Visual Studio Solution")
        src = repo_root / "src"
        src.mkdir()
        (src / "App.csproj").write_text("<Project></Project>")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        # Should only have one zone (the solution), not a separate csproj zone
        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].name == "App", "Expected zones[0].name to equal 'App'"
        assert zones[0].marker.suffix == ".sln", "Expected zones[0].marker.suffix to equal '.sln'"

    def test_pyproject_takes_precedence_over_setup_py(self, repo_root):
        """pyproject.toml should take precedence over setup.py."""
        (repo_root / "pyproject.toml").write_text("[project]")
        (repo_root / "setup.py").write_text("from setuptools import setup")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].marker.name == "pyproject.toml", "Expected zones[0].marker.name to equal 'pyproject.toml'"

    def test_skip_node_modules(self, repo_root):
        """Should not detect zones inside node_modules."""
        (repo_root / "package.json").write_text("{}")
        node_modules = repo_root / "node_modules" / "some-package"
        node_modules.mkdir(parents=True)
        (node_modules / "package.json").write_text("{}")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        # Should only detect root zone, not nested package
        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].path == repo_root, "Expected zones[0].path to equal repo_root"

    def test_skip_venv(self, repo_root):
        """Should not detect zones inside venv."""
        (repo_root / "pyproject.toml").write_text("[project]")
        venv = repo_root / "venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "setup.py").write_text("# virtual env file")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].path == repo_root, "Expected zones[0].path to equal repo_root"

    def test_skip_pycache(self, repo_root):
        """Should not detect zones inside __pycache__."""
        cache_dir = repo_root / "__pycache__"
        cache_dir.mkdir()
        # This would be weird but test the skip logic
        (cache_dir / "pyproject.toml").write_text("[project]")

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert zones == [], "Expected zones to equal []"

    def test_zones_sorted_by_path_depth(self, repo_root):
        """Should return zones sorted by path depth (outer first)."""
        # Create sibling zones at different depths
        backend = repo_root / "backend"
        deep = repo_root / "services" / "api"
        backend.mkdir()
        deep.mkdir(parents=True)
        (backend / "pyproject.toml").write_text("[project]")
        (deep / "Cargo.toml").write_text('[package]\nname = "api"')

        detector = ZoneDetector(repo_root)
        zones = detector.detect_zones()

        assert len(zones) == 2, "Expected len(zones) to equal 2"
        # Shallower zone should come first (fewer path parts)
        assert len(zones[0].path.parts) <= len(zones[1].path.parts), "Expected len(zones[0].path.parts) <= len(zones[1].path.parts)"


class TestDeriveZoneName:
    """Tests for _derive_zone_name method."""

    @pytest.fixture
    def detector(self, tmp_path):
        return ZoneDetector(tmp_path)

    def test_derive_name_from_sln(self, detector, tmp_path):
        """Should use stem for .sln files."""
        marker = tmp_path / "MySolution.sln"
        marker.touch()

        name = detector._derive_zone_name(marker)

        assert name == "MySolution", "Expected name to equal 'MySolution'"

    def test_derive_name_from_csproj(self, detector, tmp_path):
        """Should use stem for .csproj files."""
        marker = tmp_path / "MyProject.csproj"
        marker.touch()

        name = detector._derive_zone_name(marker)

        assert name == "MyProject", "Expected name to equal 'MyProject'"

    def test_derive_name_from_pyproject(self, detector, tmp_path):
        """Should use directory name for pyproject.toml."""
        subdir = tmp_path / "backend"
        subdir.mkdir()
        marker = subdir / "pyproject.toml"
        marker.touch()

        name = detector._derive_zone_name(marker)

        assert name == "backend", "Expected name to equal 'backend'"


class TestDeriveZonePath:
    """Tests for _derive_zone_path method."""

    @pytest.fixture
    def detector(self, tmp_path):
        return ZoneDetector(tmp_path)

    def test_derive_path_from_sln(self, detector, tmp_path):
        """Should use parent directory for .sln files."""
        marker = tmp_path / "MySolution.sln"
        marker.touch()

        path = detector._derive_zone_path(marker)

        assert path == tmp_path, "Expected path to equal tmp_path"

    def test_derive_path_from_csproj(self, detector, tmp_path):
        """Should use parent directory for .csproj files."""
        project_dir = tmp_path / "MyProject"
        project_dir.mkdir()
        marker = project_dir / "MyProject.csproj"
        marker.touch()

        path = detector._derive_zone_path(marker)

        assert path == project_dir, "Expected path to equal project_dir"

    def test_derive_path_from_pyproject(self, detector, tmp_path):
        """Should use parent directory for pyproject.toml."""
        subdir = tmp_path / "backend"
        subdir.mkdir()
        marker = subdir / "pyproject.toml"
        marker.touch()

        path = detector._derive_zone_path(marker)

        assert path == subdir, "Expected path to equal subdir"


class TestDetectZonesConvenienceFunction:
    """Tests for detect_zones convenience function."""

    def test_detect_zones_function(self, tmp_path):
        """Should work as shorthand for ZoneDetector.detect_zones."""
        (tmp_path / "pyproject.toml").write_text("[project]")

        zones = detect_zones(tmp_path)

        assert len(zones) == 1, "Expected len(zones) to equal 1"
        assert zones[0].language == "python", "Expected zones[0].language to equal 'python'"

    def test_detect_zones_empty(self, tmp_path):
        """Should return empty list for repo without markers."""
        zones = detect_zones(tmp_path)
        assert zones == [], "Expected zones to equal []"
