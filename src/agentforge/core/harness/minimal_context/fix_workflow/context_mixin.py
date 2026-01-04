# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow-context

"""
Context Building Mixin
======================

Methods for pre-computing and refreshing violation context.
Uses AST analysis and the Python provider for deterministic analysis.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..state_store import TaskState


class ContextMixin:
    """
    Context building methods for fix workflow.

    Pre-computes rich context before the agent starts using code-based
    analysis (not LLM), enabling more informed fix attempts.
    """

    # Type hints for mixin - provided by main class
    project_path: Path
    conformance_tools: Any
    state_store: Any

    def _read_source_file(self, full_path: Path) -> tuple[str, list[str]] | None:
        """Read source file and return (source, lines) or None on error."""
        try:
            source = full_path.read_text()
            return source, source.split('\n')
        except Exception:
            return None

    def _find_violating_function(
        self, tree: Any, line_number: int | None, num_lines: int
    ) -> str | None:
        """Find the function containing the violation line."""
        import ast
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if line_number and node.lineno <= line_number <= (node.end_lineno or num_lines):
                    return node.name
        return None

    def _add_provider_context(
        self, precomputed: dict, provider: Any,
        full_path: Path, func_name: str, check_id: str,
    ) -> None:
        """Add violation context from provider (location, metrics, suggestions)."""
        violation_context = provider.get_violation_context(full_path, func_name, check_id)
        if "error" in violation_context:
            return

        if violation_context.get("location"):
            loc = violation_context["location"]
            precomputed["function_lines"] = f"{loc['start']}-{loc['end']}"

        if violation_context.get("metrics"):
            precomputed["analysis"] = violation_context["metrics"]

        self._add_extraction_suggestions(precomputed, full_path, violation_context)

        if violation_context.get("strategy"):
            precomputed["fix_strategy"] = violation_context["strategy"]

    def _add_extraction_suggestions(
        self, precomputed: dict, full_path: Path, violation_context: dict
    ) -> None:
        """Add validated extraction suggestions or explanation if not possible."""
        raw_suggestions = violation_context.get("suggestions")
        if not raw_suggestions:
            return

        validated = self._validate_extraction_suggestions(full_path, raw_suggestions)
        if validated:
            precomputed["extraction_suggestions"] = validated
        else:
            precomputed["extraction_not_possible"] = (
                "All suggested extractions were rejected by the refactoring "
                "tool. The code contains early returns, break/continue statements, "
                "or other control flow that makes simple extraction unsafe. "
                "Consider restructuring the code (e.g., using result variables "
                "instead of early returns) before extracting."
            )

    def _add_class_context(
        self, precomputed: dict, tree: Any, func_name: str
    ) -> None:
        """Add class context if function is a method."""
        import ast
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == func_name:
                    precomputed["parent_class"] = node.name
                    precomputed["class_methods"] = [
                        {"name": m.name, "line": m.lineno, "end_line": m.end_lineno}
                        for m in node.body
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    return

    def _add_check_definition(self, precomputed: dict, check_id: str) -> None:
        """Add check definition from conformance tools."""
        try:
            result = self.conformance_tools.get_check_definition(
                "get_check_definition", {"check_id": check_id}
            )
            if result.success:
                precomputed["check_definition"] = result.output
        except Exception:
            pass

    def _add_file_context(
        self, precomputed: dict, lines: list[str], line_number: int
    ) -> None:
        """Add file context around violation line."""
        start = max(0, line_number - 10)
        end = min(len(lines), line_number + 10)
        context_lines = [
            f"{'>>> ' if i + 1 == line_number else '    '}{i + 1:4d}: {lines[i]}"
            for i in range(start, end)
        ]
        precomputed["file_context"] = "\n".join(context_lines)

    def _add_python_context(
        self, precomputed: dict, full_path: Path, lines: list[str],
        line_number: int | None, check_id: str
    ) -> None:
        """Add Python-specific context using AST analysis."""
        from ....discovery.providers.python_provider import PythonProvider

        provider = PythonProvider()
        try:
            tree = provider.parse_file(full_path)
            if tree is None:
                return

            func_name = self._find_violating_function(tree, line_number, len(lines))
            if not func_name:
                return

            precomputed["violating_function"] = func_name
            self._add_provider_context(precomputed, provider, full_path, func_name, check_id)

            func_source = provider.get_function_source(full_path, func_name)
            if func_source:
                precomputed["function_source"] = func_source

            self._add_class_context(precomputed, tree, func_name)
        except SyntaxError:
            pass  # File has syntax errors, skip AST analysis

    def _precompute_violation_context(
        self,
        violation_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Pre-compute rich context for a violation fix using deterministic tools.

        This runs BEFORE the agent starts, using code-based analysis (not LLM).
        Uses PythonProvider as the single source of truth for AST analysis.
        """
        precomputed: dict[str, Any] = {}

        file_path = violation_data.get("file_path")
        line_number = violation_data.get("line_number")
        check_id = violation_data.get("check_id")

        if not file_path:
            return precomputed

        full_path = self.project_path / file_path
        if not full_path.exists():
            return precomputed

        result = self._read_source_file(full_path)
        if result is None:
            return precomputed
        source, lines = result

        # For Python files, use the PythonProvider for unified AST analysis
        if file_path.endswith('.py'):
            self._add_python_context(precomputed, full_path, lines, line_number, check_id or "")

        if check_id:
            self._add_check_definition(precomputed, check_id)

        if line_number and lines:
            self._add_file_context(precomputed, lines, line_number)

        return precomputed

    def _refresh_precomputed_context(
        self,
        file_path: str,
        function_name: str,
        state: "TaskState",
    ) -> dict[str, Any] | None:
        """Refresh pre-computed context for a new function after extraction."""
        from ....discovery.providers.python_provider import PythonProvider

        full_path = self.project_path / file_path
        if not full_path.exists():
            return None

        try:
            provider = PythonProvider()

            location = provider.get_function_location(full_path, function_name)
            if not location:
                return None

            func_source = provider.get_function_source(full_path, function_name)
            check_id = state.context_data.get("check_id", "")
            violation_context = provider.get_violation_context(
                full_path, function_name, check_id
            )

            result: dict[str, Any] = {
                "violating_function": function_name,
                "function_lines": f"{location[0]}-{location[1]}",
                "function_source": func_source,
            }

            if "error" not in violation_context:
                if violation_context.get("metrics"):
                    result["analysis"] = violation_context["metrics"]
                if violation_context.get("suggestions"):
                    result["extraction_suggestions"] = violation_context["suggestions"]
                if violation_context.get("strategy"):
                    result["fix_strategy"] = violation_context["strategy"]

            return result
        except Exception:
            return None

    def _maybe_refresh_context_for_new_function(
        self,
        output: str,
        file_path: str,
        state: "TaskState",
    ) -> None:
        """Check if output contains a new function name and refresh context."""
        from .utils import extract_function_name_from_output

        new_function = extract_function_name_from_output(output)
        if new_function and new_function != state.context_data.get("precomputed", {}).get("violating_function"):
            new_context = self._refresh_precomputed_context(file_path, new_function, state)
            if new_context:
                state.context_data["precomputed"] = new_context
                self.state_store.update_context_data(state.task_id, "precomputed", new_context)
