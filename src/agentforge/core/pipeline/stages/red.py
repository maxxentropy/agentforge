# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: red-phase-executor
# @test_path: tests/unit/pipeline/stages/test_red.py

"""
RED Phase Executor
==================

Implements the RED phase of TDD: generate tests BEFORE implementation.

This stage:
1. Generates test files based on specification
2. Writes test files to disk
3. Runs tests to confirm they fail (expected - no implementation)
4. Produces artifact with failing test details

TDD Philosophy: "Write tests first, watch them fail"
"""

import logging
import re
import subprocess
import sys
from typing import Any

from ..llm_stage_executor import LLMStageExecutor, OutputValidation
from ..stage_executor import StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class RedPhaseExecutor(LLMStageExecutor):
    """
    RED phase executor - Test generation.

    Generates test files from specification before implementation.
    Tests should fail initially (no implementation exists yet).

    This enforces TDD discipline and ensures testability.
    """

    stage_name = "red"
    artifact_type = "test_suite"

    required_input_fields = ["spec_id", "components", "test_cases"]

    output_fields = [
        "spec_id",
        "test_files",
        "test_results",
    ]

    SYSTEM_PROMPT = """You are an expert test engineer implementing Test-Driven Development (TDD).

Your task is to generate test files based on a specification. These tests will be written BEFORE the implementation exists, so they SHOULD FAIL initially.

For each test case in the specification:
1. Generate proper test code following the Given/When/Then pattern
2. Use appropriate assertions
3. Include proper setup and teardown
4. Handle edge cases

Test Framework: pytest (Python)
Style:
- Use descriptive test names
- Use fixtures for setup
- Include docstrings explaining the test
- Group related tests in classes

IMPORTANT:
- Tests should be complete and runnable
- Tests should fail because the implementation doesn't exist yet
- Don't mock the component under test - we want real failures
- Do mock external dependencies

Output each test file with a clear file path marker.
"""

    USER_MESSAGE_TEMPLATE = """Generate test files for this specification:

SPEC ID: {spec_id}
TITLE: {title}

COMPONENTS TO TEST:
{components_detail}

TEST CASES FROM SPEC:
{test_cases_detail}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

Generate complete test files. For each file, use this format:

### FILE: tests/test_component_name.py
```python
# Test file content here
```

Requirements:
1. Generate a test file for each component that has test cases
2. Include all test cases from the spec
3. Add sensible additional edge case tests
4. Use pytest fixtures for setup
5. Tests should be runnable but will fail (no implementation yet)
"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.test_runner = config.get("test_runner", "pytest") if config else "pytest"

    def execute(self, context: StageContext) -> StageResult:
        """Execute RED phase: generate tests then verify they fail."""
        # Step 1: Generate test files using LLM
        generation_result = super().execute(context)

        if generation_result.status != StageStatus.COMPLETED:
            return generation_result

        artifact = generation_result.artifacts
        test_files = artifact.get("test_files", [])

        if not test_files:
            return StageResult.failed("No test files generated")

        # Step 2: Write test files to disk
        written_files = self._write_test_files(context, test_files)

        if not written_files:
            return StageResult.failed("Failed to write test files")

        # Step 3: Run tests (expecting failures)
        test_results = self._run_tests(context, written_files)

        # Step 4: Validate that tests failed appropriately
        validation = self._validate_red_results(test_results)

        if not validation["valid"] and validation.get("unexpected_passes"):
            # Some tests passed - implementation may already exist
            logger.warning(f"Unexpected passing tests: {validation['unexpected_passes']}")
            artifact["warnings"] = [
                f"Some tests passed unexpectedly: {validation['unexpected_passes']}"
            ]

        # Update artifact with results
        artifact["test_files"] = [{"path": f, "content": ""} for f in written_files]
        artifact["test_results"] = test_results
        artifact["failing_tests"] = validation.get("failing_tests", [])
        artifact["unexpected_passes"] = validation.get("unexpected_passes", [])
        if validation.get("warnings"):
            artifact["warnings"] = validation["warnings"]

        return StageResult.success(artifacts=artifact)

    def get_system_prompt(self, context: StageContext) -> str:
        """Get test generation system prompt."""
        return self.SYSTEM_PROMPT

    def _format_component(self, comp: dict) -> str:
        """Format a single component with its interface."""
        result = f"\n### {comp.get('name', 'Unknown')}\n"
        result += f"Type: {comp.get('type', 'unknown')}\n"
        result += f"File: {comp.get('file_path', 'unknown')}\n"
        result += f"Description: {comp.get('description', 'N/A')}\n"

        interface = comp.get("interface", {})
        if interface.get("methods"):
            result += "Methods:\n"
            for method in interface["methods"]:
                result += f"  - {method.get('signature', 'N/A')}\n"
                result += f"    {method.get('description', '')}\n"
        return result

    def _format_test_case(self, tc: dict) -> str:
        """Format a single test case."""
        result = f"\n### {tc.get('id', 'TC-?')}: {tc.get('description', 'N/A')}\n"
        result += f"Component: {tc.get('component', 'unknown')}\n"
        result += f"Type: {tc.get('type', 'unit')}\n"
        result += f"Given: {tc.get('given', 'N/A')}\n"
        result += f"When: {tc.get('when', 'N/A')}\n"
        result += f"Then: {tc.get('then', 'N/A')}\n"
        return result

    def _format_acceptance_criteria(self, criteria: list | Any) -> str:
        """Format acceptance criteria list."""
        if not isinstance(criteria, list):
            return "- No specific criteria"
        if not criteria:
            return "- No specific criteria"
        return "\n".join([
            f"- {c.get('criterion', c) if isinstance(c, dict) else c}"
            for c in criteria
        ])

    def get_user_message(self, context: StageContext) -> str:
        """Build user message for test generation."""
        spec = context.input_artifacts

        components_detail = "".join(
            self._format_component(comp) for comp in spec.get("components", [])
        )
        test_cases_detail = "".join(
            self._format_test_case(tc) for tc in spec.get("test_cases", [])
        )

        return self.USER_MESSAGE_TEMPLATE.format(
            spec_id=spec.get("spec_id", "SPEC-UNKNOWN"),
            title=spec.get("title", "Unknown Feature"),
            components_detail=components_detail or "(No components defined)",
            test_cases_detail=test_cases_detail or "(No test cases defined)",
            acceptance_criteria=self._format_acceptance_criteria(spec.get("acceptance_criteria", [])),
        )

    def parse_response(
        self,
        llm_result: dict[str, Any],
        context: StageContext,
    ) -> dict[str, Any] | None:
        """Parse generated test files from response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")

        # Extract file blocks
        test_files = self._extract_file_blocks(response_text)

        if not test_files:
            logger.error("No test files found in response")
            return None

        return {
            "spec_id": context.input_artifacts.get("spec_id"),
            "test_files": test_files,
            "test_results": {},  # Will be populated after running tests
            "failing_tests": [],
        }

    def _extract_file_blocks(self, response_text: str) -> list[dict[str, str]]:
        """Extract file path and content blocks from response."""
        files = []

        # Pattern: ### FILE: path/to/file.py followed by code block
        pattern = r"###\s*FILE:\s*([^\n]+)\n```(?:python)?\n(.*?)```"

        matches = re.findall(pattern, response_text, re.DOTALL)

        for file_path, content in matches:
            file_path = file_path.strip()
            content = content.strip()

            if file_path and content:
                files.append({
                    "path": file_path,
                    "content": content,
                })

        return files

    def _write_test_files(
        self,
        context: StageContext,
        test_files: list[dict[str, str]],
    ) -> list[str]:
        """Write test files to disk."""
        written = []

        for file_info in test_files:
            file_path = context.project_path / file_info["path"]

            try:
                # Create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write content
                file_path.write_text(file_info["content"])

                written.append(str(file_path.relative_to(context.project_path)))
                logger.info(f"Wrote test file: {file_path}")

            except Exception as e:
                logger.error(f"Failed to write {file_path}: {e}")

        return written

    def _run_tests(
        self,
        context: StageContext,
        test_files: list[str],
    ) -> dict[str, Any]:
        """Run tests and collect results."""
        results = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "total": 0,
            "test_details": [],
            "output": "",
        }

        try:
            # Build pytest command
            cmd = [
                sys.executable, "-m", "pytest",
                "-v",
                "--tb=short",
                "-q",
            ] + test_files

            # Run pytest
            process = subprocess.run(
                cmd,
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            results["output"] = process.stdout + process.stderr
            results["exit_code"] = process.returncode

            # Parse results
            self._parse_pytest_output(process.stdout + process.stderr, results)

        except subprocess.TimeoutExpired:
            results["error"] = "Test run timed out"
        except Exception as e:
            results["error"] = str(e)

        return results

    def _parse_pytest_output(self, output: str, results: dict[str, Any]) -> None:
        """Parse pytest output to extract test counts."""
        # Extract test results with full path format
        passed_tests = re.findall(r"(\S+::\S+)\s+PASSED", output)
        failed_tests = re.findall(r"(\S+::\S+)\s+FAILED", output)
        error_tests = re.findall(r"(\S+::\S+)\s+ERROR", output)

        results["passed"] = len(passed_tests)
        results["failed"] = len(failed_tests)
        results["errors"] = len(error_tests)
        results["total"] = results["passed"] + results["failed"] + results["errors"]

        # Record test details
        for test in failed_tests:
            results["test_details"].append({
                "name": test,
                "status": "failed",
            })
        for test in passed_tests:
            results["test_details"].append({
                "name": test,
                "status": "passed",
            })

    def _validate_red_results(self, test_results: dict[str, Any]) -> dict[str, Any]:
        """
        Validate RED phase results.

        In RED phase, tests SHOULD fail because implementation doesn't exist.
        Unexpected passes might indicate:
        - Implementation already exists
        - Tests are trivially passing
        - Mocking is hiding real failures
        """
        validation = {
            "valid": True,
            "failing_tests": [],
            "unexpected_passes": [],
            "warnings": [],
        }

        # If no tests ran, that's a problem
        if test_results.get("total", 0) == 0:
            validation["valid"] = False
            validation["warnings"].append("No tests were executed")
            return validation

        # Collect failing tests (expected in RED)
        for test in test_results.get("test_details", []):
            if test["status"] == "failed":
                validation["failing_tests"].append(test["name"])
            elif test["status"] == "passed":
                validation["unexpected_passes"].append(test["name"])

        # All tests passing in RED is suspicious
        if test_results.get("failed", 0) == 0 and test_results.get("passed", 0) > 0:
            validation["warnings"].append(
                "All tests passed - verify implementation doesn't exist"
            )

        # Some passes are OK (setup tests, etc.) but should be minority
        total = max(test_results.get("total", 1), 1)
        pass_ratio = test_results.get("passed", 0) / total
        if pass_ratio > 0.5:
            validation["warnings"].append(
                f"{pass_ratio:.0%} of tests passed - expected failures in RED phase"
            )

        return validation

    def validate_output(self, artifact: dict[str, Any] | None) -> OutputValidation:
        """Validate RED phase artifact."""
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])

        errors = []
        warnings = []

        if not artifact.get("test_files"):
            errors.append("No test files generated")

        test_results = artifact.get("test_results", {})
        if test_results.get("total", 0) == 0:
            warnings.append("No tests were executed")

        # Check for failing tests (expected in RED)
        if not artifact.get("failing_tests"):
            warnings.append("No failing tests - expected in RED phase")

        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


def create_red_executor(config: dict | None = None) -> RedPhaseExecutor:
    """Create RedPhaseExecutor instance."""
    return RedPhaseExecutor(config)
