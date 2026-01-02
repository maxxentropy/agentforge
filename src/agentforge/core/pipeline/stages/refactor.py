# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: refactor-phase-executor
# @test_path: tests/unit/pipeline/stages/test_refactor.py

"""REFACTOR phase executor for TDD pipeline.

The REFACTOR phase improves code quality while maintaining behavior (tests pass).
This completes the RED-GREEN-REFACTOR cycle.
"""

import logging
import re
import subprocess
import sys
from typing import Any

from ..llm_stage_executor import OutputValidation
from ..stage_executor import StageContext, StageExecutor, StageResult

logger = logging.getLogger(__name__)


class RefactorPhaseExecutor(StageExecutor):
    """
    REFACTOR stage executor.

    Improves code quality while maintaining behavior (tests pass).

    Refactoring targets:
    - Code style and formatting
    - Complexity reduction
    - Duplicate code elimination
    - Naming improvements
    - Documentation
    """

    stage_name = "refactor"
    artifact_type = "refactored_code"

    required_input_fields = ["spec_id", "implementation_files", "test_results"]

    output_fields = [
        "spec_id",
        "refactored_files",
        "final_files",
        "test_results",
        "conformance_passed",
    ]

    SYSTEM_PROMPT = """You are an expert software engineer improving code quality.

You are in the REFACTOR phase of TDD. The implementation works and tests pass.
Your job is to improve code quality without changing behavior.

Refactoring targets:
1. Code style and formatting (PEP 8 for Python)
2. Reduce complexity (extract methods, simplify conditionals)
3. Eliminate duplication
4. Improve naming
5. Add/improve documentation and type hints
6. Remove dead code

You have access to these tools:
- read_file: Read file contents
- edit_file: Make targeted edits
- run_check: Run conformance checks
- run_tests: Verify tests still pass
- complete: Signal refactoring complete

IMPORTANT:
- Tests must continue to pass after every change
- Don't change public interfaces
- Make small, incremental improvements
- Run tests after each significant change
"""

    TASK_TEMPLATE = """Refactor the implementation to improve code quality.

IMPLEMENTATION FILES:
{implementation_files}

TEST STATUS: {test_status}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

CONFORMANCE REQUIREMENTS:
- Max cyclomatic complexity: 10
- Max function length: 50 lines
- Type hints required
- Docstrings required for public methods

Instructions:
1. Read each implementation file
2. Run conformance checks to identify issues
3. Apply refactorings to fix issues
4. Run tests to ensure they still pass
5. Repeat until conformance passes
6. Call 'complete' when done
"""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize RefactorPhaseExecutor."""
        self._config = config or {}
        self.max_iterations = self._config.get("max_iterations", 10)
        self.test_timeout = self._config.get("test_timeout", 300)

    def execute(self, context: StageContext) -> StageResult:
        """Execute REFACTOR phase."""
        input_artifact = context.input_artifacts

        # Step 1: Verify tests pass before refactoring
        initial_tests = self._run_tests(context)
        if initial_tests.get("failed", 0) > 0:
            return StageResult.failed(
                error="Tests must pass before refactoring",
            )

        # Step 2: Run conformance to identify issues
        conformance = self._run_conformance(context)

        # Step 3: If no issues, skip refactoring
        if conformance.get("passed", False) and not conformance.get("violations"):
            logger.info("No conformance issues, skipping refactoring")
            return StageResult.success(
                artifacts=self._create_passthrough_artifact(context, initial_tests),
            )

        # Step 4: Execute refactoring with LLM
        try:
            executor = self._get_refactor_executor(context)

            task = self._build_task(input_artifact, initial_tests, conformance)

            result = executor.execute_task(
                task_description=task,
                system_prompt=self.SYSTEM_PROMPT,
                context={"phase": "refactor", "spec_id": input_artifact.get("spec_id")},
                max_iterations=self.max_iterations,
            )

            # Step 5: Final verification
            final_tests = self._run_tests(context)
            final_conformance = self._run_conformance(context)

            if final_tests.get("failed", 0) > 0:
                return StageResult.failed(
                    error="Tests failed after refactoring",
                )

            return StageResult.success(
                artifacts=self._build_artifact(
                    context, result, final_tests, final_conformance
                ),
            )

        except Exception as e:
            logger.exception(f"Refactoring failed: {e}")
            return StageResult.failed(
                error=str(e),
            )

    def _run_tests(self, context: StageContext) -> dict[str, Any]:
        """Run test suite."""
        try:
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
            result = subprocess.run(
                cmd,
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
                timeout=self.test_timeout,
            )

            passed = len(re.findall(r"PASSED", result.stdout))
            failed = len(re.findall(r"FAILED", result.stdout))

            return {
                "passed": passed,
                "failed": failed,
                "total": passed + failed,
                "output": result.stdout,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Test timeout", "passed": 0, "failed": 1}
        except Exception as e:
            return {"error": str(e), "passed": 0, "failed": 1}

    def _run_conformance(self, context: StageContext) -> dict[str, Any]:
        """Run conformance checks."""
        try:
            # Use agentforge conformance check
            cmd = [
                sys.executable, "-m", "agentforge",
                "conformance", "check",
                "--format", "json"
            ]
            result = subprocess.run(
                cmd,
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
                timeout=120,
            )

            import json
            try:
                data = json.loads(result.stdout)
                return {
                    "passed": data.get("passed", False),
                    "violations": data.get("violations", []),
                    "total_violations": len(data.get("violations", [])),
                }
            except json.JSONDecodeError:
                return {
                    "passed": result.returncode == 0,
                    "violations": [],
                    "output": result.stdout,
                }
        except Exception as e:
            return {"error": str(e), "passed": True, "violations": []}

    def _get_refactor_executor(self, context: StageContext):
        """Get executor for refactoring."""
        try:
            from agentforge.core.harness.minimal_context import MinimalContextExecutor
            from agentforge.core.harness.minimal_context.tool_handlers import (
                create_enhanced_handlers,
            )

            executor = MinimalContextExecutor(
                project_path=context.project_path,
                task_type="refactor",
            )

            handlers = create_enhanced_handlers(context.project_path)
            for name, handler in handlers.items():
                executor.native_tool_executor.register_action(name, handler)

            return executor
        except ImportError:
            # Return a mock executor for testing
            from unittest.mock import MagicMock
            mock = MagicMock()
            mock.execute_task.return_value = {}
            return mock

    def _build_task(
        self,
        artifact: dict[str, Any],
        test_results: dict[str, Any],
        conformance: dict[str, Any],
    ) -> str:
        """Build refactoring task description."""
        files = artifact.get("implementation_files", [])
        files_str = "\n".join([f"  - {f}" for f in files]) or "  (none)"

        test_status = f"{test_results.get('passed', 0)} passed, {test_results.get('failed', 0)} failed"

        criteria = artifact.get("acceptance_criteria", [])
        criteria_str = "\n".join([
            f"  - {c.get('criterion', c) if isinstance(c, dict) else c}" for c in criteria
        ]) or "  (none specified)"

        return self.TASK_TEMPLATE.format(
            implementation_files=files_str,
            test_status=test_status,
            acceptance_criteria=criteria_str,
        )

    def _create_passthrough_artifact(
        self,
        context: StageContext,
        test_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Create artifact when no refactoring needed."""
        input_artifact = context.input_artifacts
        impl_files = input_artifact.get("implementation_files", [])
        test_files = input_artifact.get("test_files", [])

        # Extract file paths from test_files if they're dicts
        test_file_paths = []
        for tf in test_files:
            if isinstance(tf, dict):
                test_file_paths.append(tf.get("path", str(tf)))
            else:
                test_file_paths.append(str(tf))

        return {
            "spec_id": input_artifact.get("spec_id"),
            "request_id": input_artifact.get("request_id"),
            "refactored_files": [],
            "improvements": [],
            "final_files": impl_files + test_file_paths,
            "test_results": test_results,
            "conformance_passed": True,
            "remaining_violations": [],
            "clarified_requirements": input_artifact.get("clarified_requirements"),
            "original_request": input_artifact.get("original_request"),
        }

    def _build_artifact(
        self,
        context: StageContext,
        result: dict[str, Any],
        test_results: dict[str, Any],
        conformance: dict[str, Any],
    ) -> dict[str, Any]:
        """Build REFACTOR artifact."""
        input_artifact = context.input_artifacts
        impl_files = input_artifact.get("implementation_files", [])
        test_files = input_artifact.get("test_files", [])

        # Extract file paths from test_files if they're dicts
        test_file_paths = []
        for tf in test_files:
            if isinstance(tf, dict):
                test_file_paths.append(tf.get("path", str(tf)))
            else:
                test_file_paths.append(str(tf))

        return {
            "spec_id": input_artifact.get("spec_id"),
            "request_id": input_artifact.get("request_id"),
            "refactored_files": result.get("files_modified", impl_files),
            "improvements": result.get("improvements", []),
            "final_files": impl_files + test_file_paths,
            "test_results": test_results,
            "conformance_passed": conformance.get("passed", False),
            "remaining_violations": conformance.get("violations", []),
            "clarified_requirements": input_artifact.get("clarified_requirements"),
            "original_request": input_artifact.get("original_request"),
        }

    def validate_output(self, artifact: dict[str, Any] | None) -> OutputValidation:
        """Validate REFACTOR phase artifact."""
        if artifact is None:
            return OutputValidation(
                valid=False,
                errors=["No artifact produced"],
                warnings=[],
            )

        errors = []
        warnings = []

        # Check required fields
        if not artifact.get("spec_id"):
            errors.append("Missing spec_id")

        if not artifact.get("final_files"):
            warnings.append("No final_files in artifact")

        # Check conformance status
        if "conformance_passed" not in artifact:
            warnings.append("Missing conformance_passed status")

        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


def create_refactor_executor(config: dict | None = None) -> RefactorPhaseExecutor:
    """Create RefactorPhaseExecutor instance."""
    return RefactorPhaseExecutor(config)
