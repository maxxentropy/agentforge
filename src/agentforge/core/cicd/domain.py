# @spec_file: .agentforge/specs/core-cicd-v1.yaml
# @spec_id: core-cicd-v1
# @component_id: core-cicd-domain
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
CI/CD Domain Entities
=====================

Pure domain objects for CI/CD integration. No I/O operations.
These entities represent the core business logic for baseline comparison,
violation tracking, and CI result management.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any


class CIMode(Enum):
    """CI execution modes."""
    FULL = "full"           # Check entire codebase
    INCREMENTAL = "incremental"  # Check only changed files
    PR = "pr"               # Baseline comparison mode for PRs


class ExitCode(IntEnum):
    """Structured exit codes for CI integration."""
    SUCCESS = 0             # No violations or only warnings
    VIOLATIONS_FOUND = 1    # Errors found
    CONFIG_ERROR = 2        # Configuration error
    RUNTIME_ERROR = 3       # Runtime error
    BASELINE_NOT_FOUND = 4  # Baseline file missing when required

    @property
    def description(self) -> str:
        """Human-readable description of the exit code."""
        descriptions = {
            ExitCode.SUCCESS: "Success (no violations or only warnings)",
            ExitCode.VIOLATIONS_FOUND: "Violations found (errors)",
            ExitCode.CONFIG_ERROR: "Configuration error",
            ExitCode.RUNTIME_ERROR: "Runtime error",
            ExitCode.BASELINE_NOT_FOUND: "Baseline not found (when required)",
        }
        return descriptions.get(self, "Unknown exit code")


@dataclass
class CIViolation:
    """
    Individual violation record for CI/CD context.

    Extends the core Violation concept with CI-specific features
    like SARIF conversion and baseline hashing.
    """
    check_id: str
    file_path: str
    line: int | None
    message: str
    severity: str  # "error" | "warning" | "info"
    rule_id: str | None = None
    contract_id: str | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None
    fix_hint: str | None = None
    code_snippet: str | None = None

    @property
    def hash(self) -> str:
        """
        Generate deterministic hash for baseline comparison.

        Hash is based on: check_id:file:line:message
        This allows tracking violations across runs even if
        other metadata changes.
        """
        line_str = str(self.line) if self.line else "0"
        composite = f"{self.check_id}:{self.file_path}:{line_str}:{self.message}"
        return hashlib.sha256(composite.encode()).hexdigest()[:16]

    def to_sarif_result(self) -> dict[str, Any]:
        """
        Convert to SARIF 2.1.0 result format.

        Returns a dict conforming to the SARIF result schema:
        https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
        """
        # Map severity to SARIF level
        level_map = {
            "error": "error",
            "warning": "warning",
            "info": "note",
        }
        level = level_map.get(self.severity, "warning")

        # Build physical location
        physical_location: dict[str, Any] = {
            "artifactLocation": {
                "uri": self.file_path,
                "uriBaseId": "%SRCROOT%",
            }
        }

        # Add region if line is specified
        if self.line:
            region: dict[str, Any] = {"startLine": self.line}
            if self.column:
                region["startColumn"] = self.column
            if self.end_line:
                region["endLine"] = self.end_line
            if self.end_column:
                region["endColumn"] = self.end_column
            physical_location["region"] = region

        result: dict[str, Any] = {
            "ruleId": self.rule_id or self.check_id,
            "level": level,
            "message": {"text": self.message},
            "locations": [{"physicalLocation": physical_location}],
        }

        # Add fix hint if available
        if self.fix_hint:
            result["fixes"] = [{
                "description": {"text": self.fix_hint}
            }]

        # Add fingerprint for deduplication
        result["partialFingerprints"] = {
            "primaryLocationLineHash": self.hash
        }

        return result

    def to_junit_testcase(self, suite_name: str) -> dict[str, Any]:
        """
        Convert to JUnit XML testcase format.

        Args:
            suite_name: Name of the test suite (typically the contract)

        Returns:
            Dict representing a JUnit testcase with failure
        """
        location = f"{self.file_path}"
        if self.line:
            location += f":{self.line}"

        return {
            "name": f"{self.check_id}@{location}",
            "classname": suite_name,
            "failure": {
                "message": self.message,
                "type": self.severity,
                "text": f"File: {self.file_path}\nLine: {self.line or 'N/A'}\n\n{self.message}"
            }
        }


@dataclass
class BaselineEntry:
    """
    Single entry in the violation baseline.

    Stores the hash and metadata needed to identify a violation
    across runs without storing the full violation details.
    """
    hash: str
    check_id: str
    file_path: str
    line: int | None
    message_preview: str  # First 100 chars of message
    first_seen: datetime
    last_seen: datetime

    @classmethod
    def from_violation(cls, violation: CIViolation) -> "BaselineEntry":
        """Create baseline entry from a violation."""
        now = datetime.utcnow()
        return cls(
            hash=violation.hash,
            check_id=violation.check_id,
            file_path=violation.file_path,
            line=violation.line,
            message_preview=violation.message[:100] if len(violation.message) > 100 else violation.message,
            first_seen=now,
            last_seen=now,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hash": self.hash,
            "check_id": self.check_id,
            "file_path": self.file_path,
            "line": self.line,
            "message_preview": self.message_preview,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaselineEntry":
        """Create from dictionary."""
        return cls(
            hash=data["hash"],
            check_id=data["check_id"],
            file_path=data["file_path"],
            line=data.get("line"),
            message_preview=data["message_preview"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
        )


@dataclass
class Baseline:
    """
    Collection of known violations (baseline).

    The baseline represents the current state of violations on the main branch.
    PR checks compare against this to identify new vs existing violations.
    """
    schema_version: str
    created_at: datetime
    updated_at: datetime
    commit_sha: str | None
    entries: dict[str, BaselineEntry]  # hash -> entry

    def contains(self, violation: CIViolation) -> bool:
        """Check if violation exists in baseline."""
        return violation.hash in self.entries

    def get_entry(self, violation: CIViolation) -> BaselineEntry | None:
        """Get baseline entry for a violation if it exists."""
        return self.entries.get(violation.hash)

    def add(self, violation: CIViolation) -> None:
        """Add or update a violation in the baseline."""
        if violation.hash in self.entries:
            # Update last_seen
            self.entries[violation.hash].last_seen = datetime.utcnow()
        else:
            self.entries[violation.hash] = BaselineEntry.from_violation(violation)
        self.updated_at = datetime.utcnow()

    def remove(self, violation_hash: str) -> bool:
        """Remove a violation from the baseline by hash."""
        if violation_hash in self.entries:
            del self.entries[violation_hash]
            self.updated_at = datetime.utcnow()
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "commit_sha": self.commit_sha,
            "entries": {h: e.to_dict() for h, e in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Baseline":
        """Create from dictionary."""
        entries = {
            h: BaselineEntry.from_dict(e)
            for h, e in data.get("entries", {}).items()
        }
        return cls(
            schema_version=data["schema_version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            commit_sha=data.get("commit_sha"),
            entries=entries,
        )

    @classmethod
    def create_empty(cls, commit_sha: str | None = None) -> "Baseline":
        """Create a new empty baseline."""
        now = datetime.utcnow()
        return cls(
            schema_version="1.0",
            created_at=now,
            updated_at=now,
            commit_sha=commit_sha,
            entries={},
        )


@dataclass
class BaselineComparison:
    """
    Result of comparing current violations against baseline.

    This is the core of PR checking - categorizing violations as:
    - new: Introduced in this PR (should block)
    - fixed: Resolved in this PR (celebrate!)
    - existing: Already in baseline (tech debt)
    """
    new_violations: list[CIViolation]
    fixed_violations: list[BaselineEntry]
    existing_violations: list[CIViolation]

    @property
    def introduces_violations(self) -> bool:
        """Check if PR introduces new violations."""
        return len(self.new_violations) > 0

    @property
    def net_change(self) -> int:
        """
        Net change in violation count.

        Negative = improvement (more fixed than introduced)
        Positive = regression (more introduced than fixed)
        """
        return len(self.new_violations) - len(self.fixed_violations)

    @property
    def has_improvements(self) -> bool:
        """Check if any violations were fixed."""
        return len(self.fixed_violations) > 0

    @property
    def new_errors(self) -> list[CIViolation]:
        """Get only error-level new violations."""
        return [v for v in self.new_violations if v.severity == "error"]

    @property
    def new_warnings(self) -> list[CIViolation]:
        """Get only warning-level new violations."""
        return [v for v in self.new_violations if v.severity == "warning"]

    def should_fail(self, fail_on_new_errors: bool = True, fail_on_new_warnings: bool = False) -> bool:
        """
        Determine if the PR should fail based on configuration.

        Args:
            fail_on_new_errors: Fail if any new errors introduced
            fail_on_new_warnings: Fail if any new warnings introduced

        Returns:
            True if PR should fail
        """
        if fail_on_new_errors and len(self.new_errors) > 0:
            return True
        return bool(fail_on_new_warnings and len(self.new_warnings) > 0)

    def should_fail_ratchet(self) -> bool:
        """
        Determine if check should fail in ratchet mode.

        Ratchet mode only fails if there are MORE violations than before.
        This allows gradual improvement without blocking on existing tech debt.

        Returns:
            True if total violations increased (regression)
        """
        return self.net_change > 0

    @classmethod
    def compare(cls, violations: list[CIViolation], baseline: Baseline) -> "BaselineComparison":
        """
        Compare violations against baseline.

        Args:
            violations: Current violations from the check run
            baseline: The baseline to compare against

        Returns:
            BaselineComparison with categorized violations
        """
        current_hashes: set[str] = set()
        new_violations: list[CIViolation] = []
        existing_violations: list[CIViolation] = []

        for violation in violations:
            current_hashes.add(violation.hash)
            if baseline.contains(violation):
                existing_violations.append(violation)
            else:
                new_violations.append(violation)

        # Find fixed violations (in baseline but not in current)
        fixed_violations: list[BaselineEntry] = []
        for hash_val, entry in baseline.entries.items():
            if hash_val not in current_hashes:
                fixed_violations.append(entry)

        return cls(
            new_violations=new_violations,
            fixed_violations=fixed_violations,
            existing_violations=existing_violations,
        )


@dataclass
class CIResult:
    """
    Complete result of a CI check run.

    Contains all information needed to generate output reports
    and determine the exit code.
    """
    mode: CIMode
    exit_code: ExitCode
    violations: list[CIViolation]
    comparison: BaselineComparison | None  # Only for PR mode
    files_checked: int
    checks_run: int
    duration_seconds: float
    started_at: datetime
    completed_at: datetime
    commit_sha: str | None = None
    base_ref: str | None = None
    head_ref: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def total_violations(self) -> int:
        """Total number of violations found."""
        return len(self.violations)

    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of warning-level violations."""
        return sum(1 for v in self.violations if v.severity == "warning")

    @property
    def info_count(self) -> int:
        """Count of info-level violations."""
        return sum(1 for v in self.violations if v.severity == "info")

    @property
    def is_success(self) -> bool:
        """Check if the result indicates success."""
        return self.exit_code == ExitCode.SUCCESS

    def get_violations_by_file(self) -> dict[str, list[CIViolation]]:
        """Group violations by file path."""
        by_file: dict[str, list[CIViolation]] = {}
        for violation in self.violations:
            if violation.file_path not in by_file:
                by_file[violation.file_path] = []
            by_file[violation.file_path].append(violation)
        return by_file

    def get_violations_by_check(self) -> dict[str, list[CIViolation]]:
        """Group violations by check ID."""
        by_check: dict[str, list[CIViolation]] = {}
        for violation in self.violations:
            if violation.check_id not in by_check:
                by_check[violation.check_id] = []
            by_check[violation.check_id].append(violation)
        return by_check

    def to_summary_dict(self) -> dict[str, Any]:
        """Generate summary dictionary for logging/reporting."""
        summary: dict[str, Any] = {
            "mode": self.mode.value,
            "exit_code": self.exit_code.value,
            "exit_code_description": self.exit_code.description,
            "total_violations": self.total_violations,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "info": self.info_count,
            "files_checked": self.files_checked,
            "checks_run": self.checks_run,
            "duration_seconds": round(self.duration_seconds, 2),
        }

        if self.comparison:
            summary["baseline_comparison"] = {
                "new_violations": len(self.comparison.new_violations),
                "fixed_violations": len(self.comparison.fixed_violations),
                "existing_violations": len(self.comparison.existing_violations),
                "net_change": self.comparison.net_change,
            }

        if self.commit_sha:
            summary["commit_sha"] = self.commit_sha

        if self.errors:
            summary["runtime_errors"] = self.errors

        return summary


@dataclass
class CIConfig:
    """
    Configuration for CI check runs.

    Controls behavior like parallelism, failure conditions,
    and output formats.
    """
    mode: CIMode = CIMode.FULL
    parallel_enabled: bool = True
    max_workers: int = 4
    fail_on_new_errors: bool = True
    fail_on_new_warnings: bool = False
    total_errors_threshold: int | None = None  # Absolute cap
    ratchet_enabled: bool = False  # Only fail if violations increase from baseline
    baseline_path: str = ".agentforge/baseline.json"
    output_sarif: bool = True
    output_junit: bool = False
    output_markdown: bool = True
    sarif_path: str = ".agentforge/results.sarif"
    junit_path: str = ".agentforge/results.xml"
    markdown_path: str = ".agentforge/results.md"
    cache_enabled: bool = True
    cache_path: str = ".agentforge/cache/"
    cache_ttl_hours: int = 24
    incremental_paths: list[str] | None = None  # Files to check in incremental mode
    base_ref: str | None = None  # Git base ref for PR mode
    head_ref: str | None = None  # Git head ref for PR mode

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode.value,
            "parallel": {
                "enabled": self.parallel_enabled,
                "max_workers": self.max_workers,
            },
            "fail_on": {
                "new_errors": self.fail_on_new_errors,
                "new_warnings": self.fail_on_new_warnings,
                "total_errors_exceed": self.total_errors_threshold,
            },
            "ratchet_enabled": self.ratchet_enabled,
            "baseline_path": self.baseline_path,
            "output": {
                "sarif": {"enabled": self.output_sarif, "path": self.sarif_path},
                "junit": {"enabled": self.output_junit, "path": self.junit_path},
                "markdown": {"enabled": self.output_markdown, "path": self.markdown_path},
            },
            "cache": {
                "enabled": self.cache_enabled,
                "path": self.cache_path,
                "ttl_hours": self.cache_ttl_hours,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CIConfig":
        """Create from dictionary."""
        parallel = data.get("parallel", {})
        fail_on = data.get("fail_on", {})
        output = data.get("output", {})
        cache = data.get("cache", {})

        mode_str = data.get("mode", "full")
        mode = CIMode(mode_str) if mode_str in [m.value for m in CIMode] else CIMode.FULL

        return cls(
            mode=mode,
            parallel_enabled=parallel.get("enabled", True),
            max_workers=parallel.get("max_workers", 4),
            fail_on_new_errors=fail_on.get("new_errors", True),
            fail_on_new_warnings=fail_on.get("new_warnings", False),
            total_errors_threshold=fail_on.get("total_errors_exceed"),
            ratchet_enabled=data.get("ratchet_enabled", False),
            baseline_path=data.get("baseline_path", ".agentforge/baseline.json"),
            output_sarif=output.get("sarif", {}).get("enabled", True),
            output_junit=output.get("junit", {}).get("enabled", False),
            output_markdown=output.get("markdown", {}).get("enabled", True),
            sarif_path=output.get("sarif", {}).get("path", ".agentforge/results.sarif"),
            junit_path=output.get("junit", {}).get("path", ".agentforge/results.xml"),
            markdown_path=output.get("markdown", {}).get("path", ".agentforge/results.md"),
            cache_enabled=cache.get("enabled", True),
            cache_path=cache.get("path", ".agentforge/cache/"),
            cache_ttl_hours=cache.get("ttl_hours", 24),
        )

    @classmethod
    def for_github_actions(cls) -> "CIConfig":
        """Create configuration optimized for GitHub Actions."""
        return cls(
            mode=CIMode.PR,
            parallel_enabled=True,
            max_workers=4,
            output_sarif=True,
            output_junit=False,
            output_markdown=True,
        )

    @classmethod
    def for_azure_devops(cls) -> "CIConfig":
        """Create configuration optimized for Azure DevOps."""
        return cls(
            mode=CIMode.PR,
            parallel_enabled=True,
            max_workers=4,
            output_sarif=False,  # Azure doesn't support SARIF natively
            output_junit=True,   # Azure uses JUnit for test results
            output_markdown=True,
        )
