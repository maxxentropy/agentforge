# @spec_file: .agentforge/specs/core-cicd-v1.yaml
# @spec_id: core-cicd-v1
# @component_id: core-cicd-runner
# @test_path: tests/test_python_checks.py

"""
CI Runner
=========

Main orchestrator for CI/CD conformance checking.
Handles parallel execution, caching, and mode-specific logic.

Runs unified contracts from ContractRegistry which includes:
- User-defined contracts (from .agentforge/contracts/)
- Builtin contracts (from contracts/builtin/)
- Operation contracts (from contracts/builtin/operations/)
"""

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from agentforge.core.cicd.baseline import BaselineError, BaselineManager, GitHelper
from agentforge.core.cicd.domain import (
    BaselineComparison,
    CIConfig,
    CIMode,
    CIResult,
    CIViolation,
    ExitCode,
)


class CIRunner:
    """
    Main CI/CD conformance check runner.

    Orchestrates:
    - Check execution in different modes (full, incremental, PR)
    - Parallel execution for performance
    - Caching to avoid redundant checks
    - Baseline comparison for PR mode
    """

    def __init__(self, repo_root: Path, config: CIConfig | None = None):
        """
        Initialize CI runner.

        Args:
            repo_root: Repository root directory
            config: CI configuration (defaults to sensible defaults)
        """
        self.repo_root = repo_root
        self.config = config or CIConfig()
        self.baseline_manager = BaselineManager(
            str(repo_root / self.config.baseline_path)
        )
        self.cache = CheckCache(repo_root / self.config.cache_path) if self.config.cache_enabled else None

    def run(self, contracts: list[dict[str, Any]]) -> CIResult:
        """
        Execute CI conformance check.

        Args:
            contracts: List of contract definitions to check

        Returns:
            CIResult with violations and exit code
        """
        started_at = datetime.utcnow()
        start_time = time.time()

        try:
            # Determine files to check based on mode
            files_to_check = self._get_files_to_check()

            # Filter contracts to applicable ones
            applicable_contracts = self._filter_contracts(contracts, files_to_check)

            # Execute checks (unified - includes operation contracts via ContractRegistry)
            violations = self._execute_checks(applicable_contracts, files_to_check)

            # Handle baseline comparison for PR mode or ratchet mode
            comparison = None
            if self.config.mode == CIMode.PR or self.config.ratchet_enabled:
                comparison = self._compare_baseline(violations)

            # Determine exit code
            exit_code = self._determine_exit_code(violations, comparison)

            completed_at = datetime.utcnow()
            duration = time.time() - start_time

            return CIResult(
                mode=self.config.mode,
                exit_code=exit_code,
                violations=violations,
                comparison=comparison,
                files_checked=len(files_to_check) if files_to_check else 0,
                checks_run=sum(len(c.get("checks", [])) for c in applicable_contracts),
                duration_seconds=duration,
                started_at=started_at,
                completed_at=completed_at,
                commit_sha=self._get_commit_sha(),
                base_ref=self.config.base_ref,
                head_ref=self.config.head_ref,
            )

        except BaselineError as e:
            return self._error_result(
                ExitCode.BASELINE_NOT_FOUND,
                str(e),
                started_at,
                time.time() - start_time,
            )
        except Exception as e:
            return self._error_result(
                ExitCode.RUNTIME_ERROR,
                str(e),
                started_at,
                time.time() - start_time,
            )

    def _get_files_to_check(self) -> set[str] | None:
        """
        Get files to check based on mode.

        Returns:
            Set of file paths for incremental/PR mode, None for full mode
        """
        if self.config.mode == CIMode.FULL:
            return None  # Check all files

        if self.config.incremental_paths:
            return set(self.config.incremental_paths)

        if self.config.base_ref:
            try:
                changed = GitHelper.get_changed_files(
                    self.config.base_ref,
                    self.config.head_ref or "HEAD"
                )
                return set(changed)
            except Exception:
                # Fall back to full check if git fails
                return None

        return None

    def _filter_contracts(
        self,
        contracts: list[dict[str, Any]],
        files_to_check: set[str] | None
    ) -> list[dict[str, Any]]:
        """
        Filter contracts to those applicable to the files being checked.

        For incremental mode, only include contracts that apply to changed files.
        """
        if files_to_check is None:
            return contracts

        applicable = []
        for contract in contracts:
            # Check if any contract applies_to patterns match changed files
            if self._contract_applies_to_files(contract, files_to_check):
                applicable.append(contract)

        return applicable

    def _contract_applies_to_files(
        self,
        contract: dict[str, Any],
        files: set[str]
    ) -> bool:
        """Check if contract applies to any of the given files."""
        from pathlib import PurePath

        checks = contract.get("checks", [])
        for check in checks:
            applies_to = check.get("applies_to", {})
            patterns = applies_to.get("paths", ["**/*"])
            exclude_patterns = applies_to.get("exclude_paths", [])

            for file_path in files:
                # Use PurePath.match for proper ** handling
                path = PurePath(file_path)
                matches = any(path.match(p) for p in patterns)
                excluded = any(path.match(p) for p in exclude_patterns)
                if matches and not excluded:
                    return True

        return False

    def _execute_checks(
        self,
        contracts: list[dict[str, Any]],
        files_to_check: set[str] | None
    ) -> list[CIViolation]:
        """
        Execute all checks, optionally in parallel.

        Args:
            contracts: Contracts to check
            files_to_check: Optional set of files to limit checking

        Returns:
            List of violations found
        """
        # Lazy import to avoid circular imports
        from agentforge.core.contracts_execution import execute_check

        # Flatten to (contract_id, check) pairs
        check_tasks: list[tuple] = []
        for contract in contracts:
            contract_id = contract.get("id", "unknown")
            for check in contract.get("checks", []):
                check_tasks.append((contract_id, check))

        violations: list[CIViolation] = []

        if self.config.parallel_enabled and len(check_tasks) > 1:
            violations = self._execute_parallel(check_tasks, files_to_check, execute_check)
        else:
            violations = self._execute_sequential(check_tasks, files_to_check, execute_check)

        return violations

    def _execute_parallel(
        self,
        check_tasks: list[tuple],
        files_to_check: set[str] | None,
        execute_check_fn
    ) -> list[CIViolation]:
        """Execute checks in parallel using ThreadPoolExecutor."""
        violations: list[CIViolation] = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(
                    self._run_single_check,
                    contract_id, check, files_to_check, execute_check_fn
                ): (contract_id, check)
                for contract_id, check in check_tasks
            }

            for future in as_completed(futures):
                contract_id, check = futures[future]
                try:
                    result_violations = future.result()
                    violations.extend(result_violations)
                except Exception as e:
                    # Log error but continue with other checks
                    violations.append(CIViolation(
                        check_id=check.get("id", "unknown"),
                        file_path="<runtime>",
                        line=None,
                        message=f"Check execution failed: {e}",
                        severity="error",
                        contract_id=contract_id,
                    ))

        return violations

    def _execute_sequential(
        self,
        check_tasks: list[tuple],
        files_to_check: set[str] | None,
        execute_check_fn
    ) -> list[CIViolation]:
        """Execute checks sequentially."""
        violations: list[CIViolation] = []

        for contract_id, check in check_tasks:
            try:
                result_violations = self._run_single_check(
                    contract_id, check, files_to_check, execute_check_fn
                )
                violations.extend(result_violations)
            except Exception as e:
                violations.append(CIViolation(
                    check_id=check.get("id", "unknown"),
                    file_path="<runtime>",
                    line=None,
                    message=f"Check execution failed: {e}",
                    severity="error",
                    contract_id=contract_id,
                ))

        return violations

    def _run_single_check(
        self,
        contract_id: str,
        check: dict[str, Any],
        files_to_check: set[str] | None,
        execute_check_fn
    ) -> list[CIViolation]:
        """
        Run a single check, using cache if available.

        Args:
            contract_id: ID of the contract
            check: Check configuration
            files_to_check: Optional file filter
            execute_check_fn: Function to execute check

        Returns:
            List of violations from this check
        """
        check_id = check.get("id", "unknown")

        # Check cache first
        if self.cache:
            cache_key = self._get_cache_key(check_id, files_to_check)
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # Determine file paths for this check
        file_paths = None
        if files_to_check:
            file_paths = [self.repo_root / f for f in files_to_check if (self.repo_root / f).exists()]

        # Execute check
        results = execute_check_fn(check, self.repo_root, file_paths)

        # Convert to CIViolation
        violations = []
        for result in results:
            if not result.passed:
                violations.append(CIViolation(
                    check_id=result.check_id,
                    file_path=result.file_path or "<unknown>",
                    line=result.line_number,
                    message=result.message,
                    severity=result.severity,
                    rule_id=result.check_id,  # Use check_id as rule_id
                    contract_id=contract_id,
                    fix_hint=result.fix_hint,
                ))

        # Store in cache
        if self.cache:
            cache_key = self._get_cache_key(check_id, files_to_check)
            self.cache.set(cache_key, violations)

        return violations

    def _get_cache_key(self, check_id: str, files: set[str] | None) -> str:
        """Generate cache key for a check."""
        if files is None:
            # For full mode, hash based on check_id only (files may change)
            return f"{check_id}_full"

        # For incremental, include file hashes
        file_hashes = []
        for f in sorted(files):
            file_path = self.repo_root / f
            if file_path.exists():
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()[:8]
                file_hashes.append(f"{f}:{file_hash}")

        combined = f"{check_id}:{'|'.join(file_hashes)}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _compare_baseline(self, violations: list[CIViolation]) -> BaselineComparison:
        """Compare violations against baseline."""
        return self.baseline_manager.compare(violations)

    def _determine_exit_code(
        self,
        violations: list[CIViolation],
        comparison: BaselineComparison | None
    ) -> ExitCode:
        """Determine exit code based on violations and config."""
        # Check absolute threshold
        if self.config.total_errors_threshold:
            error_count = sum(1 for v in violations if v.severity == "error")
            if error_count > self.config.total_errors_threshold:
                return ExitCode.VIOLATIONS_FOUND

        # Ratchet mode: only fail if violations INCREASED from baseline
        if self.config.ratchet_enabled and comparison:
            if comparison.should_fail_ratchet():
                return ExitCode.VIOLATIONS_FOUND
            return ExitCode.SUCCESS

        # For PR mode, use baseline comparison
        if comparison:
            if comparison.should_fail(
                self.config.fail_on_new_errors,
                self.config.fail_on_new_warnings
            ):
                return ExitCode.VIOLATIONS_FOUND
            return ExitCode.SUCCESS

        # For non-PR mode, check violations based on min_severity
        severity_order = ['info', 'warning', 'error']
        min_idx = severity_order.index(self.config.min_severity)

        for severity in severity_order[min_idx:]:
            if any(v.severity == severity for v in violations):
                return ExitCode.VIOLATIONS_FOUND

        return ExitCode.SUCCESS

    def _get_commit_sha(self) -> str | None:
        """Get current commit SHA if available."""
        try:
            return GitHelper.get_current_sha()
        except Exception:
            return None

    def _error_result(
        self,
        exit_code: ExitCode,
        error_message: str,
        started_at: datetime,
        duration: float
    ) -> CIResult:
        """Create error result."""
        return CIResult(
            mode=self.config.mode,
            exit_code=exit_code,
            violations=[],
            comparison=None,
            files_checked=0,
            checks_run=0,
            duration_seconds=duration,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            errors=[error_message],
        )


class CheckCache:
    """
    Simple file-based cache for check results.

    Caches check results by a key derived from check_id and file content hashes.
    Results are stored as JSON with a TTL for automatic expiration.
    """

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours for cache entries
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)

    def get(self, key: str) -> list[CIViolation] | None:
        """
        Get cached result if valid.

        Args:
            key: Cache key

        Returns:
            List of CIViolation if cache hit, None if miss or expired
        """
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)

            # Check TTL
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.utcnow() - cached_at > self.ttl:
                cache_file.unlink()
                return None

            # Deserialize violations
            return [
                CIViolation(**v)
                for v in data["violations"]
            ]
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, key: str, violations: list[CIViolation]) -> None:
        """
        Store result in cache.

        Args:
            key: Cache key
            violations: Violations to cache
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"{key}.json"

        data = {
            "cached_at": datetime.utcnow().isoformat(),
            "violations": [
                {
                    "check_id": v.check_id,
                    "file_path": v.file_path,
                    "line": v.line,
                    "message": v.message,
                    "severity": v.severity,
                    "rule_id": v.rule_id,
                    "contract_id": v.contract_id,
                    "column": v.column,
                    "end_line": v.end_line,
                    "end_column": v.end_column,
                    "fix_hint": v.fix_hint,
                    "code_snippet": v.code_snippet,
                }
                for v in violations
            ]
        }

        with open(cache_file, "w") as f:
            json.dump(data, f)

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        if not self.cache_dir.exists():
            return 0

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def prune_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries pruned
        """
        if not self.cache_dir.exists():
            return 0

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                cached_at = datetime.fromisoformat(data["cached_at"])
                if datetime.utcnow() - cached_at > self.ttl:
                    cache_file.unlink()
                    count += 1
            except (json.JSONDecodeError, KeyError, OSError):
                # Remove corrupted cache files
                cache_file.unlink()
                count += 1

        return count
