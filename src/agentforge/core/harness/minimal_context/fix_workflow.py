# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Minimal Context Fix Workflow
============================

Fix violation workflow using the minimal context architecture.
Each step is a fresh conversation with bounded context.

Features:
- Template-based context building (TemplateContextBuilder)
- AGENT.md configuration hierarchy
- Dynamic project fingerprints
- Full audit trail with context snapshots
- Progressive compaction for token efficiency

Test verification uses the violation's test_path field, which is computed
at violation detection time from:
1. Lineage metadata embedded in the source file (explicit, auditable)
2. Convention-based detection (fallback for legacy files)
"""

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

# Use the discovery provider as single source of truth for Python AST analysis
from ...discovery.providers.python_provider import PythonProvider

# Refactoring provider for validating extractions
from ...refactoring.registry import get_refactoring_provider
from ..conformance_tools import ConformanceTools
from ..git_tools import GitTools
from ..python_tools import PythonTools
from ..refactoring_tools import RefactoringTools
from ..test_runner_tools import RunnerTools
from ..violation_tools import ViolationTools
from .executor import AdaptiveBudget, MinimalContextExecutor, StepOutcome
from .phase_machine import PhaseMachine
from .state_store import Phase, TaskState, TaskStateStore
from .working_memory import WorkingMemoryManager


# Helper functions to reduce complexity in action methods
def _detect_source_indent(content_lines: list[str]) -> int:
    """Detect indentation of first non-empty line in content."""
    for line in content_lines:
        if line.strip():
            return len(line) - len(line.lstrip())
    return 0


def _adjust_content_indentation(
    content_lines: list[str], target_indent: int, source_indent: int
) -> list[str]:
    """Adjust content lines to match target indentation."""
    indent_delta = target_indent - source_indent
    result = []
    for line in content_lines:
        if line.strip():
            current_indent = len(line) - len(line.lstrip())
            new_indent = max(0, current_indent + indent_delta)
            result.append(' ' * new_indent + line.lstrip())
        else:
            result.append('')
    return result


def _validate_replace_params(
    file_path: str | None, start_line: int | None, end_line: int | None, new_content: str | None
) -> str | None:
    """Validate replace_lines parameters. Returns error message or None."""
    if not file_path:
        return "Missing file_path"
    if start_line is None or end_line is None:
        return "Missing start_line or end_line"
    if new_content is None:
        return "Missing new_content"
    return None


def _validate_insert_params(
    file_path: str | None, line_number: int | None, new_content: str | None
) -> str | None:
    """Validate insert_lines parameters. Returns error message or None."""
    if not file_path:
        return "Missing file_path"
    if line_number is None:
        return "Missing line_number"
    if new_content is None:
        return "Missing new_content"
    return None


def _extract_function_name_from_output(output: str) -> str | None:
    """Extract function name from check output using known patterns."""
    import re
    patterns = [
        r"Function '([^']+)' has complexity \d+",
        r"Function '([^']+)' has \d+ lines",
        r"Function '([^']+)' has nesting depth \d+",
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return None


class MinimalContextFixWorkflow:
    """
    Fix violation workflow using minimal context architecture v2.

    Key differences from FixViolationWorkflow:
    - State persisted to disk, not in memory
    - Each step is a fresh 2-message conversation
    - Token usage bounded regardless of step count
    - Resumable after crashes

    V2 Architecture features (always enabled):
    - TemplateContextBuilder with task-type specific templates
    - AGENT.md configuration hierarchy
    - Dynamic project fingerprinting
    - Full audit trail with context snapshots
    - Progressive compaction for token efficiency
    - PhaseMachine for explicit phase transitions with guards
    - Enhanced loop detection with semantic analysis
    - Fact extraction from tool outputs instead of raw data
    - Targets ~4000 tokens per step
    """

    def __init__(
        self,
        project_path: Path,
        base_iterations: int = 15,
        max_iterations: int = 50,
        require_commit_approval: bool = True,
    ):
        """
        Initialize workflow.

        Args:
            project_path: Project root
            base_iterations: Initial step budget (extends with progress)
            max_iterations: Hard ceiling for steps (cost control)
            require_commit_approval: Require human approval for commits
        """
        self.project_path = Path(project_path)
        self.base_iterations = base_iterations
        self.max_iterations = max_iterations
        self.require_commit_approval = require_commit_approval

        # Initialize state store
        self.state_store = TaskStateStore(project_path)

        # Initialize tools
        self.violation_tools = ViolationTools(project_path)
        self.conformance_tools = ConformanceTools(project_path)
        self.git_tools = GitTools(project_path, require_approval=require_commit_approval)
        self.test_tools = RunnerTools(project_path)
        self.python_tools = PythonTools(project_path)
        self.refactoring_tools = RefactoringTools(project_path)

        # Build action executors
        self.action_executors = self._build_action_executors()

        # Create executor with template-based context building
        # Provides: AGENT.md config, fingerprints, templates, audit logging
        self.executor = MinimalContextExecutor(
            project_path=project_path,
            task_type="fix_violation",
            compaction_enabled=True,
            audit_enabled=True,
        )

        # Register action executors with the executor
        self.executor.register_actions(self.action_executors)

        # Share state store between workflow and executor
        # This ensures task state is shared across all components
        self.executor.state_store = self.state_store
        self.executor.context_builder.state_store = self.state_store

    def _build_action_executors(self) -> dict[str, Callable]:
        """Build action executors for all tools."""
        executors = {}

        # Wrap tool executors to match action executor signature
        def wrap_tool_executor(tool_executor):
            def wrapper(action_name: str, params: dict[str, Any], state: TaskState):
                result = tool_executor(action_name, params)
                return {
                    "status": "success" if result.success else "failure",
                    "summary": result.output[:200] if result.output else "",
                    "error": result.error if hasattr(result, "error") else None,
                    "output": result.output,
                }
            return wrapper

        # Register tool executors
        for name, executor in self.violation_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.conformance_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.git_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.test_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.python_tools.get_tool_executors().items():
            executors[name] = wrap_tool_executor(executor)

        for name, executor in self.refactoring_tools.get_tool_executors().items():
            if name == "extract_function":
                # Special handling for extract_function: auto-run check after success
                executors[name] = self._wrap_extract_function(executor)
            else:
                executors[name] = wrap_tool_executor(executor)

        # Add file read/edit actions - WRAPPED with test verification
        # These actions can break tests, so we verify after each modification
        executors["read_file"] = self._action_read_file  # read-only, no wrap needed
        executors["edit_file"] = self._with_test_verification(self._action_edit_file)
        executors["replace_lines"] = self._with_test_verification(self._action_replace_lines)
        executors["insert_lines"] = self._with_test_verification(self._action_insert_lines)
        executors["write_file"] = self._with_test_verification(self._action_write_file)
        executors["run_check"] = self._action_run_check
        executors["run_tests"] = self._action_run_tests
        executors["load_context"] = self._action_load_context
        executors["plan_fix"] = self._action_plan_fix

        return executors

    def _track_modified_file(self, state: TaskState, file_path: str) -> None:
        """Track a modified file in state context."""
        if "files_modified" not in state.context_data:
            state.context_data["files_modified"] = []
        if file_path not in state.context_data["files_modified"]:
            state.context_data["files_modified"].append(file_path)
            self.state_store.update_context_data(
                state.task_id, "files_modified", state.context_data["files_modified"]
            )

    def _save_file_for_revert(self, file_path: str | None) -> tuple[str | None, bool]:
        """Save file content for potential revert. Returns (content, existed)."""
        if not file_path:
            return None, False
        full_path = self.project_path / file_path
        if full_path.exists():
            return full_path.read_text(), True
        return None, False

    def _revert_file_changes(
        self, file_path: str | None, original_content: str | None, file_existed: bool
    ) -> None:
        """Revert file to original state."""
        if not file_path:
            return
        full_path = self.project_path / file_path
        if original_content is not None:
            full_path.write_text(original_content)
        elif not file_existed and full_path.exists():
            full_path.unlink()

    def _build_test_revert_result(
        self, test_path: str | None, baseline_failures: int,
        after_failures: int, after_output: str
    ) -> dict[str, Any]:
        """Build failure result for reverted test failure."""
        return {
            "status": "failure",
            "error": "Modification broke tests - REVERTED",
            "summary": "✗ REVERTED - tests got worse",
            "output": (
                f"--- CORRECTNESS CHECK FAILED ---\n"
                f"✗ Modification introduced new test failures - changes REVERTED\n\n"
                f"Test path: {test_path or 'all tests'}\n"
                f"Before: {baseline_failures} failures\n"
                f"After: {after_failures} failures\n\n"
                f"Test output:\n{after_output[:800] if after_output else 'No output'}\n\n"
                f"The change was syntactically valid but broke behavior.\n"
                f"Original file content has been restored.\n"
                f"Try a different approach that preserves existing functionality."
            ),
        }

    def _with_test_verification(self, action_fn: Callable) -> Callable:
        """
        Wrap a file-modifying action with test verification and auto-revert.

        CORRECTNESS FIRST principle: We cannot go from "violation" to "broken".
        """
        def wrapper(action_name: str, params: dict[str, Any], state: TaskState) -> dict[str, Any]:
            file_path = params.get("path") or params.get("file_path") or state.context_data.get("file_path")
            test_path = state.context_data.get("test_path")

            # Run baseline tests
            baseline_result = self.test_tools.run_tests(
                "run_tests", {"test_path": test_path} if test_path else {}
            )
            baseline_failures = self._count_test_failures(baseline_result.output)

            original_content, file_existed = self._save_file_for_revert(file_path)
            result = action_fn(action_name, params, state)

            if result.get("status") == "failure":
                return result

            after_result = self.test_tools.run_tests(
                "run_tests", {"test_path": test_path} if test_path else {}
            )
            after_failures = self._count_test_failures(after_result.output)

            tests_got_worse = (
                (baseline_result.success and not after_result.success) or
                (after_failures > baseline_failures)
            )

            if tests_got_worse:
                self._revert_file_changes(file_path, original_content, file_existed)
                return self._build_test_revert_result(
                    test_path, baseline_failures, after_failures, after_result.output
                )

            test_status = "✓ Tests verified" if after_result.success else "○ No new failures"
            result["summary"] = f"{result.get('summary', '')} | {test_status}"
            result["output"] = (
                f"{result.get('output', '')}\n\n"
                f"--- CORRECTNESS VERIFIED ---\n"
                f"{test_status} (tested: {test_path or 'all'}, before: {baseline_failures}, after: {after_failures})"
            )

            return result

        return wrapper

    def _validate_python_file(self, file_path: Path) -> str | None:
        """
        Validate a Python file for syntax and import errors.

        Returns None if valid, or an error message if invalid.
        This catches:
        1. Syntax errors (ast.parse)
        2. Undefined names at module level (import check)

        This is a FAST check that runs before the slower test verification.
        """
        import ast
        import sys

        if file_path.suffix != '.py':
            return None  # Only validate Python files

        if not file_path.exists():
            return f"File does not exist: {file_path}"

        try:
            source = file_path.read_text()
        except Exception as e:
            return f"Cannot read file: {e}"

        # Step 1: Check syntax with ast.parse
        try:
            ast.parse(source)
        except SyntaxError as e:
            return f"Syntax error at line {e.lineno}: {e.msg}"

        # Step 2: Try to compile and import to catch undefined names
        # We use subprocess to avoid polluting the current process
        module_path = str(file_path.resolve())

        # Create a test script that imports the module
        check_script = f'''
import sys
import importlib.util
try:
    spec = importlib.util.spec_from_file_location("_check_module", {repr(module_path)})
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("OK")
except AttributeError as e:
    print(f"AttributeError: {{e}}")
    sys.exit(1)
except NameError as e:
    print(f"NameError: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"{{type(e).__name__}}: {{e}}")
    sys.exit(1)
'''

        try:
            result = subprocess.run(
                [sys.executable, "-c", check_script],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.project_path),
                env={**subprocess.os.environ, "PYTHONPATH": str(self.project_path)}
            )

            if result.returncode != 0:
                error_msg = result.stdout.strip() or result.stderr.strip()
                return f"Import validation failed: {error_msg}"

        except subprocess.TimeoutExpired:
            return "Import validation timed out"
        except Exception:
            # If subprocess fails, fall back to just syntax check (already passed)
            pass

        return None  # All validations passed

    def _format_focused_read(
        self, lines: list[str], violation_line: int, path: str
    ) -> tuple[str, str]:
        """Format a focused read around violation line. Returns (content, summary)."""
        start_line = max(0, violation_line - 30)
        end_line = min(len(lines), violation_line + 70)
        focused_lines = lines[start_line:end_line]
        numbered = [f"{i + start_line + 1:4d}: {line}" for i, line in enumerate(focused_lines)]
        content = "\n".join(numbered)
        summary = f"Read {path} lines {start_line+1}-{end_line} (violation at line {violation_line})"
        return content, summary

    def _format_generic_read(
        self, lines: list[str], total_chars: int, path: str
    ) -> tuple[str, str]:
        """Format a generic file read. Returns (content, summary)."""
        numbered = [f"{i+1:4d}: {line}" for i, line in enumerate(lines[:100])]
        content = "\n".join(numbered)
        if len(lines) > 100:
            content += f"\n... [{len(lines) - 100} more lines]"
        summary = f"Read {total_chars} chars from {path}"
        return content, summary

    def _action_read_file(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Read a file, focusing on the violation area if known."""
        path = params.get("path") or params.get("file_path")
        if not path:
            return {"status": "failure", "error": "No path specified"}

        full_path = self.project_path / path
        if not full_path.exists():
            return {"status": "failure", "error": f"File not found: {path}"}

        try:
            content = full_path.read_text()
            lines = content.split("\n")

            violation_line = state.context_data.get("line_number")
            violation_file = state.context_data.get("file_path")
            is_violation_file = violation_line and violation_file and path == violation_file

            if is_violation_file:
                output_content, summary = self._format_focused_read(lines, violation_line, path)
            else:
                output_content, summary = self._format_generic_read(lines, len(content), path)

            # Store in working memory
            task_dir = self.state_store._task_dir(state.task_id)
            memory = WorkingMemoryManager(task_dir)
            memory.load_context(
                f"full_file:{path}", output_content[:5000], state.current_step, expires_after_steps=2
            )

            return {"status": "success", "summary": summary, "output": output_content[:3000]}
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def _action_edit_file(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Edit a file with fuzzy whitespace matching."""
        path = params.get("path") or params.get("file_path") or state.context_data.get("file_path")
        old_text = params.get("old_text")
        new_text = params.get("new_text")

        if not path:
            return {"status": "failure", "error": "No path specified"}
        if old_text is None or new_text is None:
            return {"status": "failure", "error": "old_text and new_text required"}

        full_path = self.project_path / path
        if not full_path.exists():
            return {"status": "failure", "error": f"File not found: {path}"}

        try:
            content = full_path.read_text()

            # Try exact match first
            if old_text in content:
                new_content = content.replace(old_text, new_text, 1)
                full_path.write_text(new_content)
            else:
                # Try fuzzy match with whitespace normalization
                match_result = self._fuzzy_find_and_replace(content, old_text, new_text)
                if match_result is None:
                    # Show what we were looking for to help debugging
                    old_preview = old_text[:100].replace('\n', '\\n')
                    return {
                        "status": "failure",
                        "error": f"old_text not found in file. Looking for: {old_preview}..."
                    }
                new_content = match_result
                full_path.write_text(new_content)

            self._track_modified_file(state, path)

            return {
                "status": "success",
                "summary": f"Edited {path}: replaced {len(old_text)} chars with {len(new_text)} chars",
            }
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def _fuzzy_find_and_replace(
        self, content: str, old_text: str, new_text: str
    ) -> str | None:
        """
        Find old_text in content with fuzzy whitespace matching.

        Strategy:
        1. Normalize both to find the match location
        2. Find the actual text span in the original
        3. Replace with properly indented new_text
        """

        # Normalize whitespace for matching
        def normalize(s: str) -> str:
            # Replace leading whitespace on each line with a marker
            lines = s.split('\n')
            return '\n'.join(line.lstrip() for line in lines)

        norm_content = normalize(content)
        norm_old = normalize(old_text)

        if norm_old not in norm_content:
            return None

        # Find where the normalized text appears
        norm_start = norm_content.find(norm_old)

        # Map back to original content by counting newlines
        content_lines = content.split('\n')
        norm_lines_before = norm_content[:norm_start].count('\n')

        # Find the actual start line in original content
        start_line = norm_lines_before

        # Count how many lines in old_text
        old_lines = old_text.strip().split('\n')
        num_lines = len(old_lines)

        # Detect indentation from the first line of the match
        if start_line < len(content_lines):
            actual_line = content_lines[start_line]
            leading_spaces = len(actual_line) - len(actual_line.lstrip())
            base_indent = ' ' * leading_spaces
        else:
            base_indent = ''

        # Re-indent new_text to match
        new_lines = new_text.strip().split('\n')
        if new_lines:
            # Detect the indentation in new_text
            first_new_line = new_lines[0]
            new_indent = len(first_new_line) - len(first_new_line.lstrip())

            # Adjust each line
            adjusted_lines = []
            for line in new_lines:
                if line.strip():
                    line_indent = len(line) - len(line.lstrip())
                    relative_indent = line_indent - new_indent
                    adjusted_lines.append(base_indent + ' ' * max(0, relative_indent) + line.lstrip())
                else:
                    adjusted_lines.append('')

            new_text_adjusted = '\n'.join(adjusted_lines)
        else:
            new_text_adjusted = new_text

        # Replace the lines
        result_lines = (
            content_lines[:start_line] +
            new_text_adjusted.split('\n') +
            content_lines[start_line + num_lines:]
        )

        return '\n'.join(result_lines)

    def _action_replace_lines(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """
        Replace lines in a file by line number.

        This is more robust than text-based replacement because
        line numbers are unambiguous.

        Parameters:
            file_path: Path to the file
            start_line: First line to replace (1-indexed, inclusive)
            end_line: Last line to replace (1-indexed, inclusive)
            new_content: New content to insert (will be auto-indented)
        """
        file_path = params.get("file_path") or params.get("path") or state.context_data.get("file_path")
        start_line = params.get("start_line")
        end_line = params.get("end_line")
        new_content = params.get("new_content")

        # Validate parameters using helper
        if error := _validate_replace_params(file_path, start_line, end_line, new_content):
            return {"status": "failure", "error": error}

        full_path = self.project_path / file_path
        if not full_path.exists():
            return {"status": "failure", "error": f"File not found: {file_path}"}

        try:
            original_content = full_path.read_text()
            lines = original_content.split('\n')

            # Validate line range
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return {
                    "status": "failure",
                    "error": f"Invalid line range {start_line}-{end_line} (file has {len(lines)} lines)"
                }

            # Detect and adjust indentation using helpers
            original_line = lines[start_line - 1]
            target_indent = len(original_line) - len(original_line.lstrip())
            content_lines = new_content.split('\n')
            source_indent = _detect_source_indent(content_lines)
            new_lines = _adjust_content_indentation(content_lines, target_indent, source_indent)

            # Replace lines
            result_lines = lines[:start_line - 1] + new_lines + lines[end_line:]
            new_source = '\n'.join(result_lines)

            full_path.write_text(new_source)

            # VALIDATION: Check that the modified file is still valid Python
            validation_error = self._validate_python_file(full_path)
            if validation_error:
                # Rollback: restore original content
                full_path.write_text(original_content)
                return {
                    "status": "failure",
                    "error": f"Code validation failed - REVERTED: {validation_error}",
                    "summary": "✗ REVERTED - code validation failed",
                }

            self._track_modified_file(state, file_path)

            return {
                "status": "success",
                "summary": f"Replaced lines {start_line}-{end_line} with {len(new_lines)} new lines",
            }

        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def _detect_insert_indentation(
        self, lines: list[str], line_number: int, explicit_indent: int | None
    ) -> int:
        """Detect indentation level for insert operation."""
        if explicit_indent is not None:
            return explicit_indent
        context_line = lines[line_number - 1] if line_number <= len(lines) else ""
        if context_line.strip():
            return len(context_line) - len(context_line.lstrip())
        return 0

    def _process_insert_content(self, content: str, indent_str: str) -> list[str]:
        """Process and indent content for insertion."""
        new_lines = []
        for line in content.split('\n'):
            if line.strip():
                stripped = line.lstrip()
                line_indent = len(line) - len(stripped)
                indented = indent_str + ' ' * line_indent + stripped if line_indent else indent_str + stripped
                new_lines.append(indented)
            else:
                new_lines.append('')
        if new_lines and new_lines[-1].strip():
            new_lines.append('')
        return new_lines

    def _action_insert_lines(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Insert lines into a file at a specific line number."""
        file_path = params.get("file_path") or params.get("path") or state.context_data.get("file_path")
        line_number = params.get("line_number") or params.get("before_line")
        new_content = params.get("new_content") or params.get("content")

        # Validate parameters using helper
        if error := _validate_insert_params(file_path, line_number, new_content):
            return {"status": "failure", "error": error}

        full_path = self.project_path / file_path
        if not full_path.exists():
            return {"status": "failure", "error": f"File not found: {file_path}"}

        try:
            lines = full_path.read_text().split('\n')

            if line_number < 1 or line_number > len(lines) + 1:
                return {"status": "failure", "error": f"Invalid line number {line_number} (file has {len(lines)} lines)"}

            indent_level = self._detect_insert_indentation(lines, line_number, params.get("indent_level"))
            new_lines = self._process_insert_content(new_content, ' ' * indent_level)

            insert_index = line_number - 1
            result_lines = lines[:insert_index] + new_lines + lines[insert_index:]
            full_path.write_text('\n'.join(result_lines))

            self._track_modified_file(state, file_path)

            return {"status": "success", "summary": f"Inserted {len(new_lines)} lines before line {line_number}"}

        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def _action_write_file(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """
        Write/create a file with the given content.

        Parameters:
            path: Path to the file (relative to project)
            content: Content to write to the file
        """
        path = params.get("path") or params.get("file_path")
        content = params.get("content")

        if not path:
            return {"status": "failure", "error": "Missing required parameter: path"}
        if content is None:
            return {"status": "failure", "error": "Missing required parameter: content"}

        try:
            full_path = self.project_path / path

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists (for message)
            is_new = not full_path.exists()

            # Write the content
            full_path.write_text(content)

            if is_new:
                return {
                    "status": "success",
                    "summary": f"Created new file: {path} ({len(content)} chars)",
                }
            else:
                return {
                    "status": "success",
                    "summary": f"Overwrote file: {path} ({len(content)} chars)",
                }

        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def _check_tests_worsened(self, baseline_result, after_result) -> bool:
        """Check if tests got worse after an operation."""
        if baseline_result.success and not after_result.success:
            return True
        if not baseline_result.success and not after_result.success:
            baseline_failures = self._count_test_failures(baseline_result.output)
            after_failures = self._count_test_failures(after_result.output)
            return after_failures > baseline_failures
        return False

    def _build_revert_result(
        self, file_path: str, original_content: str | None, result, after_result
    ) -> dict[str, Any]:
        """Revert file and build failure result."""
        if original_content is not None:
            full_path = self.project_path / file_path
            full_path.write_text(original_content)

        return {
            "status": "failure",
            "error": "Extraction broke tests - REVERTED",
            "output": (
                f"{result.output}\n\n"
                f"--- CORRECTNESS CHECK FAILED ---\n"
                f"✗ Extraction introduced new test failures - changes REVERTED\n"
                f"Test output: {after_result.output[:500] if after_result.output else 'No output'}\n"
                f"The extraction was syntactically valid but broke behavior.\n"
                f"Try a different extraction range or approach."
            ),
            "summary": "✗ REVERTED - new test failures",
        }

    def _update_verification_and_context(
        self, state: TaskState, file_path: str, params: dict,
        check_result, after_result, baseline_passed: bool
    ) -> None:
        """Update verification status and refresh context."""
        checks_passing = check_result.success
        self.state_store.update_verification(
            state.task_id,
            checks_passing=1 if checks_passing else 0,
            checks_failing=0 if checks_passing else 1,
            tests_passing=after_result.success,
            details={
                "last_check": check_result.output[:500] if check_result.output else "",
                "tests_verified": True,
                "baseline_passed": baseline_passed,
            },
        )

        source_function = params.get("source_function")
        if source_function:
            new_context = self._refresh_precomputed_context(file_path, source_function, state)
            if new_context:
                state.context_data["precomputed"] = new_context
                self.state_store.update_context_data(state.task_id, "precomputed", new_context)

    def _wrap_extract_function(self, tool_executor: Callable) -> Callable:
        """
        Wrap extract_function to enforce CORRECTNESS FIRST:
        1. Run tests BEFORE extraction to establish baseline
        2. Save original content before extraction
        3. Run extraction (syntax validated by tool)
        4. RUN TESTS AFTER - if MORE tests fail than before, REVERT
        5. Only then run conformance check
        6. Refresh context with new line numbers
        """
        def wrapper(action_name: str, params: dict[str, Any], state: TaskState):
            file_path = params.get("file_path") or state.context_data.get("file_path")
            baseline_result = self.test_tools.run_tests("run_tests", {})

            # Save original content before any changes
            original_content = None
            if file_path:
                full_path = self.project_path / file_path
                if full_path.exists():
                    original_content = full_path.read_text()

            result = tool_executor(action_name, params)
            base_result = {
                "status": "success" if result.success else "failure",
                "summary": result.output[:200] if result.output else "",
                "error": result.error if hasattr(result, "error") else None,
                "output": result.output,
            }

            if not (result.success and file_path):
                return base_result

            after_result = self.test_tools.run_tests("run_tests", {})
            if self._check_tests_worsened(baseline_result, after_result):
                return self._build_revert_result(file_path, original_content, result, after_result)

            check_id = state.context_data.get("check_id")
            if not check_id:
                return base_result

            check_result = self.conformance_tools.run_conformance_check(
                "run_conformance_check", {"check_id": check_id, "file_path": file_path}
            )
            self._update_verification_and_context(
                state, file_path, params, check_result, after_result, baseline_result.success
            )

            checks_passing = check_result.success
            check_status = "✓ Check PASSED" if checks_passing else "○ Check still failing"
            check_summary = check_result.output[:300] if check_result.output else ""
            base_result["output"] = (
                f"{base_result['output']}\n\n"
                f"--- CORRECTNESS VERIFIED ---\n"
                f"✓ No new failures\n\n"
                f"--- Conformance Check ---\n"
                f"{check_status}\n{check_summary}"
            )
            base_result["summary"] = f"{base_result['summary']} | ✓ No new failures | {check_status}"

            if checks_passing:
                base_result["hint"] = "All checks passed! You can now use 'complete' action."

            return base_result
        return wrapper

    def _count_test_failures(self, output: str) -> int:
        """Extract failure count from pytest output."""
        import re
        if not output:
            return 0
        # Match patterns like "1 failed" or "5 failed"
        match = re.search(r'(\d+) failed', output)
        if match:
            return int(match.group(1))
        return 0

    def _action_run_check(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Run conformance check - uses targeted check when check_id available."""
        file_path = params.get("file_path") or params.get("path") or state.context_data.get("file_path")
        check_id = params.get("check_id") or state.context_data.get("check_id")

        # Run appropriate check based on available parameters
        result = self._run_conformance_check(check_id, file_path)

        # Update verification status
        passing = result.success
        self.state_store.update_verification(
            state.task_id,
            checks_passing=1 if passing else 0,
            checks_failing=0 if passing else 1,
            tests_passing=state.verification.tests_passing,
            details={"last_check": result.output[:500]},
        )

        # If check failed, refresh context with updated line numbers
        if not passing and result.output and file_path:
            self._maybe_refresh_context_for_new_function(result.output, file_path, state)

        return {
            "status": "success" if passing else "partial",
            "summary": result.output[:200],
            "output": result.output,
        }

    def _run_conformance_check(self, check_id: str | None, file_path: str | None):
        """Run appropriate conformance check based on available parameters."""
        if check_id and file_path:
            return self.conformance_tools.run_conformance_check(
                "run_conformance_check",
                {"check_id": check_id, "file_path": file_path}
            )
        if file_path:
            return self.conformance_tools.check_file("check_file", {"file_path": file_path})
        return self.conformance_tools.run_full_check("run_full_check", {})

    def _maybe_refresh_context_for_new_function(
        self, output: str, file_path: str, state: TaskState
    ) -> None:
        """Refresh context if output indicates a new function to fix."""
        new_function_name = _extract_function_name_from_output(output)
        if not new_function_name:
            return

        new_context = self._refresh_precomputed_context(file_path, new_function_name, state)
        if new_context:
            state.context_data["precomputed"] = new_context
            self.state_store.update_context_data(state.task_id, "precomputed", new_context)

    def _refresh_precomputed_context(
        self,
        file_path: str,
        function_name: str,
        state: TaskState,
    ) -> dict[str, Any] | None:
        """Refresh pre-computed context for a new function after extraction.

        Uses PythonProvider with violation-type-specific context.
        """
        full_path = self.project_path / file_path
        if not full_path.exists():
            return None

        try:
            provider = PythonProvider()

            # Get function location
            location = provider.get_function_location(full_path, function_name)
            if not location:
                return None

            # Get function source
            func_source = provider.get_function_source(full_path, function_name)

            # Get the check_id from state to provide violation-specific context
            check_id = state.context_data.get("check_id", "")

            # Get violation-type-specific context
            violation_context = provider.get_violation_context(
                full_path, function_name, check_id
            )

            result = {
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

    def _action_run_tests(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Run tests."""
        path = params.get("path")
        if path:
            result = self.test_tools.run_single_test("run_single_test", {"test_path": path})
        else:
            # Run affected tests based on modified files
            files = state.context_data.get("files_modified", [])
            if files:
                result = self.test_tools.run_affected_tests("run_affected_tests", {"files": files})
            else:
                result = self.test_tools.run_tests("run_tests", {})

        # Update verification status
        tests_passed = result.success
        self.state_store.update_verification(
            state.task_id,
            checks_passing=state.verification.checks_passing,
            checks_failing=state.verification.checks_failing,
            tests_passing=tests_passed,
            details={"last_test": result.output[:500]},
        )

        return {
            "status": "success" if tests_passed else "failure",
            "summary": result.output[:200],
            "output": result.output,
        }

    def _action_load_context(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Load additional context into working memory."""
        # Support multiple parameter formats
        item = params.get("item", "")
        path = params.get("path") or params.get("file_path") or params.get("file")

        # If path provided directly, treat as file load
        if path:
            item = f"full_file:{path}"

        # If no item specified, try to infer from other params
        if not item:
            # Maybe they passed a query - redirect to read_file
            query = params.get("query", "")
            if query:
                # Try to extract a file path from query
                return {"status": "failure", "error": "Use 'read_file' action to read files, not 'load_context'. Try: read_file with path parameter."}

        task_dir = self.state_store._task_dir(state.task_id)
        memory = WorkingMemoryManager(task_dir)

        if item.startswith("full_file:"):
            path = item[10:]
            full_path = self.project_path / path
            if full_path.exists():
                content = full_path.read_text()
                memory.load_context(item, content[:5000], state.current_step, expires_after_steps=3)
                return {"status": "success", "summary": f"Loaded {path} into context"}
            else:
                return {"status": "failure", "error": f"File not found: {path}"}

        return {"status": "failure", "error": "Unknown context item format. Use 'read_file' to read files or 'load_context' with item='full_file:path/to/file.py'"}

    def _action_plan_fix(
        self,
        action_name: str,
        params: dict[str, Any],
        state: TaskState,
    ) -> dict[str, Any]:
        """Record fix plan and advance to implement phase."""
        diagnosis = params.get("diagnosis", "")
        approach = params.get("approach", "")

        self.state_store.update_context_data(state.task_id, "diagnosis", diagnosis)
        self.state_store.update_context_data(state.task_id, "approach", approach)
        self.state_store.update_phase(state.task_id, Phase.IMPLEMENT)

        return {
            "status": "success",
            "summary": f"Plan recorded: {approach[:100]}",
        }

    def _read_source_file(self, full_path: Path) -> tuple[str, list[str]] | None:
        """Read source file and return (source, lines) or None on error."""
        try:
            source = full_path.read_text()
            return source, source.split('\n')
        except Exception:
            return None

    def _find_violating_function(
        self, tree, line_number: int | None, num_lines: int
    ) -> str | None:
        """Find the function containing the violation line."""
        import ast
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if line_number and node.lineno <= line_number <= (node.end_lineno or num_lines):
                    return node.name
        return None

    def _add_provider_context(
        self, precomputed: dict, provider: PythonProvider,
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
        self, precomputed: dict, tree, func_name: str
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

    def _add_python_context(
        self, precomputed: dict, full_path: Path, lines: list[str],
        line_number: int | None, check_id: str
    ) -> None:
        """Add Python-specific context using AST analysis."""
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

    def _validate_extraction_suggestions(
        self,
        file_path: Path,
        suggestions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Validate extraction suggestions with the refactoring provider.

        Uses rope (for Python) to verify each suggested extraction is actually
        possible without breaking control flow. This prevents the agent from
        repeatedly attempting invalid extractions.

        Args:
            file_path: Path to the source file
            suggestions: List of extraction suggestions with start_line/end_line

        Returns:
            List of validated suggestions (only those that can actually be extracted)
        """
        provider = get_refactoring_provider(file_path, self.project_path)
        if provider is None:
            # No refactoring provider for this file type - return suggestions as-is
            return suggestions

        validated = []
        try:
            for suggestion in suggestions:
                start_line = suggestion.get("start_line")
                end_line = suggestion.get("end_line")

                if start_line is None or end_line is None:
                    continue

                # Check if rope can extract this range
                can_extract = provider.can_extract_function(
                    file_path, start_line, end_line
                )

                if can_extract.can_extract:
                    # Add validation status to suggestion
                    suggestion["validated"] = True
                    validated.append(suggestion)
                else:
                    # Log why it was rejected (for debugging)
                    # but don't include in suggestions to agent
                    pass
        finally:
            provider.close()

        return validated

    def fix_violation(
        self,
        violation_id: str,
        on_step: Callable[[StepOutcome], None] | None = None,
    ) -> dict[str, Any]:
        """
        Attempt to fix a violation using minimal context architecture.

        Args:
            violation_id: Violation ID to fix
            on_step: Optional callback after each step

        Returns:
            Dict with fix results
        """

        # Normalize violation ID
        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"

        # Read violation data directly from YAML (structured, auditable)
        violations_dir = self.project_path / ".agentforge" / "violations"
        violation_file = violations_dir / f"{violation_id}.yaml"

        if not violation_file.exists():
            return {
                "success": False,
                "error": f"Violation not found: {violation_id}",
                "violation_id": violation_id,
            }

        try:
            with open(violation_file) as f:
                violation_data = yaml.safe_load(f)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read violation YAML: {e}",
                "violation_id": violation_id,
            }

        # Extract structured context from YAML
        violation_context = {
            "violation_id": violation_data.get("violation_id", violation_id),
            "check_id": violation_data.get("check_id"),
            "file_path": violation_data.get("file_path"),
            "line_number": violation_data.get("line_number"),
            "severity": violation_data.get("severity"),
            "message": violation_data.get("message"),
            "fix_hint": violation_data.get("fix_hint"),
            "contract_id": violation_data.get("contract_id"),
        }

        # Pre-compute rich context using deterministic tools (no LLM)
        # This gives the agent everything it needs to make good edits
        precomputed = self._precompute_violation_context(violation_data)

        # Build context_data with both violation info and pre-computed analysis
        context_data = {
            # Basic violation info
            "violation_id": violation_id,
            "check_id": violation_context.get("check_id"),
            "file_path": violation_context.get("file_path"),
            "line_number": violation_context.get("line_number"),
            "severity": violation_context.get("severity"),
            "message": violation_context.get("message"),
            "fix_hint": violation_context.get("fix_hint"),
            "contract_id": violation_context.get("contract_id"),
            # Test path for verification (from lineage metadata or convention fallback)
            "test_path": violation_data.get("test_path"),
            # Pre-computed analysis (from AST, not LLM)
            "precomputed": precomputed,
        }

        # Create task in state store
        task_state = self.state_store.create_task(
            task_type="fix_violation",
            goal=f"Fix conformance violation {violation_id}",
            success_criteria=[
                "Conformance check passes for the affected file",
                "All existing tests continue to pass",
                "Minimal changes made to fix the issue",
            ],
            constraints=[
                "Only modify files directly related to the violation",
                "Follow existing code patterns",
                "Do not introduce new violations",
            ],
            context_data=context_data,
            task_id=f"fix-{violation_id}",
        )

        # Initialize PhaseMachine for enhanced phase transitions (Phase 4)
        phase_machine = PhaseMachine()
        task_state.set_phase_machine(phase_machine)
        self.state_store._save_state(task_state)

        # If we have precomputed function_source, seed a CODE_STRUCTURE fact
        # This allows the phase machine to transition directly to IMPLEMENT
        if precomputed.get("function_source"):
            task_dir = self.state_store._task_dir(task_state.task_id)
            memory_manager = WorkingMemoryManager(task_dir)
            memory_manager.add_fact(
                fact_id="precomputed_structure",
                category="code_structure",
                statement=f"Function '{precomputed.get('violating_function', 'target')}' analyzed: {precomputed.get('function_lines', 'lines known')}",
                confidence=1.0,
                source="precomputed_analysis",
                step=0,
            )

        # Run until complete with adaptive budget
        budget = AdaptiveBudget(
            base_budget=self.base_iterations,
            max_budget=self.max_iterations,
        )
        outcomes = self.executor.run_until_complete(
            task_id=task_state.task_id,
            max_iterations=self.max_iterations,
            on_step=on_step,
            adaptive_budget=budget,
        )

        # Load final state
        final_state = self.state_store.load(task_state.task_id)

        return {
            "success": final_state.phase == Phase.COMPLETE,
            "violation_id": violation_id,
            "task_id": task_state.task_id,
            "phase": final_state.phase.value,
            "steps_taken": len(outcomes),
            "total_tokens": sum(o.tokens_used for o in outcomes),
            "files_modified": final_state.context_data.get("files_modified", []),
            "tests_passed": final_state.verification.tests_passing,
            "conformance_passed": final_state.verification.checks_failing == 0,
            "error": final_state.error,
        }

    def resume_task(
        self,
        task_id: str,
        on_step: Callable[[StepOutcome], None] | None = None,
    ) -> dict[str, Any]:
        """
        Resume an existing task.

        Args:
            task_id: Task ID to resume
            on_step: Optional callback after each step

        Returns:
            Dict with fix results
        """
        state = self.state_store.load(task_id)
        if not state:
            return {
                "success": False,
                "error": f"Task not found: {task_id}",
            }

        if state.phase in [Phase.COMPLETE, Phase.FAILED, Phase.ESCALATED]:
            return {
                "success": state.phase == Phase.COMPLETE,
                "task_id": task_id,
                "phase": state.phase.value,
                "error": "Task already complete",
            }

        # Continue execution with adaptive budget
        remaining_budget = max(self.base_iterations, self.max_iterations - state.current_step)
        budget = AdaptiveBudget(
            base_budget=self.base_iterations,
            max_budget=remaining_budget,
        )
        outcomes = self.executor.run_until_complete(
            task_id=task_id,
            max_iterations=remaining_budget,
            on_step=on_step,
            adaptive_budget=budget,
        )

        # Load final state
        final_state = self.state_store.load(task_id)

        return {
            "success": final_state.phase == Phase.COMPLETE,
            "task_id": task_id,
            "phase": final_state.phase.value,
            "steps_taken": len(outcomes),
            "total_tokens": sum(o.tokens_used for o in outcomes),
            "files_modified": final_state.context_data.get("files_modified", []),
            "tests_passed": final_state.verification.tests_passing,
            "conformance_passed": final_state.verification.checks_failing == 0,
            "error": final_state.error,
        }


def create_minimal_fix_workflow(
    project_path: Path,
    require_commit_approval: bool = True,
    base_iterations: int = 15,
    max_iterations: int = 50,
) -> MinimalContextFixWorkflow:
    """
    Factory function to create a MinimalContextFixWorkflow using v2 architecture.

    V2 Architecture features are always enabled:
    - TemplateContextBuilder with task-type specific templates
    - AGENT.md configuration hierarchy
    - Dynamic project fingerprinting
    - Full audit trail with context snapshots
    - Progressive compaction for token efficiency
    - PhaseMachine for phase transitions
    - Enhanced loop detection

    Args:
        project_path: Project root directory
        require_commit_approval: Require human approval for commits
        base_iterations: Initial step budget (extends with progress)
        max_iterations: Hard ceiling for steps (cost control)

    Returns:
        Configured MinimalContextFixWorkflow with v2 executor
    """
    return MinimalContextFixWorkflow(
        project_path=project_path,
        base_iterations=base_iterations,
        max_iterations=max_iterations,
        require_commit_approval=require_commit_approval,
    )
