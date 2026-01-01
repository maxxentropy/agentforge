# @spec_file: .agentforge/specs/bridge-mappings-v1.yaml
# @spec_id: bridge-mappings-v1
# @component_id: bridge-mappings-registry
# @test_path: tests/unit/tools/bridge/test_registry.py

"""
Mapping Registry
================

Registry for pattern-to-check mappings.
Provides decorator-based registration and lookup.
"""

from typing import List, Dict, Type, Optional

from bridge.mappings.base import PatternMapping
from bridge.domain import MappingContext, GeneratedCheck


class MappingRegistry:
    """
    Registry for pattern mappings.

    Usage:
        @MappingRegistry.register
        class MyMapping(PatternMapping):
            pattern_key = "my_pattern"
            ...

        # Later
        mappings = MappingRegistry.get_mappings_for_language("csharp")
    """

    _mappings: Dict[str, Type[PatternMapping]] = {}
    _instances: Dict[str, PatternMapping] = {}

    @classmethod
    def register(cls, mapping_class: Type[PatternMapping]) -> Type[PatternMapping]:
        """
        Decorator to register a pattern mapping.

        Args:
            mapping_class: The PatternMapping class to register

        Returns:
            The same class (unchanged)
        """
        key = f"{mapping_class.pattern_key}:{mapping_class.__name__}"
        cls._mappings[key] = mapping_class
        return mapping_class

    @classmethod
    def get_all_mappings(cls) -> List[PatternMapping]:
        """Get instances of all registered mappings."""
        result = []
        for key, mapping_class in cls._mappings.items():
            if key not in cls._instances:
                cls._instances[key] = mapping_class()
            result.append(cls._instances[key])
        return result

    @classmethod
    def get_mappings_for_language(cls, language: str) -> List[PatternMapping]:
        """Get mappings that apply to a specific language."""
        all_mappings = cls.get_all_mappings()
        return [
            m for m in all_mappings
            if not m.languages or language.lower() in [l.lower() for l in m.languages]
        ]

    @classmethod
    def get_mappings_for_pattern(cls, pattern_key: str) -> List[PatternMapping]:
        """Get mappings that handle a specific pattern."""
        all_mappings = cls.get_all_mappings()
        return [m for m in all_mappings if m.pattern_key == pattern_key]

    @classmethod
    def get_mapping_info(cls) -> List[dict]:
        """Get info about all registered mappings."""
        return [m.get_info() for m in cls.get_all_mappings()]

    @classmethod
    def generate_checks(
        cls,
        context: MappingContext,
        pattern_filter: Optional[str] = None
    ) -> List[GeneratedCheck]:
        """
        Generate checks for a context using all applicable mappings.

        Args:
            context: The mapping context
            pattern_filter: Optional pattern to filter by

        Returns:
            List of generated checks
        """
        checks = []
        mappings = cls.get_mappings_for_language(context.language)

        for mapping in mappings:
            if pattern_filter and mapping.pattern_key != pattern_filter:
                continue

            try:
                generated = mapping.generate(context)
                checks.extend(generated)
            except Exception as e:
                # Log but don't fail on individual mapping errors
                import logging
                logging.warning(f"Mapping {mapping.__class__.__name__} failed: {e}")

        return checks

    @classmethod
    def clear(cls) -> None:
        """Clear registry (mainly for testing)."""
        cls._mappings.clear()
        cls._instances.clear()
