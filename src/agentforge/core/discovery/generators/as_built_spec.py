"""
As-Built Specification Generator
================================

Generates specification YAML files from discovered code, implementing the
Artifact Parity Principle. After brownfield discovery, the generated specs
are identical in structure to greenfield specs.

The generated specs enable:
1. Lineage metadata embedding in source files
2. Proper spec_id → component_id → test_path chain
3. Full audit trail for violations and fixes
"""

import ast
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ..domain import SourceTestLinkage, CoverageGapAnalysis


@dataclass
class DiscoveredEntity:
    """An entity (class, function, enum) discovered in code."""
    name: str
    entity_type: str  # "class", "function", "enum", "dataclass"
    line_number: int
    description: str = ""
    methods: list[str] = field(default_factory=list)
    test_methods: list[str] = field(default_factory=list)


@dataclass
class DiscoveredComponent:
    """A component (module/file) discovered in code."""
    name: str  # e.g., "context_models"
    location: str  # e.g., "src/agentforge/core/harness/minimal_context/context_models.py"
    test_location: str | None = None  # e.g., "tests/unit/harness/test_context_models.py"
    description: str = ""
    entities: list[DiscoveredEntity] = field(default_factory=list)

    @property
    def component_id(self) -> str:
        """Generate a stable component_id from the component name."""
        # Use module path to create unique ID
        path_parts = self.location.replace("/", "-").replace("\\", "-")
        if path_parts.endswith(".py"):
            path_parts = path_parts[:-3]
        # Simplify: take last 2-3 parts
        parts = path_parts.split("-")
        if len(parts) > 3:
            parts = parts[-3:]
        return "-".join(parts).lower()


@dataclass
class AsBuiltSpec:
    """An as-built specification generated from discovered code."""
    spec_id: str
    name: str
    version: str = "1.0"
    status: str = "as-built"
    description: str = ""
    components: list[DiscoveredComponent] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to YAML-compatible dict."""
        return {
            "spec_id": self.spec_id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "schema_version": "2.0",
            "generated_at": self.generated_at.isoformat(),
            "generated_by": "brownfield-discovery",
            "description": self.description,
            "components": [
                {
                    "name": c.name,
                    "component_id": c.component_id,
                    "location": c.location,
                    "test_location": c.test_location,
                    "description": c.description,
                    "entities": [
                        {
                            "name": e.name,
                            "type": e.entity_type,
                            "line_number": e.line_number,
                            "description": e.description,
                            "methods": e.methods,
                            "test_methods": e.test_methods,
                        }
                        for e in c.entities
                    ],
                }
                for c in self.components
            ],
        }


class AsBuiltSpecGenerator:
    """
    Generates as-built specifications from brownfield discovery results.

    The generated specs follow the same structure as greenfield specs,
    enabling full lineage tracking and orchestration engine integration.
    """

    # Path prefixes to strip for cleaner spec names
    # These are common project structure prefixes that add noise
    STRIP_PREFIXES = [
        "src-agentforge-",
        "src/agentforge/",
        "tools-",
        "tools/",
        "lib-",
        "lib/",
    ]

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.specs_dir = root_path / ".agentforge" / "specs"

    def _simplify_path(self, path: str) -> str:
        """
        Simplify a path by removing common project prefixes.

        Examples:
            src/agentforge/core/harness -> core-harness
            tools/discovery -> discovery
            src-agentforge-core-v1 -> core-v1
        """
        result = path

        # Normalize separators
        result = result.replace("/", "-").replace("\\", "-")

        # Strip common prefixes
        for prefix in self.STRIP_PREFIXES:
            normalized_prefix = prefix.replace("/", "-").replace("\\", "-")
            if result.startswith(normalized_prefix):
                result = result[len(normalized_prefix):]
                break

        # Clean up any leading/trailing dashes
        result = result.strip("-")

        return result

    def generate_from_test_analysis(
        self,
        test_analysis: CoverageGapAnalysis,
        zone_name: str = "main",
    ) -> list[AsBuiltSpec]:
        """
        Generate as-built specs from test analysis linkages.

        Groups source files by directory/module and creates a spec per group.

        Args:
            test_analysis: Test analysis with source-to-test linkages
            zone_name: Name of the code zone (for multi-zone repos)

        Returns:
            List of generated AsBuiltSpec objects
        """
        # Group linkages by directory
        dir_groups: dict[str, list[SourceTestLinkage]] = {}

        for linkage in test_analysis.linkages:
            source_path = Path(linkage.source_path)
            # Use parent directory as grouping key
            parent = str(source_path.parent)
            if parent not in dir_groups:
                dir_groups[parent] = []
            dir_groups[parent].append(linkage)

        specs = []
        for dir_path, linkages in dir_groups.items():
            spec = self._generate_spec_for_directory(dir_path, linkages, zone_name)
            if spec and spec.components:
                specs.append(spec)

        return specs

    def _generate_spec_for_directory(
        self,
        dir_path: str,
        linkages: list[SourceTestLinkage],
        zone_name: str,
    ) -> AsBuiltSpec | None:
        """Generate a spec for a single directory."""
        # Simplify the path (removes src-agentforge-, tools-, etc.)
        simplified = self._simplify_path(dir_path)

        # Generate spec_id from simplified path
        spec_id = f"{simplified}-v1".lower()

        # Clean up spec_id (only alphanumeric and dashes)
        spec_id = re.sub(r"[^a-z0-9-]", "-", spec_id)
        spec_id = re.sub(r"-+", "-", spec_id)
        spec_id = spec_id.strip("-")

        # Generate human-readable name
        name = simplified.replace("-", "_")

        spec = AsBuiltSpec(
            spec_id=spec_id,
            name=name,
            description=f"Specification for {dir_path}",
        )

        for linkage in linkages:
            component = self._analyze_source_file(linkage)
            if component:
                spec.components.append(component)

        return spec

    def _analyze_source_file(self, linkage: SourceTestLinkage) -> DiscoveredComponent | None:
        """Analyze a source file to extract component information."""
        source_path = self.root_path / linkage.source_path

        if not source_path.exists() or source_path.suffix != ".py":
            return None

        try:
            content = source_path.read_text()
        except Exception:
            return None

        # Extract module name from path
        module_name = source_path.stem

        # Parse entities from source
        entities = self._extract_entities(content)

        # Match entities to test methods if we have test info
        if linkage.test_paths:
            for test_path in linkage.test_paths:
                self._match_test_methods(entities, test_path)

        component = DiscoveredComponent(
            name=module_name,
            location=linkage.source_path,
            test_location=linkage.test_paths[0] if linkage.test_paths else None,
            description=self._extract_module_docstring(content),
            entities=entities,
        )

        return component

    def _extract_entities(self, content: str) -> list[DiscoveredEntity]:
        """Extract classes, functions, and enums from Python source."""
        entities = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return entities

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                entity_type = self._classify_class(node)
                methods = [
                    m.name for m in node.body
                    if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")
                ]

                entities.append(DiscoveredEntity(
                    name=node.name,
                    entity_type=entity_type,
                    line_number=node.lineno,
                    description=ast.get_docstring(node) or "",
                    methods=methods,
                ))

            elif isinstance(node, ast.FunctionDef):
                # Only top-level functions (not methods)
                if not node.name.startswith("_"):
                    entities.append(DiscoveredEntity(
                        name=node.name,
                        entity_type="function",
                        line_number=node.lineno,
                        description=ast.get_docstring(node) or "",
                    ))

        return entities

    def _classify_class(self, node: ast.ClassDef) -> str:
        """Classify a class as enum, dataclass, or regular class."""
        if self._is_enum_class(node):
            return "enum"
        if self._is_dataclass(node):
            return "dataclass"
        return "class"

    def _is_enum_class(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from an Enum type."""
        enum_types = {"Enum", "IntEnum", "StrEnum"}
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in enum_types:
                return True
            if isinstance(base, ast.Attribute) and base.attr in enum_types:
                return True
        return False

    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        """Check if class has dataclass decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                return True
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == "dataclass":
                    return True
        return False

    def _extract_module_docstring(self, content: str) -> str:
        """Extract the module-level docstring."""
        try:
            tree = ast.parse(content)
            return ast.get_docstring(tree) or ""
        except SyntaxError:
            return ""

    def _match_test_methods(self, entities: list[DiscoveredEntity], test_path: str) -> None:
        """Match test methods to entities by naming convention."""
        full_test_path = self.root_path / test_path

        if not full_test_path.exists():
            return

        try:
            content = full_test_path.read_text()
        except Exception:
            return

        # Find test methods and match to entities
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_name = node.name
                # Try to match to entities
                for entity in entities:
                    entity_lower = entity.name.lower()
                    if entity_lower in test_name.lower():
                        if test_name not in entity.test_methods:
                            entity.test_methods.append(test_name)

    def save_specs(self, specs: list[AsBuiltSpec]) -> list[Path]:
        """Save generated specs to disk."""
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for spec in specs:
            # Create filename from spec_id
            filename = f"{spec.spec_id}.yaml"
            filepath = self.specs_dir / filename

            yaml_content = yaml.dump(
                spec.to_dict(),
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

            # Add header (generic - the status field in YAML indicates as-built)
            header = f"""# ═══════════════════════════════════════════════════════════════════════════════
# Specification: {spec.name}
# ═══════════════════════════════════════════════════════════════════════════════
# Generated: {spec.generated_at.isoformat()}
# Generator: brownfield-discovery
# ═══════════════════════════════════════════════════════════════════════════════

"""
            filepath.write_text(header + yaml_content)
            saved_paths.append(filepath)

        return saved_paths

    def generate_lineage_updates(
        self,
        specs: list[AsBuiltSpec],
    ) -> dict[str, dict[str, str]]:
        """
        Generate lineage metadata updates for source files.

        Returns a dict mapping source_path -> lineage metadata to embed.

        Example:
            {
                "tools/context.py": {
                    "spec_file": ".agentforge/specs/as-built-tools-v1.yaml",
                    "spec_id": "as-built-tools-v1",
                    "component_id": "context",
                    "test_path": "tests/unit/test_context.py",
                }
            }
        """
        updates = {}

        for spec in specs:
            spec_file = f".agentforge/specs/{spec.spec_id}.yaml"

            for component in spec.components:
                updates[component.location] = {
                    "spec_file": spec_file,
                    "spec_id": spec.spec_id,
                    "component_id": component.component_id,
                    "test_path": component.test_location,
                }

                # Also generate updates for test files (linking back to impl)
                if component.test_location:
                    updates[component.test_location] = {
                        "spec_file": spec_file,
                        "spec_id": spec.spec_id,
                        "component_id": component.component_id,
                        "impl_path": component.location,
                    }

        return updates
