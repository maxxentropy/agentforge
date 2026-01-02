# Bootstrapping AgentForge: Using AgentForge to Build the Agent Harness

## The Meta-Challenge

We want to use AgentForge's capabilities to build the Agent Harness that will make AgentForge autonomous. This is classic bootstrapping - using a tool to improve itself.

**Current State:**
- AgentForge has SPEC, Conformance, Discovery, Bridge, TDFLOW, CI/CD
- AgentForge does NOT have a codebase profile of itself yet
- AgentForge contracts exist but aren't generated from discovery

**Target State:**
- Agent Harness layer built using SPEC → TDFLOW workflow
- New code verified by Conformance against AgentForge's own patterns
- Each component has specs, tests, and verified implementations

---

## Phase 0: Self-Discovery (Foundation)

Before we can use AgentForge to build itself, we need to understand AgentForge's own patterns.

### Step 0.1: Run Discovery on AgentForge

```bash
# Discover AgentForge's patterns
agentforge discover --path . --output .agentforge/self_profile.yaml --verbose

# Generate contracts from discovered patterns
agentforge bridge preview
agentforge bridge generate --zone python --dry-run
```

**Expected Discoveries:**
- Python patterns (dataclasses, ABC, typing)
- Project structure (tools/, cli/, tests/)
- Naming conventions
- Test patterns (pytest, fixtures)
- Domain patterns (workflows, phases, verification)

### Step 0.2: Create AgentForge Self-Contract

```yaml
# contracts/agentforge-internal.contract.yaml
contract:
  name: "agentforge-internal"
  version: "1.0.0"
  description: "Patterns for AgentForge internal development"
  
zones:
  - name: "tools"
    paths: ["tools/**/*.py"]
    
  - name: "cli"
    paths: ["cli/**/*.py"]
    
  - name: "tests"
    paths: ["tests/**/*.py"]

checks:
  # Structural patterns
  - id: "dataclass-for-domain"
    type: "pattern"
    description: "Domain entities use @dataclass"
    pattern: "class.*:.*# domain"
    
  - id: "abc-for-interfaces"
    type: "pattern"
    description: "Abstract base classes for interfaces"
    
  # Naming patterns
  - id: "test-naming"
    type: "naming"
    pattern: "test_*.py"
    scope: "tests/"
    
  # Architecture patterns
  - id: "tools-independence"
    type: "import"
    description: "tools/ modules don't import from cli/"
    zone: "tools"
    forbidden_imports: ["cli.*"]
```

---

## Phase 1: SPEC the Agent Harness Components

Use AgentForge's SPEC workflow to create detailed specifications for each Agent Harness component.

### Component 1: Session Manager

```bash
# Start SPEC workflow for Session Manager
agentforge intake "Create a Session Manager that implements the Initializer-Worker 
pattern for long-running agent sessions. It should manage session lifecycle, 
externalize state to disk, and support checkpointing for recovery."

# Expected flow:
# INTAKE → CLARIFY → ANALYZE → DRAFT → VALIDATE
```

**Specification Requirements:**
- Session lifecycle (create, checkpoint, resume, complete, abort)
- State externalization (session.yaml, artifacts/)
- Token budget tracking
- Integration with existing workflows

### Component 2: Memory System

```bash
agentforge intake "Create a 4-tier Memory System with Session Memory (ephemeral), 
Task Memory (per-task persistent), Project Memory (project-wide), and 
Organization Memory (cross-project learning). Memory should be YAML-based 
and integrate with context assembly."
```

### Component 3: Recovery Strategies

```bash
agentforge intake "Create a SHIELDA-based Recovery Strategy system with 6 levels:
simple_retry, context_enrichment, approach_pivot, task_decomposition, 
human_escalation, and graceful_abort. Each strategy should have clear triggers 
and actions."
```

### Component 4: Tool Selector

```bash
agentforge intake "Create a Tool Selector that provides phase-appropriate tooling.
Given a workflow and phase, return only the tools relevant to that phase.
Support domain-specific tools (dotnet, pytest) in addition to base tools."
```

### Component 5: Agent Monitor

```bash
agentforge intake "Create an Agent Monitor that detects pathological behaviors:
loop detection (same action 3+ times), drift detection (semantic distance from 
original task), thrashing detection (repeatedly changing same lines), and 
context pressure monitoring."
```

### Component 6: Human Escalation

```bash
agentforge intake "Create a Human Escalation system with automatic triggers
(stuck, ambiguity, security), a CLI dashboard for monitoring agents, and
an override interface for human intervention."
```

---

## Phase 2: TDFLOW Implementation

For each component specification, run through TDFLOW:

### Example: Session Manager

```bash
# Start TDFLOW session from spec
agentforge tdflow start --spec .agentforge/workspace/session_manager/specification.yaml

# RED: Generate failing tests
agentforge tdflow red
# → Creates tests/unit/harness/test_session_manager.py
# → Tests should FAIL (no implementation yet)

# GREEN: Generate implementation
agentforge tdflow green
# → Creates tools/harness/session.py
# → Tests should PASS

# REFACTOR: Clean up
agentforge tdflow refactor

# VERIFY: Final verification
agentforge tdflow verify
# → Runs conformance check against agentforge-internal contract
# → Verifies tests pass
# → Checks patterns followed
```

### Verification at Each Step

```bash
# After each TDFLOW phase, verify against AgentForge patterns
agentforge conformance check --contracts agentforge-internal

# Check CI baseline (no new violations)
agentforge ci run --mode incremental
```

---

## Phase 3: Integration

### Step 3.1: Wire Components Together

```bash
# Spec the integration layer
agentforge intake "Create an AgentOrchestrator that integrates SessionManager,
MemorySystem, RecoveryStrategies, ToolSelector, and AgentMonitor into a 
coherent agent loop. The orchestrator should use existing SPEC and TDFLOW
workflows through AgentForge core."
```

### Step 3.2: Create Agent Harness CLI

```bash
agentforge intake "Create CLI commands for the Agent Harness:
- agentforge agent start <task> - Start autonomous agent
- agentforge agent status - Show agent status
- agentforge agent guide <message> - Inject human guidance
- agentforge agent abort - Abort with documentation"
```

---

## Execution Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BOOTSTRAP EXECUTION ORDER                             │
│                                                                              │
│  Phase 0: Self-Discovery                                                     │
│  ├── 0.1 Run discovery on AgentForge                                         │
│  ├── 0.2 Generate self-contract                                              │
│  └── 0.3 Verify current code passes self-contract                            │
│                                                                              │
│  Phase 1: SPEC Components (can parallelize after 1.1)                        │
│  ├── 1.1 Session Manager spec                                                │
│  ├── 1.2 Memory System spec                                                  │
│  ├── 1.3 Recovery Strategies spec                                            │
│  ├── 1.4 Tool Selector spec                                                  │
│  ├── 1.5 Agent Monitor spec                                                  │
│  └── 1.6 Human Escalation spec                                               │
│                                                                              │
│  Phase 2: TDFLOW Implementation (sequential - dependencies)                  │
│  ├── 2.1 Session Manager (foundation)                                        │
│  ├── 2.2 Memory System (needs session)                                       │
│  ├── 2.3 Tool Selector (independent)                                         │
│  ├── 2.4 Agent Monitor (needs session)                                       │
│  ├── 2.5 Recovery Strategies (needs monitor)                                 │
│  └── 2.6 Human Escalation (needs all above)                                  │
│                                                                              │
│  Phase 3: Integration                                                        │
│  ├── 3.1 Agent Orchestrator                                                  │
│  ├── 3.2 CLI Commands                                                        │
│  └── 3.3 End-to-end testing                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Practical Constraints

### What Works Now (Human-in-Loop)

Currently, AgentForge requires human copy-paste between CLI and Claude. This means:

1. **SPEC workflow**: Human runs `agentforge intake`, copies prompt to Claude, pastes response back
2. **TDFLOW workflow**: Human runs phase commands, copies prompts, pastes code back
3. **Verification**: Fully automated (conformance, tests)

### The Bootstrap Paradox

To make AgentForge fully autonomous, we need the Agent Harness.
To build the Agent Harness well, we'd ideally use AgentForge autonomously.

**Resolution:** Build the Agent Harness using AgentForge in human-in-loop mode, then use the result to make future development autonomous.

### Recommended Approach

**Option A: Full Human-in-Loop Bootstrap**
- Human orchestrates entire process
- Use SPEC for each component
- Use TDFLOW for implementation
- Verify with conformance
- ~4-6 weeks of focused work

**Option B: Hybrid Bootstrap**
- Build minimal Session Manager first (manual)
- Use minimal Agent Harness for remaining components
- Progressively increase autonomy
- ~6-8 weeks, but builds confidence

**Option C: Claude Code Assisted**
- Use Claude Code (current session) to generate initial implementations
- Verify with AgentForge conformance
- Iterate until passing
- ~2-3 weeks, fastest but less rigorous

---

## Starting Point: Phase 0

Let's start with self-discovery:

```bash
# Step 1: Run discovery
agentforge discover --path . --verbose

# Step 2: Review discovered patterns
cat .agentforge/codebase_profile.yaml

# Step 3: Generate contract from patterns
agentforge bridge preview --zone python

# Step 4: Verify current code
agentforge conformance check
```

This gives us the foundation to build new components that follow AgentForge's established patterns.

---

## Success Criteria

The bootstrap is complete when:

1. ✅ Agent Harness components implemented with tests
2. ✅ All components pass AgentForge conformance
3. ✅ Agent can complete simple TDFLOW task autonomously
4. ✅ Agent can recover from common failures
5. ✅ Human can monitor and intervene when needed
6. ✅ CI/CD validates all changes

At that point, AgentForge can be used to improve itself autonomously.
