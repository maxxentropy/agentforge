# AgentForge PRD Package

This package contains the complete Product Requirements Document and supporting specifications for the AgentForge "Correctness-First" Agentic Coding System.

## Document Index

### Core Documents

| Document | Description |
|----------|-------------|
| [PRD_v2.md](PRD_v2.md) | Main Product Requirements Document |
| [workflows/spec_workflow.yaml](workflows/spec_workflow.yaml) | Complete SPEC workflow definition |
| [architecture/context_retrieval.md](architecture/context_retrieval.md) | Hybrid LSP + Vector retrieval architecture |
| [architecture/executor_abstraction.md](architecture/executor_abstraction.md) | Human-in-loop to API transition design |
| [architecture/prompt_contracts.md](architecture/prompt_contracts.md) | Prompt contract specification and examples |
| [schemas/spec_workflow_schemas.md](schemas/spec_workflow_schemas.md) | JSON schemas for SPEC workflow artifacts |

### Ready-to-Use Prompt Templates

| Template | State | Usage |
|----------|-------|-------|
| [prompts/spec/intake.md](prompts/spec/intake.md) | INTAKE | Capture initial request |
| [prompts/spec/clarify.md](prompts/spec/clarify.md) | CLARIFY | Q&A dialogue |
| [prompts/spec/analyze.md](prompts/spec/analyze.md) | ANALYZE | Codebase analysis |
| [prompts/spec/draft.md](prompts/spec/draft.md) | DRAFT | Write specification |
| [prompts/spec/validate.md](prompts/spec/validate.md) | VALIDATE | Final review |

### Formal Prompt Contracts (Machine-Verifiable)

| Contract | Description |
|----------|-------------|
| [contracts/spec.intake.v1.yaml](contracts/spec.intake.v1.yaml) | INTAKE with JSON Schema validation |
| [contracts/spec.clarify.v1.yaml](contracts/spec.clarify.v1.yaml) | CLARIFY with JSON Schema validation |
| [contracts/spec.analyze.v1.yaml](contracts/spec.analyze.v1.yaml) | ANALYZE with JSON Schema validation |
| [contracts/spec.draft.v1.yaml](contracts/spec.draft.v1.yaml) | DRAFT with JSON Schema validation |
| [contracts/spec.validate.v1.yaml](contracts/spec.validate.v1.yaml) | VALIDATE with JSON Schema validation |

### Configuration Files (Machine-Verifiable)

| Config | Schema | Purpose |
|--------|--------|---------|
| [config/execution.yaml](config/execution.yaml) | [execution.schema.yaml](schemas/execution.schema.yaml) | Execution mode settings |
| [config/architecture.yaml](config/architecture.yaml) | [architecture.schema.yaml](schemas/architecture.schema.yaml) | Project rules |
| [config/context_retrieval.yaml](config/context_retrieval.yaml) | [context_retrieval.schema.yaml](schemas/context_retrieval.schema.yaml) | Code retrieval |

### Directory Structure

```
agentforge-prd/
├── README.md                           # This file
├── QUICKSTART.md                       # Getting started guide
├── PRD_v2.md                          # Main PRD document
├── run_contract.py                    # CLI runner
│
├── contracts/                         # Formal prompt contracts (verifiable)
│   ├── spec.intake.v1.yaml
│   ├── spec.clarify.v1.yaml
│   ├── spec.analyze.v1.yaml
│   ├── spec.draft.v1.yaml
│   └── spec.validate.v1.yaml
│
├── schemas/                           # JSON Schemas for validation
│   ├── prompt-contract.schema.yaml    # Meta-schema for contracts
│   ├── intake_record.schema.yaml      # Output schemas
│   ├── clarification_log.schema.yaml
│   ├── analysis_report.schema.yaml
│   ├── validation_report.schema.yaml
│   ├── execution.schema.yaml          # Config schemas
│   ├── architecture.schema.yaml
│   └── context_retrieval.schema.yaml
│
├── config/                            # Configuration files (verifiable)
│   ├── execution.yaml                 # Execution mode settings
│   ├── architecture.yaml              # Project architecture rules
│   └── context_retrieval.yaml         # Code retrieval settings
│
├── prompts/                           # Human-readable templates
│   └── spec/
│       ├── intake.md
│       ├── clarify.md
│       ├── analyze.md
│       ├── draft.md
│       └── validate.md
│
├── tools/                             # Validation tools
│   ├── contract_validator.py          # Contract validation
│   └── validate_schema.py             # Schema validation
│
├── docs/                              # Design documentation
│   └── design/
│       ├── context_retrieval.md       # LSP + vector design
│       ├── executor_abstraction.md    # Execution modes design
│       └── prompt_contracts.md        # Contract concept design
│
├── workflows/
│   └── spec_workflow.yaml             # SPEC workflow definition
│
├── sample_data/
│   └── project_context.yaml           # Sample project config
│
└── outputs/                           # Generated files (gitignore)
```

## Key Design Decisions

### 1. LSP Integration (vs Custom AST Parsers)
Instead of building custom Abstract Syntax Tree parsers for each language, we leverage existing Language Server Protocol implementations:
- **csharp-lsp**: Uses Roslyn for compiler-accurate C# analysis
- **pyright-lsp**: Microsoft's Python type checker
- **clangd-lsp**: For C/C++ support

This provides compiler-accurate information with zero maintenance burden.

### 2. Hybrid Retrieval (LSP + Vector)
Context retrieval combines:
- **Structural (LSP)**: Precise code relationships (what depends on what)
- **Semantic (Embeddings)**: Conceptual similarity (what's related in meaning)

Neither alone is sufficient; together they provide comprehensive retrieval.

### 3. SPEC-First Development
The SPEC workflow is prioritized because:
- "Correctness is upstream" — bad specs lead to bad code
- Detailed specs enable verification
- Two developers should produce similar implementations from same spec

### 4. Plugin Architecture
Extensibility via plugins for:
- Language providers (via LSP adapters)
- Verification checks
- Workflow templates
- Context retrievers

### 5. Executor Abstraction (Human → API Evolution)
The system is designed to work identically in multiple execution modes:
- **Phase 1 (Subscription)**: Human copies prompts to Claude — $0 cost, build confidence
- **Phase 2 (API)**: Direct API calls — unattended, cost-tracked
- **Phase 3 (Parallel)**: Multiple concurrent agents — batch processing

**Key Principle**: Same prompts + same verification = same outputs, regardless of mode.

**Criticality Routing**:
- Critical workflows (SPEC) → Always human-attended
- Standard workflows (TDFLOW) → Unattended OK, human reviews output
- Routine workflows (DOCUMENT) → Fully autonomous, parallel-capable

## Bootstrapping Strategy

AgentForge is designed to build itself using itself:

```
Stage 1: Manual SPEC Workflow
├── Create SPEC workflow + prompt contracts (done)
├── Validate by using it via subscription ($0)
└── Output: Working SPEC workflow

Stage 2: Use SPEC to Specify Components
├── SPEC → Verification Engine specification
├── SPEC → Context Retrieval specification
├── SPEC → TDFLOW workflow specification
└── Output: Detailed specs for all components

Stage 3: Implement from Specs
├── Build components to specification
├── Verify against acceptance criteria
└── Output: Working components

Stage 4: Use TDFLOW to Implement Remaining Features
├── Now have working SPEC + TDFLOW
├── Use them to build everything else
└── Output: Complete system
```

**Key Principle:** Each stage produces artifacts that drive the next stage.

## Implementation Phases

1. **Phase 1**: SPEC Workflow MVP
2. **Phase 2**: Context Retrieval (LSP + Vector)
3. **Phase 3**: TDFLOW Integration
4. **Phase 4**: Language Expansion
5. **Phase 5**: API Integration

## Open Questions

1. **Context Retrieval Tuning**: Optimal balance between LSP structural and vector semantic retrieval requires empirical testing
2. **Token Budgets**: Optimal context budgets per layer need validation
3. **Verification Check ROI**: Which checks provide most value per compute cost

## Next Steps

- [ ] Finalize SPEC workflow verification checks
- [ ] Design TDFLOW workflow
- [ ] Create implementation task breakdown
- [ ] Prototype LSP adapter layer
