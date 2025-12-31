"""
Tool Executor Bridge
====================

Bridges the gap between the Agent Harness tool system and the LLM Executor.
Converts tool definitions into executable functions.
"""

import subprocess
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from agentforge.core.harness.llm_executor_domain import ToolResult


# Type alias for tool executor functions
ToolExecutor = Callable[[str, Dict[str, Any]], ToolResult]


class ToolExecutorBridge:
    """Creates executable tool functions from tool definitions.

    This bridge provides default implementations for common tools
    and allows custom tool registration.
    """

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize the bridge.

        Args:
            working_dir: Working directory for file operations
        """
        self.working_dir = working_dir or Path.cwd()
        self._custom_tools: Dict[str, ToolExecutor] = {}

    def register_custom_tool(self, name: str, executor: ToolExecutor) -> None:
        """Register a custom tool executor.

        Args:
            name: Tool name
            executor: Executor function
        """
        self._custom_tools[name] = executor

    def get_default_executors(self) -> Dict[str, ToolExecutor]:
        """Get default tool executors for common operations.

        Returns:
            Dict mapping tool names to executor functions
        """
        executors = {
            "read_file": self._execute_read_file,
            "write_file": self._execute_write_file,
            "edit_file": self._execute_edit_file,
            "glob": self._execute_glob,
            "grep": self._execute_grep,
            "bash": self._execute_bash,
            "run_tests": self._execute_run_tests,
            "list_files": self._execute_list_files,
        }

        # Add custom tools
        executors.update(self._custom_tools)

        return executors

    def _execute_read_file(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Read a file's contents."""
        path = params.get("path")
        if not path:
            return ToolResult.failure_result(name, "Missing required parameter: path")

        file_path = self._resolve_path(path)
        try:
            if not file_path.exists():
                return ToolResult.failure_result(name, f"File not found: {path}")

            content = file_path.read_text(encoding="utf-8")
            return ToolResult.success_result(name, content)
        except Exception as e:
            return ToolResult.failure_result(name, f"Error reading file: {e}")

    def _execute_write_file(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Write content to a file."""
        path = params.get("path")
        content = params.get("content")

        if not path:
            return ToolResult.failure_result(name, "Missing required parameter: path")
        if content is None:
            return ToolResult.failure_result(name, "Missing required parameter: content")

        file_path = self._resolve_path(path)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return ToolResult.success_result(name, f"Successfully wrote to {path}")
        except Exception as e:
            return ToolResult.failure_result(name, f"Error writing file: {e}")

    def _execute_edit_file(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Edit a file using search/replace."""
        path = params.get("path")
        old_string = params.get("old_string")
        new_string = params.get("new_string")

        if not path:
            return ToolResult.failure_result(name, "Missing required parameter: path")
        if old_string is None:
            return ToolResult.failure_result(name, "Missing required parameter: old_string")
        if new_string is None:
            return ToolResult.failure_result(name, "Missing required parameter: new_string")

        file_path = self._resolve_path(path)
        try:
            if not file_path.exists():
                return ToolResult.failure_result(name, f"File not found: {path}")

            content = file_path.read_text(encoding="utf-8")
            if old_string not in content:
                return ToolResult.failure_result(
                    name,
                    f"String not found in file: {old_string[:50]}..."
                )

            new_content = content.replace(old_string, new_string, 1)
            file_path.write_text(new_content, encoding="utf-8")
            return ToolResult.success_result(name, f"Successfully edited {path}")
        except Exception as e:
            return ToolResult.failure_result(name, f"Error editing file: {e}")

    def _execute_glob(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Find files matching a pattern."""
        pattern = params.get("pattern")
        search_path = params.get("path", ".")

        if not pattern:
            return ToolResult.failure_result(name, "Missing required parameter: pattern")

        base_path = self._resolve_path(search_path)
        try:
            matches = list(base_path.glob(pattern))
            if not matches:
                return ToolResult.success_result(name, "No matches found")

            # Return relative paths
            result = "\n".join(
                str(m.relative_to(self.working_dir) if m.is_relative_to(self.working_dir) else m)
                for m in sorted(matches)[:100]  # Limit to 100 results
            )
            return ToolResult.success_result(name, result)
        except Exception as e:
            return ToolResult.failure_result(name, f"Error searching files: {e}")

    def _execute_grep(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Search for text in files."""
        pattern = params.get("pattern")
        search_path = params.get("path", ".")

        if not pattern:
            return ToolResult.failure_result(name, "Missing required parameter: pattern")

        try:
            # Use subprocess for grep (more reliable for text search)
            cmd = ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.js",
                   pattern, str(self._resolve_path(search_path))]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return ToolResult.success_result(name, result.stdout[:10000])  # Limit output
            elif result.returncode == 1:
                return ToolResult.success_result(name, "No matches found")
            else:
                return ToolResult.failure_result(name, result.stderr)
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(name, "Search timed out")
        except Exception as e:
            return ToolResult.failure_result(name, f"Error searching: {e}")

    def _execute_bash(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a shell command."""
        command = params.get("command")

        if not command:
            return ToolResult.failure_result(name, "Missing required parameter: command")

        # Safety check - block dangerous commands
        dangerous_patterns = ["rm -rf /", "dd if=", ":(){ :|:& };:", "mkfs"]
        for pattern in dangerous_patterns:
            if pattern in command:
                return ToolResult.failure_result(
                    name,
                    f"Command blocked for safety: contains '{pattern}'"
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.working_dir)
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            if result.returncode == 0:
                return ToolResult.success_result(name, output[:10000])
            else:
                return ToolResult.failure_result(
                    name,
                    f"Command failed (exit {result.returncode}): {output[:5000]}"
                )
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(name, "Command timed out (120s)")
        except Exception as e:
            return ToolResult.failure_result(name, f"Error executing command: {e}")

    def _execute_run_tests(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """Run tests using pytest."""
        test_path = params.get("test_path", "tests/")

        try:
            cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for tests
                cwd=str(self.working_dir)
            )

            output = result.stdout + result.stderr
            if result.returncode == 0:
                return ToolResult.success_result(name, f"Tests passed!\n{output[:5000]}")
            else:
                return ToolResult.failure_result(
                    name,
                    f"Tests failed (exit {result.returncode}):\n{output[:5000]}"
                )
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(name, "Tests timed out (5 minutes)")
        except Exception as e:
            return ToolResult.failure_result(name, f"Error running tests: {e}")

    def _execute_list_files(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """List files in a directory."""
        path = params.get("path", ".")

        dir_path = self._resolve_path(path)
        try:
            if not dir_path.exists():
                return ToolResult.failure_result(name, f"Directory not found: {path}")
            if not dir_path.is_dir():
                return ToolResult.failure_result(name, f"Not a directory: {path}")

            entries = []
            for item in sorted(dir_path.iterdir())[:100]:  # Limit
                prefix = "d " if item.is_dir() else "f "
                entries.append(f"{prefix}{item.name}")

            return ToolResult.success_result(name, "\n".join(entries))
        except Exception as e:
            return ToolResult.failure_result(name, f"Error listing directory: {e}")

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to working directory."""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.working_dir / p


def create_tool_bridge(working_dir: Optional[Path] = None) -> ToolExecutorBridge:
    """Factory function to create a tool executor bridge.

    Args:
        working_dir: Optional working directory

    Returns:
        Configured ToolExecutorBridge
    """
    return ToolExecutorBridge(working_dir)
