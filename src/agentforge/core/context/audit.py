# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: audit-v1
# @component_id: context-audit-logger
# @test_path: tests/unit/context/test_audit.py

"""
Context Audit Logger
====================

Full transparency in agent thinking through comprehensive audit logging:
- Context snapshots per step
- Token breakdowns
- Compaction decisions
- Extended thinking content
- Reproducibility via hashing

Prime Directive: Total transparency in the thinking process.
Every decision the agent makes must be traceable.

Audit Directory Structure:
    {project}/.agentforge/context_audit/
    └── {task_id}/
        ├── summary.yaml           # Task completion summary
        ├── step_1.yaml            # Step audit entry
        ├── step_1_context.yaml    # Full context snapshot
        ├── step_1_thinking.md     # Extended thinking (if enabled)
        └── ...

Usage:
    ```python
    logger = ContextAuditLogger(project_path, task_id="fix-V-001")

    # Log each step
    logger.log_step(
        step=1,
        context=context_dict,
        token_breakdown={"fingerprint": 500, "task": 200},
        compaction=compaction_audit,
        thinking="The extraction looks good...",
        response="action: extract_function\\n...",
    )

    # Log task completion
    logger.log_task_summary(
        total_steps=8,
        final_status="completed",
        total_tokens=25000,
        cached_tokens=12000,
    )
    ```
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

import yaml


class ContextAuditLogger:
    """
    Comprehensive audit logger for agent context and decisions.

    Provides full transparency by logging:
    - Context snapshots for each step
    - Token usage breakdowns
    - Compaction decisions and their effects
    - Extended thinking content
    - Reproducibility hashes
    """

    def __init__(self, project_path: Path, task_id: str):
        """
        Initialize audit logger for a task.

        Args:
            project_path: Root path of the project
            task_id: Unique identifier for this task execution
        """
        self.project_path = Path(project_path).resolve()
        self.task_id = task_id
        self.audit_dir = (
            self.project_path / ".agentforge" / "context_audit" / task_id
        )
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Track steps logged for summary
        self._steps_logged: list[int] = []
        self._total_thinking_tokens = 0

    def log_step(
        self,
        step: int,
        context: dict[str, Any],
        token_breakdown: dict[str, int],
        compaction: dict[str, Any] | None = None,
        thinking: str | None = None,
        response: str | None = None,
    ) -> None:
        """
        Log complete audit for a single step.

        Args:
            step: Step number (1-indexed)
            context: Full context dictionary
            token_breakdown: Tokens per section
            compaction: Compaction audit info (if compaction occurred)
            thinking: Extended thinking content (if enabled)
            response: LLM response content
        """
        audit_entry: dict[str, Any] = {
            "task_id": self.task_id,
            "step": step,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "token_breakdown": token_breakdown,
            "total_tokens": sum(token_breakdown.values()),
            "context_hash": self._hash_context(context),
            "sections_present": list(context.keys()),
        }

        if compaction:
            audit_entry["compaction"] = compaction

        if thinking:
            thinking_path = self.audit_dir / f"step_{step}_thinking.md"
            thinking_path.write_text(
                f"# Step {step} Thinking\n\n{thinking}",
                encoding="utf-8",
            )
            audit_entry["thinking_file"] = thinking_path.name
            thinking_tokens = len(thinking) // 4
            audit_entry["thinking_tokens"] = thinking_tokens
            self._total_thinking_tokens += thinking_tokens

        if response:
            audit_entry["response_tokens"] = len(response) // 4

        # Save audit entry
        self._save_yaml(f"step_{step}.yaml", audit_entry)

        # Save full context snapshot
        self._save_yaml(f"step_{step}_context.yaml", context)

        self._steps_logged.append(step)

    def log_task_summary(
        self,
        total_steps: int,
        final_status: str,
        total_tokens: int,
        cached_tokens: int = 0,
        compaction_events: int = 0,
        tokens_saved: int = 0,
    ) -> None:
        """
        Log task completion summary.

        Args:
            total_steps: Total steps executed
            final_status: Final status (completed, failed, escalated)
            total_tokens: Total input tokens used
            cached_tokens: Tokens served from cache
            compaction_events: Number of compaction events
            tokens_saved: Total tokens saved via compaction
        """
        # Calculate effective tokens (cache reduces cost by ~90%)
        effective_tokens = total_tokens - int(cached_tokens * 0.9)

        summary: dict[str, Any] = {
            "task_id": self.task_id,
            "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "total_steps": total_steps,
            "final_status": final_status,
            "total_input_tokens": total_tokens,
            "cached_tokens": cached_tokens,
            "effective_tokens": effective_tokens,
        }

        if compaction_events > 0:
            summary["compaction_events"] = compaction_events
            summary["total_tokens_saved"] = tokens_saved

        if self._total_thinking_tokens > 0:
            summary["thinking_enabled"] = True
            summary["total_thinking_tokens"] = self._total_thinking_tokens

        self._save_yaml("summary.yaml", summary)

    def get_step_audit(self, step: int) -> dict[str, Any] | None:
        """Retrieve audit entry for a step."""
        path = self.audit_dir / f"step_{step}.yaml"
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        return None

    def get_step_context(self, step: int) -> dict[str, Any] | None:
        """Retrieve full context snapshot for a step."""
        path = self.audit_dir / f"step_{step}_context.yaml"
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        return None

    def get_thinking(self, step: int) -> str | None:
        """Retrieve thinking content for a step."""
        path = self.audit_dir / f"step_{step}_thinking.md"
        if path.exists():
            content = path.read_text(encoding="utf-8")
            # Remove the header we added
            if content.startswith(f"# Step {step} Thinking\n\n"):
                return content[len(f"# Step {step} Thinking\n\n") :]
            return content
        return None

    def get_summary(self) -> dict[str, Any] | None:
        """Retrieve task summary."""
        path = self.audit_dir / "summary.yaml"
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        return None

    def list_steps(self) -> list[int]:
        """List all logged step numbers."""
        steps: list[int] = []
        for path in self.audit_dir.glob("step_*_context.yaml"):
            try:
                step = int(path.stem.split("_")[1])
                steps.append(step)
            except (ValueError, IndexError):
                continue
        return sorted(steps)

    def _hash_context(self, context: dict[str, Any]) -> str:
        """Compute reproducibility hash for context."""
        # Sort keys and convert to JSON for consistent hashing
        content = json.dumps(context, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _save_yaml(self, filename: str, data: dict[str, Any]) -> None:
        """Save data as YAML file."""
        path = self.audit_dir / filename
        yaml_content = yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        path.write_text(yaml_content, encoding="utf-8")

    @classmethod
    def load_task_audit(
        cls, project_path: Path, task_id: str
    ) -> Optional["ContextAuditLogger"]:
        """
        Load an existing task audit for review.

        Returns None if the audit doesn't exist.
        """
        audit_dir = (
            Path(project_path).resolve()
            / ".agentforge"
            / "context_audit"
            / task_id
        )
        if not audit_dir.exists():
            return None

        logger = cls(project_path, task_id)
        return logger

    @classmethod
    def list_task_audits(cls, project_path: Path) -> list[str]:
        """List all task IDs with audit data."""
        audit_root = Path(project_path).resolve() / ".agentforge" / "context_audit"
        if not audit_root.exists():
            return []

        return [
            d.name
            for d in audit_root.iterdir()
            if d.is_dir() and (d / "summary.yaml").exists()
        ]
