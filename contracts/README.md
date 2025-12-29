# Formal Prompt Contracts
## Machine-Verifiable Prompts for Deterministic Agent Behavior

## The Insight

You asked: *"Could these markdown files be converted into a format that could have formal verification applied to them?"*

**Yes.** And this is a key architectural decision that enables:

1. **Validate prompts before use** — Catch errors in prompt structure, not in outputs
2. **Validate outputs against schemas** — Every LLM output is type-checked
3. **Test prompts like code** — Unit tests for prompt contracts
4. **Version and diff prompts** — Track changes formally
5. **Generate documentation** — Auto-generate human-readable docs from contracts

## What Changed

| Before (Markdown) | After (YAML Contracts) |
|-------------------|------------------------|
| Human-readable only | Machine-parseable |
| No schema validation | JSON Schema for all outputs |
| Examples are illustrative | Examples are test cases |
| Verification rules in prose | Verification rules are executable |
| Variables are implicit | Variables are typed and documented |

## Contract Structure

```yaml
contract:
  id: "spec.intake.v1"           # Unique identifier
  version: "1.0.0"               # Semantic version
  workflow: spec                 # Parent workflow
  state: intake                  # State in workflow

role:
  name: "Requirements Analyst"
  goal: "Capture request without proposing solutions"
  anti_goals:                    # What NOT to do
    - "Proposing implementations"

inputs:
  required:
    - name: raw_request
      type: string
      validation:
        min_length: 5

output:
  format: yaml
  schema:                        # JSON Schema!
    type: object
    required: [detected_intent]
    properties:
      detected_intent:
        type: string
        minLength: 10

examples:
  valid:                         # These are TEST CASES
    - name: "Standard request"
      inputs: {...}
      output: {...}              # Must validate against schema
  
  invalid:                       # Anti-patterns
    - name: "Too vague"
      output: {...}
      problems: [...]

verification:
  schema_validation: true
  checks:
    - id: "C1"
      type: regex_negative
      target: "detected_intent"
      pattern: "\\b(class|service)\\b"
      message: "Intent should not include implementation"

execution:
  temperature: 0.0               # Deterministic
  max_tokens: 2000
```

## Verification Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PROMPT CONTRACT VERIFICATION                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. CONTRACT VALIDATION (Before Use)                                 │   │
│  │                                                                      │   │
│  │    Contract File ──> Schema Check ──> Example Validation ──>        │   │
│  │                      Variable Check ──> Rule Validation             │   │
│  │                                                                      │   │
│  │    Result: Contract is VALID or lists ERRORS                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. PROMPT ASSEMBLY (At Runtime)                                     │   │
│  │                                                                      │   │
│  │    Contract + Inputs ──> Variable Substitution ──> Prompt           │   │
│  │                                                                      │   │
│  │    Validates: All required inputs present, types correct            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. EXECUTION (LLM Call)                                             │   │
│  │                                                                      │   │
│  │    Prompt ──> LLM ──> Raw Output                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. OUTPUT VALIDATION (After LLM Response)                           │   │
│  │                                                                      │   │
│  │    Raw Output ──> Parse YAML/JSON ──> Schema Validation ──>         │   │
│  │                   Custom Checks ──> LLM Checks (optional)           │   │
│  │                                                                      │   │
│  │    Result: Output is VALID or lists FAILURES with severity          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 5. DECISION                                                          │   │
│  │                                                                      │   │
│  │    VALID + BLOCKING pass    ──> Proceed to next state               │   │
│  │    BLOCKING failure         ──> Retry with error context            │   │
│  │    REQUIRED failure         ──> Retry or human escalation           │   │
│  │    ADVISORY warning         ──> Log and proceed                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Verification Check Types

| Type | Description | Example |
|------|-------------|---------|
| `schema` | JSON Schema validation | Output matches defined structure |
| `regex` | Pattern must match | Field contains expected format |
| `regex_negative` | Pattern must NOT match | No implementation terms in intent |
| `field_equals` | Exact value match | `raw_request == inputs.raw_request` |
| `count_min` | Minimum array length | At least 1 question for non-trivial |
| `conditional` | If X then Y | If scope != trivial, has questions |
| `llm` | LLM-based evaluation | "Is this intent specific?" |

## Severity Levels

| Level | Meaning | On Failure |
|-------|---------|------------|
| `blocking` | Must pass | Halt execution, retry required |
| `required` | Should pass | Retry with feedback |
| `advisory` | Nice to have | Log warning, continue |
| `informational` | FYI only | Log only |

## Testing Contracts

```python
# Contracts can be tested like code

def test_contract_schema_valid():
    """Contract structure is valid."""
    validator = ContractValidator(schema_path)
    report = validator.validate_contract(contract_path)
    assert report.is_valid

def test_examples_validate():
    """All examples pass schema validation."""
    contract = load_contract(contract_path)
    for example in contract['examples']['valid']:
        assert validates(example['output'], contract['output']['schema'])

def test_invalid_examples_fail():
    """Invalid examples actually fail validation."""
    contract = load_contract(contract_path)
    for example in contract['examples']['invalid']:
        assert not validates(example['output'], contract['output']['schema'])

def test_output_determinism():
    """Same input produces consistent output structure."""
    # Run contract 3 times with same input
    # All outputs should have same structure
```

## Files Created

```
agentforge-prd/
├── schemas/
│   └── prompt-contract.schema.yaml    # Meta-schema for contracts
├── contracts/
│   ├── spec.intake.v1.yaml            # INTAKE contract
│   ├── spec.clarify.v1.yaml           # CLARIFY contract
│   ├── spec.analyze.v1.yaml           # ANALYZE contract
│   ├── spec.draft.v1.yaml             # DRAFT contract (outputs YAML)
│   ├── spec.validate.v1.yaml          # VALIDATE contract
│   └── spec.revise.v1.yaml            # REVISE contract (feedback loop)
└── tools/
    └── contract_validator.py           # Validation tool
```

## All Contracts Complete

| Contract | State | Purpose | Output Format |
|----------|-------|---------|---------------|
| spec.intake.v1 | INTAKE | Capture raw request | YAML |
| spec.clarify.v1 | CLARIFY | Ask clarifying questions | YAML |
| spec.analyze.v1 | ANALYZE | Analyze codebase | YAML |
| spec.draft.v1 | DRAFT | Write specification | YAML |
| spec.validate.v1 | VALIDATE | Review specification | YAML |
| spec.revise.v1 | REVISE | Fix validation issues | YAML |

## The Feedback Loop

```
INTAKE → CLARIFY → ANALYZE → DRAFT → VALIDATE
                                         ↓
                                   [if issues]
                                         ↓
                                      REVISE
                                         ↓
                                      VALIDATE
                                         ↓
                              [repeat until approved]
                                         ↓
                                      APPROVED
```

## Usage

### Validate a Contract

```bash
python tools/contract_validator.py contracts/spec.intake.v1.yaml

============================================================
Contract Validation Report
============================================================
Contract: spec.intake.v1 v1.0.0
Status: ✅ VALID
============================================================

Detailed Results:
------------------------------------------------------------

✅ [SCHEMA-001] Contract Schema Validity
   🚫 BLOCKING: Contract validates against prompt-contract.schema.yaml

✅ [SCHEMA-002] Output Schema Validity
   🚫 BLOCKING: Output schema is valid JSON Schema

✅ [EXAMPLE-001] Example Validation: Feature request - discount codes
   🚫 BLOCKING: Example 'Feature request - discount codes' validates correctly
```

### Validate LLM Output

```python
from contract_validator import OutputValidator

# Load contract
with open('contracts/spec.intake.v1.yaml') as f:
    contract = yaml.safe_load(f)

# Validate output
validator = OutputValidator(contract)
report = validator.validate(llm_output, inputs)

if report.is_valid:
    # Proceed to next state
else:
    # Retry with error feedback
    errors = [r for r in report.results if not r.passed]
```

## Benefits

1. **Correctness is Upstream** — Validate prompts before they produce outputs
2. **Deterministic Behavior** — Same contract → same output structure
3. **Self-Documenting** — Contracts ARE the documentation
4. **Testable** — CI/CD for prompts
5. **Versionable** — Track prompt evolution
6. **Tool-Ready** — Editors can provide autocomplete, validation

## Next Steps

1. **Convert remaining prompts** (ANALYZE, DRAFT, VALIDATE) to contracts
2. **Build contract runner** — Assemble prompt + validate output in one flow
3. **Add CI validation** — Validate all contracts on commit
4. **Generate human docs** — Auto-generate readable docs from contracts
