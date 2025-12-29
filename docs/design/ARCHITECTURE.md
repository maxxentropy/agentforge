# AgentForge Architecture Document

**Version:** 1.0  
**Last Updated:** December 29, 2025  
**Status:** Foundation Complete, Core Workflows Operational

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Philosophy](#2-core-philosophy)
3. [Architecture Layers](#3-architecture-layers)
4. [SPEC Workflow](#4-spec-workflow)
5. [Prompt Contract System](#5-prompt-contract-system)
6. [Execution System](#6-execution-system)
7. [Revision System](#7-revision-system)
8. [Schema System](#8-schema-system)
9. [Planned Components](#9-planned-components)
10. [Data Flow](#10-data-flow)
11. [File Structure](#11-file-structure)

---

## 1. System Overview

AgentForge is a "Correctness-First" agentic coding system. It transforms raw feature requests into verified specifications through a structured workflow, then (in future phases) implements code via Test-Driven Development.

### Current State

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENTFORGE SYSTEM                                │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    SPEC WORKFLOW (Operational)                    │   │
│  │                                                                   │   │
│  │   INTAKE → CLARIFY → ANALYZE → DRAFT → VALIDATE ←→ REVISE       │   │
│  │                                                                   │   │
│  │   Output: Verified specification.yaml                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   TDFLOW WORKFLOW (Planned)                       │   │
│  │                                                                   │   │
│  │   RED (Write Test) → GREEN (Implement) → REFACTOR                │   │
│  │                                                                   │   │
│  │   Input: specification.yaml                                       │   │
│  │   Output: Verified implementation                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   SUPPORTING SYSTEMS                              │   │
│  │                                                                   │   │
│  │   • Prompt Contracts (Operational)                                │   │
│  │   • Schema Validation (Operational)                               │   │
│  │   • Execution Engine (Operational - CLI + API)                    │   │
│  │   • Revision System (Operational - Interactive + Autonomous)      │   │
│  │   • Context Retrieval (Designed, Not Implemented)                 │   │
│  │   • Verification Engine (Designed, Not Implemented)               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### What Works Today

| Component | Status | Description |
|-----------|--------|-------------|
| SPEC Workflow | ✅ Operational | 6-state workflow with feedback loop |
| Prompt Contracts | ✅ Operational | 7 contracts with schema validation |
| CLI Executor | ✅ Operational | Claude Code CLI + Anthropic API |
| Revision System | ✅ Operational | Interactive + autonomous modes |
| Schema System | ✅ Operational | 11 schemas for all artifacts |
| YAML Output | ✅ Operational | All outputs are structured YAML |

### What's Designed But Not Built

| Component | Status | Description |
|-----------|--------|-------------|
| Context Retrieval | 📐 Designed | LSP + Vector hybrid for code context |
| Verification Engine | 📐 Designed | Run compiler, tests, static analysis |
| TDFLOW Workflow | 📐 Designed | Test-driven implementation workflow |
| Parallel Execution | 📐 Designed | Multi-agent swarm for batch work |

---

## 2. Core Philosophy

### "Correctness is Upstream"

The system enforces quality at the earliest possible stage:

```
                    Cost to Fix
                         │
                    10x  │                              ●
                         │                          ●
                         │                      ●
                     1x  │  ●───●───●
                         │
                         └──────────────────────────────────
                            Spec  Design  Code  Test  Prod
                            
        AgentForge Focus: ▲▲▲▲▲▲▲▲▲▲▲
```

**Key Principles:**

1. **Specification Before Implementation** - Detailed specs prevent misunderstandings
2. **Verification at Every Stage** - Every output is schema-validated
3. **Human-in-the-Loop Where It Matters** - Agent handles routine, human handles judgment
4. **Structured Handoffs** - All state is serializable YAML
5. **Auditability** - Full trace of decisions and rationale

---

## 3. Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                           │
│                                                                          │
│   execute.py CLI                                                         │
│   • intake, clarify, analyze, draft, validate, revise, render-spec      │
│   • --use-api flag for API mode                                          │
│   • --auto flag for autonomous revision                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           WORKFLOW LAYER                                 │
│                                                                          │
│   workflows/spec_workflow.yaml                                           │
│   • State definitions                                                    │
│   • Transition rules                                                     │
│   • Verification requirements                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CONTRACT LAYER                                  │
│                                                                          │
│   contracts/*.yaml                                                       │
│   • Prompt structure (system + user sections)                            │
│   • Input/output definitions                                             │
│   • Verification rules                                                   │
│   • Examples as test cases                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION LAYER                                  │
│                                                                          │
│   run_contract.py                                                        │
│   • ContractRunner class                                                 │
│   • Prompt assembly                                                      │
│   • Variable substitution                                                │
│                                                                          │
│   execute.py (execution functions)                                       │
│   • call_claude_code() - CLI execution                                   │
│   • call_anthropic_api() - API execution                                 │
│   • extract_yaml_from_response() - Output parsing                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         VALIDATION LAYER                                 │
│                                                                          │
│   schemas/*.yaml                                                         │
│   • JSON Schema definitions                                              │
│   • Output structure enforcement                                         │
│                                                                          │
│   tools/validate_schema.py                                               │
│   • Runtime schema validation                                            │
│   • Error reporting                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                                │
│                                                                          │
│   outputs/*.yaml                                                         │
│   • intake_record.yaml                                                   │
│   • clarification_log.yaml                                               │
│   • analysis_report.yaml                                                 │
│   • specification.yaml                                                   │
│   • validation_report.yaml                                               │
│   • revision_session.yaml                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. SPEC Workflow

The SPEC workflow transforms a raw feature request into a verified specification.

### State Machine

```
                                    ┌─────────┐
                                    │ INTAKE  │
                                    └────┬────┘
                                         │
                                         ▼
                                    ┌─────────┐
                              ┌─────│ CLARIFY │◄────┐
                              │     └────┬────┘     │
                              │          │          │
                              │          ▼          │
                              │     ┌─────────┐     │
                              └────►│ ANALYZE │─────┘
                                    └────┬────┘
                                         │
                                         ▼
                                    ┌─────────┐
                              ┌─────│  DRAFT  │◄────┐
                              │     └────┬────┘     │
                              │          │          │
                              │          ▼          │
                              │     ┌──────────┐    │
                              │     │ VALIDATE │────┘
                              │     └────┬─────┘
                              │          │
                              │    [if issues]
                              │          │
                              │          ▼
                              │     ┌─────────┐
                              └─────│ REVISE  │
                                    └────┬────┘
                                         │
                                         ▼
                                    ┌──────────┐
                                    │ VALIDATE │
                                    └────┬─────┘
                                         │
                              [repeat until approved]
                                         │
                                         ▼
                                    ┌──────────┐
                                    │ APPROVED │
                                    └──────────┘
```

### State Details

| State | Role | Input | Output | Purpose |
|-------|------|-------|--------|---------|
| INTAKE | Requirements Analyst | Raw request | intake_record.yaml | Capture intent without solving |
| CLARIFY | Requirements Analyst | intake_record | clarification_log.yaml | Resolve ambiguities via Q&A |
| ANALYZE | Architect | intake + clarification | analysis_report.yaml | Examine codebase, find patterns |
| DRAFT | Specification Writer | All prior outputs | specification.yaml | Write complete spec |
| VALIDATE | Reviewer | specification + analysis | validation_report.yaml | Comprehensive quality review |
| REVISE | Reviser | specification + validation | specification.yaml (updated) | Address issues |

### Contracts

Each state has a corresponding contract:

| Contract | File | Version |
|----------|------|---------|
| INTAKE | contracts/spec.intake.v1.yaml | 1.0.0 |
| CLARIFY | contracts/spec.clarify.v1.yaml | 1.0.0 |
| ANALYZE | contracts/spec.analyze.v1.yaml | 1.0.0 |
| DRAFT | contracts/spec.draft.v1.yaml | 2.0.0 |
| VALIDATE | contracts/spec.validate.v1.yaml | 1.0.0 |
| REVISE | contracts/spec.revise.v1.yaml | 1.0.0 |
| REVISE.DECIDE | contracts/spec.revise.decide.v1.yaml | 1.0.0 |

---

## 5. Prompt Contract System

Prompt contracts are machine-verifiable definitions that replace loose markdown prompts.

### Contract Structure

```yaml
contract:
  id: "spec.intake.v1"
  version: "1.0.0"
  workflow: spec
  state: intake

role:
  name: "Requirements Analyst"
  persona: "..."
  goal: "Capture request without proposing solutions"
  anti_goals:
    - "Proposing implementations"

inputs:
  required:
    - name: raw_request
      type: string
      validation:
        min_length: 5
  optional:
    - name: priority
      type: enum
      values: [critical, high, medium, low]

output:
  format: yaml
  schema: intake_record.schema.yaml

template:
  system:
    sections:
      - name: role
        content: |
          # Role
          ...
  user:
    sections:
      - name: request
        content: |
          # Request
          {raw_request}
      - name: conditional_section
        condition: "priority"
        content: |
          Priority: {priority}

verification:
  schema_validation: true
  checks:
    - id: "C1"
      type: regex_negative
      pattern: "\\b(class|service)\\b"
      target: "detected_intent"
      message: "Intent should not include implementation details"

examples:
  valid:
    - name: "Standard request"
      inputs:
        raw_request: "Add discount codes"
      output:
        detected_intent: "Allow customers to apply discount codes"
        detected_scope: medium

execution:
  temperature: 0.0
  max_tokens: 2000
```

### Benefits

| Before (Markdown) | After (YAML Contracts) |
|-------------------|------------------------|
| Human-readable only | Machine-parseable |
| No validation | Schema-validated |
| Examples are illustrative | Examples are test cases |
| Verification in prose | Verification is executable |
| Variables implicit | Variables typed & documented |

---

## 6. Execution System

The execution system runs contracts through LLM and validates outputs.

### Execution Modes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXECUTION MODES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   MODE 1: Claude Code CLI (Default)                                      │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  execute.py ──► claude --output-format json ──► Response         │  │
│   │                                                                   │  │
│   │  • Uses Claude subscription ($0 marginal cost)                   │  │
│   │  • Requires Claude Code CLI installed                            │  │
│   │  • Good for development and interactive use                      │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   MODE 2: Anthropic API (--use-api)                                      │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  execute.py ──► anthropic.Anthropic() ──► Response               │  │
│   │                                                                   │  │
│   │  • Requires ANTHROPIC_API_KEY                                    │  │
│   │  • Pay-per-token                                                 │  │
│   │  • Good for automation and CI/CD                                 │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   MODE 3: Parallel Swarm (Planned)                                       │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  orchestrator ──► [Agent 1] ──►                                  │  │
│   │               ──► [Agent 2] ──► Merged Result                    │  │
│   │               ──► [Agent 3] ──►                                  │  │
│   │                                                                   │  │
│   │  • Multiple concurrent API calls                                 │  │
│   │  • For batch processing                                          │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Execution Flow

```python
def execute_contract(contract_id, inputs, use_api=False):
    # 1. Load contract
    runner = ContractRunner()
    contract = runner.load_contract(contract_id)
    
    # 2. Assemble prompt
    prompt_data = runner.assemble_prompt(contract, inputs)
    system = prompt_data['prompt']['system']
    user = prompt_data['prompt']['user']
    
    # 3. Execute
    if use_api:
        response = call_anthropic_api(system, user)
    else:
        response = call_claude_code(system, user)
    
    # 4. Extract YAML from response
    yaml_content = extract_yaml_from_response(response)
    
    # 5. Parse and return
    return yaml.safe_load(yaml_content)
```

---

## 7. Revision System

The revision system addresses validation issues with human-agent collaboration.

### Modes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        REVISION MODES                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   INTERACTIVE MODE (default)                                             │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  For each issue:                                                 │  │
│   │    1. Display problem + recommendation                           │  │
│   │    2. Show options (parsed from recommendation)                  │  │
│   │    3. Human selects option or provides custom                    │  │
│   │    4. Record decision with rationale                             │  │
│   │    5. Save session (can quit and resume)                         │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   AUTONOMOUS MODE (--auto)                                               │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  For each issue:                                                 │  │
│   │    1. Agent evaluates issue + options                            │  │
│   │    2. If confident → Select option, document rationale           │  │
│   │    3. If uncertain → Flag for human (requires_human: true)       │  │
│   │    4. Continue until all evaluated                               │  │
│   │    5. If any flagged → Pause for human input                     │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   CONTINUE MODE (--continue)                                             │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  1. Load existing session                                        │  │
│   │  2. Find issues pending human decision                           │  │
│   │  3. Present each to human                                        │  │
│   │  4. Record decisions                                             │  │
│   │  5. When complete → Ready to apply                               │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Session Structure

```yaml
# outputs/revision_session.yaml
session_id: "a1b2c3d4"
created_at: "2025-12-29T01:30:00Z"
updated_at: "2025-12-29T01:45:00Z"
spec_file: "outputs/specification.yaml"
spec_version: "1.0"
validation_file: "outputs/validation_report.yaml"
validation_verdict: "approved_with_notes"
mode: "autonomous"
status: "pending_human"  # in_progress | pending_human | ready_to_apply | applied

issues:
  - id: "W1"
    type: "WARNING"
    location: "Section 4.2 Validation Rules"
    description: |
      No upper bound specified for FixedAmount discount Value.
    recommendation: |
      Add reasonable upper bound, e.g., <= 10000
    options:
      - id: "1"
        label: "Set limit/bound to $10,000"
        resolution: "Add constraint: <= 10000"
        confidence: null
      - id: "skip"
        label: "Skip - defer to implementation"
        resolution: "Deferred to implementation"
      - id: "custom"
        label: "Custom resolution..."
        resolution: null
    decision:
      selected_option: "1"
      decided_by: "agent"
      rationale: "Standard e-commerce upper bound"
      confidence: "high"
      requires_human: false
      timestamp: "2025-12-29T01:35:00Z"

summary:
  total_issues: 4
  resolved: 3
  deferred: 0
  pending_human: 1
```

### Agent Decision Framework

| Decide Autonomously | Flag for Human |
|---------------------|----------------|
| Clear technical fixes | Architectural decisions |
| Obvious best option | Business logic ambiguity |
| Standard validation issues | Trade-offs with no clear winner |
| Unambiguous recommendations | Domain expertise required |

---

## 8. Schema System

All outputs are validated against JSON Schema definitions.

### Output Schemas

| Schema | Purpose | Key Fields |
|--------|---------|------------|
| intake_record.schema.yaml | INTAKE output | detected_intent, detected_scope, initial_questions |
| clarification_log.schema.yaml | CLARIFY output | exchanges[], resolved_questions[], scope |
| analysis_report.schema.yaml | ANALYZE output | existing_components[], patterns[], risks[] |
| specification.schema.yaml | DRAFT output | metadata, overview, requirements, entities, interfaces |
| validation_report.schema.yaml | VALIDATE output | overall_verdict, blocking_issues[], warnings[] |
| revision_session.schema.yaml | REVISE session | issues[], decisions[], summary |

### Meta Schemas

| Schema | Purpose |
|--------|---------|
| prompt-contract.schema.yaml | Validates contract structure |
| execution.schema.yaml | Execution configuration |
| architecture.schema.yaml | Project architecture rules |
| context_retrieval.schema.yaml | Code retrieval configuration |

### Validation Flow

```
LLM Output ──► extract_yaml_from_response() ──► yaml.safe_load() 
                                                      │
                                                      ▼
                                              Schema Validation
                                                      │
                                    ┌─────────────────┴─────────────────┐
                                    ▼                                   ▼
                                 VALID                              INVALID
                                    │                                   │
                                    ▼                                   ▼
                              Save to outputs/                    Error + Retry
```

---

## 9. Planned Components

### Context Retrieval System (Designed)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT RETRIEVAL (PLANNED)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   HYBRID RETRIEVAL: LSP + Vector                                         │
│                                                                          │
│   ┌───────────────────────────────┐ ┌───────────────────────────────┐   │
│   │     STRUCTURAL (LSP)          │ │      SEMANTIC (Vector)        │   │
│   │                               │ │                               │   │
│   │ • Symbol definitions          │ │ • Conceptual similarity       │   │
│   │ • Reference tracking          │ │ • Natural language queries    │   │
│   │ • Type hierarchies            │ │ • Documentation matching      │   │
│   │ • Dependency graphs           │ │ • Pattern detection           │   │
│   │                               │ │                               │   │
│   │ Source: csharp-lsp, pyright   │ │ Source: Embeddings + FAISS    │   │
│   └───────────────────────────────┘ └───────────────────────────────┘   │
│                    │                              │                      │
│                    └──────────────┬───────────────┘                      │
│                                   ▼                                      │
│                         ┌─────────────────┐                              │
│                         │ Context Merger  │                              │
│                         │                 │                              │
│                         │ Budget: 8000    │                              │
│                         │ tokens max      │                              │
│                         └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘

Design Document: docs/design/context_retrieval.md
Configuration: config/context_retrieval.yaml
Schema: schemas/context_retrieval.schema.yaml
```

### Verification Engine (Designed)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VERIFICATION ENGINE (PLANNED)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   THE JUDGE: Non-LLM verification layer                                  │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  COMPILE CHECK                                                   │   │
│   │  command: "dotnet build {project_path}"                         │   │
│   │  blocking: true                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  TEST CHECK                                                      │   │
│   │  command: "dotnet test {project_path}"                          │   │
│   │  blocking: true                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  REGEX CHECK                                                     │   │
│   │  pattern: "public [a-zA-Z0-9_<>]+ [a-zA-Z0-9_]+;"               │   │
│   │  negative_match: true                                            │   │
│   │  message: "Use properties instead of public fields"             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  ARCHITECTURE CHECK                                              │   │
│   │  rule: "Domain cannot reference Infrastructure"                 │   │
│   │  method: AST analysis or import scanning                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   Config: correctness.yaml (to be created)                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### TDFLOW Workflow (Designed)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TDFLOW WORKFLOW (PLANNED)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Test-Driven Agentic Workflow                                           │
│                                                                          │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌──────────┐          │
│   │   RED   │────►│ VERIFY  │────►│  GREEN  │────►│  VERIFY  │          │
│   │         │     │  FAIL   │     │         │     │   PASS   │          │
│   └─────────┘     └────┬────┘     └─────────┘     └────┬─────┘          │
│       │                │                                │                │
│       │           [must fail]                      [must pass]           │
│       │                │                                │                │
│       │                ▼                                ▼                │
│       │         ┌───────────┐                    ┌──────────┐           │
│       └─────────│   RETRY   │                    │ REFACTOR │           │
│                 └───────────┘                    └────┬─────┘           │
│                                                       │                  │
│                                                       ▼                  │
│                                                 ┌──────────┐            │
│                                                 │   DONE   │            │
│                                                 └──────────┘            │
│                                                                          │
│   Input: specification.yaml (from SPEC workflow)                         │
│   Output: Verified implementation with passing tests                     │
│                                                                          │
│   Reference: Research document on TDFlow methodology                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Data Flow

### Complete Workflow Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   USER INPUT                                                             │
│   "Add discount codes to orders"                                         │
│        │                                                                 │
│        ▼                                                                 │
│   ┌─────────┐                                                           │
│   │ INTAKE  │──────────────► intake_record.yaml                         │
│   └────┬────┘                • detected_intent                          │
│        │                      • detected_scope                           │
│        ▼                      • initial_questions                        │
│   ┌─────────┐                                                           │
│   │ CLARIFY │──────────────► clarification_log.yaml                     │
│   └────┬────┘                • exchanges[]                               │
│        │                      • resolved_questions[]                     │
│        ▼                      • scope.in_scope[]                         │
│   ┌─────────┐                                                           │
│   │ ANALYZE │──────────────► analysis_report.yaml                       │
│   └────┬────┘                • existing_components[]                     │
│        │                      • patterns_discovered[]                    │
│        ▼                      • risks[]                                  │
│   ┌─────────┐                                                           │
│   │  DRAFT  │──────────────► specification.yaml                         │
│   └────┬────┘                • metadata                                  │
│        │                      • requirements.functional[]                │
│        ▼                      • entities[]                               │
│   ┌──────────┐               • interfaces[]                              │
│   │ VALIDATE │─────────────► validation_report.yaml                     │
│   └────┬─────┘               • overall_verdict                           │
│        │                      • blocking_issues[]                        │
│        │                      • warnings[]                               │
│   [if issues]                                                            │
│        │                                                                 │
│        ▼                                                                 │
│   ┌─────────┐                                                           │
│   │ REVISE  │──────────────► revision_session.yaml                      │
│   └────┬────┘                • issues[]                                  │
│        │                      • decisions[]                              │
│        │                      • status                                   │
│        │                                                                 │
│        └─────────► specification.yaml (updated)                         │
│                                                                          │
│   FINAL OUTPUT                                                           │
│   specification.yaml (approved) + specification.md (rendered)            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. File Structure

```
agentforge-prd/
├── README.md                              # Project overview
├── QUICKSTART.md                          # Getting started guide
├── PRD_v2.md                              # Product Requirements Document
├── execute.py                             # Main CLI (recommended entry point)
├── run_contract.py                        # Contract runner library
│
├── contracts/                             # Prompt contracts (machine-verifiable)
│   ├── README.md                          # Contract documentation
│   ├── spec.intake.v1.yaml                # INTAKE contract
│   ├── spec.clarify.v1.yaml               # CLARIFY contract
│   ├── spec.analyze.v1.yaml               # ANALYZE contract
│   ├── spec.draft.v1.yaml                 # DRAFT contract (v2.0.0 - YAML output)
│   ├── spec.validate.v1.yaml              # VALIDATE contract
│   ├── spec.revise.v1.yaml                # REVISE contract
│   └── spec.revise.decide.v1.yaml         # Agent decision contract
│
├── schemas/                               # JSON Schema definitions
│   ├── README.md                          # Schema documentation
│   ├── prompt-contract.schema.yaml        # Meta-schema for contracts
│   ├── intake_record.schema.yaml          # INTAKE output schema
│   ├── clarification_log.schema.yaml      # CLARIFY output schema
│   ├── analysis_report.schema.yaml        # ANALYZE output schema
│   ├── specification.schema.yaml          # DRAFT output schema
│   ├── validation_report.schema.yaml      # VALIDATE output schema
│   ├── revision_session.schema.yaml       # REVISE session schema
│   ├── execution.schema.yaml              # Execution config schema
│   ├── architecture.schema.yaml           # Architecture config schema
│   ├── context_retrieval.schema.yaml      # Context retrieval config schema
│   └── assembled_prompt.schema.yaml       # Assembled prompt schema
│
├── prompts/                               # Human-readable prompt templates
│   └── spec/
│       ├── intake.md
│       ├── clarify.md
│       ├── analyze.md
│       ├── draft.md
│       ├── validate.md
│       └── revise.md
│
├── workflows/                             # Workflow definitions
│   └── spec_workflow.yaml                 # SPEC workflow (6 states)
│
├── config/                                # Configuration files
│   ├── README.md                          # Config documentation
│   ├── execution.yaml                     # Execution mode settings
│   ├── architecture.yaml                  # Project architecture rules
│   └── context_retrieval.yaml             # Context retrieval settings
│
├── tools/                                 # Utility tools
│   ├── contract_validator.py              # Validate contracts
│   └── validate_schema.py                 # Validate YAML against schema
│
├── docs/                                  # Documentation
│   ├── ARCHITECTURE.md                    # This document
│   ├── NEXT_STEPS.md                      # Roadmap and priorities
│   ├── CONTEXT.md                         # Resume context document
│   ├── SESSION_REPORT_2025-12-29.md       # Session report
│   └── design/
│       ├── README.md
│       ├── context_retrieval.md           # LSP + Vector design
│       ├── executor_abstraction.md        # Execution modes design
│       └── prompt_contracts.md            # Contract concept design
│
├── sample_data/                           # Sample/test data
│   └── project_context.yaml               # Sample project config
│
├── setup/                                 # Setup utilities
│   ├── install.sh                         # Installation script
│   └── yaml-only.md                       # YAML output enforcement
│
└── outputs/                               # Generated files (gitignored)
    ├── intake_record.yaml
    ├── clarification_log.yaml
    ├── analysis_report.yaml
    ├── specification.yaml
    ├── specification.yaml.bak             # Backup before revision
    ├── specification.md                   # Rendered spec
    ├── validation_report.yaml
    └── revision_session.yaml
```

---

## Appendix: Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Output Format | YAML (not Markdown) | Machine-parseable, schema-validatable |
| Execution Default | Claude Code CLI | $0 cost, uses subscription |
| Revision State | Session file | Persistent, resumable, auditable |
| Agent Handoff | Explicit flags | Agent knows its limits |
| Specification First | Before TDFLOW | Correctness is upstream |
| LSP for Context | Not custom parsers | Compiler-accurate, zero maintenance |

---

*Document Version: 1.0*  
*Last Updated: December 29, 2025*
