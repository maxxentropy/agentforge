# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-registry
# @test_path: tests/unit/contracts/test_registry.py

"""
Contract Registry
=================

Storage and retrieval of approved contracts.

The registry provides:
- Persistent storage of approved contracts
- Lookup by contract set ID or request ID
- Version management for contract evolution
- Listing of available contract templates
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .draft import ApprovedContracts, ContractDraft


class ContractRegistry:
    """Registry of approved contracts.

    Storage structure:
        {project_path}/.agentforge/contracts/
        ├── approved/
        │   ├── {contract_set_id}.yaml
        │   └── ...
        ├── drafts/
        │   ├── {draft_id}.yaml
        │   └── ...
        └── index.yaml  # Maps request_id -> contract_set_id
    """

    def __init__(self, project_path: Path):
        """Initialize contract registry.

        Args:
            project_path: Root project directory
        """
        self.project_path = Path(project_path).resolve()
        self.contracts_dir = self.project_path / ".agentforge" / "contracts"
        self.approved_dir = self.contracts_dir / "approved"
        self.drafts_dir = self.contracts_dir / "drafts"

        # Ensure directories exist
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)

    def register(self, contracts: ApprovedContracts) -> str:
        """Register approved contracts.

        Args:
            contracts: The approved contracts to register

        Returns:
            The contract_set_id
        """
        # Save contracts
        contracts_path = self.approved_dir / f"{contracts.contract_set_id}.yaml"
        contracts_path.write_text(contracts.to_yaml(), encoding="utf-8")

        # Update index
        self._update_index(contracts.request_id, contracts.contract_set_id)

        return contracts.contract_set_id

    def get(self, contract_set_id: str) -> ApprovedContracts | None:
        """Retrieve contracts by ID.

        Args:
            contract_set_id: The contract set identifier

        Returns:
            ApprovedContracts if found, None otherwise
        """
        contracts_path = self.approved_dir / f"{contract_set_id}.yaml"
        if not contracts_path.exists():
            return None

        yaml_str = contracts_path.read_text(encoding="utf-8")
        return ApprovedContracts.from_yaml(yaml_str)

    def get_for_request(self, request_id: str) -> ApprovedContracts | None:
        """Get contracts associated with a request.

        Args:
            request_id: The request identifier

        Returns:
            ApprovedContracts if found, None otherwise
        """
        index = self._load_index()
        contract_set_id = index.get("request_mappings", {}).get(request_id)

        if not contract_set_id:
            return None

        return self.get(contract_set_id)

    def list_approved(self) -> list[dict[str, Any]]:
        """List all approved contract sets.

        Returns:
            List of contract set summaries
        """
        summaries = []
        for path in sorted(self.approved_dir.glob("*.yaml")):
            contracts = self.get(path.stem)
            if contracts:
                summaries.append({
                    "contract_set_id": contracts.contract_set_id,
                    "request_id": contracts.request_id,
                    "approved_at": contracts.approved_at,
                    "version": contracts.version,
                    "stage_count": len(contracts.stage_contracts),
                })
        return summaries

    def save_draft(self, draft: ContractDraft) -> str:
        """Save a contract draft.

        Args:
            draft: The draft to save

        Returns:
            The draft_id
        """
        draft_path = self.drafts_dir / f"{draft.draft_id}.yaml"
        draft_path.write_text(draft.to_yaml(), encoding="utf-8")
        return draft.draft_id

    def get_draft(self, draft_id: str) -> ContractDraft | None:
        """Retrieve a draft by ID.

        Args:
            draft_id: The draft identifier

        Returns:
            ContractDraft if found, None otherwise
        """
        draft_path = self.drafts_dir / f"{draft_id}.yaml"
        if not draft_path.exists():
            return None

        yaml_str = draft_path.read_text(encoding="utf-8")
        return ContractDraft.from_yaml(yaml_str)

    def list_drafts(self) -> list[dict[str, Any]]:
        """List all pending drafts.

        Returns:
            List of draft summaries
        """
        summaries = []
        for path in sorted(self.drafts_dir.glob("*.yaml")):
            draft = self.get_draft(path.stem)
            if draft:
                summaries.append({
                    "draft_id": draft.draft_id,
                    "request_summary": draft.request_summary,
                    "detected_scope": draft.detected_scope,
                    "created_at": draft.created_at,
                    "confidence": draft.confidence,
                    "stage_count": len(draft.stage_contracts),
                    "open_questions": len(draft.open_questions),
                })
        return summaries

    def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft.

        Args:
            draft_id: The draft identifier

        Returns:
            True if deleted, False if not found
        """
        draft_path = self.drafts_dir / f"{draft_id}.yaml"
        if draft_path.exists():
            draft_path.unlink()
            return True
        return False

    def evolve(
        self,
        contract_set_id: str,
        stage_updates: dict[str, dict[str, Any]] | None = None,
        new_triggers: list[dict[str, Any]] | None = None,
        reason: str = "",
    ) -> str:
        """Create new version of contracts with changes.

        Args:
            contract_set_id: Original contract set ID
            stage_updates: Updates to stage contracts by stage name
            new_triggers: New escalation triggers to add
            reason: Reason for evolution

        Returns:
            New contract_set_id
        """
        original = self.get(contract_set_id)
        if not original:
            raise ValueError(f"Contract set not found: {contract_set_id}")

        # Parse version
        major, minor = map(int, original.version.split("."))
        new_version = f"{major}.{minor + 1}"

        # Generate new ID
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        new_id = f"CONTRACT-{timestamp}"

        # Create evolved contracts
        evolved = ApprovedContracts(
            contract_set_id=new_id,
            draft_id=original.draft_id,
            request_id=original.request_id,
            stage_contracts=original.stage_contracts.copy(),
            escalation_triggers=original.escalation_triggers.copy(),
            quality_gates=original.quality_gates.copy(),
            version=new_version,
        )

        # Apply stage updates
        if stage_updates:
            for stage_name, updates in stage_updates.items():
                for i, sc in enumerate(evolved.stage_contracts):
                    if sc.stage_name == stage_name:
                        # Update fields
                        if "output_schema" in updates:
                            sc.output_schema = updates["output_schema"]
                        if "input_schema" in updates:
                            sc.input_schema = updates["input_schema"]
                        if "output_requirements" in updates:
                            sc.output_requirements = updates["output_requirements"]
                        if "input_requirements" in updates:
                            sc.input_requirements = updates["input_requirements"]
                        break

        # Add new triggers
        if new_triggers:
            from .draft import EscalationTrigger
            for trigger_data in new_triggers:
                evolved.escalation_triggers.append(
                    EscalationTrigger.from_dict(trigger_data)
                )

        # Register evolved contracts
        self.register(evolved)

        return new_id

    def _load_index(self) -> dict[str, Any]:
        """Load the contract index."""
        index_path = self.contracts_dir / "index.yaml"
        if index_path.exists():
            return yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        return {"request_mappings": {}}

    def _save_index(self, index: dict[str, Any]) -> None:
        """Save the contract index."""
        index_path = self.contracts_dir / "index.yaml"
        index_path.write_text(
            yaml.dump(index, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def _update_index(self, request_id: str, contract_set_id: str) -> None:
        """Update index with new mapping."""
        index = self._load_index()
        if "request_mappings" not in index:
            index["request_mappings"] = {}
        index["request_mappings"][request_id] = contract_set_id
        index["last_updated"] = datetime.now(UTC).isoformat()
        self._save_index(index)


def generate_contract_set_id() -> str:
    """Generate a unique contract set ID."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"CONTRACT-{timestamp}"


def generate_draft_id() -> str:
    """Generate a unique draft ID."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"DRAFT-{timestamp}"
