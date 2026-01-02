# Agent Harness Implementation Plan

## Using AgentForge to Build the Autonomous Agent Framework

**Document Version:** 1.0  
**Created:** 2025-12-30  
**Estimated Duration:** 6-8 weeks

---

## Overview

This document provides a complete, step-by-step implementation plan for building the Agent Harness layer using AgentForge's SPEC and TDFLOW workflows. Each step includes the exact commands and prompts to use.

### Architecture Summary

```
┌────────────────────────────────────────────────────────────────┐
│  NEW: Agent Harness Layer                                       │
│  ├── Session Manager (Phase 1)                                  │
│  ├── Memory System (Phase 2)                                    │
│  ├── Tool Selector (Phase 3)                                    │
│  ├── Agent Monitor (Phase 4)                                    │
│  ├── Recovery Strategies (Phase 5)                              │
│  ├── Human Escalation (Phase 6)                                 │
│  └── Agent Orchestrator (Phase 7)                               │
├────────────────────────────────────────────────────────────────┤
│  EXISTING: AgentForge Core                                      │
│  ├── SPEC Workflow                                              │
│  ├── TDFLOW Workflow                                            │
│  ├── Conformance Checker                                        │
│  ├── Discovery Engine                                           │
│  └── Bridge                                                     │
└────────────────────────────────────────────────────────────────┘
```

### Component Dependencies

```
Phase 1: Session Manager ──────────────────┐
                                           │
Phase 2: Memory System ───────────────────┤
         (depends on Session)              │
                                           ├──► Phase 7: Orchestrator
Phase 3: Tool Selector ───────────────────┤    (integrates all)
         (independent)                     │
                                           │
Phase 4: Agent Monitor ───────────────────┤
         (depends on Session)              │
                                           │
Phase 5: Recovery Strategies ─────────────┤
         (depends on Monitor)              │
                                           │
Phase 6: Human Escalation ────────────────┘
         (depends on Recovery)
```

---

## Phase 0: Foundation Setup

### Step 0.1: Run Self-Discovery

```bash
# Discover AgentForge's own patterns
agentforge discover --path . --verbose

# Review the generated profile
cat .agentforge/codebase_profile.yaml
```

### Step 0.2: Generate Self-Contract (Optional)

```bash
# Preview what Bridge would generate
agentforge bridge preview

# Generate contracts from discovered patterns
agentforge bridge generate
```

### Step 0.3: Baseline Conformance

```bash
# Establish baseline - all new code must not increase violations
agentforge ci baseline save

# Verify current state
agentforge conformance check
```

### Step 0.4: Create Harness Directory Structure

```bash
mkdir -p tools/harness
mkdir -p tests/unit/harness
mkdir -p tests/integration/harness
touch tools/harness/__init__.py
touch tests/unit/harness/__init__.py
touch tests/integration/harness/__init__.py
```

---

## Phase 1: Session Manager

**Goal:** Implement the Initializer-Worker pattern for managing agent work sessions.

**Duration:** 1 week

### Step 1.1: SPEC Intake

```bash
agentforge intake
```

**Intake Prompt:**
```
Create a Session Manager component for the Agent Harness that implements the 
Initializer-Worker pattern for long-running agent sessions.

CONTEXT:
- This is part of a larger Agent Harness layer being added to AgentForge
- It will integrate with existing SPEC and TDFLOW workflows
- State must be externalized to survive context window resets

REQUIREMENTS:
1. Session Lifecycle Management
   - Create new sessions with unique IDs
   - Track session state (active, paused, completed, aborted)
   - Support session checkpointing for recovery
   - Clean termination with state preservation

2. State Externalization
   - Persist session state to .agentforge/sessions/{session_id}/
   - State file: session.yaml with full session metadata
   - Artifacts directory for session outputs
   - Support atomic state updates

3. Token Budget Tracking
   - Track tokens used vs budget per session
   - Warn when approaching budget limit
   - Support budget extension

4. Workflow Integration
   - Track current workflow (spec, tdflow, etc.)
   - Track current phase within workflow
   - Track attempt number for retries

5. Session Artifacts
   - Maintain list of files created/modified
   - Track verification results per phase
   - Support artifact retrieval for context

CONSTRAINTS:
- Must use dataclasses for domain entities
- Must follow AgentForge patterns (Result pattern, etc.)
- Must be fully testable with no external dependencies
- State format must be YAML for human readability

RELATED FILES:
- tools/spec/domain.py (example of domain entities)
- tools/tdflow/domain.py (example of workflow state)
- tools/workflows/domain.py (workflow phase definitions)
```

### Step 1.2: SPEC Clarify

After intake, the system will prompt for clarifications. Expected questions and answers:

```yaml
clarifications:
  - question: "Should sessions support pause/resume across process restarts?"
    answer: "Yes, session state must be fully serializable to disk and 
             resumable in a new process."
  
  - question: "How should session IDs be generated?"
    answer: "Use UUID4 for uniqueness. Format: session-{uuid4}"
  
  - question: "What happens if a session file is corrupted?"
    answer: "Return a SessionCorrupted error with the path. Do not attempt 
             automatic recovery - escalate to human."
  
  - question: "Should sessions track wall-clock time or just token usage?"
    answer: "Both. Track started_at, last_activity, and elapsed_seconds 
             in addition to token counts."
  
  - question: "How should concurrent session access be handled?"
    answer: "Single-writer model. Use file locking for atomic updates. 
             Return SessionLocked error if lock cannot be acquired."
```

### Step 1.3: SPEC Analyze

The system will analyze the codebase for related patterns. Review the analysis.

```bash
# Review the analysis output
cat .agentforge/workspace/session_manager/analysis.yaml
```

### Step 1.4: SPEC Draft

The system will generate a specification. Review and iterate.

```bash
# Review the draft specification
cat .agentforge/workspace/session_manager/specification.yaml
```

### Step 1.5: SPEC Validate

```bash
agentforge spec validate
```

### Step 1.6: TDFLOW Red Phase

```bash
agentforge tdflow start --spec .agentforge/workspace/session_manager/specification.yaml
agentforge tdflow red
```

**Expected test file:** `tests/unit/harness/test_session_manager.py`

**Test categories to verify:**
- Session creation
- Session state transitions
- State persistence and loading
- Token budget tracking
- Checkpoint and resume
- Error handling

### Step 1.7: TDFLOW Green Phase

```bash
agentforge tdflow green
```

**Expected implementation file:** `tools/harness/session.py`

### Step 1.8: TDFLOW Verify

```bash
agentforge tdflow verify
```

### Step 1.9: Conformance Check

```bash
# Verify new code follows patterns
agentforge conformance check

# Verify no regression from baseline
agentforge ci run --mode incremental
```

---

## Phase 2: Memory System

**Goal:** Implement 4-tier memory hierarchy for agent context persistence.

**Duration:** 1 week

**Dependency:** Phase 1 (Session Manager)

### Step 2.1: SPEC Intake

```bash
agentforge intake
```

**Intake Prompt:**
```
Create a Memory System component for the Agent Harness that implements a 
4-tier memory hierarchy for agent context persistence.

CONTEXT:
- Integrates with Session Manager from Phase 1
- Provides persistent memory across sessions
- Enables context assembly for agent prompts

MEMORY TIERS:

1. Session Memory (Tier 1)
   - Ephemeral, cleared each session
   - Contains: current thoughts, scratch notes, working state
   - Storage: in-memory only
   - Lifecycle: created with session, destroyed on session end

2. Task Memory (Tier 2)
   - Persistent across sessions for a single task
   - Contains: feature list, progress log, attempt history
   - Storage: .agentforge/tasks/{task_id}/memory.yaml
   - Lifecycle: created with task, archived on completion

3. Project Memory (Tier 3)
   - Persistent for the project
   - Contains: codebase profile, contracts, learned patterns
   - Storage: .agentforge/project_memory.yaml
   - Lifecycle: created on init, grows over time

4. Organization Memory (Tier 4)
   - Persistent across projects
   - Contains: failure patterns, recovery strategies, best practices
   - Storage: ~/.agentforge/org_memory.yaml
   - Lifecycle: grows across all projects

REQUIREMENTS:

1. Memory Operations
   - get(tier, key) -> value or None
   - set(tier, key, value)
   - delete(tier, key)
   - list_keys(tier, prefix=None)
   - merge(tier, key, partial_value)

2. Memory Queries
   - search(query, tiers=[1,2,3,4]) -> relevant memories
   - get_context(max_tokens) -> assembled context from all tiers

3. Persistence
   - Auto-save on mutation for tiers 2-4
   - Atomic writes with temp files
   - Load on demand with caching

4. Integration
   - Link to Session via session_id
   - Link to Task via task_id
   - Access project memory via codebase profile path

CONSTRAINTS:
- YAML format for all persistent storage
- Must handle missing/corrupted files gracefully
- Must support concurrent read access
- Write operations should be synchronous and atomic

RELATED FILES:
- tools/harness/session.py (Session Manager from Phase 1)
- tools/context_assembler.py (existing context assembly)
- .agentforge/codebase_profile.yaml (project memory source)
```

### Step 2.2: SPEC Clarify

```yaml
clarifications:
  - question: "Should tier 4 (org memory) be shared across users?"
    answer: "No, org memory is per-user, stored in user's home directory."
  
  - question: "How should memory conflicts be resolved when merging?"
    answer: "Last-write-wins with timestamp tracking. Log conflicts for 
             human review but don't block."
  
  - question: "What's the maximum size for a single memory entry?"
    answer: "No hard limit, but warn if entry exceeds 10KB. Large data 
             should be stored as files and referenced by path."
  
  - question: "Should search use embeddings or keyword matching?"
    answer: "Start with keyword matching. Design interface to allow 
             embedding-based search as future enhancement."
```

### Step 2.3-2.9: Continue SPEC and TDFLOW

Follow same pattern as Phase 1:
- SPEC Analyze
- SPEC Draft
- SPEC Validate
- TDFLOW Red (tests)
- TDFLOW Green (implementation)
- TDFLOW Verify
- Conformance Check

---

## Phase 3: Tool Selector

**Goal:** Implement phase-appropriate tool selection for focused agent tooling.

**Duration:** 1 week

**Dependency:** None (can parallel with Phase 2)

### Step 3.1: SPEC Intake

```bash
agentforge intake
```

**Intake Prompt:**
```
Create a Tool Selector component for the Agent Harness that provides 
phase-appropriate tooling to agents based on their current workflow state.

CONTEXT:
- Agents should receive only tools relevant to their current task
- Reduces decision paralysis from having too many tools
- Enables domain-specific tool injection

CORE CONCEPT:
Instead of giving an agent 50 tools, give it the 3-5 tools appropriate 
for its current phase. A "red" phase agent gets test-writing tools, 
not deployment tools.

REQUIREMENTS:

1. Tool Profiles
   Define tool sets for each workflow phase:
   
   SPEC Workflow:
   - intake: [file_read, directory_list, search_code, write_yaml]
   - clarify: [file_read, ask_user, write_yaml]
   - analyze: [file_read, search_code, discover_patterns, write_yaml]
   - draft: [file_read, write_markdown, write_code]
   - validate: [conformance_check, write_yaml]
   
   TDFLOW Workflow:
   - red: [file_read, write_test, run_test]
   - green: [file_read, write_code, run_test, conformance_check]
   - refactor: [file_read, modify_code, run_test, conformance_check]
   - verify: [run_test, conformance_check, write_yaml]

2. Domain Tools
   Inject domain-specific tools based on project language:
   
   Python:
   - pytest, ruff_check, ruff_format, mypy
   
   .NET:
   - dotnet_build, dotnet_test, dotnet_format
   
   TypeScript:
   - npm_test, eslint, prettier

3. Tool Interface
   - get_tools(workflow, phase, domain) -> list[ToolDefinition]
   - register_tool(tool_definition)
   - register_domain_tools(domain, tools)

4. Tool Definition Schema
   Each tool has:
   - name: unique identifier
   - description: for agent understanding
   - parameters: JSON schema
   - handler: callable or MCP reference
   - requires_approval: bool (for sensitive operations)

5. Tool Composition
   - Base tools (always available): file_read, write_file
   - Phase tools (from profile)
   - Domain tools (from project language)
   - Custom tools (user-registered)

CONSTRAINTS:
- Tool definitions in YAML for configurability
- Must be extensible for new workflows/phases
- Must handle missing domain gracefully (fall back to base tools)

RELATED FILES:
- tools/workflows/domain.py (workflow definitions)
- contracts/ (existing tool-like checks)
```

### Step 3.2: SPEC Clarify

```yaml
clarifications:
  - question: "Should tools be lazily loaded or pre-loaded?"
    answer: "Lazily loaded. Only instantiate tool handlers when actually 
             invoked."
  
  - question: "How should tool conflicts be resolved (same name, different phases)?"
    answer: "Phase-specific tools override base tools. Log warning if 
             duplicate names with different definitions."
  
  - question: "Should tool profiles be configurable per-project?"
    answer: "Yes. Allow .agentforge/tool_profiles.yaml to override defaults."
  
  - question: "How should approval-required tools work?"
    answer: "Return a PendingApproval result that the harness handles. 
             Tool execution pauses until approval received."
```

### Step 3.3-3.9: Continue SPEC and TDFLOW

Follow same pattern as Phase 1.

---

## Phase 4: Agent Monitor

**Goal:** Implement self-monitoring to detect pathological agent behaviors.

**Duration:** 1 week

**Dependency:** Phase 1 (Session Manager)

### Step 4.1: SPEC Intake

```bash
agentforge intake
```

**Intake Prompt:**
```
Create an Agent Monitor component for the Agent Harness that detects 
pathological agent behaviors and provides health assessments.

CONTEXT:
- Autonomous agents can get stuck in loops, drift from tasks, or thrash
- Early detection enables recovery before wasting resources
- Integrates with Session Manager to track agent state

PATHOLOGIES TO DETECT:

1. Loop Detection
   - Same action repeated 3+ times consecutively
   - Same error occurring 3+ times
   - State returning to previous state repeatedly
   
2. Drift Detection
   - Agent focus diverging from original task
   - Working on files unrelated to task scope
   - Generating outputs not matching requirements
   
3. Thrashing Detection
   - Same lines modified repeatedly (>3 times)
   - Alternating between two states
   - Undo/redo patterns in changes
   
4. Context Pressure
   - Token usage approaching budget
   - Context window filling with low-value content
   - Repeated context overflow recoveries

5. Progress Stall
   - No successful verifications in N attempts
   - No file changes in N iterations
   - Stuck in same workflow phase too long

REQUIREMENTS:

1. Observation Interface
   - observe_action(action) - record agent action
   - observe_output(output) - record agent output  
   - observe_verification(result) - record verification result
   - observe_state_change(old_state, new_state) - record transitions

2. Detection Interface
   - detect_loop() -> LoopDetection | None
   - detect_drift(original_task) -> float (0.0-1.0 drift score)
   - detect_thrashing() -> ThrashingDetection | None
   - get_context_pressure() -> float (0.0-1.0)
   - get_progress_score() -> float (0.0-1.0)

3. Health Assessment
   - get_health() -> AgentHealth
     - overall: healthy | degraded | critical
     - issues: list of detected problems
     - recommendation: continue | checkpoint | escalate | abort

4. Configuration
   - Thresholds for each detection type
   - Configurable via .agentforge/monitor_config.yaml

CONSTRAINTS:
- Must be lightweight (minimal overhead per observation)
- Must maintain bounded history (sliding window)
- Must not block agent execution
- Detection methods must be deterministic

RELATED FILES:
- tools/harness/session.py (Session Manager)
- tools/workflows/domain.py (workflow states)
```

### Step 4.2: SPEC Clarify

```yaml
clarifications:
  - question: "How large should the observation history window be?"
    answer: "Default 100 observations. Configurable per detection type."
  
  - question: "Should drift detection use semantic similarity?"
    answer: "Initially use keyword overlap. Design for future embedding 
             support but start simple."
  
  - question: "How often should health be assessed?"
    answer: "On-demand via get_health(). Caller decides frequency."
  
  - question: "Should monitor persist observations across sessions?"
    answer: "No. Each session starts fresh. Task-level patterns tracked 
             in Task Memory instead."
```

### Step 4.3-4.9: Continue SPEC and TDFLOW

Follow same pattern as Phase 1.

---

## Phase 5: Recovery Strategies

**Goal:** Implement SHIELDA-based multi-level recovery for agent failures.

**Duration:** 1 week

**Dependency:** Phase 4 (Agent Monitor)

### Step 5.1: SPEC Intake

```bash
agentforge intake
```

**Intake Prompt:**
```
Create a Recovery Strategies component for the Agent Harness that implements 
SHIELDA-based multi-level recovery for handling agent failures.

CONTEXT:
- Based on SHIELDA framework (Structured Handling of Exceptions in 
  LLM-Driven Agentic Workflows)
- Integrates with Agent Monitor for trigger detection
- Provides escalating recovery strategies

RECOVERY LEVELS (in order of escalation):

Level 1: Simple Retry
- Triggers: compile_error, single_test_failure, lint_violation
- Actions: inject_error_into_context, retry_same_phase
- Max attempts: 3
- Example: "Build failed, here's the error, try again"

Level 2: Context Enrichment
- Triggers: repeated_same_error, architectural_violation, pattern_mismatch
- Actions: retrieve_related_code, add_pattern_examples, retry_same_phase
- Max attempts: 2
- Example: "Here's how similar code handles this pattern"

Level 3: Approach Pivot
- Triggers: 5_consecutive_failures, incompatible_requirements
- Actions: summarize_failed_approaches, request_alternative_strategy, 
           clear_implementation_artifacts, retry_from_planning
- Max attempts: 1
- Example: "Previous approaches failed, try a different strategy"

Level 4: Task Decomposition
- Triggers: task_too_complex, multiple_unrelated_failures
- Actions: analyze_failure_patterns, propose_subtasks, queue_subtasks,
           mark_parent_blocked
- Max attempts: 1
- Example: "Task is too large, breaking into smaller pieces"

Level 5: Human Escalation
- Triggers: decomposition_failed, security_concern, ambiguous_requirement
- Actions: generate_escalation_report, preserve_all_context, 
           notify_human, await_human_input
- Example: "I'm stuck and need human guidance"

Level 6: Graceful Abort
- Triggers: human_requests_abort, impossible_constraint, resource_exhaustion
- Actions: document_failure_reason, rollback_partial_changes, 
           archive_session, mark_task_failed
- Example: "Task cannot be completed, documenting why"

REQUIREMENTS:

1. Strategy Selection
   - select_strategy(failure_context) -> RecoveryStrategy
   - Considers: failure type, attempt history, monitor health
   - Returns appropriate strategy level

2. Strategy Execution
   - execute_strategy(strategy, context) -> RecoveryResult
   - RecoveryResult: success | retry | escalate | abort
   - Each strategy has defined actions

3. Escalation Logic
   - Automatic escalation when current level exhausted
   - Track escalation history
   - Prevent infinite escalation loops

4. Configuration
   - Per-level max attempts
   - Custom triggers per project
   - Escalation overrides

5. Reporting
   - Log all recovery attempts
   - Generate recovery report for human review
   - Track recovery success rates

CONSTRAINTS:
- Strategies must be stateless (state in session/memory)
- Must integrate with existing verification results
- Must not lose work during recovery
- Human escalation must be non-blocking (queue and continue)

RELATED FILES:
- tools/harness/monitor.py (Agent Monitor)
- tools/harness/session.py (Session Manager)
- tools/harness/memory.py (Memory System)
```

### Step 5.2: SPEC Clarify

```yaml
clarifications:
  - question: "Should strategies be pluggable/extensible?"
    answer: "Yes. Define base strategy interface. Allow custom strategies 
             registered via config."
  
  - question: "How should 'related code' be retrieved for context enrichment?"
    answer: "Use existing context retrieval. Pass failure context as query 
             to find relevant examples."
  
  - question: "What defines 'task too complex' for decomposition trigger?"
    answer: "Heuristics: >5 distinct failures across >3 files, or monitor 
             drift score >0.5, or explicit complexity flag in spec."
  
  - question: "How should rollback work for graceful abort?"
    answer: "Git-based if available: stash or revert uncommitted changes. 
             Otherwise, restore from last checkpoint artifacts."
```

### Step 5.3-5.9: Continue SPEC and TDFLOW

Follow same pattern as Phase 1.

---

## Phase 6: Human Escalation

**Goal:** Implement human-in-the-loop interface for agent oversight.

**Duration:** 1 week

**Dependency:** Phase 5 (Recovery Strategies)

### Step 6.1: SPEC Intake

```bash
agentforge intake
```

**Intake Prompt:**
```
Create a Human Escalation component for the Agent Harness that provides 
human-in-the-loop oversight capabilities for autonomous agents.

CONTEXT:
- Triggered by Recovery Strategies when agent needs human help
- Provides CLI interface for monitoring and intervention
- Enables approval workflows for sensitive operations

ESCALATION TYPES:

1. Guidance Request
   - Agent is stuck and needs direction
   - Human provides text guidance that's injected into context
   - Agent resumes with guidance

2. Approval Request
   - Agent wants to perform sensitive operation
   - Human approves or rejects
   - Agent proceeds or takes alternative action

3. Clarification Request
   - Specification is ambiguous
   - Human provides clarification
   - Agent updates understanding and continues

4. Review Request
   - Agent completed work, wants human review
   - Human approves, requests changes, or rejects
   - Agent proceeds, revises, or aborts

5. Takeover Request
   - Agent cannot proceed autonomously
   - Human takes over manually
   - Agent provides full context dump for handoff

REQUIREMENTS:

1. Escalation Queue
   - queue_escalation(type, context, agent_id)
   - get_pending_escalations() -> list
   - resolve_escalation(id, resolution)

2. CLI Commands
   - agentforge agent status - show all agents and their state
   - agentforge agent escalations - list pending escalations
   - agentforge agent guide <agent_id> "<message>" - provide guidance
   - agentforge agent approve <escalation_id> - approve request
   - agentforge agent reject <escalation_id> "<reason>" - reject request
   - agentforge agent abort <agent_id> - abort agent task
   - agentforge agent takeover <agent_id> - generate takeover context

3. Notification
   - Console output when escalation queued
   - Optional: file-based notification for external monitoring
   - Escalation persists until resolved

4. Context Preservation
   - Full context dump for escalations
   - Include: task, session, attempt history, last error
   - Formatted for human readability

5. Resolution Injection
   - Human resolution injected into agent context
   - Agent notified of resolution type
   - Agent adapts behavior based on resolution

CONSTRAINTS:
- CLI must work with agents running in background
- Escalations persist across process restarts
- Must support multiple concurrent agents
- Resolution must be atomic (no partial resolutions)

RELATED FILES:
- tools/harness/recovery.py (Recovery Strategies)
- tools/harness/session.py (Session Manager)
- cli/click_commands/ (existing CLI patterns)
```

### Step 6.2: SPEC Clarify

```yaml
clarifications:
  - question: "How should background agents be implemented?"
    answer: "Out of scope for this component. Assume agent runs in 
             foreground with periodic escalation checks. Background 
             execution is future enhancement."
  
  - question: "Should there be timeout on escalations?"
    answer: "No automatic timeout. Escalations wait indefinitely. 
             Human can explicitly abort if no longer relevant."
  
  - question: "How should multiple pending escalations be prioritized?"
    answer: "FIFO by default. Add priority field for future 
             enhancement. Critical escalations (security) could 
             jump queue."
  
  - question: "Should escalation context include file contents?"
    answer: "Include relevant snippets, not full files. Link to 
             files for full context. Keep escalation payload 
             under 5KB."
```

### Step 6.3-6.9: Continue SPEC and TDFLOW

Follow same pattern as Phase 1.

---

## Phase 7: Agent Orchestrator

**Goal:** Integrate all harness components into a cohesive agent loop.

**Duration:** 1.5 weeks

**Dependency:** All previous phases (1-6)

### Step 7.1: SPEC Intake

```bash
agentforge intake
```

**Intake Prompt:**
```
Create an Agent Orchestrator component that integrates all Agent Harness 
components into a cohesive autonomous agent loop.

CONTEXT:
- Integrates: Session Manager, Memory System, Tool Selector, Agent Monitor,
  Recovery Strategies, Human Escalation
- Executes agents through SPEC and TDFLOW workflows
- Provides the main entry point for autonomous operation

THE AGENT LOOP:

1. INITIALIZE
   - Create or resume session
   - Load task and project memory
   - Determine current workflow and phase
   - Select appropriate tools

2. PERCEIVE
   - Gather context from memory tiers
   - Retrieve relevant code/docs
   - Assemble prompt with phase requirements

3. PLAN
   - Generate action via LLM (external - out of scope)
   - Parse action into executable form
   - Validate action is allowed for current phase

4. ACT
   - Execute action (file operations, tool calls)
   - Record action in session
   - Update scratch memory

5. VERIFY (AgentForge Core)
   - Run phase-appropriate verification
   - Conformance check
   - Build/test as needed

6. REFLECT
   - Update monitor with observations
   - Check health status
   - Persist state changes

7. DECIDE
   - If verification passed: advance phase
   - If verification failed: select recovery strategy
   - If escalation needed: queue and pause
   - If complete: finalize and report

REQUIREMENTS:

1. Orchestrator Interface
   - start_task(task_description) -> session_id
   - resume_session(session_id) -> session_id
   - run_iteration() -> IterationResult
   - get_status() -> AgentStatus

2. Iteration Result
   - outcome: advanced | retry | escalated | completed | aborted
   - next_action: what orchestrator recommends next
   - artifacts: files created/modified
   - verification: results of checks

3. Context Assembly
   - Use Memory System for context
   - Apply token budgets
   - Prioritize by relevance

4. Workflow Integration
   - Use existing SPEC workflow engine
   - Use existing TDFLOW workflow engine
   - Support custom workflows

5. CLI Commands
   - agentforge agent start "<task>" - start new agent task
   - agentforge agent resume <session_id> - resume paused agent
   - agentforge agent step <session_id> - run single iteration
   - agentforge agent run <session_id> - run until completion/escalation

ARCHITECTURE:

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentOrchestrator                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Session   │  │   Memory    │  │   Tool Selector     │  │
│  │   Manager   │  │   System    │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│  ┌──────┴────────────────┴─────────────────────┴──────────┐ │
│  │                    Agent Loop                           │ │
│  │  INIT → PERCEIVE → PLAN → ACT → VERIFY → REFLECT → ... │ │
│  └──────┬────────────────┬─────────────────────┬──────────┘ │
│         │                │                     │             │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────────┴──────────┐  │
│  │   Monitor   │  │  Recovery   │  │  Human Escalation   │  │
│  └─────────────┘  │  Strategies │  │                     │  │
│                   └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AgentForge Core                           │
│  SPEC Workflow │ TDFLOW Workflow │ Conformance │ Discovery  │
└─────────────────────────────────────────────────────────────┘
```

CONSTRAINTS:
- LLM calls are out of scope (return prompts for external execution)
- Must support human-in-loop mode (current) and future API mode
- Must checkpoint after every iteration
- Must handle interrupts gracefully (Ctrl+C)

RELATED FILES:
- tools/harness/session.py
- tools/harness/memory.py
- tools/harness/tools.py
- tools/harness/monitor.py
- tools/harness/recovery.py
- tools/harness/escalation.py
- tools/spec/ (SPEC workflow)
- tools/tdflow/ (TDFLOW workflow)
```

### Step 7.2: SPEC Clarify

```yaml
clarifications:
  - question: "How should LLM interaction work in human-in-loop mode?"
    answer: "Orchestrator generates prompt, returns it to caller. Caller 
             (human or API) provides response. Orchestrator continues 
             with response."
  
  - question: "Should the orchestrator support parallel agents?"
    answer: "Not in initial version. Single agent per orchestrator 
             instance. Parallel execution via multiple instances."
  
  - question: "How should Ctrl+C be handled?"
    answer: "Catch signal, checkpoint current state, mark session as 
             paused, exit cleanly. Session resumable."
  
  - question: "What if a component is not available (e.g., Memory System)?"
    answer: "Orchestrator should work with degraded capabilities. Use 
             in-memory fallbacks. Log warnings."
```

### Step 7.3-7.9: Continue SPEC and TDFLOW

Follow same pattern as Phase 1.

---

## Phase 8: Integration Testing

**Goal:** End-to-end testing of the complete Agent Harness.

**Duration:** 1 week

### Step 8.1: Create Integration Test Suite

```bash
agentforge intake
```

**Intake Prompt:**
```
Create an integration test suite for the Agent Harness that validates 
end-to-end autonomous operation.

TEST SCENARIOS:

1. Simple Task Completion
   - Start agent with simple TDFLOW task
   - Agent completes without recovery
   - Verify: session complete, artifacts correct, tests passing

2. Recovery from Compile Error
   - Start agent with task that will have compile error
   - Agent recovers via simple retry
   - Verify: recovery logged, task completes

3. Context Enrichment Recovery
   - Start agent with task needing pattern example
   - Simple retry fails, context enrichment succeeds
   - Verify: escalation to level 2, then success

4. Human Escalation
   - Start agent with ambiguous task
   - Agent escalates to human
   - Simulate human guidance
   - Agent completes with guidance
   - Verify: escalation queued, resolution applied

5. Session Resume
   - Start agent, interrupt mid-task
   - Resume session
   - Verify: state restored, continues correctly

6. Multi-Phase Workflow
   - Start agent with SPEC workflow
   - Complete through all phases
   - Transition to TDFLOW
   - Complete implementation
   - Verify: cross-workflow transition works

7. Graceful Abort
   - Start agent with impossible task
   - Agent escalates through levels
   - Human requests abort
   - Verify: clean abort, documentation generated

8. Monitor Detection
   - Start agent that will loop
   - Monitor detects loop
   - Recovery triggered
   - Verify: loop detected, recovery applied
```

### Step 8.2: Run Integration Tests

```bash
pytest tests/integration/harness/ -v
```

### Step 8.3: Conformance Verification

```bash
# Final conformance check on all new code
agentforge conformance check

# Verify no regression from Phase 0 baseline
agentforge ci run --mode incremental --base-ref phase-0-baseline
```

---

## Verification Checklist

After each phase, verify:

- [ ] SPEC workflow completed (INTAKE → CLARIFY → ANALYZE → DRAFT → VALIDATE)
- [ ] TDFLOW workflow completed (RED → GREEN → REFACTOR → VERIFY)
- [ ] All unit tests passing
- [ ] Conformance check passing
- [ ] No new violations vs baseline
- [ ] Code follows AgentForge patterns
- [ ] Documentation updated

---

## Success Criteria

The implementation is complete when:

1. **Unit Test Coverage**
   - [ ] Session Manager: >90% coverage
   - [ ] Memory System: >90% coverage
   - [ ] Tool Selector: >90% coverage
   - [ ] Agent Monitor: >90% coverage
   - [ ] Recovery Strategies: >90% coverage
   - [ ] Human Escalation: >90% coverage
   - [ ] Agent Orchestrator: >80% coverage

2. **Integration Tests**
   - [ ] All 8 scenarios passing

3. **Conformance**
   - [ ] 0 new violations vs Phase 0 baseline
   - [ ] All code follows discovered patterns

4. **Functionality**
   - [ ] Agent can complete simple TDFLOW task
   - [ ] Agent can recover from common failures
   - [ ] Human can monitor and intervene
   - [ ] Sessions persist and resume correctly

5. **Documentation**
   - [ ] README for harness module
   - [ ] CLI command documentation
   - [ ] Architecture decision records

---

## Appendix A: File Structure

After implementation, the harness structure should be:

```
tools/harness/
├── __init__.py
├── session.py          # Phase 1: Session Manager
├── memory.py           # Phase 2: Memory System
├── tools.py            # Phase 3: Tool Selector
├── monitor.py          # Phase 4: Agent Monitor
├── recovery.py         # Phase 5: Recovery Strategies
├── escalation.py       # Phase 6: Human Escalation
├── orchestrator.py     # Phase 7: Agent Orchestrator
└── domain.py           # Shared domain entities

cli/click_commands/
├── agent.py            # Phase 6-7: Agent CLI commands

tests/unit/harness/
├── __init__.py
├── test_session.py
├── test_memory.py
├── test_tools.py
├── test_monitor.py
├── test_recovery.py
├── test_escalation.py
└── test_orchestrator.py

tests/integration/harness/
├── __init__.py
└── test_agent_scenarios.py
```

---

## Appendix B: Contract Additions

Add these checks to `agentforge.contract.yaml` for harness code:

```yaml
# Harness-specific checks
- id: harness-session-state
  name: "Session state serializable"
  description: "All session state must be YAML-serializable"
  type: custom
  enabled: true
  severity: error
  applies_to:
    paths:
      - "tools/harness/**/*.py"

- id: harness-no-global-state
  name: "No global mutable state"
  description: "Harness modules must not have global mutable state"
  type: regex
  enabled: true
  severity: error
  config:
    pattern: "^[A-Z_]+\\s*=\\s*\\[|^[A-Z_]+\\s*=\\s*\\{"
    mode: forbid
  applies_to:
    paths:
      - "tools/harness/**/*.py"
```

---

## Appendix C: Configuration Files

### .agentforge/harness_config.yaml

```yaml
# Agent Harness Configuration
session:
  checkpoint_interval: 5  # Checkpoint every N iterations
  max_token_budget: 100000
  state_directory: .agentforge/sessions

memory:
  session_max_entries: 100
  task_auto_save: true
  project_path: .agentforge/project_memory.yaml
  org_path: ~/.agentforge/org_memory.yaml

tools:
  domain: auto  # Detect from codebase_profile
  custom_profiles: .agentforge/tool_profiles.yaml

monitor:
  history_window: 100
  loop_threshold: 3
  drift_threshold: 0.5
  thrash_threshold: 3

recovery:
  level_1_max_attempts: 3
  level_2_max_attempts: 2
  level_3_max_attempts: 1
  auto_escalate: true

escalation:
  queue_path: .agentforge/escalations/
  notify_console: true
  notify_file: .agentforge/escalation_notifications.log
```

---

## Notes

- Each phase builds on previous phases - follow order for dependencies
- SPEC workflow ensures requirements are clear before implementation
- TDFLOW ensures tests exist before implementation (correctness-first)
- Conformance checks ensure code follows AgentForge patterns
- Human-in-loop mode works now; API mode is future enhancement
