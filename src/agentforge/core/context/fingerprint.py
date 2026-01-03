# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: fingerprint-v1
# @component_id: fingerprint-generator
# @test_path: tests/unit/context/test_fingerprint.py

"""
Project Fingerprint Generator
=============================

Generates compact, high-signal project context (~500 tokens) that:
- Identifies project language, framework, patterns
- Caches per project, invalidates on significant changes
- Adds task-specific constraints at runtime
- Replaces verbose static system prompts

Usage:
    ```python
    generator = FingerprintGenerator(project_path)

    # Base fingerprint (cached)
    fingerprint = generator.generate()

    # With task context (not cached, extends base)
    fingerprint = generator.with_task_context(
        task_type="fix_violation",
        constraints={"correctness_first": True},
        success_criteria=["Tests pass"],
    )

    # Get compact YAML for LLM context
    context_yaml = fingerprint.to_context_yaml()
    ```
"""

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import BaseModel, Field


class ProjectIdentity(BaseModel):
    """Basic project identification."""

    name: str
    path: str
    content_hash: str = Field(description="For cache invalidation")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TechnicalProfile(BaseModel):
    """Technical characteristics of the project."""

    language: str
    version: str | None = None
    frameworks: list[str] = Field(default_factory=list)
    build_system: str | None = None
    test_framework: str = "unknown"


class DetectedPatterns(BaseModel):
    """Code patterns detected in the project."""

    architecture: str | None = None  # clean_architecture, mvc, etc.
    naming: str = "unknown"  # snake_case, camelCase
    imports: str = "unknown"  # absolute, relative
    error_handling: str = "unknown"  # exceptions, result_types
    docstrings: str = "unknown"  # google, numpy, sphinx


class ProjectStructure(BaseModel):
    """Project directory structure."""

    source_root: str = "src"
    test_root: str = "tests"
    config_files: list[str] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)


class ProjectFingerprint(BaseModel):
    """
    Complete project fingerprint for context inclusion.

    Target: ~500 tokens when serialized to YAML.
    """

    identity: ProjectIdentity
    technical: TechnicalProfile
    patterns: DetectedPatterns
    structure: ProjectStructure

    # Task-specific (added at runtime, not cached)
    task_type: str | None = None
    task_constraints: dict[str, Any] = Field(default_factory=dict)
    success_criteria: list[str] = Field(default_factory=list)

    def to_context_yaml(self) -> str:
        """
        Serialize to compact YAML for context inclusion.

        Only includes non-empty, relevant fields.
        """
        output: dict[str, Any] = {}

        # Project section (always included)
        output["project"] = {
            "name": self.identity.name,
            "language": self.technical.language,
        }
        if self.technical.frameworks:
            output["project"]["framework"] = ", ".join(self.technical.frameworks)
        if self.technical.version:
            output["project"]["version"] = self.technical.version

        # Patterns section (only non-unknown values)
        patterns: dict[str, str] = {}
        if self.patterns.architecture:
            patterns["architecture"] = self.patterns.architecture
        if self.patterns.naming != "unknown":
            patterns["naming"] = self.patterns.naming
        if self.patterns.docstrings != "unknown":
            patterns["docstrings"] = self.patterns.docstrings
        if patterns:
            output["patterns"] = patterns

        # Task constraints (if present)
        if self.task_constraints:
            output["constraints"] = self.task_constraints

        # Success criteria (if present)
        if self.success_criteria:
            output["success"] = self.success_criteria

        return yaml.dump(output, default_flow_style=False, sort_keys=False)

    def estimate_tokens(self) -> int:
        """Estimate token count (chars / 4)."""
        return len(self.to_context_yaml()) // 4

    def with_task_context(
        self,
        task_type: str,
        constraints: dict[str, Any],
        success_criteria: list[str],
    ) -> "ProjectFingerprint":
        """
        Create a copy with task-specific context.

        Does not modify the cached base fingerprint.
        """
        return ProjectFingerprint(
            identity=self.identity,
            technical=self.technical,
            patterns=self.patterns,
            structure=self.structure,
            task_type=task_type,
            task_constraints=constraints,
            success_criteria=success_criteria,
        )


class FingerprintGenerator:
    """
    Generates and caches project fingerprints.

    Detection strategies:
    1. Config files (pyproject.toml, package.json, etc.)
    2. Directory structure
    3. Code analysis (imports, patterns)
    """

    # Class-level cache
    _cache: ClassVar[dict[str, ProjectFingerprint]] = {}
    _cache_hashes: ClassVar[dict[str, str]] = {}

    # Files that trigger cache invalidation
    SIGNIFICANT_FILES = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "package.json",
        "tsconfig.json",
        "Cargo.toml",
        "go.mod",
        ".agentforge/AGENT.md",
    ]

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    def generate(self, force_refresh: bool = False) -> ProjectFingerprint:
        """
        Generate or retrieve cached fingerprint.

        Args:
            force_refresh: Force regeneration even if cached

        Returns:
            ProjectFingerprint for this project
        """
        project_key = str(self.project_path)
        current_hash = self._compute_content_hash()

        # Check cache validity
        if not force_refresh and project_key in self._cache:
            if self._cache_hashes.get(project_key) == current_hash:
                return self._cache[project_key]

        # Generate new fingerprint
        fingerprint = ProjectFingerprint(
            identity=self._detect_identity(current_hash),
            technical=self._detect_technical(),
            patterns=self._detect_patterns(),
            structure=self._detect_structure(),
        )

        # Cache it
        self._cache[project_key] = fingerprint
        self._cache_hashes[project_key] = current_hash

        return fingerprint

    def with_task_context(
        self,
        task_type: str,
        constraints: dict[str, Any],
        success_criteria: list[str],
    ) -> ProjectFingerprint:
        """
        Get fingerprint with task-specific context.

        This is the primary method for use in execution.
        """
        base = self.generate()
        return base.with_task_context(task_type, constraints, success_criteria)

    def _compute_content_hash(self) -> str:
        """
        Compute hash of significant files for cache invalidation.

        Includes file content and modification time.
        """
        hasher = hashlib.sha256()

        for filename in self.SIGNIFICANT_FILES:
            filepath = self.project_path / filename
            if filepath.exists():
                # Include content
                hasher.update(filepath.read_bytes())
                # Include mtime for change detection
                hasher.update(str(filepath.stat().st_mtime).encode())

        return hasher.hexdigest()[:16]

    def _detect_identity(self, content_hash: str) -> ProjectIdentity:
        """Detect project identity."""
        return ProjectIdentity(
            name=self.project_path.name,
            path=str(self.project_path),
            content_hash=content_hash,
        )

    def _detect_python(self) -> TechnicalProfile | None:
        """Detect Python project characteristics."""
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            build_system = self._detect_python_build_system(content)
            frameworks = self._detect_python_frameworks(content)
            test_framework = "pytest" if "pytest" in content else "unknown"
            version_match = re.search(
                r'(?:requires-python|python_requires)\s*=\s*"[><=]*(\d+\.\d+)', content
            )
            return TechnicalProfile(
                language="python", version=version_match.group(1) if version_match else None,
                frameworks=frameworks, build_system=build_system, test_framework=test_framework,
            )
        if (self.project_path / "setup.py").exists():
            test_framework = "pytest" if (self.project_path / "tests").exists() else "unknown"
            return TechnicalProfile(
                language="python", version=None, frameworks=[],
                build_system="setuptools", test_framework=test_framework,
            )
        return None

    def _detect_python_build_system(self, content: str) -> str | None:
        """Detect Python build system from pyproject.toml content."""
        if "hatchling" in content or "[tool.hatch" in content:
            return "hatch"
        if "poetry" in content or "[tool.poetry" in content:
            return "poetry"
        if "setuptools" in content:
            return "setuptools"
        return None

    def _detect_python_frameworks(self, content: str) -> list[str]:
        """Detect Python frameworks from pyproject.toml content."""
        frameworks = []
        if "pytest" in content:
            frameworks.append("pytest")
        for pattern in ("pydantic", "fastapi", "django", "flask", "click", "typer"):
            if pattern in content.lower() and pattern not in frameworks:
                frameworks.append(pattern)
        return frameworks

    def _detect_node(self) -> TechnicalProfile | None:
        """Detect Node.js/TypeScript project characteristics."""
        package_json = self.project_path / "package.json"
        if not package_json.exists():
            return None
        content = package_json.read_text()
        language = "typescript" if (self.project_path / "tsconfig.json").exists() else "javascript"
        test_framework = "jest" if "jest" in content else ("mocha" if "mocha" in content else "unknown")
        frameworks = [f for f in ("react", "express", "next") if f in content]
        return TechnicalProfile(
            language=language, version=None, frameworks=frameworks,
            build_system="npm", test_framework=test_framework,
        )

    def _detect_simple_language(self) -> TechnicalProfile | None:
        """Detect C#, Rust, or Go projects."""
        if list(self.project_path.glob("*.csproj")):
            return TechnicalProfile(
                language="csharp", version=None, frameworks=[],
                build_system="dotnet", test_framework="xunit",
            )
        if (self.project_path / "Cargo.toml").exists():
            return TechnicalProfile(
                language="rust", version=None, frameworks=[],
                build_system="cargo", test_framework="cargo test",
            )
        if (self.project_path / "go.mod").exists():
            return TechnicalProfile(
                language="go", version=None, frameworks=[],
                build_system="go", test_framework="go test",
            )
        return None

    def _detect_technical(self) -> TechnicalProfile:
        """Detect technical characteristics."""
        # Try each language detector in order
        for detector in (self._detect_python, self._detect_node, self._detect_simple_language):
            if profile := detector():
                return profile
        return TechnicalProfile(
            language="unknown", version=None, frameworks=[],
            build_system=None, test_framework="unknown",
        )

    def _detect_patterns(self) -> DetectedPatterns:
        """Detect code patterns from source files."""
        patterns = DetectedPatterns()

        # Check for architecture patterns
        src_dir = self.project_path / "src"
        if src_dir.exists():
            subdirs = [d.name for d in src_dir.iterdir() if d.is_dir()]

            if "domain" in subdirs and "infrastructure" in subdirs:
                patterns.architecture = "clean_architecture"
            elif "models" in subdirs and "views" in subdirs:
                patterns.architecture = "mvc"
            elif "handlers" in subdirs and "services" in subdirs:
                patterns.architecture = "hexagonal"

        # Sample source files for code patterns
        py_files = list(self.project_path.glob("src/**/*.py"))[:10]
        if py_files:
            patterns.naming = "snake_case"  # Python convention

            for py_file in py_files:
                try:
                    content = py_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                # Import style
                if re.search(r"from\s+src\.", content) or re.search(
                    r"from\s+\w+\.", content
                ):
                    patterns.imports = "absolute"
                elif re.search(r"from\s+\.", content):
                    patterns.imports = "relative"

                # Docstring style
                if '"""' in content:
                    if re.search(r"Args:\s*\n", content):
                        patterns.docstrings = "google"
                    elif re.search(r"Parameters\s*\n\s*-+", content):
                        patterns.docstrings = "numpy"
                    elif re.search(r":param\s+", content):
                        patterns.docstrings = "sphinx"

                # Error handling
                if "raise " in content:
                    patterns.error_handling = "exceptions"
                elif "Result[" in content or "Either[" in content:
                    patterns.error_handling = "result_types"

        return patterns

    def _detect_structure(self) -> ProjectStructure:
        """Detect project directory structure."""
        source_root = "src"
        test_root = "tests"
        config_files: list[str] = []
        entry_points: list[str] = []

        # Find source root
        for candidate in ["src", "lib", "app", "source"]:
            if (self.project_path / candidate).is_dir():
                source_root = candidate
                break

        # Find test root
        for candidate in ["tests", "test", "spec", "specs"]:
            if (self.project_path / candidate).is_dir():
                test_root = candidate
                break

        # Find config files
        config_patterns = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "package.json",
            "tsconfig.json",
            "Cargo.toml",
            "go.mod",
            ".agentforge/*.yaml",
            ".agentforge/*.md",
        ]
        for pattern in config_patterns:
            for f in self.project_path.glob(pattern):
                rel_path = str(f.relative_to(self.project_path))
                if rel_path not in config_files:
                    config_files.append(rel_path)

        # Find entry points (check root and common locations)
        entry_patterns = [
            "main.py",
            "__main__.py",
            "cli.py",
            "app.py",
            "index.js",
            "index.ts",
            "main.go",
            "main.rs",
        ]

        # Search locations: root, source_root, and common directories
        search_dirs = [
            self.project_path,
            self.project_path / source_root,
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in entry_patterns:
                entry_file = search_dir / pattern
                if entry_file.exists():
                    rel_path = str(entry_file.relative_to(self.project_path))
                    # Skip files in test directories (but not files that just have "test" in path)
                    if rel_path.startswith("test") or "/test" in rel_path:
                        continue
                    if rel_path not in entry_points and len(entry_points) < 5:
                        entry_points.append(rel_path)

        return ProjectStructure(
            source_root=source_root,
            test_root=test_root,
            config_files=config_files[:10],  # Limit
            entry_points=entry_points[:5],  # Limit
        )

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached fingerprints."""
        cls._cache.clear()
        cls._cache_hashes.clear()
