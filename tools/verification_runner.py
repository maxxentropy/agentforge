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
    from .verification_ast import ASTChecker
except ImportError:
    # Allow running as standalone script
    from pyright_runner import PyrightRunner
    from command_runner import CommandRunner
    from verification_ast import ASTChecker


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
        self._ast_checker = None

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

    @property
    def ast_checker(self) -> ASTChecker:
        """Lazy-load AST checker."""
        if self._ast_checker is None:
            self._ast_checker = ASTChecker(self.command_runner)
        return self._ast_checker

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

    def _check_dependencies_met(self, deps: List[str], completed: set, results: list) -> bool:
        """Check if all dependencies are met."""
        return all(
            d in completed and any(r.check_id == d and r.passed for r in results)
            for d in deps
        )

    def _create_skip_result(self, check: Dict, message: str) -> CheckResult:
        """Create a skipped check result."""
        return CheckResult(
            check_id=check["id"],
            check_name=check.get("name", check["id"]),
            status=CheckStatus.SKIPPED,
            severity=Severity(check.get("severity", "required")),
            message=message,
        )

    def _skip_remaining_checks(self, checks: List[Dict], completed: set, report: "VerificationReport"):
        """Skip remaining checks due to fail_fast."""
        for check in checks:
            if check["id"] not in completed:
                report.add_result(self._create_skip_result(
                    check, "Skipped due to fail_fast on previous blocking failure"))

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
            passed=0, failed=0, skipped=0, errors=0,
            blocking_failures=0, required_failures=0, advisory_warnings=0, duration_ms=0,
        )

        fail_fast = settings.get("fail_fast", False)
        completed_checks = set()

        for check in checks:
            deps = check.get("depends_on", [])
            if deps and not self._check_dependencies_met(deps, completed_checks, report.results):
                report.add_result(self._create_skip_result(check, f"Skipped due to failed dependencies: {deps}"))
                continue

            result = self.run_check(check, settings)
            report.add_result(result)
            completed_checks.add(check["id"])

            if fail_fast and result.is_blocking_failure:
                self._skip_remaining_checks(checks, completed_checks, report)
                break

        report.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return report

    def _get_check_handlers(self) -> Dict[str, Callable]:
        """Return dispatch table for check types."""
        return {
            "command": self._run_command_check,
            "regex": self._run_regex_check,
            "file_exists": self._run_file_exists_check,
            "import_check": self._run_import_check,
            "custom": self._run_custom_check,
            "contracts": self._run_contracts_check,
            "lsp_query": self._run_lsp_query_check,
            "ast_check": self._run_ast_check,
        }

    def run_check(self, check: Dict, settings: Dict[str, Any] = None) -> CheckResult:
        """Run a single verification check."""
        settings = settings or {}
        check_id = check["id"]
        check_name = check.get("name", check_id)
        check_type = check.get("type", "command")
        severity = Severity(check.get("severity", "required"))

        start_time = datetime.now()

        try:
            handler = self._get_check_handlers().get(check_type)
            if handler:
                result = handler(check, settings)
            else:
                result = CheckResult(
                    check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                    severity=severity, message=f"Unknown check type: {check_type}",
                )
        except Exception as e:
            result = CheckResult(
                check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                severity=severity, message=f"Check raised exception: {str(e)}", details=str(e),
            )

        result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        result.fix_suggestion = check.get("fix_suggestion")
        return result

    def _check_output_indicators(self, output: str, passed: bool,
                                  success_indicators: list, failure_indicators: list) -> bool:
        """Check output for success/failure indicators and adjust passed status."""
        if passed and failure_indicators:
            for indicator in failure_indicators:
                if indicator in output:
                    return False
        if not passed and success_indicators:
            for indicator in success_indicators:
                if indicator in output:
                    return True
        return passed

    def _parse_error_output(self, output: str, error_parser: Dict | None) -> list:
        """Parse structured errors from command output."""
        if not error_parser:
            return []
        pattern = error_parser["pattern"]
        return [match.groupdict() for match in re.finditer(pattern, output)]

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

        if not os.path.isabs(working_dir):
            working_dir = str(self.project_root / working_dir)

        try:
            command_list = shlex.split(command) if isinstance(command, str) else command
            result = subprocess.run(
                command_list, shell=False, capture_output=True, text=True,
                timeout=timeout, cwd=working_dir, env={**os.environ, "NO_COLOR": "1"},
            )

            output = result.stdout + result.stderr
            passed = self._check_output_indicators(
                output, result.returncode == 0,
                check.get("success_indicators", []), check.get("failure_indicators", [])
            )
            errors = self._parse_error_output(output, check.get("error_parser")) if not passed else []

            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity,
                message=check.get("message", f"Command {'succeeded' if passed else 'failed'}"),
                output=output[:5000] if len(output) > 5000 else output,
                errors=errors, details=f"Exit code: {result.returncode}",
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                severity=severity, message=f"Command timed out after {timeout}s",
            )

        except Exception as e:
            return CheckResult(
                check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                severity=severity, message=f"Command execution failed: {str(e)}",
            )

    def _collect_files_for_check(self, include_patterns: list, exclude_patterns: list) -> list:
        """Collect files matching include patterns, excluding those matching exclude patterns."""
        all_files = []
        for pattern in include_patterns:
            pattern = self._substitute_variables(pattern)
            matches = glob.glob(str(self.project_root / pattern), recursive=True)
            all_files.extend(matches)

        files = []
        for f in all_files:
            rel_path = os.path.relpath(f, self.project_root)
            excluded = any(
                fnmatch.fnmatch(rel_path, self._substitute_variables(exc))
                for exc in exclude_patterns
            )
            if not excluded:
                files.append(f)
        return files

    def _search_patterns_in_file(self, file_path: str, patterns: list) -> list:
        """Search for patterns in a single file, returning matches."""
        matches = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pat_def in patterns:
                pat_name = pat_def.get("name", "pattern")
                pattern = pat_def["pattern"]
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    rel_path = os.path.relpath(file_path, self.project_root)
                    matches.append({
                        "file": rel_path, "line": line_num,
                        "pattern_name": pat_name, "match": match.group()[:100],
                    })
        except Exception:
            pass
        return matches

    def _determine_regex_result(self, matches_found: list, negative_match: bool,
                                  check_message: str) -> tuple[bool, str, list]:
        """Determine regex check result. Returns (passed, message, errors)."""
        if negative_match:
            passed = len(matches_found) == 0
            message = "No forbidden patterns found" if passed else check_message or "Pattern should not match"
            errors = [{"file": m["file"], "line": m["line"], "match": m["match"]}
                      for m in matches_found[:20]] if not passed else []
        else:
            passed = len(matches_found) > 0
            message = f"Found {len(matches_found)} match(es)" if passed else check_message or "Pattern should match"
            errors = []
        return passed, message, errors

    def _run_regex_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a regex pattern check on source files."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        patterns = check.get("patterns", [])
        if not patterns and check.get("pattern"):
            patterns = [{"name": "pattern", "pattern": check["pattern"]}]

        include_patterns = check.get("file_patterns", settings.get("include_patterns", ["**/*.cs"]))
        exclude_patterns = check.get("exclude_patterns", settings.get("exclude_patterns", []))

        files = self._collect_files_for_check(include_patterns, exclude_patterns)
        matches_found = []
        for file_path in files:
            matches_found.extend(self._search_patterns_in_file(file_path, patterns))

        passed, message, errors = self._determine_regex_result(
            matches_found, check.get("negative_match", False), check.get("message"))

        return CheckResult(
            check_id=check_id, check_name=check_name,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            severity=severity, message=message, errors=errors,
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

    def _find_forbidden_import_violations(self, source_file: str, forbidden_imports: list,
                                           rule_message: str) -> list:
        """Check a single file for forbidden import violations."""
        violations = []
        try:
            with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            using_pattern = r"using\s+([a-zA-Z0-9_.]+)\s*;"
            usings = re.findall(using_pattern, content)
            rel_path = os.path.relpath(source_file, self.project_root)

            for using in usings:
                for forbidden in forbidden_imports:
                    if forbidden in using:
                        line_num = self._find_using_line(content, using)
                        violations.append({
                            "file": rel_path, "line": line_num, "import": using,
                            "forbidden": forbidden, "message": rule_message,
                        })
        except Exception:
            pass
        return violations

    def _find_using_line(self, content: str, using: str) -> int | None:
        """Find the line number of a using statement."""
        for i, line in enumerate(content.split("\n"), 1):
            if f"using {using}" in line:
                return i
        return None

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
            rule_message = rule.get("message", f"Forbidden import")

            source_files = glob.glob(str(self.project_root / source_pattern), recursive=True)
            for source_file in source_files:
                violations.extend(self._find_forbidden_import_violations(
                    source_file, forbidden_imports, rule_message))

        passed = len(violations) == 0
        return CheckResult(
            check_id=check_id, check_name=check_name,
            status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
            severity=severity,
            message=check.get("message", "Layer dependencies OK") if passed else f"Found {len(violations)} violation(s)",
            errors=violations[:20], details=f"Checked {len(rules)} rules",
        )

    def _load_custom_function(self, function_path: str) -> Callable:
        """Load a custom function from module.function path."""
        parts = function_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid function path: {function_path}")

        module_name, func_name = parts
        tools_dir = Path(__file__).parent
        module_file = tools_dir / f"{module_name}.py"

        if module_file.exists():
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            module = importlib.import_module(module_name)

        return getattr(module, func_name)

    def _convert_custom_result(self, result: Any, check_id: str, check_name: str,
                                severity: Severity, default_message: str) -> CheckResult:
        """Convert custom function result to CheckResult."""
        if isinstance(result, CheckResult):
            return result
        if isinstance(result, dict):
            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if result.get("passed", False) else CheckStatus.FAILED,
                severity=severity, message=result.get("message", default_message),
                errors=result.get("errors", []), details=result.get("details"),
            )
        if isinstance(result, bool):
            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if result else CheckStatus.FAILED,
                severity=severity, message=default_message,
            )
        return CheckResult(
            check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
            severity=severity, message=f"Custom check returned unexpected type: {type(result)}",
        )

    def _run_custom_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run a custom Python function check."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        function_path = check.get("function")
        parameters = {k: self._substitute_variables(v) if isinstance(v, str) else v
                      for k, v in check.get("parameters", {}).items()}

        try:
            func = self._load_custom_function(function_path)
            result = func(project_root=self.project_root, context=self.context, **parameters)
            return self._convert_custom_result(result, check_id, check_name, severity, check.get("message", ""))
        except Exception as e:
            return CheckResult(
                check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                severity=severity, message=f"Custom check failed: {str(e)}", details=str(e),
            )

    def _get_contract_results(self, check: Dict):
        """Get contract results based on check config. Returns (results, error_msg)."""
        from contracts import ContractRegistry, run_contract, run_all_contracts

        contract_name = check.get("contract")
        if contract_name:
            registry = ContractRegistry(self.project_root)
            contract = registry.get_contract(contract_name)
            if not contract:
                return None, f"Contract not found: {contract_name}"
            return [run_contract(contract, self.project_root, registry)], None

        return run_all_contracts(
            self.project_root, language=check.get("language"), repo_type=check.get("repo_type")
        ), None

    def _build_contract_errors(self, results: list) -> list:
        """Build error details from contract results."""
        errors = []
        for result in results:
            for check_result in result.check_results:
                if not check_result.passed and not check_result.exempted:
                    errors.append({
                        "contract": result.contract_name, "check": check_result.check_id,
                        "severity": check_result.severity, "message": check_result.message,
                        "file": check_result.file_path, "line": check_result.line_number,
                    })
        return errors

    def _aggregate_contract_stats(self, results: list) -> dict:
        """Aggregate statistics from contract results."""
        return {
            "errors": sum(len(r.errors) for r in results),
            "warnings": sum(len(r.warnings) for r in results),
            "exempted": sum(r.exempted_count for r in results),
            "all_passed": all(r.passed for r in results),
        }

    def _run_contracts_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run contract-based checks using the contracts module."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        try:
            results, error_msg = self._get_contract_results(check)
            if error_msg:
                return CheckResult(check_id=check_id, check_name=check_name,
                                   status=CheckStatus.ERROR, severity=severity, message=error_msg)

            stats = self._aggregate_contract_stats(results)
            passed = stats["all_passed"] and (stats["warnings"] == 0 if check.get("fail_on_warning") else True)

            message = f"Ran {len(results)} contracts: {stats['errors']} errors, {stats['warnings']} warnings"
            if stats["exempted"] > 0:
                message += f", {stats['exempted']} exempted"

            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity, message=message, errors=self._build_contract_errors(results)[:50],
                details=f"Contracts: {', '.join(r.contract_name for r in results)}",
            )

        except ImportError as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=f"Could not import contracts module: {e}")
        except Exception as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=f"Contracts check failed: {str(e)}", details=str(e))

    def _filter_pyright_diagnostics(self, diagnostics: list, file_set: set, severity_filter: list) -> list:
        """Filter pyright diagnostics to target files and severities."""
        filtered = []
        for diag in diagnostics:
            diag_path = str(Path(diag.file).resolve()) if diag.file else ""
            if diag_path in file_set and diag.severity in severity_filter:
                filtered.append(diag)
        return filtered

    def _run_lsp_query_check(self, check: Dict, settings: Dict) -> CheckResult:
        """Run semantic Python analysis using pyright CLI."""
        check_id = check["id"]
        check_name = check.get("name", check_id)
        severity = Severity(check.get("severity", "required"))

        try:
            include_patterns = check.get("file_patterns", settings.get("include_patterns", ["**/*.py"]))
            exclude_patterns = check.get("exclude_patterns", settings.get("exclude_patterns", []))
            files = self._collect_files_for_check(include_patterns, exclude_patterns)

            result = self.pyright_runner.check_project()
            file_set = set(str(Path(f).resolve()) for f in files)
            filtered_diags = self._filter_pyright_diagnostics(
                result.diagnostics, file_set, check.get("severity_filter", ["error"])
            )

            errors = [{
                "file": os.path.relpath(d.file, self.project_root) if d.file else "",
                "line": d.line, "column": d.column, "message": d.message,
                "rule": d.rule, "severity": d.severity,
            } for d in filtered_diags[:50]]

            passed = len(filtered_diags) == 0
            message = f"Found {len(filtered_diags)} type issues" if not passed else f"Type check passed ({result.files_analyzed} files analyzed)"

            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity, message=message, errors=errors,
                details=f"Analyzed {len(files)} files, {result.error_count} errors, {result.warning_count} warnings",
            )

        except RuntimeError as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=str(e), details="Install pyright with: pip install pyright")
        except Exception as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=f"LSP query check failed: {str(e)}", details=str(e))

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

            include_patterns = check.get("file_patterns", settings.get("include_patterns", ["**/*.py"]))
            exclude_patterns = check.get("exclude_patterns", settings.get("exclude_patterns", []))
            files = [Path(f) for f in self._collect_files_for_check(include_patterns, exclude_patterns)]

            violations = self._collect_ast_violations(files, metric, max_value)

            errors = [{
                "file": os.path.relpath(v["file"], self.project_root),
                "line": v.get("line"), "function": v.get("function"),
                "value": v.get("value"), "max": max_value, "message": v.get("message"),
            } for v in violations[:50]]

            passed = len(violations) == 0
            message = (f"Found {len(violations)} {metric} violations (max: {max_value})"
                       if not passed else f"All {len(files)} files pass {metric} check (max: {max_value})")

            return CheckResult(
                check_id=check_id, check_name=check_name,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=severity, message=message, errors=errors,
                details=f"Checked {len(files)} files for {metric}",
            )

        except Exception as e:
            return CheckResult(check_id=check_id, check_name=check_name, status=CheckStatus.ERROR,
                               severity=severity, message=f"AST check failed: {str(e)}", details=str(e))

    def _collect_ast_violations(self, files: List[Path], metric: str, max_value: int) -> list:
        """Collect AST violations across files."""
        violations = []
        for file_path in files:
            try:
                source = file_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source)
                violations.extend(self.ast_checker.check_metric(tree, source, metric, max_value, file_path))
            except SyntaxError:
                continue
        return violations

    def generate_report(self, report: VerificationReport, format: str = "text") -> str:
        """Generate formatted report."""
        if format == "yaml":
            return self._generate_yaml_report(report)
        elif format == "json":
            return self._generate_json_report(report)
        else:
            return self._generate_text_report(report)

    def _format_check_result(self, result: CheckResult) -> list:
        """Format a single check result for text report."""
        status_icons = {CheckStatus.PASSED: "✓", CheckStatus.FAILED: "✗", CheckStatus.SKIPPED: "○", CheckStatus.ERROR: "!"}
        lines = [
            f"\n{status_icons.get(result.status, '?')} {result.check_id}: {result.check_name} [{result.severity.value.upper()}]",
            f"  {result.message}"
        ]
        if result.details:
            lines.append(f"  Details: {result.details}")
        if result.errors:
            lines.append(f"  Errors ({len(result.errors)}):")
            for err in result.errors[:5]:
                err_str = ", ".join(f"{k}: {v}" for k, v in err.items()) if isinstance(err, dict) else str(err)
                lines.append(f"    - {err_str}")
            if len(result.errors) > 5:
                lines.append(f"    ... and {len(result.errors) - 5} more")
        if result.fix_suggestion and not result.passed:
            lines.append(f"  Fix: {result.fix_suggestion}")
        if result.duration_ms > 0:
            lines.append(f"  Duration: {result.duration_ms}ms")
        return lines

    def _generate_text_report(self, report: VerificationReport) -> str:
        """Generate human-readable text report."""
        lines = [
            "", "=" * 70, "VERIFICATION REPORT", "=" * 70,
            f"  Timestamp: {report.timestamp}", f"  Profile: {report.profile or 'custom'}",
            f"  Project: {report.project_path or 'N/A'}", f"  Duration: {report.duration_ms}ms",
            "", "-" * 70, "SUMMARY", "-" * 70,
            f"  Total Checks:      {report.total_checks}", f"  Passed:            {report.passed}",
            f"  Failed:            {report.failed}", f"  Skipped:           {report.skipped}",
            f"  Errors:            {report.errors}", "",
            f"  Blocking Failures: {report.blocking_failures}", f"  Required Failures: {report.required_failures}",
            f"  Advisory Warnings: {report.advisory_warnings}", "",
            f"  VERDICT: {'PASS' if report.is_valid else 'FAIL'}", "",
            "-" * 70, "DETAILED RESULTS", "-" * 70,
        ]

        for result in report.results:
            lines.extend(self._format_check_result(result))

        lines.extend(["", "=" * 70])
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

def _build_verification_parser():
    """Build argument parser for verification CLI."""
    import argparse
    parser = argparse.ArgumentParser(
        description="AgentForge Verification Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python verification_runner.py --profile ci\n"
               "  python verification_runner.py --checks compile_check,test_check"
    )
    parser.add_argument("--profile", "-p", help="Check profile to run")
    parser.add_argument("--checks", "-c", help="Comma-separated list of check IDs")
    parser.add_argument("--project", help="Path to project file")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--config", help="Path to correctness.yaml")
    parser.add_argument("--format", "-f", choices=["text", "yaml", "json"], default="text")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--fail-on-advisory", action="store_true")
    return parser


def _run_verification(runner, args):
    """Run verification checks based on args."""
    if args.profile:
        return runner.run_profile(args.profile)
    if args.checks:
        return runner.run_checks(check_ids=[c.strip() for c in args.checks.split(",")])
    return runner.run_checks(all_checks=True)


def main():
    parser = _build_verification_parser()
    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    config_path = Path(args.config) if args.config else None

    runner = VerificationRunner(config_path=config_path, project_root=project_root)
    runner.set_context(project_path=args.project, project_root=str(project_root))

    report = _run_verification(runner, args)
    output = runner.generate_report(report, format=args.format)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Report saved to: {args.output}")
    else:
        print(output)

    if not report.is_valid or (args.fail_on_advisory and report.advisory_warnings > 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
