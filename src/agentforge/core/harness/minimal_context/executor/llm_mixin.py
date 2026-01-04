"""
LLM Interaction Mixin
=====================

LLM calling and response parsing for the executor.
"""

import asyncio
import inspect
import re
from typing import TYPE_CHECKING, Any

import yaml

from ..context_models import AgentResponse

if TYPE_CHECKING:
    from agentforge.core.generate.provider import LLMProvider


class LLMMixin:
    """
    Mixin for LLM interaction in executor.

    Handles LLM calls, message formatting, and response parsing.
    """

    # Type hints for attributes from main class
    provider: "LLMProvider"
    max_tokens: int

    def _call_llm(self, messages: list[dict[str, str]]) -> tuple:
        """Call the LLM provider."""
        prompt = self._messages_to_prompt(messages)

        result = self.provider.generate(prompt, self.max_tokens)

        if inspect.iscoroutine(result):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, result)
                    response = future.result()
            else:
                response = asyncio.run(result)
        else:
            response = result

        if isinstance(response, tuple) and len(response) == 2:
            response_text, token_usage = response
            if hasattr(token_usage, 'prompt_tokens') and hasattr(token_usage, 'completion_tokens'):
                tokens_used = token_usage.prompt_tokens + token_usage.completion_tokens
            else:
                tokens_used = self.provider.count_tokens(prompt) + self.provider.count_tokens(response_text)
        else:
            response_text = response
            tokens_used = self.provider.count_tokens(prompt) + self.provider.count_tokens(response_text)

        return response_text, tokens_used

    def _messages_to_prompt(self, messages: list[dict[str, str]]) -> str:
        """Convert messages to single prompt string."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"<system>\n{content}\n</system>\n")
            elif role == "user":
                parts.append(f"<user>\n{content}\n</user>\n")
        return "\n".join(parts)

    def _parse_action(self, response_text: str) -> tuple:
        """Parse and validate action from LLM response."""
        # Look for action block
        action_match = re.search(
            r"```action\s*\n(.*?)```",
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if action_match:
            action_yaml = action_match.group(1).strip()
            result = self._parse_and_validate_yaml(action_yaml, "action")
            if result:
                return result

        # Look for yaml block
        yaml_match = re.search(
            r"```yaml\s*\n(.*?)```",
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if yaml_match:
            yaml_content = yaml_match.group(1).strip()
            result = self._parse_and_validate_yaml(yaml_content, "yaml")
            if result:
                return result

        # Fallback: look for simple action pattern
        simple_match = re.search(r"action:\s*(\w+)", response_text)
        if simple_match:
            return simple_match.group(1), {}

        simple_match = re.search(r"name:\s*(\w+)", response_text)
        if simple_match:
            return simple_match.group(1), {}

        if "complete" in response_text.lower():
            return "complete", {}

        return "unknown", {}

    def _parse_and_validate_yaml(
        self,
        yaml_content: str,
        block_type: str,
    ) -> tuple | None:
        """Parse YAML content and validate against AgentResponse schema."""
        try:
            action_data = yaml.safe_load(yaml_content)
            if not isinstance(action_data, dict):
                return None

            name = action_data.get("name") or action_data.get("action")
            if not name:
                return None

            params = action_data.get("parameters", {}) or {}
            reasoning = action_data.get("reasoning")

            try:
                validated = AgentResponse(
                    action=name,
                    parameters=params,
                    reasoning=reasoning,
                )
                return validated.action, validated.parameters
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Response validation failed: {e}. "
                    f"Action: {name}, Parameters: {params}"
                )
                return name, params

        except yaml.YAMLError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"YAML parsing failed: {e}")
            return None

    def _validate_path_parameter(self, parameters: dict[str, Any]) -> str | None:
        """Validate path/file_path parameter if present. Returns error or None."""
        path = parameters.get("path") or parameters.get("file_path")
        if path and not isinstance(path, str):
            return "Path parameter must be a string"
        return None

    def _validate_content_parameter(self, parameters: dict[str, Any]) -> str | None:
        """Validate content parameter if present. Returns error or None."""
        content = parameters.get("content")
        if content is not None and not isinstance(content, str):
            return "Content parameter must be a string"
        return None

    def _validate_response_parameters(
        self,
        action_name: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Validate response parameters at runtime.

        Ensures action parameters are well-formed before execution.
        This method is required by the minimal-context-validation contract.

        Args:
            action_name: The action being executed
            parameters: The parameters for the action

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(action_name, str) or not action_name:
            return False, "Action name must be a non-empty string"

        if not isinstance(parameters, dict):
            return False, "Parameters must be a dictionary"

        # Run parameter validators
        validators = [self._validate_path_parameter, self._validate_content_parameter]
        for validator in validators:
            error = validator(parameters)
            if error:
                return False, error

        return True, None
