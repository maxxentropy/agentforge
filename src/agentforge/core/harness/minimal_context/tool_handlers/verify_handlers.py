# @spec_file: specs/tools/01-tool-handlers.yaml
# @spec_id: tool-handlers-v1
# @component_id: verify-handlers
# @test_path: tests/unit/harness/tool_handlers/test_verify_handlers.py

"""
Verification Handlers
=====================

Handlers for verification operations: run_check, run_tests.

These handlers wrap existing infrastructure (ConformanceManager, TestRunner)
to provide consistent interfaces for the agent.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .types import ActionHandler


def create_run_check_handler(project_path: Optional[Path] = None) -> ActionHandler:
    """
    Create a run_check action handler.

    Re-runs conformance checking after a fix to verify the violation is resolved.
    Wraps ConformanceManager and VerificationRunner.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: Dict[str, Any]) -> str:
        file_path = params.get("file_path") or params.get("path")
        check_type = params.get("check_type")
        check_id = params.get("check_id")

        # Get context for violation-specific checking
        context = params.get("_context", {})
        target_violation = context.get("violation_id")
        context_check_id = context.get("check_id")

        # Use context check_id if not provided directly
        if not check_id and context_check_id:
            check_id = context_check_id

        # Use context file_path if not provided directly
        if not file_path and context.get("file_path"):
            file_path = context.get("file_path")

        try:
            # Try to use ConformanceTools if available
            try:
                from agentforge.harness.conformance_tools import ConformanceTools

                conformance = ConformanceTools(base_path)

                if check_id and file_path:
                    # Targeted check (faster)
                    result = conformance.run_conformance_check(
                        "run_conformance_check",
                        {"check_id": check_id, "file_path": file_path},
                    )
                elif file_path:
                    # File-level check
                    result = conformance.check_file("check_file", {"file_path": file_path})
                else:
                    # Full check
                    result = conformance.run_full_check("run_full_check", {})

                if result.success:
                    return (
                        f"CHECK PASSED\n"
                        f"  File: {file_path or 'all'}\n"
                        f"  Check: {check_id or 'all'}\n"
                        f"  {result.output[:500] if result.output else 'All checks passing'}"
                    )
                else:
                    return (
                        f"CHECK FAILED\n"
                        f"  File: {file_path or 'all'}\n"
                        f"  Check: {check_id or 'all'}\n"
                        f"  {result.output[:800] if result.output else 'Violations found'}"
                    )

            except ImportError:
                # Fall back to direct runner invocation
                return _run_check_fallback(base_path, file_path, check_type)

        except FileNotFoundError as e:
            return f"ERROR: Configuration not found: {e}"
        except Exception as e:
            return f"ERROR: Check failed: {e}"

    def _run_check_fallback(
        base_path: Path, file_path: Optional[str], check_type: Optional[str]
    ) -> str:
        """Fallback implementation using subprocess."""
        cmd = [sys.executable, "-m", "agentforge", "verify"]

        if file_path:
            cmd.extend(["--file", file_path])
        if check_type:
            cmd.extend(["--check", check_type])

        try:
            result = subprocess.run(
                cmd,
                cwd=str(base_path),
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return f"CHECK PASSED\n{result.stdout[:500]}"
            else:
                return f"CHECK FAILED\n{result.stdout[:500]}\n{result.stderr[:300]}"

        except subprocess.TimeoutExpired:
            return "ERROR: Check timed out after 120 seconds"
        except Exception as e:
            return f"ERROR: Failed to run check: {e}"

    return handler


def create_run_check_handler_v2(project_path: Optional[Path] = None) -> ActionHandler:
    """
    Enhanced run_check handler with violation-specific checking.

    Can verify a specific violation ID was resolved or run general checks.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: Dict[str, Any]) -> str:
        file_path = params.get("file_path")
        check_type = params.get("check_type")
        violation_id = params.get("violation_id")

        # Get context from working memory if available
        context = params.get("_context", {})
        target_violation = context.get("violation_id") or violation_id

        try:
            # If we have a target violation, check if it's resolved
            if target_violation:
                return _check_violation_resolved(base_path, target_violation, file_path)
            else:
                # General check
                return _run_general_check(base_path, file_path, check_type)

        except Exception as e:
            return f"ERROR: Check failed: {e}"

    def _check_violation_resolved(
        base_path: Path, violation_id: str, file_path: Optional[str]
    ) -> str:
        """Check if a specific violation was resolved."""
        import yaml

        # Load violation data
        violation_file = base_path / ".agentforge" / "violations" / f"{violation_id}.yaml"

        if not violation_file.exists():
            return f"ERROR: Violation {violation_id} not found"

        try:
            with open(violation_file) as f:
                violation = yaml.safe_load(f)
        except Exception as e:
            return f"ERROR: Failed to load violation: {e}"

        target_file = file_path or violation.get("file_path")
        check_id = violation.get("check_id")

        if not target_file:
            return "ERROR: No file path available for violation"

        # Try to use ConformanceTools
        try:
            from agentforge.harness.conformance_tools import ConformanceTools

            conformance = ConformanceTools(base_path)

            result = conformance.run_conformance_check(
                "run_conformance_check",
                {"check_id": check_id, "file_path": target_file},
            )

            if result.success:
                # Mark as resolved
                violation["status"] = "resolved"
                with open(violation_file, "w") as f:
                    yaml.dump(violation, f, default_flow_style=False)

                return (
                    f"VIOLATION {violation_id} RESOLVED\n"
                    f"  File: {target_file}\n"
                    f"  Check: {check_id}\n"
                    f"  The specific violation no longer appears."
                )
            else:
                return (
                    f"VIOLATION {violation_id} STILL PRESENT\n"
                    f"  File: {target_file}\n"
                    f"  Check: {check_id}\n"
                    f"  Message: {violation.get('message', 'Unknown')}\n"
                    f"  The violation was not fixed by the changes."
                )

        except ImportError:
            return (
                "ERROR: ConformanceTools not available. "
                "Cannot verify violation resolution."
            )

    def _run_general_check(
        base_path: Path, file_path: Optional[str], check_type: Optional[str]
    ) -> str:
        """Run general conformance check."""
        try:
            from agentforge.harness.conformance_tools import ConformanceTools

            conformance = ConformanceTools(base_path)

            if file_path:
                result = conformance.check_file("check_file", {"file_path": file_path})
            else:
                result = conformance.run_full_check("run_full_check", {})

            if result.success:
                return f"CHECK PASSED (all checks run)\n{result.output[:500]}"
            else:
                return f"CHECK FAILED\n{result.output[:800]}"

        except ImportError:
            return "ERROR: ConformanceTools not available"

    return handler


def create_run_tests_handler(project_path: Optional[Path] = None) -> ActionHandler:
    """
    Create a run_tests action handler.

    Runs tests to verify changes don't break existing functionality.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: Dict[str, Any]) -> str:
        test_path = params.get("path") or params.get("test_path")
        verbose = params.get("verbose", False)

        # Get context for affected files
        context = params.get("_context", {})
        files_modified = context.get("files_modified", [])

        try:
            # Try to use TestRunnerTools if available
            try:
                from agentforge.harness.test_runner_tools import TestRunnerTools

                test_tools = TestRunnerTools(base_path)

                if test_path:
                    # Run specific test
                    result = test_tools.run_single_test(
                        "run_single_test", {"test_path": test_path}
                    )
                elif files_modified:
                    # Run tests affected by modified files
                    result = test_tools.run_affected_tests(
                        "run_affected_tests", {"files": files_modified}
                    )
                else:
                    # Run all tests
                    result = test_tools.run_tests("run_tests", {})

                if result.success:
                    return (
                        f"TESTS PASSED\n"
                        f"  {result.output[:500] if result.output else 'All tests passing'}"
                    )
                else:
                    return (
                        f"TESTS FAILED\n"
                        f"  {result.output[:800] if result.output else 'Test failures detected'}"
                    )

            except ImportError:
                # Fall back to pytest directly
                return _run_pytest_fallback(base_path, test_path, verbose)

        except Exception as e:
            return f"ERROR: Tests failed: {e}"

    def _run_pytest_fallback(
        base_path: Path, test_path: Optional[str], verbose: bool
    ) -> str:
        """Fallback implementation using pytest directly."""
        cmd = [sys.executable, "-m", "pytest"]

        if test_path:
            cmd.append(test_path)
        else:
            cmd.append("tests/")

        cmd.append("-v" if verbose else "-q")
        cmd.append("--tb=short")
        cmd.append("-x")  # Stop on first failure

        try:
            result = subprocess.run(
                cmd,
                cwd=str(base_path),
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                return f"TESTS PASSED\n{result.stdout[-500:]}"
            else:
                # Extract failure info
                output = result.stdout[-800:] if result.stdout else ""
                stderr = result.stderr[-300:] if result.stderr else ""
                return f"TESTS FAILED\n{output}\n{stderr}"

        except subprocess.TimeoutExpired:
            return "ERROR: Tests timed out after 300 seconds"
        except Exception as e:
            return f"ERROR: Failed to run tests: {e}"

    return handler


def create_validate_python_handler(project_path: Optional[Path] = None) -> ActionHandler:
    """
    Create a validate_python action handler.

    Validates a Python file for syntax and import errors.
    This is a fast check that catches errors before running full tests.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: Dict[str, Any]) -> str:
        file_path = params.get("file_path") or params.get("path")

        if not file_path:
            return "ERROR: file_path parameter required"

        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = base_path / file_path

        if not full_path.exists():
            return f"ERROR: File not found: {file_path}"

        if not full_path.suffix == ".py":
            return f"ERROR: Not a Python file: {file_path}"

        try:
            import ast

            source = full_path.read_text()

            # Step 1: Check syntax with ast.parse
            try:
                ast.parse(source)
            except SyntaxError as e:
                return f"SYNTAX ERROR at line {e.lineno}: {e.msg}"

            # Step 2: Try to compile and import to catch undefined names
            check_script = f"""
import sys
import importlib.util
try:
    spec = importlib.util.spec_from_file_location("_check_module", {repr(str(full_path))})
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("OK")
except AttributeError as e:
    print(f"AttributeError: {{e}}")
    sys.exit(1)
except NameError as e:
    print(f"NameError: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"{{type(e).__name__}}: {{e}}")
    sys.exit(1)
"""

            result = subprocess.run(
                [sys.executable, "-c", check_script],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(base_path),
                env={**subprocess.os.environ, "PYTHONPATH": str(base_path)},
            )

            if result.returncode != 0:
                error_msg = result.stdout.strip() or result.stderr.strip()
                return f"VALIDATION FAILED: {error_msg}"

            return (
                f"VALIDATION PASSED\n"
                f"  File: {file_path}\n"
                f"  Syntax: OK\n"
                f"  Imports: OK"
            )

        except subprocess.TimeoutExpired:
            return "ERROR: Validation timed out"
        except Exception as e:
            return f"ERROR: Validation failed: {e}"

    return handler
