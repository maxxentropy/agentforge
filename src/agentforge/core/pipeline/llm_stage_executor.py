# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_id: pipeline-controller-phase2-v1
# @component_id: llm-stage-executor
# @test_path: tests/unit/pipeline/test_llm_stage_executor.py

"""
LLM Stage Executor
==================

Base classes for LLM-driven pipeline stages.

LLMStageExecutor provides common patterns for:
- System prompt templating
- User message construction
- Response parsing (YAML/JSON extraction)
- Integration with MinimalContextExecutor

ToolBasedStageExecutor extends this for stages that use
tool calls to produce their artifacts.
"""

import json
import logging
import re
from abc import abstractmethod
from typing import Any, Dict, List, Optional

import yaml

from .stage_executor import StageContext, StageExecutor, StageResult, StageStatus

logger = logging.getLogger(__name__)


class LLMStageExecutor(StageExecutor):
    """
    Base class for stages that use LLM for execution.

    Provides common patterns for LLM-based stages:
    - System prompt templating
    - Response parsing (YAML/JSON extraction)
    - Retry with feedback

    Subclasses implement:
    - get_system_prompt(): System prompt for LLM
    - get_user_message(): User message construction
    - parse_response(): Extract artifact from LLM response
    """

    # LLM configuration - override in subclasses
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8000
    temperature: float = 0.7

    # Tools to provide - override in subclasses
    tools: List[Dict[str, Any]] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM stage executor.

        Args:
            config: Stage-specific configuration
        """
        self.config = config or {}
        self._executor = None  # MinimalContextExecutor, lazily created

    def execute(self, context: StageContext) -> StageResult:
        """
        Execute the stage using LLM.

        Calls lifecycle methods in order:
        1. get_system_prompt()
        2. get_user_message()
        3. _run_with_llm()
        4. parse_response()

        Args:
            context: Stage execution context

        Returns:
            StageResult with artifact or error
        """
        try:
            # Build prompts
            system_prompt = self.get_system_prompt(context)
            user_message = self.get_user_message(context)

            # Execute with LLM
            llm_result = self._run_with_llm(
                context=context,
                system_prompt=system_prompt,
                user_message=user_message,
                tools=self.tools if self.tools else None,
            )

            # Parse response
            artifact = self.parse_response(llm_result, context)

            if artifact is None:
                return StageResult(
                    status=StageStatus.FAILED,
                    error="Failed to parse LLM response into artifact",
                )

            return StageResult(
                status=StageStatus.COMPLETED,
                artifacts=artifact,
            )

        except Exception as e:
            logger.exception(f"Stage {self.stage_name} failed: {e}")
            return StageResult(
                status=StageStatus.FAILED,
                error=f"LLM execution failed: {e}",
            )

    @abstractmethod
    def get_system_prompt(self, context: StageContext) -> str:
        """
        Get system prompt for this stage.

        Override to provide stage-specific system prompt.
        Can use context to include relevant information.

        Args:
            context: Stage execution context

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def get_user_message(self, context: StageContext) -> str:
        """
        Get user message for this stage.

        Override to construct the user message from context.

        Args:
            context: Stage execution context

        Returns:
            User message string
        """
        pass

    @abstractmethod
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response into stage artifact.

        Override to extract structured artifact from LLM output.
        Return None if parsing fails.

        Args:
            llm_result: Raw LLM response
            context: Stage execution context

        Returns:
            Parsed artifact dict or None if parsing fails
        """
        pass

    def _run_with_llm(
        self,
        context: StageContext,
        system_prompt: str,
        user_message: str,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Execute LLM-based stage logic.

        Convenience method for stages that delegate to LLM.

        Args:
            context: Stage context
            system_prompt: System prompt for LLM
            user_message: User message
            tools: Optional tool definitions

        Returns:
            LLM response dict
        """
        # For now, return a mock response - actual LLM integration
        # will be done when MinimalContextExecutor is wired up
        # This allows tests to mock this method
        logger.info(f"Running LLM for stage {context.stage_name}")

        # Try to get actual executor if available
        try:
            executor = self._get_executor(context)

            task_context = {
                "pipeline_id": context.pipeline_id,
                "stage_name": context.stage_name,
                "input_artifacts": context.input_artifacts,
                "user_request": context.request,
            }

            if context.config.get("previous_feedback"):
                task_context["feedback"] = context.config["previous_feedback"]

            result = executor.execute_task(
                task_description=user_message,
                system_prompt=system_prompt,
                context=task_context,
                tools=tools,
                max_iterations=10,
            )

            return result

        except ImportError:
            # MinimalContextExecutor not available - return mock
            logger.warning("MinimalContextExecutor not available, using mock")
            return {"response": "", "content": "", "tool_results": []}

    def _get_executor(self, context: StageContext):
        """Get or create MinimalContextExecutor for this stage."""
        if self._executor is None:
            from agentforge.core.harness.minimal_context import MinimalContextExecutor

            self._executor = MinimalContextExecutor(
                project_path=context.project_path,
                task_type=f"stage_{self.stage_name}",
            )
        return self._executor

    # --- Utility Methods ---

    def extract_yaml_from_response(self, response_text: str) -> Optional[Dict]:
        """
        Extract YAML block from LLM response.

        Handles both code-fenced YAML and raw YAML.

        Args:
            response_text: LLM response text

        Returns:
            Parsed YAML dict or None if parsing fails
        """
        # Try to find YAML code block
        yaml_match = re.search(
            r"```ya?ml\s*\n(.*?)\n```",
            response_text,
            re.DOTALL | re.IGNORECASE,
        )

        if yaml_match:
            try:
                return yaml.safe_load(yaml_match.group(1))
            except yaml.YAMLError as e:
                logger.debug(f"Failed to parse YAML from code block: {e}")

        # Try to parse entire response as YAML
        try:
            return yaml.safe_load(response_text)
        except yaml.YAMLError:
            pass

        return None

    def extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """
        Extract JSON from LLM response.

        Handles both code-fenced JSON and embedded JSON objects.

        Args:
            response_text: LLM response text

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        # Try to find JSON code block
        json_match = re.search(
            r"```json\s*\n(.*?)\n```",
            response_text,
            re.DOTALL | re.IGNORECASE,
        )

        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def validate_input(self, artifacts: Dict[str, Any]) -> List[str]:
        """Validate input artifacts."""
        errors = []
        for required in self.get_required_inputs():
            if required not in artifacts:
                errors.append(f"Missing required artifact: {required}")
        return errors

    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """
        Validate output artifact.

        Override in subclasses for custom validation.

        Args:
            artifact: Output artifact to validate

        Returns:
            OutputValidation result
        """
        from .stage_executor import StageResult

        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact produced"])

        return OutputValidation(valid=True, errors=[], warnings=[])


class ToolBasedStageExecutor(LLMStageExecutor):
    """
    Stage executor that relies on tool use for output.

    Instead of parsing LLM text, this expects the LLM to use
    a specific tool to produce the artifact.
    """

    # Tool that produces the artifact - override in subclasses
    artifact_tool_name: str = "complete"

    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract artifact from tool use result.

        Looks for the configured artifact_tool_name in tool_results.

        Args:
            llm_result: LLM response with tool results
            context: Stage execution context

        Returns:
            Extracted artifact or None
        """
        # Check if the expected tool was called
        tool_results = llm_result.get("tool_results", [])

        for tool_result in tool_results:
            if tool_result.get("tool_name") == self.artifact_tool_name:
                return tool_result.get("input", {})

        # Fall back to final_artifact if present
        if llm_result.get("final_artifact"):
            return llm_result["final_artifact"]

        return None


# Validation result dataclass (defined here to avoid circular import)
from dataclasses import dataclass, field


@dataclass
class OutputValidation:
    """Result of output validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
