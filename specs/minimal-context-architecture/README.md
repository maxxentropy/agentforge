# Minimal Context Architecture Specification

**Version:** 2.0
**Status:** Specification Complete
**Date:** January 2025

## Overview

This specification defines AgentForge's context management system, designed to achieve Claude Code-level effectiveness via the Anthropic API while maintaining:

- **Total transparency** in agent thinking
- **Correctness first** in all operations
- **Multi-project, multi-task** scalability
- **Optimal token efficiency** without sacrificing quality

## Document Structure

### Specifications

| File | Description | Spec ID |
|------|-------------|---------|
| [02-agent-config.yaml](./02-agent-config.yaml) | AGENT.md configuration chain | agent-config-v1 |
| [03-fingerprint.yaml](./03-fingerprint.yaml) | Dynamic project fingerprint generator | fingerprint-v1 |
| [04-context-templates.yaml](./04-context-templates.yaml) | Task-type context templates | context-templates-v1 |
| [05-llm-integration.yaml](./05-llm-integration.yaml) | Native API integration (tools, thinking) | llm-integration-v1 |
| [06-compaction.yaml](./06-compaction.yaml) | Progressive compaction manager | compaction-v1 |
| [07-audit.yaml](./07-audit.yaml) | Transparency and audit logging | audit-v1 |
| [08-migration.yaml](./08-migration.yaml) | Migration plan and timeline | migration-v1 |

### Implementation Guides

| File | Description |
|------|-------------|
| [implementation/README.md](./implementation/README.md) | Implementation overview and index |
| [implementation/01-overview-and-simulation.md](./implementation/01-overview-and-simulation.md) | LLM Simulation system |
| [implementation/02-agent-config.md](./implementation/02-agent-config.md) | Agent Config implementation |
| [implementation/03-fingerprint.md](./implementation/03-fingerprint.md) | Fingerprint implementation |
| [implementation/04-context-templates.md](./implementation/04-context-templates.md) | Templates implementation |
| [implementation/05-integration-testing.md](./implementation/05-integration-testing.md) | Integration and testing |

### Supporting Documents

| File | Description |
|------|-------------|
| [docs/architecture/context_engineering_assessment.md](./docs/architecture/context_engineering_assessment.md) | Strategic analysis of Claude Code vs API capabilities |

## Key Principles

```yaml
principles:
  bounded_context: "Each step gets fresh, bounded context (no accumulation)"
  facts_over_data: "Store conclusions with confidence, not raw output"
  explicit_phases: "State machine with guards prevents invalid transitions"
  precomputation: "Do work before LLM calls, reduce model burden"
  native_integration: "Use API features (tools, thinking), not workarounds"
  llm_free_development: "All features testable without API calls"
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ MINIMAL CONTEXT ARCHITECTURE                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AGENT.md Chain ──► Fingerprint Generator                        │
│         │                    │                                   │
│         └──────────┬─────────┘                                   │
│                    ▼                                             │
│            Context Templates                                     │
│                    │                                             │
│         ┌─────────┼─────────┐                                   │
│         ▼         ▼         ▼                                   │
│    Native     Extended   Compaction                              │
│    Tools      Thinking   Manager                                 │
│         │         │         │                                   │
│         └─────────┼─────────┘                                   │
│                   ▼                                              │
│             LLM Executor                                         │
│                   │                                              │
│                   ▼                                              │
│            Audit Logger                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Token Budget Allocation

| Component | Tokens | Notes |
|-----------|--------|-------|
| System prompt | 150 | Minimal, cacheable |
| Tier 1 (always) | 800 | Fingerprint, task, phase |
| Tier 2 (phase) | 1500 | Phase-specific content |
| Tier 3 (on-demand) | 1000 | Historical, additional |
| Buffer | 550 | Response headroom |
| **Total** | **4000** | Per-step budget |

## Implementation Status

| Component | Location | Status |
|-----------|----------|--------|
| AgentConfigLoader | `src/agentforge/core/context/agent_config.py` | ✅ Complete |
| FingerprintGenerator | `src/agentforge/core/context/fingerprint.py` | ✅ Complete |
| Context Templates | `src/agentforge/core/context/templates/` | ✅ Complete |
| LLM Client | `src/agentforge/core/llm/` | ✅ Complete |
| Tool Definitions | `src/agentforge/core/llm/tools.py` | ✅ Complete |
| CompactionManager | `src/agentforge/core/context/compaction.py` | ✅ Complete |
| ContextAuditLogger | `src/agentforge/core/context/audit.py` | ✅ Complete |
| TemplateContextBuilder | `src/agentforge/core/harness/minimal_context/template_context_builder.py` | ✅ Complete |
| MinimalContextExecutorV2 | `src/agentforge/core/harness/minimal_context/executor_v2.py` | ✅ Complete |

## Related Documents

- [North Star Specification](../NorthStar/north_star_specification.md)
- [Agent Harness Specs](../agent-harness/)
