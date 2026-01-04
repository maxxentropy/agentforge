# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: transaction-logger
# @test_path: tests/unit/audit/test_transaction_logger.py

"""
Transaction Logger
==================

Records individual transactions (LLM calls, tool executions, decisions)
with full context for complete reproducibility.

A transaction captures:
- Input: Full prompt sent to LLM
- Output: Complete response received
- Thinking: Extended thinking content (if enabled)
- Tool calls: All tool invocations with inputs/outputs
- Decision: Parsed action and parameters
- Duration: Timing information
- Tokens: Token usage breakdown
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class TransactionType(str, Enum):
    """Type of audit transaction."""

    LLM_CALL = "llm_call"  # Direct LLM invocation
    TOOL_CALL = "tool_call"  # Tool execution
    HUMAN_INTERACTION = "human_interaction"  # HITL escalation
    SPAWN = "spawn"  # Agent delegation/spawn
    DECISION = "decision"  # Logical decision point
    STATE_CHANGE = "state_change"  # Pipeline/task state change


@dataclass
class ToolCallRecord:
    """Record of a single tool invocation."""

    tool_name: str
    input_params: dict[str, Any]
    output: Any
    duration_ms: int
    success: bool
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class TokenUsage:
    """Token usage breakdown for an LLM interaction."""

    input: int = 0
    output: int = 0
    thinking: int = 0
    cached: int = 0

    @property
    def total(self) -> int:
        """Total tokens used."""
        return self.input + self.output + self.thinking

    def to_dict(self) -> dict[str, int]:
        """Serialize to dictionary."""
        return {
            "input": self.input,
            "output": self.output,
            "thinking": self.thinking,
            "cached": self.cached,
            "total": self.total,
        }


@dataclass
class TransactionRecord:
    """
    Complete record of a single transaction.

    Captures everything needed to understand what happened and why.
    """

    # Identity
    transaction_id: str  # Format: TX-{sequence:04d}
    thread_id: str  # Owning thread
    sequence: int  # Transaction sequence within thread

    # Classification
    transaction_type: TransactionType
    stage_name: str | None = None  # Pipeline stage if applicable

    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    duration_ms: int = 0

    # LLM interaction (for LLM_CALL type)
    llm_request: dict[str, Any] | None = None  # Full prompt structure
    llm_response: str | None = None  # Complete response text
    thinking: str | None = None  # Extended thinking content

    # Tool calls (may occur within LLM interaction)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)

    # Parsed decision
    action_name: str | None = None
    action_params: dict[str, Any] | None = None
    action_result: dict[str, Any] | None = None

    # Tokens
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_thinking: int = 0
    tokens_cached: int = 0

    # Artifact changes
    artifacts_before: dict[str, Any] | None = None
    artifacts_after: dict[str, Any] | None = None
    artifacts_delta: list[str] | None = None  # Keys that changed

    # Integrity
    previous_hash: str | None = None  # Hash of previous transaction
    content_hash: str | None = None  # Hash of this transaction's content

    # Spawn info (for SPAWN type)
    spawned_thread_id: str | None = None
    spawn_reason: str | None = None

    # Human interaction (for HUMAN_INTERACTION type)
    human_prompt: str | None = None
    human_response: str | None = None
    human_context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for storage."""
        data = {
            "transaction_id": self.transaction_id,
            "thread_id": self.thread_id,
            "sequence": self.sequence,
            "transaction_type": self.transaction_type.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }

        if self.stage_name:
            data["stage_name"] = self.stage_name

        # Merge optional sections
        for partial in [
            self._llm_fields(),
            self._tool_calls_fields(),
            self._action_fields(),
            self._token_fields(),
            self._integrity_fields(),
            self._spawn_fields(),
            self._human_fields(),
        ]:
            data.update(partial)

        return data

    def _llm_fields(self) -> dict[str, Any]:
        """Serialize LLM interaction fields."""
        fields: dict[str, Any] = {}
        if self.llm_request:
            fields["llm_request"] = self.llm_request
        if self.llm_response:
            fields["llm_response_length"] = len(self.llm_response)
        if self.thinking:
            fields["thinking_length"] = len(self.thinking)
        return fields

    def _tool_calls_fields(self) -> dict[str, Any]:
        """Serialize tool call records."""
        if not self.tool_calls:
            return {}
        return {
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "input_params": tc.input_params,
                    "output_summary": str(tc.output)[:200] if tc.output else None,
                    "duration_ms": tc.duration_ms,
                    "success": tc.success,
                    "error": tc.error,
                }
                for tc in self.tool_calls
            ]
        }

    def _action_fields(self) -> dict[str, Any]:
        """Serialize parsed action/decision fields."""
        if not self.action_name:
            return {}
        return {
            "action": {
                "name": self.action_name,
                "params": self.action_params,
                "result": self.action_result,
            }
        }

    def _token_fields(self) -> dict[str, Any]:
        """Serialize token usage fields."""
        if not (self.tokens_input or self.tokens_output):
            return {}
        return {
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "thinking": self.tokens_thinking,
                "cached": self.tokens_cached,
                "total": self.tokens_input + self.tokens_output + self.tokens_thinking,
            }
        }

    def _integrity_fields(self) -> dict[str, Any]:
        """Serialize integrity chain and artifact fields."""
        fields: dict[str, Any] = {}
        if self.artifacts_delta:
            fields["artifacts_delta"] = self.artifacts_delta
        if self.previous_hash:
            fields["previous_hash"] = self.previous_hash
        if self.content_hash:
            fields["content_hash"] = self.content_hash
        return fields

    def _spawn_fields(self) -> dict[str, Any]:
        """Serialize spawn/delegation fields."""
        if not self.spawned_thread_id:
            return {}
        return {
            "spawn": {
                "spawned_thread_id": self.spawned_thread_id,
                "reason": self.spawn_reason,
            }
        }

    def _human_fields(self) -> dict[str, Any]:
        """Serialize human interaction fields."""
        if not self.human_prompt:
            return {}
        return {
            "human_interaction": {
                "prompt": self.human_prompt,
                "response": self.human_response,
                "context": self.human_context,
            }
        }


class TransactionLogger:
    """
    Logs transactions for a single thread.

    Manages:
    - Sequential transaction recording
    - Full conversation archival
    - Hash chain maintenance
    """

    def __init__(self, project_path: Path, thread_id: str):
        """
        Initialize transaction logger for a thread.

        Args:
            project_path: Root project directory
            thread_id: Unique thread identifier
        """
        from .integrity_chain import IntegrityChain

        self.project_path = Path(project_path).resolve()
        self.thread_id = thread_id

        self.thread_dir = self.project_path / ".agentforge" / "audit" / "threads" / thread_id
        self.transactions_dir = self.thread_dir / "transactions"
        self.transactions_dir.mkdir(parents=True, exist_ok=True)

        self._sequence = self._get_next_sequence()
        self._integrity_chain = IntegrityChain(self.thread_dir)
        self._last_hash: str | None = self._integrity_chain.get_last_hash()

    def log_transaction(self, record: TransactionRecord) -> Path:
        """
        Log a transaction record.

        Args:
            record: Transaction to log

        Returns:
            Path to saved transaction file
        """
        # Ensure sequence and hashing
        if record.sequence == 0:
            record.sequence = self._sequence
            record.transaction_id = f"TX-{self._sequence:04d}"
            self._sequence += 1

        # Get transaction data for hashing (before we add hash fields)
        tx_data = record.to_dict()

        # Append to integrity chain (this computes and stores hashes)
        block = self._integrity_chain.append(record.transaction_id, tx_data)

        # Update record with hash info
        record.previous_hash = block.previous_hash
        record.content_hash = block.content_hash
        self._last_hash = block.content_hash

        # Save transaction metadata (now includes hash fields)
        tx_path = self.transactions_dir / f"{record.transaction_id}.yaml"
        tx_data_with_hash = record.to_dict()
        tx_path.write_text(
            yaml.dump(tx_data_with_hash, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        # Save full LLM content separately (if present)
        if record.llm_request or record.llm_response:
            llm_path = self.transactions_dir / f"{record.transaction_id}-llm.md"
            llm_content = self._format_llm_content(record)
            llm_path.write_text(llm_content, encoding="utf-8")

        # Save thinking separately (if present and large)
        if record.thinking and len(record.thinking) > 1000:
            thinking_path = self.transactions_dir / f"{record.transaction_id}-thinking.md"
            thinking_path.write_text(
                f"# Transaction {record.transaction_id} Thinking\n\n{record.thinking}",
                encoding="utf-8",
            )

        return tx_path

    def log_llm_call(
        self,
        request: dict[str, Any],
        response: str,
        thinking: str | None = None,
        action_name: str | None = None,
        action_params: dict[str, Any] | None = None,
        action_result: dict[str, Any] | None = None,
        tool_calls: list[ToolCallRecord] | None = None,
        tokens: TokenUsage | None = None,
        duration_ms: int = 0,
        stage_name: str | None = None,
    ) -> TransactionRecord:
        """
        Convenience method to log an LLM call transaction.

        Args:
            request: Full LLM request (messages, system prompt, etc.)
            response: Complete LLM response text
            thinking: Extended thinking content
            action_name: Parsed action name
            action_params: Parsed action parameters
            action_result: Action execution result
            tool_calls: List of tool call records
            tokens: Token usage breakdown
            duration_ms: Call duration in milliseconds
            stage_name: Pipeline stage name if applicable

        Returns:
            The created TransactionRecord
        """
        tokens = tokens or TokenUsage()
        record = TransactionRecord(
            transaction_id="",
            thread_id=self.thread_id,
            sequence=0,
            transaction_type=TransactionType.LLM_CALL,
            stage_name=stage_name,
            llm_request=request,
            llm_response=response,
            thinking=thinking,
            action_name=action_name,
            action_params=action_params,
            action_result=action_result,
            tool_calls=tool_calls or [],
            tokens_input=tokens.input,
            tokens_output=tokens.output,
            tokens_thinking=tokens.thinking,
            tokens_cached=tokens.cached,
            duration_ms=duration_ms,
        )

        self.log_transaction(record)
        return record

    def log_spawn(
        self,
        spawned_thread_id: str,
        reason: str,
        context: dict[str, Any] | None = None,
    ) -> TransactionRecord:
        """
        Log an agent spawn/delegation event.

        Args:
            spawned_thread_id: ID of the spawned child thread
            reason: Why this spawn occurred
            context: Additional context for the spawn

        Returns:
            The created TransactionRecord
        """
        record = TransactionRecord(
            transaction_id="",
            thread_id=self.thread_id,
            sequence=0,
            transaction_type=TransactionType.SPAWN,
            spawned_thread_id=spawned_thread_id,
            spawn_reason=reason,
            artifacts_before=context,
        )

        self.log_transaction(record)
        return record

    def log_human_interaction(
        self,
        prompt: str,
        response: str | None,
        context: dict[str, Any] | None = None,
        duration_ms: int = 0,
    ) -> TransactionRecord:
        """
        Log a human-in-the-loop interaction.

        Args:
            prompt: Question/request shown to human
            response: Human's response
            context: Full context at time of interaction
            duration_ms: Time human took to respond

        Returns:
            The created TransactionRecord
        """
        record = TransactionRecord(
            transaction_id="",
            thread_id=self.thread_id,
            sequence=0,
            transaction_type=TransactionType.HUMAN_INTERACTION,
            human_prompt=prompt,
            human_response=response,
            human_context=context,
            duration_ms=duration_ms,
        )

        self.log_transaction(record)
        return record

    def get_transaction(self, transaction_id: str) -> TransactionRecord | None:
        """Load a transaction by ID."""
        tx_path = self.transactions_dir / f"{transaction_id}.yaml"
        if not tx_path.exists():
            return None

        data = yaml.safe_load(tx_path.read_text(encoding="utf-8"))
        return self._dict_to_record(data)

    def list_transactions(self) -> list[str]:
        """List all transaction IDs in order."""
        transactions = []
        for path in sorted(self.transactions_dir.glob("TX-*.yaml")):
            if "-llm" not in path.name and "-thinking" not in path.name:
                transactions.append(path.stem)
        return transactions

    def get_full_llm_content(self, transaction_id: str) -> str | None:
        """Get full LLM prompt+response for a transaction."""
        llm_path = self.transactions_dir / f"{transaction_id}-llm.md"
        if llm_path.exists():
            return llm_path.read_text(encoding="utf-8")
        return None

    def _get_next_sequence(self) -> int:
        """Get next transaction sequence number."""
        existing = list(self.transactions_dir.glob("TX-*.yaml"))
        if not existing:
            return 1
        # Parse highest sequence
        max_seq = 0
        for path in existing:
            try:
                seq = int(path.stem.split("-")[1])
                max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                pass
        return max_seq + 1

    def _format_llm_content(self, record: TransactionRecord) -> str:
        """Format full LLM content for archival."""
        parts = [f"# Transaction {record.transaction_id} - LLM Interaction\n"]
        parts.append(f"**Timestamp:** {record.timestamp}\n")
        parts.append(f"**Thread:** {record.thread_id}\n")

        if record.stage_name:
            parts.append(f"**Stage:** {record.stage_name}\n")

        parts.append("\n## Request\n")
        if record.llm_request:
            request = record.llm_request
            if "system" in request:
                parts.append("### System Prompt\n```\n")
                parts.append(str(request["system"]))
                parts.append("\n```\n")
            if "messages" in request:
                parts.append("### Messages\n")
                for msg in request["messages"]:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    parts.append(f"**{role}:**\n```\n{content}\n```\n")

        parts.append("\n## Response\n```\n")
        parts.append(record.llm_response or "(no response)")
        parts.append("\n```\n")

        if record.thinking:
            parts.append("\n## Extended Thinking\n")
            parts.append(record.thinking)
            parts.append("\n")

        return "".join(parts)

    def _dict_to_record(self, data: dict[str, Any]) -> TransactionRecord:
        """Convert dictionary to TransactionRecord."""
        # Parse tool calls if present
        tool_calls = []
        for tc in data.get("tool_calls", []):
            tool_calls.append(
                ToolCallRecord(
                    tool_name=tc.get("tool_name", ""),
                    input_params=tc.get("input_params", {}),
                    output=tc.get("output_summary"),
                    duration_ms=tc.get("duration_ms", 0),
                    success=tc.get("success", True),
                    error=tc.get("error"),
                )
            )

        # Parse action if present
        action = data.get("action", {})

        # Parse tokens if present
        tokens = data.get("tokens", {})

        # Parse spawn if present
        spawn = data.get("spawn", {})

        # Parse human interaction if present
        human = data.get("human_interaction", {})

        return TransactionRecord(
            transaction_id=data.get("transaction_id", ""),
            thread_id=data.get("thread_id", self.thread_id),
            sequence=data.get("sequence", 0),
            transaction_type=TransactionType(data.get("transaction_type", "llm_call")),
            stage_name=data.get("stage_name"),
            timestamp=data.get("timestamp", ""),
            duration_ms=data.get("duration_ms", 0),
            tool_calls=tool_calls,
            action_name=action.get("name"),
            action_params=action.get("params"),
            action_result=action.get("result"),
            tokens_input=tokens.get("input", 0),
            tokens_output=tokens.get("output", 0),
            tokens_thinking=tokens.get("thinking", 0),
            tokens_cached=tokens.get("cached", 0),
            spawned_thread_id=spawn.get("spawned_thread_id"),
            spawn_reason=spawn.get("reason"),
            human_prompt=human.get("prompt"),
            human_response=human.get("response"),
            human_context=human.get("context"),
            previous_hash=data.get("previous_hash"),
            content_hash=data.get("content_hash"),
        )
