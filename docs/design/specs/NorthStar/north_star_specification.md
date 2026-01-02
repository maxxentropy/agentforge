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

### 2.4 TDFlow with Conformance Integration

**Critical Design Point:** Conformance checking is not a separate phase—it's a continuous gate within TDFlow. The agent cannot produce code that violates contracts; violations must be fixed before proceeding.

#### 2.4.1 The Conformance Gate

Every code edit triggers a verification cycle:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                    TDFlow with Integrated Conformance                         │
│                                                                               │
│   ┌───────────────────────────────────────────────────────────────────────┐  │
│   │                            RED PHASE                                   │  │
│   │                                                                        │  │
│   │   Agent writes tests from specification                                │  │
│   │   Exit Gate: All tests fail (no implementation exists)                 │  │
│   │                                                                        │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                        │
│                                      ▼                                        │
│   ┌───────────────────────────────────────────────────────────────────────┐  │
│   │                           GREEN PHASE                                  │  │
│   │                                                                        │  │
│   │   ┌─────────────────────────────────────────────────────────────────┐ │  │
│   │   │                      EDIT → VERIFY LOOP                          │ │  │
│   │   │                                                                  │ │  │
│   │   │   Agent writes/edits code                                        │ │  │
│   │   │            │                                                     │ │  │
│   │   │            ▼                                                     │ │  │
│   │   │   ┌────────────────────────────────────────────────────────┐    │ │  │
│   │   │   │              VERIFICATION GATE                          │    │ │  │
│   │   │   │                                                         │    │ │  │
│   │   │   │   1. Syntax Check        (< 1s)   Must pass to continue │    │ │  │
│   │   │   │   2. Type Check          (1-5s)   Must pass for GREEN   │    │ │  │
│   │   │   │   3. Conformance Checks  (1-2s)   Must pass for GREEN   │    │ │  │
│   │   │   │   4. Affected Tests      (5-30s)  Must pass for GREEN   │    │ │  │
│   │   │   │                                                         │    │ │  │
│   │   │   └────────────────────────────────────────────────────────┘    │ │  │
│   │   │            │                                                     │ │  │
│   │   │            ▼                                                     │ │  │
│   │   │   All gates pass? ──No──▶ Agent sees failures, fixes, loops     │ │  │
│   │   │            │                                                     │ │  │
│   │   │           Yes                                                    │ │  │
│   │   │            │                                                     │ │  │
│   │   └────────────┼─────────────────────────────────────────────────────┘ │  │
│   │                │                                                        │  │
│   │   Exit Gate: All tests pass AND all conformance checks pass            │  │
│   │                                                                        │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                        │
│                                      ▼                                        │
│   ┌───────────────────────────────────────────────────────────────────────┐  │
│   │                          REFACTOR PHASE                                │  │
│   │                                                                        │  │
│   │   Agent improves code quality (same edit→verify loop)                  │  │
│   │   Exit Gate: Tests pass AND Conformance passes AND Quality metrics     │  │
│   │                                                                        │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 2.4.2 Contract Categories

Conformance checks enforce different categories of constraints:

```yaml
# Contract categories enforced during code generation

style_contracts:
  description: "Code formatting and naming"
  checks:
    - naming-conventions        # Variables, functions, classes follow patterns
    - documentation-required    # Docstrings on public APIs
    - import-order              # Imports organized correctly
    - line-length               # Code formatting rules
    - no-print-statements       # Use logging instead
  enforcement: every_edit
  
architecture_contracts:
  description: "Structural design rules"
  checks:
    - layer-dependencies        # Domain cannot import Infrastructure
    - no-circular-imports       # Dependency graph is acyclic
    - interface-segregation     # Layers communicate through contracts
    - bounded-contexts          # Module boundaries respected
  enforcement: every_edit
  
pattern_contracts:
  description: "Design pattern compliance"
  checks:
    - repository-pattern        # Data access follows repository pattern
    - dependency-injection      # No direct instantiation of dependencies
    - error-handling            # Exceptions follow defined patterns
    - command-query-separation  # Methods either command or query, not both
  enforcement: every_edit
  
security_contracts:
  description: "Security requirements"
  checks:
    - no-secrets-in-code        # No hardcoded credentials
    - input-validation          # All external inputs validated
    - sql-injection             # Parameterized queries only
    - auth-required             # Protected endpoints have auth
  enforcement: every_edit
  
quality_contracts:
  description: "Code quality metrics"
  checks:
    - max-complexity            # Cyclomatic complexity <= threshold
    - max-file-length           # Files under size limit
    - max-function-length       # Functions under size limit
    - no-duplicate-code         # DRY principle enforced
  enforcement: phase_end
```

#### 2.4.3 Verification Timing

Different checks run at different times based on speed and importance:

| Check Type | When | Speed | Blocking |
|------------|------|-------|----------|
| Syntax | Every edit | <1s | Immediate (can't proceed) |
| Type check (pyright) | Every edit | 1-5s | GREEN completion |
| Conformance (style) | Every edit | <1s | GREEN completion |
| Conformance (architecture) | Every edit | 1-2s | GREEN completion |
| Conformance (security) | Every edit | <1s | GREEN completion |
| Unit tests (affected) | Every edit | 5-30s | GREEN completion |
| Integration tests | Phase end | 1-5m | REFACTOR completion |
| Quality metrics | Phase end | 10-30s | REFACTOR completion |
| Full test suite | Phase end | 1-10m | DELIVER gate |

#### 2.4.4 Agent Context with Verification Status

The agent receives verification results as part of its context:

```yaml
# Context provided to agent during GREEN phase

verification_status:
  tests:
    status: "failing"
    total: 14
    passing: 12
    failing: 2
    failures:
      - test: "test_oauth_token_refresh"
        file: "tests/auth/test_oauth.py"
        line: 45
        error: "AttributeError: 'NoneType' object has no attribute 'refresh'"
        
      - test: "test_oauth_token_expiry"
        file: "tests/auth/test_oauth.py"
        line: 67
        error: "AssertionError: Expected token to be expired"
        
  conformance:
    status: "failing"
    total: 12
    passing: 11
    failing: 1
    violations:
      - check_id: "documentation-required"
        contract: "style_contracts"
        severity: "major"
        file: "auth/oauth.py"
        line: 45
        message: "Function 'refresh_token' missing docstring"
        fix_hint: "Add docstring with Args, Returns, and Raises sections"
        
  type_check:
    status: "passing"
    errors: 0
    warnings: 2
    
  syntax:
    status: "passing"

  phase_exit_ready: false
  blocking_issues:
    - "2 tests failing in test_oauth.py"
    - "1 conformance violation: missing docstring"
    
  next_suggested_action: "Add docstring to refresh_token function, then fix test failures"
```

#### 2.4.5 Phase Exit Criteria

Each TDFlow phase has explicit, verifiable exit criteria:

```yaml
# RED Phase Exit Criteria
red_phase:
  exit_criteria:
    required:
      - tests_exist: true
        description: "At least one test per requirement"
      - all_tests_fail: true
        description: "No test passes (implementation doesn't exist)"
      - tests_are_valid: true
        description: "Tests run without syntax/import errors"
    
    verification:
      - check: "tests_exist"
        method: "count_tests_per_requirement"
        threshold: ">= 1"
      - check: "all_tests_fail"
        method: "run_test_suite"
        expected: "0 passing"
      - check: "tests_are_valid"
        method: "pytest --collect-only"
        expected: "exit code 0"

# GREEN Phase Exit Criteria
green_phase:
  exit_criteria:
    required:
      - all_tests_pass: true
        description: "Every test from RED phase passes"
      - conformance_pass: true
        description: "All conformance checks pass"
      - type_check_pass: true
        description: "No type errors (warnings allowed)"
      - no_regressions: true
        description: "Existing tests still pass"
    
    verification:
      - check: "all_tests_pass"
        method: "run_test_suite"
        expected: "100% passing"
      - check: "conformance_pass"
        method: "run_conformance_checks"
        categories: ["style", "architecture", "pattern", "security"]
        expected: "0 violations"
      - check: "type_check_pass"
        method: "pyright"
        expected: "0 errors"
      - check: "no_regressions"
        method: "run_full_test_suite"
        expected: "no new failures"

# REFACTOR Phase Exit Criteria
refactor_phase:
  exit_criteria:
    required:
      - all_tests_pass: true
      - full_conformance_pass: true
        description: "All checks including quality metrics"
      - coverage_threshold: true
        description: "Code coverage meets minimum"
      - complexity_threshold: true
        description: "No function exceeds complexity limit"
    
    verification:
      - check: "coverage_threshold"
        method: "pytest --cov"
        threshold: ">= 80%"
      - check: "complexity_threshold"
        method: "radon cc"
        threshold: "<= 10"
      - check: "full_conformance_pass"
        method: "run_conformance_checks"
        categories: ["all"]
        expected: "0 violations"
```

#### 2.4.6 The Verification Loop Implementation

```python
class GreenPhaseExecutor:
    """
    Executes GREEN phase with integrated conformance checking.
    Agent cannot exit phase until all gates pass.
    """
    
    def execute_step(self, task_id: str, state: TaskState) -> StepResult:
        # Get agent's action
        action = self.get_agent_action(state)
        
        if action.type == "edit_file":
            # Execute the edit
            edit_result = self.execute_edit(action)
            
            if not edit_result.success:
                return StepResult(
                    success=False,
                    error=edit_result.error
                )
            
            # IMMEDIATELY run verification
            verification = self.run_verification_gate(action.file_path)
            
            # Update state with verification results
            state.verification_status = verification
            
            if not verification.all_passed:
                # Agent will see failures in next step's context
                return StepResult(
                    success=True,  # Edit succeeded, but phase not complete
                    phase_complete=False,
                    verification=verification
                )
        
        # Check if phase can exit
        if self.check_phase_exit_criteria(state):
            return StepResult(
                success=True,
                phase_complete=True,
                artifact=self.build_phase_artifact(state)
            )
        
        return StepResult(success=True, phase_complete=False)
    
    def run_verification_gate(self, file_path: str) -> VerificationResult:
        """Run all verification checks on modified file."""
        
        result = VerificationResult()
        
        # 1. Syntax check (fast fail)
        syntax = self.check_syntax(file_path)
        result.add("syntax", syntax)
        if not syntax.passed:
            return result  # Stop here, syntax must pass
        
        # 2. Type check
        type_check = self.run_type_check(file_path)
        result.add("type_check", type_check)
        
        # 3. Conformance checks (your contracts!)
        for category in ["style", "architecture", "pattern", "security"]:
            conformance = self.run_conformance_checks(file_path, category)
            result.add(f"conformance_{category}", conformance)
        
        # 4. Affected tests
        tests = self.run_affected_tests(file_path)
        result.add("tests", tests)
        
        return result
    
    def check_phase_exit_criteria(self, state: TaskState) -> bool:
        """Check if all GREEN phase exit criteria are met."""
        v = state.verification_status
        
        return (
            v.get("syntax", {}).get("passed", False) and
            v.get("type_check", {}).get("passed", False) and
            v.get("conformance_style", {}).get("passed", False) and
            v.get("conformance_architecture", {}).get("passed", False) and
            v.get("conformance_pattern", {}).get("passed", False) and
            v.get("conformance_security", {}).get("passed", False) and
            v.get("tests", {}).get("passed", False)
        )
```

#### 2.4.7 Key Principle: Verified at Generation Time

**The agent cannot produce non-conformant code.**

This is fundamentally different from traditional CI/CD where violations are caught after commit. In AgentForge:

```
Traditional CI/CD:
  Developer writes code → Commits → CI runs → Violations found → Developer fixes

AgentForge:
  Agent writes code → Verification runs → Violations found → Agent fixes → Loop
                                                                      ↓
                                                              Only conformant
                                                              code exits phase
```

The conformance gate ensures:
1. Every line of generated code meets all contracts
2. Violations are fixed before the agent can proceed
3. The human never sees non-conformant code
4. Trust is built into the generation process, not bolted on after

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

### Phase 3: Agent Specialization
- [ ] Agent definition contract (meta-contract)
- [ ] Agent definition loader
- [ ] Core agent definitions (8 agents)
- [ ] Agent-specific system prompt builder
- [ ] Tool restriction enforcement (AgentToolBridge)
- [ ] Path constraint enforcement
- [ ] Agent orchestrator
- [ ] Review loop implementation
- [ ] Audit trail agent tracking

### Phase 4: Full Pipeline
- [ ] Pipeline controller
- [ ] Stage executors (red, green, refactor)
- [ ] Full verification chain
- [ ] Autonomous clarification
- [ ] Stage-to-agent mapping
- [ ] Multi-agent handoffs

### Phase 5: Flexible Execution
- [ ] Goal type classification
- [ ] Pipeline templates (design, implement, test, review, fix)
- [ ] External artifact import with validation
- [ ] Iteration protocol
- [ ] User decision handling (approve, revise, reject, exit)
- [ ] Task composition (--from-task)
- [ ] Artifact lifecycle states
- [ ] Pipeline extension (continue to later stages)
- [ ] Staleness detection for referenced artifacts

### Phase 6: Production
- [ ] Multi-repo support
- [ ] Audit trail and replay
- [ ] Cost tracking
- [ ] CLI dashboard (`agentforge status --watch`)
- [ ] Web dashboard (localhost:8420)
- [ ] Real-time WebSocket updates
- [ ] Escalation resolution UI
- [ ] Iteration decision UI
- [ ] Project-specific agent customization

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

## Part 11: Observability & Dashboard

The observability layer enables "trust but verify at a glance"—allowing users to monitor all active work, peek into any task's progress, and handle escalations without disrupting autonomous execution.

### 11.1 Information Hierarchy

The dashboard presents information at four levels of detail:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   LEVEL 1: GLOBAL DASHBOARD                                                  │
│   "What's happening across all my work?"                                    │
│                                                                              │
│   Shows: All active tasks, completion status, escalations                   │
│   Actions: Start new task, view escalations, access any task                │
│                                                                              │
│                                    │                                         │
│                                    ▼                                         │
│   LEVEL 2: TASK VIEW                                                         │
│   "What's the status of this specific task?"                                │
│                                                                              │
│   Shows: Pipeline progress, current phase, files modified, cost             │
│   Actions: View phases, abort task, export audit report                     │
│                                                                              │
│                                    │                                         │
│                                    ▼                                         │
│   LEVEL 3: PHASE VIEW                                                        │
│   "What's happening in this phase?"                                         │
│                                                                              │
│   Shows: Exit criteria status, files touched, recent steps                  │
│   Actions: View step details, see blocking issues                           │
│                                                                              │
│                                    │                                         │
│                                    ▼                                         │
│   LEVEL 4: STEP VIEW                                                         │
│   "What exactly did the agent do/see here?"                                 │
│                                                                              │
│   Shows: Full context sent, LLM response, tool results, state diff          │
│   Actions: Replay step, view raw artifacts                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Data Model

#### Task Summary (Levels 1 & 2)

```yaml
# Aggregated from state store, computed on request
# Endpoint: GET /api/tasks/{task_id}

task_summary:
  task_id: "task-20251231-oauth2"
  repo: "backend-service"
  request: "Add OAuth2 authentication to the API"
  
  status:
    state: "in_progress"  # pending, in_progress, escalated, completed, failed
    phase: "green"
    phase_progress: 0.65   # Estimated % through current phase
    overall_progress: 0.72 # Estimated % through entire pipeline
    
  timing:
    started_at: "2025-12-31T10:00:00Z"
    last_activity: "2025-12-31T12:15:32Z"
    elapsed_seconds: 8132
    estimated_remaining_seconds: 2700
    
  steps:
    total: 34
    by_phase:
      intake: 3
      clarify: 5
      analyze: 8
      spec: 6
      red: 4
      green: 8  # current
      
  health:
    tests_passing: 8
    tests_total: 10
    conformance_passing: 12
    conformance_total: 12
    escalations_pending: 0
    errors_recent: 0
    
  cost:
    tokens_used: 142340
    estimated_cost_usd: 2.13
    
  files:
    created: ["auth/oauth.py", "auth/providers/google.py"]
    modified: ["config/auth.yaml", "api/routes/auth.py"]
    
  current_action:
    step: 34
    action: "edit_file"
    target: "auth/oauth.py"
    started_at: "2025-12-31T12:15:20Z"
```

#### Phase Detail (Level 3)

```yaml
# Endpoint: GET /api/tasks/{task_id}/phases/{phase}

phase_detail:
  task_id: "task-20251231-oauth2"
  phase: "green"
  
  status: "in_progress"
  started_at: "2025-12-31T11:45:00Z"
  
  objective: "Implement code to pass all tests from RED phase"
  
  exit_criteria:
    - name: "syntax_passing"
      status: "passed"
      
    - name: "type_check_passing"
      status: "passed"
      
    - name: "conformance_passing"
      status: "passed"
      details: "12/12 checks passing"
      
    - name: "tests_passing"
      status: "failing"
      details: "8/10 tests passing"
      blocking: true
      failures:
        - test: "test_oauth_token_expiry"
          error: "AssertionError: Expected token.expired to be True"
        - test: "test_oauth_provider_google"
          error: "KeyError: 'client_secret'"
  
  files_touched:
    - path: "auth/oauth.py"
      changes: 145
      last_modified: "2025-12-31T12:15:20Z"
    - path: "auth/token.py"
      changes: 67
      last_modified: "2025-12-31T12:10:05Z"
      
  steps:
    total: 8
    recent:
      - step: 6
        action: "edit_file"
        target: "auth/oauth.py"
        result: "success"
        summary: "Added refresh_token method"
        
      - step: 7
        action: "run_tests"
        result: "partial"
        summary: "8/10 passing, 2 failures"
```

#### Step Detail (Level 4)

```yaml
# Endpoint: GET /api/tasks/{task_id}/steps/{step}

step_detail:
  task_id: "task-20251231-oauth2"
  step: 34
  phase: "green"
  
  timestamp: "2025-12-31T12:15:20Z"
  duration_seconds: 8.3
  
  action:
    type: "edit_file"
    target: "auth/oauth.py"
    parameters:
      changes: "Added token expiry check"
      
  llm_call:
    model: "claude-sonnet-4-20250514"
    prompt_tokens: 6204
    completion_tokens: 892
    
  context_sent:
    task_frame: { ... }
    current_state: { ... }
    recent_actions: [ ... ]
    verification_status: { ... }
    
  llm_response:
    reasoning: "The test is failing because we're not checking token expiry..."
    action_chosen: "edit_file"
    
  result:
    success: true
    output: "File modified successfully"
    
  state_after:
    verification_status:
      tests: { passing: 8, failing: 2 }
      conformance: { passing: 12, failing: 0 }
      
  diff:
    file: "auth/oauth.py"
    patch: |
      @@ -45,6 +45,10 @@
       def is_expired(self) -> bool:
      -    return False
      +    return datetime.utcnow() > self.expires_at
```

### 11.3 CLI Dashboard

The primary interface for status checking:

```bash
# Quick status overview
agentforge status

┌──────────────────────────────────────────────────────────────┐
│ AGENTFORGE STATUS                                            │
├──────────────────────────────────────────────────────────────┤
│ Active: 2    Completed: 5    Escalated: 1                   │
│                                                              │
│ ● backend-service    GREEN ██████░░░░ 65%   2h 15m          │
│   "Add OAuth2 authentication"                                │
│   Tests: 8/10  Conformance: ✓  Last: edit_file (12s ago)    │
│                                                              │
│ ● api-gateway        SPEC  ████░░░░░░ 40%   45m             │
│   "Add rate limiting middleware"                             │
│   Last: analyze_requirements (2m ago)                        │
│                                                              │
│ ⚠ data-layer         ESCALATED                    3h 20m    │
│   "Migrate to PostgreSQL"                                    │
│   Waiting: Clarification on schema migration strategy        │
└──────────────────────────────────────────────────────────────┘

# Live watch mode
agentforge status --watch

# Detailed task view
agentforge status task-20251231-oauth2 --detail

# JSON output for scripting
agentforge status --json
```

### 11.4 Web Dashboard

Local web interface for richer interaction:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔧 AGENTFORGE DASHBOARD                                    localhost:8420   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─── Active Tasks ────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │ 🟢 Add OAuth2 authentication          backend-service          │ │   │
│  │  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━░░░░░░░░░░░░░░ 72%       │ │   │
│  │  │    INTAKE ✓  CLARIFY ✓  ANALYZE ✓  SPEC ✓  RED ✓  [GREEN]     │ │   │
│  │  │                                                                 │ │   │
│  │  │    ⏱ 2h 15m elapsed    💰 $2.13    📊 Tests: 8/10 passing     │ │   │
│  │  │    Last: edit_file auth/oauth.py (12s ago)                     │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │ 🟡 Add rate limiting                  api-gateway              │ │   │
│  │  │    ━━━━━━━━━━━━━━━━░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 35%       │ │   │
│  │  │    INTAKE ✓  CLARIFY ✓  [ANALYZE]                              │ │   │
│  │  │                                                                 │ │   │
│  │  │    ⏱ 45m elapsed    💰 $0.67    📊 Analyzing codebase...      │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─── Needs Attention ─────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ⚠️  data-layer: Migrate to PostgreSQL                              │   │
│  │      ESCALATED 3h 20m ago                                           │   │
│  │      Question: "Should we use blue-green deployment for migration?" │   │
│  │                                                                      │   │
│  │      [Respond] [View Context] [Abort Task]                          │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─── Recent Completions ──────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ✅ Add user preferences API    frontend    Completed 1h ago        │   │
│  │  ✅ Fix payment webhook handler backend     Completed 3h ago        │   │
│  │                                                                      │   │
│  │  [View All Completed]                                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Task Detail View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Back    Add OAuth2 authentication                        backend-service  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Status: IN PROGRESS          Started: Dec 31, 10:00 AM                     │
│  Phase: GREEN (Implementing)  Elapsed: 2h 15m                               │
│                                                                              │
│  ┌─── Pipeline Progress ───────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  INTAKE ━━━ CLARIFY ━━━ ANALYZE ━━━ SPEC ━━━ RED ━━━ GREEN ─── ...  │   │
│  │    ✓   3     ✓   5       ✓   8      ✓  6    ✓  4    ●  8           │   │
│  │   steps    steps       steps     steps   steps   steps              │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─── Current Phase: GREEN ────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Objective: Implement code to pass all tests                        │   │
│  │                                                                      │   │
│  │  Exit Criteria:                                                      │   │
│  │    ✅ Syntax check passing                                          │   │
│  │    ✅ Type check passing                                            │   │
│  │    ✅ Conformance (12/12 passing)                                   │   │
│  │    ❌ Tests (8/10 passing) ← BLOCKING                               │   │
│  │                                                                      │   │
│  │  Failing Tests:                                                      │   │
│  │    • test_oauth_token_expiry                                        │   │
│  │      AssertionError: Expected token.expired to be True              │   │
│  │    • test_oauth_provider_google                                     │   │
│  │      KeyError: 'client_secret'                                      │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─── Files Modified ──────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  📄 auth/oauth.py              +145 lines   [View Diff]             │   │
│  │  📄 auth/token.py               +67 lines   [View Diff]             │   │
│  │  📄 auth/providers/google.py    +89 lines   [View Diff]             │   │
│  │  📄 config/auth.yaml            +12 lines   [View Diff]             │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─── Step Timeline ───────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  12:15:32  #34  edit_file auth/oauth.py                     ✓      │   │
│  │            "Fixed token expiry calculation"                          │   │
│  │                                                                      │   │
│  │  12:15:20  #33  run_tests                                   ✗      │   │
│  │            "8/10 passing, 2 failures"                               │   │
│  │                                                                      │   │
│  │  12:14:55  #32  edit_file auth/oauth.py                     ✓      │   │
│  │            "Added refresh_token method"                              │   │
│  │                                                                      │   │
│  │  [Load More...]                                                      │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─── Cost & Metrics ──────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Total Steps: 34          Tokens Used: 142,340                      │   │
│  │  Estimated Cost: $2.13    Avg Tokens/Step: 4,186                    │   │
│  │                                                                      │   │
│  │  [View Full Audit Trail]  [Export Report]  [Abort Task]             │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.5 Implementation Architecture

#### State Aggregator

Reads from state store and computes dashboard-ready summaries:

```python
class StateAggregator:
    """
    Aggregates state from disk into dashboard-ready summaries.
    Watches for changes and updates cached summaries.
    """
    
    def __init__(self, agentforge_root: Path):
        self.root = agentforge_root
        self.tasks_dir = agentforge_root / "tasks"
        self._cache: Dict[str, TaskSummary] = {}
        
    def get_all_tasks(self) -> List[TaskSummary]:
        """Get summary of all tasks."""
        summaries = []
        for task_dir in self.tasks_dir.iterdir():
            if task_dir.is_dir():
                summary = self.get_task_summary(task_dir.name)
                summaries.append(summary)
        return sorted(summaries, key=lambda t: t.last_activity, reverse=True)
    
    def get_task_summary(self, task_id: str) -> TaskSummary:
        """Build summary from task state files."""
        task_dir = self.tasks_dir / task_id
        
        # Load state files
        task = yaml.safe_load((task_dir / "task.yaml").read_text())
        state = yaml.safe_load((task_dir / "state.yaml").read_text())
        actions = yaml.safe_load((task_dir / "actions.yaml").read_text())
        
        # Compute derived fields
        return TaskSummary(
            task_id=task_id,
            request=task["request"],
            repo=task.get("repo"),
            status=self._compute_status(state),
            phase=state["current_phase"],
            progress=self._estimate_progress(state, actions),
            timing=self._compute_timing(actions),
            health=self._compute_health(state),
            cost=self._compute_cost(actions),
            current_action=self._get_current_action(actions)
        )
    
    def get_phase_detail(self, task_id: str, phase: str) -> PhaseDetail:
        """Get detailed info about a specific phase."""
        ...
    
    def get_step_detail(self, task_id: str, step: int) -> StepDetail:
        """Get full detail about a specific step including context sent."""
        ...
```

#### Dashboard API

REST and WebSocket endpoints for dashboard:

```python
from fastapi import FastAPI, WebSocket

app = FastAPI(title="AgentForge Dashboard")

@app.get("/api/tasks")
async def list_tasks() -> List[TaskSummary]:
    """List all tasks with summaries."""
    return aggregator.get_all_tasks()

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> TaskSummary:
    """Get task summary."""
    return aggregator.get_task_summary(task_id)

@app.get("/api/tasks/{task_id}/phases/{phase}")
async def get_phase(task_id: str, phase: str) -> PhaseDetail:
    """Get phase detail."""
    return aggregator.get_phase_detail(task_id, phase)

@app.get("/api/tasks/{task_id}/steps/{step}")
async def get_step(task_id: str, step: int) -> StepDetail:
    """Get step detail with full context."""
    return aggregator.get_step_detail(task_id, step)

@app.post("/api/tasks/{task_id}/escalations/{escalation_id}/resolve")
async def resolve_escalation(
    task_id: str, 
    escalation_id: str, 
    response: EscalationResponse
):
    """Resolve an escalation from the dashboard."""
    return escalation_manager.resolve(task_id, escalation_id, response)

@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """Real-time updates via WebSocket."""
    await websocket.accept()
    async for update in state_watcher.updates():
        await websocket.send_json(update)
```

#### Real-Time Updates

File system watcher for live updates:

```python
class StateWatcher:
    """
    Watches state directory for changes and emits updates.
    Uses filesystem events (inotify on Linux, FSEvents on macOS).
    """
    
    async def updates(self) -> AsyncIterator[StateUpdate]:
        """Yield updates as state changes."""
        async for event in self.watch_directory(self.tasks_dir):
            if event.is_relevant():
                task_id = self.extract_task_id(event.path)
                summary = self.aggregator.get_task_summary(task_id)
                yield StateUpdate(
                    type="task_updated",
                    task_id=task_id,
                    summary=summary
                )
```

### 11.6 Data Sources

All dashboard data comes from the existing state store:

| Data | Source | Available |
|------|--------|-----------|
| Task goal/request | `task.yaml` | ✅ |
| Current phase | `state.yaml` | ✅ |
| All steps taken | `actions.yaml` | ✅ |
| Token usage per step | `actions.yaml` | ✅ |
| Verification status | `state.yaml` | ✅ |
| Files modified | `actions.yaml` | ✅ |
| Escalations | `escalations/` | ✅ |
| Full context per step | `actions.yaml` | ✅ |
| Diffs | `artifacts/snapshots/` | ✅ |

The dashboard is purely a **read layer** on top of the existing state store—no additional data storage required.

### 11.7 Implementation Phases

1. **CLI status command** (2-4 hours)
   - `agentforge status` with Rich table
   - `agentforge status {task_id}` for detail
   - JSON output for scripting
   
2. **JSON API** (4-6 hours)
   - REST endpoints for all data levels
   - Shared by CLI and web dashboard
   
3. **Watch mode** (2-4 hours)
   - File system watcher
   - Live terminal updates with Rich Live
   - WebSocket push for web clients

4. **Web dashboard** (1-2 days)
   - Simple React/Svelte frontend
   - Real-time WebSocket updates
   - Escalation resolution UI
   - Diff viewer for file changes

---

## Part 12: Agent Specialization System

Different pipeline stages require different expertise. A test engineer thinks differently than a software architect. A security reviewer looks for different things than a developer. AgentForge's agent specialization system ensures the right expertise is applied at each stage, with appropriate tool restrictions and verified handoffs.

### 12.1 Core Principle: Specialized Agents, Not Generic Assistants

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   GENERIC ASSISTANT (what we DON'T want)                                    │
│                                                                              │
│   "I'm Claude. I can do anything. Here's some code, tests, and docs."       │
│                                                                              │
│   Problems:                                                                  │
│   - No separation of concerns                                               │
│   - No tool restrictions (can do anything)                                  │
│   - No verification of role-appropriate output                              │
│   - No clear handoffs                                                       │
│   - Can't audit "who decided what"                                          │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SPECIALIZED AGENTS (what we want)                                         │
│                                                                              │
│   Test Engineer: "I design tests. I think adversarially. I don't write     │
│                   implementation code—that's not my job."                   │
│                                                                              │
│   Benefits:                                                                  │
│   - Clear responsibility per role                                           │
│   - Tools restricted to role's needs                                        │
│   - Output verified against role's contract                                 │
│   - Explicit handoffs between agents                                        │
│   - Full audit trail of which agent made which decision                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Agent Definition Schema

Each agent role is defined by a contract-verified YAML file:

```yaml
# .agentforge/agents/test_engineer.yaml

agent:
  role: test_engineer
  version: "1.0"
  display_name: "Test Engineer"

identity:
  description: |
    You are a Test Engineer. You design comprehensive test strategies
    that verify requirements are met. You think adversarially—how could
    this fail? What edge cases exist? You write tests that serve as
    executable specifications.
    
  expertise:
    - Test strategy and design
    - TDD/BDD methodologies
    - Edge case identification
    - Test pyramid (unit, integration, e2e)
    - Property-based testing
    - Mutation testing concepts
    
  thinking_style: |
    You think like a skeptic. "Prove to me this works." You consider
    happy paths, error paths, edge cases, and boundary conditions.
    You write tests that would catch bugs, not just tests that pass.

capabilities:
  tools:
    allowed:
      - read_file           # Read specs and existing code
      - create_file         # Create test files
      - run_tests           # Verify tests fail/pass
      - analyze_coverage    # Check requirement coverage
      - search_codebase     # Find existing patterns
    forbidden:
      - edit_file           # Cannot modify implementation
      - deploy              # Not a deployment role
      - commit              # Not responsible for commits
    path_constraints:
      create_file: "tests/**/*"  # Can only create in tests/
      
  output:
    contract: test_suite
    must_verify:
      - all_tests_fail: true      # RED phase: tests must fail
      - requirement_coverage: 100% # Every requirement has tests

constraints:
  - "Every acceptance criterion must have at least one test"
  - "Tests must be deterministic and isolated"
  - "Test names must describe the expected behavior"
  - "Do not write implementation code"
  - "Do not modify existing non-test files"

orchestration:
  stage: red
  receives_from: [software_architect]
  hands_off_to: [software_developer]
  reviewed_by: []
```

### 12.3 Agent Definition Contract

The agent definition itself is validated against a meta-contract:

```yaml
# contracts/agent_definition.yaml

contract: agent_definition
version: "1.0"
description: Schema for agent role definitions

schema:
  agent:
    type: object
    required: true
    properties:
      role:
        type: string
        required: true
        pattern: "^[a-z_]+$"
        description: Unique identifier for this agent role
      version:
        type: string
        required: true
        pattern: "^\\d+\\.\\d+$"
      display_name:
        type: string
        required: true

  identity:
    type: object
    required: true
    properties:
      description:
        type: string
        required: true
        min_length: 100
        description: Detailed description of who this agent is
      expertise:
        type: array
        required: true
        min_items: 3
        items:
          type: string
      thinking_style:
        type: string
        required: true
        min_length: 50

  capabilities:
    type: object
    required: true
    properties:
      tools:
        type: object
        required: true
        properties:
          allowed:
            type: array
            required: true
            items:
              type: string
          forbidden:
            type: array
            items:
              type: string
          path_constraints:
            type: object
            additionalProperties:
              type: string
      output:
        type: object
        required: true
        properties:
          contract:
            type: string
            required: true
          must_verify:
            type: object
            required: true

  constraints:
    type: array
    required: true
    min_items: 1
    items:
      type: string

  orchestration:
    type: object
    required: true
    properties:
      stage:
        type: string
        required: true
      receives_from:
        type: array
        items:
          type: string
      hands_off_to:
        type: array
        items:
          type: string
      reviewed_by:
        type: array
        items:
          type: string
      reviews:
        type: array
        items:
          type: string

validation:
  - allowed and forbidden tools must not overlap
  - output contract must exist in contracts directory
  - receives_from agents must exist
  - hands_off_to agents must exist
  - reviewed_by agents must exist
```

### 12.4 Pipeline Stage to Agent Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   STAGE              PRIMARY AGENT              REVIEWERS                    │
│                                                                              │
│   INTAKE ──────────▶ Requirements Analyst       (none)                      │
│                      📋 Extract intent                                       │
│                                                                              │
│   CLARIFY ─────────▶ Business Analyst           (none)                      │
│                      🔍 Resolve ambiguity                                    │
│                                                                              │
│   ANALYZE ─────────▶ Software Architect         (none)                      │
│                      🏗️ Assess impact                                        │
│                                                                              │
│   SPEC ────────────▶ Software Architect         Security Architect          │
│                      🏗️ Design solution          🔒 Validate security        │
│                                                                              │
│   RED ─────────────▶ Test Engineer              (none)                      │
│                      🧪 Write failing tests                                  │
│                                                                              │
│   GREEN ───────────▶ Software Developer         (none)                      │
│                      💻 Implement solution                                   │
│                                                                              │
│   REFACTOR ────────▶ Senior Developer           Security Architect          │
│                      👨‍💻 Improve quality          🔒 Security scan            │
│                                                                              │
│   DELIVER ─────────▶ DevOps Engineer            (none)                      │
│                      🚀 Package & document                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

Configuration:

```yaml
# .agentforge/orchestration/pipeline.yaml

pipeline:
  stages:
    intake:
      primary: requirements_analyst
      reviewers: []
      
    clarify:
      primary: business_analyst
      reviewers: []
      
    analyze:
      primary: software_architect
      reviewers: []
      
    spec:
      primary: software_architect
      reviewers: [security_architect]
      review_mode: blocking  # Must pass review to proceed
      
    red:
      primary: test_engineer
      reviewers: []
      
    green:
      primary: software_developer
      reviewers: []
      
    refactor:
      primary: senior_developer
      reviewers: [security_architect]
      review_mode: blocking
      
    deliver:
      primary: devops_engineer
      reviewers: []
```

### 12.5 Complete Agent Definitions

#### Requirements Analyst (INTAKE)

```yaml
agent:
  role: requirements_analyst
  version: "1.0"
  display_name: "Requirements Analyst"

identity:
  description: |
    You extract clear, actionable requirements from ambiguous user requests.
    You identify what's being asked, what's in scope, what's out of scope,
    and what questions need answers before proceeding. You don't make
    assumptions—you surface them as questions.
    
  expertise:
    - Requirements elicitation and analysis
    - Scope definition and boundary setting
    - Stakeholder communication patterns
    - User story decomposition
    - Ambiguity identification
    
  thinking_style: |
    You read carefully and ask "what exactly do they mean?" You identify
    implicit assumptions and make them explicit. You think about what
    could go wrong if requirements are misunderstood.

capabilities:
  tools:
    allowed:
      - read_file
      - search_codebase
      - read_documentation
    forbidden:
      - edit_file
      - create_file
      - run_tests
      - deploy
  output:
    contract: intake_record
    must_verify:
      - intent_extracted: true
      - scope_defined: true
      - ambiguities_listed: true

constraints:
  - "Do not assume unstated requirements"
  - "Surface all ambiguities as explicit questions"
  - "Identify what is NOT in scope"
  - "Do not propose solutions—only extract requirements"

orchestration:
  stage: intake
  receives_from: []
  hands_off_to: [business_analyst]
  reviewed_by: []
```

#### Business Analyst (CLARIFY)

```yaml
agent:
  role: business_analyst
  version: "1.0"
  display_name: "Business Analyst"

identity:
  description: |
    You resolve ambiguities and gather the context needed for implementation.
    You can answer questions by analyzing the codebase, or escalate to
    humans when genuine clarification is needed. You bridge the gap between
    user intent and technical specification.
    
  expertise:
    - Business process analysis
    - Requirements clarification
    - Codebase context extraction
    - Stakeholder communication
    - Domain knowledge synthesis
    
  thinking_style: |
    You try to answer questions before escalating. "Can I figure this out
    from the existing code?" You're resourceful but know when to ask.
    You provide confidence scores for your inferences.

capabilities:
  tools:
    allowed:
      - read_file
      - search_codebase
      - read_documentation
      - escalate_question     # Request human clarification
    forbidden:
      - edit_file
      - create_file
      - run_tests
  output:
    contract: clarification
    must_verify:
      - all_questions_addressed: true
      - confidence_scores_provided: true

constraints:
  - "Attempt to answer from codebase before escalating"
  - "Provide confidence scores for inferred answers"
  - "Only escalate genuinely ambiguous questions"
  - "Do not make architectural decisions"

orchestration:
  stage: clarify
  receives_from: [requirements_analyst]
  hands_off_to: [software_architect]
  reviewed_by: []
```

#### Software Architect (ANALYZE, SPEC)

```yaml
agent:
  role: software_architect
  version: "1.0"
  display_name: "Software Architect"

identity:
  description: |
    You design software solutions with a focus on clean architecture,
    maintainability, and long-term evolution. You think in terms of
    boundaries, contracts, and trade-offs. You consider the big picture
    before diving into details.
    
  expertise:
    - System design and architecture patterns
    - Clean Architecture, DDD, CQRS
    - API design and contracts
    - Dependency management
    - Performance and scalability
    - Technical debt assessment
    
  thinking_style: |
    You consider the big picture first, then zoom into details.
    You always ask "what are the trade-offs?" and "how will this
    evolve over time?" You prefer explicit contracts over implicit
    assumptions. You think about what could break.

capabilities:
  tools:
    allowed:
      - read_file
      - search_codebase
      - analyze_dependencies
      - view_architecture_diagram
      - read_documentation
    forbidden:
      - edit_file           # Architects design, don't implement
      - create_file         # No direct file creation
      - run_tests           # Not implementation
      - deploy
  output:
    contract: specification  # For SPEC stage
    must_verify:
      - requirements_addressed: true
      - interfaces_defined: true
      - constraints_documented: true

constraints:
  - "Do not propose solutions that violate existing architectural boundaries"
  - "Always consider backward compatibility"
  - "Identify security implications for design decisions"
  - "Document trade-offs for significant decisions"
  - "Do not write implementation code"

orchestration:
  stage: spec              # Primary for SPEC, also used in ANALYZE
  receives_from: [business_analyst]
  hands_off_to: [test_engineer]
  reviewed_by: [security_architect]
```

#### Security Architect (REVIEW ROLE)

```yaml
agent:
  role: security_architect
  version: "1.0"
  display_name: "Security Architect"

identity:
  description: |
    You review designs and code for security vulnerabilities. You think
    like an attacker—how could this be exploited? You ensure security
    is built in, not bolted on. You distinguish between blocking issues
    (must fix) and advisory issues (should consider).
    
  expertise:
    - OWASP Top 10 vulnerabilities
    - Authentication and authorization patterns
    - Input validation and sanitization
    - Secrets management
    - Secure coding practices
    - Threat modeling
    
  thinking_style: |
    You assume malicious input. You look for trust boundaries and verify
    they're enforced. You think "how would I attack this?" You're
    thorough but pragmatic—not everything is critical.

capabilities:
  tools:
    allowed:
      - read_file
      - search_codebase
      - run_security_scan
      - analyze_dependencies   # Check for vulnerable deps
    forbidden:
      - edit_file             # Reviewers don't modify
      - create_file
      - run_tests
      - deploy
  output:
    contract: security_review
    must_verify:
      - review_complete: true
      - issues_categorized: true  # blocking vs advisory

constraints:
  - "Categorize issues as blocking or advisory"
  - "Blocking issues must have clear remediation"
  - "Do not modify code—only review"
  - "Consider both design and implementation security"
  - "Check for common vulnerabilities (injection, XSS, CSRF, etc.)"

orchestration:
  stage: null              # Review role, not primary for any stage
  receives_from: []
  hands_off_to: []
  reviewed_by: []
  reviews: [software_architect, senior_developer]  # Who this agent reviews
```

#### Test Engineer (RED)

```yaml
agent:
  role: test_engineer
  version: "1.0"
  display_name: "Test Engineer"

identity:
  description: |
    You design comprehensive test strategies that verify requirements
    are met. You think adversarially—how could this fail? What edge
    cases exist? You write tests that serve as executable specifications.
    Your tests define the expected behavior before implementation exists.
    
  expertise:
    - Test strategy and design
    - TDD/BDD methodologies
    - Edge case identification
    - Test pyramid (unit, integration, e2e)
    - Property-based testing
    - Code coverage analysis
    
  thinking_style: |
    You think like a skeptic. "Prove to me this works." You consider
    happy paths, error paths, edge cases, and boundary conditions.
    You write tests that would catch bugs, not just tests that pass.

capabilities:
  tools:
    allowed:
      - read_file
      - create_file         # Create test files only
      - run_tests           # Verify tests fail
      - analyze_coverage
      - search_codebase     # Find existing test patterns
    forbidden:
      - edit_file           # Cannot modify implementation
      - deploy
      - commit
    path_constraints:
      create_file: "tests/**/*"
  output:
    contract: test_suite
    must_verify:
      - all_tests_fail: true
      - requirement_coverage: 100%

constraints:
  - "Every acceptance criterion must have at least one test"
  - "Tests must be deterministic and isolated"
  - "Test names must describe the expected behavior"
  - "Tests must currently fail (RED phase)"
  - "Do not write implementation code"
  - "Follow existing test patterns in codebase"

orchestration:
  stage: red
  receives_from: [software_architect]
  hands_off_to: [software_developer]
  reviewed_by: []
```

#### Software Developer (GREEN)

```yaml
agent:
  role: software_developer
  version: "1.0"
  display_name: "Software Developer"

identity:
  description: |
    You write clean, working code that passes tests. You focus on making
    tests pass with the simplest solution that could work, then rely on
    refactoring to improve. You follow existing patterns in the codebase
    exactly—consistency is more important than cleverness.
    
  expertise:
    - Software development (primary language)
    - Clean code principles
    - Design patterns
    - Debugging and problem-solving
    - Reading and matching code style
    - Test-driven development
    
  thinking_style: |
    You make tests pass one at a time. You write the minimum code needed.
    You don't over-engineer or anticipate future requirements beyond
    what's specified. You match existing code style exactly.

capabilities:
  tools:
    allowed:
      - read_file
      - edit_file
      - create_file
      - run_tests
      - run_conformance_check
      - run_type_check
      - search_codebase
    forbidden:
      - deploy
      - commit              # Commits happen in DELIVER
    path_constraints:
      edit_file: "!tests/**/*"  # Cannot modify test files
  output:
    contract: implementation
    must_verify:
      - all_tests_pass: true
      - conformance_pass: true
      - type_check_pass: true
      - no_regressions: true

constraints:
  - "Only modify files necessary to pass tests"
  - "Follow existing code patterns and style"
  - "All conformance checks must pass"
  - "No commented-out code or TODOs"
  - "Do not modify test files"

orchestration:
  stage: green
  receives_from: [test_engineer]
  hands_off_to: [senior_developer]
  reviewed_by: []
```

#### Senior Developer (REFACTOR)

```yaml
agent:
  role: senior_developer
  version: "1.0"
  display_name: "Senior Developer"

identity:
  description: |
    You improve code quality through refactoring. You eliminate duplication,
    improve naming, extract methods, and ensure the code is maintainable.
    You have a keen eye for code smells and know how to fix them without
    breaking functionality.
    
  expertise:
    - Code refactoring techniques
    - Design patterns and when to apply them
    - Code smell identification
    - Performance optimization
    - Maintainability assessment
    - Technical debt reduction
    
  thinking_style: |
    You look at code and ask "how could this be clearer?" You see
    patterns that could be extracted and duplication that could be
    eliminated. You balance perfection with pragmatism.

capabilities:
  tools:
    allowed:
      - read_file
      - edit_file
      - create_file
      - run_tests
      - run_conformance_check
      - run_type_check
      - analyze_complexity
      - search_codebase
    forbidden:
      - deploy
      - commit
  output:
    contract: implementation  # Same as GREEN, refined
    must_verify:
      - all_tests_pass: true
      - conformance_pass: true
      - complexity_acceptable: true
      - no_code_smells: true

constraints:
  - "Tests must pass after every change"
  - "Do not change behavior—only improve structure"
  - "Reduce complexity where possible"
  - "Improve naming for clarity"
  - "Extract reusable components"

orchestration:
  stage: refactor
  receives_from: [software_developer]
  hands_off_to: [devops_engineer]
  reviewed_by: [security_architect]
```

#### DevOps Engineer (DELIVER)

```yaml
agent:
  role: devops_engineer
  version: "1.0"
  display_name: "DevOps Engineer"

identity:
  description: |
    You package deliverables for deployment. You create documentation,
    generate changelogs, verify deployment readiness, and prepare
    release artifacts. You ensure everything needed for deployment
    is in place and properly documented.
    
  expertise:
    - Release management
    - Documentation generation
    - Changelog creation
    - Deployment verification
    - Configuration management
    - CI/CD pipelines
    
  thinking_style: |
    You think about "what does someone need to deploy this?" You
    ensure all artifacts are present, documented, and verified.
    You're methodical and checklist-oriented.

capabilities:
  tools:
    allowed:
      - read_file
      - create_file           # Documentation, configs
      - generate_changelog
      - verify_deployment_ready
      - create_release_notes
      - search_codebase
    forbidden:
      - edit_file             # Implementation is frozen
      - run_tests             # Testing is complete
    path_constraints:
      create_file: "docs/**/*,deploy/**/*,*.md"
  output:
    contract: delivery_report
    must_verify:
      - documentation_complete: true
      - changelog_generated: true
      - deployment_ready: true

constraints:
  - "Do not modify implementation code"
  - "Ensure all documentation is up to date"
  - "Verify all deployment prerequisites"
  - "Create clear release notes"

orchestration:
  stage: deliver
  receives_from: [senior_developer]
  hands_off_to: []
  reviewed_by: []
```

### 12.6 Agent Orchestration

#### Stage Execution with Agents

```python
class AgentOrchestrator:
    """
    Determines which agent(s) execute each stage.
    Handles handoffs and reviews between agents.
    """
    
    def __init__(self, config_path: Path):
        self.pipeline_config = self.load_pipeline_config(config_path)
        self.agent_definitions = self.load_agent_definitions(config_path)
    
    def execute_stage(
        self,
        stage: str,
        task_id: str,
        input_artifact: dict
    ) -> StageResult:
        """Execute a stage with appropriate agent(s)."""
        stage_config = self.pipeline_config["stages"][stage]
        
        # Load primary agent
        primary_role = stage_config["primary"]
        primary_agent = self.load_agent(primary_role)
        
        # Execute primary agent
        result = self.execute_agent_loop(
            agent=primary_agent,
            task_id=task_id,
            input_artifact=input_artifact
        )
        
        if not result.success:
            return result
        
        # Run reviews if configured
        reviewers = stage_config.get("reviewers", [])
        if reviewers:
            result = self.execute_review_loop(
                primary_agent=primary_agent,
                primary_result=result,
                reviewers=reviewers,
                task_id=task_id,
                review_mode=stage_config.get("review_mode", "blocking")
            )
        
        return result
    
    def load_agent(self, role: str) -> Agent:
        """Load agent with role-specific configuration."""
        definition = self.agent_definitions[role]
        
        return Agent(
            role=role,
            system_prompt=self.build_system_prompt(definition),
            allowed_tools=definition["capabilities"]["tools"]["allowed"],
            forbidden_tools=definition["capabilities"]["tools"].get("forbidden", []),
            path_constraints=definition["capabilities"]["tools"].get("path_constraints", {}),
            output_contract=definition["capabilities"]["output"]["contract"],
            verification=definition["capabilities"]["output"]["must_verify"],
            constraints=definition["constraints"]
        )
    
    def execute_agent_loop(
        self,
        agent: Agent,
        task_id: str,
        input_artifact: dict
    ) -> StageResult:
        """Execute agent steps until stage completion or escalation."""
        state = self.state_store.load(task_id)
        state.current_agent = agent.role
        
        max_steps = 100  # Safety limit
        for step in range(max_steps):
            # Build context with agent-specific filtering
            context = self.context_builder.build(
                state=state,
                agent=agent,
                input_artifact=input_artifact
            )
            
            # Execute single step
            step_result = self.executor.execute_step(
                agent=agent,
                context=context
            )
            
            # Record in audit trail
            self.audit_trail.record(task_id, step_result, agent.role)
            
            # Update state
            self.state_store.update(task_id, step_result)
            
            # Check completion
            if step_result.stage_complete:
                return StageResult(
                    success=True,
                    artifact=step_result.artifact
                )
            
            if step_result.escalate:
                return StageResult(
                    success=False,
                    escalate=True,
                    reason=step_result.escalation_reason
                )
        
        return StageResult(
            success=False,
            error=f"Agent {agent.role} exceeded max steps"
        )
```

#### Review Loop

```python
def execute_review_loop(
    self,
    primary_agent: Agent,
    primary_result: StageResult,
    reviewers: List[str],
    task_id: str,
    review_mode: str,
    max_iterations: int = 3
) -> StageResult:
    """
    Execute review cycle between primary agent and reviewers.
    
    Review modes:
    - blocking: Must pass all reviews to proceed
    - advisory: Reviews logged but don't block
    """
    current_artifact = primary_result.artifact
    
    for iteration in range(max_iterations):
        all_reviews_passed = True
        blocking_issues = []
        advisory_issues = []
        
        # Each reviewer evaluates
        for reviewer_role in reviewers:
            reviewer = self.load_agent(reviewer_role)
            review = self.execute_review(
                reviewer=reviewer,
                artifact=current_artifact,
                task_id=task_id
            )
            
            if review.blocking_issues:
                all_reviews_passed = False
                blocking_issues.extend(review.blocking_issues)
            
            advisory_issues.extend(review.advisory_issues)
        
        # Log advisory issues regardless
        if advisory_issues:
            self.audit_trail.record_advisory(task_id, advisory_issues)
        
        # Check if we can proceed
        if all_reviews_passed or review_mode == "advisory":
            return StageResult(
                success=True,
                artifact=current_artifact,
                review_notes=advisory_issues
            )
        
        # Feed blocking issues to primary for revision
        revision_result = self.execute_agent_loop(
            agent=primary_agent,
            task_id=task_id,
            input_artifact={
                **current_artifact,
                "review_feedback": {
                    "blocking_issues": blocking_issues,
                    "iteration": iteration + 1
                }
            }
        )
        
        if not revision_result.success:
            return revision_result
        
        current_artifact = revision_result.artifact
    
    # Max iterations reached
    return StageResult(
        success=False,
        escalate=True,
        reason=f"Failed to resolve review issues after {max_iterations} iterations",
        blocking_issues=blocking_issues
    )
```

### 12.7 System Prompt Construction

Each agent receives a tailored system prompt built from its definition:

```python
AGENT_SYSTEM_PROMPT_TEMPLATE = """# Role: {display_name}

## Who You Are
{identity_description}

## Your Expertise
{expertise_list}

## How You Think
{thinking_style}

## Rules You Must Follow
{constraints_list}

## Tools Available
You have access to these tools and ONLY these tools:
{tools_list}

Tools you are FORBIDDEN from using (requests will be rejected):
{forbidden_tools_list}

## What You Must Produce
Your output must conform to the `{output_contract}` contract.

Before completing, you must verify:
{verification_list}

## Current Context
Stage: {current_stage}
Task: {task_goal}
You are receiving input from: {receives_from}
You will hand off to: {hands_off_to}

---

Stay in your role. Focus on your expertise. 
Do not attempt to do work outside your role.
Produce verified output that meets your contract.
"""

def build_system_prompt(self, definition: dict) -> str:
    """Build system prompt from agent definition."""
    return AGENT_SYSTEM_PROMPT_TEMPLATE.format(
        display_name=definition["agent"]["display_name"],
        identity_description=definition["identity"]["description"],
        expertise_list=self._format_list(definition["identity"]["expertise"]),
        thinking_style=definition["identity"]["thinking_style"],
        constraints_list=self._format_list(definition["constraints"]),
        tools_list=self._format_tools(definition["capabilities"]["tools"]["allowed"]),
        forbidden_tools_list=self._format_list(
            definition["capabilities"]["tools"].get("forbidden", [])
        ),
        output_contract=definition["capabilities"]["output"]["contract"],
        verification_list=self._format_dict(
            definition["capabilities"]["output"]["must_verify"]
        ),
        current_stage=self.current_stage,
        task_goal=self.task_goal,
        receives_from=", ".join(definition["orchestration"].get("receives_from", ["none"])),
        hands_off_to=", ".join(definition["orchestration"].get("hands_off_to", ["none"]))
    )
```

### 12.8 Tool Enforcement

The tool bridge enforces agent-specific tool restrictions:

```python
class AgentToolBridge:
    """
    Wraps tool execution with agent-specific restrictions.
    Rejects requests for forbidden tools.
    Enforces path constraints.
    """
    
    def __init__(self, agent: Agent, base_tools: Dict[str, Tool]):
        self.agent = agent
        self.base_tools = base_tools
        self.allowed_tools = set(agent.allowed_tools)
        self.forbidden_tools = set(agent.forbidden_tools)
        self.path_constraints = agent.path_constraints
    
    def execute(self, tool_name: str, params: dict) -> ToolResult:
        """Execute tool with agent restrictions."""
        
        # Check if tool is allowed
        if tool_name in self.forbidden_tools:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is forbidden for {self.agent.role}. "
                      f"Allowed tools: {', '.join(self.allowed_tools)}"
            )
        
        if tool_name not in self.allowed_tools:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is not available. "
                      f"Allowed tools: {', '.join(self.allowed_tools)}"
            )
        
        # Check path constraints
        if tool_name in self.path_constraints:
            path = params.get("path") or params.get("file_path")
            if path and not self._path_allowed(path, self.path_constraints[tool_name]):
                return ToolResult(
                    success=False,
                    error=f"Path '{path}' is not allowed for {self.agent.role}. "
                          f"Constraint: {self.path_constraints[tool_name]}"
                )
        
        # Execute the actual tool
        tool = self.base_tools[tool_name]
        return tool.execute(params)
    
    def _path_allowed(self, path: str, constraint: str) -> bool:
        """Check if path matches constraint pattern."""
        import fnmatch
        
        # Handle negation
        if constraint.startswith("!"):
            return not fnmatch.fnmatch(path, constraint[1:])
        
        # Handle multiple patterns (comma-separated)
        patterns = [p.strip() for p in constraint.split(",")]
        return any(fnmatch.fnmatch(path, p) for p in patterns)
```

### 12.9 Audit Trail Integration

Every step records which agent made the decision:

```yaml
# In actions.yaml

actions:
  - step: 15
    timestamp: "2025-12-31T11:45:00Z"
    phase: "spec"
    agent:
      role: "software_architect"
      version: "1.0"
    action:
      type: "create_design"
      tool: "create_artifact"
      params:
        artifact_type: "specification"
    result:
      success: true
      artifact_path: "artifacts/phases/spec/specification.yaml"
    context_tokens: 6204
    
  - step: 16
    timestamp: "2025-12-31T11:46:30Z"
    phase: "spec"
    agent:
      role: "security_architect"
      version: "1.0"
      mode: "review"
    action:
      type: "security_review"
    result:
      success: true
      blocking_issues:
        - id: "SEC-001"
          severity: "high"
          description: "Missing input validation on OAuth callback URL"
          remediation: "Validate callback URL against whitelist"
      advisory_issues:
        - id: "SEC-002"
          severity: "medium"
          description: "Consider adding rate limiting to token endpoint"
    context_tokens: 5891
    
  - step: 17
    timestamp: "2025-12-31T11:48:00Z"
    phase: "spec"
    agent:
      role: "software_architect"
      version: "1.0"
    action:
      type: "revise_design"
      revision_for: ["SEC-001"]  # Addressing blocking issue
    result:
      success: true
      changes:
        - "Added callback URL validation to specification"
```

### 12.10 Token Budget Adjustment

Agent definitions add to the system prompt. Updated token budget:

```python
TOKEN_BUDGET = {
    "system_prompt": 1500,    # Increased from 1000 for agent identity
    "task_frame": 500,
    "current_state": 4000,    # Reduced slightly to compensate
    "recent_actions": 1000,
    "verification_status": 200,
    "available_actions": 800,
    # ──────────────────────────
    # Total: 8000 max (unchanged)
}

# Breakdown of system prompt:
# - Agent identity: ~400 tokens
# - Agent expertise: ~150 tokens
# - Agent thinking style: ~100 tokens
# - Agent constraints: ~200 tokens
# - Tool descriptions: ~400 tokens
# - Output requirements: ~150 tokens
# - Stage context: ~100 tokens
# Total: ~1500 tokens
```

### 12.11 File Structure

```
.agentforge/
├── agents/                            # Agent definitions
│   ├── requirements_analyst.yaml
│   ├── business_analyst.yaml
│   ├── software_architect.yaml
│   ├── security_architect.yaml
│   ├── test_engineer.yaml
│   ├── software_developer.yaml
│   ├── senior_developer.yaml
│   └── devops_engineer.yaml
├── orchestration/
│   └── pipeline.yaml                  # Stage → Agent mapping
├── contracts/
│   ├── agent_definition.yaml          # Meta-contract for agents
│   ├── security_review.yaml           # Output contract for reviews
│   └── ...
└── tasks/
    └── {task_id}/
        └── actions.yaml               # Includes agent info per step
```

### 12.12 Benefits of Agent Specialization

| Benefit | How It Works |
|---------|--------------|
| **Separation of concerns** | Each agent focuses on one job |
| **Tool safety** | Agents can't access tools outside their role |
| **Quality through expertise** | System prompts tune thinking for the task |
| **Cross-validation** | Reviewers catch issues primary agents miss |
| **Clear accountability** | Audit trail shows exactly which agent decided what |
| **Trust through constraints** | Restricted capabilities = bounded risk |
| **Consistent output** | Each role produces contract-verified artifacts |

### 12.13 Project Customization

Projects can customize or extend agent definitions:

```yaml
# .agentforge/agents/software_developer.yaml (project override)

# Extend base definition
extends: "agentforge:software_developer"

# Override specific fields
identity:
  expertise:
    - Python development      # Base expertise
    - Django framework        # Project-specific
    - PostgreSQL              # Project-specific
    
capabilities:
  tools:
    allowed:
      - read_file
      - edit_file
      - create_file
      - run_tests
      - run_conformance_check
      - run_type_check
      - search_codebase
      - run_django_migrations  # Project-specific tool
      
constraints:
  - "Only modify files necessary to pass tests"
  - "Follow existing code patterns and style"
  - "All conformance checks must pass"
  - "Use Django ORM for database access"  # Project-specific
  - "Follow project's API versioning scheme"  # Project-specific
```

---

## Part 13: Flexible Pipeline Execution

Not all tasks require the full pipeline. A user might want only a design specification, or tests for an existing spec, or a security review. This section defines how AgentForge supports flexible entry points, exit points, iteration, and task composition—while maintaining the verification guarantees defined in Part 2 and Part 8.

### 13.1 Core Principle: Goal-Driven, Not Stage-Driven

Users express **goals**. The system determines **stages**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   RIGID PIPELINE (what we're moving beyond)                                 │
│                                                                              │
│   INTAKE → CLARIFY → ANALYZE → SPEC → RED → GREEN → REFACTOR → DELIVER     │
│   ────────────────────────────────────────────────────────────────────▶     │
│                     (must run all, in order)                                │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   FLEXIBLE PIPELINE (capability graph)                                      │
│                                                                              │
│   ┌────────┐    ┌─────────┐    ┌─────────┐    ┌──────┐                     │
│   │ INTAKE │───▶│ CLARIFY │───▶│ ANALYZE │───▶│ SPEC │──┬──▶ EXIT         │
│   └────────┘    └─────────┘    └─────────┘    └──────┘  │    (design)     │
│        ▲                                          ▲      │                  │
│        │                                          │      │                  │
│   [external                                  [iterate]   │                  │
│    artifact]                                      │      │                  │
│                                                   └──────┤                  │
│                                                          │                  │
│                                                          ▼                  │
│                                                     ┌─────┐                 │
│                                            ┌───────│ RED │──┬──▶ EXIT     │
│                                            │       └─────┘  │    (tests)  │
│                                       [external         │   │              │
│                                        spec]            ▼   │              │
│                                                    ┌───────┐│              │
│                                                    │ GREEN │┤              │
│                                                    └───────┘│              │
│                                                         │   │              │
│                                                         ▼   │              │
│                                                   ┌──────────┐             │
│                                                   │ REFACTOR │──▶ EXIT    │
│                                                   └──────────┘             │
│                                                         │                  │
│                                                         ▼                  │
│                                                   ┌─────────┐              │
│                                                   │ DELIVER │──▶ EXIT     │
│                                                   └─────────┘   (full)    │
│                                                                              │
│   Key capabilities:                                                         │
│   - Any stage can be an EXIT point (with verified artifact)                 │
│   - Some stages can ITERATE (loop with user feedback)                       │
│   - External artifacts can provide ENTRY points                             │
│   - Tasks can COMPOSE (build on artifacts from other tasks)                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Compatibility with Trust Model

**Critical Design Constraint:** Flexible execution does not weaken verification.

The trust equation from Part 8 remains:
```
TRUST = VERIFIED_INPUTS + CONSTRAINED_PROCESS + VERIFIED_OUTPUTS
```

How this applies to flexible execution:

| Scenario | Verification Approach |
|----------|----------------------|
| Early exit (e.g., exit at SPEC) | SPEC artifact validated against `specification` contract before exit |
| External artifact (e.g., --from-spec) | External artifact validated against `specification` contract before acceptance |
| Skipped stages | No verification needed—stages don't run, no artifacts produced |
| Iteration | Each iteration produces artifact validated against stage contract |
| Task composition | Referenced artifact re-validated against contract at import |

**Non-negotiable rule:** No artifact enters or exits the pipeline without contract validation. External artifacts are NOT trusted until validated.

```python
def import_external_artifact(
    self,
    artifact_path: Path,
    expected_contract: str
) -> ImportResult:
    """
    Import external artifact with mandatory validation.
    
    External artifacts are UNTRUSTED until validated.
    """
    # Load artifact
    artifact = yaml.safe_load(artifact_path.read_text())
    
    # MANDATORY: Validate against contract
    validation = self.contract_validator.validate(artifact, expected_contract)
    
    if not validation.passed:
        return ImportResult(
            success=False,
            error=f"External artifact failed {expected_contract} contract validation",
            violations=validation.errors
        )
    
    # Only now is it trusted
    return ImportResult(
        success=True,
        artifact=artifact,
        validation_hash=validation.artifact_hash  # Proof of validation
    )
```

### 13.3 Goal Types and Default Pipelines

User goals map to pipeline templates:

| Goal Type | Command | Default Entry | Default Exit | Stages Executed |
|-----------|---------|---------------|--------------|-----------------|
| `design` | `agentforge design "..."` | INTAKE | SPEC | INTAKE → CLARIFY → ANALYZE → SPEC |
| `implement` | `agentforge implement "..."` | INTAKE | DELIVER | Full pipeline |
| `test` | `agentforge test --spec X` | RED | RED | RED only |
| `review` | `agentforge review ./path` | ANALYZE | ANALYZE | ANALYZE only |
| `fix` | `agentforge fix V-xxx` | ANALYZE | GREEN | ANALYZE → GREEN |
| `document` | `agentforge document ./path` | ANALYZE | DELIVER | ANALYZE → DELIVER |

Goal type can be explicit or inferred:

```python
def classify_goal(self, goal_text: str, flags: dict) -> GoalType:
    """
    Classify user goal into pipeline type.
    
    Explicit flags take precedence over inference.
    """
    # Explicit goal type
    if flags.get("pipeline"):
        return GoalType(flags["pipeline"])
    
    # Infer from flags
    if flags.get("from_spec"):
        return GoalType.IMPLEMENT  # Has spec, wants implementation
    if flags.get("from_tests"):
        return GoalType.IMPLEMENT  # Has tests, wants implementation
    
    # Infer from goal text
    goal_lower = goal_text.lower()
    
    if any(word in goal_lower for word in ["design", "spec", "plan", "architect"]):
        return GoalType.DESIGN
    if any(word in goal_lower for word in ["test", "write tests"]):
        return GoalType.TEST
    if any(word in goal_lower for word in ["review", "analyze", "assess"]):
        return GoalType.REVIEW
    if any(word in goal_lower for word in ["fix", "repair", "resolve"]):
        return GoalType.FIX
    if any(word in goal_lower for word in ["document", "docs"]):
        return GoalType.DOCUMENT
    
    # Default: full implementation
    return GoalType.IMPLEMENT
```

### 13.4 Stage Properties

Each stage declares its flexibility capabilities:

```yaml
# Stage property definitions

stages:
  intake:
    entry_point: true           # Can start here
    exit_point: false           # Not useful as sole output
    iterable: false             # No iteration
    skippable_if: "external_spec_provided"
    output_contract: intake_record
    
  clarify:
    entry_point: false
    exit_point: false
    iterable: false
    skippable_if: "no_ambiguities OR external_spec_provided"
    output_contract: clarification
    
  analyze:
    entry_point: true           # Can start here for review tasks
    exit_point: true            # Can exit here for review tasks
    iterable: false
    skippable_if: never
    output_contract: analysis
    
  spec:
    entry_point: false
    exit_point: true            # Design tasks exit here
    iterable: true              # Can iterate on design
    max_iterations: 5
    skippable_if: "external_spec_provided"
    output_contract: specification
    reviewers: [security_architect]
    
  red:
    entry_point: true           # Can start here with external spec
    exit_point: true            # Test-only tasks exit here
    iterable: false             # Tests should be right first time
    skippable_if: "external_tests_provided"
    prerequisites: [specification]
    output_contract: test_suite
    
  green:
    entry_point: false
    exit_point: true            # Fix tasks might exit here
    iterable: false             # Conformance loop handles this
    skippable_if: never
    prerequisites: [specification, test_suite]
    output_contract: implementation
    
  refactor:
    entry_point: false
    exit_point: true
    iterable: false
    skippable_if: "trivial_change"
    prerequisites: [implementation]
    output_contract: implementation
    reviewers: [security_architect]
    
  deliver:
    entry_point: false
    exit_point: true            # Default exit for implementation
    iterable: false
    skippable_if: never
    prerequisites: [implementation]
    output_contract: delivery_report
```

### 13.5 Pipeline Templates

Pre-defined configurations for common goal types:

```yaml
# .agentforge/pipelines/design.yaml

pipeline:
  name: design
  description: "Design a solution, iterate on specification"
  goal_type: design
  
  stages:
    - name: intake
      required: true
      
    - name: clarify
      required: true
      skip_if: "no_ambiguities"
      
    - name: analyze
      required: true
      
    - name: spec
      required: true
      iterate: true
      iterate_prompt: "Review the specification. Approve, request changes, or exit."
      default_exit: true
      reviewers: [security_architect]

  exit:
    stage: spec
    deliverable: specification
    summary_template: "design_summary"
    
  continuation:
    prompt: "Would you like to continue to implementation?"
    next_pipeline: implement
    provides: [specification]  # What this pipeline provides to the next
```

```yaml
# .agentforge/pipelines/implement.yaml

pipeline:
  name: implement
  description: "Full implementation from request to delivery"
  goal_type: implement
  
  accepts_external:
    specification:
      contract: specification
      skips_to: red
    test_suite:
      contract: test_suite
      skips_to: green
      requires: [specification]  # Must also have spec
  
  stages:
    - name: intake
      required: true
      skip_if: "spec_provided"
      
    - name: clarify
      required: true
      skip_if: "spec_provided"
      
    - name: analyze
      required: true
      
    - name: spec
      required: true
      skip_if: "spec_provided"
      iterate: true
      reviewers: [security_architect]
      
    - name: red
      required: true
      skip_if: "tests_provided"
      
    - name: green
      required: true
      
    - name: refactor
      required: true
      reviewers: [security_architect]
      
    - name: deliver
      required: true
      default_exit: true

  exit:
    stage: deliver
    deliverable: delivery_report
```

```yaml
# .agentforge/pipelines/test.yaml

pipeline:
  name: test
  description: "Write tests for existing specification"
  goal_type: test
  
  requires_external:
    specification:
      contract: specification
      source: "user_provided OR task_reference"
      
  stages:
    - name: analyze
      required: true
      purpose: "Understand codebase context for test design"
      
    - name: red
      required: true
      default_exit: true

  exit:
    stage: red
    deliverable: test_suite
```

### 13.6 Iteration Protocol

For stages that support iteration, a structured feedback loop:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ITERATION LOOP                                                            │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                                                                      │   │
│   │   Agent produces artifact (version N)                                │   │
│   │                │                                                     │   │
│   │                ▼                                                     │   │
│   │   Contract validation (must pass)                                    │   │
│   │                │                                                     │   │
│   │                ▼                                                     │   │
│   │   Artifact presented to user                                         │   │
│   │                │                                                     │   │
│   │                ▼                                                     │   │
│   │   ┌─────────────────────────────────────────────────────────────┐   │   │
│   │   │                                                              │   │   │
│   │   │  User Decision:                                              │   │   │
│   │   │                                                              │   │   │
│   │   │  [APPROVE]  ──▶ Proceed to next stage                       │   │   │
│   │   │                 (or exit if default_exit)                    │   │   │
│   │   │                                                              │   │   │
│   │   │  [REVISE]   ──▶ Provide feedback ─┐                         │   │   │
│   │   │                                    │                         │   │   │
│   │   │  [REJECT]   ──▶ Go back to previous stage                   │   │   │
│   │   │                                                              │   │   │
│   │   │  [EXIT]     ──▶ Exit pipeline with current artifact         │   │   │
│   │   │                 (delivers version N as final)                │   │   │
│   │   │                                                              │   │   │
│   │   │  [CONTINUE] ──▶ Extend pipeline to later stage              │   │   │
│   │   │                 (e.g., design → implement)                   │   │   │
│   │   │                                                              │   │   │
│   │   └─────────────────────────────────────────────────────────────┘   │   │
│   │                                    │                                 │   │
│   │                                    │ (if REVISE)                     │   │
│   │                                    ▼                                 │   │
│   │   Feedback added to agent context                                    │   │
│   │                │                                                     │   │
│   │                ▼                                                     │   │
│   │   Agent revises artifact (version N+1) ──────────────────────────┐  │   │
│   │                                                                   │  │   │
│   │   ◀───────────────────────────────────────────────────────────────┘  │   │
│   │                                                                      │   │
│   │   (loop continues until APPROVE, REJECT, EXIT, or max iterations)   │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Feedback Structure

User feedback is structured for agent consumption:

```yaml
# iteration_feedback.yaml

feedback:
  task_id: "task-20251231-oauth2"
  stage: "spec"
  iteration: 2
  previous_version: "artifacts/specification_v1.yaml"
  
  decision: "revise"
  
  overall_comments: |
    The specification is on the right track, but needs more detail
    in several areas before we can proceed to implementation.
    
  specific_issues:
    - location: "requirements.REQ-003"
      issue: "Missing acceptance criteria for token refresh"
      suggestion: "Add measurable criteria like 'refresh completes within 100ms'"
      priority: "must_address"
      
    - location: "interfaces.oauth_callback"
      issue: "No input validation specified"
      suggestion: "Add URL whitelist validation for callback parameter"
      priority: "must_address"
      
    - location: "constraints"
      issue: "Rate limiting not addressed"
      suggestion: "Consider adding rate limit requirements"
      priority: "should_consider"
      
  timestamp: "2025-12-31T10:30:00Z"
  
# Agent receives this in context for next iteration
```

#### Feedback in Agent Context

Feedback integrates with minimal context architecture (Part 3):

```yaml
# Added to current_state when iterating

iteration_context:
  iteration: 2
  max_iterations: 5
  
  previous_artifact: "artifacts/specification_v1.yaml"
  
  feedback:
    overall: "Needs more detail in several areas"
    must_address:
      - "REQ-003: Add acceptance criteria for token refresh"
      - "oauth_callback: Add URL whitelist validation"
    should_consider:
      - "Add rate limiting requirements"
      
  instruction: |
    Revise the specification to address the MUST_ADDRESS items.
    Consider the SHOULD_CONSIDER items.
    Produce version 2 of the specification.
```

### 13.7 Artifact Lifecycle

Artifacts have explicit states that determine what operations are valid:

```yaml
artifact_states:
  draft:
    description: "Being worked on by agent"
    valid_operations: [update, validate]
    can_exit_pipeline: false
    
  pending_review:
    description: "Awaiting user feedback in iteration loop"
    valid_operations: [approve, revise, reject, exit]
    can_exit_pipeline: true  # User can exit with current version
    
  approved:
    description: "User accepted, proceeding to next stage"
    valid_operations: [proceed, extend]
    can_exit_pipeline: true
    
  final:
    description: "Pipeline exited, this is the deliverable"
    valid_operations: [read, export, reference]
    can_exit_pipeline: false  # Already exited
    immutable: true  # Cannot be modified
    
transitions:
  draft → pending_review:     "Agent completes + validation passes"
  pending_review → draft:     "User requests revision"
  pending_review → approved:  "User approves"
  pending_review → final:     "User exits pipeline"
  approved → final:           "Pipeline completes OR user exits"
  approved → draft:           "User rejects (goes back)"
```

### 13.8 Task Composition

Tasks can reference artifacts from other tasks:

```bash
# Day 1: Design session
agentforge design "Add OAuth2 authentication to the API"
# Task: task-123-design-oauth
# Iterate on spec, exit with approved specification

# Day 2: Implementation session  
agentforge implement --from-task task-123-design-oauth "Implement the OAuth2 spec"
# Uses verified specification from task-123
# Skips to RED phase
```

Implementation:

```yaml
# Task state showing composition

task:
  id: "task-456-implement-oauth"
  goal: "Implement the OAuth2 spec we designed"
  goal_type: implement
  
  inputs:
    external:
      specification:
        source: "task_reference"
        task_id: "task-123-design-oauth"
        artifact_path: "artifacts/specification_final.yaml"
        imported_at: "2025-12-31T14:00:00Z"
        
        # CRITICAL: Validation at import time
        validation:
          contract: "specification"
          status: "passed"
          hash: "abc123..."  # Proof of validation
          
  pipeline:
    template: "implement"
    entry_stage: "red"        # Skip to RED, we have the spec
    exit_stage: "deliver"
    
    skipped_stages:
      - intake: "spec_provided"
      - clarify: "spec_provided"
      - spec: "spec_provided"
```

#### Artifact Staleness Check

When referencing artifacts from other tasks, check for staleness:

```python
def validate_referenced_artifact(
    self,
    source_task_id: str,
    artifact_type: str,
    current_codebase_hash: str
) -> ValidationResult:
    """
    Validate that a referenced artifact is still valid.
    
    Checks:
    1. Contract validation (always)
    2. Staleness (has codebase changed significantly?)
    """
    # Load artifact
    artifact = self.load_artifact(source_task_id, artifact_type)
    
    # 1. Contract validation
    contract_check = self.validate_contract(artifact, artifact_type)
    if not contract_check.passed:
        return ValidationResult(
            valid=False,
            error="Contract validation failed",
            details=contract_check.errors
        )
    
    # 2. Staleness check
    source_task = self.load_task(source_task_id)
    original_codebase_hash = source_task.codebase_hash
    
    if original_codebase_hash != current_codebase_hash:
        # Codebase has changed - analyze impact
        changes = self.analyze_codebase_changes(
            original_codebase_hash,
            current_codebase_hash
        )
        
        if changes.affects_artifact(artifact):
            return ValidationResult(
                valid=False,
                error="Codebase has changed in ways that may invalidate this artifact",
                details=changes.relevant_changes,
                suggestion="Consider re-running the design phase"
            )
    
    return ValidationResult(valid=True, artifact=artifact)
```

### 13.9 Command Interface

Complete CLI for flexible execution:

```bash
# ═══════════════════════════════════════════════════════════════════════════
# GOAL-BASED COMMANDS (system determines pipeline)
# ═══════════════════════════════════════════════════════════════════════════

agentforge design "Add OAuth2 authentication"
# → Runs: INTAKE → CLARIFY → ANALYZE → SPEC
# → Exits at: SPEC (with iteration)

agentforge implement "Add OAuth2 authentication"
# → Runs: Full pipeline
# → Exits at: DELIVER

agentforge test --spec ./spec.yaml
# → Runs: ANALYZE → RED
# → Exits at: RED

agentforge review ./src/auth/
# → Runs: ANALYZE only
# → Exits at: ANALYZE

agentforge fix V-04b31cde217a
# → Runs: ANALYZE → GREEN
# → Exits at: GREEN

# ═══════════════════════════════════════════════════════════════════════════
# EXPLICIT PIPELINE CONTROL
# ═══════════════════════════════════════════════════════════════════════════

agentforge start "Add OAuth2" --pipeline design
# Explicit pipeline selection

agentforge start "Add OAuth2" --through spec
# Run until SPEC then exit

agentforge start "Add OAuth2" --exit-after analyze
# Run until ANALYZE then exit

agentforge start "Add OAuth2" --skip-to red --spec ./spec.yaml
# Skip to RED with external spec

# ═══════════════════════════════════════════════════════════════════════════
# EXTERNAL ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

agentforge implement --from-spec ./spec.yaml "Implement OAuth2"
# Provide external spec, skip to RED

agentforge implement --from-task task-123 "Continue OAuth2"
# Use spec from prior task

agentforge implement --from-spec ./spec.yaml --from-tests ./tests/ "Implement"
# Provide both spec and tests, skip to GREEN

# ═══════════════════════════════════════════════════════════════════════════
# ITERATION CONTROL
# ═══════════════════════════════════════════════════════════════════════════

agentforge design "Add OAuth2" --iterate
# Pause for feedback at each iterable stage

agentforge design "Add OAuth2" --iterate-at spec
# Only pause at SPEC

agentforge design "Add OAuth2" --no-iterate
# Skip all iteration (auto-approve)

# ═══════════════════════════════════════════════════════════════════════════
# TASK CONTINUATION
# ═══════════════════════════════════════════════════════════════════════════

agentforge continue task-123
# Resume where task left off

agentforge continue task-123 --extend-to deliver
# Continue design task through to delivery

agentforge continue task-123 --revise
# Re-enter iteration on current stage

agentforge feedback task-123 "Add rate limiting to the spec"
# Provide iteration feedback (triggers revision)

# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE INFORMATION
# ═══════════════════════════════════════════════════════════════════════════

agentforge pipelines list
# Show available pipeline templates

agentforge pipelines show design
# Show design pipeline stages and options

agentforge pipelines validate ./custom-pipeline.yaml
# Validate custom pipeline definition
```

### 13.10 State Model Extensions

Extended state.yaml to support flexible execution:

```yaml
# state.yaml with flexible execution support

task:
  id: "task-20251231-oauth2"
  goal: "Design OAuth2 authentication"
  goal_type: "design"
  
pipeline:
  template: "design"
  entry_stage: "intake"
  exit_stage: "spec"           # Where we'll stop
  current_stage: "spec"
  
  # Stage statuses
  stages:
    intake:
      status: "completed"
      artifact: "artifacts/intake_record.yaml"
      completed_at: "2025-12-31T10:05:00Z"
      
    clarify:
      status: "completed"
      artifact: "artifacts/clarification.yaml"
      completed_at: "2025-12-31T10:12:00Z"
      
    analyze:
      status: "completed"
      artifact: "artifacts/analysis.yaml"
      completed_at: "2025-12-31T10:25:00Z"
      
    spec:
      status: "iterating"      # In iteration loop
      artifact: "artifacts/specification_v2.yaml"
      iteration:
        current: 2
        max: 5
        history:
          - version: 1
            artifact: "artifacts/specification_v1.yaml"
            presented_at: "2025-12-31T10:30:00Z"
            decision: "revise"
            feedback_ref: "iteration_history/spec/v1_feedback.yaml"
        awaiting: "user_decision"
        
    # Stages not yet reached
    red:
      status: "pending"
    green:
      status: "pending"
    refactor:
      status: "pending"
    deliver:
      status: "pending"
      
  # Skipped stages (if any)
  skipped:
    - stage: "clarify"
      reason: "no_ambiguities"  # Only if actually skipped

# External inputs (if provided)
external_inputs:
  # None for this task, but would be:
  # specification:
  #   source: "user_provided"
  #   path: "/path/to/spec.yaml"
  #   validated_at: "..."
  #   validation_hash: "..."

# Continuation options
continuation:
  can_extend: true
  available_pipelines: ["implement"]
  provides_artifacts: ["specification"]
```

### 13.11 Integration with Agent System (Part 12)

Flexible execution integrates seamlessly with agent specialization:

```python
class FlexibleAgentOrchestrator:
    """
    Extends AgentOrchestrator to support flexible pipeline execution.
    """
    
    def execute_pipeline(
        self,
        task_id: str,
        pipeline: PipelineConfig,
        external_inputs: Dict[str, Artifact] = None
    ) -> PipelineResult:
        """Execute pipeline with flexibility."""
        
        # Determine which stages to execute
        stages = self.compute_stages_to_execute(
            pipeline=pipeline,
            external_inputs=external_inputs
        )
        
        for stage in stages:
            # Load appropriate agent(s) for stage
            stage_config = self.get_stage_config(stage.name)
            primary_agent = self.load_agent(stage_config.primary)
            
            # Determine input artifact
            if stage.is_entry_point and external_inputs:
                input_artifact = external_inputs.get(stage.input_type)
            else:
                input_artifact = self.get_previous_artifact(task_id, stage)
            
            # Execute stage with agent
            result = self.execute_stage_with_agent(
                task_id=task_id,
                stage=stage,
                agent=primary_agent,
                input_artifact=input_artifact
            )
            
            if not result.success:
                return PipelineResult(success=False, error=result.error)
            
            # Handle reviews (from Part 12)
            if stage_config.reviewers:
                result = self.execute_review_loop(
                    primary_agent=primary_agent,
                    result=result,
                    reviewers=stage_config.reviewers,
                    task_id=task_id
                )
            
            # Handle iteration
            if stage.iterate and pipeline.iteration_enabled:
                result = self.handle_iteration_loop(
                    task_id=task_id,
                    stage=stage,
                    agent=primary_agent,
                    result=result
                )
                
                if result.exit_requested:
                    return self.finalize_exit(task_id, stage, result)
            
            # Check for exit
            if stage.name == pipeline.exit_stage:
                return self.finalize_exit(task_id, stage, result)
        
        return PipelineResult(success=True, task_id=task_id)
```

### 13.12 Audit Trail Extensions

Audit trail captures flexible execution events:

```yaml
# actions.yaml extended for flexible execution

task_id: "task-20251231-oauth2"
pipeline:
  template: "design"
  entry_stage: "intake"
  exit_stage: "spec"
  
actions:
  # ... regular step actions ...
  
  # Iteration events
  - type: "iteration_presented"
    timestamp: "2025-12-31T10:30:00Z"
    stage: "spec"
    iteration: 1
    artifact: "artifacts/specification_v1.yaml"
    artifact_hash: "abc123"
    
  - type: "user_decision"
    timestamp: "2025-12-31T10:45:00Z"
    stage: "spec"
    iteration: 1
    decision: "revise"
    feedback_ref: "iteration_history/spec/v1_feedback.yaml"
    
  - type: "iteration_started"
    timestamp: "2025-12-31T10:45:01Z"
    stage: "spec"
    iteration: 2
    input_feedback: "iteration_history/spec/v1_feedback.yaml"
    
  # ... more step actions ...
  
  - type: "user_decision"
    timestamp: "2025-12-31T11:15:00Z"
    stage: "spec"
    iteration: 2
    decision: "approve"
    artifact: "artifacts/specification_v2.yaml"
    artifact_hash: "def456"
    
  - type: "pipeline_exit"
    timestamp: "2025-12-31T11:15:01Z"
    exit_stage: "spec"
    exit_type: "default_exit"  # vs "early_exit" or "user_exit"
    deliverable: "artifacts/specification_final.yaml"
    
# External input events (if applicable)
external_inputs:
  - type: "external_artifact_imported"
    timestamp: "2025-12-31T10:00:00Z"
    artifact_type: "specification"
    source_path: "/user/provided/spec.yaml"
    validation:
      contract: "specification"
      status: "passed"
      hash: "xyz789"
```

### 13.13 Dashboard Extensions (Part 11)

Task summary extended for flexible execution:

```yaml
# Extended task_summary for dashboard

task_summary:
  task_id: "task-20251231-oauth2"
  goal: "Design OAuth2 authentication"
  goal_type: "design"
  
  pipeline:
    template: "design"
    entry_stage: "intake"
    exit_stage: "spec"
    progress: 0.85              # Through exit stage
    
  current_stage:
    name: "spec"
    status: "iterating"
    iteration: 2
    awaiting: "user_decision"   # Dashboard can highlight this
    
  iteration_summary:
    stage: "spec"
    current: 2
    max: 5
    decisions:
      - iteration: 1
        decision: "revise"
        at: "2025-12-31T10:45:00Z"
        
  available_actions:
    - "approve"     # Accept current spec
    - "revise"      # Request changes
    - "exit"        # Exit with current
    - "extend"      # Continue to implementation
```

Dashboard UI shows:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Task: Design OAuth2 authentication                                          │
│                                                                              │
│ Pipeline: design    Exit: SPEC                                              │
│                                                                              │
│ INTAKE ✓ ━━━ CLARIFY ✓ ━━━ ANALYZE ✓ ━━━ SPEC ●                            │
│                                            ↑                                 │
│                                      ITERATING                               │
│                                      Round 2/5                               │
│                                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ⏳ AWAITING YOUR DECISION                                                │ │
│ │                                                                          │ │
│ │ The specification (v2) is ready for review.                             │ │
│ │                                                                          │ │
│ │ [View Spec]  [Approve]  [Request Changes]  [Exit]  [Extend to Impl]    │ │
│ │                                                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.14 Summary: Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Verification preserved** | All artifacts validated against contracts—external, internal, at entry, at exit, always |
| **Goals, not stages** | Users express intent; system determines pipeline |
| **Flexible but constrained** | Entry/exit points configurable within pipeline rules |
| **Iteration is optional** | Can be enabled/disabled per stage and per run |
| **Composition enabled** | Tasks can build on artifacts from other tasks |
| **Audit trail complete** | Every decision, iteration, and external input recorded |
| **Agent system compatible** | Same agent specialization, just different stage sequences |
| **Minimal context compatible** | Feedback becomes part of context, same token budget |

### 13.15 Compatibility Matrix

How flexible execution interacts with other parts:

| Part | Interaction | Compatibility |
|------|-------------|---------------|
| **Part 2: Verification Chain** | External artifacts validated; early exits produce verified artifacts | ✅ Fully compatible |
| **Part 3: Minimal Context** | Iteration feedback added to context; same token budget | ✅ Fully compatible |
| **Part 4: Pipeline Controller** | Extended, not replaced; core loop unchanged | ✅ Extends Part 4 |
| **Part 5: Audit Trail** | New event types added; same append-only structure | ✅ Fully compatible |
| **Part 6: Self-Clarification** | Iteration is refinement; clarification is ambiguity—different purposes | ✅ Complementary |
| **Part 8: Trust Model** | Trust equation unchanged; verification at all boundaries | ✅ Fully compatible |
| **Part 11: Dashboard** | New UI elements for iteration and decisions | ✅ Extends Part 11 |
| **Part 12: Agent System** | Same agents execute; just different stage sequences | ✅ Fully compatible |

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
| **State Aggregator** | Component that computes dashboard summaries from state store |
| **Task Summary** | High-level view of a task's status and progress |
| **Step Detail** | Full context and result of a single agent step |
| **Agent** | Specialized persona with restricted tools and expertise |
| **Agent Definition** | YAML file defining an agent's identity, tools, and constraints |
| **Primary Agent** | Agent responsible for executing a stage |
| **Reviewer Agent** | Agent that validates another agent's output |
| **Review Loop** | Cycle where reviewers validate and primary agent revises |
| **Tool Restriction** | Enforcement of allowed/forbidden tools per agent role |
| **Path Constraint** | Rule limiting which files an agent can create/modify |
| **Handoff** | Verified artifact passed from one agent to another |
| **Goal Type** | Classification of user intent (design, implement, test, etc.) |
| **Pipeline Template** | Pre-defined stage configuration for a goal type |
| **Entry Point** | Stage where pipeline execution begins |
| **Exit Point** | Stage where pipeline execution ends (delivers artifact) |
| **Iteration** | User feedback loop to refine an artifact |
| **External Artifact** | User-provided artifact that skips earlier stages |
| **Task Composition** | Building a task using artifacts from another task |
| **Artifact Lifecycle** | States an artifact moves through (draft → pending → approved → final) |
| **Early Exit** | Exiting pipeline before the default exit stage |
| **Pipeline Extension** | Continuing a task beyond its original exit stage |

### B. File Locations

```
.agentforge/
├── config/
│   ├── settings.yaml         # Global settings
│   └── repos.yaml            # Repository definitions
├── agents/                   # Agent definitions
│   ├── requirements_analyst.yaml
│   ├── business_analyst.yaml
│   ├── software_architect.yaml
│   ├── security_architect.yaml
│   ├── test_engineer.yaml
│   ├── software_developer.yaml
│   ├── senior_developer.yaml
│   └── devops_engineer.yaml
├── pipelines/                # Pipeline templates
│   ├── design.yaml           # Design pipeline (exits at SPEC)
│   ├── implement.yaml        # Full implementation pipeline
│   ├── test.yaml             # Test-only pipeline
│   ├── review.yaml           # Review pipeline
│   └── fix.yaml              # Violation fix pipeline
├── orchestration/
│   └── stage_config.yaml     # Stage → Agent mapping
├── contracts/                # Contract definitions
│   ├── agent_definition.yaml # Meta-contract for agent definitions
│   ├── pipeline_template.yaml# Meta-contract for pipelines
│   └── ...
├── tasks/                    # Active and completed tasks
│   └── {task_id}/
│       ├── task.yaml         # Goal, goal_type, constraints
│       ├── state.yaml        # Pipeline state, iteration state
│       ├── actions.yaml      # Complete step history with agent info
│       ├── working_memory.yaml
│       ├── external_inputs/  # User-provided artifacts (validated)
│       │   └── specification.yaml
│       ├── iteration_history/# User feedback per stage
│       │   └── spec/
│       │       ├── v1_feedback.yaml
│       │       └── v2_approval.yaml
│       └── artifacts/
│           ├── intake_record.yaml
│           ├── specification_v1.yaml  # Iteration versions
│           ├── specification_v2.yaml
│           └── specification_final.yaml
├── violations/               # Conformance violations
├── escalations/              # Pending escalations
└── audit/                    # Audit reports
```

### C. CLI Reference

```bash
# ═══════════════════════════════════════════════════════════════════════════
# GOAL-BASED COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

agentforge design "request"             # Design pipeline (exits at SPEC)
agentforge implement "request"          # Full implementation pipeline
agentforge test --spec ./spec.yaml      # Test pipeline (RED only)
agentforge review ./path                # Review pipeline (ANALYZE only)
agentforge fix {violation_id}           # Fix pipeline (ANALYZE → GREEN)

# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE CONTROL
# ═══════════════════════════════════════════════════════════════════════════

agentforge start "request"              # Start (auto-detect goal type)
agentforge start "request" --pipeline design  # Explicit pipeline
agentforge start "request" --through spec     # Exit after SPEC
agentforge start "request" --exit-after analyze  # Exit after ANALYZE
agentforge start "request" --iterate          # Pause at iterable stages
agentforge start "request" --iterate-at spec  # Pause only at SPEC
agentforge start "request" --no-iterate       # Skip all iteration

# ═══════════════════════════════════════════════════════════════════════════
# EXTERNAL ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

agentforge implement --from-spec ./spec.yaml "request"  # Skip to RED
agentforge implement --from-task task-123 "request"     # Use prior task's spec
agentforge implement --from-tests ./tests/ --from-spec ./spec.yaml "request"

# ═══════════════════════════════════════════════════════════════════════════
# TASK MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

agentforge status [--all]               # Check task status
agentforge status --watch               # Live status updates
agentforge status {task_id}             # Detailed task view
agentforge status {task_id} --phase {p} # Phase detail
agentforge status {task_id} --step {n}  # Step detail with context
agentforge resume {task_id}             # Resume paused task
agentforge abort {task_id}              # Abort task

# ═══════════════════════════════════════════════════════════════════════════
# ITERATION & CONTINUATION
# ═══════════════════════════════════════════════════════════════════════════

agentforge continue {task_id}           # Resume where task left off
agentforge continue {task_id} --extend-to deliver  # Extend to later stage
agentforge continue {task_id} --revise  # Re-enter iteration
agentforge feedback {task_id} "comments"  # Provide iteration feedback
agentforge approve {task_id}            # Approve current iteration
agentforge reject {task_id}             # Reject and go back

# ═══════════════════════════════════════════════════════════════════════════
# ESCALATION
# ═══════════════════════════════════════════════════════════════════════════

agentforge escalations list             # Show pending escalations
agentforge resolve {escalation_id}      # Resolve escalation

# ═══════════════════════════════════════════════════════════════════════════
# AUDIT & ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

agentforge inspect {task_id}            # Inspect task state
agentforge audit {task_id}              # Generate audit report
agentforge replay {task_id}             # Replay task actions
agentforge fork {task_id}               # Fork from checkpoint
agentforge cost {task_id}               # Show cost breakdown

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

agentforge dashboard                    # Launch web dashboard
agentforge dashboard --port {port}      # Custom port

# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

agentforge pipelines list               # Show available pipelines
agentforge pipelines show {name}        # Show pipeline details
agentforge pipelines validate ./custom.yaml  # Validate custom pipeline

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

agentforge config show                  # Show configuration
agentforge repo add {path}              # Add repository
```

---

**End of Specification**