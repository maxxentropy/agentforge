# Minimal Context Architecture Specification

## Overview

This specification defines how AgentForge manages context for LLM-powered agents. The core principle is **stateless steps with verified state**—each step receives only the context it needs, built from persisted verified state rather than accumulated conversation history.

## Problem Statement

Naive conversation accumulation causes:
- **Unbounded growth**: Each step adds to context, eventually hitting limits
- **Rate limit failures**: 48K+ tokens per request exceeds API limits
- **Cost explosion**: Later steps cost 10x+ more than early steps
- **Multi-day impossibility**: Can't maintain conversation across sessions

## Solution: Stateless Step Execution

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   EVERY STEP IS A FRESH CONVERSATION                                    │
│                                                                          │
│   LLM receives exactly 2 messages:                                      │
│   1. System prompt (phase-appropriate)                                  │
│   2. Current context (built from verified state)                        │
│                                                                          │
│   Context size: 4-8K tokens ALWAYS, regardless of step number           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Architecture

### State Store

All state persists to disk. The agent has no memory except what's in the state store.

```
.agentforge/tasks/{task_id}/
├── task.yaml                 # Immutable: goal, success criteria
├── state.yaml                # Mutable: current phase, status, verification
├── actions.yaml              # Append-only: complete log of all actions
├── working_memory.yaml       # Rolling: last N actions for context
└── artifacts/
    ├── inputs/               # Verified inputs (spec, violation, etc.)
    ├── outputs/              # Verified outputs from each phase
    └── snapshots/            # File states before/after changes
```

### Context Schema

Every step receives context in this fixed structure:

```yaml
# Target: 4-8K tokens total

task_frame:                    # ~500 tokens, constant
  id: "{task_id}"
  goal: "Single sentence description"
  success_criteria:
    - "Measurable criterion 1"
    - "Measurable criterion 2"
  phase: "current_phase"
  constraints:
    - "Constraint 1"
    - "Constraint 2"

current_state:                 # ~3-5K tokens, bounded
  # Task-type specific content
  # See Context Schemas section

recent_actions:                # ~500-1K tokens, last 3 only
  - step: 7
    action: "edit_file"
    target: "path/to/file.py"
    result: "success"
    summary: "One line description of what happened"
    
  - step: 8
    action: "run_check"
    target: "conformance"
    result: "failing"
    summary: "2 of 5 checks now passing"

verification_status:           # ~200 tokens
  checks_passing: 3
  checks_failing: 2
  tests_passing: true
  ready_for_completion: false

available_actions:             # ~500 tokens, phase-specific
  - name: "read_file"
    description: "Read file contents"
  - name: "edit_file"
    description: "Modify file contents"
  - name: "run_check"
    description: "Run verification check"
  - name: "complete"
    description: "Mark task complete (only when all criteria met)"
  - name: "escalate"
    description: "Request human help (when stuck)"
```

### Context Schemas by Task Type

Different tasks require different context shapes:

#### Fix Violation

```yaml
context_schema: fix_violation
max_tokens: 6000

current_state:
  violation:
    id: "V-xxxxx"
    check_id: "check-name"
    severity: "major"
    file_path: "path/to/file.py"
    message: "What's wrong"
    fix_hint: "How to fix (if available)"
    
  check_definition:            # What the check actually looks for
    pattern: "regex or description"
    requirement: "What correct code looks like"
    
  file_content:                # The file being fixed
    path: "path/to/file.py"
    content: |
      # Truncated to relevant section if large
      # Shows line numbers for reference
    
  verification:
    last_check_result: "3 of 5 passing"
    remaining_issues:
      - line: 45
        issue: "Missing help parameter"
```

#### Implement Feature

```yaml
context_schema: implement_feature
max_tokens: 8000

current_state:
  spec:                        # Verified specification
    title: "Feature name"
    requirements:
      - id: "REQ-1"
        description: "..."
        acceptance_criteria: "..."
    constraints:
      - "..."
      
  target_files:                # Files to create/modify
    - path: "path/to/new_file.py"
      status: "to_create"
    - path: "path/to/existing.py"
      status: "to_modify"
      relevant_section: |
        # Only the part being modified
        
  test_requirements:           # What tests must pass
    - "Test X must pass"
    - "Coverage must be > 80%"
```

#### Write Tests (RED phase)

```yaml
context_schema: write_tests
max_tokens: 6000

current_state:
  spec:
    requirements:
      - id: "REQ-1"
        acceptance_criteria: "..."
        
  test_patterns:               # Existing test patterns in codebase
    example_test: |
      def test_example():
          # Shows project's test style
          
  target_test_file:
    path: "tests/test_feature.py"
    existing_content: null     # Or existing tests if modifying
```

### Token Budget Enforcement

Hard limits enforced by the context builder:

```python
TOKEN_BUDGET = {
    "system_prompt": 1000,
    "task_frame": 500,
    "current_state": 4500,     # Largest allocation
    "recent_actions": 1000,    
    "verification_status": 200,
    "available_actions": 800,
    # ─────────────────────────
    # Total: 8000 max
}
```

Compression strategies when content exceeds allocation:

| Content Type | Compression Strategy |
|--------------|---------------------|
| File content | Show first/last N lines, middle replaced with `# ... {X} lines omitted ...` |
| Recent actions | Keep only last 3 (or 2 if still over) |
| Tool results | Summarize to single line |
| Error messages | Truncate to first 500 chars |
| Lists | Keep first N items + "and X more" |

### Just-In-Time Context Loading

Agents can request additional context when needed:

```yaml
available_actions:
  - name: "load_context"
    description: "Load additional context into working memory"
    parameters:
      item:
        type: "string"
        enum:
          - "full_file:{path}"      # Load complete file
          - "related_files"          # Load files that import/are imported by current
          - "test_output"            # Load full test output
          - "spec_section:{id}"      # Load specific spec section
          - "error_details"          # Load full error trace
    note: "Loaded content appears in next step's context. Use sparingly."
```

When agent calls `load_context`, the item is added to `working_memory.yaml` and included in subsequent steps until explicitly cleared or displaced by newer items.

### Step Execution Flow

```python
class MinimalContextExecutor:
    def execute_step(self, task_id: str) -> StepResult:
        # 1. Load current state from disk
        state = self.state_store.load(task_id)
        
        # 2. Build minimal context (always 4-8K tokens)
        context = self.context_builder.build(state)
        
        # 3. Single LLM call with fresh conversation
        response = self.llm.generate(
            messages=[
                {"role": "system", "content": self.get_system_prompt(state.phase)},
                {"role": "user", "content": self.format_context(context)}
            ]
        )
        
        # 4. Parse and execute action
        action = self.action_parser.parse(response)
        result = self.action_executor.execute(action, state)
        
        # 5. Update state on disk
        self.state_store.record_action(task_id, action, result)
        self.state_store.update_verification(task_id)
        self.state_store.update_working_memory(task_id, action, result)
        
        # 6. Check completion
        if self.is_complete(state):
            return StepResult(complete=True, success=True)
        if self.should_escalate(state, result):
            return StepResult(complete=True, escalate=True)
            
        return StepResult(complete=False)
```

### State Transitions

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Load   │────▶│  Build  │────▶│  Call   │────▶│ Execute │
│  State  │     │ Context │     │   LLM   │     │ Action  │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
     ▲                                               │
     │                                               ▼
     │          ┌─────────┐     ┌─────────┐     ┌─────────┐
     └──────────│  Next   │◀────│ Update  │◀────│ Verify  │
                │  Step   │     │  State  │     │ Result  │
                └─────────┘     └─────────┘     └─────────┘
```

### Working Memory Management

`working_memory.yaml` is a bounded rolling buffer:

```yaml
# .agentforge/tasks/{task_id}/working_memory.yaml

max_items: 5
items:
  - type: "action_result"
    step: 8
    content:
      action: "edit_file"
      result: "success"
      summary: "Added help parameter to 3 commands"
    added_at: "2025-12-31T12:00:00Z"
    
  - type: "loaded_context"
    key: "full_file:cli/commands/spec.py"
    content: |
      # Full file content
    added_at: "2025-12-31T12:01:00Z"
    expires_after_steps: 3     # Auto-remove after 3 steps
    
  - type: "action_result"
    step: 9
    content:
      action: "run_check"
      result: "partial"
      summary: "4 of 5 checks passing"
    added_at: "2025-12-31T12:02:00Z"
```

When new items exceed `max_items`, oldest items are evicted (FIFO), unless marked as `pinned: true`.

### System Prompts by Phase

Each phase has a focused system prompt:

```python
SYSTEM_PROMPTS = {
    "fix_violation": """You are fixing a conformance violation.

Your goal: Make the code pass the conformance check.

Process:
1. Understand what the check requires
2. Identify what's wrong in the current code
3. Make minimal edits to fix the issue
4. Verify the fix by running the check

Rules:
- Only modify code related to the violation
- Make minimal changes
- Verify before marking complete
- Escalate if stuck after 3 different approaches

Actions available: {actions}
""",
    
    "implement_red": """You are writing failing tests for a specification.

Your goal: Create tests that define the expected behavior.

Process:
1. Read the requirements and acceptance criteria
2. Write tests that would pass if the feature worked
3. Verify tests fail (implementation doesn't exist yet)

Rules:
- One test per acceptance criterion minimum
- Tests must be runnable
- Tests must currently fail
- Follow existing test patterns in codebase

Actions available: {actions}
""",
    
    # ... other phases
}
```

### Verification at Every Step

After each action, verification runs:

```python
def update_verification(self, task_id: str):
    state = self.load(task_id)
    
    verification = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Run task-specific verification
    if state.task_type == "fix_violation":
        result = self.run_conformance_check(
            state.violation.check_id,
            state.violation.file_path
        )
        verification["checks"]["conformance"] = {
            "passing": result.passing,
            "details": result.summary
        }
        
    elif state.task_type == "implement_feature":
        test_result = self.run_tests(state.test_path)
        verification["checks"]["tests"] = {
            "passing": test_result.all_passed,
            "details": f"{test_result.passed}/{test_result.total} passing"
        }
    
    # Update state
    state.verification = verification
    state.ready_for_completion = all(
        c["passing"] for c in verification["checks"].values()
    )
    self.save(state)
```

## Implementation Requirements

### Required Components

1. **StateStore** - Manages task state on disk
2. **ContextBuilder** - Builds minimal context from state
3. **TokenBudget** - Enforces token limits
4. **MinimalContextExecutor** - Executes steps with fresh context
5. **WorkingMemoryManager** - Manages rolling buffer

### File Changes

```
tools/harness/
├── minimal_context/
│   ├── __init__.py
│   ├── state_store.py         # Task state persistence
│   ├── context_builder.py     # Builds step context
│   ├── context_schemas.py     # Task-type specific schemas
│   ├── token_budget.py        # Enforces limits
│   ├── working_memory.py      # Rolling buffer management
│   └── executor.py            # Stateless step execution
```

### Migration from Current Executor

The current `LLMExecutor` accumulates conversation history. It should be replaced with `MinimalContextExecutor` that:

1. Never passes conversation history
2. Always builds context from state store
3. Guarantees token budget compliance
4. Records all actions to append-only log

## Success Criteria

- [ ] Step 1 and Step 100 use same token count (±10%)
- [ ] No step exceeds 8K tokens
- [ ] All state recoverable from disk after crash
- [ ] Multi-day execution works (stop/resume)
- [ ] Rate limits not exceeded at any step
- [ ] Full audit trail in actions.yaml

## Token Budget Proof

```
Step   | Old Architecture | New Architecture
-------|------------------|------------------
1      | 6,667           | 6,000
2      | 19,597          | 6,000
3      | 27,436          | 6,000
4      | 38,738          | 6,000
5      | 48,399          | 6,000
...    | ∞               | 6,000
100    | (impossible)    | 6,000
```

## References

- North Star: `agentforge start "request"` runs to completion autonomously
- Trust Equation: Verified Input → Constrained Process → Verified Output
- Human Role: Escalation target, not gatekeeper