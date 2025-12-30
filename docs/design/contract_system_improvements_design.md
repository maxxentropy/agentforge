# Contract System Improvements Design Document

**Version:** 1.0  
**Date:** 2025-12-30  
**Status:** DRAFT - Ready for Review

---

## Executive Summary

This document proposes three major improvements to AgentForge's contract system:

1. **Replace regex-based architecture checks with LSP-based semantic analysis** - Current layer violation checks use regex patterns that miss edge cases and produce false positives
2. **Introduce "Generative Patterns" contracts** - Define what new code SHOULD look like, not just what existing code must pass
3. **Enable meaningful default checks** - The current `agentforge.contract.yaml` disables most checks, defeating the tool's purpose

---

## Part 1: LSP-Based Architecture Contract

### Problem Statement

The current `_architecture-python.contract.yaml` uses regex patterns for layer dependency checks:

```yaml
# Current: Regex-based (PROBLEMATIC)
- id: domain-no-infrastructure
  type: regex
  config:
    pattern: "from\\s+(\\w+\\.)?infrastructure(\\.|\\s+import)"
    mode: forbid
```

**Issues with regex approach:**

| Problem | Example | Impact |
|---------|---------|--------|
| False negatives | `import myapp.infrastructure.db` | Violating code passes |
| False positives | `doc = "imports infrastructure"` | Valid code flagged |
| No semantic understanding | Aliased imports | Violations slip through |
| No transitive detection | A→B→Infrastructure | Hidden violations |

### Proposed Solution

Replace regex checks with LSP-based import analysis using a new custom check that leverages the AST and LSP infrastructure.

#### New Check Type: `import_analysis`

Add a new custom check function in `builtin_checks.py`:

```python
def check_layer_imports(
    repo_root: Path, 
    file_paths: List[Path],
    layer_rules: Dict[str, List[str]],
    layer_detection: Dict[str, str]
) -> List[Dict]:
    """
    Check for layer boundary violations using AST import analysis.
    
    Args:
        layer_rules: Maps layer names to forbidden import targets
                     {"domain": ["infrastructure", "application", "presentation"]}
        layer_detection: Maps path patterns to layer names
                        {"**/domain/**": "domain", "**/infrastructure/**": "infrastructure"}
    
    Returns:
        List of violations with file, line, imported module, and violated rule
    """
```

#### Revised Architecture Contract

```yaml
# File: contracts/builtin/_architecture-python.contract.yaml
schema_version: "1.0"

contract:
  name: "_architecture-python"
  type: architecture
  description: |
    Python Clean Architecture enforcement using semantic analysis.
    Detects layer violations through AST-based import inspection.
  version: "2.0.0"
  enabled: true
  extends: "_patterns-python"
  applies_to:
    languages:
      - python
    repo_types:
      - service
      - api
  tags:
    - builtin
    - python
    - architecture
    - clean-architecture

checks:
  # ===========================================================================
  # Clean Architecture Layer Enforcement (Semantic Analysis)
  # ===========================================================================

  - id: layer-dependency-violations
    name: "Clean Architecture Layer Violations"
    description: |
      Enforces dependency direction in Clean Architecture:
      - Domain layer: No dependencies on other layers
      - Application layer: May depend on Domain only
      - Infrastructure layer: May depend on Domain and Application
      - Presentation layer: May depend on Application only
    type: custom
    severity: error
    config:
      module: builtin_checks
      function: check_layer_imports
      params:
        layer_detection:
          "**/domain/**": "domain"
          "**/core/**": "domain"
          "**/entities/**": "domain"
          "**/application/**": "application"
          "**/use_cases/**": "application"
          "**/services/**": "application"
          "**/infrastructure/**": "infrastructure"
          "**/adapters/**": "infrastructure"
          "**/repositories/**": "infrastructure"
          "**/presentation/**": "presentation"
          "**/api/**": "presentation"
          "**/cli/**": "presentation"
          "**/web/**": "presentation"
        layer_rules:
          domain:
            forbidden:
              - infrastructure
              - application
              - presentation
              - adapters
              - repositories
              - api
              - cli
              - web
            message: "Domain layer must have no external dependencies"
          application:
            forbidden:
              - infrastructure
              - presentation
              - adapters
              - repositories
              - api
              - cli
              - web
            allowed:
              - domain
              - core
              - entities
            message: "Application layer may only depend on Domain"
          infrastructure:
            forbidden:
              - presentation
              - api
              - cli
              - web
            allowed:
              - domain
              - application
              - core
              - entities
            message: "Infrastructure may depend on Domain and Application"
    applies_to:
      paths:
        - "**/*.py"
      exclude_paths:
        - "**/tests/**"
        - "**/__init__.py"
        - "**/conftest.py"
    fix_hint: |
      Move the import to the appropriate layer or use dependency injection.
      Domain should never import from infrastructure - inject interfaces instead.

  # ===========================================================================
  # Dependency Injection Pattern Detection
  # ===========================================================================

  - id: constructor-injection-required
    name: "Constructor Injection Required"
    description: |
      Service classes should receive dependencies through constructor injection,
      not instantiate them directly.
    type: custom
    severity: warning
    config:
      module: builtin_checks
      function: check_constructor_injection
      params:
        class_patterns:
          - "*Service"
          - "*Repository"
          - "*Handler"
          - "*UseCase"
        forbidden_instantiations:
          - "HttpClient("
          - "SqlConnection("
          - "requests.Session("
          - "aiohttp.ClientSession("
        check_for_init_params: true
    applies_to:
      paths:
        - "**/application/**/*.py"
        - "**/services/**/*.py"
        - "**/use_cases/**/*.py"
      exclude_paths:
        - "**/tests/**"
    fix_hint: "Inject dependencies through __init__ parameters instead of instantiating directly"

  # ===========================================================================
  # Interface Segregation (Protocol Usage)
  # ===========================================================================

  - id: protocol-based-abstractions
    name: "Use Protocol for Abstractions"
    description: |
      Abstract dependencies should use typing.Protocol for interface definitions,
      enabling structural typing and easier testing.
    type: lsp_query
    severity: info
    config:
      query: symbols
      filter:
        kind: class
        name_pattern: "^I[A-Z].*"  # Classes starting with I (interface convention)
      assertion: all_exist
    applies_to:
      paths:
        - "**/domain/**/*.py"
        - "**/application/interfaces/**/*.py"
    fix_hint: "Define interfaces using typing.Protocol for better type safety"

  # ===========================================================================
  # No Direct Infrastructure Access in Domain
  # ===========================================================================

  - id: domain-purity
    name: "Domain Layer Purity"
    description: |
      Domain layer should contain only pure business logic - no I/O operations,
      HTTP calls, database access, or filesystem operations.
    type: custom
    severity: error
    config:
      module: builtin_checks
      function: check_domain_purity
      params:
        forbidden_imports:
          - requests
          - httpx
          - aiohttp
          - urllib
          - sqlite3
          - psycopg2
          - pymongo
          - redis
          - sqlalchemy
          - django.db
          - flask_sqlalchemy
        forbidden_calls:
          - "open("
          - "Path.read"
          - "Path.write"
          - "os.path"
          - "shutil."
          - "subprocess."
    applies_to:
      paths:
        - "**/domain/**/*.py"
        - "**/core/**/*.py"
        - "**/entities/**/*.py"
      exclude_paths:
        - "**/tests/**"
    fix_hint: "Move I/O operations to infrastructure layer; domain should be pure business logic"

  # ===========================================================================
  # Circular Import Prevention
  # ===========================================================================

  - id: no-circular-imports
    name: "No Circular Imports"
    description: "Modules should not have circular import dependencies"
    type: custom
    severity: error
    config:
      module: builtin_checks
      function: check_circular_imports
      params:
        ignore_type_checking: true  # Allow TYPE_CHECKING imports
        max_depth: 5
    applies_to:
      paths:
        - "**/*.py"
      exclude_paths:
        - "**/tests/**"
    fix_hint: |
      Break circular imports by:
      1. Moving shared types to a separate module
      2. Using TYPE_CHECKING guards for type hints
      3. Restructuring dependencies to flow in one direction
```

### Implementation Requirements

The following new functions need to be added to `builtin_checks.py`:

#### 1. `check_layer_imports`

```python
def check_layer_imports(
    repo_root: Path,
    file_paths: List[Path],
    layer_detection: Dict[str, str],
    layer_rules: Dict[str, Dict]
) -> List[Dict]:
    """
    Detect layer boundary violations using AST import analysis.
    
    Algorithm:
    1. For each file, determine its layer based on layer_detection patterns
    2. Parse imports using AST
    3. Resolve import targets to their layers
    4. Check against layer_rules for violations
    """
    import ast
    import fnmatch
    
    violations = []
    
    def get_layer(file_path: Path) -> Optional[str]:
        rel_path = str(file_path.relative_to(repo_root))
        for pattern, layer in layer_detection.items():
            if fnmatch.fnmatch(rel_path, pattern):
                return layer
        return None
    
    def get_import_layer(import_name: str) -> Optional[str]:
        # Map import name to layer based on path patterns
        for pattern, layer in layer_detection.items():
            # Convert glob to import path pattern
            import_pattern = pattern.replace("**/", "").replace("/**", "").replace("/", ".")
            if import_pattern.rstrip(".*") in import_name:
                return layer
        return None
    
    for file_path in file_paths:
        source_layer = get_layer(file_path)
        if not source_layer or source_layer not in layer_rules:
            continue
            
        rules = layer_rules[source_layer]
        forbidden = set(rules.get("forbidden", []))
        
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, IOError):
            continue
        
        for node in ast.walk(tree):
            import_names = []
            
            if isinstance(node, ast.Import):
                import_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_names = [node.module]
            
            for import_name in import_names:
                target_layer = get_import_layer(import_name)
                if target_layer and target_layer in forbidden:
                    violations.append({
                        "message": f"{source_layer} layer imports from {target_layer}: {import_name}",
                        "file": str(file_path.relative_to(repo_root)),
                        "line": node.lineno,
                        "severity": "error",
                        "fix_hint": rules.get("message", "Fix layer dependency violation")
                    })
    
    return violations
```

#### 2. `check_constructor_injection`

```python
def check_constructor_injection(
    repo_root: Path,
    file_paths: List[Path],
    class_patterns: List[str],
    forbidden_instantiations: List[str],
    check_for_init_params: bool = True
) -> List[Dict]:
    """
    Verify that service classes use constructor injection.
    
    Checks:
    1. Classes matching patterns have __init__ with parameters
    2. No direct instantiation of infrastructure types
    """
    import ast
    import fnmatch
    
    violations = []
    
    for file_path in file_paths:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, IOError):
            continue
        
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            
            # Check if class matches any pattern
            matches_pattern = any(
                fnmatch.fnmatch(node.name, pattern) 
                for pattern in class_patterns
            )
            
            if not matches_pattern:
                continue
            
            # Find __init__ method
            init_method = None
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    init_method = item
                    break
            
            # Check for init parameters (excluding self)
            if check_for_init_params and init_method:
                params = [
                    arg.arg for arg in init_method.args.args 
                    if arg.arg != "self"
                ]
                if not params:
                    violations.append({
                        "message": f"Class '{node.name}' has no injected dependencies",
                        "file": str(file_path.relative_to(repo_root)),
                        "line": node.lineno,
                        "severity": "warning",
                        "fix_hint": "Add dependencies as __init__ parameters"
                    })
            
            # Check for forbidden instantiations in __init__
            if init_method:
                for child in ast.walk(init_method):
                    if isinstance(child, ast.Call):
                        call_str = ast.unparse(child.func) if hasattr(ast, 'unparse') else ""
                        for forbidden in forbidden_instantiations:
                            if forbidden.rstrip("(") in call_str:
                                violations.append({
                                    "message": f"Direct instantiation of '{forbidden}' in {node.name}",
                                    "file": str(file_path.relative_to(repo_root)),
                                    "line": child.lineno,
                                    "severity": "warning",
                                    "fix_hint": "Inject this dependency through constructor"
                                })
    
    return violations
```

---

## Part 2: Generative Patterns Contract

### Problem Statement

Current contracts are **validation-focused**: they check if existing code passes certain rules. This leads to:

1. Rules disabled where code doesn't comply
2. Thresholds set to pass existing code
3. No guidance for generating NEW code

We need **generative contracts** that define what new code SHOULD look like - patterns that Claude Code should follow when generating code.

### Design: Generative Contract Schema Extension

Add a new contract type `generative` with template-based pattern definitions:

```yaml
schema_version: "1.0"

contract:
  name: "_generative-python"
  type: generative
  description: |
    Defines patterns for generating new Python code.
    These patterns guide code generation, not just validation.
  version: "1.0.0"
  applies_to:
    languages:
      - python

# =============================================================================
# GENERATIVE PATTERNS - What new code should look like
# =============================================================================

patterns:
  # ---------------------------------------------------------------------------
  # Class Patterns
  # ---------------------------------------------------------------------------
  
  - id: service-class
    name: "Service Class Pattern"
    description: "Pattern for application service classes"
    trigger:
      when: "creating a class that orchestrates business logic"
      indicators:
        - "service"
        - "use case"
        - "handler"
        - "orchestrator"
    template: |
      from typing import Protocol
      from dataclasses import dataclass
      
      # Define result type for explicit error handling
      @dataclass(frozen=True)
      class {ClassName}Result:
          success: bool
          data: {ResultType} | None = None
          error: str | None = None
      
      class {ClassName}:
          """
          {description}
          
          Responsibilities:
              - {responsibility_1}
              - {responsibility_2}
          """
          
          def __init__(
              self,
              {dependency_1}: {DependencyType1},
              {dependency_2}: {DependencyType2},
          ) -> None:
              self._{dependency_1} = {dependency_1}
              self._{dependency_2} = {dependency_2}
          
          def execute(self, {params}) -> {ClassName}Result:
              """Execute the service operation."""
              try:
                  # Business logic here
                  result = self._do_work({params})
                  return {ClassName}Result(success=True, data=result)
              except Exception as e:
                  return {ClassName}Result(success=False, error=str(e))
          
          def _do_work(self, {params}) -> {ResultType}:
              """Internal implementation."""
              pass
    rules:
      - "Dependencies injected through constructor"
      - "Result type for explicit success/failure"
      - "Single public method (execute/run/handle)"
      - "Private methods for implementation details"
      - "Type hints on all parameters and returns"
    
  - id: repository-interface
    name: "Repository Interface Pattern"
    description: "Pattern for data access abstraction"
    trigger:
      when: "defining data access interface"
      indicators:
        - "repository"
        - "data access"
        - "persistence"
    template: |
      from typing import Protocol, TypeVar, Generic, Optional, List
      from abc import abstractmethod
      
      T = TypeVar("T")
      TId = TypeVar("TId")
      
      class Repository(Protocol[T, TId]):
          """
          Repository interface for {EntityName} persistence.
          
          Implement this protocol in infrastructure layer.
          """
          
          @abstractmethod
          def get_by_id(self, id: TId) -> Optional[T]:
              """Retrieve entity by identifier."""
              ...
          
          @abstractmethod
          def get_all(self) -> List[T]:
              """Retrieve all entities."""
              ...
          
          @abstractmethod
          def add(self, entity: T) -> T:
              """Add new entity, returning with generated ID."""
              ...
          
          @abstractmethod
          def update(self, entity: T) -> T:
              """Update existing entity."""
              ...
          
          @abstractmethod
          def delete(self, id: TId) -> bool:
              """Delete entity by ID, returns success status."""
              ...
    rules:
      - "Use typing.Protocol for structural typing"
      - "Generic type parameters for entity and ID types"
      - "All methods have return type hints"
      - "Abstract methods only - no implementation"
      - "Place in domain/application layer"

  - id: domain-entity
    name: "Domain Entity Pattern"
    description: "Pattern for domain entities with encapsulation"
    trigger:
      when: "creating a domain entity or aggregate"
      indicators:
        - "entity"
        - "aggregate"
        - "domain object"
    template: |
      from dataclasses import dataclass, field
      from typing import Optional, List
      from datetime import datetime
      
      @dataclass
      class {EntityName}:
          """
          {description}
          
          Invariants:
              - {invariant_1}
              - {invariant_2}
          """
          
          # Identity
          id: Optional[{IdType}] = None
          
          # Required attributes
          {required_attr}: {AttrType}
          
          # Optional attributes with defaults
          {optional_attr}: {OptionalType} = None
          
          # Collections
          {collection_attr}: List[{ItemType}] = field(default_factory=list)
          
          # Audit fields
          created_at: datetime = field(default_factory=datetime.utcnow)
          updated_at: Optional[datetime] = None
          
          def __post_init__(self) -> None:
              """Validate invariants after initialization."""
              self._validate()
          
          def _validate(self) -> None:
              """Enforce domain invariants."""
              if not self.{required_attr}:
                  raise ValueError("{required_attr} is required")
          
          # Domain behavior methods
          def {behavior_method}(self, {params}) -> None:
              """
              {behavior_description}
              
              Raises:
                  ValueError: If {error_condition}
              """
              self._validate_can_{behavior}()
              # Behavior implementation
              self.updated_at = datetime.utcnow()
          
          def _validate_can_{behavior}(self) -> None:
              """Check preconditions for {behavior}."""
              pass
    rules:
      - "Use dataclass for value semantics"
      - "Validate invariants in __post_init__"
      - "Encapsulate behavior in methods"
      - "No infrastructure dependencies"
      - "Immutable where possible (frozen=True for value objects)"

  # ---------------------------------------------------------------------------
  # Function Patterns
  # ---------------------------------------------------------------------------
  
  - id: result-returning-function
    name: "Result-Returning Function Pattern"
    description: "Functions that can fail should return Result types"
    trigger:
      when: "function can fail in expected ways"
      indicators:
        - "may fail"
        - "validation"
        - "external call"
        - "parsing"
    template: |
      from typing import TypeVar, Generic
      from dataclasses import dataclass
      
      T = TypeVar("T")
      E = TypeVar("E")
      
      @dataclass(frozen=True)
      class Result(Generic[T, E]):
          """Explicit success/failure result."""
          _value: T | None = None
          _error: E | None = None
          
          @property
          def is_success(self) -> bool:
              return self._error is None
          
          @property
          def value(self) -> T:
              if self._error is not None:
                  raise ValueError(f"Cannot get value from failed result: {self._error}")
              return self._value  # type: ignore
          
          @property
          def error(self) -> E:
              if self._error is None:
                  raise ValueError("Cannot get error from successful result")
              return self._error
          
          @classmethod
          def success(cls, value: T) -> "Result[T, E]":
              return cls(_value=value)
          
          @classmethod
          def failure(cls, error: E) -> "Result[T, E]":
              return cls(_error=error)
      
      
      def {function_name}({params}) -> Result[{SuccessType}, {ErrorType}]:
          """
          {description}
          
          Returns:
              Result with {SuccessType} on success, {ErrorType} on failure.
          """
          try:
              # Implementation
              result = {implementation}
              return Result.success(result)
          except {ExpectedException} as e:
              return Result.failure({ErrorType}(str(e)))
    rules:
      - "Return Result type instead of raising exceptions for expected failures"
      - "Exceptions only for unexpected/programmer errors"
      - "Caller must handle both success and failure cases"
      - "Type hints make failure modes explicit"

  # ---------------------------------------------------------------------------
  # Module Patterns  
  # ---------------------------------------------------------------------------
  
  - id: module-structure
    name: "Module Structure Pattern"
    description: "Standard module organization"
    trigger:
      when: "creating a new Python module"
    template: |
      """
      {module_name} - {brief_description}
      
      This module provides:
          - {capability_1}
          - {capability_2}
      
      Example:
          >>> from {package}.{module_name} import {MainClass}
          >>> obj = {MainClass}()
          >>> obj.{method}()
      """
      
      # Standard library imports (alphabetized)
      from dataclasses import dataclass
      from typing import TYPE_CHECKING, List, Optional
      
      # Third-party imports (alphabetized)
      
      # Local imports (relative, alphabetized)
      from .{sibling_module} import {SiblingClass}
      
      # Type-only imports to avoid circular dependencies
      if TYPE_CHECKING:
          from .{type_only_module} import {TypeOnlyClass}
      
      # Module-level constants
      DEFAULT_{CONSTANT} = {value}
      
      # Public API
      __all__ = ["{MainClass}", "{helper_function}"]
      
      
      # Type definitions
      @dataclass(frozen=True)
      class {DataType}:
          """Value object for {purpose}."""
          {field}: {FieldType}
      
      
      # Main classes
      class {MainClass}:
          """
          {class_description}
          """
          pass
      
      
      # Helper functions
      def {helper_function}({params}) -> {ReturnType}:
          """
          {function_description}
          """
          pass
    rules:
      - "Module docstring with description and example"
      - "Imports organized: stdlib, third-party, local"
      - "TYPE_CHECKING for type-only imports"
      - "__all__ defines public API"
      - "Classes before functions"

  # ---------------------------------------------------------------------------
  # Test Patterns
  # ---------------------------------------------------------------------------
  
  - id: unit-test-class
    name: "Unit Test Pattern"
    description: "Pattern for pytest unit tests"
    trigger:
      when: "writing unit tests"
    template: |
      """Tests for {module_name}."""
      
      import pytest
      from unittest.mock import Mock, patch
      
      from {package}.{module_name} import {ClassUnderTest}
      
      
      class Test{ClassUnderTest}:
          """Unit tests for {ClassUnderTest}."""
          
          @pytest.fixture
          def mock_{dependency}(self) -> Mock:
              """Create mock {dependency}."""
              mock = Mock(spec={DependencyType})
              mock.{method}.return_value = {default_return}
              return mock
          
          @pytest.fixture
          def sut(self, mock_{dependency}: Mock) -> {ClassUnderTest}:
              """Create system under test with mocked dependencies."""
              return {ClassUnderTest}({dependency}=mock_{dependency})
          
          # Happy path tests
          
          def test_{method}_returns_expected_result(
              self, 
              sut: {ClassUnderTest}, 
              mock_{dependency}: Mock
          ) -> None:
              """Test that {method} returns expected result when {condition}."""
              # Arrange
              mock_{dependency}.{dep_method}.return_value = {expected_value}
              
              # Act
              result = sut.{method}({params})
              
              # Assert
              assert result.is_success
              assert result.value == {expected}
              mock_{dependency}.{dep_method}.assert_called_once_with({expected_args})
          
          # Edge case tests
          
          def test_{method}_handles_empty_input(self, sut: {ClassUnderTest}) -> None:
              """Test that {method} handles empty input gracefully."""
              result = sut.{method}({empty_input})
              
              assert result.is_success
              assert result.value == {empty_result}
          
          # Error case tests
          
          def test_{method}_returns_failure_when_{error_condition}(
              self,
              sut: {ClassUnderTest},
              mock_{dependency}: Mock
          ) -> None:
              """Test that {method} returns failure when {error_condition}."""
              # Arrange
              mock_{dependency}.{dep_method}.side_effect = {Exception}("{message}")
              
              # Act
              result = sut.{method}({params})
              
              # Assert
              assert not result.is_success
              assert "{expected_error}" in result.error
    rules:
      - "One test class per class under test"
      - "Fixtures for dependencies and SUT"
      - "Arrange-Act-Assert structure"
      - "Descriptive test names: test_{method}_{expected_behavior}_when_{condition}"
      - "Separate happy path, edge cases, and error cases"
      - "Type hints on test methods"

# =============================================================================
# ANTI-PATTERNS - What to avoid
# =============================================================================

anti_patterns:
  - id: god-class
    name: "God Class"
    description: "Class that does too much"
    indicators:
      - "More than 10 public methods"
      - "More than 300 lines"
      - "Dependencies on many unrelated modules"
    remedy: "Split into focused classes with single responsibility"
    
  - id: anemic-domain
    name: "Anemic Domain Model"
    description: "Domain entities with no behavior, just getters/setters"
    indicators:
      - "Entity classes with only data attributes"
      - "Business logic in services instead of entities"
      - "No validation in domain objects"
    remedy: "Move behavior into domain entities; encapsulate invariants"
    
  - id: service-locator
    name: "Service Locator"
    description: "Global registry for dependencies"
    indicators:
      - "Container.resolve()"
      - "ServiceLocator.get()"
      - "Global dependency container"
    remedy: "Use constructor injection; pass dependencies explicitly"
    
  - id: exception-as-flow-control
    name: "Exceptions for Flow Control"
    description: "Using exceptions for expected failure cases"
    indicators:
      - "try/except around validation"
      - "Raising exceptions for user input errors"
      - "Catching broad Exception types"
    remedy: "Use Result types for expected failures; exceptions for unexpected errors"
```

### Integration with Code Generation

These patterns should be:

1. **Referenced in SPEC workflow prompts** - When generating code, include relevant patterns
2. **Validated post-generation** - After code is generated, validate it matches the pattern
3. **Searchable in context retrieval** - When building context, include matching patterns

---

## Part 3: Default Enabled Checks

### Problem Statement

The current `agentforge.contract.yaml` disables almost every inherited check:

```yaml
# Current state - defeats the purpose
- id: ruff-lint
  enabled: false  # Enable when ruff is installed

- id: mypy-strict
  enabled: false  # Enable when mypy is installed

- id: require-tests-directory
  enabled: false  # Enable when tests are added
```

### Proposed Default Configuration

#### Tier 1: Always Enabled (Errors)

These checks should ALWAYS run and fail the build if violated:

| Check ID | Type | Rationale |
|----------|------|-----------|
| `layer-dependency-violations` | custom | Core architecture enforcement |
| `domain-purity` | custom | Prevents infrastructure leakage |
| `no-hardcoded-secrets` | regex | Security - no secrets in code |
| `no-private-keys` | file_exists | Security - no keys committed |
| `yaml-safe-load` | regex | Security - YAML injection prevention |
| `contract-schema-version` | regex | Contract integrity |

#### Tier 2: Enabled by Default (Warnings)

These should run and warn, but not fail:

| Check ID | Type | Rationale |
|----------|------|-----------|
| `max-cyclomatic-complexity` | ast_check | Code quality |
| `max-function-length` | ast_check | Code quality |
| `max-nesting-depth` | ast_check | Readability |
| `max-parameter-count` | ast_check | Interface design |
| `max-class-size` | ast_check | Single responsibility |
| `constructor-injection-required` | custom | DI pattern |
| `no-bare-except` | regex | Error handling quality |
| `no-star-imports` | regex | Import clarity |

#### Tier 3: Optional (Info/Disabled)

Enable per-project based on tooling:

| Check ID | Type | Prerequisite |
|----------|------|--------------|
| `ruff-lint` | command | `pip install ruff` |
| `ruff-format` | command | `pip install ruff` |
| `mypy-strict` | command | `pip install mypy` |
| `pytest-pass` | command | tests exist |
| `bandit-scan` | command | `pip install bandit` |

### Revised agentforge.contract.yaml

```yaml
schema_version: "1.0"

contract:
  name: "agentforge"
  type: patterns
  description: |
    AgentForge project contract with production-ready defaults.
    
    This contract enables meaningful checks by default while allowing
    teams to customize based on their tooling and workflow.
  version: "2.0.0"
  enabled: true
  extends:
    - "_architecture-python"
    - "_patterns-python"
    - "_typing-python"
    - "_security-python"
    - "_testing-python"
    - "_cli-python"
  applies_to:
    languages:
      - python
  tags:
    - agentforge
    - python
    - production

checks:
  # ===========================================================================
  # TIER 1: ALWAYS ENABLED - Errors
  # ===========================================================================
  
  # Architecture checks - ENABLED
  - id: layer-dependency-violations
    enabled: true
    severity: error
  
  - id: domain-purity
    enabled: true
    severity: error
  
  # Security checks - ENABLED  
  - id: no-secrets-in-code
    enabled: true
    severity: error
  
  - id: no-private-keys
    enabled: true
    severity: error
  
  - id: no-env-files
    enabled: true
    severity: error
  
  # Project-specific security
  - id: yaml-safe-load
    name: "Use yaml.safe_load"
    description: "Always use safe_load for YAML parsing"
    type: regex
    severity: error
    enabled: true
    config:
      pattern: "yaml\\.load\\s*\\([^)]*\\)(?!.*Loader)"
      mode: forbid
    applies_to:
      paths:
        - "**/*.py"
    fix_hint: "Use yaml.safe_load() instead of yaml.load()"

  # ===========================================================================
  # TIER 2: ENABLED BY DEFAULT - Warnings
  # ===========================================================================
  
  # Code quality metrics - ENABLED as warnings
  - id: max-cyclomatic-complexity
    enabled: true
    severity: warning
    config:
      metric: cyclomatic_complexity
      threshold: 10
  
  - id: max-function-length
    enabled: true
    severity: warning
    config:
      metric: function_length
      threshold: 50
  
  - id: max-nesting-depth
    enabled: true
    severity: warning
    config:
      metric: nesting_depth
      threshold: 4
  
  - id: max-parameter-count
    enabled: true
    severity: warning
    config:
      metric: parameter_count
      threshold: 5
  
  - id: max-class-size
    enabled: true
    severity: warning
    config:
      metric: class_size
      threshold: 20
  
  # Pattern checks - ENABLED
  - id: no-bare-except
    enabled: true
    severity: warning
  
  - id: no-star-imports
    enabled: true
    severity: warning
  
  - id: no-breakpoint
    enabled: true
    severity: error
  
  - id: no-pdb-import
    enabled: true
    severity: error
  
  # DI pattern - ENABLED (warning, not error)
  - id: constructor-injection-required
    enabled: true
    severity: warning
  
  # File structure - ENABLED
  - id: require-tools-init
    enabled: true
    severity: warning
  
  - id: require-schemas-dir
    enabled: true
    severity: warning
  
  - id: require-builtin-contracts
    enabled: true
    severity: warning
  
  - id: max-file-lines
    enabled: true
    severity: warning
    config:
      max_lines: 500
      max_bytes: 100000

  # ===========================================================================
  # TIER 3: TOOL-DEPENDENT - Disabled until tools available
  # ===========================================================================
  
  # These check for tool availability before running
  - id: ruff-lint
    name: "Ruff Linting"
    type: command
    severity: warning
    enabled: false  # Enable with: agentforge contract enable ruff-lint
    config:
      command: "ruff"
      args: ["check", "."]
      prerequisite: "which ruff"  # Only run if ruff is installed

  - id: ruff-format
    name: "Ruff Formatting"
    type: command
    severity: info
    enabled: false
    config:
      command: "ruff"
      args: ["format", "--check", "."]
      prerequisite: "which ruff"

  - id: mypy-standard
    name: "mypy Type Check"
    type: command
    severity: warning
    enabled: false  # Enable with: agentforge contract enable mypy-standard
    config:
      command: "mypy"
      args: [".", "--ignore-missing-imports"]
      prerequisite: "which mypy"

  - id: pytest-pass
    name: "pytest Tests Pass"
    type: command
    severity: error
    enabled: false  # Enable with: agentforge contract enable pytest-pass
    config:
      command: "pytest"
      args: ["tests/", "-v", "--tb=short"]
      prerequisite: "test -d tests"

  - id: bandit-scan
    name: "Bandit Security Scan"
    type: command
    severity: warning
    enabled: false
    config:
      command: "bandit"
      args: ["-r", ".", "-ll"]
      prerequisite: "which bandit"

  # ===========================================================================
  # OVERRIDES - Project-specific adjustments
  # ===========================================================================
  
  # CLI tool uses print() intentionally - override inherited check
  - id: no-print-statements
    enabled: false  # CLI tools use print() for output
  
  # Project uses tools/ not src/ layout
  - id: require-init-files
    enabled: false  # Non-standard layout
  
  # execute.py is the entry point
  - id: require-main-entry
    enabled: false  # Using execute.py instead
```

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Priority: HIGH)

1. **Add new builtin check functions** (~2 days)
   - `check_layer_imports()`
   - `check_constructor_injection()`
   - `check_domain_purity()`
   - `check_circular_imports()`

2. **Update `_architecture-python.contract.yaml`** (~1 day)
   - Replace regex checks with custom checks
   - Add new semantic checks

3. **Update `agentforge.contract.yaml`** (~0.5 day)
   - Enable default checks
   - Configure appropriate severities

### Phase 2: Generative Patterns (~3 days)

1. **Define generative contract schema**
   - Add `patterns` and `anti_patterns` sections
   - Define template structure

2. **Create `_generative-python.contract.yaml`**
   - Service class pattern
   - Repository interface pattern
   - Domain entity pattern
   - Result type pattern
   - Test class pattern

3. **Integrate with SPEC workflow**
   - Include relevant patterns in DRAFT phase prompt
   - Validate generated code against patterns

### Phase 3: Validation & Testing (~2 days)

1. **Add unit tests for new checks**
   - Test layer violation detection
   - Test DI pattern detection
   - Test false positive/negative cases

2. **Run against AgentForge codebase**
   - Fix any violations in existing code
   - Document exemptions where needed

3. **Update documentation**
   - Update CONTEXT.md with new patterns
   - Add examples to contract README

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| New checks produce false positives | Medium | High | Thorough testing; severity=warning initially |
| Performance impact of AST analysis | Low | Medium | Cache parsed ASTs; parallel processing |
| Generative patterns too rigid | Medium | Medium | Make patterns customizable; allow overrides |
| Breaking existing workflows | Low | High | Gradual rollout; feature flags |

---

## Success Metrics

1. **Accuracy**: < 5% false positive rate on layer violation checks
2. **Coverage**: > 80% of generated code matches generative patterns
3. **Adoption**: All new code passes Tier 1 checks without exemptions
4. **Performance**: Full verification completes in < 30 seconds

---

## Appendix A: Check Type Decision Matrix

| Scenario | Use This Type | NOT This |
|----------|---------------|----------|
| Layer dependency violations | `custom` (AST) | `regex` |
| Import analysis | `custom` (AST) | `regex` |
| Method/class naming | `lsp_query` | `regex` |
| Symbol visibility | `lsp_query` | `regex` |
| Code metrics | `ast_check` | `regex` |
| Hardcoded secrets | `regex` | ❌ |
| TODO comments | `regex` | ❌ |
| File exists/forbidden | `file_exists` | `regex` |
| External tool (ruff, mypy) | `command` | `custom` |
| Complex multi-file logic | `custom` | anything else |

---

## Appendix B: Migration Guide

### Migrating Existing Regex Checks to LSP/AST

**Before (Regex):**
```yaml
- id: domain-no-infrastructure
  type: regex
  config:
    pattern: "from\\s+(\\w+\\.)?infrastructure"
    mode: forbid
```

**After (Custom AST):**
```yaml
- id: layer-dependency-violations
  type: custom
  config:
    module: builtin_checks
    function: check_layer_imports
    params:
      layer_rules:
        domain:
          forbidden: [infrastructure]
```

**Benefits:**
- Semantic understanding of imports
- No false positives from strings/comments
- Detects aliased imports
- Can detect transitive violations
