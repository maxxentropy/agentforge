"""
Conflict Resolver
=================

Detects and resolves conflicts between generated and existing contracts.
"""

from pathlib import Path
from typing import Any

from .domain import (
    Conflict,
    ConflictType,
    GeneratedCheck,
    GeneratedContract,
    ResolutionStrategy,
)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class ConflictResolver:
    """
    Detects and resolves conflicts between generated and existing contracts.

    Conflict types:
    - DUPLICATE_ID: Same check ID exists in another contract
    - OVERLAPPING_SCOPE: Same files covered by similar pattern
    - CONTRADICTING: Rules contradict each other
    - VERSION_MISMATCH: Existing was generated with older mapping
    """

    def __init__(
        self,
        root_path: Path,
        contracts_dir: str = "contracts",
        resolution_strategy: ResolutionStrategy = ResolutionStrategy.SKIP,
    ):
        """
        Initialize conflict resolver.

        Args:
            root_path: Repository root path
            contracts_dir: Directory containing existing contracts
            resolution_strategy: Default strategy for resolving conflicts
        """
        self.root_path = Path(root_path).resolve()
        self.contracts_dir = self.root_path / contracts_dir
        self.default_strategy = resolution_strategy
        self._existing_checks: dict[str, dict[str, Any]] = {}
        self._existing_contracts: dict[str, dict[str, Any]] = {}

    def load_existing_contracts(self) -> None:
        """Load all existing contracts from contracts directory."""
        if yaml is None:
            return

        if not self.contracts_dir.exists():
            return

        for contract_file in self.contracts_dir.glob("*.yaml"):
            try:
                content = yaml.safe_load(contract_file.read_text())
                if not isinstance(content, dict):
                    continue

                contract_name = contract_file.stem
                self._existing_contracts[contract_name] = {
                    "path": str(contract_file.relative_to(self.root_path)),
                    "content": content,
                }

                # Index checks by ID
                for check in content.get("checks", []):
                    if isinstance(check, dict) and "id" in check:
                        self._existing_checks[check["id"]] = {
                            "contract": contract_name,
                            "contract_path": str(contract_file.relative_to(self.root_path)),
                            "check": check,
                        }
            except Exception:
                # Skip malformed contracts
                continue

    def detect_conflicts(
        self,
        generated_contract: GeneratedContract
    ) -> list[Conflict]:
        """
        Detect conflicts between a generated contract and existing ones.

        Args:
            generated_contract: The contract being generated

        Returns:
            List of detected conflicts
        """
        conflicts = []

        for check in generated_contract.checks:
            # Check for duplicate IDs
            if check.id in self._existing_checks:
                existing = self._existing_checks[check.id]
                conflicts.append(Conflict(
                    conflict_type=ConflictType.DUPLICATE_ID,
                    generated_check_id=check.id,
                    existing_contract=existing["contract_path"],
                    existing_check_id=check.id,
                    resolution=self._determine_resolution(ConflictType.DUPLICATE_ID),
                    reason=f"Check ID '{check.id}' already exists in {existing['contract']}",
                ))

            # Check for overlapping scope
            overlap_conflict = self._check_overlapping_scope(check)
            if overlap_conflict:
                conflicts.append(overlap_conflict)

        return conflicts

    def _check_overlapping_scope(self, check: GeneratedCheck) -> Conflict | None:
        """Check if generated check overlaps with existing checks."""
        check_paths = set(check.applies_to.get("paths", []))
        if not check_paths:
            return None

        for check_id, existing_info in self._existing_checks.items():
            existing_check = existing_info["check"]
            existing_paths = set(existing_check.get("applies_to", {}).get("paths", []))

            # Check for path overlap
            if check_paths & existing_paths:
                # Check if same type of check
                if existing_check.get("type") == check.check_type:
                    return Conflict(
                        conflict_type=ConflictType.OVERLAPPING_SCOPE,
                        generated_check_id=check.id,
                        existing_contract=existing_info["contract_path"],
                        existing_check_id=check_id,
                        resolution=self._determine_resolution(ConflictType.OVERLAPPING_SCOPE),
                        reason=f"Overlaps with existing check '{check_id}'",
                    )

        return None

    def _determine_resolution(self, conflict_type: ConflictType) -> ResolutionStrategy:
        """Determine resolution strategy for a conflict type."""
        # Use default strategy for most conflicts
        if conflict_type == ConflictType.DUPLICATE_ID:
            return ResolutionStrategy.RENAME
        elif conflict_type == ConflictType.OVERLAPPING_SCOPE:
            return ResolutionStrategy.SKIP
        elif conflict_type == ConflictType.CONTRADICTING:
            return ResolutionStrategy.WARN
        else:
            return self.default_strategy

    def resolve_conflicts(
        self,
        conflicts: list[Conflict],
        generated_contract: GeneratedContract
    ) -> GeneratedContract:
        """
        Apply conflict resolutions to a generated contract.

        Args:
            conflicts: List of conflicts to resolve
            generated_contract: The contract to modify

        Returns:
            Modified contract with conflicts resolved
        """
        checks_to_keep: list = []
        renamed_checks: set[str] = set()

        for check in generated_contract.checks:
            check_conflicts = [c for c in conflicts if c.generated_check_id == check.id]

            if not check_conflicts:
                checks_to_keep.append(check)
                continue

            self._apply_resolutions(check, check_conflicts, renamed_checks, checks_to_keep)

        generated_contract.checks = checks_to_keep
        return generated_contract

    def _apply_resolutions(
        self,
        check: Any,
        check_conflicts: list[Conflict],
        renamed_checks: set[str],
        checks_to_keep: list,
    ) -> None:
        """Apply all resolutions for a single check."""
        for conflict in check_conflicts:
            kept = self._apply_single_resolution(check, conflict, renamed_checks)
            if kept:
                checks_to_keep.append(check)

    def _apply_single_resolution(
        self, check: Any, conflict: Conflict, renamed_checks: set[str]
    ) -> bool:
        """Apply a single resolution strategy. Returns True if check should be kept."""
        if conflict.resolution == ResolutionStrategy.SKIP:
            return False

        if conflict.resolution == ResolutionStrategy.RENAME:
            new_id = self._generate_unique_id(check.id, renamed_checks)
            check.id = new_id
            conflict.new_id = new_id
            renamed_checks.add(new_id)
            return True

        if conflict.resolution == ResolutionStrategy.WARN:
            check.review_required = True
            check.review_reason = f"CONFLICT: {conflict.reason}"
            return True

        # OVERWRITE and MERGE both keep the check
        return True

    def _generate_unique_id(self, base_id: str, existing: set[str]) -> str:
        """Generate a unique check ID by adding suffix."""
        counter = 1
        new_id = f"{base_id}-v{counter}"

        while new_id in existing or new_id in self._existing_checks:
            counter += 1
            new_id = f"{base_id}-v{counter}"

        return new_id

    def get_existing_check_ids(self) -> set[str]:
        """Get set of all existing check IDs."""
        return set(self._existing_checks.keys())

    def get_existing_contract_names(self) -> set[str]:
        """Get set of all existing contract names."""
        return set(self._existing_contracts.keys())
