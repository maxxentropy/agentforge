# @spec_file: .agentforge/specs/cicd-v1.yaml
# @spec_id: cicd-v1
# @component_id: tools-cicd-baseline
# @test_path: tests/unit/tools/cicd/test_baseline.py

"""
Baseline Management
===================

Handles loading, saving, and comparing violation baselines.
Baselines track known violations to distinguish new issues from tech debt.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from tools.cicd.domain import (
    Baseline,
    BaselineComparison,
    BaselineEntry,
    CIViolation,
)


class BaselineManager:
    """
    Manages violation baselines for CI/CD integration.

    The baseline file stores a snapshot of known violations on the main branch.
    PR checks compare against this to identify new violations (regressions)
    versus existing ones (tech debt).
    """

    def __init__(self, baseline_path: str = ".agentforge/baseline.json"):
        """
        Initialize baseline manager.

        Args:
            baseline_path: Path to the baseline file (relative to repo root)
        """
        self.baseline_path = Path(baseline_path)

    def load(self) -> Optional[Baseline]:
        """
        Load baseline from file.

        Returns:
            Baseline if file exists and is valid, None otherwise
        """
        if not self.baseline_path.exists():
            return None

        try:
            with open(self.baseline_path, "r") as f:
                data = json.load(f)
            return Baseline.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise BaselineError(f"Failed to load baseline: {e}") from e

    def save(self, baseline: Baseline) -> None:
        """
        Save baseline to file.

        Args:
            baseline: The baseline to save
        """
        # Ensure directory exists
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.baseline_path, "w") as f:
            json.dump(baseline.to_dict(), f, indent=2)

    def create_from_violations(
        self,
        violations: List[CIViolation],
        commit_sha: Optional[str] = None
    ) -> Baseline:
        """
        Create a new baseline from current violations.

        Args:
            violations: Current violations to use as baseline
            commit_sha: Optional commit SHA to associate with baseline

        Returns:
            New Baseline containing all violations
        """
        baseline = Baseline.create_empty(commit_sha)
        for violation in violations:
            baseline.add(violation)
        return baseline

    def update(
        self,
        violations: List[CIViolation],
        commit_sha: Optional[str] = None
    ) -> Tuple[Baseline, int, int]:
        """
        Update existing baseline with new violations.

        Adds new violations and marks stale ones (in baseline but not in violations).

        Args:
            violations: Current violations
            commit_sha: Optional commit SHA

        Returns:
            Tuple of (updated baseline, added count, removed count)
        """
        existing = self.load()
        if existing is None:
            baseline = self.create_from_violations(violations, commit_sha)
            return baseline, len(violations), 0

        # Track current violation hashes
        current_hashes = {v.hash for v in violations}

        # Count additions
        added = 0
        for violation in violations:
            if not existing.contains(violation):
                existing.add(violation)
                added += 1
            else:
                # Update last_seen
                existing.add(violation)

        # Count and remove stale entries (optional - could also keep them)
        removed = 0
        stale_hashes = [h for h in existing.entries if h not in current_hashes]
        for h in stale_hashes:
            existing.remove(h)
            removed += 1

        existing.commit_sha = commit_sha
        existing.updated_at = datetime.utcnow()

        return existing, added, removed

    def compare(self, violations: List[CIViolation]) -> BaselineComparison:
        """
        Compare violations against baseline.

        Args:
            violations: Current violations to compare

        Returns:
            BaselineComparison categorizing violations as new/fixed/existing

        Raises:
            BaselineError: If baseline doesn't exist
        """
        baseline = self.load()
        if baseline is None:
            raise BaselineError("Baseline not found. Run 'agentforge ci baseline save' first.")

        return BaselineComparison.compare(violations, baseline)

    def exists(self) -> bool:
        """Check if baseline file exists."""
        return self.baseline_path.exists()

    def get_stats(self) -> Optional[dict]:
        """
        Get statistics about the baseline.

        Returns:
            Dict with baseline stats, or None if baseline doesn't exist
        """
        baseline = self.load()
        if baseline is None:
            return None

        entries = list(baseline.entries.values())
        by_check: dict = {}
        by_file: dict = {}

        for entry in entries:
            by_check[entry.check_id] = by_check.get(entry.check_id, 0) + 1
            by_file[entry.file_path] = by_file.get(entry.file_path, 0) + 1

        return {
            "total_entries": len(entries),
            "created_at": baseline.created_at.isoformat(),
            "updated_at": baseline.updated_at.isoformat(),
            "commit_sha": baseline.commit_sha,
            "by_check": by_check,
            "by_file": by_file,
            "oldest_entry": min((e.first_seen for e in entries), default=None),
            "newest_entry": max((e.last_seen for e in entries), default=None),
        }


class GitHelper:
    """
    Git operations for CI/CD integration.

    Provides methods to get changed files for incremental checking
    and commit information.
    """

    @staticmethod
    def get_changed_files(base_ref: str, head_ref: str = "HEAD") -> List[str]:
        """
        Get list of files changed between two refs.

        Args:
            base_ref: Base reference (e.g., 'origin/main', commit SHA)
            head_ref: Head reference (default: HEAD)

        Returns:
            List of changed file paths
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            return files
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to get changed files: {e.stderr}") from e

    @staticmethod
    def get_merge_base(ref1: str, ref2: str = "HEAD") -> str:
        """
        Get the merge base between two refs.

        Args:
            ref1: First reference
            ref2: Second reference

        Returns:
            Merge base commit SHA
        """
        try:
            result = subprocess.run(
                ["git", "merge-base", ref1, ref2],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to get merge base: {e.stderr}") from e

    @staticmethod
    def get_current_sha() -> str:
        """Get the current HEAD commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to get current SHA: {e.stderr}") from e

    @staticmethod
    def get_current_branch() -> str:
        """Get the current branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to get current branch: {e.stderr}") from e

    @staticmethod
    def is_git_repo() -> bool:
        """Check if current directory is a git repository."""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_repo_root() -> Path:
        """Get the root directory of the git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to get repo root: {e.stderr}") from e

    @staticmethod
    def file_exists_at_ref(file_path: str, ref: str) -> bool:
        """Check if a file exists at a specific ref."""
        try:
            subprocess.run(
                ["git", "cat-file", "-e", f"{ref}:{file_path}"],
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False


class BaselineError(Exception):
    """Error related to baseline operations."""
    pass


class GitError(Exception):
    """Error related to git operations."""
    pass
