# @spec_file: specs/minimal-context-architecture/05-llm-integration.yaml
# @spec_id: llm-integration-v1
# @component_id: native-tool-executor
# @test_path: tests/unit/harness/test_native_tool_executor.py

"""
Native Tool Executor
====================

Adapter that bridges LLM native tool calls to registered action executors.

This enables the executor to use Anthropic's native tool_use API instead
of parsing YAML from text responses. Benefits:
- Structured inputs validated by JSON Schema
- No parsing errors or ambiguity
- Direct tool call IDs for result correlation
- Better error handling

Usage:
    ```python
    from agentforge.core.harness.minimal_context.native_tool_executor import (
        NativeToolExecutor,
        create_enhanced_handlers,  # Full handler set
    )

    # Create executor with enhanced handlers (recommended)
    handlers = create_enhanced_handlers(project_path)
    executor = NativeToolExecutor(actions=handlers)

    # Or use registry for custom handler sets
    from agentforge.core.harness.minimal_context.tool_handlers import (
        ToolHandlerRegistry,
    )

    registry = ToolHandlerRegistry(project_path)
    registry.add_file_handlers().add_verify_handlers()
    executor = NativeToolExecutor(actions=registry.get_handlers())

    # Use with LLM client
    response = llm_client.complete_with_tools(
        system=system_prompt,
        messages=messages,
        tools=get_tools_for_task("fix_violation"),
        tool_executor=executor,
    )
    ```
"""

import logging
import traceback
from typing import Any, Callable, Dict, Optional

from ...llm.interface import ToolCall, ToolExecutor, ToolResult

logger = logging.getLogger(__name__)


# Type alias for action handlers
ActionHandler = Callable[[Dict[str, Any]], Any]


class NativeToolExecutor(ToolExecutor):
    """
    Executes LLM tool calls by delegating to registered action handlers.

    This adapter bridges the gap between the LLM's native tool_use format
    and the executor's action handler system.

    Attributes:
        actions: Dict mapping tool names to handler functions
        context: Optional shared context dict passed to handlers
    """

    def __init__(
        self,
        actions: Optional[Dict[str, ActionHandler]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the executor.

        Args:
            actions: Initial action handlers dict
            context: Shared context for handlers
        """
        self.actions: Dict[str, ActionHandler] = actions or {}
        self.context: Dict[str, Any] = context or {}
        self._execution_log: list = []

    def register_action(self, name: str, handler: ActionHandler) -> None:
        """
        Register an action handler.

        Args:
            name: Tool/action name (e.g., "read_file")
            handler: Function that takes params dict and returns result
        """
        self.actions[name] = handler
        logger.debug(f"Registered action handler: {name}")

    def register_actions(self, handlers: Dict[str, ActionHandler]) -> None:
        """
        Register multiple action handlers.

        Args:
            handlers: Dict mapping names to handler functions
        """
        for name, handler in handlers.items():
            self.register_action(name, handler)

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call from the LLM.

        Finds the registered handler for the tool and executes it
        with the provided input parameters.

        Args:
            tool_call: The tool call from the LLM

        Returns:
            ToolResult with execution outcome
        """
        tool_name = tool_call.name
        tool_input = tool_call.input
        tool_id = tool_call.id

        logger.debug(f"Executing tool: {tool_name} (id={tool_id})")

        # Check if action is registered
        if tool_name not in self.actions:
            error_msg = f"Unknown tool: {tool_name}. Available: {list(self.actions.keys())}"
            logger.error(error_msg)
            self._log_execution(tool_call, error=error_msg)
            return ToolResult(
                tool_use_id=tool_id,
                content=error_msg,
                is_error=True,
            )

        # Get handler and execute
        handler = self.actions[tool_name]

        try:
            # Inject context if handler accepts it
            params = dict(tool_input)
            if self.context:
                params["_context"] = self.context

            result = handler(params)

            # Convert result to string if needed
            if result is None:
                result_str = "Success"
            elif isinstance(result, str):
                result_str = result
            elif isinstance(result, dict):
                # Format dict nicely
                import json
                result_str = json.dumps(result, indent=2, default=str)
            else:
                result_str = str(result)

            self._log_execution(tool_call, result=result_str)

            return ToolResult(
                tool_use_id=tool_id,
                content=result_str,
                is_error=False,
            )

        except Exception as e:
            error_msg = f"Tool execution failed: {e}\n{traceback.format_exc()}"
            logger.error(f"Error executing {tool_name}: {e}")
            self._log_execution(tool_call, error=error_msg)
            return ToolResult(
                tool_use_id=tool_id,
                content=error_msg,
                is_error=True,
            )

    def _log_execution(
        self,
        tool_call: ToolCall,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log tool execution for audit trail."""
        self._execution_log.append({
            "tool_id": tool_call.id,
            "tool_name": tool_call.name,
            "input": tool_call.input,
            "result": result,
            "error": error,
            "success": error is None,
        })

    def get_execution_log(self) -> list:
        """Get the execution log for audit purposes."""
        return list(self._execution_log)

    def clear_execution_log(self) -> None:
        """Clear the execution log."""
        self._execution_log.clear()

    def has_action(self, name: str) -> bool:
        """Check if an action is registered."""
        return name in self.actions

    def list_actions(self) -> list:
        """List all registered action names."""
        return sorted(self.actions.keys())


def create_enhanced_handlers(project_path=None) -> Dict[str, ActionHandler]:
    """
    Create enhanced action handlers from the tool_handlers module.

    This includes all P0 handlers required for the fix_violation workflow:
    - File operations: read_file, write_file, edit_file, replace_lines, insert_lines
    - Search: search_code, load_context, find_related
    - Verification: run_check, run_tests, validate_python
    - Terminal: complete, escalate, cannot_fix, plan_fix

    Args:
        project_path: Base path for file operations

    Returns:
        Dict of action name to handler
    """
    from .tool_handlers import create_standard_handlers as create_full_handlers

    return create_full_handlers(project_path)


def create_fix_violation_handlers(project_path=None) -> Dict[str, ActionHandler]:
    """
    Create handlers specifically for the fix_violation workflow.

    This is the recommended handler set for violation fixing tasks.

    Args:
        project_path: Project root path

    Returns:
        Dict of action name to handler
    """
    from .tool_handlers import create_fix_violation_handlers as create_handlers

    return create_handlers(project_path)
