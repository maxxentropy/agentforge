"""Unit tests for mapping registry."""

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "tools"))

from bridge.mappings.registry import MappingRegistry
from bridge.mappings.base import PatternMapping
from bridge.domain import CheckTemplate, MappingContext, GeneratedCheck
from typing import List


class TestMappingRegistry:
    """Tests for the mapping registry."""

    def test_has_registered_mappings(self):
        """Registry should have mappings registered via decorators."""
        # Import mapping modules to ensure decorators run
        from bridge.mappings import cqrs, architecture, conventions  # noqa: F401

        mappings = MappingRegistry._mappings
        assert len(mappings) > 0

    def test_get_mapping_info(self):
        """Can get info about registered mappings."""
        from bridge.mappings import cqrs, architecture, conventions  # noqa: F401

        info = MappingRegistry.get_mapping_info()

        assert isinstance(info, list)
        assert len(info) > 0

        # Check structure of info items
        for item in info:
            assert "pattern_key" in item
            assert "languages" in item
            assert "min_confidence" in item
            assert "version" in item

    def test_get_mappings_for_language(self):
        """Mappings are filtered by language."""
        from bridge.mappings import cqrs, architecture, conventions  # noqa: F401

        csharp_mappings = MappingRegistry.get_mappings_for_language("csharp")
        python_mappings = MappingRegistry.get_mappings_for_language("python")

        # C# and Python have different mappings
        csharp_keys = {m.pattern_key for m in csharp_mappings}
        python_keys = {m.pattern_key for m in python_mappings}

        # CQRS mapping is C# only
        assert "cqrs" in csharp_keys
        # pytest mapping is Python only
        assert "framework_pytest" in python_keys

    def test_generate_checks_from_context(self):
        """Can generate checks from a context."""
        from bridge.mappings import cqrs, architecture, conventions  # noqa: F401

        context = MappingContext(
            zone_name="core",
            language="python",
            patterns={
                "framework_pytest": {"confidence": 0.95},
            },
            structure={},
            frameworks=["pytest"],
        )

        checks = MappingRegistry.generate_checks(context)

        assert isinstance(checks, list)
        # Should have at least the pytest markers check
        assert len(checks) > 0

    def test_generate_checks_with_pattern_filter(self):
        """Can filter by pattern."""
        from bridge.mappings import cqrs, architecture, conventions  # noqa: F401

        context = MappingContext(
            zone_name="core",
            language="python",
            patterns={
                "framework_pytest": {"confidence": 0.95},
                "type_hints": {"confidence": 0.8},
            },
            structure={},
            frameworks=["pytest"],
        )

        # Only get pytest checks
        checks = MappingRegistry.generate_checks(context, pattern_filter="framework_pytest")

        # All checks should be from framework_pytest pattern
        for check in checks:
            assert check.source_pattern == "framework_pytest"


class TestCustomMapping:
    """Tests for creating custom mappings."""

    def test_can_create_and_register_custom_mapping(self):
        """Can create and register a custom mapping."""
        # Save original mappings
        original_mappings = dict(MappingRegistry._mappings)
        original_instances = dict(MappingRegistry._instances)

        try:
            @MappingRegistry.register
            class TestMapping(PatternMapping):
                pattern_key = "test_pattern"
                languages = ["test_lang"]
                min_confidence = 0.5

                def matches(self, context: MappingContext) -> bool:
                    return context.is_pattern_detected("test_pattern")

                def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
                    return [
                        CheckTemplate(
                            id_template="{zone}-test-check",
                            name="Test Check",
                            description="A test check",
                            check_type="custom",
                            config={},
                        )
                    ]

            # Mapping should be registered
            assert any("test_pattern" in k for k in MappingRegistry._mappings.keys())

        finally:
            # Restore original mappings
            MappingRegistry._mappings = original_mappings
            MappingRegistry._instances = original_instances
