"""
Structure Analyzer
==================

Detects architectural patterns from directory structure and organization.
Identifies Clean Architecture layers, module boundaries, and project layout.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..domain import Detection, DetectionSource, LayerInfo
from ..providers.base import LanguageProvider

# Clean Architecture layer patterns
LAYER_PATTERNS = {
    "domain": {
        "directories": ["domain", "core", "entities", "model", "models"],
        "file_patterns": ["entity", "value_object", "aggregate", "domain_event"],
        "weight": 1.0,
    },
    "application": {
        "directories": ["application", "app", "use_cases", "usecases", "services"],
        "file_patterns": ["command", "query", "handler", "service", "use_case"],
        "weight": 0.9,
    },
    "infrastructure": {
        "directories": ["infrastructure", "infra", "persistence", "adapters"],
        "file_patterns": ["repository", "adapter", "gateway", "client"],
        "weight": 0.9,
    },
    "presentation": {
        "directories": ["api", "web", "ui", "presentation", "controllers", "views"],
        "file_patterns": ["controller", "endpoint", "view", "router"],
        "weight": 0.8,
    },
}

# Common project structure patterns
STRUCTURE_PATTERNS = {
    "clean_architecture": {
        "required_layers": ["domain", "application"],
        "optional_layers": ["infrastructure", "presentation"],
        "min_layers": 2,
    },
    "hexagonal": {
        "required_layers": ["domain"],
        "markers": ["ports", "adapters"],
        "min_layers": 1,
    },
    "layered": {
        "required_layers": ["presentation", "application"],
        "optional_layers": ["domain", "infrastructure"],
        "min_layers": 2,
    },
    "flat": {
        "required_layers": [],
        "min_layers": 0,
    },
}


@dataclass
class DirectoryInfo:
    """Information about a directory in the project."""
    path: Path
    relative_path: str
    file_count: int = 0
    total_lines: int = 0
    detected_layer: str | None = None
    confidence: float = 0.0
    signals: list[str] = field(default_factory=list)


@dataclass
class StructureAnalysisResult:
    """Result of structure analysis."""
    architecture_style: str
    confidence: float
    layers: dict[str, LayerInfo]
    directories: list[DirectoryInfo]
    entry_points: list[Path]
    test_directories: list[Path]
    source_root: Path | None = None
    signals: list[str] = field(default_factory=list)


class StructureAnalyzer:
    """
    Analyzes codebase structure to detect architectural patterns.

    Uses multiple signals:
    - Directory naming conventions
    - File organization patterns
    - Import relationships (via provider)
    - Code distribution metrics
    """

    def __init__(self, provider: LanguageProvider):
        self.provider = provider
        self._dir_cache: dict[Path, DirectoryInfo] = {}
        self._dotnet_projects: dict[str, dict[str, Any]] = {}

    def analyze(self, root: Path) -> StructureAnalysisResult:
        """
        Perform full structure analysis on a codebase.

        Args:
            root: Root directory of the codebase

        Returns:
            StructureAnalysisResult with detected architecture
        """
        # For .NET projects, detect layers from project names first
        if self.provider.language_name == "csharp":
            self._detect_dotnet_layers(root)

        # Find all relevant directories
        directories = self._scan_directories(root)

        # Detect layers in each directory
        for dir_info in directories:
            self._detect_layer(dir_info, root)

        # Aggregate into layer information
        layers = self._aggregate_layers(directories)

        # Detect architecture style
        style, style_confidence, signals = self._detect_architecture_style(layers)

        # Find entry points and test directories
        entry_points = self._find_entry_points(root)
        test_dirs = self._find_test_directories(root)

        # Detect source root
        source_root = self._detect_source_root(root, directories)

        return StructureAnalysisResult(
            architecture_style=style,
            confidence=style_confidence,
            layers=layers,
            directories=directories,
            entry_points=entry_points,
            test_directories=test_dirs,
            source_root=source_root,
            signals=signals,
        )

    def _scan_directories(self, root: Path) -> list[DirectoryInfo]:
        """Scan and catalog all directories containing source files."""
        directories = []
        source_files = self.provider.get_source_files(root)

        # Group files by directory
        dir_files: dict[Path, list[Path]] = {}
        for f in source_files:
            parent = f.parent
            if parent not in dir_files:
                dir_files[parent] = []
            dir_files[parent].append(f)

        # Create DirectoryInfo for each
        for dir_path, files in dir_files.items():
            try:
                relative = dir_path.relative_to(root)
            except ValueError:
                relative = dir_path

            total_lines = sum(self.provider.count_lines(f) for f in files)

            info = DirectoryInfo(
                path=dir_path,
                relative_path=str(relative),
                file_count=len(files),
                total_lines=total_lines,
            )
            directories.append(info)
            self._dir_cache[dir_path] = info

        return directories

    def _detect_layer(self, dir_info: DirectoryInfo, root: Path) -> None:
        """Detect which architectural layer a directory belongs to."""
        path_parts = Path(dir_info.relative_path).parts
        dir_info.relative_path.lower()

        best_match = None
        best_score = 0.0
        signals = []

        for layer_name, layer_config in LAYER_PATTERNS.items():
            score = 0.0
            layer_signals = []

            # Check directory name matches
            for pattern in layer_config["directories"]:
                # Exact match on any path component
                for part in path_parts:
                    if part.lower() == pattern:
                        score += 0.8 * layer_config["weight"]
                        layer_signals.append(f"directory_exact:{pattern}")
                        break
                    elif pattern in part.lower():
                        score += 0.4 * layer_config["weight"]
                        layer_signals.append(f"directory_partial:{pattern}")

            # Check file pattern matches in directory
            files_in_dir = list(dir_info.path.glob(f"*{list(self.provider.file_extensions)[0]}"))
            for file_pattern in layer_config["file_patterns"]:
                matching_files = [f for f in files_in_dir if file_pattern in f.stem.lower()]
                if matching_files:
                    score += 0.3 * layer_config["weight"] * min(len(matching_files) / 3, 1.0)
                    layer_signals.append(f"file_pattern:{file_pattern}({len(matching_files)})")

            if score > best_score:
                best_score = score
                best_match = layer_name
                signals = layer_signals

        if best_match and best_score >= 0.3:
            dir_info.detected_layer = best_match
            dir_info.confidence = min(best_score, 1.0)
            dir_info.signals = signals

    def _aggregate_layers(self, directories: list[DirectoryInfo]) -> dict[str, LayerInfo]:
        """Aggregate directory detections into layer information."""
        layers: dict[str, LayerInfo] = {}

        for dir_info in directories:
            if not dir_info.detected_layer:
                continue

            layer_name = dir_info.detected_layer

            if layer_name not in layers:
                layers[layer_name] = LayerInfo(
                    name=layer_name,
                    paths=[],
                    file_count=0,
                    line_count=0,
                    detection=Detection(
                        value=layer_name,
                        confidence=0.0,
                        source=DetectionSource.STRUCTURAL,
                        signals=[],
                    ),
                )

            layer = layers[layer_name]
            layer.paths.append(dir_info.relative_path)
            layer.file_count += dir_info.file_count
            layer.line_count += dir_info.total_lines
            layer.detection.signals.extend(dir_info.signals)

            # Update confidence as weighted average
            total_files = sum(d.file_count for d in directories if d.detected_layer == layer_name)
            if total_files > 0:
                weighted_conf = sum(
                    d.confidence * d.file_count
                    for d in directories
                    if d.detected_layer == layer_name
                ) / total_files
                layer.detection.confidence = weighted_conf

        return layers

    def _detect_architecture_style(
        self, layers: dict[str, LayerInfo]
    ) -> tuple[str, float, list[str]]:
        """Detect the overall architecture style from detected layers."""
        detected_layer_names = set(layers.keys())
        signals = []

        best_style = "unknown"
        best_score = 0.0

        for style_name, style_config in STRUCTURE_PATTERNS.items():
            required = set(style_config.get("required_layers", []))
            optional = set(style_config.get("optional_layers", []))
            markers = set(style_config.get("markers", []))
            min_layers = style_config.get("min_layers", 0)

            # Check required layers
            if not required.issubset(detected_layer_names):
                continue

            # Calculate score
            score = 0.0
            style_signals = []

            # Required layers matched
            if required:
                score += 0.5 * (len(required & detected_layer_names) / len(required))
                style_signals.append(f"required_layers:{required & detected_layer_names}")

            # Optional layers present
            if optional:
                optional_present = optional & detected_layer_names
                score += 0.3 * (len(optional_present) / len(optional))
                if optional_present:
                    style_signals.append(f"optional_layers:{optional_present}")

            # Marker directories (for hexagonal)
            if markers:
                # Would need to scan for these specifically
                pass

            # Layer count bonus
            if len(detected_layer_names) >= min_layers:
                score += 0.2

            if score > best_score:
                best_score = score
                best_style = style_name
                signals = style_signals

        # Confidence based on how many layers we detected
        if detected_layer_names:
            avg_layer_confidence = sum(
                l.detection.confidence for l in layers.values()
            ) / len(layers)
            final_confidence = (best_score + avg_layer_confidence) / 2
        else:
            final_confidence = 0.0
            best_style = "flat"

        return best_style, final_confidence, signals

    def _find_entry_points(self, root: Path) -> list[Path]:
        """Find application entry points."""
        entry_points = []

        # Common entry point patterns
        patterns = [
            "main.py", "__main__.py", "app.py", "cli.py",
            "manage.py", "wsgi.py", "asgi.py", "execute.py",
        ]

        for pattern in patterns:
            matches = list(root.rglob(pattern))
            entry_points.extend(matches)

        # Also check for scripts in pyproject.toml
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            entry_points.extend(self._find_pyproject_scripts(pyproject))

        return list(set(entry_points))

    def _find_pyproject_scripts(self, pyproject: Path) -> list[Path]:
        """Extract script entry points from pyproject.toml."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return []

        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)

            scripts = data.get("project", {}).get("scripts", {})
            entry_points = []

            for _name, entry in scripts.items():
                # Entry format: "module:function"
                if ":" in entry:
                    module = entry.split(":")[0]
                    module_path = module.replace(".", "/") + ".py"
                    full_path = pyproject.parent / module_path
                    if full_path.exists():
                        entry_points.append(full_path)

            return entry_points
        except Exception:
            return []

    def _find_test_directories(self, root: Path) -> list[Path]:
        """Find test directories in the project."""
        test_dirs = []

        patterns = ["tests", "test", "testing", "spec", "specs"]

        for pattern in patterns:
            # Direct children
            direct = root / pattern
            if direct.is_dir():
                test_dirs.append(direct)

            # Also check src/tests pattern
            src_test = root / "src" / pattern
            if src_test.is_dir():
                test_dirs.append(src_test)

        return test_dirs

    def _detect_source_root(
        self, root: Path, directories: list[DirectoryInfo]
    ) -> Path | None:
        """Detect the main source root directory."""
        # Common source root patterns
        patterns = ["src", "lib", "app", "source"]

        for pattern in patterns:
            candidate = root / pattern
            if candidate.is_dir():
                # Check if it has source files
                has_files = any(d.path.is_relative_to(candidate) for d in directories)
                if has_files:
                    return candidate

        # If no standard pattern, check if root itself is the source root
        root_files = any(d.path == root for d in directories)
        if root_files:
            return root

        # Return directory with most source files
        if directories:
            by_files = sorted(directories, key=lambda d: d.file_count, reverse=True)
            if by_files:
                return by_files[0].path.parent

        return None

    def get_layer_for_path(self, path: Path) -> str | None:
        """Get the detected layer for a given path."""
        if path in self._dir_cache:
            return self._dir_cache[path].detected_layer

        # Check parent directories
        for parent in path.parents:
            if parent in self._dir_cache:
                return self._dir_cache[parent].detected_layer

        return None

    def _detect_dotnet_layers(self, root: Path) -> None:
        """
        Detect layers from .NET project names.

        .NET Clean Architecture projects typically follow naming conventions:
        - Company.Project.Domain → domain layer
        - Company.Project.Application → application layer
        - Company.Project.Infrastructure → infrastructure layer
        - Company.Project.Api/Web → presentation layer
        """
        # .NET layer indicators in project names
        dotnet_layer_patterns = {
            "domain": [".domain", ".core", ".entities", ".model"],
            "application": [".application", ".usecases", ".services", ".business"],
            "infrastructure": [".infrastructure", ".persistence", ".data", ".repository", ".external"],
            "presentation": [".api", ".web", ".presentation", ".ui", ".mvc", ".blazor", ".grpc"],
        }

        # Find all csproj files
        for csproj in root.rglob("*.csproj"):
            project_name = csproj.stem.lower()
            project_dir = csproj.parent

            detected_layer = None
            confidence = 0.0
            signals = []

            for layer, patterns in dotnet_layer_patterns.items():
                for pattern in patterns:
                    if pattern in project_name:
                        detected_layer = layer
                        confidence = 0.9  # High confidence for explicit naming
                        signals.append(f"project_name:{pattern}")
                        break
                if detected_layer:
                    break

            if detected_layer:
                self._dotnet_projects[str(csproj)] = {
                    "layer": detected_layer,
                    "confidence": confidence,
                    "signals": signals,
                    "directory": project_dir,
                }

                # Pre-populate directory cache
                try:
                    relative = project_dir.relative_to(root)
                except ValueError:
                    relative = project_dir

                self._dir_cache[project_dir] = DirectoryInfo(
                    path=project_dir,
                    relative_path=str(relative),
                    detected_layer=detected_layer,
                    confidence=confidence,
                    signals=signals,
                )

    def _find_dotnet_entry_points(self, root: Path) -> list[Path]:
        """Find .NET application entry points."""
        entry_points = []

        for csproj in root.rglob("*.csproj"):
            try:
                content = csproj.read_text(encoding='utf-8')

                # Check for executable output type
                if "<OutputType>Exe</OutputType>" in content:
                    entry_points.append(csproj)
                    continue

                # Check for web SDK (ASP.NET Core)
                if 'Sdk="Microsoft.NET.Sdk.Web"' in content:
                    entry_points.append(csproj)
                    continue

                # Check for common web packages
                if "Microsoft.AspNetCore" in content:
                    entry_points.append(csproj)
                    continue

            except Exception:
                continue

        return entry_points

    def _find_dotnet_test_directories(self, root: Path) -> list[Path]:
        """Find .NET test project directories."""
        test_dirs = []

        for csproj in root.rglob("*.csproj"):
            project_name = csproj.stem.lower()

            # Check project name
            if any(test in project_name for test in [".test", ".tests", "test.", "tests."]):
                test_dirs.append(csproj.parent)
                continue

            # Check for test packages
            try:
                content = csproj.read_text(encoding='utf-8')
                test_packages = ["xunit", "nunit", "mstest", "Microsoft.NET.Test.Sdk"]
                if any(pkg in content for pkg in test_packages):
                    test_dirs.append(csproj.parent)
            except Exception:
                continue

        return test_dirs
