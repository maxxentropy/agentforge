"""
Cross-Zone Interaction Detection
================================

Detects interactions between zones:
- Docker Compose service dependencies
- Shared schemas referenced by multiple zones
- HTTP API calls between zones
- Shared library/package references
"""

import re
from pathlib import Path
from typing import Any

from agentforge.core.discovery.domain import Interaction, InteractionType, Zone

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class InteractionDetector:
    """
    Detects cross-zone interactions.

    Analyzes docker-compose files, schema directories, and
    code imports to find how zones communicate.
    """

    def __init__(self, repo_root: Path, zones: list[Zone]):
        self.repo_root = repo_root
        self.zones = zones
        self._zone_by_path: dict[Path, Zone] = {z.path: z for z in zones}

    def detect_all(self) -> list[Interaction]:
        """Detect all cross-zone interactions."""
        interactions: list[Interaction] = []

        # Docker Compose interactions
        interactions.extend(self._detect_docker_compose())

        # Shared schemas
        interactions.extend(self._detect_shared_schemas())

        # Shared packages/references
        interactions.extend(self._detect_shared_packages())

        return interactions

    def _detect_docker_compose(self) -> list[Interaction]:
        """Detect interactions from docker-compose.yaml files."""
        if yaml is None:
            return []

        interactions: list[Interaction] = []

        # Find all docker-compose files
        compose_patterns = [
            "docker-compose.yaml",
            "docker-compose.yml",
            "docker-compose*.yaml",
            "docker-compose*.yml",
            "**/docker-compose.yaml",
            "**/docker-compose.yml",
        ]

        compose_files: set[Path] = set()
        for pattern in compose_patterns:
            compose_files.update(self.repo_root.glob(pattern))

        for compose_file in compose_files:
            try:
                compose_data = yaml.safe_load(compose_file.read_text())
                if not compose_data:
                    continue

                services = compose_data.get("services", {})
                if not services:
                    continue

                # Map services to zones based on build context
                service_zones = self._map_services_to_zones(services)

                # Detect depends_on relationships
                for svc_name, svc_config in services.items():
                    depends = svc_config.get("depends_on", [])
                    if isinstance(depends, dict):
                        depends = list(depends.keys())

                    for dep in depends:
                        from_zone = service_zones.get(svc_name)
                        to_zone = service_zones.get(dep)

                        # Only record cross-zone dependencies
                        if from_zone and to_zone and from_zone != to_zone:
                            interaction = Interaction(
                                id=f"{svc_name}-to-{dep}",
                                interaction_type=InteractionType.DOCKER_COMPOSE,
                                from_zone=from_zone,
                                to_zone=to_zone,
                                details={
                                    "from_service": svc_name,
                                    "to_service": dep,
                                    "compose_file": str(compose_file.relative_to(self.repo_root)),
                                },
                            )
                            interactions.append(interaction)

            except Exception:
                # Skip malformed compose files
                continue

        return interactions

    def _map_services_to_zones(self, services: dict[str, Any]) -> dict[str, str]:
        """Map docker-compose services to zone names."""
        service_zones: dict[str, str] = {}

        for svc_name, svc_config in services.items():
            if not svc_config:
                continue

            build_config = svc_config.get("build")
            if not build_config:
                continue

            # Get build context
            if isinstance(build_config, str):
                context = build_config
            elif isinstance(build_config, dict):
                context = build_config.get("context", ".")
            else:
                continue

            # Resolve context path
            context_path = (self.repo_root / context).resolve()

            # Find which zone contains this context
            for zone in self.zones:
                zone_path = zone.path if zone.path.is_absolute() else (self.repo_root / zone.path)
                zone_path = zone_path.resolve()

                try:
                    context_path.relative_to(zone_path)
                    service_zones[svc_name] = zone.name
                    break
                except ValueError:
                    continue

        return service_zones

    def _detect_shared_schemas(self) -> list[Interaction]:
        """Detect shared schema directories used by multiple zones."""
        interactions: list[Interaction] = []

        # Common schema directories
        schema_dirs = ["schemas", "contracts", "openapi", "proto", "api-specs"]

        for schema_dir_name in schema_dirs:
            schema_path = self.repo_root / schema_dir_name
            if not schema_path.exists() or not schema_path.is_dir():
                continue

            # Find which zones reference files in this directory
            referencing_zones = self._find_zones_referencing(schema_path)

            if len(referencing_zones) > 1:
                interaction = Interaction(
                    id=f"shared-{schema_dir_name}",
                    interaction_type=InteractionType.SHARED_SCHEMA,
                    zones=sorted(referencing_zones),
                    details={
                        "schema_path": schema_dir_name,
                        "format": self._detect_schema_format(schema_path),
                    },
                )
                interactions.append(interaction)

        return interactions

    def _find_zones_referencing(self, target_path: Path) -> list[str]:
        """Find zones that reference a target path in their code."""
        referencing_zones: set[str] = []

        target_relative = target_path.relative_to(self.repo_root)
        target_name = target_path.name

        for zone in self.zones:
            zone_path = zone.path if zone.path.is_absolute() else (self.repo_root / zone.path)

            # Check for references to the target in zone files
            patterns_to_search = [
                f'"{target_name}',       # String reference
                f"'{target_name}",       # String reference (single quote)
                f"/{target_name}",       # Path reference
                str(target_relative),    # Relative path reference
            ]

            for file_path in self._get_zone_files(zone_path, zone.language):
                try:
                    content = file_path.read_text(errors="ignore")
                    if any(pattern in content for pattern in patterns_to_search):
                        referencing_zones.add(zone.name)
                        break
                except Exception:
                    continue

        return list(referencing_zones)

    def _get_zone_files(self, zone_path: Path, language: str) -> list[Path]:
        """Get source files in a zone for analysis."""
        extensions = {
            "python": [".py"],
            "csharp": [".cs"],
            "typescript": [".ts", ".tsx", ".js", ".jsx"],
            "go": [".go"],
            "rust": [".rs"],
        }

        exts = extensions.get(language, [])
        files: list[Path] = []

        for ext in exts:
            files.extend(zone_path.rglob(f"*{ext}"))

        # Limit to prevent performance issues
        return files[:100]

    def _detect_schema_format(self, schema_path: Path) -> str | None:
        """Detect the format of schemas in a directory."""
        if list(schema_path.glob("*.json")):
            return "json-schema"
        if list(schema_path.glob("*.yaml")) or list(schema_path.glob("*.yml")):
            return "openapi"
        if list(schema_path.glob("*.proto")):
            return "protobuf"
        return None

    def _detect_shared_packages(self) -> list[Interaction]:
        """Detect shared library/package references between zones."""
        interactions: list[Interaction] = []

        # Find .NET project references across zones
        project_zones = self._map_projects_to_zones()

        for zone in self.zones:
            if zone.language != "csharp":
                continue

            zone_path = zone.path if zone.path.is_absolute() else (self.repo_root / zone.path)
            for csproj in zone_path.rglob("*.csproj"):
                references = self._get_project_references(csproj)

                for ref_path in references:
                    # Find which zone owns the referenced project
                    ref_resolved = (csproj.parent / ref_path).resolve()
                    for ref_proj, ref_zone in project_zones.items():
                        if ref_resolved == ref_proj.resolve() and ref_zone != zone.name:
                            interaction_id = f"{zone.name}-refs-{ref_zone}"
                            # Avoid duplicates
                            if not any(i.id == interaction_id for i in interactions):
                                interactions.append(Interaction(
                                    id=interaction_id,
                                    interaction_type=InteractionType.SHARED_LIBRARY,
                                    from_zone=zone.name,
                                    to_zone=ref_zone,
                                    details={
                                        "reference_type": "project_reference",
                                        "from_project": str(csproj.name),
                                        "to_project": str(ref_proj.name),
                                    },
                                ))
                            break

        return interactions

    def _map_projects_to_zones(self) -> dict[Path, str]:
        """Map .csproj files to their zone names."""
        project_zones: dict[Path, str] = {}

        for zone in self.zones:
            if zone.language != "csharp":
                continue

            zone_path = zone.path if zone.path.is_absolute() else (self.repo_root / zone.path)
            for csproj in zone_path.rglob("*.csproj"):
                project_zones[csproj] = zone.name

        return project_zones

    def _get_project_references(self, csproj: Path) -> list[str]:
        """Extract ProjectReference paths from a .csproj file."""
        references: list[str] = []

        try:
            content = csproj.read_text()
            # Simple regex to extract ProjectReference Include paths
            pattern = r'<ProjectReference\s+Include="([^"]+)"'
            matches = re.findall(pattern, content)
            references.extend(matches)
        except Exception:
            pass

        return references


def detect_interactions(repo_root: Path, zones: list[Zone]) -> list[Interaction]:
    """
    Convenience function for interaction detection.

    Args:
        repo_root: Path to repository root
        zones: List of detected zones

    Returns:
        List of detected cross-zone interactions

    Example:
        >>> zones = detect_zones(repo_root)
        >>> interactions = detect_interactions(repo_root, zones)
        >>> for i in interactions:
        ...     print(f"{i.from_zone} -> {i.to_zone}: {i.interaction_type.value}")
    """
    detector = InteractionDetector(repo_root, zones)
    return detector.detect_all()
