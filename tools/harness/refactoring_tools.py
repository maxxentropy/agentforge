# @spec_file: .agentforge/specs/harness-v1.yaml
# @spec_id: harness-v1
# @component_id: tools-harness-refactoring_tools
# @test_path: tests/integration/harness/test_harness_workflow.py

"""
Refactoring Tools
=================

Semantic refactoring tools using language-aware tooling.

For Python: Uses the `rope` library which correctly handles:
- Control flow (early returns, break, continue)
- Variable scope and parameter detection
- Return value handling

CORRECTNESS FIRST: Extractions that would break semantics are REJECTED,
not silently applied to produce broken code.
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llm_executor_domain import ToolResult


class RefactoringTools:
    """
    Refactoring tools using proper language-aware tooling.

    For Python: Uses the `rope` library which correctly handles:
    - Control flow (early returns, break, continue)
    - Variable scope and parameter detection
    - Return value handling

    For other languages: Will use LSP codeAction (future).

    CORRECTNESS FIRST: Extractions that would break semantics are REJECTED,
    not silently applied to produce broken code.
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self._providers = {}  # Cache of refactoring providers

    def _get_provider(self, file_path: Path):
        """Get the appropriate refactoring provider for a file."""
        from ..refactoring import get_refactoring_provider
        suffix = file_path.suffix
        if suffix not in self._providers:
            self._providers[suffix] = get_refactoring_provider(file_path, self.project_path)
        return self._providers[suffix]

    def extract_function(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Extract a code block into a helper function.

        Uses language-aware refactoring (rope for Python) that:
        - REJECTS extractions that would break control flow (early returns)
        - Correctly handles parameters and return values
        - Validates the result is semantically correct

        Parameters:
            file_path: Path to the file
            start_line: First line of code to extract (1-indexed)
            end_line: Last line of code to extract (1-indexed, inclusive)
            new_function_name: Name for the extracted helper

        Returns:
            ToolResult with success/failure and details
        """
        file_path = params.get("file_path")
        start_line = params.get("start_line")
        end_line = params.get("end_line")
        new_function_name = params.get("new_function_name")

        # Validate parameters
        if not file_path:
            return ToolResult.failure_result(
                "extract_function", "Missing required parameter: file_path"
            )
        if start_line is None or end_line is None:
            return ToolResult.failure_result(
                "extract_function", "Missing required parameters: start_line and end_line"
            )
        if not new_function_name:
            return ToolResult.failure_result(
                "extract_function", "Missing required parameter: new_function_name"
            )

        full_path = self.project_path / file_path
        if not full_path.exists():
            return ToolResult.failure_result(
                "extract_function", f"File not found: {file_path}"
            )

        # Get the appropriate refactoring provider
        provider = self._get_provider(full_path)
        if provider is None:
            return ToolResult.failure_result(
                "extract_function",
                f"No refactoring support for {full_path.suffix} files. "
                f"Currently supported: .py (Python via rope)"
            )

        # First check if extraction is valid
        can_extract = provider.can_extract_function(full_path, start_line, end_line)
        if not can_extract.can_extract:
            return ToolResult.failure_result(
                "extract_function",
                f"✗ {can_extract.reason}"
            )

        # Perform the extraction
        result = provider.extract_function(
            full_path, start_line, end_line, new_function_name
        )

        if not result.success:
            return ToolResult.failure_result(
                "extract_function",
                f"✗ {result.error}"
            )

        # Write the new content
        full_path.write_text(result.new_content)

        return ToolResult.success_result(
            "extract_function",
            f"✓ {result.changes_description}\n"
            f"  Refactoring validated by rope - semantics preserved"
        )

    def simplify_conditional(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Simplify a complex conditional using guard clause pattern.

        Transforms:
            if x:
                ... lots of code ...
            else:
                return None

        Into:
            if not x:
                return None
            ... lots of code (dedented) ...

        Parameters:
            file_path: Path to the Python file
            function_name: Name of the function
            if_line: Line number of the if statement to simplify
        """
        file_path = params.get("file_path")
        function_name = params.get("function_name")
        if_line = params.get("if_line")

        if not all([file_path, function_name, if_line]):
            return ToolResult.failure_result(
                "simplify_conditional",
                "Missing required parameters: file_path, function_name, if_line"
            )

        full_path = self.project_path / file_path
        if not full_path.exists():
            return ToolResult.failure_result(
                "simplify_conditional", f"File not found: {file_path}"
            )

        try:
            source = full_path.read_text()
            tree = ast.parse(source)
            lines = source.split('\n')

            # Find the if statement at the specified line
            target_if = None
            for node in ast.walk(tree):
                if isinstance(node, ast.If) and node.lineno == if_line:
                    target_if = node
                    break

            if not target_if:
                return ToolResult.failure_result(
                    "simplify_conditional",
                    f"No if statement found at line {if_line}"
                )

            # Check if this is a guard clause pattern (else returns early)
            if not target_if.orelse:
                return ToolResult.failure_result(
                    "simplify_conditional",
                    "If statement has no else clause - cannot simplify to guard"
                )

            # Check if else is a simple return
            if len(target_if.orelse) != 1 or not isinstance(target_if.orelse[0], ast.Return):
                return ToolResult.failure_result(
                    "simplify_conditional",
                    "Else clause is not a simple return - cannot simplify"
                )

            # Get the return value
            return_node = target_if.orelse[0]
            if return_node.value is None:
                return_value = "None"
            else:
                return_value = ast.unparse(return_node.value)

            # Negate the condition
            negated_test = ast.UnaryOp(op=ast.Not(), operand=target_if.test)
            negated_condition = ast.unparse(negated_test)

            # Detect indentation
            if_line_content = lines[if_line - 1]
            base_indent = len(if_line_content) - len(if_line_content.lstrip())
            indent_str = ' ' * base_indent

            # Build the new code
            # Guard clause first
            guard = f"{indent_str}if {negated_condition}:\n{indent_str}    return {return_value}"

            # Then the body (dedented one level from the original if body)
            body_start = target_if.body[0].lineno - 1
            body_end = target_if.body[-1].end_lineno
            body_lines = lines[body_start:body_end]

            # Dedent body by one level (4 spaces)
            dedented_body = []
            for line in body_lines:
                if line.strip():
                    if line.startswith(indent_str + '    '):
                        dedented_body.append(line[4:])  # Remove 4 spaces
                    else:
                        dedented_body.append(line)
                else:
                    dedented_body.append('')

            # Replace the original if/else with guard + body
            if_start = if_line - 1
            if_end = target_if.orelse[-1].end_lineno

            new_lines = (
                lines[:if_start] +
                [guard] +
                dedented_body +
                lines[if_end:]
            )

            new_source = '\n'.join(new_lines)

            # Validate
            try:
                ast.parse(new_source)
            except SyntaxError as e:
                return ToolResult.failure_result(
                    "simplify_conditional",
                    f"Simplification would produce invalid Python: {e}"
                )

            full_path.write_text(new_source)

            return ToolResult.success_result(
                "simplify_conditional",
                f"✓ Simplified conditional at line {if_line}\n"
                f"  Converted to guard clause pattern"
            )

        except Exception as e:
            return ToolResult.failure_result(
                "simplify_conditional", f"Error: {e}"
            )

    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "extract_function": self.extract_function,
            "simplify_conditional": self.simplify_conditional,
        }


# Tool definitions for prompt building
REFACTORING_TOOL_DEFINITIONS = [
    {
        "name": "extract_function",
        "description": (
            "Extract lines of code into a new helper function. "
            "Automatically detects parameters and handles indentation. "
            "Use for reducing cyclomatic complexity."
        ),
        "parameters": {
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to the Python file",
            },
            "source_function": {
                "type": "string",
                "required": True,
                "description": "Name of the function to refactor",
            },
            "start_line": {
                "type": "integer",
                "required": True,
                "description": "First line of code to extract (1-indexed)",
            },
            "end_line": {
                "type": "integer",
                "required": True,
                "description": "Last line of code to extract (1-indexed, inclusive)",
            },
            "new_function_name": {
                "type": "string",
                "required": True,
                "description": "Name for the new helper function",
            },
        },
    },
    {
        "name": "simplify_conditional",
        "description": (
            "Convert if/else with return in else to guard clause pattern. "
            "Reduces nesting depth."
        ),
        "parameters": {
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to the Python file",
            },
            "function_name": {
                "type": "string",
                "required": True,
                "description": "Name of the function containing the if statement",
            },
            "if_line": {
                "type": "integer",
                "required": True,
                "description": "Line number of the if statement to simplify (1-indexed)",
            },
        },
    },
]
