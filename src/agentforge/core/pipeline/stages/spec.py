# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: spec-executor
# @test_path: tests/unit/pipeline/stages/test_spec.py

"""
Spec Stage Executor
===================

SPEC is the fourth stage of the pipeline. It generates a detailed
technical specification including:
- Component design
- Interface definitions
- Test case specifications
- Acceptance criteria

This is a critical stage that bridges analysis to implementation.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import yaml

from ..llm_stage_executor import LLMStageExecutor, OutputValidation
from ..stage_executor import StageContext, StageResult

logger = logging.getLogger(__name__)


class SpecExecutor(LLMStageExecutor):
    """
    SPEC stage executor.

    Generates a detailed technical specification including:
    - Component design
    - Interface definitions
    - Test case specifications
    - Acceptance criteria

    This is a critical stage that bridges analysis to implementation.
    """

    stage_name = "spec"
    artifact_type = "specification"

    required_input_fields = ["request_id", "analysis", "components"]

    output_fields = [
        "spec_id",
        "request_id",
        "components",
        "test_cases",
    ]

    SYSTEM_PROMPT = """You are an expert software architect creating a detailed technical specification.

Given the requirements and codebase analysis, you must produce a specification that includes:

1. COMPONENT DESIGN
   - Clear component definitions with responsibilities
   - Interface contracts between components
   - Data models and schemas

2. IMPLEMENTATION PLAN
   - Ordered list of implementation steps
   - File-by-file changes required
   - Dependencies between changes

3. TEST CASES
   - Unit test specifications for each component
   - Integration test specifications
   - Edge cases and error conditions

4. ACCEPTANCE CRITERIA
   - Clear, measurable success criteria
   - Performance requirements if applicable
   - Security considerations

Output your specification as YAML in a code block.

IMPORTANT:
- Be precise and actionable
- Include enough detail for implementation
- Test cases should be concrete, not abstract
- Consider the existing codebase structure
"""

    USER_MESSAGE_TEMPLATE = """Create a technical specification for this feature:

REQUIREMENTS:
{requirements}

ANALYSIS SUMMARY:
{analysis_summary}

COMPLEXITY: {complexity}
ESTIMATED EFFORT: {effort}

AFFECTED FILES:
{affected_files}

IDENTIFIED COMPONENTS:
{components}

RISKS:
{risks}

Create a detailed specification:

```yaml
spec_id: "{spec_id}"
request_id: "{request_id}"
title: "Feature Title"
version: "1.0"
created_at: "{timestamp}"

overview:
  description: |
    Brief description of what this specification covers.
  goals:
    - Primary goal 1
    - Primary goal 2
  non_goals:
    - What this does NOT include

components:
  - name: "ComponentName"
    type: "class"  # class, module, function, api
    file_path: "src/path/to/file.py"
    description: "What this component does"
    responsibilities:
      - "Responsibility 1"
      - "Responsibility 2"
    interface:
      methods:
        - name: "method_name"
          signature: "def method_name(param1: str) -> bool"
          description: "What it does"
          params:
            - name: "param1"
              type: "str"
              description: "Parameter description"
          returns: "bool indicating success"
          raises:
            - "ValueError: when param1 is empty"
    dependencies:
      - "other_module"

test_cases:
  - id: "TC001"
    component: "ComponentName"
    type: "unit"  # unit, integration, e2e
    description: "Test description"
    given: "Initial state or preconditions"
    when: "Action taken"
    then: "Expected outcome"
    priority: "high"  # high, medium, low

interfaces:
  - name: "InterfaceName"
    type: "protocol"  # protocol, abstract_class, api
    methods:
      - signature: "def method(args) -> return_type"

data_models:
  - name: "ModelName"
    type: "dataclass"
    fields:
      - name: "field_name"
        type: "str"
        description: "Field description"
        required: true

implementation_order:
  - step: 1
    description: "First implementation step"
    files: ["file1.py"]
    depends_on: []
  - step: 2
    description: "Second step"
    files: ["file2.py"]
    depends_on: [1]

acceptance_criteria:
  - criterion: "All unit tests pass"
    measurable: true
  - criterion: "No regressions in existing tests"
    measurable: true
  - criterion: "Code coverage >= 80%"
    measurable: true

security_considerations:
  - consideration: "Input validation required"
    mitigation: "Validate all inputs before processing"

performance_requirements:
  - requirement: "Response time < 200ms"
    applies_to: "API endpoints"
```
"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._spec_counter = 0

    def get_system_prompt(self, context: StageContext) -> str:
        """Get spec generation system prompt."""
        return self.SYSTEM_PROMPT

    def get_user_message(self, context: StageContext) -> str:
        """Build user message for spec generation."""
        artifact = context.input_artifacts
        analysis = artifact.get("analysis", {})

        # Generate spec ID
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        self._spec_counter += 1
        spec_id = f"SPEC-{timestamp}-{self._spec_counter:04d}"

        # Format affected files
        affected_files = artifact.get("affected_files", [])
        files_str = (
            "\n".join(
                [
                    f"  - {f.get('path', 'unknown')} ({f.get('change_type', 'modify')}): {f.get('reason', '')}"
                    for f in affected_files
                ]
            )
            or "  (none identified)"
        )

        # Format components
        components = artifact.get("components", [])
        components_str = (
            "\n".join(
                [
                    f"  - {c.get('name', 'unknown')} ({c.get('type', 'unknown')}): {c.get('description', '')}"
                    for c in components
                ]
            )
            or "  (none identified)"
        )

        # Format risks
        risks = artifact.get("risks", [])
        risks_str = (
            "\n".join(
                [
                    f"  - [{r.get('severity', 'medium')}] {r.get('description', '')}"
                    for r in risks
                ]
            )
            or "  (none identified)"
        )

        return self.USER_MESSAGE_TEMPLATE.format(
            requirements=artifact.get("clarified_requirements", ""),
            analysis_summary=analysis.get("summary", "No analysis summary"),
            complexity=analysis.get("complexity", "medium"),
            effort=analysis.get("estimated_effort", "unknown"),
            affected_files=files_str,
            components=components_str,
            risks=risks_str,
            spec_id=spec_id,
            request_id=artifact.get("request_id", "REQ-UNKNOWN"),
            timestamp=datetime.now(UTC).isoformat(),
        )

    def parse_response(
        self,
        llm_result: dict[str, Any],
        context: StageContext,
    ) -> dict[str, Any] | None:
        """Parse specification from LLM response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")

        spec = self.extract_yaml_from_response(response_text)

        if spec is None:
            logger.error("Failed to extract YAML specification")
            return None

        # Ensure required fields
        if "spec_id" not in spec:
            timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            spec["spec_id"] = f"SPEC-{timestamp}"

        spec.setdefault("request_id", context.input_artifacts.get("request_id"))
        spec.setdefault("components", [])
        spec.setdefault("test_cases", [])
        spec.setdefault("interfaces", [])
        spec.setdefault("acceptance_criteria", [])

        return spec

    def validate_output(self, artifact: dict[str, Any] | None) -> OutputValidation:
        """Validate specification artifact."""
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])

        errors: list[str] = []
        warnings: list[str] = []

        self._validate_required_fields(artifact, errors)
        self._validate_components(artifact.get("components", []), errors, warnings)
        self._validate_test_cases(artifact.get("test_cases", []), warnings)

        if not artifact.get("acceptance_criteria"):
            warnings.append("No acceptance criteria defined")

        return OutputValidation(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_required_fields(
        self, artifact: dict[str, Any], errors: list[str]
    ) -> None:
        """Validate required top-level fields."""
        if not artifact.get("spec_id"):
            errors.append("Missing spec_id")

    def _validate_components(
        self, components: list[dict], errors: list[str], warnings: list[str]
    ) -> None:
        """Validate components have required fields."""
        if not components:
            errors.append("Specification must define at least one component")
            return

        for i, comp in enumerate(components):
            if not comp.get("name"):
                errors.append(f"Component {i} missing name")
            if not comp.get("file_path") and not comp.get("files"):
                warnings.append(f"Component {comp.get('name', i)} has no file path")

    def _validate_test_cases(self, test_cases: list[dict], warnings: list[str]) -> None:
        """Validate test cases have required fields."""
        if not test_cases:
            warnings.append("No test cases defined")
            return

        for i, tc in enumerate(test_cases):
            if not tc.get("id"):
                warnings.append(f"Test case {i} missing id")
            if not tc.get("description"):
                warnings.append(f"Test case {tc.get('id', i)} missing description")

    def finalize(self, context: StageContext, result: StageResult) -> None:
        """Save spec to standard location."""
        # Save to .agentforge/specs/ for easy access
        if result.is_success() and result.artifacts:
            try:
                specs_dir = context.project_path / ".agentforge" / "specs"
                specs_dir.mkdir(parents=True, exist_ok=True)

                spec_id = result.artifacts.get("spec_id", "unknown")
                spec_file = specs_dir / f"{spec_id}.yaml"

                with open(spec_file, "w") as f:
                    yaml.dump(
                        result.artifacts, f, default_flow_style=False, sort_keys=False
                    )

                logger.info(f"Saved specification to {spec_file}")
            except Exception as e:
                logger.warning(f"Failed to save spec to specs directory: {e}")

    def get_required_inputs(self) -> list:
        """Get required inputs for spec stage."""
        return self.required_input_fields


def create_spec_executor(config: dict | None = None) -> SpecExecutor:
    """Create SpecExecutor instance."""
    return SpecExecutor(config)
