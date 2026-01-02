# Context Engineering Assessment

## AgentForge API Context Management Strategy

**Document Version:** 1.0  
**Date:** January 2025  
**Status:** Strategic Analysis Complete  
**Purpose:** Capture analysis of how to achieve Claude Code-level effectiveness via API

---

## Executive Summary

This document captures the strategic analysis of how AgentForge can achieve results comparable to Claude Code when using the Anthropic API directly. The core finding is that **there are no fundamental technical barriers** - Claude Code's effectiveness comes from disciplined context management, not special API access.

### Key Conclusions

1. **Full API Parity Exists**: Native tools, extended thinking, prompt caching - all available
2. **We Can Exceed Claude Code** in some areas: Pre-computed analysis, explicit control, audit trails
3. **Design Differences Are Choices**: Autonomous vs interactive is a feature, not limitation
4. **The Gap Is Implementation**: We need to build the infrastructure, not unlock hidden features

---

## Table of Contents

1. [The Fundamental Insight](#1-the-fundamental-insight)
2. [What Claude Code Actually Has](#2-what-claude-code-actually-has)
3. [Limitation Analysis](#3-limitation-analysis)
4. [Multi-Project Scope](#4-multi-project-scope)
5. [Generalized Context Architecture](#5-generalized-context-architecture)
6. [The AGENT.md Chain](#6-the-agentmd-chain)
7. [Token Budget Strategy](#7-token-budget-strategy)
8. [Correctness Integration](#8-correctness-integration)
9. [Transparency Requirements](#9-transparency-requirements)
10. [Implementation Priorities](#10-implementation-priorities)

---

## 1. The Fundamental Insight

Claude Code's success isn't magic - it's **disciplined context reconstruction**. The API gives us the same model; we just need to give it the same quality of context.

```
COMPARISON MATRIX
─────────────────────────────────────────────────────────────────────────────────
                    CLAUDE CODE              API (naive)              API (optimized)
─────────────────────────────────────────────────────────────────────────────────
Persistent Config   CLAUDE.md               Giant system prompt      Compact fingerprint
Tool Results        Cleared after use       Accumulated forever      Facts extracted
Compaction          At 95% automatic        Hope it fits             Budget enforced
File Access         Just-in-time            Pre-load everything      Fetch on demand
─────────────────────────────────────────────────────────────────────────────────
```

**The Prime Directive**: Optimize token usage WITHOUT sacrificing useful context that produces valuable results. We achieve this through:
- Structured, high-signal context over verbose prose
- Conclusions (facts) over raw data
- Pre-computation over runtime inference
- Explicit budgeting over hope-based fitting

---

## 2. What Claude Code Actually Has

### 2.1 Context Structure Analysis

From reverse-engineering Claude Code's behavior:

```
┌─────────────────────────────────────────────────────────────────┐
│ CLAUDE CODE CONTEXT STRUCTURE                                    │
├─────────────────────────────────────────────────────────────────┤
│ 1. System Instructions (~2000 tokens)                           │
│    - Core behavioral rules                                       │
│    - Tool definitions                                            │
│    - Response format                                             │
│                                                                  │
│ 2. CLAUDE.md Chain (~500-2000 tokens)                           │
│    - ~/.claude/CLAUDE.md (global preferences)                    │
│    - project/CLAUDE.md (project-specific)                        │
│    - Survives compaction                                         │
│                                                                  │
│ 3. Compacted Summary (when triggered)                           │
│    - "Here's what we've done so far..."                         │
│    - Conclusions, not history                                    │
│                                                                  │
│ 4. Recent Context (~2000-4000 tokens)                           │
│    - Last few tool calls + results                              │
│    - Current working state                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Mechanisms

| Mechanism | How It Works | Why It Matters |
|-----------|--------------|----------------|
| CLAUDE.md chain | Hierarchical config files | User control, project specificity |
| Automatic compaction | Summarize at 95% capacity | Prevents context overflow |
| Tool result clearing | Discard raw output, keep conclusions | Reduces token bloat |
| Just-in-time retrieval | Fetch files when needed | Avoids pre-loading everything |

---

## 3. Limitation Analysis

### 3.1 Native Tool Integration

**What Claude Code Has:**
- Tools defined in structured API parameter
- Model outputs tool_use blocks natively
- Tool results fed back as tool_result blocks
- Automatic formatting and parsing

**What We Have Access To:**
```python
# The Anthropic API DOES support native tools!
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=[
        {
            "name": "read_file",
            "description": "Read contents of a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    ],
    tool_choice={"type": "auto"},
    messages=[...]
)
```

**Gap Assessment: NONE**

We have full access to native tool integration. Early prototypes using text-based tool parsing should be migrated to native API tools.

**Action Required:**
- Refactor to use native `tools` parameter
- Use `tool_use` / `tool_result` content blocks
- Remove text-based tool parsing (keep as fallback only)

---

### 3.2 Automatic Compaction

**What Claude Code Has:**
- Monitors context usage continuously
- At ~95% capacity, triggers summarization
- Summarization done BY Claude mid-conversation
- CLAUDE.md content preserved through compaction
- Seamless to user

**What We Have Access To:**
- Manual implementation with same capabilities
- Choice of rules-based OR LLM summarization
- Explicit control over what's preserved

**Gap Assessment: MINOR (implementation needed)**

| Aspect | Claude Code | API Implementation |
|--------|-------------|-------------------|
| Triggering | Automatic | We implement the trigger |
| Summarization | Built-in | Extra API call |
| Preservation | CLAUDE.md | We define what's preserved |
| Seamlessness | Native | Explicit but can be seamless |

**What Makes It Different:**
- We pay for summarization calls (but save on future calls)
- We must explicitly manage the trigger
- We have MORE control over what's preserved

**Action Required:**
- Implement `CompactionManager` with configurable threshold
- Define preservation rules (fingerprint always preserved)
- Add summarization fallback for complex compactions

---

### 3.3 Extended Thinking

**What Claude Code Has:**
- "Thinking..." indicator in UI
- Model reasons through complex problems
- Thinking is visible for transparency
- Uses more tokens but better results
- Automatic for complex tasks

**What We Have Access To:**
```python
# Extended thinking IS available via API!
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    messages=[...]
)

# Response includes thinking blocks for transparency
for block in response.content:
    if block.type == "thinking":
        print(f"Thinking: {block.thinking}")
```

**Gap Assessment: NONE**

Extended thinking is fully available. This aligns perfectly with our "total transparency in thinking" requirement.

**Action Required:**
- Add `thinking` parameter support to LLM executor
- Configure thinking budget per task type
- Log thinking blocks for audit/debugging
- Use for: complex refactoring, multi-step planning, ambiguous situations

---

### 3.4 CLAUDE.md Chain

**What Claude Code Has:**
```
~/.claude/CLAUDE.md        (global preferences)
project/CLAUDE.md          (project-specific)
project/subdir/CLAUDE.md   (directory-specific)

- Hierarchical override (deeper wins)
- User-editable
- Survives compaction
- Read at conversation start
```

**What We Can Build:**
```
~/.agentforge/AGENT.md           (global preferences)
project/.agentforge/AGENT.md     (project-specific)
project/.agentforge/tasks/       (task-type overrides)
  ├── fix_violation.md
  ├── implement_feature.md
  └── discovery.md

PLUS (improvements over Claude Code):
- Auto-generated fingerprints (more accurate)
- Versioned (tracked in git)
- Validated (schema-checked)
- Dynamic (regenerated on codebase changes)
```

**Gap Assessment: NONE (we can do BETTER)**

We can implement the same hierarchical config with additional features:
- Schema validation
- Auto-generation from codebase analysis
- Version tracking
- Task-type specialization

**Action Required:**
- Implement AGENT.md loader with hierarchy
- Support markdown + YAML frontmatter format
- Auto-generate fingerprint sections
- Validate against schema

---

### 3.5 Multi-file Awareness

**What Claude Code Has:**
- Direct file system access
- Real-time directory navigation
- Search across files (grep, find)
- Mental model of codebase built on-demand
- Multiple files simultaneously

**What We Have:**
```
PRE-COMPUTED (available immediately):
- AST analysis of all Python files
- Dependency graphs
- Pattern detection
- Discovery profiles

ON-DEMAND (via tools):
- read_file tool
- search_code tool
- list_directory tool
```

**Gap Assessment: DIFFERENT, NOT WORSE**

| Aspect | Claude Code | AgentForge |
|--------|-------------|------------|
| Initial awareness | On-demand exploration | Pre-computed analysis |
| Speed of access | Real-time | Cached (faster) |
| Depth of analysis | Surface (reads files) | Deep (AST parsed) |
| Token cost | Pays for every read | Pre-computed, cheaper |
| Dynamic changes | Sees immediately | Must refresh cache |

**What We Do Better:**
- Pre-computed AST gives STRUCTURED understanding
- Dependency graphs show relationships Claude Code must discover
- Pattern detection already done, not runtime inference
- Cheaper (no token cost for analysis)

**What Claude Code Does Better:**
- Real-time changes visible immediately
- Exploratory navigation more natural
- No cache invalidation issues

**Action Required:**
- Implement cache invalidation on file changes
- Add file watcher for real-time updates (optional)
- Ensure tools available for dynamic exploration
- Pre-compute more (class hierarchies, call graphs)

---

### 3.6 Interactive Debugging

**What Claude Code Has:**
- Real-time conversation
- Clarifying questions mid-task
- Show intermediate results
- User can redirect/correct
- Natural debugging flow

**What We Have:**
- Autonomous execution
- Structured escalation for questions
- Batch processing
- Progress callbacks
- Post-hoc review

**Gap Assessment: DESIGN CHOICE**

This isn't a technical limitation - it's a different design goal.

| Mode | Best For | Trade-off |
|------|----------|-----------|
| Interactive | Exploratory work, debugging, learning | Requires human presence |
| Autonomous | Scale, overnight runs, CI/CD | Less immediate feedback |

**What We Could Add:**
```python
class ExecutionMode(Enum):
    AUTONOMOUS = "autonomous"      # Run to completion
    SUPERVISED = "supervised"      # Pause at checkpoints
    INTERACTIVE = "interactive"    # Real-time human-in-loop
```

**Action Required:**
- Add `ExecutionMode` enum to task configuration
- Implement `SUPERVISED` mode (pause at phase transitions)
- Consider `INTERACTIVE` mode for specific use cases
- Escalation already provides async human-in-loop

---

### 3.7 Additional Capabilities

| Capability | Gap | Notes |
|------------|-----|-------|
| Streaming responses | NONE | API supports streaming |
| Context window size | NONE | Same 200K window |
| Prompt caching | NONE | API supports, 90% cheaper |
| Rate limits | TIER DEPENDENT | Scale tier for production |
| Model version | NONE | We specify exact version |
| Possible fine-tuning | UNKNOWN | Claude Code might have task-specific tuning |

---

### 3.8 Summary Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│ CAPABILITY COMPARISON: CLAUDE CODE vs AGENTFORGE API             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ✅ FULL PARITY (no gap):                                         │
│    • Native tool integration (use tools parameter)               │
│    • Extended thinking (use thinking parameter)                  │
│    • Context window size (200K)                                  │
│    • Prompt caching (automatic)                                  │
│    • Streaming (supported)                                       │
│    • Model version (we choose)                                   │
│                                                                  │
│ ✅ WE CAN DO BETTER:                                             │
│    • AGENT.md chain (dynamic fingerprints + user config)         │
│    • Multi-file awareness (pre-computed AST > runtime reads)     │
│    • Compaction (explicit control > black box)                   │
│    • Transparency (full audit trail)                             │
│                                                                  │
│ ⚠️ DIFFERENT BY DESIGN:                                          │
│    • Interactive debugging (we optimize for autonomy)            │
│    • Execution mode (async vs real-time)                         │
│                                                                  │
│ ❓ UNKNOWN:                                                       │
│    • Possible fine-tuning advantages in Claude Code              │
│    • Internal optimizations we can't see                         │
│                                                                  │
│ 💰 COST CONSIDERATION:                                           │
│    • Scale tier needed for production autonomy                   │
│    • Thinking mode increases token cost                          │
│    • But: pre-computation REDUCES ongoing costs                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Multi-Project Scope

AgentForge is not a single-task tool. It's a **general-purpose agentic framework** for managing development at scale.

### 4.1 Task Type Diversity

| Task Type | Context Needs | Key Differences |
|-----------|---------------|-----------------|
| `fix_violation` | Violation details, target function, extraction suggestions | Narrow focus, pre-computed fixes |
| `implement_feature` | Spec requirements, failing tests, existing patterns | Needs spec context, test expectations |
| `write_tests` | Acceptance criteria, code under test, test patterns | Needs testable interface, coverage goals |
| `refactor` | Code smells, safety constraints, pattern library | Needs smell detection, refactoring catalog |
| `spec_design` | Requirements, stakeholder constraints, domain model | Needs requirements elicitation |
| `code_review` | Diff, standards, historical issues | Needs change context, reviewer guidelines |
| `discovery` | File structure, dependencies, pattern detection | Needs broad view, not narrow focus |
| `bridge` | Existing code, target contracts, mapping rules | Needs bidirectional mapping |

### 4.2 Multi-Project Operating Context

```
┌─────────────────────────────────────────────────────────────────┐
│ AGENTFORGE OPERATING CONTEXT                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GLOBAL LEVEL                                                    │
│  └─► User preferences                                            │
│  └─► Cross-project learnings                                     │
│  └─► Tool configurations                                         │
│                                                                  │
│  PROJECT LEVEL (many)                                            │
│  ├─► Project A (Python, FastAPI)                                 │
│  │   ├─► Fingerprint A                                           │
│  │   ├─► Task 1: fix_violation                                   │
│  │   ├─► Task 2: implement_feature                               │
│  │   └─► Task 3: write_tests                                     │
│  │                                                               │
│  ├─► Project B (C#, Clean Architecture)                          │
│  │   ├─► Fingerprint B                                           │
│  │   ├─► Task 4: discovery                                       │
│  │   └─► Task 5: bridge                                          │
│  │                                                               │
│  └─► Project C (TypeScript, React)                               │
│      └─► ...                                                     │
│                                                                  │
│  ISOLATION REQUIREMENTS:                                         │
│  • Context MUST NOT leak between projects                        │
│  • Fingerprints are project-specific                             │
│  • But learnings CAN transfer (patterns, not data)               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Generalized Context Architecture

### 5.1 Context Template System

Each task type defines its own context requirements through templates:

```yaml
context_templates:
  # BASE TEMPLATE (inherited by all task types)
  base:
    tier1_always:
      - section: fingerprint
        source: project_fingerprint
        max_tokens: 500
        compaction: never
        
      - section: task_frame
        source: task_definition
        max_tokens: 300
        compaction: never
        
      - section: phase_state
        source: phase_machine
        max_tokens: 100
        compaction: never
    
    tier2_phase_dependent:
      # Defined by specific task type
      
    tier3_on_demand:
      - section: historical_facts
        source: fact_store
        max_tokens: 500
        compaction: aggressive
```

### 5.2 Task-Type Templates

Each task type extends the base template with phase-specific sections:

**fix_violation:**
- Analyze: violation_details, check_definition, file_overview
- Implement: target_function_source, extraction_suggestions, action_hints
- Verify: verification_command, recent_results

**implement_feature:**
- Analyze: spec_requirements, acceptance_criteria, existing_tests
- Implement: failing_tests, target_location, similar_patterns
- Verify: test_expectations, coverage_delta

**discovery:**
- Scan: file_structure, entry_points
- Analyze: dependency_graph, pattern_candidates, architecture_hints
- Synthesize: discovered_patterns, zone_boundaries

### 5.3 Tiered Context Budget

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1: ALWAYS PRESENT (~800 tokens)                            │
│ ────────────────────────────────────────────────────────────────│
│ • Project fingerprint (500 tokens)                              │
│ • Current task goal + success criteria (200 tokens)             │
│ • Current phase + step budget (100 tokens)                      │
│                                                                  │
│ These tokens are NON-NEGOTIABLE. Every call gets them.          │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2: PHASE-DEPENDENT (~1000-2000 tokens)                     │
│ ────────────────────────────────────────────────────────────────│
│ Content varies by task type AND current phase.                   │
│ Pre-computed analysis, action hints, relevant code.              │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3: ON-DEMAND (~500-1500 tokens)                            │
│ ────────────────────────────────────────────────────────────────│
│ • Historical facts (only if relevant)                            │
│ • Additional file contents (only if requested)                   │
│ • Error details (only if debugging)                              │
│                                                                  │
│ These are FETCHED, not pre-loaded.                              │
├─────────────────────────────────────────────────────────────────┤
│ TIER 4: NEVER IN CONTEXT                                        │
│ ────────────────────────────────────────────────────────────────│
│ • Raw tool output (extract facts, discard raw)                   │
│ • Full file contents (only relevant sections)                    │
│ • Old action history (keep last 2-3 only)                        │
│ • Successful operations (we know they worked)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. The AGENT.md Chain

### 6.1 Hierarchy Structure

```
~/.agentforge/AGENT.md                    # Global preferences
project/.agentforge/AGENT.md              # Project-specific
project/.agentforge/tasks/fix_violation.md  # Task-type specific
```

### 6.2 Example Global AGENT.md

```yaml
---
# Global AgentForge Preferences
# This file is always included in agent context

preferences:
  communication: concise
  risk_tolerance: conservative
  
defaults:
  max_steps: 20
  require_tests: true
  auto_commit: false
  
style:
  code_comments: minimal
  docstrings: google
  
instructions: |
  - Always verify tests pass before marking complete
  - Prefer small, focused changes over large refactors
  - When uncertain, escalate rather than guess
```

### 6.3 Example Project AGENT.md

```yaml
---
# AgentForge config for this project

project:
  name: my-project
  language: python
  test_command: "pytest -xvs"
  
patterns:
  docstrings: numpy  # Override global
  
constraints:
  - "Never modify files in /vendor"
  - "All new code must have type hints"
  
instructions: |
  This is a data pipeline project. Be careful with:
  - Null handling in transforms
  - Memory usage in large file operations
```

### 6.4 Fingerprint Hierarchy

```yaml
fingerprint:
  # LEVEL 1: Global (user preferences)
  global:
    user_preferences:
      communication_style: "technical, concise"
      risk_tolerance: "conservative"
    learned_patterns:
      effective_strategies:
        - "extract_function reduces complexity reliably"
      
  # LEVEL 2: Project (cached, regenerated on changes)
  project:
    identity:
      name: "agentforge"
      language: "python"
    patterns:
      architecture: "clean architecture"
      naming: "snake_case"
      
  # LEVEL 3: Task Type (workflow-specific)
  task_type:
    type: "fix_violation"
    workflow:
      phases: [analyze, implement, verify]
    constraints:
      correctness_first: true
      
  # LEVEL 4: Task Instance (this execution)
  instance:
    task_id: "fix-V-abc123"
    target:
      file: "src/executor.py"
      entity: "execute"
```

---

## 7. Token Budget Strategy

### 7.1 Budget Allocation

| Component | Tokens | % of 4000 | Notes |
|-----------|--------|-----------|-------|
| System prompt | 150 | 4% | Minimal, cacheable |
| Fingerprint | 500 | 12% | Never compacted |
| Task frame | 300 | 8% | Never compacted |
| Phase state | 100 | 2% | Never compacted |
| Tier 2 (phase) | 1500 | 38% | Compactable |
| Tier 3 (on-demand) | 1000 | 25% | Aggressive compact |
| Response buffer | 450 | 11% | Reserved |

### 7.2 Compaction Strategy

Progressive compaction sacrifices low-value tokens first:

```
Phase 1: Truncate precomputed (most compressible)
Phase 2: Reduce facts to high-confidence only
Phase 3: Reduce actions to top 5
Phase 4: Truncate domain context
Phase 5: Reduce recent actions to 1
Phase 6: LLM summarization (last resort)
```

### 7.3 Cost Comparison

```
NAIVE APPROACH (accumulated context)
────────────────────────────────────────────────────────────────
Step 1:  System(2000) + Task(500) + Tool1(1000) = 3500 tokens
Step 5:  System(2000) + Task(500) + Tools(5000) = 7500 tokens
Step 10: System(2000) + Task(500) + Tools(10000) = 12500 tokens
Step 20: System(2000) + Task(500) + Tools(20000) = 22500 tokens

Total for 20 steps: ~250,000 tokens (input alone!)

MINIMAL CONTEXT APPROACH (reconstructed)
────────────────────────────────────────────────────────────────
Every step: System(150) + Context(3000) = 3150 tokens

Total for 20 steps: ~63,000 tokens (75% reduction)

With prompt caching (system prompt cached):
Total effective cost: ~50,000 token-equivalents
```

---

## 8. Correctness Integration

### 8.1 Correctness Checkpoints in Context Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ CORRECTNESS CHECKPOINTS IN CONTEXT FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. TASK CREATION                                                │
│     └─► Embed test_path in task context (from lineage)           │
│     └─► Embed success_criteria (verifiable)                      │
│                                                                  │
│  2. PRECOMPUTATION                                               │
│     └─► Validate extraction suggestions with rope                │
│     └─► Only include suggestions that CAN work                   │
│                                                                  │
│  3. ACTION EXECUTION                                             │
│     └─► Save original before modification                        │
│     └─► Run targeted tests AFTER every file change               │
│     └─► REVERT if tests regress                                  │
│                                                                  │
│  4. FACT EXTRACTION                                              │
│     └─► Test results become VERIFICATION facts (confidence=1.0)  │
│     └─► Failed actions become ERROR facts (prevent repeat)       │
│                                                                  │
│  5. CONTEXT REBUILD                                              │
│     └─► Always include current verification status               │
│     └─► Block 'complete' unless checks pass                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Never Compromise Correctness for Tokens

- Test verification runs ALWAYS, even if over token budget
- Verification status is NEVER compacted
- Error facts are PRESERVED to prevent repeated mistakes
- Success criteria CANNOT be removed from context

---

## 9. Transparency Requirements

### 9.1 Audit Trail

Every context build is logged:

```yaml
# .agentforge/context_audit/fix-V-abc123/step_4.yaml
task_id: fix-V-abc123
step: 4
timestamp: 2024-01-15T10:30:00Z

token_breakdown:
  fingerprint: 487
  task_frame: 312
  understanding: 398
  precomputed: 1203
  actions: 287
  recent: 156
  directive: 89
  total: 2932

compaction:
  applied: false
  budget: 4000
  headroom: 1068

context_hash: "sha256:abc123..."  # For reproducibility
```

### 9.2 Thinking Block Logging

When extended thinking is enabled:

```yaml
thinking_log:
  task_id: fix-V-abc123
  step: 4
  thinking_budget: 10000
  thinking_used: 3500
  
  thinking_content: |
    Let me analyze the extraction suggestions...
    The first suggestion at lines 67-78 looks promising because...
    However, I need to verify that extracting this block won't...
```

### 9.3 Reproducibility

- Context snapshots enable replay
- Deterministic context building (same input = same output)
- Hash verification for debugging

---

## 10. Implementation Priorities

### 10.1 Phase 1: Foundation (Critical)

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| Native tools API integration | P0 | 2d | Correctness + features |
| Extended thinking support | P0 | 1d | Quality + transparency |
| AGENT.md loader | P0 | 2d | Project customization |
| Context template system | P0 | 3d | Multi-task support |

### 10.2 Phase 2: Optimization

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| Prompt caching optimization | P1 | 1d | Cost reduction |
| Compaction manager | P1 | 2d | Context management |
| Fingerprint generator | P1 | 2d | Better context |
| Tier 2 phase templates | P1 | 3d | Task specialization |

### 10.3 Phase 3: Enhancement

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| File watcher integration | P2 | 2d | Real-time awareness |
| Supervised execution mode | P2 | 2d | Debugging support |
| Cross-project learning | P2 | 3d | Knowledge transfer |
| Context audit dashboard | P2 | 2d | Transparency |

---

## Appendix A: API Feature Reference

### Native Tools

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=[...],
    tool_choice={"type": "auto"},  # or "any", "tool"
    messages=[...]
)
```

### Extended Thinking

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[...]
)
```

### Prompt Caching

Automatic when system prompt is stable. 90% discount on cached tokens.

### Streaming

```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        yield text
```

---

## Appendix B: Related Documents

- [Minimal Context Architecture Spec](./minimal_context_architecture_spec.yaml)
- [North Star Specification](../specs/NorthStar/north_star_specification.md)
- [Agent Harness Implementation Plan](../specs/agent-harness/PLAN.md)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2025 | Claude + Human | Initial assessment |
