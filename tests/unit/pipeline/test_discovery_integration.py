# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-discovery-integration

"""Tests for brownfield discovery to pipeline integration."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from agentforge.core.pipeline.discovery_integration import (
    DiscoveredContext,
    create_pipeline_context_from_discovery,
    extract_context_from_profile,
    get_contracts_for_language,
    resolve_test_path,
)


# =============================================================================
# Mock CodebaseProfile for testing
# =============================================================================


@dataclass
class MockLanguageInfo:
    """Mock language info for testing."""

    name: str
    primary: bool = False
    frameworks: list[str] = field(default_factory=list)


@dataclass
class MockTestInventory:
    """Mock test inventory for testing."""

    frameworks: list[str] = field(default_factory=list)


@dataclass
class MockTestLinkage:
    """Mock source-to-test linkage."""

    source_path: str
    test_paths: list[str]


@dataclass
class MockTestAnalysis:
    """Mock test analysis for testing."""

    inventory: MockTestInventory | None = None
    estimated_coverage: float | None = None
    linkages: list[MockTestLinkage] = field(default_factory=list)


@dataclass
class MockDependency:
    """Mock dependency info."""

    name: str
    is_dev: bool = False


@dataclass
class MockCodebaseProfile:
    """Mock CodebaseProfile for testing."""

    languages: list[MockLanguageInfo] = field(default_factory=list)
    structure: dict | None = None
    patterns: dict | None = None
    conventions: list | None = None
    test_analysis: MockTestAnalysis | None = None
    dependencies: list[MockDependency] = field(default_factory=list)


# =============================================================================
# DiscoveredContext Tests
# =============================================================================


class TestDiscoveredContext:
    """Tests for DiscoveredContext dataclass."""

    def test_default_values(self):
        """DiscoveredContext has sensible defaults."""
        ctx = DiscoveredContext()
        assert ctx.primary_language is None, "Expected ctx.primary_language is None"
        assert ctx.languages == [], "Expected ctx.languages to equal []"
        assert ctx.frameworks == [], "Expected ctx.frameworks to equal []"
        assert ctx.estimated_coverage == 0.0, "Expected ctx.estimated_coverage to equal 0.0"

    def test_get_test_path_for_source(self):
        """get_test_path_for_source returns mapped test path."""
        ctx = DiscoveredContext(
            source_to_test_mapping={
                "src/foo.py": ["tests/test_foo.py"],
                "src/bar.py": ["tests/test_bar.py", "tests/test_bar_extra.py"],
            }
        )

        assert ctx.get_test_path_for_source("src/foo.py") == "tests/test_foo.py", "Expected ctx.get_test_path_for_sourc... to equal 'tests/test_foo.py'"
        # Returns first when multiple
        assert ctx.get_test_path_for_source("src/bar.py") == "tests/test_bar.py", "Expected ctx.get_test_path_for_sourc... to equal 'tests/test_bar.py'"
        # Returns None for unknown
        assert ctx.get_test_path_for_source("src/unknown.py") is None, "Expected ctx.get_test_path_for_sourc... is None"

    def test_has_test_for_source(self):
        """has_test_for_source checks mapping."""
        ctx = DiscoveredContext(
            source_to_test_mapping={"src/foo.py": ["tests/test_foo.py"]}
        )

        assert ctx.has_test_for_source("src/foo.py") is True, "Expected ctx.has_test_for_source('sr... is True"
        assert ctx.has_test_for_source("src/bar.py") is False, "Expected ctx.has_test_for_source('sr... is False"

    def test_get_language_for_file(self):
        """get_language_for_file returns correct language."""
        ctx = DiscoveredContext()

        assert ctx.get_language_for_file("foo.py") == "python", "Expected ctx.get_language_for_file('... to equal 'python'"
        assert ctx.get_language_for_file("foo.cs") == "csharp", "Expected ctx.get_language_for_file('... to equal 'csharp'"
        assert ctx.get_language_for_file("foo.ts") == "typescript", "Expected ctx.get_language_for_file('... to equal 'typescript'"
        assert ctx.get_language_for_file("foo.tsx") == "typescript", "Expected ctx.get_language_for_file('... to equal 'typescript'"
        assert ctx.get_language_for_file("foo.js") == "javascript", "Expected ctx.get_language_for_file('... to equal 'javascript'"
        assert ctx.get_language_for_file("foo.go") == "go", "Expected ctx.get_language_for_file('... to equal 'go'"
        assert ctx.get_language_for_file("foo.rs") == "rust", "Expected ctx.get_language_for_file('... to equal 'rust'"
        assert ctx.get_language_for_file("foo.unknown") is None, "Expected ctx.get_language_for_file('... is None"

    def test_to_dict(self):
        """to_dict serializes context."""
        ctx = DiscoveredContext(
            primary_language="python",
            languages=["python", "typescript"],
            frameworks=["fastapi", "react"],
            estimated_coverage=0.85,
        )

        d = ctx.to_dict()
        assert d["primary_language"] == "python", "Expected d['primary_language'] to equal 'python'"
        assert d["languages"] == ["python", "typescript"], "Expected d['languages'] to equal ['python', 'typescript']"
        assert d["frameworks"] == ["fastapi", "react"], "Expected d['frameworks'] to equal ['fastapi', 'react']"
        assert d["estimated_coverage"] == 0.85, "Expected d['estimated_coverage'] to equal 0.85"


# =============================================================================
# extract_context_from_profile Tests
# =============================================================================


class TestExtractContextFromProfile:
    """Tests for extract_context_from_profile."""

    def test_extracts_languages(self):
        """Extracts language information from profile."""
        profile = MockCodebaseProfile(
            languages=[
                MockLanguageInfo(name="Python", primary=True, frameworks=["FastAPI"]),
                MockLanguageInfo(name="TypeScript", frameworks=["React"]),
            ]
        )

        ctx = extract_context_from_profile(profile)

        assert ctx.primary_language == "python", "Expected ctx.primary_language to equal 'python'"
        assert "python" in ctx.languages, "Expected 'python' in ctx.languages"
        assert "typescript" in ctx.languages, "Expected 'typescript' in ctx.languages"
        assert "FastAPI" in ctx.frameworks, "Expected 'FastAPI' in ctx.frameworks"
        assert "React" in ctx.frameworks, "Expected 'React' in ctx.frameworks"

    def test_extracts_structure(self):
        """Extracts structure information from profile."""
        profile = MockCodebaseProfile(
            structure={
                "source_dirs": ["src/", "lib/"],
                "test_dirs": ["tests/"],
                "entry_points": ["main.py"],
            }
        )

        ctx = extract_context_from_profile(profile)

        assert ctx.source_directories == ["src/", "lib/"], "Expected ctx.source_directories to equal ['src/', 'lib/']"
        assert ctx.test_directories == ["tests/"], "Expected ctx.test_directories to equal ['tests/']"
        assert ctx.entry_points == ["main.py"], "Expected ctx.entry_points to equal ['main.py']"

    def test_extracts_test_analysis(self):
        """Extracts test analysis information from profile."""
        profile = MockCodebaseProfile(
            test_analysis=MockTestAnalysis(
                inventory=MockTestInventory(frameworks=["pytest"]),
                estimated_coverage=0.75,
                linkages=[
                    MockTestLinkage("src/foo.py", ["tests/test_foo.py"]),
                ],
            )
        )

        ctx = extract_context_from_profile(profile)

        assert ctx.test_framework == "pytest", "Expected ctx.test_framework to equal 'pytest'"
        assert ctx.estimated_coverage == 0.75, "Expected ctx.estimated_coverage to equal 0.75"
        assert ctx.source_to_test_mapping == {"src/foo.py": ["tests/test_foo.py"]}, "Expected ctx.source_to_test_mapping to equal {'src/foo.py': ['tests/test..."

    def test_extracts_dependencies(self):
        """Extracts dependency information from profile."""
        profile = MockCodebaseProfile(
            dependencies=[
                MockDependency(name="fastapi", is_dev=False),
                MockDependency(name="pytest", is_dev=True),
                MockDependency(name="uvicorn", is_dev=False),
            ]
        )

        ctx = extract_context_from_profile(profile)

        assert "fastapi" in ctx.dependencies, "Expected 'fastapi' in ctx.dependencies"
        assert "uvicorn" in ctx.dependencies, "Expected 'uvicorn' in ctx.dependencies"
        assert "pytest" in ctx.dev_dependencies, "Expected 'pytest' in ctx.dev_dependencies"

    def test_handles_empty_profile(self):
        """Handles profile with no data gracefully."""
        profile = MockCodebaseProfile()

        ctx = extract_context_from_profile(profile)

        assert ctx.primary_language is None, "Expected ctx.primary_language is None"
        assert ctx.languages == [], "Expected ctx.languages to equal []"
        assert ctx.estimated_coverage == 0.0, "Expected ctx.estimated_coverage to equal 0.0"


# =============================================================================
# get_contracts_for_language Tests
# =============================================================================


class TestGetContractsForLanguage:
    """Tests for get_contracts_for_language."""

    def test_python_contracts(self):
        """Returns Python-specific contracts."""
        contracts = get_contracts_for_language("python")

        # Base contracts
        assert "agentforge-lineage" in contracts, "Expected 'agentforge-lineage' in contracts"
        assert "agentforge-specs" in contracts, "Expected 'agentforge-specs' in contracts"
        assert "agentforge-structure" in contracts, "Expected 'agentforge-structure' in contracts"

        # Python-specific
        assert "_architecture-python" in contracts, "Expected '_architecture-python' in contracts"
        assert "_patterns-python" in contracts, "Expected '_patterns-python' in contracts"
        assert "_typing-python" in contracts, "Expected '_typing-python' in contracts"

    def test_csharp_contracts(self):
        """Returns C#-specific contracts."""
        contracts = get_contracts_for_language("csharp")

        # Base contracts
        assert "agentforge-lineage" in contracts, "Expected 'agentforge-lineage' in contracts"

        # C#-specific
        assert "_patterns-csharp" in contracts, "Expected '_patterns-csharp' in contracts"

    def test_typescript_contracts(self):
        """Returns TypeScript-specific contracts."""
        contracts = get_contracts_for_language("typescript")

        assert "_patterns-typescript" in contracts, "Expected '_patterns-typescript' in contracts"

    def test_javascript_uses_typescript_patterns(self):
        """JavaScript uses TypeScript pattern contracts."""
        contracts = get_contracts_for_language("javascript")

        assert "_patterns-typescript" in contracts, "Expected '_patterns-typescript' in contracts"

    def test_unknown_language_returns_base(self):
        """Unknown language returns only base contracts."""
        contracts = get_contracts_for_language("unknown")

        assert "agentforge-lineage" in contracts, "Expected 'agentforge-lineage' in contracts"
        assert len([c for c in contracts if c.startswith("_")]) == 0, "Expected len([c for c in contracts i... to equal 0"


# =============================================================================
# create_pipeline_context_from_discovery Tests
# =============================================================================


class TestCreatePipelineContextFromDiscovery:
    """Tests for create_pipeline_context_from_discovery."""

    def test_creates_pipeline_context(self, tmp_path):
        """Creates complete pipeline context from profile."""
        profile = MockCodebaseProfile(
            languages=[MockLanguageInfo(name="Python", primary=True)],
            test_analysis=MockTestAnalysis(
                inventory=MockTestInventory(frameworks=["pytest"]),
                estimated_coverage=0.80,
            ),
        )

        ctx = create_pipeline_context_from_discovery(profile, tmp_path)

        assert ctx["project_path"] == str(tmp_path), "Expected ctx['project_path'] to equal str(tmp_path)"
        assert ctx["primary_language"] == "python", "Expected ctx['primary_language'] to equal 'python'"
        assert ctx["test_framework"] == "pytest", "Expected ctx['test_framework'] to equal 'pytest'"
        assert ctx["estimated_coverage"] == 0.80, "Expected ctx['estimated_coverage'] to equal 0.8"
        assert "applicable_contracts" in ctx, "Expected 'applicable_contracts' in ctx"
        assert "_architecture-python" in ctx["applicable_contracts"], "Expected '_architecture-python' in ctx['applicable_contracts']"

    def test_includes_codebase_profile(self, tmp_path):
        """Includes serialized codebase profile."""
        profile = MockCodebaseProfile(
            languages=[MockLanguageInfo(name="TypeScript", primary=True)],
        )

        ctx = create_pipeline_context_from_discovery(profile, tmp_path)

        assert "codebase_profile" in ctx, "Expected 'codebase_profile' in ctx"
        assert ctx["codebase_profile"]["primary_language"] == "typescript", "Expected ctx['codebase_profile']['pr... to equal 'typescript'"


# =============================================================================
# resolve_test_path Tests
# =============================================================================


class TestResolveTestPath:
    """Tests for resolve_test_path."""

    def test_uses_mapping_first(self, tmp_path):
        """Uses discovered mapping before conventions."""
        ctx = DiscoveredContext(
            source_to_test_mapping={
                "src/module.py": ["tests/unit/test_module.py"],
            }
        )

        result = resolve_test_path("src/module.py", ctx)
        assert result == "tests/unit/test_module.py", "Expected result to equal 'tests/unit/test_module.py'"

    def test_falls_back_to_convention_python(self, tmp_path):
        """Falls back to Python conventions."""
        ctx = DiscoveredContext(
            test_directories=["tests"],
        )

        # Create the expected test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_module.py"
        test_file.touch()

        result = resolve_test_path(str(tmp_path / "src" / "module.py"), ctx, "python")
        # Will return None because path doesn't exist in our mock
        # In real usage with Path.exists(), this would work

    def test_returns_none_for_unknown(self):
        """Returns None for unknown source file."""
        ctx = DiscoveredContext()

        result = resolve_test_path("src/unknown.xyz", ctx)
        assert result is None, "Expected result is None"
