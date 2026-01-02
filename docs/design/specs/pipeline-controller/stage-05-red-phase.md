# Pipeline Controller Specification - Stage 5: RED Phase (Test Generation)

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1-4  
**Estimated Effort:** 5-6 days

---

## 1. Overview

### 1.1 Purpose

The RED phase implements Test-Driven Development by generating tests BEFORE implementation:

1. Generate test files based on specification
2. Run tests to confirm they fail (no implementation yet)
3. Produce test artifact with failing test details

### 1.2 TDD Philosophy

```
Specification (from SPEC stage)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                          RED PHASE                               │
│                                                                  │
│  "Write tests first, watch them fail"                           │
│                                                                  │
│  Input: Specification with test_cases                           │
│  Output: Test files + failing test results                      │
│                                                                  │
│  Steps:                                                         │
│  1. Read spec test_cases                                        │
│  2. Generate test file for each component                       │
│  3. Write tests following Given/When/Then                       │
│  4. Run tests (should fail)                                     │
│  5. Validate all expected tests fail appropriately              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
   GREEN PHASE (implementation)
```

---

## 2. RED Phase Executor

### 2.1 RedPhaseExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/red.py

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import logging
import subprocess
import sys

from ..llm_stage_executor import LLMStageExecutor
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
    
    SYSTEM_PROMPT = """You are an expert test engineer implementing Test-Driven Development.

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

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.test_runner = config.get("test_runner", "pytest") if config else "pytest"
    
    def _execute(self, context: StageContext) -> StageResult:
        """Execute RED phase: generate tests then verify they fail."""
        # Step 1: Generate test files using LLM
        generation_result = super()._execute(context)
        
        if not generation_result.success:
            return generation_result
        
        artifact = generation_result.artifact
        test_files = artifact.get("test_files", [])
        
        if not test_files:
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error="No test files generated",
            )
        
        # Step 2: Write test files to disk
        written_files = self._write_test_files(context, test_files)
        
        if not written_files:
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error="Failed to write test files",
            )
        
        # Step 3: Run tests (expecting failures)
        test_results = self._run_tests(context, written_files)
        
        # Step 4: Validate that tests failed appropriately
        validation = self._validate_red_results(test_results)
        
        if not validation["valid"]:
            if validation.get("unexpected_passes"):
                # Some tests passed - implementation may already exist
                logger.warning(f"Unexpected passing tests: {validation['unexpected_passes']}")
                artifact["warnings"] = [
                    f"Some tests passed unexpectedly: {validation['unexpected_passes']}"
                ]
        
        # Update artifact with results
        artifact["test_files"] = written_files
        artifact["test_results"] = test_results
        artifact["failing_tests"] = validation.get("failing_tests", [])
        
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.COMPLETED,
            artifact=artifact,
        )
    
    def get_system_prompt(self, context: StageContext) -> str:
        """Get test generation system prompt."""
        return self.SYSTEM_PROMPT
    
    def get_user_message(self, context: StageContext) -> str:
        """Build user message for test generation."""
        spec = context.input_artifact
        
        # Format components detail
        components = spec.get("components", [])
        components_detail = ""
        for comp in components:
            components_detail += f"\n### {comp.get('name', 'Unknown')}\n"
            components_detail += f"Type: {comp.get('type', 'unknown')}\n"
            components_detail += f"File: {comp.get('file_path', 'unknown')}\n"
            components_detail += f"Description: {comp.get('description', 'N/A')}\n"
            
            # Include interface if present
            interface = comp.get("interface", {})
            if interface.get("methods"):
                components_detail += "Methods:\n"
                for method in interface["methods"]:
                    components_detail += f"  - {method.get('signature', 'N/A')}\n"
                    components_detail += f"    {method.get('description', '')}\n"
        
        # Format test cases
        test_cases = spec.get("test_cases", [])
        test_cases_detail = ""
        for tc in test_cases:
            test_cases_detail += f"\n### {tc.get('id', 'TC-?')}: {tc.get('description', 'N/A')}\n"
            test_cases_detail += f"Component: {tc.get('component', 'unknown')}\n"
            test_cases_detail += f"Type: {tc.get('type', 'unit')}\n"
            test_cases_detail += f"Given: {tc.get('given', 'N/A')}\n"
            test_cases_detail += f"When: {tc.get('when', 'N/A')}\n"
            test_cases_detail += f"Then: {tc.get('then', 'N/A')}\n"
        
        # Format acceptance criteria
        criteria = spec.get("acceptance_criteria", [])
        criteria_detail = "\n".join([
            f"- {c.get('criterion', 'N/A')}"
            for c in criteria
        ]) or "- No specific criteria"
        
        return self.USER_MESSAGE_TEMPLATE.format(
            spec_id=spec.get("spec_id", "SPEC-UNKNOWN"),
            title=spec.get("title", "Unknown Feature"),
            components_detail=components_detail,
            test_cases_detail=test_cases_detail,
            acceptance_criteria=criteria_detail,
        )
    
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Parse generated test files from response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")
        
        # Extract file blocks
        test_files = self._extract_file_blocks(response_text)
        
        if not test_files:
            logger.error("No test files found in response")
            return None
        
        return {
            "spec_id": context.input_artifact.get("spec_id"),
            "test_files": test_files,
            "test_results": {},  # Will be populated after running tests
            "failing_tests": [],
        }
    
    def _extract_file_blocks(self, response_text: str) -> List[Dict[str, str]]:
        """Extract file path and content blocks from response."""
        import re
        
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
        test_files: List[Dict[str, str]],
    ) -> List[str]:
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
        test_files: List[str],
    ) -> Dict[str, Any]:
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
            self._parse_pytest_output(process.stdout, results)
            
        except subprocess.TimeoutExpired:
            results["error"] = "Test run timed out"
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def _parse_pytest_output(self, output: str, results: Dict[str, Any]) -> None:
        """Parse pytest output to extract test counts."""
        import re
        
        # Look for summary line: "X passed, Y failed, Z errors"
        summary_match = re.search(
            r"(\d+) passed.*?(\d+) failed|(\d+) failed.*?(\d+) passed|(\d+) passed|(\d+) failed",
            output
        )
        
        if summary_match:
            groups = summary_match.groups()
            for i, g in enumerate(groups):
                if g:
                    if "passed" in output[summary_match.start():summary_match.end()]:
                        results["passed"] = int(g)
                    if "failed" in output[summary_match.start():summary_match.end()]:
                        results["failed"] = int(g)
        
        # Count individual test results
        passed_tests = re.findall(r"(test_\w+)\s+PASSED", output)
        failed_tests = re.findall(r"(test_\w+)\s+FAILED", output)
        error_tests = re.findall(r"(test_\w+)\s+ERROR", output)
        
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
    
    def _validate_red_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
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
        pass_ratio = test_results.get("passed", 0) / max(test_results.get("total", 1), 1)
        if pass_ratio > 0.5:
            validation["warnings"].append(
                f"{pass_ratio:.0%} of tests passed - expected failures in RED phase"
            )
        
        return validation
    
    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """Validate RED phase artifact."""
        from ..stage_executor import OutputValidation
        
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


def create_red_executor(config: Optional[Dict] = None) -> RedPhaseExecutor:
    """Create RedPhaseExecutor instance."""
    return RedPhaseExecutor(config)
```

### 2.2 Test File Generation Patterns

```python
# Generated test file example

# tests/test_oauth_provider.py
"""
Tests for OAuth Provider component.

Generated from SPEC-20260102-0001
These tests are written BEFORE implementation (TDD RED phase).
"""

import pytest
from unittest.mock import Mock, patch


class TestOAuthProvider:
    """Unit tests for OAuthProvider class."""
    
    @pytest.fixture
    def provider(self):
        """Create OAuthProvider instance for testing."""
        # Import will fail until implementation exists
        from src.auth.oauth_provider import OAuthProvider
        return OAuthProvider(client_id="test", client_secret="secret")
    
    # TC001: Test successful authentication flow
    def test_authenticate_returns_token_on_success(self, provider):
        """
        Given: Valid OAuth credentials
        When: authenticate() is called with valid code
        Then: Returns access token
        """
        # Arrange
        code = "valid_auth_code"
        
        # Act
        result = provider.authenticate(code)
        
        # Assert
        assert result is not None
        assert "access_token" in result
        assert result["access_token"] != ""
    
    # TC002: Test invalid code handling
    def test_authenticate_raises_on_invalid_code(self, provider):
        """
        Given: Invalid authorization code
        When: authenticate() is called
        Then: Raises AuthenticationError
        """
        # Arrange
        invalid_code = "invalid_code"
        
        # Act & Assert
        with pytest.raises(AuthenticationError):
            provider.authenticate(invalid_code)
    
    # TC003: Test token refresh
    def test_refresh_token_returns_new_token(self, provider):
        """
        Given: Valid refresh token
        When: refresh_token() is called
        Then: Returns new access token
        """
        # Arrange
        refresh_token = "valid_refresh_token"
        
        # Act
        result = provider.refresh_token(refresh_token)
        
        # Assert
        assert result is not None
        assert "access_token" in result
    
    # Edge case: Empty code
    def test_authenticate_raises_on_empty_code(self, provider):
        """
        Given: Empty authorization code
        When: authenticate() is called
        Then: Raises ValueError
        """
        with pytest.raises(ValueError):
            provider.authenticate("")
    
    # Edge case: None code
    def test_authenticate_raises_on_none_code(self, provider):
        """
        Given: None as authorization code
        When: authenticate() is called
        Then: Raises ValueError
        """
        with pytest.raises(ValueError):
            provider.authenticate(None)
```

---

## 3. RED Phase Artifact

### 3.1 Schema

```yaml
# Schema for RED phase artifact

spec_id: string
request_id: string

test_files:
  - path: string          # Relative path to test file
    content: string       # Full file content (for reference)

test_results:
  passed: number
  failed: number
  errors: number
  skipped: number
  total: number
  exit_code: number
  output: string          # Raw pytest output
  test_details:
    - name: string
      status: enum [passed, failed, error, skipped]
      message: string     # Error message if failed

failing_tests: [string]   # List of failing test names (expected)
unexpected_passes: [string]  # Tests that passed unexpectedly

warnings: [string]        # Any warnings from validation

# Carried forward
components: [...]         # From spec
acceptance_criteria: [...] # From spec
```

---

## 4. Test Generation Strategies

### 4.1 Component-Based Test Organization

```
tests/
├── unit/
│   ├── test_oauth_provider.py    # Tests for OAuthProvider
│   ├── test_token_manager.py     # Tests for TokenManager
│   └── test_user_auth.py         # Tests for UserAuth
├── integration/
│   └── test_oauth_flow.py        # End-to-end OAuth flow
└── conftest.py                   # Shared fixtures
```

### 4.2 Test Case Mapping

| Spec Test Case | Generated Test |
|----------------|----------------|
| TC001: Happy path | `test_<action>_returns_<result>_on_success` |
| TC002: Error case | `test_<action>_raises_<error>_on_<condition>` |
| TC003: Edge case | `test_<action>_handles_<edge_condition>` |

---

## 5. Integration with Test Framework

### 5.1 pytest Configuration

```ini
# pytest.ini for RED phase tests

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    red: Tests from RED phase (expected to fail initially)
    unit: Unit tests
    integration: Integration tests
```

### 5.2 Test Markers

```python
# Using markers for RED phase tests

import pytest

@pytest.mark.red
class TestOAuthProvider:
    """RED phase tests - expected to fail until implementation."""
    
    @pytest.mark.unit
    def test_authenticate_success(self):
        ...
    
    @pytest.mark.integration
    def test_full_oauth_flow(self):
        ...
```

---

## 6. Configuration

### 6.1 Stage Configuration

```yaml
# .agentforge/config/stages/red.yaml

stage: red

test_framework: pytest
test_directory: tests

generation:
  include_edge_cases: true
  include_error_cases: true
  tests_per_component: 5-10
  
validation:
  allow_some_passes: true
  max_pass_ratio: 0.3  # Warn if more than 30% pass
  
execution:
  timeout_seconds: 300
  parallel: false  # Run sequentially for clearer output
  collect_coverage: false  # Coverage meaningless in RED
```

---

## 7. Test Specification

### 7.1 Unit Tests

```python
# tests/unit/pipeline/stages/test_red.py

class TestRedPhaseExecutor:
    """Tests for RedPhaseExecutor."""
    
    def test_generates_test_files_from_spec(self, mock_llm, tmp_path):
        """Generates test files based on spec test_cases."""
    
    def test_writes_test_files_to_disk(self, mock_llm, tmp_path):
        """Test files are written to correct locations."""
    
    def test_runs_pytest_on_generated_tests(self, mock_llm, tmp_path):
        """Runs pytest on generated test files."""
    
    def test_reports_failing_tests(self, mock_llm, tmp_path):
        """Reports expected failing tests."""
    
    def test_warns_on_unexpected_passes(self, mock_llm, tmp_path):
        """Warns when tests pass unexpectedly."""
    
    def test_handles_pytest_timeout(self, mock_llm, tmp_path):
        """Handles test execution timeout."""
    
    def test_parses_pytest_output_correctly(self):
        """Correctly parses pytest summary output."""


class TestTestFileExtraction:
    """Tests for file block extraction."""
    
    def test_extracts_single_file(self):
        """Extracts single file from response."""
    
    def test_extracts_multiple_files(self):
        """Extracts multiple files from response."""
    
    def test_handles_missing_file_marker(self):
        """Handles response without file markers."""
```

### 7.2 Integration Tests

```python
# tests/integration/pipeline/stages/test_red_phase.py

class TestRedPhaseIntegration:
    """Integration tests for RED phase."""
    
    def test_full_spec_to_tests_flow(self, mock_llm, tmp_path):
        """Full flow from spec to generated tests."""
    
    def test_tests_fail_without_implementation(self, tmp_path):
        """Generated tests fail when no implementation exists."""
    
    def test_tests_pass_with_stub_implementation(self, tmp_path):
        """Tests pass when stub implementation is added."""
```

---

## 8. Success Criteria

1. **Functional:**
   - [ ] Generates test files from specification
   - [ ] Tests follow Given/When/Then pattern
   - [ ] Tests are runnable with pytest
   - [ ] Correctly reports failing tests

2. **Quality:**
   - [ ] Generated tests are readable
   - [ ] Edge cases are covered
   - [ ] Tests are properly organized

3. **TDD Compliance:**
   - [ ] Tests fail initially (no implementation)
   - [ ] Warns on unexpected passes
   - [ ] Clear path to GREEN phase

---

## 9. Dependencies

- **Stage 4:** Specification with test_cases
- **External:** pytest
- **Existing:** MinimalContextExecutor

---

*Next: Stage 6 - GREEN Phase (Implementation)*
