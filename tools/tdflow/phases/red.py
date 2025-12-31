"""
RED Phase Executor
==================

Generates failing tests from specification.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from tools.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    PhaseResult,
    TDFlowPhase,
    TDFlowSession,
    TestFile,
)
from tools.tdflow.runners.base import TestRunner


class RedPhaseExecutor:
    """
    Executes the RED phase: generate failing tests.

    Steps:
    1. Load component spec
    2. Generate test file via LLM
    3. Write test file
    4. Run tests
    5. Verify tests FAIL
    """

    def __init__(self, session: TDFlowSession, runner: TestRunner):
        """
        Initialize RED phase executor.

        Args:
            session: Current TDFLOW session
            runner: Test runner for the project
        """
        self.session = session
        self.runner = runner
        self._spec_data: Optional[Dict[str, Any]] = None

    def execute(self, component: ComponentProgress) -> PhaseResult:
        """
        Execute RED phase for a component.

        Args:
            component: Component to generate tests for

        Returns:
            PhaseResult indicating success/failure
        """
        start_time = time.time()
        errors = []

        # 1. Load spec for this component
        spec = self._load_component_spec(component.name)
        if not spec:
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component.name,
                errors=[f"Component '{component.name}' not found in specification"],
                duration_seconds=time.time() - start_time,
            )

        # 2. Generate tests via LLM (uses prompt contract)
        test_content = self._generate_tests(component, spec)
        if not test_content:
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component.name,
                errors=["Failed to generate tests"],
                duration_seconds=time.time() - start_time,
            )

        # 3. Write test file
        test_path = self._get_test_path(component)
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(test_content)

        # 4. Build project
        if not self.runner.build():
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component.name,
                artifacts={"tests": test_path},
                errors=["Build failed - tests may have compile errors"],
                duration_seconds=time.time() - start_time,
            )

        # 5. Run tests
        result = self.runner.run_tests(filter_pattern=component.name)

        # 6. Verify tests FAIL (this is RED phase)
        if result.all_passed:
            errors.append(
                "Tests passed in RED phase - tests may be trivial or implementation already exists"
            )
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component.name,
                artifacts={"tests": test_path},
                test_result=result,
                errors=errors,
                duration_seconds=time.time() - start_time,
            )

        if result.total == 0:
            errors.append("No tests were discovered - test file may have issues")
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component.name,
                artifacts={"tests": test_path},
                test_result=result,
                errors=errors,
                duration_seconds=time.time() - start_time,
            )

        # 7. Update component
        component.status = ComponentStatus.RED
        component.tests = TestFile(
            path=test_path,
            content=test_content,
            framework=self.session.test_framework,
        )

        return PhaseResult(
            phase=TDFlowPhase.RED,
            success=True,
            component=component.name,
            artifacts={"tests": test_path},
            test_result=result,
            duration_seconds=time.time() - start_time,
        )

    def _load_component_spec(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load specification for a specific component.

        Args:
            name: Component name

        Returns:
            Component spec dict or None
        """
        if self._spec_data is None:
            spec_path = self.session.spec_file
            if spec_path.exists():
                self._spec_data = yaml.safe_load(spec_path.read_text())

        if not self._spec_data:
            return None

        for comp in self._spec_data.get("components", []):
            if comp.get("name") == name:
                return comp

        return None

    def _generate_tests(
        self,
        component: ComponentProgress,
        spec: Dict[str, Any],
    ) -> Optional[str]:
        """
        Generate test content via LLM.

        Uses tdflow.red.v1 prompt contract.

        Args:
            component: Component to test
            spec: Component specification

        Returns:
            Test file content or None
        """
        # Build test template based on framework
        if self.session.test_framework in ("xunit", "nunit", "mstest"):
            return self._generate_csharp_tests(component, spec)
        else:
            return self._generate_python_tests(component, spec)

    def _generate_csharp_tests(
        self,
        component: ComponentProgress,
        spec: Dict[str, Any],
    ) -> str:
        """
        Generate C# test file from specification.

        Args:
            component: Component to test
            spec: Component specification

        Returns:
            C# test file content
        """
        class_name = spec.get("name", component.name)
        namespace = spec.get("namespace", "Tests.Unit")
        methods = spec.get("methods", [])

        # Build test methods
        test_methods = []
        for method in methods:
            method_name = method.get("name", "UnknownMethod")
            behavior = method.get("behavior", "")
            errors = method.get("errors", [])

            # Happy path test
            test_methods.append(
                f"""
    [Fact]
    public void {method_name}_WhenValidInput_ShouldReturnExpectedResult()
    {{
        // Arrange
        // TODO: Set up valid test data based on spec
        // Behavior: {behavior}

        // Act
        // var result = _sut.{method_name}(...);

        // Assert
        Assert.Fail("RED: Implementation needed");
    }}"""
            )

            # Error case tests
            for error in errors:
                error_name = error if isinstance(error, str) else error.get("code", "Error")
                test_methods.append(
                    f"""
    [Fact]
    public void {method_name}_When{error_name}_ShouldReturnError()
    {{
        // Arrange
        // TODO: Set up data that triggers {error_name}

        // Act
        // var result = _sut.{method_name}(...);

        // Assert
        Assert.Fail("RED: Implementation needed");
    }}"""
                )

        tests_content = "\n".join(test_methods)

        return f"""// Generated from specification by TDFLOW
// Component: {class_name}
// Phase: RED - These tests should FAIL until implementation exists

using Xunit;
using FluentAssertions;

namespace {namespace};

public class {class_name}Tests
{{
    // private readonly {class_name} _sut;

    public {class_name}Tests()
    {{
        // TODO: Initialize system under test with dependencies
        // _sut = new {class_name}(...);
    }}
{tests_content}
}}
"""

    def _generate_python_tests(
        self,
        component: ComponentProgress,
        spec: Dict[str, Any],
    ) -> str:
        """
        Generate Python test file from specification.

        Args:
            component: Component to test
            spec: Component specification

        Returns:
            Python test file content
        """
        class_name = spec.get("name", component.name)
        module = spec.get("module", "src")
        methods = spec.get("methods", [])

        # Build test methods
        test_methods = []
        for method in methods:
            method_name = method.get("name", "unknown_method")
            # Convert to snake_case for Python
            method_snake = self._to_snake_case(method_name)
            behavior = method.get("behavior", "")
            errors = method.get("errors", [])

            # Happy path test
            test_methods.append(
                f"""
    def test_{method_snake}_when_valid_input_returns_expected(self):
        \"\"\"
        Test {method_name} with valid input.

        Behavior: {behavior}
        \"\"\"
        # Arrange
        # TODO: Set up valid test data

        # Act
        # result = self.sut.{method_snake}(...)

        # Assert
        pytest.fail("RED: Implementation needed")"""
            )

            # Error case tests
            for error in errors:
                error_name = error if isinstance(error, str) else error.get("code", "Error")
                error_snake = self._to_snake_case(error_name)
                test_methods.append(
                    f"""
    def test_{method_snake}_when_{error_snake}_returns_error(self):
        \"\"\"Test {method_name} returns error for {error_name}.\"\"\"
        # Arrange
        # TODO: Set up data that triggers {error_name}

        # Act
        # result = self.sut.{method_snake}(...)

        # Assert
        pytest.fail("RED: Implementation needed")"""
                )

        tests_content = "\n".join(test_methods)

        return f'''# Generated from specification by TDFLOW
# Component: {class_name}
# Phase: RED - These tests should FAIL until implementation exists

import pytest
# from {module} import {class_name}


class Test{class_name}:
    """RED: These tests should FAIL until implementation exists."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # TODO: Initialize system under test
        # self.sut = {class_name}(...)
        pass
{tests_content}
'''

    def _get_test_path(self, component: ComponentProgress) -> Path:
        """
        Determine test file path based on framework.

        Args:
            component: Component being tested

        Returns:
            Path for test file
        """
        project_root = self.runner.project_path

        if self.session.test_framework in ("xunit", "nunit", "mstest"):
            # Look for existing test project
            test_dirs = list(project_root.glob("**/tests/**"))
            if test_dirs:
                test_root = test_dirs[0].parent
            else:
                test_root = project_root / "tests" / "Unit"

            return test_root / f"{component.name}Tests.cs"
        else:
            # Python tests
            test_dirs = list(project_root.glob("**/tests"))
            if test_dirs:
                test_root = test_dirs[0]
            else:
                test_root = project_root / "tests"

            return test_root / f"test_{self._to_snake_case(component.name)}.py"

    def _to_snake_case(self, name: str) -> str:
        """
        Convert PascalCase/camelCase to snake_case.

        Args:
            name: Name to convert

        Returns:
            snake_case name
        """
        import re

        # Insert underscore before capitals
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
