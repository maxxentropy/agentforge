# @spec_file: .agentforge/specs/core-bridge-v1.yaml
# @spec_id: core-bridge-v1
# @component_id: core-bridge-orchestrator
# @test_path: tests/unit/tools/tdflow/test_orchestrator.py

"""
Bridge Orchestrator
===================

Main orchestrator for the Profile-to-Conformance Bridge.
Coordinates profile loading, mapping, conflict resolution, and contract generation.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .conflict_resolver import ConflictResolver
from .contract_builder import ContractBuilder
from .domain import (
    Conflict,
    ContractSummary,
    GeneratedContract,
    GenerationReport,
    ReviewItem,
)
from .mappings import MappingRegistry
from .profile_loader import ProfileLoader


class BridgeOrchestrator:
    """
    Orchestrates the Profile-to-Conformance Bridge process.

    Workflow:
    1. Load codebase profile
    2. Create mapping contexts for each zone
    3. Run pattern mappings to generate checks
    4. Detect and resolve conflicts
    5. Build and write contract files
    6. Generate report

    Example:
        >>> orchestrator = BridgeOrchestrator(Path("."))
        >>> contracts, report = orchestrator.generate()
        >>> for contract in contracts:
        ...     print(f"{contract.name}: {len(contract.checks)} checks")
    """

    def __init__(
        self,
        root_path: Path,
        profile_path: Path | None = None,
        output_dir: str = "contracts",
        confidence_threshold: float = 0.6,
        verbose: bool = False,
    ):
        """
        Initialize bridge orchestrator.

        Args:
            root_path: Repository root path
            profile_path: Optional custom profile path
            output_dir: Output directory for contracts
            confidence_threshold: Minimum confidence for check inclusion
            verbose: Enable verbose output
        """
        self.root_path = Path(root_path).resolve()
        self.profile_path = profile_path
        self.output_dir = output_dir
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose

        # Components
        self.loader = ProfileLoader(self.root_path)
        self.resolver = ConflictResolver(self.root_path, output_dir)
        self.builder = ContractBuilder(self.root_path, output_dir)

        # State
        self._profile: dict[str, Any] | None = None
        self._contracts: list[GeneratedContract] = []
        self._all_conflicts: list[Conflict] = []

    def generate(
        self,
        zone_filter: str | None = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> tuple[list[GeneratedContract], GenerationReport]:
        """
        Generate contracts from profile.

        Args:
            zone_filter: Optional zone name to filter to
            dry_run: Preview without writing files
            force: Overwrite existing contracts

        Returns:
            Tuple of (list of generated contracts, generation report)
        """
        datetime.now()

        # Load profile
        if self.verbose:
            print(f"Loading profile from {self.profile_path or '.agentforge/codebase_profile.yaml'}...")

        self._profile = self.loader.load(self.profile_path)

        # Load existing contracts for conflict detection
        if self.verbose:
            print("Loading existing contracts...")
        self.resolver.load_existing_contracts()

        # Get zones to process
        zones = self.loader.get_zones()
        if zone_filter:
            zones = [z for z in zones if z == zone_filter]
            if not zones:
                raise ValueError(f"Zone not found: {zone_filter}")

        if self.verbose:
            print(f"Processing {len(zones)} zone(s): {zones}")

        # Generate contracts for each zone
        self._contracts = []
        self._all_conflicts = []

        for zone_name in zones:
            try:
                contract = self._generate_zone_contract(zone_name)
                if contract and contract.checks:
                    self._contracts.append(contract)
            except Exception as e:
                if self.verbose:
                    print(f"  Warning: Failed to generate for zone {zone_name}: {e}")

        # Write contracts (unless dry run)
        written_paths = []
        if not dry_run:
            for contract in self._contracts:
                path = self.builder.write_contract(contract)
                if path:
                    written_paths.append(path)
                    if self.verbose:
                        print(f"  Wrote: {path}")

        # Generate report
        report = self._generate_report(
            zones_processed=len(zones),
            dry_run=dry_run,
            written_paths=written_paths,
        )

        return self._contracts, report

    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def _create_zone_context(self, zone_name: str):
        """Create mapping context for a zone."""
        return self.loader.create_context(
            zone_name if zone_name != "default" else None
        )

    def _handle_conflicts(self, contract: GeneratedContract) -> GeneratedContract:
        """Detect and resolve conflicts in a contract."""
        conflicts = self.resolver.detect_conflicts(contract)
        if not conflicts:
            return contract
        self._log(f"    Detected {len(conflicts)} conflict(s)")
        self._all_conflicts.extend(conflicts)
        return self.resolver.resolve_conflicts(conflicts, contract)

    def _generate_zone_contract(
        self,
        zone_name: str
    ) -> GeneratedContract | None:
        """Generate contract for a single zone."""
        self._log(f"  Generating checks for zone: {zone_name}...")

        context = self._create_zone_context(zone_name)
        checks = MappingRegistry.generate_checks(context)

        self._log(f"    Generated {len(checks)} checks from mappings")

        if not checks:
            return None

        contract = self.builder.build_contract(
            zone_name=zone_name if zone_name != "default" else None,
            language=context.language,
            checks=checks,
            profile_path=self.loader.profile_path or "",
            profile_hash=self.loader.profile_hash or "",
            confidence_threshold=self.confidence_threshold,
        )

        contract = self._handle_conflicts(contract)
        self._log(f"    Final: {contract.enabled_count} enabled, {contract.disabled_count} disabled")

        return contract

    def _generate_report(
        self,
        zones_processed: int,
        dry_run: bool,
        written_paths: list[Path],
    ) -> GenerationReport:
        """Generate summary report."""
        report = GenerationReport(
            generated_at=datetime.now(),
            profile_path=self.loader.profile_path or "",
            profile_hash=self.loader.profile_hash or "",
            profile_generated=self.loader.profile_generated_at,
            confidence_threshold=self.confidence_threshold,
            output_directory=self.output_dir,
            dry_run=dry_run,
            zones_processed=zones_processed,
            contracts_generated=len(self._contracts),
        )

        # Calculate totals
        for contract in self._contracts:
            report.total_checks += len(contract.checks)
            report.checks_enabled += contract.enabled_count
            report.checks_disabled += contract.disabled_count

            # Build contract summary
            patterns_mapped = {}
            for check in contract.checks:
                pattern = check.source_pattern
                if pattern not in patterns_mapped:
                    patterns_mapped[pattern] = {
                        "confidence": check.source_confidence,
                        "checks_generated": 0,
                        "review_required": False,
                    }
                patterns_mapped[pattern]["checks_generated"] += 1
                if check.review_required:
                    patterns_mapped[pattern]["review_required"] = True

            summary = ContractSummary(
                path=str(self.builder.get_output_path(contract.name)),
                zone=contract.zone,
                language=contract.language,
                total_checks=len(contract.checks),
                enabled_checks=contract.enabled_count,
                disabled_checks=contract.disabled_count,
                patterns_mapped=patterns_mapped,
            )
            report.contracts.append(summary)

            # Build review items
            review_items = []
            for check in contract.checks:
                if check.review_required:
                    review_items.append(ReviewItem(
                        contract=contract.name,
                        check_id=check.id,
                        reason=check.review_reason or "Review required",
                        action="Review and enable if pattern is intentional",
                    ))
            if review_items:
                report.review_required[contract.name] = review_items

        # Add conflicts
        report.conflicts = self._all_conflicts
        report.conflicts_detected = len(self._all_conflicts)
        report.conflicts_resolved = len([c for c in self._all_conflicts if c.new_id])

        # Add next steps
        if report.checks_disabled > 0:
            report.next_steps.append("Review disabled checks in generated contracts")
            report.next_steps.append("Enable checks after verification")
        if report.contracts_generated > 0:
            report.next_steps.append("Run: agentforge conformance check")
        report.next_steps.append("Re-run: agentforge bridge refresh after profile updates")

        return report

    def preview(self) -> str:
        """
        Preview what would be generated without writing.

        Returns:
            Summary string of what would be generated
        """
        contracts, report = self.generate(dry_run=True)

        lines = [
            "Would generate:",
            "",
        ]

        for contract in contracts:
            path = self.builder.get_output_path(contract.name)
            lines.append(f"  {path} ({len(contract.checks)} checks)")

            for check in contract.checks:
                status = "[enabled]" if check.enabled else "[disabled, needs review]"
                lines.append(f"    - {check.id} {status}")

        if self._all_conflicts:
            lines.append("")
            lines.append(f"Conflicts detected: {len(self._all_conflicts)}")
            for conflict in self._all_conflicts:
                lines.append(f"  - {conflict.generated_check_id}: {conflict.reason}")

        return "\n".join(lines)

    def list_mappings(self, pattern_filter: str | None = None) -> list[dict]:
        """
        List available pattern mappings.

        Args:
            pattern_filter: Optional pattern key to filter by

        Returns:
            List of mapping info dictionaries
        """
        mappings = MappingRegistry.get_mapping_info()

        if pattern_filter:
            mappings = [m for m in mappings if m["pattern_key"] == pattern_filter]

        return mappings

    def refresh(
        self,
        zone_filter: str | None = None,
    ) -> tuple[list[GeneratedContract], GenerationReport]:
        """
        Regenerate contracts from updated profile.

        Same as generate() but meant to be called after profile updates.

        Args:
            zone_filter: Optional zone to regenerate

        Returns:
            Tuple of (contracts, report)
        """
        return self.generate(zone_filter=zone_filter, dry_run=False, force=True)

    def write_report(self, report: GenerationReport, path: Path | None = None) -> Path:
        """
        Write generation report to file.

        Args:
            report: Report to write
            path: Optional custom path

        Returns:
            Path to written report
        """
        import yaml

        if path is None:
            report_dir = self.root_path / ".agentforge" / "bridge"
            report_dir.mkdir(parents=True, exist_ok=True)
            path = report_dir / "generation_report.yaml"

        path.write_text(yaml.dump(report.to_dict(), default_flow_style=False, sort_keys=False))
        return path
