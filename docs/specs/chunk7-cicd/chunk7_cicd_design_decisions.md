# Chunk 7: CI/CD Integration Design Decisions

## CI/CD Integration

**Document Version:** 1.0  
**Last Updated:** 2025-12-30

---

## Decision Log

### D1: Baseline-Based PR Checking

**Context:** How to determine if a PR introduces new violations vs pre-existing ones?

**Decision:** Maintain a baseline file on main branch, compare PR violations against it.

**Rationale:**
- Teams don't want to fix all existing violations before adopting
- New violations should block, existing ones are "tech debt"
- Clear signal: "you made it worse" vs "it was already broken"
- Enables gradual adoption

**Implementation:**
```python
class BaselineComparison:
    new_violations: List[Violation]      # Block PR
    fixed_violations: List[Violation]    # Celebrate!
    existing_violations: List[Violation] # Allow (for now)
```

**Alternative Considered:** Fail on any violation.
- Rejected: Adoption blocker for existing codebases.

---

### D2: SARIF as Primary Output Format

**Context:** Which output format for GitHub Code Scanning integration?

**Decision:** SARIF (Static Analysis Results Interchange Format) as primary.

**Rationale:**
- Industry standard for static analysis
- Native GitHub Code Scanning integration
- Rich metadata support (severity, fix hints, rule definitions)
- Enables "Security" tab integration in GitHub

**Implementation:**
- Generate SARIF 2.1.0 compliant output
- Include rule definitions for all checks
- Map severity levels: error → error, warning → warning

---

### D3: Parallel Check Execution

**Context:** CI environments are time-sensitive. How to optimize?

**Decision:** Run checks in parallel using ThreadPoolExecutor.

**Rationale:**
- Most checks are I/O bound (file reading) or CPU independent
- CI runners typically have multiple cores
- Can reduce check time by 2-4x

**Configuration:**
```yaml
ci:
  parallel:
    enabled: true
    max_workers: 4  # Or auto-detect from os.cpu_count()
```

**Caveats:**
- Some checks may have shared state - need to isolate
- Error handling must be thread-safe

---

### D4: Incremental Checking for PRs

**Context:** Full codebase checks are slow. PRs only change a few files.

**Decision:** Only run checks on files changed in PR (incremental mode).

**Rationale:**
- 10-100x faster for typical PRs
- Focuses feedback on what developer changed
- Still run full check on main branch merges

**Implementation:**
```python
changed_files = git_diff(base_ref, head_ref)
applicable_checks = filter_checks_by_paths(all_checks, changed_files)
```

**Edge Cases:**
- Config file changes → run all checks
- Contract file changes → run all checks
- Architecture changes → may need broader scope

---

### D5: PR Comment Updates (Not Duplicates)

**Context:** Multiple pushes to PR shouldn't create multiple comments.

**Decision:** Find and update existing AgentForge comment, or create if first time.

**Rationale:**
- Clean PR conversation thread
- Easy to see latest status
- No spam from CI bot

**Implementation:**
```javascript
const existingComment = comments.find(c => 
  c.body.includes('AgentForge Conformance Report')
);
if (existingComment) {
  updateComment(existingComment.id, newContent);
} else {
  createComment(newContent);
}
```

---

### D6: Fail on Errors Only (Default)

**Context:** Should warnings fail the build?

**Decision:** By default, only errors fail. Configurable.

**Rationale:**
- Errors = must fix before merge
- Warnings = should fix but not blocking
- Teams can customize based on maturity

**Configuration:**
```yaml
ci:
  fail_on:
    new_errors: true
    new_warnings: false  # Configurable to true
    total_errors_exceed: 10  # Absolute cap
```

---

### D7: Check Result Caching

**Context:** Repeated CI runs on same code waste time.

**Decision:** Cache check results by file hash + check ID.

**Rationale:**
- Same file + same check = same result
- Invalidates automatically on file change
- TTL of 24 hours to handle rule updates

**Cache Key:**
```python
cache_key = f"{check_id}_{file_sha256[:16]}"
```

**Storage:**
- Local: `.agentforge/cache/`
- CI: GitHub Actions cache, Azure Pipeline cache

---

### D8: Exit Codes for CI Integration

**Context:** CI systems use exit codes to determine pass/fail.

**Decision:** Structured exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success (no violations or only warnings) |
| 1 | Violations found (errors) |
| 2 | Configuration error |
| 3 | Runtime error |
| 4 | Baseline not found (when required) |

**Rationale:**
- CI can distinguish "failed checks" from "tool crashed"
- Enables different handling for different failures
- Standard practice for CLI tools

---

### D9: Platform Abstraction

**Context:** Support multiple CI platforms (GitHub, Azure, GitLab).

**Decision:** Core runner is platform-agnostic, with platform-specific integrations.

**Architecture:**
```
┌─────────────────────────────────┐
│         CIRunner (core)         │
│  - Run checks                   │
│  - Generate SARIF/JUnit/JSON    │
└─────────────┬───────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
 GitHub    Azure     GitLab
 - PR API  - PR API  - MR API
 - SARIF   - JUnit   - CodeQuality
```

**Rationale:**
- Core logic reusable
- Platform-specific features isolated
- Easy to add new platforms

---

### D10: Workflow Template Generation

**Context:** Users need to create CI workflow files manually.

**Decision:** `agentforge ci init` generates platform-specific workflow files.

**Rationale:**
- Reduces friction for adoption
- Best practices built in
- Templates can be customized

**Usage:**
```bash
agentforge ci init --platform github
# Creates .github/workflows/agentforge.yml

agentforge ci init --platform azure
# Creates azure-pipelines/agentforge.yml
```

---

### D11: Markdown Summary Format

**Context:** How to format PR comments for maximum usefulness?

**Decision:** Structured markdown with:
1. Summary table (pass/fail counts)
2. New violations (introduced in PR) - expanded
3. Fixed violations - one-liner celebration
4. Existing violations - collapsed details

**Rationale:**
- Most important info first (new violations)
- Celebrate wins (fixed violations)
- Don't hide tech debt but don't spam
- Collapsible sections for long lists

---

### D12: Auto-Update Baseline on Main

**Context:** When to update the baseline file?

**Decision:** Automatically update baseline when main branch is pushed.

**Rationale:**
- Baseline always reflects main branch state
- No manual intervention required
- Violations that slip through become "accepted" (intentional trade-off)

**Implementation:**
```yaml
# In GitHub Actions
- if: github.ref == 'refs/heads/main'
  run: |
    agentforge ci baseline save
    git add .agentforge/baseline.json
    git commit -m "Update conformance baseline"
    git push
```

**Alternative:** Manual baseline updates.
- Rejected: Too much friction, baseline would become stale.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CI/CD Pipeline                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │   Trigger   │  │   Checkout  │  │     AgentForge CI Run       │  │
│  │  (push/PR)  │──▶│   (git)    │──▶│                             │  │
│  └─────────────┘  └─────────────┘  │  ┌─────────────────────────┐│  │
│                                     │  │    Incremental Detect   ││  │
│                                     │  │    (changed files)      ││  │
│                                     │  └───────────┬─────────────┘│  │
│                                     │              │              │  │
│                                     │  ┌───────────▼─────────────┐│  │
│                                     │  │   Parallel Execution    ││  │
│                                     │  │   (with caching)        ││  │
│                                     │  └───────────┬─────────────┘│  │
│                                     │              │              │  │
│                                     │  ┌───────────▼─────────────┐│  │
│                                     │  │  Baseline Comparison    ││  │
│                                     │  │  (new vs existing)      ││  │
│                                     │  └───────────┬─────────────┘│  │
│                                     │              │              │  │
│                                     │  ┌───────────▼─────────────┐│  │
│                                     │  │   Output Generation     ││  │
│                                     │  │  - SARIF                ││  │
│                                     │  │  - JUnit                ││  │
│                                     │  │  - Markdown             ││  │
│                                     │  └─────────────────────────┘│  │
│                                     └─────────────────────────────┘  │
│                                                    │                 │
│          ┌─────────────────────────────────────────┼─────────┐       │
│          │                                         │         │       │
│          ▼                                         ▼         ▼       │
│  ┌───────────────┐                    ┌────────────────┐ ┌────────┐  │
│  │ Upload SARIF  │                    │  PR Comment    │ │ Exit   │  │
│  │ (Code Scan)   │                    │  (summary)     │ │ Code   │  │
│  └───────────────┘                    └────────────────┘ └────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| CI runner timeout | Incremental mode + parallel execution |
| Flaky checks | Caching + deterministic checks only |
| Token/API limits | Batch PR comments, rate limit handling |
| Baseline drift | Auto-update on main, hash-based comparison |
| Platform API changes | Abstraction layer, version pinning |

---

## Security Considerations

1. **PR from forks:** Limited token permissions, can't update baseline
2. **Secret handling:** No secrets in check output, use environment variables
3. **Artifact security:** SARIF files may contain file paths - OK for code scanning
4. **API tokens:** Use minimum required permissions

---

## Future Considerations

### Near-Term
- **GitLab support:** Add MR integration, Code Quality report
- **Bitbucket support:** PR comments, build status
- **Slack/Teams notifications:** Alert on failures

### Long-Term
- **Cloud service:** Hosted baseline storage, trend dashboards
- **GitHub App:** Richer integration than Actions
- **Policy as Code:** Define required checks via config, not UI
