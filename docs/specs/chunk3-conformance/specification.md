# Per-Repository Conformance Tracking System

**Version:** 1.0
**Status:** draft
**Date:** 2025-12-30

---

## 1. Overview

### 1.1 Purpose

Provide a comprehensive per-repository conformance tracking system that stores
conformance state, violations, exemptions, and historical trends in a structured
.agentforge/ directory. This enables continuous monitoring of how well a codebase
adheres to defined architectural contracts, answering: How correct is this codebase
right now? What violations exist? Are we improving over time?

### 1.2 Background

This is Chunk 3 of the AgentForge workspace architecture. It builds upon:
- Chunk 1 (Workspace Config): repo.yaml lives in .agentforge/
- Chunk 2 (Contract System): contracts define what to check
- Phase 1 (Verification Engine): runs the checks, produces results

The conformance system bridges verification output to persistent, trackable state
that enables trend analysis, exemption management, and CI/CD integration.

### 1.3 Scope

**In Scope:**
- .agentforge/ directory structure within each repository
- conformance_report.yaml schema definition
- codebase_profile.yaml schema definition
- violations/ directory and violation record schema
- exemptions/ directory and exemption schema
- history/ directory and snapshot schema
- CLI commands for conformance operations
- Integration points with Verification Engine and Contract System

**Out of Scope:**
- Actual violation detection logic (Phase 1 Verification Engine responsibility)
- Brownfield discovery logic (Chunk 4 responsibility)
- Cross-repo aggregation (Chunk 7)
- CI/CD integration details (Chunk 8)

### 1.4 Assumptions

- Severity levels align with Chunk 2 (Contract System) using blocker, critical, major, minor, info
- All schemas use JSON Schema draft-07 for compatibility with existing schemas
- Violation identity based on hash of (contract_id + check_id + file_path + line_number + rule_id)
- Daily history snapshots with 90-day default retention
- Exemptions require approved_by field for audit trail
- Expired exemptions auto-convert to violations with status 'exemption_expired'
- Smart merge for incremental runs - update only checked files/contracts, preserve others

### 1.5 Constraints

- All conformance YAML files SHALL include schema_version field with pattern "^\d+\.\d+$"
- Individual files per violation for git-friendly tracking
- History retention policy required to prevent unbounded growth
- Atomic file operations required to handle concurrent access
- IDs SHALL use lowercase with hyphens pattern "^[a-z][a-z0-9_-]*$"

---

## 2. Requirements

### 2.1 Functional Requirements

**FR-001: Directory Structure Creation**

*Priority:* MUST

The system SHALL create and maintain the following directory structure within
each repository:

.agentforge/
├── repo.yaml                    # Repository configuration (Chunk 1)
├── conformance_report.yaml      # Current conformance state
├── codebase_profile.yaml        # Extracted codebase metadata
├── local.yaml                   # Machine-specific overrides (gitignored)
├── violations/                  # Individual violation records
│   └── V-{hash}.yaml           # One file per violation
├── exemptions/                  # Approved exemptions
│   └── {exemption-id}.yaml     # One file per exemption
└── history/                     # Historical snapshots
    └── YYYY-MM-DD.yaml         # One file per day

*Rationale:* Single source of truth for all conformance data. Git-friendly structure enables
tracking changes over time via commits.


*Acceptance Criteria:*

```gherkin
Scenario: AC-001
  Given A repository without .agentforge/ directory
  When conformance init command is executed
  Then All required directories and placeholder files are created

Scenario: AC-002
  Given A repository with existing .agentforge/ directory
  When conformance check command is executed
  Then Missing subdirectories are created without affecting existing files

```

**FR-002: Conformance Report Generation**

*Priority:* MUST

The system SHALL generate conformance_report.yaml containing:
- schema_version: Version of the conformance report schema
- generated_at: ISO 8601 timestamp of report generation
- run_id: Unique identifier for this verification run (UUID v4)
- run_type: Either 'full' or 'incremental'
- summary: Aggregated counts by status (passed, failed, exempted, stale)
- by_severity: Breakdown of violations by severity level
- by_contract: Breakdown of violations by contract_id
- contracts_checked: List of contract IDs included in this run
- files_checked: Count of files analyzed
- stale_count: Number of violations not re-checked this run
- trend: Comparison with previous run (delta for each count)

*Rationale:* Single-file summary enables quick assessment of conformance state without
parsing individual violation files.


*Acceptance Criteria:*

```gherkin
Scenario: AC-003
  Given Verification run completes with 10 failures, 5 exempted, 85 passed
  When Conformance report is generated
  Then Summary shows total=100, passed=85, failed=10, exempted=5

Scenario: AC-004
  Given Previous run had 15 failures, current run has 10 failures
  When Conformance report is generated
  Then Trend shows failed_delta=-5

Scenario: AC-005
  Given Incremental run checks only 'naming-conventions' contract
  When Conformance report is generated
  Then contracts_checked contains only 'naming-conventions'

```

**FR-003: Violation Record Management**

*Priority:* MUST

The system SHALL create individual violation files with the following fields:
- violation_id: Hash-based ID (V-{sha256-12-chars})
- contract_id: Reference to the contract that was violated
- check_id: Specific check within the contract
- severity: One of blocker, critical, major, minor, info
- file_path: Relative path to the violating file
- line_number: Line number of the violation (nullable for file-level violations)
- column_number: Column number if available (nullable)
- message: Human-readable description of the violation
- fix_hint: Suggested remediation (nullable)
- code_snippet: Relevant code context (nullable, max 5 lines)
- detected_at: ISO 8601 timestamp of first detection
- last_seen_at: ISO 8601 timestamp of most recent detection
- status: One of open, resolved, exemption_expired, stale
- resolution: Details if resolved (nullable)

*Rationale:* Individual files enable granular git history for violation lifecycle.
Hash-based IDs ensure stable identity across runs.


*Acceptance Criteria:*

```gherkin
Scenario: AC-006
  Given Same violation detected in two consecutive runs
  When Violation records are compared
  Then Both runs reference the same violation_id

Scenario: AC-007
  Given Violation exists but file/contract not checked in incremental run
  When Conformance merge completes
  Then Violation status is set to 'stale'

Scenario: AC-008
  Given Previously detected violation no longer fails check
  When Full verification run completes
  Then Violation status is updated to 'resolved' with resolved_at timestamp

```

**FR-004: Violation Identity Calculation**

*Priority:* MUST

The system SHALL calculate violation identity using SHA-256 hash of:
- contract_id
- check_id
- file_path (normalized with forward slashes)
- line_number (as string, or 'file' for file-level violations)
- rule_id (if applicable, else empty string)

The violation_id format SHALL be: V-{first-12-chars-of-hash}

In case of hash collision (same 12-char prefix), the system SHALL append
a numeric suffix: V-{hash}-1, V-{hash}-2, etc.

*Rationale:* Composite key provides high uniqueness. Truncated hash balances readability
with collision resistance.


*Acceptance Criteria:*

```gherkin
Scenario: AC-009
  Given Violation at file.py:42 for check 'no-print-statements'
  When Violation ID is calculated twice
  Then Both calculations produce identical violation_id

Scenario: AC-010
  Given Two violations produce same 12-char hash prefix
  When Second violation is stored
  Then Second violation gets suffix '-1' appended to ID

```

**FR-005: Exemption Management**

*Priority:* MUST

The system SHALL support exemptions with the following fields:
- id: Unique exemption identifier (lowercase with hyphens)
- contract_id: Contract being exempted
- check_ids: List of specific checks exempted (or '*' for all)
- reason: Justification for the exemption
- approved_by: Username, email, or 'self' for acknowledged debt
- approved_date: ISO 8601 date of approval
- expires: Optional ISO 8601 date when exemption expires
- review_date: Optional date to reconsider exemption
- status: One of active, expired, resolved, under_review
- scope: Definition of what is covered:
  - type: One of check_id, file_pattern, violation_id, global
  - patterns: List of glob patterns (for file_pattern type)
  - violation_ids: List of specific violation IDs (for violation_id type)
  - lines: Optional line range restrictions

*Rationale:* Exemptions enable pragmatic handling of known debt while maintaining
visibility and accountability.


*Acceptance Criteria:*

```gherkin
Scenario: AC-011
  Given Exemption with pattern 'tests/**/*.py' for check 'docstring-required'
  When Violation in 'tests/unit/test_foo.py' is evaluated
  Then Violation is marked as exempted with exemption_id reference

Scenario: AC-012
  Given Exemption with expires='2025-01-15' and current date is '2025-01-16'
  When Conformance check runs
  Then Exemption status is set to 'expired' and covered violations become open

```

**FR-006: Exemption Expiry Handling**

*Priority:* MUST

The system SHALL handle exemption expiry as follows:
1. During conformance check, validate all exemption expiry dates
2. If exemption.expires < current_date:
   - Set exemption.status to 'expired'
   - Find all violations covered by this exemption
   - Update violation.status to 'exemption_expired'
   - Set violation.exemption_expired_at timestamp
3. Generate warning in conformance report for expired exemptions

*Rationale:* Expired exemptions must surface as violations to prevent silent accumulation
of technical debt.


*Acceptance Criteria:*

```gherkin
Scenario: AC-013
  Given Exemption 'legacy-console-logging' expires yesterday
  When Conformance check runs
  Then All 5 violations it covered now have status 'exemption_expired'

Scenario: AC-014
  Given Exemption expires today
  When Conformance check runs at 00:00:01
  Then Exemption is still active (expires means end of day)

```

**FR-007: History Snapshot Generation**

*Priority:* MUST

The system SHALL generate daily history snapshots containing:
- schema_version: Version of the history schema
- date: ISO 8601 date (YYYY-MM-DD)
- generated_at: ISO 8601 timestamp
- summary:
  - total_checks: Number of checks executed
  - passed: Count of passed checks
  - failed: Count of failed checks
  - exempted: Count of exempted violations
  - stale: Count of stale violations
- by_severity: Counts per severity level
- by_contract: Counts per contract_id
- files_analyzed: Total files checked
- contracts_checked: List of contract IDs

Only one snapshot per day SHALL exist. Later runs on same day SHALL
overwrite the previous snapshot.

*Rationale:* Summary-only snapshots enable trend visualization without disk bloat.
Daily granularity balances detail with storage efficiency.


*Acceptance Criteria:*

```gherkin
Scenario: AC-015
  Given Conformance check runs on 2025-01-15
  When History snapshot is saved
  Then File .agentforge/history/2025-01-15.yaml is created

Scenario: AC-016
  Given Two conformance runs on same day
  When Second run completes
  Then History file contains data from second run only

```

**FR-008: History Retention Policy**

*Priority:* MUST

The system SHALL enforce history retention policy:
- Default retention: 90 days
- Configurable via repo.yaml conformance.history_retention_days
- Minimum allowed: 7 days
- Maximum allowed: 365 days

During conformance check, the system SHALL:
1. Calculate cutoff date (today - retention_days)
2. Delete history files older than cutoff date
3. Log count of pruned files

*Rationale:* Prevents unbounded growth of history directory while maintaining
sufficient data for trend analysis.


*Acceptance Criteria:*

```gherkin
Scenario: AC-017
  Given Retention set to 30 days and 50 history files exist
  When Conformance check runs
  Then Files older than 30 days are deleted

Scenario: AC-018
  Given User sets history_retention_days to 3
  When Configuration is validated
  Then Error: minimum retention is 7 days

```

**FR-009: Incremental Run Smart Merge**

*Priority:* MUST

The system SHALL support incremental verification runs that:
1. Accept list of contracts and/or files to check
2. Run verification only for specified scope
3. Merge results with existing conformance state:
   - Update violations for checked files/contracts
   - Mark violations for unchecked files/contracts as 'stale'
   - Preserve stale violations (do not delete)
   - Update conformance_report with run_type='incremental'
   - Record contracts_checked and files_checked in report
4. Full run (no scope restriction) SHALL:
   - Clear stale status from all violations
   - Delete violations for files that no longer exist
   - Delete violations for checks that no longer fail

*Rationale:* Incremental runs enable fast feedback during development while
maintaining complete conformance picture.


*Acceptance Criteria:*

```gherkin
Scenario: AC-019
  Given 100 existing violations, incremental run checks 10 files
  When Incremental run finds 2 new violations in checked files
  Then Total violations = 102 (100 preserved + 2 new)

Scenario: AC-020
  Given Violation V-abc123 exists for unchecked file
  When Incremental run completes
  Then V-abc123 status is 'stale', not deleted

Scenario: AC-021
  Given Full run finds violation V-abc123 no longer fails
  When Full run completes
  Then V-abc123 status is 'resolved'

```

**FR-010: Codebase Profile Extraction**

*Priority:* SHOULD

The system SHALL generate codebase_profile.yaml containing:
- schema_version: Version of the profile schema
- generated_at: ISO 8601 timestamp
- languages: List of detected programming languages with percentages
- frameworks: List of detected frameworks/libraries
- structure:
  - root_path: Repository root
  - layers: Identified architectural layers (if detectable)
  - key_directories: Important directories with descriptions
  - entry_points: Main entry point files
- patterns_detected:
  - naming_conventions: Detected naming patterns
  - file_organization: How files are organized
  - test_structure: Test file locations and naming
- dependencies:
  - direct: List of direct dependencies
  - dev: List of development dependencies
- metrics:
  - total_files: Count of source files
  - total_lines: Approximate lines of code
  - by_language: Breakdown by language

Profile MAY be auto-detected or manually curated. Auto-detected fields
SHALL include confidence score.

*Rationale:* Codebase profile provides context for contracts and enables
intelligent defaults for new repositories.


*Acceptance Criteria:*

```gherkin
Scenario: AC-022
  Given Python repository with pytest tests in tests/ directory
  When Codebase profile is generated
  Then languages includes 'Python', test_structure shows 'tests/'

Scenario: AC-023
  Given Auto-detected naming convention with 80% confidence
  When Profile is saved
  Then Field includes 'confidence: 0.8' and 'source: auto-detected'

```

**FR-011: Conformance CLI - Check Command**

*Priority:* MUST

The system SHALL provide CLI command:

agentforge conformance check [OPTIONS]

Options:
  --contracts LIST    Comma-separated contract IDs to check
  --files LIST        Comma-separated file paths/patterns to check
  --full              Force full run (clear stale violations)
  --no-history        Skip history snapshot generation
  --exit-code         Return non-zero exit code based on severity threshold
  --severity-threshold LEVEL  Minimum severity to cause non-zero exit (default: blocker)

The command SHALL:
1. Load contracts from Chunk 2 Contract System
2. Run verification via Phase 1 Verification Engine
3. Transform results into violation records
4. Apply exemption matching
5. Merge with existing conformance state
6. Generate conformance_report.yaml
7. Generate history snapshot (unless --no-history)
8. Return exit code based on --severity-threshold

*Rationale:* Primary entry point for conformance verification. Supports both CI/CD
and interactive development workflows.


*Acceptance Criteria:*

```gherkin
Scenario: AC-024
  Given 3 blocker violations exist, threshold is 'critical'
  When conformance check --exit-code runs
  Then Exit code is non-zero (blockers exceed threshold)

Scenario: AC-025
  Given Only 'minor' violations exist, threshold is 'major'
  When conformance check --exit-code runs
  Then Exit code is 0

```

**FR-012: Conformance CLI - Report Command**

*Priority:* MUST

The system SHALL provide CLI command:

agentforge conformance report [OPTIONS]

Options:
  --format FORMAT     Output format: text, json, yaml (default: text)
  --verbose           Include violation details
  --by-severity       Group output by severity
  --by-contract       Group output by contract

The command SHALL display current conformance state from
conformance_report.yaml without running new checks.

*Rationale:* Quick access to current conformance state without re-running verification.


*Acceptance Criteria:*

```gherkin
Scenario: AC-026
  Given conformance_report.yaml shows 5 blockers, 10 majors
  When conformance report --format text runs
  Then Output shows summary with blocker and major counts

Scenario: AC-027
  Given conformance report --by-severity --verbose
  When Command runs
  Then Output groups violations by severity with full details

```

**FR-013: Conformance CLI - Violations Command**

*Priority:* MUST

The system SHALL provide CLI command:

agentforge conformance violations [SUBCOMMAND] [OPTIONS]

Subcommands:
  list                List all violations
    --status STATUS   Filter by status (open, resolved, stale, exemption_expired)
    --severity LEVEL  Filter by severity
    --contract ID     Filter by contract
    --file PATTERN    Filter by file pattern
    --limit N         Limit results (default: 50)
  
  show ID             Show detailed violation record
  
  resolve ID          Mark violation as resolved
    --reason TEXT     Resolution reason (required)
  
  prune               Remove resolved/stale violations
    --older-than DAYS Only prune violations older than N days (default: 30)
    --dry-run         Show what would be pruned without deleting

*Rationale:* Granular violation management for investigation and cleanup.


*Acceptance Criteria:*

```gherkin
Scenario: AC-028
  Given 20 open violations, 10 resolved
  When conformance violations list --status open
  Then Only 20 open violations shown

Scenario: AC-029
  Given Violation V-abc123 exists
  When conformance violations resolve V-abc123 --reason 'Fixed in PR#456'
  Then Violation status is 'resolved', resolution contains reason

```

**FR-014: Conformance CLI - History Command**

*Priority:* SHOULD

The system SHALL provide CLI command:

agentforge conformance history [OPTIONS]

Options:
  --days N            Show last N days (default: 30)
  --format FORMAT     Output format: text, json, yaml, csv
  --metric METRIC     Specific metric to track: total, failed, passed, exempted

The command SHALL display trend data from history/ directory.

*Rationale:* Trend visualization helps teams track improvement over time.


*Acceptance Criteria:*

```gherkin
Scenario: AC-030
  Given 30 days of history snapshots exist
  When conformance history --days 7 --metric failed
  Then Output shows failed count for each of last 7 days

```

**FR-015: Conformance CLI - Init Command**

*Priority:* MUST

The system SHALL provide CLI command:

agentforge conformance init [OPTIONS]

Options:
  --force             Overwrite existing conformance files

The command SHALL:
1. Create .agentforge/ directory if not exists
2. Create violations/, exemptions/, history/ subdirectories
3. Create .gitkeep files in empty directories
4. Generate initial codebase_profile.yaml (auto-detected)
5. Generate initial conformance_report.yaml (empty state)
6. Add local.yaml to .gitignore if not present

*Rationale:* Easy onboarding for new repositories.


*Acceptance Criteria:*

```gherkin
Scenario: AC-031
  Given Repository without .agentforge/ directory
  When conformance init runs
  Then All directories and initial files are created

Scenario: AC-032
  Given .agentforge/ already exists with violations
  When conformance init runs (without --force)
  Then Error: .agentforge/ already exists, use --force to reinitialize

```

**FR-016: Severity Mapping**

*Priority:* MUST

The system SHALL map between Contract System and Verification Engine severity levels:

Contract Severity → Conformance Severity
- error           → blocker
- warning         → major
- info            → minor

Verification Severity → Conformance Severity
- BLOCKING        → blocker
- REQUIRED        → critical
- ADVISORY        → major
- INFORMATIONAL   → info

The canonical conformance severity levels SHALL be:
- blocker: Blocks CI, must be fixed or exempted immediately
- critical: Should be fixed soon, may block CI in strict mode
- major: Should be addressed, tracked for resolution
- minor: Low priority, tracked for awareness
- info: Informational only, no action required

*Rationale:* Unified severity model enables consistent reporting across different
check types and integration points.


*Acceptance Criteria:*

```gherkin
Scenario: AC-033
  Given Contract check with severity='error'
  When Violation is recorded
  Then Violation severity is 'blocker'

Scenario: AC-034
  Given Verification check with severity=ADVISORY
  When Violation is recorded
  Then Violation severity is 'major'

```

**FR-017: Atomic File Operations**

*Priority:* MUST

The system SHALL use atomic file operations for all writes:
1. Write content to temporary file in same directory
2. Verify temporary file content is valid YAML
3. Rename temporary file to target filename (atomic on POSIX)
4. Include run_id in conformance_report.yaml for conflict detection

If concurrent modification is detected (run_id mismatch), the system
SHALL log a warning and proceed with current run's data.

*Rationale:* Prevents data corruption from concurrent CI jobs or interrupted writes.


*Acceptance Criteria:*

```gherkin
Scenario: AC-035
  Given conformance_report.yaml is being updated
  When Process is interrupted mid-write
  Then Either old or new file exists completely, never partial

Scenario: AC-036
  Given Two CI jobs run conformance check simultaneously
  When Both complete
  Then conformance_report.yaml is valid YAML from one of the runs

```

### 2.2 Non-Functional Requirements

**NFR-001: Performance - Large Codebase**

The system SHOULD complete conformance check operations within acceptable
time limits:
- Report generation: < 5 seconds for 10,000 violation records
- History snapshot: < 1 second
- Violation store operations: < 100ms per violation
- Full conformance check: Linear scaling with number of checks/files

**NFR-002: Storage Efficiency**

The system SHOULD maintain reasonable storage footprint:
- Average violation file: < 2KB
- History snapshot: < 5KB
- 90-day history: < 500KB total
- Conformance report: < 50KB for 1000 violations

**NFR-003: Git-Friendly Output**

All generated YAML files SHALL be formatted for minimal git diffs:
- Consistent key ordering (alphabetical within sections)
- No trailing whitespace
- Single newline at end of file
- Literal block style for multi-line strings
- 2-space indentation
- No flow style for complex structures

**NFR-004: Schema Validation**

All conformance YAML files SHALL validate against their JSON Schema:
- conformance_report.yaml → conformance_report.schema.yaml
- codebase_profile.yaml → codebase_profile.schema.yaml
- violations/*.yaml → violation.schema.yaml
- exemptions/*.yaml → exemption.schema.yaml
- history/*.yaml → history_snapshot.schema.yaml

Invalid files SHALL cause operations to fail with descriptive error messages.

---

## 3. Data Model

### 3.1 Entities

#### ConformanceReport

**Layer:** Domain | **Type:** aggregate_root

Represents the current conformance state of a repository. Aggregates
summary statistics from all violations and provides trend comparison
with previous runs.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| schema_version | string | False | pattern: ^\d+\.\d+$, required | Schema version for migration support |
| generated_at | datetime | False | required, iso8601 | Timestamp of report generation |
| run_id | string | False | required, uuid-v4 | Unique identifier for this verification run |
| run_type | string | False | enum: full, incremental, required | Type of verification run |
| summary | ConformanceSummary | False | required | Aggregated counts by status |
| by_severity | Dictionary<Severity, int> | False | required | Violation counts by severity level |
| by_contract | Dictionary<string, int> | False | required | Violation counts by contract ID |
| contracts_checked | List<string> | False | required | Contract IDs included in this run |
| files_checked | int | False | required, min: 0 | Count of files analyzed |
| stale_count | int | False | required, min: 0 | Number of stale violations |
| trend | ConformanceTrend | True | - | Comparison with previous run |

**Methods:**

- `calculate_summary(violations: List<Violation>) -> ConformanceSummary`: Calculate summary statistics from violation list
- `calculate_trend(previous_report: ConformanceReport) -> ConformanceTrend`: Calculate delta from previous report

**Invariants:**

- summary.total == summary.passed + summary.failed + summary.exempted
- sum(by_severity.values) == summary.failed + summary.exempted

#### ConformanceSummary

**Layer:** Domain | **Type:** value_object

Aggregated counts of check results by status.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| total | int | False | min: 0 | Total number of checks executed |
| passed | int | False | min: 0 | Checks that passed |
| failed | int | False | min: 0 | Checks that failed (not exempted) |
| exempted | int | False | min: 0 | Violations covered by exemptions |
| stale | int | False | min: 0 | Violations not checked this run |

**Invariants:**

- total >= passed + failed + exempted

#### ConformanceTrend

**Layer:** Domain | **Type:** value_object

Delta values comparing current run to previous run.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| total_delta | int | False | - | Change in total checks |
| passed_delta | int | False | - | Change in passed count |
| failed_delta | int | False | - | Change in failed count |
| exempted_delta | int | False | - | Change in exempted count |
| previous_run_id | string | False | uuid-v4 | Run ID of comparison baseline |

#### Violation

**Layer:** Domain | **Type:** entity

A single instance where code fails a contract check. Immutable identity
based on hash of composite key. Tracks lifecycle from detection through
resolution.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| violation_id | string | False | pattern: ^V-[a-f0-9]{12}(-\d+)?$, required | Hash-based unique identifier |
| contract_id | string | False | pattern: ^[a-z][a-z0-9_-]*$, required | Contract that was violated |
| check_id | string | False | pattern: ^[a-z][a-z0-9_-]*$, required | Specific check within contract |
| severity | Severity | False | required | Violation severity level |
| file_path | string | False | required, relative-path | Relative path to violating file |
| line_number | int | True | min: 1 | Line number (null for file-level) |
| column_number | int | True | min: 1 | Column number if available |
| message | string | False | required, max-length: 500 | Human-readable description |
| fix_hint | string | True | max-length: 500 | Suggested remediation |
| code_snippet | string | True | max-lines: 5 | Relevant code context |
| detected_at | datetime | False | required, iso8601 | First detection timestamp |
| last_seen_at | datetime | False | required, iso8601 | Most recent detection |
| status | ViolationStatus | False | required | Current violation status |
| resolved_at | datetime | True | iso8601 | Resolution timestamp |
| resolution | string | True | max-length: 500 | Resolution details |
| exemption_id | string | True | pattern: ^[a-z][a-z0-9_-]*$ | Covering exemption if any |
| exemption_expired_at | datetime | True | iso8601 | When covering exemption expired |

**Methods:**

- `calculate_id(contract_id: string, check_id: string, file_path: string, line_number: int?, rule_id: string?) -> string`: Calculate violation ID from composite key
- `mark_resolved(reason: string) -> Violation`: Mark violation as resolved
- `mark_stale() -> Violation`: Mark violation as stale
- `mark_exemption_expired() -> Violation`: Mark violation as having expired exemption

**Invariants:**

- status == 'resolved' implies resolved_at is not null
- status == 'exemption_expired' implies exemption_expired_at is not null
- exemption_id is not null implies status in ('exempted', 'exemption_expired')

#### ViolationStatus

**Layer:** Domain | **Type:** enum

Possible states for a violation throughout its lifecycle.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| open | string | False | - | Active violation requiring attention |
| resolved | string | False | - | Violation has been fixed |
| exempted | string | False | - | Covered by active exemption |
| exemption_expired | string | False | - | Exemption expired, needs attention |
| stale | string | False | - | Not checked in recent incremental run |

#### Severity

**Layer:** Domain | **Type:** enum

Canonical severity levels for conformance violations.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| blocker | string | False | - | Blocks CI, must fix immediately |
| critical | string | False | - | Should fix soon, may block in strict mode |
| major | string | False | - | Should address, tracked for resolution |
| minor | string | False | - | Low priority, tracked for awareness |
| info | string | False | - | Informational only |

#### Exemption

**Layer:** Domain | **Type:** entity

Approved exception to a contract check with justification and optional
expiration. Scope can be global, file patterns, specific checks, or
individual violations.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| id | string | False | pattern: ^[a-z][a-z0-9_-]*$, required | Unique exemption identifier |
| contract_id | string | False | pattern: ^[a-z][a-z0-9_-]*$, required | Contract being exempted |
| check_ids | List<string> | False | required, min-items: 1 | Checks exempted (* for all) |
| reason | string | False | required, min-length: 10 | Justification for exemption |
| approved_by | string | False | required | Approver (username, email, or 'self') |
| approved_date | date | False | required, iso8601-date | Date of approval |
| expires | date | True | iso8601-date | Expiration date (end of day) |
| review_date | date | True | iso8601-date | Date to reconsider exemption |
| status | ExemptionStatus | False | required | Current exemption status |
| scope | ExemptionScope | False | required | What this exemption covers |

**Methods:**

- `is_expired() -> bool`: Check if exemption has expired
- `is_active() -> bool`: Check if exemption is currently active
- `covers_violation(violation: Violation) -> bool`: Check if this exemption covers a violation
- `covers_file(file_path: string) -> bool`: Check if file path matches scope patterns

**Invariants:**

- expires is null or expires >= approved_date
- review_date is null or review_date >= approved_date
- status == 'expired' implies expires is not null and expires < today

#### ExemptionStatus

**Layer:** Domain | **Type:** enum

Possible states for an exemption.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| active | string | False | - | Exemption is in effect |
| expired | string | False | - | Past expiration date |
| resolved | string | False | - | Underlying issue fixed |
| under_review | string | False | - | Being reconsidered |

#### ExemptionScope

**Layer:** Domain | **Type:** value_object

Defines what violations an exemption covers.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| type | string | False | enum: check_id, file_pattern, violation_id, global, required | Type of scope restriction |
| patterns | List<string> | True | glob-patterns | File glob patterns (for file_pattern type) |
| violation_ids | List<string> | True | pattern: ^V-[a-f0-9]{12}(-\d+)?$ | Specific violation IDs (for violation_id type) |
| lines | LineRange | True | - | Optional line range restriction |

**Invariants:**

- type == 'file_pattern' implies patterns is not null and not empty
- type == 'violation_id' implies violation_ids is not null and not empty
- type == 'global' implies patterns is null and violation_ids is null

#### LineRange

**Layer:** Domain | **Type:** value_object

Line range for scoping exemptions to specific code regions.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| start | int | False | min: 1 | Start line (inclusive) |
| end | int | False | min: 1 | End line (inclusive) |

**Invariants:**

- end >= start

#### HistorySnapshot

**Layer:** Domain | **Type:** entity

Point-in-time summary of conformance state for trend analysis.
One snapshot per day, contains only aggregate counts.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| schema_version | string | False | pattern: ^\d+\.\d+$, required | Schema version |
| date | date | False | required, iso8601-date | Snapshot date |
| generated_at | datetime | False | required, iso8601 | Generation timestamp |
| summary | ConformanceSummary | False | required | Aggregate counts |
| by_severity | Dictionary<Severity, int> | False | required | Counts by severity |
| by_contract | Dictionary<string, int> | False | required | Counts by contract |
| files_analyzed | int | False | min: 0 | Files checked |
| contracts_checked | List<string> | False | required | Contracts included |

#### CodebaseProfile

**Layer:** Domain | **Type:** aggregate_root

Extracted metadata about codebase structure, patterns, and conventions.
May be auto-detected or manually curated.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| schema_version | string | False | pattern: ^\d+\.\d+$, required | Schema version |
| generated_at | datetime | False | required, iso8601 | Generation timestamp |
| languages | List<LanguageInfo> | False | required | Detected programming languages |
| frameworks | List<string> | False | - | Detected frameworks/libraries |
| structure | CodebaseStructure | False | required | Directory and layer organization |
| patterns_detected | DetectedPatterns | True | - | Naming and organization patterns |
| dependencies | DependencyInfo | True | - | Project dependencies |
| metrics | CodebaseMetrics | True | - | Size and composition metrics |

#### LanguageInfo

**Layer:** Domain | **Type:** value_object

Information about a programming language used in the codebase.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| name | string | False | required | Language name |
| percentage | float | False | min: 0, max: 100 | Percentage of codebase |
| confidence | float | True | min: 0, max: 1 | Detection confidence (for auto-detected) |
| source | string | False | enum: auto-detected, manual | How this was determined |

#### CodebaseStructure

**Layer:** Domain | **Type:** value_object

Organization of the codebase directories and layers.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| root_path | string | False | required | Repository root path |
| layers | List<LayerInfo> | True | - | Architectural layers if detectable |
| key_directories | List<DirectoryInfo> | False | - | Important directories |
| entry_points | List<string> | True | - | Main entry point files |

#### LayerInfo

**Layer:** Domain | **Type:** value_object

Information about an architectural layer.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| name | string | False | required | Layer name |
| path | string | False | required | Layer directory path |
| description | string | True | - | Layer responsibilities |

#### DirectoryInfo

**Layer:** Domain | **Type:** value_object

Information about a key directory.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| path | string | False | required | Directory path |
| purpose | string | False | required | What this directory contains |

#### DetectedPatterns

**Layer:** Domain | **Type:** value_object

Naming and organization patterns detected in the codebase.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| naming_conventions | List<NamingConvention> | True | - | File and symbol naming patterns |
| file_organization | string | True | - | How files are organized |
| test_structure | TestStructure | True | - | Test file organization |

#### NamingConvention

**Layer:** Domain | **Type:** value_object

A detected naming convention.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| applies_to | string | False | required | What this applies to (files, classes, functions) |
| pattern | string | False | required | Naming pattern description |
| examples | List<string> | True | - | Example names following convention |
| confidence | float | True | min: 0, max: 1 | Detection confidence |

#### TestStructure

**Layer:** Domain | **Type:** value_object

How tests are organized in the codebase.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| test_directories | List<string> | False | - | Where tests are located |
| naming_pattern | string | True | - | Test file naming pattern |
| framework | string | True | - | Test framework used |

#### DependencyInfo

**Layer:** Domain | **Type:** value_object

Project dependencies information.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| direct | List<string> | False | - | Direct dependencies |
| dev | List<string> | False | - | Development dependencies |

#### CodebaseMetrics

**Layer:** Domain | **Type:** value_object

Size and composition metrics for the codebase.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| total_files | int | False | min: 0 | Total source files |
| total_lines | int | False | min: 0 | Approximate lines of code |
| by_language | Dictionary<string, int> | True | - | Lines by language |

#### ConformanceManager

**Layer:** Application | **Type:** entity

Orchestrates conformance operations: running checks, updating violations,
generating reports, and pruning stale data. Main application service
integrating VerificationRunner output with .agentforge/ filesystem.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| repo_path | string | False | required | Repository root path |
| agentforge_path | string | False | required | Path to .agentforge/ directory |
| violation_store | ViolationStore | False | required | Violation storage manager |
| history_store | HistoryStore | False | required | History storage manager |
| exemption_registry | ExemptionRegistry | False | required | Exemption lookup service |

**Methods:**

- `run_conformance_check(contracts: List<string>?, files: List<string>?, full_run: bool) -> ConformanceReport`: Execute conformance check with optional scope
- `generate_report() -> ConformanceReport`: Generate report from current state
- `update_violations(check_results: List<CheckResult>, run_type: string) -> int`: Update violation store with check results
- `apply_exemptions(violations: List<Violation>) -> int`: Apply exemptions to violations
- `save_history_snapshot(report: ConformanceReport) -> void`: Save daily history snapshot
- `prune_violations(older_than_days: int, statuses: List<ViolationStatus>) -> int`: Remove old resolved/stale violations

#### ViolationStore

**Layer:** Infrastructure | **Type:** entity

Manages violations/ directory. Handles CRUD operations for violation files,
ID generation, smart merge logic, and stale detection.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| violations_path | string | False | required | Path to violations/ directory |
| violations_cache | Dictionary<string, Violation> | False | - | In-memory cache of loaded violations |

**Methods:**

- `load_all() -> List<Violation>`: Load all violations from disk
- `get(violation_id: string) -> Violation?`: Get violation by ID
- `save(violation: Violation) -> void`: Save violation to disk atomically
- `delete(violation_id: string) -> bool`: Delete violation file
- `find_by_file(file_path: string) -> List<Violation>`: Find violations for a file
- `find_by_contract(contract_id: string) -> List<Violation>`: Find violations for a contract
- `mark_stale(except_files: List<string>, except_contracts: List<string>) -> int`: Mark violations as stale except for specified scope
- `generate_id(contract_id: string, check_id: string, file_path: string, line_number: int?, rule_id: string?) -> string`: Generate violation ID from composite key

#### HistoryStore

**Layer:** Infrastructure | **Type:** entity

Manages history/ directory. Handles daily snapshot creation, retention
policy enforcement, and trend calculation.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| history_path | string | False | required | Path to history/ directory |
| retention_days | int | False | min: 7, max: 365, default: 90 | History retention in days |

**Methods:**

- `save_snapshot(snapshot: HistorySnapshot) -> void`: Save or overwrite daily snapshot
- `get_snapshot(date: date) -> HistorySnapshot?`: Get snapshot for specific date
- `get_range(start_date: date, end_date: date) -> List<HistorySnapshot>`: Get snapshots for date range
- `prune_old_snapshots() -> int`: Delete snapshots older than retention period
- `calculate_trend(days: int, metric: string) -> Dictionary<string, List<int>>`: Calculate trend data for visualization

#### ExemptionRegistry

**Layer:** Infrastructure | **Type:** entity

Manages exemptions/ directory and provides lookup functionality.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| exemptions_path | string | False | required | Path to exemptions/ directory |
| exemptions_cache | Dictionary<string, Exemption> | False | - | In-memory cache of loaded exemptions |

**Methods:**

- `load_all() -> List<Exemption>`: Load all exemptions from disk
- `find_for_violation(violation: Violation) -> Exemption?`: Find exemption that covers a violation
- `get_expired() -> List<Exemption>`: Get all expired exemptions
- `update_status(exemption_id: string, status: ExemptionStatus) -> void`: Update exemption status

#### ConformanceConfig

**Layer:** Domain | **Type:** value_object

Conformance configuration stored in repo.yaml.

**Properties:**

| Property | Type | Nullable | Constraints | Description |
|----------|------|----------|-------------|-------------|
| history_retention_days | int | False | min: 7, max: 365, default: 90 | Days to retain history snapshots |
| severity_threshold | Severity | False | default: blocker | Minimum severity for non-zero exit code |
| auto_prune | bool | False | default: true | Auto-prune old resolved violations |
| auto_prune_days | int | False | min: 7, default: 30 | Days before auto-pruning resolved violations |
| notify_on_new_violations | bool | False | default: false | Emit notification on new violations |

---

## 4. Interfaces

#### ConformanceCheck

**Type:** command | **Path:** `CLI: agentforge conformance check`

**Request Body:** `Options:
  --contracts: Optional[List[str]]
  --files: Optional[List[str]]
  --full: bool = False
  --no-history: bool = False
  --exit-code: bool = False
  --severity-threshold: Severity = blocker
`

**Success Response:** `ConformanceReport`

**Error Codes:**
- `NoAgentForgeDirectory`
- `InvalidContract`
- `VerificationFailed`

#### ConformanceReport

**Type:** query | **Path:** `CLI: agentforge conformance report`

**Request Body:** `Options:
  --format: str = "text" (text|json|yaml)
  --verbose: bool = False
  --by-severity: bool = False
  --by-contract: bool = False
`

**Success Response:** `FormattedReport`

**Error Codes:**
- `NoConformanceReport`

#### ViolationsList

**Type:** query | **Path:** `CLI: agentforge conformance violations list`

**Request Body:** `Options:
  --status: Optional[ViolationStatus]
  --severity: Optional[Severity]
  --contract: Optional[str]
  --file: Optional[str]
  --limit: int = 50
`

**Success Response:** `List[ViolationSummary]`

**Error Codes:**
- `NoViolationsDirectory`

#### ViolationShow

**Type:** query | **Path:** `CLI: agentforge conformance violations show {id}`

**Request Body:** `Path parameters:
  id: str (violation_id)
`

**Success Response:** `Violation`

**Error Codes:**
- `ViolationNotFound`

#### ViolationResolve

**Type:** command | **Path:** `CLI: agentforge conformance violations resolve {id}`

**Request Body:** `Path parameters:
  id: str (violation_id)
Options:
  --reason: str (required)
`

**Success Response:** `Violation`

**Error Codes:**
- `ViolationNotFound`
- `ReasonRequired`

#### ViolationPrune

**Type:** command | **Path:** `CLI: agentforge conformance violations prune`

**Request Body:** `Options:
  --older-than: int = 30
  --dry-run: bool = False
`

**Success Response:** `PruneResult`

**Error Codes:**
- `NoViolationsDirectory`

#### ConformanceHistory

**Type:** query | **Path:** `CLI: agentforge conformance history`

**Request Body:** `Options:
  --days: int = 30
  --format: str = "text" (text|json|yaml|csv)
  --metric: str = "failed" (total|failed|passed|exempted)
`

**Success Response:** `HistoryData`

**Error Codes:**
- `NoHistoryDirectory`

#### ConformanceInit

**Type:** command | **Path:** `CLI: agentforge conformance init`

**Request Body:** `Options:
  --force: bool = False
`

**Success Response:** `InitResult`

**Error Codes:**
- `DirectoryExists`

---

## 5. Workflows

### Run Conformance Check

**Trigger:** Developer or CI runs 'agentforge conformance check'

**Steps:**

1. **User:** Executes 'agentforge conformance check' with optional scope
2. **ConformanceManager:** Loads configuration from repo.yaml
3. **ConformanceManager:** Determines run type (full or incremental) based on options
4. **ConformanceManager:** Invokes VerificationEngine with specified contracts/files
5. **VerificationEngine:** Runs checks and returns List<CheckResult>
6. **ConformanceManager:** Transforms CheckResult into Violation records
7. **ExemptionRegistry:** Matches violations against exemptions, marks exempted violations
8. **ExemptionRegistry:** Identifies expired exemptions, updates their status
9. **ViolationStore:** Merges new violations with existing (smart merge for incremental)
   - *Alternative:* For incremental: mark unchecked violations as stale
   - *Alternative:* For full: resolve violations that no longer fail
10. **ConformanceManager:** Generates ConformanceReport with summary and trend
11. **HistoryStore:** Saves daily history snapshot (unless --no-history)
12. **HistoryStore:** Prunes old history snapshots per retention policy
13. **ConformanceManager:** Returns exit code based on severity threshold

**Success:** Conformance state updated, report generated, history recorded

### Handle Expired Exemption

**Trigger:** Conformance check detects exemption past expiration date

**Steps:**

1. **ConformanceManager:** During check, requests expired exemptions from registry
2. **ExemptionRegistry:** Returns list of exemptions where expires < current_date
3. **ConformanceManager:** For each expired exemption, finds covered violations
4. **ViolationStore:** Updates violation.status to 'exemption_expired'
5. **ViolationStore:** Sets violation.exemption_expired_at timestamp
6. **ExemptionRegistry:** Updates exemption.status to 'expired'
7. **ConformanceManager:** Adds warning to conformance report about expired exemptions

**Success:** Expired exemptions surfaced as violations requiring attention

### Resolve Violation Manually

**Trigger:** User runs 'agentforge conformance violations resolve V-xxx'

**Steps:**

1. **User:** Executes resolve command with violation ID and reason
2. **CLI:** Validates violation ID exists
   - *Alternative:* If not found: return ViolationNotFound error
3. **CLI:** Validates reason is provided
   - *Alternative:* If missing: return ReasonRequired error
4. **ViolationStore:** Loads violation from file
5. **ViolationStore:** Updates status to 'resolved', sets resolved_at and resolution
6. **ViolationStore:** Saves violation file atomically
7. **CLI:** Displays updated violation details

**Success:** Violation marked as resolved with documented reason

### Initialize Conformance

**Trigger:** User runs 'agentforge conformance init' in new repository

**Steps:**

1. **User:** Executes 'conformance init' command
2. **CLI:** Checks if .agentforge/ directory exists
   - *Alternative:* If exists and no --force: return DirectoryExists error
3. **ConformanceManager:** Creates .agentforge/ directory
4. **ConformanceManager:** Creates violations/, exemptions/, history/ subdirectories
5. **ConformanceManager:** Creates .gitkeep files in empty directories
6. **ConformanceManager:** Generates initial codebase_profile.yaml (auto-detected)
7. **ConformanceManager:** Generates initial conformance_report.yaml (empty state)
8. **ConformanceManager:** Adds local.yaml to .gitignore if not present
9. **CLI:** Displays initialization summary

**Success:** .agentforge/ directory structure created and ready for use

---

## 6. Error Handling

| Error Code | Condition | Response | User Message |
|------------|-----------|----------|--------------|
| NoAgentForgeDirectory | .agentforge/ directory does not exist in repository | Return error with suggestion to run 'conformance init' | No .agentforge/ directory found. Run 'agentforge conformance init' to initialize.
 |
| InvalidContract | Specified contract ID not found in contract registry | Return error listing available contracts | Contract '{contract_id}' not found. Available contracts: {list}.
 |
| VerificationFailed | Verification engine encounters unrecoverable error | Return error with engine details, no state changes | Verification failed: {error_message}. No conformance state was modified.
 |
| NoConformanceReport | conformance_report.yaml does not exist | Return error suggesting to run check first | No conformance report found. Run 'agentforge conformance check' first.
 |
| ViolationNotFound | Requested violation ID does not exist | Return error with suggestion to list violations | Violation '{violation_id}' not found. Use 'violations list' to see available violations.
 |
| ReasonRequired | Resolve command called without --reason | Return error explaining requirement | Resolution reason is required. Use --reason 'your reason' to document why this was resolved.
 |
| DirectoryExists | .agentforge/ already exists when running init | Return error suggesting --force option | .agentforge/ directory already exists. Use --force to reinitialize (existing data will be preserved).
 |
| SchemaValidationError | YAML file fails schema validation | Return error with validation details | Schema validation failed for {file_path}: {validation_error}
 |
| AtomicWriteFailed | Atomic file rename operation fails | Return error, ensure no partial files remain | Failed to write {file_path}. Check disk space and permissions.
 |
| HashCollision | Two different violations produce same 12-char hash | Append numeric suffix to ID (-1, -2, etc.) | None |
| RetentionPolicyViolation | User sets retention outside allowed range | Return error with valid range | History retention must be between 7 and 365 days. Got: {value}
 |

---

## 7. Testing Notes

### Unit Test Focus

- Violation ID calculation produces consistent results
- Smart merge correctly handles incremental vs full runs
- Exemption matching for all scope types (check_id, file_pattern, violation_id, global)
- Exemption expiry date handling (boundary conditions)
- History retention pruning logic
- Severity mapping between systems
- Atomic file operations with temp file + rename
- ConformanceSummary calculation accuracy
- Trend calculation from previous report

### Integration Test Scenarios

- Full conformance check lifecycle from init to report
- Incremental check preserving existing violations
- Exemption expiry transitioning violations to exemption_expired
- History accumulation over multiple days
- CLI commands with various option combinations
- Concurrent check handling (no corruption)
- Recovery from partial/corrupted files

### Edge Cases

- Empty repository (no source files)
- Repository with no violations (perfect conformance)
- Violation at line 0 (file-level violation)
- Exemption with * for all checks
- File path with special characters
- Hash collision handling with -1 suffix
- Exactly 90-day-old history snapshot (boundary)
- Exemption expiring today at midnight
- Two violations with same location but different checks
- Incremental run with no changes

---

## Glossary

| Term | Definition |
|------|------------|
| Conformance | The degree to which a codebase adheres to its defined architectural contracts.
Measured as ratio of passed checks to total checks.
 |
| Violation | A single instance where code fails a contract check. Identified by hash of
contract, check, file, and line number.
 |
| Exemption | An approved exception to a contract check. Allows known technical debt to
exist without failing conformance checks. Requires justification and may expire.
 |
| Stale Violation | A violation from a previous run that was not re-checked in the current
incremental run because its file or contract was not in scope.
 |
| Smart Merge | The process of combining incremental run results with existing conformance
state. Updates only violations for checked scope, preserves others as stale.
 |
| History Snapshot | Daily summary of conformance metrics stored for trend analysis. Contains
only aggregate counts, not full violation details.
 |
| Severity Threshold | The minimum violation severity that causes CLI to return non-zero exit code.
Used for CI/CD gating decisions.
 |
| Atomic Write | File write operation using temp file + rename pattern to ensure either
complete old or complete new file exists, never partial.
 |
| Codebase Profile | Extracted metadata about a repository including languages, frameworks,
structure, and patterns. May be auto-detected or manually curated.
 |
| Run ID | UUID v4 identifying a specific verification run. Used for conflict detection
and trend comparison. |
