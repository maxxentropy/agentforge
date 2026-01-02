# P0 Tool Handlers Specification

**Version:** 1.0  
**Status:** Draft  
**Date:** January 2025

## Overview

This directory contains specifications for the P0 tool handlers required to make the `fix_violation` workflow functional.

## Quick Reference

### Handlers to Implement

| Handler | Purpose | Priority | Status |
|---------|---------|----------|--------|
| `edit_file` | Replace specific lines in a file | P0 | ✅ Implemented |
| `run_check` | Re-run conformance check to verify fix | P0 | ✅ Implemented |
| `search_code` | Find related code (regex + semantic) | P0 | ✅ Implemented |
| `cannot_fix` | Escalate unfixable issues | P0 | ✅ Implemented |
| `load_context` | Load additional file context | P1 | ✅ Implemented |
| `run_tests` | Execute tests to verify changes | P1 | ✅ Implemented |

### Existing Handlers (Already Implemented)

| Handler | Location |
|---------|----------|
| `read_file` | native_tool_executor.py |
| `write_file` | native_tool_executor.py |
| `complete` | native_tool_executor.py |
| `escalate` | native_tool_executor.py |

## Specification Files

| File | Description |
|------|-------------|
| [01-file-handlers.yaml](01-file-handlers.yaml) | `edit_file`, `read_file`, `write_file` specs |
| [02-search-handlers.yaml](02-search-handlers.yaml) | `search_code`, `load_context` specs |
| [03-verify-handlers.yaml](03-verify-handlers.yaml) | `run_check`, `run_tests` specs |
| [04-terminal-handlers.yaml](04-terminal-handlers.yaml) | `complete`, `escalate`, `cannot_fix` specs |
| [05-integration.yaml](05-integration.yaml) | Module structure and executor integration |

## Module Structure

```
src/agentforge/core/harness/minimal_context/tool_handlers/
├── __init__.py           # Exports create_standard_handlers
├── types.py              # ActionHandler type, HandlerContext protocol
├── file_handlers.py      # read_file, write_file, edit_file
├── search_handlers.py    # search_code, load_context
├── verify_handlers.py    # run_check, run_tests
└── terminal_handlers.py  # complete, escalate, cannot_fix
```

## Handler Signature

All handlers follow the same pattern:

```python
def create_xyz_handler(project_path: Path = None) -> ActionHandler:
    """
    Create an xyz action handler.
    
    Args:
        project_path: Base path for operations
        
    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    def handler(params: Dict[str, Any]) -> str:
        # Access context via params["_context"]
        # Perform action
        # Return result string (SUCCESS or ERROR)
        ...
    
    return handler
```

## Key Design Decisions

### 1. Return Strings, Not Exceptions

Handlers return result strings that the LLM can understand:
- Success: `"SUCCESS: Edited module.py\n  Lines 10-15 replaced"`
- Error: `"ERROR: File not found: module.py"`

The LLM sees errors and can potentially recover (e.g., search for correct path).

### 2. Context Injection

Executor injects task context via `params["_context"]`:
```python
params["_context"] = {
    "violation_id": "V-001",
    "task_id": "T-123",
    "files_examined": ["src/a.py", "src/b.py"],
    ...
}
```

### 3. Wrap Existing Infrastructure

| Handler | Wraps |
|---------|-------|
| `run_check` | `ConformanceManager` + `VerificationRunner` |
| `search_code` | `VectorSearch` (semantic) + regex |
| `run_tests` | `TDFlow` test runners |
| `cannot_fix` | `EscalationManager` |

### 4. Audit Everything

All tool executions logged with:
- Tool name, parameters, result
- Execution time
- Success/failure status

## Implementation Checklist

### Phase 1: Module Setup (0.5 day) ✅ COMPLETE
- [x] Create `tool_handlers/` directory
- [x] Create `__init__.py` with exports
- [x] Create `types.py`
- [x] Move existing handlers from `native_tool_executor.py`

### Phase 2: New Handlers (3 days) ✅ COMPLETE
- [x] `edit_file` handler + tests
- [x] `search_code` handler + tests
- [x] `run_check` handler + tests
- [x] `cannot_fix` handler + tests

### Phase 3: Integration (1 day) ✅ COMPLETE
- [x] Update `NativeToolExecutor` to use new module
- [x] Add context injection
- [x] Add audit logging
- [x] Integration tests

### Phase 4: Validation (1 day) - PENDING
- [ ] End-to-end test with real violation
- [ ] Documentation

## Test Locations

```
tests/unit/harness/tool_handlers/
├── test_file_handlers.py
├── test_search_handlers.py
├── test_verify_handlers.py
└── test_terminal_handlers.py

tests/integration/tool_handlers/
├── test_handler_integration.py
└── test_fix_violation_workflow.py
```

## Related Documents

- [Markdown Spec](/home/claude/agentforge/specs/minimal-context-architecture/implementation/p0-tool-handlers-spec.md) - Detailed implementation specification
- [North Star Gap Analysis](/home/claude/agentforge/docs/analysis/northstar-gap-analysis.md) - Overall gap analysis
- [Minimal Context V2 Review](/home/claude/agentforge/docs/reviews/minimal-context-v2-code-review.md) - Code review of executor

## Success Criteria

1. **Functional**: All P0 handlers work in isolation and integrated
2. **Verified**: `fix_violation` can edit files, verify fixes, escalate if needed
3. **Tested**: 90%+ unit test coverage for handlers
4. **Observable**: All executions logged for audit replay
