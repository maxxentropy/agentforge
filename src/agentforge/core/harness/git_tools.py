"""
Git Tools
=========

Tools for Git operations with safety guardrails.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .llm_executor_domain import ToolResult


class GitTools:
    """
    Git tools with safety constraints.

    Only allows:
    - Status, diff, log (read operations)
    - Add, commit (with message validation)
    - Never push, force, or destructive operations
    """

    # Blocked git operations
    BLOCKED_COMMANDS = [
        "push",
        "force",
        "reset --hard",
        "clean -fd",
        "checkout --",
        "rebase",
        "merge",
        "cherry-pick",
        "branch -D",
        "branch -d",
        "remote",
    ]

    def __init__(self, project_path: Path, require_approval: bool = True):
        """
        Initialize git tools.

        Args:
            project_path: Project root directory
            require_approval: If True, commits need human approval
        """
        self.project_path = Path(project_path)
        self.require_approval = require_approval
        self._pending_commit: Dict[str, Any] = {}

    def git_status(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Show git status.

        Returns:
            ToolResult with status output
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
            )

            if result.returncode == 0:
                if not result.stdout.strip():
                    return ToolResult.success_result(
                        "git_status", "Working directory clean"
                    )
                return ToolResult.success_result("git_status", result.stdout)
            else:
                return ToolResult.failure_result("git_status", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_status", f"Error: {e}")

    def git_diff(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Show git diff for a file or all changes.

        Parameters:
            file_path: Optional file to diff (default: all changes)
            staged: If True, show staged changes
        """
        file_path = params.get("file_path")
        staged = params.get("staged", False)

        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            if file_path:
                cmd.append(file_path)

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_path)
            )

            if result.returncode == 0:
                if not result.stdout.strip():
                    return ToolResult.success_result("git_diff", "No changes")
                # Limit output size
                output = result.stdout[:5000]
                if len(result.stdout) > 5000:
                    output += "\n... (output truncated)"
                return ToolResult.success_result("git_diff", output)
            else:
                return ToolResult.failure_result("git_diff", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_diff", f"Error: {e}")

    def git_log(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Show recent git commit history.

        Parameters:
            count: Number of commits to show (default: 10)
            oneline: Use oneline format (default: True)
        """
        count = params.get("count", 10)
        oneline = params.get("oneline", True)

        try:
            cmd = ["git", "log", f"-{count}"]
            if oneline:
                cmd.append("--oneline")

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_path)
            )

            if result.returncode == 0:
                return ToolResult.success_result("git_log", result.stdout)
            else:
                return ToolResult.failure_result("git_log", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_log", f"Error: {e}")

    def git_add(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Stage files for commit.

        Parameters:
            files: List of file paths to stage
        """
        files = params.get("files", [])
        if not files:
            return ToolResult.failure_result(
                "git_add", "Missing required parameter: files (list of paths)"
            )

        if isinstance(files, str):
            files = [files]

        try:
            cmd = ["git", "add"] + files
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_path)
            )

            if result.returncode == 0:
                return ToolResult.success_result(
                    "git_add", f"Staged {len(files)} file(s): {', '.join(files)}"
                )
            else:
                return ToolResult.failure_result("git_add", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_add", f"Error: {e}")

    def git_commit(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Create a commit with the staged changes.

        Parameters:
            message: Commit message
            violation_id: Optional violation ID for tracking

        Note: If require_approval is True, commit is staged for human approval.
        """
        message = params.get("message")
        violation_id = params.get("violation_id")

        if not message:
            return ToolResult.failure_result(
                "git_commit", "Missing required parameter: message"
            )

        # Validate message
        if len(message) < 10:
            return ToolResult.failure_result(
                "git_commit", "Commit message too short (minimum 10 characters)"
            )

        # Add violation reference to message if provided
        if violation_id:
            if not violation_id.startswith("V-"):
                violation_id = f"V-{violation_id}"
            message = f"fix({violation_id}): {message}"

        if self.require_approval:
            # Stage for approval instead of committing
            self._pending_commit = {"message": message, "violation_id": violation_id}
            return ToolResult.success_result(
                "git_commit",
                f"Commit staged for approval:\n\nMessage: {message}\n\n"
                f"Run 'agentforge agent approve-commit' to apply.",
            )

        # Direct commit (only if approval not required)
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
            )

            if result.returncode == 0:
                return ToolResult.success_result(
                    "git_commit", f"Committed: {message}\n{result.stdout}"
                )
            else:
                return ToolResult.failure_result("git_commit", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_commit", f"Error: {e}")

    def get_pending_commit(self) -> Dict[str, Any]:
        """Get pending commit awaiting approval."""
        return self._pending_commit

    def clear_pending_commit(self):
        """Clear pending commit."""
        self._pending_commit = {}

    def apply_pending_commit(self) -> ToolResult:
        """Apply the pending commit (called after human approval)."""
        if not self._pending_commit:
            return ToolResult.failure_result("apply_pending_commit", "No pending commit")

        message = self._pending_commit["message"]

        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
            )

            self._pending_commit = {}

            if result.returncode == 0:
                return ToolResult.success_result(
                    "apply_pending_commit", f"Committed: {message}"
                )
            else:
                return ToolResult.failure_result("apply_pending_commit", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("apply_pending_commit", f"Error: {e}")

    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "git_status": self.git_status,
            "git_diff": self.git_diff,
            "git_log": self.git_log,
            "git_add": self.git_add,
            "git_commit": self.git_commit,
        }


# Tool definitions
GIT_TOOL_DEFINITIONS = [
    {
        "name": "git_status",
        "description": "Show current git status (modified/staged files)",
        "parameters": {},
    },
    {
        "name": "git_diff",
        "description": "Show git diff for changes",
        "parameters": {
            "file_path": {
                "type": "string",
                "required": False,
                "description": "Specific file to diff",
            },
            "staged": {
                "type": "boolean",
                "required": False,
                "description": "Show staged changes instead of unstaged",
            },
        },
    },
    {
        "name": "git_log",
        "description": "Show recent git commit history",
        "parameters": {
            "count": {
                "type": "integer",
                "required": False,
                "description": "Number of commits to show (default: 10)",
            },
            "oneline": {
                "type": "boolean",
                "required": False,
                "description": "Use oneline format (default: True)",
            },
        },
    },
    {
        "name": "git_add",
        "description": "Stage files for commit",
        "parameters": {
            "files": {
                "type": "array",
                "required": True,
                "description": "List of file paths to stage",
            }
        },
    },
    {
        "name": "git_commit",
        "description": "Create a commit (requires human approval by default)",
        "parameters": {
            "message": {
                "type": "string",
                "required": True,
                "description": "Commit message (min 10 chars)",
            },
            "violation_id": {
                "type": "string",
                "required": False,
                "description": "Violation ID for tracking",
            },
        },
    },
]
