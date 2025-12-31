# Using the Agent Harness Implementation Plan with Claude Code

## Overview

This guide explains how to use the implementation plan document to build the Agent Harness using Claude Code (Anthropic's CLI coding agent).

---

## Setup

### Step 1: Add the Plan to Your Project

Save the implementation plan to your AgentForge project:

```bash
# Create a specs directory for implementation plans
mkdir -p specs/agent-harness

# Copy the implementation plan (assuming you downloaded it)
cp agent_harness_implementation_plan.md specs/agent-harness/PLAN.md

# Also copy the proposal for architectural context
cp agentforge_autonomous_framework_proposal.md specs/agent-harness/ARCHITECTURE.md
```

### Step 2: Create a CLAUDE.md File

Claude Code uses `CLAUDE.md` as persistent instructions. Add harness-specific guidance:

```bash
# Add to your existing CLAUDE.md or create one
cat >> CLAUDE.md << 'EOF'

## Agent Harness Development

When working on the Agent Harness:

1. **Read the plan first**: `specs/agent-harness/PLAN.md`
2. **Follow phases in order**: Dependencies matter
3. **Use AgentForge workflows**: SPEC for design, TDFLOW for implementation
4. **Verify after each change**: `python execute.py conformance check`
5. **Follow existing patterns**: Check `tools/spec/domain.py` and `tools/tdflow/domain.py`

### Current Phase
<!-- Update this as you progress -->
Phase: 0 (Foundation)
Status: Not started

### Harness File Locations
- Implementation: `tools/harness/`
- Tests: `tests/unit/harness/`
- Integration tests: `tests/integration/harness/`
EOF
```

### Step 3: Create a Session Tracking File

Track progress across Claude Code sessions:

```bash
cat > specs/agent-harness/PROGRESS.md << 'EOF'
# Agent Harness Progress Tracker

## Current State
- **Active Phase**: 0 (Foundation)
- **Active Component**: None
- **Workflow Stage**: Not started
- **Last Session**: N/A

## Phase Checklist

### Phase 0: Foundation
- [ ] Run self-discovery
- [ ] Save baseline
- [ ] Create directory structure

### Phase 1: Session Manager
- [ ] SPEC: Intake
- [ ] SPEC: Clarify
- [ ] SPEC: Analyze
- [ ] SPEC: Draft
- [ ] SPEC: Validate
- [ ] TDFLOW: Red (tests)
- [ ] TDFLOW: Green (implementation)
- [ ] TDFLOW: Verify
- [ ] Conformance check

### Phase 2: Memory System
- [ ] SPEC complete
- [ ] TDFLOW complete
- [ ] Conformance check

### Phase 3: Tool Selector
- [ ] SPEC complete
- [ ] TDFLOW complete
- [ ] Conformance check

### Phase 4: Agent Monitor
- [ ] SPEC complete
- [ ] TDFLOW complete
- [ ] Conformance check

### Phase 5: Recovery Strategies
- [ ] SPEC complete
- [ ] TDFLOW complete
- [ ] Conformance check

### Phase 6: Human Escalation
- [ ] SPEC complete
- [ ] TDFLOW complete
- [ ] Conformance check

### Phase 7: Agent Orchestrator
- [ ] SPEC complete
- [ ] TDFLOW complete
- [ ] Conformance check

### Phase 8: Integration Testing
- [ ] All scenarios passing
- [ ] Final conformance check

## Session Log
<!-- Add entries as you work -->

EOF
```

---

## Working with Claude Code

### Starting a New Session

When you start Claude Code, give it context:

```bash
claude
```

Then in Claude Code:

```
Read the implementation plan at specs/agent-harness/PLAN.md and the progress 
tracker at specs/agent-harness/PROGRESS.md. Tell me where we are and what's next.
```

### Phase 0: Foundation (First Session)

```
Let's start Phase 0 of the Agent Harness implementation. According to the plan:

1. Run self-discovery on the AgentForge codebase
2. Save a baseline for conformance
3. Create the harness directory structure

Execute these steps and update PROGRESS.md when done.
```

### Starting a New Phase

When beginning a new phase (e.g., Phase 1):

```
We're starting Phase 1: Session Manager. 

Read the intake prompt from specs/agent-harness/PLAN.md (the Phase 1 section).

First, let's run the AgentForge SPEC workflow. Execute:
  python execute.py intake

Then provide the intake prompt from the plan.
```

### Continuing SPEC Workflow

After intake:

```
The intake is complete. Continue with SPEC clarify phase.

The expected clarifications are in the plan - use those as the answers 
when the system asks questions.
```

### Transitioning to TDFLOW

After SPEC is validated:

```
SPEC is complete for Session Manager. Now let's do TDFLOW.

1. Start TDFLOW with the specification
2. Generate failing tests (RED phase)
3. Show me the tests before we proceed to GREEN
```

### Implementing (GREEN Phase)

```
The tests look good. Now implement the Session Manager to make them pass.

Follow the patterns from:
- tools/spec/domain.py (dataclasses, domain entities)
- tools/tdflow/domain.py (workflow state)

After implementation, run the tests and show me results.
```

### Verification

After implementation:

```
Run verification:
1. python -m pytest tests/unit/harness/test_session_manager.py -v
2. python execute.py conformance check
3. python execute.py ci run --mode incremental

Show me any failures or violations.
```

### Ending a Session

Before ending:

```
Update specs/agent-harness/PROGRESS.md with:
- What we completed
- Current state
- Any issues or notes for next session

Also commit our work:
git add -A
git commit -m "Phase 1: Session Manager - [current status]"
```

---

## Prompt Templates by Workflow Stage

### SPEC Intake Prompt

```
We're doing SPEC intake for [COMPONENT NAME].

The intake prompt is in specs/agent-harness/PLAN.md under Phase [N].

Run: python execute.py intake

Then provide the intake prompt from the plan. Save the intake record.
```

### SPEC Clarify Prompt

```
Continue SPEC workflow - clarify phase.

Use the clarifications from the plan as answers. If there are additional 
questions not in the plan, use your judgment based on the architecture 
document at specs/agent-harness/ARCHITECTURE.md.
```

### SPEC Draft Prompt

```
Generate the specification draft. 

Make sure it includes:
- All requirements from intake
- Clarifications incorporated
- Testable acceptance criteria
- Interface definitions
```

### TDFLOW Red Prompt

```
Start TDFLOW for [COMPONENT].

Generate comprehensive failing tests that cover:
- Happy path
- Error cases
- Edge cases
- Integration points

Put tests in tests/unit/harness/test_[component].py
```

### TDFLOW Green Prompt

```
Implement [COMPONENT] to make all tests pass.

Follow patterns from existing code:
- Dataclasses for domain entities
- Result pattern for error handling
- Type hints throughout
- Docstrings for public methods

Put implementation in tools/harness/[component].py
```

### Verification Prompt

```
Run full verification:

1. Unit tests: pytest tests/unit/harness/ -v
2. Conformance: python execute.py conformance check
3. CI check: python execute.py ci run --mode incremental

Fix any issues before we proceed.
```

---

## Handling Long Components

For complex phases like Agent Orchestrator:

### Break Into Sub-Tasks

```
Phase 7 (Orchestrator) is large. Let's break it into sub-tasks:

1. First: Core orchestrator class with initialization
2. Second: The agent loop (PERCEIVE → PLAN → ACT → VERIFY)
3. Third: Integration with all harness components
4. Fourth: CLI commands

Start with sub-task 1. Show me the design before implementing.
```

### Incremental Testing

```
Before moving to the next sub-task:
1. Run existing tests
2. Add tests for new functionality
3. Verify no regressions

Show me test results.
```

---

## Resuming After a Break

When returning to the project:

```
I'm resuming work on the Agent Harness.

1. Read specs/agent-harness/PROGRESS.md for current state
2. Read the last few entries in the session log
3. Tell me exactly where we left off and what's next

Don't make any changes yet - just summarize the status.
```

Then:

```
Good. Let's continue from [where we left off].

[Specific instruction based on status]
```

---

## Troubleshooting

### If Tests Fail

```
Tests are failing. Before fixing:

1. Show me the failing test output
2. Identify root cause
3. Propose fix approach

Don't change code until I approve the approach.
```

### If Conformance Fails

```
Conformance check found violations.

1. List all violations
2. For each, explain what pattern was violated
3. Propose fixes

Show me the specific code changes needed.
```

### If Stuck

```
I'm stuck on [problem].

1. Re-read the relevant section of PLAN.md
2. Check ARCHITECTURE.md for design guidance
3. Look at similar existing code in the project
4. Propose 2-3 alternative approaches

Let's discuss before proceeding.
```

---

## Quick Reference

### Key Commands

```bash
# Discovery
python execute.py discover --path . --verbose

# SPEC workflow
python execute.py intake
python execute.py spec status
python execute.py spec validate

# TDFLOW workflow  
python execute.py tdflow start --spec [path]
python execute.py tdflow red
python execute.py tdflow green
python execute.py tdflow verify

# Verification
python execute.py conformance check
python execute.py ci run --mode incremental
pytest tests/unit/harness/ -v
```

### Key Files

```
specs/agent-harness/
├── PLAN.md              # Implementation plan (this guide references)
├── ARCHITECTURE.md      # Architectural proposal
└── PROGRESS.md          # Progress tracker (update each session)

tools/harness/           # Implementation goes here
tests/unit/harness/      # Unit tests go here
tests/integration/harness/  # Integration tests
```

### Session Workflow

```
1. Start Claude Code
2. Load context (plan + progress)
3. Identify current phase/step
4. Execute step
5. Verify (tests + conformance)
6. Update progress tracker
7. Commit changes
8. End session or continue
```

---

## Example Full Session

Here's a complete example session for Phase 1:

```
> claude

You: Read specs/agent-harness/PLAN.md and specs/agent-harness/PROGRESS.md. 
     What's the current status?

Claude: [Reads files, reports Phase 0 is complete, Phase 1 not started]

You: Let's start Phase 1: Session Manager. Begin with SPEC intake using 
     the prompt from the plan.

Claude: [Runs agentforge intake, uses the Session Manager prompt]

You: Good. Now handle clarifications using the Q&A from the plan.

Claude: [Works through clarify phase]

You: Generate the specification draft.

Claude: [Creates specification]

You: Validate the spec and then start TDFLOW.

Claude: [Validates, starts TDFLOW, generates tests]

You: The tests look good. Implement the Session Manager.

Claude: [Implements tools/harness/session.py]

You: Run all verification - tests, conformance, CI check.

Claude: [Runs verification, shows results]

You: All passing. Update PROGRESS.md, commit the changes, and summarize 
     what we accomplished.

Claude: [Updates progress, commits, provides summary]

You: Great session. We'll continue with Phase 2 next time.
```

---

## Tips for Success

1. **One phase at a time** - Don't rush ahead
2. **Verify often** - Run tests after every change
3. **Update progress** - Keep PROGRESS.md current
4. **Commit frequently** - Small, focused commits
5. **Read existing code** - Follow established patterns
6. **Ask Claude to explain** - If something's unclear, ask before proceeding
7. **Use the plan** - The intake prompts are carefully crafted
