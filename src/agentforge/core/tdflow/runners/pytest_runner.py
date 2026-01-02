"""
Pytest Runner
=============

Runs tests via pytest.
"""

import json
import re
import subprocess
from pathlib import Path

from agentforge.core.tdflow.domain import RunResult
from agentforge.core.tdflow.runners.base import TestRunner


class PytestRunner(TestRunner):
    """
    Test runner for Python projects using pytest.
    """

    def run_tests(self, filter_pattern: str | None = None) -> RunResult:
        """
        Run pytest and parse results.

        Args:
            filter_pattern: Optional filter (-k pattern)

        Returns:
            RunResult with parsed data
        """
        cmd = ["python", "-m", "pytest", "-v", "--tb=short"]

        if filter_pattern:
            cmd.extend(["-k", filter_pattern])

        # JSON output for better parsing (requires pytest-json-report)
        report_path = self.project_path / ".agentforge" / "pytest_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Try with json-report first
        cmd_with_json = cmd + [
            "--json-report",
            f"--json-report-file={report_path}",
        ]

        result = subprocess.run(
            cmd_with_json,
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )

        # If json-report failed (not installed), run without it
        if "unrecognized arguments" in result.stderr:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_path,
            )
            return self._parse_output(result.stdout + result.stderr, result.returncode)

        # Try JSON report first
        if report_path.exists():
            try:
                return self._parse_json_report(report_path, result.stdout)
            except Exception:
                pass

        return self._parse_output(result.stdout + result.stderr, result.returncode)

    def _parse_json_report(self, report_path: Path, output: str) -> RunResult:
        """
        Parse pytest JSON report.

        Args:
            report_path: Path to JSON report file
            output: Raw console output

        Returns:
            RunResult with parsed data
        """
        with open(report_path) as f:
            report = json.load(f)

        summary = report.get("summary", {})
        return RunResult(
            total=summary.get("total", 0),
            passed=summary.get("passed", 0),
            failed=summary.get("failed", 0),
            errors=summary.get("error", 0),
            duration_seconds=report.get("duration", 0.0),
            output=output,
        )

    def _parse_output(self, output: str, returncode: int) -> RunResult:
        """
        Parse pytest output.

        Args:
            output: Combined stdout/stderr
            returncode: Process return code

        Returns:
            RunResult with parsed data
        """
        total = passed = failed = errors = 0
        duration = 0.0

        # Parse summary line: "== 3 passed, 1 failed in 0.12s =="
        # Or: "== 5 passed in 1.23s =="
        summary_match = re.search(
            r"=+\s*([\d\w\s,]+)\s+in\s+([\d.]+)s?\s*=+",
            output,
            re.IGNORECASE,
        )

        if summary_match:
            summary_text = summary_match.group(1)
            duration = float(summary_match.group(2))

            # Parse individual counts
            passed_match = re.search(r"(\d+)\s+passed", summary_text)
            if passed_match:
                passed = int(passed_match.group(1))

            failed_match = re.search(r"(\d+)\s+failed", summary_text)
            if failed_match:
                failed = int(failed_match.group(1))

            error_match = re.search(r"(\d+)\s+error", summary_text)
            if error_match:
                errors = int(error_match.group(1))

            skipped_match = re.search(r"(\d+)\s+skipped", summary_text)
            skipped = int(skipped_match.group(1)) if skipped_match else 0

            total = passed + failed + errors + skipped

        # Fallback: count test results from verbose output
        if total == 0:
            passed = len(re.findall(r"PASSED", output))
            failed = len(re.findall(r"FAILED", output))
            errors = len(re.findall(r"ERROR", output))
            total = passed + failed + errors

        return RunResult(
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            duration_seconds=duration,
            output=output,
        )

    def get_coverage(self) -> float:
        """
        Run with coverage and return percentage.

        Returns:
            Coverage percentage (0-100)
        """
        # Run pytest with coverage
        cov_json = self.project_path / ".agentforge" / "coverage.json"
        cov_json.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov",
            f"--cov-report=json:{cov_json}",
            "--cov-report=term",
        ]

        subprocess.run(cmd, cwd=self.project_path, capture_output=True)

        if cov_json.exists():
            with open(cov_json) as f:
                data = json.load(f)
            return data.get("totals", {}).get("percent_covered", 0.0)

        return 0.0

    def discover_tests(self) -> list[str]:
        """
        Discover tests via pytest --collect-only.

        Returns:
            List of test names
        """
        cmd = ["python", "-m", "pytest", "--collect-only", "-q"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )

        tests = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            # Test lines look like: "test_foo.py::test_bar"
            if "::" in line and not line.startswith("="):
                tests.append(line)

        return tests

    def build(self) -> bool:
        """
        Build/install the project.

        For Python, this typically means installing in development mode.

        Returns:
            True if successful
        """
        # Check if pyproject.toml exists
        if (self.project_path / "pyproject.toml").exists():
            result = subprocess.run(
                ["pip", "install", "-e", ".", "--quiet"],
                cwd=self.project_path,
                capture_output=True,
            )
            return result.returncode == 0

        # No explicit build needed for Python
        return True
