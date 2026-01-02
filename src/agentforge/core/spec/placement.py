# @spec_file: .agentforge/specs/core-spec-v1.yaml
# @spec_id: core-spec-v1
# @component_id: core-spec-placement
# @test_path: tests/unit/core/spec/test_placement.py

"""
Spec Placement Analyzer.

Determines where new features belong in the spec space to prevent fragmentation.
Features are COMPONENTS within specs, not standalone specs.

Usage:
    analyzer = SpecPlacementAnalyzer(specs_dir)
    decision = analyzer.analyze(
        feature_description="Add rate limiting to API",
        target_locations=["src/agentforge/core/api/rate_limiter.py"]
    )

    if decision.action == PlacementAction.EXTEND:
        # Add as component to existing spec
        print(f"Extend {decision.spec_id} with new component")
    elif decision.action == PlacementAction.CREATE:
        # Create new spec
        print(f"Create new spec: {decision.suggested_spec_id}")
    elif decision.action == PlacementAction.ESCALATE:
        # Ask user to decide
        print(f"Multiple options: {decision.options}")
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class PlacementAction(Enum):
    """Action to take for spec placement."""
    EXTEND = "extend"      # Add as component to existing spec
    CREATE = "create"      # Create new spec
    ESCALATE = "escalate"  # Multiple valid options, ask user


@dataclass
class SpecInfo:
    """Information about an existing spec."""
    spec_id: str
    name: str
    file_path: Path
    description: str
    covered_locations: set[str]  # Directory prefixes this spec covers
    components: list[dict[str, Any]]

    @classmethod
    def from_yaml(cls, file_path: Path, data: dict[str, Any]) -> 'SpecInfo':
        """Create SpecInfo from parsed YAML."""
        covered_locations = set()
        components = data.get('components', [])

        for comp in components:
            location = comp.get('location', '')
            if location:
                # Extract the exact directory where the component lives
                # src/agentforge/cli/main.py -> src/agentforge/cli
                # src/agentforge/core/api/client.py -> src/agentforge/core/api
                dir_path = Path(location).parent
                covered_locations.add(str(dir_path))

                # Also add subdirectories as covered
                # (files in src/agentforge/cli/commands/ are covered by cli spec)
                # We don't add parent dirs - that would cause over-matching

        return cls(
            spec_id=data.get('spec_id', ''),
            name=data.get('name', ''),
            file_path=file_path,
            description=data.get('description', ''),
            covered_locations=covered_locations,
            components=components,
        )


@dataclass
class PlacementDecision:
    """Result of placement analysis."""
    action: PlacementAction
    reason: str

    # For EXTEND action
    spec_id: str | None = None
    spec_file: Path | None = None

    # For CREATE action
    suggested_spec_id: str | None = None
    suggested_location: str | None = None

    # For ESCALATE action
    options: list[dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        if self.action == PlacementAction.EXTEND:
            return f"EXTEND {self.spec_id}: {self.reason}"
        elif self.action == PlacementAction.CREATE:
            return f"CREATE {self.suggested_spec_id}: {self.reason}"
        else:
            return f"ESCALATE: {self.reason} (Options: {len(self.options)})"


class SpecPlacementAnalyzer:
    """
    Analyzes the spec space to determine where new features belong.

    Prevents spec fragmentation by:
    1. Indexing existing specs by location coverage
    2. Matching new feature locations to covering specs
    3. Recommending EXTEND vs CREATE vs ESCALATE
    """

    def __init__(self, specs_dir: Path | None = None):
        """
        Initialize analyzer.

        Args:
            specs_dir: Path to specs directory (default: .agentforge/specs/)
        """
        self.specs_dir = specs_dir or Path('.agentforge/specs')
        self._specs: dict[str, SpecInfo] = {}
        self._location_index: dict[str, list[str]] = {}  # prefix -> spec_ids
        self._loaded = False

    def load_specs(self) -> None:
        """Load and index all existing specs."""
        self._specs.clear()
        self._location_index.clear()

        if not self.specs_dir.exists():
            self._loaded = True
            return

        for spec_file in self.specs_dir.glob('*.yaml'):
            try:
                with open(spec_file) as f:
                    data = yaml.safe_load(f)

                if not data or 'spec_id' not in data:
                    continue

                spec_info = SpecInfo.from_yaml(spec_file, data)
                self._specs[spec_info.spec_id] = spec_info

                # Index by covered locations
                for location in spec_info.covered_locations:
                    if location not in self._location_index:
                        self._location_index[location] = []
                    self._location_index[location].append(spec_info.spec_id)

            except (OSError, yaml.YAMLError):
                continue

        self._loaded = True

    def _ensure_loaded(self) -> None:
        """Ensure specs are loaded."""
        if not self._loaded:
            self.load_specs()

    def get_spec_ids(self) -> list[str]:
        """Get all loaded spec IDs."""
        self._ensure_loaded()
        return list(self._specs.keys())

    def get_spec(self, spec_id: str) -> SpecInfo | None:
        """Get spec info by ID."""
        self._ensure_loaded()
        return self._specs.get(spec_id)

    def find_covering_specs(self, location: str) -> list[SpecInfo]:
        """
        Find specs that cover a given location.

        A spec covers a location if the location is within a directory
        that the spec has components in.

        Args:
            location: File path (e.g., src/agentforge/core/api/rate_limiter.py)

        Returns:
            List of SpecInfo for specs covering this location
        """
        self._ensure_loaded()

        covering = []
        # Get directory of the location
        location_dir = str(Path(location).parent)

        # Check each spec's covered locations
        for spec in self._specs.values():
            for covered_dir in spec.covered_locations:
                # Check if location is within or equal to covered directory
                # src/agentforge/cli/commands/new.py is within src/agentforge/cli
                if location_dir == covered_dir or location_dir.startswith(covered_dir + '/'):
                    if spec not in covering:
                        covering.append(spec)
                    break

        return covering

    def _extract_module_from_location(self, location: str) -> tuple[str, str]:
        """
        Extract module name and suggested spec_id from location.

        Args:
            location: File path

        Returns:
            (module_name, suggested_spec_id)
        """
        parts = Path(location).parts

        # Standard structure: src/agentforge/{area}/{module}/...
        # e.g., src/agentforge/core/api/... -> core-api
        # e.g., src/agentforge/cli/commands/... -> cli-commands

        if len(parts) >= 4:
            area = parts[2] if len(parts) > 2 else 'core'  # core, cli, etc.
            module = parts[3] if len(parts) > 3 else 'main'

            # Handle special cases
            if area == 'cli' and module == 'commands':
                return 'cli-commands', 'cli-commands-v1'
            elif area == 'cli' and module == 'click_commands':
                return 'cli-click-commands', 'cli-click-commands-v1'
            elif area == 'core':
                return f'core-{module}', f'core-{module}-v1'
            else:
                return f'{area}-{module}', f'{area}-{module}-v1'

        return 'unknown', 'unknown-v1'

    def analyze(
        self,
        feature_description: str,
        target_locations: list[str],
        explicit_spec_id: str | None = None,
    ) -> PlacementDecision:
        """
        Analyze where a new feature should be placed.

        Args:
            feature_description: Description of the feature
            target_locations: List of file paths where implementation will live
            explicit_spec_id: If provided, validate this spec exists

        Returns:
            PlacementDecision indicating EXTEND, CREATE, or ESCALATE
        """
        self._ensure_loaded()

        # If explicit spec provided, validate and use it
        if explicit_spec_id:
            if explicit_spec_id in self._specs:
                spec = self._specs[explicit_spec_id]
                return PlacementDecision(
                    action=PlacementAction.EXTEND,
                    reason="Explicitly specified spec",
                    spec_id=explicit_spec_id,
                    spec_file=spec.file_path,
                )
            else:
                # Spec doesn't exist - could be intentional new spec
                return PlacementDecision(
                    action=PlacementAction.CREATE,
                    reason=f"Specified spec '{explicit_spec_id}' does not exist",
                    suggested_spec_id=explicit_spec_id,
                )

        # No specs loaded - must create new
        if not self._specs:
            module, suggested_id = self._extract_module_from_location(
                target_locations[0] if target_locations else ''
            )
            return PlacementDecision(
                action=PlacementAction.CREATE,
                reason="No existing specs found",
                suggested_spec_id=suggested_id,
            )

        # Find covering specs for all target locations
        all_covering: dict[str, int] = {}  # spec_id -> count of locations covered

        for location in target_locations:
            covering = self.find_covering_specs(location)
            for spec in covering:
                all_covering[spec.spec_id] = all_covering.get(spec.spec_id, 0) + 1

        # No covering specs - need to create new
        if not all_covering:
            module, suggested_id = self._extract_module_from_location(
                target_locations[0] if target_locations else ''
            )
            return PlacementDecision(
                action=PlacementAction.CREATE,
                reason="No existing spec covers these locations",
                suggested_spec_id=suggested_id,
                suggested_location=str(self.specs_dir / f"{suggested_id}.yaml"),
            )

        # Sort by coverage count
        sorted_specs = sorted(
            all_covering.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Single clear winner
        if len(sorted_specs) == 1:
            spec_id = sorted_specs[0][0]
            spec = self._specs[spec_id]
            return PlacementDecision(
                action=PlacementAction.EXTEND,
                reason="Location covered by existing spec",
                spec_id=spec_id,
                spec_file=spec.file_path,
            )

        # Multiple options with same coverage - escalate
        top_count = sorted_specs[0][1]
        tied_specs = [s for s in sorted_specs if s[1] == top_count]

        if len(tied_specs) > 1:
            options = []
            for spec_id, count in tied_specs:
                spec = self._specs[spec_id]
                options.append({
                    'spec_id': spec_id,
                    'description': spec.description,
                    'coverage_count': count,
                    'file_path': str(spec.file_path),
                })

            return PlacementDecision(
                action=PlacementAction.ESCALATE,
                reason="Multiple specs could cover these locations",
                options=options,
            )

        # Clear winner
        spec_id = sorted_specs[0][0]
        spec = self._specs[spec_id]
        return PlacementDecision(
            action=PlacementAction.EXTEND,
            reason=f"Best coverage match ({sorted_specs[0][1]}/{len(target_locations)} locations)",
            spec_id=spec_id,
            spec_file=spec.file_path,
        )

    def suggest_component_id(
        self,
        spec_id: str,
        component_name: str,
    ) -> str:
        """
        Suggest a component_id following naming conventions.

        Args:
            spec_id: Parent spec ID (e.g., cli-v1)
            component_name: Component name (e.g., spec_adapt)

        Returns:
            Suggested component_id (e.g., cli-spec-adapt)
        """
        # Remove version suffix
        base = re.sub(r'-v\d+$', '', spec_id)

        # Normalize component name
        normalized = component_name.lower().replace('-', '_')

        return f"{base}-{normalized}"

    def validate_unique_component_id(
        self,
        spec_id: str,
        component_id: str,
    ) -> bool:
        """
        Check if component_id is unique within the spec.

        Args:
            spec_id: Spec to check
            component_id: Proposed component ID

        Returns:
            True if unique, False if already exists
        """
        self._ensure_loaded()

        spec = self._specs.get(spec_id)
        if not spec:
            return True

        return all(comp.get('component_id') != component_id for comp in spec.components)
