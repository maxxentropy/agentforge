# @spec_file: .agentforge/specs/core-bridge-mappings-v1.yaml
# @spec_id: core-bridge-mappings-v1
# @component_id: bridge-mappings-repository
# @test_path: tests/unit/tools/bridge/test_registry.py

"""
Repository Pattern Mappings
===========================

Mappings for Repository pattern enforcement.
"""

from typing import List

from bridge.mappings.base import PatternMapping
from bridge.mappings.registry import MappingRegistry
from bridge.domain import CheckTemplate, MappingContext


@MappingRegistry.register
class RepositoryPatternMapping(PatternMapping):
    """
    Repository pattern enforcement.

    Generates checks for:
    - Repository interface naming (I*Repository)
    - Repository implementations in Infrastructure layer
    """

    pattern_key = "repository"
    languages = ["csharp"]
    min_confidence = 0.5
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when Repository pattern is detected."""
        if context.is_pattern_detected("repository"):
            return context.get_pattern_confidence("repository") >= self.min_confidence
        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get Repository pattern check templates."""
        templates = [
            CheckTemplate(
                id_template="{zone}-repository-interface-naming",
                name="Repository Interface Naming",
                description="Repository interfaces should start with 'I' and end with 'Repository'",
                check_type="naming",
                severity="warning",
                config={
                    "pattern": "^I.*Repository$",
                    "symbol_type": "interface",
                },
                applies_to_paths=[
                    "**/Domain/**/*.cs",
                    "**/Interfaces/**/*.cs",
                    "**/Abstractions/**/*.cs",
                ],
            ),
            CheckTemplate(
                id_template="{zone}-repository-impl-location",
                name="Repository Implementation Location",
                description="Repository implementations should be in Infrastructure layer",
                check_type="file_location",
                severity="warning",
                config={
                    "class_pattern": ".*Repository$",
                    "not_interface": True,
                    "required_path_contains": [
                        "Infrastructure",
                        "Persistence",
                        "Data",
                        "Repositories",
                    ],
                },
                applies_to_paths=["**/*.cs"],
                exclude_paths=["**/Domain/**", "**/Tests/**"],
            ),
        ]

        return templates


@MappingRegistry.register
class GenericRepositoryMapping(PatternMapping):
    """
    Generic Repository pattern (base class).

    Detects use of generic repository pattern.
    """

    pattern_key = "generic_repository"
    languages = ["csharp"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when generic repository pattern is detected."""
        # Check for generic_repository specifically or repository with generic indicator
        if context.is_pattern_detected("generic_repository"):
            return context.get_pattern_confidence("generic_repository") >= self.min_confidence

        # Check metadata for generic indicator
        repo_meta = context.get_pattern_metadata("repository")
        if repo_meta.get("primary") == "generic_repository":
            return True

        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get generic repository check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-generic-repository-usage",
                name="Use Generic Repository",
                description="Repositories should inherit from generic base",
                check_type="ast",
                severity="info",
                config={
                    "class_pattern": ".*Repository$",
                    "must_inherit": ["IRepository<", "Repository<", "GenericRepository<"],
                },
                applies_to_paths=["**/Infrastructure/**/*.cs"],
                review_reason="Verify generic repository is the intended pattern",
            ),
        ]
