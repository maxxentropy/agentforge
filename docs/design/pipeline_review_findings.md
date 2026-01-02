# Pipeline Controller - Code Review Findings

**Review Date:** January 2, 2026
**Commit:** 3685146
**Status:** Approved for Production
**Tracking:** This document tracks implementation of review recommendations

---

## High Priority

### 1. File Locking for Concurrent Pipeline Access
- **Location:** `src/agentforge/core/pipeline/controller.py:234-264`
- **Issue:** The `approve()`, `reject()`, and `abort()` methods load state, check status, modify, and save without locking. Concurrent CLI calls could corrupt state.
- **Solution:** Add file-based locking in `StateStore` for atomic operations
- **Status:** [x] Fixed - Added `transaction()` context manager to `StateStore`

### 2. Path Traversal Protection in File Handlers
- **Location:** `src/agentforge/core/pipeline/stages/green.py` (file handlers)
- **Issue:** `project_path / user_input` could escape project directory with `../../` paths
- **Solution:** Add `.resolve()` + `is_relative_to()` validation
- **Status:** [x] Fixed - Added `_validate_path()` method with containment check

---

## Medium Priority

### 3. Magic Numbers to Named Constants
- **Location:** `src/agentforge/core/pipeline/stages/green.py:187-188`
- **Issue:** Hard-coded values `20` and `120` for max_iterations and test_timeout
- **Solution:** Define as class constants with descriptive names
- **Status:** [x] Fixed - Added `DEFAULT_MAX_ITERATIONS` and `DEFAULT_TEST_TIMEOUT_SECONDS`

### 4. Type Aliases for Configuration Dicts
- **Location:** Multiple files using `dict[str, Any]` for config
- **Issue:** Inconsistent typing, `Config` type alias would improve clarity
- **Solution:** Create `StageConfigDict` type alias in a shared types module
- **Status:** [x] Fixed - Created `types.py` with `StageConfigDict`, `ArtifactDict`, etc.

### 5. Async State Persistence Option
- **Location:** `src/agentforge/core/pipeline/state_store.py`
- **Issue:** YAML file I/O for every state save could be expensive for rapid iterations
- **Solution:** Consider write batching or async persistence for high-frequency updates
- **Status:** [ ] Deferred (not blocking)

---

## Low Priority

### 6. Duplicate Annotations in __init__.py
- **Location:** `src/agentforge/core/pipeline/__init__.py:1-11`
- **Issue:** Duplicate `@spec_file` and `@spec_id` annotations
- **Solution:** Clean up to single set of annotations
- **Status:** [x] Fixed - Removed duplicate annotations

### 7. Property-Based Tests for State Machine
- **Location:** `tests/unit/pipeline/test_state.py`
- **Issue:** State transitions could benefit from property-based testing
- **Solution:** Add hypothesis-based tests for state machine invariants
- **Status:** [ ] Deferred

### 8. CLI Help Text Improvements
- **Location:** `src/agentforge/cli/click_commands/pipeline.py`
- **Issue:** CLI command options could use more examples
- **Solution:** Add usage examples to help strings
- **Status:** [ ] Deferred

---

## Implementation Notes

### File Locking Pattern
```python
# In StateStore
import fcntl
from contextlib import contextmanager

@contextmanager
def lock(self, pipeline_id: str):
    lock_path = self._get_state_path(pipeline_id).with_suffix('.lock')
    lock_path.touch(exist_ok=True)
    with open(lock_path, 'w') as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
```

### Path Traversal Protection Pattern
```python
def _validate_path(self, path: str, project_path: Path) -> Path:
    """Validate path is within project directory."""
    file_path = (project_path / path).resolve()
    if not file_path.is_relative_to(project_path.resolve()):
        raise ValueError(f"Path escapes project directory: {path}")
    return file_path
```

---

*Last Updated: January 2, 2026*
*Fixes Applied: January 2, 2026 - Issues #1-4, #6 resolved*
