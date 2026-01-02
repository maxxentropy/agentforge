# P0 Tool Handlers Specification

**Version:** 1.1
**Status:** Implemented
**Date:** January 2026

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

### All Handlers (Consolidated in tool_handlers module)

| Handler | Location |
|---------|----------|
| `read_file` | tool_handlers/file_handlers.py |
| `write_file` | tool_handlers/file_handlers.py |
| `edit_file` | tool_handlers/file_handlers.py |
| `complete` | tool_handlers/terminal_handlers.py |
| `escalate` | tool_handlers/terminal_handlers.py |
| `cannot_fix` | tool_handlers/terminal_handlers.py |

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
├── __init__.py           # Exports create_standard_handlers, ToolHandlerRegistry
├── types.py              # ActionHandler type, HandlerContext protocol, validate_path_security
├── constants.py          # Configuration constants (timeouts, limits, etc.)
├── file_handlers.py      # read_file, write_file, edit_file, replace_lines, insert_lines
├── search_handlers.py    # search_code, load_context, find_related
├── verify_handlers.py    # run_check, run_tests, validate_python
└── terminal_handlers.py  # complete, escalate, cannot_fix, request_help, plan_fix
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

### Phase 1: Module Setup ✅ COMPLETE
- [x] Create `tool_handlers/` directory
- [x] Create `__init__.py` with exports
- [x] Create `types.py` with ActionHandler, HandlerContext, validate_path_security
- [x] Create `constants.py` for configuration values
- [x] Move handlers from `native_tool_executor.py` (legacy code quarantined)

### Phase 2: New Handlers ✅ COMPLETE
- [x] `edit_file` handler + tests
- [x] `search_code` handler + tests
- [x] `run_check` handler + tests
- [x] `cannot_fix` handler + tests
- [x] Additional handlers: `replace_lines`, `insert_lines`, `find_related`, `validate_python`

### Phase 3: Integration ✅ COMPLETE
- [x] Update `NativeToolExecutor` to use new module
- [x] Add context injection
- [x] Add audit logging
- [x] Add debug logging to all handlers
- [x] Add path traversal security protection
- [x] Integration tests for context injection

### Phase 4: Validation - IN PROGRESS
- [x] Integration tests for fix_violation workflow (17 tests)
- [ ] End-to-end test with real LLM
- [ ] Documentation

## Test Locations

```
tests/unit/harness/tool_handlers/
├── test_file_handlers.py
├── test_search_handlers.py
├── test_verify_handlers.py
├── test_terminal_handlers.py
├── test_registry.py
└── test_types.py          # Path security validation tests

tests/integration/tool_handlers/
└── test_context_injection.py  # Context injection integration tests

tests/integration/workflows/
├── conftest.py                      # Fixtures: project_with_violation, simulated LLM
└── test_fix_violation_workflow.py   # Full workflow integration tests (17 tests)
```

## Related Documents

- [Implementation Spec](p0-tool-handlers-spec.md) - Detailed implementation specification
- [Tool Handlers YAML](01-tool-handlers.yaml) - Machine-readable specification
- [LLM Integration Spec](../minimal-context-architecture/05-llm-integration.yaml) - Executor integration
- [North Star Spec](../NorthStar/north_star_specification.md) - Overall system architecture

## Success Criteria

1. **Functional**: All P0 handlers work in isolation and integrated ✅
2. **Verified**: `fix_violation` can edit files, verify fixes, escalate if needed ✅
3. **Tested**: 137 tests passing (unit + integration) ✅
4. **Observable**: All executions logged for audit replay ✅

## Test Summary

| Test Suite | Count | Status |
|------------|-------|--------|
| Unit: file_handlers | 22 | ✅ Pass |
| Unit: search_handlers | 17 | ✅ Pass |
| Unit: verify_handlers | 12 | ✅ Pass |
| Unit: terminal_handlers | 19 | ✅ Pass |
| Unit: registry | 29 | ✅ Pass |
| Unit: types | 11 | ✅ Pass |
| Integration: context_injection | 10 | ✅ Pass |
| Integration: workflows | 17 | ✅ Pass |
| **Total** | **137** | ✅ Pass |
