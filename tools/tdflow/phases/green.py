"""
GREEN Phase Executor
====================

Generates implementation based on specifications and failing tests.

Supports two generation modes:
1. LLM-based: Uses GenerationEngine for intelligent implementation generation
2. Template-based: Falls back to scaffolding templates when no LLM is available

When using LLM generation, the engine provides:
  - Full working implementations based on spec and tests
  - Intelligent code that satisfies test requirements
  - Iterative refinement if tests don't pass

When using template generation, you get:
  - Structural scaffolding with NotImplementedError stubs
  - Correct class structure with dependencies
  - Method signatures with parameters and return types
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

import yaml

from tools.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    ImplementationFile,
    PhaseResult,
    TDFlowPhase,
    TDFlowSession,
)
from tools.tdflow.runners.base import TestRunner

if TYPE_CHECKING:
    from tools.generate.engine import GenerationEngine


class GreenPhaseExecutor:
    """
    Executes the GREEN phase: generate implementation.

    Steps:
    1. Load failing tests
    2. Load spec requirements
    3. Gather context (similar code, patterns)
    4. Generate implementation via LLM (or scaffolding)
    5. Write implementation file
    6. Run tests
    7. Verify tests PASS
    """

    MAX_ITERATIONS = 3

    def __init__(
        self,
        session: TDFlowSession,
        runner: TestRunner,
        generator: Optional["GenerationEngine"] = None,
    ):
        """
        Initialize GREEN phase executor.

        Args:
            session: Current TDFLOW session
            runner: Test runner for the project
            generator: Optional LLM generation engine for intelligent implementation
        """
        self.session = session
        self.runner = runner
        self.generator = generator
        self._spec_data: Optional[Dict[str, Any]] = None

    def execute(self, component: ComponentProgress) -> PhaseResult:
        """
        Execute GREEN phase for a component.

        Args:
            component: Component to implement

        Returns:
            PhaseResult indicating success/failure
        """
        start_time = time.time()

        # 1. Verify component is in RED state
        if component.status != ComponentStatus.RED:
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component=component.name,
                errors=[f"Component must be in RED state, not {component.status.value}"],
                duration_seconds=time.time() - start_time,
            )

        # 2. Get failing tests
        if not component.tests:
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component=component.name,
                errors=["No tests found - run RED phase first"],
                duration_seconds=time.time() - start_time,
            )

        # 3. Load component spec
        spec = self._load_component_spec(component.name)
        if not spec:
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component=component.name,
                errors=[f"Component '{component.name}' not found in specification"],
                duration_seconds=time.time() - start_time,
            )

        # 4. Iterate until tests pass or max iterations
        for iteration in range(self.MAX_ITERATIONS):
            # Generate implementation via LLM
            impl_content = self._generate_implementation(component, spec, iteration)
            if not impl_content:
                continue

            # Write implementation
            impl_path = self._get_impl_path(component, spec)
            impl_path.parent.mkdir(parents=True, exist_ok=True)
            impl_path.write_text(impl_content)

            # Build project
            if not self.runner.build():
                continue  # Try again with compile errors as feedback

            # Run tests
            result = self.runner.run_tests(filter_pattern=component.name)

            # Check if tests pass
            if result.all_passed:
                # Success! Update component
                component.status = ComponentStatus.GREEN
                component.implementation = ImplementationFile(
                    path=impl_path,
                    content=impl_content,
                )
                component.coverage = self.runner.get_coverage()

                return PhaseResult(
                    phase=TDFlowPhase.GREEN,
                    success=True,
                    component=component.name,
                    artifacts={"implementation": impl_path},
                    test_result=result,
                    duration_seconds=time.time() - start_time,
                )

        # Max iterations reached
        return PhaseResult(
            phase=TDFlowPhase.GREEN,
            success=False,
            component=component.name,
            errors=[f"Failed to pass tests after {self.MAX_ITERATIONS} iterations"],
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

    def _generate_implementation(
        self,
        component: ComponentProgress,
        spec: Dict[str, Any],
        iteration: int,
    ) -> Optional[str]:
        """
        Generate implementation via LLM or templates.

        When a generator is available, uses LLM for intelligent implementation.
        Otherwise, falls back to template scaffolding.

        Args:
            component: Component to implement
            spec: Component specification
            iteration: Current iteration number

        Returns:
            Implementation file content or None
        """
        # Try LLM generation first if available
        if self.generator:
            llm_result = self._generate_impl_with_llm(component, spec, iteration)
            if llm_result:
                return llm_result

        # Fall back to template generation
        if self.session.test_framework in ("xunit", "nunit", "mstest"):
            return self._generate_csharp_impl(component, spec)
        else:
            return self._generate_python_impl(component, spec)

    def _generate_impl_with_llm(
        self,
        component: ComponentProgress,
        spec: Dict[str, Any],
        iteration: int,
    ) -> Optional[str]:
        """
        Generate implementation using LLM via GenerationEngine.

        Args:
            component: Component to implement
            spec: Component specification
            iteration: Current iteration number (used for error context)

        Returns:
            Implementation content or None if generation fails
        """
        if not self.generator:
            return None

        try:
            from tools.generate.domain import GenerationContext, GenerationPhase

            # Get existing test content for context
            existing_tests = None
            if component.tests:
                existing_tests = component.tests.content

            # Build generation context
            context = GenerationContext.for_green(
                spec=self._spec_data or {},
                component_name=component.name,
                existing_tests=existing_tests,
            )

            # Run generation (async -> sync)
            result = asyncio.run(self.generator.generate(context, dry_run=False))

            if result.success and result.files:
                # Return the first generated file's content
                return result.files[0].content

            return None

        except Exception:
            # Fall back to template generation
            return None

    def _generate_csharp_impl(
        self,
        component: ComponentProgress,
        spec: Dict[str, Any],
    ) -> str:
        """
        Generate C# implementation from specification.

        Args:
            component: Component to implement
            spec: Component specification

        Returns:
            C# implementation content
        """
        class_name = spec.get("name", component.name)
        namespace = spec.get("namespace", "Application.Services")
        methods = spec.get("methods", [])
        dependencies = spec.get("dependencies", [])

        # Build dependency fields and constructor
        fields = []
        ctor_params = []
        ctor_assigns = []
        for dep in dependencies:
            dep_name = dep if isinstance(dep, str) else dep.get("name", "Unknown")
            field_name = f"_{dep_name[1:].lower()}" if dep_name.startswith("I") else f"_{dep_name.lower()}"
            fields.append(f"    private readonly {dep_name} {field_name};")
            ctor_params.append(f"{dep_name} {field_name.lstrip('_')}")
            ctor_assigns.append(f"        {field_name} = {field_name.lstrip('_')};")

        fields_str = "\n".join(fields) if fields else ""
        ctor_params_str = ", ".join(ctor_params)
        ctor_assigns_str = "\n".join(ctor_assigns) if ctor_assigns else "        // No dependencies"

        # Build method stubs
        method_strs = []
        for method in methods:
            method_name = method.get("name", "UnknownMethod")
            return_type = method.get("returns", "void")
            params = method.get("parameters", [])
            behavior = method.get("behavior", "")

            # Build parameter list
            param_strs = []
            for param in params:
                if isinstance(param, dict):
                    param_strs.append(f"{param.get('type', 'object')} {param.get('name', 'arg')}")
                else:
                    param_strs.append(f"object {param}")
            params_str = ", ".join(param_strs)

            method_strs.append(
                f"""
    /// <summary>
    /// {behavior}
    /// </summary>
    public {return_type} {method_name}({params_str})
    {{
        // TODO: Implement to satisfy spec behavior:
        // {behavior}
        throw new NotImplementedException();
    }}"""
            )

        methods_str = "\n".join(method_strs)

        return f"""// Generated by TDFLOW GREEN phase
// Component: {class_name}
// Spec: {self.session.spec_file}

namespace {namespace};

public class {class_name}
{{
{fields_str}

    public {class_name}({ctor_params_str})
    {{
{ctor_assigns_str}
    }}
{methods_str}
}}
"""

    def _generate_python_impl(
        self,
        component: ComponentProgress,
        spec: Dict[str, Any],
    ) -> str:
        """
        Generate Python implementation from specification.

        Args:
            component: Component to implement
            spec: Component specification

        Returns:
            Python implementation content
        """
        class_name = spec.get("name", component.name)
        methods = spec.get("methods", [])
        dependencies = spec.get("dependencies", [])

        # Build __init__ parameters
        init_params = ["self"]
        init_assigns = []
        for dep in dependencies:
            dep_name = dep if isinstance(dep, str) else dep.get("name", "unknown")
            param_name = self._to_snake_case(dep_name)
            init_params.append(f"{param_name}")
            init_assigns.append(f"        self._{param_name} = {param_name}")

        init_params_str = ", ".join(init_params)
        init_assigns_str = "\n".join(init_assigns) if init_assigns else "        pass"

        # Build method stubs
        method_strs = []
        for method in methods:
            method_name = method.get("name", "unknown_method")
            method_snake = self._to_snake_case(method_name)
            params = method.get("parameters", [])
            behavior = method.get("behavior", "")
            return_type = method.get("returns", "None")

            # Build parameter list
            param_strs = ["self"]
            for param in params:
                if isinstance(param, dict):
                    param_strs.append(f"{param.get('name', 'arg')}: {param.get('type', 'Any')}")
                else:
                    param_strs.append(f"{param}")
            params_str = ", ".join(param_strs)

            method_strs.append(
                f'''
    def {method_snake}({params_str}) -> {return_type}:
        """
        {behavior}
        """
        # TODO: Implement to satisfy spec behavior
        raise NotImplementedError()'''
            )

        methods_str = "\n".join(method_strs)

        return f'''"""
{class_name}
{"=" * len(class_name)}

Generated by TDFLOW GREEN phase.
Spec: {self.session.spec_file}
"""

from typing import Any


class {class_name}:
    """
    {spec.get("description", f"{class_name} implementation.")}
    """

    def __init__({init_params_str}):
        """Initialize {class_name}."""
{init_assigns_str}
{methods_str}
'''

    def _get_impl_path(self, component: ComponentProgress, spec: Dict[str, Any]) -> Path:
        """
        Determine implementation file path.

        Uses impl_file from spec if provided, otherwise generates path.

        Args:
            component: Component being implemented
            spec: Component specification

        Returns:
            Path for implementation file
        """
        project_root = self.runner.project_path

        # Use impl_file from spec if provided
        if spec.get("impl_file"):
            return project_root / spec["impl_file"]

        # Use spec layer if available
        layer = spec.get("layer", "Application")

        if self.session.test_framework in ("xunit", "nunit", "mstest"):
            # Look for src directory
            src_dirs = list(project_root.glob("**/src"))
            if src_dirs:
                src_root = src_dirs[0]
            else:
                src_root = project_root / "src"

            return src_root / layer / f"{component.name}.cs"
        else:
            # Python implementation
            src_dirs = list(project_root.glob("**/src"))
            if src_dirs:
                src_root = src_dirs[0]
            else:
                src_root = project_root / "src"

            return src_root / f"{self._to_snake_case(component.name)}.py"

    def _to_snake_case(self, name: str) -> str:
        """
        Convert PascalCase/camelCase to snake_case.

        Handles compound names with dots (e.g., "TokenBudget.record_usage").

        Args:
            name: Name to convert

        Returns:
            snake_case name
        """
        import re

        # Handle compound names with dots - take just the method part
        if "." in name:
            name = name.split(".")[-1]

        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
