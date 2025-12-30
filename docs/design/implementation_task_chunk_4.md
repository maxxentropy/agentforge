# Implementation Task: Chunk 4 - Brownfield Discovery System

## Overview

Implement the brownfield discovery system as specified in `docs/specs/chunk4-brownfield-discovery/specification.md`. This system analyzes existing codebases and reverse-engineers the artifacts that would have been produced through the greenfield workflow, implementing the **Artifact Parity Principle**.

**Read the full specification first:** `docs/specs/chunk4-brownfield-discovery/specification.md`

---

## Architecture Summary

```
tools/discovery/
├── __init__.py                 # Public exports
├── domain.py                   # Domain entities and types
├── manager.py                  # DiscoveryManager orchestration
├── providers/
│   ├── __init__.py
│   ├── base.py                 # LanguageProvider abstract base
│   ├── python_provider.py      # Python-specific analysis
│   └── dotnet_provider.py      # .NET-specific analysis (Phase 7)
├── analyzers/
│   ├── __init__.py
│   ├── structure.py            # StructureAnalyzer
│   ├── patterns.py             # PatternExtractor
│   ├── architecture.py         # ArchitectureMapper
│   ├── conventions.py          # ConventionInferrer
│   └── tests.py                # TestGapAnalyzer
└── generators/
    ├── __init__.py
    └── profile.py              # ProfileGenerator

cli/commands/discover.py        # CLI command implementation

Output:
.agentforge/
├── codebase_profile.yaml       # Primary output (enhanced)
├── architecture.yaml           # As-built architecture (optional)
└── specs/                      # As-built specifications (optional)
    └── {feature}.yaml
```

---

## Phase 1: Domain Model & Types

Create the domain entities that represent discovery concepts.

### 1.1 `tools/discovery/domain.py`

```python
"""
Brownfield Discovery Domain Model
=================================

Pure domain objects for discovery operations. No I/O operations.
These entities represent detected patterns, conventions, and structure.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class DetectionSource(Enum):
    """How a value was determined."""
    AUTO_DETECTED = "auto-detected"
    HUMAN_CURATED = "human-curated"
    INFERRED = "inferred"


class ConfidenceLevel(Enum):
    """Confidence classification for detections."""
    HIGH = "high"       # >= 0.9
    MEDIUM = "medium"   # 0.6 - 0.9
    LOW = "low"         # 0.3 - 0.6
    UNCERTAIN = "uncertain"  # < 0.3
    
    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        """Convert numeric score to confidence level."""
        if score >= 0.9:
            return cls.HIGH
        elif score >= 0.6:
            return cls.MEDIUM
        elif score >= 0.3:
            return cls.LOW
        else:
            return cls.UNCERTAIN


class DiscoveryPhase(Enum):
    """Phases of discovery process."""
    LANGUAGE = "language"
    STRUCTURE = "structure"
    PATTERNS = "patterns"
    ARCHITECTURE = "architecture"
    CONVENTIONS = "conventions"
    TESTS = "tests"


class OnboardingStatus(Enum):
    """Status of module onboarding."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ANALYZED = "analyzed"
    FAILED = "failed"


@dataclass
class Detection:
    """Base class for all detections with confidence tracking."""
    confidence: float
    source: DetectionSource = DetectionSource.AUTO_DETECTED
    evidence: Optional[Dict[str, Any]] = None
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_score(self.confidence)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "confidence": self.confidence,
            "source": self.source.value,
        }
        if self.evidence:
            result["evidence"] = self.evidence
        return result


@dataclass
class LanguageInfo(Detection):
    """Detected programming language."""
    name: str
    percentage: float
    frameworks: List[str] = field(default_factory=list)
    version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "name": self.name,
            "percentage": self.percentage,
        })
        if self.frameworks:
            result["frameworks"] = self.frameworks
        if self.version:
            result["version"] = self.version
        return result


@dataclass
class ProjectInfo:
    """Information about a detected project."""
    path: Path
    name: str
    language: str
    project_type: str  # "library", "executable", "web", "test"
    framework: Optional[str] = None
    references: List[str] = field(default_factory=list)
    packages: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class LayerInfo(Detection):
    """Detected architectural layer."""
    name: str
    path: str
    purpose: Optional[str] = None
    projects: List[str] = field(default_factory=list)
    allowed_references: List[str] = field(default_factory=list)
    actual_references: List[str] = field(default_factory=list)
    
    @property
    def has_violations(self) -> bool:
        """Check if layer has dependency violations."""
        forbidden = set(self.actual_references) - set(self.allowed_references) - {self.name}
        return len(forbidden) > 0
    
    def get_violations(self) -> List[str]:
        """Get list of forbidden dependencies."""
        forbidden = set(self.actual_references) - set(self.allowed_references) - {self.name}
        return list(forbidden)


@dataclass
class ArchitectureViolation:
    """A detected architecture layer violation."""
    from_layer: str
    to_layer: str
    from_project: Optional[str] = None
    to_project: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    import_statement: Optional[str] = None
    severity: str = "major"


@dataclass
class PatternDetection(Detection):
    """A detected coding pattern."""
    name: str
    detected: bool
    primary: Optional[str] = None  # Primary variant if multiple exist
    examples: List[str] = field(default_factory=list)
    locations: Optional[Dict[str, str]] = None  # e.g., {"commands": "src/Commands/"}
    naming: Optional[str] = None  # e.g., "{Action}{Entity}Command"
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "detected": self.detected,
        })
        if self.primary:
            result["primary"] = self.primary
        if self.examples:
            result["examples"] = self.examples[:5]  # Limit to 5 examples
        if self.locations:
            result["locations"] = self.locations
        if self.naming:
            result["naming"] = self.naming
        return result


@dataclass
class ConventionDetection(Detection):
    """A detected naming or organization convention."""
    name: str
    pattern: str
    consistency: float  # 0.0 to 1.0
    exceptions: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "pattern": self.pattern,
            "consistency": self.consistency,
        })
        if self.exceptions:
            result["exceptions"] = self.exceptions[:10]  # Limit
        if self.alternatives:
            result["alternatives"] = self.alternatives[:3]  # Limit
        return result


@dataclass
class TestInventory:
    """Inventory of tests in the codebase."""
    total_test_files: int = 0
    total_test_methods: int = 0
    frameworks: List[str] = field(default_factory=list)
    categories: Dict[str, int] = field(default_factory=dict)  # unit, integration, e2e


@dataclass 
class TestGap:
    """An identified gap in test coverage."""
    gap_type: str  # "untested_project", "untested_class", "untested_method"
    location: str
    note: Optional[str] = None


@dataclass
class TestAnalysis(Detection):
    """Results of test gap analysis."""
    inventory: TestInventory
    estimated_coverage: float
    gaps: List[TestGap] = field(default_factory=list)
    test_patterns: Optional[Dict[str, str]] = None  # naming, setup, mocking


@dataclass
class DependencyInfo:
    """Information about an external dependency."""
    name: str
    version: str
    source: str  # "nuget", "pypi", "npm"
    is_dev: bool = False
    license: Optional[str] = None
    has_known_issues: bool = False
    issue_details: Optional[str] = None


@dataclass
class DiscoveryMetadata:
    """Metadata about a discovery run."""
    version: str
    run_date: datetime
    run_type: str  # "full", "incremental", "phase"
    duration_ms: int
    phases_completed: List[str]
    repo_root: str


@dataclass
class OnboardingProgress:
    """Tracks incremental onboarding progress."""
    status: OnboardingStatus
    modules: Dict[str, OnboardingStatus] = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        return self.status == OnboardingStatus.ANALYZED


@dataclass
class CodebaseProfile:
    """
    Complete profile of a discovered codebase.
    
    This is the primary output of brownfield discovery.
    """
    schema_version: str
    generated_at: datetime
    discovery_metadata: DiscoveryMetadata
    
    # Language & Framework
    languages: List[LanguageInfo]
    
    # Structure
    structure: Dict[str, Any]  # Flexible structure info
    
    # Patterns
    patterns: Dict[str, PatternDetection]
    
    # Architecture
    architecture: Optional[Dict[str, Any]] = None
    
    # Conventions
    conventions: Optional[Dict[str, Any]] = None
    
    # Tests
    test_analysis: Optional[TestAnalysis] = None
    
    # Dependencies
    dependencies: List[DependencyInfo] = field(default_factory=list)
    
    # Onboarding
    onboarding_progress: Optional[OnboardingProgress] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "discovery_metadata": {
                "version": self.discovery_metadata.version,
                "run_date": self.discovery_metadata.run_date.isoformat(),
                "run_type": self.discovery_metadata.run_type,
                "duration_ms": self.discovery_metadata.duration_ms,
                "phases_completed": self.discovery_metadata.phases_completed,
            },
            "languages": [lang.to_dict() for lang in self.languages],
            "structure": self.structure,
            "patterns": {
                name: pattern.to_dict() 
                for name, pattern in self.patterns.items()
            },
        }
        
        if self.architecture:
            result["architecture"] = self.architecture
        if self.conventions:
            result["conventions"] = self.conventions
        if self.test_analysis:
            result["test_analysis"] = {
                "inventory": {
                    "total_test_files": self.test_analysis.inventory.total_test_files,
                    "total_test_methods": self.test_analysis.inventory.total_test_methods,
                    "frameworks": self.test_analysis.inventory.frameworks,
                    "categories": self.test_analysis.inventory.categories,
                },
                "estimated_coverage": self.test_analysis.estimated_coverage,
                "gaps": [
                    {"type": g.gap_type, "location": g.location, "note": g.note}
                    for g in self.test_analysis.gaps[:20]  # Limit
                ],
            }
        if self.dependencies:
            result["dependencies"] = [
                {
                    "name": d.name,
                    "version": d.version,
                    "source": d.source,
                }
                for d in self.dependencies
            ]
        if self.onboarding_progress:
            result["onboarding_progress"] = {
                "status": self.onboarding_progress.status.value,
                "modules": {
                    k: v.value for k, v in self.onboarding_progress.modules.items()
                },
            }
            
        return result
```

---

## Phase 2: Language Provider Interface

Create the abstract interface that all language providers must implement.

### 2.1 `tools/discovery/providers/__init__.py`

```python
"""
Language Providers for Brownfield Discovery
============================================

Provides language-specific analysis capabilities.
"""

from .base import LanguageProvider
from .python_provider import PythonProvider

__all__ = ["LanguageProvider", "PythonProvider"]
```

### 2.2 `tools/discovery/providers/base.py`

```python
"""
Language Provider Abstract Base
===============================

Defines the interface that all language providers must implement.
Each provider handles language-specific parsing, symbol extraction,
and dependency analysis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Set


@dataclass
class Symbol:
    """A code symbol (class, function, method, etc.)."""
    name: str
    kind: str  # "class", "function", "method", "property", "variable"
    file_path: Path
    line_number: int
    end_line: Optional[int] = None
    parent: Optional[str] = None  # For methods, the class name
    visibility: str = "public"  # "public", "private", "protected"
    signature: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = None
    base_classes: List[str] = None
    return_type: Optional[str] = None
    parameters: List[Dict[str, str]] = None


@dataclass
class Import:
    """An import/using statement."""
    module: str
    names: List[str]  # Specific imports, or ["*"] for star import
    alias: Optional[str] = None
    file_path: Path = None
    line_number: int = 0
    is_relative: bool = False


@dataclass
class Dependency:
    """An external package dependency."""
    name: str
    version: Optional[str] = None
    version_constraint: Optional[str] = None  # ">=1.0", "^2.0", etc.
    is_dev: bool = False
    source: str = "unknown"  # "pypi", "nuget", "npm"


class LanguageProvider(ABC):
    """
    Abstract base class for language-specific analysis.
    
    Implementations provide:
    - Project detection and metadata extraction
    - File parsing and AST access
    - Symbol extraction (classes, methods, etc.)
    - Import analysis
    - Dependency extraction
    """
    
    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name (e.g., 'python', 'csharp')."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> Set[str]:
        """Return supported file extensions (e.g., {'.py', '.pyi'})."""
        pass
    
    @property
    @abstractmethod
    def project_markers(self) -> Set[str]:
        """Return project marker files (e.g., {'pyproject.toml', 'setup.py'})."""
        pass
    
    @abstractmethod
    def detect_project(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Detect if path contains a project of this language.
        
        Args:
            path: Directory to check
            
        Returns:
            Project info dict if detected, None otherwise.
            Dict should include:
            - name: Project name
            - version: Project version (if available)
            - framework: Framework name (if detected)
            - project_file: Path to main project file
        """
        pass
    
    @abstractmethod
    def parse_file(self, path: Path) -> Optional[Any]:
        """
        Parse a source file and return its AST.
        
        Args:
            path: Path to source file
            
        Returns:
            Parsed AST or None if parsing fails
        """
        pass
    
    @abstractmethod
    def extract_symbols(self, path: Path) -> List[Symbol]:
        """
        Extract all symbols from a source file.
        
        Args:
            path: Path to source file
            
        Returns:
            List of Symbol objects
        """
        pass
    
    @abstractmethod
    def get_imports(self, path: Path) -> List[Import]:
        """
        Extract all imports from a source file.
        
        Args:
            path: Path to source file
            
        Returns:
            List of Import objects
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, project_path: Path) -> List[Dependency]:
        """
        Extract dependencies from project configuration.
        
        Args:
            project_path: Path to project root or project file
            
        Returns:
            List of Dependency objects
        """
        pass
    
    def get_source_files(self, root: Path, exclude_patterns: List[str] = None) -> List[Path]:
        """
        Find all source files under root.
        
        Args:
            root: Directory to search
            exclude_patterns: Glob patterns to exclude
            
        Returns:
            List of source file paths
        """
        exclude_patterns = exclude_patterns or []
        exclude_patterns.extend([
            "**/node_modules/**",
            "**/.git/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/bin/**",
            "**/obj/**",
        ])
        
        files = []
        for ext in self.file_extensions:
            for path in root.rglob(f"*{ext}"):
                # Check exclusions
                skip = False
                for pattern in exclude_patterns:
                    if path.match(pattern):
                        skip = True
                        break
                if not skip:
                    files.append(path)
                    
        return sorted(files)
    
    def count_lines(self, path: Path) -> int:
        """Count lines of code in a file."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip() and not line.strip().startswith('#'))
        except Exception:
            return 0
```

---

## Phase 3: Python Provider Implementation

Implement the Python language provider using the ast module.

### 3.1 `tools/discovery/providers/python_provider.py`

```python
"""
Python Language Provider
========================

Provides Python-specific analysis using the ast module.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from .base import LanguageProvider, Symbol, Import, Dependency


class PythonProvider(LanguageProvider):
    """Python language provider using ast module for analysis."""
    
    @property
    def language_name(self) -> str:
        return "python"
    
    @property
    def file_extensions(self) -> Set[str]:
        return {".py", ".pyi"}
    
    @property
    def project_markers(self) -> Set[str]:
        return {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"}
    
    def detect_project(self, path: Path) -> Optional[Dict[str, Any]]:
        """Detect Python project and extract metadata."""
        if not path.is_dir():
            path = path.parent
            
        # Check for project markers
        for marker in self.project_markers:
            marker_path = path / marker
            if marker_path.exists():
                return self._parse_project_file(marker_path)
                
        return None
    
    def _parse_project_file(self, path: Path) -> Dict[str, Any]:
        """Parse project configuration file."""
        result = {
            "name": path.parent.name,
            "version": None,
            "framework": None,
            "project_file": str(path),
        }
        
        if path.name == "pyproject.toml":
            result.update(self._parse_pyproject_toml(path))
        elif path.name == "setup.py":
            result.update(self._parse_setup_py(path))
        elif path.name == "requirements.txt":
            # Detect frameworks from requirements
            frameworks = self._detect_frameworks_from_requirements(path)
            if frameworks:
                result["framework"] = frameworks[0]
                
        return result
    
    def _parse_pyproject_toml(self, path: Path) -> Dict[str, Any]:
        """Parse pyproject.toml for project metadata."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return {}
                
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
                
            project = data.get("project", {})
            result = {
                "name": project.get("name", path.parent.name),
                "version": project.get("version"),
            }
            
            # Detect framework from dependencies
            deps = project.get("dependencies", [])
            frameworks = self._detect_frameworks_from_deps(deps)
            if frameworks:
                result["framework"] = frameworks[0]
                
            return result
        except Exception:
            return {}
    
    def _parse_setup_py(self, path: Path) -> Dict[str, Any]:
        """Parse setup.py for project metadata."""
        try:
            content = path.read_text()
            result = {}
            
            # Extract name
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                result["name"] = name_match.group(1)
                
            # Extract version
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                result["version"] = version_match.group(1)
                
            return result
        except Exception:
            return {}
    
    def _detect_frameworks_from_requirements(self, path: Path) -> List[str]:
        """Detect frameworks from requirements.txt."""
        try:
            content = path.read_text()
            deps = [line.split("==")[0].split(">=")[0].strip().lower() 
                   for line in content.splitlines() if line.strip()]
            return self._detect_frameworks_from_deps(deps)
        except Exception:
            return []
    
    def _detect_frameworks_from_deps(self, deps: List[str]) -> List[str]:
        """Detect frameworks from dependency list."""
        frameworks = []
        deps_lower = [d.lower() if isinstance(d, str) else "" for d in deps]
        
        framework_markers = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "starlette": "Starlette",
            "pytest": "pytest",
            "sqlalchemy": "SQLAlchemy",
            "pydantic": "Pydantic",
        }
        
        for marker, name in framework_markers.items():
            if any(marker in d for d in deps_lower):
                frameworks.append(name)
                
        return frameworks
    
    def parse_file(self, path: Path) -> Optional[ast.AST]:
        """Parse Python file to AST."""
        try:
            content = path.read_text(encoding='utf-8')
            return ast.parse(content, filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            return None
    
    def extract_symbols(self, path: Path) -> List[Symbol]:
        """Extract symbols from Python file."""
        tree = self.parse_file(path)
        if tree is None:
            return []
            
        symbols = []
        
        class SymbolVisitor(ast.NodeVisitor):
            def __init__(self, file_path: Path):
                self.file_path = file_path
                self.current_class = None
                
            def visit_ClassDef(self, node: ast.ClassDef):
                # Get base classes
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(f"{self._get_attr_name(base)}")
                        
                # Get decorators
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                
                # Get docstring
                docstring = ast.get_docstring(node)
                
                symbols.append(Symbol(
                    name=node.name,
                    kind="class",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    end_line=node.end_lineno,
                    visibility=self._get_visibility(node.name),
                    docstring=docstring,
                    decorators=decorators,
                    base_classes=bases,
                ))
                
                # Visit methods
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class
                
            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._visit_function(node)
                
            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._visit_function(node, is_async=True)
                
            def _visit_function(self, node, is_async=False):
                # Get decorators
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                
                # Get return type
                return_type = None
                if node.returns:
                    return_type = self._get_annotation_str(node.returns)
                    
                # Get parameters
                params = []
                for arg in node.args.args:
                    param = {"name": arg.arg}
                    if arg.annotation:
                        param["type"] = self._get_annotation_str(arg.annotation)
                    params.append(param)
                    
                # Build signature
                param_strs = [p["name"] for p in params]
                signature = f"{'async ' if is_async else ''}def {node.name}({', '.join(param_strs)})"
                if return_type:
                    signature += f" -> {return_type}"
                    
                kind = "method" if self.current_class else "function"
                
                symbols.append(Symbol(
                    name=node.name,
                    kind=kind,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    end_line=node.end_lineno,
                    parent=self.current_class,
                    visibility=self._get_visibility(node.name),
                    signature=signature,
                    docstring=ast.get_docstring(node),
                    decorators=decorators,
                    return_type=return_type,
                    parameters=params,
                ))
                
            def _get_visibility(self, name: str) -> str:
                if name.startswith("__") and not name.endswith("__"):
                    return "private"
                elif name.startswith("_"):
                    return "protected"
                return "public"
                
            def _get_decorator_name(self, node) -> str:
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    return self._get_attr_name(node)
                elif isinstance(node, ast.Call):
                    return self._get_decorator_name(node.func)
                return "unknown"
                
            def _get_attr_name(self, node: ast.Attribute) -> str:
                parts = []
                while isinstance(node, ast.Attribute):
                    parts.append(node.attr)
                    node = node.value
                if isinstance(node, ast.Name):
                    parts.append(node.id)
                return ".".join(reversed(parts))
                
            def _get_annotation_str(self, node) -> str:
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    return self._get_attr_name(node)
                elif isinstance(node, ast.Subscript):
                    value = self._get_annotation_str(node.value)
                    if isinstance(node.slice, ast.Tuple):
                        slices = ", ".join(self._get_annotation_str(e) for e in node.slice.elts)
                    else:
                        slices = self._get_annotation_str(node.slice)
                    return f"{value}[{slices}]"
                elif isinstance(node, ast.Constant):
                    return repr(node.value)
                return "Any"
        
        visitor = SymbolVisitor(path)
        visitor.visit(tree)
        return symbols
    
    def get_imports(self, path: Path) -> List[Import]:
        """Extract imports from Python file."""
        tree = self.parse_file(path)
        if tree is None:
            return []
            
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(Import(
                        module=alias.name,
                        names=[alias.name.split(".")[-1]],
                        alias=alias.asname,
                        file_path=path,
                        line_number=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(Import(
                        module=node.module,
                        names=[alias.name for alias in node.names],
                        file_path=path,
                        line_number=node.lineno,
                        is_relative=node.level > 0,
                    ))
                    
        return imports
    
    def get_dependencies(self, project_path: Path) -> List[Dependency]:
        """Extract dependencies from Python project."""
        dependencies = []
        
        if project_path.is_file():
            project_path = project_path.parent
            
        # Try pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            dependencies.extend(self._parse_pyproject_deps(pyproject))
            
        # Try requirements.txt
        requirements = project_path / "requirements.txt"
        if requirements.exists():
            dependencies.extend(self._parse_requirements_txt(requirements))
            
        # Try requirements-dev.txt
        dev_requirements = project_path / "requirements-dev.txt"
        if dev_requirements.exists():
            for dep in self._parse_requirements_txt(dev_requirements):
                dep.is_dev = True
                dependencies.append(dep)
                
        return dependencies
    
    def _parse_pyproject_deps(self, path: Path) -> List[Dependency]:
        """Parse dependencies from pyproject.toml."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return []
                
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
                
            deps = []
            
            # Main dependencies
            for dep in data.get("project", {}).get("dependencies", []):
                parsed = self._parse_dep_string(dep)
                if parsed:
                    deps.append(parsed)
                    
            # Dev dependencies
            for dep in data.get("project", {}).get("optional-dependencies", {}).get("dev", []):
                parsed = self._parse_dep_string(dep)
                if parsed:
                    parsed.is_dev = True
                    deps.append(parsed)
                    
            return deps
        except Exception:
            return []
    
    def _parse_requirements_txt(self, path: Path) -> List[Dependency]:
        """Parse requirements.txt file."""
        deps = []
        try:
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    parsed = self._parse_dep_string(line)
                    if parsed:
                        deps.append(parsed)
        except Exception:
            pass
        return deps
    
    def _parse_dep_string(self, dep: str) -> Optional[Dependency]:
        """Parse a dependency specification string."""
        # Handle various formats: package, package==1.0, package>=1.0, package[extra]
        match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*\])?(?:([<>=!]+)(.+))?$', dep.strip())
        if match:
            name, op, version = match.groups()
            return Dependency(
                name=name,
                version=version,
                version_constraint=f"{op}{version}" if op else None,
                source="pypi",
            )
        return None
```

---

## Phase 4: Analyzers

Create the analysis components that extract specific information.

### 4.1 `tools/discovery/analyzers/__init__.py`

```python
"""
Discovery Analyzers
===================

Components for analyzing specific aspects of a codebase.
"""

from .structure import StructureAnalyzer
from .patterns import PatternExtractor
from .architecture import ArchitectureMapper
from .conventions import ConventionInferrer
from .tests import TestGapAnalyzer

__all__ = [
    "StructureAnalyzer",
    "PatternExtractor",
    "ArchitectureMapper",
    "ConventionInferrer",
    "TestGapAnalyzer",
]
```

### 4.2 `tools/discovery/analyzers/structure.py`

```python
"""
Structure Analyzer
==================

Analyzes directory structure to detect architectural patterns.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from ..domain import Detection, DetectionSource, LayerInfo


class StructureAnalyzer:
    """Analyzes project structure to detect architecture."""
    
    # Known architectural patterns
    CLEAN_ARCHITECTURE_PATTERNS = {
        "domain": ["domain", "core", "entities", "model", "models"],
        "application": ["application", "services", "usecases", "use_cases"],
        "infrastructure": ["infrastructure", "infra", "persistence", "data"],
        "presentation": ["api", "web", "presentation", "controllers", "ui"],
    }
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze project structure.
        
        Returns:
            Structure information including:
            - style: Architecture style detected
            - confidence: Detection confidence
            - layers: List of detected layers
            - entry_points: Main entry points
            - test_projects: Test project locations
        """
        # Build directory tree
        tree = self._build_directory_tree()
        
        # Detect architecture style
        style, confidence, layers = self._detect_architecture(tree)
        
        # Find entry points
        entry_points = self._find_entry_points(tree)
        
        # Find test projects
        test_projects = self._find_test_projects(tree)
        
        # Find key directories
        key_dirs = self._identify_key_directories(tree)
        
        return {
            "root_path": str(self.repo_root),
            "style": style,
            "confidence": confidence,
            "layers": [layer.to_dict() if hasattr(layer, 'to_dict') else layer for layer in layers],
            "entry_points": entry_points,
            "test_projects": test_projects,
            "key_directories": key_dirs,
        }
    
    def _build_directory_tree(self) -> Dict[str, Any]:
        """Build a tree representation of the directory structure."""
        tree = {"name": self.repo_root.name, "path": str(self.repo_root), "children": {}, "files": []}
        
        excluded = {".git", "node_modules", "__pycache__", "venv", ".venv", 
                   "bin", "obj", ".vs", ".idea", "dist", "build"}
        
        def add_to_tree(path: Path, node: Dict):
            for item in path.iterdir():
                if item.name in excluded or item.name.startswith("."):
                    continue
                    
                if item.is_dir():
                    child = {"name": item.name, "path": str(item), "children": {}, "files": []}
                    node["children"][item.name] = child
                    add_to_tree(item, child)
                else:
                    node["files"].append(item.name)
                    
        add_to_tree(self.repo_root, tree)
        return tree
    
    def _detect_architecture(self, tree: Dict) -> Tuple[str, float, List[Dict]]:
        """Detect architecture style from directory structure."""
        # Flatten all directory names
        all_dirs = self._get_all_directories(tree)
        dir_names_lower = {d["name"].lower(): d for d in all_dirs}
        
        # Check for Clean Architecture patterns
        clean_arch_score = 0
        detected_layers = []
        
        for layer_name, patterns in self.CLEAN_ARCHITECTURE_PATTERNS.items():
            for pattern in patterns:
                if pattern in dir_names_lower:
                    clean_arch_score += 1
                    dir_info = dir_names_lower[pattern]
                    detected_layers.append({
                        "name": layer_name,
                        "path": dir_info["path"],
                        "detected_by": pattern,
                    })
                    break
        
        # Calculate confidence
        if clean_arch_score >= 3:
            return "clean-architecture", 0.85 + (clean_arch_score - 3) * 0.05, detected_layers
        elif clean_arch_score >= 2:
            return "layered", 0.6 + clean_arch_score * 0.1, detected_layers
        else:
            # Check for simple src/tests structure
            if "src" in dir_names_lower or "lib" in dir_names_lower:
                return "standard", 0.7, []
            return "unknown", 0.3, []
    
    def _get_all_directories(self, tree: Dict, depth: int = 3) -> List[Dict]:
        """Get all directories up to a certain depth."""
        dirs = []
        
        def collect(node: Dict, current_depth: int):
            if current_depth > depth:
                return
            for name, child in node.get("children", {}).items():
                dirs.append({"name": name, "path": child["path"]})
                collect(child, current_depth + 1)
                
        collect(tree, 0)
        return dirs
    
    def _find_entry_points(self, tree: Dict) -> List[str]:
        """Find main entry point files/projects."""
        entry_points = []
        
        # Python entry points
        python_entries = ["main.py", "app.py", "__main__.py", "manage.py", "wsgi.py", "asgi.py"]
        
        # .NET entry points
        dotnet_entries = ["Program.cs", "Startup.cs"]
        
        def search(node: Dict, path: str):
            for f in node.get("files", []):
                if f in python_entries or f in dotnet_entries:
                    entry_points.append(f"{path}/{f}" if path else f)
                elif f.endswith(".csproj"):
                    # Check if it's an executable project
                    entry_points.append(f"{path}/{f}" if path else f)
            for name, child in node.get("children", {}).items():
                search(child, f"{path}/{name}" if path else name)
                
        search(tree, "")
        return entry_points
    
    def _find_test_projects(self, tree: Dict) -> List[str]:
        """Find test project directories."""
        test_dirs = []
        test_patterns = ["test", "tests", "unittest", "unittests", 
                        "integration", "integrationtests", "e2e"]
        
        def search(node: Dict, path: str):
            name_lower = node.get("name", "").lower()
            if any(p in name_lower for p in test_patterns):
                test_dirs.append(path or node.get("name", ""))
            for name, child in node.get("children", {}).items():
                search(child, f"{path}/{name}" if path else name)
                
        search(tree, "")
        return test_dirs
    
    def _identify_key_directories(self, tree: Dict) -> List[Dict[str, str]]:
        """Identify key directories and their purposes."""
        key_dirs = []
        
        known_purposes = {
            "src": "Source code",
            "lib": "Library code",
            "tests": "Test files",
            "test": "Test files",
            "docs": "Documentation",
            "config": "Configuration files",
            "scripts": "Utility scripts",
            "migrations": "Database migrations",
            "static": "Static assets",
            "templates": "Template files",
            "schemas": "Schema definitions",
            "contracts": "Contract definitions",
        }
        
        for name, child in tree.get("children", {}).items():
            purpose = known_purposes.get(name.lower())
            if purpose:
                key_dirs.append({"path": name, "purpose": purpose})
                
        return key_dirs
```

### 4.3 `tools/discovery/analyzers/patterns.py`

```python
"""
Pattern Extractor
=================

Extracts coding patterns from the codebase.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

from ..domain import PatternDetection, DetectionSource
from ..providers.base import LanguageProvider, Symbol


class PatternExtractor:
    """Extracts coding patterns using AST analysis."""
    
    def __init__(self, provider: LanguageProvider, repo_root: Path):
        self.provider = provider
        self.repo_root = repo_root
        
    def extract_all(self) -> Dict[str, PatternDetection]:
        """Extract all detectable patterns."""
        # Get all source files
        files = self.provider.get_source_files(self.repo_root)
        
        # Collect symbols from all files
        all_symbols = []
        all_imports = []
        
        for file_path in files:
            symbols = self.provider.extract_symbols(file_path)
            imports = self.provider.get_imports(file_path)
            all_symbols.extend(symbols)
            all_imports.extend(imports)
        
        patterns = {}
        
        # Detect error handling pattern
        patterns["error_handling"] = self._detect_error_handling(all_symbols)
        
        # Detect CQRS pattern
        patterns["cqrs"] = self._detect_cqrs(all_symbols, all_imports)
        
        # Detect repository pattern
        patterns["repository"] = self._detect_repository(all_symbols)
        
        # Detect dependency injection
        patterns["dependency_injection"] = self._detect_di(all_symbols)
        
        # Detect DDD patterns
        patterns["ddd"] = self._detect_ddd(all_symbols)
        
        return patterns
    
    def _detect_error_handling(self, symbols: List[Symbol]) -> PatternDetection:
        """Detect error handling pattern (Result<T> vs exceptions)."""
        result_returns = 0
        other_returns = 0
        examples = []
        
        for symbol in symbols:
            if symbol.kind in ("function", "method") and symbol.return_type:
                return_type = symbol.return_type.lower()
                if "result" in return_type:
                    result_returns += 1
                    if len(examples) < 5:
                        examples.append(f"{symbol.name}() → {symbol.return_type}")
                elif return_type not in ("none", "void"):
                    other_returns += 1
        
        total = result_returns + other_returns
        if total == 0:
            return PatternDetection(
                name="error_handling",
                detected=False,
                confidence=0.0,
            )
        
        result_ratio = result_returns / total
        
        if result_ratio > 0.5:
            return PatternDetection(
                name="error_handling",
                detected=True,
                primary="result_pattern",
                confidence=min(0.5 + result_ratio * 0.4, 0.95),
                examples=examples,
                evidence={"result_returns": result_returns, "other_returns": other_returns},
            )
        else:
            return PatternDetection(
                name="error_handling",
                detected=True,
                primary="exception_pattern",
                confidence=0.6,  # Default assumption
                evidence={"result_returns": result_returns, "other_returns": other_returns},
            )
    
    def _detect_cqrs(self, symbols: List[Symbol], imports: List) -> PatternDetection:
        """Detect CQRS pattern."""
        command_classes = []
        query_classes = []
        handler_classes = []
        framework = None
        
        # Check for MediatR imports
        for imp in imports:
            if "mediatr" in imp.module.lower() or "mediator" in imp.module.lower():
                framework = "MediatR"
                break
        
        for symbol in symbols:
            if symbol.kind == "class":
                name_lower = symbol.name.lower()
                
                # Check naming patterns
                if name_lower.endswith("command"):
                    command_classes.append(symbol.name)
                elif name_lower.endswith("query"):
                    query_classes.append(symbol.name)
                elif name_lower.endswith("handler"):
                    handler_classes.append(symbol.name)
                    
                # Check base classes
                if symbol.base_classes:
                    for base in symbol.base_classes:
                        base_lower = base.lower()
                        if "irequest" in base_lower or "icommand" in base_lower:
                            command_classes.append(symbol.name)
                        elif "iquery" in base_lower:
                            query_classes.append(symbol.name)
                        elif "irequesthandler" in base_lower or "ihandler" in base_lower:
                            handler_classes.append(symbol.name)
        
        total = len(command_classes) + len(query_classes)
        
        if total >= 2 or (framework and total >= 1):
            confidence = min(0.6 + total * 0.03, 0.95)
            if framework:
                confidence = min(confidence + 0.1, 0.95)
                
            return PatternDetection(
                name="cqrs",
                detected=True,
                primary=framework or "custom",
                confidence=confidence,
                examples=[f"Commands: {', '.join(command_classes[:3])}" if command_classes else None,
                         f"Queries: {', '.join(query_classes[:3])}" if query_classes else None],
                evidence={
                    "command_classes": len(command_classes),
                    "query_classes": len(query_classes),
                    "handler_classes": len(handler_classes),
                },
            )
        
        return PatternDetection(name="cqrs", detected=False, confidence=0.3)
    
    def _detect_repository(self, symbols: List[Symbol]) -> PatternDetection:
        """Detect repository pattern."""
        interfaces = []
        implementations = []
        
        for symbol in symbols:
            if symbol.kind == "class":
                name = symbol.name
                
                if name.startswith("I") and "Repository" in name:
                    interfaces.append(name)
                elif "Repository" in name and not name.startswith("I"):
                    implementations.append(name)
                    
        total = len(interfaces) + len(implementations)
        
        if total >= 2:
            return PatternDetection(
                name="repository",
                detected=True,
                primary="interface_pattern" if interfaces else "concrete_only",
                confidence=min(0.6 + total * 0.05, 0.95),
                examples=interfaces[:3] or implementations[:3],
                evidence={
                    "interfaces": len(interfaces),
                    "implementations": len(implementations),
                },
            )
        
        return PatternDetection(name="repository", detected=False, confidence=0.3)
    
    def _detect_di(self, symbols: List[Symbol]) -> PatternDetection:
        """Detect dependency injection patterns."""
        constructor_injection = 0
        private_readonly_fields = 0
        
        for symbol in symbols:
            if symbol.kind == "method" and symbol.name == "__init__":
                if symbol.parameters and len(symbol.parameters) > 1:  # More than just self
                    constructor_injection += 1
                    
            elif symbol.kind == "class":
                # Would need field analysis - simplified for now
                pass
        
        if constructor_injection >= 3:
            return PatternDetection(
                name="dependency_injection",
                detected=True,
                primary="constructor_injection",
                confidence=min(0.6 + constructor_injection * 0.03, 0.9),
                evidence={"constructor_injection_count": constructor_injection},
            )
        
        return PatternDetection(name="dependency_injection", detected=False, confidence=0.3)
    
    def _detect_ddd(self, symbols: List[Symbol]) -> PatternDetection:
        """Detect Domain-Driven Design patterns."""
        entities = []
        value_objects = []
        aggregates = []
        
        ddd_markers = {
            "entity": entities,
            "valueobject": value_objects,
            "aggregate": aggregates,
            "aggregateroot": aggregates,
        }
        
        for symbol in symbols:
            if symbol.kind == "class" and symbol.base_classes:
                for base in symbol.base_classes:
                    base_lower = base.lower()
                    for marker, collection in ddd_markers.items():
                        if marker in base_lower:
                            collection.append(symbol.name)
                            break
        
        total = len(entities) + len(value_objects) + len(aggregates)
        
        if total >= 2:
            return PatternDetection(
                name="ddd",
                detected=True,
                primary="tactical_patterns",
                confidence=min(0.6 + total * 0.05, 0.95),
                examples=[
                    f"Entities: {', '.join(entities[:3])}" if entities else None,
                    f"Aggregates: {', '.join(aggregates[:3])}" if aggregates else None,
                ],
                evidence={
                    "entities": len(entities),
                    "value_objects": len(value_objects),
                    "aggregates": len(aggregates),
                },
            )
        
        return PatternDetection(name="ddd", detected=False, confidence=0.3)
```

### 4.4 `tools/discovery/analyzers/architecture.py`

```python
"""
Architecture Mapper
===================

Maps dependencies between layers and detects violations.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict

from ..domain import LayerInfo, ArchitectureViolation
from ..providers.base import LanguageProvider


class ArchitectureMapper:
    """Maps architecture and detects layer violations."""
    
    # Standard Clean Architecture rules
    CLEAN_ARCH_RULES = {
        "domain": {
            "allowed": [],  # Domain should have no dependencies
            "forbidden": ["infrastructure", "application", "presentation", "api"],
        },
        "application": {
            "allowed": ["domain"],
            "forbidden": ["infrastructure", "presentation", "api"],
        },
        "infrastructure": {
            "allowed": ["domain", "application"],
            "forbidden": ["presentation", "api"],
        },
        "presentation": {
            "allowed": ["application", "infrastructure"],
            "forbidden": [],
        },
        "api": {
            "allowed": ["application", "infrastructure"],
            "forbidden": ["domain"],  # API shouldn't directly use domain
        },
    }
    
    def __init__(self, provider: LanguageProvider, repo_root: Path, structure: Dict):
        self.provider = provider
        self.repo_root = repo_root
        self.structure = structure
        self.layers = structure.get("layers", [])
        
    def map_architecture(self) -> Dict[str, Any]:
        """
        Map architecture and find violations.
        
        Returns:
            Architecture mapping with violations
        """
        if not self.layers:
            return {"style": "unknown", "confidence": 0.3, "violations": []}
        
        # Build layer to path mapping
        layer_paths = {}
        for layer in self.layers:
            layer_name = layer.get("name", "").lower()
            layer_path = layer.get("path", "")
            if layer_name and layer_path:
                layer_paths[layer_name] = Path(layer_path)
        
        # Analyze imports for each layer
        violations = []
        layer_dependencies = defaultdict(set)
        
        for layer in self.layers:
            layer_name = layer.get("name", "").lower()
            layer_path = self.repo_root / layer.get("path", "")
            
            if not layer_path.exists():
                continue
                
            # Get all source files in this layer
            files = self.provider.get_source_files(layer_path)
            
            for file_path in files:
                imports = self.provider.get_imports(file_path)
                
                for imp in imports:
                    # Check which layer this import belongs to
                    target_layer = self._get_layer_for_import(imp.module, layer_paths)
                    
                    if target_layer and target_layer != layer_name:
                        layer_dependencies[layer_name].add(target_layer)
                        
                        # Check if this is a violation
                        if self._is_violation(layer_name, target_layer):
                            violations.append(ArchitectureViolation(
                                from_layer=layer_name,
                                to_layer=target_layer,
                                file_path=str(file_path.relative_to(self.repo_root)),
                                line_number=imp.line_number,
                                import_statement=imp.module,
                            ))
        
        # Build layer info with actual dependencies
        layer_infos = []
        for layer in self.layers:
            layer_name = layer.get("name", "").lower()
            rules = self.CLEAN_ARCH_RULES.get(layer_name, {})
            
            layer_infos.append({
                "name": layer_name,
                "path": layer.get("path"),
                "allowed_references": rules.get("allowed", []),
                "actual_references": list(layer_dependencies.get(layer_name, set())),
            })
        
        return {
            "style": self.structure.get("style", "unknown"),
            "confidence": self.structure.get("confidence", 0.5),
            "layers": layer_infos,
            "violations": [
                {
                    "type": "layer_dependency",
                    "from_layer": v.from_layer,
                    "to_layer": v.to_layer,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "import": v.import_statement,
                    "severity": "major",
                }
                for v in violations
            ],
        }
    
    def _get_layer_for_import(self, module: str, layer_paths: Dict[str, Path]) -> Optional[str]:
        """Determine which layer an import belongs to."""
        module_parts = module.lower().split(".")
        
        for layer_name, layer_path in layer_paths.items():
            # Check if any part of the module matches the layer
            layer_parts = str(layer_path).lower().replace("\\", "/").split("/")
            
            for part in module_parts:
                if part in layer_parts or part == layer_name:
                    return layer_name
                    
        return None
    
    def _is_violation(self, from_layer: str, to_layer: str) -> bool:
        """Check if importing from to_layer into from_layer is a violation."""
        rules = self.CLEAN_ARCH_RULES.get(from_layer, {})
        
        # If explicitly forbidden
        if to_layer in rules.get("forbidden", []):
            return True
            
        # If not explicitly allowed (and rules exist)
        allowed = rules.get("allowed", [])
        if allowed and to_layer not in allowed:
            return True
            
        return False
```

### 4.5 `tools/discovery/analyzers/conventions.py`

```python
"""
Convention Inferrer
===================

Infers naming conventions and file organization patterns.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter

from ..domain import ConventionDetection
from ..providers.base import LanguageProvider, Symbol


class ConventionInferrer:
    """Infers coding conventions from the codebase."""
    
    def __init__(self, provider: LanguageProvider, repo_root: Path):
        self.provider = provider
        self.repo_root = repo_root
        
    def infer_all(self) -> Dict[str, Any]:
        """Infer all conventions."""
        files = self.provider.get_source_files(self.repo_root)
        
        all_symbols = []
        for file_path in files:
            symbols = self.provider.extract_symbols(file_path)
            all_symbols.extend(symbols)
        
        return {
            "naming": {
                "files": self._infer_file_naming(files),
                "classes": self._infer_class_naming(all_symbols),
                "functions": self._infer_function_naming(all_symbols),
                "private_fields": self._infer_field_naming(all_symbols),
                "interfaces": self._infer_interface_naming(all_symbols),
            },
            "file_organization": self._infer_file_organization(files, all_symbols),
        }
    
    def _infer_file_naming(self, files: List[Path]) -> Dict[str, Any]:
        """Infer file naming convention."""
        patterns = Counter()
        
        for file_path in files:
            name = file_path.stem
            if name.startswith("_"):
                continue  # Skip special files
                
            if self._is_snake_case(name):
                patterns["snake_case"] += 1
            elif self._is_pascal_case(name):
                patterns["PascalCase"] += 1
            elif self._is_kebab_case(name):
                patterns["kebab-case"] += 1
            elif self._is_camel_case(name):
                patterns["camelCase"] += 1
            else:
                patterns["mixed"] += 1
        
        return self._build_convention_result(patterns, list(files))
    
    def _infer_class_naming(self, symbols: List[Symbol]) -> Dict[str, Any]:
        """Infer class naming convention."""
        patterns = Counter()
        classes = [s for s in symbols if s.kind == "class"]
        
        for symbol in classes:
            name = symbol.name
            if self._is_pascal_case(name):
                patterns["PascalCase"] += 1
            elif self._is_snake_case(name):
                patterns["snake_case"] += 1
            else:
                patterns["mixed"] += 1
        
        return self._build_convention_result(patterns, [s.name for s in classes])
    
    def _infer_function_naming(self, symbols: List[Symbol]) -> Dict[str, Any]:
        """Infer function/method naming convention."""
        patterns = Counter()
        functions = [s for s in symbols if s.kind in ("function", "method") 
                    and not s.name.startswith("_")]
        
        for symbol in functions:
            name = symbol.name
            if self._is_snake_case(name):
                patterns["snake_case"] += 1
            elif self._is_pascal_case(name):
                patterns["PascalCase"] += 1
            elif self._is_camel_case(name):
                patterns["camelCase"] += 1
            else:
                patterns["mixed"] += 1
        
        return self._build_convention_result(patterns, [s.name for s in functions])
    
    def _infer_field_naming(self, symbols: List[Symbol]) -> Dict[str, Any]:
        """Infer private field naming convention."""
        patterns = Counter()
        private_methods = [s for s in symbols if s.kind == "method" 
                         and s.name.startswith("_") and not s.name.startswith("__")]
        
        for symbol in private_methods:
            name = symbol.name
            if name.startswith("_") and self._is_camel_case(name[1:]):
                patterns["_camelCase"] += 1
            elif name.startswith("_") and self._is_snake_case(name[1:]):
                patterns["_snake_case"] += 1
            else:
                patterns["other"] += 1
        
        return self._build_convention_result(patterns, [s.name for s in private_methods])
    
    def _infer_interface_naming(self, symbols: List[Symbol]) -> Dict[str, Any]:
        """Infer interface naming convention."""
        patterns = Counter()
        classes = [s for s in symbols if s.kind == "class"]
        
        # Look for interface-like classes (ABC, Protocol, or I-prefix)
        interfaces = []
        for symbol in classes:
            if symbol.name.startswith("I") and len(symbol.name) > 1 and symbol.name[1].isupper():
                patterns["I{Name}"] += 1
                interfaces.append(symbol.name)
            elif symbol.base_classes:
                if any("abc" in b.lower() or "protocol" in b.lower() for b in symbol.base_classes):
                    if symbol.name.endswith("Protocol"):
                        patterns["{Name}Protocol"] += 1
                    elif symbol.name.endswith("Interface"):
                        patterns["{Name}Interface"] += 1
                    interfaces.append(symbol.name)
        
        return self._build_convention_result(patterns, interfaces)
    
    def _infer_file_organization(self, files: List[Path], symbols: List[Symbol]) -> Dict[str, Any]:
        """Infer file organization pattern."""
        # Check classes per file
        file_class_counts = Counter()
        
        for symbol in symbols:
            if symbol.kind == "class":
                file_class_counts[str(symbol.file_path)] += 1
        
        if not file_class_counts:
            return {"style": "unknown", "consistency": 0.0}
        
        single_class_files = sum(1 for count in file_class_counts.values() if count == 1)
        multi_class_files = sum(1 for count in file_class_counts.values() if count > 1)
        
        total = single_class_files + multi_class_files
        if total == 0:
            return {"style": "unknown", "consistency": 0.0}
        
        if single_class_files / total > 0.8:
            return {
                "style": "one_class_per_file",
                "consistency": single_class_files / total,
            }
        else:
            return {
                "style": "multiple_classes_per_file",
                "consistency": multi_class_files / total,
            }
    
    def _build_convention_result(self, patterns: Counter, samples: List) -> Dict[str, Any]:
        """Build convention detection result from pattern counts."""
        if not patterns:
            return {"pattern": "unknown", "consistency": 0.0}
        
        total = sum(patterns.values())
        most_common = patterns.most_common(1)[0]
        pattern_name, count = most_common
        
        consistency = count / total if total > 0 else 0.0
        
        result = {
            "pattern": pattern_name,
            "consistency": round(consistency, 2),
        }
        
        # Add alternatives if there are multiple patterns
        if len(patterns) > 1:
            alternatives = []
            for pattern, cnt in patterns.most_common()[1:3]:  # Top 2 alternatives
                if cnt > 0:
                    alternatives.append({
                        "pattern": pattern,
                        "frequency": round(cnt / total, 2),
                    })
            if alternatives:
                result["alternatives"] = alternatives
        
        return result
    
    def _is_snake_case(self, name: str) -> bool:
        return bool(re.match(r'^[a-z][a-z0-9_]*$', name))
    
    def _is_pascal_case(self, name: str) -> bool:
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
    
    def _is_camel_case(self, name: str) -> bool:
        return bool(re.match(r'^[a-z][a-zA-Z0-9]*$', name)) and any(c.isupper() for c in name)
    
    def _is_kebab_case(self, name: str) -> bool:
        return bool(re.match(r'^[a-z][a-z0-9-]*$', name)) and '-' in name
```

### 4.6 `tools/discovery/analyzers/tests.py`

```python
"""
Test Gap Analyzer
=================

Analyzes test coverage and identifies gaps.
"""

from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict

from ..domain import TestInventory, TestGap, TestAnalysis
from ..providers.base import LanguageProvider, Symbol


class TestGapAnalyzer:
    """Analyzes test coverage without running tests."""
    
    def __init__(self, provider: LanguageProvider, repo_root: Path, test_dirs: List[str]):
        self.provider = provider
        self.repo_root = repo_root
        self.test_dirs = test_dirs
        
    def analyze(self) -> TestAnalysis:
        """Analyze test coverage and gaps."""
        # Find test files
        test_files = self._find_test_files()
        
        # Extract test methods
        test_inventory = self._build_test_inventory(test_files)
        
        # Find source files
        source_files = self._find_source_files()
        
        # Analyze gaps
        gaps = self._find_gaps(source_files, test_files)
        
        # Estimate coverage
        coverage = self._estimate_coverage(source_files, test_files)
        
        # Detect test patterns
        patterns = self._detect_test_patterns(test_files)
        
        return TestAnalysis(
            confidence=0.7,  # Static analysis is inherently limited
            inventory=test_inventory,
            estimated_coverage=coverage,
            gaps=gaps,
            test_patterns=patterns,
        )
    
    def _find_test_files(self) -> List[Path]:
        """Find all test files."""
        test_files = []
        
        for test_dir in self.test_dirs:
            test_path = self.repo_root / test_dir
            if test_path.exists():
                test_files.extend(self.provider.get_source_files(test_path))
        
        # Also look for test files by naming convention
        all_files = self.provider.get_source_files(self.repo_root)
        for f in all_files:
            name = f.stem.lower()
            if (name.startswith("test_") or name.endswith("_test") or 
                name.startswith("test") or name.endswith("tests")):
                if f not in test_files:
                    test_files.append(f)
        
        return test_files
    
    def _find_source_files(self) -> List[Path]:
        """Find all source files (excluding tests)."""
        test_file_set = set(self._find_test_files())
        all_files = self.provider.get_source_files(self.repo_root)
        
        source_files = []
        for f in all_files:
            if f not in test_file_set:
                name = f.stem.lower()
                if not (name.startswith("test_") or name.endswith("_test") or
                       name.startswith("test") or "conftest" in name):
                    source_files.append(f)
        
        return source_files
    
    def _build_test_inventory(self, test_files: List[Path]) -> TestInventory:
        """Build inventory of tests."""
        inventory = TestInventory()
        inventory.total_test_files = len(test_files)
        
        frameworks = set()
        categories = defaultdict(int)
        
        for test_file in test_files:
            symbols = self.provider.extract_symbols(test_file)
            imports = self.provider.get_imports(test_file)
            
            # Count test methods
            for symbol in symbols:
                if symbol.kind in ("function", "method"):
                    name = symbol.name.lower()
                    if name.startswith("test_") or name.startswith("test"):
                        inventory.total_test_methods += 1
                        
                        # Categorize
                        file_path_str = str(test_file).lower()
                        if "integration" in file_path_str:
                            categories["integration"] += 1
                        elif "e2e" in file_path_str or "end_to_end" in file_path_str:
                            categories["e2e"] += 1
                        else:
                            categories["unit"] += 1
            
            # Detect frameworks
            for imp in imports:
                module = imp.module.lower()
                if "pytest" in module:
                    frameworks.add("pytest")
                elif "unittest" in module:
                    frameworks.add("unittest")
                elif "nose" in module:
                    frameworks.add("nose")
        
        inventory.frameworks = list(frameworks)
        inventory.categories = dict(categories)
        
        return inventory
    
    def _find_gaps(self, source_files: List[Path], test_files: List[Path]) -> List[TestGap]:
        """Find files/classes without tests."""
        gaps = []
        
        # Build set of tested file stems
        test_stems = set()
        for tf in test_files:
            stem = tf.stem.lower()
            # test_foo.py -> foo, foo_test.py -> foo
            if stem.startswith("test_"):
                test_stems.add(stem[5:])
            elif stem.endswith("_test"):
                test_stems.add(stem[:-5])
            elif stem.endswith("_tests"):
                test_stems.add(stem[:-6])
        
        # Check each source file
        for source_file in source_files:
            stem = source_file.stem.lower()
            if stem not in test_stems and not stem.startswith("__"):
                gaps.append(TestGap(
                    gap_type="untested_file",
                    location=str(source_file.relative_to(self.repo_root)),
                ))
        
        return gaps[:50]  # Limit to 50 gaps
    
    def _estimate_coverage(self, source_files: List[Path], test_files: List[Path]) -> float:
        """Estimate test coverage based on file matching."""
        if not source_files:
            return 1.0
        
        test_stems = set()
        for tf in test_files:
            stem = tf.stem.lower()
            if stem.startswith("test_"):
                test_stems.add(stem[5:])
            elif stem.endswith("_test"):
                test_stems.add(stem[:-5])
            elif stem.endswith("_tests"):
                test_stems.add(stem[:-6])
        
        covered = 0
        for source_file in source_files:
            stem = source_file.stem.lower()
            if stem in test_stems or stem.startswith("__"):
                covered += 1
        
        return round(covered / len(source_files), 2)
    
    def _detect_test_patterns(self, test_files: List[Path]) -> Dict[str, str]:
        """Detect test naming and organization patterns."""
        patterns = {}
        naming_patterns = defaultdict(int)
        
        for test_file in test_files[:20]:  # Sample first 20
            symbols = self.provider.extract_symbols(test_file)
            
            for symbol in symbols:
                if symbol.kind in ("function", "method") and symbol.name.startswith("test"):
                    name = symbol.name
                    
                    # Detect patterns
                    if "_should_" in name.lower():
                        naming_patterns["should_when"] += 1
                    elif "_given_" in name.lower():
                        naming_patterns["given_when_then"] += 1
                    elif "_" in name and name.count("_") >= 2:
                        naming_patterns["method_scenario_expected"] += 1
                    else:
                        naming_patterns["simple"] += 1
        
        if naming_patterns:
            most_common = max(naming_patterns, key=naming_patterns.get)
            pattern_names = {
                "should_when": "Should_{Expected}_When_{Condition}",
                "given_when_then": "Given_{Context}_When_{Action}_Then_{Expected}",
                "method_scenario_expected": "{Method}_{Scenario}_{Expected}",
                "simple": "test_{description}",
            }
            patterns["naming"] = pattern_names.get(most_common, "unknown")
        
        return patterns
```

---

## Phase 5: Profile Generator

Create the component that consolidates all analysis into the final profile.

### 5.1 `tools/discovery/generators/__init__.py`

```python
"""Profile generators."""

from .profile import ProfileGenerator

__all__ = ["ProfileGenerator"]
```

### 5.2 `tools/discovery/generators/profile.py`

```python
"""
Profile Generator
=================

Consolidates discovery results into codebase_profile.yaml.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from ..domain import (
    CodebaseProfile, DiscoveryMetadata, LanguageInfo, 
    PatternDetection, OnboardingProgress, OnboardingStatus
)


class ProfileGenerator:
    """Generates codebase_profile.yaml from discovery results."""
    
    SCHEMA_VERSION = "1.0"
    ENGINE_VERSION = "1.0.0"
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.agentforge_path = repo_root / ".agentforge"
        
    def generate(
        self,
        languages: List[LanguageInfo],
        structure: Dict[str, Any],
        patterns: Dict[str, PatternDetection],
        architecture: Optional[Dict[str, Any]] = None,
        conventions: Optional[Dict[str, Any]] = None,
        test_analysis: Optional[Any] = None,
        dependencies: Optional[List] = None,
        run_type: str = "full",
        duration_ms: int = 0,
        phases_completed: List[str] = None,
    ) -> CodebaseProfile:
        """Generate a CodebaseProfile from discovery results."""
        
        metadata = DiscoveryMetadata(
            version=self.ENGINE_VERSION,
            run_date=datetime.utcnow(),
            run_type=run_type,
            duration_ms=duration_ms,
            phases_completed=phases_completed or [],
            repo_root=str(self.repo_root),
        )
        
        profile = CodebaseProfile(
            schema_version=self.SCHEMA_VERSION,
            generated_at=datetime.utcnow(),
            discovery_metadata=metadata,
            languages=languages,
            structure=structure,
            patterns=patterns,
            architecture=architecture,
            conventions=conventions,
            test_analysis=test_analysis,
            dependencies=dependencies or [],
        )
        
        return profile
    
    def save(self, profile: CodebaseProfile) -> Path:
        """Save profile to .agentforge/codebase_profile.yaml."""
        self.agentforge_path.mkdir(parents=True, exist_ok=True)
        
        output_path = self.agentforge_path / "codebase_profile.yaml"
        
        data = profile.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        return output_path
    
    def load_existing(self) -> Optional[CodebaseProfile]:
        """Load existing profile if present."""
        profile_path = self.agentforge_path / "codebase_profile.yaml"
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Convert back to CodebaseProfile (simplified)
            # Full implementation would reconstruct all objects
            return data  # Return raw dict for now
        except Exception:
            return None
    
    def merge_with_existing(
        self,
        new_profile: CodebaseProfile,
        preserve_curated: bool = True
    ) -> CodebaseProfile:
        """Merge new profile with existing, preserving human curations."""
        existing = self.load_existing()
        
        if existing is None:
            return new_profile
        
        # In a full implementation, this would:
        # 1. Keep all human-curated values from existing
        # 2. Update auto-detected values with new findings
        # 3. Track what changed
        
        # For now, just return new profile
        return new_profile
```

---

## Phase 6: Discovery Manager

Create the main orchestrator that coordinates all phases.

### 6.1 `tools/discovery/__init__.py`

```python
"""
Brownfield Discovery System
===========================

Analyzes existing codebases and generates codebase_profile.yaml.
Implements the Artifact Parity Principle.
"""

from .manager import DiscoveryManager
from .domain import (
    CodebaseProfile, LanguageInfo, PatternDetection,
    ConventionDetection, TestAnalysis, DiscoveryPhase
)

__all__ = [
    "DiscoveryManager",
    "CodebaseProfile",
    "LanguageInfo",
    "PatternDetection",
    "ConventionDetection",
    "TestAnalysis",
    "DiscoveryPhase",
]
```

### 6.2 `tools/discovery/manager.py`

```python
"""
Discovery Manager
=================

Orchestrates the brownfield discovery process.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from .domain import (
    DiscoveryPhase, LanguageInfo, PatternDetection,
    CodebaseProfile, DetectionSource, OnboardingProgress, OnboardingStatus
)
from .providers.base import LanguageProvider
from .providers.python_provider import PythonProvider
from .analyzers.structure import StructureAnalyzer
from .analyzers.patterns import PatternExtractor
from .analyzers.architecture import ArchitectureMapper
from .analyzers.conventions import ConventionInferrer
from .analyzers.tests import TestGapAnalyzer
from .generators.profile import ProfileGenerator


class DiscoveryManager:
    """
    Orchestrates brownfield discovery.
    
    Coordinates:
    - Language detection and provider selection
    - Structure analysis
    - Pattern extraction
    - Architecture mapping
    - Convention inference
    - Test gap analysis
    - Profile generation
    """
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.agentforge_path = self.repo_root / ".agentforge"
        self.provider: Optional[LanguageProvider] = None
        self.profile_generator = ProfileGenerator(self.repo_root)
        
        # Available providers
        self._providers = {
            "python": PythonProvider,
            # "dotnet": DotNetProvider,  # Phase 7
        }
        
    def discover(
        self,
        phases: List[str] = None,
        module_path: Path = None,
        update: bool = False,
    ) -> CodebaseProfile:
        """
        Run discovery process.
        
        Args:
            phases: Specific phases to run, or None for all
            module_path: Specific module to discover
            update: Whether to update existing profile
            
        Returns:
            Generated CodebaseProfile
        """
        start_time = time.time()
        
        # Default to all phases
        if phases is None:
            phases = [p.value for p in DiscoveryPhase]
        
        # Results storage
        languages = []
        structure = {}
        patterns = {}
        architecture = None
        conventions = None
        test_analysis = None
        dependencies = []
        completed_phases = []
        
        # Phase 1: Language Detection
        if DiscoveryPhase.LANGUAGE.value in phases:
            languages = self._detect_languages()
            completed_phases.append(DiscoveryPhase.LANGUAGE.value)
            
            # Select provider based on primary language
            if languages:
                self._select_provider(languages[0].name)
        
        if not self.provider:
            # Default to Python provider
            self.provider = PythonProvider()
        
        # Phase 2: Structure Analysis
        if DiscoveryPhase.STRUCTURE.value in phases:
            analyzer = StructureAnalyzer(self.repo_root)
            structure = analyzer.analyze()
            completed_phases.append(DiscoveryPhase.STRUCTURE.value)
        
        # Phase 3: Pattern Extraction
        if DiscoveryPhase.PATTERNS.value in phases:
            extractor = PatternExtractor(self.provider, self.repo_root)
            patterns = extractor.extract_all()
            completed_phases.append(DiscoveryPhase.PATTERNS.value)
        
        # Phase 4: Architecture Mapping
        if DiscoveryPhase.ARCHITECTURE.value in phases and structure:
            mapper = ArchitectureMapper(self.provider, self.repo_root, structure)
            architecture = mapper.map_architecture()
            completed_phases.append(DiscoveryPhase.ARCHITECTURE.value)
        
        # Phase 5: Convention Inference
        if DiscoveryPhase.CONVENTIONS.value in phases:
            inferrer = ConventionInferrer(self.provider, self.repo_root)
            conventions = inferrer.infer_all()
            completed_phases.append(DiscoveryPhase.CONVENTIONS.value)
        
        # Phase 6: Test Gap Analysis
        if DiscoveryPhase.TESTS.value in phases:
            test_dirs = structure.get("test_projects", [])
            analyzer = TestGapAnalyzer(self.provider, self.repo_root, test_dirs)
            test_analysis = analyzer.analyze()
            completed_phases.append(DiscoveryPhase.TESTS.value)
        
        # Get dependencies
        dependencies = self.provider.get_dependencies(self.repo_root)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Generate profile
        profile = self.profile_generator.generate(
            languages=languages,
            structure=structure,
            patterns=patterns,
            architecture=architecture,
            conventions=conventions,
            test_analysis=test_analysis,
            dependencies=[{
                "name": d.name,
                "version": d.version,
                "source": d.source,
            } for d in dependencies],
            run_type="full" if phases is None else "phase",
            duration_ms=duration_ms,
            phases_completed=completed_phases,
        )
        
        # Merge with existing if updating
        if update:
            profile = self.profile_generator.merge_with_existing(profile)
        
        return profile
    
    def _detect_languages(self) -> List[LanguageInfo]:
        """Detect programming languages in the repository."""
        languages = []
        
        # Count files by extension
        extension_counts: Dict[str, int] = {}
        total_files = 0
        
        excluded = {".git", "node_modules", "__pycache__", "venv", ".venv", 
                   "bin", "obj", ".vs", ".idea", "dist", "build"}
        
        for path in self.repo_root.rglob("*"):
            if path.is_file() and not any(ex in path.parts for ex in excluded):
                ext = path.suffix.lower()
                if ext:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
                    total_files += 1
        
        if total_files == 0:
            return languages
        
        # Map extensions to languages
        extension_to_lang = {
            ".py": "python",
            ".pyi": "python",
            ".cs": "csharp",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
        }
        
        lang_counts: Dict[str, int] = {}
        for ext, count in extension_counts.items():
            lang = extension_to_lang.get(ext)
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + count
        
        # Sort by count and build language info
        sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        
        for lang, count in sorted_langs:
            percentage = (count / total_files) * 100
            if percentage >= 1.0:  # Only include if >= 1%
                # Detect frameworks
                frameworks = self._detect_frameworks(lang)
                
                languages.append(LanguageInfo(
                    name=lang,
                    percentage=round(percentage, 1),
                    confidence=0.95,  # High confidence from file extension
                    frameworks=frameworks,
                ))
        
        return languages
    
    def _detect_frameworks(self, language: str) -> List[str]:
        """Detect frameworks for a language."""
        frameworks = []
        
        if language == "python":
            # Check for common Python frameworks
            requirements = self.repo_root / "requirements.txt"
            pyproject = self.repo_root / "pyproject.toml"
            
            markers = {
                "fastapi": "FastAPI",
                "flask": "Flask",
                "django": "Django",
                "pytest": "pytest",
                "sqlalchemy": "SQLAlchemy",
            }
            
            for file_path in [requirements, pyproject]:
                if file_path.exists():
                    content = file_path.read_text().lower()
                    for marker, name in markers.items():
                        if marker in content:
                            frameworks.append(name)
        
        elif language == "csharp":
            # Check .csproj files for frameworks
            for csproj in self.repo_root.rglob("*.csproj"):
                content = csproj.read_text()
                if "Microsoft.AspNetCore" in content:
                    frameworks.append("ASP.NET Core")
                if "Microsoft.EntityFrameworkCore" in content:
                    frameworks.append("Entity Framework Core")
        
        return list(set(frameworks))
    
    def _select_provider(self, language: str) -> None:
        """Select appropriate language provider."""
        language = language.lower()
        
        provider_class = self._providers.get(language)
        if provider_class:
            self.provider = provider_class()
        else:
            # Default to Python provider
            self.provider = PythonProvider()
    
    def save_profile(self, profile: CodebaseProfile) -> Path:
        """Save profile to disk."""
        return self.profile_generator.save(profile)
    
    def get_summary(self, profile: CodebaseProfile) -> Dict[str, Any]:
        """Get a summary of the profile for display."""
        patterns_detected = sum(
            1 for p in profile.patterns.values() 
            if isinstance(p, PatternDetection) and p.detected
        )
        
        violations = 0
        if profile.architecture and "violations" in profile.architecture:
            violations = len(profile.architecture["violations"])
        
        return {
            "languages": len(profile.languages),
            "primary_language": profile.languages[0].name if profile.languages else "unknown",
            "architecture_style": profile.structure.get("style", "unknown"),
            "patterns_detected": patterns_detected,
            "architecture_violations": violations,
            "test_coverage": (
                profile.test_analysis.estimated_coverage 
                if profile.test_analysis else None
            ),
            "duration_ms": profile.discovery_metadata.duration_ms,
        }
```

---

## Phase 7: CLI Commands

Create the CLI interface for discovery operations.

### 7.1 `cli/commands/discover.py`

```python
"""
Discovery CLI Commands
======================

CLI interface for brownfield discovery operations.
"""

import sys
import json
from pathlib import Path
from typing import Optional


def _get_manager():
    """Get DiscoveryManager for current directory."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
    from discovery.manager import DiscoveryManager
    return DiscoveryManager(Path.cwd())


def run_discover(args):
    """Run brownfield discovery."""
    print("\n" + "=" * 60)
    print("BROWNFIELD DISCOVERY")
    print("=" * 60)
    
    manager = _get_manager()
    
    # Determine phases
    phases = None
    if hasattr(args, 'phase') and args.phase:
        phases = [args.phase]
    
    # Run discovery
    try:
        print("\nAnalyzing codebase...")
        print("-" * 40)
        
        profile = manager.discover(
            phases=phases,
            update=getattr(args, 'update', False),
        )
        
        # Get summary
        summary = manager.get_summary(profile)
        
        # Display results
        _display_results(profile, summary, getattr(args, 'verbose', False))
        
        # Save unless dry-run
        if not getattr(args, 'dry_run', False):
            output_path = manager.save_profile(profile)
            print(f"\n✓ Profile saved to: {output_path}")
        else:
            print("\n(dry-run: profile not saved)")
        
        # JSON output option
        if getattr(args, 'json', False):
            print("\n" + "-" * 40)
            print("JSON Output:")
            print(json.dumps(profile.to_dict(), indent=2, default=str))
        
        # Trigger conformance check unless disabled
        if not getattr(args, 'no_conformance', False):
            _trigger_conformance()
        
    except Exception as e:
        print(f"\nError during discovery: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _display_results(profile, summary, verbose: bool):
    """Display discovery results."""
    print(f"\nPhase 1: Language Detection")
    for lang in profile.languages:
        frameworks = f" ({', '.join(lang.frameworks)})" if lang.frameworks else ""
        print(f"  ✓ {lang.name}: {lang.percentage}%{frameworks}")
    
    print(f"\nPhase 2: Structure Analysis")
    style = profile.structure.get("style", "unknown")
    confidence = profile.structure.get("confidence", 0)
    print(f"  ✓ Architecture: {style} (confidence: {confidence:.2f})")
    
    layers = profile.structure.get("layers", [])
    if layers:
        print(f"  ✓ Layers: {', '.join(l.get('name', '?') for l in layers)}")
    
    entry_points = profile.structure.get("entry_points", [])
    if entry_points:
        print(f"  ✓ Entry points: {len(entry_points)} found")
    
    test_projects = profile.structure.get("test_projects", [])
    if test_projects:
        print(f"  ✓ Test projects: {len(test_projects)} found")
    
    print(f"\nPhase 3: Pattern Extraction")
    for name, pattern in profile.patterns.items():
        if hasattr(pattern, 'detected') and pattern.detected:
            primary = f" ({pattern.primary})" if hasattr(pattern, 'primary') and pattern.primary else ""
            conf = pattern.confidence if hasattr(pattern, 'confidence') else 0
            print(f"  ✓ {name}: detected{primary} (confidence: {conf:.2f})")
        elif verbose:
            print(f"  - {name}: not detected")
    
    if profile.architecture:
        print(f"\nPhase 4: Architecture Mapping")
        violations = profile.architecture.get("violations", [])
        if violations:
            print(f"  ⚠ {len(violations)} layer violations detected")
            if verbose:
                for v in violations[:5]:
                    print(f"    - {v.get('from_layer')} → {v.get('to_layer')}: {v.get('file_path')}")
        else:
            print(f"  ✓ No layer violations")
    
    if profile.conventions:
        print(f"\nPhase 5: Convention Inference")
        naming = profile.conventions.get("naming", {})
        for conv_type, conv_data in naming.items():
            if isinstance(conv_data, dict):
                pattern = conv_data.get("pattern", "unknown")
                consistency = conv_data.get("consistency", 0)
                print(f"  ✓ {conv_type}: {pattern} (consistency: {consistency:.0%})")
    
    if profile.test_analysis:
        print(f"\nPhase 6: Test Gap Analysis")
        inv = profile.test_analysis.inventory
        print(f"  ✓ {inv.total_test_methods} tests in {inv.total_test_files} files")
        print(f"  ✓ Frameworks: {', '.join(inv.frameworks) or 'unknown'}")
        print(f"  ✓ Estimated coverage: {profile.test_analysis.estimated_coverage:.0%}")
        
        gaps = profile.test_analysis.gaps
        if gaps:
            print(f"  ⚠ {len(gaps)} files without tests")
    
    # Summary
    print("\n" + "-" * 40)
    print("Summary:")
    print(f"  Primary language: {summary['primary_language']}")
    print(f"  Architecture: {summary['architecture_style']}")
    print(f"  Patterns detected: {summary['patterns_detected']}")
    print(f"  Architecture violations: {summary['architecture_violations']}")
    if summary['test_coverage'] is not None:
        print(f"  Test coverage (est.): {summary['test_coverage']:.0%}")
    print(f"  Analysis time: {summary['duration_ms']}ms")


def _trigger_conformance():
    """Trigger conformance check if available."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
        from conformance.manager import ConformanceManager
        
        manager = ConformanceManager(Path.cwd())
        if manager.is_initialized():
            print("\n" + "-" * 40)
            print("Triggering conformance check...")
            # This would integrate with Chunk 3
            print("(conformance integration pending)")
    except ImportError:
        pass  # Conformance not available
```

### 7.2 Update `cli/parser.py`

Add the discover command to the CLI parser:

```python
# Add to cli/parser.py

def create_parser():
    # ... existing code ...
    
    # Add discover command
    discover_parser = subparsers.add_parser(
        'discover',
        help='Run brownfield discovery'
    )
    discover_parser.add_argument(
        '--phase',
        choices=['language', 'structure', 'patterns', 'architecture', 'conventions', 'tests'],
        help='Run specific phase only'
    )
    discover_parser.add_argument(
        '--update',
        action='store_true',
        help='Update existing profile (preserve human curations)'
    )
    discover_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be discovered without saving'
    )
    discover_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    discover_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    discover_parser.add_argument(
        '--no-conformance',
        action='store_true',
        help='Skip automatic conformance check'
    )
```

---

## Phase 8: Integration with Chunk 3

Connect discovery to the conformance system.

### 8.1 Conformance Integration

After discovery completes, violations should flow to Chunk 3:

```python
# In discovery/manager.py, add to discover() method:

def _integrate_with_conformance(self, profile: CodebaseProfile) -> None:
    """Send architecture violations to conformance system."""
    try:
        from conformance.manager import ConformanceManager
        
        conformance = ConformanceManager(self.repo_root)
        if not conformance.is_initialized():
            return
        
        # Convert architecture violations to conformance format
        if profile.architecture and "violations" in profile.architecture:
            for violation in profile.architecture["violations"]:
                # Create conformance-compatible violation
                # This integrates with FR-013
                pass
    except ImportError:
        pass  # Conformance not available
```

---

## Testing Strategy

### Unit Tests

Create `tests/unit/tools/discovery/`:

```
tests/unit/tools/discovery/
├── __init__.py
├── test_domain.py
├── test_providers.py
├── test_analyzers.py
├── test_manager.py
└── test_generators.py
```

### Test Fixtures

Create sample projects for testing:

```
tests/fixtures/discovery/
├── python_clean_arch/
│   ├── pyproject.toml
│   ├── src/
│   │   ├── domain/
│   │   │   └── entities.py
│   │   ├── application/
│   │   │   └── services.py
│   │   └── infrastructure/
│   │       └── persistence.py
│   └── tests/
│       └── test_entities.py
├── python_minimal/
│   ├── requirements.txt
│   └── main.py
└── mixed_patterns/
    └── ...
```

### Key Test Cases

1. **Language Detection**: Verify correct language identification
2. **Structure Analysis**: Verify layer detection for Clean Architecture
3. **Pattern Extraction**: Verify Result<T>, CQRS patterns detected
4. **Convention Inference**: Verify naming conventions detected
5. **Profile Generation**: Verify valid YAML output

---

## Acceptance Criteria Checklist

### Must Have

- [ ] Language detection works for Python
- [ ] Structure analysis detects Clean Architecture
- [ ] At least 3 patterns detected (error_handling, cqrs, repository)
- [ ] CLI `agentforge discover` runs successfully
- [ ] Generates valid codebase_profile.yaml
- [ ] Profile validates against schema

### Should Have

- [ ] Convention inference works
- [ ] Test gap analysis works
- [ ] Architecture violations detected
- [ ] Conformance integration triggers

### Nice to Have

- [ ] .NET provider implemented
- [ ] Incremental discovery
- [ ] Human curation workflow

---

## Implementation Notes

### Start Here

1. Create the directory structure
2. Implement domain.py (entities)
3. Implement python_provider.py
4. Implement structure analyzer
5. Test on AgentForge itself

### Key Files to Create

| File | Priority | Lines (est.) |
|------|----------|--------------|
| `tools/discovery/domain.py` | P0 | 300 |
| `tools/discovery/providers/base.py` | P0 | 150 |
| `tools/discovery/providers/python_provider.py` | P0 | 350 |
| `tools/discovery/analyzers/structure.py` | P0 | 200 |
| `tools/discovery/analyzers/patterns.py` | P0 | 300 |
| `tools/discovery/analyzers/architecture.py` | P1 | 200 |
| `tools/discovery/analyzers/conventions.py` | P1 | 250 |
| `tools/discovery/analyzers/tests.py` | P1 | 200 |
| `tools/discovery/generators/profile.py` | P0 | 150 |
| `tools/discovery/manager.py` | P0 | 300 |
| `cli/commands/discover.py` | P0 | 200 |

**Total: ~2,600 lines**

### Validation

Test on AgentForge itself:

```bash
cd /path/to/agentforge
python execute.py discover --verbose
```

Expected output:
- Detects Python as primary language
- Identifies pytest framework
- Detects patterns from existing code
- Generates .agentforge/codebase_profile.yaml

---

*End of Implementation Task*
