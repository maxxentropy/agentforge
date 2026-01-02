# @spec_file: .agentforge/specs/core-bridge-mappings-v1.yaml
# @spec_id: core-bridge-mappings-v1
# @component_id: bridge-mappings-architecture
# @test_path: tests/unit/tools/bridge/test_registry.py

"""
Architecture Pattern Mappings
=============================

Mappings for architectural patterns like Clean Architecture,
Hexagonal Architecture, and layer dependency enforcement.
"""


from ..domain import CheckTemplate, MappingContext
from .base import PatternMapping
from .registry import MappingRegistry


@MappingRegistry.register
class CleanArchitectureMapping(PatternMapping):
    """
    Clean Architecture layer enforcement.

    Generates checks for:
    - Domain layer isolation (no outer dependencies)
    - Application layer isolation (only depends on Domain)
    - Presentation no direct Infrastructure access
    """

    pattern_key = "clean-architecture"
    languages = ["csharp", "python", "typescript"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when Clean Architecture is detected."""
        style = context.get_architecture_style()
        if style and "clean" in style.lower():
            return True

        # Check for layer structure that indicates Clean Architecture
        return (
            context.has_layer("domain") and
            context.has_layer("application") and
            (context.has_layer("infrastructure") or context.has_layer("presentation"))
        )

    def get_templates(self, context: MappingContext) -> list[CheckTemplate]:
        """Get Clean Architecture check templates."""
        templates = []

        # Domain isolation
        domain_paths = context.get_layer_paths("domain")
        if domain_paths or context.has_layer("domain"):
            templates.append(CheckTemplate(
                id_template="{zone}-domain-isolation",
                name="Domain Layer Isolation",
                description="Domain must not depend on outer layers",
                check_type="architecture",
                severity="error",
                config={
                    "layer": "domain",
                    "forbidden_dependencies": [
                        "infrastructure",
                        "presentation",
                        "api",
                        "web",
                    ],
                },
                applies_to_paths=domain_paths or ["**/Domain/**"],
            ))

        # Application isolation
        application_paths = context.get_layer_paths("application")
        if application_paths or context.has_layer("application"):
            templates.append(CheckTemplate(
                id_template="{zone}-application-isolation",
                name="Application Layer Isolation",
                description="Application may only depend on Domain",
                check_type="architecture",
                severity="error",
                config={
                    "layer": "application",
                    "allowed_dependencies": ["domain"],
                    "forbidden_dependencies": [
                        "infrastructure",
                        "presentation",
                    ],
                },
                applies_to_paths=application_paths or ["**/Application/**"],
            ))

        # Presentation no direct Infrastructure
        presentation_paths = context.get_layer_paths("presentation")
        if presentation_paths or context.has_layer("presentation"):
            templates.append(CheckTemplate(
                id_template="{zone}-presentation-no-infra",
                name="Presentation No Direct Infrastructure",
                description="Presentation should not directly access Infrastructure",
                check_type="architecture",
                severity="warning",
                config={
                    "layer": "presentation",
                    "forbidden_dependencies": ["infrastructure"],
                },
                applies_to_paths=presentation_paths or ["**/Presentation/**", "**/Api/**"],
            ))

        return templates


@MappingRegistry.register
class HexagonalArchitectureMapping(PatternMapping):
    """
    Hexagonal/Ports & Adapters Architecture enforcement.

    Generates checks for:
    - Core/Domain isolation
    - Adapter implementations
    - Port interface definitions
    """

    pattern_key = "hexagonal-architecture"
    languages = ["csharp", "python"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when Hexagonal Architecture is detected."""
        style = context.get_architecture_style()
        if style and "hexagonal" in style.lower():
            return True
        if style and "ports" in style.lower():
            return True

        # Check for port/adapter structure
        return context.has_layer("ports") or context.has_layer("adapters")

    def get_templates(self, context: MappingContext) -> list[CheckTemplate]:
        """Get Hexagonal Architecture check templates."""
        templates = []

        # Core isolation
        templates.append(CheckTemplate(
            id_template="{zone}-hexagonal-core-isolation",
            name="Hexagonal Core Isolation",
            description="Core/Domain must not depend on adapters",
            check_type="architecture",
            severity="error",
            config={
                "layer": "core",
                "forbidden_dependencies": ["adapters", "infrastructure"],
            },
            applies_to_paths=["**/Core/**", "**/Domain/**"],
        ))

        # Ports are interfaces only
        templates.append(CheckTemplate(
            id_template="{zone}-hexagonal-ports-interfaces",
            name="Ports Are Interfaces",
            description="Ports should only contain interfaces",
            check_type="naming",
            severity="warning",
            config={
                "pattern": "^I[A-Z].*",
                "symbol_type": "interface",
                "required_in_path": True,
            },
            applies_to_paths=["**/Ports/**"],
            review_reason="Verify port structure matches hexagonal pattern",
        ))

        return templates


@MappingRegistry.register
class LayerViolationMapping(PatternMapping):
    """
    Generic layer violation detection based on discovered layers.

    Works with any layer structure found in the profile.
    """

    pattern_key = "layer-structure"
    languages = []  # All languages
    min_confidence = 0.5
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when any layer structure is detected."""
        layers = context.structure.get("layers", {})
        return len(layers) >= 2

    def get_templates(self, context: MappingContext) -> list[CheckTemplate]:
        """Generate layer checks dynamically based on discovered layers."""
        templates = []
        layers = context.structure.get("layers", {})

        # Define layer hierarchy (inner → outer)
        layer_order = ["domain", "application", "infrastructure", "presentation", "api"]

        for layer_name, layer_info in layers.items():
            layer_paths = layer_info.get("paths", [])
            if not layer_paths:
                continue

            # Find forbidden dependencies (layers that are "outer")
            layer_idx = layer_order.index(layer_name) if layer_name in layer_order else -1
            if layer_idx >= 0:
                forbidden = [l for l in layer_order[layer_idx + 1:] if l in layers]
                if forbidden:
                    templates.append(CheckTemplate(
                        id_template=f"{{zone}}-{layer_name}-no-outer-deps",
                        name=f"{layer_name.title()} No Outer Dependencies",
                        description=f"{layer_name.title()} should not depend on outer layers",
                        check_type="architecture",
                        severity="warning",
                        config={
                            "layer": layer_name,
                            "forbidden_dependencies": forbidden,
                        },
                        applies_to_paths=layer_paths,
                    ))

        return templates
