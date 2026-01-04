"""
Command Check Handlers
======================

Shell command execution checks.
"""

import subprocess

from .types import CheckContext, CheckResult


def execute_command_check(ctx: CheckContext) -> list[CheckResult]:
    """Execute a command-based check."""
    command = ctx.config.get("command")
    args = ctx.config.get("args", [])
    working_dir = ctx.config.get("working_dir")
    timeout = ctx.config.get("timeout", 60)
    expected_exit_code = ctx.config.get("expected_exit_code", 0)

    if not command:
        return [CheckResult(
            check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
            severity="error", message="Command check missing 'command' in config"
        )]

    cwd = ctx.repo_root / working_dir if working_dir else ctx.repo_root

    try:
        result = subprocess.run(
            [command] + args, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != expected_exit_code:
            return [CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                severity=ctx.severity, fix_hint=ctx.fix_hint,
                message=f"Command failed with exit code {result.returncode}: {result.stderr or result.stdout}"
            )]

        return []

    except subprocess.TimeoutExpired:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity=ctx.severity, message=f"Command timed out after {timeout}s")]
    except FileNotFoundError:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity=ctx.severity, message=f"Command not found: {command}")]
    except Exception as e:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity="error", message=f"Command execution failed: {e}")]
