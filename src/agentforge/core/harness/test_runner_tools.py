"""
Test Runner Tools
=================

Tools for running tests to verify fixes.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict

from .llm_executor_domain import ToolResult


class TestRunnerTools:
    """Tools for running pytest and validating changes."""

    def __init__(self, project_path: Path, timeout: int = 300):
        """
        Initialize test runner tools.

        Args:
            project_path: Project root directory
            timeout: Default timeout in seconds for test runs
        """
        self.project_path = Path(project_path)
        self.timeout = timeout

    def run_tests(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run pytest on specified path.

        Parameters:
            test_path: Path to tests (default: "tests/")
            verbose: Show verbose output
            fail_fast: Stop on first failure (default: True)
            markers: Pytest markers to select (e.g., "unit" or "not slow")

        Returns:
            ToolResult with test output
        """
        test_path = params.get("test_path", "tests/")
        verbose = params.get("verbose", False)
        fail_fast = params.get("fail_fast", True)
        markers = params.get("markers")

        try:
            cmd = ["python", "-m", "pytest", test_path, "--tb=short"]
            if verbose:
                cmd.append("-v")
            if fail_fast:
                cmd.append("-x")
            if markers:
                cmd.extend(["-m", markers])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.project_path),
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            # Limit output size
            if len(output) > 3000:
                output = output[-3000:]
                output = "... (output truncated)\n" + output

            if result.returncode == 0:
                return ToolResult.success_result("run_tests", f"Tests passed\n{output}")
            else:
                return ToolResult.failure_result(
                    "run_tests", f"Tests failed (exit {result.returncode})\n{output}"
                )

        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(
                "run_tests", f"Tests timed out after {self.timeout}s"
            )
        except Exception as e:
            return ToolResult.failure_result("run_tests", f"Error: {e}")

    def run_single_test(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run a single test file or test function.

        Parameters:
            test_path: Full path to test (e.g., "tests/unit/test_foo.py::test_bar")

        Returns:
            ToolResult with test output
        """
        test_path = params.get("test_path")
        if not test_path:
            return ToolResult.failure_result(
                "run_single_test", "Missing required parameter: test_path"
            )

        try:
            cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=long"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for single test
                cwd=str(self.project_path),
            )

            output = result.stdout + result.stderr

            if result.returncode == 0:
                return ToolResult.success_result("run_single_test", f"Passed\n{output}")
            else:
                return ToolResult.failure_result("run_single_test", f"Failed\n{output}")

        except subprocess.TimeoutExpired:
            return ToolResult.failure_result("run_single_test", "Test timed out (120s)")
        except Exception as e:
            return ToolResult.failure_result("run_single_test", f"Error: {e}")

    def run_affected_tests(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run tests that might be affected by changes to specific files.

        Parameters:
            changed_files: List of changed file paths

        Returns:
            ToolResult with test output
        """
        changed_files = params.get("changed_files", [])
        if not changed_files:
            return ToolResult.failure_result(
                "run_affected_tests", "Missing required parameter: changed_files"
            )

        if isinstance(changed_files, str):
            changed_files = [changed_files]

        # Determine related test files
        test_paths = []
        for file_path in changed_files:
            file_path = Path(file_path)

            # Try to find corresponding test file
            if file_path.suffix == ".py":
                # Check for test_<name>.py pattern
                test_name = f"test_{file_path.stem}.py"
                potential_tests = list(
                    self.project_path.rglob(f"**/{test_name}")
                )
                test_paths.extend(str(t.relative_to(self.project_path)) for t in potential_tests)

                # Check for <name>_test.py pattern
                test_name = f"{file_path.stem}_test.py"
                potential_tests = list(
                    self.project_path.rglob(f"**/{test_name}")
                )
                test_paths.extend(str(t.relative_to(self.project_path)) for t in potential_tests)

        if not test_paths:
            return ToolResult.success_result(
                "run_affected_tests",
                f"No related tests found for: {', '.join(changed_files)}",
            )

        # Remove duplicates
        test_paths = list(set(test_paths))

        # Run the tests
        return self.run_tests(
            "run_tests",
            {"test_path": " ".join(test_paths), "verbose": True, "fail_fast": True},
        )

    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "run_tests": self.run_tests,
            "run_single_test": self.run_single_test,
            "run_affected_tests": self.run_affected_tests,
        }


# Tool definitions
TEST_TOOL_DEFINITIONS = [
    {
        "name": "run_tests",
        "description": "Run pytest on specified path",
        "parameters": {
            "test_path": {
                "type": "string",
                "required": False,
                "description": "Path to tests (default: tests/)",
            },
            "verbose": {
                "type": "boolean",
                "required": False,
                "description": "Show verbose output",
            },
            "fail_fast": {
                "type": "boolean",
                "required": False,
                "description": "Stop on first failure (default: True)",
            },
            "markers": {
                "type": "string",
                "required": False,
                "description": "Pytest markers to select (e.g., 'unit' or 'not slow')",
            },
        },
    },
    {
        "name": "run_single_test",
        "description": "Run a single test file or function",
        "parameters": {
            "test_path": {
                "type": "string",
                "required": True,
                "description": "Full path to test (e.g., tests/unit/test_foo.py::test_bar)",
            }
        },
    },
    {
        "name": "run_affected_tests",
        "description": "Run tests that might be affected by changes to specific files",
        "parameters": {
            "changed_files": {
                "type": "array",
                "required": True,
                "description": "List of changed file paths",
            }
        },
    },
]
