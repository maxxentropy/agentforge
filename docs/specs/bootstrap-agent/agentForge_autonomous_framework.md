# AgentForge Autonomous Framework Proposal

## A Correctness-First Architecture for Long-Running AI Agents

**Document Version:** 1.0  
**Created:** 2025-12-30  
**Status:** Proposal for Discussion

---

## Executive Summary

This proposal outlines how to evolve AgentForge from a correctness verification toolkit into the foundation for **fully autonomous AI agents**. The key insight is that AgentForge already provides the critical "correctness layer" that most agent frameworks lack—deterministic verification, structured workflows, and machine-readable context. 

What's needed is an **Agent Harness** layer that provides session management, persistent memory, recovery strategies, and human escalation—transforming AgentForge into a complete autonomous development system.

**Core Principles:**
1. **Correctness First** — Agents verify outputs through deterministic tools, not self-assessment
2. **Machine-Readable Context Always** — All agent context is structured (YAML/JSON), never prose-only
3. **Domain Specialization** — Agents discover project patterns and receive tailored tooling
4. **Focused Tooling** — Agents get only the tools appropriate for their current task phase

---

## Part 1: The Problem with Current Agent Frameworks

### 1.1 The Autonomy-Correctness Paradox

Most agent frameworks optimize for autonomy (doing more without human intervention) at the expense of correctness. They give agents broad tool access and hope the LLM figures it out. This leads to:

- **Self-delusion**: Agent believes its code is correct because it "looks right"
- **Context drift**: Over long sessions, agent forgets constraints and makes inconsistent decisions
- **Unverified outputs**: No deterministic check that code compiles, tests pass, or patterns are followed
- **Kitchen-sink tooling**: Agent has 50 tools when it needs 3, leading to decision paralysis

### 1.2 What the Research Tells Us

The research document identifies critical patterns for successful autonomous agents:

| Pattern | Problem Solved | AgentForge Analog |
|---------|---------------|-------------------|
| **Initializer-Worker** | Context exhaustion in long sessions | Workflow state machine + artifact persistence |
| **SHIELDA** | Unstructured error handling | Recovery strategies per workflow phase |
| **MCP** | Tool integration complexity | Tool providers per language/domain |
| **Progressive Disclosure** | Context bloat | Hierarchical context layers |
| **External State** | Memory loss between sessions | feature_list.json, artifact_bundle.yaml |

### 1.3 The AgentForge Advantage

AgentForge already solves the hard problems:

| Capability | Status | Impact |
|------------|--------|--------|
| **Deterministic Verification** | ✅ Chunks 3, 7 | Agent outputs are verified by compiler, tests, static analysis |
| **Structured Workflows** | ✅ Chunk 1 | Agent follows defined state machine (SPEC, TDFLOW) |
| **Machine-Readable Context** | ✅ Chunks 2, 4, 5 | Contracts, profiles, specs are all YAML/JSON |
| **Domain Discovery** | ✅ Chunk 4 | Agent learns project patterns automatically |
| **Pattern-to-Contract Bridge** | ✅ Chunk 5 | Discovered patterns become verification rules |
| **CI Integration** | ✅ Chunk 7 | Baseline comparison, incremental checking |

**What's missing:** The Agent Harness that orchestrates long-running autonomous operation.

---

## Part 2: Architecture Overview

### 2.1 The Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 1: ORCHESTRATION                                    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │    Task      │  │    Agent     │  │   Multi-     │  │      Human       │ │
│  │    Queue     │  │  Dispatcher  │  │   Agent      │  │    Dashboard     │ │
│  │              │  │              │  │   Coordinator│  │                  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                    LAYER 2: AGENT HARNESS                                    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Session    │  │    Memory    │  │   Recovery   │  │      Human       │ │
│  │   Manager    │  │    System    │  │   Strategies │  │   Escalation     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────────┐   │
│  │   Loop       │  │   Self-      │  │        Tool Selection            │   │
│  │   Controller │  │   Monitor    │  │    (Phase-Appropriate Tooling)   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────────────┘   │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                    LAYER 3: AGENTFORGE CORE (Correctness)                    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │    SPEC      │  │ Conformance  │  │  Discovery   │  │     TDFLOW       │ │
│  │   Workflow   │  │   Checker    │  │    Engine    │  │    Workflow      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────────┐   │
│  │    Bridge    │  │    CI/CD     │  │      Context Assembler           │   │
│  │  Generation  │  │  Integration │  │  (Machine-Readable Context)      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────────────┘   │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                    LAYER 4: DOMAIN SPECIALIZATION                            │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Domain Profiles                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  .NET/C#    │  │   Python    │  │ TypeScript  │  │   Custom    │  │   │
│  │  │  Profile    │  │   Profile   │  │   Profile   │  │   Profile   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Toolkits per Domain                               │   │
│  │  Build │ Test │ Lint │ Format │ Analyze │ Deploy │ Document          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                    LAYER 5: EXECUTION                                        │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────────┐   │
│  │     LLM      │  │   Sandbox    │  │        MCP Servers               │   │
│  │   Provider   │  │   Container  │  │  (External Tool Integration)     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 The Correctness-First Loop

Every agent action follows this loop:

```
                    ┌─────────────────┐
                    │    PERCEIVE     │
                    │  Read state,    │
                    │  gather context │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     PLAN        │
                    │  Determine next │
                    │  action (LLM)   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     ACT         │
                    │  Execute action │
                    │  (file, tool)   │
                    └────────┬────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                    ★ VERIFY (AgentForge) ★                     │
│                                                                │
│  This is where AgentForge differs from other frameworks:       │
│                                                                │
│  1. Run deterministic checks (compile, test, lint)             │
│  2. Check conformance against contracts                        │
│  3. Validate against workflow phase requirements               │
│  4. Generate structured verification report                    │
│                                                                │
│  The agent does NOT self-assess. The Judge decides.            │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    REFLECT      │
                    │  Update state,  │
                    │  persist memory │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
               Pass │                 │ Fail
                    ▼                 ▼
           ┌─────────────┐    ┌─────────────┐
           │  PROCEED    │    │   RECOVER   │
           │  Next phase │    │  (SHIELDA)  │
           └─────────────┘    └─────────────┘
```

---

## Part 3: Core Components

### 3.1 Agent Harness

The Agent Harness is the new layer that enables autonomous operation.

#### 3.1.1 Session Manager

Manages discrete "work sessions" following the Initializer-Worker pattern.

```python
@dataclass
class AgentSession:
    """A single work session for the agent."""
    session_id: str
    task_id: str
    workflow: str                    # "spec", "tdflow", "bugfix"
    phase: str                       # Current workflow phase
    attempt: int                     # Attempt number for current phase
    context_budget: int              # Token budget for this session
    started_at: datetime
    
    # Externalized state (survives session boundaries)
    state_file: Path                 # .agentforge/sessions/{id}/state.yaml
    artifacts_dir: Path              # .agentforge/sessions/{id}/artifacts/
    
    def checkpoint(self):
        """Save state for potential continuation."""
        pass
    
    def can_continue(self) -> bool:
        """Check if session has budget remaining."""
        pass
```

**Session Lifecycle:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SESSION LIFECYCLE                                │
│                                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌───────┐  │
│  │ ORIENT  │───>│ EXECUTE │───>│ VERIFY  │───>│ PERSIST │───>│ YIELD │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └───────┘  │
│       │              │              │              │              │      │
│       │              │              │              │              │      │
│   Read state    Run phase      AgentForge     Save to      Clear        │
│   artifacts     (LLM call)     checks         artifacts    context      │
│                                                             window      │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Memory System

Four-tier memory architecture:

```yaml
# Tier 1: Session Memory (ephemeral - cleared each session)
session_memory:
  current_thought: "Working on implementing OrderService"
  scratch_notes: "Tried approach A, failed due to..."
  token_count: 4523

# Tier 2: Task Memory (persistent across sessions for a task)
task_memory:
  task_id: "feature-order-discount"
  feature_list:
    - id: "discount-calc"
      status: "in_progress"
      attempts: 2
    - id: "discount-rules"
      status: "pending"
  progress_log:
    - session: 1
      completed: "Wrote failing tests for discount calculation"
    - session: 2
      completed: "Implemented basic discount logic, tests now passing"

# Tier 3: Project Memory (persistent for the project)
project_memory:
  codebase_profile: ".agentforge/codebase_profile.yaml"
  contracts: "contracts/*.contract.yaml"
  learned_patterns:
    - pattern: "Always use Result<T> for service methods"
      confidence: 0.95
      learned_from: ["task-123", "task-145"]

# Tier 4: Organizational Memory (persistent across projects)
org_memory:
  failure_modes:
    - type: "circular_dependency"
      frequency: 12
      recovery: "Extract interface to break cycle"
  best_practices:
    - domain: "clean_architecture"
      rules: ["Domain has no external dependencies"]
```

#### 3.1.3 Recovery Strategies (SHIELDA-Based)

```yaml
recovery_strategies:
  # Level 1: Simple retry with feedback
  simple_retry:
    triggers:
      - compile_error
      - single_test_failure
      - lint_violation
    max_attempts: 3
    actions:
      - inject_error_into_context
      - retry_same_phase

  # Level 2: Context enrichment
  context_enrichment:
    triggers:
      - repeated_same_error
      - architectural_violation
      - pattern_mismatch
    max_attempts: 2
    actions:
      - retrieve_related_code
      - add_pattern_examples
      - retry_same_phase

  # Level 3: Approach pivot
  approach_pivot:
    triggers:
      - 5_consecutive_failures
      - incompatible_requirements
    actions:
      - summarize_failed_approaches
      - request_alternative_strategy
      - clear_implementation_artifacts
      - retry_from_planning

  # Level 4: Task decomposition
  decomposition:
    triggers:
      - task_too_complex
      - multiple_unrelated_failures
    actions:
      - analyze_failure_patterns
      - propose_subtasks
      - queue_subtasks
      - mark_parent_blocked

  # Level 5: Human escalation
  human_escalation:
    triggers:
      - decomposition_failed
      - security_concern
      - ambiguous_requirement
    actions:
      - generate_escalation_report
      - preserve_all_context
      - notify_human
      - await_human_input

  # Level 6: Graceful abort
  graceful_abort:
    triggers:
      - human_requests_abort
      - impossible_constraint
      - resource_exhaustion
    actions:
      - document_failure_reason
      - rollback_partial_changes
      - archive_session
      - mark_task_failed
```

#### 3.1.4 Self-Monitoring

Detects agent pathologies:

```python
class AgentMonitor:
    """Detects problematic agent behaviors."""
    
    def detect_loop(self, recent_actions: list) -> bool:
        """Detect if agent is in a loop (same action 3+ times)."""
        if len(recent_actions) < 3:
            return False
        return len(set(recent_actions[-3:])) == 1
    
    def detect_drift(self, current_focus: str, original_task: str) -> float:
        """Measure semantic distance from original task."""
        # Returns 0.0 (on-track) to 1.0 (completely drifted)
        pass
    
    def detect_thrashing(self, file_changes: list) -> bool:
        """Detect if agent is repeatedly changing same lines."""
        pass
    
    def get_health(self) -> AgentHealth:
        """Overall agent health assessment."""
        return AgentHealth(
            loop_detected=self.detect_loop(...),
            drift_score=self.detect_drift(...),
            thrashing_detected=self.detect_thrashing(...),
            context_pressure=self.context_usage / self.context_budget,
            recommendation="continue" | "checkpoint" | "escalate"
        )
```

### 3.2 Tool Selection (Phase-Appropriate Tooling)

**The Problem:** Giving an agent 50 tools creates decision paralysis and increases error rate.

**The Solution:** Agents receive only the tools appropriate for their current workflow phase.

```yaml
# Tool profiles per workflow phase

spec_workflow_tools:
  intake:
    - file_read           # Read codebase
    - directory_list      # Understand structure
    - search_code         # Find patterns
    - write_yaml          # Produce intake record
    
  clarify:
    - file_read
    - ask_user            # Request clarification
    - write_yaml          # Update clarification log
    
  analyze:
    - file_read
    - search_code
    - parse_ast           # Understand code structure
    - discover_patterns   # Run AgentForge discovery
    - write_yaml          # Produce analysis report
    
  draft:
    - file_read
    - write_markdown      # Write specification
    - write_code          # Write interface definitions
    
  validate:
    - conformance_check   # AgentForge conformance
    - write_yaml          # Produce validation report

tdflow_tools:
  red:
    - file_read
    - write_test          # Create test file
    - run_test            # Verify tests fail
    
  green:
    - file_read
    - write_code          # Create implementation
    - run_test            # Verify tests pass
    - conformance_check   # Check patterns followed
    
  refactor:
    - file_read
    - modify_code         # Refactor implementation
    - run_test            # Verify still passing
    - conformance_check   # Check patterns followed
```

**Implementation:**

```python
class ToolSelector:
    """Provides phase-appropriate tooling."""
    
    def __init__(self, tool_profiles: dict):
        self.profiles = tool_profiles
    
    def get_tools_for_phase(
        self, 
        workflow: str, 
        phase: str,
        domain: str
    ) -> list[Tool]:
        """Get tools appropriate for current context."""
        base_tools = self.profiles[workflow][phase]
        domain_tools = self.get_domain_tools(domain)
        return self.merge_tools(base_tools, domain_tools)
    
    def get_domain_tools(self, domain: str) -> list[Tool]:
        """Get domain-specific tools (e.g., dotnet, pytest)."""
        if domain == "dotnet":
            return [
                Tool("dotnet_build", "Compile .NET project"),
                Tool("dotnet_test", "Run .NET tests"),
                Tool("dotnet_format", "Format .NET code"),
            ]
        elif domain == "python":
            return [
                Tool("pytest", "Run Python tests"),
                Tool("ruff_check", "Lint Python code"),
                Tool("ruff_format", "Format Python code"),
            ]
        # ... more domains
```

### 3.3 Domain Specialization

Agents specialize based on discovered project characteristics.

#### 3.3.1 Domain Profile Generation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOMAIN SPECIALIZATION FLOW                            │
│                                                                          │
│   ┌─────────────┐                                                        │
│   │   Project   │                                                        │
│   │   Source    │                                                        │
│   └──────┬──────┘                                                        │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐     ┌─────────────────────────────────────────────┐   │
│   │  AgentForge │────>│            codebase_profile.yaml            │   │
│   │  Discovery  │     │                                             │   │
│   │  (Chunk 4)  │     │  language: csharp                           │   │
│   └─────────────┘     │  framework: aspnet                          │   │
│                       │  architecture: clean_architecture           │   │
│                       │  patterns:                                  │   │
│                       │    - cqrs: {confidence: 0.92, impl: mediatr}│   │
│                       │    - repository: {confidence: 0.88}         │   │
│                       │    - result_pattern: {confidence: 0.95}     │   │
│                       │  structure:                                 │   │
│                       │    layers: [Domain, Application, Infra, Api]│   │
│                       └──────────────────────┬──────────────────────┘   │
│                                              │                          │
│                                              ▼                          │
│   ┌─────────────┐     ┌─────────────────────────────────────────────┐   │
│   │  AgentForge │────>│           contracts/*.contract.yaml         │   │
│   │   Bridge    │     │                                             │   │
│   │  (Chunk 5)  │     │  - patterns.contract.yaml                   │   │
│   └─────────────┘     │  - architecture.contract.yaml               │   │
│                       │  - naming.contract.yaml                     │   │
│                       └──────────────────────┬──────────────────────┘   │
│                                              │                          │
│                                              ▼                          │
│                       ┌─────────────────────────────────────────────┐   │
│                       │           Agent Domain Profile               │   │
│                       │                                             │   │
│                       │  - Language: C# (.NET 8)                    │   │
│                       │  - Tools: dotnet build/test/format          │   │
│                       │  - Patterns to follow: CQRS, Repository     │   │
│                       │  - Constraints: Domain has no deps          │   │
│                       │  - Naming: PascalCase, I-prefix interfaces  │   │
│                       │  - Error handling: Result<T> pattern        │   │
│                       └─────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Context Injection

Domain profile injects constraints into every agent context:

```yaml
# Constitution layer (always present, ~500 tokens)
constitution:
  project: "OrderService"
  language: "C# 12 / .NET 8"
  architecture: "Clean Architecture"
  
  mandatory_patterns:
    - name: "Result<T>"
      description: "All service methods return Result<T>, never throw for business logic"
      example: "public Result<Order> CreateOrder(CreateOrderCommand cmd)"
    
    - name: "CQRS"
      description: "Commands and Queries are separate, use MediatR handlers"
      example: "public class CreateOrderCommand : IRequest<Result<Order>>"
  
  forbidden:
    - "Domain layer must not reference Infrastructure"
    - "No public fields, use properties"
    - "No async void methods"
  
  naming:
    classes: "PascalCase"
    interfaces: "I{Name}"
    private_fields: "_camelCase"
    async_methods: "{Name}Async"
```

### 3.4 Machine-Readable Context (Always)

**Every piece of context the agent receives is structured.**

#### 3.4.1 Context Assembly

```python
class ContextAssembler:
    """Assembles machine-readable context for agent."""
    
    def assemble(
        self,
        task: Task,
        phase: str,
        attempt: int,
        error_context: Optional[ErrorContext]
    ) -> AgentContext:
        """Build structured context for agent."""
        
        context = AgentContext()
        
        # Layer 1: Constitution (always, ~500 tokens)
        context.add_layer(
            "constitution",
            self.load_yaml(".agentforge/constitution.yaml"),
            priority="critical",
            max_tokens=500
        )
        
        # Layer 2: Project context (~2000 tokens)
        context.add_layer(
            "project",
            self.load_yaml(".agentforge/codebase_profile.yaml"),
            priority="high",
            max_tokens=2000
        )
        
        # Layer 3: Task context (~3000 tokens)
        context.add_layer(
            "task",
            {
                "task_id": task.id,
                "description": task.description,
                "specification": self.load_spec(task.spec_path),
                "related_code": self.retrieve_relevant_code(task),
            },
            priority="high",
            max_tokens=3000
        )
        
        # Layer 4: Phase context (~2000 tokens)
        context.add_layer(
            "phase",
            {
                "workflow": task.workflow,
                "current_phase": phase,
                "phase_requirements": self.get_phase_requirements(phase),
                "expected_outputs": self.get_expected_outputs(phase),
                "verification_criteria": self.get_verification_criteria(phase),
            },
            priority="medium",
            max_tokens=2000
        )
        
        # Layer 5: Error context (only on retry, variable)
        if error_context:
            context.add_layer(
                "error",
                {
                    "attempt_number": attempt,
                    "previous_error": error_context.error,
                    "compiler_output": error_context.compiler_output,
                    "test_failures": error_context.test_failures,
                    "suggested_fix": error_context.suggested_fix,
                },
                priority="critical",
                max_tokens=1500
            )
        
        return context.compile(max_total_tokens=10000)
```

#### 3.4.2 Artifact Bundle

All agent outputs are structured:

```yaml
# artifact_bundle.yaml - Complete record of agent work
bundle:
  id: "bundle-20251230-abc123"
  task_id: "feature-order-discount"
  created_at: "2025-12-30T15:30:00Z"
  
workflow_state:
  workflow: "tdflow"
  current_phase: "green"
  previous_phase: "red"
  attempt: 2

inputs:
  specification:
    path: "specs/order-discount.yaml"
    hash: "sha256:abc123..."
  context_snapshot:
    layers_used: ["constitution", "project", "task", "phase", "error"]
    total_tokens: 8234

outputs:
  files_created:
    - path: "src/Services/DiscountService.cs"
      hash: "sha256:def456..."
      lines: 87
      
  files_modified:
    - path: "src/Interfaces/IOrderService.cs"
      hash_before: "sha256:111..."
      hash_after: "sha256:222..."
      diff_summary: "Added CalculateDiscount method"

verification:
  # AgentForge conformance results
  conformance:
    status: "passed"
    contracts_checked: 3
    checks_run: 15
    violations: []
    
  # Build/test results
  build:
    status: "passed"
    output: "Build succeeded. 0 Warning(s). 0 Error(s)."
    
  tests:
    status: "passed"
    total: 12
    passed: 12
    failed: 0

attempt_history:
  - attempt: 1
    outcome: "tests_failed"
    error_summary: "DiscountService.CalculateDiscount returned wrong value"
    recovery: "simple_retry"
    
  - attempt: 2
    outcome: "passed"
    changes: "Fixed percentage calculation logic"

metrics:
  llm_calls: 2
  tokens_used: 18432
  duration_seconds: 45.2
```

---

## Part 4: Workflow Integration

### 4.1 The Agent Workflow Engine

Workflows define the state machine that agents follow.

```yaml
# workflows/tdflow.yaml
workflow:
  name: "tdflow"
  description: "Test-Driven Feature Development"
  
states:
  - name: "red"
    role: "test_writer"
    description: "Write failing tests that specify behavior"
    
    tools_allowed:
      - file_read
      - write_test
      - run_test
      
    inputs:
      required:
        - specification
      optional:
        - related_tests
        
    outputs:
      - test_files
      
    verification:
      - type: "compile"
        must_pass: true
      - type: "test"
        must_pass: false  # Tests MUST fail
        min_failures: 1
        
    transitions:
      tests_fail: "green"           # Correct: tests fail
      tests_pass: "red"             # Wrong: tests shouldn't pass yet
      compile_fail: "red"           # Retry with error context
      
  - name: "green"
    role: "implementer"
    description: "Write minimal code to make tests pass"
    
    tools_allowed:
      - file_read
      - write_code
      - run_test
      - conformance_check
      
    inputs:
      required:
        - specification
        - test_files
      optional:
        - related_implementations
        
    outputs:
      - implementation_files
      
    verification:
      - type: "compile"
        must_pass: true
      - type: "test"
        must_pass: true
      - type: "conformance"
        must_pass: true
        
    transitions:
      all_pass: "refactor"
      tests_fail: "green"           # Keep trying
      conformance_fail: "green"     # Fix pattern violations
      compile_fail: "green"         # Fix compilation
      
  - name: "refactor"
    role: "refactorer"
    description: "Improve code quality while maintaining behavior"
    # ... similar structure
    
  - name: "verify"
    role: "verifier"
    description: "Final verification and documentation"
    # ...
```

### 4.2 Workflow Orchestration

```python
class WorkflowOrchestrator:
    """Orchestrates agent through workflow phases."""
    
    async def run_phase(
        self,
        session: AgentSession,
        phase: WorkflowPhase
    ) -> PhaseResult:
        """Execute a single workflow phase."""
        
        # 1. Assemble context for this phase
        context = self.context_assembler.assemble(
            task=session.task,
            phase=phase.name,
            attempt=session.attempt,
            error_context=session.last_error
        )
        
        # 2. Get tools for this phase
        tools = self.tool_selector.get_tools_for_phase(
            workflow=session.workflow,
            phase=phase.name,
            domain=session.domain
        )
        
        # 3. Build prompt with structured context
        prompt = self.prompt_builder.build(
            phase=phase,
            context=context,
            tools=tools
        )
        
        # 4. Execute LLM call
        response = await self.llm.complete(
            prompt=prompt,
            tools=tools,
            max_tokens=4000
        )
        
        # 5. Process agent outputs
        outputs = self.process_outputs(response, phase)
        
        # 6. Run AgentForge verification
        verification = await self.verify_outputs(outputs, phase)
        
        # 7. Determine transition
        transition = self.determine_transition(phase, verification)
        
        return PhaseResult(
            outputs=outputs,
            verification=verification,
            transition=transition
        )
    
    async def verify_outputs(
        self,
        outputs: PhaseOutputs,
        phase: WorkflowPhase
    ) -> VerificationResult:
        """Run AgentForge verification."""
        
        results = []
        
        for check in phase.verification:
            if check.type == "compile":
                result = await self.runner.compile()
            elif check.type == "test":
                result = await self.runner.test()
            elif check.type == "conformance":
                result = await self.conformance_checker.run()
            
            results.append(CheckResult(
                check=check,
                passed=self.evaluate_check(result, check),
                output=result
            ))
        
        return VerificationResult(
            checks=results,
            overall_passed=all(r.passed for r in results if r.check.must_pass)
        )
```

---

## Part 5: Human-in-the-Loop Integration

### 5.1 Escalation Triggers

```yaml
human_escalation:
  automatic_triggers:
    # Capability limits
    - condition: "recovery_attempts > 5"
      message: "Agent stuck after 5 recovery attempts"
      
    # Ambiguity
    - condition: "spec_ambiguity_score > 0.7"
      message: "Specification has unresolved ambiguities"
      
    # Security
    - condition: "action_requires_approval"
      actions: ["git_push", "deploy", "delete_file"]
      message: "Action requires human approval"
      
    # Drift detection
    - condition: "drift_score > 0.5"
      message: "Agent appears to have drifted from original task"

  manual_triggers:
    - command: "ask_user"
      description: "Agent explicitly requests human input"
```

### 5.2 Human Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENTFORGE DASHBOARD                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ACTIVE AGENTS                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Agent-001   │ SPEC/ANALYZE  │ ████████░░ 80% │ 🟢 Healthy              │ │
│  │ Agent-002   │ TDFLOW/GREEN  │ ██████████ 100% │ ⚠️ Needs Approval      │ │
│  │ Agent-003   │ TDFLOW/RED    │ ██░░░░░░░░ 20% │ 🔴 Escalated            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  PENDING APPROVALS                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ [APPROVE] [REJECT] Agent-002 wants to: git push to feature branch      │ │
│  │           Preview: 3 files changed, 127 insertions, 12 deletions       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ESCALATIONS                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Agent-003: STUCK - 5 failed attempts implementing OrderService         │ │
│  │                                                                        │ │
│  │ Summary: Tests expect decimal precision but implementation uses float  │ │
│  │                                                                        │ │
│  │ Options:                                                               │ │
│  │   [1] Provide guidance: ____________________                           │ │
│  │   [2] Take over manually                                               │ │
│  │   [3] Decompose into subtasks                                          │ │
│  │   [4] Abort task                                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  COMPLETED TODAY                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ✅ feature-user-auth    │ TDFLOW │ 3 sessions │ 2.1 hours │ 0 issues   │ │
│  │ ✅ bugfix-null-check    │ BUGFIX │ 1 session  │ 0.3 hours │ 0 issues   │ │
│  │ ⚠️ feature-reporting   │ SPEC   │ 2 sessions │ 1.5 hours │ 1 warning  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Human Override Interface

Humans can directly edit agent state:

```bash
# View agent state
agentforge agent status agent-003

# Inject guidance
agentforge agent guide agent-003 "Use decimal type, not float, for currency"

# Edit task memory directly
agentforge agent edit agent-003 --file task_memory.yaml

# Force phase transition
agentforge agent transition agent-003 --to green

# Abort with documentation
agentforge agent abort agent-003 --reason "Requirements changed"
```

---

## Part 6: MCP Integration

AgentForge becomes an MCP server that other agents can use.

### 6.1 AgentForge as Correctness Oracle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL AGENT (Claude Desktop, etc.)                   │
│                                                                              │
│  "I wrote this implementation. Is it correct?"                               │
└───────────────────────────────────────────┬─────────────────────────────────┘
                                            │
                                            ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         AGENTFORGE MCP SERVER                                  │
│                                                                                │
│  Resources:                          Tools:                                    │
│  - agentforge://contracts            - conformance_check                       │
│  - agentforge://profile              - discover                                │
│  - agentforge://spec/current         - tdflow_verify                           │
│                                                                                │
│  Prompts:                                                                      │
│  - verify_implementation             "Check my code against project rules"     │
│  - review_patterns                   "What patterns should I follow?"          │
│                                                                                │
└───────────────────────────────────────────┬───────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VERIFICATION RESULT                             │
│                                                                              │
│  {                                                                           │
│    "passed": false,                                                          │
│    "violations": [                                                           │
│      {                                                                       │
│        "check": "domain-isolation",                                          │
│        "file": "src/Domain/Order.cs",                                        │
│        "line": 5,                                                            │
│        "message": "Domain imports Infrastructure.Database",                  │
│        "fix": "Use constructor injection with interface"                     │
│      }                                                                       │
│    ],                                                                        │
│    "patterns_to_follow": ["Use IOrderRepository, not DbContext directly"]   │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Multi-Agent Coordination

Multiple agents can share AgentForge as their source of truth:

```yaml
# Agent coordination via shared AgentForge state
coordination:
  project: "OrderService"
  
  agents:
    - id: "spec-agent"
      role: "specification"
      workflow: "spec"
      current_task: "feature-discount"
      status: "in_progress"
      
    - id: "impl-agent-1"
      role: "implementation"
      workflow: "tdflow"
      waiting_on: "spec-agent"  # Blocked until spec complete
      
    - id: "impl-agent-2"
      role: "implementation"
      workflow: "tdflow"
      current_task: "feature-auth"  # Independent task
      status: "in_progress"
      
    - id: "review-agent"
      role: "review"
      workflow: "review"
      waiting_on: ["impl-agent-1", "impl-agent-2"]
      
  coordination_rules:
    - "All agents use same conformance contracts"
    - "Spec must be approved before implementation starts"
    - "All implementations verified before review"
    - "Merge conflicts trigger human escalation"
```

---

## Part 7: Implementation Roadmap

### Phase 1: Agent Harness Foundation (2-3 weeks)

**Components:**
- Session Manager
- Basic Memory System (Session + Task tiers)
- Tool Selector (phase-appropriate tooling)
- Simple Recovery (retry with error context)

**Integration:**
- Connect to existing AgentForge workflows (SPEC, TDFLOW)
- Use existing conformance checking

**Deliverable:** Single agent can complete a simple TDFLOW task autonomously

### Phase 2: Self-Monitoring & Recovery (2 weeks)

**Components:**
- Agent Monitor (loop, drift, thrashing detection)
- Full SHIELDA recovery strategies
- Context enrichment on failure
- Task decomposition

**Deliverable:** Agent can recover from common failures without human intervention

### Phase 3: Human Integration (2 weeks)

**Components:**
- Escalation triggers
- Human dashboard (CLI first, web later)
- Override interface
- Approval workflows

**Deliverable:** Human can monitor, guide, and override agents

### Phase 4: Multi-Agent Coordination (3 weeks)

**Components:**
- Agent Dispatcher
- Task Queue
- Coordination rules
- Shared state management

**Deliverable:** Multiple agents can work on related tasks without conflicts

### Phase 5: MCP Server (2 weeks)

**Components:**
- Full MCP server implementation
- Resources, Tools, Prompts
- External agent integration

**Deliverable:** External agents (Claude Desktop) can use AgentForge as correctness oracle

### Phase 6: Learning & Optimization (Ongoing)

**Components:**
- Organizational Memory
- Pattern learning from successes
- Failure mode database
- Self-optimization

**Deliverable:** System improves over time based on experience

---

## Part 8: Success Criteria

### 8.1 Correctness Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code compilation rate | >95% | % of generated code that compiles |
| Test pass rate | >90% | % of generated code that passes tests |
| Conformance rate | >95% | % of code following project patterns |
| First-attempt success | >60% | % of tasks completed without retry |

### 8.2 Autonomy Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Human interventions | <20% | % of tasks requiring human help |
| Autonomous session length | >5 phases | Phases completed without intervention |
| Recovery success rate | >80% | % of failures recovered automatically |
| Task completion rate | >85% | % of tasks completed (vs. aborted) |

### 8.3 Efficiency Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Token efficiency | <50K/task | Average tokens per completed task |
| Time to completion | <1 hour | Average time for medium-complexity task |
| Context utilization | >70% | % of context that's relevant |

---

## Part 9: Key Differentiators

### 9.1 vs. Claude Code / Devin / Cursor

| Capability | Others | AgentForge Framework |
|------------|--------|---------------------|
| Deterministic verification | ❌ Self-assessment | ✅ Compiler, tests, conformance |
| Domain specialization | ❌ Generic | ✅ Auto-discovered patterns |
| Structured context | ❌ Prose prompts | ✅ Machine-readable YAML |
| Workflow enforcement | ❌ Freeform | ✅ State machine with verification |
| Recovery strategies | ❌ Retry | ✅ SHIELDA-based multi-level |
| Memory persistence | ❌ Session only | ✅ 4-tier hierarchy |

### 9.2 The Core Insight

**Other agents ask:** "Does this code look correct?"

**AgentForge agents ask:** "Do the tests pass? Does it compile? Does it follow the patterns?"

The difference is fundamental: opinion vs. verification.

---

## Appendix A: Integration with Existing AgentForge

| Existing Component | Role in Framework |
|-------------------|-------------------|
| SPEC Workflow | Requirements-first task definition |
| TDFLOW Workflow | Implementation workflow |
| Conformance Checker | Correctness verification |
| Discovery Engine | Domain profiling |
| Bridge | Pattern-to-contract generation |
| CI/CD Integration | Baseline comparison, output formats |
| Contracts | Machine-readable rules |

**No existing components need modification.** The Agent Harness sits above them.

---

## Appendix B: Research References

1. **Initializer-Worker Pattern** - Long-running autonomy through externalized state
2. **SHIELDA Framework** - Structured exception handling for agents
3. **MCP** - Universal tool integration
4. **Progressive Disclosure** - Hierarchical context loading
5. **Anthropic Agent SDK** - Best practices for Claude agents
6. **Context Engineering** - Anthropic's research on effective context

---

## Conclusion

AgentForge already solves the hard problem: **correctness verification**. What's needed is the orchestration layer that enables autonomous operation while leveraging AgentForge's verification capabilities.

The proposed architecture:
1. **Preserves all existing AgentForge functionality**
2. **Adds autonomous capabilities through a new Agent Harness layer**
3. **Maintains correctness-first philosophy throughout**
4. **Enables gradual adoption (start with single agent, grow to multi-agent)**

The result is an AI agent framework where **autonomy serves correctness**, not the other way around.
