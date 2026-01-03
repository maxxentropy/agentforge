# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-cli-tests

"""Tests for contract CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from agentforge.core.contracts.cli import (
    task_contracts,
    list_command,
    show_command,
    approve_command,
    delete_command,
)
from agentforge.core.contracts.draft import (
    ApprovedContracts,
    ContractDraft,
    StageContract,
)
from agentforge.core.contracts.registry import ContractRegistry


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with contracts."""
    registry = ContractRegistry(tmp_path)

    # Create a sample draft
    draft = ContractDraft(
        draft_id="DRAFT-TEST-001",
        request_summary="Test authentication feature",
        detected_scope="feature",
        confidence=0.85,
        stage_contracts=[
            StageContract(stage_name="intake"),
            StageContract(stage_name="implement"),
        ],
    )
    registry.save_draft(draft)

    # Create a sample approved contract
    approved = ApprovedContracts(
        contract_set_id="CONTRACT-TEST-001",
        draft_id="DRAFT-OLD",
        request_id="REQ-001",
        stage_contracts=[
            StageContract(stage_name="intake"),
        ],
    )
    registry.register(approved)

    return tmp_path


class TestListCommand:
    """Tests for list command."""

    def test_list_drafts(self, runner, temp_project):
        """List pending drafts."""
        result = runner.invoke(
            task_contracts,
            ["list", "--drafts", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "PENDING DRAFTS" in result.output
        assert "DRAFT-TEST-001" in result.output

    def test_list_approved(self, runner, temp_project):
        """List approved contracts."""
        result = runner.invoke(
            task_contracts,
            ["list", "--approved", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "APPROVED CONTRACTS" in result.output
        assert "CONTRACT-TEST-001" in result.output

    def test_list_both(self, runner, temp_project):
        """List both drafts and approved."""
        result = runner.invoke(
            task_contracts,
            ["list", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "PENDING DRAFTS" in result.output
        assert "APPROVED CONTRACTS" in result.output

    def test_list_empty(self, runner, tmp_path):
        """List with no contracts."""
        result = runner.invoke(
            task_contracts,
            ["list", "-p", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "(none)" in result.output


class TestShowCommand:
    """Tests for show command."""

    def test_show_draft(self, runner, temp_project):
        """Show a draft."""
        result = runner.invoke(
            task_contracts,
            ["show", "DRAFT-TEST-001", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "CONTRACT REVIEW" in result.output or "Test authentication" in result.output

    def test_show_draft_yaml(self, runner, temp_project):
        """Show draft as YAML."""
        result = runner.invoke(
            task_contracts,
            ["show", "DRAFT-TEST-001", "--yaml", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "draft_id:" in result.output
        assert "DRAFT-TEST-001" in result.output

    def test_show_approved(self, runner, temp_project):
        """Show an approved contract."""
        result = runner.invoke(
            task_contracts,
            ["show", "CONTRACT-TEST-001", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "CONTRACT-TEST-001" in result.output

    def test_show_approved_yaml(self, runner, temp_project):
        """Show approved contract as YAML."""
        result = runner.invoke(
            task_contracts,
            ["show", "CONTRACT-TEST-001", "--yaml", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "contract_set_id:" in result.output

    def test_show_not_found(self, runner, temp_project):
        """Show nonexistent contract."""
        result = runner.invoke(
            task_contracts,
            ["show", "NONEXISTENT", "-p", str(temp_project)],
        )

        assert result.exit_code != 0
        assert "not found" in result.output


class TestApproveCommand:
    """Tests for approve command."""

    def test_approve_draft(self, runner, temp_project):
        """Approve a draft."""
        result = runner.invoke(
            task_contracts,
            ["approve", "DRAFT-TEST-001", "-r", "REQ-NEW", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "Approved" in result.output
        assert "REQ-NEW" in result.output

        # Verify draft is deleted and approved exists
        registry = ContractRegistry(temp_project)
        assert registry.get_draft("DRAFT-TEST-001") is None
        approved = registry.get_for_request("REQ-NEW")
        assert approved is not None

    def test_approve_not_found(self, runner, temp_project):
        """Approve nonexistent draft."""
        result = runner.invoke(
            task_contracts,
            ["approve", "NONEXISTENT", "-r", "REQ", "-p", str(temp_project)],
        )

        assert result.exit_code != 0
        assert "not found" in result.output


class TestDeleteCommand:
    """Tests for delete command."""

    def test_delete_draft_with_force(self, runner, temp_project):
        """Delete a draft with force flag."""
        result = runner.invoke(
            task_contracts,
            ["delete", "DRAFT-TEST-001", "-f", "-p", str(temp_project)],
        )

        assert result.exit_code == 0
        assert "Deleted" in result.output

        # Verify draft is gone
        registry = ContractRegistry(temp_project)
        assert registry.get_draft("DRAFT-TEST-001") is None

    def test_delete_not_found(self, runner, temp_project):
        """Delete nonexistent draft."""
        result = runner.invoke(
            task_contracts,
            ["delete", "NONEXISTENT", "-f", "-p", str(temp_project)],
        )

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_delete_cancelled(self, runner, temp_project):
        """Delete cancelled by user."""
        result = runner.invoke(
            task_contracts,
            ["delete", "DRAFT-TEST-001", "-p", str(temp_project)],
            input="n\n",  # Say no to confirmation
        )

        assert "Cancelled" in result.output

        # Verify draft still exists
        registry = ContractRegistry(temp_project)
        assert registry.get_draft("DRAFT-TEST-001") is not None


class TestContractGroup:
    """Tests for contract command group."""

    def test_contract_help(self, runner):
        """Show contract command help."""
        result = runner.invoke(task_contracts, ["--help"])

        assert result.exit_code == 0
        assert "Task contract management" in result.output

    def test_contract_subcommands(self, runner):
        """Contract has expected subcommands."""
        result = runner.invoke(task_contracts, ["--help"])

        assert "draft" in result.output
        assert "review" in result.output
        assert "list" in result.output
        assert "show" in result.output
        assert "approve" in result.output
        assert "delete" in result.output
