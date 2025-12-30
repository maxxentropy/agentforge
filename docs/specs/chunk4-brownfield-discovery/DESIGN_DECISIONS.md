# Chunk 4: Brownfield Discovery - Design Decisions Summary

## Quick Reference

| Aspect | Decision |
|--------|----------|
| **Primary Output** | `codebase_profile.yaml` |
| **Location** | `.agentforge/codebase_profile.yaml` |
| **Primary Language** | Python (provider architecture) |
| **Integration** | Triggers Chunk 3 conformance automatically |
| **Estimated Effort** | ~10 days |

---

## Key Design Decisions

### DD-001: Artifact Parity Principle

**Decision:** Brownfield discovery produces the same artifact types as greenfield workflow.

**Rationale:** 
- Enables consistent tooling regardless of project origin
- Violations in brownfield become remediation backlog, not blockers
- Supports gradual improvement of legacy codebases

**Implications:**
- Must generate specification.yaml (as-built)
- Must generate architecture.yaml (as-built)  
- Must integrate with conformance system

---

### DD-002: Language Provider Architecture

**Decision:** Use abstract LanguageProvider interface with language-specific implementations.

**Rationale:**
- Different languages require different analysis tools (AST, LSP, etc.)
- Enables future language support without core changes
- Leverages existing infrastructure (Python AST, .NET LSP)

**Interface:**
```python
class LanguageProvider(ABC):
    def detect_project(self, path: Path) -> ProjectInfo
    def parse_file(self, path: Path) -> AST
    def extract_symbols(self, path: Path) -> List[Symbol]
    def get_dependencies(self, project_path: Path) -> List[Dependency]
```

---

### DD-003: Confidence Scoring for All Detections

**Decision:** Every detection includes a confidence score (0.0-1.0).

**Rationale:**
- Enables human review prioritization
- Supports automated filtering (only apply high-confidence)
- Provides transparency about detection quality

**Thresholds:**
| Range | Interpretation | Action |
|-------|----------------|--------|
| 0.9+ | High confidence | Auto-apply |
| 0.6-0.9 | Medium confidence | Apply with flag |
| 0.3-0.6 | Low confidence | Flag for review |
| <0.3 | Uncertain | Require human decision |

---

### DD-004: Incremental Discovery Support

**Decision:** Support module-by-module discovery with progress tracking.

**Rationale:**
- Large codebases can't be analyzed all at once
- Enables gradual onboarding
- Allows re-analysis of specific modules

**Tracking:**
```yaml
onboarding_progress:
  status: in_progress
  modules:
    src/Domain: analyzed
    src/Application: analyzed
    src/Infrastructure: in_progress
    src/Api: not_started
```

---

### DD-005: Human Curation Workflow

**Decision:** Allow human override of any detected value, preserved across re-discovery.

**Rationale:**
- Machines can't perfectly infer intent
- Business context affects pattern choices
- Supports "teach once, remember always"

**Mechanism:**
- All values marked `source: auto-detected` or `source: human-curated`
- Curated values never overwritten by re-discovery
- Export/import for sharing curations

---

### DD-006: Phased Discovery Pipeline

**Decision:** Discovery runs in 6 sequential phases.

**Phases:**
1. **Language Detection** - What languages/frameworks?
2. **Structure Analysis** - How is it organized?
3. **Pattern Extraction** - What patterns are used?
4. **Architecture Mapping** - What are the dependencies?
5. **Convention Inference** - What naming conventions?
6. **Test Gap Analysis** - What's tested?

**Rationale:**
- Each phase builds on previous
- Enables partial runs (`--phase patterns`)
- Clear progress reporting

---

### DD-007: Integration with Chunk 3 Conformance

**Decision:** Discovery automatically triggers conformance check unless `--no-conformance`.

**Rationale:**
- Brownfield violations should be tracked immediately
- Enables remediation backlog generation
- Consistent with greenfield workflow

**Flow:**
```
Discovery → Profile Generated → Conformance Check → Violations Tracked
```

---

### DD-008: Pattern Detection via Multiple Signals

**Decision:** Detect patterns by combining multiple signal types with weighted scoring.

**Signal Types:**
| Type | Example | Weight |
|------|---------|--------|
| Explicit | `[Command]` attribute | 1.0 |
| Structural | Files in `Commands/` | 0.8 |
| Naming | `*Command.cs` | 0.7 |
| AST | Inherits `IRequest<T>` | 0.9 |
| Statistical | >70% return `Result<T>` | 0.6 |

**Rationale:**
- Single signals can be misleading
- Combined signals increase confidence
- Supports codebases with mixed patterns

---

### DD-009: Reuse Existing Infrastructure

**Decision:** Build on existing tools rather than rebuilding.

**Reuse:**
| Component | From | For |
|-----------|------|-----|
| AST parsing | `builtin_checks_architecture.py` | Pattern detection |
| LSP adapters | `tools/lsp_adapter.py` | Symbol extraction |
| Layer detection | Chunk 2 architecture checks | Architecture mapping |
| Violation tracking | Chunk 3 conformance | Remediation backlog |

---

### DD-010: Schema Enhancement

**Decision:** Enhance existing `codebase_profile.schema.yaml` rather than replace.

**Additions:**
- `discovery_metadata` - Run info
- `patterns` - Detected patterns with confidence
- `conventions` - Naming conventions
- `architecture` - Layer violations
- `test_analysis` - Coverage gaps
- `onboarding_progress` - Module status

---

## Implementation Priority

### Must Have (MVP)
1. Language detection (Python, .NET)
2. Structure analysis (Clean Architecture)
3. Pattern extraction (3+ patterns)
4. Architecture mapping (layer violations)
5. CLI: `agentforge discover`
6. Profile generation
7. Chunk 3 integration

### Should Have
1. Convention inference
2. Test gap analysis
3. Incremental discovery
4. Human curation
5. Dependency analysis

### Nice to Have
1. As-built spec generation
2. TypeScript provider
3. Architecture visualization
4. Pattern trend analysis

---

## Open Questions for Implementation

1. **How to handle mixed-language projects?**
   - Primary language determines provider?
   - Multiple providers with merged results?

2. **What's the minimum confidence for auto-apply?**
   - Proposed: 0.7 for patterns, 0.9 for architecture

3. **How to detect custom patterns?**
   - Configurable pattern definitions?
   - Learn from user examples?

4. **Performance targets for large codebases?**
   - <60 seconds for 1000 files?
   - Caching strategy?

---

## Test Strategy

| Test Type | Scope |
|-----------|-------|
| Unit | Each analyzer independently |
| Integration | Full discovery on sample projects |
| Snapshot | Profile output stability |
| Contract | Schema validation |

**Sample Projects:**
1. `tests/fixtures/discovery/python_clean_arch/`
2. `tests/fixtures/discovery/dotnet_clean_arch/`
3. `tests/fixtures/discovery/mixed_patterns/`
4. `tests/fixtures/discovery/minimal/`

---

## Files to Create

```
tools/discovery/
├── __init__.py
├── manager.py              # DiscoveryManager
├── domain.py               # Domain entities
├── providers/
│   ├── __init__.py
│   ├── base.py             # LanguageProvider ABC
│   ├── python_provider.py
│   └── dotnet_provider.py
├── analyzers/
│   ├── __init__.py
│   ├── structure.py
│   ├── patterns.py
│   ├── architecture.py
│   ├── conventions.py
│   └── tests.py
└── generators/
    ├── __init__.py
    └── profile.py

cli/commands/discover.py

tests/unit/tools/discovery/
├── __init__.py
├── test_manager.py
├── test_providers.py
├── test_analyzers.py
└── test_generators.py

tests/fixtures/discovery/
├── python_clean_arch/
├── dotnet_clean_arch/
├── mixed_patterns/
└── minimal/
```

---

## Related Documents

- [Full Specification](specification.md) - 1494 lines, comprehensive
- [YAML Specification](specification.yaml) - Machine-readable format
- [Chunk 3 Specification](../chunk3-conformance/specification.md) - Integration reference
- [Contract System](../../design/contract_system_improvements_design.md) - Pattern definitions
