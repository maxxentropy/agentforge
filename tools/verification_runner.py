#!/usr/bin/env python3
"""
Verification Runner
====================

Deterministic verification engine that runs actual checks instead of LLM judgment.
Implements "Correctness is Upstream" philosophy.

Check Types:
  - command: Shell commands (dotnet build, dotnet test, etc.)
  - regex: Pattern matching on source files
  - file_exists: Verify required files exist
  - import_check: Verify layer/import dependencies
  - custom: Python function for complex checks
  - contracts: Run contract-based checks from the contracts module

Usage:
    python tools/verification_runner.py --profile ci --project MyProject.csproj
    python tools/verification_runner.py --checks compile_check,test_check
"""

import ast
import os
import re
import sys
import yaml
import glob
import shlex
import subprocess
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import fnmatch
import json

# Import our runners
try:
    from .pyright_runner import PyrightRunner
    from .command_runner import CommandRunner
except ImportError:
    # Allow running as standalone script
    from pyright_runner import PyrightRunner
    from command_runner import CommandRunner


class Severity(Enum):
    BLOCKING = "blocking"
    REQUIRED = "required"
    ADVISORY = "advisory"
    INFORMATIONAL = "informational"


class CheckStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class CheckResult:
    """Result of a single verification check."""
    check_id: str
    check_name: str
    status: CheckStatus
    severity: Severity
    message: str
    duration_ms: int = 0
    details: Optional[str] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    output: Optional[str] = None
    fix_suggestion: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASSED

    @property
    def is_blocking_failure(self) -> bool:
        return not self.passed and self.severity == Severity.BLOCKING


@dataclass
class VerificationReport:
    """Complete verification report with all check results."""
    timestamp: str
    profile: Optional[str]
    project_path: Optional[str]
    working_dir: str
    total_checks: int
    passed: int
    failed: int
    skipped: int
    errors: int
    blocking_failures: int
    required_failures: int
    advisory_warnings: int
    duration_ms: int
    results: List[CheckResult] = field(default_factory=list)
    is_valid: bool = True

    def add_result(self, result: CheckResult):
        self.results.append(result)
        if result.status == CheckStatus.PASSED:
            self.passed += 1
        elif result.status == CheckStatus.FAILED:
            self.failed += 1
            if result.severity == Severity.BLOCKING:
                self.blocking_failures += 1
                self.is_valid = False
            elif result.severity == Severity.REQUIRED:
                self.required_failures += 1
            elif result.severity == Severity.ADVISORY:
                self.advisory_warnings += 1
        elif result.status == CheckStatus.SKIPPED:
            self.skipped += 1
        elif result.status == CheckStatus.ERROR:
            self.errors += 1
            if result.severity == Severity.BLOCKING:
                self.is_valid = False


class VerificationRunner:
    """
    Runs verification checks defined in correctness.yaml.

    Replaces LLM-based validation with deterministic verification.
    """

    def __init__(self, config_path: Path = None, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.config_path = config_path or self.project_root / "config" / "correctness.yaml"
        self.config = self._load_config()
        self.context: Dict[str, Any] = {}

        # Initialize runners (lazy loading to avoid import errors if tools not installed)
        self._pyright_runner = None
        self._command_runner = None

    @property
    def pyright_runner(self) -> PyrightRunner:
        """Lazy-load pyright runner."""
        if self._pyright_runner is None:
            self._pyright_runner = PyrightRunner(self.project_root)
        return self._pyright_runner

    @property
    def command_runner(self) -> CommandRunner:
        """Lazy-load command runner."""
        if self._command_runner is None:
            self._command_runner = CommandRunner(self.project_root)
        return self._command_runner

    def _load_config(self) -> Dict[str, Any]:
        """Load verification configuration."""
        if not self.config_path.exists():
            return {"checks": [], "profiles": {}, "settings": {}}

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def set_context(self, **kwargs):
        """Set context variables for template substitution."""
        self.context.update(kwargs)

    def _substitute_variables(self, text: str) -> str:
        """Replace {variable} placeholders with context values."""
        if not text or not isinstance(text, str):
            return text

        result = text
        for key, value in self.context.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        return result

    def get_checks_for_profile(self, profile_name: str) -> List[Dict]:
        """Get check definitions for a profile."""
        profiles = self.config.get("profiles", {})
        profile = profiles.get(profile_name)

        if not profile:
            raise ValueError(f"Unknown profile: {profile_name}")

        check_ids = profile.get("checks", [])
        all_checks = {c["id"]: c for c in self.config.get("checks", [])}

        if check_ids == "all":
            return list(all_checks.values())

        return [all_checks[cid] for cid in check_ids if cid in all_checks]

    def get_checks_by_ids(self, check_ids: List[str]) -> List[Dict]:
        """Get specific checks by ID."""
        all_checks = {c["id"]: c for c in self.config.get("checks", [])}
        return [all_checks[cid] for cid in check_ids if cid in all_checks]

    def run_profile(self, profile_name: str) -> VerificationReport:
        """Run all checks in a profile."""
        checks = self.get_checks_for_profile(profile_name)
        profile = self.config.get("profiles", {}).get(profile_name, {})
        settings = {**self.config.get("settings", {}), **profile.get("settings", {})}

        return self._run_checks(checks, settings, profile_name)

    def run_checks(self, check_ids: List[str] = None, all_checks: bool = False) -> VerificationReport:
        """Run specific checks or all checks."""
        if all_checks:
            checks = self.config.get("checks", [])
        elif check_ids:
            checks = self.get_checks_by_ids(check_ids)
        else:
            checks = self.config.get("checks", [])

        settings = self.config.get("settings", {})
        return self._run_checks(checks, settings, None)

    def _run_checks(
        self,
        checks: List[Dict],
        settings: Dict[str, Any],
        profile: Optional[str]
    ) -> VerificationReport:
        """Execute a list of checks and generate report."""
        start_time = datetime.now()

        report = VerificationReport(
            timestamp=start_time.isoformat() + "Z",
            profile=profile,
            project_path=self.context.get("project_path"),
            working_dir=str(self.project_root),
            total_checks=len(checks),
            passed=0,
            failed=0,
            skipped=0,
            errors=0,
            blocking_failures=0,
            required_failures=0,
            advisory_warnings=0,
            duration_ms=0,
        )

        fail_fast = settings.get("fail_fast", False)
        completed_checks = set()

        # Build dependency graph
        check_deps = {c["id"]: c.get("depends_on", []) for c in checks}

        # Run checks respecting dependencies
        for check in checks:
            check_id = check["id"]

            # Check dependencies
            deps = check.get("depends_on", [])
            deps_met = all(
                d in completed_checks and
                any(r.check_id == d and r.passed for r in report.results)
                for d in deps
            )

            if not deps_met and deps:
                result = CheckResult(
                    check_id=check_id,
                    check_name=check.get("name", check_id),
                    status=CheckStatus.SKIPPED,
                    severity=Severity(check.get("severity", "required")),
                    message=f"Skipped due to failed dependencies: {deps}",
                )
                report.add_result(result)
                continue

            # Run the check
            result = self.run_check(check, settings)
            report.add_result(result)
            completed_checks.add(check_id)

            # Fail fast if blocking failure
            if fail_fast and result.is_blocking_failure:
                # Skip remaining checks
                for remaining in checks:
                    if remaining["id"] not in completed_checks:
                        skip_result = CheckResult(
                            check_id=remaining["id"],
                            check_name=remaining.get("name", remaining["id"]),
                            status=CheckStatus.SKIPPED,
                            severity=Severity(remaining.get("severity", "required")),
                            message="Skipped due to fail_fast on previous blocking failure",
                        )
                        report.add_result(skip_result)
                break

        end_time = datetime.now()
        report.duration_ms = int((end_time - start_time).total_seconds() * 1000)

        return report

    def run_check(self, check: Dict, settings: Dict[str, Any] = None) -> CheckResult:
        """Run a single verification check."""
        settings = settings or {}
        check_id = check["id"]
        check_name = check.get("name", check_id)
        check_type = check.get("type", "command")
        severity = Severity(check.get("severity", "required"))

        start_time = datetime.now()

        try:
            if check_type == "command":
                result = self._run_command_check(check, settings)
            elif check_type == "regex":
                result = self._run_regex_check(check, settings)
            elif check_type == "file_exists":
                result = self._run_file_exists_check(check, settings)
            elif check_type == "import_check":
                result = self._run_import_check(check, settings)
            elif check_type == "custom":
                result = self._run_custom_check(check, settings)
            elif check_type == "contracts":
                result = self._run_contracts_check(check, settings)
            elif check_type == "lsp_query":
                result = self._run_lsp_query_check(check, settings)
            elif check_type == "ast_check":
                result = self._run_ast_check(check, settings)
            else:
                result = CheckResult(
                    check_id=check_id,
                    check_name=check_name,
                    status=CheckStatus.ERROR,
                    severity=severity,
                    message=f"Unknown check type: {check_type}",
                )

        except Exception as e:
            result = CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"Check raised exception: {str(e)}",
                details=str(e),
            )

        end_time = datetime.now()
        result.duration_ms = int((end_time - start_time).total_seconds() * 1000)
        result.fix_suggestion = check.get("fix_suggestion")

        return result

    def _run_command_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a shell command check."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        command = self._substitute_variables(check["command"])
        working_dir = self._substitute_variables(
            check.get("working_dir", settings.get("working_dir", "."))
        )
        timeout = check.get("timeout", settings.get("default_timeout", 300))

        # Resolve working directory
        if not os.path.isabs(working_dir):
            working_dir = str(self.project_root / working_dir)

        try:
            # Parse command string into list to avoid shell=True security risk
            # If shell features are needed, use explicit shell invocation in config:
            # command: "sh -c 'complex | command'"
            if isinstance(command, str):
                command_list = shlex.split(command)
            else:
                command_list = command

            result = subprocess.run(
                command_list,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                env={**os.environ, "NO_COLOR": "1"},
            )

            output = result.stdout + result.stderr
            passed = result.returncode == 0

            # Check for success/failure indicators
            success_indicators = check.get("success_indicators", [])
            failure_indicators = check.get("failure_indicators", [])

            if passed and failure_indicators:
                for indicator in failure_indicators:
                    if indicator in output:
                        passed = False
                        break

            if not passed and success_indicators:
                for indicator in success_indicators:
                    if indicator in output:
                        passed = True
                        break

            # Parse structured errors if available
            errors = []
            error_parser = check.get("error_parser")
            if error_parser and not passed:
                pattern = error_parser["pattern"]
                for match in re.finditer(pattern, output):
                    errors.append(match.groupdict())

            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity,
                message=check.get("message", f"Command {'succeeded' if passed else 'failed'}"),
                output=output[:5000] if len(output) > 5000 else output,
                errors=errors,
                details=f"Exit code: {result.returncode}",
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"Command timed out after {timeout}s",
            )

        except Exception as e:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"Command execution failed: {str(e)}",
            )

    def _run_regex_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a regex pattern check on source files."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        # Get patterns (single or multiple)
        patterns = check.get("patterns", [])
        if not patterns and check.get("pattern"):
            patterns = [{"name": "pattern", "pattern": check["pattern"]}]

        negative_match = check.get("negative_match", False)

        # Get file patterns
        include_patterns = check.get(
            "file_patterns",
            settings.get("include_patterns", ["**/*.cs"])
        )
        exclude_patterns = check.get(
            "exclude_patterns",
            settings.get("exclude_patterns", [])
        )

        # Find matching files
        all_files = []
        for pattern in include_patterns:
            pattern = self._substitute_variables(pattern)
            matches = glob.glob(str(self.project_root / pattern), recursive=True)
            all_files.extend(matches)

        # Filter exclusions
        files = []
        for f in all_files:
            rel_path = os.path.relpath(f, self.project_root)
            excluded = any(
                fnmatch.fnmatch(rel_path, self._substitute_variables(exc))
                for exc in exclude_patterns
            )
            if not excluded:
                files.append(f)

        # Search for patterns
        matches_found = []

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for pat_def in patterns:
                    pat_name = pat_def.get("name", "pattern")
                    pattern = pat_def["pattern"]

                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count("\n") + 1
                        rel_path = os.path.relpath(file_path, self.project_root)
                        matches_found.append({
                            "file": rel_path,
                            "line": line_num,
                            "pattern_name": pat_name,
                            "match": match.group()[:100],
                        })
            except Exception:
                continue

        # Determine pass/fail
        if negative_match:
            # Pattern should NOT be found
            passed = len(matches_found) == 0
            message = (
                check.get("message", f"Pattern should not match")
                if not passed else "No forbidden patterns found"
            )
        else:
            # Pattern SHOULD be found
            passed = len(matches_found) > 0
            message = (
                check.get("message", f"Pattern should match")
                if not passed else f"Found {len(matches_found)} match(es)"
            )

        return CheckResult(
            check_id=check_id,
            check_name=check_name,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            severity=severity,
            message=message,
            errors=[
                {"file": m["file"], "line": m["line"], "match": m["match"]}
                for m in matches_found[:20]  # Limit to first 20
            ] if not passed and negative_match else [],
            details=f"Searched {len(files)} files, found {len(matches_found)} matches",
        )

    def _run_file_exists_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Check if required files exist."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        files = check.get("files", [])
        missing = []
        found = []

        for file_spec in files:
            if isinstance(file_spec, str):
                file_path = file_spec
                file_message = f"{file_spec} not found"
            else:
                file_path = file_spec.get("path")
                file_message = file_spec.get("message", f"{file_path} not found")

            file_path = self._substitute_variables(file_path)
            full_path = self.project_root / file_path

            if full_path.exists():
                found.append(file_path)
            else:
                missing.append({"path": file_path, "message": file_message})

        passed = len(missing) == 0

        return CheckResult(
            check_id=check_id,
            check_name=check_name,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            severity=severity,
            message=check.get("message", "All required files exist") if passed else f"Missing {len(missing)} file(s)",
            errors=missing,
            details=f"Found {len(found)} of {len(files)} required files",
        )

    def _run_import_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Check import/dependency rules (layer isolation)."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        rules = check.get("rules", [])
        violations = []

        for rule in rules:
            source_pattern = self._substitute_variables(rule["source_pattern"])
            forbidden_imports = rule.get("forbidden_imports", [])

            # Find source files
            source_files = glob.glob(
                str(self.project_root / source_pattern),
                recursive=True
            )

            for source_file in source_files:
                try:
                    with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Check for using statements
                    using_pattern = r"using\s+([a-zA-Z0-9_.]+)\s*;"
                    usings = re.findall(using_pattern, content)

                    for using in usings:
                        for forbidden in forbidden_imports:
                            if forbidden in using:
                                rel_path = os.path.relpath(source_file, self.project_root)
                                line_num = None
                                for i, line in enumerate(content.split("\n"), 1):
                                    if f"using {using}" in line:
                                        line_num = i
                                        break

                                violations.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "import": using,
                                    "forbidden": forbidden,
                                    "message": rule.get("message", f"Forbidden import: {forbidden}"),
                                })
                except Exception:
                    continue

        passed = len(violations) == 0

        return CheckResult(
            check_id=check_id,
            check_name=check_name,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            severity=severity,
            message=check.get("message", "Layer dependencies OK") if passed else f"Found {len(violations)} violation(s)",
            errors=violations[:20],
            details=f"Checked {len(rules)} rules",
        )

    def _run_custom_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a custom Python function check."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        function_path = check.get("function")
        parameters = check.get("parameters", {})

        # Substitute variables in parameters
        for key, value in parameters.items():
            if isinstance(value, str):
                parameters[key] = self._substitute_variables(value)

        try:
            # Parse module.function path
            parts = function_path.rsplit(".", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid function path: {function_path}")

            module_name, func_name = parts

            # Try to import from tools directory
            tools_dir = Path(__file__).parent
            module_file = tools_dir / f"{module_name}.py"

            if module_file.exists():
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                module = importlib.import_module(module_name)

            func = getattr(module, func_name)

            # Call the function
            result = func(
                project_root=self.project_root,
                context=self.context,
                **parameters
            )

            # Handle different return types
            if isinstance(result, CheckResult):
                return result
            elif isinstance(result, dict):
                return CheckResult(
                    check_id=check_id,
                    check_name=check_name,
                    status=CheckStatus.PASSED if result.get("passed", False) else CheckStatus.FAILED,
                    severity=severity,
                    message=result.get("message", check.get("message", "")),
                    errors=result.get("errors", []),
                    details=result.get("details"),
                )
            elif isinstance(result, bool):
                return CheckResult(
                    check_id=check_id,
                    check_name=check_name,
                    status=CheckStatus.PASSED if result else CheckStatus.FAILED,
                    severity=severity,
                    message=check.get("message", ""),
                )
            else:
                return CheckResult(
                    check_id=check_id,
                    check_name=check_name,
                    status=CheckStatus.ERROR,
                    severity=severity,
                    message=f"Custom check returned unexpected type: {type(result)}",
                )

        except Exception as e:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"Custom check failed: {str(e)}",
                details=str(e),
            )

    def _run_contracts_check(self, check: Dict, settings: Dict) -> CheckResult:
        """
        Run contract-based checks using the contracts module.

        This integrates the contract system with the verification runner,
        allowing contracts to be run as part of verification profiles.

        Config options:
          - contract: Specific contract name to run (optional)
          - language: Filter by language (optional)
          - repo_type: Filter by repo type (optional)
          - fail_on_warning: Treat warnings as failures (default: false)
        """
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        try:
            from contracts import ContractRegistry, run_contract, run_all_contracts

            # Get config options
            contract_name = check.get("contract")
            language = check.get("language")
            repo_type = check.get("repo_type")
            fail_on_warning = check.get("fail_on_warning", False)

            # Run contracts
            if contract_name:
                # Run specific contract
                registry = ContractRegistry(self.project_root)
                contract = registry.get_contract(contract_name)
                if not contract:
                    return CheckResult(
                        check_id=check_id,
                        check_name=check_name,
                        status=CheckStatus.ERROR,
                        severity=severity,
                        message=f"Contract not found: {contract_name}",
                    )
                results = [run_contract(contract, self.project_root, registry)]
            else:
                # Run all applicable contracts
                results = run_all_contracts(
                    self.project_root,
                    language=language,
                    repo_type=repo_type
                )

            # Aggregate results
            total_errors = sum(len(r.errors) for r in results)
            total_warnings = sum(len(r.warnings) for r in results)
            total_exempted = sum(r.exempted_count for r in results)
            all_passed = all(r.passed for r in results)

            # Determine pass/fail
            if fail_on_warning:
                passed = all_passed and total_warnings == 0
            else:
                passed = all_passed

            # Build error details
            errors = []
            for result in results:
                for check_result in result.check_results:
                    if not check_result.passed and not check_result.exempted:
                        errors.append({
                            "contract": result.contract_name,
                            "check": check_result.check_id,
                            "severity": check_result.severity,
                            "message": check_result.message,
                            "file": check_result.file_path,
                            "line": check_result.line_number,
                        })

            message = f"Ran {len(results)} contracts: {total_errors} errors, {total_warnings} warnings"
            if total_exempted > 0:
                message += f", {total_exempted} exempted"

            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity,
                message=message,
                errors=errors[:50],  # Limit to first 50
                details=f"Contracts: {', '.join(r.contract_name for r in results)}",
            )

        except ImportError as e:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"Could not import contracts module: {e}",
            )
        except Exception as e:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"Contracts check failed: {str(e)}",
                details=str(e),
            )

    def _run_lsp_query_check(self, check: Dict, settings: Dict) -> CheckResult:
        """
        Run semantic Python analysis using pyright CLI.

        NOTE: This uses pyright as a subprocess with --outputjson,
        NOT an actual LSP server connection.

        Config options:
            - file_patterns: Glob patterns for files to check
            - severity_filter: Which severities to report (error, warning, information)
            - rules: Specific pyright rules to check (optional)
        """
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        try:
            # Get file patterns to check
            file_patterns = check.get(
                "file_patterns",
                settings.get("include_patterns", ["**/*.py"])
            )
            exclude_patterns = check.get(
                "exclude_patterns",
                settings.get("exclude_patterns", [])
            )
            severity_filter = check.get("severity_filter", ["error"])

            # Find matching files
            all_files = []
            for pattern in file_patterns:
                pattern = self._substitute_variables(pattern)
                matches = glob.glob(str(self.project_root / pattern), recursive=True)
                all_files.extend(matches)

            # Filter exclusions
            files = []
            for f in all_files:
                rel_path = os.path.relpath(f, self.project_root)
                excluded = any(
                    fnmatch.fnmatch(rel_path, self._substitute_variables(exc))
                    for exc in exclude_patterns
                )
                if not excluded:
                    files.append(f)

            # Run pyright on the project (more efficient than per-file)
            result = self.pyright_runner.check_project()

            # Filter diagnostics to only files in our list
            file_set = set(str(Path(f).resolve()) for f in files)
            filtered_diags = []

            for diag in result.diagnostics:
                diag_path = str(Path(diag.file).resolve()) if diag.file else ""
                if diag_path in file_set and diag.severity in severity_filter:
                    filtered_diags.append(diag)

            # Build error details
            errors = [
                {
                    "file": os.path.relpath(d.file, self.project_root) if d.file else "",
                    "line": d.line,
                    "column": d.column,
                    "message": d.message,
                    "rule": d.rule,
                    "severity": d.severity,
                }
                for d in filtered_diags[:50]  # Limit to first 50
            ]

            passed = len(filtered_diags) == 0
            message = (
                f"Found {len(filtered_diags)} type issues"
                if not passed
                else f"Type check passed ({result.files_analyzed} files analyzed)"
            )

            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity,
                message=message,
                errors=errors,
                details=f"Analyzed {len(files)} files, {result.error_count} errors, {result.warning_count} warnings",
            )

        except RuntimeError as e:
            # Pyright not installed
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=str(e),
                details="Install pyright with: pip install pyright",
            )
        except Exception as e:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"LSP query check failed: {str(e)}",
                details=str(e),
            )

    def _run_ast_check(self, check: Dict, settings: Dict) -> CheckResult:
        """
        Run AST-based code quality checks using Python's ast module.

        Supported metrics:
            - cyclomatic_complexity: Check function complexity
            - function_length: Check function line count
            - nesting_depth: Check nesting depth
            - parameter_count: Check function parameter count
            - class_size: Check class method count
            - import_count: Check module import count

        Config options:
            - metric: Which metric to check
            - max_value: Maximum allowed value
            - file_patterns: Glob patterns for files to check
        """
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        try:
            config = check.get("config", {})
            metric = config.get("metric", "")
            max_value = config.get("max_value", 10)

            # Get file patterns
            file_patterns = check.get(
                "file_patterns",
                settings.get("include_patterns", ["**/*.py"])
            )
            exclude_patterns = check.get(
                "exclude_patterns",
                settings.get("exclude_patterns", [])
            )

            # Find matching files
            all_files = []
            for pattern in file_patterns:
                pattern = self._substitute_variables(pattern)
                matches = glob.glob(str(self.project_root / pattern), recursive=True)
                all_files.extend(matches)

            # Filter exclusions
            files = []
            for f in all_files:
                rel_path = os.path.relpath(f, self.project_root)
                excluded = any(
                    fnmatch.fnmatch(rel_path, self._substitute_variables(exc))
                    for exc in exclude_patterns
                )
                if not excluded:
                    files.append(Path(f))

            # Run the appropriate metric check
            violations = []

            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        source = f.read()
                    tree = ast.parse(source)

                    file_violations = self._check_ast_metric(
                        tree, source, metric, max_value, file_path
                    )
                    violations.extend(file_violations)
                except SyntaxError:
                    continue  # Skip files with syntax errors

            # Build result
            errors = [
                {
                    "file": os.path.relpath(v["file"], self.project_root),
                    "line": v.get("line"),
                    "function": v.get("function"),
                    "value": v.get("value"),
                    "max": max_value,
                    "message": v.get("message"),
                }
                for v in violations[:50]
            ]

            passed = len(violations) == 0
            message = (
                f"Found {len(violations)} {metric} violations (max: {max_value})"
                if not passed
                else f"All {len(files)} files pass {metric} check (max: {max_value})"
            )

            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity,
                message=message,
                errors=errors,
                details=f"Checked {len(files)} files for {metric}",
            )

        except Exception as e:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.ERROR,
                severity=severity,
                message=f"AST check failed: {str(e)}",
                details=str(e),
            )

    def _check_ast_metric(
        self,
        tree: ast.AST,
        source: str,
        metric: str,
        max_value: int,
        file_path: Path
    ) -> List[Dict]:
        """Check a specific AST metric and return violations."""
        violations = []

        if metric == "function_length":
            violations = self._check_function_length(tree, max_value, file_path)
        elif metric == "nesting_depth":
            violations = self._check_nesting_depth(tree, max_value, file_path)
        elif metric == "parameter_count":
            violations = self._check_parameter_count(tree, max_value, file_path)
        elif metric == "class_size":
            violations = self._check_class_size(tree, max_value, file_path)
        elif metric == "import_count":
            violations = self._check_import_count(tree, max_value, file_path)
        elif metric == "cyclomatic_complexity":
            # Use radon for complexity (more accurate than manual counting)
            violations = self._check_complexity_with_radon(file_path, max_value)

        return violations

    def _check_function_length(
        self, tree: ast.AST, max_lines: int, file_path: Path
    ) -> List[Dict]:
        """Check function lengths."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno + 1
                    if length > max_lines:
                        violations.append({
                            "file": str(file_path),
                            "function": node.name,
                            "line": node.lineno,
                            "value": length,
                            "message": f"Function '{node.name}' is {length} lines (max: {max_lines})",
                        })

        return violations

    def _check_nesting_depth(
        self, tree: ast.AST, max_depth: int, file_path: Path
    ) -> List[Dict]:
        """Check nesting depth."""
        violations = []

        nesting_nodes = (
            ast.If, ast.For, ast.While, ast.With,
            ast.Try, ast.ExceptHandler
        )

        def check_depth(node: ast.AST, current_depth: int, parent_func: str):
            new_depth = current_depth
            if isinstance(node, nesting_nodes):
                new_depth = current_depth + 1
                if new_depth > max_depth:
                    violations.append({
                        "file": str(file_path),
                        "function": parent_func,
                        "line": node.lineno,
                        "value": new_depth,
                        "message": f"Nesting depth {new_depth} in '{parent_func}' (max: {max_depth})",
                    })

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    check_depth(child, 0, child.name)
                else:
                    check_depth(child, new_depth, parent_func)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                check_depth(node, 0, node.name)

        return violations

    def _check_parameter_count(
        self, tree: ast.AST, max_params: int, file_path: Path
    ) -> List[Dict]:
        """Check function parameter count."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count parameters (excluding self/cls for methods)
                args = node.args
                param_count = (
                    len(args.args) +
                    len(args.posonlyargs) +
                    len(args.kwonlyargs) +
                    (1 if args.vararg else 0) +
                    (1 if args.kwarg else 0)
                )

                # Subtract 1 for self/cls in methods
                if args.args and args.args[0].arg in ('self', 'cls'):
                    param_count -= 1

                if param_count > max_params:
                    violations.append({
                        "file": str(file_path),
                        "function": node.name,
                        "line": node.lineno,
                        "value": param_count,
                        "message": f"Function '{node.name}' has {param_count} parameters (max: {max_params})",
                    })

        return violations

    def _check_class_size(
        self, tree: ast.AST, max_methods: int, file_path: Path
    ) -> List[Dict]:
        """Check class method count."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(
                    1 for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )

                if method_count > max_methods:
                    violations.append({
                        "file": str(file_path),
                        "function": node.name,
                        "line": node.lineno,
                        "value": method_count,
                        "message": f"Class '{node.name}' has {method_count} methods (max: {max_methods})",
                    })

        return violations

    def _check_import_count(
        self, tree: ast.AST, max_imports: int, file_path: Path
    ) -> List[Dict]:
        """Check module import count."""
        import_count = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        )

        if import_count > max_imports:
            return [{
                "file": str(file_path),
                "function": "<module>",
                "line": 1,
                "value": import_count,
                "message": f"Module has {import_count} imports (max: {max_imports})",
            }]

        return []

    def _check_complexity_with_radon(
        self, file_path: Path, max_complexity: int
    ) -> List[Dict]:
        """Check cyclomatic complexity using radon."""
        violations = []

        result = self.command_runner.run_radon_cc(file_path)

        if not result.parsed_output:
            return violations

        # radon output is dict of file_path -> list of functions
        for funcs in result.parsed_output.values():
            for func in funcs:
                complexity = func.get("complexity", 0)
                if complexity > max_complexity:
                    violations.append({
                        "file": str(file_path),
                        "function": func.get("name"),
                        "line": func.get("lineno"),
                        "value": complexity,
                        "message": f"Function '{func.get('name')}' has complexity {complexity} (max: {max_complexity})",
                    })

        return violations

    def generate_report(self, report: VerificationReport, format: str = "text") -> str:
        """Generate formatted report."""
        if format == "yaml":
            return self._generate_yaml_report(report)
        elif format == "json":
            return self._generate_json_report(report)
        else:
            return self._generate_text_report(report)

    def _generate_text_report(self, report: VerificationReport) -> str:
        """Generate human-readable text report."""
        lines = [
            "",
            "=" * 70,
            "VERIFICATION REPORT",
            "=" * 70,
            f"  Timestamp: {report.timestamp}",
            f"  Profile: {report.profile or 'custom'}",
            f"  Project: {report.project_path or 'N/A'}",
            f"  Duration: {report.duration_ms}ms",
            "",
            "-" * 70,
            "SUMMARY",
            "-" * 70,
            f"  Total Checks:      {report.total_checks}",
            f"  Passed:            {report.passed}",
            f"  Failed:            {report.failed}",
            f"  Skipped:           {report.skipped}",
            f"  Errors:            {report.errors}",
            "",
            f"  Blocking Failures: {report.blocking_failures}",
            f"  Required Failures: {report.required_failures}",
            f"  Advisory Warnings: {report.advisory_warnings}",
            "",
            f"  VERDICT: {'PASS' if report.is_valid else 'FAIL'}",
            "",
        ]

        # Detailed results
        lines.extend([
            "-" * 70,
            "DETAILED RESULTS",
            "-" * 70,
        ])

        for result in report.results:
            status_icon = {
                CheckStatus.PASSED: "✓",
                CheckStatus.FAILED: "✗",
                CheckStatus.SKIPPED: "○",
                CheckStatus.ERROR: "!",
            }.get(result.status, "?")

            severity_badge = f"[{result.severity.value.upper()}]"

            lines.append(f"\n{status_icon} {result.check_id}: {result.check_name} {severity_badge}")
            lines.append(f"  {result.message}")

            if result.details:
                lines.append(f"  Details: {result.details}")

            if result.errors:
                lines.append(f"  Errors ({len(result.errors)}):")
                for err in result.errors[:5]:
                    if isinstance(err, dict):
                        err_str = ", ".join(f"{k}: {v}" for k, v in err.items())
                        lines.append(f"    - {err_str}")
                    else:
                        lines.append(f"    - {err}")
                if len(result.errors) > 5:
                    lines.append(f"    ... and {len(result.errors) - 5} more")

            if result.fix_suggestion and not result.passed:
                lines.append(f"  Fix: {result.fix_suggestion}")

            if result.duration_ms > 0:
                lines.append(f"  Duration: {result.duration_ms}ms")

        lines.extend([
            "",
            "=" * 70,
        ])

        return "\n".join(lines)

    def _generate_yaml_report(self, report: VerificationReport) -> str:
        """Generate YAML report."""
        data = {
            "verification_report": {
                "timestamp": report.timestamp,
                "profile": report.profile,
                "project_path": report.project_path,
                "working_dir": report.working_dir,
                "duration_ms": report.duration_ms,
                "summary": {
                    "total_checks": report.total_checks,
                    "passed": report.passed,
                    "failed": report.failed,
                    "skipped": report.skipped,
                    "errors": report.errors,
                    "blocking_failures": report.blocking_failures,
                    "required_failures": report.required_failures,
                    "advisory_warnings": report.advisory_warnings,
                    "is_valid": report.is_valid,
                },
                "results": [
                    {
                        "check_id": r.check_id,
                        "check_name": r.check_name,
                        "status": r.status.value,
                        "severity": r.severity.value,
                        "message": r.message,
                        "duration_ms": r.duration_ms,
                        "details": r.details,
                        "errors": r.errors if r.errors else None,
                        "fix_suggestion": r.fix_suggestion,
                    }
                    for r in report.results
                ],
            }
        }

        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def _generate_json_report(self, report: VerificationReport) -> str:
        """Generate JSON report."""
        data = {
            "verification_report": {
                "timestamp": report.timestamp,
                "profile": report.profile,
                "project_path": report.project_path,
                "working_dir": report.working_dir,
                "duration_ms": report.duration_ms,
                "summary": {
                    "total_checks": report.total_checks,
                    "passed": report.passed,
                    "failed": report.failed,
                    "skipped": report.skipped,
                    "errors": report.errors,
                    "blocking_failures": report.blocking_failures,
                    "required_failures": report.required_failures,
                    "advisory_warnings": report.advisory_warnings,
                    "is_valid": report.is_valid,
                },
                "results": [
                    {
                        "check_id": r.check_id,
                        "check_name": r.check_name,
                        "status": r.status.value,
                        "severity": r.severity.value,
                        "message": r.message,
                        "duration_ms": r.duration_ms,
                        "details": r.details,
                        "errors": r.errors if r.errors else None,
                        "fix_suggestion": r.fix_suggestion,
                    }
                    for r in report.results
                ],
            }
        }

        return json.dumps(data, indent=2)


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="AgentForge Verification Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all checks
  python verification_runner.py

  # Run CI profile
  python verification_runner.py --profile ci

  # Run specific checks
  python verification_runner.py --checks compile_check,test_check

  # Run with project path
  python verification_runner.py --profile ci --project MyApp/MyApp.csproj

  # Output as YAML
  python verification_runner.py --profile ci --format yaml
"""
    )

    parser.add_argument(
        "--profile", "-p",
        help="Check profile to run (quick, ci, full, architecture, precommit)"
    )
    parser.add_argument(
        "--checks", "-c",
        help="Comma-separated list of check IDs to run"
    )
    parser.add_argument(
        "--project",
        help="Path to project file (e.g., MyApp.csproj)"
    )
    parser.add_argument(
        "--project-root",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--config",
        help="Path to correctness.yaml config file"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "yaml", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--fail-on-advisory",
        action="store_true",
        help="Exit with failure on advisory warnings too"
    )

    args = parser.parse_args()

    # Set up runner
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    config_path = Path(args.config) if args.config else None

    runner = VerificationRunner(
        config_path=config_path,
        project_root=project_root
    )

    # Set context
    if args.project:
        runner.set_context(
            project_path=args.project,
            project_root=str(project_root),
        )
    else:
        runner.set_context(project_root=str(project_root))

    # Run checks
    if args.profile:
        report = runner.run_profile(args.profile)
    elif args.checks:
        check_ids = [c.strip() for c in args.checks.split(",")]
        report = runner.run_checks(check_ids=check_ids)
    else:
        report = runner.run_checks(all_checks=True)

    # Generate output
    output = runner.generate_report(report, format=args.format)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report saved to: {args.output}")
    else:
        print(output)

    # Exit code
    if not report.is_valid:
        sys.exit(1)
    elif args.fail_on_advisory and report.advisory_warnings > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
