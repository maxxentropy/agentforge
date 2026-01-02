"""
Rollback Manager
================

Manages rollback of failed fix attempts.
"""

import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .llm_executor_domain import ToolResult


@dataclass
class BackupManifest:
    """Manifest for a file backup."""

    backup_id: str
    created_at: datetime
    files: list[dict[str, Any]] = field(default_factory=list)
    label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "backup_id": self.backup_id,
            "created_at": self.created_at.isoformat(),
            "files": self.files,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupManifest":
        """Deserialize from dict."""
        return cls(
            backup_id=data["backup_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            files=data.get("files", []),
            label=data.get("label"),
        )


class RollbackManager:
    """
    Manages file backups and rollback for fix attempts.
    """

    def __init__(self, project_path: Path):
        """
        Initialize rollback manager.

        Args:
            project_path: Project root directory
        """
        self.project_path = Path(project_path)
        self.backup_dir = self.project_path / ".agentforge" / "backups"
        self._current_backup: str | None = None

    def create_backup(self, files: list[str], label: str | None = None) -> str:
        """
        Create backup of files before modification.

        Args:
            files: List of file paths to backup (relative to project root)
            label: Optional label for backup

        Returns:
            Backup ID
        """
        backup_id = f"{label or 'backup'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        manifest = BackupManifest(
            backup_id=backup_id,
            created_at=datetime.utcnow(),
            label=label,
        )

        for file_path in files:
            src = self.project_path / file_path
            if src.exists():
                # Preserve directory structure
                rel_path = Path(file_path)
                dst = backup_path / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                manifest.files.append(
                    {
                        "path": file_path,
                        "backed_up": True,
                        "size": src.stat().st_size,
                    }
                )
            else:
                manifest.files.append(
                    {
                        "path": file_path,
                        "backed_up": False,
                        "reason": "File did not exist",
                    }
                )

        # Save manifest
        with open(backup_path / "manifest.yaml", "w") as f:
            yaml.dump(manifest.to_dict(), f, default_flow_style=False)

        self._current_backup = backup_id
        return backup_id

    def get_current_backup(self) -> str | None:
        """Get the current backup ID."""
        return self._current_backup

    def list_backups(self, limit: int = 20) -> list[BackupManifest]:
        """
        List available backups.

        Args:
            limit: Maximum backups to return

        Returns:
            List of backup manifests
        """
        if not self.backup_dir.exists():
            return []

        backups = []
        for backup_path in sorted(self.backup_dir.iterdir(), reverse=True):
            if len(backups) >= limit:
                break

            manifest_file = backup_path / "manifest.yaml"
            if manifest_file.exists():
                try:
                    with open(manifest_file) as f:
                        data = yaml.safe_load(f)
                    backups.append(BackupManifest.from_dict(data))
                except Exception:
                    pass

        return backups

    def rollback(self, backup_id: str | None = None) -> ToolResult:
        """
        Rollback to a backup.

        Args:
            backup_id: Backup to restore (default: current backup)

        Returns:
            ToolResult indicating success/failure
        """
        backup_id = backup_id or self._current_backup
        if not backup_id:
            return ToolResult.failure_result("rollback", "No backup specified")

        backup_path = self.backup_dir / backup_id
        manifest_file = backup_path / "manifest.yaml"

        if not manifest_file.exists():
            return ToolResult.failure_result("rollback", f"Backup not found: {backup_id}")

        with open(manifest_file) as f:
            manifest = BackupManifest.from_dict(yaml.safe_load(f))

        restored = []
        errors = []

        for file_info in manifest.files:
            if not file_info.get("backed_up"):
                continue

            file_path = file_info["path"]
            src = backup_path / file_path
            dst = self.project_path / file_path

            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                restored.append(file_path)
            except Exception as e:
                errors.append(f"{file_path}: {e}")

        if errors:
            return ToolResult.failure_result(
                "rollback",
                f"Partial rollback. Restored: {restored}. Errors: {errors}",
            )

        return ToolResult.success_result(
            "rollback", f"Rolled back {len(restored)} files from {backup_id}"
        )

    def delete_backup(self, backup_id: str) -> ToolResult:
        """
        Delete a backup.

        Args:
            backup_id: Backup to delete

        Returns:
            ToolResult indicating success/failure
        """
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            return ToolResult.failure_result(
                "delete_backup", f"Backup not found: {backup_id}"
            )

        try:
            shutil.rmtree(backup_path)
            return ToolResult.success_result(
                "delete_backup", f"Deleted backup: {backup_id}"
            )
        except Exception as e:
            return ToolResult.failure_result("delete_backup", f"Error deleting: {e}")

    def cleanup_old_backups(self, keep: int = 10) -> int:
        """
        Clean up old backups, keeping only the most recent.

        Args:
            keep: Number of backups to keep

        Returns:
            Number of backups deleted
        """
        if not self.backup_dir.exists():
            return 0

        backups = sorted(
            [d for d in self.backup_dir.iterdir() if d.is_dir()], reverse=True
        )

        deleted = 0
        for backup_path in backups[keep:]:
            try:
                shutil.rmtree(backup_path)
                deleted += 1
            except Exception:
                pass

        return deleted

    def git_rollback(self, files: list[str] | None = None) -> ToolResult:
        """
        Rollback using git checkout.

        Args:
            files: Specific files to rollback (default: all modified)

        Returns:
            ToolResult
        """
        try:
            cmd = ["git", "checkout", "--"] + files if files else ["git", "checkout", "--", "."]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_path)
            )

            if result.returncode == 0:
                return ToolResult.success_result("git_rollback", "Changes reverted")
            else:
                return ToolResult.failure_result("git_rollback", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_rollback", f"Error: {e}")

    def git_stash(self, message: str | None = None) -> ToolResult:
        """
        Stash current changes.

        Args:
            message: Optional stash message

        Returns:
            ToolResult
        """
        try:
            cmd = ["git", "stash", "push"]
            if message:
                cmd.extend(["-m", message])

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.project_path)
            )

            if result.returncode == 0:
                return ToolResult.success_result("git_stash", result.stdout.strip())
            else:
                return ToolResult.failure_result("git_stash", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_stash", f"Error: {e}")

    def git_stash_pop(self) -> ToolResult:
        """
        Pop the most recent stash.

        Returns:
            ToolResult
        """
        try:
            result = subprocess.run(
                ["git", "stash", "pop"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
            )

            if result.returncode == 0:
                return ToolResult.success_result("git_stash_pop", "Stash applied")
            else:
                return ToolResult.failure_result("git_stash_pop", result.stderr)

        except Exception as e:
            return ToolResult.failure_result("git_stash_pop", f"Error: {e}")

    def get_tool_executors(self) -> dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "rollback": lambda n, p: self.rollback(p.get("backup_id")),
            "git_rollback": lambda n, p: self.git_rollback(p.get("files")),
            "git_stash": lambda n, p: self.git_stash(p.get("message")),
            "git_stash_pop": lambda n, p: self.git_stash_pop(),
        }


# Tool definitions
ROLLBACK_TOOL_DEFINITIONS = [
    {
        "name": "rollback",
        "description": "Rollback files to a previous backup",
        "parameters": {
            "backup_id": {
                "type": "string",
                "required": False,
                "description": "Backup ID to restore (default: most recent)",
            }
        },
    },
    {
        "name": "git_rollback",
        "description": "Discard uncommitted changes using git checkout",
        "parameters": {
            "files": {
                "type": "array",
                "required": False,
                "description": "Specific files to rollback (default: all)",
            }
        },
    },
    {
        "name": "git_stash",
        "description": "Stash current changes",
        "parameters": {
            "message": {
                "type": "string",
                "required": False,
                "description": "Optional stash message",
            }
        },
    },
    {
        "name": "git_stash_pop",
        "description": "Apply the most recent stash",
        "parameters": {},
    },
]
