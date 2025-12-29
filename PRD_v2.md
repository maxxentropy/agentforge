# AgentForge PRD v2.0
## Correctness-First Agentic Coding System

**Version:** 2.0  
**Status:** Draft  
**Last Updated:** 2025-01-15  
**Authors:** Human + Claude Collaboration

---

## 1. Vision & Principles

### 1.1 Mission Statement

AgentForge is a development tool that produces production-quality specifications, code, tests, and other development artifacts in a reliable, repeatable manner. It achieves this through rigorous verification at every step, ensuring that **correctness is upstream of everything**.

### 1.2 Core Principle: "Correctness is Upstream"

The system does not allow an agent to proceed to the next step until the current step satisfies a formal **CorrectnessSpecification**. The "Definition of Done" is algorithmic, not linguistic.

**Key Insight:** LLMs are probabilistic generators; software correctness requires deterministic verification. The "Judge" pattern—where verification is performed by tools external to the generating model—is fundamental.

### 1.3 Design Principles

| Principle | Description |
|-----------|-------------|
| **Deterministic Verification** | Correctness is determined by compilers, tests, and static analysis—not by the LLM that generated the code |
| **Spec-Driven Development** | Detailed specifications drive implementation; garbage-in-garbage-out is prevented at the source |
| **Progressive Refinement** | Start with user intent, progressively refine through structured dialogue until unambiguous |
| **Hybrid Intelligence** | Combine LLM creativity with deterministic tooling for best results |
| **Language Agnostic Core** | Core engine is language-agnostic; language support via plugins |
| **Observable & Debuggable** | Full traceability of every decision and action |

### 1.4 Success Metrics

- **Specification Quality:** Specs detailed enough that two developers produce similar implementations
- **First-Pass Success Rate:** % of generated code that passes verification on first attempt
- **Iteration Efficiency:** Average iterations to pass verification
- **User Intervention Rate:** % of tasks requiring human escalation
- **Mode Equivalence:** Outputs are identical regardless of execution mode (human vs API)

### 1.5 Evolution Path

AgentForge is designed to evolve from human-in-loop to autonomous execution:

```
Phase 1: SUBSCRIPTION          Phase 2: API               Phase 3: PARALLEL
┌─────────────────────┐       ┌─────────────────────┐    ┌─────────────────────┐
│ Human-in-the-Loop   │       │ API Sequential      │    │ API Parallel        │
│                     │       │                     │    │                     │
│ • Copy/paste prompts│  ──>  │ • Direct API calls  │ ──>│ • Multiple agents   │
│ • Zero API cost     │       │ • Unattended work   │    │ • Batch processing  │
│ • Build confidence  │       │ • Same verification │    │ • Cost-managed      │
│ • Refine prompts    │       │ • Cost tracking     │    │ • Fire-and-forget   │
└─────────────────────┘       └─────────────────────┘    └─────────────────────┘

Key Principle: IDENTICAL outputs regardless of execution mode
```

**Criticality-Based Routing:**
- **Critical workflows** (SPEC): Always human-attended, even with API
- **Standard workflows** (TDFLOW): Unattended with API, human reviews output
- **Routine workflows** (DOCUMENT): Fully autonomous, parallel-capable

---

## 2. User Personas & Scenarios

### 2.1 Primary Persona: Solo Developer

**Profile:**
- Works primarily in .NET/C# with some Python
- Follows Clean Architecture principles
- Uses Claude via subscription (human-in-loop)
- Wants consistent, high-quality output without constant supervision

**Pain Points:**
- LLM output is inconsistent
- Specifications are often ambiguous
- Code doesn't follow project patterns
- Too much back-and-forth to get correct code

### 2.2 Key Scenarios

1. **New Feature Development:** Transform vague requirement into complete spec, then implementation
2. **Bug Fix:** Reproduce issue, fix, verify no regression
3. **Refactoring:** Characterize existing behavior, refactor, verify behavior preserved
4. **Code Review:** Analyze existing code against architectural rules

### 2.3 Anti-Scenarios (What This Is NOT)

- **Not a Chat Interface:** Not another way to talk to Claude
- **Not Fully Autonomous:** Human remains in the loop for decisions
- **Not Language-Specific:** Not just for .NET (though that's primary)

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SPEC LAYER (YAML)                           │
│  architecture.yaml │ task_types.yaml │ correctness.yaml         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SUPERVISOR LAYER (Python CLI)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Workflow  │  │   Context   │  │      THE JUDGE          │  │
│  │   Engine    │  │   Engine    │  │ (Verification Engine)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTOR LAYER (Claude)                       │
│         Current: Human Copy-Paste │ Future: API Calls           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Layer Definitions

#### 3.2.1 Spec Layer
YAML configuration files that define:
- **architecture.yaml:** Project structure, layer rules, conventions
- **workflows/*.yaml:** Workflow definitions (SPEC, TDFLOW, etc.)
- **correctness/*.yaml:** Verification check definitions

#### 3.2.2 Supervisor Layer (Python CLI)
The orchestration engine that:
- Manages workflow state transitions
- Assembles context for each step
- Executes verification checks
- Generates prompts and processes responses

#### 3.2.3 Executor Layer

The Executor Layer is abstracted to support multiple modes:

| Mode | Implementation | Use Case |
|------|----------------|----------|
| Human-in-Loop | User copies prompts to Claude subscription | Development, critical workflows |
| API Sequential | Direct Anthropic API calls | Standard unattended workflows |
| API Parallel | Concurrent API calls | Routine batch processing |

**Key Design Principle:** Same prompts + same verification = same outputs, regardless of mode.

See: `architecture/executor_abstraction.md` for full specification.

### 3.3 Plugin Architecture

**Decision:** Plugin-based architecture for extensibility

**Extension Points:**
- Language Providers (via LSP adapters)
- Verification Checks
- Workflow Templates
- Context Retrievers
- Output Formatters

### 3.4 Key Design Decision: LSP Integration

Instead of building custom AST parsers, we leverage existing Language Server Protocol implementations:

- **csharp-lsp:** C# language intelligence via Roslyn
- **pyright-lsp:** Python type checking and intelligence
- **clangd-lsp:** C/C++ language intelligence

**Benefits:**
- Compiler-accurate information
- Standardized interface across languages
- Community-maintained
- Richer data (types, hover info, diagnostics)

---

## 4. Context Retrieval Architecture

### 4.1 Overview

Hybrid retrieval combining:
- **Structural Data (via LSP):** What is connected in code
- **Semantic Data (via Embeddings):** What is conceptually related

### 4.2 LSP Adapter Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LSP ADAPTER LAYER                                 │
│                                                                             │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                      │
│   │ csharp-lsp  │   │ pyright-lsp │   │ clangd-lsp  │   (future LSPs)      │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                      │
│          │                 │                 │                              │
│          └─────────────────┼─────────────────┘                              │
│                            ▼                                                │
│                 ┌─────────────────────┐                                     │
│                 │  Unified LSP Client │                                     │
│                 └─────────────────────┘                                     │
│                            │                                                │
│    LSP Operations:         │                                                │
│    - textDocument/documentSymbol  → Find symbols in file                   │
│    - textDocument/definition      → Find where symbol is defined           │
│    - textDocument/references      → Find all usages of symbol              │
│    - workspace/symbol             → Search symbols across project          │
│    - textDocument/hover           → Get type info and documentation        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Structure Index (Cached)

SQLite database populated from LSP queries:

```sql
-- Files table
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    language TEXT,
    hash TEXT,
    last_indexed TIMESTAMP
);

-- Symbols table
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    name TEXT,
    qualified_name TEXT,
    kind TEXT,  -- class, interface, method, property, function
    visibility TEXT,
    start_line INTEGER,
    end_line INTEGER,
    signature TEXT,
    docstring TEXT
);

-- Dependencies table
CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY,
    from_symbol_id INTEGER REFERENCES symbols(id),
    to_symbol_id INTEGER REFERENCES symbols(id),
    dependency_type TEXT  -- inherits, implements, calls, uses
);

-- References table
CREATE TABLE symbol_references (
    id INTEGER PRIMARY KEY,
    symbol_id INTEGER REFERENCES symbols(id),
    referencing_file_id INTEGER REFERENCES files(id),
    line_number INTEGER,
    context TEXT
);
```

### 4.4 Vector Index

For semantic search across code and documentation:

- **Engine:** hnswlib (local, no external service)
- **Embedding Model:** text-embedding-3-small (or local alternative)
- **Chunking:** Symbol-based (one chunk per class/method/function)

### 4.5 Fusion Retrieval Pipeline

```
Query → Entity Extraction → Parallel Retrieval:
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
        LSP-Based Lookup              Vector Similarity Search
        (structural)                  (semantic)
                │                               │
                └───────────────┬───────────────┘
                                ▼
                        Fusion Ranker
                        (Reciprocal Rank Fusion)
                                │
                                ▼
                        Budget Manager
                        (Select within token limit)
                                │
                                ▼
                        Context Chunks
```

### 4.6 Budget Management

Context is organized in layers with token budgets:

| Layer | Budget | Purpose |
|-------|--------|---------|
| Constitution | ~500 | Core rules, never change |
| Project Context | ~2000 | Project structure, conventions |
| Task Context | ~3000 | Current task specifics |
| Step Context | ~2000 | Current workflow step |
| Error Context | Variable | Retry feedback |

---

## 5. Workflow Engine

### 5.1 Workflow Definition Language

Workflows are defined as YAML state machines:

```yaml
workflow:
  name: string
  description: string
  entry_state: string
  terminal_states: [string]
  
states:
  - name: string
    role: string
    inputs: [...]
    outputs: [...]
    verification:
      blocking: [...]
      required: [...]
      advisory: [...]
    transitions:
      - to: string
        condition: string
```

### 5.2 Available Workflows

| Workflow | Purpose | States |
|----------|---------|--------|
| **SPEC** | Requirements → Specification | INTAKE → CLARIFY → ANALYZE → DRAFT → VALIDATE |
| **TDFLOW** | Specification → Implementation | SPEC → RED → GREEN → REVIEW |
| **BUGFIX** | Bug → Fix | REPRODUCE → FIX → VERIFY → REGRESSION |
| **REFACTOR** | Code → Improved Code | CHARACTERIZE → REFACTOR → VERIFY |

### 5.3 SPEC Workflow (Primary)

See: `workflows/spec_workflow.yaml` for complete definition.

**Philosophy:** You can't verify correct implementation of incorrect specifications. SPEC quality is upstream of everything.

---

## 6. Verification Engine ("The Judge")

### 6.1 Philosophy

The Judge uses **deterministic verification** as the **source of truth**, but can use LLMs to interpret results:

```
┌─────────────────────────────────────────────────────────────────┐
│                        THE JUDGE                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          DETERMINISTIC CORE (Source of Truth)           │   │
│  │  - Compiler output: PASS/FAIL                           │   │
│  │  - Test runner output: X passed, Y failed               │   │
│  │  - Static analysis: violations found/not found          │   │
│  │  - Schema validation: valid/invalid                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          LLM AUGMENTATION (Interpretation)              │   │
│  │  - Parse errors into structured data                    │   │
│  │  - Correlate failures to likely causes                  │   │
│  │  - Generate fix suggestions                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Verification Severity Levels

| Level | Description | On Failure |
|-------|-------------|------------|
| **Blocking** | Must pass to proceed | Halt |
| **Required** | Must pass before completion | Retry with feedback |
| **Advisory** | Should pass; human can override | Warn and prompt |
| **Informational** | Reported only | Log |

### 6.3 Check Types

| Type | Implementation | Example |
|------|----------------|---------|
| Command | Run external tool | `dotnet build`, `pytest` |
| Schema | JSON Schema validation | Validate YAML structure |
| Regex | Pattern matching | No TODO markers |
| LSP Diagnostic | Query language server | Get compilation errors |
| LLM | Ask LLM to evaluate | Check for ambiguity |
| Human | Require human confirmation | Approve scope |

---

## 7. Error Recovery

### 7.1 Recovery Strategies

| Strategy | Trigger | Action |
|----------|---------|--------|
| Simple Retry | First failure | Inject error context, retry |
| Context Enrichment | 2+ similar failures | Add more context, retry |
| Decomposition | Task too complex | Break into subtasks |
| Human Escalation | All else fails | Request human help |
| Graceful Abort | Impossible/requested | Document and archive |

### 7.2 Escalation Criteria

- Max retries exceeded (configurable, default 3)
- Same error repeated 3+ times
- Contradictory requirements detected
- Human explicitly requests abort

---

## 8. User Experience

### 8.1 CLI Commands

```bash
# Project setup
forge init                    # Initialize project configuration
forge index                   # Index codebase for retrieval

# Task management  
forge task new "description"  # Create new task
forge task status             # Show current task state
forge task list               # List all tasks

# Workflow execution
forge prompt                  # Generate prompt for current state
forge verify <file>           # Run verification on output
forge next                    # Advance to next state (if verified)

# Debugging
forge trace show              # Show execution trace
forge trace replay <id>       # Replay from checkpoint
```

### 8.2 Human-in-Loop Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User                          AgentForge              Claude    │
│   │                               │                       │     │
│   │  forge task new "Add X"       │                       │     │
│   │ ─────────────────────────────>│                       │     │
│   │                               │ Create task           │     │
│   │                               │ Assemble context      │     │
│   │  <prompt for INTAKE>          │                       │     │
│   │ <─────────────────────────────│                       │     │
│   │                               │                       │     │
│   │  [copy prompt] ───────────────────────────────────────>│    │
│   │                               │                       │     │
│   │  <─────────────────────────────────── [response] ─────│     │
│   │                               │                       │     │
│   │  forge verify <response>      │                       │     │
│   │ ─────────────────────────────>│                       │     │
│   │                               │ Run checks            │     │
│   │  Verification: PASS           │                       │     │
│   │  <prompt for next state>      │                       │     │
│   │ <─────────────────────────────│                       │     │
│   │                               │                       │     │
│   │  ... continues ...            │                       │     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Implementation Roadmap

### Phase 1: SPEC Workflow MVP
- [ ] Core workflow engine (state machine)
- [ ] SPEC workflow implementation (5 states)
- [ ] Basic verification checks (schema, regex)
- [ ] CLI commands (task, prompt, verify)
- [ ] Human-in-loop flow

### Phase 2: Context Retrieval
- [ ] LSP adapter layer
- [ ] Structure index (SQLite cache)
- [ ] Vector index (embeddings)
- [ ] Fusion retrieval pipeline

### Phase 3: TDFLOW Integration
- [ ] TDFLOW workflow implementation
- [ ] Compilation verification (via LSP diagnostics)
- [ ] Test execution verification
- [ ] Code generation prompts

### Phase 4: Language Expansion
- [ ] Python provider (pyright-lsp)
- [ ] Language provider plugin interface
- [ ] Multi-language project support

### Phase 5: API Integration
- [ ] Direct Claude API integration
- [ ] Remove human copy-paste requirement
- [ ] Parallel agent exploration

---

## 10. Appendices

### A. File Structure

```
agentforge/
├── agentforge/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point
│   ├── workflow/
│   │   ├── engine.py          # State machine engine
│   │   └── states.py          # State definitions
│   ├── context/
│   │   ├── retriever.py       # Hybrid retrieval
│   │   ├── lsp_adapter.py     # LSP integration
│   │   └── vector_index.py    # Embedding search
│   ├── verification/
│   │   ├── judge.py           # Verification engine
│   │   └── checks/            # Check implementations
│   ├── execution/
│   │   ├── executor.py        # Executor interface
│   │   ├── human_executor.py  # Human-in-loop implementation
│   │   ├── api_executor.py    # API implementation
│   │   └── cost_tracker.py    # Cost management
│   └── prompts/
│       └── templates/         # Prompt templates
├── config/
│   ├── workflows/             # Workflow definitions
│   ├── schemas/               # JSON schemas
│   ├── correctness/           # Verification rules
│   ├── execution.yaml         # Execution mode config
│   └── criticality.yaml       # Workflow criticality levels
├── tests/
└── pyproject.toml
```

### B. Configuration Schema Reference

See: `schemas/` directory

### C. Glossary

| Term | Definition |
|------|------------|
| **The Judge** | Verification engine that determines correctness via deterministic tools |
| **SPEC Workflow** | Workflow for transforming requirements into specifications |
| **TDFLOW** | Test-Driven Flow: RED → GREEN → REFACTOR |
| **LSP** | Language Server Protocol - standard for code intelligence |
| **Fusion Retrieval** | Combining structural (AST) and semantic (vector) search |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-14 | Initial PRD |
| 2.0 | 2025-01-15 | Expanded architecture, SPEC workflow detail, LSP integration |
