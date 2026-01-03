# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: conversation-archive
# @test_path: tests/unit/audit/test_conversation_archive.py

"""
Conversation Archive
====================

Archives complete LLM conversations for full transparency.

Each conversation turn captures:
- Full system prompt
- Complete user message
- Full assistant response
- Extended thinking (if enabled)
- Tool calls and results

This enables:
- Complete reproducibility of agent decisions
- Post-hoc analysis of reasoning
- Training data extraction
- Debugging and auditing
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ToolCallDetail:
    """Details of a tool call within a conversation."""

    tool_name: str
    input_params: dict[str, Any]
    output: Any
    success: bool
    error: str | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "tool_name": self.tool_name,
            "input_params": self.input_params,
            "success": self.success,
            "duration_ms": self.duration_ms,
        }
        if self.output is not None:
            # Truncate large outputs for summary
            output_str = str(self.output)
            data["output"] = output_str[:500] if len(output_str) > 500 else output_str
            data["output_length"] = len(output_str)
        if self.error:
            data["error"] = self.error
        return data


@dataclass
class ConversationTurn:
    """A single turn in a conversation (request + response)."""

    turn_id: str
    thread_id: str
    sequence: int  # Turn number within thread

    # Request
    system_prompt: str
    user_message: str
    model: str

    # Response
    response: str
    thinking: str | None = None

    # Tool use within this turn
    tool_calls: list[ToolCallDetail] = field(default_factory=list)

    # Token usage
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_thinking: int = 0
    tokens_cached: int = 0

    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    duration_ms: int = 0

    # Context
    stage_name: str | None = None
    pipeline_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "turn_id": self.turn_id,
            "thread_id": self.thread_id,
            "sequence": self.sequence,
            "model": self.model,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "thinking": self.tokens_thinking,
                "cached": self.tokens_cached,
                "total": self.tokens_input + self.tokens_output + self.tokens_thinking,
            },
        }

        if self.stage_name:
            data["stage_name"] = self.stage_name
        if self.pipeline_id:
            data["pipeline_id"] = self.pipeline_id

        # Store content lengths for summary
        data["content_lengths"] = {
            "system_prompt": len(self.system_prompt),
            "user_message": len(self.user_message),
            "response": len(self.response),
            "thinking": len(self.thinking) if self.thinking else 0,
        }

        if self.tool_calls:
            data["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
            data["tool_call_count"] = len(self.tool_calls)

        return data

    def to_markdown(self) -> str:
        """Format turn as markdown for archival."""
        parts = [f"# Conversation Turn {self.turn_id}\n"]
        parts.append(f"**Thread:** {self.thread_id}\n")
        parts.append(f"**Sequence:** {self.sequence}\n")
        parts.append(f"**Model:** {self.model}\n")
        parts.append(f"**Timestamp:** {self.timestamp}\n")

        if self.stage_name:
            parts.append(f"**Stage:** {self.stage_name}\n")
        if self.pipeline_id:
            parts.append(f"**Pipeline:** {self.pipeline_id}\n")

        parts.append("\n## System Prompt\n")
        parts.append("```\n")
        parts.append(self.system_prompt)
        parts.append("\n```\n")

        parts.append("\n## User Message\n")
        parts.append("```\n")
        parts.append(self.user_message)
        parts.append("\n```\n")

        if self.tool_calls:
            parts.append("\n## Tool Calls\n")
            for tc in self.tool_calls:
                parts.append(f"\n### {tc.tool_name}\n")
                parts.append(f"**Success:** {tc.success}\n")
                parts.append(f"**Duration:** {tc.duration_ms}ms\n")
                parts.append("\n**Input:**\n```json\n")
                import json

                parts.append(json.dumps(tc.input_params, indent=2))
                parts.append("\n```\n")
                if tc.output:
                    parts.append("\n**Output:**\n```\n")
                    output_str = str(tc.output)
                    parts.append(output_str[:2000] if len(output_str) > 2000 else output_str)
                    parts.append("\n```\n")
                if tc.error:
                    parts.append(f"\n**Error:** {tc.error}\n")

        parts.append("\n## Response\n")
        parts.append("```\n")
        parts.append(self.response)
        parts.append("\n```\n")

        if self.thinking:
            parts.append("\n## Extended Thinking\n")
            parts.append(self.thinking)
            parts.append("\n")

        parts.append("\n## Token Usage\n")
        parts.append(f"- Input: {self.tokens_input}\n")
        parts.append(f"- Output: {self.tokens_output}\n")
        if self.tokens_thinking:
            parts.append(f"- Thinking: {self.tokens_thinking}\n")
        if self.tokens_cached:
            parts.append(f"- Cached: {self.tokens_cached}\n")
        parts.append(f"- **Total:** {self.tokens_input + self.tokens_output + self.tokens_thinking}\n")
        parts.append(f"\n**Duration:** {self.duration_ms}ms\n")

        return "".join(parts)


class ConversationArchive:
    """
    Archives complete conversations for a thread.

    Storage structure:
        {thread_dir}/conversations/
        ├── index.yaml           # Turn index with metadata
        ├── TURN-0001.md        # Full conversation content
        ├── TURN-0001.yaml      # Structured metadata
        └── ...
    """

    def __init__(self, thread_dir: Path):
        """
        Initialize conversation archive.

        Args:
            thread_dir: Thread directory
        """
        self.thread_dir = Path(thread_dir)
        self.conversations_dir = self.thread_dir / "conversations"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

        self._sequence = self._get_next_sequence()

    def archive_turn(
        self,
        system_prompt: str,
        user_message: str,
        response: str,
        model: str,
        thread_id: str,
        thinking: str | None = None,
        tool_calls: list[ToolCallDetail] | None = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_thinking: int = 0,
        tokens_cached: int = 0,
        duration_ms: int = 0,
        stage_name: str | None = None,
        pipeline_id: str | None = None,
    ) -> ConversationTurn:
        """
        Archive a conversation turn.

        Args:
            system_prompt: Full system prompt sent
            user_message: Complete user message
            response: Full assistant response
            model: Model used
            thread_id: Owning thread
            thinking: Extended thinking content
            tool_calls: Tool calls made during turn
            tokens_*: Token usage
            duration_ms: Turn duration
            stage_name: Pipeline stage if applicable
            pipeline_id: Pipeline ID if applicable

        Returns:
            Created ConversationTurn
        """
        turn_id = f"TURN-{self._sequence:04d}"
        self._sequence += 1

        turn = ConversationTurn(
            turn_id=turn_id,
            thread_id=thread_id,
            sequence=self._sequence - 1,
            system_prompt=system_prompt,
            user_message=user_message,
            response=response,
            model=model,
            thinking=thinking,
            tool_calls=tool_calls or [],
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_thinking=tokens_thinking,
            tokens_cached=tokens_cached,
            duration_ms=duration_ms,
            stage_name=stage_name,
            pipeline_id=pipeline_id,
        )

        # Save markdown (full content)
        md_path = self.conversations_dir / f"{turn_id}.md"
        md_path.write_text(turn.to_markdown(), encoding="utf-8")

        # Save YAML (structured metadata)
        yaml_path = self.conversations_dir / f"{turn_id}.yaml"
        yaml_path.write_text(
            yaml.dump(turn.to_dict(), default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        # Update index
        self._update_index(turn)

        return turn

    def get_turn(self, turn_id: str) -> ConversationTurn | None:
        """Get a turn by ID."""
        yaml_path = self.conversations_dir / f"{turn_id}.yaml"
        if not yaml_path.exists():
            return None

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        return self._dict_to_turn(data, turn_id)

    def get_turn_content(self, turn_id: str) -> str | None:
        """Get full markdown content of a turn."""
        md_path = self.conversations_dir / f"{turn_id}.md"
        if md_path.exists():
            return md_path.read_text(encoding="utf-8")
        return None

    def list_turns(self) -> list[str]:
        """List all turn IDs in order."""
        turns = []
        for path in sorted(self.conversations_dir.glob("TURN-*.yaml")):
            turns.append(path.stem)
        return turns

    def get_summary(self) -> dict[str, Any]:
        """Get archive summary."""
        index_path = self.conversations_dir / "index.yaml"
        if index_path.exists():
            return yaml.safe_load(index_path.read_text(encoding="utf-8"))
        return {"turns": [], "total_turns": 0}

    def get_total_tokens(self) -> dict[str, int]:
        """Get total token usage across all turns."""
        summary = self.get_summary()
        totals = {
            "input": 0,
            "output": 0,
            "thinking": 0,
            "cached": 0,
            "total": 0,
        }

        for turn_meta in summary.get("turns", []):
            tokens = turn_meta.get("tokens", {})
            totals["input"] += tokens.get("input", 0)
            totals["output"] += tokens.get("output", 0)
            totals["thinking"] += tokens.get("thinking", 0)
            totals["cached"] += tokens.get("cached", 0)

        totals["total"] = totals["input"] + totals["output"] + totals["thinking"]
        return totals

    def _get_next_sequence(self) -> int:
        """Get next turn sequence number."""
        existing = list(self.conversations_dir.glob("TURN-*.yaml"))
        if not existing:
            return 1

        max_seq = 0
        for path in existing:
            try:
                seq = int(path.stem.split("-")[1])
                max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                pass
        return max_seq + 1

    def _update_index(self, turn: ConversationTurn) -> None:
        """Update archive index."""
        index_path = self.conversations_dir / "index.yaml"

        if index_path.exists():
            index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        else:
            index = {"turns": [], "created_at": datetime.now(UTC).isoformat()}

        # Add turn summary to index
        index["turns"].append(
            {
                "turn_id": turn.turn_id,
                "sequence": turn.sequence,
                "timestamp": turn.timestamp,
                "model": turn.model,
                "stage_name": turn.stage_name,
                "tokens": {
                    "input": turn.tokens_input,
                    "output": turn.tokens_output,
                    "thinking": turn.tokens_thinking,
                    "total": turn.tokens_input + turn.tokens_output + turn.tokens_thinking,
                },
                "tool_call_count": len(turn.tool_calls),
                "duration_ms": turn.duration_ms,
            }
        )

        index["total_turns"] = len(index["turns"])
        index["last_updated"] = datetime.now(UTC).isoformat()

        index_path.write_text(
            yaml.dump(index, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def _dict_to_turn(self, data: dict[str, Any], turn_id: str) -> ConversationTurn:
        """Convert dictionary to ConversationTurn (metadata only)."""
        tokens = data.get("tokens", {})
        return ConversationTurn(
            turn_id=turn_id,
            thread_id=data.get("thread_id", ""),
            sequence=data.get("sequence", 0),
            system_prompt="",  # Not stored in YAML
            user_message="",  # Not stored in YAML
            response="",  # Not stored in YAML
            model=data.get("model", ""),
            tokens_input=tokens.get("input", 0),
            tokens_output=tokens.get("output", 0),
            tokens_thinking=tokens.get("thinking", 0),
            tokens_cached=tokens.get("cached", 0),
            duration_ms=data.get("duration_ms", 0),
            stage_name=data.get("stage_name"),
            pipeline_id=data.get("pipeline_id"),
        )
