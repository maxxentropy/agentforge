# Pipeline Controller Specification - Stage 6: GREEN Phase (Implementation)

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1-5  
**Estimated Effort:** 6-7 days

---

## 1. Overview

### 1.1 Purpose

The GREEN phase implements code to make the RED phase tests pass:

1. Read failing tests from RED phase
2. Implement minimal code to pass each test
3. Run tests iteratively until all pass
4. Produce implementation artifact

### 1.2 TDD Philosophy

```
RED Phase Artifact (failing tests)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         GREEN PHASE                              │
│                                                                  │
│  "Write the simplest code that makes tests pass"                │
│                                                                  │
│  Input: Failing tests + specification                           │
│  Output: Implementation files + passing tests                   │
│                                                                  │
│  Loop:                                                          │
│  1. Pick a failing test                                         │
│  2. Write/modify code to pass it                                │
│  3. Run tests                                                   │
│  4. If still failing, adjust                                    │
│  5. Repeat until all pass                                       │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
   REFACTOR PHASE
```

---

## 2. GREEN Phase Executor

### 2.1 GreenPhaseExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/green.py

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone
import logging
import subprocess
import sys

from ..stage_executor import StageExecutor, StageContext, StageResult, StageStatus

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

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_iterations = config.get("max_iterations", 20) if config else 20
        self.test_timeout = config.get("test_timeout", 120) if config else 120
    
    def _execute(self, context: StageContext) -> StageResult:
        """Execute GREEN phase with iterative implementation."""
        artifact = context.input_artifact
        
        # Initialize tracking
        implementation_files = []
        iterations = 0
        all_tests_pass = False
        
        # Get initial test state
        test_results = self._run_all_tests(context, artifact.get("test_files", []))
        
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
            test_results = self._run_all_tests(context, artifact.get("test_files", []))
            
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
        
        return StageResult(
            stage_name=self.stage_name,
            status=status,
            artifact=final_artifact,
        )
    
    def _build_user_message(self, context: StageContext) -> str:
        """Build initial user message."""
        artifact = context.input_artifact
        spec = context.stage_artifacts.get("spec", artifact)
        
        # Format failing tests
        failing = artifact.get("failing_tests", [])
        failing_str = "\n".join([f"  - {t}" for t in failing]) or "  (none recorded)"
        
        # Format test files
        test_files = artifact.get("test_files", [])
        files_str = "\n".join([f"  - {f}" for f in test_files]) or "  (none)"
        
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
            components=components_str,
            implementation_order=order_str,
        )
    
    def _build_iteration_message(
        self,
        test_results: Dict[str, Any],
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
        executor: "MinimalContextExecutor",
        context: StageContext,
    ) -> None:
        """Register tool handlers for implementation."""
        from agentforge.core.harness.minimal_context.tool_handlers import (
            create_read_file_handler,
            create_write_file_handler,
            create_edit_file_handler,
        )
        
        project_path = context.project_path
        
        executor.native_tool_executor.register_action(
            "read_file",
            create_read_file_handler(project_path)
        )
        executor.native_tool_executor.register_action(
            "write_file",
            create_write_file_handler(project_path)
        )
        executor.native_tool_executor.register_action(
            "edit_file",
            create_edit_file_handler(project_path)
        )
        
        # Custom run_tests handler
        def run_tests_handler(params: Dict[str, Any]) -> str:
            test_files = params.get("test_files", [])
            test_name = params.get("test_name")
            
            results = self._run_all_tests(
                context,
                test_files if test_files else context.input_artifact.get("test_files", []),
                specific_test=test_name
            )
            
            return f"Tests: {results['passed']} passed, {results['failed']} failed"
        
        executor.native_tool_executor.register_action("run_tests", run_tests_handler)
        
        # Complete implementation handler (just returns the data)
        def complete_handler(params: Dict[str, Any]) -> str:
            return f"IMPLEMENTATION_COMPLETE:{params}"
        
        executor.native_tool_executor.register_action(
            "complete_implementation",
            complete_handler
        )
    
    def _run_all_tests(
        self,
        context: StageContext,
        test_files: List[str],
        specific_test: Optional[str] = None,
    ) -> Dict[str, Any]:
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
                cmd.extend(test_files)
            
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
    
    def _parse_pytest_output(self, output: str, results: Dict[str, Any]) -> None:
        """Parse pytest output."""
        import re
        
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
    
    def _check_completion(self, result: Dict[str, Any]) -> bool:
        """Check if completion was signaled."""
        tool_results = result.get("tool_results", [])
        for tr in tool_results:
            if tr.get("tool_name") == "complete_implementation":
                return True
            if "IMPLEMENTATION_COMPLETE:" in str(tr.get("result", "")):
                return True
        return False
    
    def _extract_completion_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract completion data from tool result."""
        tool_results = result.get("tool_results", [])
        for tr in tool_results:
            if tr.get("tool_name") == "complete_implementation":
                return tr.get("input", {})
        return {}
    
    def _extract_written_files(self, result: Dict[str, Any]) -> List[str]:
        """Extract list of files written during this iteration."""
        files = []
        tool_results = result.get("tool_results", [])
        
        for tr in tool_results:
            if tr.get("tool_name") == "write_file":
                path = tr.get("input", {}).get("path")
                if path:
                    files.append(path)
        
        return files
    
    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """Validate GREEN phase artifact."""
        from ..stage_executor import OutputValidation
        
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


def create_green_executor(config: Optional[Dict] = None) -> GreenPhaseExecutor:
    """Create GreenPhaseExecutor instance."""
    return GreenPhaseExecutor(config)
```

---

## 3. Implementation Strategy

### 3.1 Iterative Development Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    GREEN PHASE LOOP                              │
│                                                                  │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│   │  READ    │────▶│ IMPLEMENT│────▶│   TEST   │               │
│   │  TESTS   │     │   CODE   │     │          │               │
│   └──────────┘     └──────────┘     └────┬─────┘               │
│                                          │                      │
│                         ┌────────────────┴────────────────┐    │
│                         │                                  │    │
│                         ▼                                  ▼    │
│                  ┌──────────┐                      ┌──────────┐ │
│                  │  FAIL    │                      │  PASS    │ │
│                  │          │                      │          │ │
│                  └────┬─────┘                      └────┬─────┘ │
│                       │                                  │      │
│                       │                                  ▼      │
│                       │                          ┌──────────┐  │
│                       │                          │ COMPLETE │  │
│                       │                          └──────────┘  │
│                       │                                         │
│                       └─────────────────────────────────────────│
│                                    (loop back)                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Implementation Priorities

1. **Make imports work first** - Create module structure
2. **Stub classes/functions** - Basic structure to pass import tests
3. **Implement core logic** - Main functionality
4. **Handle edge cases** - Error handling, validation
5. **Complete interface** - All methods from spec

---

## 4. GREEN Phase Artifact

### 4.1 Schema

```yaml
# Schema for GREEN phase artifact

spec_id: string
request_id: string

implementation_files:
  - string  # List of created/modified files

test_results:
  passed: number
  failed: number
  errors: number
  total: number
  test_details:
    - name: string
      status: enum [passed, failed, error]
      message: string

passing_tests: number
all_tests_pass: boolean
iterations: number

# If failed
error: string

# Carried forward
components: [...]
test_files: [string]
```

---

## 5. Code Generation Patterns

### 5.1 Module Structure Generation

```python
# Example: Generated implementation structure

# src/auth/__init__.py
"""Authentication module."""
from .oauth_provider import OAuthProvider
from .token_manager import TokenManager

__all__ = ["OAuthProvider", "TokenManager"]


# src/auth/oauth_provider.py
"""OAuth provider implementation."""

from typing import Dict, Any, Optional
from dataclasses import dataclass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


@dataclass
class OAuthConfig:
    """OAuth configuration."""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]


class OAuthProvider:
    """
    OAuth 2.0 provider implementation.
    
    Handles authentication flow, token management, and refresh.
    """
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize provider with credentials."""
        self.client_id = client_id
        self.client_secret = client_secret
    
    def authenticate(self, code: str) -> Dict[str, Any]:
        """
        Authenticate with authorization code.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dict containing access_token and refresh_token
            
        Raises:
            ValueError: If code is empty or None
            AuthenticationError: If authentication fails
        """
        if not code:
            raise ValueError("Authorization code is required")
        
        # Implementation here
        ...
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict containing new access_token
        """
        ...
```

### 5.2 Minimal Implementation Strategy

```python
# Strategy: Start with stubs, fill in as tests demand

# Iteration 1: Make imports work
class OAuthProvider:
    pass

# Iteration 2: Constructor passes
class OAuthProvider:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

# Iteration 3: Method signature passes
class OAuthProvider:
    def authenticate(self, code: str) -> Dict[str, Any]:
        return {"access_token": "token"}

# Iteration 4: Validation passes
class OAuthProvider:
    def authenticate(self, code: str) -> Dict[str, Any]:
        if not code:
            raise ValueError("Authorization code is required")
        return {"access_token": "token"}

# Final: Full implementation
```

---

## 6. Error Handling

### 6.1 Common Failure Patterns

| Issue | Detection | Resolution |
|-------|-----------|------------|
| Import error | Test fails with ImportError | Create missing module/class |
| Missing method | Test fails with AttributeError | Add method stub |
| Wrong return type | AssertionError on type | Fix return type |
| Missing validation | Test expects exception | Add validation |
| Logic error | Assertion mismatch | Debug and fix logic |

### 6.2 Self-Healing Strategies

```python
# When tests fail, the GREEN phase:

1. Reads error message
2. Identifies failure type:
   - ImportError → Create module/class
   - AttributeError → Add method
   - AssertionError → Fix logic
   - Exception type → Add exception class
3. Makes targeted fix
4. Re-runs specific test
5. If pass, runs full suite
6. Repeats until done
```

---

## 7. Configuration

### 7.1 Stage Configuration

```yaml
# .agentforge/config/stages/green.yaml

stage: green

execution:
  max_iterations: 20
  test_timeout_seconds: 120
  continue_on_partial_success: true

implementation:
  style: minimal  # minimal, standard, comprehensive
  include_docstrings: true
  include_type_hints: true
  
testing:
  run_after_each_file: true
  run_specific_test_first: true
  full_suite_on_completion: true
```

---

## 8. Test Specification

### 8.1 Unit Tests

```python
# tests/unit/pipeline/stages/test_green.py

class TestGreenPhaseExecutor:
    """Tests for GreenPhaseExecutor."""
    
    def test_reads_test_files_first(self, mock_llm, tmp_path):
        """First action is reading test files."""
    
    def test_creates_implementation_files(self, mock_llm, tmp_path):
        """Creates files to implement components."""
    
    def test_runs_tests_after_changes(self, mock_llm, tmp_path):
        """Runs tests after each implementation."""
    
    def test_iterates_until_tests_pass(self, mock_llm, tmp_path):
        """Continues iterating until all tests pass."""
    
    def test_stops_at_max_iterations(self, mock_llm, tmp_path):
        """Stops after max iterations even if failing."""
    
    def test_signals_completion_when_done(self, mock_llm, tmp_path):
        """Calls complete_implementation when all pass."""
    
    def test_tracks_implementation_files(self, mock_llm, tmp_path):
        """Tracks all files created/modified."""


class TestIterativeImplementation:
    """Tests for iterative implementation logic."""
    
    def test_makes_progress_each_iteration(self, mock_llm, tmp_path):
        """Each iteration reduces failing tests."""
    
    def test_handles_regression(self, mock_llm, tmp_path):
        """Handles case where fix breaks other tests."""
```

### 8.2 Integration Tests

```python
# tests/integration/pipeline/stages/test_green_phase.py

class TestGreenPhaseIntegration:
    """Integration tests for GREEN phase."""
    
    def test_red_to_green_flow(self, mock_llm, tmp_path):
        """Full flow from RED (failing) to GREEN (passing)."""
    
    def test_complex_implementation(self, mock_llm, tmp_path):
        """Implements multiple related components."""
    
    def test_handles_import_dependencies(self, mock_llm, tmp_path):
        """Correctly handles import dependencies between files."""
```

---

## 9. Success Criteria

1. **Functional:**
   - [ ] Reads and understands test requirements
   - [ ] Creates implementation files
   - [ ] Iterates until tests pass
   - [ ] Handles common error patterns

2. **Quality:**
   - [ ] Generated code follows style guidelines
   - [ ] Minimal implementation (no over-engineering)
   - [ ] Proper error handling

3. **TDD Compliance:**
   - [ ] Only implements what tests require
   - [ ] All tests pass at completion
   - [ ] Clean handoff to REFACTOR

---

## 10. Dependencies

- **Stage 5:** RED phase test files and failing tests
- **P0 Tool Handlers:** read_file, write_file, edit_file
- **Existing:** MinimalContextExecutor, pytest

---

*Next: Stage 7 - Refactor & Deliver Stages*
