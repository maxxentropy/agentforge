# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: audit-manager
# @test_path: tests/unit/audit/test_audit_manager.py

"""
Audit Manager
=============

Central coordinator for the unified audit trail system.

AuditManager provides a high-level API for:
- Creating and managing threads (with automatic correlation)
- Logging complete LLM interactions
- Tracking agent spawning and delegation
- Recording human-in-the-loop interactions
- Verifying audit trail integrity

Usage:
    ```python
    audit = AuditManager(project_path)

    # Create root thread (user-initiated)
    thread_id = audit.create_root_thread(
        name="implement-feature",
        description="Implement user authentication"
    )

    # Log an LLM interaction
    audit.log_llm_interaction(
        thread_id=thread_id,
        system_prompt="You are an expert...",
        user_message="Implement the login flow",
        response="I'll create the following...",
        thinking="Let me analyze the requirements...",
    )

    # Spawn a child agent for delegation
    child_id = audit.spawn_child_thread(
        parent_thread_id=thread_id,
        name="security-review",
        reason="Delegating security analysis"
    )

    # Log human interaction
    audit.log_human_interaction(
        thread_id=thread_id,
        prompt="Should we use OAuth or JWT?",
        response="Use JWT for this use case",
    )

    # Verify integrity
    result = audit.verify_thread(thread_id)
    print(f"Integrity: {result.valid}")
    ```
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .conversation_archive import ConversationArchive, ConversationTurn, ToolCallDetail
from .integrity_chain import ChainVerificationResult, IntegrityChain, verify_thread_integrity
from .thread_correlator import SpawnType, ThreadCorrelator, ThreadInfo, ThreadStatus
from .transaction_logger import (
    TokenUsage,
    ToolCallRecord,
    TransactionLogger,
    TransactionRecord,
    TransactionType,
)


class AuditManager:
    """
    Central coordinator for unified audit trail.

    Manages:
    - Thread lifecycle (create, start, complete)
    - Transaction logging with integrity chain
    - Conversation archival
    - Thread correlation for delegation
    - Human interaction recording
    """

    def __init__(self, project_path: Path):
        """
        Initialize audit manager.

        Args:
            project_path: Root project directory
        """
        self.project_path = Path(project_path).resolve()
        self.audit_dir = self.project_path / ".agentforge" / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        self.correlator = ThreadCorrelator(self.project_path)

        # Cache of active loggers
        self._loggers: dict[str, TransactionLogger] = {}
        self._archives: dict[str, ConversationArchive] = {}
        self._chains: dict[str, IntegrityChain] = {}

    def create_root_thread(
        self,
        name: str,
        description: str | None = None,
        thread_type: str = "pipeline",
        thread_id: str | None = None,
    ) -> str:
        """
        Create a new root thread (user-initiated execution).

        Args:
            name: Human-readable name for the thread
            description: Description of the thread's purpose
            thread_type: Type of thread (pipeline, agent, task)
            thread_id: Optional specific thread ID (generated if not provided)

        Returns:
            Created thread ID
        """
        if thread_id is None:
            thread_id = self._generate_thread_id(thread_type)

        self.correlator.create_thread(
            thread_id=thread_id,
            thread_type=thread_type,
            name=name,
            description=description,
        )

        self.correlator.start_thread(thread_id)

        return thread_id

    def spawn_child_thread(
        self,
        parent_thread_id: str,
        name: str,
        reason: str,
        description: str | None = None,
        thread_type: str = "agent",
        spawn_type: SpawnType = SpawnType.DELEGATION,
        delegated_task: str | None = None,
        delegated_context: dict[str, Any] | None = None,
        thread_id: str | None = None,
    ) -> str:
        """
        Spawn a child thread for delegation.

        This is called when an agent needs to spawn a sub-agent
        to handle a portion of the work.

        Args:
            parent_thread_id: ID of the parent thread
            name: Name for the child thread
            reason: Why this thread is being spawned
            description: Description of child's purpose
            thread_type: Type of child thread
            spawn_type: Type of spawn (delegation, parallel, retry)
            delegated_task: Task description passed to child
            delegated_context: Context passed to child
            thread_id: Optional specific thread ID

        Returns:
            Created child thread ID
        """
        if thread_id is None:
            thread_id = self._generate_thread_id(thread_type)

        self.correlator.create_thread(
            thread_id=thread_id,
            parent_thread_id=parent_thread_id,
            thread_type=thread_type,
            name=name,
            description=description,
            spawn_type=spawn_type,
            spawn_reason=reason,
        )

        # Log spawn as transaction in parent
        parent_logger = self._get_logger(parent_thread_id)
        parent_logger.log_spawn(
            spawned_thread_id=thread_id,
            reason=reason,
            context={
                "delegated_task": delegated_task,
                "delegated_context": delegated_context,
            },
        )

        self.correlator.start_thread(thread_id)

        return thread_id

    def spawn_parallel_group(
        self,
        parent_thread_id: str,
        tasks: list[dict[str, Any]],
        group_name: str | None = None,
    ) -> list[str]:
        """
        Spawn a group of parallel child threads.

        Args:
            parent_thread_id: ID of the parent thread
            tasks: List of task definitions with 'name', 'description'
            group_name: Optional name for the parallel group

        Returns:
            List of created child thread IDs
        """
        group_id = group_name or f"parallel-{uuid.uuid4().hex[:8]}"

        # Add thread_id to each task
        for i, task in enumerate(tasks):
            task["thread_id"] = self._generate_thread_id("parallel")

        threads = self.correlator.create_parallel_group(
            parent_thread_id=parent_thread_id,
            group_id=group_id,
            tasks=tasks,
            spawn_type=SpawnType.PARALLEL,
        )

        # Log spawn as transaction in parent
        parent_logger = self._get_logger(parent_thread_id)
        parent_logger.log_spawn(
            spawned_thread_id=f"group:{group_id}",
            reason=f"Parallel execution of {len(tasks)} tasks",
            context={
                "parallel_group_id": group_id,
                "task_count": len(tasks),
                "task_names": [t.get("name") for t in tasks],
            },
        )

        # Start all child threads
        for thread in threads:
            self.correlator.start_thread(thread.thread_id)

        return [t.thread_id for t in threads]

    def log_llm_interaction(
        self,
        thread_id: str,
        system_prompt: str,
        user_message: str,
        response: str,
        model: str = "claude-sonnet-4-20250514",
        thinking: str | None = None,
        action_name: str | None = None,
        action_params: dict[str, Any] | None = None,
        action_result: dict[str, Any] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        tokens: TokenUsage | None = None,
        duration_ms: int = 0,
        stage_name: str | None = None,
        pipeline_id: str | None = None,
    ) -> str:
        """
        Log a complete LLM interaction.

        This captures the full prompt, response, thinking, and parsed action
        for complete reproducibility.

        Args:
            thread_id: Thread to log to
            system_prompt: Full system prompt
            user_message: Complete user message
            response: Full assistant response
            model: Model used
            thinking: Extended thinking content
            action_name: Parsed action name
            action_params: Parsed action parameters
            action_result: Action execution result
            tool_calls: Tool calls made during interaction
            tokens: Token usage breakdown
            duration_ms: Interaction duration
            stage_name: Pipeline stage if applicable
            pipeline_id: Pipeline ID if applicable

        Returns:
            Transaction ID
        """
        tokens = tokens or TokenUsage()
        # Convert tool_calls to ToolCallRecord
        tool_records = []
        if tool_calls:
            for tc in tool_calls:
                tool_records.append(
                    ToolCallRecord(
                        tool_name=tc.get("tool_name", "unknown"),
                        input_params=tc.get("input_params", {}),
                        output=tc.get("output"),
                        duration_ms=tc.get("duration_ms", 0),
                        success=tc.get("success", True),
                        error=tc.get("error"),
                    )
                )

        # Log transaction
        logger = self._get_logger(thread_id)
        record = logger.log_llm_call(
            request={
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
                "model": model,
            },
            response=response,
            thinking=thinking,
            action_name=action_name,
            action_params=action_params,
            action_result=action_result,
            tool_calls=tool_records,
            tokens=tokens,
            duration_ms=duration_ms,
            stage_name=stage_name,
        )

        # Archive full conversation
        archive = self._get_archive(thread_id)
        tool_details = [
            ToolCallDetail(
                tool_name=tr.tool_name,
                input_params=tr.input_params,
                output=tr.output,
                success=tr.success,
                error=tr.error,
                duration_ms=tr.duration_ms,
            )
            for tr in tool_records
        ]

        archive.archive_turn(
            system_prompt=system_prompt,
            user_message=user_message,
            response=response,
            model=model,
            thread_id=thread_id,
            thinking=thinking,
            tool_calls=tool_details,
            tokens=tokens,
            duration_ms=duration_ms,
            stage_name=stage_name,
            pipeline_id=pipeline_id,
        )

        return record.transaction_id

    def log_human_interaction(
        self,
        thread_id: str,
        prompt: str,
        response: str | None,
        context: dict[str, Any] | None = None,
        duration_ms: int = 0,
    ) -> str:
        """
        Log a human-in-the-loop interaction.

        Captures the full context at the time of escalation,
        the question asked, and the human's response.

        Args:
            thread_id: Thread to log to
            prompt: Question/request shown to human
            response: Human's response
            context: Full context at time of interaction
            duration_ms: Time human took to respond

        Returns:
            Transaction ID
        """
        logger = self._get_logger(thread_id)
        record = logger.log_human_interaction(
            prompt=prompt,
            response=response,
            context=context,
            duration_ms=duration_ms,
        )

        return record.transaction_id

    def complete_thread(
        self,
        thread_id: str,
        outcome: str = "success",
        error: str | None = None,
    ) -> None:
        """
        Mark a thread as completed.

        Aggregates statistics and updates the thread manifest.

        Args:
            thread_id: Thread to complete
            outcome: Outcome status (success, failed)
            error: Error message if failed
        """
        # Aggregate statistics from logger and archive
        logger = self._get_logger(thread_id)
        archive = self._get_archive(thread_id)

        transaction_count = len(logger.list_transactions())
        token_totals = archive.get_total_tokens()

        # Get total duration from transactions
        total_duration = 0
        for tx_id in logger.list_transactions():
            tx = logger.get_transaction(tx_id)
            if tx:
                total_duration += tx.duration_ms

        self.correlator.complete_thread(
            thread_id=thread_id,
            outcome=outcome,
            error=error,
            transaction_count=transaction_count,
            total_tokens=token_totals.get("total", 0),
            total_duration_ms=total_duration,
        )

        # Clean up caches
        self._loggers.pop(thread_id, None)
        self._archives.pop(thread_id, None)
        self._chains.pop(thread_id, None)

    def verify_thread(self, thread_id: str) -> ChainVerificationResult:
        """
        Verify integrity of a thread's audit trail.

        Args:
            thread_id: Thread to verify

        Returns:
            Verification result
        """
        thread_dir = self.audit_dir / "threads" / thread_id
        return verify_thread_integrity(thread_dir)

    def get_thread_info(self, thread_id: str) -> ThreadInfo | None:
        """Get thread information."""
        return self.correlator.get_thread(thread_id)

    def get_thread_tree(self, thread_id: str) -> dict[str, Any]:
        """Get complete thread tree from root."""
        return self.correlator.get_thread_tree(thread_id)

    def get_ancestry(self, thread_id: str) -> list[ThreadInfo]:
        """Get ancestry chain from thread to root."""
        return self.correlator.get_ancestry(thread_id)

    def get_transactions(self, thread_id: str) -> list[str]:
        """List transaction IDs for a thread."""
        logger = self._get_logger(thread_id)
        return logger.list_transactions()

    def get_transaction(self, thread_id: str, transaction_id: str) -> TransactionRecord | None:
        """Get a specific transaction."""
        logger = self._get_logger(thread_id)
        return logger.get_transaction(transaction_id)

    def get_conversation_turns(self, thread_id: str) -> list[str]:
        """List conversation turn IDs for a thread."""
        archive = self._get_archive(thread_id)
        return archive.list_turns()

    def get_conversation_content(self, thread_id: str, turn_id: str) -> str | None:
        """Get full conversation content for a turn."""
        archive = self._get_archive(thread_id)
        return archive.get_turn_content(turn_id)

    def list_root_threads(self) -> list[str]:
        """List all root thread IDs."""
        index = self.correlator._load_index()
        return index.get("root_threads", [])

    def get_summary(self, thread_id: str) -> dict[str, Any]:
        """
        Get comprehensive summary of a thread.

        Includes thread info, statistics, and child thread summaries.
        """
        info = self.get_thread_info(thread_id)
        if not info:
            return {}

        summary = info.to_dict()

        # Add transaction count
        logger = self._get_logger(thread_id)
        summary["transaction_count"] = len(logger.list_transactions())

        # Add token summary
        archive = self._get_archive(thread_id)
        summary["token_summary"] = archive.get_total_tokens()

        # Add children summaries
        if info.child_thread_ids:
            summary["children_summary"] = []
            for child_id in info.child_thread_ids:
                child_info = self.get_thread_info(child_id)
                if child_info:
                    summary["children_summary"].append(
                        {
                            "thread_id": child_id,
                            "name": child_info.name,
                            "status": child_info.status.value,
                            "outcome": child_info.outcome,
                        }
                    )

        return summary

    def _get_logger(self, thread_id: str) -> TransactionLogger:
        """Get or create transaction logger for thread."""
        if thread_id not in self._loggers:
            self._loggers[thread_id] = TransactionLogger(self.project_path, thread_id)
        return self._loggers[thread_id]

    def _get_archive(self, thread_id: str) -> ConversationArchive:
        """Get or create conversation archive for thread."""
        if thread_id not in self._archives:
            thread_dir = self.audit_dir / "threads" / thread_id
            self._archives[thread_id] = ConversationArchive(thread_dir)
        return self._archives[thread_id]

    def _get_chain(self, thread_id: str) -> IntegrityChain:
        """Get or create integrity chain for thread."""
        if thread_id not in self._chains:
            thread_dir = self.audit_dir / "threads" / thread_id
            self._chains[thread_id] = IntegrityChain(thread_dir)
        return self._chains[thread_id]

    def _generate_thread_id(self, thread_type: str) -> str:
        """Generate a unique thread ID."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"{thread_type}-{timestamp}-{short_uuid}"
