# @spec_file: .agentforge/specs/core-spec-v1.yaml
# @spec_id: core-spec-v1
# @component_id: core-spec-placement

"""
Tests for SpecPlacementAnalyzer.

Tests the spec placement analysis that prevents spec fragmentation
by determining where new features belong in the spec space.
"""

from pathlib import Path

import pytest
import yaml


class TestPlacementActionEnum:
    """Tests for PlacementAction enum."""

    def test_placement_action_values(self):
        """PlacementAction should have EXTEND, CREATE, ESCALATE values."""
        from agentforge.core.spec.placement import PlacementAction

        assert PlacementAction.EXTEND.value == "extend", "Expected PlacementAction.EXTEND.value to equal 'extend'"
        assert PlacementAction.CREATE.value == "create", "Expected PlacementAction.CREATE.value to equal 'create'"
        assert PlacementAction.ESCALATE.value == "escalate", "Expected PlacementAction.ESCALATE.value to equal 'escalate'"


class TestSpecInfo:
    """Tests for SpecInfo dataclass."""

    def test_spec_info_from_yaml(self, tmp_path):
        """Should create SpecInfo from YAML data."""
        from agentforge.core.spec.placement import SpecInfo

        spec_file = tmp_path / "test-v1.yaml"
        data = {
            'spec_id': 'test-v1',
            'name': 'test',
            'description': 'Test spec',
            'components': [
                {'name': 'comp1', 'location': 'src/agentforge/core/test/comp1.py'},
                {'name': 'comp2', 'location': 'src/agentforge/core/test/comp2.py'},
            ]
        }

        spec_info = SpecInfo.from_yaml(spec_file, data)

        assert spec_info.spec_id == 'test-v1', "Expected spec_info.spec_id to equal 'test-v1'"
        assert spec_info.name == 'test', "Expected spec_info.name to equal 'test'"
        assert len(spec_info.components) == 2, "Expected len(spec_info.components) to equal 2"

    def test_spec_info_covered_locations(self, tmp_path):
        """Should extract covered location prefixes from components."""
        from agentforge.core.spec.placement import SpecInfo

        spec_file = tmp_path / "core-api-v1.yaml"
        data = {
            'spec_id': 'core-api-v1',
            'name': 'core_api',
            'description': 'API module',
            'components': [
                {'name': 'client', 'location': 'src/agentforge/core/api/client.py'},
                {'name': 'server', 'location': 'src/agentforge/core/api/server.py'},
            ]
        }

        spec_info = SpecInfo.from_yaml(spec_file, data)

        assert 'src/agentforge/core/api' in spec_info.covered_locations, "Expected 'src/agentforge/core/api' in spec_info.covered_locations"


class TestPlacementDecision:
    """Tests for PlacementDecision dataclass."""

    def test_placement_decision_extend(self):
        """EXTEND decision should have spec_id and spec_file."""
        from agentforge.core.spec.placement import PlacementAction, PlacementDecision

        decision = PlacementDecision(
            action=PlacementAction.EXTEND,
            reason="Location covered by existing spec",
            spec_id="cli-v1",
            spec_file=Path(".agentforge/specs/cli-v1.yaml"),
        )

        assert decision.action == PlacementAction.EXTEND, "Expected decision.action to equal PlacementAction.EXTEND"
        assert decision.spec_id == "cli-v1", "Expected decision.spec_id to equal 'cli-v1'"
        assert "EXTEND cli-v1" in str(decision), "Expected 'EXTEND cli-v1' in str(decision)"

    def test_placement_decision_create(self):
        """CREATE decision should have suggested_spec_id."""
        from agentforge.core.spec.placement import PlacementAction, PlacementDecision

        decision = PlacementDecision(
            action=PlacementAction.CREATE,
            reason="No existing spec covers this location",
            suggested_spec_id="core-newmodule-v1",
        )

        assert decision.action == PlacementAction.CREATE, "Expected decision.action to equal PlacementAction.CREATE"
        assert decision.suggested_spec_id == "core-newmodule-v1", "Expected decision.suggested_spec_id to equal 'core-newmodule-v1'"
        assert "CREATE" in str(decision), "Expected 'CREATE' in str(decision)"

    def test_placement_decision_escalate(self):
        """ESCALATE decision should have options list."""
        from agentforge.core.spec.placement import PlacementAction, PlacementDecision

        decision = PlacementDecision(
            action=PlacementAction.ESCALATE,
            reason="Multiple specs could cover",
            options=[
                {'spec_id': 'spec-a', 'coverage_count': 2},
                {'spec_id': 'spec-b', 'coverage_count': 2},
            ]
        )

        assert decision.action == PlacementAction.ESCALATE, "Expected decision.action to equal PlacementAction.ESCALATE"
        assert len(decision.options) == 2, "Expected len(decision.options) to equal 2"
        assert "ESCALATE" in str(decision), "Expected 'ESCALATE' in str(decision)"


class TestSpecPlacementAnalyzer:
    """Tests for SpecPlacementAnalyzer."""

    @pytest.fixture
    def specs_dir(self, tmp_path):
        """Create a temporary specs directory with test specs."""
        specs = tmp_path / ".agentforge" / "specs"
        specs.mkdir(parents=True)

        # Create CLI spec
        cli_spec = {
            'spec_id': 'cli-v1',
            'name': 'cli',
            'description': 'CLI module',
            'components': [
                {'name': 'main', 'location': 'src/agentforge/cli/main.py'},
                {'name': 'core', 'location': 'src/agentforge/cli/core.py'},
            ]
        }
        (specs / "cli-v1.yaml").write_text(yaml.dump(cli_spec))

        # Create core-api spec
        api_spec = {
            'spec_id': 'core-api-v1',
            'name': 'core_api',
            'description': 'API module',
            'components': [
                {'name': 'client', 'location': 'src/agentforge/core/api/client.py'},
            ]
        }
        (specs / "core-api-v1.yaml").write_text(yaml.dump(api_spec))

        return specs

    def test_analyzer_load_specs(self, specs_dir):
        """Should load specs from directory."""
        from agentforge.core.spec.placement import SpecPlacementAnalyzer

        analyzer = SpecPlacementAnalyzer(specs_dir)
        analyzer.load_specs()

        spec_ids = analyzer.get_spec_ids()
        assert 'cli-v1' in spec_ids, "Expected 'cli-v1' in spec_ids"
        assert 'core-api-v1' in spec_ids, "Expected 'core-api-v1' in spec_ids"

    def test_analyzer_empty_specs_dir(self, tmp_path):
        """Should handle empty specs directory."""
        from agentforge.core.spec.placement import SpecPlacementAnalyzer

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        analyzer = SpecPlacementAnalyzer(empty_dir)
        analyzer.load_specs()

        assert analyzer.get_spec_ids() == [], "Expected analyzer.get_spec_ids() to equal []"

    def test_analyzer_find_covering_specs(self, specs_dir):
        """Should find specs that cover a location."""
        from agentforge.core.spec.placement import SpecPlacementAnalyzer

        analyzer = SpecPlacementAnalyzer(specs_dir)

        # CLI location should be covered by cli-v1
        covering = analyzer.find_covering_specs('src/agentforge/cli/commands/new.py')
        assert len(covering) == 1, "Expected len(covering) to equal 1"
        assert covering[0].spec_id == 'cli-v1', "Expected covering[0].spec_id to equal 'cli-v1'"

        # API location should be covered by core-api-v1
        covering = analyzer.find_covering_specs('src/agentforge/core/api/rate_limiter.py')
        assert len(covering) == 1, "Expected len(covering) to equal 1"
        assert covering[0].spec_id == 'core-api-v1', "Expected covering[0].spec_id to equal 'core-api-v1'"

    def test_analyzer_analyze_extend(self, specs_dir):
        """Should recommend EXTEND when location covered by existing spec."""
        from agentforge.core.spec.placement import PlacementAction, SpecPlacementAnalyzer

        analyzer = SpecPlacementAnalyzer(specs_dir)

        decision = analyzer.analyze(
            feature_description="Add new CLI command",
            target_locations=['src/agentforge/cli/commands/newcmd.py'],
        )

        assert decision.action == PlacementAction.EXTEND, "Expected decision.action to equal PlacementAction.EXTEND"
        assert decision.spec_id == 'cli-v1', "Expected decision.spec_id to equal 'cli-v1'"

    def test_analyzer_analyze_create(self, specs_dir):
        """Should recommend CREATE when no spec covers location."""
        from agentforge.core.spec.placement import PlacementAction, SpecPlacementAnalyzer

        analyzer = SpecPlacementAnalyzer(specs_dir)

        decision = analyzer.analyze(
            feature_description="Add new module",
            target_locations=['src/agentforge/core/newmodule/thing.py'],
        )

        assert decision.action == PlacementAction.CREATE, "Expected decision.action to equal PlacementAction.CREATE"
        assert decision.suggested_spec_id == 'core-newmodule-v1', "Expected decision.suggested_spec_id to equal 'core-newmodule-v1'"

    def test_analyzer_analyze_escalate(self, tmp_path):
        """Should recommend ESCALATE when multiple specs could cover."""
        from agentforge.core.spec.placement import PlacementAction, SpecPlacementAnalyzer

        # Create overlapping specs
        specs = tmp_path / ".agentforge" / "specs"
        specs.mkdir(parents=True)

        spec_a = {
            'spec_id': 'core-shared-v1',
            'name': 'shared',
            'description': 'Shared utilities',
            'components': [
                {'name': 'util', 'location': 'src/agentforge/core/shared/util.py'},
            ]
        }
        spec_b = {
            'spec_id': 'core-shared-extra-v1',
            'name': 'shared_extra',
            'description': 'Extra shared utilities',
            'components': [
                {'name': 'extra', 'location': 'src/agentforge/core/shared/extra.py'},
            ]
        }
        (specs / "core-shared-v1.yaml").write_text(yaml.dump(spec_a))
        (specs / "core-shared-extra-v1.yaml").write_text(yaml.dump(spec_b))

        analyzer = SpecPlacementAnalyzer(specs)

        decision = analyzer.analyze(
            feature_description="Add shared feature",
            target_locations=['src/agentforge/core/shared/new.py'],
        )

        assert decision.action == PlacementAction.ESCALATE, "Expected decision.action to equal PlacementAction.ESCALATE"
        assert len(decision.options) == 2, "Expected len(decision.options) to equal 2"

    def test_analyzer_explicit_spec_id(self, specs_dir):
        """Should use explicit spec_id when provided."""
        from agentforge.core.spec.placement import PlacementAction, SpecPlacementAnalyzer

        analyzer = SpecPlacementAnalyzer(specs_dir)

        decision = analyzer.analyze(
            feature_description="Add feature",
            target_locations=['src/agentforge/core/anywhere/thing.py'],
            explicit_spec_id='cli-v1',
        )

        assert decision.action == PlacementAction.EXTEND, "Expected decision.action to equal PlacementAction.EXTEND"
        assert decision.spec_id == 'cli-v1', "Expected decision.spec_id to equal 'cli-v1'"

    def test_suggest_component_id(self, specs_dir):
        """Should generate correct component_id."""
        from agentforge.core.spec.placement import SpecPlacementAnalyzer

        analyzer = SpecPlacementAnalyzer(specs_dir)

        comp_id = analyzer.suggest_component_id('cli-v1', 'spec_adapt')
        assert comp_id == 'cli-spec_adapt', "Expected comp_id to equal 'cli-spec_adapt'"

        comp_id = analyzer.suggest_component_id('core-api-v1', 'rate-limiter')
        assert comp_id == 'core-api-rate_limiter', "Expected comp_id to equal 'core-api-rate_limiter'"

    def test_validate_unique_component_id(self, specs_dir):
        """Should validate component_id uniqueness."""
        from agentforge.core.spec.placement import SpecPlacementAnalyzer

        analyzer = SpecPlacementAnalyzer(specs_dir)

        # 'main' exists in cli-v1 components (based on our fixture)
        # Note: component_id isn't in our fixture, so this should return True
        assert analyzer.validate_unique_component_id('cli-v1', 'new-component') is True, "Expected analyzer.validate_unique_co... is True"
