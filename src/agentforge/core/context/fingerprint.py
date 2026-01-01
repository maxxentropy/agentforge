# @spec_file: specs/minimal-context-architecture/03-fingerprint.yaml
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class ProjectIdentity(BaseModel):
    """Basic project identification."""

    name: str
    path: str
    content_hash: str = Field(description="For cache invalidation")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TechnicalProfile(BaseModel):
    """Technical characteristics of the project."""

    language: str
    version: Optional[str] = None
    frameworks: List[str] = Field(default_factory=list)
    build_system: Optional[str] = None
    test_framework: str = "unknown"


class DetectedPatterns(BaseModel):
    """Code patterns detected in the project."""

    architecture: Optional[str] = None  # clean_architecture, mvc, etc.
    naming: str = "unknown"  # snake_case, camelCase
    imports: str = "unknown"  # absolute, relative
    error_handling: str = "unknown"  # exceptions, result_types
    docstrings: str = "unknown"  # google, numpy, sphinx


class ProjectStructure(BaseModel):
    """Project directory structure."""

    source_root: str = "src"
    test_root: str = "tests"
    config_files: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)


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
    task_type: Optional[str] = None
    task_constraints: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: List[str] = Field(default_factory=list)

    def to_context_yaml(self) -> str:
        """
        Serialize to compact YAML for context inclusion.

        Only includes non-empty, relevant fields.
        """
        output: Dict[str, Any] = {}

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
        patterns: Dict[str, str] = {}
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
        constraints: Dict[str, Any],
        success_criteria: List[str],
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
    _cache: ClassVar[Dict[str, ProjectFingerprint]] = {}
    _cache_hashes: ClassVar[Dict[str, str]] = {}

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
        constraints: Dict[str, Any],
        success_criteria: List[str],
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

    def _detect_technical(self) -> TechnicalProfile:
        """Detect technical characteristics."""
        language = "unknown"
        version: Optional[str] = None
        frameworks: List[str] = []
        build_system: Optional[str] = None
        test_framework = "unknown"

        # Python detection
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            language = "python"
            content = pyproject.read_text()

            # Build system
            if "hatchling" in content or "[tool.hatch" in content:
                build_system = "hatch"
            elif "poetry" in content or "[tool.poetry" in content:
                build_system = "poetry"
            elif "setuptools" in content:
                build_system = "setuptools"

            # Test framework
            if "pytest" in content:
                test_framework = "pytest"
                frameworks.append("pytest")

            # Frameworks
            framework_patterns = [
                ("pydantic", "pydantic"),
                ("fastapi", "fastapi"),
                ("django", "django"),
                ("flask", "flask"),
                ("click", "click"),
                ("typer", "typer"),
            ]
            for pattern, name in framework_patterns:
                if pattern in content.lower():
                    if name not in frameworks:
                        frameworks.append(name)

            # Python version (matches requires-python = ">=3.11" or python_requires=">=3.11")
            version_match = re.search(
                r'(?:requires-python|python_requires)\s*=\s*"[><=]*(\d+\.\d+)',
                content,
            )
            if version_match:
                version = version_match.group(1)

        # setup.py fallback
        elif (self.project_path / "setup.py").exists():
            language = "python"
            build_system = "setuptools"
            if (self.project_path / "tests").exists():
                test_framework = "pytest"

        # Node.js detection
        package_json = self.project_path / "package.json"
        if package_json.exists() and language == "unknown":
            content = package_json.read_text()

            if (self.project_path / "tsconfig.json").exists():
                language = "typescript"
            else:
                language = "javascript"

            build_system = "npm"

            # Test framework
            if "jest" in content:
                test_framework = "jest"
            elif "mocha" in content:
                test_framework = "mocha"

            # Frameworks
            if "react" in content:
                frameworks.append("react")
            if "express" in content:
                frameworks.append("express")
            if "next" in content:
                frameworks.append("next")

        # C# detection
        csproj_files = list(self.project_path.glob("*.csproj"))
        if csproj_files and language == "unknown":
            language = "csharp"
            build_system = "dotnet"
            test_framework = "xunit"

        # Rust detection
        if (self.project_path / "Cargo.toml").exists() and language == "unknown":
            language = "rust"
            build_system = "cargo"
            test_framework = "cargo test"

        # Go detection
        if (self.project_path / "go.mod").exists() and language == "unknown":
            language = "go"
            build_system = "go"
            test_framework = "go test"

        return TechnicalProfile(
            language=language,
            version=version,
            frameworks=frameworks,
            build_system=build_system,
            test_framework=test_framework,
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
        config_files: List[str] = []
        entry_points: List[str] = []

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
