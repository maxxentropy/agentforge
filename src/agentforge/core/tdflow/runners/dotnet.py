# @spec_file: .agentforge/specs/core-tdflow-runners-v1.yaml
# @spec_id: core-tdflow-runners-v1
# @component_id: tdflow-runners-dotnet
# @test_path: tests/unit/tools/tdflow/runners/test_dotnet.py

"""
DotNet Test Runner
==================

Runs tests via 'dotnet test'.
"""

import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from agentforge.core.tdflow.domain import TestResult
from agentforge.core.tdflow.runners.base import TestRunner


class DotNetTestRunner(TestRunner):
    """
    Test runner for .NET projects using dotnet test.

    Supports xUnit, NUnit, and MSTest frameworks.
    """

    def run_tests(self, filter_pattern: str | None = None) -> TestResult:
        """
        Run dotnet test and parse results.

        Args:
            filter_pattern: Optional test filter (e.g., "ClassName", "MethodName")

        Returns:
            TestResult with parsed test counts
        """
        cmd = ["dotnet", "test", str(self.project_path), "--no-restore"]

        if filter_pattern:
            cmd.extend(["--filter", filter_pattern])

        # Add TRX output for better parsing
        trx_path = self.project_path / ".agentforge" / "test_results.trx"
        trx_path.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--logger", f"trx;LogFileName={trx_path}"])

        # Add coverage collection
        cmd.extend(["--collect:XPlat Code Coverage"])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )

        # Try to parse TRX file first, fall back to output parsing
        if trx_path.exists():
            try:
                return self._parse_trx(trx_path, result.stdout + result.stderr)
            except Exception:
                pass

        return self._parse_output(result.stdout + result.stderr, result.returncode)

    def _parse_trx(self, trx_path: Path, output: str) -> TestResult:
        """
        Parse TRX (Visual Studio Test Results) file.

        Args:
            trx_path: Path to TRX file
            output: Raw console output for fallback

        Returns:
            TestResult with parsed data
        """
        tree = ET.parse(trx_path)
        root = tree.getroot()

        # Handle XML namespace
        ns = {"vs": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}

        counters = root.find(".//vs:ResultSummary/vs:Counters", ns)
        if counters is not None:
            total = int(counters.get("total", 0))
            passed = int(counters.get("passed", 0))
            failed = int(counters.get("failed", 0))
            errors = int(counters.get("error", 0))

            # Get duration from Times element
            times = root.find(".//vs:Times", ns)
            duration = 0.0
            if times is not None:
                start = times.get("start")
                finish = times.get("finish")
                if start and finish:
                    from datetime import datetime

                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    finish_dt = datetime.fromisoformat(finish.replace("Z", "+00:00"))
                    duration = (finish_dt - start_dt).total_seconds()

            return TestResult(
                total=total,
                passed=passed,
                failed=failed,
                errors=errors,
                duration_seconds=duration,
                output=output,
            )

        # Fallback to output parsing
        return self._parse_output(output, 0 if passed == total else 1)

    def _parse_output(self, output: str, returncode: int) -> TestResult:
        """
        Parse dotnet test output.

        Args:
            output: Combined stdout/stderr from dotnet test
            returncode: Process return code

        Returns:
            TestResult with parsed data
        """
        total = passed = failed = 0

        # Parse: "Passed: X, Failed: Y, Skipped: Z, Total: N"
        # Or: "Passed!  - Failed:     0, Passed:     3, Skipped:     0, Total:     3"
        match = re.search(r"Passed:\s*(\d+)", output)
        if match:
            passed = int(match.group(1))

        match = re.search(r"Failed:\s*(\d+)", output)
        if match:
            failed = int(match.group(1))

        match = re.search(r"Total:\s*(\d+)", output)
        if match:
            total = int(match.group(1))

        # Parse duration if available: "Duration: 1.234 s"
        duration = 0.0
        match = re.search(r"Duration:\s*([\d.]+)\s*s", output)
        if match:
            duration = float(match.group(1))

        # If we got no total but have passed/failed, calculate it
        if total == 0 and (passed > 0 or failed > 0):
            total = passed + failed

        return TestResult(
            total=total,
            passed=passed,
            failed=failed,
            errors=0 if returncode == 0 or failed > 0 else 1,
            duration_seconds=duration,
            output=output,
        )

    def get_coverage(self) -> float:
        """
        Get coverage from last test run.

        Parses coverage.cobertura.xml if available.

        Returns:
            Coverage percentage (0-100)
        """
        # Find coverage file
        coverage_files = list(self.project_path.glob("**/coverage.cobertura.xml"))
        if not coverage_files:
            return 0.0

        # Use most recent
        coverage_file = max(coverage_files, key=lambda p: p.stat().st_mtime)

        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            # Get line-rate attribute from coverage element
            line_rate = root.get("line-rate")
            if line_rate:
                return float(line_rate) * 100

            return 0.0
        except Exception:
            return 0.0

    def discover_tests(self) -> list[str]:
        """
        Discover tests via dotnet test --list-tests.

        Returns:
            List of test names
        """
        cmd = ["dotnet", "test", str(self.project_path), "--list-tests", "--no-build"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_path)

        tests = []
        in_test_list = False

        for line in result.stdout.split("\n"):
            line = line.strip()

            # Start collecting after "The following Tests are available:"
            if "following" in line.lower() and "test" in line.lower():
                in_test_list = True
                continue

            if in_test_list and line and not line.startswith("-"):
                tests.append(line)

        return tests

    def build(self) -> bool:
        """
        Build the project.

        Returns:
            True if build succeeded
        """
        result = subprocess.run(
            ["dotnet", "build", str(self.project_path), "--no-restore"],
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )
        return result.returncode == 0
