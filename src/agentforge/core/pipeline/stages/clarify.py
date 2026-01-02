# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_id: pipeline-controller-phase2-v1
# @component_id: clarify-executor
# @test_path: tests/unit/pipeline/stages/test_clarify.py

"""
Clarify Stage Executor
======================

CLARIFY is the second stage of the pipeline. It resolves ambiguities
in the user's request by:
- Iteratively resolving blocking questions
- Incorporating answers into refined requirements
- Escalating when human input is needed
- Producing ClarifiedRequirements for the next stage
"""

import logging
from typing import Any, Dict, List, Optional

from ..llm_stage_executor import LLMStageExecutor, OutputValidation
from ..stage_executor import StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class ClarifyExecutor(LLMStageExecutor):
    """
    CLARIFY stage executor.

    Iteratively resolves questions from INTAKE stage through:
    - Asking blocking questions
    - Incorporating answers
    - Producing refined requirements

    This stage may escalate to request human answers.
    """

    stage_name = "clarify"
    artifact_type = "clarified_requirements"

    required_input_fields = ["request_id", "detected_scope"]

    output_fields = [
        "request_id",
        "clarified_requirements",
        "scope_confirmed",
    ]

    SYSTEM_PROMPT = """You are a software requirements analyst refining a development request.

You have access to:
1. The original request
2. Initial analysis from intake
3. Any answers provided to clarifying questions

Your task is to:
1. Incorporate any answers into a refined understanding
2. Identify if there are remaining BLOCKING questions
3. Produce a clear, unambiguous requirements statement

If blocking questions remain unanswered, you should indicate this - do NOT make assumptions.

Output your analysis as YAML in a code block.
"""

    USER_MESSAGE_TEMPLATE = """Refine these requirements based on the information gathered:

ORIGINAL REQUEST:
{original_request}

INTAKE ANALYSIS:
- Scope: {scope}
- Priority: {priority}
- Initial Questions: {questions}

{answers_section}

{feedback_section}

Produce clarified requirements:

```yaml
request_id: "{request_id}"
clarified_requirements: |
  Clear, unambiguous description of what needs to be done.
  Include all relevant details from the answers.

scope_confirmed: true  # or false if still unclear

answered_questions:
  - question: "What specific feature?"
    answer: "The provided answer"
    incorporated: true

remaining_questions:
  - question: "Still unanswered?"
    priority: "blocking"
    reason: "Required for implementation"

refined_scope: "feature_addition"  # May change from initial detection
refined_components:
  - name: "component_name"
    files_likely_affected:
      - "src/path/to/file.py"

ready_for_analysis: true  # false if blocking questions remain
```
"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_clarification_rounds = config.get("max_rounds", 3) if config else 3

    def execute(self, context: StageContext) -> StageResult:
        """Execute clarify stage with potential iteration."""
        input_artifact = context.input_artifacts

        # Check if there are blocking questions
        initial_questions = input_artifact.get("initial_questions", [])
        blocking_questions = [
            q for q in initial_questions if q.get("priority") == "blocking"
        ]

        # If no blocking questions, we can skip clarification
        if not blocking_questions:
            logger.info("No blocking questions, skipping clarification")
            return StageResult(
                status=StageStatus.COMPLETED,
                artifacts=self._create_passthrough_artifact(context),
            )

        # Check if we have answers (from feedback or context)
        answers = input_artifact.get("question_answers", {})
        feedback = context.config.get("previous_feedback")

        # If we have blocking questions but no answers, escalate
        if blocking_questions and not answers and not feedback:
            return self._escalate_for_answers(context, blocking_questions)

        # Run LLM clarification with available information
        return super().execute(context)

    def get_system_prompt(self, context: StageContext) -> str:
        """Get system prompt for clarify."""
        return self.SYSTEM_PROMPT

    def get_user_message(self, context: StageContext) -> str:
        """Build user message with intake data and answers."""
        artifact = context.input_artifacts

        # Format questions
        questions = artifact.get("initial_questions", [])
        questions_str = (
            "\n".join(
                [
                    f"  - [{q.get('priority', 'optional')}] {q.get('question', 'N/A')}"
                    for q in questions
                ]
            )
            or "  (none)"
        )

        # Format answers section
        answers = artifact.get("question_answers", {})
        answers_section = ""
        if answers:
            answers_lines = [f"  - Q: {q}\n    A: {a}" for q, a in answers.items()]
            answers_section = "ANSWERS PROVIDED:\n" + "\n".join(answers_lines)

        # Format feedback section
        feedback_section = ""
        if context.config.get("previous_feedback"):
            feedback_section = (
                f"ADDITIONAL CONTEXT FROM USER:\n{context.config['previous_feedback']}"
            )

        return self.USER_MESSAGE_TEMPLATE.format(
            original_request=artifact.get("original_request", context.request),
            scope=artifact.get("detected_scope", "unknown"),
            priority=artifact.get("priority", "medium"),
            questions=questions_str,
            answers_section=answers_section,
            feedback_section=feedback_section,
            request_id=artifact.get("request_id", "REQ-UNKNOWN"),
        )

    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Parse clarification response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")

        artifact = self.extract_yaml_from_response(response_text)

        if artifact is None:
            logger.error("Failed to extract YAML from clarify response")
            return None

        # Carry forward request_id
        if "request_id" not in artifact:
            artifact["request_id"] = context.input_artifacts.get("request_id")

        # Ensure required fields
        artifact.setdefault("clarified_requirements", "")
        artifact.setdefault("scope_confirmed", False)
        artifact.setdefault("answered_questions", [])
        artifact.setdefault("remaining_questions", [])
        artifact.setdefault("ready_for_analysis", False)

        return artifact

    def _create_passthrough_artifact(self, context: StageContext) -> Dict[str, Any]:
        """Create artifact when no clarification needed."""
        input_artifact = context.input_artifacts

        return {
            "request_id": input_artifact.get("request_id"),
            "clarified_requirements": input_artifact.get("original_request"),
            "scope_confirmed": True,
            "answered_questions": [],
            "remaining_questions": [],
            "refined_scope": input_artifact.get("detected_scope"),
            "refined_components": input_artifact.get("detected_components", []),
            "ready_for_analysis": True,
            # Carry forward
            "original_request": input_artifact.get("original_request"),
            "priority": input_artifact.get("priority"),
            "keywords": input_artifact.get("keywords", []),
        }

    def _escalate_for_answers(
        self,
        context: StageContext,
        blocking_questions: List[Dict],
    ) -> StageResult:
        """Escalate to get answers to blocking questions."""
        questions_text = "\n".join(
            [
                f"  - {q.get('question', 'N/A')} (context: {q.get('context', 'N/A')})"
                for q in blocking_questions
            ]
        )

        return StageResult.escalate(
            escalation_type="clarification_needed",
            message=f"Blocking questions require answers:\n{questions_text}",
            context={
                "request_id": context.input_artifacts.get("request_id"),
                "blocking_questions": blocking_questions,
                "status": "awaiting_answers",
            },
        )

    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> OutputValidation:
        """Validate clarify artifact."""
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])

        errors = []
        warnings = []

        # Must have clarified requirements
        if not artifact.get("clarified_requirements"):
            errors.append("Missing clarified_requirements")

        # Check for remaining blocking questions
        remaining = artifact.get("remaining_questions", [])
        blocking_remaining = [q for q in remaining if q.get("priority") == "blocking"]

        if blocking_remaining and artifact.get("ready_for_analysis"):
            warnings.append("Marked ready but blocking questions remain")

        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def get_required_inputs(self) -> list:
        """Get required inputs for clarify stage."""
        return self.required_input_fields


def create_clarify_executor(config: Optional[Dict] = None) -> ClarifyExecutor:
    """Create ClarifyExecutor instance."""
    return ClarifyExecutor(config)
