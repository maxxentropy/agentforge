# Implementation Spec Part 3: Project Fingerprint

## 4. Fingerprint Generator Implementation

### 4.1 Purpose

Generate compact, high-signal project context (~500 tokens) that:
- Identifies project language, framework, patterns
- Caches per project, invalidates on significant changes
- Adds task-specific constraints at runtime
- Replaces verbose static system prompts

### 4.2 Models

```python
# src/agentforge/core/context/fingerprint.py

from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib
import re
import yaml


class ProjectIdentity(BaseModel):
    """Basic project identification."""
    name: str
    path: str
    content_hash: str = Field(description="For cache invalidation")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


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
        output = {}
        
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
        patterns = {}
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
```

### 4.3 Generator Implementation

```python
# src/agentforge/core/context/fingerprint.py (continued)

class FingerprintGenerator:
    """
    Generates and caches project fingerprints.
    
    Detection strategies:
    1. Config files (pyproject.toml, package.json, etc.)
    2. Directory structure
    3. Code analysis (imports, patterns)
    """
    
    # Class-level cache
    _cache: Dict[str, ProjectFingerprint] = {}
    _cache_hashes: Dict[str, str] = {}
    
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
        version = None
        frameworks: List[str] = []
        build_system = None
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
            
            # Python version
            version_match = re.search(
                r'python\s*[><=]+\s*"?(\d+\.\d+)',
                content
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
            test_framework = "xunit"  # Common default
        
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
                    content = py_file.read_text(encoding='utf-8')
                except:
                    continue
                
                # Import style
                if re.search(r'from\s+src\.', content) or re.search(r'from\s+\w+\.', content):
                    patterns.imports = "absolute"
                elif re.search(r'from\s+\.', content):
                    patterns.imports = "relative"
                
                # Docstring style
                if '"""' in content:
                    if re.search(r'Args:\s*\n', content):
                        patterns.docstrings = "google"
                    elif re.search(r'Parameters\s*\n\s*-+', content):
                        patterns.docstrings = "numpy"
                    elif re.search(r':param\s+', content):
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
            "pyproject.toml", "setup.py", "setup.cfg",
            "package.json", "tsconfig.json",
            "Cargo.toml", "go.mod",
            ".agentforge/*.yaml", ".agentforge/*.md",
        ]
        for pattern in config_patterns:
            for f in self.project_path.glob(pattern):
                rel_path = str(f.relative_to(self.project_path))
                if rel_path not in config_files:
                    config_files.append(rel_path)
        
        # Find entry points
        entry_patterns = [
            "main.py", "__main__.py", "cli.py", "app.py",
            "index.js", "index.ts", "main.go", "main.rs",
        ]
        for pattern in entry_patterns:
            for f in self.project_path.glob(f"**/{pattern}"):
                if "test" not in str(f).lower():
                    rel_path = str(f.relative_to(self.project_path))
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
```

### 4.4 Tests

```python
# tests/unit/context/test_fingerprint.py

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentforge.core.context.fingerprint import (
    ProjectFingerprint,
    FingerprintGenerator,
    TechnicalProfile,
    DetectedPatterns,
)


class TestProjectFingerprint:
    """Tests for ProjectFingerprint model."""
    
    def test_to_context_yaml_minimal(self):
        """Test YAML output with minimal data."""
        from agentforge.core.context.fingerprint import ProjectIdentity, ProjectStructure
        
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
        from agentforge.core.context.fingerprint import ProjectIdentity, ProjectStructure
        
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
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        from agentforge.core.context.fingerprint import ProjectIdentity, ProjectStructure
        
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
        from agentforge.core.context.fingerprint import ProjectIdentity, ProjectStructure
        
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
        pyproject.write_text("""
[project]
name = "test-project"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0.0",
    "pytest>=7.0.0",
]
""")
        
        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()
        
        assert fp.technical.language == "python"
        assert "pydantic" in fp.technical.frameworks
        assert "pytest" in fp.technical.frameworks
        assert fp.technical.version == "3.11"
    
    def test_detect_node_project(self, temp_project):
        """Detect Node.js project from package.json."""
        package_json = temp_project / "package.json"
        package_json.write_text("""
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
""")
        
        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()
        
        assert fp.technical.language == "javascript"
        assert "react" in fp.technical.frameworks
        assert "express" in fp.technical.frameworks
        assert fp.technical.test_framework == "jest"
    
    def test_detect_typescript_project(self, temp_project):
        """Detect TypeScript project."""
        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "tsconfig.json").write_text('{}')
        
        generator = FingerprintGenerator(temp_project)
        fp = generator.generate()
        
        assert fp.technical.language == "typescript"
    
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
    
    def test_cache_hit(self, temp_project):
        """Test that cache is used on second call."""
        (temp_project / "pyproject.toml").write_text('[project]\nname = "test"')
        
        generator = FingerprintGenerator(temp_project)
        
        fp1 = generator.generate()
        fp2 = generator.generate()
        
        # Same object (cached)
        assert fp1 is fp2
    
    def test_cache_invalidation(self, temp_project):
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
    
    def test_with_task_context(self, temp_project):
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
```

### 4.5 Integration Points

```python
# Usage in executor

class MinimalContextExecutor:
    def __init__(self, project_path: Path, task_type: str, ...):
        ...
        # Generate fingerprint
        self.fingerprint_generator = FingerprintGenerator(project_path)
    
    def execute_step(self, task: Task, ...):
        # Get fingerprint with task context
        fingerprint = self.fingerprint_generator.with_task_context(
            task_type=self.task_type,
            constraints={
                "correctness_first": True,
                "test_verification": "required",
                "auto_revert": "on_test_failure",
            },
            success_criteria=task.success_criteria,
        )
        
        # Include in context
        context["fingerprint"] = fingerprint.to_context_yaml()
```

---

**[Saved Part 3 - Fingerprint Implementation]**

*Continue to Part 4: Context Templates...*
