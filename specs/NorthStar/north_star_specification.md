# AgentForge North Star Design Specification

**Version:** 1.0  
**Status:** Reference Architecture  
**Date:** 2025-12-31  

---

## Executive Summary

AgentForge is **autonomous software development infrastructure** that removes the human bottleneck from software development by creating a trust infrastructure where verified processes replace manual review.

### The Vision

```bash
agentforge start "Add OAuth2 authentication to the API"
```

User walks away. Days later, the work is done—fully tested, conformance verified, complete audit trail. Human intervention only if the system encounters genuine ambiguity or failure.

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **Trust the process, not the output** | Verification at every stage makes review unnecessary |
| **Human as escalation target, not gatekeeper** | Autonomous by default, human when needed |
| **Verified input → Constrained process → Verified output** | Every stage boundary is validated |
| **Complete auditability** | Every decision recorded, replayable, provable |

---

## Part 1: System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                         AGENTFORGE SYSTEM                                    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      PIPELINE CONTROLLER                                │ │
│  │                                                                         │ │
│  │   Entry Point: agentforge start "user request"                         │ │
│  │   Exit Point:  Verified, tested, delivered code                        │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        VERIFICATION CHAIN                               │ │
│  │                                                                         │ │
│  │  INTAKE ──▶ CLARIFY ──▶ ANALYZE ──▶ SPEC ──▶ RED ──▶ GREEN ──▶ DELIVER │ │
│  │    │          │           │          │        │        │          │     │ │
│  │    ▼          ▼           ▼          ▼        ▼        ▼          ▼     │ │
│  │  [yaml]    [yaml]      [yaml]     [yaml]   [yaml]   [yaml]     [yaml]  │ │
│  │  verified  verified    verified   verified verified verified   verified │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                       EXECUTION ENGINE                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │   Minimal   │  │    State    │  │    Tool     │  │  Escalation │   │ │
│  │  │   Context   │  │    Store    │  │   Bridge    │  │   Manager   │   │ │
│  │  │  Executor   │  │             │  │             │  │             │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      TRUST INFRASTRUCTURE                               │ │
│  │                                                                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  Contracts   │  │ Conformance  │  │    Audit     │                  │ │
│  │  │   System     │  │    Engine    │  │    Trail     │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Overview

| Component | Purpose | Status |
|-----------|---------|--------|
| **Pipeline Controller** | Orchestrates full request→delivery lifecycle | Design |
| **Verification Chain** | Validates artifacts at each stage boundary | Partial |
| **Minimal Context Executor** | Stateless LLM execution with bounded context | Design |
| **State Store** | Persists task state to disk | Design |
| **Tool Bridge** | Connects agents to executable tools | Built |
| **Escalation Manager** | Routes blockers to humans | Built |
| **Contracts System** | Defines and validates artifact schemas | Built |
| **Conformance Engine** | Verifies code meets contracts | Built |
| **Audit Trail** | Records every decision for replay | Design |

---

## Part 2: The Verification Chain

### 2.1 Pipeline Stages

Every request flows through a defined sequence of stages. Each stage:
- Receives **verified input** (validated against contract)
- Executes within **defined constraints**
- Produces **verified output** (validated against contract)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   USER REQUEST                                                               │
│   "Add OAuth2 authentication to the API"                                    │
│                                                                              │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────┐                                                           │
│   │   INTAKE    │  Extract structured information from request              │
│   │             │  Output: IntakeRecord.yaml                                │
│   └─────────────┘  Contract: intake_record                                  │
│         │                                                                    │
│         ▼ (verified)                                                         │
│   ┌─────────────┐                                                           │
│   │   CLARIFY   │  Resolve ambiguities (auto + escalation)                  │
│   │             │  Output: ClarificationResult.yaml                         │
│   └─────────────┘  Contract: clarification                                  │
│         │                                                                    │
│         ▼ (verified)                                                         │
│   ┌─────────────┐                                                           │
│   │   ANALYZE   │  Understand codebase context and constraints              │
│   │             │  Output: AnalysisResult.yaml                              │
│   └─────────────┘  Contract: analysis                                       │
│         │                                                                    │
│         ▼ (verified)                                                         │
│   ┌─────────────┐                                                           │
│   │    SPEC     │  Create detailed implementation specification             │
│   │             │  Output: Specification.yaml                               │
│   └─────────────┘  Contract: specification                                  │
│         │                                                                    │
│         ▼ (verified)                                                         │
│   ┌─────────────┐                                                           │
│   │    RED      │  Generate failing tests from spec                         │
│   │             │  Output: TestSuite                                        │
│   └─────────────┘  Contract: test_suite                                     │
│         │                                                                    │
│         ▼ (verified)                                                         │
│   ┌─────────────┐                                                           │
│   │   GREEN     │  Implement to pass tests                                  │
│   │             │  Output: Implementation                                   │
│   └─────────────┘  Contract: implementation                                 │
│         │                                                                    │
│         ▼ (verified)                                                         │
│   ┌─────────────┐                                                           │
│   │  REFACTOR   │  Clean up, verify conformance                             │
│   │             │  Output: FinalDeliverable                                 │
│   └─────────────┘  Contract: deliverable                                    │
│         │                                                                    │
│         ▼ (verified)                                                         │
│   ┌─────────────┐                                                           │
│   │  DELIVER    │  Commit, document, report                                 │
│   │             │  Output: DeliveryReport.yaml                              │
│   └─────────────┘  Contract: delivery_report                                │
│         │                                                                    │
│         ▼                                                                    │
│   COMPLETED WORK                                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stage Contracts

Each stage boundary is defined by a contract specifying the exact schema of artifacts passed between stages.

#### IntakeRecord Contract

```yaml
contract: intake_record
version: "1.0"
description: Output of intake stage

schema:
  request_id:
    type: string
    required: true
    
  original_request:
    type: string
    required: true
    description: Verbatim user request
    
  extracted_intent:
    type: object
    required: true
    properties:
      action:
        type: string
        enum: [create, modify, delete, refactor, fix, analyze]
      target:
        type: string
        description: What is being acted upon
      scope:
        type: string
        enum: [file, module, feature, system]
        
  initial_complexity:
    type: string
    enum: [trivial, simple, moderate, complex, epic]
    
  identified_ambiguities:
    type: array
    items:
      type: object
      properties:
        area:
          type: string
        question:
          type: string
        impact:
          type: string
          enum: [blocking, significant, minor]
          
  suggested_approach:
    type: string
    
  metadata:
    type: object
    properties:
      intake_timestamp:
        type: string
        format: datetime
      tokens_used:
        type: integer
```

#### Specification Contract

```yaml
contract: specification
version: "1.0"
description: Verified implementation specification

schema:
  spec_id:
    type: string
    required: true
    
  title:
    type: string
    required: true
    max_length: 100
    
  description:
    type: string
    required: true
    
  requirements:
    type: array
    required: true
    min_items: 1
    items:
      type: object
      properties:
        id:
          type: string
          pattern: "^REQ-[0-9]{3}$"
        description:
          type: string
          required: true
        priority:
          type: string
          enum: [must, should, could, wont]
        acceptance_criteria:
          type: array
          min_items: 1
          items:
            type: string
        verification_method:
          type: string
          enum: [test, inspection, analysis, demonstration]
          
  constraints:
    type: array
    items:
      type: object
      properties:
        id:
          type: string
        description:
          type: string
        rationale:
          type: string
          
  interfaces:
    type: array
    items:
      type: object
      properties:
        name:
          type: string
        type:
          type: string
          enum: [api, event, file, database]
        direction:
          type: string
          enum: [input, output, bidirectional]
        contract_ref:
          type: string
          
  files_to_modify:
    type: array
    items:
      type: string
      
  files_to_create:
    type: array
    items:
      type: string
      
  dependencies:
    type: array
    items:
      type: string
      
  estimated_complexity:
    type: string
    enum: [trivial, simple, moderate, complex, epic]
    
  trace_to_request:
    type: string
    description: How this spec addresses the original request

validation:
  - every requirement has at least one acceptance criterion
  - all file paths are valid relative paths
  - no circular dependencies
```

#### TestSuite Contract

```yaml
contract: test_suite
version: "1.0"
description: Output of RED phase - failing tests

schema:
  suite_id:
    type: string
    required: true
    
  spec_ref:
    type: string
    required: true
    description: Reference to specification this tests
    
  test_files:
    type: array
    required: true
    min_items: 1
    items:
      type: object
      properties:
        path:
          type: string
          required: true
        tests:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              requirement_ref:
                type: string
                pattern: "^REQ-[0-9]{3}$"
              acceptance_criterion:
                type: string
                
  coverage_mapping:
    type: object
    description: Maps requirements to tests
    additionalProperties:
      type: array
      items:
        type: string
        
  verification:
    type: object
    properties:
      all_tests_fail:
        type: boolean
        required: true
        const: true
      no_implementation_exists:
        type: boolean
        required: true
        const: true

validation:
  - every requirement in spec has at least one test
  - all tests currently fail (verified by execution)
```

#### Implementation Contract

```yaml
contract: implementation
version: "1.0"
description: Output of GREEN phase

schema:
  implementation_id:
    type: string
    required: true
    
  spec_ref:
    type: string
    required: true
    
  test_suite_ref:
    type: string
    required: true
    
  files_created:
    type: array
    items:
      type: object
      properties:
        path:
          type: string
        purpose:
          type: string
        lines:
          type: integer
          
  files_modified:
    type: array
    items:
      type: object
      properties:
        path:
          type: string
        changes_summary:
          type: string
        lines_added:
          type: integer
        lines_removed:
          type: integer
          
  verification:
    type: object
    properties:
      all_tests_pass:
        type: boolean
        required: true
        const: true
      conformance_passing:
        type: boolean
        required: true
        const: true
      no_regressions:
        type: boolean
        required: true
        const: true

validation:
  - all tests from test_suite now pass
  - conformance checks pass
  - no existing tests broken
```

### 2.3 Stage Verification

Each stage transition includes verification:

```python
class StageVerifier:
    """Verifies artifacts at stage boundaries."""
    
    def verify_transition(
        self,
        from_stage: str,
        to_stage: str,
        artifact: dict
    ) -> VerificationResult:
        """
        Verify artifact is valid for stage transition.
        
        Returns:
            VerificationResult with pass/fail and details
        """
        contract = self.get_contract_for_transition(from_stage, to_stage)
        
        # Schema validation
        schema_result = self.validate_schema(artifact, contract.schema)
        if not schema_result.valid:
            return VerificationResult(
                passed=False,
                stage=f"{from_stage}->{to_stage}",
                errors=schema_result.errors
            )
        
        # Custom validation rules
        for rule in contract.validation:
            rule_result = self.evaluate_rule(rule, artifact)
            if not rule_result.passed:
                return VerificationResult(
                    passed=False,
                    stage=f"{from_stage}->{to_stage}",
                    errors=[rule_result.error]
                )
        
        # All passed
        return VerificationResult(
            passed=True,
            stage=f"{from_stage}->{to_stage}",
            artifact_hash=self.hash_artifact(artifact)
        )
```

---

## Part 3: Minimal Context Architecture

### 3.1 The Problem

Naive conversation accumulation causes:
- **Unbounded growth**: Each step adds tokens, eventually hitting limits
- **Rate limit failures**: 48K+ tokens/minute exceeds API limits
- **Cost explosion**: Later steps cost 10x more than early steps
- **Multi-day impossibility**: Can't maintain context across sessions

### 3.2 The Solution

**Stateless steps with verified state.** Each step:
1. Reads current state from disk
2. Builds minimal context (4-8K tokens, always)
3. Makes single LLM call (2 messages: system + context)
4. Executes action
5. Updates state on disk

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   EVERY STEP IS A FRESH CONVERSATION                                        │
│                                                                              │
│   Step 1:  [System] + [Context from state]  →  6K tokens                    │
│   Step 10: [System] + [Context from state]  →  6K tokens                    │
│   Step 100: [System] + [Context from state] →  6K tokens                    │
│                                                                              │
│   Context is CONSTANT, not growing                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 State Store Structure

```
.agentforge/tasks/{task_id}/
├── task.yaml                 # Immutable: goal, success criteria
├── state.yaml                # Mutable: current phase, status
├── actions.yaml              # Append-only: complete audit trail
├── working_memory.yaml       # Rolling: last N items for context
└── artifacts/
    ├── inputs/               # Verified inputs to this task
    ├── outputs/              # Verified outputs from each phase
    └── snapshots/            # File states before/after changes
```

### 3.4 Context Schema

Each step receives a fixed-structure context:

```yaml
# Target: 4-8K tokens regardless of step number

task_frame:                    # ~500 tokens, constant
  id: "{task_id}"
  goal: "Single sentence description"
  success_criteria:
    - "Criterion 1"
    - "Criterion 2"
  phase: "current_phase"
  constraints:
    - "Constraint 1"

current_state:                 # ~3-5K tokens, bounded
  # Phase-specific content
  # Truncated/summarized to fit budget

recent_actions:                # ~500-1K tokens, last 3 only
  - step: 7
    action: "edit_file"
    result: "success"
    summary: "What happened"

verification_status:           # ~200 tokens
  checks_passing: 3
  checks_failing: 2
  ready_for_completion: false

available_actions:             # ~500 tokens
  - name: "action_name"
    description: "What it does"
```

### 3.5 Token Budget Enforcement

```python
TOKEN_BUDGET = {
    "system_prompt": 1000,
    "task_frame": 500,
    "current_state": 4500,
    "recent_actions": 1000,
    "verification_status": 200,
    "available_actions": 800,
    # Total: 8000 max
}
```

Compression strategies:
- **Files**: First/last N lines, middle omitted
- **Actions**: Keep only last 3
- **Tool results**: Summarize to single line
- **Errors**: Truncate to 500 chars

### 3.6 Step Execution Flow

```python
class MinimalContextExecutor:
    def execute_step(self, task_id: str) -> StepResult:
        # 1. Load state from disk (not from conversation)
        state = self.state_store.load(task_id)
        
        # 2. Build minimal context (always 4-8K tokens)
        context = self.context_builder.build(state)
        
        # 3. Single LLM call - fresh conversation
        response = self.llm.generate(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context}
            ]
        )
        
        # 4. Parse and execute action
        action = self.parse_action(response)
        result = self.execute_action(action)
        
        # 5. Update state on disk
        self.state_store.update(task_id, action, result)
        
        # 6. Check completion
        return self.evaluate_completion(state)
```

---

## Part 4: Pipeline Controller

### 4.1 Single Entry Point

The entire system is accessed through one command:

```bash
agentforge start "user request here"
```

This triggers the full pipeline autonomously.

### 4.2 Pipeline Controller Design

```python
class PipelineController:
    """
    Orchestrates full request→delivery lifecycle.
    Human intervention only on escalation.
    """
    
    def __init__(
        self,
        project_path: Path,
        escalation_handler: EscalationHandler,
        supervised: bool = False
    ):
        self.project_path = project_path
        self.escalation_handler = escalation_handler
        self.supervised = supervised
        
        # Initialize stage executors
        self.stages = {
            "intake": IntakeExecutor(),
            "clarify": ClarifyExecutor(),
            "analyze": AnalyzeExecutor(),
            "spec": SpecExecutor(),
            "red": RedPhaseExecutor(),
            "green": GreenPhaseExecutor(),
            "refactor": RefactorExecutor(),
            "deliver": DeliverExecutor(),
        }
        
        self.verifier = StageVerifier()
        self.state_store = StateStore(project_path / ".agentforge" / "tasks")
    
    def execute(self, user_request: str) -> PipelineResult:
        """
        Execute full pipeline from request to delivery.
        
        This is THE entry point. Everything flows from here.
        """
        # Create task
        task_id = self.state_store.create_task(user_request)
        
        # Define stage sequence
        stage_sequence = [
            "intake", "clarify", "analyze", "spec",
            "red", "green", "refactor", "deliver"
        ]
        
        current_artifact = {"original_request": user_request}
        
        for stage_name in stage_sequence:
            # Execute stage
            result = self._execute_stage(
                task_id=task_id,
                stage=stage_name,
                input_artifact=current_artifact
            )
            
            if result.escalated:
                # Wait for human resolution
                resolution = self.escalation_handler.wait_for_resolution(
                    task_id=task_id,
                    stage=stage_name,
                    issue=result.escalation_reason
                )
                
                if resolution.abort:
                    return PipelineResult(success=False, reason="User aborted")
                
                # Retry with resolution context
                result = self._execute_stage(
                    task_id=task_id,
                    stage=stage_name,
                    input_artifact=current_artifact,
                    resolution=resolution
                )
            
            if not result.success:
                return PipelineResult(
                    success=False,
                    stage=stage_name,
                    error=result.error
                )
            
            # Verify output
            verification = self.verifier.verify_transition(
                from_stage=stage_name,
                to_stage=self._next_stage(stage_name),
                artifact=result.artifact
            )
            
            if not verification.passed:
                # Agent attempts to fix, escalates if can't
                result = self._resolve_verification_failure(
                    task_id, stage_name, verification
                )
                
                if not result.success:
                    return PipelineResult(
                        success=False,
                        stage=stage_name,
                        error=f"Verification failed: {verification.errors}"
                    )
            
            # Supervised mode: pause for human approval
            if self.supervised:
                approval = self.escalation_handler.request_approval(
                    task_id=task_id,
                    stage=stage_name,
                    artifact=result.artifact
                )
                if not approval.approved:
                    return PipelineResult(success=False, reason="User rejected")
            
            # Move to next stage
            current_artifact = result.artifact
        
        return PipelineResult(
            success=True,
            task_id=task_id,
            deliverable=current_artifact
        )
    
    def _execute_stage(
        self,
        task_id: str,
        stage: str,
        input_artifact: dict,
        resolution: Optional[Resolution] = None
    ) -> StageResult:
        """Execute a single stage."""
        executor = self.stages[stage]
        
        # Run until stage completes or escalates
        while True:
            step_result = executor.execute_step(
                task_id=task_id,
                input_artifact=input_artifact,
                resolution=resolution
            )
            
            if step_result.stage_complete:
                return step_result
            
            if step_result.escalate:
                return StageResult(escalated=True, reason=step_result.escalation_reason)
            
            # Continue to next step in stage
```

### 4.3 Execution Modes

```python
class ExecutionMode(Enum):
    AUTONOMOUS = "autonomous"      # Default: full auto, escalate on failure
    SUPERVISED = "supervised"      # Human approves each stage
    INTERACTIVE = "interactive"    # Human involved at every step
```

```bash
# Fully autonomous (default)
agentforge start "Add OAuth2 authentication"

# Human approves each stage
agentforge start "Add OAuth2 authentication" --supervised

# Approve only specific stages
agentforge start "Add OAuth2 authentication" --approve design --approve commit
```

### 4.4 Escalation Handling

```python
class EscalationHandler:
    """Handles human escalation when agent is stuck."""
    
    def escalate(
        self,
        task_id: str,
        stage: str,
        reason: str,
        context: dict
    ) -> None:
        """
        Escalate to human. Non-blocking - records escalation
        and waits for resolution.
        """
        escalation = Escalation(
            task_id=task_id,
            stage=stage,
            reason=reason,
            context=context,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.store.save(escalation)
        self.notifier.notify_human(escalation)
    
    def wait_for_resolution(
        self,
        task_id: str,
        timeout: Optional[timedelta] = None
    ) -> Resolution:
        """
        Wait for human to resolve escalation.
        
        In async mode, this returns immediately and pipeline
        resumes when resolution is provided.
        """
        # Poll for resolution or use webhooks
        ...
```

---

## Part 5: Audit Trail and Replay

### 5.1 Complete Audit Trail

Every task produces a complete, human-readable history:

```
.agentforge/tasks/{task_id}/
├── task.yaml                     # Original request, goal, constraints
├── state.yaml                    # Final state
├── actions.yaml                  # COMPLETE AUDIT TRAIL
├── artifacts/
│   ├── inputs/
│   │   └── original_request.yaml
│   ├── phases/
│   │   ├── intake/
│   │   │   └── intake_record.yaml    (verified)
│   │   ├── clarify/
│   │   │   └── clarification.yaml    (verified)
│   │   ├── analyze/
│   │   │   └── analysis.yaml         (verified)
│   │   ├── spec/
│   │   │   └── specification.yaml    (verified)
│   │   ├── red/
│   │   │   └── test_suite.yaml       (verified)
│   │   ├── green/
│   │   │   └── implementation.yaml   (verified)
│   │   └── deliver/
│   │       └── delivery_report.yaml  (verified)
│   └── snapshots/
│       ├── step_001.patch
│       ├── step_002.patch
│       └── ...
```

### 5.2 Actions Log Format

```yaml
# actions.yaml - Append-only, complete history

task_id: "task-20251231-oauth2-auth"
request: "Add OAuth2 authentication to the API"
started_at: "2025-12-31T10:00:00Z"
completed_at: "2025-12-31T14:32:00Z"
outcome: "success"
total_steps: 47
total_tokens: 284203
total_cost_usd: 4.26

actions:
  - step: 1
    timestamp: "2025-12-31T10:00:05Z"
    phase: "intake"
    context_tokens: 5842
    action:
      type: "analyze_request"
      input_hash: "abc123"
    result:
      status: "success"
      output_artifact: "artifacts/phases/intake/intake_record.yaml"
      output_hash: "def456"
    verification:
      passed: true
      contract: "intake_record"
    llm_call:
      model: "claude-sonnet-4-20250514"
      prompt_tokens: 5842
      completion_tokens: 1203
      
  # ... every step recorded ...
```

### 5.3 Replay Capabilities

#### Action Replay (Deterministic)

Re-execute file operations without LLM calls:

```bash
agentforge replay {task_id} --actions-only

# Useful for: Apply same changes to different branch
```

#### Fork from Checkpoint

Resume from any step with fresh agent:

```bash
agentforge fork {task_id} --from-step 23

# Useful for: Step 24 went wrong, retry from 23
```

#### Full Re-run with Comparison

Run same request again, compare paths:

```bash
agentforge start "Add OAuth2 authentication" --compare-to {task_id}

# Useful for: Is the agent consistent? Did improvements help?
```

### 5.4 Audit Commands

```bash
# Inspect context at specific step
agentforge inspect {task_id} --step 23 --show context

# Generate audit report
agentforge audit {task_id} --format pdf

# Compare two task executions
agentforge compare {task_id_1} {task_id_2}

# Show cost breakdown
agentforge cost {task_id}
```

---

## Part 6: Self-Clarification

### 6.1 Autonomous Clarification

The clarify phase doesn't require human input by default. The agent:
1. Identifies what it doesn't know
2. Attempts to answer from codebase context
3. Only escalates genuinely ambiguous items

```python
class ClarifyExecutor:
    """
    Clarify phase - autonomous by default.
    """
    
    def execute(self, task_id: str, intake: IntakeRecord) -> ClarifyResult:
        # Generate questions from ambiguities
        questions = self.generate_questions(intake)
        
        answers = []
        escalations = []
        
        for question in questions:
            # Attempt to answer from context
            answer = self.attempt_answer(question)
            
            if answer.confidence >= 0.8:
                answers.append(Answer(
                    question=question,
                    answer=answer.text,
                    source="agent_inference",
                    confidence=answer.confidence
                ))
            else:
                escalations.append(question)
        
        # Only escalate if blocking and can't proceed without
        if escalations and self.requires_human_input(escalations):
            human_answers = self.escalate_for_clarification(escalations)
            answers.extend(human_answers)
        
        return ClarifyResult(answers=answers)
```

### 6.2 Clarification Output

```yaml
# clarification.yaml

questions:
  - question: "Should OAuth2 support refresh tokens?"
    source: "agent_inference"
    answer: "Yes - existing auth patterns use refresh tokens"
    confidence: 0.92
    evidence:
      - file: "auth/token_manager.py"
        snippet: "def refresh_token(...):"
        
  - question: "Which OAuth2 providers to support?"
    source: "agent_inference"
    answer: "Google and GitHub - found in existing config"
    confidence: 0.88
    evidence:
      - file: "config/auth_providers.yaml"
        
  - question: "Should PKCE flow be required?"
    source: "human_escalation"
    answer: "Yes, PKCE required for all public clients"
    confidence: 1.0
    resolved_by: "user"
    resolved_at: "2025-12-31T10:15:00Z"
```

---

## Part 7: Multi-Repository Management

### 7.1 Repository Configuration

```yaml
# ~/.agentforge/repos.yaml

repositories:
  - name: "backend-service"
    path: "/path/to/backend"
    default_branch: "main"
    contracts_path: "contracts/"
    
  - name: "api-gateway"
    path: "/path/to/gateway"
    default_branch: "main"
    
  - name: "data-layer"
    path: "/path/to/data"
    default_branch: "develop"
```

### 7.2 Multi-Repo Commands

```bash
# Start work on specific repo
agentforge start "Add authentication" --repo backend-service

# Start work on multiple repos
agentforge start "Add rate limiting" --repo api-gateway
agentforge start "Add user analytics" --repo data-layer

# Check status across all repos
agentforge status --all

# Output:
# backend-service:  IN_PROGRESS (stage: green, 60%)
# api-gateway:      DELIVERED ✓
# data-layer:       ESCALATED (needs clarification)
```

### 7.3 Cross-Repo Dependencies

```yaml
# In specification.yaml

dependencies:
  external:
    - repo: "data-layer"
      artifact: "user_events_schema"
      version: ">=1.2.0"
      
  tasks:
    - task_id: "task-xyz-user-events"
      required_stage: "deliver"
      reason: "Need events schema before implementing analytics"
```

---

## Part 8: Trust Model

### 8.1 The Trust Equation

```
TRUST = VERIFIED_INPUTS + CONSTRAINED_PROCESS + VERIFIED_OUTPUTS
```

At every stage:
- Input is verified against contract before agent sees it
- Agent works within defined constraints (tools, scope, budget)
- Output is verified against contract before next stage sees it

### 8.2 What This Enables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   BEFORE: "Trust me, the agent did the right thing"                         │
│                                                                              │
│   AFTER:  "Here's exactly what the agent did, step by step,                 │
│            with every input it saw and every output it produced,            │
│            all verified, all auditable, all replayable."                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Human Role

| Scenario | Human Action |
|----------|--------------|
| Everything works | None required |
| Genuine ambiguity | Answer clarifying question |
| Agent stuck | Review context, provide guidance |
| Verification fails repeatedly | Investigate and fix constraints |
| Suspicious output | Audit trail review |

Human is **escalation target**, not **gatekeeper**.

---

## Part 9: Implementation Roadmap

### Phase 1: Foundation (Current)
- [x] Contract system
- [x] Conformance engine
- [x] Spec system (intake loop)
- [x] Agent harness (session, memory, tools)
- [x] LLM executor (needs refactor)
- [ ] Minimal context architecture
- [ ] State store

### Phase 2: Self-Hosting
- [ ] Fix-violation workflow
- [ ] Domain-specific tools (Python, conformance)
- [ ] Verify on own codebase

### Phase 3: Full Pipeline
- [ ] Pipeline controller
- [ ] Stage executors (red, green, refactor)
- [ ] Full verification chain
- [ ] Autonomous clarification

### Phase 4: Production
- [ ] Multi-repo support
- [ ] Audit trail and replay
- [ ] Cost tracking
- [ ] Dashboard/monitoring

---

## Part 10: Success Metrics

### System Health
- Steps per task completion
- Escalation rate (target: <5%)
- Verification pass rate (target: >95%)
- Token efficiency (tokens per successful task)

### Trust Metrics
- Rework rate (human-requested changes post-delivery)
- Defect rate (bugs found in delivered code)
- Audit trail completeness

### Productivity Metrics
- Tasks completed per week
- Repos managed simultaneously
- Human time per task (target: <5 minutes for simple tasks)

---

## Appendices

### A. Glossary

| Term | Definition |
|------|------------|
| **Stage** | A phase in the pipeline (intake, clarify, etc.) |
| **Artifact** | Verified YAML output from a stage |
| **Contract** | Schema defining valid artifact structure |
| **Verification** | Process of validating artifact against contract |
| **Escalation** | Request for human intervention |
| **State Store** | Disk-based persistence for task state |
| **Minimal Context** | Bounded token budget per step |

### B. File Locations

```
.agentforge/
├── config/
│   ├── settings.yaml         # Global settings
│   └── repos.yaml            # Repository definitions
├── contracts/                # Contract definitions
├── tasks/                    # Active and completed tasks
│   └── {task_id}/
├── violations/               # Conformance violations
├── escalations/              # Pending escalations
└── audit/                    # Audit reports
```

### C. CLI Reference

```bash
# Core commands
agentforge start "request"              # Start autonomous pipeline
agentforge status [--all]               # Check task status
agentforge resume {task_id}             # Resume paused task
agentforge abort {task_id}              # Abort task

# Escalation
agentforge escalations list             # Show pending escalations
agentforge resolve {escalation_id}      # Resolve escalation

# Audit
agentforge inspect {task_id}            # Inspect task state
agentforge audit {task_id}              # Generate audit report
agentforge replay {task_id}             # Replay task actions
agentforge fork {task_id}               # Fork from checkpoint

# Configuration
agentforge config show                  # Show configuration
agentforge repo add {path}              # Add repository
```

---

**End of Specification**
