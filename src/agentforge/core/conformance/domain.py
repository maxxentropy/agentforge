"""
Conformance Domain Entities
===========================

Pure domain objects for conformance tracking. No I/O operations.
These entities represent the core business logic for tracking violations,
exemptions, and conformance state.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict
import hashlib
import fnmatch


class Severity(Enum):
    """Canonical severity levels for violations."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"

    @classmethod
    def from_contract_severity(cls, severity: str) -> "Severity":
        """Map contract severity to conformance severity."""
        mapping = {
            "error": cls.BLOCKER,
            "warning": cls.MAJOR,
            "info": cls.MINOR,
        }
        return mapping.get(severity.lower(), cls.MAJOR)

    @property
    def weight(self) -> int:
        """Numeric weight for sorting (higher = more severe)."""
        weights = {
            Severity.BLOCKER: 5,
            Severity.CRITICAL: 4,
            Severity.MAJOR: 3,
            Severity.MINOR: 2,
            Severity.INFO: 1,
        }
        return weights.get(self, 0)


class ViolationStatus(Enum):
    """Possible states for a violation."""
    OPEN = "open"
    RESOLVED = "resolved"
    EXEMPTION_EXPIRED = "exemption_expired"
    STALE = "stale"


class ExemptionStatus(Enum):
    """Possible states for an exemption."""
    ACTIVE = "active"
    EXPIRED = "expired"
    RESOLVED = "resolved"
    UNDER_REVIEW = "under_review"


class ExemptionScopeType(Enum):
    """Types of exemption scope."""
    CHECK_ID = "check_id"
    FILE_PATTERN = "file_pattern"
    VIOLATION_ID = "violation_id"
    GLOBAL = "global"


@dataclass
class ExemptionScope:
    """Defines what violations an exemption covers."""
    type: ExemptionScopeType
    patterns: Optional[List[str]] = None
    violation_ids: Optional[List[str]] = None
    lines: Optional[tuple] = None  # (start, end)

    def matches_file(self, file_path: str) -> bool:
        """Check if file path matches scope patterns."""
        if self.type == ExemptionScopeType.GLOBAL:
            return True
        if self.type == ExemptionScopeType.FILE_PATTERN and self.patterns:
            return any(fnmatch.fnmatch(file_path, p) for p in self.patterns)
        return False

    def matches_violation_id(self, violation_id: str) -> bool:
        """Check if violation ID matches scope."""
        if self.type == ExemptionScopeType.GLOBAL:
            return True
        if self.type == ExemptionScopeType.VIOLATION_ID and self.violation_ids:
            return violation_id in self.violation_ids
        return False

    def matches_line(self, line_number: Optional[int]) -> bool:
        """Check if line number falls within scope."""
        if not self.lines:
            return True
        if not line_number:
            return True
        start, end = self.lines
        return start <= line_number <= end


@dataclass
class Violation:
    """Individual violation record."""
    violation_id: str
    contract_id: str
    check_id: str
    severity: Severity
    file_path: str
    message: str
    detected_at: datetime
    last_seen_at: datetime
    status: ViolationStatus
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    rule_id: Optional[str] = None
    fix_hint: Optional[str] = None
    code_snippet: Optional[str] = None
    resolution: Optional[Dict] = None
    exemption_id: Optional[str] = None
    exemption_expired_at: Optional[datetime] = None
    # Test path for verification during fixes - computed at detection time
    # This is the path to run pytest on to verify changes don't break tests
    test_path: Optional[str] = None

    @staticmethod
    def generate_id(
        contract_id: str,
        check_id: str,
        file_path: str,
        line_number: Optional[int],
        rule_id: Optional[str] = None
    ) -> str:
        """
        Generate deterministic violation ID from composite key.

        The ID is based on a SHA-256 hash of the key components, ensuring
        the same violation produces the same ID across runs.

        Args:
            contract_id: The contract that was violated
            check_id: The specific check within the contract
            file_path: Path to the file containing the violation
            line_number: Line number (or None for file-level violations)
            rule_id: Optional rule ID for compound checks

        Returns:
            Violation ID in format V-{12 hex chars}
        """
        # Normalize file path for consistent hashing
        normalized_path = file_path.replace("\\", "/")
        line_str = str(line_number) if line_number else "file"
        rule_str = rule_id or ""

        composite = f"{contract_id}|{check_id}|{normalized_path}|{line_str}|{rule_str}"
        hash_digest = hashlib.sha256(composite.encode()).hexdigest()[:12]
        return f"V-{hash_digest}"

    @staticmethod
    def compute_test_path(file_path: str, project_root: "Path") -> Optional[str]:
        """
        Compute the test path for verifying changes to a file.

        This is called at violation detection time and stored with the violation.
        The test_path tells the fix workflow which tests to run to verify
        that changes don't break existing functionality.

        Strategy (in order of preference):
        1. Read lineage metadata from file (explicit, auditable)
        2. Read from codebase_profile.yaml test linkage (brownfield discovery)
        3. Fall back to convention-based detection (legacy files)

        Args:
            file_path: Path to the file with the violation (relative to project)
            project_root: Project root path for existence checks

        Returns:
            Test path to run, or None for no specific tests
        """
        from pathlib import Path as P

        # STRATEGY 1: Try to read lineage metadata from the file
        # This is the preferred path - explicit linkage from the spec/generation chain
        try:
            from agentforge.core.lineage import parse_lineage_from_file
            full_path = project_root / file_path
            if full_path.exists():
                lineage = parse_lineage_from_file(full_path)
                if lineage and lineage.test_path:
                    # Lineage provides explicit test path - use it
                    return lineage.test_path
        except ImportError:
            pass  # Lineage module not available, use fallback

        # STRATEGY 2: Read from codebase_profile.yaml test linkage
        # This is populated by brownfield discovery and gives explicit mappings
        try:
            import yaml
            profile_path = project_root / ".agentforge" / "codebase_profile.yaml"
            if profile_path.exists():
                profile_data = yaml.safe_load(profile_path.read_text())
                test_analysis = profile_data.get("test_analysis")
                if test_analysis and "linkages" in test_analysis:
                    linkages = test_analysis["linkages"]
                    # linkages is a dict: {source_path: [test_paths]}
                    if file_path in linkages and linkages[file_path]:
                        # Return the first (primary) test path
                        return linkages[file_path][0]
        except Exception:
            pass  # Profile not available or malformed, use fallback

        # STRATEGY 3: Convention-based detection (fallback for legacy files)

        # Test files run themselves
        if file_path.startswith("tests/") and "/test_" in file_path:
            if (project_root / file_path).exists():
                return file_path

        # conftest.py runs the containing directory
        if file_path.endswith("conftest.py"):
            parent = str(P(file_path).parent)
            if (project_root / parent).exists():
                return parent

        # Source files - find corresponding test directory
        # Convention: tools/X/... -> tests/unit/tools/X/
        if file_path.startswith("tools/"):
            parts = file_path.split("/")
            if len(parts) >= 2:
                # tools/conformance/... -> tests/unit/tools/conformance/
                test_dir = f"tests/unit/tools/{parts[1]}/"
                if (project_root / test_dir).exists():
                    return test_dir
                # Fallback to tools test directory
                fallback = "tests/unit/tools/"
                if (project_root / fallback).exists():
                    return fallback

        # CLI files -> integration tests
        if file_path.startswith("cli/"):
            test_dir = "tests/integration/cli/"
            if (project_root / test_dir).exists():
                return test_dir
            fallback = "tests/integration/"
            if (project_root / fallback).exists():
                return fallback

        # No specific test path - will run all tests (or skip verification)
        return None

    def mark_resolved(self, reason: str, resolved_by: str = "system") -> None:
        """Mark violation as resolved."""
        self.status = ViolationStatus.RESOLVED
        self.resolution = {
            "resolved_at": datetime.utcnow().isoformat(),
            "resolved_by": resolved_by,
            "reason": reason,
        }

    def mark_stale(self) -> None:
        """Mark violation as stale (not checked in incremental run)."""
        self.status = ViolationStatus.STALE

    def mark_exemption_expired(self) -> None:
        """Mark violation as having an expired exemption."""
        self.status = ViolationStatus.EXEMPTION_EXPIRED
        self.exemption_expired_at = datetime.utcnow()

    def reopen(self) -> None:
        """Reopen a resolved or stale violation."""
        self.status = ViolationStatus.OPEN
        self.resolution = None


@dataclass
class Exemption:
    """Approved exception to contract checks."""
    id: str
    contract_id: str
    check_ids: List[str]
    reason: str
    approved_by: str
    approved_date: date
    status: ExemptionStatus
    scope: ExemptionScope
    expires: Optional[date] = None
    review_date: Optional[date] = None
    notes: Optional[str] = None
    ticket: Optional[str] = None
    tags: Optional[List[str]] = None

    def is_expired(self) -> bool:
        """Check if exemption has expired."""
        if not self.expires:
            return False
        return date.today() > self.expires

    def is_active(self) -> bool:
        """Check if exemption is currently active."""
        return self.status == ExemptionStatus.ACTIVE and not self.is_expired()

    def needs_review(self) -> bool:
        """Check if exemption is due for review."""
        if not self.review_date:
            return False
        return date.today() >= self.review_date

    def covers_check(self, check_id: str) -> bool:
        """Check if this exemption covers a specific check."""
        return "*" in self.check_ids or check_id in self.check_ids

    def covers_violation(self, violation: "Violation") -> bool:
        """
        Check if this exemption covers a violation.

        An exemption covers a violation if:
        1. Same contract
        2. Check is covered (explicit or wildcard)
        3. Exemption is active (not expired)
        4. Scope matches the violation location
        """
        if violation.contract_id != self.contract_id:
            return False
        if not self.covers_check(violation.check_id):
            return False
        if not self.is_active():
            return False

        # Check scope
        if self.scope.type == ExemptionScopeType.GLOBAL:
            return True
        if self.scope.type == ExemptionScopeType.CHECK_ID:
            return True  # Already checked above
        if self.scope.type == ExemptionScopeType.FILE_PATTERN:
            if not self.scope.matches_file(violation.file_path):
                return False
            return self.scope.matches_line(violation.line_number)
        if self.scope.type == ExemptionScopeType.VIOLATION_ID:
            return self.scope.matches_violation_id(violation.violation_id)

        return False


@dataclass
class ConformanceSummary:
    """Aggregate counts for conformance state."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    exempted: int = 0
    stale: int = 0

    def __post_init__(self):
        """Validate invariant: total >= passed + failed + exempted."""
        # Note: stale violations are not included in total for active checks
        if self.total < self.passed + self.failed + self.exempted:
            # Adjust total if needed (for flexibility during construction)
            self.total = self.passed + self.failed + self.exempted + self.stale

    @property
    def compliance_rate(self) -> float:
        """Calculate compliance rate (0.0 to 1.0)."""
        if self.total == 0:
            return 1.0
        return self.passed / self.total

    @property
    def open_issues(self) -> int:
        """Count of issues requiring attention (failed + stale)."""
        return self.failed + self.stale


@dataclass
class ConformanceReport:
    """Current conformance state for a repository."""
    schema_version: str
    generated_at: datetime
    run_id: str
    run_type: str  # "full" or "incremental"
    summary: ConformanceSummary
    by_severity: Dict[str, int]
    by_contract: Dict[str, int]
    contracts_checked: List[str]
    files_checked: int
    trend: Optional[Dict] = None

    def has_blockers(self) -> bool:
        """Check if there are any blocker-level violations."""
        return self.by_severity.get("blocker", 0) > 0

    def has_critical(self) -> bool:
        """Check if there are any critical-level violations."""
        return self.by_severity.get("critical", 0) > 0

    def is_passing(self, threshold: Severity = Severity.BLOCKER) -> bool:
        """
        Check if conformance passes at a given severity threshold.

        Args:
            threshold: Minimum severity to fail on

        Returns:
            True if no violations at or above threshold
        """
        for severity_name, count in self.by_severity.items():
            if count > 0:
                try:
                    severity = Severity(severity_name)
                    if severity.weight >= threshold.weight:
                        return False
                except ValueError:
                    continue
        return True


@dataclass
class HistorySnapshot:
    """Point-in-time summary for trend analysis."""
    schema_version: str
    date: date
    generated_at: datetime
    summary: ConformanceSummary
    by_severity: Dict[str, int]
    by_contract: Dict[str, int]
    files_analyzed: int
    contracts_checked: List[str]

    def delta_from(self, previous: "HistorySnapshot") -> Dict[str, int]:
        """Calculate delta from a previous snapshot."""
        return {
            "total_delta": self.summary.total - previous.summary.total,
            "passed_delta": self.summary.passed - previous.summary.passed,
            "failed_delta": self.summary.failed - previous.summary.failed,
            "exempted_delta": self.summary.exempted - previous.summary.exempted,
        }
