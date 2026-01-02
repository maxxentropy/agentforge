# Chunk 4: Brownfield Discovery - Final Implementation Prompt

## Mission

Implement brownfield discovery that supports:
1. **Multiple languages** in the same repo (Python + .NET + Node.js)
2. **Zone detection** - auto-detect language boundaries, allow manual override
3. **Cross-zone interactions** - track how zones communicate
4. **Per-zone conformance** - each zone gets its own contracts

## Required Reading (In Order)

1. `docs/specs/chunk4-brownfield-discovery/specification.md` - Base requirements
2. `docs/specs/chunk4-brownfield-discovery/multi_zone_addendum.md` - Multi-zone design ⭐
3. `docs/design/implementation_task_chunk_4.md` - Implementation details
4. `docs/prompts/chunk4_dotnet_supplement.md` - .NET provider code

## Key Concept: Zones

A **zone** is a coherent area of code with its own language, patterns, and contracts.

```
my-repo/
├── edge/                    # Python zone (auto-detected from pyproject.toml)
│   ├── pyproject.toml
│   └── controller/
├── services/                # .NET zone (auto-detected from .sln)
│   ├── MyService.sln
│   └── src/
└── schemas/                 # Shared (referenced by multiple zones)
    └── telemetry.json
```

## Architecture

```
tools/discovery/
├── __init__.py
├── domain.py                   # Zone, Interaction, CodebaseProfile
├── manager.py                  # Multi-zone orchestration
├── zones/
│   ├── __init__.py
│   ├── detector.py             # Auto-detect zones from project markers
│   ├── config.py               # Parse repo.yaml zone config
│   └── merger.py               # Merge auto + manual zones
├── providers/
│   ├── __init__.py
│   ├── base.py                 # LanguageProvider ABC
│   ├── python_provider.py
│   └── dotnet_provider.py      # PRIMARY - implement first
├── analyzers/
│   ├── __init__.py
│   ├── structure.py            # Per-zone structure analysis
│   ├── patterns.py             # Per-zone pattern detection
│   ├── architecture.py
│   ├── conventions.py
│   ├── tests.py
│   └── interactions.py         # Cross-zone interaction detection
└── generators/
    ├── __init__.py
    └── profile.py              # Multi-zone YAML output

cli/commands/discover.py        # CLI with --zone flag
```

## Implementation Order

### Phase 1: Domain Model
```python
# domain.py

@dataclass
class Zone:
    """A coherent area of code with its own language."""
    name: str
    path: Path
    language: str
    marker: Optional[Path] = None  # pyproject.toml, .sln, etc.
    detection: str = "auto"  # auto | manual | hybrid
    purpose: Optional[str] = None
    contracts: List[str] = field(default_factory=list)

@dataclass  
class Interaction:
    """Cross-zone communication."""
    id: str
    type: str  # http_api, docker_compose, shared_schema, etc.
    from_zone: Optional[str] = None
    to_zone: Optional[str] = None
    zones: List[str] = field(default_factory=list)  # For shared resources
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ZoneProfile:
    """Discovery results for a single zone."""
    zone: Zone
    structure: Dict[str, Any]
    patterns: Dict[str, PatternDetection]
    conventions: Optional[Dict[str, Any]] = None
    frameworks: List[str] = field(default_factory=list)

@dataclass
class CodebaseProfile:
    """Complete multi-zone profile."""
    schema_version: str
    generated_at: datetime
    discovery_metadata: DiscoveryMetadata
    languages: List[LanguageInfo]  # Aggregated across zones
    zones: Dict[str, ZoneProfile]
    interactions: List[Interaction]
```

### Phase 2: Zone Detection
```python
# zones/detector.py

class ZoneDetector:
    """Auto-detect language zones from project markers."""
    
    MARKERS = {
        "csharp": [("*.sln", "solution"), ("*.csproj", "project")],
        "python": [("pyproject.toml", "pyproject"), ("setup.py", "setup")],
        "typescript": [("package.json", "npm")],
    }
    
    def detect(self, repo_root: Path) -> List[Zone]:
        zones = []
        
        # .NET zones (solution-level first)
        for sln in repo_root.rglob("*.sln"):
            if not self._is_in_existing_zone(sln, zones):
                zones.append(Zone(
                    name=sln.stem,
                    path=sln.parent,
                    language="csharp",
                    marker=sln,
                ))
        
        # Python zones
        for pyproject in repo_root.rglob("pyproject.toml"):
            if not self._is_in_existing_zone(pyproject, zones):
                zones.append(Zone(
                    name=pyproject.parent.name,
                    path=pyproject.parent,
                    language="python",
                    marker=pyproject,
                ))
        
        # Node.js zones (if not in existing zone)
        for pkg in repo_root.rglob("package.json"):
            if "node_modules" not in str(pkg):
                if not self._is_in_existing_zone(pkg, zones):
                    zones.append(Zone(
                        name=pkg.parent.name,
                        path=pkg.parent,
                        language="typescript",
                        marker=pkg,
                    ))
        
        return zones
    
    def _is_in_existing_zone(self, path: Path, zones: List[Zone]) -> bool:
        """Check if path is already covered by an existing zone."""
        for zone in zones:
            try:
                path.relative_to(zone.path)
                return True
            except ValueError:
                continue
        return False
```

### Phase 3: Zone Configuration Merge
```python
# zones/merger.py

class ZoneMerger:
    """Merge auto-detected zones with manual configuration."""
    
    def merge(self, auto_zones: List[Zone], config: Dict) -> List[Zone]:
        config_zones = config.get("zones", {})
        result = []
        
        for auto_zone in auto_zones:
            if auto_zone.name in config_zones:
                manual = config_zones[auto_zone.name]
                
                if manual.get("exclude"):
                    continue
                
                # Manual overrides auto
                merged = Zone(
                    name=auto_zone.name,
                    path=Path(manual.get("path", str(auto_zone.path))),
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
        for name, cfg in config_zones.items():
            if not any(z.name == name for z in result) and not cfg.get("exclude"):
                result.append(Zone(
                    name=name,
                    path=Path(cfg["path"]),
                    language=cfg["language"],
                    detection="manual",
                    purpose=cfg.get("purpose"),
                    contracts=cfg.get("contracts", []),
                ))
        
        return result
```

### Phase 4: Multi-Zone Manager
```python
# manager.py

class DiscoveryManager:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.zone_detector = ZoneDetector()
        self.zone_merger = ZoneMerger()
        self.interaction_detector = InteractionDetector()
        
        self._providers = {
            "python": PythonProvider,
            "csharp": DotNetProvider,
        }
    
    def discover(self, zone_name: str = None) -> CodebaseProfile:
        start_time = time.time()
        
        # Step 1: Detect zones
        auto_zones = self.zone_detector.detect(self.repo_root)
        
        # Step 2: Load config and merge
        config = self._load_config()
        zones = self.zone_merger.merge(auto_zones, config)
        
        # Step 3: Filter to specific zone if requested
        if zone_name:
            zones = [z for z in zones if z.name == zone_name]
        
        # Step 4: Analyze each zone
        zone_profiles = {}
        for zone in zones:
            provider = self._get_provider(zone.language)
            zone_profiles[zone.name] = self._analyze_zone(zone, provider)
        
        # Step 5: Detect cross-zone interactions
        interactions = self.interaction_detector.detect(zones, self.repo_root)
        
        # Step 6: Build unified profile
        return self._build_profile(zones, zone_profiles, interactions, start_time)
    
    def _analyze_zone(self, zone: Zone, provider: LanguageProvider) -> ZoneProfile:
        """Run full analysis on a single zone."""
        # Structure
        structure_analyzer = StructureAnalyzer(zone.path)
        structure = structure_analyzer.analyze()
        
        # Patterns
        pattern_extractor = PatternExtractor(provider, zone.path)
        patterns = pattern_extractor.extract_all()
        
        # Conventions
        convention_inferrer = ConventionInferrer(provider, zone.path)
        conventions = convention_inferrer.infer_all()
        
        # Frameworks
        deps = provider.get_dependencies(zone.path)
        frameworks = self._detect_frameworks(zone.language, deps)
        
        return ZoneProfile(
            zone=zone,
            structure=structure,
            patterns=patterns,
            conventions=conventions,
            frameworks=frameworks,
        )
```

### Phase 5: Interaction Detection
```python
# analyzers/interactions.py

class InteractionDetector:
    """Detect cross-zone interactions."""
    
    def detect(self, zones: List[Zone], repo_root: Path) -> List[Interaction]:
        interactions = []
        
        # Docker Compose
        interactions.extend(self._detect_docker_compose(zones, repo_root))
        
        # Shared schemas
        interactions.extend(self._detect_shared_schemas(zones, repo_root))
        
        return interactions
    
    def _detect_docker_compose(self, zones: List[Zone], repo_root: Path) -> List[Interaction]:
        """Detect interactions from docker-compose files."""
        interactions = []
        
        for compose_file in repo_root.rglob("docker-compose*.yaml"):
            try:
                compose = yaml.safe_load(compose_file.read_text())
                services = compose.get("services", {})
                
                # Map services to zones
                service_zones = self._map_services_to_zones(services, zones, compose_file.parent)
                
                # Find depends_on relationships across zones
                for svc_name, svc_config in services.items():
                    depends = svc_config.get("depends_on", [])
                    if isinstance(depends, dict):
                        depends = list(depends.keys())
                    
                    for dep in depends:
                        from_zone = service_zones.get(svc_name)
                        to_zone = service_zones.get(dep)
                        
                        if from_zone and to_zone and from_zone != to_zone:
                            interactions.append(Interaction(
                                id=f"{svc_name}-to-{dep}",
                                type="docker_compose",
                                from_zone=from_zone,
                                to_zone=to_zone,
                                details={
                                    "compose_file": str(compose_file),
                                    "from_service": svc_name,
                                    "to_service": dep,
                                },
                            ))
            except Exception:
                continue
        
        return interactions
    
    def _detect_shared_schemas(self, zones: List[Zone], repo_root: Path) -> List[Interaction]:
        """Detect shared schema directories."""
        interactions = []
        
        schema_dirs = ["schemas", "contracts", "openapi", "proto"]
        
        for dir_name in schema_dirs:
            schema_path = repo_root / dir_name
            if schema_path.exists() and schema_path.is_dir():
                # This schema dir is potentially shared
                interactions.append(Interaction(
                    id=f"shared-{dir_name}",
                    type="shared_schema",
                    zones=[z.name for z in zones],
                    details={
                        "path": str(schema_path.relative_to(repo_root)),
                    },
                ))
        
        return interactions
```

### Phase 6: DotNetProvider (Primary)

See `docs/prompts/chunk4_dotnet_supplement.md` for complete implementation.

Key methods:
- `detect_project()` - Parse .sln/.csproj
- `extract_symbols()` - Regex-based class/method extraction
- `get_imports()` - Parse `using` statements
- `get_dependencies()` - Extract NuGet PackageReferences

### Phase 7: CLI
```python
# cli/commands/discover.py

def run_discover(args):
    manager = DiscoveryManager(Path.cwd())
    
    # List zones only
    if getattr(args, 'list_zones', False):
        zones = manager.zone_detector.detect(manager.repo_root)
        print("Detected zones:")
        for zone in zones:
            print(f"  {zone.name}: {zone.language} @ {zone.path}")
        return
    
    # Run discovery
    zone_name = getattr(args, 'zone', None)
    profile = manager.discover(zone_name=zone_name)
    
    # Display results
    _display_multi_zone_results(profile)
    
    # Save
    if not getattr(args, 'dry_run', False):
        output_path = manager.save_profile(profile)
        print(f"\n✓ Profile saved to: {output_path}")

# CLI arguments
parser.add_argument('--zone', help='Analyze specific zone only')
parser.add_argument('--list-zones', action='store_true', help='List detected zones')
parser.add_argument('--interactions', action='store_true', help='Show zone interactions')
```

## Expected Output

```yaml
# .agentforge/codebase_profile.yaml
schema_version: "1.1"
generated_at: "2025-12-30T..."

discovery_metadata:
  version: "1.0.0"
  run_type: full
  zones_discovered: 2
  detection_mode: auto

languages:
  - name: python
    percentage: 35.0
    zones: [edge-controller]
  - name: csharp
    percentage: 65.0
    zones: [core-service]

zones:
  edge-controller:
    language: python
    path: edge/
    marker: edge/pyproject.toml
    detection: auto
    
    structure:
      style: standard
      entry_points: [edge/main.py]
      
    patterns:
      error_handling:
        detected: true
        primary: exception_pattern
        confidence: 0.7
        
    frameworks: [pytest, pydantic, docker-py]
    
  core-service:
    language: csharp
    path: services/
    marker: services/CoreService.sln
    detection: auto
    
    structure:
      style: clean-architecture
      confidence: 0.92
      layers:
        - {name: domain, path: services/src/CoreService.Domain}
        - {name: application, path: services/src/CoreService.Application}
        - {name: infrastructure, path: services/src/CoreService.Infrastructure}
        - {name: api, path: services/src/CoreService.Api}
        
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
        confidence: 0.85
      ddd:
        detected: true
        confidence: 0.82
        
    frameworks:
      - ASP.NET Core
      - Entity Framework Core
      - MediatR
      - xUnit

interactions:
  - id: edge-to-core
    type: docker_compose
    from_zone: edge-controller
    to_zone: core-service
    details:
      compose_file: docker/docker-compose.yaml
      
  - id: shared-schemas
    type: shared_schema
    zones: [edge-controller, core-service]
    details:
      path: schemas/
```

## Validation Checklist

### Multi-Zone
- [ ] Auto-detects multiple zones from project markers
- [ ] Handles Python + .NET in same repo
- [ ] Manual zone config in repo.yaml merges with auto
- [ ] `--zone <name>` filters to single zone
- [ ] `--list-zones` shows detected zones

### .NET Zone (Primary)
- [ ] Parses .sln and .csproj files
- [ ] Extracts NuGet PackageReferences
- [ ] Detects Clean Architecture from project names
- [ ] Identifies MediatR/CQRS patterns
- [ ] Detects Result<T> pattern
- [ ] Extracts classes/interfaces/methods

### Python Zone
- [ ] Parses pyproject.toml
- [ ] Extracts symbols via AST
- [ ] Detects pytest, pydantic

### Interactions
- [ ] Detects docker-compose relationships
- [ ] Identifies shared schema directories

### Output
- [ ] Valid YAML profile with zones section
- [ ] All detections have confidence scores
- [ ] Backward compatible (single zone = old format)

## Test on Real Multi-Zone Repo

```bash
cd /path/to/multi-zone-repo
python execute.py discover --list-zones
python execute.py discover --verbose
python execute.py discover --zone core-service
```

---

## Start Here

1. **Domain model** with Zone, Interaction, ZoneProfile
2. **ZoneDetector** for auto-detection
3. **DotNetProvider** (this is the primary use case)
4. **DiscoveryManager** with multi-zone orchestration
5. **InteractionDetector** for docker-compose
6. **Profile generator** for multi-zone YAML
7. **CLI** with --zone flag

**Priority: Get .NET zone detection working first, then add Python support.**
