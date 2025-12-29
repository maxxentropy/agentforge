# Design Documents

This directory contains **design documentation** that explains the architecture
and rationale behind AgentForge. These are explanatory documents, not specifications.

## Document Purpose

| Document | Purpose |
|----------|---------|
| `context_retrieval.md` | Explains hybrid LSP + vector search design |
| `executor_abstraction.md` | Explains human-in-loop vs API execution modes |
| `prompt_contracts.md` | Explains prompt contract concepts (superseded by actual contracts) |

## Relationship to Specifications

```
docs/design/           ← Explains WHY and HOW (design rationale)
    │
    ▼
config/                ← Actual configuration (verifiable)
schemas/               ← Validation schemas (machine-verifiable)
contracts/             ← Prompt contracts (machine-verifiable)
```

## Design vs Specification

| Aspect | Design Docs (here) | Specifications (config/, schemas/) |
|--------|--------------------|------------------------------------|
| Purpose | Explain rationale | Define structure |
| Format | Markdown with diagrams | YAML with JSON Schema |
| Verifiable | No | Yes |
| Audience | Humans | Humans + Machines |
| Changes | Update freely | Version and validate |

## Reading Order

1. **PRD_v2.md** — Start here for overall vision
2. **prompt_contracts.md** — Understand the contract concept
3. **executor_abstraction.md** — Understand execution modes
4. **context_retrieval.md** — Understand code retrieval

Then look at the actual implementations:
- `contracts/` — Real prompt contracts
- `config/` — Real configuration files
- `schemas/` — Validation schemas

## Note on prompt_contracts.md

The `prompt_contracts.md` file describes the prompt contract concept. The actual
contracts are now in `contracts/*.yaml`. The design doc remains useful for
understanding the WHY behind the contract structure.
