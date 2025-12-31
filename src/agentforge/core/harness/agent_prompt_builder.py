"""
Agent Prompt Builder
====================

Builds prompts for the agent LLM to decide on actions.
Uses XML-structured prompts for clear parsing.
"""

from typing import List, Optional
import yaml

from agentforge.core.harness.llm_executor_domain import (
    ExecutionContext,
    ConversationMessage,
    ToolResult,
)


SYSTEM_PROMPT = """You are an autonomous software engineering agent. Your role is to complete tasks by using available tools.

## Response Format

You MUST respond in the following XML format:

<thinking>
[Your step-by-step reasoning about what to do next]
</thinking>

<action type="[action_type]">
[Action content - see below for each type]
</action>

## Action Types

### tool_call
Execute one or more tools:
<action type="tool_call">
<tool name="tool_name">
<parameter name="param1">value1</parameter>
<parameter name="param2">value2</parameter>
</tool>
</action>

### complete
Mark the task as complete:
<action type="complete">
<summary>Brief summary of what was accomplished</summary>
</action>

### ask_user
Ask the user for clarification:
<action type="ask_user">
<question>Your question to the user</question>
</action>

### escalate
Escalate to human when stuck:
<action type="escalate">
<reason>Why you need human intervention</reason>
</action>

## Guidelines

1. Think step-by-step before acting
2. Use tools to gather information before making changes
3. Prefer reading files before editing them
4. Test changes when possible
5. If stuck after 3 attempts, consider escalating
6. Complete the task when the original request is satisfied

## Important Rules

- Always include <thinking> section with your reasoning
- Only use tools from the available tools list
- Be precise with file paths and code
- Report errors clearly
"""


class AgentPromptBuilder:
    """Builds prompts for agent execution."""

    def __init__(self, system_prompt: Optional[str] = None):
        """Initialize prompt builder.

        Args:
            system_prompt: Custom system prompt (uses default if not provided)
        """
        self.system_prompt = system_prompt or SYSTEM_PROMPT

    def build_system_prompt(self, context: ExecutionContext) -> str:
        """Build the system prompt with available tools.

        Args:
            context: Execution context

        Returns:
            Complete system prompt
        """
        tools_section = self._build_tools_section(context.available_tools)

        return f"{self.system_prompt}\n\n{tools_section}"

    def build_user_prompt(self, context: ExecutionContext) -> str:
        """Build the user prompt with task and history.

        Args:
            context: Execution context

        Returns:
            User prompt string
        """
        sections = []

        # Task section
        sections.append(self._build_task_section(context))

        # Memory context if available
        if context.memory_context:
            sections.append(self._build_memory_section(context.memory_context))

        # Conversation history
        if context.conversation_history:
            sections.append(self._build_history_section(context.recent_messages))

        # Status section
        sections.append(self._build_status_section(context))

        return "\n\n".join(sections)

    def build_messages(self, context: ExecutionContext) -> List[dict]:
        """Build complete message list for LLM API.

        Args:
            context: Execution context

        Returns:
            List of message dicts for API call
        """
        messages = []

        # System message
        system_content = self.build_system_prompt(context)
        messages.append({"role": "system", "content": system_content})

        # Convert conversation history to messages
        for msg in context.conversation_history:
            if msg.role == "user":
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == "tool_result":
                # Tool results are formatted as user messages with results
                messages.append({"role": "user", "content": f"Tool Results:\n{msg.content}"})

        # If this is the first message (no history), add the task as user message
        if not context.conversation_history:
            user_prompt = self.build_user_prompt(context)
            messages.append({"role": "user", "content": user_prompt})

        return messages

    def _build_tools_section(self, tools: List[str]) -> str:
        """Build the available tools section."""
        if not tools:
            return "## Available Tools\n\nNo tools available."

        tool_list = "\n".join(f"- {tool}" for tool in tools)

        return f"""## Available Tools

{tool_list}

### Tool Descriptions

- **read_file**: Read contents of a file. Parameters: path (required)
- **write_file**: Write content to a file. Parameters: path (required), content (required)
- **edit_file**: Edit a file with search/replace. Parameters: path, old_string, new_string
- **glob**: Find files matching a pattern. Parameters: pattern (required), path (optional)
- **grep**: Search for text in files. Parameters: pattern (required), path (optional)
- **bash**: Execute a shell command. Parameters: command (required)
- **run_tests**: Run test suite. Parameters: test_path (optional)
"""

    def _build_task_section(self, context: ExecutionContext) -> str:
        """Build the task description section."""
        return f"""<task>
<description>{context.task_description}</description>
<phase>{context.current_phase}</phase>
<iteration>{context.iteration}</iteration>
</task>"""

    def _build_memory_section(self, memory: dict) -> str:
        """Build the memory context section."""
        memory_yaml = yaml.dump(memory, default_flow_style=False, sort_keys=False)
        return f"""<memory_context>
{memory_yaml}
</memory_context>"""

    def _build_history_section(self, messages: List[ConversationMessage]) -> str:
        """Build the conversation history section."""
        if not messages:
            return ""

        history_parts = []
        for msg in messages:
            if msg.role == "user":
                history_parts.append(f"<user_message>\n{msg.content}\n</user_message>")
            elif msg.role == "assistant":
                history_parts.append(f"<assistant_message>\n{msg.content}\n</assistant_message>")
            elif msg.role == "tool_result":
                history_parts.append(f"<tool_results>\n{msg.content}\n</tool_results>")

        return f"""<conversation_history>
{chr(10).join(history_parts)}
</conversation_history>"""

    def _build_status_section(self, context: ExecutionContext) -> str:
        """Build the current status section."""
        return f"""<status>
<tokens_used>{context.tokens_used}</tokens_used>
<tokens_remaining>{context.tokens_remaining}</tokens_remaining>
<iteration>{context.iteration}</iteration>
</status>

Now decide on your next action. Remember to include your thinking process."""

    def format_tool_results(self, results: List[ToolResult]) -> str:
        """Format tool results for conversation history.

        Args:
            results: List of tool results

        Returns:
            Formatted string for history
        """
        parts = []
        for result in results:
            status = "SUCCESS" if result.success else "ERROR"
            output = result.output if result.success else result.error
            parts.append(f"[{result.tool_name}] {status}:\n{output}")

        return "\n\n".join(parts)
