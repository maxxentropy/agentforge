# Lineage Audit Trail Design

## Problem

The current system tries to reverse-engineer relationships between specs, tests, and code at runtime. This is fragile - when file paths change or conventions evolve, the detection breaks silently.

## Solution

Embed explicit lineage metadata at creation time. Every generated artifact knows its origin.

## Lineage Chain

```
Spec Element → Test File → Implementation File → Violation
     ↓              ↓              ↓                 ↓
  (has ID)    (embeds spec_id)  (embeds spec_id)  (reads metadata)
                               (embeds test_path)
```

## 1. Spec Format Extension

```yaml
# specs/agent-harness/human_escalation_spec.yaml
schema_version: "2.0"
spec_id: "agent-harness.human-escalation"  # Unique spec identifier

components:
  - id: "escalation_manager"          # Stable component ID (used in lineage)
    name: Escalation Manager
    location: tools/harness/escalation/manager.py
    test_location: tests/unit/tools/harness/escalation/test_manager.py

    methods:
      - id: "create_escalation"       # Stable method ID
        name: create_escalation
        description: Create a new escalation request
        # ... rest of method spec
```

## 2. Lineage Metadata Format

Embedded as structured comments at the top of generated files:

```python
# ═══════════════════════════════════════════════════════════════════════════════
# LINEAGE METADATA - DO NOT EDIT
# ═══════════════════════════════════════════════════════════════════════════════
# @generated: 2025-01-15T10:30:00Z
# @generator: tdflow.red.v1
# @spec_file: specs/agent-harness/human_escalation_spec.yaml
# @spec_id: agent-harness.human-escalation
# @component_id: escalation_manager
# @test_path: tests/unit/tools/harness/escalation/test_manager.py
# ═══════════════════════════════════════════════════════════════════════════════
```

## 3. Lineage Data Structure

```python
@dataclass
class LineageMetadata:
    """Metadata embedded in generated files for audit trail."""
    generated_at: datetime
    generator: str              # e.g., "tdflow.red.v1", "tdflow.green.v1"
    spec_file: str              # Path to spec file
    spec_id: str                # Unique spec identifier
    component_id: str           # Component within spec
    method_ids: List[str]       # Methods covered (for partial generation)
    test_path: Optional[str]    # Path to test file (for impl files)
    impl_path: Optional[str]    # Path to impl file (for test files)

    @classmethod
    def parse_from_file(cls, file_path: Path) -> Optional["LineageMetadata"]:
        """Extract lineage metadata from file header comments."""
        ...

    def to_header_comments(self) -> str:
        """Generate header comment block for embedding."""
        ...
```

## 4. Integration Points

### RED Phase (Test Generation)
- Read spec with IDs
- Generate test file with embedded lineage:
  - `@spec_file`, `@spec_id`, `@component_id`
  - `@impl_path` (where implementation will go)

### GREEN Phase (Implementation Generation)
- Read spec with IDs
- Read test file's lineage metadata
- Generate impl file with embedded lineage:
  - `@spec_file`, `@spec_id`, `@component_id`
  - `@test_path` (from test file location)

### Violation Detection
- When creating violation, read file's lineage metadata
- Extract `test_path` directly - no computation needed
- Store in violation record

### Fix Workflow
- Read `test_path` from violation
- Run exactly those tests
- Full audit trail: violation → code → spec → test

## 5. Fallback Behavior

For files without lineage metadata (legacy or manual):
1. Log warning: "No lineage metadata found in {file}"
2. Fall back to convention-based detection (existing code)
3. Mark violation as `lineage_source: "inferred"` vs `"explicit"`

## 6. Benefits

1. **Explicit over implicit**: Relationships are declared, not detected
2. **Auditable**: Every artifact traces to its origin
3. **Stable**: File moves don't break linkage (IDs are stable)
4. **Debuggable**: When something fails, the chain is visible
5. **Extensible**: Can add more metadata (author, ticket, etc.)

## 7. Migration Path

1. Add schema_version check to spec loader
2. Generate IDs for existing specs (deterministic from name)
3. New generated files get full lineage
4. Old files work with fallback detection
5. Gradually migrate as files are regenerated
