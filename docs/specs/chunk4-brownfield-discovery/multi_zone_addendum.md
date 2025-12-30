# Chunk 4 Addendum: Multi-Zone Discovery

## Overview

This addendum extends Chunk 4 to support repositories containing multiple languages/technologies. Instead of assuming 1 repo = 1 language, discovery now detects **zones** - distinct areas of the codebase with their own language, patterns, and conformance rules.

## Core Concepts

### Zone

A zone is a coherent area of code with:
- A primary language
- Its own project structure
- Its own patterns and conventions
- Its own conformance rules (contracts)

```yaml
zones:
  edge-controller:
    language: python
    path: edge/
    marker: edge/pyproject.toml
    
  core-service:
    language: csharp
    path: services/
    marker: services/CoreService.sln
```

### Cross-Zone Interaction

Interactions between zones (API calls, shared contracts, etc.):

```yaml
interactions:
  - id: edge-to-service
    from_zone: edge-controller
    to_zone: core-service
    type: http_api
    details:
      endpoint_base: "http://localhost:5000/api/v1"
      contract: openapi/service.yaml
      
  - id: shared-models
    zones: [edge-controller, core-service]
    type: shared_schema
    details:
      schema: schemas/device_telemetry.json
```

### Per-Zone Conformance

Each zone can have its own contracts:

```yaml
# .agentforge/repo.yaml
zones:
  edge-controller:
    contracts:
      - contracts/python-common.contract.yaml
      - contracts/edge-specific.contract.yaml
      
  core-service:
    contracts:
      - contracts/dotnet-clean-arch.contract.yaml
      - contracts/cqrs-patterns.contract.yaml
```

---

## Zone Detection Algorithm

### Phase 1: Auto-Detection

```python
def detect_zones(repo_root: Path) -> List[Zone]:
    """
    Auto-detect language zones from project markers.
    
    Priority order for markers:
    1. Solution files (.sln) - defines .NET zone boundary
    2. pyproject.toml - defines Python zone boundary
    3. package.json - defines Node.js zone boundary
    4. go.mod - defines Go zone boundary
    5. Cargo.toml - defines Rust zone boundary
    6. Fallback: directory with multiple source files
    """
    zones = []
    
    # .NET zones (solution-level)
    for sln in repo_root.rglob("*.sln"):
        if not _is_in_existing_zone(sln, zones):
            zones.append(Zone(
                name=_derive_zone_name(sln),
                path=sln.parent,
                language="csharp",
                marker=sln,
                detection="auto",
            ))
    
    # .NET zones (project-level, if no solution)
    for csproj in repo_root.rglob("*.csproj"):
        if not _is_in_existing_zone(csproj, zones):
            zones.append(Zone(
                name=_derive_zone_name(csproj),
                path=csproj.parent,
                language="csharp",
                marker=csproj,
                detection="auto",
            ))
    
    # Python zones
    for marker in ["pyproject.toml", "setup.py"]:
        for path in repo_root.rglob(marker):
            if not _is_in_existing_zone(path, zones):
                zones.append(Zone(
                    name=_derive_zone_name(path),
                    path=path.parent,
                    language="python",
                    marker=path,
                    detection="auto",
                ))
    
    # Node.js zones
    for pkg_json in repo_root.rglob("package.json"):
        if not _is_in_existing_zone(pkg_json, zones):
            zones.append(Zone(
                name=_derive_zone_name(pkg_json),
                path=pkg_json.parent,
                language="typescript",  # or javascript
                marker=pkg_json,
                detection="auto",
            ))
    
    return zones

def _is_in_existing_zone(path: Path, zones: List[Zone]) -> bool:
    """Check if path is already covered by an existing zone."""
    for zone in zones:
        try:
            path.relative_to(zone.path)
            return True
        except ValueError:
            continue
    return False

def _derive_zone_name(marker: Path) -> str:
    """Derive a zone name from marker file."""
    if marker.suffix == ".sln":
        return marker.stem
    return marker.parent.name
```

### Phase 2: Manual Override

Users can override or extend auto-detection in `repo.yaml`:

```yaml
# .agentforge/repo.yaml
discovery:
  mode: auto  # auto | manual | hybrid
  
zones:
  # Override auto-detected zone
  edge-controller:
    path: edge/
    language: python
    purpose: "Edge device management and Docker orchestration"
    contracts:
      - contracts/python-edge.contract.yaml
    
  # Add zone that wasn't auto-detected
  shared-schemas:
    path: schemas/
    language: json-schema
    purpose: "Shared data contracts between zones"
    
  # Exclude a directory from zone detection
  scripts:
    exclude: true
```

### Phase 3: Zone Merging

When manual config exists, merge with auto-detection:

```python
def merge_zones(auto_zones: List[Zone], config: Dict) -> List[Zone]:
    """Merge auto-detected zones with manual configuration."""
    result = []
    config_zones = config.get("zones", {})
    
    for auto_zone in auto_zones:
        if auto_zone.name in config_zones:
            manual = config_zones[auto_zone.name]
            
            # Check for exclusion
            if manual.get("exclude"):
                continue
                
            # Merge: manual overrides auto
            merged = Zone(
                name=auto_zone.name,
                path=Path(manual.get("path", auto_zone.path)),
                language=manual.get("language", auto_zone.language),
                marker=auto_zone.marker,
                detection="hybrid",
                purpose=manual.get("purpose"),
                contracts=manual.get("contracts", []),
            )
            result.append(merged)
        else:
            result.append(auto_zone)
    
    # Add manual-only zones
    for name, config in config_zones.items():
        if not any(z.name == name for z in result):
            if not config.get("exclude"):
                result.append(Zone(
                    name=name,
                    path=Path(config["path"]),
                    language=config["language"],
                    detection="manual",
                    purpose=config.get("purpose"),
                    contracts=config.get("contracts", []),
                ))
    
    return result
```

---

## Cross-Zone Interaction Detection

### Types of Interactions

| Type | Description | Detection Method |
|------|-------------|------------------|
| `http_api` | REST/HTTP calls between zones | URL patterns, HttpClient usage |
| `grpc` | gRPC service calls | .proto files, client generation |
| `message_queue` | Async messaging | Queue client imports, topic names |
| `shared_schema` | Shared data contracts | Schema files referenced by multiple zones |
| `shared_library` | Shared code/packages | Package references, project references |
| `docker_compose` | Container orchestration | docker-compose.yaml service definitions |
| `file_system` | Shared file/volume access | Mount points, file paths |

### Detection Implementation

```python
class InteractionDetector:
    """Detects cross-zone interactions."""
    
    def detect_all(self, zones: List[Zone], repo_root: Path) -> List[Interaction]:
        interactions = []
        
        # Docker Compose interactions
        interactions.extend(self._detect_docker_compose(zones, repo_root))
        
        # HTTP API interactions
        interactions.extend(self._detect_http_calls(zones))
        
        # Shared schemas
        interactions.extend(self._detect_shared_schemas(zones, repo_root))
        
        # Shared packages/references
        interactions.extend(self._detect_shared_packages(zones))
        
        return interactions
    
    def _detect_docker_compose(self, zones: List[Zone], repo_root: Path) -> List[Interaction]:
        """Detect interactions from docker-compose.yaml."""
        interactions = []
        
        for compose_file in repo_root.rglob("docker-compose*.yaml"):
            compose = yaml.safe_load(compose_file.read_text())
            services = compose.get("services", {})
            
            # Map services to zones
            service_zones = {}
            for svc_name, svc_config in services.items():
                build_context = svc_config.get("build", {})
                if isinstance(build_context, dict):
                    context = build_context.get("context", ".")
                else:
                    context = build_context or "."
                
                # Find which zone this service belongs to
                for zone in zones:
                    if context.startswith(str(zone.path)):
                        service_zones[svc_name] = zone.name
                        break
            
            # Detect depends_on relationships
            for svc_name, svc_config in services.items():
                depends = svc_config.get("depends_on", [])
                if isinstance(depends, dict):
                    depends = list(depends.keys())
                
                for dep in depends:
                    if svc_name in service_zones and dep in service_zones:
                        from_zone = service_zones[svc_name]
                        to_zone = service_zones[dep]
                        
                        if from_zone != to_zone:
                            interactions.append(Interaction(
                                id=f"{svc_name}-to-{dep}",
                                from_zone=from_zone,
                                to_zone=to_zone,
                                type="docker_compose",
                                details={
                                    "from_service": svc_name,
                                    "to_service": dep,
                                    "compose_file": str(compose_file),
                                },
                            ))
        
        return interactions
    
    def _detect_http_calls(self, zones: List[Zone]) -> List[Interaction]:
        """Detect HTTP API calls between zones."""
        interactions = []
        
        # Look for URL patterns, HttpClient usage, requests library usage
        # This is heuristic - look for localhost URLs, service names, etc.
        
        url_patterns = [
            r'http://localhost:\d+',
            r'http://\w+-service',
            r'https?://\$\{?\w+_HOST\}?',
        ]
        
        for zone in zones:
            # Scan zone files for URL patterns
            # If URL matches another zone's service, record interaction
            pass
        
        return interactions
    
    def _detect_shared_schemas(self, zones: List[Zone], repo_root: Path) -> List[Interaction]:
        """Detect shared schema files."""
        interactions = []
        
        # Find schema directories
        schema_dirs = ["schemas", "contracts", "openapi", "proto"]
        
        for schema_dir in schema_dirs:
            schema_path = repo_root / schema_dir
            if schema_path.exists():
                # Check which zones reference these schemas
                referencing_zones = []
                
                for zone in zones:
                    # Check if zone imports/references schemas
                    # This varies by language
                    pass
                
                if len(referencing_zones) > 1:
                    interactions.append(Interaction(
                        id=f"shared-{schema_dir}",
                        zones=referencing_zones,
                        type="shared_schema",
                        details={
                            "schema_path": str(schema_path),
                        },
                    ))
        
        return interactions
```

---

## Per-Zone Conformance

### Contract Association

Each zone can have its own contracts:

```yaml
# .agentforge/repo.yaml
zones:
  edge-controller:
    contracts:
      - contracts/python-common.contract.yaml
      - contracts/edge-device.contract.yaml
      
  core-service:
    contracts:
      - contracts/dotnet-base.contract.yaml
      - contracts/clean-architecture.contract.yaml
      - contracts/cqrs.contract.yaml
```

### Conformance Check Integration

```python
class ConformanceManager:
    def check_zone(self, zone: Zone) -> ConformanceReport:
        """Run conformance checks for a specific zone."""
        contracts = self._load_zone_contracts(zone)
        
        # Filter files to zone path
        zone_files = self._get_zone_files(zone)
        
        # Run checks
        violations = []
        for contract in contracts:
            violations.extend(
                self._run_contract_checks(contract, zone_files)
            )
        
        return ConformanceReport(
            zone=zone.name,
            violations=violations,
        )
    
    def check_all_zones(self, zones: List[Zone]) -> Dict[str, ConformanceReport]:
        """Run conformance for all zones."""
        return {
            zone.name: self.check_zone(zone)
            for zone in zones
        }
```

### Cross-Zone Contracts

Some contracts apply across zones (e.g., shared schema validation):

```yaml
# contracts/cross-zone.contract.yaml
id: cross-zone-compatibility
version: "1.0"
scope: cross-zone

checks:
  - id: schema-sync
    description: "Shared schemas must be in sync across zones"
    type: schema_compatibility
    params:
      schema_path: schemas/
      
  - id: api-contract
    description: "API contracts must match between caller and provider"
    type: openapi_compatibility
    params:
      provider_zone: core-service
      consumer_zones: [edge-controller]
```

---

## Updated Codebase Profile Schema

```yaml
# codebase_profile.yaml (multi-zone)
schema_version: "1.1"
generated_at: "2025-12-30T..."

discovery_metadata:
  version: "1.0.0"
  run_type: full
  duration_ms: 4523
  zones_discovered: 2
  detection_mode: auto  # auto | manual | hybrid

# Global language summary
languages:
  - name: python
    percentage: 35.0
    zones: [edge-controller]
  - name: csharp
    percentage: 65.0
    zones: [core-service]

# Zone definitions
zones:
  edge-controller:
    language: python
    path: edge/
    marker: edge/pyproject.toml
    detection: auto
    purpose: "Edge device management"
    
    structure:
      style: standard
      entry_points:
        - edge/main.py
      test_projects:
        - edge/tests/
        
    patterns:
      error_handling:
        detected: true
        primary: exception_pattern
        confidence: 0.7
        
    conventions:
      naming:
        files:
          pattern: snake_case
          consistency: 0.95
          
    frameworks:
      - pytest
      - pydantic
      - docker-py
      
    contracts:
      - contracts/python-common.contract.yaml
      
  core-service:
    language: csharp
    path: services/
    marker: services/CoreService.sln
    detection: auto
    purpose: "Core business logic service"
    
    structure:
      style: clean-architecture
      confidence: 0.92
      layers:
        - name: domain
          path: services/src/CoreService.Domain
        - name: application
          path: services/src/CoreService.Application
        - name: infrastructure
          path: services/src/CoreService.Infrastructure
        - name: api
          path: services/src/CoreService.Api
      entry_points:
        - services/src/CoreService.Api/CoreService.Api.csproj
      test_projects:
        - services/tests/CoreService.UnitTests
        
    patterns:
      cqrs:
        detected: true
        primary: MediatR
        confidence: 0.94
      error_handling:
        detected: true
        primary: result_pattern
        confidence: 0.88
      repository:
        detected: true
        primary: generic_repository
        confidence: 0.85
      ddd:
        detected: true
        primary: tactical_patterns
        confidence: 0.82
        
    conventions:
      naming:
        interfaces:
          pattern: "I{Name}"
          consistency: 0.98
        classes:
          pattern: PascalCase
          consistency: 0.99
          
    frameworks:
      - ASP.NET Core
      - Entity Framework Core
      - MediatR
      - FluentValidation
      - xUnit
      
    contracts:
      - contracts/dotnet-clean-arch.contract.yaml
      - contracts/cqrs.contract.yaml

# Cross-zone interactions
interactions:
  - id: edge-to-core-api
    from_zone: edge-controller
    to_zone: core-service
    type: http_api
    details:
      protocol: REST
      base_url: "http://core-service:5000/api/v1"
      auth: jwt_bearer
      
  - id: docker-orchestration
    from_zone: edge-controller
    to_zone: core-service
    type: docker_compose
    details:
      compose_file: docker/docker-compose.yaml
      from_service: edge-controller
      to_service: core-api
      
  - id: shared-telemetry-schema
    zones: [edge-controller, core-service]
    type: shared_schema
    details:
      schema: schemas/device_telemetry.json
      format: json-schema

# Conformance summary (per zone)
conformance_summary:
  edge-controller:
    total_violations: 12
    by_severity:
      major: 2
      minor: 10
  core-service:
    total_violations: 5
    by_severity:
      major: 1
      minor: 4
```

---

## CLI Updates

```bash
# Discover all zones (default)
agentforge discover

# Discover specific zone
agentforge discover --zone core-service

# List detected zones
agentforge discover --list-zones

# Show zone interactions
agentforge discover --interactions

# Override detection mode
agentforge discover --mode manual

# Conformance per zone
agentforge conformance check --zone edge-controller
agentforge conformance check --zone core-service
agentforge conformance check  # All zones
```

---

## Implementation Priority

### P0 - Core Multi-Zone Support
1. Zone domain model (`Zone`, `Interaction`)
2. Auto-detection algorithm
3. Per-zone provider dispatch
4. Multi-zone profile generation
5. Updated CLI with `--zone` flag

### P1 - Configuration Support
6. repo.yaml zone configuration parsing
7. Auto/manual/hybrid merge logic
8. Per-zone contract association

### P2 - Interaction Detection
9. Docker Compose interaction detection
10. Shared schema detection
11. Basic HTTP call detection (heuristic)

### P3 - Per-Zone Conformance
12. Zone-scoped conformance checks
13. Cross-zone contract support
14. Per-zone violation tracking

---

## Migration Path

Existing single-language repos continue to work:
- If only one zone detected → behaves like before
- Profile structure is backward compatible
- `zones` section is optional in output
