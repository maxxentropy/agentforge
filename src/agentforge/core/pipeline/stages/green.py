# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: green-phase-executor
# @test_path: tests/unit/pipeline/stages/test_green.py

"""
GREEN Phase Executor
====================

Implements the GREEN phase of TDD: implement code to make tests pass.

This stage:
1. Reads failing tests from RED phase
2. Implements minimal code to pass each test
3. Runs tests iteratively until all pass
4. Produces implementation artifact

TDD Philosophy: "Write the simplest code that makes tests pass"
"""

import logging
import re
import subprocess
import sys
from typing import Any

from ..llm_stage_executor import OutputValidation
from ..stage_executor import StageContext, StageExecutor, StageResult, StageStatus

logger = logging.getLogger(__name__)


class GreenPhaseExecutor(StageExecutor):
    """
    GREEN phase executor - Implementation.

    Implements code to make RED phase tests pass.
    Uses iterative approach: implement -> test -> fix -> repeat.

    This is the most complex stage as it involves:
    - Understanding test requirements
    - Generating implementation code
    - Iterating until tests pass
    - Handling compilation/import errors
    """

    stage_name = "green"
    artifact_type = "implementation"

    required_input_fields = ["spec_id", "test_files", "failing_tests"]

    output_fields = [
        "spec_id",
        "implementation_files",
        "test_results",
    ]

    # Tools for implementation
    tools = [
        {
            "name": "read_file",
            "description": "Read a file from the project",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write content to a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "edit_file",
            "description": "Edit a specific section of a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_content": {"type": "string"},
                    "new_content": {"type": "string"},
                },
                "required": ["path", "old_content", "new_content"],
            },
        },
        {
            "name": "run_tests",
            "description": "Run the test suite",
            "input_schema": {
                "type": "object",
                "properties": {
                    "test_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific test files to run (optional)",
                    },
                    "test_name": {
                        "type": "string",
                        "description": "Specific test name to run (optional)",
                    },
                },
            },
        },
        {
            "name": "complete_implementation",
            "description": "Signal that implementation is complete",
            "input_schema": {
                "type": "object",
                "properties": {
                    "implementation_files": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "summary": {"type": "string"},
                },
                "required": ["implementation_files"],
            },
        },
    ]

    SYSTEM_PROMPT = """You are an expert software developer implementing code to pass tests.

You are in the GREEN phase of TDD. Tests have been written (RED phase) and you must now write the MINIMAL implementation to make them pass.

Your approach:
1. Read the failing tests to understand requirements
2. Implement code to make tests pass
3. Run tests to verify
4. Fix any remaining failures
5. Repeat until all tests pass

IMPORTANT PRINCIPLES:
- Write the SIMPLEST code that passes the tests
- Don't add features not tested
- Don't optimize prematurely
- Follow existing code style
- Handle errors properly

You have access to these tools:
- read_file: Read existing code or tests
- write_file: Create new implementation files
- edit_file: Modify existing files
- run_tests: Run tests to check progress
- complete_implementation: Signal completion when all tests pass

Begin by reading the test files to understand what you need to implement.
"""

    USER_MESSAGE_TEMPLATE = """Implement code to make these tests pass:

SPEC ID: {spec_id}

FAILING TESTS ({num_failing}):
{failing_tests}

TEST FILES:
{test_files}

COMPONENTS TO IMPLEMENT:
{components}

IMPLEMENTATION ORDER (from spec):
{implementation_order}

Instructions:
1. Read the test files to understand requirements
2. Create/modify implementation files
3. Run tests after each significant change
4. Continue until all tests pass
5. Call complete_implementation when done

Start by reading the test files.
"""

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self.max_iterations = self._config.get("max_iterations", 20)
        self.test_timeout = self._config.get("test_timeout", 120)

    def execute(self, context: StageContext) -> StageResult:
        """Execute GREEN phase with iterative implementation."""
        artifact = context.input_artifacts

        # Initialize tracking
        implementation_files = []
        iterations = 0
        all_tests_pass = False

        # Get test files from input
        test_file_paths = []
        for tf in artifact.get("test_files", []):
            if isinstance(tf, dict):
                test_file_paths.append(tf.get("path", ""))
            else:
                test_file_paths.append(str(tf))

        # Get initial test state
        test_results = self._run_all_tests(context, test_file_paths)

        # Set up executor with tools
        executor = self._get_executor(context)
        self._register_implementation_tools(executor, context)

        # Build initial message
        system_prompt = self.SYSTEM_PROMPT
        user_message = self._build_user_message(context)

        # Iterative implementation loop
        while iterations < self.max_iterations and not all_tests_pass:
            iterations += 1
            logger.info(f"GREEN phase iteration {iterations}/{self.max_iterations}")

            # Execute LLM step
            result = executor.execute_task(
                task_description=user_message,
                system_prompt=system_prompt,
                context={
                    "iteration": iterations,
                    "test_results": test_results,
                    "implementation_files": implementation_files,
                },
                tools=self.tools,
                max_iterations=10,  # Tool calls per LLM iteration
            )

            # Check for completion signal
            if self._check_completion(result):
                completion_data = self._extract_completion_data(result)
                implementation_files = completion_data.get("implementation_files", implementation_files)
                break

            # Update implementation files from tool calls
            new_files = self._extract_written_files(result)
            for f in new_files:
                if f not in implementation_files:
                    implementation_files.append(f)

            # Run tests
            test_results = self._run_all_tests(context, test_file_paths)

            # Check if all pass
            if test_results.get("failed", 1) == 0 and test_results.get("passed", 0) > 0:
                all_tests_pass = True
                logger.info("All tests passing!")
            else:
                # Update message with current status
                user_message = self._build_iteration_message(test_results, iterations)

        # Build final artifact
        final_artifact = {
            "spec_id": artifact.get("spec_id"),
            "implementation_files": implementation_files,
            "test_results": test_results,
            "passing_tests": test_results.get("passed", 0),
            "iterations": iterations,
            "all_tests_pass": all_tests_pass,
        }

        # Determine status
        if all_tests_pass:
            status = StageStatus.COMPLETED
        elif iterations >= self.max_iterations:
            status = StageStatus.FAILED
            final_artifact["error"] = f"Max iterations ({self.max_iterations}) reached"
        else:
            status = StageStatus.FAILED
            final_artifact["error"] = "Implementation incomplete"

        if status == StageStatus.COMPLETED:
            return StageResult.success(artifacts=final_artifact)
        else:
            return StageResult(
                status=status,
                artifacts=final_artifact,
                error=final_artifact.get("error"),
            )

    def _get_executor(self, context: StageContext):
        """Get the LLM executor for this stage."""
        # Import here to avoid circular imports
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor

        return MinimalContextExecutor(
            project_path=context.project_path,
        )

    def _build_user_message(self, context: StageContext) -> str:
        """Build initial user message."""
        artifact = context.input_artifacts
        spec = artifact  # Use input_artifacts as spec source

        # Format failing tests
        failing = artifact.get("failing_tests", [])
        failing_str = "\n".join([f"  - {t}" for t in failing]) or "  (none recorded)"

        # Format test files
        test_files = artifact.get("test_files", [])
        files_list = []
        for tf in test_files:
            if isinstance(tf, dict):
                files_list.append(tf.get("path", "unknown"))
            else:
                files_list.append(str(tf))
        files_str = "\n".join([f"  - {f}" for f in files_list]) or "  (none)"

        # Format components
        components = spec.get("components", [])
        components_str = ""
        for comp in components:
            components_str += f"\n  {comp.get('name', 'Unknown')}:\n"
            components_str += f"    File: {comp.get('file_path', 'TBD')}\n"
            components_str += f"    Type: {comp.get('type', 'unknown')}\n"

        # Format implementation order
        impl_order = spec.get("implementation_order", [])
        order_str = "\n".join([
            f"  {o.get('step', '?')}. {o.get('description', 'N/A')}"
            for o in impl_order
        ]) or "  (not specified)"

        return self.USER_MESSAGE_TEMPLATE.format(
            spec_id=artifact.get("spec_id", "SPEC-UNKNOWN"),
            num_failing=len(failing),
            failing_tests=failing_str,
            test_files=files_str,
            components=components_str or "  (none specified)",
            implementation_order=order_str,
        )

    def _build_iteration_message(
        self,
        test_results: dict[str, Any],
        iteration: int,
    ) -> str:
        """Build message for subsequent iterations."""
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        total = passed + failed

        message = f"""Iteration {iteration} complete.

TEST RESULTS:
  Passed: {passed}/{total}
  Failed: {failed}/{total}

"""

        if failed > 0:
            message += "REMAINING FAILURES:\n"
            for detail in test_results.get("test_details", []):
                if detail.get("status") == "failed":
                    message += f"  - {detail.get('name', 'unknown')}\n"
                    if detail.get("message"):
                        message += f"    Error: {detail['message'][:200]}\n"

            message += "\nContinue implementing to fix remaining failures."
        else:
            message += "All tests pass! Call complete_implementation to finish."

        return message

    def _register_implementation_tools(
        self,
        executor,
        context: StageContext,
    ) -> None:
        """Register tool handlers for implementation."""
        project_path = context.project_path

        # Read file handler
        def read_file_handler(params: dict[str, Any]) -> str:
            path = params.get("path", "")
            file_path = project_path / path
            if file_path.exists():
                return file_path.read_text()
            return f"File not found: {path}"

        # Write file handler
        def write_file_handler(params: dict[str, Any]) -> str:
            path = params.get("path", "")
            content = params.get("content", "")
            file_path = project_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return f"Wrote {len(content)} bytes to {path}"

        # Edit file handler
        def edit_file_handler(params: dict[str, Any]) -> str:
            path = params.get("path", "")
            old_content = params.get("old_content", "")
            new_content = params.get("new_content", "")
            file_path = project_path / path

            if not file_path.exists():
                return f"File not found: {path}"

            content = file_path.read_text()
            if old_content not in content:
                return f"Content not found in {path}"

            content = content.replace(old_content, new_content, 1)
            file_path.write_text(content)
            return f"Updated {path}"

        # Run tests handler
        def run_tests_handler(params: dict[str, Any]) -> str:
            test_files = params.get("test_files", [])
            test_name = params.get("test_name")

            if not test_files:
                test_files = [
                    tf.get("path") if isinstance(tf, dict) else str(tf)
                    for tf in context.input_artifacts.get("test_files", [])
                ]

            results = self._run_all_tests(
                context,
                test_files,
                specific_test=test_name
            )

            return f"Tests: {results['passed']} passed, {results['failed']} failed"

        # Complete implementation handler
        def complete_handler(params: dict[str, Any]) -> str:
            return f"IMPLEMENTATION_COMPLETE:{params}"

        # Register handlers
        if hasattr(executor, "native_tool_executor"):
            executor.native_tool_executor.register_action("read_file", read_file_handler)
            executor.native_tool_executor.register_action("write_file", write_file_handler)
            executor.native_tool_executor.register_action("edit_file", edit_file_handler)
            executor.native_tool_executor.register_action("run_tests", run_tests_handler)
            executor.native_tool_executor.register_action("complete_implementation", complete_handler)

    def _run_all_tests(
        self,
        context: StageContext,
        test_files: list[str],
        specific_test: str | None = None,
    ) -> dict[str, Any]:
        """Run tests and return results."""
        results = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "test_details": [],
        }

        try:
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]

            if specific_test:
                cmd.extend(["-k", specific_test])
            elif test_files:
                cmd.extend([f for f in test_files if f])

            process = subprocess.run(
                cmd,
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
                timeout=self.test_timeout,
            )

            self._parse_pytest_output(process.stdout + process.stderr, results)

        except subprocess.TimeoutExpired:
            results["error"] = "Test timeout"
        except Exception as e:
            results["error"] = str(e)

        return results

    def _parse_pytest_output(self, output: str, results: dict[str, Any]) -> None:
        """Parse pytest output."""
        # Extract test results
        passed = re.findall(r"(\S+::\S+)\s+PASSED", output)
        failed = re.findall(r"(\S+::\S+)\s+FAILED", output)

        results["passed"] = len(passed)
        results["failed"] = len(failed)
        results["total"] = len(passed) + len(failed)

        for test in passed:
            results["test_details"].append({"name": test, "status": "passed"})

        for test in failed:
            # Try to extract error message
            error_match = re.search(
                rf"{re.escape(test)}.*?(?:AssertionError|Error|Exception):\s*(.+?)(?:\n|$)",
                output,
                re.DOTALL
            )
            message = error_match.group(1)[:200] if error_match else None
            results["test_details"].append({
                "name": test,
                "status": "failed",
                "message": message,
            })

    def _check_completion(self, result: dict[str, Any]) -> bool:
        """Check if completion was signaled."""
        tool_results = result.get("tool_results", [])
        for tr in tool_results:
            if tr.get("tool_name") == "complete_implementation":
                return True
            if "IMPLEMENTATION_COMPLETE:" in str(tr.get("result", "")):
                return True
        return False

    def _extract_completion_data(self, result: dict[str, Any]) -> dict[str, Any]:
        """Extract completion data from tool result."""
        tool_results = result.get("tool_results", [])
        for tr in tool_results:
            if tr.get("tool_name") == "complete_implementation":
                return tr.get("input", {})
        return {}

    def _extract_written_files(self, result: dict[str, Any]) -> list[str]:
        """Extract list of files written during this iteration."""
        files = []
        tool_results = result.get("tool_results", [])

        for tr in tool_results:
            if tr.get("tool_name") == "write_file":
                path = tr.get("input", {}).get("path")
                if path:
                    files.append(path)

        return files

    def validate_output(self, artifact: dict[str, Any] | None) -> OutputValidation:
        """Validate GREEN phase artifact."""
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])

        errors = []
        warnings = []

        if not artifact.get("implementation_files"):
            errors.append("No implementation files produced")

        if not artifact.get("all_tests_pass"):
            test_results = artifact.get("test_results", {})
            failed = test_results.get("failed", 0)
            if failed > 0:
                errors.append(f"{failed} tests still failing")

        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


def create_green_executor(config: dict | None = None) -> GreenPhaseExecutor:
    """Create GreenPhaseExecutor instance."""
    return GreenPhaseExecutor(config)
