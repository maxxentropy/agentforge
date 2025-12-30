# Chunk 4: Brownfield Discovery - Complete Specification

## Executive Summary

**Brownfield Discovery** is the system for analyzing existing codebases and reverse-engineering the artifacts that would have been produced if the code had been developed through the AgentForge greenfield workflow. It implements the **Artifact Parity Principle**: a brownfield project that completes onboarding should have identical artifacts to a greenfield project.

### Core Insight

Brownfield discovery is NOT just "detect patterns" - it's **reverse-engineer the greenfield artifacts** from existing code:
- Specifications (as-built)
- Architecture definitions (as-built)
- Validation reports (with violations as remediation backlog)
- Test coverage analysis (with gaps identified)

---

## Table of Contents

1. [Background & Context](#1-background--context)
2. [Design Philosophy](#2-design-philosophy)
3. [Functional Requirements](#3-functional-requirements)
4. [Technical Architecture](#4-technical-architecture)
5. [Discovery Phases](#5-discovery-phases)
6. [Output Artifacts](#6-output-artifacts)
7. [CLI Interface](#7-cli-interface)
8. [Integration Points](#8-integration-points)
9. [Schemas](#9-schemas)
10. [Acceptance Criteria](#10-acceptance-criteria)
11. [Implementation Guidance](#11-implementation-guidance)
12. [Risks & Mitigations](#12-risks--mitigations)

---

## 1. Background & Context

### 1.1 Position in Architecture

This is **Chunk 4** of the AgentForge workspace architecture. It builds upon:

| Chunk | Name | Relationship |
|-------|------|--------------|
| Chunk 1 | Workspace Config | Provides repo.yaml configuration |
| Chunk 2 | Contract System | Provides contracts to validate against |
| Chunk 3 | Conformance Tracking | Receives violations, tracks remediation |

### 1.2 The Problem

Most real-world codebases are **brownfield** - they exist before AgentForge adoption:
- They have undocumented patterns and conventions
- They may not follow Clean Architecture consistently
- They lack the specifications that greenfield would produce
- New features must blend with existing code

Without brownfield discovery:
- Agents generate code that clashes with existing patterns
- Violations are discovered late in the workflow
- Technical debt is invisible
- Onboarding is manual and error-prone

### 1.3 The Solution: Artifact Parity

```
┌────────────────────────────────────────────────────────────────────────┐
│                     ARTIFACT PARITY PRINCIPLE                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  GREENFIELD                          BROWNFIELD                        │
│                                                                        │
│  Write spec ──────────────────────── Reverse-engineer spec from code   │
│       │                                      │                         │
│       ▼                                      ▼                         │
│  specification.yaml ═══════════════ specification.yaml (as-built)      │
│                                                                        │
│  Validate spec ───────────────────── Validate spec                     │
│       │                                      │                         │
│       ▼                                      ▼                         │
│  validation_report.yaml ═══════════ validation_report.yaml             │
│  (issues fixed before proceeding)    (violations = remediation backlog)│
│                                                                        │
│  Define architecture ─────────────── Extract architecture              │
│       │                                      │                         │
│       ▼                                      ▼                         │
│  architecture.yaml ════════════════ architecture.yaml (as-built)       │
│                                                                        │
│  The artifacts are THE SAME. The path to get there is different.       │
│  Violations in brownfield become remediation backlog, not blockers.    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Scope

**In Scope:**
- Language and framework detection
- Project structure analysis
- Pattern extraction (error handling, CQRS, repositories, etc.)
- Architecture mapping (layers, dependencies)
- Convention inference (naming, file organization)
- As-built specification generation
- Codebase profile generation
- Test gap analysis
- Dependency analysis
- Incremental onboarding support

**Out of Scope:**
- Violation remediation (Chunk 3 handles tracking)
- Cross-repo aggregation (Chunk 7)
- CI/CD integration (Chunk 8)
- Automated code fixes (future capability)

---

## 2. Design Philosophy

### 2.1 Core Principles

1. **Artifact Parity**: Brownfield produces identical artifact types as greenfield
2. **Non-Destructive**: Discovery never modifies existing code
3. **Confidence Scoring**: All extractions include confidence levels
4. **Human Curation**: Allow human override of detected patterns
5. **Incremental**: Support module-by-module discovery for large codebases
6. **Language Agnostic**: Core abstractions work across languages

### 2.2 Detection Philosophy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DETECTION CONFIDENCE LEVELS                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  HIGH CONFIDENCE (0.9+)                                              │
│  ├── Project file analysis (*.csproj, pyproject.toml)                │
│  ├── Explicit markers (attributes, decorators, comments)             │
│  └── Structural patterns (directory names, file counts)              │
│                                                                      │
│  MEDIUM CONFIDENCE (0.6-0.9)                                         │
│  ├── AST pattern matching (Result<T> returns, base classes)          │
│  ├── Naming convention inference (sample-based)                      │
│  └── Import/dependency analysis                                      │
│                                                                      │
│  LOW CONFIDENCE (0.3-0.6)                                            │
│  ├── Heuristic matching (code structure similarity)                  │
│  ├── Comment/documentation extraction                                │
│  └── Statistical inference (minority patterns)                       │
│                                                                      │
│  REQUIRES HUMAN (below 0.3)                                          │
│  └── Flag for manual review, don't auto-apply                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Pattern Extraction Strategy

Patterns are extracted through multiple signals:

| Signal Type | Example | Weight |
|-------------|---------|--------|
| **Explicit** | `[Command]` attribute | 1.0 |
| **Structural** | Files in `Commands/` folder | 0.8 |
| **Naming** | `*Command.cs` file names | 0.7 |
| **AST** | Class inherits `IRequest<T>` | 0.9 |
| **Statistical** | >70% of methods return `Result<T>` | 0.6 |

---

## 3. Functional Requirements

### FR-001: Language Detection

**Description:** Detect primary and secondary programming languages in the codebase.

**Inputs:**
- Repository root path

**Outputs:**
- List of detected languages with percentages
- Confidence scores for each detection
- Framework/toolchain information

**Acceptance Criteria:**
- AC-001.1: Detects language from project files (*.csproj → C#, pyproject.toml → Python)
- AC-001.2: Calculates language percentages by file count and/or LOC
- AC-001.3: Identifies frameworks (ASP.NET Core, FastAPI, etc.)
- AC-001.4: Confidence score >= 0.9 for project-file-based detection

---

### FR-002: Project Structure Analysis

**Description:** Map the directory structure and identify architectural components.

**Inputs:**
- Repository root path
- Optional: hints from repo.yaml

**Outputs:**
- Layer mapping (if Clean Architecture detected)
- Entry points (main projects, executables)
- Test project locations
- Shared/common code locations

**Acceptance Criteria:**
- AC-002.1: Identifies src/, tests/, docs/ structure variations
- AC-002.2: Maps directories to architectural layers when pattern matches
- AC-002.3: Detects entry point projects (console, web, library)
- AC-002.4: Identifies test projects and test frameworks in use
- AC-002.5: Handles monorepo and single-project structures

---

### FR-003: Pattern Extraction

**Description:** Extract coding patterns in use throughout the codebase.

**Patterns to Detect:**

| Pattern | Detection Method |
|---------|------------------|
| Error Handling | Return types (Result<T>, exceptions), try/catch frequency |
| CQRS | Command/Query classes, MediatR usage, handler patterns |
| Repository | Interface patterns, data access abstractions |
| Domain-Driven Design | Entities, Value Objects, Aggregates, Domain Events |
| Dependency Injection | Constructor parameters, DI framework usage |
| Async Patterns | async/await usage, Task returns |

**Acceptance Criteria:**
- AC-003.1: Detects Result<T> pattern vs exception-based error handling
- AC-003.2: Identifies CQRS patterns (Commands, Queries, Handlers)
- AC-003.3: Extracts repository interface patterns
- AC-003.4: Detects DDD tactical patterns (Entity, ValueObject, etc.)
- AC-003.5: Each pattern includes usage examples from actual code
- AC-003.6: Patterns include confidence scores

---

### FR-004: Architecture Mapping

**Description:** Create a map of the actual architecture including dependencies.

**Outputs:**
- Layer definitions with actual boundaries
- Dependency graph between layers/projects
- Layer violation list (actual cross-layer dependencies)

**Acceptance Criteria:**
- AC-004.1: Detects Clean Architecture layers from paths and namespaces
- AC-004.2: Builds project/module dependency graph
- AC-004.3: Identifies layer violations (Domain → Infrastructure, etc.)
- AC-004.4: Outputs architecture.yaml (as-built) format
- AC-004.5: Integrates with Chunk 2 architecture checks

---

### FR-005: Convention Inference

**Description:** Learn naming conventions and file organization patterns.

**Conventions to Detect:**

| Convention | Examples |
|------------|----------|
| File Naming | PascalCase, snake_case, kebab-case |
| Class Naming | EntityService, IEntityRepository |
| Method Naming | GetById, FindByEmail |
| Field Naming | _privateField, m_member |
| Test Naming | Should_DoX_When_Y, Test_Method_Scenario |

**Acceptance Criteria:**
- AC-005.1: Infers file naming convention from sample
- AC-005.2: Detects interface naming patterns (I-prefix, -able suffix)
- AC-005.3: Identifies private field naming (_camelCase, etc.)
- AC-005.4: Extracts test naming patterns
- AC-005.5: Reports consistency percentage for each convention

---

### FR-006: As-Built Specification Generation

**Description:** Generate specification.yaml files that describe what was actually built.

**Scope:**
- One specification per logical component/feature (auto-detected or configured)
- Specifications describe actual behavior, not intended behavior
- Marked clearly as "as-built" vs "as-intended"

**Acceptance Criteria:**
- AC-006.1: Generates specification structure from code analysis
- AC-006.2: Extracts entities and their properties
- AC-006.3: Identifies API endpoints and their contracts
- AC-006.4: Links to actual source files
- AC-006.5: Marks specifications as source: "discovered"

---

### FR-007: Codebase Profile Generation

**Description:** Combine all analysis into a comprehensive codebase_profile.yaml.

**Acceptance Criteria:**
- AC-007.1: Consolidates all discovery outputs
- AC-007.2: Validates against codebase_profile.schema.yaml
- AC-007.3: Includes overall confidence score
- AC-007.4: Supports incremental updates (merge new with existing)
- AC-007.5: Tracks what has been analyzed vs not analyzed

---

### FR-008: Test Gap Analysis

**Description:** Analyze existing tests and identify coverage gaps.

**Outputs:**
- Test inventory (unit, integration, e2e)
- Test-to-code mapping where possible
- Coverage gaps (code without tests)
- Test pattern analysis

**Acceptance Criteria:**
- AC-008.1: Identifies test projects and frameworks
- AC-008.2: Counts test methods by category
- AC-008.3: Maps tests to source files where naming allows
- AC-008.4: Reports estimated coverage without running tests
- AC-008.5: Identifies untested public APIs

---

### FR-009: Dependency Analysis

**Description:** Analyze external dependencies for currency and risk.

**Outputs:**
- Package inventory with versions
- Outdated package report
- Security vulnerability flags (where data available)
- License inventory

**Acceptance Criteria:**
- AC-009.1: Parses package files (*.csproj, requirements.txt, package.json)
- AC-009.2: Lists all dependencies with versions
- AC-009.3: Flags packages with known issues (configurable source)
- AC-009.4: Extracts license information where available

---

### FR-010: Incremental Onboarding

**Description:** Support discovery of large codebases in phases.

**Acceptance Criteria:**
- AC-010.1: Can discover single module/project at a time
- AC-010.2: Tracks onboarding progress (what's analyzed vs not)
- AC-010.3: Merges incremental discoveries into unified profile
- AC-010.4: Supports re-analysis of previously discovered modules

---

### FR-011: Human Curation Workflow

**Description:** Allow humans to review and override detected patterns.

**Acceptance Criteria:**
- AC-011.1: All detections marked as auto-detected or human-curated
- AC-011.2: Curated values override auto-detected
- AC-011.3: Re-discovery preserves human curations
- AC-011.4: Export/import curation decisions

---

### FR-012: CLI Integration

**Description:** Provide command-line interface for discovery operations.

**Commands:**

| Command | Description |
|---------|-------------|
| `agentforge discover` | Run full discovery |
| `agentforge discover --module <path>` | Discover specific module |
| `agentforge discover --patterns` | Pattern extraction only |
| `agentforge discover --architecture` | Architecture mapping only |
| `agentforge discover --update` | Update existing profile |
| `agentforge discover --diff` | Show changes since last run |
| `agentforge discover --export` | Export profile as report |

**Acceptance Criteria:**
- AC-012.1: All commands execute and produce valid output
- AC-012.2: Progress reporting for long-running operations
- AC-012.3: JSON output option for programmatic use
- AC-012.4: Respects configuration from repo.yaml

---

### FR-013: Integration with Conformance System

**Description:** Discovered code flows through Chunk 3 conformance system.

**Acceptance Criteria:**
- AC-013.1: Discovery triggers conformance check automatically
- AC-013.2: Violations tracked in .agentforge/violations/
- AC-013.3: Remediation backlog generated from violations
- AC-013.4: As-built specs validated against contracts

---

## 4. Technical Architecture

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BROWNFIELD DISCOVERY                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     DISCOVERY MANAGER                             │   │
│  │  (Orchestrates discovery phases, manages state)                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│         ┌────────────────────┼────────────────────┐                     │
│         ▼                    ▼                    ▼                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│  │   LANGUAGE  │     │  STRUCTURE  │     │   PATTERN   │               │
│  │   DETECTOR  │     │  ANALYZER   │     │  EXTRACTOR  │               │
│  └─────────────┘     └─────────────┘     └─────────────┘               │
│         │                    │                    │                     │
│         ▼                    ▼                    ▼                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│  │ ARCHITECTURE│     │ CONVENTION  │     │  TEST GAP   │               │
│  │   MAPPER    │     │  INFERRER   │     │  ANALYZER   │               │
│  └─────────────┘     └─────────────┘     └─────────────┘               │
│         │                    │                    │                     │
│         └────────────────────┼────────────────────┘                     │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     PROFILE GENERATOR                             │   │
│  │  (Consolidates outputs, generates codebase_profile.yaml)          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  CONFORMANCE INTEGRATION                          │   │
│  │  (Triggers Chunk 3 violation tracking)                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Language Provider Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      LANGUAGE PROVIDER INTERFACE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  interface LanguageProvider:                                             │
│    detect_project(path) → ProjectInfo                                    │
│    parse_file(path) → AST                                                │
│    extract_symbols(path) → List[Symbol]                                  │
│    get_imports(path) → List[Import]                                      │
│    get_dependencies(project_path) → List[Dependency]                     │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ PythonProvider │  │ DotNetProvider │  │ TypeScriptProv │             │
│  ├────────────────┤  ├────────────────┤  ├────────────────┤             │
│  │ AST: ast       │  │ AST: roslyn/lsp│  │ AST: ts-parser │             │
│  │ Deps: pip/pypi │  │ Deps: nuget    │  │ Deps: npm      │             │
│  │ Project: pyproj│  │ Project: csproj│  │ Project: pkg.js│             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Data Flow

```
Repository Root
       │
       ▼
┌──────────────┐     ┌──────────────┐
│   Language   │────▶│  Structure   │
│   Detection  │     │   Analysis   │
└──────────────┘     └──────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│   Pattern    │────▶│ Architecture │
│  Extraction  │     │   Mapping    │
└──────────────┘     └──────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│  Convention  │     │   Test Gap   │
│  Inference   │     │   Analysis   │
└──────────────┘     └──────────────┘
       │                    │
       └────────┬───────────┘
                ▼
        ┌──────────────┐
        │   Profile    │
        │  Generator   │
        └──────────────┘
                │
                ▼
        ┌──────────────┐
        │ codebase_    │
        │ profile.yaml │
        └──────────────┘
                │
                ▼
        ┌──────────────┐
        │ Conformance  │
        │   Check      │
        └──────────────┘
                │
                ▼
        ┌──────────────┐
        │  Violations  │
        │  (Chunk 3)   │
        └──────────────┘
```

---

## 5. Discovery Phases

### Phase 1: Project Detection

**Goal:** Identify what kind of project this is.

**Process:**
1. Scan for project marker files:
   - `*.csproj`, `*.sln` → .NET
   - `pyproject.toml`, `setup.py`, `requirements.txt` → Python
   - `package.json` → Node.js/TypeScript
   - `Cargo.toml` → Rust
   - `go.mod` → Go

2. Parse project files for metadata:
   - Framework versions
   - Package references
   - Build configuration

3. Calculate language percentages by file extension

**Output:**
```yaml
languages:
  - name: csharp
    percentage: 78.5
    confidence: 0.95
    source: auto-detected
    frameworks:
      - ASP.NET Core 8.0
      - Entity Framework Core 8.0
  - name: typescript
    percentage: 15.2
    confidence: 0.90
    source: auto-detected
```

---

### Phase 2: Structure Analysis

**Goal:** Map the directory structure to architectural concepts.

**Process:**
1. Build directory tree with file counts
2. Match against known patterns:
   - `src/Domain`, `src/Application`, `src/Infrastructure` → Clean Architecture
   - `src/`, `tests/`, `docs/` → Standard layout
   - `packages/` → Monorepo

3. Identify entry points:
   - Projects with `<OutputType>Exe</OutputType>`
   - `Program.cs`, `main.py`, `index.ts`

4. Identify test projects:
   - Projects with test framework references
   - Directories named `tests`, `test`, `__tests__`

**Output:**
```yaml
structure:
  style: clean-architecture
  confidence: 0.85
  layers:
    - name: Domain
      path: src/MyApp.Domain
      purpose: Business entities and rules
    - name: Application
      path: src/MyApp.Application
      purpose: Use cases and orchestration
    - name: Infrastructure
      path: src/MyApp.Infrastructure
      purpose: External concerns implementation
    - name: Api
      path: src/MyApp.Api
      purpose: HTTP API entry point
  entry_points:
    - src/MyApp.Api/MyApp.Api.csproj
  test_projects:
    - tests/MyApp.UnitTests
    - tests/MyApp.IntegrationTests
```

---

### Phase 3: Pattern Extraction

**Goal:** Identify coding patterns in use.

**Process for each pattern type:**

#### Error Handling Pattern
1. Analyze method return types
2. Count `Result<T>` vs `void`/direct returns
3. Count try/catch blocks
4. Calculate dominant pattern

```yaml
patterns:
  error_handling:
    primary: result_pattern
    confidence: 0.82
    evidence:
      result_returns: 156
      exception_throws: 23
      try_catch_blocks: 34
    examples:
      - "Order.ApplyDiscount() → Result<Order>"
      - "PaymentService.Process() → Result<PaymentConfirmation>"
```

#### CQRS Pattern
1. Look for MediatR references
2. Find classes implementing `IRequest<T>`, `IRequestHandler<T>`
3. Check for `Commands/` and `Queries/` folders

```yaml
patterns:
  cqrs:
    detected: true
    confidence: 0.91
    framework: MediatR
    evidence:
      command_classes: 24
      query_classes: 18
      handler_classes: 42
    locations:
      commands: src/Application/Commands/
      queries: src/Application/Queries/
    naming:
      commands: "{Action}{Entity}Command"
      queries: "Get{Entity}Query"
```

---

### Phase 4: Architecture Mapping

**Goal:** Document actual architecture including violations.

**Process:**
1. Build project reference graph from project files
2. Build import graph from code analysis
3. Classify each project into layers
4. Identify cross-layer dependencies
5. Flag violations

**Output:**
```yaml
architecture:
  style: clean-architecture
  layers:
    - name: domain
      projects:
        - MyApp.Domain
      allowed_references: []
      actual_references: []
      
    - name: application
      projects:
        - MyApp.Application
      allowed_references: [domain]
      actual_references: [domain]
      
    - name: infrastructure
      projects:
        - MyApp.Infrastructure
      allowed_references: [domain, application]
      actual_references: [domain, application]
      
    - name: presentation
      projects:
        - MyApp.Api
      allowed_references: [application, infrastructure]
      actual_references: [application, infrastructure, domain]  # VIOLATION
      
  violations:
    - type: layer_dependency
      from_layer: presentation
      to_layer: domain
      from_project: MyApp.Api
      to_project: MyApp.Domain
      severity: major
      locations:
        - file: MyApp.Api/Controllers/OrderController.cs
          line: 15
          import: "using MyApp.Domain.Entities"
```

---

### Phase 5: Convention Inference

**Goal:** Learn the naming and organization conventions.

**Process:**
1. Collect samples of each naming type
2. Analyze patterns statistically
3. Identify dominant convention
4. Calculate consistency

**Output:**
```yaml
conventions:
  naming:
    files:
      pattern: PascalCase
      consistency: 0.96
      exceptions: ["README.md", "docker-compose.yml"]
      
    classes:
      pattern: PascalCase
      consistency: 0.99
      
    interfaces:
      pattern: "I{Name}"
      consistency: 0.94
      examples: ["IOrderRepository", "IPaymentService"]
      
    private_fields:
      pattern: "_camelCase"
      consistency: 0.87
      alternatives:
        - pattern: "m_camelCase"
          frequency: 0.13
          
    methods:
      pattern: PascalCase
      async_suffix: true
      consistency: 0.91
      
  file_organization:
    style: "one_class_per_file"
    consistency: 0.89
    exceptions:
      - pattern: "*Extensions.cs"
        note: "Multiple extension classes per file"
        
  test_naming:
    pattern: "Should_{Expected}_When_{Condition}"
    consistency: 0.72
    alternatives:
      - pattern: "{Method}_{Scenario}_{Expected}"
        frequency: 0.28
```

---

### Phase 6: Test Gap Analysis

**Goal:** Understand test coverage without running tests.

**Process:**
1. Inventory test files and methods
2. Map tests to source files by convention
3. Identify public APIs without corresponding tests
4. Analyze test patterns

**Output:**
```yaml
test_analysis:
  inventory:
    total_test_files: 45
    total_test_methods: 312
    frameworks:
      - xUnit
    categories:
      unit: 256
      integration: 48
      e2e: 8
      
  coverage_estimate:
    files_with_tests: 67
    files_without_tests: 23
    estimated_coverage: 0.74
    
  gaps:
    untested_projects:
      - MyApp.Infrastructure
        note: "0 test files found"
    untested_classes:
      - MyApp.Domain.Services.PricingCalculator
      - MyApp.Application.Commands.CancelOrderHandler
      
  patterns:
    naming: "Should_{Expected}_When_{Condition}"
    setup: "constructor injection"
    mocking: "NSubstitute"
```

---

## 6. Output Artifacts

### 6.1 Primary Output: codebase_profile.yaml

Location: `.agentforge/codebase_profile.yaml`

This is the consolidated output of discovery. See [Section 9: Schemas](#9-schemas) for full schema.

### 6.2 Secondary Outputs

| Artifact | Location | Purpose |
|----------|----------|---------|
| As-built specs | `.agentforge/specs/` | Reverse-engineered specifications |
| Architecture (as-built) | `.agentforge/architecture.yaml` | Actual architecture map |
| Discovery log | `.agentforge/discovery_log.yaml` | Audit trail of discovery |
| Remediation backlog | Chunk 3 violations | Via conformance integration |

---

## 7. CLI Interface

### 7.1 Main Command

```bash
agentforge discover [OPTIONS]
```

### 7.2 Options

| Option | Description |
|--------|-------------|
| `--module <path>` | Discover specific module only |
| `--phase <name>` | Run specific phase (language, structure, patterns, architecture, conventions, tests) |
| `--update` | Update existing profile (preserve human curations) |
| `--diff` | Show what changed since last discovery |
| `--dry-run` | Show what would be discovered without writing |
| `--json` | Output as JSON for programmatic use |
| `--verbose` | Detailed progress output |
| `--no-conformance` | Skip automatic conformance check |

### 7.3 Examples

```bash
# Full discovery
agentforge discover

# Discover and show diff from last run
agentforge discover --diff

# Discover only the Domain project
agentforge discover --module src/MyApp.Domain

# Pattern extraction only
agentforge discover --phase patterns

# Update profile, preserving human curations
agentforge discover --update

# JSON output for CI integration
agentforge discover --json > discovery_results.json
```

### 7.4 Output Format

```
============================================================
BROWNFIELD DISCOVERY
============================================================

Phase 1: Language Detection
  ✓ Detected: C# (78.5%), TypeScript (15.2%), Other (6.3%)
  ✓ Frameworks: ASP.NET Core 8.0, Entity Framework Core 8.0

Phase 2: Structure Analysis
  ✓ Architecture: Clean Architecture (confidence: 0.85)
  ✓ Layers: Domain, Application, Infrastructure, Api
  ✓ Entry points: 1 found
  ✓ Test projects: 2 found

Phase 3: Pattern Extraction
  ✓ Error handling: Result<T> pattern (confidence: 0.82)
  ✓ CQRS: MediatR (confidence: 0.91)
  ✓ Repositories: Interface pattern (confidence: 0.88)
  
Phase 4: Architecture Mapping
  ✓ Layer graph built
  ⚠ 3 layer violations detected

Phase 5: Convention Inference
  ✓ Naming: PascalCase files, I-prefix interfaces
  ✓ Consistency: 91% overall

Phase 6: Test Gap Analysis
  ✓ 312 tests in 45 files
  ⚠ Estimated coverage: 74%
  ⚠ 23 files without tests

------------------------------------------------------------
Discovery complete. Profile saved to .agentforge/codebase_profile.yaml

Summary:
  Patterns detected: 8
  Conventions inferred: 12
  Violations found: 3 (will be tracked in conformance system)
  Files analyzed: 234
  
Run 'agentforge conformance report' to see full violation details.
```

---

## 8. Integration Points

### 8.1 Integration with Chunk 1 (Workspace Config)

- Reads `repo.yaml` for configuration hints
- Respects ignore patterns from configuration
- Updates profile location from config if specified

### 8.2 Integration with Chunk 2 (Contract System)

- Uses contract definitions to validate discovered patterns
- Leverages AST checks for pattern detection
- Feeds architecture violations to contract checks

### 8.3 Integration with Chunk 3 (Conformance Tracking)

```
Discovery completes
       │
       ▼
Trigger conformance check (automatic unless --no-conformance)
       │
       ▼
Violations created in .agentforge/violations/
       │
       ▼
Remediation backlog available via 'agentforge conformance violations list'
```

### 8.4 Integration with Existing Tools

| Component | Integration |
|-----------|-------------|
| LSP Adapters | Use for accurate symbol extraction |
| AST Checks | Use for pattern detection |
| Vector Search | Could use for semantic similarity in pattern matching |
| Context Retrieval | Feed profile to improve context selection |

---

## 9. Schemas

### 9.1 Enhanced codebase_profile.schema.yaml

The existing schema needs enhancement. Proposed additions:

```yaml
# Additional properties for codebase_profile.schema.yaml

properties:
  discovery_metadata:
    type: object
    properties:
      version:
        type: string
        description: "Discovery engine version"
      run_date:
        type: string
        format: date-time
      run_type:
        type: string
        enum: [full, incremental, phase]
      duration_ms:
        type: integer
      phases_completed:
        type: array
        items:
          type: string
          
  patterns:
    type: object
    properties:
      error_handling:
        $ref: "#/definitions/PatternDetection"
      cqrs:
        $ref: "#/definitions/PatternDetection"
      repository:
        $ref: "#/definitions/PatternDetection"
      ddd:
        $ref: "#/definitions/PatternDetection"
      dependency_injection:
        $ref: "#/definitions/PatternDetection"
        
  conventions:
    type: object
    properties:
      naming:
        $ref: "#/definitions/NamingConventions"
      file_organization:
        $ref: "#/definitions/FileOrganization"
      test_naming:
        $ref: "#/definitions/ConventionDetection"
        
  architecture:
    type: object
    properties:
      style:
        type: string
      confidence:
        type: number
      layers:
        type: array
        items:
          $ref: "#/definitions/ArchitectureLayer"
      violations:
        type: array
        items:
          $ref: "#/definitions/ArchitectureViolation"
          
  test_analysis:
    type: object
    properties:
      inventory:
        $ref: "#/definitions/TestInventory"
      coverage_estimate:
        $ref: "#/definitions/CoverageEstimate"
      gaps:
        $ref: "#/definitions/TestGaps"
        
  dependencies:
    type: array
    items:
      $ref: "#/definitions/DependencyInfo"
      
  onboarding_progress:
    type: object
    properties:
      status:
        type: string
        enum: [not_started, in_progress, complete]
      modules:
        type: object
        additionalProperties:
          type: string
          enum: [not_started, in_progress, analyzed]
          
definitions:
  PatternDetection:
    type: object
    properties:
      detected:
        type: boolean
      primary:
        type: string
      confidence:
        type: number
        minimum: 0
        maximum: 1
      source:
        type: string
        enum: [auto-detected, human-curated]
      evidence:
        type: object
      examples:
        type: array
        items:
          type: string
          
  ConventionDetection:
    type: object
    properties:
      pattern:
        type: string
      consistency:
        type: number
        minimum: 0
        maximum: 1
      source:
        type: string
        enum: [auto-detected, human-curated]
      exceptions:
        type: array
        items:
          type: string
      alternatives:
        type: array
        items:
          type: object
          properties:
            pattern:
              type: string
            frequency:
              type: number
```

---

## 10. Acceptance Criteria

### 10.1 Core Functionality

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-CORE-01 | Discovery runs without errors on valid Python project | Must |
| AC-CORE-02 | Discovery runs without errors on valid .NET project | Must |
| AC-CORE-03 | Generates valid codebase_profile.yaml | Must |
| AC-CORE-04 | Profile validates against schema | Must |
| AC-CORE-05 | All detections include confidence scores | Must |

### 10.2 Pattern Detection

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-PAT-01 | Detects Result<T> pattern in C# with >80% accuracy | Must |
| AC-PAT-02 | Detects MediatR CQRS pattern | Should |
| AC-PAT-03 | Detects repository interface pattern | Should |
| AC-PAT-04 | Provides code examples for each pattern | Must |

### 10.3 Architecture

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-ARCH-01 | Detects Clean Architecture layer structure | Must |
| AC-ARCH-02 | Identifies layer violations | Must |
| AC-ARCH-03 | Produces architecture.yaml | Should |

### 10.4 Integration

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-INT-01 | Triggers Chunk 3 conformance check | Must |
| AC-INT-02 | Violations appear in conformance report | Must |
| AC-INT-03 | Respects repo.yaml configuration | Should |

### 10.5 CLI

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-CLI-01 | `agentforge discover` completes successfully | Must |
| AC-CLI-02 | `--module` flag works for partial discovery | Should |
| AC-CLI-03 | `--json` produces valid JSON output | Should |
| AC-CLI-04 | Progress reporting works | Should |

---

## 11. Implementation Guidance

### 11.1 Recommended Implementation Order

1. **Phase 1: Core Infrastructure** (~2 days)
   - Discovery manager skeleton
   - Language provider interface
   - Python provider (use existing AST)
   - Profile generator

2. **Phase 2: Structure Analysis** (~1 day)
   - Directory tree builder
   - Layer detection
   - Entry point detection
   - Test project detection

3. **Phase 3: Pattern Extraction** (~2 days)
   - Error handling pattern detector
   - CQRS pattern detector
   - Repository pattern detector
   - Generic pattern framework

4. **Phase 4: Architecture Mapping** (~1 day)
   - Dependency graph builder
   - Layer violation detection
   - Integration with Chunk 2 checks

5. **Phase 5: Convention Inference** (~1 day)
   - Naming convention analyzer
   - Consistency calculator
   - File organization detector

6. **Phase 6: CLI & Integration** (~1 day)
   - CLI commands
   - Chunk 3 integration
   - Output formatting

7. **Phase 7: .NET Provider** (~2 days)
   - csproj parsing
   - LSP integration for symbols
   - NuGet dependency analysis

### 11.2 File Organization

```
tools/
├── discovery/
│   ├── __init__.py
│   ├── manager.py              # DiscoveryManager orchestration
│   ├── domain.py               # Domain entities
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py             # LanguageProvider interface
│   │   ├── python_provider.py
│   │   └── dotnet_provider.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── structure.py        # StructureAnalyzer
│   │   ├── patterns.py         # PatternExtractor
│   │   ├── architecture.py     # ArchitectureMapper
│   │   ├── conventions.py      # ConventionInferrer
│   │   └── tests.py            # TestGapAnalyzer
│   └── generators/
│       ├── __init__.py
│       └── profile.py          # ProfileGenerator

cli/
└── commands/
    └── discover.py             # CLI command implementation

schemas/
└── codebase_profile.schema.yaml  # Enhanced schema

tests/
└── unit/
    └── tools/
        └── discovery/
            ├── test_manager.py
            ├── test_providers.py
            ├── test_analyzers.py
            └── test_generators.py
```

### 11.3 Key Classes

```python
# manager.py
class DiscoveryManager:
    """Orchestrates the discovery process."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.provider = self._detect_provider()
        
    def discover(
        self,
        phases: List[str] = None,
        module_path: Path = None,
        update: bool = False
    ) -> CodebaseProfile:
        """Run discovery phases and generate profile."""
        
    def _detect_provider(self) -> LanguageProvider:
        """Detect and return appropriate language provider."""

# providers/base.py
class LanguageProvider(ABC):
    """Abstract base for language-specific analysis."""
    
    @abstractmethod
    def detect_project(self, path: Path) -> ProjectInfo: ...
    
    @abstractmethod
    def parse_file(self, path: Path) -> AST: ...
    
    @abstractmethod
    def extract_symbols(self, path: Path) -> List[Symbol]: ...
    
    @abstractmethod
    def get_dependencies(self, project_path: Path) -> List[Dependency]: ...

# analyzers/patterns.py
class PatternExtractor:
    """Extracts coding patterns from codebase."""
    
    def extract_all(self, provider: LanguageProvider) -> Dict[str, PatternDetection]:
        """Extract all detectable patterns."""
        
    def extract_error_handling(self, ...) -> PatternDetection: ...
    def extract_cqrs(self, ...) -> PatternDetection: ...
    def extract_repository(self, ...) -> PatternDetection: ...
```

### 11.4 Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit | Each analyzer independently |
| Integration | Full discovery on sample projects |
| Snapshot | Profile output stability |
| Contract | Schema validation |

**Sample Projects for Testing:**
1. `tests/fixtures/discovery/python_clean_arch/` - Python Clean Architecture
2. `tests/fixtures/discovery/dotnet_clean_arch/` - .NET Clean Architecture
3. `tests/fixtures/discovery/mixed_patterns/` - Inconsistent patterns
4. `tests/fixtures/discovery/minimal/` - Minimal project

---

## 12. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| False pattern detection | Medium | High | Confidence scores, human curation |
| Large codebase performance | High | Medium | Incremental discovery, caching |
| Language-specific complexity | Medium | High | Start with Python, make extensible |
| Pattern conflicts | Low | Medium | Report conflicts for human resolution |
| Integration complexity | Medium | Medium | Clear interfaces, staged rollout |

---

## Appendix A: Pattern Detection Details

### A.1 Result<T> Pattern Detection

**Signals:**
1. Generic type named `Result<T>` or `Result<TSuccess, TError>`
2. Methods returning this type
3. `.IsSuccess`, `.IsFailure` property access
4. `.Match()` method calls

**Detection Algorithm:**
```
for each method in codebase:
    if return_type matches Result<*>:
        result_count++
    elif return_type is void or direct:
        if has try/catch:
            exception_count++
        else:
            simple_count++

if result_count / total > 0.5:
    pattern = "result_pattern"
    confidence = result_count / total
else:
    pattern = "exception_pattern"
    confidence = exception_count / total
```

### A.2 CQRS Pattern Detection

**Signals:**
1. MediatR package reference
2. Classes implementing `IRequest<T>`, `IRequestHandler<T, TResponse>`
3. `Commands/` and `Queries/` directories
4. Naming patterns: `*Command.cs`, `*Query.cs`, `*Handler.cs`

### A.3 Clean Architecture Detection

**Signals:**
1. Directory names: Domain, Application, Infrastructure, Presentation/Api/Web
2. Project naming: `*.Domain`, `*.Application`, etc.
3. Namespace structure matching directories
4. Project reference direction (inner → outer)

---

## Appendix B: Example Outputs

### B.1 Minimal codebase_profile.yaml

```yaml
schema_version: "1.0"
generated_at: "2025-12-30T18:00:00Z"

discovery_metadata:
  version: "1.0.0"
  run_date: "2025-12-30T18:00:00Z"
  run_type: full
  duration_ms: 4523
  phases_completed:
    - language
    - structure
    - patterns
    - architecture
    - conventions

languages:
  - name: csharp
    percentage: 82.3
    confidence: 0.95
    source: auto-detected
    frameworks:
      - name: ASP.NET Core
        version: "8.0"
      - name: Entity Framework Core
        version: "8.0"

structure:
  root_path: "."
  style: clean-architecture
  confidence: 0.88
  layers:
    - name: Domain
      path: src/MyApp.Domain
      purpose: Business entities and domain logic
    - name: Application
      path: src/MyApp.Application
      purpose: Use cases and application services
    - name: Infrastructure
      path: src/MyApp.Infrastructure
      purpose: External concerns (database, APIs)
    - name: Api
      path: src/MyApp.Api
      purpose: HTTP API entry point
  entry_points:
    - src/MyApp.Api/MyApp.Api.csproj
  test_projects:
    - tests/MyApp.UnitTests
    - tests/MyApp.IntegrationTests

patterns:
  error_handling:
    detected: true
    primary: result_pattern
    confidence: 0.84
    source: auto-detected
    evidence:
      result_returns: 127
      exception_throws: 18
    examples:
      - "Order.ApplyDiscount() → Result<Order>"
      
  cqrs:
    detected: true
    primary: mediatr
    confidence: 0.91
    source: auto-detected
    evidence:
      command_classes: 24
      query_classes: 18
      handler_classes: 42

conventions:
  naming:
    files:
      pattern: PascalCase
      consistency: 0.96
      source: auto-detected
    interfaces:
      pattern: "I{Name}"
      consistency: 0.94
      source: auto-detected
    private_fields:
      pattern: "_camelCase"
      consistency: 0.87
      source: auto-detected

architecture:
  style: clean-architecture
  confidence: 0.88
  violations:
    - type: layer_dependency
      from_layer: presentation
      to_layer: domain
      severity: major
      count: 3

test_analysis:
  inventory:
    total_test_files: 45
    total_test_methods: 312
  coverage_estimate:
    estimated_coverage: 0.74
  gaps:
    untested_files: 23

onboarding_progress:
  status: complete
  modules:
    src/MyApp.Domain: analyzed
    src/MyApp.Application: analyzed
    src/MyApp.Infrastructure: analyzed
    src/MyApp.Api: analyzed
```

---

*End of Specification*
