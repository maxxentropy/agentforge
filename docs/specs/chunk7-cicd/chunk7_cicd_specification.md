# Chunk 7: CI/CD Integration

## Specification Document

**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2025-12-30  
**Depends On:** Chunk 3 (Conformance), Chunk 5 (Bridge)

---

## Executive Summary

CI/CD Integration enables AgentForge to run in automated pipelines, enforcing conformance checks on every commit, PR, and deployment. This closes the loop from development to continuous enforcement.

**Key Value Proposition:**
- Automated conformance checking in CI/CD
- PR comments with violation summaries
- Trend tracking over time
- Fail builds on critical violations

---

## 1. Problem Statement

### 1.1 Current State

AgentForge has powerful conformance checking, but:
- Runs only on developer machines
- No automated enforcement
- No integration with PR workflows
- No historical tracking across builds

### 1.2 Gap

- Developers can bypass checks
- No visibility for reviewers
- Violations discovered too late
- No enforcement at merge time

### 1.3 Solution

CI/CD integration that:
1. Runs conformance checks on every push/PR
2. Posts results as PR comments
3. Blocks merges on critical violations
4. Tracks trends over time
5. Integrates with existing CI systems (GitHub Actions, Azure DevOps)

---

## 2. Architecture

### 2.1 Components

```
tools/cicd/
├── __init__.py
├── runner.py              # CI-optimized conformance runner
├── reporter.py            # Generate CI-friendly reports
├── github_integration.py  # GitHub Actions + PR comments
├── azure_integration.py   # Azure DevOps integration
├── baseline.py            # Baseline management for PRs
└── config.py              # CI configuration loader

.github/
└── workflows/
    └── agentforge.yml     # GitHub Actions workflow template

azure-pipelines/
└── agentforge.yml         # Azure DevOps template
```

### 2.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AgentForge CI Runner                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Discover  │  │   Bridge    │  │     Conformance         │  │
│  │  (Chunk 4)  │──▶  (Chunk 5)  │──▶     (Chunk 3)           │  │
│  │             │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └───────────┬─────────────┘  │
│                                                 │                │
│                                                 ▼                │
│                                    ┌─────────────────────────┐  │
│                                    │   CI Reporter           │  │
│                                    │  - SARIF output         │  │
│                                    │  - JUnit XML            │  │
│                                    │  - PR comment           │  │
│                                    │  - Exit code            │  │
│                                    └─────────────┬───────────┘  │
└──────────────────────────────────────────────────┼──────────────┘
                                                   │
                       ┌───────────────────────────┼───────────────┐
                       │                           │               │
                       ▼                           ▼               ▼
              ┌─────────────────┐     ┌─────────────────┐  ┌─────────────┐
              │  GitHub Actions │     │   Azure DevOps  │  │   GitLab    │
              │  - Check status │     │   - Pipeline    │  │   (future)  │
              │  - PR comment   │     │   - PR policy   │  │             │
              │  - Code scanning│     │                 │  │             │
              └─────────────────┘     └─────────────────┘  └─────────────┘
```

---

## 3. CI Runner

### 3.1 CI-Optimized Execution

```python
class CIRunner:
    """
    Optimized runner for CI/CD environments.
    
    Features:
    - Parallel check execution
    - Incremental checking (only changed files)
    - Caching for faster subsequent runs
    - Machine-readable output formats
    """
    
    def run(
        self,
        mode: Literal["full", "incremental", "pr"],
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> CIResult:
        """
        Run conformance checks in CI mode.
        
        Args:
            mode: 
                - full: Check entire codebase
                - incremental: Check only changed files since base_ref
                - pr: Check changes in PR, compare to baseline
            base_ref: Base branch/commit for comparison
            head_ref: Head branch/commit (default: current)
        """
        pass
```

### 3.2 Incremental Checking

For PRs, only check files that changed:

```python
def get_changed_files(base_ref: str, head_ref: str) -> List[Path]:
    """Get files changed between base and head."""
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, head_ref],
        capture_output=True, text=True
    )
    return [Path(f) for f in result.stdout.strip().split("\n") if f]

def filter_checks_for_files(
    checks: List[Check], 
    changed_files: List[Path]
) -> List[Check]:
    """Filter checks to only those applicable to changed files."""
    applicable = []
    for check in checks:
        if check.applies_to_any(changed_files):
            applicable.append(check)
    return applicable
```

### 3.3 Baseline Comparison

Compare PR violations against baseline (main branch):

```python
@dataclass
class BaselineComparison:
    """Comparison of PR violations against baseline."""
    new_violations: List[Violation]      # Introduced in this PR
    fixed_violations: List[Violation]    # Fixed by this PR
    existing_violations: List[Violation] # Pre-existing, unchanged
    
    @property
    def introduces_violations(self) -> bool:
        return len(self.new_violations) > 0
    
    @property
    def net_change(self) -> int:
        return len(self.new_violations) - len(self.fixed_violations)
```

---

## 4. Output Formats

### 4.1 SARIF (Static Analysis Results Interchange Format)

GitHub Code Scanning compatible:

```json
{
  "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "AgentForge",
          "version": "1.0.0",
          "rules": [
            {
              "id": "AF001",
              "name": "cqrs-command-naming",
              "shortDescription": { "text": "CQRS Command Naming" },
              "defaultConfiguration": { "level": "error" }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "AF001",
          "level": "error",
          "message": { "text": "Command class should end with 'Command'" },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": { "uri": "src/Application/CreateOrder.cs" },
                "region": { "startLine": 10, "startColumn": 1 }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### 4.2 JUnit XML

For Azure DevOps and other CI systems:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="AgentForge Conformance" tests="15" failures="3" errors="0">
  <testsuite name="patterns" tests="10" failures="2">
    <testcase name="cqrs-command-naming" classname="patterns">
      <failure message="Command class should end with 'Command'">
        File: src/Application/CreateOrder.cs
        Line: 10
      </failure>
    </testcase>
    <testcase name="repository-naming" classname="patterns"/>
  </testsuite>
  <testsuite name="architecture" tests="5" failures="1">
    <testcase name="domain-isolation" classname="architecture">
      <failure message="Domain layer imports from Infrastructure">
        File: src/Domain/Order.cs
        Line: 5
      </failure>
    </testcase>
  </testsuite>
</testsuites>
```

### 4.3 Markdown Summary

For PR comments:

```markdown
## AgentForge Conformance Report

### Summary
| Status | Count |
|--------|-------|
| ✅ Passed | 12 |
| ❌ Failed | 3 |
| ⚠️ Warnings | 2 |

### New Violations (introduced in this PR)
| Rule | File | Line | Message |
|------|------|------|---------|
| cqrs-command-naming | src/Application/CreateOrder.cs | 10 | Command should end with 'Command' |

### Fixed Violations 🎉
- `repository-naming` in `src/Infrastructure/OrderRepo.cs`

### Pre-existing Violations
<details>
<summary>2 violations (click to expand)</summary>

| Rule | File | Message |
|------|------|---------|
| domain-isolation | src/Domain/Order.cs | Imports Infrastructure |

</details>

---
*Powered by [AgentForge](https://github.com/maxxentropy/agentforge)*
```

---

## 5. GitHub Actions Integration

### 5.1 Workflow Template

```yaml
# .github/workflows/agentforge.yml
name: AgentForge Conformance

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

permissions:
  contents: read
  pull-requests: write
  security-events: write  # For SARIF upload

jobs:
  conformance:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for baseline comparison
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install AgentForge
        run: pip install agentforge
      
      - name: Run Conformance Checks
        id: conformance
        run: |
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            agentforge ci run \
              --mode pr \
              --base-ref ${{ github.event.pull_request.base.sha }} \
              --head-ref ${{ github.event.pull_request.head.sha }} \
              --output-sarif results.sarif \
              --output-markdown summary.md
          else
            agentforge ci run \
              --mode full \
              --output-sarif results.sarif
          fi
        continue-on-error: true
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
        if: always()
      
      - name: Comment on PR
        uses: actions/github-script@v7
        if: github.event_name == 'pull_request'
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('summary.md', 'utf8');
            
            // Find existing comment
            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });
            
            const botComment = comments.find(c => 
              c.user.type === 'Bot' && 
              c.body.includes('AgentForge Conformance Report')
            );
            
            if (botComment) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: botComment.id,
                body: summary
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: summary
              });
            }
      
      - name: Fail on New Violations
        if: steps.conformance.outcome == 'failure'
        run: |
          echo "::error::Conformance check failed with new violations"
          exit 1
```

### 5.2 GitHub Action (Reusable)

```yaml
# action.yml (for marketplace)
name: 'AgentForge Conformance'
description: 'Run AgentForge conformance checks on your codebase'

inputs:
  mode:
    description: 'Check mode: full, incremental, or pr'
    required: false
    default: 'pr'
  fail-on-violations:
    description: 'Fail the build if violations are found'
    required: false
    default: 'true'
  comment-on-pr:
    description: 'Post results as PR comment'
    required: false
    default: 'true'

outputs:
  violations:
    description: 'Number of violations found'
  new-violations:
    description: 'Number of new violations (PR mode)'
  fixed-violations:
    description: 'Number of fixed violations (PR mode)'

runs:
  using: 'composite'
  steps:
    - name: Install AgentForge
      shell: bash
      run: pip install agentforge
    
    - name: Run Checks
      shell: bash
      run: agentforge ci run --mode ${{ inputs.mode }} --output-json results.json
    
    # ... rest of implementation
```

---

## 6. Azure DevOps Integration

### 6.1 Pipeline Template

```yaml
# azure-pipelines/agentforge.yml
trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
    displayName: 'Use Python 3.11'

  - script: pip install agentforge
    displayName: 'Install AgentForge'

  - script: |
      if [ -n "$(System.PullRequest.SourceBranch)" ]; then
        agentforge ci run \
          --mode pr \
          --base-ref $(System.PullRequest.TargetBranch) \
          --output-junit results.xml \
          --output-markdown summary.md
      else
        agentforge ci run \
          --mode full \
          --output-junit results.xml
      fi
    displayName: 'Run Conformance Checks'
    continueOnError: true

  - task: PublishTestResults@2
    inputs:
      testResultsFormat: 'JUnit'
      testResultsFiles: 'results.xml'
      testRunTitle: 'AgentForge Conformance'
    displayName: 'Publish Test Results'

  - task: PowerShell@2
    condition: eq(variables['Build.Reason'], 'PullRequest')
    inputs:
      targetType: 'inline'
      script: |
        $summary = Get-Content summary.md -Raw
        $url = "$(System.CollectionUri)$(System.TeamProject)/_apis/git/repositories/$(Build.Repository.ID)/pullRequests/$(System.PullRequest.PullRequestId)/threads?api-version=7.0"
        
        $body = @{
          comments = @(
            @{
              parentCommentId = 0
              content = $summary
              commentType = 1
            }
          )
          status = 1
        } | ConvertTo-Json -Depth 10
        
        Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" -Headers @{
          Authorization = "Bearer $(System.AccessToken)"
        }
    displayName: 'Comment on PR'
```

### 6.2 Build Policy

Configure as a required check:

```yaml
# Branch policy configuration (via Azure DevOps API or UI)
policies:
  - type: Build
    settings:
      buildDefinitionId: <agentforge-pipeline-id>
      displayName: "AgentForge Conformance"
      manualQueueOnly: false
      queueOnSourceUpdateOnly: true
      validDuration: 720  # 12 hours
```

---

## 7. CLI Commands

### 7.1 CI-Specific Commands

```bash
# Run in CI mode
agentforge ci run [OPTIONS]

Options:
  --mode [full|incremental|pr]  Check mode (default: full)
  --base-ref TEXT               Base reference for comparison
  --head-ref TEXT               Head reference (default: HEAD)
  --output-sarif FILE           Output SARIF file
  --output-junit FILE           Output JUnit XML file
  --output-markdown FILE        Output Markdown summary
  --output-json FILE            Output JSON results
  --fail-on [error|warning|any] When to fail (default: error)
  --baseline FILE               Use baseline file for comparison
  --save-baseline FILE          Save current state as baseline
  --parallel / --no-parallel    Run checks in parallel (default: true)

# Generate baseline
agentforge ci baseline save [--output FILE]

# Compare to baseline
agentforge ci baseline compare --baseline FILE

# Generate workflow files
agentforge ci init [--platform github|azure|gitlab]
```

### 7.2 Examples

```bash
# Full check (e.g., on main branch)
agentforge ci run --mode full --output-sarif results.sarif

# PR check with baseline comparison
agentforge ci run \
  --mode pr \
  --base-ref origin/main \
  --output-markdown summary.md \
  --fail-on error

# Save baseline for current main branch
agentforge ci baseline save --output .agentforge/baseline.json

# Generate GitHub Actions workflow
agentforge ci init --platform github
# Creates .github/workflows/agentforge.yml

# Incremental check (only changed files)
agentforge ci run \
  --mode incremental \
  --base-ref HEAD~5 \
  --output-junit results.xml
```

---

## 8. Configuration

### 8.1 CI Configuration File

```yaml
# .agentforge/ci.yaml
schema_version: "1.0"

ci:
  # Default mode for CI runs
  default_mode: pr
  
  # Fail conditions
  fail_on:
    new_errors: true
    new_warnings: false
    total_errors_exceed: 10
  
  # Checks to skip in CI (for performance)
  skip_checks: []
  
  # Checks that are warnings-only in CI
  warn_only:
    - docstrings-required
    - type-hints
  
  # Parallel execution
  parallel:
    enabled: true
    max_workers: 4
  
  # Caching
  cache:
    enabled: true
    directory: .agentforge/cache
    ttl_hours: 24
  
  # Baseline configuration
  baseline:
    file: .agentforge/baseline.json
    auto_update_on_main: true

# Platform-specific settings
github:
  post_pr_comment: true
  upload_sarif: true
  required_check: true

azure:
  post_pr_comment: true
  publish_test_results: true
  pipeline_decorator: true
```

### 8.2 Environment Variables

```bash
# GitHub
GITHUB_TOKEN          # For PR comments (auto-provided in Actions)
GITHUB_REPOSITORY     # owner/repo
GITHUB_EVENT_NAME     # push, pull_request, etc.

# Azure DevOps
SYSTEM_ACCESSTOKEN    # For API calls
BUILD_REPOSITORY_ID   # Repository ID
SYSTEM_PULLREQUEST_PULLREQUESTID  # PR ID

# AgentForge
AGENTFORGE_CI_MODE    # Override default mode
AGENTFORGE_FAIL_ON    # Override fail conditions
AGENTFORGE_NO_CACHE   # Disable caching
```

---

## 9. Baseline Management

### 9.1 Baseline File Format

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-12-30T15:00:00Z",
  "commit": "abc123def456",
  "branch": "main",
  "summary": {
    "total_checks": 25,
    "passing": 22,
    "failing": 3
  },
  "violations": [
    {
      "check_id": "domain-isolation",
      "file": "src/Domain/Order.cs",
      "line": 5,
      "hash": "sha256:abc123"
    }
  ]
}
```

### 9.2 Baseline Strategy

```
main branch (protected)
     │
     │  Baseline saved automatically after merge
     ▼
┌─────────────────────────────────────────┐
│  .agentforge/baseline.json              │
│  - Current "accepted" violations        │
│  - Updated on each main merge           │
└────────────────────┬────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
  PR #1           PR #2           PR #3
  Compare to      Compare to      Compare to
  baseline        baseline        baseline
     │               │               │
     ▼               ▼               ▼
  +2 new         -1 fixed        0 change
  violations     violation       (OK)
  (FAIL)         (PASS)          (PASS)
```

---

## 10. Performance Optimization

### 10.1 Incremental Checking

Only check files that changed:

```python
def get_applicable_checks(
    changed_files: List[Path],
    all_checks: List[Check]
) -> List[Check]:
    """Filter checks to only those affected by changed files."""
    applicable = []
    
    for check in all_checks:
        # Check if any changed file matches the check's applies_to paths
        for pattern in check.applies_to.paths:
            for file in changed_files:
                if file.match(pattern):
                    applicable.append(check)
                    break
    
    return applicable
```

### 10.2 Parallel Execution

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_checks_parallel(
    checks: List[Check],
    max_workers: int = 4
) -> List[CheckResult]:
    """Run checks in parallel for faster CI execution."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check.run): check for check in checks}
        
        for future in as_completed(futures):
            check = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(CheckResult(
                    check_id=check.id,
                    status="error",
                    error=str(e)
                ))
    
    return results
```

### 10.3 Caching

```python
class CheckCache:
    """Cache check results by file hash."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, check: Check, file: Path) -> str:
        """Generate cache key from check ID + file hash."""
        file_hash = hashlib.sha256(file.read_bytes()).hexdigest()[:16]
        return f"{check.id}_{file_hash}"
    
    def get(self, key: str) -> Optional[CheckResult]:
        """Get cached result if exists and not expired."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            if datetime.fromisoformat(data["cached_at"]) > datetime.now() - timedelta(hours=24):
                return CheckResult.from_dict(data["result"])
        return None
    
    def set(self, key: str, result: CheckResult) -> None:
        """Cache a result."""
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({
            "cached_at": datetime.now().isoformat(),
            "result": result.to_dict()
        }))
```

---

## 11. Success Criteria

### 11.1 Functional Requirements

- [ ] `agentforge ci run --mode full` runs all checks
- [ ] `agentforge ci run --mode pr` compares to baseline
- [ ] SARIF output uploads to GitHub Code Scanning
- [ ] JUnit output publishes to Azure DevOps
- [ ] PR comments show summary with diff from baseline
- [ ] Exit code reflects pass/fail status

### 11.2 Performance Requirements

- [ ] Incremental check runs in < 30 seconds for typical PR
- [ ] Full check runs in < 5 minutes for medium codebase
- [ ] Parallel execution uses available cores efficiently
- [ ] Caching reduces repeated check time by > 50%

### 11.3 Integration Requirements

- [ ] GitHub Actions workflow template works out of box
- [ ] Azure DevOps pipeline template works out of box
- [ ] Branch protection can require AgentForge check
- [ ] PR comments update on subsequent pushes (don't create duplicates)

---

## 12. Implementation Plan

### Phase 1: Core CI Runner (Day 1-2)
- CI-optimized runner with mode selection
- Incremental file detection
- Parallel execution

### Phase 2: Output Formats (Day 2-3)
- SARIF generation
- JUnit XML generation
- Markdown summary

### Phase 3: Baseline Management (Day 3)
- Baseline save/load
- PR comparison
- Violation diffing

### Phase 4: GitHub Integration (Day 4)
- Workflow template
- PR comment posting
- SARIF upload

### Phase 5: Azure DevOps Integration (Day 5)
- Pipeline template
- Test results publishing
- PR comment API

### Phase 6: CLI & Config (Day 5-6)
- `agentforge ci` commands
- Configuration file support
- Init command for workflow generation

### Phase 7: Testing & Documentation (Day 6-7)
- Integration tests with mock CI
- Template testing
- User documentation

---

## Appendix A: Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | Violations found (errors) |
| 2 | Configuration error |
| 3 | Runtime error |
| 4 | Baseline not found (when required) |

## Appendix B: Comparison to Other Tools

| Feature | AgentForge CI | ESLint | SonarQube |
|---------|---------------|--------|-----------|
| Custom pattern checks | ✅ | ✅ | ✅ |
| Architecture enforcement | ✅ | ❌ | ✅ |
| Auto-generate from discovery | ✅ | ❌ | ❌ |
| PR baseline comparison | ✅ | ❌ | ✅ |
| SARIF output | ✅ | ✅ | ❌ |
| Self-hosted | ✅ | ✅ | ✅ |
| Cloud option | Future | ❌ | ✅ |
