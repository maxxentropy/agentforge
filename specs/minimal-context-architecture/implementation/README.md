# Minimal Context Architecture - Implementation Specification

**Status:** Complete  
**Date:** January 2025  
**Total Parts:** 5

## Overview

This implementation specification provides detailed implementation guidance for the Minimal Context Architecture, including a key innovation: **LLM simulation for development and testing**.

## Key Innovation: LLM Simulation

All components can be developed and tested WITHOUT invoking the real LLM API:

```bash
# Development mode - no API costs
export AGENTFORGE_LLM_MODE=simulated
pytest tests/  # All tests pass without API

# Record real session for replay
export AGENTFORGE_LLM_MODE=record
export AGENTFORGE_LLM_RECORDING=session.yaml
python -m agentforge fix src/file.py  # Records responses

# Replay recorded session (deterministic)
export AGENTFORGE_LLM_MODE=playback
python -m agentforge fix src/file.py  # Uses recorded responses
```

## Document Parts

| Part | File | Content |
|------|------|---------|
| 1 | [01-overview-and-simulation.md](./01-overview-and-simulation.md) | LLM simulation system, client interface, factory |
| 2 | [02-agent-config.md](./02-agent-config.md) | AGENT.md configuration chain implementation |
| 3 | [03-fingerprint.md](./03-fingerprint.md) | Dynamic project fingerprint generator |
| 4 | [04-context-templates.md](./04-context-templates.md) | Task-type context templates |
| 5 | [05-integration-testing.md](./05-integration-testing.md) | Executor integration, testing strategy |

## Quick Reference

### New Directories

```
src/agentforge/core/
├── context/           # Configuration, fingerprint, templates
│   └── templates/     # Task-type specific templates
└── llm/               # LLM client abstraction
```

### Environment Variables

| Variable | Purpose | Values |
|----------|---------|--------|
| `AGENTFORGE_LLM_MODE` | LLM client mode | `real`, `simulated`, `record`, `playback` |
| `AGENTFORGE_LLM_SCRIPT` | Simulation script path | File path |
| `AGENTFORGE_LLM_RECORDING` | Recording file path | File path |
| `ANTHROPIC_API_KEY` | API key (real mode) | `sk-ant-...` |

### Implementation Phases

1. **Foundation** (Week 1-2): agent_config.py, fingerprint.py
2. **LLM Abstraction** (Week 2-3): interface.py, simulated.py, factory.py
3. **Context Templates** (Week 3-4): base.py, fix_violation.py, etc.
4. **Integration** (Week 4-5): executor update, compaction, audit
5. **Validation** (Week 5): Real API testing, token comparison

## Related Documents

- [Assessment](../../docs/architecture/context_engineering_assessment.md) - Strategic analysis
- [Spec Index](../README.md) - Component specifications
- [Migration Plan](../08-migration.yaml) - Detailed timeline
