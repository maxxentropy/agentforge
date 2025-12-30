# Implementation Task: Contract System Improvements

## Overview

Implement the contract system improvements defined in `docs/design/CONTRACT_SYSTEM_IMPROVEMENTS.md`. This task covers three major areas:

1. Replace regex-based architecture checks with AST-based semantic analysis
2. Create new builtin check functions for layer enforcement
3. Update contract files with proper defaults

**Read the full design document first:** `docs/design/CONTRACT_SYSTEM_IMPROVEMENTS.md`

---

## Phase 1: New Builtin Check Functions

### Task 1.1: Add `check_layer_imports` to `tools/builtin_checks.py`

Create a function that detects Clean Architecture layer violations using AST import analysis.

**Signature:**
```python
def check_layer_imports(
    repo_root: Path,
    file_paths: List[Path],
    layer_detection: Dict[str, str],
    layer_rules: Dict[str, Dict]
) -> List[Dict]:
```

**Requirements:**
- Parse Python files using `ast` module
- Detect layer from file path using `layer_detection` patterns
- Extract all imports (both `import x` and `from x import y`)
- Map imported modules to their layers
- Check against `layer_rules` for violations
- Return violations with file, line, message, and fix_hint

**Test cases to handle:**
```python
# Should detect: domain importing from infrastructure
# File: domain/order.py
from infrastructure.db import Database  # VIOLATION

# Should detect: qualified imports
import myapp.infrastructure.repositories  # VIOLATION

# Should NOT flag: allowed imports
from domain.entities import Order  # OK in application layer

# Should NOT flag: stdlib imports
import json  # OK everywhere
```

### Task 1.2: Add `check_constructor_injection` to `tools/builtin_checks.py`

Create a function that verifies service classes use constructor injection.

**Signature:**
```python
def check_constructor_injection(
    repo_root: Path,
    file_paths: List[Path],
    class_patterns: List[str],
    forbidden_instantiations: List[str],
    check_for_init_params: bool = True
) -> List[Dict]:
```

**Requirements:**
- Find classes matching `class_patterns` (e.g., `*Service`, `*Handler`)
- Check that `__init__` has parameters (besides `self`)
- Detect direct instantiation of forbidden types in `__init__`
- Return violations with class name, line, and fix hint

### Task 1.3: Add `check_domain_purity` to `tools/builtin_checks.py`

Create a function that ensures domain layer contains no I/O operations.

**Signature:**
```python
def check_domain_purity(
    repo_root: Path,
    file_paths: List[Path],
    forbidden_imports: List[str],
    forbidden_calls: List[str]
) -> List[Dict]:
```

**Requirements:**
- Detect imports of I/O libraries (requests, sqlite3, etc.)
- Detect calls to I/O functions (open, Path.read, subprocess, etc.)
- Return violations with specific import/call identified

### Task 1.4: Add `check_circular_imports` to `tools/builtin_checks.py`

Create a function that detects circular import dependencies.

**Signature:**
```python
def check_circular_imports(
    repo_root: Path,
    file_paths: List[Path],
    ignore_type_checking: bool = True,
    max_depth: int = 5
) -> List[Dict]:
```

**Requirements:**
- Build import graph from all files
- Detect cycles in the graph
- Optionally ignore imports inside `if TYPE_CHECKING:` blocks
- Return the cycle path in the violation message

### Task 1.5: Update `BUILTIN_CHECKS` Registry

Add all new functions to the registry at the bottom of `builtin_checks.py`:

```python
BUILTIN_CHECKS = {
    # Existing checks...
    
    # New architecture checks
    "layer_imports": check_layer_imports,
    "constructor_injection": check_constructor_injection,
    "domain_purity": check_domain_purity,
    "circular_imports": check_circular_imports,
}
```

---

## Phase 2: Update Architecture Contract

### Task 2.1: Replace `contracts/builtin/_architecture-python.contract.yaml`

Replace the existing regex-based checks with the new custom checks.

**Key changes:**
- Remove regex checks for `domain-no-infrastructure`, `domain-no-application`, etc.
- Add `layer-dependency-violations` check using `check_layer_imports`
- Add `constructor-injection-required` check
- Add `domain-purity` check
- Add `no-circular-imports` check

**Use the YAML structure from the design document**, specifically the section titled "Revised Architecture Contract".

Ensure:
- All checks have proper `applies_to` paths
- Exclude paths include `**/tests/**`
- Fix hints are actionable
- Severity levels are appropriate (error for layer violations, warning for DI)

---

## Phase 3: Update AgentForge Contract

### Task 3.1: Revise `contracts/agentforge.contract.yaml`

Update to enable meaningful defaults per the design document.

**Tier 1 - Enable as Errors:**
- `layer-dependency-violations`
- `domain-purity`
- `no-secrets-in-code`
- `no-private-keys`
- `no-env-files`
- `yaml-safe-load`

**Tier 2 - Enable as Warnings:**
- `max-cyclomatic-complexity` (threshold: 10)
- `max-function-length` (threshold: 50)
- `max-nesting-depth` (threshold: 4)
- `max-parameter-count` (threshold: 5)
- `max-class-size` (threshold: 20)
- `no-bare-except`
- `no-star-imports`
- `no-breakpoint`
- `no-pdb-import`
- `constructor-injection-required`
- `max-file-lines` (threshold: 500)

**Tier 3 - Keep Disabled (tool-dependent):**
- `ruff-lint`
- `ruff-format`
- `mypy-standard`
- `pytest-pass`
- `bandit-scan`

**Overrides (disabled for this project):**
- `no-print-statements` - CLI tool uses print
- `require-init-files` - non-standard layout
- `require-main-entry` - uses execute.py

---

## Phase 4: Unit Tests

### Task 4.1: Create `tests/unit/tools/test_builtin_checks_architecture.py`

Write comprehensive tests for the new check functions.

**Test categories:**

1. **`check_layer_imports` tests:**
   - Test domain importing infrastructure (should fail)
   - Test domain importing application (should fail)
   - Test application importing domain (should pass)
   - Test stdlib imports (should pass)
   - Test relative imports within same layer (should pass)
   - Test `from x import y` form
   - Test `import x.y.z` form

2. **`check_constructor_injection` tests:**
   - Test service class with no __init__ params (should fail)
   - Test service class with injected dependencies (should pass)
   - Test direct instantiation in __init__ (should fail)
   - Test non-service class (should be ignored)

3. **`check_domain_purity` tests:**
   - Test importing requests (should fail)
   - Test calling open() (should fail)
   - Test pure business logic (should pass)

4. **`check_circular_imports` tests:**
   - Test A→B→A cycle (should fail)
   - Test A→B→C→A cycle (should fail)
   - Test TYPE_CHECKING imports with ignore flag (should pass)
   - Test no cycles (should pass)

**Test file structure:**
```python
"""Tests for architecture-related builtin checks."""

import pytest
from pathlib import Path
from textwrap import dedent
from tools.builtin_checks import (
    check_layer_imports,
    check_constructor_injection,
    check_domain_purity,
    check_circular_imports,
)


class TestCheckLayerImports:
    """Tests for layer import violation detection."""
    
    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project structure."""
        # Create domain/, application/, infrastructure/ directories
        # with sample Python files
        ...
    
    def test_domain_importing_infrastructure_fails(self, temp_project: Path) -> None:
        ...
```

---

## Acceptance Criteria

### Functional Requirements

- [ ] `check_layer_imports` correctly identifies layer violations
- [ ] `check_layer_imports` does not flag stdlib or third-party imports
- [ ] `check_constructor_injection` identifies classes without DI
- [ ] `check_domain_purity` catches I/O in domain layer
- [ ] `check_circular_imports` detects import cycles
- [ ] Architecture contract uses new checks instead of regex
- [ ] AgentForge contract has proper defaults enabled
- [ ] All new checks are in `BUILTIN_CHECKS` registry

### Quality Requirements

- [ ] All new functions have type hints
- [ ] All new functions have docstrings with Args/Returns
- [ ] Unit tests cover happy path and edge cases
- [ ] No regressions in existing functionality

### Verification

After implementation, run:
```bash
# Run the new unit tests
python -m pytest tests/unit/tools/test_builtin_checks_architecture.py -v

# Run verification on the AgentForge repo itself
python -m tools.verification_runner --repo-root . --contract contracts/agentforge.contract.yaml

# Check that the contract loads without errors
python -c "from tools.contracts_registry import ContractRegistry; r = ContractRegistry('.'); print(r.load_contract('agentforge'))"
```

---

## Implementation Notes

### Pattern: Custom Check Function Signature

All custom check functions must follow this signature:

```python
def check_name(
    repo_root: Path,
    file_paths: List[Path],
    **params  # Additional parameters from contract config
) -> List[Dict]:
    """
    Description of what the check does.
    
    Args:
        repo_root: Root path of the repository
        file_paths: List of files to check (already filtered by applies_to)
        **params: Additional parameters from contract config.params
    
    Returns:
        List of violation dictionaries with keys:
        - message: str (required)
        - file: str (relative path, required)
        - line: int (optional)
        - severity: str (optional, overrides check severity)
        - fix_hint: str (optional)
    """
```

### Pattern: AST Import Extraction

```python
import ast

def extract_imports(source: str) -> List[Tuple[str, int]]:
    """Extract all imports from source with line numbers."""
    tree = ast.parse(source)
    imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno))
    
    return imports
```

### Pattern: Glob-based Layer Detection

```python
import fnmatch

def get_layer_for_file(file_path: Path, layer_detection: Dict[str, str]) -> Optional[str]:
    """Determine which layer a file belongs to."""
    rel_path = str(file_path)
    for pattern, layer in layer_detection.items():
        if fnmatch.fnmatch(rel_path, pattern):
            return layer
    return None
```

---

## Files to Modify/Create

| File | Action |
|------|--------|
| `tools/builtin_checks.py` | ADD new check functions |
| `contracts/builtin/_architecture-python.contract.yaml` | REPLACE with new version |
| `contracts/agentforge.contract.yaml` | UPDATE with proper defaults |
| `tests/unit/tools/test_builtin_checks_architecture.py` | CREATE new test file |

---

## Questions to Resolve During Implementation

1. **Layer mapping for imports:** How to map `from tools.workspace import X` to the "tools" layer? Need heuristic based on project structure.

2. **Third-party detection:** Should we use a list of known third-party packages, or detect based on not being in repo? Suggest: if import path doesn't exist in repo, treat as external.

3. **Transitive violations:** Should Phase 1 include transitive detection (A imports B, B imports infrastructure, so A transitively violates)? Suggest: defer to Phase 2, keep initial implementation simple.

---

## Reference: Existing Code Patterns

Look at these files for patterns to follow:
- `tools/builtin_checks.py` - existing check function patterns
- `tools/verification_ast.py` - AST analysis patterns
- `tests/unit/tools/test_verification_checks.py` - test patterns
- `contracts/builtin/_patterns-python.contract.yaml` - contract structure

Good luck! Read the design document thoroughly before starting.