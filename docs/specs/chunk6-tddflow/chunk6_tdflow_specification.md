# Chunk 6: TDFLOW - Test-Driven Implementation Workflow

## Specification Document

**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2025-12-30  
**Depends On:** Chunk 3 (Conformance), Chunk 4 (Discovery), Chunk 5 (Bridge)

---

## Executive Summary

TDFLOW extends AgentForge from specification to implementation. It implements a test-driven development workflow where the agent writes failing tests first, then implements code to pass them, then refactors - all while maintaining traceability to the original specification.

**Key Value Proposition:**
- SPEC workflow produces `specification.yaml`
- TDFLOW consumes specification, produces tested code
- Full traceability: requirement → test → implementation

---

## 1. Problem Statement

### 1.1 Current State

The SPEC workflow produces detailed specifications:
```yaml
# specification.yaml
components:
  - name: DiscountService
    type: class
    methods:
      - name: ApplyDiscount
        parameters: [order: Order, code: string]
        returns: Result<Order>
        behavior: "Validates code, applies discount, returns modified order"
```

But there's no automated path from specification to implementation.

### 1.2 Gap

- Specifications are detailed but not executable
- No test generation from specs
- No implementation verification against specs
- Manual handoff breaks traceability

### 1.3 Solution

TDFLOW workflow:
```
specification.yaml → RED (failing test) → GREEN (implementation) → REFACTOR → verified code
```

Each phase is verifiable and produces artifacts.

---

## 2. TDFLOW Workflow

### 2.1 State Machine

```
┌─────────────┐
│    INIT     │ Load specification
└──────┬──────┘
       │
       ▼
┌─────────────┐
│     RED     │ Generate failing test
└──────┬──────┘
       │ verify: test exists AND test fails
       ▼
┌─────────────┐
│    GREEN    │ Generate implementation
└──────┬──────┘
       │ verify: test passes
       ▼
┌─────────────┐
│  REFACTOR   │ Clean up (optional)
└──────┬──────┘
       │ verify: test still passes
       ▼
┌─────────────┐
│   VERIFY    │ Run conformance + coverage
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    DONE     │ All checks pass
└─────────────┘
```

### 2.2 Phase Definitions

#### INIT Phase
**Input:** `specification.yaml` from SPEC workflow  
**Output:** `tdflow_session.yaml` with parsed spec  
**Verification:** Spec is valid, components extractable

#### RED Phase
**Input:** Component from spec (one at a time)  
**Output:** Test file(s) that fail  
**Verification:** 
- Test file exists at expected location
- Test compiles/parses
- Test FAILS when run (no implementation yet)

**Exit Criteria:** `dotnet test` or `pytest` returns failure

#### GREEN Phase
**Input:** Failing test + spec requirements  
**Output:** Implementation file(s)  
**Verification:**
- Implementation file exists
- Implementation compiles
- Test PASSES

**Exit Criteria:** `dotnet test` or `pytest` returns success

#### REFACTOR Phase (Optional)
**Input:** Passing implementation  
**Output:** Cleaned implementation  
**Verification:**
- Test still passes
- Conformance checks pass
- No new violations introduced

**Exit Criteria:** Tests pass AND conformance clean

#### VERIFY Phase
**Input:** Complete implementation  
**Output:** Verification report  
**Verification:**
- All tests pass
- Conformance checks pass
- Coverage meets threshold
- Spec requirements traceable

---

## 3. Test Generation Strategy

### 3.1 Test Structure

For each component in spec, generate:

```
tests/
├── Unit/
│   └── {Component}Tests.cs      # Unit tests per method
└── Integration/
    └── {Component}IntegrationTests.cs  # Integration tests
```

### 3.2 Test Template (C#)

```csharp
// Generated from specification.yaml
// Component: {component.name}
// Method: {method.name}

namespace {Namespace}.Tests.Unit;

public class {Component}Tests
{
    // RED: This test should FAIL until implementation exists
    
    [Fact]
    public void {Method}_WhenValidInput_ShouldReturnExpectedResult()
    {
        // Arrange
        var sut = new {Component}({dependencies});
        {arrange_from_spec}
        
        // Act
        var result = sut.{Method}({parameters});
        
        // Assert
        {assertions_from_spec}
    }
    
    [Fact]
    public void {Method}_WhenInvalidInput_ShouldReturnError()
    {
        // Arrange
        var sut = new {Component}({dependencies});
        
        // Act
        var result = sut.{Method}({invalid_parameters});
        
        // Assert
        result.IsFailure.Should().BeTrue();
    }
}
```

### 3.3 Test Template (Python)

```python
# Generated from specification.yaml
# Component: {component.name}
# Method: {method.name}

import pytest
from {module} import {Component}

class Test{Component}:
    """RED: These tests should FAIL until implementation exists."""
    
    def test_{method}_when_valid_input_returns_expected(self):
        # Arrange
        sut = {Component}({dependencies})
        {arrange_from_spec}
        
        # Act
        result = sut.{method}({parameters})
        
        # Assert
        {assertions_from_spec}
    
    def test_{method}_when_invalid_input_returns_error(self):
        # Arrange
        sut = {Component}({dependencies})
        
        # Act
        result = sut.{method}({invalid_parameters})
        
        # Assert
        assert result.is_failure
```

### 3.4 Spec-to-Test Mapping

| Spec Element | Test Generation |
|--------------|-----------------|
| `method.parameters` | Test input setup |
| `method.returns` | Assert return type |
| `method.behavior` | Assert behavior (LLM interprets) |
| `method.errors` | Error case tests |
| `method.preconditions` | Guard clause tests |
| `method.postconditions` | State verification tests |
| `component.invariants` | Invariant tests |

---

## 4. Implementation Generation

### 4.1 Implementation Structure

```
src/
└── {Layer}/
    └── {Component}.cs
```

### 4.2 Implementation Template (C#)

```csharp
// Generated to pass tests from specification.yaml
// Component: {component.name}

namespace {Namespace};

public class {Component} : I{Component}
{
    private readonly {dependencies};
    
    public {Component}({dependency_params})
    {
        {dependency_assignments}
    }
    
    public {ReturnType} {Method}({parameters})
    {
        // Implementation to satisfy:
        // - Behavior: {method.behavior}
        // - Preconditions: {method.preconditions}
        // - Postconditions: {method.postconditions}
        
        {implementation}
    }
}
```

### 4.3 Context Retrieval for Implementation

GREEN phase uses context from:
1. **Failing test** - What needs to pass
2. **Specification** - Behavioral requirements
3. **Codebase profile** - Patterns to follow
4. **Existing code** - Similar implementations (via LSP/vector search)

---

## 5. Verification Strategy

### 5.1 RED Phase Verification

```bash
# Must fail with specific exit code
dotnet test --filter "{TestClass}" && exit 1 || exit 0
```

Expected: Test runner finds tests, tests FAIL, runner exits non-zero.

### 5.2 GREEN Phase Verification

```bash
# Must pass
dotnet test --filter "{TestClass}"
```

Expected: All tests pass, runner exits zero.

### 5.3 REFACTOR Phase Verification

```bash
# Tests still pass
dotnet test --filter "{TestClass}"

# No new conformance violations
agentforge conformance check --baseline
```

### 5.4 Final Verification

```yaml
# verification_report.yaml
spec_file: specification.yaml
implementation_verified: true

components:
  - name: DiscountService
    tests:
      - name: ApplyDiscount_WhenValidCode_ReturnsDiscountedOrder
        status: pass
      - name: ApplyDiscount_WhenInvalidCode_ReturnsError
        status: pass
    coverage: 92%
    conformance: pass
    
traceability:
  - requirement: "Apply discount to order"
    test: ApplyDiscount_WhenValidCode_ReturnsDiscountedOrder
    implementation: DiscountService.ApplyDiscount
    status: verified
```

---

## 6. CLI Interface

### 6.1 Commands

```bash
# Start TDFLOW from specification
agentforge tdflow start --spec specification.yaml

# Run RED phase (generate tests)
agentforge tdflow red [--component NAME]

# Run GREEN phase (generate implementation)
agentforge tdflow green [--component NAME]

# Run REFACTOR phase
agentforge tdflow refactor [--component NAME]

# Verify complete implementation
agentforge tdflow verify

# Show session status
agentforge tdflow status

# Resume interrupted session
agentforge tdflow resume
```

### 6.2 Example Session

```bash
$ agentforge tdflow start --spec .agentforge/workspace/spec/specification.yaml

TDFLOW Session Started
━━━━━━━━━━━━━━━━━━━━━━
Specification: specification.yaml
Components: 3 (DiscountService, DiscountValidator, DiscountRepository)
Session: .agentforge/tdflow/session_20251230.yaml

$ agentforge tdflow red --component DiscountService

RED Phase: DiscountService
━━━━━━━━━━━━━━━━━━━━━━━━━━
Generating tests for 3 methods...

Created: tests/Unit/DiscountServiceTests.cs
  - ApplyDiscount_WhenValidCode_ReturnsDiscountedOrder
  - ApplyDiscount_WhenInvalidCode_ReturnsError
  - ApplyDiscount_WhenExpiredCode_ReturnsError

Running tests...
✗ 3 tests FAILED (expected - no implementation yet)

RED phase complete. Run 'agentforge tdflow green' to implement.

$ agentforge tdflow green --component DiscountService

GREEN Phase: DiscountService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generating implementation to pass tests...

Context loaded:
  - Spec: DiscountService requirements
  - Tests: 3 failing tests
  - Patterns: Result<T>, Repository pattern
  - Similar: OrderService.ApplyPromotion (85% similar)

Created: src/Application/Services/DiscountService.cs

Running tests...
✓ 3 tests PASSED

GREEN phase complete. Run 'agentforge tdflow refactor' or 'agentforge tdflow verify'.

$ agentforge tdflow verify

VERIFY Phase
━━━━━━━━━━━━
Component: DiscountService

Tests:        ✓ 3/3 passing
Coverage:     92% (target: 80%)
Conformance:  ✓ No violations
Traceability: ✓ All requirements mapped

✓ DiscountService verified successfully
```

---

## 7. Session Management

### 7.1 Session File

```yaml
# .agentforge/tdflow/session_20251230.yaml
schema_version: "1.0"
session_id: "tdflow_20251230_143052"
started_at: "2025-12-30T14:30:52Z"

source:
  spec_file: ".agentforge/workspace/spec/specification.yaml"
  spec_hash: "sha256:abc123"

config:
  test_framework: xunit  # or pytest
  coverage_threshold: 80
  auto_refactor: false

components:
  - name: DiscountService
    status: green  # init | red | green | refactor | verified
    tests:
      file: tests/Unit/DiscountServiceTests.cs
      count: 3
      passing: 3
    implementation:
      file: src/Application/Services/DiscountService.cs
      created_at: "2025-12-30T14:35:00Z"
    coverage: 92
    
  - name: DiscountValidator
    status: red
    tests:
      file: tests/Unit/DiscountValidatorTests.cs
      count: 5
      passing: 0
    implementation: null

current_phase: green
current_component: DiscountValidator

history:
  - timestamp: "2025-12-30T14:30:52Z"
    action: session_start
  - timestamp: "2025-12-30T14:31:00Z"
    action: red_phase
    component: DiscountService
  - timestamp: "2025-12-30T14:35:00Z"
    action: green_phase
    component: DiscountService
```

### 7.2 Incremental Progress

TDFLOW processes one component at a time:
1. Complete RED-GREEN-REFACTOR for Component A
2. Move to Component B
3. Session tracks progress, allows resume

---

## 8. Integration Points

### 8.1 With SPEC Workflow

```
SPEC: intake → clarify → analyze → draft → validate → revise → verify
                                                              ↓
                                                    specification.yaml
                                                              ↓
TDFLOW:                                        start → red → green → refactor → verify
```

### 8.2 With Conformance (Chunk 3)

TDFLOW uses conformance checks during:
- REFACTOR phase: Ensure no new violations
- VERIFY phase: Final conformance check

### 8.3 With Discovery (Chunk 4)

TDFLOW uses discovered patterns:
- Test structure: Match existing test organization
- Implementation patterns: Follow detected patterns (Result<T>, CQRS, etc.)
- Naming conventions: Match codebase style

### 8.4 With Bridge (Chunk 5)

Generated contracts apply to TDFLOW outputs:
- New code must pass pattern checks
- Implementation follows enforced conventions

---

## 9. Prompt Contracts

### 9.1 `tdflow.red.v1.yaml`

```yaml
schema_version: "1.0"

contract:
  name: tdflow.red
  version: "1.0"
  description: Generate failing tests from specification
  
input:
  type: object
  required: [component, spec]
  properties:
    component:
      type: object
      description: Component definition from specification
    spec:
      type: object
      description: Full specification context
    test_framework:
      type: string
      enum: [xunit, nunit, pytest, jest]
    existing_tests:
      type: array
      description: Existing test patterns in codebase

output:
  type: object
  required: [test_file, test_cases]
  properties:
    test_file:
      type: object
      properties:
        path: { type: string }
        content: { type: string }
    test_cases:
      type: array
      items:
        type: object
        properties:
          name: { type: string }
          method_under_test: { type: string }
          scenario: { type: string }
          expected_to_fail: { type: boolean, const: true }

quality_criteria:
  - "Each spec method has at least 2 tests (happy path + error)"
  - "Tests follow existing naming conventions"
  - "Tests are independent and isolated"
  - "Tests will fail without implementation"
```

### 9.2 `tdflow.green.v1.yaml`

```yaml
schema_version: "1.0"

contract:
  name: tdflow.green
  version: "1.0"
  description: Generate implementation to pass failing tests
  
input:
  type: object
  required: [component, tests, spec]
  properties:
    component:
      type: object
      description: Component definition from specification
    tests:
      type: object
      description: Failing tests to pass
    spec:
      type: object
      description: Behavioral requirements
    context:
      type: object
      description: Similar code, patterns, conventions
    patterns:
      type: array
      description: Patterns to follow (from discovery/bridge)

output:
  type: object
  required: [implementation_file]
  properties:
    implementation_file:
      type: object
      properties:
        path: { type: string }
        content: { type: string }
    dependencies:
      type: array
      description: Any new dependencies needed
    notes:
      type: string
      description: Implementation decisions

quality_criteria:
  - "All tests pass after implementation"
  - "Follows detected patterns (Result<T>, DI, etc.)"
  - "Matches codebase conventions"
  - "Implements all spec requirements"
```

### 9.3 `tdflow.refactor.v1.yaml`

```yaml
schema_version: "1.0"

contract:
  name: tdflow.refactor
  version: "1.0"
  description: Refactor implementation while keeping tests green
  
input:
  type: object
  required: [implementation, tests]
  properties:
    implementation:
      type: object
      description: Current implementation
    tests:
      type: object
      description: Tests that must keep passing
    conformance_violations:
      type: array
      description: Current violations to fix
    style_guide:
      type: object
      description: Code style requirements

output:
  type: object
  required: [refactored_implementation]
  properties:
    refactored_implementation:
      type: object
      properties:
        path: { type: string }
        content: { type: string }
    changes:
      type: array
      description: Summary of refactoring changes
    violations_fixed:
      type: array
      description: Conformance violations addressed

quality_criteria:
  - "All tests still pass"
  - "No new conformance violations"
  - "Code is cleaner/more maintainable"
  - "Behavior unchanged"
```

---

## 10. Error Handling

### 10.1 RED Phase Failures

| Error | Cause | Resolution |
|-------|-------|------------|
| Tests compile but pass | Spec incomplete | Return to SPEC workflow |
| Tests don't compile | Invalid test generation | Regenerate with feedback |
| No tests generated | Spec not parseable | Validate spec format |

### 10.2 GREEN Phase Failures

| Error | Cause | Resolution |
|-------|-------|------------|
| Tests still fail | Implementation incomplete | Iterate GREEN phase |
| Compile errors | Invalid implementation | Regenerate with errors |
| Wrong behavior | Misunderstood spec | Review spec + regenerate |

### 10.3 REFACTOR Phase Failures

| Error | Cause | Resolution |
|-------|-------|------------|
| Tests now fail | Refactor changed behavior | Revert, try smaller change |
| New violations | Refactor introduced issues | Fix violations |

---

## 11. Success Criteria

### 11.1 Functional Requirements

- [ ] `tdflow start` creates session from spec
- [ ] `tdflow red` generates failing tests
- [ ] `tdflow green` generates passing implementation
- [ ] `tdflow refactor` cleans up without breaking tests
- [ ] `tdflow verify` produces verification report
- [ ] Session survives interruption and resume

### 11.2 Quality Requirements

- [ ] Generated tests follow codebase conventions
- [ ] Generated implementation follows detected patterns
- [ ] Full traceability from requirement to code
- [ ] Coverage meets configured threshold

### 11.3 Integration Requirements

- [ ] Works with dotnet test and pytest
- [ ] Uses context from LSP/vector search
- [ ] Respects conformance contracts
- [ ] Integrates with SPEC workflow output

---

## 12. Implementation Plan

### Phase 1: Core Infrastructure (Day 1)
- Session management (create, load, save, resume)
- Test runner abstraction (dotnet test, pytest)
- CLI skeleton

### Phase 2: RED Phase (Day 2)
- Test generation prompt contract
- Spec-to-test mapping logic
- Test file creation
- Failure verification

### Phase 3: GREEN Phase (Day 2-3)
- Implementation generation prompt contract
- Context retrieval for implementation
- Pass verification

### Phase 4: REFACTOR + VERIFY (Day 3)
- Refactor prompt contract
- Conformance integration
- Verification report generation

### Phase 5: Integration (Day 4)
- SPEC workflow integration
- Discovery/Bridge pattern usage
- End-to-end testing

---

## Appendix A: Test Runner Abstraction

```python
class TestRunner(ABC):
    @abstractmethod
    def discover_tests(self, path: Path) -> List[TestCase]: ...
    
    @abstractmethod
    def run_tests(self, filter: str = None) -> TestResult: ...
    
    @abstractmethod
    def get_coverage(self) -> CoverageReport: ...

class DotNetTestRunner(TestRunner):
    def run_tests(self, filter: str = None) -> TestResult:
        cmd = ["dotnet", "test"]
        if filter:
            cmd.extend(["--filter", filter])
        # Parse output...

class PytestRunner(TestRunner):
    def run_tests(self, filter: str = None) -> TestResult:
        cmd = ["pytest", "-v"]
        if filter:
            cmd.extend(["-k", filter])
        # Parse output...
```

## Appendix B: Spec-to-Test Example

**Input Spec:**
```yaml
components:
  - name: DiscountService
    methods:
      - name: ApplyDiscount
        parameters:
          - name: order
            type: Order
          - name: code
            type: string
        returns: Result<Order>
        behavior: |
          Validates the discount code exists and is not expired.
          Applies the discount percentage to order total.
          Returns modified order or error if code invalid.
        errors:
          - InvalidDiscountCode
          - ExpiredDiscountCode
```

**Generated Tests:**
```csharp
public class DiscountServiceTests
{
    [Fact]
    public void ApplyDiscount_WhenValidCode_ReturnsDiscountedOrder()
    {
        // Arrange
        var order = new Order { Total = 100m };
        var sut = new DiscountService(_mockRepo.Object);
        _mockRepo.Setup(r => r.GetByCode("SAVE10"))
            .Returns(new Discount { Code = "SAVE10", Percent = 10 });
        
        // Act
        var result = sut.ApplyDiscount(order, "SAVE10");
        
        // Assert
        result.IsSuccess.Should().BeTrue();
        result.Value.Total.Should().Be(90m);
    }
    
    [Fact]
    public void ApplyDiscount_WhenInvalidCode_ReturnsError()
    {
        // Arrange
        var order = new Order { Total = 100m };
        var sut = new DiscountService(_mockRepo.Object);
        _mockRepo.Setup(r => r.GetByCode("INVALID"))
            .Returns((Discount)null);
        
        // Act
        var result = sut.ApplyDiscount(order, "INVALID");
        
        // Assert
        result.IsFailure.Should().BeTrue();
        result.Error.Should().Be(DiscountErrors.InvalidDiscountCode);
    }
    
    [Fact]
    public void ApplyDiscount_WhenExpiredCode_ReturnsError()
    {
        // Arrange
        var order = new Order { Total = 100m };
        var sut = new DiscountService(_mockRepo.Object);
        _mockRepo.Setup(r => r.GetByCode("EXPIRED"))
            .Returns(new Discount { Code = "EXPIRED", ExpiresAt = DateTime.Yesterday });
        
        // Act
        var result = sut.ApplyDiscount(order, "EXPIRED");
        
        // Assert
        result.IsFailure.Should().BeTrue();
        result.Error.Should().Be(DiscountErrors.ExpiredDiscountCode);
    }
}
```
