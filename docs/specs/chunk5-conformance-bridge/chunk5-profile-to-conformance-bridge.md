# Chunk 5: Profile-to-Conformance Bridge

## Specification Document

**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2025-12-30  
**Authors:** AgentForge Team

---

## Executive Summary

The Profile-to-Conformance Bridge closes the loop between Chunk 4 (Brownfield Discovery) and Chunk 3 (Conformance Tracking). It transforms discovered patterns into enforceable contracts, enabling automated enforcement of codebase conventions.

**Key Value Proposition:**
- Discovery tells you "this codebase uses MediatR CQRS"
- Bridge generates contracts that enforce "commands must implement IRequest"
- Conformance tracks violations of those patterns

**Without the Bridge:** Discovery output is informational only, requiring manual contract creation.  
**With the Bridge:** Discovered patterns become automatically enforced rules.

---

## 1. Problem Statement

### 1.1 Current State

Chunk 4 produces `codebase_profile.yaml` containing:
```yaml
patterns:
  cqrs:
    detected: true
    primary: MediatR
    confidence: 0.92
  error_handling:
    detected: true
    primary: result_pattern
    confidence: 0.85
  repository:
    detected: true
    confidence: 0.88
```

Chunk 3 enforces rules via contracts:
```yaml
checks:
  - id: cqrs-command-pattern
    type: ast
    pattern: "class.*Command.*:.*IRequest"
```

### 1.2 Gap

No automated mechanism connects discovery to conformance:
- User must manually interpret discovery output
- User must manually write matching contracts
- Patterns can drift without detection
- No feedback loop to discovery

### 1.3 Solution

Create a **Bridge** that:
1. Reads codebase profile
2. Maps patterns to check definitions
3. Generates contract YAML
4. Integrates with conformance

---

## 2. Core Concepts

### 2.1 Pattern-to-Check Mapping

Each discovered pattern maps to one or more enforceable checks:

| Discovered Pattern | Generated Check Type | Purpose |
|-------------------|---------------------|---------|
| `cqrs.MediatR` | Naming + AST | Commands implement IRequest |
| `result_pattern` | AST | Methods return Result<T> |
| `repository` | Naming + Structure | Repository interfaces exist |
| `clean-architecture` | Architecture | Layer dependencies enforced |
| `interface_prefix` | Naming | Interfaces start with 'I' |
| `async_suffix` | Naming | Async methods end with 'Async' |

### 2.2 Confidence-Based Enablement

Generated checks are enabled/disabled based on detection confidence:

| Confidence Level | Score Range | Auto-Enable | Review Required |
|-----------------|-------------|-------------|-----------------|
| HIGH | ≥ 0.9 | ✅ Yes | No |
| MEDIUM | 0.6 - 0.9 | ❌ No (draft) | Yes |
| LOW | 0.3 - 0.6 | ❌ No (suggested) | Yes |
| UNCERTAIN | < 0.3 | ❌ Not generated | N/A |

### 2.3 Zone Scoping

Multi-zone repositories get per-zone contracts:

```
zones/
├── edge-controller/     → contracts/edge-controller.contract.yaml (Python)
└── core-service/        → contracts/core-service.contract.yaml (.NET)
```

Each zone's contract only applies to files within that zone.

### 2.4 Generation Metadata

Generated contracts include provenance tracking:

```yaml
generation_metadata:
  source_profile: ".agentforge/codebase_profile.yaml"
  source_hash: "sha256:abc123..."
  generated_at: "2025-12-30T22:00:00Z"
  confidence_threshold: 0.8
  pattern_versions:
    cqrs: "1.0"
    repository: "1.0"
```

---

## 3. Architecture

### 3.1 Component Structure

```
tools/
├── bridge/
│   ├── __init__.py           # Public exports
│   ├── domain.py             # Bridge domain entities
│   ├── generator.py          # Contract generation logic
│   ├── mappings/
│   │   ├── __init__.py
│   │   ├── base.py           # PatternMapping ABC
│   │   ├── cqrs.py           # CQRS/MediatR mappings
│   │   ├── architecture.py   # Clean Architecture mappings
│   │   ├── conventions.py    # Naming convention mappings
│   │   └── registry.py       # Mapping registry
│   ├── resolver.py           # Conflict detection/resolution
│   └── report.py             # Generation report output
├── discovery/                 # Existing Chunk 4
└── conformance/               # Existing Chunk 3

cli/commands/
└── bridge.py                  # CLI commands
```

### 3.2 Data Flow

```
┌─────────────────────────────────────┐
│    codebase_profile.yaml            │
│    (from agentforge discover)       │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Profile Loader                │
│  - Load and validate profile        │
│  - Extract zones and patterns       │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Mapping Engine                │
│  - Look up pattern → check mappings │
│  - Apply confidence thresholds      │
│  - Resolve zone scoping             │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Contract Generator            │
│  - Build contract YAML structure    │
│  - Set enabled/disabled by conf.    │
│  - Add generation metadata          │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Conflict Resolver             │
│  - Check for existing contracts     │
│  - Detect overlapping checks        │
│  - Produce diff/merge suggestions   │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Output Writer                 │
│  - contracts/{zone}.contract.yaml   │
│  - bridge/generation_report.yaml    │
└─────────────────────────────────────┘
```

---

## 4. Pattern Mappings

### 4.1 Mapping Definition Structure

```python
@dataclass
class PatternMapping:
    """Maps a discovered pattern to generated checks."""
    pattern_key: str                    # Key in profile (e.g., "cqrs")
    pattern_values: List[str]           # Specific values (e.g., ["MediatR"])
    generated_checks: List[CheckTemplate]
    languages: List[str]                # ["csharp", "python"]
    min_confidence: float = 0.5
    
@dataclass
class CheckTemplate:
    """Template for generating a check."""
    id_template: str                    # "{zone}-cqrs-commands"
    name: str
    description: str
    check_type: str                     # "ast", "naming", "regex", "custom"
    config: Dict[str, Any]
    severity: str = "warning"
    scope_paths: List[str] = None       # Default scope
    fix_hint: str = None
```

### 4.2 CQRS / MediatR Mapping

**Trigger:** `patterns.cqrs.detected = true` AND `patterns.cqrs.primary = "MediatR"`

**Generated Checks:**

```yaml
# Check 1: Command naming
- id: "{zone}-cqrs-command-naming"
  name: "CQRS Command Naming"
  description: "Commands should end with 'Command'"
  type: naming
  severity: minor
  config:
    pattern: ".*Command$"
    symbol_type: class
  applies_to:
    paths:
      - "**/Commands/**/*.cs"
      - "**/Application/**/Commands/**"

# Check 2: Command implements IRequest
- id: "{zone}-cqrs-command-interface"
  name: "Commands Implement IRequest"
  description: "Commands must implement IRequest<TResponse>"
  type: ast
  severity: warning
  config:
    class_pattern: ".*Command$"
    must_implement: ["IRequest", "IRequest<"]
  applies_to:
    paths:
      - "**/Commands/**/*.cs"

# Check 3: Handler naming
- id: "{zone}-cqrs-handler-naming"
  name: "CQRS Handler Naming"
  description: "Handlers should end with 'Handler'"
  type: naming
  severity: minor
  config:
    pattern: ".*Handler$"
    symbol_type: class
  applies_to:
    paths:
      - "**/Handlers/**/*.cs"
      - "**/*Handler.cs"

# Check 4: Query naming
- id: "{zone}-cqrs-query-naming"
  name: "CQRS Query Naming"
  description: "Queries should end with 'Query'"
  type: naming
  severity: minor
  config:
    pattern: ".*Query$"
    symbol_type: class
  applies_to:
    paths:
      - "**/Queries/**/*.cs"
```

### 4.3 Result Pattern Mapping

**Trigger:** `patterns.error_handling.primary = "result_pattern"`

**Generated Checks:**

```yaml
# Check 1: Application layer returns Result
- id: "{zone}-result-return-types"
  name: "Application Returns Result"
  description: "Application layer methods should return Result<T>"
  type: ast
  severity: info  # Advisory, not blocking
  enabled: false  # Requires manual review
  config:
    method_scope: "public"
    layer: "application"
    return_pattern: "Result<|ErrorOr<|Either<"
  applies_to:
    paths:
      - "**/Application/**/*.cs"
      - "**/application/**/*.py"
  generation:
    review_required: true
    reason: "Result pattern enforcement may break existing code"
```

### 4.4 Clean Architecture Mapping

**Trigger:** `structure.style = "clean-architecture"` AND `structure.layers` defined

**Generated Checks:**

```yaml
# Check 1: Domain isolation
- id: "{zone}-domain-isolation"
  name: "Domain Layer Isolation"
  description: "Domain must not depend on outer layers"
  type: architecture
  severity: error
  config:
    layer: domain
    forbidden_dependencies:
      - infrastructure
      - presentation
      - api
      - web
  applies_to:
    paths: "{layers.domain.paths}"  # Dynamically set from discovery

# Check 2: Application isolation
- id: "{zone}-application-isolation"
  name: "Application Layer Isolation"
  description: "Application may only depend on Domain"
  type: architecture
  severity: error
  config:
    layer: application
    allowed_dependencies:
      - domain
    forbidden_dependencies:
      - infrastructure
      - presentation
  applies_to:
    paths: "{layers.application.paths}"

# Check 3: No direct Infrastructure from Presentation
- id: "{zone}-presentation-no-infra"
  name: "Presentation No Direct Infrastructure"
  description: "Presentation should not directly access Infrastructure"
  type: architecture
  severity: warning
  config:
    layer: presentation
    forbidden_dependencies:
      - infrastructure
  applies_to:
    paths: "{layers.presentation.paths}"
```

### 4.5 Repository Pattern Mapping

**Trigger:** `patterns.repository.detected = true`

**Generated Checks:**

```yaml
# Check 1: Repository interface exists
- id: "{zone}-repository-interface-required"
  name: "Repository Interface Required"
  description: "Repositories should have interface definitions"
  type: naming
  severity: warning
  config:
    pattern: "I.*Repository$"
    symbol_type: interface
    min_count: 1
  applies_to:
    paths:
      - "**/Domain/**/*.cs"
      - "**/Interfaces/**/*.cs"

# Check 2: Repository implementation location
- id: "{zone}-repository-impl-in-infra"
  name: "Repository Implementation in Infrastructure"
  description: "Repository implementations should be in Infrastructure"
  type: file_location
  severity: warning
  config:
    class_pattern: ".*Repository$"
    not_interface: true
    required_path_contains: ["Infrastructure", "Persistence", "Data"]
  applies_to:
    paths:
      - "**/*.cs"
    exclude_paths:
      - "**/Domain/**"
```

### 4.6 Naming Convention Mappings

**Trigger:** `conventions.naming` exists

**Generated Checks:**

```yaml
# Check: Interface I-prefix (from conventions.naming.interfaces)
- id: "{zone}-interface-i-prefix"
  name: "Interface I-Prefix"
  description: "Interfaces must start with 'I'"
  type: naming
  severity: warning
  config:
    pattern: "^I[A-Z]"
    symbol_type: interface
  # Only generated if conventions.naming.interfaces.consistency >= 0.8

# Check: Async suffix (from conventions.naming.async_methods)
- id: "{zone}-async-suffix"
  name: "Async Method Suffix"
  description: "Async methods should end with 'Async'"
  type: naming
  severity: info
  config:
    pattern: ".*Async$"
    symbol_type: method
    has_modifier: "async"
  # Only generated if conventions.naming.async_methods.consistency >= 0.8
```

### 4.7 Python-Specific Mappings

**Trigger:** Zone language = "python"

```yaml
# Check: pytest markers (from frameworks contains "pytest")
- id: "{zone}-pytest-markers"
  name: "pytest Markers Required"
  description: "Tests should have appropriate pytest markers"
  type: ast
  severity: info
  config:
    decorator_patterns: ["@pytest.mark"]
    scope: "test_*"
  applies_to:
    paths:
      - "**/tests/**/*.py"

# Check: Type hints (from conventions.type_hints)
- id: "{zone}-type-hints"
  name: "Type Hints Required"
  description: "Functions should have type hints"
  type: ast
  severity: info
  enabled: false  # Advisory
  config:
    require_return_type: true
    require_param_types: true
```

---

## 5. Conflict Resolution

### 5.1 Conflict Types

| Type | Description | Resolution |
|------|-------------|------------|
| **Duplicate ID** | Generated check ID matches existing | Skip or rename |
| **Overlapping Scope** | Same files, similar pattern | Merge or keep existing |
| **Contradicting Rules** | Generated rule contradicts existing | Warn, keep existing |
| **Version Mismatch** | Existing was generated with older mapping | Offer upgrade |

### 5.2 Resolution Strategy

```python
class ConflictResolver:
    def resolve(self, generated: Contract, existing: List[Contract]) -> Resolution:
        conflicts = self._detect_conflicts(generated, existing)
        
        for conflict in conflicts:
            if conflict.type == ConflictType.DUPLICATE_ID:
                # Rename generated check
                conflict.resolution = self._rename_check(conflict.generated_check)
                
            elif conflict.type == ConflictType.OVERLAPPING_SCOPE:
                # Keep existing, mark generated as duplicate
                conflict.resolution = Resolution.SKIP
                conflict.reason = "Existing check covers same scope"
                
            elif conflict.type == ConflictType.CONTRADICTING:
                # Warn but don't generate
                conflict.resolution = Resolution.WARN
                conflict.reason = "Contradicts existing rule"
        
        return conflicts
```

### 5.3 Resolution Output

```yaml
# .agentforge/bridge/conflicts.yaml
conflicts:
  - id: domain-isolation-duplicate
    type: duplicate_id
    existing:
      contract: "contracts/architecture.contract.yaml"
      check_id: "domain-isolation"
    generated:
      check_id: "core-service-domain-isolation"
    resolution: skip
    reason: "Existing check already enforces domain isolation"
    
  - id: async-suffix-scope-overlap
    type: overlapping_scope
    existing:
      contract: "contracts/naming.contract.yaml"
      check_id: "async-method-naming"
    generated:
      check_id: "core-service-async-suffix"
    resolution: merge
    merged_check:
      id: "async-method-naming"
      applies_to:
        paths:
          - "**/*.cs"  # Combined scope
          - "services/**/*.cs"
```

---

## 6. CLI Interface

### 6.1 Commands

```bash
# Generate contracts from profile
agentforge bridge generate [OPTIONS]

Options:
  --profile PATH        Path to codebase_profile.yaml (default: .agentforge/)
  --output-dir PATH     Output directory for contracts (default: contracts/)
  --zone NAME           Generate for specific zone only
  --confidence FLOAT    Minimum confidence threshold (default: 0.6)
  --dry-run             Preview without writing files
  --force               Overwrite existing contracts
  --format [yaml|json]  Output format

# Preview what would be generated
agentforge bridge preview

# Show pattern → check mappings
agentforge bridge mappings [--pattern NAME]

# Diff generated vs existing
agentforge bridge diff

# Apply generated contracts interactively
agentforge bridge apply [--auto]

# Regenerate from updated profile
agentforge bridge refresh
```

### 6.2 Example Usage

```bash
# Full workflow
$ agentforge discover
✓ Profile saved to .agentforge/codebase_profile.yaml

$ agentforge bridge generate --dry-run
Would generate:
  contracts/core-service.contract.yaml (8 checks)
    - core-service-cqrs-command-naming [enabled]
    - core-service-cqrs-handler-naming [enabled]
    - core-service-domain-isolation [enabled]
    - core-service-result-return-types [disabled, needs review]
    ...
  contracts/edge-controller.contract.yaml (4 checks)
    - edge-controller-type-hints [disabled, needs review]
    ...

Conflicts detected: 1
  - domain-isolation: duplicate of existing check

$ agentforge bridge generate
✓ Generated contracts/core-service.contract.yaml
✓ Generated contracts/edge-controller.contract.yaml
✓ Report saved to .agentforge/bridge/generation_report.yaml

$ agentforge conformance check
```

---

## 7. Output Formats

### 7.1 Generated Contract

```yaml
# contracts/core-service.contract.yaml
# ============================================================================
# AUTO-GENERATED CONTRACT - DO NOT EDIT MANUALLY
# 
# Generated by: AgentForge Bridge v1.0.0
# Source: .agentforge/codebase_profile.yaml
# Generated: 2025-12-30T22:00:00Z
# 
# To regenerate: agentforge bridge refresh --zone core-service
# To customize: Copy to a new file and modify
# ============================================================================

schema_version: "1.0"

contract:
  name: "core-service"
  type: patterns
  description: |
    Auto-generated patterns for core-service zone.
    Based on discovered patterns with HIGH confidence.
  version: "1.0.0-generated"
  enabled: true
  applies_to:
    languages:
      - csharp
    paths:
      - "services/**/*.cs"
    exclude_paths:
      - "**/tests/**"
      - "**/Tests/**"
      - "**/*.Tests.cs"
  tags:
    - generated
    - core-service
    - csharp

generation_metadata:
  source_profile: ".agentforge/codebase_profile.yaml"
  source_hash: "sha256:a1b2c3d4e5f6..."
  generated_at: "2025-12-30T22:00:00Z"
  generator_version: "1.0.0"
  zone: core-service
  confidence_threshold: 0.8
  patterns_mapped:
    - cqrs: 0.92
    - repository: 0.88
    - clean-architecture: 0.90
  regenerate_command: "agentforge bridge refresh --zone core-service"

checks:
  # ===========================================================================
  # CQRS Pattern (confidence: 0.92)
  # ===========================================================================
  
  - id: core-service-cqrs-command-naming
    name: "CQRS Command Naming"
    description: "Commands should follow naming convention"
    type: naming
    enabled: true
    severity: minor
    config:
      pattern: ".*Command$"
      symbol_type: class
    applies_to:
      paths:
        - "**/Commands/**/*.cs"
        - "**/Application/**/Commands/**"
    generation:
      source_pattern: cqrs
      source_confidence: 0.92
      mapping_version: "1.0"
  
  - id: core-service-cqrs-handler-naming
    name: "CQRS Handler Naming"
    description: "Handlers should follow naming convention"
    type: naming
    enabled: true
    severity: minor
    config:
      pattern: ".*Handler$"
      symbol_type: class
    applies_to:
      paths:
        - "**/Handlers/**/*.cs"
        - "**/*Handler.cs"
    generation:
      source_pattern: cqrs
      source_confidence: 0.92
      mapping_version: "1.0"

  # ===========================================================================
  # Clean Architecture (confidence: 0.90)
  # ===========================================================================
  
  - id: core-service-domain-isolation
    name: "Domain Layer Isolation"
    description: "Domain must not depend on outer layers"
    type: architecture
    enabled: true
    severity: error
    config:
      layer: domain
      forbidden_dependencies:
        - infrastructure
        - presentation
        - api
    applies_to:
      paths:
        - "services/src/CoreService.Domain/**/*.cs"
    generation:
      source_pattern: clean-architecture
      source_confidence: 0.90
      mapping_version: "1.0"

  # ===========================================================================
  # Result Pattern (confidence: 0.85) - NEEDS REVIEW
  # ===========================================================================
  
  - id: core-service-result-return-types
    name: "Application Returns Result"
    description: "Application layer methods should return Result<T>"
    type: ast
    enabled: false  # MEDIUM confidence - requires review
    severity: info
    config:
      method_scope: public
      layer: application
      return_pattern: "Result<|ErrorOr<"
    applies_to:
      paths:
        - "services/src/CoreService.Application/**/*.cs"
    generation:
      source_pattern: error_handling
      source_confidence: 0.85
      mapping_version: "1.0"
      review_required: true
      review_reason: "MEDIUM confidence (0.85) - verify pattern is intentional"
    fix_hint: "Enable this check after confirming Result<T> is the intended pattern"
```

### 7.2 Generation Report

```yaml
# .agentforge/bridge/generation_report.yaml
schema_version: "1.0"
generated_at: "2025-12-30T22:00:00Z"
generator_version: "1.0.0"

source:
  profile_path: ".agentforge/codebase_profile.yaml"
  profile_hash: "sha256:a1b2c3d4e5f6..."
  profile_generated: "2025-12-30T21:50:00Z"

configuration:
  confidence_threshold: 0.8
  output_directory: "contracts/"
  dry_run: false

summary:
  zones_processed: 2
  contracts_generated: 2
  total_checks_generated: 12
  checks_enabled: 8
  checks_disabled: 4
  conflicts_detected: 1
  conflicts_resolved: 1

contracts:
  - path: "contracts/core-service.contract.yaml"
    zone: core-service
    language: csharp
    checks:
      total: 8
      enabled: 6
      disabled: 2
    patterns_mapped:
      cqrs:
        confidence: 0.92
        checks_generated: 3
      clean-architecture:
        confidence: 0.90
        checks_generated: 3
      error_handling:
        confidence: 0.85
        checks_generated: 1
        review_required: true
      repository:
        confidence: 0.88
        checks_generated: 1
        
  - path: "contracts/edge-controller.contract.yaml"
    zone: edge-controller
    language: python
    checks:
      total: 4
      enabled: 2
      disabled: 2
    patterns_mapped:
      error_handling:
        confidence: 0.70
        checks_generated: 1
        review_required: true
      pytest:
        confidence: 0.95
        checks_generated: 2
      type_hints:
        confidence: 0.65
        checks_generated: 1
        review_required: true

conflicts:
  - type: duplicate_id
    existing_contract: "contracts/architecture.contract.yaml"
    existing_check: "domain-isolation"
    generated_check: "core-service-domain-isolation"
    resolution: renamed
    new_id: "core-service-layer-domain-isolation"

review_required:
  - contract: "contracts/core-service.contract.yaml"
    checks:
      - id: core-service-result-return-types
        reason: "MEDIUM confidence (0.85)"
        action: "Review and enable if Result<T> is intentional pattern"
        
  - contract: "contracts/edge-controller.contract.yaml"
    checks:
      - id: edge-controller-type-hints
        reason: "MEDIUM confidence (0.65)"
        action: "Review type hint coverage before enabling"

next_steps:
  - "Review disabled checks in generation report"
  - "Enable checks after verification"
  - "Run: agentforge conformance check"
  - "Re-run: agentforge bridge refresh after profile updates"
```

---

## 8. Integration Points

### 8.1 With Discovery (Chunk 4)

```bash
# Option 1: Separate commands
agentforge discover
agentforge bridge generate

# Option 2: Combined flag
agentforge discover --generate-contracts

# Option 3: Auto-bridge on profile update
# In .agentforge/config.yaml:
bridge:
  auto_generate: true
  confidence_threshold: 0.8
```

### 8.2 With Conformance (Chunk 3)

Generated contracts work identically to manual contracts:

```bash
# Check all contracts (including generated)
agentforge conformance check

# Check only generated contracts
agentforge conformance check --tags generated

# Exclude generated contracts
agentforge conformance check --exclude-tags generated
```

### 8.3 With Zone Configuration

Zone-specific contracts respect zone boundaries:

```yaml
# In repo.yaml, user can override generated contracts
zones:
  core-service:
    contracts:
      - contracts/core-service.contract.yaml  # Generated
      - contracts/custom-core-rules.yaml      # Custom additions
    contract_overrides:
      core-service-result-return-types:
        enabled: true  # Override generated disabled state
```

---

## 9. Implementation Plan

### Phase 1: Core Infrastructure (Day 1-2)
1. Domain model (`GeneratedContract`, `CheckTemplate`, `PatternMapping`)
2. Profile loader with validation
3. Basic generator structure
4. CLI skeleton

### Phase 2: Pattern Mappings (Day 2-3)
1. CQRS/MediatR mapping
2. Clean Architecture mapping
3. Repository pattern mapping
4. Naming convention mappings

### Phase 3: Conflict Resolution (Day 3)
1. Existing contract scanner
2. Conflict detection
3. Resolution strategies
4. Diff output

### Phase 4: Integration & Polish (Day 4)
1. Full CLI implementation
2. Generation report
3. Conformance integration
4. Documentation

---

## 10. Success Criteria

### 10.1 Functional Requirements

- [ ] `agentforge bridge generate` produces valid contract YAML
- [ ] Generated contracts pass schema validation
- [ ] Generated contracts work with `agentforge conformance check`
- [ ] HIGH confidence patterns auto-enabled
- [ ] MEDIUM/LOW confidence patterns disabled with review flag
- [ ] Zone scoping produces per-zone contracts
- [ ] Conflicts with existing contracts detected
- [ ] Generation report tracks all mappings

### 10.2 Quality Requirements

- [ ] No false positives from high-confidence mappings
- [ ] Clear provenance in generated contracts
- [ ] Regeneration produces stable output (idempotent)
- [ ] Manual customizations preserved on refresh

### 10.3 Integration Requirements

- [ ] Full pipeline works: discover → bridge → conformance
- [ ] `--generate-contracts` flag on discover
- [ ] Zone boundaries respected
- [ ] Tags allow filtering generated contracts

---

## 11. Appendix

### A. Mapping Registry

Complete list of supported pattern → check mappings:

| Pattern Key | Pattern Value | Language | Check Type | Check ID Template |
|------------|---------------|----------|------------|-------------------|
| `cqrs` | `MediatR` | csharp | naming | `{zone}-cqrs-command-naming` |
| `cqrs` | `MediatR` | csharp | ast | `{zone}-cqrs-command-interface` |
| `cqrs` | `*` | * | naming | `{zone}-cqrs-handler-naming` |
| `repository` | `true` | csharp | naming | `{zone}-repository-interface` |
| `repository` | `true` | csharp | location | `{zone}-repository-in-infra` |
| `clean-architecture` | `*` | * | architecture | `{zone}-domain-isolation` |
| `clean-architecture` | `*` | * | architecture | `{zone}-application-isolation` |
| `error_handling` | `result_pattern` | * | ast | `{zone}-result-return-types` |
| `interface_prefix` | `I{Name}` | csharp | naming | `{zone}-interface-i-prefix` |
| `async_suffix` | `{Name}Async` | csharp | naming | `{zone}-async-suffix` |
| `pytest` | `true` | python | ast | `{zone}-pytest-markers` |
| `type_hints` | `true` | python | ast | `{zone}-type-hints` |

### B. Extension Points

To add new pattern mappings:

1. Create mapping class in `tools/bridge/mappings/`
2. Implement `PatternMapping` interface
3. Register in `mappings/registry.py`
4. Add tests in `tests/unit/tools/bridge/`

```python
# Example: Custom mapping
class MyPatternMapping(PatternMapping):
    pattern_key = "my_pattern"
    languages = ["csharp"]
    
    def generate_checks(self, detection: Detection, zone: Zone) -> List[Check]:
        if detection.confidence < 0.5:
            return []
        
        return [
            Check(
                id=f"{zone.name}-my-pattern-check",
                type="custom",
                config={...},
            )
        ]
```

### C. Configuration Schema

```yaml
# .agentforge/bridge.yaml (optional)
bridge:
  enabled: true
  auto_generate: false  # Generate on discover
  
  confidence:
    auto_enable_threshold: 0.9
    include_threshold: 0.5
    
  output:
    directory: "contracts/generated/"
    file_pattern: "{zone}.contract.yaml"
    
  mappings:
    # Enable/disable specific mappings
    cqrs: true
    repository: true
    clean-architecture: true
    conventions: true
    
  conflicts:
    strategy: "skip"  # skip | rename | merge | overwrite
    
  zones:
    # Per-zone overrides
    core-service:
      extra_checks:
        - id: custom-check
          type: regex
          config: {...}
```