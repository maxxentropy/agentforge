# AgentForge Next Steps & Roadmap

**Last Updated:** December 29, 2025  
**Current Phase:** Foundation Complete  
**Next Phase:** Verification & Context Integration

---

## Executive Summary

The SPEC workflow foundation is complete and operational. The next priorities are:

1. **Verification Engine** - Run actual compiler/tests (not just LLM-based validation)
2. **Context Retrieval** - LSP + Vector hybrid for code context
3. **TDFLOW Workflow** - Test-driven implementation workflow
4. **Real-World Testing** - Validate with actual .NET projects

---

## Current State Assessment

### ✅ Complete & Operational

| Component | Status | Notes |
|-----------|--------|-------|
| SPEC Workflow | ✅ Complete | 6 states, full feedback loop |
| Prompt Contracts | ✅ Complete | 7 contracts, all schema-validated |
| CLI Executor | ✅ Complete | Claude Code + API modes |
| Revision System | ✅ Complete | Interactive + autonomous |
| Schema System | ✅ Complete | 11 schemas |
| YAML Output | ✅ Complete | All outputs structured |
| Session Persistence | ✅ Complete | Revision sessions |
| Human-Agent Handoff | ✅ Complete | Agent flags uncertain |

### 📐 Designed But Not Implemented

| Component | Design Doc | Priority |
|-----------|------------|----------|
| Verification Engine | PRD_v2.md Section 4.2 | HIGH |
| Context Retrieval | docs/design/context_retrieval.md | HIGH |
| TDFLOW Workflow | Research document | MEDIUM |
| Parallel Execution | docs/design/executor_abstraction.md | LOW |

### ❌ Not Yet Designed

| Component | Notes |
|-----------|-------|
| Plugin System | Language providers, custom verifications |
| CI/CD Integration | GitHub Actions, Azure DevOps |
| Project Templates | .NET, Python starter configs |
| Web UI | Optional visual interface |

---

## Prioritized Roadmap

### Phase 1: Verification Engine (HIGH PRIORITY)

**Goal:** Replace LLM-based validation with actual verification

**Why Now:** Currently, VALIDATE uses LLM judgment. We need deterministic checks:
- Does it compile?
- Do tests pass?
- Do architecture rules hold?

**Deliverables:**

1. **correctness.yaml Configuration**
   ```yaml
   checks:
     - id: compile_check
       type: command
       command: "dotnet build {project_path}"
       blocking: true
   
     - id: test_check
       type: command
       command: "dotnet test {project_path}"
       blocking: true
   
     - id: no_public_fields
       type: regex
       pattern: "public [a-zA-Z0-9_<>]+ [a-zA-Z0-9_]+;"
       negative_match: true
       message: "Use properties instead of public fields"
   
     - id: domain_isolation
       type: import_check
       layer: Domain
       forbidden: [Infrastructure, Presentation]
   ```

2. **Verification Runner (Python)**
   ```python
   class VerificationRunner:
       def run_command_check(self, check, context) -> CheckResult
       def run_regex_check(self, check, files) -> CheckResult
       def run_import_check(self, check, files) -> CheckResult
       def generate_report(self, results) -> VerificationReport
   ```

3. **Integration with VALIDATE**
   - Run verification checks before LLM validation
   - Include check results in validation_report.yaml
   - LLM validates semantics, runner validates mechanics

**Effort:** 2-3 days

---

### Phase 2: Context Retrieval (HIGH PRIORITY)

**Goal:** Provide relevant code context to ANALYZE and DRAFT states

**Why Now:** Currently, ANALYZE has no actual code to analyze. Need to:
- Find relevant files based on feature request
- Extract dependencies and patterns
- Stay within token budget

**Deliverables:**

1. **LSP Adapter Layer**
   ```python
   class LSPAdapter:
       def get_definition(self, symbol) -> Location
       def get_references(self, symbol) -> List[Location]
       def get_type_hierarchy(self, type_name) -> TypeTree
       def get_diagnostics(self, file) -> List[Diagnostic]
   ```

2. **Vector Search Integration**
   ```python
   class VectorSearch:
       def index_codebase(self, root_path)
       def search(self, query, top_k=10) -> List[CodeChunk]
   ```

3. **Context Assembler**
   ```python
   class ContextAssembler:
       def retrieve(self, query, budget_tokens) -> CodeContext
       # Combines LSP (structural) + Vector (semantic)
       # Respects token budget
       # Ranks by relevance
   ```

4. **Configuration**
   ```yaml
   # config/context_retrieval.yaml
   retrieval:
     structural:
       enabled: true
       lsp_servers:
         csharp: "csharp-ls"
         python: "pyright"
     semantic:
       enabled: true
       embedding_model: "text-embedding-3-small"
       chunk_size: 500
     budget:
       default_tokens: 6000
       max_tokens: 12000
   ```

**Effort:** 3-5 days

---

### Phase 3: TDFLOW Workflow (MEDIUM PRIORITY)

**Goal:** Implement test-driven development workflow

**Why Now:** After SPEC produces a specification, need to implement it correctly.

**Workflow:**
```
specification.yaml
        │
        ▼
    ┌───────┐
    │  RED  │ Write failing test
    └───┬───┘
        │
        ▼
  ┌───────────┐
  │ VERIFY    │ Run test → MUST FAIL
  │ FAILURE   │
  └─────┬─────┘
        │
        ▼
    ┌───────┐
    │ GREEN │ Write implementation
    └───┬───┘
        │
        ▼
  ┌───────────┐
  │ VERIFY    │ Run test → MUST PASS
  │ SUCCESS   │
  └─────┬─────┘
        │
        ▼
  ┌──────────┐
  │ REFACTOR │ Improve code
  └────┬─────┘
        │
        ▼
  ┌───────────┐
  │ VERIFY    │ Tests still pass
  │ SUCCESS   │
  └─────┬─────┘
        │
        ▼
    ┌──────┐
    │ DONE │
    └──────┘
```

**Deliverables:**

1. **TDFLOW Workflow Definition**
   - workflows/tdflow_workflow.yaml
   - State machine with verification gates

2. **TDFLOW Contracts**
   - contracts/tdflow.red.v1.yaml (write test)
   - contracts/tdflow.green.v1.yaml (write implementation)
   - contracts/tdflow.refactor.v1.yaml (improve code)

3. **Test Runner Integration**
   - Execute tests via Verification Engine
   - Parse test results into structured format
   - Generate feedback prompts on failure

**Effort:** 3-4 days

---

### Phase 4: Real-World Testing (MEDIUM PRIORITY)

**Goal:** Validate system with actual .NET projects

**Why Now:** Need to prove the system works on real code, not just samples.

**Test Scenarios:**

1. **Simple Feature**
   - Add validation to existing entity
   - Expected: Clean SPEC → implementation

2. **Medium Feature**
   - Add new domain entity with repository
   - Expected: Full SPEC cycle with clarifications

3. **Complex Feature**
   - Cross-cutting feature (audit logging)
   - Expected: Multiple SPEC iterations, architectural analysis

**Deliverables:**

1. **Test Project Repository**
   - Sample .NET Clean Architecture project
   - Known patterns and conventions
   - Pre-configured architecture.yaml

2. **Test Scenarios Document**
   - Defined feature requests
   - Expected outputs at each stage
   - Success criteria

3. **Issue Log**
   - Problems encountered
   - Fixes applied
   - Lessons learned

**Effort:** 2-3 days

---

### Phase 5: Polish & Documentation (LOW PRIORITY)

**Goal:** Production readiness

**Deliverables:**

1. **Error Handling**
   - Graceful failures
   - Retry logic
   - User-friendly error messages

2. **Logging**
   - Structured logging
   - Trace IDs for debugging
   - Cost tracking for API calls

3. **Documentation**
   - User guide
   - API reference
   - Tutorial videos

4. **Packaging**
   - pip installable package
   - Docker container
   - Claude Code MCP server

**Effort:** Ongoing

---

## Implementation Order

```
Week 1-2: Verification Engine
├── Day 1: correctness.yaml schema
├── Day 2: Command runner (dotnet build/test)
├── Day 3: Regex checker
├── Day 4: Import/architecture checker
└── Day 5: Integration with VALIDATE

Week 2-3: Context Retrieval
├── Day 1: LSP adapter interface
├── Day 2: C# LSP integration (csharp-ls)
├── Day 3: Vector search (embeddings)
├── Day 4: Context assembler
└── Day 5: Integration with ANALYZE/DRAFT

Week 3-4: TDFLOW
├── Day 1: Workflow definition
├── Day 2: RED contract
├── Day 3: GREEN contract
├── Day 4: Test runner integration
└── Day 5: End-to-end testing

Week 4+: Real-world Testing & Polish
├── Test with actual .NET projects
├── Fix issues discovered
├── Document learnings
└── Prepare for broader use
```

---

## Technical Decisions Needed

### 1. LSP Server Selection

**Options:**
- csharp-ls (lightweight, .NET-based)
- OmniSharp (feature-rich, heavier)
- Roslyn direct (most control, most work)

**Recommendation:** Start with csharp-ls for simplicity

### 2. Vector Database

**Options:**
- FAISS (local, fast, simple)
- ChromaDB (local, more features)
- Pinecone (cloud, managed)

**Recommendation:** FAISS for local development, consider cloud later

### 3. Embedding Model

**Options:**
- text-embedding-3-small (cheap, good)
- text-embedding-3-large (better, more expensive)
- Local model (free, requires GPU)

**Recommendation:** text-embedding-3-small for now

### 4. Test Framework Integration

**Options:**
- Parse dotnet test output
- Use TRX format
- Direct xUnit/NUnit integration

**Recommendation:** Parse dotnet test --logger trx output

---

## Success Criteria

### Phase 1 Complete When:
- [ ] `dotnet build` check runs and catches compilation errors
- [ ] `dotnet test` check runs and reports test failures
- [ ] Regex checks catch architecture violations
- [ ] Verification report includes deterministic results

### Phase 2 Complete When:
- [ ] ANALYZE receives actual code context
- [ ] DRAFT has access to existing patterns
- [ ] Token budget is respected
- [ ] Context is relevant (not random files)

### Phase 3 Complete When:
- [ ] TDFLOW produces failing test from spec
- [ ] TDFLOW produces passing implementation
- [ ] Verification gates enforce RED/GREEN states
- [ ] Full cycle works end-to-end

### Phase 4 Complete When:
- [ ] Successfully specified 3+ features on real project
- [ ] TDFLOW implemented 1+ feature correctly
- [ ] Issues documented and addressed
- [ ] System ready for daily use

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LSP complexity | HIGH | Start simple, expand gradually |
| Token budget overflow | MEDIUM | Aggressive chunking, prioritization |
| Test parsing fragility | MEDIUM | Use structured output (TRX) |
| LLM inconsistency | MEDIUM | Schema validation, retry logic |
| Context irrelevance | HIGH | Hybrid retrieval, relevance scoring |

---

## Resource Requirements

### Tools Needed
- .NET 8 SDK
- csharp-ls or OmniSharp
- Python 3.10+
- Claude Code CLI or API key
- (Optional) FAISS for vector search

### Environment Setup
```bash
# Core
pip install pyyaml jsonschema anthropic

# Context retrieval (when implemented)
pip install faiss-cpu openai

# LSP (when implemented)
dotnet tool install -g csharp-ls
```

---

## Quick Reference

### Commands Available Now
```bash
python execute.py intake --request "..."
python execute.py clarify --answer "..."
python execute.py analyze
python execute.py draft
python execute.py validate
python execute.py revise [--auto] [--continue] [--apply]
python execute.py render-spec
```

### Commands Coming
```bash
python execute.py verify           # Run verification checks
python execute.py context "query"  # Test context retrieval
python execute.py tdflow start     # Start TDFLOW from spec
python execute.py tdflow red       # Write failing test
python execute.py tdflow green     # Write implementation
```

---

*This document should be updated as phases complete.*
