# SPEC.ADAPT Prompt Template
# Version: 1.0.0
#
# Usage:
# 1. Replace {variables} with actual values
# 2. Output is a structured YAML specification document
# 3. Output feeds into VALIDATE → REVISE → TDFLOW workflow

---

# Role

You are adapting an external specification to AgentForge codebase conventions.
The external spec is the **SOURCE OF TRUTH** for requirements and design decisions.
Your job is to **MAP** concepts to codebase reality, not to redesign.

# Key Principle

**ADAPT transforms, it doesn't second-guess.**

- DO NOT invent requirements not in the external spec
- DO NOT question design decisions already made
- DO preserve the original intent exactly
- DO map abstract concepts to concrete codebase locations
- DO add structure where the external spec is informal

# Output Format

Output a YAML document matching this exact structure:

```yaml
metadata:
  version: "1.0"
  status: draft
  feature_name: "Feature Name"
  created_date: "YYYY-MM-DD"
  source: external-spec-adaptation
  original_source: "{original_file_path}"

overview:
  purpose: |
    Clear statement from external spec (preserve original wording).
  background: |
    Context if provided in external spec.
  scope:
    includes:
      - What is covered (derived from external spec)
    excludes:
      - What is explicitly out of scope
  assumptions:
    - Assumptions from external spec
  constraints:
    - Technical or business constraints from external spec

# CRITICAL: Map external components to codebase locations
components:
  - name: ComponentName
    location: src/agentforge/core/{module}/{file}.py  # CONCRETE PATH
    test_location: tests/unit/{module}/test_{file}.py  # CONCRETE PATH
    component_id: {module}-{feature}-{component}      # GENERATED ID
    description: |
      Description from external spec (preserve wording).
    methods:
      - method_name
    dependencies:
      - OtherComponent
    integration_points:
      - module: existing.module.path
        reason: Why integration needed

requirements:
  functional:
    - id: FR-001
      title: "Requirement Title"
      priority: must  # must | should | could | wont
      description: |
        The system SHALL [behavior from external spec].
        Preserve original requirement intent exactly.
      rationale: "Why (if stated in external spec)"
      acceptance_criteria:
        - id: AC-001
          given: "Precondition"
          when: "Action"
          then: "Expected outcome"
  non_functional:
    - id: NFR-001
      title: "Performance/Security/etc"
      priority: must
      description: |
        Non-functional requirement from external spec.
      acceptance_criteria:
        - id: AC-010
          given: "Condition"
          when: "Load/Action"
          then: "Measurable outcome"

# Include if external spec has entity definitions
entities:
  - name: EntityName
    layer: Domain  # Domain | Application | Infrastructure | Presentation
    type: entity   # entity | aggregate_root | value_object | enum | dto
    description: |
      From external spec.
    properties:
      - name: PropertyName
        type: string
        nullable: false
        description: "From external spec"
    invariants:
      - "Business rules from external spec"

# Include if external spec has workflow definitions
workflows:
  - name: "Workflow Name"
    description: "From external spec"
    trigger: "What starts this workflow"
    steps:
      - step: 1
        actor: User | System
        action: "Action description"
    success_outcome: "Expected result"

# Include if external spec has error cases
error_handling:
  - error_code: ErrorName
    condition: "When this error occurs"
    response: "How system responds"
    user_message: "What user sees"

testing_notes:
  unit_test_focus:
    - "Key areas to test"
  integration_test_scenarios:
    - "Scenarios needing integration tests"
  edge_cases:
    - "Edge cases from external spec"

# Preserve any open questions from external spec
open_questions:
  - question: "Question from external spec"
    context: "Why it matters"
    proposed_answer: "If answer suggested"
    status: open  # open | resolved | deferred

# Generated IDs for this spec
spec_id: {module}-{feature}-v1
schema_version: "2.0"
```

# Adaptation Tasks

## 1. Location Mapping

Map each component to a CONCRETE file path following codebase conventions:

| Pattern | Location |
|---------|----------|
| Core module | `src/agentforge/core/{module}/{file}.py` |
| CLI command | `src/agentforge/cli/commands/{name}.py` |
| Test file | `tests/unit/{module}/test_{file}.py` |

Use the codebase profile to determine which module fits best.

## 2. ID Generation

Generate stable, unique identifiers:

- `spec_id`: `{module}-{feature}-v1` (e.g., `core-rate-limiting-v1`)
- `component_id`: `{module}-{feature}-{component}` (e.g., `core-rate-limiting-limiter`)

Check existing specs to ensure uniqueness.

## 3. Requirement Formalization

Transform informal requirements into formal FR-XXX format:

| External Spec | Adapted Spec |
|--------------|--------------|
| "should limit to 100/min" | FR-001: "The system SHALL limit requests to 100 per minute per API key" |
| "return 429 when exceeded" | FR-002: "The system SHALL return HTTP 429 when rate limit is exceeded" |

Add Given/When/Then acceptance criteria if not present.

## 4. Integration Analysis

Identify integration points with existing code:
- Which existing modules does this feature touch?
- What existing interfaces will it implement?
- What existing code needs modification?

---

# Task

## External Specification (PRIMARY INPUT)

{external_spec_content}

## Codebase Profile

{codebase_profile}

## Existing Specs (for ID uniqueness check)

{existing_spec_ids}

---

# Instructions

Adapt the external specification to AgentForge format:

1. **Preserve original intent** - The external spec is authoritative
2. **Map to concrete paths** - Every component needs a real file location
3. **Generate stable IDs** - spec_id, component_id following conventions
4. **Formalize requirements** - FR-XXX with acceptance criteria
5. **Identify integrations** - Flag existing code that will be touched
6. **Output ONLY valid YAML** - No prose before or after
7. **Start output with "metadata:"** - No preamble

The output spec will feed directly into VALIDATE → REVISE → TDFLOW.
