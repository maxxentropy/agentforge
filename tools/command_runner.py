"""
Command runner for external tool execution.

Runs linting/analysis tools as subprocesses and parses their output.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CommandResult:
    """Result of running an external command."""
    success: bool
    return_code: int
    stdout: str
    stderr: str
    parsed_output: Any | None = None


class CommandRunner:
    """Runs external commands for contract checks."""

    def __init__(self, working_dir: Path | None = None):
        self.working_dir = working_dir or Path.cwd()

    def run(
        self,
        command: list[str],
        *,
        parse_json: bool = False,
        timeout: int = 120,
        success_codes: list[int] | None = None
    ) -> CommandResult:
        """
        Run a command and return the result.

        Args:
            command: Command and arguments as list.
            parse_json: If True, parse stdout as JSON.
            timeout: Timeout in seconds.
            success_codes: Return codes considered success. Default [0].

        Returns:
            CommandResult with output.
        """
        success_codes = success_codes or [0]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.working_dir,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                parsed_output=None
            )
        except FileNotFoundError:
            return CommandResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Command not found: {command[0]}",
                parsed_output=None
            )

        parsed = None
        if parse_json and result.stdout:
            try:
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError:
                pass  # Leave parsed as None

        return CommandResult(
            success=result.returncode in success_codes,
            return_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            parsed_output=parsed
        )

    # Convenience methods for common tools

    def run_ruff_check(self, path: Path | str) -> CommandResult:
        """Run ruff linter."""
        return self.run(
            ["ruff", "check", str(path), "--output-format=json"],
            parse_json=True
        )

    def run_ruff_format_check(self, path: Path | str) -> CommandResult:
        """Check if ruff formatting is needed."""
        return self.run(
            ["ruff", "format", "--check", str(path)],
            success_codes=[0, 1]  # 1 means formatting needed
        )

    def run_mypy(self, path: Path | str) -> CommandResult:
        """Run mypy type checker."""
        return self.run(
            ["mypy", str(path), "--output=json"],
            parse_json=True,
            success_codes=[0, 1]  # 1 means type errors found
        )

    def run_bandit(self, path: Path | str) -> CommandResult:
        """Run bandit security scanner."""
        return self.run(
            ["bandit", "-r", str(path), "-f", "json"],
            parse_json=True,
            success_codes=[0, 1]  # 1 means issues found
        )

    def run_radon_cc(self, path: Path | str) -> CommandResult:
        """Run radon cyclomatic complexity."""
        return self.run(
            ["radon", "cc", str(path), "-j"],
            parse_json=True
        )
