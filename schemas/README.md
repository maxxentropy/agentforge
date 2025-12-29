# Schemas

Machine-verifiable JSON Schemas for all AgentForge artifacts.

## Schema Files

### Output Schemas (Workflow Artifacts)

| Schema | Validates | State |
|--------|-----------|-------|
| `assembled_prompt.schema.yaml` | `outputs/*_prompt.yaml` | (all) |
| `intake_record.schema.yaml` | `outputs/intake_record.yaml` | INTAKE |
| `clarification_log.schema.yaml` | `outputs/clarification_log.yaml` | CLARIFY |
| `analysis_report.schema.yaml` | `outputs/analysis_report.yaml` | ANALYZE |
| `specification.schema.yaml` | `outputs/specification.yaml` | DRAFT |
| `validation_report.schema.yaml` | `outputs/validation_report.yaml` | VALIDATE |

### Config Schemas

| Schema | Validates | Purpose |
|--------|-----------|---------|
| `execution.schema.yaml` | `config/execution.yaml` | Execution mode settings |
| `architecture.schema.yaml` | `config/architecture.yaml` | Project architecture rules |
| `context_retrieval.schema.yaml` | `config/context_retrieval.yaml` | Code retrieval settings |

### Meta Schemas

| Schema | Validates | Purpose |
|--------|-----------|---------|
| `prompt-contract.schema.yaml` | `contracts/*.yaml` | Contract structure |

## Usage

### Validate an Output File

```bash
# Validate intake record
python tools/validate_schema.py schemas/intake_record.schema.yaml outputs/intake_record.yaml

# Validate analysis report
python tools/validate_schema.py schemas/analysis_report.schema.yaml outputs/analysis_report.yaml
```

### Example Output

```
Schema: schemas/intake_record.schema.yaml
Data:   outputs/intake_record.yaml

✅ VALID
```

Or if invalid:

```
Schema: schemas/intake_record.schema.yaml
Data:   outputs/intake_record.yaml

❌ INVALID

Errors:
  detected_intent: 'Add stuff' is too short
  key_entities -> 0 -> confidence: 1.5 is greater than the maximum of 1
```

## Schema Summary

### intake_record.schema.yaml

Required fields:
- `raw_request` - Verbatim user input
- `detected_intent` - What user wants (10-500 chars)
- `detected_scope` - trivial | small | medium | large | unclear
- `detected_type` - feature | bugfix | refactor | documentation | configuration | unknown
- `key_entities[]` - Entities with name, type, confidence
- `initial_questions[]` - Questions with priority, category

### clarification_log.schema.yaml

Required fields:
- `questions_asked[]` - Q&A exchanges with implications
- `scope_definition.in_scope[]` - What's included
- `scope_definition.out_of_scope[]` - What's excluded

Optional:
- `assumptions_made[]` - Documented assumptions
- `domain_terms_defined{}` - Glossary

### analysis_report.schema.yaml

Required fields:
- `existing_components[]` - Code being modified (min 1)
- `patterns_discovered[]` - Patterns to follow (min 1)
- `constraints_discovered[]` - Limitations
- `risks_identified[]` - Risks with mitigation
- `recommended_approach` - Implementation strategy

### validation_report.schema.yaml

Required fields:
- `overall_verdict` - approved | approved_with_notes | needs_revision | rejected
- `checklist_results[]` - Validation checks (min 10)

Optional:
- `blocking_issues[]` - Must fix
- `warnings[]` - Should fix
- `strengths[]` - What's good
- `revision_guidance` - How to fix
- `approval_conditions[]` - Conditions if approved_with_notes

### specification.schema.yaml

The structured specification document from DRAFT stage.

Required fields:
- `metadata` - version, status, feature_name, created_date
- `overview` - purpose, scope (includes/excludes)
- `requirements.functional[]` - FR-XXX with acceptance criteria
- `entities[]` - Domain entities with properties, methods, invariants

Optional:
- `requirements.non_functional[]` - NFR-XXX performance, security, etc.
- `interfaces[]` - API endpoints, commands, queries
- `workflows[]` - Business process flows
- `error_handling[]` - Error codes and responses
- `testing_notes` - Unit test focus, integration scenarios, edge cases
- `open_questions[]` - Unresolved questions
- `glossary[]` - Term definitions

Render to Markdown:
```bash
python execute.py render-spec
```

## Relationship to Contracts

The schemas here define the **data structures**. The contracts in `contracts/` define:
- How to generate the data (prompts)
- Additional verification rules
- Examples and anti-patterns

```
contracts/spec.intake.v1.yaml
    └── output.schema: (embedded, matches intake_record.schema.yaml)
    └── verification.checks: (additional rules beyond schema)
```

## Adding New Schemas

1. Create `{name}.schema.yaml` with JSON Schema draft-07
2. Include `$id` for reference
3. Use `additionalProperties: false` for strictness
4. Add `description` to all fields
5. Test with `validate_schema.py`
