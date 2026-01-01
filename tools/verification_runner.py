#!/usr/bin/env python3

# @spec_file: .agentforge/specs/tools-v1.yaml
# @spec_id: tools-v1
# @component_id: tools-verification_runner
# @test_path: tests/test_python_checks.py

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

import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

# Import types
try:
    from .verification_types import Severity, CheckStatus, CheckResult, VerificationReport
    from .verification_checks import CheckRunner
    from .verification_reports import ReportGenerator
except ImportError:
    from verification_types import Severity, CheckStatus, CheckResult, VerificationReport
    from verification_checks import CheckRunner
    from verification_reports import ReportGenerator

# Import runners
try:
    from .pyright_runner import PyrightRunner
    from .command_runner import CommandRunner
    from .verification_ast import ASTChecker
except ImportError:
    # Allow running as standalone script
    from pyright_runner import PyrightRunner
    from command_runner import CommandRunner
    from verification_ast import ASTChecker


class VerificationRunner(CheckRunner, ReportGenerator):
    """
    Runs verification checks defined in correctness.yaml.

    Replaces LLM-based validation with deterministic verification.
    """

    def __init__(self, config_path: Path = None, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.config_path = config_path or self.project_root / "config" / "correctness.yaml"
        # Load config inline
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {"checks": [], "profiles": {}, "settings": {}}
        self.context: Dict[str, Any] = {}
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

    # =========================================================================
    # Profile and Check Management
    # =========================================================================

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

    # =========================================================================
    # Check Execution
    # =========================================================================

    def _check_deps_met(self, deps: List[str], completed: set, results: list) -> bool:
        """Check if dependencies are met."""
        return all(d in completed and any(r.check_id == d and r.passed for r in results) for d in deps)

    def _create_skip_result(self, check: Dict, message: str) -> CheckResult:
        """Create a skipped check result."""
        return CheckResult(
            check_id=check["id"], check_name=check.get("name", check["id"]),
            status=CheckStatus.SKIPPED, severity=Severity(check.get("severity", "required")),
            message=message,
        )

    def _run_checks(self, checks: List[Dict], settings: Dict[str, Any],
                    profile: Optional[str]) -> VerificationReport:
        """Execute a list of checks and generate report."""
        start_time = datetime.now()
        report = VerificationReport(
            timestamp=start_time.isoformat() + "Z", profile=profile,
            project_path=self.context.get("project_path"), working_dir=str(self.project_root),
            total_checks=len(checks), passed=0, failed=0, skipped=0, errors=0,
            blocking_failures=0, required_failures=0, advisory_warnings=0, duration_ms=0,
        )

        fail_fast, completed = settings.get("fail_fast", False), set()

        for check in checks:
            deps = check.get("depends_on", [])
            if deps and not self._check_deps_met(deps, completed, report.results):
                report.add_result(self._create_skip_result(check, f"Skipped: dependencies {deps}"))
                continue

            result = self.run_check(check, settings)
            report.add_result(result)
            completed.add(check["id"])

            if fail_fast and result.is_blocking_failure:
                for c in checks:
                    if c["id"] not in completed:
                        report.add_result(self._create_skip_result(c, "Skipped: fail_fast"))
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
