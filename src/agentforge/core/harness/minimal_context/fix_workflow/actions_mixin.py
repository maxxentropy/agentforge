# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: fix-workflow-actions

"""
Action Methods Mixin
====================

File operation action methods for the fix workflow.
Handles read, edit, replace, insert, write operations.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .utils import (
    adjust_content_indentation,
    detect_source_indent,
    validate_insert_params,
    validate_replace_params,
)

if TYPE_CHECKING:
    from ..state_store import TaskState
    from ..working_memory import WorkingMemoryManager


class ActionsMixin:
    """
    Action methods for fix workflow.

    Provides file operations (read, edit, replace, insert, write)
    and check/test execution actions.
    """

    # Type hints for mixin - provided by main class
    project_path: Path
    state_store: Any
    test_tools: Any
    conformance_tools: Any
    _validate_python_file: Any  # From ValidationMixin
    _refresh_precomputed_context: Any  # From ContextMixin

    def _track_modified_file(self, state: "TaskState", file_path: str) -> None:
        """Track a modified file in state context."""
        if "files_modified" not in state.context_data:
            state.context_data["files_modified"] = []
        if file_path not in state.context_data["files_modified"]:
            state.context_data["files_modified"].append(file_path)
            self.state_store.update_context_data(
                state.task_id, "files_modified", state.context_data["files_modified"]
            )

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
        state: "TaskState",
    ) -> dict[str, Any]:
        """Read a file, focusing on the violation area if known."""
        from ..working_memory import WorkingMemoryManager

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
        state: "TaskState",
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
        state: "TaskState",
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
        if error := validate_replace_params(file_path, start_line, end_line, new_content):
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
            source_indent = detect_source_indent(content_lines)
            new_lines = adjust_content_indentation(content_lines, target_indent, source_indent)

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
        state: "TaskState",
    ) -> dict[str, Any]:
        """Insert lines into a file at a specific line number."""
        file_path = params.get("file_path") or params.get("path") or state.context_data.get("file_path")
        line_number = params.get("line_number") or params.get("before_line")
        new_content = params.get("new_content") or params.get("content")

        # Validate parameters using helper
        if error := validate_insert_params(file_path, line_number, new_content):
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
        state: "TaskState",
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

    def _action_run_check(
        self,
        action_name: str,
        params: dict[str, Any],
        state: "TaskState",
    ) -> dict[str, Any]:
        """Run conformance check - uses targeted check when check_id available."""
        file_path = self._extract_file_path(params, state)
        check_id = params.get("check_id") or state.context_data.get("check_id")

        result = self._run_conformance_check(check_id, file_path)
        self._update_check_verification(state, result)
        self._maybe_refresh_context_on_failure(state, result, file_path)

        return self._build_check_result(result)

    def _extract_file_path(self, params: dict[str, Any], state: "TaskState") -> str | None:
        """Extract file path from params or state context."""
        return params.get("file_path") or params.get("path") or state.context_data.get("file_path")

    def _update_check_verification(self, state: "TaskState", result) -> None:
        """Update verification status based on check result."""
        passing = result.success
        self.state_store.update_verification(
            state.task_id,
            checks_passing=1 if passing else 0,
            checks_failing=0 if passing else 1,
            tests_passing=state.verification.tests_passing,
            details={"last_check": result.output[:500]},
        )

    def _maybe_refresh_context_on_failure(
        self, state: "TaskState", result, file_path: str | None
    ) -> None:
        """Refresh precomputed context if check failed with actionable output."""
        if result.success or not result.output or not file_path:
            return

        from .utils import extract_function_name_from_output
        new_function_name = extract_function_name_from_output(result.output)
        if not new_function_name:
            return

        new_context = self._refresh_precomputed_context(file_path, new_function_name, state)
        if new_context:
            state.context_data["precomputed"] = new_context
            self.state_store.update_context_data(state.task_id, "precomputed", new_context)

    def _build_check_result(self, result) -> dict[str, Any]:
        """Build standardized check result dictionary."""
        return {
            "status": "success" if result.success else "partial",
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

    def _action_run_tests(
        self,
        action_name: str,
        params: dict[str, Any],
        state: "TaskState",
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
        state: "TaskState",
    ) -> dict[str, Any]:
        """Load additional context into working memory."""
        from ..working_memory import WorkingMemoryManager

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

    def _check_tests_worsened(self, baseline_result: Any, after_result: Any) -> bool:
        """Check if tests got worse after an operation."""
        if baseline_result.success and not after_result.success:
            return True
        if not baseline_result.success and not after_result.success:
            baseline_failures = self._count_test_failures(baseline_result.output)
            after_failures = self._count_test_failures(after_result.output)
            return after_failures > baseline_failures
        return False

    def _count_test_failures(self, output: str) -> int:
        """Extract failure count from pytest output."""
        import re
        if not output:
            return 0
        match = re.search(r'(\d+) failed', output)
        if match:
            return int(match.group(1))
        return 0

    def _build_extraction_revert_result(
        self, file_path: str, original_content: str | None, result: Any, after_result: Any
    ) -> dict[str, Any]:
        """Revert file and build failure result for extract_function."""
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
        self, state: "TaskState", file_path: str, params: dict,
        check_result: Any, after_result: Any, baseline_passed: bool
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

    def _wrap_extract_function(self, tool_executor: Any) -> Any:
        """
        Wrap extract_function to enforce CORRECTNESS FIRST:
        1. Run tests BEFORE extraction to establish baseline
        2. Save original content before extraction
        3. Run extraction (syntax validated by tool)
        4. RUN TESTS AFTER - if MORE tests fail than before, REVERT
        5. Only then run conformance check
        6. Refresh context with new line numbers
        """
        from collections.abc import Callable

        def wrapper(action_name: str, params: dict[str, Any], state: "TaskState") -> dict[str, Any]:
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
                return self._build_extraction_revert_result(file_path, original_content, result, after_result)

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

    def _action_plan_fix(
        self,
        action_name: str,
        params: dict[str, Any],
        state: "TaskState",
    ) -> dict[str, Any]:
        """Record fix plan and advance to implement phase."""
        from ..state_store import Phase

        diagnosis = params.get("diagnosis", "")
        approach = params.get("approach", "")

        self.state_store.update_context_data(state.task_id, "diagnosis", diagnosis)
        self.state_store.update_context_data(state.task_id, "approach", approach)
        self.state_store.update_phase(state.task_id, Phase.IMPLEMENT)

        return {
            "status": "success",
            "summary": f"Plan recorded: {approach[:100]}",
        }
