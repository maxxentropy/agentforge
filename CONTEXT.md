# AgentForge Context Document

**Purpose:** This document provides all context needed to resume work on AgentForge in a fresh conversation.

**Last Updated:** December 29, 2025  
**Current Status:** Foundation Complete, Ready for Phase 1

---

## Quick Orientation

AgentForge is a "Correctness-First" agentic coding system that:

1. **Transforms feature requests into verified specifications** (SPEC workflow - COMPLETE)
2. **Implements code via test-driven development** (TDFLOW workflow - PLANNED)
3. **Verifies correctness through deterministic checks** (Verification Engine - PLANNED)

### What's Built

```
SPEC WORKFLOW (6 states, fully operational):
  INTAKE → CLARIFY → ANALYZE → DRAFT → VALIDATE ←→ REVISE
  
  All states have:
  ✅ Prompt contracts (YAML, schema-validated)
  ✅ Output schemas (JSON Schema)
  ✅ CLI commands (execute.py)
  ✅ Both human and agent modes
```

### What's Next

```
1. Verification Engine - Run dotnet build/test, not just LLM judgment
2. Context Retrieval - LSP + Vector for actual code context
3. TDFLOW Workflow - Test-driven implementation
```

---

## Project Files Overview

### Core Entry Point
```
execute.py - Main CLI, run all workflows
run_contract.py - Contract runner library
```

### Contracts (7 total)
```
contracts/
├── spec.intake.v1.yaml        # Capture feature request
├── spec.clarify.v1.yaml       # Q&A to resolve ambiguity
├── spec.analyze.v1.yaml       # Analyze codebase (needs context retrieval)
├── spec.draft.v1.yaml         # Write specification (v2.0.0 - YAML output)
├── spec.validate.v1.yaml      # Review specification
├── spec.revise.v1.yaml        # Apply fixes to specification
└── spec.revise.decide.v1.yaml # Agent decision-making
```

### Schemas (11 total)
```
schemas/
├── prompt-contract.schema.yaml     # Meta-schema for contracts
├── intake_record.schema.yaml       # INTAKE output
├── clarification_log.schema.yaml   # CLARIFY output
├── analysis_report.schema.yaml     # ANALYZE output
├── specification.schema.yaml       # DRAFT output (comprehensive)
├── validation_report.schema.yaml   # VALIDATE output
├── revision_session.schema.yaml    # REVISE session state
├── execution.schema.yaml           # Execution config
├── architecture.schema.yaml        # Project rules
├── context_retrieval.schema.yaml   # Context retrieval config
└── assembled_prompt.schema.yaml    # Assembled prompt structure
```

### Documentation
```
docs/
├── ARCHITECTURE.md            # Complete system architecture
├── NEXT_STEPS.md              # Prioritized roadmap
├── CONTEXT.md                 # This document
├── SESSION_REPORT_2025-12-29.md  # Session report
└── design/
    ├── context_retrieval.md   # LSP + Vector design
    ├── executor_abstraction.md # Execution modes
    └── prompt_contracts.md    # Contract concept
```

### Workflow Definition
```
workflows/
└── spec_workflow.yaml         # SPEC workflow (6 states + terminals)
```

### Generated Outputs (gitignored)
```
outputs/
├── intake_record.yaml
├── clarification_log.yaml
├── analysis_report.yaml
├── specification.yaml
├── specification.yaml.bak     # Backup before revision
├── specification.md           # Rendered markdown
├── validation_report.yaml
└── revision_session.yaml      # Active revision session
```

---

## Key Design Decisions

### 1. All Outputs are YAML
- Machine-parseable
- Schema-validatable
- Human-readable with literal blocks (|)
- Markdown rendered on demand (render-spec command)

### 2. Two Execution Modes
```python
# Default: Claude Code CLI (uses subscription, $0)
python execute.py draft

# API mode (pay-per-token)
python execute.py draft --use-api
```

### 3. Revision System Modes
```bash
# Human decides each issue
python execute.py revise

# Agent decides, flags uncertain for human
python execute.py revise --auto

# Resume paused session
python execute.py revise --continue

# Apply all decisions
python execute.py revise --apply
```

### 4. Agent Handoff
Agent can flag decisions as `requires_human: true` with a `human_prompt` explaining why. Session pauses until human resolves.

---

## How the CLI Works

### Contract Execution Flow
```python
def execute_contract(contract_id, inputs, use_api=False):
    # 1. Load contract from contracts/{contract_id}.yaml
    runner = ContractRunner()
    contract = runner.load_contract(contract_id)
    
    # 2. Assemble prompt (substitute variables)
    prompt_data = runner.assemble_prompt(contract, inputs)
    
    # 3. Call LLM (Claude Code CLI or API)
    if use_api:
        response = call_anthropic_api(system, user)
    else:
        response = call_claude_code(system, user)
    
    # 4. Extract YAML from response
    yaml_content = extract_yaml_from_response(response)
    
    # 5. Parse and return
    return yaml.safe_load(yaml_content)
```

### Claude Code CLI Integration
```python
def call_claude_code(system, user):
    # Uses --output-format json for structured output
    # Uses --append-system-prompt to enforce YAML-only
    cmd = [
        'claude', '--output-format', 'json',
        '--append-system-prompt', yaml_enforcement_text,
        '-p', prompt_file
    ]
    result = subprocess.run(cmd, capture_output=True)
    # Parse JSON, extract 'result' field
    return json.loads(result.stdout)['result']
```

---

## Contract Structure

```yaml
contract:
  id: "spec.intake.v1"
  version: "1.0.0"
  workflow: spec
  state: intake

role:
  name: "Requirements Analyst"
  persona: "You are a requirements analyst..."
  goal: "Capture request without proposing solutions"
  anti_goals:
    - "Proposing implementations"

inputs:
  required:
    - name: raw_request
      type: string
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
          {role.persona}
  user:
    sections:
      - name: request
        content: |
          {raw_request}
      - name: conditional
        condition: "priority"  # Only included if priority provided
        content: |
          Priority: {priority}

verification:
  schema_validation: true
  checks:
    - id: C1
      type: regex_negative
      pattern: "\\b(class|service)\\b"
      target: detected_intent

execution:
  temperature: 0.0
  max_tokens: 2000
```

---

## Specification Schema (Key Structure)

The DRAFT stage produces specification.yaml with this structure:

```yaml
metadata:
  version: "1.0"
  status: draft
  feature_name: "Discount Codes"
  created_date: "2025-12-29"

overview:
  purpose: |
    Allow customers to apply discount codes...
  scope:
    includes:
      - "Apply percentage discounts"
    excludes:
      - "Loyalty programs"
  assumptions:
    - "One code per order"
  constraints:
    - "Discounts cannot exceed order total"

requirements:
  functional:
    - id: FR-001
      title: "Apply Discount Code"
      priority: must
      description: |
        The system SHALL allow...
      acceptance_criteria:
        - id: AC-001
          given: "A valid discount code exists"
          when: "User applies code to order"
          then: "Order total is reduced"

  non_functional:
    - id: NFR-001
      title: "Response Time"
      category: performance
      requirement: "< 200ms"

entities:
  - name: DiscountCode
    type: entity
    layer: Domain
    properties:
      - name: Code
        type: string
        constraints: ["Required", "Unique"]
    methods:
      - name: IsValid
        returns: bool
    invariants:
      - "Expiration date must be in future"

interfaces:
  - name: ApplyDiscountCode
    type: command
    path: "POST /api/orders/{id}/discount"
    layer: Application
    request:
      body: "{ code: string }"
    response:
      success: "200 OK with updated order"
      error_codes: ["INVALID_CODE", "EXPIRED_CODE"]

workflows:
  - name: "Apply Discount Flow"
    trigger: "User clicks Apply"
    steps:
      - step: 1
        actor: User
        action: "Enter code"
      - step: 2
        actor: System
        action: "Validate code"

error_handling:
  - error_code: INVALID_CODE
    condition: "Code not found"
    response: "400 Bad Request"
    user_message: "Invalid discount code"

testing_notes:
  unit_test_focus:
    - "DiscountCode.IsValid()"
  edge_cases:
    - "Expired at exact boundary"

glossary:
  - term: "Discount Code"
    definition: "A string..."
```

---

## Revision Session Structure

```yaml
session_id: "a1b2c3d4"
status: pending_human  # in_progress | pending_human | ready_to_apply | applied
mode: autonomous       # interactive | autonomous | paused_for_human

issues:
  - id: W1
    type: WARNING
    location: "Section 4.2"
    description: "No upper bound for FixedAmount"
    recommendation: "Add limit, e.g., <= 10000"
    options:
      - id: "1"
        label: "Set limit to $10,000"
        resolution: "Add constraint: <= 10000"
      - id: "skip"
        label: "Defer to implementation"
      - id: "custom"
        label: "Custom resolution..."
    decision:
      selected_option: "1"
      decided_by: agent
      rationale: "Standard e-commerce limit"
      confidence: high
      requires_human: false
      timestamp: "2025-12-29T01:35:00Z"

summary:
  total_issues: 4
  resolved: 3
  pending_human: 1
```

---

## Immediate Next Task

### Phase 1: Verification Engine

**Goal:** Replace LLM-based validation with actual verification

**First Steps:**

1. Create `schemas/correctness.schema.yaml`
   ```yaml
   checks:
     - id: compile_check
       type: command
       command: "dotnet build {project_path}"
       blocking: true
   ```

2. Create `tools/verification_runner.py`
   ```python
   class VerificationRunner:
       def run_check(self, check, context) -> CheckResult
       def generate_report(self, results) -> VerificationReport
   ```

3. Integrate with `run_validate` in execute.py

**See:** docs/NEXT_STEPS.md for full details

---

## Common Commands

```bash
# Full SPEC workflow
python execute.py intake --request "Add discount codes to orders"
python execute.py clarify --answer "One code per order, percentage or fixed"
python execute.py analyze
python execute.py draft
python execute.py validate

# Revision loop
python execute.py revise              # Interactive
python execute.py revise --auto       # Autonomous
python execute.py revise --continue   # Resume
python execute.py revise --apply      # Apply changes
python execute.py validate            # Re-check

# Utilities
python execute.py render-spec         # YAML → Markdown
python execute.py revise --status     # Show session
```

---

## Development Tips

### Testing a Contract Change
```bash
# Validate contract structure
python tools/contract_validator.py contracts/spec.draft.v1.yaml

# Validate output against schema
python tools/validate_schema.py schemas/specification.schema.yaml outputs/specification.yaml
```

### Debugging Output Parsing
```python
# In execute.py, extract_yaml_from_response handles:
# - YAML in ```yaml blocks
# - YAML in generic ``` blocks
# - Raw YAML starting with key:
```

### Adding a New Contract
1. Create `contracts/spec.{state}.v1.yaml`
2. Create output schema in `schemas/`
3. Create prompt template in `prompts/spec/`
4. Add `run_{state}` function in `execute.py`
5. Add subparser in `main()`

---

## Key Files to Read First

1. **docs/ARCHITECTURE.md** - Complete system architecture
2. **docs/NEXT_STEPS.md** - Prioritized roadmap
3. **execute.py** - Main CLI, see how everything connects
4. **contracts/spec.draft.v1.yaml** - Most complex contract (v2.0.0)
5. **schemas/specification.schema.yaml** - Most detailed schema

---

## Questions to Ask When Resuming

1. "What was I working on?" → Check NEXT_STEPS.md
2. "What's already done?" → Check this document's "What's Built" section
3. "How does X work?" → Check ARCHITECTURE.md
4. "What happened last session?" → Check SESSION_REPORT_*.md files
5. "What are the priorities?" → Check NEXT_STEPS.md Phase 1-5

---

## Contact Points

### Repository
This is a local development project. All files in `agentforge-prd/`.

### User Preferences
- .NET development focus
- Clean Architecture patterns
- TDD methodology
- YAML over JSON for configs
- Correctness before speed

---

*This document should be updated when major changes occur.*
