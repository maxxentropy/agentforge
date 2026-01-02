# External Spec Adaptation Workflow

## Overview

External specifications (from architects, other Claude instances, or design documents) are **rich design artifacts** that already contain the detail level of a DRAFT spec. Rather than parsing and reconstructing them, we **adapt** them to codebase conventions and inject them into the existing spec workflow.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SPEC WORKFLOW PATHWAYS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Greenfield (vague request):                                                 │
│    "Add OAuth" → INTAKE → CLARIFY → ANALYZE → DRAFT ─┐                      │
│                                                       │                      │
│  External Spec (rich artifact):                       ▼                      │
│    External Spec → ADAPT ─────────────────────────→ DRAFT                   │
│                      │                                │                      │
│                      │ SA agent maps concepts         ▼                      │
│                      │ to codebase reality      ┌──────────┐                │
│                      │                          │ VALIDATE │                │
│                      │                          └────┬─────┘                │
│  Brownfield (existing code):                         │                      │
│    Code → DISCOVER → as-built spec                   ▼                      │
│                                              ┌───────────┐                  │
│                                              │  REVISE   │                  │
│                                              └─────┬─────┘                  │
│                                                    │                        │
│                                                    ▼                        │
│                                              ┌──────────┐                   │
│                                              │  TDFLOW  │                   │
│                                              └──────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## The ADAPT Phase

**Command:** `agentforge spec adapt --input <external_spec>`

The ADAPT phase is the **on-ramp** for external specifications. It:

1. **Accepts rich external spec** as primary input (markdown, YAML, any format)
2. **Uses SA agent** for deep architectural review
3. **Maps abstract concepts** to concrete codebase locations
4. **Produces canonical draft** compatible with VALIDATE/REVISE/TDFLOW

### What ADAPT Does

| Input (External Spec) | ADAPT Transformation | Output (Draft Spec) |
|----------------------|---------------------|-------------------|
| "RateLimiter component" | Maps to `src/agentforge/core/api/rate_limiter.py` | `location: src/agentforge/core/api/rate_limiter.py` |
| "should limit to 100/min" | Extracts as FR-001 | `requirements.functional[0]` with acceptance criteria |
| Component relationships | Identifies integration points | `integration_points` section |
| Implicit assumptions | Makes explicit via SA review | `assumptions` and `constraints` |

### What ADAPT Does NOT Do

- Does not "parse and reconstruct" - the external spec IS the design
- Does not ask clarifying questions - assumes external spec is authoritative
- Does not invent requirements - only transforms what's provided
- Does not replace human/architect judgment - enhances with codebase context

## Implementation

### CLI Command

```bash
# Adapt external spec to codebase conventions
agentforge spec adapt --input external_spec.md

# With explicit spec ID override
agentforge spec adapt --input external_spec.md --spec-id core-rate-limiting-v1

# Skip SA review for trusted/pre-validated specs
agentforge spec adapt --input external_spec.md --skip-review

# Continue with existing workflow
agentforge spec validate --spec-file outputs/specification.yaml
agentforge spec revise --spec-file outputs/specification.yaml
agentforge tdflow start --spec outputs/specification.yaml
```

### ADAPT Prompt Structure

```markdown
# Role
You are adapting an external specification to AgentForge codebase conventions.
The external spec is the SOURCE OF TRUTH for requirements and design decisions.
Your job is to MAP concepts to codebase reality, not to redesign.

# External Specification (PRIMARY INPUT)
{external_spec_content}

# Codebase Context
{codebase_profile}
{existing_patterns}
{relevant_existing_code}

# Adaptation Tasks

1. **Location Mapping**
   - Map each component to a concrete file path following codebase conventions
   - Identify which module/package each component belongs to
   - Determine test file locations using existing test patterns

2. **ID Generation**
   - Generate spec_id: {module}-{feature}-v1
   - Generate component_ids: {module}-{feature}-{component}
   - Ensure uniqueness against existing specs

3. **Integration Analysis**
   - Identify which existing modules this spec integrates with
   - Flag potential conflicts with existing code
   - Note required changes to existing files

4. **Requirement Formalization**
   - Transform requirements into FR-XXX format with acceptance criteria
   - Preserve original intent exactly
   - Add Given/When/Then structure where missing

# Output
Produce a complete specification.yaml in AgentForge format.
```

### SA Agent Integration

The ADAPT phase invokes the software-architect agent for deep analysis:

```python
sa_result = task_tool(
    subagent_type="software-architect",
    prompt=f"""
    Analyze this external specification for adaptation to the AgentForge codebase.

    ## External Specification
    {external_spec}

    ## Codebase Profile
    {codebase_profile}

    ## Required Analysis
    1. Where should each component live? (follow existing patterns)
    2. What existing code does this integrate with?
    3. Are there any conflicts with existing functionality?
    4. What's the recommended component_id naming?
    5. What test patterns should be used?

    Provide concrete paths and IDs, not abstract recommendations.
    """
)
```

## Example Workflow

### Input: External Spec (from architect)

```markdown
# Feature: API Rate Limiting

## Overview
Add rate limiting to protect API endpoints from abuse.

## Components

### RateLimiter
Core rate limiting logic using sliding window algorithm.
- check_limit(api_key) -> bool
- record_request(api_key) -> None
- get_remaining(api_key) -> int

### RateLimitMiddleware
FastAPI middleware that applies rate limiting to requests.
- Extracts API key from header
- Returns 429 when limit exceeded

## Requirements
- Limit: 100 requests per minute per API key
- Window: Sliding 60-second window
- Response: 429 Too Many Requests with Retry-After header

## Acceptance Criteria
- Given a valid API key with < 100 requests in last minute
- When a request is made
- Then the request is allowed

- Given a valid API key with >= 100 requests in last minute
- When a request is made
- Then 429 is returned with Retry-After header
```

### ADAPT Output: Canonical Draft Spec

```yaml
metadata:
  version: "1.0"
  status: draft
  feature_name: "API Rate Limiting"
  created_date: "2024-01-02"
  source: external-spec-adaptation
  original_source: "external_spec.md"

overview:
  purpose: |
    Add rate limiting to protect API endpoints from abuse.
  scope:
    includes:
      - Sliding window rate limiting algorithm
      - FastAPI middleware integration
      - 429 response handling with Retry-After
    excludes:
      - Distributed rate limiting (single-instance only)
      - Per-endpoint rate limits

# Adapted from external spec with codebase mappings
components:
  - name: RateLimiter
    location: src/agentforge/core/api/rate_limiter.py
    test_location: tests/unit/api/test_rate_limiter.py
    component_id: core-api-rate_limiter
    description: |
      Core rate limiting logic using sliding window algorithm.
    methods:
      - check_limit
      - record_request
      - get_remaining
    integration_points:
      - module: agentforge.core.api
        reason: API infrastructure module

  - name: RateLimitMiddleware
    location: src/agentforge/core/api/middleware.py
    test_location: tests/unit/api/test_middleware.py
    component_id: core-api-middleware
    description: |
      FastAPI middleware that applies rate limiting to requests.
    dependencies:
      - RateLimiter

requirements:
  functional:
    - id: FR-001
      title: "Request rate limiting"
      priority: must
      description: |
        The system SHALL limit requests to 100 per minute per API key
        using a sliding 60-second window.
      acceptance_criteria:
        - id: AC-001
          given: "A valid API key with < 100 requests in last minute"
          when: "A request is made"
          then: "The request is allowed"
        - id: AC-002
          given: "A valid API key with >= 100 requests in last minute"
          when: "A request is made"
          then: "429 Too Many Requests is returned with Retry-After header"

spec_id: core-api-rate-limiting-v1
schema_version: "2.0"
```

### Continue with Existing Workflow

```bash
# Validate the adapted spec
agentforge spec validate --spec-file outputs/specification.yaml

# Revise if needed
agentforge spec revise --spec-file outputs/specification.yaml

# Implement via TDFLOW
agentforge tdflow start --spec outputs/specification.yaml
```

## Key Design Decisions

1. **External spec is authoritative** - ADAPT transforms, doesn't second-guess
2. **Single ADAPT phase** - Not a multi-phase sub-workflow
3. **Reuses existing workflow** - Output feeds VALIDATE → REVISE → TDFLOW
4. **SA agent for mapping** - Deep analysis of where things should live
5. **Preserves traceability** - `original_source` field tracks provenance

## File Locations

```
src/agentforge/cli/click_commands/spec.py  # Add 'adapt' command
src/agentforge/cli/commands/spec.py        # Add run_adapt() handler
prompts/spec/adapt.md                       # ADAPT prompt template
```
