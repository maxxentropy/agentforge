# Prompt Contract Specification
## Ensuring Deterministic, Verifiable Outputs Across Execution Modes

## 1. Overview

A **Prompt Contract** defines the exact structure, content, and expected output of every prompt in the system. Contracts ensure:

1. **Determinism**: Same prompt → same output structure (regardless of execution mode)
2. **Verifiability**: Outputs can be validated against schemas
3. **Traceability**: Every output element maps to a prompt element
4. **Consistency**: Prompts are versioned and immutable within a version

## 2. Contract Structure

Every prompt contract has these components:

```yaml
prompt_contract:
  # Identity
  id: string                    # Unique identifier
  version: string               # Semantic version
  workflow: string              # Which workflow this belongs to
  state: string                 # Which state in the workflow
  
  # Purpose
  role: string                  # The role the LLM should assume
  goal: string                  # What this prompt should accomplish
  
  # Input Specification
  inputs:
    required: [InputSpec]       # Must be provided
    optional: [InputSpec]       # May be provided
    context: [ContextSpec]      # Retrieved context
  
  # Output Specification  
  output:
    format: string              # yaml | json | markdown | code
    schema: Schema              # JSON Schema for validation
    examples: [Example]         # Concrete examples
  
  # Prompt Template
  template:
    system: string              # System message (role, rules, format)
    user: string                # User message template with {variables}
  
  # Verification
  verification:
    schema_validation: boolean  # Validate against schema
    custom_checks: [Check]      # Additional validation rules
  
  # Metadata
  temperature: float            # LLM temperature (0.0 for deterministic)
  max_tokens: int               # Maximum output tokens
  estimated_cost_usd: float     # Estimated API cost
```

## 3. The Prompt Template Structure

### 3.1 System Message Components

The system message establishes the **invariant rules** for the interaction:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM MESSAGE STRUCTURE                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. ROLE DEFINITION                                                   │   │
│  │    Who you are, your expertise, your perspective                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. OUTPUT FORMAT SPECIFICATION                                       │   │
│  │    Exact format required (YAML, JSON, Markdown)                      │   │
│  │    Schema definition or reference                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. RULES AND CONSTRAINTS                                             │   │
│  │    What you MUST do                                                  │   │
│  │    What you MUST NOT do                                              │   │
│  │    Quality criteria                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. EXAMPLES                                                          │   │
│  │    Good output examples                                              │   │
│  │    Bad output examples (what to avoid)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 User Message Components

The user message provides the **variable content** for this specific invocation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER MESSAGE STRUCTURE                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. TASK DESCRIPTION                                                  │   │
│  │    What specifically needs to be done in this invocation             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. INPUT DATA                                                        │   │
│  │    The specific inputs for this task                                 │   │
│  │    Clearly labeled and structured                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. CONTEXT                                                           │   │
│  │    Retrieved code/documentation                                      │   │
│  │    Project conventions                                               │   │
│  │    Previous state outputs (if continuing)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. OUTPUT REMINDER                                                   │   │
│  │    Brief reminder of expected format                                 │   │
│  │    Schema reference                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. Output Schema Requirements

### 4.1 Schema Design Principles

1. **Explicit over Implicit**: Every field is documented
2. **Typed and Constrained**: Use JSON Schema with enums, patterns, ranges
3. **Required vs Optional**: Clear distinction
4. **Examples Included**: Schema includes example values

### 4.2 Schema Template

```yaml
output_schema:
  $schema: "http://json-schema.org/draft-07/schema#"
  title: string
  description: string
  type: object
  
  required: [field_names]
  
  properties:
    field_name:
      type: string | number | boolean | array | object
      description: "What this field represents"
      # Constraints
      enum: [allowed_values]        # For fixed options
      pattern: "regex"              # For strings
      minimum: number               # For numbers
      maximum: number
      minLength: number             # For strings/arrays
      maxLength: number
      # Examples
      examples: [example_values]
      # Nested objects
      properties: {...}             # For objects
      items: {...}                  # For arrays
  
  # Validation rules
  additionalProperties: false       # Strict schema
```

## 5. Example Resolution

### 5.1 Why Examples Matter

Examples serve multiple purposes:
- **Calibration**: Show the LLM exactly what "good" looks like
- **Format Enforcement**: Demonstrate precise formatting
- **Edge Cases**: Show how to handle unusual inputs
- **Anti-patterns**: Show what NOT to produce

### 5.2 Example Structure

Each contract includes:

```yaml
examples:
  good_examples:
    - name: "Basic case"
      input:
        raw_request: "Add discount codes to orders"
      output:
        # Complete, valid output
      explanation: "Why this is good"
    
    - name: "Complex case"
      input:
        raw_request: "Refactor the payment system to support multiple currencies while maintaining backward compatibility"
      output:
        # Complete, valid output
      explanation: "Handles complexity well because..."
  
  bad_examples:
    - name: "Too vague"
      output:
        detected_intent: "User wants to improve the system"
      problems:
        - "Intent is not specific"
        - "Missing key details"
      correction: "User wants to add promotional discount codes that reduce order totals at checkout"
    
    - name: "Proposes solution"
      output:
        detected_intent: "User wants to add a DiscountService class"
      problems:
        - "Includes implementation details"
        - "INTAKE should not propose solutions"
      correction: "User wants to apply discount codes to reduce order totals"
```

## 6. Prompt Contract: SPEC.INTAKE

Here is the complete prompt contract for the INTAKE state:

```yaml
prompt_contract:
  id: "spec.intake.v1"
  version: "1.0.0"
  workflow: "SPEC"
  state: "INTAKE"
  
  role: "Requirements Analyst"
  goal: "Capture and understand user request without proposing solutions"
  
  inputs:
    required:
      - name: raw_request
        type: string
        description: "The user's original feature request"
        
    optional:
      - name: related_files
        type: array
        items: string
        description: "Files user thinks are relevant"
        
      - name: priority
        type: string
        enum: [critical, high, medium, low]
        default: medium
        
      - name: constraints
        type: string
        description: "Known limitations"
        
    context:
      - name: project_context
        source: project_context.yaml
        required: true
        
      - name: recent_changes
        source: git_log
        required: false
  
  output:
    format: yaml
    schema:
      $ref: "#/schemas/intake_record"
    
  template:
    system: |
      # Role
      
      You are a Requirements Analyst. Your job is to LISTEN and UNDERSTAND, not to solve or design.
      
      # Output Format
      
      You MUST output a YAML document that exactly matches this schema:
      
      ```yaml
      raw_request: string           # Verbatim user input (copy exactly)
      detected_intent: string       # One clear sentence: what does the user want?
      detected_scope: enum          # trivial | small | medium | large | unclear
      detected_type: enum           # feature | bugfix | refactor | documentation | configuration | unknown
      key_entities:                 # Named things that likely map to code
        - entity_name: string
          entity_type: enum         # class | interface | service | concept | unknown
          confidence: float         # 0.0 to 1.0
      initial_questions:            # Questions needed before proceeding
        - question: string
          priority: enum            # blocking | important | nice_to_know
          category: enum            # scope | behavior | constraint | technical
      implicit_requirements:        # Things not stated but probably expected
        - requirement: string
          confidence: float
      affected_areas:               # Parts of codebase likely touched
        - area: string
          impact: enum              # direct | indirect | unknown
      red_flags:                    # Potential problems spotted early
        - string
      ```
      
      # Rules
      
      1. **DO NOT propose solutions or implementations**
         - BAD: "User wants to add a DiscountService class"
         - GOOD: "User wants to apply discount codes to reduce order totals"
      
      2. **BE SPECIFIC in detected_intent**
         - BAD: "User wants to improve the system"
         - GOOD: "User wants to apply promotional discount codes that reduce order totals at checkout"
      
      3. **IDENTIFY at least one question** unless scope is trivial
         - Questions should be specific: "Can multiple codes apply to one order?"
         - NOT vague: "How should it work?"
      
      4. **PRESERVE raw_request exactly** - copy verbatim, including typos
      
      5. **SCOPE DEFINITIONS**:
         - trivial: < 1 hour, single file change
         - small: < 1 day, few files
         - medium: 1-3 days, multiple components
         - large: > 3 days, architectural impact
         - unclear: cannot determine without more info
      
      # Examples
      
      ## Good Example
      
      Input: "We need to add discount codes to our order system"
      
      Output:
      ```yaml
      raw_request: "We need to add discount codes to our order system"
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
        - question: "Should discounts apply before or after tax calculation?"
          priority: blocking
          category: behavior
        - question: "What types of discounts are needed (percentage, fixed amount, free shipping)?"
          priority: important
          category: scope
      implicit_requirements:
        - requirement: "Discount codes should be validated before applying"
          confidence: 0.95
        - requirement: "Invalid or expired codes should show user-friendly error messages"
          confidence: 0.9
        - requirement: "Applied discounts should be visible in order summary"
          confidence: 0.85
      affected_areas:
        - area: "Order entity/aggregate"
          impact: direct
        - area: "Checkout/order creation flow"
          impact: direct
        - area: "Order display/summary views"
          impact: indirect
      red_flags:
        - "No mention of discount code storage or management UI - may be out of scope or forgotten"
      ```
      
      ## Bad Example (DO NOT DO THIS)
      
      Input: "We need to add discount codes to our order system"
      
      BAD Output:
      ```yaml
      raw_request: "We need to add discount codes to our order system"
      detected_intent: "Create a DiscountService that validates codes and applies them to orders"
      # ❌ WRONG: This proposes an implementation (DiscountService)
      ```
      
    user: |
      # Task
      
      Analyze the following feature request and produce an intake record.
      
      # User Request
      
      {raw_request}
      
      {if related_files}
      # Related Files (user-specified)
      
      {related_files}
      {endif}
      
      {if constraints}
      # Known Constraints
      
      {constraints}
      {endif}
      
      {if priority}
      # Priority
      
      {priority}
      {endif}
      
      # Project Context
      
      {project_context}
      
      # Output
      
      Produce a YAML intake record following the schema exactly.
      Do NOT include any text before or after the YAML.
      Do NOT wrap in markdown code blocks.
  
  verification:
    schema_validation: true
    custom_checks:
      - name: intent_is_specific
        type: llm
        prompt: "Is this intent specific and actionable (not vague)? '{detected_intent}'"
        expected: "yes"
        
      - name: no_implementation_in_intent
        type: regex
        pattern: "(class|service|controller|repository|interface|method|function|API|endpoint)"
        target: detected_intent
        should_match: false
        message: "Intent should not include implementation details"
        
      - name: has_questions_if_not_trivial
        type: conditional
        condition: "detected_scope != 'trivial'"
        check: "len(initial_questions) >= 1"
        message: "Non-trivial requests should have at least one clarifying question"
        
      - name: raw_request_preserved
        type: exact_match
        field: raw_request
        expected: "{input.raw_request}"
        message: "raw_request must be preserved exactly"
  
  temperature: 0.0
  max_tokens: 2000
  estimated_cost_usd: 0.01

schemas:
  intake_record:
    $schema: "http://json-schema.org/draft-07/schema#"
    title: "IntakeRecord"
    type: object
    required:
      - raw_request
      - detected_intent
      - detected_scope
      - detected_type
      - key_entities
      - initial_questions
    properties:
      raw_request:
        type: string
        minLength: 1
      detected_intent:
        type: string
        minLength: 10
        maxLength: 500
      detected_scope:
        type: string
        enum: [trivial, small, medium, large, unclear]
      detected_type:
        type: string
        enum: [feature, bugfix, refactor, documentation, configuration, unknown]
      key_entities:
        type: array
        items:
          type: object
          required: [entity_name, entity_type, confidence]
          properties:
            entity_name:
              type: string
            entity_type:
              type: string
              enum: [class, interface, service, concept, unknown]
            confidence:
              type: number
              minimum: 0
              maximum: 1
      initial_questions:
        type: array
        items:
          type: object
          required: [question, priority, category]
          properties:
            question:
              type: string
            priority:
              type: string
              enum: [blocking, important, nice_to_know]
            category:
              type: string
              enum: [scope, behavior, constraint, technical]
      implicit_requirements:
        type: array
        items:
          type: object
          required: [requirement, confidence]
          properties:
            requirement:
              type: string
            confidence:
              type: number
              minimum: 0
              maximum: 1
      affected_areas:
        type: array
        items:
          type: object
          required: [area, impact]
          properties:
            area:
              type: string
            impact:
              type: string
              enum: [direct, indirect, unknown]
      red_flags:
        type: array
        items:
          type: string
    additionalProperties: false
```

## 7. Prompt Contract: SPEC.CLARIFY

```yaml
prompt_contract:
  id: "spec.clarify.v1"
  version: "1.0.0"
  workflow: "SPEC"
  state: "CLARIFY"
  
  role: "Requirements Analyst"
  goal: "Resolve ambiguities through structured dialogue"
  
  inputs:
    required:
      - name: intake_record
        type: object
        schema: "#/schemas/intake_record"
        
      - name: conversation_history
        type: array
        items:
          type: object
          properties:
            question: string
            answer: string
        description: "Previous Q&A in this clarification session"
        
    context:
      - name: project_context
        source: project_context.yaml
        
      - name: entity_definitions
        source: lsp_lookup
        description: "Code definitions of key_entities from intake"
  
  output:
    format: yaml
    schema:
      $ref: "#/schemas/clarify_output"
  
  template:
    system: |
      # Role
      
      You are a Requirements Analyst conducting a structured clarification interview.
      
      # Output Format
      
      You MUST output a YAML document with this structure:
      
      ```yaml
      # If asking a question:
      mode: question
      question:
        text: string              # The question to ask
        priority: enum            # blocking | important | nice_to_know
        category: enum            # scope | behavior | constraint | technical
        why_asking: string        # Brief explanation of why this matters
        options: [string]         # Suggested answers (optional, for closed questions)
      
      # If clarification is complete:
      mode: complete
      clarification_log:
        questions_asked: [...]    # Full Q&A history
        assumptions_made: [...]   # Things assumed when user didn't know
        scope_definition:
          in_scope: [...]
          out_of_scope: [...]
          deferred: [...]
        domain_terms_defined: {...}
      ```
      
      # Rules
      
      1. **ASK ONE QUESTION AT A TIME**
         - Do not overwhelm with multiple questions
         - Wait for answer before next question
      
      2. **PRIORITIZE QUESTIONS**
         - Ask BLOCKING questions first
         - Then SCOPE questions
         - Then BEHAVIOR questions
         - NICE_TO_KNOW questions last (or skip if user is done)
      
      3. **BE SPECIFIC**
         - BAD: "How should discounts work?"
         - GOOD: "Should multiple discount codes be stackable on a single order?"
      
      4. **HANDLE "I DON'T KNOW"**
         - Make a reasonable assumption
         - Document it with confidence level
         - Mark for validation during implementation
      
      5. **KNOW WHEN TO STOP**
         - All BLOCKING questions answered
         - Scope boundaries are clear
         - User signals "that's enough detail"
      
      # Question Categories
      
      - **scope**: What's included vs excluded
      - **behavior**: How should it work in specific scenarios
      - **constraint**: Limitations, performance requirements, compatibility
      - **technical**: Integration points, data formats, APIs
      
      # Examples
      
      ## Asking a Question
      
      ```yaml
      mode: question
      question:
        text: "Can multiple discount codes be applied to a single order, or is it limited to one code per order?"
        priority: blocking
        category: behavior
        why_asking: "This affects the data model and validation logic significantly"
        options:
          - "One code per order only"
          - "Multiple codes, all discounts stack"
          - "Multiple codes, best discount wins"
      ```
      
      ## Completing Clarification
      
      ```yaml
      mode: complete
      clarification_log:
        questions_asked:
          - question: "Can multiple discount codes be applied to a single order?"
            answer: "One code per order for v1"
            implications:
              - "Simpler data model - single DiscountCode reference on Order"
              - "No need for discount combination/conflict logic"
        assumptions_made:
          - assumption: "Discount codes are case-insensitive"
            reason: user_unknown
            confidence: medium
            needs_validation: true
        scope_definition:
          in_scope:
            - item: "Apply single discount code to order"
              confirmed_by: user_explicit
            - item: "Validate code exists and is not expired"
              confirmed_by: user_explicit
          out_of_scope:
            - item: "Multiple codes per order"
              reason: "Explicitly deferred to v2"
              deferred_to: "Phase 2"
          deferred:
            - item: "Admin UI for managing discount codes"
              decision_needed_by: "Before production"
              default_if_not_decided: "Direct database management"
        domain_terms_defined:
          discount_code: "Alphanumeric string (8-12 chars) entered at checkout"
          discount_rule: "The percentage or fixed amount off, with validity period"
      ```
    
    user: |
      # Intake Record
      
      {intake_record}
      
      # Conversation History
      
      {if conversation_history}
      Previous questions and answers:
      
      {for qa in conversation_history}
      Q: {qa.question}
      A: {qa.answer}
      
      {endfor}
      {else}
      No questions asked yet. Review the intake record and ask the first question.
      {endif}
      
      # Code Context
      
      {if entity_definitions}
      Relevant code definitions:
      
      {entity_definitions}
      {endif}
      
      # Project Context
      
      {project_context}
      
      # Instructions
      
      {if conversation_history}
      Based on the conversation so far:
      1. If more BLOCKING or SCOPE questions remain, ask the next most important one
      2. If clarification is sufficient, output mode: complete with full clarification_log
      {else}
      Review the intake record and ask the first clarifying question.
      Start with the highest-priority BLOCKING question.
      {endif}
  
  verification:
    schema_validation: true
    custom_checks:
      - name: mode_is_valid
        type: enum
        field: mode
        values: [question, complete]
        
      - name: question_has_required_fields
        type: conditional
        condition: "mode == 'question'"
        check: "question.text and question.priority and question.category"
        
      - name: complete_has_scope
        type: conditional
        condition: "mode == 'complete'"
        check: "clarification_log.scope_definition.in_scope"
        message: "Complete mode must define in_scope items"
  
  temperature: 0.0
  max_tokens: 1500
  estimated_cost_usd: 0.008

schemas:
  clarify_output:
    $schema: "http://json-schema.org/draft-07/schema#"
    title: "ClarifyOutput"
    type: object
    required: [mode]
    properties:
      mode:
        type: string
        enum: [question, complete]
      question:
        type: object
        properties:
          text:
            type: string
          priority:
            type: string
            enum: [blocking, important, nice_to_know]
          category:
            type: string
            enum: [scope, behavior, constraint, technical]
          why_asking:
            type: string
          options:
            type: array
            items:
              type: string
      clarification_log:
        $ref: "#/schemas/clarification_log"
```

## 8. Prompt Contract: SPEC.ANALYZE

```yaml
prompt_contract:
  id: "spec.analyze.v1"
  version: "1.0.0"
  workflow: "SPEC"
  state: "ANALYZE"
  
  role: "Software Architect"
  goal: "Analyze codebase to understand context, patterns, constraints, and risks"
  
  inputs:
    required:
      - name: intake_record
        type: object
        
      - name: clarification_log
        type: object
        
    context:
      - name: project_context
        source: project_context.yaml
        
      - name: architecture_rules
        source: architecture.yaml
        
      - name: code_context
        source: hybrid_retrieval
        budget_tokens: 6000
        description: "Retrieved code relevant to the task"
  
  output:
    format: yaml
    schema:
      $ref: "#/schemas/analysis_report"
  
  template:
    system: |
      # Role
      
      You are a Software Architect analyzing a codebase for a new feature.
      
      # Output Format
      
      You MUST output a YAML document matching this schema:
      
      ```yaml
      existing_components:
        - component_name: string
          component_type: enum       # class | interface | service | module | function
          location:
            file: string
            start_line: integer
            end_line: integer
          relevance: enum            # primary | secondary | reference
          current_behavior: string   # What it does now
          public_interface:          # Key methods/properties
            - member_name: string
              member_type: enum      # method | property | event
              signature: string
          will_be_modified: boolean
          modification_type: enum    # extend | wrap | replace | reference_only
      
      patterns_discovered:
        - pattern_name: string
          description: string
          examples:
            - file: string
              line_range: string
              snippet: string        # Relevant code excerpt (brief)
          must_follow: boolean
          rationale: string
      
      constraints_discovered:
        - constraint: string
          source: enum               # code | documentation | architecture_yaml | inferred
          location: string
          impact: string             # How this affects implementation
          severity: enum             # hard | soft
      
      risks_identified:
        - risk: string
          category: enum             # breaking_change | performance | security | complexity | dependency
          severity: enum             # high | medium | low
          likelihood: enum           # high | medium | low
          affected_areas: [string]
          mitigation_strategy: string
          contingency: string
      
      integration_points:
        - integration_type: enum     # calls | called_by | implements | raises | subscribes
          component: string
          interface_or_event: string
          notes: string
      
      recommended_approach:
        summary: string              # Brief description of recommended approach
        new_components:
          - name: string
            type: string
            layer: string            # domain | application | infrastructure | presentation
            responsibility: string
        modified_components:
          - name: string
            modification: string
        sequence_of_changes:
          - step: integer
            description: string
            files_affected: [string]
      ```
      
      # Rules
      
      1. **BE SPECIFIC** - Include file paths, line numbers, exact signatures
         - BAD: "Uses repository pattern"
         - GOOD: "OrderRepository implements IOrderRepository with GetById(Guid), Save(Order), Delete(Guid) at src/Infrastructure/Repositories/OrderRepository.cs:15-87"
      
      2. **IDENTIFY ALL PATTERNS** - Look for:
         - Error handling patterns (exceptions vs Result<T>)
         - Data access patterns (repository, direct DB, ORM usage)
         - Validation patterns (where and how)
         - Dependency injection style
         - Naming conventions
      
      3. **RESPECT ARCHITECTURE RULES**
         - Check architecture.yaml for layer constraints
         - Verify recommended approach doesn't violate rules
         - Note any tensions between desired feature and architecture
      
      4. **ASSESS RISKS HONESTLY**
         - Breaking changes to existing behavior
         - Performance implications
         - Security considerations
         - Integration complexity
      
      5. **HIGH-SEVERITY RISKS NEED MITIGATIONS**
         - Every high-severity risk must have a mitigation strategy
      
      # Example
      
      See the full example in the user message context.
    
    user: |
      # Intake Record
      
      {intake_record}
      
      # Clarification Log
      
      {clarification_log}
      
      # Architecture Rules
      
      {architecture_rules}
      
      # Retrieved Code Context
      
      {code_context}
      
      # Project Context
      
      {project_context}
      
      # Task
      
      Analyze the codebase and produce an analysis report.
      Focus on understanding:
      1. What existing code we'll interact with
      2. What patterns we must follow
      3. What constraints apply
      4. What risks exist
      5. How new code should integrate
      
      Output YAML only, no additional text.
  
  verification:
    schema_validation: true
    custom_checks:
      - name: has_primary_component
        type: custom
        check: "any(c.relevance == 'primary' for c in existing_components)"
        message: "Must identify at least one primary component"
        
      - name: has_patterns
        type: custom
        check: "len(patterns_discovered) >= 1"
        message: "Must identify at least one pattern"
        
      - name: high_risks_have_mitigation
        type: custom
        check: "all(r.mitigation_strategy for r in risks_identified if r.severity == 'high')"
        message: "High-severity risks must have mitigation strategies"
        
      - name: approach_respects_architecture
        type: llm
        prompt: |
          Architecture rules: {architecture_rules}
          Recommended approach: {recommended_approach}
          
          Does the recommended approach respect the architecture rules?
        expected_contains: "yes"
  
  temperature: 0.0
  max_tokens: 4000
  estimated_cost_usd: 0.03
```

## 9. Prompt Contract: SPEC.DRAFT

```yaml
prompt_contract:
  id: "spec.draft.v1"
  version: "1.0.0"
  workflow: "SPEC"
  state: "DRAFT"
  
  role: "Technical Specification Writer"
  goal: "Create complete, unambiguous, testable specification"
  
  inputs:
    required:
      - name: intake_record
        type: object
        
      - name: clarification_log
        type: object
        
      - name: analysis_report
        type: object
        
    context:
      - name: spec_template
        source: templates/specification.md
        
      - name: code_examples
        source: fetch_specific
        files: analysis_report.patterns_discovered.examples.file
  
  output:
    format: markdown
    structure:
      - overview
      - requirements
      - interfaces
      - data_model
      - behavior
      - acceptance_criteria
      - assumptions
      - risks
    
  template:
    system: |
      # Role
      
      You are a Technical Specification Writer.
      
      # Quality Bar
      
      The specification must be detailed enough that:
      1. Two different developers would produce substantially similar implementations
      2. A tester could write tests from the spec alone
      3. A reviewer could verify implementation correctness against the spec
      
      # Document Structure
      
      Output a Markdown document with these EXACT sections:
      
      ```markdown
      # {Feature Name} Specification
      
      **Version:** 1.0
      **Status:** Draft
      **Date:** {date}
      
      ## 1. Overview
      ### 1.1 Purpose
      ### 1.2 Scope
      ### 1.3 Glossary
      
      ## 2. Requirements
      ### 2.1 Functional Requirements
      ### 2.2 Non-Functional Requirements
      
      ## 3. Interfaces
      ### 3.1 Public API
      ### 3.2 Events
      ### 3.3 Dependencies
      
      ## 4. Data Model
      ### 4.1 Entities
      ### 4.2 Validation Rules
      
      ## 5. Behavior
      ### 5.1 Happy Path
      ### 5.2 Edge Cases
      ### 5.3 Error Handling
      
      ## 6. Acceptance Criteria
      
      ## 7. Assumptions
      
      ## 8. Risks
      ```
      
      # Writing Rules
      
      1. **USE PRECISE LANGUAGE**
         - SHALL = mandatory (MUST happen)
         - SHOULD = recommended (usually happens)
         - MAY = optional (can happen)
         - AVOID: might, could, would, probably, maybe
      
      2. **BE SPECIFIC**
         - BAD: "The system should validate the discount code"
         - GOOD: "The system SHALL verify: (1) code exists in DiscountCodes table, (2) code.StartDate <= current UTC date, (3) code.EndDate >= current UTC date, (4) code.UsageCount < code.MaxUses"
      
      3. **INCLUDE EXAMPLES FOR EVERY BEHAVIOR**
         - Each requirement should have at least one concrete example
         - Include both normal and edge cases
      
      4. **ACCEPTANCE CRITERIA IN GIVEN/WHEN/THEN**
         ```
         Given [precondition]
         When [action]
         Then [expected result]
         ```
      
      5. **FUNCTIONAL REQUIREMENTS FORMAT**
         ```
         **FR-{number}: {Title}**
         
         The system SHALL {specific behavior}.
         
         *Rationale:* {why this requirement exists}
         
         *Example:*
         - Input: {specific input}
         - Expected: {specific output}
         
         *Acceptance Criteria:*
         ```gherkin
         Given {precondition}
         When {action}
         Then {expected result}
         ```
         ```
      
      6. **NO IMPLEMENTATION DETAILS**
         - Describe WHAT, not HOW
         - Exception: When specific implementation is required for consistency
      
      7. **INTERFACES MUST BE COMPLETE**
         - Every parameter documented
         - Return values documented
         - All error conditions documented
         - Type information included
      
      # Anti-Patterns to Avoid
      
      - ❌ "The system should handle errors appropriately"
      - ✅ "The system SHALL return Result.Failure(DiscountError.CodeExpired) when code.EndDate < current UTC date"
      
      - ❌ "Fast response time"
      - ✅ "Response time SHALL be < 200ms at p95 for discount validation"
      
      - ❌ TBD, TODO, "to be determined"
      - ✅ Everything defined, or explicitly listed in Assumptions with decision date
    
    user: |
      # Source Documents
      
      ## Intake Record
      {intake_record}
      
      ## Clarification Log
      {clarification_log}
      
      ## Analysis Report
      {analysis_report}
      
      # Code Examples (for pattern reference)
      
      {code_examples}
      
      # Task
      
      Create a complete specification document following the template exactly.
      Every section must be filled with specific, testable content.
      
      Do NOT include placeholder text (TBD, TODO, etc.)
      Do NOT include implementation details unless required for consistency.
      
      Output the Markdown document only.
  
  verification:
    schema_validation: false  # Markdown doesn't have JSON schema
    custom_checks:
      - name: all_sections_present
        type: section_check
        required_sections:
          - "## 1. Overview"
          - "## 2. Requirements"
          - "### 2.1 Functional Requirements"
          - "## 3. Interfaces"
          - "## 4. Data Model"
          - "## 5. Behavior"
          - "## 6. Acceptance Criteria"
          - "## 7. Assumptions"
          - "## 8. Risks"
        
      - name: no_placeholders
        type: regex
        pattern: "(TBD|TODO|FIXME|\\?\\?\\?|to be determined|to be decided)"
        should_match: false
        case_insensitive: true
        
      - name: no_vague_modals
        type: regex
        pattern: "\\b(should|might|could|would|probably|maybe)\\b"
        scope: "section:Requirements"
        should_match: false
        exceptions: ["SHOULD"]  # Uppercase SHOULD is OK
        
      - name: requirements_have_criteria
        type: pattern_match
        pattern: "FR-\\d+"
        each_must_contain: "Given .* When .* Then"
        
      - name: interfaces_complete
        type: llm
        prompt: |
          Review the Interfaces section:
          {section:Interfaces}
          
          Are all interfaces complete with:
          - Parameter types and descriptions
          - Return types
          - Error conditions
          
          Answer: complete | incomplete with reasons
  
  temperature: 0.0
  max_tokens: 8000
  estimated_cost_usd: 0.05
```

## 10. Prompt Contract: SPEC.VALIDATE

```yaml
prompt_contract:
  id: "spec.validate.v1"
  version: "1.0.0"
  workflow: "SPEC"
  state: "VALIDATE"
  
  role: "Specification Reviewer"
  goal: "Comprehensive quality review before approval"
  
  inputs:
    required:
      - name: specification
        type: string
        format: markdown
        
      - name: analysis_report
        type: object
        
    context:
      - name: architecture_rules
        source: architecture.yaml
        
      - name: validation_checklist
        source: config/validation_checklist.yaml
  
  output:
    format: yaml
    schema:
      $ref: "#/schemas/validation_report"
  
  template:
    system: |
      # Role
      
      You are a Specification Reviewer performing final validation before implementation.
      
      # Output Format
      
      Output a YAML validation report:
      
      ```yaml
      overall_verdict: enum          # approved | approved_with_notes | needs_revision | rejected
      
      checklist_results:
        - check_id: string
          check_description: string
          status: enum               # pass | warn | fail
          notes: string
          evidence: string           # What you examined
      
      blocking_issues:               # Issues that prevent approval
        - issue_id: string
          location: string           # Where in spec
          description: string
          suggested_fix: string
      
      warnings:                      # Issues that should be fixed but don't block
        - warning_id: string
          location: string
          description: string
          recommendation: string
      
      strengths:                     # What the spec does well
        - string
      
      revision_guidance:             # If not approved
        priority_fixes: [string]     # Must fix
        recommended_improvements: [string]
        optional_enhancements: [string]
      
      approval_conditions:           # If approved_with_notes
        - string                     # What must be addressed during implementation
      ```
      
      # Validation Checklist
      
      ## Completeness (C)
      - C1: All functional requirements have acceptance criteria [BLOCKING]
      - C2: All interfaces fully specified (params, returns, errors) [BLOCKING]
      - C3: All entities have complete property definitions [BLOCKING]
      - C4: All error scenarios documented [REQUIRED]
      - C5: All edge cases identified [ADVISORY]
      
      ## Consistency (K)
      - K1: Interface names match entity names [REQUIRED]
      - K2: Data types consistent across spec [BLOCKING]
      - K3: Terminology consistent with glossary [REQUIRED]
      - K4: No contradictions between requirements [BLOCKING]
      
      ## Feasibility (F)
      - F1: Required dependencies exist or will be created [BLOCKING]
      - F2: Performance requirements achievable [REQUIRED]
      - F3: No unavailable external systems required [BLOCKING]
      
      ## Testability (T)
      - T1: All criteria in Given/When/Then format [BLOCKING]
      - T2: No subjective criteria ('fast', 'user-friendly') [REQUIRED]
      - T3: Boundary values specified for ranges [REQUIRED]
      
      ## Compliance (A)
      - A1: Interfaces in correct architectural layer [BLOCKING]
      - A2: No prohibited dependencies [BLOCKING]
      - A3: Follows established patterns [REQUIRED]
      
      # Verdict Rules
      
      - **approved**: All checks pass
      - **approved_with_notes**: No BLOCKING fails, some REQUIRED warns, clear conditions
      - **needs_revision**: Any BLOCKING fails or multiple REQUIRED fails
      - **rejected**: Fundamental problems requiring restart
      
      # Be Critical
      
      It's better to catch problems now than during implementation.
      Be specific about what's wrong and how to fix it.
    
    user: |
      # Specification to Review
      
      {specification}
      
      # Analysis Report (for context)
      
      {analysis_report}
      
      # Architecture Rules
      
      {architecture_rules}
      
      # Task
      
      Perform a comprehensive review of the specification.
      Check every item in the validation checklist.
      Be critical - catch problems now.
      
      Output YAML validation report only.
  
  verification:
    schema_validation: true
    custom_checks:
      - name: verdict_matches_results
        type: custom
        check: |
          if any(r.status == 'fail' for r in checklist_results if r.check_id.startswith(('C1','C2','C3','K2','K4','F1','F3','T1','A1','A2'))):
            return verdict in ['needs_revision', 'rejected']
          return True
        message: "Verdict must match checklist results"
        
      - name: blocking_issues_documented
        type: custom
        check: |
          fail_count = sum(1 for r in checklist_results if r.status == 'fail')
          return len(blocking_issues) >= fail_count
        message: "All failures must be documented as blocking issues"
  
  temperature: 0.0
  max_tokens: 3000
  estimated_cost_usd: 0.02
```

## 11. Prompt Assembly Engine

```python
class PromptAssembler:
    """
    Assembles prompts from contracts and inputs.
    
    Ensures consistent prompt structure regardless of execution mode.
    """
    
    def __init__(self, contracts_dir: Path):
        self.contracts = self._load_contracts(contracts_dir)
    
    def assemble(
        self,
        contract_id: str,
        inputs: dict,
        context: dict
    ) -> str:
        """Assemble a prompt from contract and inputs."""
        contract = self.contracts[contract_id]
        
        # Validate inputs against contract
        self._validate_inputs(contract, inputs)
        
        # Build system message
        system = contract['template']['system']
        
        # Build user message with variable substitution
        user = self._substitute_variables(
            contract['template']['user'],
            inputs,
            context
        )
        
        # Combine into final prompt
        # Note: For API, these become separate system/user messages
        # For human-in-loop, we combine them
        prompt = f"""=== SYSTEM ===
{system}

=== USER ===
{user}"""
        
        return prompt
    
    def _substitute_variables(
        self,
        template: str,
        inputs: dict,
        context: dict
    ) -> str:
        """Replace {variables} in template."""
        result = template
        
        # Simple variable substitution
        for key, value in {**inputs, **context}.items():
            if isinstance(value, str):
                result = result.replace(f"{{{key}}}", value)
            elif isinstance(value, dict):
                result = result.replace(f"{{{key}}}", yaml.dump(value))
            elif isinstance(value, list):
                result = result.replace(f"{{{key}}}", yaml.dump(value))
        
        # Handle conditionals {if var}...{endif}
        result = self._process_conditionals(result, {**inputs, **context})
        
        # Handle loops {for item in list}...{endfor}
        result = self._process_loops(result, {**inputs, **context})
        
        return result
    
    def get_verification_checks(self, contract_id: str) -> List[Check]:
        """Get verification checks for a contract."""
        contract = self.contracts[contract_id]
        return contract.get('verification', {}).get('custom_checks', [])
    
    def get_output_schema(self, contract_id: str) -> dict:
        """Get output schema for validation."""
        contract = self.contracts[contract_id]
        return contract.get('output', {}).get('schema', {})
```

## 12. Contract Versioning

```yaml
# Contracts are versioned and immutable within a version

versioning:
  format: "MAJOR.MINOR.PATCH"
  
  rules:
    major_bump:
      - "Breaking change to output schema"
      - "Removing required fields"
      - "Changing field types"
    
    minor_bump:
      - "Adding optional fields"
      - "Adding new examples"
      - "Clarifying rules"
    
    patch_bump:
      - "Typo fixes"
      - "Formatting improvements"
      - "No functional change"
  
  compatibility:
    - "Outputs from v1.x should validate against v1.0 schema"
    - "Verification checks should be backward compatible"
```

## 13. Testing Contracts

```python
class ContractTestSuite:
    """Tests to ensure contracts produce consistent, valid output."""
    
    def test_schema_validity(self, contract_id: str):
        """Contract's output schema is valid JSON Schema."""
        pass
    
    def test_example_outputs_validate(self, contract_id: str):
        """All examples in contract validate against schema."""
        pass
    
    def test_determinism(self, contract_id: str, inputs: dict):
        """Same inputs produce same output structure."""
        pass
    
    def test_verification_catches_bad_output(self, contract_id: str):
        """Verification checks reject invalid outputs."""
        pass
    
    def test_mode_equivalence(self, contract_id: str, inputs: dict):
        """Human and API modes produce equivalent outputs."""
        pass
```
