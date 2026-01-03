# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-registry-tests

"""Tests for contract registry."""

import pytest
from pathlib import Path

from agentforge.core.contracts.draft import (
    ApprovedContracts,
    ContractDraft,
    EscalationTrigger,
    StageContract,
    ValidationRule,
)
from agentforge.core.contracts.registry import (
    ContractRegistry,
    generate_contract_set_id,
    generate_draft_id,
)


class TestContractRegistry:
    """Tests for ContractRegistry."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project directory."""
        return tmp_path

    @pytest.fixture
    def registry(self, temp_project):
        """Create a registry for testing."""
        return ContractRegistry(temp_project)

    def test_registry_creates_directories(self, temp_project):
        """Registry creates required directories."""
        registry = ContractRegistry(temp_project)

        assert (temp_project / ".agentforge" / "contracts" / "approved").exists(), "Expected (temp_project / '.agentforg...() to be truthy"
        assert (temp_project / ".agentforge" / "contracts" / "drafts").exists(), "Expected (temp_project / '.agentforg...() to be truthy"

    def test_register_approved_contracts(self, registry):
        """Register approved contracts."""
        contracts = ApprovedContracts(
            contract_set_id="CONTRACT-20240103-120000",
            draft_id="DRAFT-001",
            request_id="REQ-001",
            stage_contracts=[
                StageContract(stage_name="intake"),
                StageContract(stage_name="clarify"),
            ],
        )

        result_id = registry.register(contracts)

        assert result_id == "CONTRACT-20240103-120000", "Expected result_id to equal 'CONTRACT-20240103-120000'"

        # Verify file created
        contracts_file = (
            registry.approved_dir / "CONTRACT-20240103-120000.yaml"
        )
        assert contracts_file.exists(), "Expected contracts_file.exists() to be truthy"

    def test_get_approved_contracts(self, registry):
        """Retrieve registered contracts."""
        contracts = ApprovedContracts(
            contract_set_id="CONTRACT-20240103-120000",
            draft_id="DRAFT-001",
            request_id="REQ-001",
            stage_contracts=[
                StageContract(
                    stage_name="intake",
                    output_requirements=["request_id", "scope"],
                ),
            ],
        )
        registry.register(contracts)

        retrieved = registry.get("CONTRACT-20240103-120000")

        assert retrieved is not None, "Expected retrieved is not None"
        assert retrieved.contract_set_id == "CONTRACT-20240103-120000", "Expected retrieved.contract_set_id to equal 'CONTRACT-20240103-120000'"
        assert len(retrieved.stage_contracts) == 1, "Expected len(retrieved.stage_contracts) to equal 1"
        assert "request_id" in retrieved.stage_contracts[0].output_requirements, "Expected 'request_id' in retrieved.stage_contracts[0..."

    def test_get_nonexistent_contracts(self, registry):
        """Get returns None for nonexistent contracts."""
        result = registry.get("CONTRACT-NONEXISTENT")

        assert result is None, "Expected result is None"

    def test_get_for_request(self, registry):
        """Get contracts by request ID."""
        contracts = ApprovedContracts(
            contract_set_id="CONTRACT-20240103-120000",
            draft_id="DRAFT-001",
            request_id="REQ-AUTH-001",
        )
        registry.register(contracts)

        retrieved = registry.get_for_request("REQ-AUTH-001")

        assert retrieved is not None, "Expected retrieved is not None"
        assert retrieved.request_id == "REQ-AUTH-001", "Expected retrieved.request_id to equal 'REQ-AUTH-001'"

    def test_get_for_request_nonexistent(self, registry):
        """Get for request returns None if not found."""
        result = registry.get_for_request("REQ-NONEXISTENT")

        assert result is None, "Expected result is None"

    def test_list_approved(self, registry):
        """List all approved contract sets."""
        # Register multiple contracts
        for i in range(3):
            contracts = ApprovedContracts(
                contract_set_id=f"CONTRACT-00{i}",
                draft_id=f"DRAFT-00{i}",
                request_id=f"REQ-00{i}",
                stage_contracts=[StageContract(stage_name="intake")],
            )
            registry.register(contracts)

        summaries = registry.list_approved()

        assert len(summaries) == 3, "Expected len(summaries) to equal 3"
        assert all("contract_set_id" in s for s in summaries), "Expected all() to be truthy"
        assert all("stage_count" in s for s in summaries), "Expected all() to be truthy"

    def test_save_draft(self, registry):
        """Save a contract draft."""
        draft = ContractDraft(
            draft_id="DRAFT-20240103-120000",
            request_summary="Add user authentication",
            detected_scope="feature",
            stage_contracts=[
                StageContract(stage_name="intake"),
            ],
        )

        result_id = registry.save_draft(draft)

        assert result_id == "DRAFT-20240103-120000", "Expected result_id to equal 'DRAFT-20240103-120000'"
        draft_file = registry.drafts_dir / "DRAFT-20240103-120000.yaml"
        assert draft_file.exists(), "Expected draft_file.exists() to be truthy"

    def test_get_draft(self, registry):
        """Retrieve a saved draft."""
        draft = ContractDraft(
            draft_id="DRAFT-20240103-120000",
            request_summary="Add authentication",
            detected_scope="feature",
            confidence=0.85,
        )
        registry.save_draft(draft)

        retrieved = registry.get_draft("DRAFT-20240103-120000")

        assert retrieved is not None, "Expected retrieved is not None"
        assert retrieved.draft_id == "DRAFT-20240103-120000", "Expected retrieved.draft_id to equal 'DRAFT-20240103-120000'"
        assert retrieved.confidence == 0.85, "Expected retrieved.confidence to equal 0.85"

    def test_get_draft_nonexistent(self, registry):
        """Get draft returns None if not found."""
        result = registry.get_draft("DRAFT-NONEXISTENT")

        assert result is None, "Expected result is None"

    def test_list_drafts(self, registry):
        """List all pending drafts."""
        for i in range(2):
            draft = ContractDraft(
                draft_id=f"DRAFT-00{i}",
                request_summary=f"Request {i}",
                detected_scope="feature",
                confidence=0.5 + i * 0.1,
            )
            registry.save_draft(draft)

        summaries = registry.list_drafts()

        assert len(summaries) == 2, "Expected len(summaries) to equal 2"
        assert all("draft_id" in s for s in summaries), "Expected all() to be truthy"
        assert all("confidence" in s for s in summaries), "Expected all() to be truthy"

    def test_delete_draft(self, registry):
        """Delete a draft."""
        draft = ContractDraft(
            draft_id="DRAFT-TO-DELETE",
            request_summary="Test",
            detected_scope="feature",
        )
        registry.save_draft(draft)

        result = registry.delete_draft("DRAFT-TO-DELETE")

        assert result is True, "Expected result is True"
        assert registry.get_draft("DRAFT-TO-DELETE") is None, "Expected registry.get_draft('DRAFT-T... is None"

    def test_delete_draft_nonexistent(self, registry):
        """Delete returns False for nonexistent draft."""
        result = registry.delete_draft("DRAFT-NONEXISTENT")

        assert result is False, "Expected result is False"

    def test_evolve_contracts(self, registry):
        """Evolve contracts to new version."""
        # Register original contracts
        original = ApprovedContracts(
            contract_set_id="CONTRACT-ORIGINAL",
            draft_id="DRAFT-001",
            request_id="REQ-001",
            stage_contracts=[
                StageContract(
                    stage_name="intake",
                    output_requirements=["request_id"],
                ),
            ],
        )
        registry.register(original)

        # Evolve with changes
        new_id = registry.evolve(
            contract_set_id="CONTRACT-ORIGINAL",
            stage_updates={
                "intake": {
                    "output_requirements": ["request_id", "auth_method"],
                }
            },
            reason="Added auth_method tracking",
        )

        # Verify new contracts
        evolved = registry.get(new_id)
        assert evolved is not None, "Expected evolved is not None"
        assert evolved.version == "1.1", "Expected evolved.version to equal '1.1'"
        assert "auth_method" in evolved.stage_contracts[0].output_requirements, "Expected 'auth_method' in evolved.stage_contracts[0]...."

    def test_evolve_adds_triggers(self, registry):
        """Evolution can add new escalation triggers."""
        original = ApprovedContracts(
            contract_set_id="CONTRACT-ORIGINAL",
            draft_id="DRAFT-001",
            request_id="REQ-001",
        )
        registry.register(original)

        new_id = registry.evolve(
            contract_set_id="CONTRACT-ORIGINAL",
            new_triggers=[
                {
                    "trigger_id": "T-NEW",
                    "condition": "New security concern",
                    "severity": "blocking",
                }
            ],
        )

        evolved = registry.get(new_id)
        assert len(evolved.escalation_triggers) == 1, "Expected len(evolved.escalation_trig... to equal 1"
        assert evolved.escalation_triggers[0].trigger_id == "T-NEW", "Expected evolved.escalation_triggers... to equal 'T-NEW'"

    def test_evolve_nonexistent_raises(self, registry):
        """Evolve raises for nonexistent contracts."""
        with pytest.raises(ValueError, match="Contract set not found"):
            registry.evolve("CONTRACT-NONEXISTENT")

    def test_index_persistence(self, registry, temp_project):
        """Index persists across registry instances."""
        contracts = ApprovedContracts(
            contract_set_id="CONTRACT-001",
            draft_id="DRAFT-001",
            request_id="REQ-PERSIST",
        )
        registry.register(contracts)

        # Create new registry instance
        new_registry = ContractRegistry(temp_project)
        retrieved = new_registry.get_for_request("REQ-PERSIST")

        assert retrieved is not None, "Expected retrieved is not None"
        assert retrieved.contract_set_id == "CONTRACT-001", "Expected retrieved.contract_set_id to equal 'CONTRACT-001'"


class TestIdGenerators:
    """Tests for ID generation functions."""

    def test_generate_contract_set_id(self):
        """Generate unique contract set ID."""
        id1 = generate_contract_set_id()
        id2 = generate_contract_set_id()

        assert id1.startswith("CONTRACT-"), "Expected id1.startswith() to be truthy"
        assert id2.startswith("CONTRACT-"), "Expected id2.startswith() to be truthy"
        # IDs should be unique (timestamp-based)
        # Note: could be same if generated in same second

    def test_generate_draft_id(self):
        """Generate unique draft ID."""
        id1 = generate_draft_id()
        id2 = generate_draft_id()

        assert id1.startswith("DRAFT-"), "Expected id1.startswith() to be truthy"
        assert id2.startswith("DRAFT-"), "Expected id2.startswith() to be truthy"
