# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_id: pipeline-controller-phase2-v1
# @component_id: intake-executor
# @test_path: tests/unit/pipeline/stages/test_intake.py

"""
Intake Stage Executor
=====================

INTAKE is the first stage of the pipeline. It parses the user's request
and produces an IntakeRecord with:
- Detected scope (bug_fix, feature_addition, refactoring, etc.)
- Priority assessment
- Initial clarifying questions
- Detected components/keywords
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..llm_stage_executor import LLMStageExecutor, OutputValidation
from ..stage_executor import StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class IntakeExecutor(LLMStageExecutor):
    """
    INTAKE stage executor.

    Parses user request and produces an IntakeRecord with:
    - Detected scope (bug_fix, feature_addition, refactoring, etc.)
    - Priority assessment
    - Initial questions for clarification
    - Detected components/areas of codebase
    """

    stage_name = "intake"
    artifact_type = "intake_record"

    # No required input fields - this is the first stage
    required_input_fields: list = []

    # Fields we produce
    output_fields = [
        "request_id",
        "detected_scope",
        "priority",
    ]

    # Valid values for validation
    VALID_SCOPES = [
        "bug_fix",
        "feature_addition",
        "refactoring",
        "documentation",
        "testing",
        "unclear",
    ]
    VALID_PRIORITIES = ["low", "medium", "high", "critical"]

    # System prompt for intake analysis
    SYSTEM_PROMPT = """You are an expert software requirements analyst. Your task is to analyze a user's development request and produce a structured intake record.

You must:
1. Identify the TYPE of request (bug_fix, feature_addition, refactoring, documentation, testing, unclear)
2. Assess PRIORITY based on keywords and context (low, medium, high, critical)
3. Generate CLARIFYING QUESTIONS for any ambiguities
4. Identify likely AFFECTED COMPONENTS based on the request

Output your analysis as YAML in a code block.

IMPORTANT:
- Questions should be specific and actionable
- Mark questions as "blocking" if the answer is required before proceeding
- Mark questions as "optional" if they can be answered later
- Be conservative with scope detection - prefer "unclear" if genuinely ambiguous
"""

    USER_MESSAGE_TEMPLATE = """Analyze this development request:

REQUEST:
{request}

{context_section}

Produce an intake record with the following structure:

```yaml
request_id: "{request_id}"
original_request: "{request}"
detected_scope: "feature_addition"  # or bug_fix, refactoring, documentation, testing, unclear
priority: "medium"  # low, medium, high, critical
confidence: 0.85  # 0.0-1.0 confidence in scope detection

initial_questions:
  - question: "What specific feature should be added?"
    priority: "blocking"  # or "optional"
    context: "Need to understand the scope"
  - question: "..."
    priority: "optional"

detected_components:
  - name: "component_name"
    confidence: 0.9
  - name: "another_component"
    confidence: 0.7

keywords:
  - "keyword1"
  - "keyword2"

estimated_complexity: "medium"  # low, medium, high
```
"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._request_counter = 0

    def get_system_prompt(self, context: StageContext) -> str:
        """Get system prompt for intake."""
        return self.SYSTEM_PROMPT

    def get_user_message(self, context: StageContext) -> str:
        """Build user message from context."""
        # Generate request ID
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self._request_counter += 1
        request_id = f"REQ-{timestamp}-{self._request_counter:04d}"

        # Build context section
        context_section = ""
        if context.input_artifacts.get("project_context"):
            context_section = (
                f"\nPROJECT CONTEXT:\n{context.input_artifacts['project_context']}"
            )

        return self.USER_MESSAGE_TEMPLATE.format(
            request=context.request,
            request_id=request_id,
            context_section=context_section,
        )

    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Parse LLM response into IntakeRecord."""
        # Get text response
        response_text = llm_result.get("response", "")
        if not response_text:
            response_text = llm_result.get("content", "")

        # Extract YAML
        artifact = self.extract_yaml_from_response(response_text)

        if artifact is None:
            logger.error("Failed to extract YAML from intake response")
            return None

        # Validate required fields
        required = ["request_id", "detected_scope"]
        for field_name in required:
            if field_name not in artifact:
                logger.error(f"Missing required field in intake: {field_name}")
                return None

        # Ensure lists exist
        artifact.setdefault("initial_questions", [])
        artifact.setdefault("detected_components", [])
        artifact.setdefault("keywords", [])

        # Add original request if not present
        if "original_request" not in artifact:
            artifact["original_request"] = context.request

        # Default priority
        if "priority" not in artifact:
            artifact["priority"] = "medium"

        return artifact

    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> OutputValidation:
        """Validate intake artifact."""
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])

        errors = []
        warnings = []

        # Required fields
        if not artifact.get("request_id"):
            errors.append("Missing request_id")
        if not artifact.get("detected_scope"):
            errors.append("Missing detected_scope")

        # Validate scope value
        if artifact.get("detected_scope") not in self.VALID_SCOPES:
            errors.append(f"Invalid scope: {artifact.get('detected_scope')}")

        # Validate priority
        if artifact.get("priority") not in self.VALID_PRIORITIES:
            warnings.append("Invalid priority, defaulting to medium")

        # Warn if no questions for unclear scope
        if artifact.get("detected_scope") == "unclear":
            if not artifact.get("initial_questions"):
                warnings.append("Unclear scope but no clarifying questions")

        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def get_required_inputs(self) -> list:
        """No required inputs for intake - it's the first stage."""
        return []


def create_intake_executor(config: Optional[Dict] = None) -> IntakeExecutor:
    """Create IntakeExecutor instance."""
    return IntakeExecutor(config)
