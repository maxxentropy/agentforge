# @spec_file: .agentforge/specs/harness-v1.yaml
# @spec_id: harness-v1
# @component_id: tools-harness-python_tools
# @test_path: tests/integration/harness/test_harness_workflow.py

"""
Python Tools for Fix Workflow
=============================

Provides Python-specific analysis tools using pyright LSP and the discovery provider.
These tools help the agent understand code structure when fixing violations.

Key capabilities:
- Analyze function complexity and structure
- Get symbol information (functions, classes, methods)
- Type checking via pyright
- Complexity metrics and extraction suggestions

Note: This module delegates to PythonProvider from the discovery system
for all AST analysis, ensuring a single source of truth.
"""

from pathlib import Path
from typing import Any, Dict

from .llm_executor_domain import ToolResult

# Use the discovery provider as single source of truth for Python AST analysis
from ..discovery.providers.python_provider import PythonProvider

# Try to import LSP adapters and pyright runner
try:
    from ..lsp_adapters import PyrightAdapter
    from ..lsp_client import LSPServerNotFound
    from ..pyright_runner import PyrightRunner, PyrightResult
except ImportError:
    PyrightAdapter = None
    LSPServerNotFound = Exception
    PyrightRunner = None
    PyrightResult = None


class PythonTools:
    """
    Python-specific tools for the fix workflow.

    Delegates to PythonProvider from the discovery system for AST analysis,
    ensuring a single source of truth. Optionally uses LSP/pyright for type checking.
    """

    def __init__(self, project_path: Path, use_lsp: bool = False):
        """
        Initialize Python tools.

        Args:
            project_path: Project root directory
            use_lsp: Whether to use LSP for enhanced analysis (requires pyright)
        """
        self.project_path = Path(project_path)
        self.provider = PythonProvider()  # Single source of truth for AST analysis
        self.lsp_adapter = None
        self.pyright_runner = None

        if use_lsp and PyrightAdapter:
            try:
                self.lsp_adapter = PyrightAdapter(str(project_path))
            except Exception:
                pass  # LSP not available

        if PyrightRunner:
            try:
                self.pyright_runner = PyrightRunner(project_path)
            except Exception:
                pass  # Pyright not available

    def analyze_function(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Analyze a Python function's structure and complexity.

        Parameters:
            file_path: Path to the Python file
            function_name: Name of the function to analyze

        Returns:
            ToolResult with detailed analysis including:
            - Complexity metrics (cyclomatic, cognitive)
            - Nesting depth
            - Branch and loop counts
            - Extraction suggestions
        """
        file_path = params.get("file_path")
        function_name = params.get("function_name")

        if not file_path:
            return ToolResult.failure_result(
                "analyze_function", "Missing required parameter: file_path"
            )
        if not function_name:
            return ToolResult.failure_result(
                "analyze_function", "Missing required parameter: function_name"
            )

        full_path = self.project_path / file_path
        if not full_path.exists():
            return ToolResult.failure_result(
                "analyze_function", f"File not found: {file_path}"
            )

        try:
            # Use PythonProvider for all analysis
            location = self.provider.get_function_location(full_path, function_name)
            if not location:
                return ToolResult.failure_result(
                    "analyze_function",
                    f"Function '{function_name}' not found in {file_path}"
                )

            # Get complexity metrics
            metrics = self.provider.analyze_complexity(full_path, function_name)

            # Get extraction suggestions
            suggestions = self.provider.get_extractable_ranges(full_path, function_name)

            # Get function source
            func_source = self.provider.get_function_source(full_path, function_name)

            # Format output
            output = f"""
=== Function Analysis: {function_name} ===
File: {file_path}
Lines: {location[0]}-{location[1]}

METRICS:
  Cyclomatic Complexity: {metrics.cyclomatic_complexity if metrics else 'N/A'} (threshold: 10)
  Cognitive Complexity: {metrics.cognitive_complexity if metrics else 'N/A'}
  Nesting Depth: {metrics.nesting_depth if metrics else 'N/A'} (threshold: 4)
  Line Count: {metrics.line_count if metrics else 'N/A'}
  Branches: {metrics.branch_count if metrics else 'N/A'}
  Loops: {metrics.loop_count if metrics else 'N/A'}
"""

            if suggestions:
                output += "\nEXTRACTION SUGGESTIONS:\n"
                for i, s in enumerate(suggestions[:5], 1):
                    extractable = "✓" if s.get('extractable', True) else "✗"
                    output += f"  {i}. [{extractable}] {s['description']}\n"
                    output += f"     Lines {s['start_line']}-{s['end_line']}, reduces complexity by ~{s['estimated_complexity_reduction']}\n"
                    if s.get('reason'):
                        output += f"     Note: {s['reason']}\n"

            if func_source:
                output += f"\nFUNCTION SOURCE:\n```python\n{func_source[:2000]}\n```"

            return ToolResult.success_result("analyze_function", output)

        except Exception as e:
            return ToolResult.failure_result(
                "analyze_function", f"Error analyzing function: {e}"
            )

    def get_symbols(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Get all symbols (functions, classes) in a Python file.

        Uses PythonProvider.extract_symbols for consistent analysis.

        Parameters:
            file_path: Path to the Python file

        Returns:
            ToolResult with list of symbols and their locations
        """
        file_path = params.get("file_path")

        if not file_path:
            return ToolResult.failure_result(
                "get_symbols", "Missing required parameter: file_path"
            )

        full_path = self.project_path / file_path
        if not full_path.exists():
            return ToolResult.failure_result(
                "get_symbols", f"File not found: {file_path}"
            )

        try:
            # Use PythonProvider for symbol extraction
            symbols = self.provider.extract_symbols(full_path)

            # Sort by line number
            symbols.sort(key=lambda s: s.line_number)

            output = f"=== Symbols in {file_path} ===\n\n"
            for s in symbols:
                kind = s.kind
                end_line = s.end_line or s.line_number
                parent_info = f" (in {s.parent})" if s.parent else ""
                output += f"  {kind:10} {s.name:30} (lines {s.line_number}-{end_line}){parent_info}\n"

            return ToolResult.success_result("get_symbols", output)

        except SyntaxError as e:
            return ToolResult.failure_result(
                "get_symbols", f"Syntax error in {file_path}: {e}"
            )
        except Exception as e:
            return ToolResult.failure_result(
                "get_symbols", f"Error parsing file: {e}"
            )

    def check_types(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run pyright type checking on a file.

        Parameters:
            file_path: Path to the Python file

        Returns:
            ToolResult with type errors/warnings
        """
        file_path = params.get("file_path")

        if not file_path:
            return ToolResult.failure_result(
                "check_types", "Missing required parameter: file_path"
            )

        if not self.pyright_runner:
            return ToolResult.failure_result(
                "check_types", "Pyright not available. Install with: pip install pyright"
            )

        full_path = self.project_path / file_path
        if not full_path.exists():
            return ToolResult.failure_result(
                "check_types", f"File not found: {file_path}"
            )

        try:
            result = self.pyright_runner.check_file(full_path)

            if result.success:
                return ToolResult.success_result(
                    "check_types",
                    f"✓ No type errors in {file_path}\n"
                    f"  Files analyzed: {result.files_analyzed}"
                )

            # Format diagnostics
            output = f"Type checking {file_path}:\n"
            output += f"  Errors: {result.error_count}, Warnings: {result.warning_count}\n\n"

            for diag in result.diagnostics[:20]:
                severity = "ERROR" if diag.severity == "error" else "WARN"
                output += f"  [{severity}] Line {diag.line}: {diag.message}\n"

            if len(result.diagnostics) > 20:
                output += f"\n  ... and {len(result.diagnostics) - 20} more\n"

            return ToolResult(
                tool_name="check_types",
                success=False,
                output=output,
                error=f"{result.error_count} type errors found"
            )

        except Exception as e:
            return ToolResult.failure_result(
                "check_types", f"Error running pyright: {e}"
            )

    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "analyze_function": self.analyze_function,
            "get_symbols": self.get_symbols,
            "check_types": self.check_types,
        }


# Tool definitions for prompt building
PYTHON_TOOL_DEFINITIONS = [
    {
        "name": "analyze_function",
        "description": "Analyze a Python function's complexity, structure, and get refactoring suggestions",
        "parameters": {
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to the Python file",
            },
            "function_name": {
                "type": "string",
                "required": True,
                "description": "Name of the function to analyze",
            },
        },
    },
    {
        "name": "get_symbols",
        "description": "List all functions and classes in a Python file with line numbers",
        "parameters": {
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to the Python file",
            },
        },
    },
    {
        "name": "check_types",
        "description": "Run pyright type checking on a Python file",
        "parameters": {
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to the Python file",
            },
        },
    },
]
