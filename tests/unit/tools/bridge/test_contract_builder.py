"""Unit tests for contract builder."""

import pytest
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "tools"))

from bridge.contract_builder import ContractBuilder
from bridge.domain import GeneratedCheck


class TestContractBuilder:
    """Tests for contract building."""

    @pytest.fixture
    def builder(self, tmp_path):
        """Create a contract builder."""
        return ContractBuilder(root_path=tmp_path, output_dir="contracts")

    @pytest.fixture
    def sample_checks(self):
        """Create sample checks."""
        return [
            GeneratedCheck(
                id="core-cqrs-command-naming",
                name="CQRS Command Naming",
                description="Commands should end with 'Command'",
                check_type="naming",
                enabled=True,
                severity="warning",
                config={"pattern": ".*Command$"},
                applies_to={"paths": ["**/*.cs"]},
                source_pattern="cqrs",
                source_confidence=0.95,
                review_required=False,
            ),
            GeneratedCheck(
                id="core-cqrs-query-naming",
                name="CQRS Query Naming",
                description="Queries should end with 'Query'",
                check_type="naming",
                enabled=False,
                severity="warning",
                config={"pattern": ".*Query$"},
                applies_to={"paths": ["**/*.cs"]},
                source_pattern="cqrs",
                source_confidence=0.7,
                review_required=True,
                review_reason="Medium confidence - needs review",
            ),
        ]

    def test_build_contract(self, builder, sample_checks):
        """Can build a contract from checks."""
        contract = builder.build_contract(
            zone_name="core",
            language="csharp",
            checks=sample_checks,
            profile_path=".agentforge/codebase_profile.yaml",
            profile_hash="sha256:abc123",
            confidence_threshold=0.6,
        )

        assert contract.name == "core"
        assert contract.zone == "core"
        assert contract.language == "csharp"
        assert len(contract.checks) == 2
        assert contract.enabled_count == 1
        assert contract.disabled_count == 1

    def test_build_contract_default_zone(self, builder, sample_checks):
        """Default zone uses 'generated' as name."""
        contract = builder.build_contract(
            zone_name=None,
            language="python",
            checks=sample_checks,
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        assert contract.name == "generated"
        assert contract.zone is None

    def test_metadata_includes_patterns(self, builder, sample_checks):
        """Metadata includes mapped patterns."""
        contract = builder.build_contract(
            zone_name="core",
            language="csharp",
            checks=sample_checks,
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        assert "cqrs" in contract.metadata.patterns_mapped
        assert contract.metadata.patterns_mapped["cqrs"] == 0.95

    def test_write_contract_creates_file(self, builder, sample_checks):
        """Writing a contract creates the file."""
        contract = builder.build_contract(
            zone_name="core",
            language="csharp",
            checks=sample_checks,
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        output_path = builder.write_contract(contract)

        assert output_path is not None
        assert output_path.exists()
        assert output_path.name == "core.contract.yaml"

    def test_write_contract_dry_run(self, builder, sample_checks):
        """Dry run returns path but doesn't create file."""
        contract = builder.build_contract(
            zone_name="core",
            language="csharp",
            checks=sample_checks,
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        output_path = builder.write_contract(contract, dry_run=True)

        assert output_path is not None
        assert not output_path.exists()

    def test_contract_yaml_has_header(self, builder, sample_checks):
        """Generated YAML has proper header."""
        contract = builder.build_contract(
            zone_name="core",
            language="csharp",
            checks=sample_checks,
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        output_path = builder.write_contract(contract)
        content = output_path.read_text()

        assert "AUTO-GENERATED CONTRACT" in content
        assert "DO NOT EDIT MANUALLY" in content
        assert "AgentForge Bridge" in content

    def test_contract_yaml_has_metadata(self, builder, sample_checks):
        """Generated YAML includes generation metadata."""
        contract = builder.build_contract(
            zone_name="core",
            language="csharp",
            checks=sample_checks,
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        output_path = builder.write_contract(contract)
        content = output_path.read_text()

        assert "generation_metadata:" in content
        assert "source_profile: test.yaml" in content
        assert "source_hash: sha256:abc" in content

    def test_contract_yaml_has_checks_with_provenance(self, builder, sample_checks):
        """Checks include generation provenance."""
        contract = builder.build_contract(
            zone_name="core",
            language="csharp",
            checks=sample_checks,
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        output_path = builder.write_contract(contract)
        content = output_path.read_text()

        assert "generation:" in content
        assert "source_pattern: cqrs" in content
        assert "source_confidence: 0.95" in content


class TestContractBuilderEdgeCases:
    """Edge case tests for contract builder."""

    @pytest.fixture
    def builder(self, tmp_path):
        """Create a contract builder."""
        return ContractBuilder(root_path=tmp_path, output_dir="contracts")

    def test_empty_checks_creates_minimal_contract(self, builder):
        """Can create contract with no checks."""
        contract = builder.build_contract(
            zone_name="empty",
            language="python",
            checks=[],
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        assert contract.name == "empty"
        assert len(contract.checks) == 0
        assert contract.enabled_count == 0

    def test_handles_special_characters_in_zone_name(self, builder):
        """Handles special characters in zone names."""
        check = GeneratedCheck(
            id="test-check",
            name="Test",
            description="Test check",
            check_type="naming",
            enabled=True,
            severity="warning",
            config={},
            applies_to={},
            source_pattern="test",
            source_confidence=0.9,
        )

        contract = builder.build_contract(
            zone_name="my-zone",
            language="python",
            checks=[check],
            profile_path="test.yaml",
            profile_hash="sha256:abc",
        )

        output_path = builder.write_contract(contract)

        assert output_path.name == "my-zone.contract.yaml"
        assert output_path.exists()
