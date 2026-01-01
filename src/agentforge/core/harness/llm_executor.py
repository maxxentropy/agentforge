# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: core-harness-llm_executor
# @test_path: tests/unit/harness/test_action_parser.py

"""
LLM Executor
============

Executes agent steps by calling the LLM and processing actions.
This is the core component that enables the Agent Harness to actually run.
"""

import time
from typing import Any, Callable, Dict, List, Optional

from agentforge.core.generate.provider import LLMProvider, get_provider
from agentforge.core.harness.llm_executor_domain import (
    ActionType,
    AgentAction,
    ExecutionContext,
    StepResult,
    ToolCall,
    ToolResult,
    LLMExecutorError,
    ToolExecutionError,
)
from agentforge.core.harness.agent_prompt_builder import AgentPromptBuilder
from agentforge.core.harness.action_parser import ActionParser


# Type alias for tool executors
ToolExecutor = Callable[[str, Dict[str, Any]], ToolResult]


class LLMExecutor:
    """Executes agent steps via LLM calls.

    This component:
    1. Builds prompts from execution context
    2. Calls the LLM to decide on actions
    3. Parses LLM responses into actions
    4. Executes tool calls
    5. Updates context with results
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        prompt_builder: Optional[AgentPromptBuilder] = None,
        action_parser: Optional[ActionParser] = None,
        tool_executors: Optional[Dict[str, ToolExecutor]] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ):
        """Initialize the executor.

        Args:
            provider: LLM provider (uses default if not provided)
            prompt_builder: Prompt builder (uses default if not provided)
            action_parser: Action parser (uses default if not provided)
            tool_executors: Dict mapping tool names to executor functions
            model: Model to use for LLM calls
            max_tokens: Maximum tokens for LLM response
        """
        self.provider = provider or get_provider()
        self.prompt_builder = prompt_builder or AgentPromptBuilder()
        self.action_parser = action_parser or ActionParser()
        self.tool_executors = tool_executors or {}
        self.model = model
        self.max_tokens = max_tokens

    def register_tool(self, name: str, executor: ToolExecutor) -> None:
        """Register a tool executor.

        Args:
            name: Tool name
            executor: Function that takes (tool_name, parameters) and returns ToolResult
        """
        self.tool_executors[name] = executor

    def register_tools(self, executors: Dict[str, ToolExecutor]) -> None:
        """Register multiple tool executors.

        Args:
            executors: Dict mapping tool names to executor functions
        """
        self.tool_executors.update(executors)

    def execute_step(self, context: ExecutionContext) -> StepResult:
        """Execute one agent step.

        Args:
            context: Current execution context

        Returns:
            StepResult with action taken and results
        """
        start_time = time.time()

        try:
            # Build messages for LLM
            messages = self.prompt_builder.build_messages(context)

            # Call LLM
            response, tokens_used = self._call_llm(messages)

            # Update token usage in context
            context.tokens_used += tokens_used

            # Parse response into action
            action = self.action_parser.parse_lenient(response)

            # Add assistant message to history
            context.add_assistant_message(
                response,
                action.tool_calls if action.action_type == ActionType.TOOL_CALL else None
            )

            # Execute tools if needed
            tool_results = []
            if action.action_type == ActionType.TOOL_CALL:
                tool_results = self._execute_tools(action.tool_calls)
                context.add_tool_results(tool_results)

            # Increment iteration
            context.iteration += 1

            duration = time.time() - start_time
            return StepResult.success_step(action, tool_results, tokens_used, duration)

        except LLMExecutorError as e:
            duration = time.time() - start_time
            return StepResult.failure_step(str(e), duration)

        except Exception as e:
            duration = time.time() - start_time
            return StepResult.failure_step(f"Unexpected error: {e}", duration)

    def _call_llm(self, messages: List[dict]) -> tuple[str, int]:
        """Call the LLM provider.

        Args:
            messages: List of message dicts for the API

        Returns:
            Tuple of (response_text, tokens_used)
        """
        import asyncio
        import inspect

        # Convert messages to prompt format expected by provider
        # The provider expects a single prompt string
        prompt = self._messages_to_prompt(messages)

        # Call the provider - may be sync (mock) or async (real provider)
        result = self.provider.generate(prompt, self.max_tokens)

        # Handle async coroutine if returned
        if inspect.iscoroutine(result):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None:
                # We're already in an async context, create a new loop in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, result)
                    response = future.result()
            else:
                # No running loop, we can use asyncio.run directly
                response = asyncio.run(result)
        else:
            # Sync response (e.g., from mock)
            response = result

        # Handle response format - provider may return (text, TokenUsage) tuple or just text
        if isinstance(response, tuple) and len(response) == 2:
            response_text, token_usage = response
            # TokenUsage has prompt_tokens and completion_tokens
            if hasattr(token_usage, 'prompt_tokens') and hasattr(token_usage, 'completion_tokens'):
                tokens_used = token_usage.prompt_tokens + token_usage.completion_tokens
            else:
                tokens_used = self.provider.count_tokens(prompt) + self.provider.count_tokens(response_text)
        else:
            response_text = response
            # Estimate tokens
            tokens_used = self.provider.count_tokens(prompt) + self.provider.count_tokens(response_text)

        return response_text, tokens_used

    def _messages_to_prompt(self, messages: List[dict]) -> str:
        """Convert message list to a single prompt string.

        This formats messages for providers that expect a single prompt
        rather than a message array.
        """
        parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                parts.append(f"<system>\n{content}\n</system>\n")
            elif role == "user":
                parts.append(f"<user>\n{content}\n</user>\n")
            elif role == "assistant":
                parts.append(f"<assistant>\n{content}\n</assistant>\n")

        return "\n".join(parts)

    def _execute_tools(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute a list of tool calls.

        Args:
            tool_calls: List of tools to execute

        Returns:
            List of ToolResult objects
        """
        results = []

        for tool_call in tool_calls:
            result = self._execute_single_tool(tool_call)
            results.append(result)

        return results

    def _execute_single_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call.

        Args:
            tool_call: Tool to execute

        Returns:
            ToolResult
        """
        start_time = time.time()
        tool_name = tool_call.name

        # Check if tool is registered
        if tool_name not in self.tool_executors:
            return ToolResult.failure_result(
                tool_name,
                f"Unknown tool: {tool_name}. Available tools: {list(self.tool_executors.keys())}",
                time.time() - start_time
            )

        try:
            executor = self.tool_executors[tool_name]
            result = executor(tool_name, tool_call.parameters)

            # Ensure we have a proper ToolResult
            if isinstance(result, ToolResult):
                return result

            # If executor returned something else, wrap it
            return ToolResult.success_result(
                tool_name,
                result,
                time.time() - start_time
            )

        except Exception as e:
            return ToolResult.failure_result(
                tool_name,
                f"Tool execution error: {e}",
                time.time() - start_time
            )

    def run_until_complete(
        self,
        context: ExecutionContext,
        max_iterations: int = 50,
        on_step: Optional[Callable[[StepResult], None]] = None,
    ) -> List[StepResult]:
        """Run the agent until completion or max iterations.

        Args:
            context: Execution context
            max_iterations: Maximum number of steps
            on_step: Optional callback after each step

        Returns:
            List of all step results
        """
        results = []

        for i in range(max_iterations):
            # Check token budget
            if context.tokens_remaining <= 0:
                results.append(StepResult.failure_step("Token budget exhausted"))
                break

            # Execute step
            result = self.execute_step(context)
            results.append(result)

            # Callback
            if on_step:
                on_step(result)

            # Check if we should stop
            if not result.should_continue:
                break

        return results


def create_default_executor(
    tool_executors: Optional[Dict[str, ToolExecutor]] = None,
    model: str = "claude-sonnet-4-20250514",
) -> LLMExecutor:
    """Create an LLM executor with default configuration.

    Args:
        tool_executors: Optional dict of tool executors
        model: Model to use

    Returns:
        Configured LLMExecutor
    """
    return LLMExecutor(
        tool_executors=tool_executors or {},
        model=model,
    )
