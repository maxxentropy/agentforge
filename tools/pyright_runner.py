# @spec_file: .agentforge/specs/tools-v1.yaml
# @spec_id: tools-v1
# @component_id: tools-pyright_runner
# @test_path: tests/test_python_checks.py

"""
Pyright runner for AgentForge contract checks.

This module provides semantic Python analysis using pyright's CLI.
It does NOT use LSP protocol - it executes pyright as a subprocess
and parses the JSON output.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PyrightDiagnostic:
    """A single diagnostic from pyright."""
    file: str
    severity: str  # "error", "warning", "information"
    message: str
    line: int
    column: int
    rule: str | None = None


@dataclass
class PyrightResult:
    """Result of running pyright."""
    success: bool
    diagnostics: list[PyrightDiagnostic]
    files_analyzed: int
    error_count: int
    warning_count: int
    raw_output: dict[str, Any]


class PyrightRunner:
    """
    Runs pyright CLI and parses results.

    This is NOT an LSP client. It simply executes pyright as a subprocess
    and parses the JSON output.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize the runner.

        Args:
            project_root: Root directory of the project. If None, uses cwd.
        """
        self.project_root = project_root or Path.cwd()
        self._verify_pyright_installed()

    def _verify_pyright_installed(self) -> None:
        """Verify pyright is installed and accessible."""
        try:
            result = subprocess.run(
                ["pyright", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("pyright --version failed")
        except FileNotFoundError:
            raise RuntimeError(
                "pyright is not installed. Install with: pip install pyright"
            )

    def check_file(self, file_path: Path) -> PyrightResult:
        """
        Run pyright on a single file.

        Args:
            file_path: Path to the Python file to check.

        Returns:
            PyrightResult with diagnostics.
        """
        return self._run_pyright([str(file_path)])

    def check_directory(self, dir_path: Path | None = None) -> PyrightResult:
        """
        Run pyright on a directory.

        Args:
            dir_path: Directory to check. Defaults to project root.

        Returns:
            PyrightResult with diagnostics.
        """
        target = str(dir_path) if dir_path else "."
        return self._run_pyright([target])

    def check_project(self) -> PyrightResult:
        """
        Run pyright on the entire project (uses pyrightconfig.json if present).

        Returns:
            PyrightResult with diagnostics.
        """
        return self._run_pyright([])

    def _run_pyright(self, args: list[str]) -> PyrightResult:
        """
        Execute pyright with given arguments.

        Args:
            args: Additional arguments to pass to pyright.

        Returns:
            Parsed PyrightResult.
        """
        cmd = ["pyright", "--outputjson"] + args

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_root,
            timeout=300  # 5 minute timeout for large projects
        )

        # pyright outputs JSON to stdout even on errors
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            # If JSON parsing fails, create error result
            return PyrightResult(
                success=False,
                diagnostics=[
                    PyrightDiagnostic(
                        file="",
                        severity="error",
                        message=f"Failed to parse pyright output: {result.stderr}",
                        line=0,
                        column=0
                    )
                ],
                files_analyzed=0,
                error_count=1,
                warning_count=0,
                raw_output={}
            )

        return self._parse_output(output)

    def _parse_output(self, output: dict[str, Any]) -> PyrightResult:
        """
        Parse pyright JSON output into structured result.

        Args:
            output: Raw JSON output from pyright.

        Returns:
            Structured PyrightResult.
        """
        diagnostics: list[PyrightDiagnostic] = []

        for diag in output.get("generalDiagnostics", []):
            range_info = diag.get("range", {})
            start = range_info.get("start", {})

            diagnostics.append(PyrightDiagnostic(
                file=diag.get("file", ""),
                severity=diag.get("severity", "error"),
                message=diag.get("message", ""),
                line=start.get("line", 0),
                column=start.get("character", 0),
                rule=diag.get("rule")
            ))

        summary = output.get("summary", {})

        return PyrightResult(
            success=summary.get("errorCount", 0) == 0,
            diagnostics=diagnostics,
            files_analyzed=summary.get("filesAnalyzed", 0),
            error_count=summary.get("errorCount", 0),
            warning_count=summary.get("warningCount", 0),
            raw_output=output
        )


# Convenience function for simple usage
def check_python_types(path: Path | str) -> PyrightResult:
    """
    Check Python types in a file or directory.

    Args:
        path: File or directory to check.

    Returns:
        PyrightResult with diagnostics.

    Example:
        result = check_python_types("src/mymodule.py")
        if not result.success:
            for diag in result.diagnostics:
                print(f"{diag.file}:{diag.line}: {diag.message}")
    """
    runner = PyrightRunner()
    path = Path(path)

    if path.is_file():
        return runner.check_file(path)
    elif path.is_dir():
        return runner.check_directory(path)
    else:
        raise ValueError(f"Path does not exist: {path}")
