# AgentForge Quick Start Guide
## Try the SPEC Workflow in 15 Minutes

This guide walks you through using the SPEC workflow to create a specification
for a simple feature using your Claude subscription (no API costs).

## Prerequisites

- Python 3.9+
- PyYAML: `pip install pyyaml`
- jsonschema: `pip install jsonschema`
- Access to Claude (claude.ai or Claude app)

## Directory Structure

```
agentforge-prd/
├── run_contract.py           # CLI runner
├── contracts/                # Formal prompt contracts
│   ├── spec.intake.v1.yaml
│   ├── spec.clarify.v1.yaml
│   ├── spec.analyze.v1.yaml
│   ├── spec.draft.v1.yaml
│   └── spec.validate.v1.yaml
├── tools/
│   └── contract_validator.py # Validation tool
├── sample_data/
│   └── project_context.yaml  # Sample project config
└── outputs/                  # Generated prompts and outputs
```

---

## Step 1: Validate the Contracts (Optional)

First, verify the contracts themselves are valid:

```bash
python run_contract.py validate-contract contracts/spec.intake.v1.yaml
```

You should see:
```
============================================================
Contract Validation Report
============================================================
Contract: spec.intake.v1 v1.0.0
Status: ✅ VALID
============================================================
```

---

## Step 2: Run INTAKE

Generate a prompt for the INTAKE state:

```bash
python run_contract.py intake --request "Add discount codes to our order system"
```

This creates a YAML prompt file in `outputs/`. The file contains:

```yaml
contract_id: spec.intake.v1
contract_version: "1.0.0"
generated_at: "2025-..."
inputs_provided:
  raw_request: "Add discount codes to our order system"
  priority: medium
prompt:
  system: |
    # Role
    You are a Requirements Analyst...
  user: |
    # Feature Request
    Add discount codes to our order system
    ...
expected_output:
  format: yaml
validation_command: "python run_contract.py validate-output ..."
```

### Validate the Prompt (Optional)

```bash
python tools/validate_schema.py schemas/assembled_prompt.schema.yaml outputs/spec.intake.v1_*_prompt.yaml
```

### Execute the Prompt

1. Open the generated `.yaml` file
2. Copy the `system` section content → paste as system message in Claude
3. Copy the `user` section content → paste as user message in Claude
4. Claude will respond with YAML
5. Save Claude's response to `outputs/intake_record.yaml`

### Validate the Output

```bash
python run_contract.py validate-output spec.intake.v1 outputs/intake_record.yaml
```

---

## Step 3: Run CLARIFY

Continue with clarification:

```bash
python run_contract.py clarify --intake-file outputs/intake_record.yaml
```

### Clarification Loop

1. Copy prompt, paste to Claude
2. Claude asks a question (mode: question)
3. Answer the question in your conversation
4. Save Claude's response
5. Add Q&A to history file and run clarify again

When Claude responds with `mode: complete`, save as `outputs/clarification_log.yaml`

### Tracking Conversation History

Create `outputs/conversation_history.yaml`:

```yaml
- question: "Can multiple discount codes be applied to a single order?"
  answer: "One code per order for v1"
- question: "Should discounts apply before or after tax?"
  answer: "Before tax"
```

Then run:
```bash
python run_contract.py clarify \
  --intake-file outputs/intake_record.yaml \
  --history-file outputs/conversation_history.yaml
```

---

## Step 4: Run ANALYZE

Generate the analysis prompt:

```bash
python run_contract.py analyze \
  --intake-file outputs/intake_record.yaml \
  --clarification-file outputs/clarification_log.yaml \
  --code-context "class Order { public decimal Total { get; } }"
```

1. Copy prompt to Claude
2. Save response as `outputs/analysis_report.yaml`

---

## Step 5: Run DRAFT

Generate the specification:

```bash
python run_contract.py draft \
  --intake-file outputs/intake_record.yaml \
  --clarification-file outputs/clarification_log.yaml \
  --analysis-file outputs/analysis_report.yaml
```

1. Copy prompt to Claude
2. Save response as `outputs/specification.md`

---

## Step 6: Run VALIDATE

Final review:

```bash
python run_contract.py validate \
  --spec-file outputs/specification.md \
  --analysis-file outputs/analysis_report.yaml
```

1. Copy prompt to Claude
2. Review the validation report
3. If `needs_revision`, go back to DRAFT
4. If `approved`, you're done!

---

## Sample Outputs

### Expected INTAKE Output

```yaml
raw_request: "Add discount codes to our order system"
detected_intent: "User wants to apply promotional discount codes to reduce order totals at checkout"
detected_scope: medium
detected_type: feature
key_entities:
  - entity_name: "Order"
    entity_type: class
    confidence: 0.95
  - entity_name: "discount code"
    entity_type: concept
    confidence: 0.9
initial_questions:
  - question: "Can multiple discount codes be applied to a single order?"
    priority: blocking
    category: behavior
  - question: "What types of discounts are needed (percentage, fixed amount, free shipping)?"
    priority: important
    category: scope
implicit_requirements:
  - requirement: "Discount codes should be validated before applying"
    confidence: 0.95
affected_areas:
  - area: "Order entity/aggregate"
    impact: direct
  - area: "Checkout flow"
    impact: direct
red_flags:
  - "No mention of discount code management UI"
```

### Expected CLARIFY Output (Question)

```yaml
mode: question
question:
  text: "Can multiple discount codes be applied to a single order, or is it limited to one code per order?"
  priority: blocking
  category: behavior
  why_asking: "This affects the data model significantly - single reference vs. collection"
  options:
    - "One code per order only"
    - "Multiple codes, all discounts stack"
    - "Multiple codes, best discount wins"
```

### Expected CLARIFY Output (Complete)

```yaml
mode: complete
clarification_log:
  questions_asked:
    - question: "Can multiple discount codes be applied?"
      answer: "One code per order for v1"
      implications:
        - "Simple data model - single DiscountCode on Order"
  assumptions_made:
    - assumption: "Codes are case-insensitive"
      reason: inferred_from_context
      confidence: medium
      needs_validation: true
  scope_definition:
    in_scope:
      - item: "Apply single discount code at checkout"
        confirmed_by: user_explicit
    out_of_scope:
      - item: "Multiple codes per order"
        reason: "Deferred to v2"
        deferred_to: "Phase 2"
    deferred: []
  domain_terms_defined:
    discount_code: "Alphanumeric string entered by customer"
```

---

## Troubleshooting

### "Contract not found"

Make sure you're running from the `agentforge-prd` directory:

```bash
cd agentforge-prd
python run_contract.py intake --request "..."
```

### "YAML parse error"

Claude might wrap the output in markdown code blocks. Remove them:

```yaml
# Remove these lines:
```yaml
# ... your content ...
```
```

### Validation Failures

If validation fails, check the specific error:

```bash
python run_contract.py validate-output spec.intake.v1 outputs/intake_record.yaml
```

Common issues:
- `detected_intent` contains implementation details (class names)
- Missing `initial_questions` for non-trivial scope
- `raw_request` was modified (must be preserved exactly)

---

## Next Steps

1. **Customize project context**: Edit `sample_data/project_context.yaml`
2. **Add architecture rules**: Create `sample_data/architecture.yaml`
3. **Try your own feature**: Run the workflow for a real feature

---

## Full Workflow Diagram

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐    ┌──────────┐
│ INTAKE  │───>│ CLARIFY  │───>│ ANALYZE  │───>│ DRAFT │───>│ VALIDATE │
└─────────┘    └──────────┘    └──────────┘    └───────┘    └──────────┘
     │              │                                            │
     │              │ (loop until                                 │
     │              │  mode: complete)                            │
     │              │                                            │
     ▼              ▼                                            ▼
 intake_       clarification_                              ┌──────────┐
 record.yaml   log.yaml                                   │ APPROVED │
                                                          └──────────┘
```

Each state:
1. Generates a prompt (via `run_contract.py`)
2. You execute in Claude
3. Save the YAML output
4. Validate (optional but recommended)
5. Move to next state
