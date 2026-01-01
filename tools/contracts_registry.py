#!/usr/bin/env python3
"""
Contract Registry
=================

Registry for loading, resolving, and managing contracts.

Handles:
- Discovery across global/workspace/repo tiers
- Builtin contract loading
- Inheritance resolution
- Exemption matching

Extracted from contracts.py for modularity.
"""

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

try:
    from .contracts_types import Contract, Exemption
except ImportError:
    from contracts_types import Contract, Exemption

# Builtin contracts directory (relative to this file)
BUILTIN_CONTRACTS_DIR = Path(__file__).parent.parent / "contracts" / "builtin"


class ContractRegistry:
    """
    Registry for loading, resolving, and executing contracts.

    Handles:
    - Discovery across global/workspace/repo tiers
    - Builtin contract loading
    - Inheritance resolution
    - Exemption matching
    """

    def __init__(self, repo_root: Path, workspace_root: Optional[Path] = None,
                 global_root: Optional[Path] = None):
        self.repo_root = Path(repo_root)
        self.workspace_root = Path(workspace_root) if workspace_root else None
        self.global_root = Path(global_root) if global_root else None

        self._contracts: Dict[str, Contract] = {}
        self._exemptions: List[Exemption] = []
        self._loaded = False

    def discover_contracts(self) -> Dict[str, Contract]:
        """Discover and load all contracts from all tiers."""
        if self._loaded:
            return self._contracts

        self._load_contracts_from_dir(BUILTIN_CONTRACTS_DIR, tier="builtin")

        if self.global_root and self.global_root.exists():
            self._load_contracts_from_dir(self.global_root, tier="global")

        if self.workspace_root and self.workspace_root.exists():
            self._load_contracts_from_dir(self.workspace_root, tier="workspace")

        repo_contracts = self.repo_root / "contracts"
        if repo_contracts.exists():
            self._load_contracts_from_dir(repo_contracts, tier="repo")

        agentforge_contracts = self.repo_root / ".agentforge" / "contracts"
        if agentforge_contracts.exists():
            self._load_contracts_from_dir(agentforge_contracts, tier="repo")

        self._loaded = True
        return self._contracts

    def _load_contracts_from_dir(self, directory: Path, tier: str):
        """Load all contract files from a directory."""
        if not directory.exists():
            return

        for yaml_file in directory.glob("**/*.contract.yaml"):
            try:
                contract = self._load_contract_file(yaml_file, tier)
                if contract:
                    self._contracts[contract.name] = contract
            except Exception as e:
                print(f"Warning: Failed to load contract {yaml_file}: {e}")

    def _load_contract_file(self, path: Path, tier: str) -> Optional[Contract]:
        """Load a single contract file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "contract" not in data:
            return None

        contract_data = data["contract"]
        checks_data = data.get("checks", [])

        extends = contract_data.get("extends", [])
        if isinstance(extends, str):
            extends = [extends]

        return Contract(
            name=contract_data["name"],
            type=contract_data["type"],
            description=contract_data.get("description"),
            version=contract_data.get("version", "1.0.0"),
            enabled=contract_data.get("enabled", True),
            extends=extends,
            applies_to=contract_data.get("applies_to", {}),
            tags=contract_data.get("tags", []),
            checks=checks_data,
            source_path=path,
            tier=tier
        )

    def resolve_inheritance(self, contract: Contract) -> Contract:
        """Resolve inheritance chain for a contract."""
        if contract._resolved:
            return contract

        inherited_checks = []
        visited = {contract.name}

        for parent_name in contract.extends:
            parent = self._resolve_contract_reference(parent_name)
            if parent is None:
                print(f"Warning: Contract '{contract.name}' extends unknown '{parent_name}'")
                continue

            if parent.name in visited:
                continue
            visited.add(parent.name)

            self.resolve_inheritance(parent)
            inherited_checks.extend(parent.all_checks())

        contract._inherited_checks = inherited_checks
        contract._resolved = True
        return contract

    def _resolve_contract_reference(self, reference: str) -> Optional[Contract]:
        """Resolve a contract reference to a Contract object."""
        if reference.startswith("_"):
            return self._contracts.get(reference)

        if reference.startswith("workspace:"):
            name = reference[10:]
            return self._contracts.get(name)

        return self._contracts.get(reference)

    # =========================================================================
    # Exemption Management
    # =========================================================================

    def load_exemptions(self) -> List[Exemption]:
        """Load all exemption files from repo."""
        if self._exemptions:
            return self._exemptions

        exemption_dirs = [
            self.repo_root / "exemptions",
            self.repo_root / ".agentforge" / "exemptions",
            self.repo_root / "contracts" / "exemptions",
        ]

        for exemption_dir in exemption_dirs:
            if exemption_dir.exists():
                self._load_exemptions_from_dir(exemption_dir)

        return self._exemptions

    def _load_exemptions_from_dir(self, directory: Path):
        """Load all exemption files from a directory."""
        for yaml_file in directory.glob("**/*.exemptions.yaml"):
            try:
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)

                if not data or "exemptions" not in data:
                    continue

                for exemption_data in data["exemptions"]:
                    exemption = self._parse_exemption(exemption_data)
                    if exemption:
                        self._exemptions.append(exemption)
            except Exception as e:
                print(f"Warning: Failed to load exemptions from {yaml_file}: {e}")

    def _parse_exemption(self, data: Dict) -> Optional[Exemption]:
        """Parse exemption data into Exemption object."""
        checks = data.get("check", [])
        if isinstance(checks, str):
            checks = [checks]

        scope = data.get("scope", {})
        scope_lines = {}
        if "lines" in scope:
            for file_path, ranges in scope["lines"].items():
                scope_lines[file_path] = [(r[0], r[1]) for r in ranges]

        expires = None
        if "expires" in data:
            try:
                expires = date.fromisoformat(data["expires"])
            except ValueError:
                pass

        return Exemption(
            id=data["id"],
            contract=data["contract"],
            checks=checks,
            reason=data["reason"],
            approved_by=data["approved_by"],
            scope_files=scope.get("files", []),
            scope_functions=scope.get("functions", []),
            scope_lines=scope_lines,
            scope_global=scope.get("global", False),
            expires=expires,
            ticket=data.get("ticket"),
            status=data.get("status", "active")
        )

    def find_exemption(self, contract_name: str, check_id: str,
                       file_path: Optional[str] = None,
                       line_number: Optional[int] = None) -> Optional[Exemption]:
        """Find an active exemption that covers a specific violation."""
        self.load_exemptions()

        for exemption in self._exemptions:
            if exemption.contract != contract_name:
                continue
            if check_id not in exemption.checks:
                continue
            if not exemption.is_active():
                continue

            if file_path:
                if line_number is not None:
                    if not exemption.covers_line(file_path, line_number):
                        continue
                elif not exemption.covers_file(file_path):
                    continue

            return exemption

        return None

    # =========================================================================
    # Contract Retrieval
    # =========================================================================

    def _contract_matches_filters(self, contract: Contract, language: Optional[str],
                                   repo_type: Optional[str], include_abstract: bool) -> bool:
        """Check if a contract matches the specified filters."""
        if not contract.enabled:
            return False
        if not include_abstract and contract.is_abstract:
            return False
        applies_to = contract.applies_to
        if language and "languages" in applies_to and language not in applies_to["languages"]:
            return False
        if repo_type and "repo_types" in applies_to and repo_type not in applies_to["repo_types"]:
            return False
        return True

    def get_enabled_contracts(self, language: Optional[str] = None,
                              repo_type: Optional[str] = None,
                              include_abstract: bool = True) -> List[Contract]:
        """Get all enabled contracts, optionally filtered."""
        self.discover_contracts()

        result = []
        for contract in self._contracts.values():
            if not self._contract_matches_filters(contract, language, repo_type, include_abstract):
                continue
            self.resolve_inheritance(contract)
            result.append(contract)

        return result

    def get_applicable_contracts(self, language: Optional[str] = None,
                                  repo_type: Optional[str] = None) -> List[Contract]:
        """Get concrete contracts that apply to this project."""
        return self.get_enabled_contracts(
            language=language,
            repo_type=repo_type,
            include_abstract=False
        )

    def get_contract(self, name: str) -> Optional[Contract]:
        """Get a specific contract by name."""
        self.discover_contracts()
        contract = self._contracts.get(name)
        if contract:
            self.resolve_inheritance(contract)
        return contract

    def get_all_contracts_data(self, language: Optional[str] = None,
                                repo_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all applicable contracts as dictionaries for CI runner consumption.

        Returns contracts with resolved inheritance in dictionary format.
        """
        contracts = self.get_applicable_contracts(language=language, repo_type=repo_type)
        result = []
        for contract in contracts:
            contract_dict = {
                "name": contract.name,
                "type": contract.type,
                "description": contract.description,
                "version": contract.version,
                "enabled": contract.enabled,
                "applies_to": contract.applies_to,
                "tags": contract.tags,
                "checks": contract.all_checks(),
                "tier": contract.tier,
            }
            result.append(contract_dict)
        return result
