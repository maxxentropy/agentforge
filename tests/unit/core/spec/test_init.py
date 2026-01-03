# @spec_file: .agentforge/specs/core-spec-v1.yaml
# @spec_id: core-spec-v1
# @component_id: core-spec-init

"""
Tests for spec module initialization and exports.

Tests that the spec module properly exports its public API.
"""



class TestModuleImports:
    """Tests for module imports."""

    def test_spec_module_import(self):
        """Should import spec module."""
        from agentforge.core import spec
        assert spec is not None, "Expected spec is not None"

    def test_exports_available(self):
        """Should export key classes."""
        from agentforge.core.spec import (
            PlacementAction,
            PlacementDecision,
            SpecPlacementAnalyzer,
        )
        assert SpecPlacementAnalyzer is not None, "Expected SpecPlacementAnalyzer is not None"
        assert PlacementDecision is not None, "Expected PlacementDecision is not None"
        assert PlacementAction is not None, "Expected PlacementAction is not None"

    def test_all_exports(self):
        """Should have __all__ defined with expected exports."""
        from agentforge.core import spec

        assert hasattr(spec, '__all__'), "Expected hasattr() to be truthy"
        assert 'SpecPlacementAnalyzer' in spec.__all__, "Expected 'SpecPlacementAnalyzer' in spec.__all__"
        assert 'PlacementDecision' in spec.__all__, "Expected 'PlacementDecision' in spec.__all__"
        assert 'PlacementAction' in spec.__all__, "Expected 'PlacementAction' in spec.__all__"
