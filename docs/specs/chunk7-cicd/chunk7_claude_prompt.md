# AgentForge Implementation Task: Chunk 7 - CI/CD Integration

## Context

You are implementing Chunk 7 of AgentForge - CI/CD Integration. This enables automated conformance checking in pipelines with PR comments, baseline comparison, and integration with GitHub Actions and Azure DevOps.

**Read these specs first:**
- `docs/specs/chunk7-cicd/specification.md` - Full specification
- `docs/specs/chunk7-cicd/DESIGN_DECISIONS.md` - Design rationale
- `docs/design/implementation_task_chunk_7.md` - Implementation guide

## Objective

Create `tools/cicd/` module that:
1. Runs conformance checks optimized for CI (parallel, incremental)
2. Compares PR violations against baseline (new vs existing)
3. Outputs SARIF (GitHub), JUnit XML (Azure), and Markdown (PR comments)
4. Provides `agentforge ci` CLI commands
5. Generates workflow templates for GitHub Actions and Azure DevOps

## Architecture

```
tools/cicd/
├── __init__.py                 # Public exports
├── domain.py                   # Domain entities
├── runner.py                   # CI-optimized runner
├── baseline.py                 # Baseline management
├── config.py                   # CI configuration
├── outputs/
│   ├── __init__.py
│   ├── sarif.py                # SARIF 2.1.0 generator
│   ├── junit.py                # JUnit XML generator
│   └── markdown.py             # Markdown summary
└── platforms/
    ├── __init__.py
    ├── github.py               # GitHub-specific logic
    └── azure.py                # Azure DevOps-specific logic

cli/click_commands/ci.py        # CLI commands
```

## Key Requirements

### 1. CI Runner Modes

```python
class CIMode(Enum):
    FULL = "full"           # Check entire codebase
    INCREMENTAL = "incremental"  # Only changed files
    PR = "pr"               # Compare to baseline
```

### 2. Baseline Comparison

For PRs, compare violations against baseline on main branch:

```python
@dataclass
class BaselineComparison:
    new_violations: List[CIViolation]      # Block PR ❌
    fixed_violations: List[BaselineEntry]  # Celebrate 🎉
    existing_violations: List[CIViolation] # Allow (tech debt)
```

### 3. Output Formats

| Format | Use Case |
|--------|----------|
| SARIF | GitHub Code Scanning |
| JUnit XML | Azure DevOps Test Results |
| Markdown | PR Comments |
| JSON | Programmatic access |

### 4. CLI Commands

```bash
# Run checks
agentforge ci run --mode [full|incremental|pr] \
  --base-ref origin/main \
  --output-sarif results.sarif \
  --output-markdown summary.md

# Baseline management
agentforge ci baseline save [--output FILE]
agentforge ci baseline compare --baseline FILE

# Generate workflow files
agentforge ci init --platform [github|azure]
```

### 5. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Violations found |
| 2 | Config error |
| 3 | Runtime error |

### 6. Performance Optimizations

- **Parallel execution:** Run checks concurrently
- **Incremental mode:** Only check changed files
- **Caching:** Cache results by file hash

## Implementation Steps

### Step 1: Domain Model (`tools/cicd/domain.py`)

Create these entities:
- `CIMode` - Enum: FULL, INCREMENTAL, PR
- `ExitCode` - Enum with exit codes
- `CIViolation` - Violation with SARIF conversion
- `BaselineEntry` - Entry in baseline file
- `Baseline` - Collection of baseline entries
- `BaselineComparison` - Result of comparing to baseline
- `CIResult` - Complete result of CI run
- `CIConfig` - CI configuration options

### Step 2: CI Runner (`tools/cicd/runner.py`)

```python
class CIRunner:
    def run(
        self,
        mode: CIMode,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> CIResult:
        # 1. Get changed files (if incremental/PR)
        # 2. Load and filter checks
        # 3. Execute checks (parallel)
        # 4. Compare to baseline (if PR mode)
        # 5. Return result
```

### Step 3: Baseline Management (`tools/cicd/baseline.py`)

```python
class BaselineManager:
    def load(self, path: Path) -> Optional[Baseline]: ...
    def save(self, baseline: Baseline, path: Path) -> None: ...
    def create_from_violations(self, violations: List) -> Baseline: ...
    def compare(self, violations: List, baseline: Baseline) -> BaselineComparison: ...
```

### Step 4: Output Generators (`tools/cicd/outputs/`)

- `sarif.py`: SARIF 2.1.0 with tool info, rules, results
- `junit.py`: JUnit XML with testsuites/testcases
- `markdown.py`: Summary table, new/fixed/existing sections

### Step 5: CLI (`cli/click_commands/ci.py`)

```python
@click.group('ci')
def ci(): ...

@ci.command('run')
def run(mode, base_ref, output_sarif, ...): ...

@ci.group('baseline')
def baseline(): ...

@baseline.command('save')
def baseline_save(): ...

@ci.command('init')
def init(platform): ...
```

### Step 6: Workflow Templates

Store as package resources or generate inline:
- `templates/github-workflow.yml`
- `templates/azure-pipeline.yml`

## Integration Points

### With Conformance (Chunk 3)

```python
from tools.conformance import ConformanceChecker, CheckRunner

# Load checks from existing contracts
checker = ConformanceChecker(project_path)
checks = checker.load_all_checks()

# Run individual checks
runner = CheckRunner(project_path)
result = runner.run_check(check)
```

### With Existing CLI

Register in `cli/main.py`:
```python
from cli.click_commands.ci import ci
cli.add_command(ci)
```

## Test Configuration

Create test fixture:

```yaml
# tests/fixtures/baseline.json
{
  "schema_version": "1.0",
  "generated_at": "2025-12-30T12:00:00Z",
  "commit": "abc123",
  "entries": [
    {
      "check_id": "domain-isolation",
      "file": "src/Domain/Order.cs",
      "line": 5,
      "hash": "def456"
    }
  ]
}
```

## Success Criteria

- [ ] `agentforge ci run --mode full` runs all checks
- [ ] `agentforge ci run --mode pr --base-ref main` compares to baseline
- [ ] SARIF output valid (test with GitHub Code Scanning)
- [ ] JUnit XML valid (test with Azure DevOps)
- [ ] Markdown renders correctly in GitHub PR
- [ ] Exit codes are correct
- [ ] `agentforge ci init --platform github` creates workflow file
- [ ] Parallel execution faster than sequential
- [ ] Tests pass

## Existing Code to Reference

- `tools/conformance/` - Check loading and execution
- `tools/conformance/runner.py` - CheckRunner for running checks
- `cli/click_commands/conformance.py` - CLI patterns
- `.agentforge/` - Output directory conventions

## Do NOT

- Modify existing conformance code unless necessary
- Implement actual GitHub/Azure API calls yet (just output files)
- Over-engineer the caching system
- Create complex plugin architecture

## Implementation Order

1. Domain model (entities, enums)
2. Baseline management (load, save, compare)
3. CI runner (modes, parallel execution)
4. Output generators (SARIF, JUnit, Markdown)
5. CLI commands
6. Workflow templates
7. Tests

Start with domain model and baseline, then runner, then outputs. CLI last.
