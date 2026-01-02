# Pipeline Controller - Complete Specification Index

**Version:** 1.0  
**Date:** January 2, 2026  
**Total Estimated Effort:** 6-10 weeks

---

## Executive Summary

The Pipeline Controller transforms AgentForge from a collection of tools into an **autonomous development system**. It orchestrates the full request→delivery lifecycle through 8 pipeline stages, with human intervention only on escalation.

```
User: "agentforge start 'Add OAuth2 authentication'"
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────┐
    │              AUTONOMOUS PIPELINE                         │
    │                                                          │
    │  INTAKE → CLARIFY → ANALYZE → SPEC → RED → GREEN →      │
    │                                          REFACTOR → DELIVER
    │                                                          │
    └─────────────────────────────────────────────────────────┘
                              │
                              ▼
              Verified, Tested, Delivered Code
```

---

## Specification Documents

| Stage | Document | Description | Est. Effort |
|-------|----------|-------------|-------------|
| 1 | [stage-01-core-architecture.md](stage-01-core-architecture.md) | PipelineController, state management, escalation | 5-7 days |
| 2 | [stage-02-stage-executor-interface.md](stage-02-stage-executor-interface.md) | StageExecutor base class, artifact contracts | 3-4 days |
| 3 | [stage-03-intake-clarify-stages.md](stage-03-intake-clarify-stages.md) | INTAKE and CLARIFY stage implementations | 4-5 days |
| 4 | [stage-04-analyze-spec-stages.md](stage-04-analyze-spec-stages.md) | ANALYZE and SPEC stage implementations | 5-6 days |
| 5 | [stage-05-red-phase.md](stage-05-red-phase.md) | RED phase (TDD test generation) | 5-6 days |
| 6 | [stage-06-green-phase.md](stage-06-green-phase.md) | GREEN phase (implementation) | 6-7 days |
| 7 | [stage-07-refactor-deliver-stages.md](stage-07-refactor-deliver-stages.md) | REFACTOR and DELIVER stages | 4-5 days |
| 8 | [stage-08-cli-commands.md](stage-08-cli-commands.md) | CLI commands (start, design, status, etc.) | 3-4 days |
| 9 | [stage-09-configuration-system.md](stage-09-configuration-system.md) | Configuration and pipeline templates | 3-4 days |

**Total: 38-48 days (6-10 weeks)**

---

## Implementation Order

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Basic pipeline execution with 2-3 stages

1. **Stage 1**: Core Architecture
   - PipelineController
   - PipelineState & StateStore
   - EscalationHandler
   - StageExecutorRegistry

2. **Stage 2**: Executor Interface
   - StageExecutor base class
   - LLMStageExecutor
   - Artifact contracts

### Phase 2: Design Pipeline (Weeks 3-4)
**Goal:** `agentforge design` works end-to-end

3. **Stage 3**: Intake & Clarify
   - IntakeExecutor
   - ClarifyExecutor

4. **Stage 4**: Analyze & Spec
   - AnalyzeExecutor (with tool use)
   - SpecExecutor

5. **Stage 8** (partial): Design CLI
   - `agentforge design` command
   - `agentforge status` command

### Phase 3: TDD Stages (Weeks 5-6)
**Goal:** `agentforge implement` works with TDD

6. **Stage 5**: RED Phase
   - Test generation
   - pytest integration

7. **Stage 6**: GREEN Phase
   - Implementation loop
   - Test verification

### Phase 4: Polish & Delivery (Weeks 7-8)
**Goal:** Full autonomous pipeline

8. **Stage 7**: Refactor & Deliver
   - Conformance integration
   - Git operations

9. **Stage 8** (complete): Full CLI
   - All commands
   - Progress display

10. **Stage 9**: Configuration
    - Pipeline templates
    - Stage configuration

---

## Key Interfaces

### PipelineController

```python
controller = PipelineController(project_path)

# Start new pipeline
result = controller.execute(
    user_request="Add OAuth2 authentication",
    pipeline_type="implement"
)

# Resume paused pipeline
result = controller.execute(
    resume_pipeline_id="PL-20260102-abc123"
)

# Control operations
controller.approve(pipeline_id)
controller.abort(pipeline_id, reason)
controller.provide_feedback(pipeline_id, feedback)
```

### StageExecutor

```python
class MyStageExecutor(LLMStageExecutor):
    stage_name = "mystage"
    
    def get_system_prompt(self, context):
        return "Your system prompt"
    
    def get_user_message(self, context):
        return "Your task"
    
    def parse_response(self, llm_result, context):
        return {"artifact": "data"}
```

### CLI Commands

```bash
# Primary
agentforge start "request"              # Full pipeline
agentforge design "request"             # Exits at SPEC
agentforge implement --from-spec SPEC   # From existing spec

# Control
agentforge status [pipeline_id]
agentforge approve <pipeline_id>
agentforge abort <pipeline_id>

# List
agentforge pipelines --status running
```

---

## Directory Structure (Final)

```
src/agentforge/core/pipeline/
├── __init__.py
├── controller.py           # PipelineController
├── state.py                # PipelineState
├── state_store.py          # PipelineStateStore
├── registry.py             # StageExecutorRegistry
├── escalation.py           # EscalationHandler
├── validator.py            # ArtifactValidator
├── stage_executor.py       # StageExecutor base
├── llm_stage_executor.py   # LLMStageExecutor
├── contract_stage_executor.py
├── artifacts.py            # Artifact dataclasses
├── config.py               # ConfigurationLoader
├── templates.py            # PipelineTemplateLoader
└── stages/
    ├── __init__.py
    ├── intake.py
    ├── clarify.py
    ├── analyze.py
    ├── spec.py
    ├── red.py
    ├── green.py
    ├── refactor.py
    └── deliver.py

cli/click_commands/
├── pipeline.py             # start, design, implement, etc.
└── config.py               # config init, show, validate

.agentforge/
├── config/
│   ├── settings.yaml
│   └── stages/
├── pipelines/
│   ├── design.yaml
│   ├── implement.yaml
│   └── fix.yaml
├── pipeline/
│   ├── active/             # Running pipelines
│   ├── completed/          # Finished pipelines
│   └── index.yaml
├── artifacts/
│   └── {pipeline_id}/
│       ├── 01-intake.yaml
│       ├── 02-clarify.yaml
│       └── ...
└── escalations/
```

---

## Dependencies

### Existing Components Used
- MinimalContextExecutor
- Tool Handlers (P0)
- LLM Abstraction
- Contracts System
- Conformance Checker

### External Dependencies
- pytest (test execution)
- git (delivery)
- GitHub CLI (PR creation, optional)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Pipeline completion rate | > 80% |
| Average pipeline duration | < 30 min |
| Test generation accuracy | > 90% |
| Tests passing after GREEN | 100% |
| Conformance after REFACTOR | > 95% |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM produces invalid code | Iterative test loop, max retries |
| Tests don't catch bugs | Spec-driven test generation, edge cases |
| Pipeline takes too long | Stage timeouts, cost limits |
| Escalation overwhelms users | Smart escalation (only blocking issues) |

---

## Next Steps After Implementation

1. **Real LLM Testing**: Validate with Claude API against real violations
2. **Dashboard**: Web UI for monitoring pipelines
3. **Multi-repo Support**: Pipelines across repositories
4. **Team Features**: Shared escalation queues, notifications
5. **Analytics**: Pipeline metrics, cost tracking

---

*This specification provides a complete blueprint for implementing the Pipeline Controller system.*
