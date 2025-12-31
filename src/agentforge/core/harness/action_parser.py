"""
Action Parser
=============

Parses LLM responses to extract agent actions.
Handles XML-structured responses from the agent prompt format.
"""

import re
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from agentforge.core.harness.llm_executor_domain import (
    ActionType,
    AgentAction,
    ToolCall,
    ActionParseError,
)


class ActionParser:
    """Parses LLM responses into AgentAction objects."""

    # Regex patterns for extracting XML sections
    THINKING_PATTERN = re.compile(
        r"<thinking>\s*(.*?)\s*</thinking>",
        re.DOTALL | re.IGNORECASE
    )
    ACTION_PATTERN = re.compile(
        r'<action\s+type=["\']([^"\']+)["\']\s*>(.*?)</action>',
        re.DOTALL | re.IGNORECASE
    )
    TOOL_PATTERN = re.compile(
        r'<tool\s+name=["\']([^"\']+)["\']\s*>(.*?)</tool>',
        re.DOTALL | re.IGNORECASE
    )
    PARAMETER_PATTERN = re.compile(
        r'<parameter\s+name=["\']([^"\']+)["\']\s*>(.*?)</parameter>',
        re.DOTALL | re.IGNORECASE
    )

    def parse(self, response: str) -> AgentAction:
        """Parse LLM response into an AgentAction.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed AgentAction

        Raises:
            ActionParseError: If response cannot be parsed
        """
        if not response or not response.strip():
            raise ActionParseError("Empty response", raw_response=response)

        # Extract thinking section
        reasoning = self._extract_thinking(response)

        # Extract action section
        action_type, action_content = self._extract_action(response)

        # Parse based on action type
        if action_type == ActionType.TOOL_CALL:
            tool_calls = self._parse_tool_calls(action_content)
            return AgentAction.tool_action(tool_calls, reasoning)

        elif action_type == ActionType.COMPLETE:
            summary = self._extract_element(action_content, "summary")
            return AgentAction.complete_action(summary or action_content.strip(), reasoning)

        elif action_type == ActionType.ASK_USER:
            question = self._extract_element(action_content, "question")
            return AgentAction(
                action_type=ActionType.ASK_USER,
                reasoning=reasoning,
                response=question or action_content.strip(),
            )

        elif action_type == ActionType.ESCALATE:
            reason = self._extract_element(action_content, "reason")
            return AgentAction.escalate_action(reason or action_content.strip())

        elif action_type == ActionType.THINK:
            return AgentAction.think_action(reasoning or action_content.strip())

        elif action_type == ActionType.RESPOND:
            return AgentAction.respond_action(action_content.strip(), reasoning)

        else:
            raise ActionParseError(
                f"Unknown action type: {action_type}",
                raw_response=response
            )

    def _extract_thinking(self, response: str) -> str:
        """Extract thinking section from response."""
        match = self.THINKING_PATTERN.search(response)
        return match.group(1).strip() if match else ""

    def _extract_action(self, response: str) -> Tuple[ActionType, str]:
        """Extract action type and content from response.

        Returns:
            Tuple of (ActionType, action_content)

        Raises:
            ActionParseError: If no valid action found
        """
        match = self.ACTION_PATTERN.search(response)
        if not match:
            # Try to infer action from response structure
            return self._infer_action(response)

        action_type_str = match.group(1).lower()
        action_content = match.group(2).strip()

        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            raise ActionParseError(
                f"Invalid action type: {action_type_str}",
                raw_response=response
            )

        return action_type, action_content

    def _infer_action(self, response: str) -> Tuple[ActionType, str]:
        """Attempt to infer action when XML structure is missing.

        This handles cases where the LLM doesn't follow the exact format.
        """
        # Check for tool call patterns without proper XML
        if self.TOOL_PATTERN.search(response):
            return ActionType.TOOL_CALL, response

        # Check for common completion phrases
        completion_phrases = [
            "task complete",
            "task is complete",
            "completed the task",
            "successfully completed",
            "finished the task",
        ]
        response_lower = response.lower()
        for phrase in completion_phrases:
            if phrase in response_lower:
                return ActionType.COMPLETE, response

        # Check for question indicators
        if response.strip().endswith("?"):
            return ActionType.ASK_USER, response

        # Default to thinking if we have thinking content
        if self.THINKING_PATTERN.search(response):
            return ActionType.THINK, response

        # If nothing matches, treat as a response
        raise ActionParseError(
            "Could not determine action type from response",
            raw_response=response
        )

    def _parse_tool_calls(self, content: str) -> List[ToolCall]:
        """Parse tool calls from action content.

        Args:
            content: Content inside <action type="tool_call">

        Returns:
            List of ToolCall objects
        """
        tool_calls = []

        for match in self.TOOL_PATTERN.finditer(content):
            tool_name = match.group(1)
            tool_content = match.group(2)

            parameters = self._parse_parameters(tool_content)
            tool_calls.append(ToolCall(name=tool_name, parameters=parameters))

        if not tool_calls:
            raise ActionParseError(
                "tool_call action has no tools defined",
                raw_response=content
            )

        return tool_calls

    def _parse_parameters(self, content: str) -> Dict[str, str]:
        """Parse parameters from tool content."""
        parameters = {}

        for match in self.PARAMETER_PATTERN.finditer(content):
            param_name = match.group(1)
            param_value = match.group(2).strip()
            parameters[param_name] = param_value

        return parameters

    def _extract_element(self, content: str, element_name: str) -> Optional[str]:
        """Extract content from a simple XML element.

        Args:
            content: XML content to search
            element_name: Name of element to extract

        Returns:
            Element content or None if not found
        """
        pattern = re.compile(
            rf"<{element_name}>\s*(.*?)\s*</{element_name}>",
            re.DOTALL | re.IGNORECASE
        )
        match = pattern.search(content)
        return match.group(1).strip() if match else None

    def parse_lenient(self, response: str) -> AgentAction:
        """Parse response with more lenient handling of malformed XML.

        Falls back to heuristic parsing if strict parsing fails.

        Args:
            response: Raw LLM response

        Returns:
            Best-effort AgentAction
        """
        try:
            return self.parse(response)
        except ActionParseError:
            # Attempt lenient parsing
            reasoning = self._extract_thinking(response) or ""

            # Look for any tool-like patterns
            if "<tool" in response.lower():
                try:
                    tool_calls = self._parse_tool_calls(response)
                    return AgentAction.tool_action(tool_calls, reasoning)
                except ActionParseError:
                    pass

            # If response looks like completion
            if any(word in response.lower() for word in ["done", "complete", "finished"]):
                return AgentAction.complete_action(response.strip(), reasoning)

            # Default to thinking/reasoning response
            return AgentAction.think_action(reasoning or response.strip())
