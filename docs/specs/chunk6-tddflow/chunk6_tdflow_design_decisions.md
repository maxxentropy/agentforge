# Chunk 6: TDFLOW Design Decisions

## Test-Driven Implementation Workflow

**Document Version:** 1.0  
**Last Updated:** 2025-12-30

---

## Decision Log

### D1: Component-by-Component Processing

**Context:** Specifications may define multiple components. How to process them?

**Decision:** Process one component at a time through full RED-GREEN-REFACTOR cycle.

**Rationale:**
- Manageable scope for LLM context
- Clear progress tracking
- Easy to resume interrupted sessions
- Tests for Component A can help generate Component B

**Alternative Considered:** Generate all tests first, then all implementations.
- Rejected: Context window limits, harder to track progress, less feedback per iteration.

---

### D2: Explicit RED Verification

**Context:** How to ensure RED phase actually produces failing tests?

**Decision:** RED phase verification REQUIRES test failure. If tests pass, abort.

**Rationale:**
- Prevents false positives (empty tests that "pass")
- Ensures tests are meaningful
- Core TDD principle: see the test fail first

**Implementation:**
```python
def verify_red_phase(test_file: Path) -> bool:
    result = test_runner.run_tests(test_file)
    if result.passed == result.total:
        raise RedPhaseError("Tests should FAIL in RED phase - no implementation exists")
    return result.failed > 0
```

---

### D3: Test Framework Abstraction

**Context:** Support multiple test frameworks (xUnit, NUnit, pytest, Jest).

**Decision:** Abstract test runner behind interface, detect framework from project.

**Rationale:**
- Same workflow regardless of framework
- Easy to add new frameworks
- Detection from project files (csproj, pyproject.toml)

**Implementation:**
```python
class TestRunner(ABC):
    @abstractmethod
    def run_tests(self, filter: str) -> TestResult: ...
    
    @classmethod
    def detect(cls, project_path: Path) -> "TestRunner":
        if (project_path / "*.csproj").exists():
            return DotNetTestRunner(project_path)
        elif (project_path / "pyproject.toml").exists():
            return PytestRunner(project_path)
```

---

### D4: Session Persistence

**Context:** TDFLOW may span multiple invocations. Need to track state.

**Decision:** Persist session state to `.agentforge/tdflow/session_{id}.yaml`.

**Rationale:**
- Allows `tdflow resume`
- Tracks which components are complete
- Stores generated file paths
- Enables audit trail

**Session Schema:**
```yaml
session_id: string
started_at: datetime
source.spec_file: string
components:
  - name: string
    status: init | red | green | refactor | verified
    tests.file: string
    implementation.file: string
current_phase: string
current_component: string
history: List[Action]
```

---

### D5: Context for GREEN Phase

**Context:** GREEN phase needs context to generate good implementations.

**Decision:** Provide layered context:
1. Failing tests (must pass these)
2. Spec requirements (behavioral contract)
3. Discovered patterns (from Chunk 4)
4. Similar code (from LSP/vector search)
5. Enforced contracts (from Chunk 5)

**Rationale:**
- Tests are primary target
- Spec provides intent
- Patterns ensure consistency
- Similar code provides templates
- Contracts enforce rules

**Priority Order:** Tests > Spec > Similar Code > Patterns

---

### D6: REFACTOR is Optional

**Context:** Not all implementations need refactoring.

**Decision:** REFACTOR phase is optional, triggered by:
- Explicit `tdflow refactor` command
- Conformance violations detected
- Coverage below threshold

**Rationale:**
- GREEN output may be good enough
- Saves LLM calls when unnecessary
- User controls when to refactor

**Skip Conditions:**
```python
def should_skip_refactor(result: GreenResult) -> bool:
    return (
        result.conformance_clean and
        result.coverage >= threshold and
        not user_requested_refactor
    )
```

---

### D7: Traceability via Comments

**Context:** Need to trace implementation back to requirements.

**Decision:** Generated code includes traceability comments.

**Rationale:**
- Clear audit trail
- Helps future maintenance
- Supports verification

**Example:**
```csharp
/// <summary>
/// Applies discount to order.
/// </summary>
/// <remarks>
/// Spec: specification.yaml#components.DiscountService.methods.ApplyDiscount
/// Tests: DiscountServiceTests.cs
/// Generated: 2025-12-30T14:35:00Z by TDFLOW
/// </remarks>
public Result<Order> ApplyDiscount(Order order, string code)
{
    // Requirement: Validates the discount code exists and is not expired.
    var discount = _repository.GetByCode(code);
    if (discount == null)
        return Result.Failure<Order>(DiscountErrors.InvalidDiscountCode);
    
    // ...
}
```

---

### D8: Test Naming Convention

**Context:** Generated tests need consistent, descriptive names.

**Decision:** Use pattern: `{Method}_{Scenario}_{ExpectedResult}`

**Examples:**
- `ApplyDiscount_WhenValidCode_ReturnsDiscountedOrder`
- `ApplyDiscount_WhenInvalidCode_ReturnsError`
- `ApplyDiscount_WhenExpiredCode_ReturnsError`

**Rationale:**
- Self-documenting
- Consistent with common conventions
- Easy to filter by method

---

### D9: Incremental Verification

**Context:** When to run verification checks?

**Decision:** Verify at each phase transition:

| Transition | Verification |
|------------|--------------|
| INIT → RED | Spec valid, tests generated |
| RED → GREEN | Tests fail (expected) |
| GREEN → REFACTOR | Tests pass |
| REFACTOR → VERIFY | Tests pass, conformance clean |
| VERIFY → DONE | Full verification report |

**Rationale:**
- Fail fast
- Clear phase boundaries
- Easy debugging when things go wrong

---

### D10: Handling Test Dependencies

**Context:** Generated tests may need mocks, fixtures, setup.

**Decision:** Infer dependencies from spec and existing test patterns.

**Sources:**
1. Spec component dependencies → Constructor mocks
2. Existing test base classes → Inherit if appropriate
3. Codebase patterns → Use same mocking framework

**Example Inference:**
```yaml
# Spec says:
component:
  name: DiscountService
  dependencies:
    - IDiscountRepository
    
# Generated test:
public class DiscountServiceTests
{
    private readonly Mock<IDiscountRepository> _mockRepo;
    private readonly DiscountService _sut;
    
    public DiscountServiceTests()
    {
        _mockRepo = new Mock<IDiscountRepository>();
        _sut = new DiscountService(_mockRepo.Object);
    }
}
```

---

### D11: Coverage Integration

**Context:** Should TDFLOW track test coverage?

**Decision:** Yes, coverage is collected during GREEN and VERIFY phases.

**Rationale:**
- Ensures tests are meaningful
- Identifies untested code
- Part of quality gate

**Implementation:**
```bash
# .NET
dotnet test --collect:"XPlat Code Coverage"

# Python  
pytest --cov={module} --cov-report=xml
```

**Threshold:** Configurable, default 80%.

---

### D12: Error Recovery Strategy

**Context:** What happens when a phase fails?

**Decision:** Phase-specific recovery strategies:

| Phase | Failure | Recovery |
|-------|---------|----------|
| RED | Tests pass | Error: Return to spec (tests not meaningful) |
| RED | Tests don't compile | Regenerate with error feedback |
| GREEN | Tests still fail | Iterate with failure details |
| GREEN | Compile error | Regenerate with error feedback |
| REFACTOR | Tests break | Revert, try smaller changes |
| VERIFY | Coverage low | Suggest additional tests |

**Max Iterations:** 3 per phase before requiring human intervention.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TDFLOW CLI                                   │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────────┐  │
│  │ start  │  │  red   │  │ green  │  │ refactor │  │   verify   │  │
│  └───┬────┘  └───┬────┘  └───┬────┘  └────┬─────┘  └─────┬──────┘  │
└──────┼───────────┼───────────┼────────────┼──────────────┼──────────┘
       │           │           │            │              │
       ▼           ▼           ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Session Manager                                 │
│  - Create/Load/Save sessions                                        │
│  - Track component progress                                         │
│  - Manage phase transitions                                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐
│  Spec Loader    │  │  Test Runner    │  │   Context Assembler     │
│  - Parse spec   │  │  - dotnet test  │  │  - Failing tests        │
│  - Extract      │  │  - pytest       │  │  - Spec requirements    │
│    components   │  │  - Coverage     │  │  - Similar code (LSP)   │
└─────────────────┘  └─────────────────┘  │  - Patterns (Discovery) │
                                          └─────────────────────────┘
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Phase Executors                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ RedExecutor │  │GreenExecutor│  │RefactorExec │  │VerifyExec │  │
│  │ - Generate  │  │ - Generate  │  │ - Clean up  │  │ - Report  │  │
│  │   tests     │  │   impl      │  │ - Fix       │  │ - Trace   │  │
│  │ - Verify    │  │ - Verify    │  │   violations│  │           │  │
│  │   failure   │  │   pass      │  │             │  │           │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Prompt Contracts                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ tdflow.red.v1   │  │ tdflow.green.v1 │  │ tdflow.refactor.v1  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM generates tests that always pass | Explicit RED verification fails if tests pass |
| Generated code doesn't compile | Iterate with compile errors as feedback |
| Tests pass but behavior wrong | Spec review, potentially more test cases |
| Context too large for LLM | Prioritize relevant context, summarize |
| Long-running sessions lose state | Persistent session files, resume capability |

---

## Future Considerations

### Near-Term
- **Parallel component processing**: Process independent components concurrently
- **Interactive mode**: Human reviews generated tests before GREEN
- **Test mutation**: Ensure tests actually verify behavior

### Long-Term
- **Learning from corrections**: Improve generation from human feedback
- **IDE integration**: VS Code extension for TDFLOW
- **CI/CD integration**: Run TDFLOW in pipeline for new features
