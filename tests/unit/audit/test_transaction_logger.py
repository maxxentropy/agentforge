# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: transaction-logger-tests

"""Tests for TransactionLogger - full LLM conversation capture."""

import yaml
import pytest

from agentforge.core.audit.transaction_logger import (
    ToolCallRecord,
    TransactionLogger,
    TransactionRecord,
    TransactionType,
)


class TestTransactionLogger:
    """Tests for TransactionLogger."""

    def test_log_llm_call(self, tmp_path):
        """Log a complete LLM interaction."""
        logger = TransactionLogger(tmp_path, "test-thread")

        record = logger.log_llm_call(
            request={"system": "You are helpful.", "messages": [{"role": "user", "content": "Hello"}]},
            response="Hello! How can I help you?",
            thinking="User is greeting, I should respond politely.",
            action_name="respond",
            action_params={"message": "Hello!"},
            tokens_input=100,
            tokens_output=50,
            tokens_thinking=30,
            duration_ms=1500,
            stage_name="clarify",
        )

        assert record.transaction_id == "TX-0001"
        assert record.thread_id == "test-thread"
        assert record.transaction_type == TransactionType.LLM_CALL
        assert record.tokens_input == 100
        assert record.stage_name == "clarify"

        # Verify file was created
        tx_path = tmp_path / ".agentforge" / "audit" / "threads" / "test-thread" / "transactions" / "TX-0001.yaml"
        assert tx_path.exists()

        # Verify content
        data = yaml.safe_load(tx_path.read_text())
        assert data["transaction_type"] == "llm_call"
        assert data["stage_name"] == "clarify"

    def test_log_llm_call_creates_llm_file(self, tmp_path):
        """Full LLM content should be saved to separate file."""
        logger = TransactionLogger(tmp_path, "test-thread")

        logger.log_llm_call(
            request={"system": "You are an expert.", "messages": [{"role": "user", "content": "Analyze this code"}]},
            response="I'll analyze the code structure...",
        )

        llm_path = tmp_path / ".agentforge" / "audit" / "threads" / "test-thread" / "transactions" / "TX-0001-llm.md"
        assert llm_path.exists()

        content = llm_path.read_text()
        assert "You are an expert" in content
        assert "Analyze this code" in content
        assert "I'll analyze the code structure" in content

    def test_sequential_transaction_ids(self, tmp_path):
        """Transactions should have sequential IDs."""
        logger = TransactionLogger(tmp_path, "test-thread")

        r1 = logger.log_llm_call(request={}, response="First")
        r2 = logger.log_llm_call(request={}, response="Second")
        r3 = logger.log_llm_call(request={}, response="Third")

        assert r1.transaction_id == "TX-0001"
        assert r2.transaction_id == "TX-0002"
        assert r3.transaction_id == "TX-0003"

    def test_hash_chain_linking(self, tmp_path):
        """Each transaction should link to previous hash."""
        logger = TransactionLogger(tmp_path, "test-thread")

        r1 = logger.log_llm_call(request={}, response="First")
        r2 = logger.log_llm_call(request={}, response="Second")

        assert r1.previous_hash is None  # First in chain
        assert r2.previous_hash == r1.content_hash

    def test_log_spawn(self, tmp_path):
        """Log a spawn/delegation event."""
        logger = TransactionLogger(tmp_path, "parent-thread")

        record = logger.log_spawn(
            spawned_thread_id="child-thread",
            reason="Delegating security analysis",
            context={"task": "security review", "priority": "high"},
        )

        assert record.transaction_type == TransactionType.SPAWN
        assert record.spawned_thread_id == "child-thread"
        assert record.spawn_reason == "Delegating security analysis"

    def test_log_human_interaction(self, tmp_path):
        """Log a human-in-the-loop interaction."""
        logger = TransactionLogger(tmp_path, "test-thread")

        record = logger.log_human_interaction(
            prompt="Should we proceed with OAuth or JWT?",
            response="Use JWT for this application",
            context={"current_auth": "none", "requirements": ["stateless"]},
            duration_ms=45000,
        )

        assert record.transaction_type == TransactionType.HUMAN_INTERACTION
        assert record.human_prompt == "Should we proceed with OAuth or JWT?"
        assert record.human_response == "Use JWT for this application"
        assert record.duration_ms == 45000

    def test_tool_calls_in_transaction(self, tmp_path):
        """Log tool calls within an LLM interaction."""
        logger = TransactionLogger(tmp_path, "test-thread")

        tool_calls = [
            ToolCallRecord(
                tool_name="read_file",
                input_params={"path": "src/main.py"},
                output="file content...",
                duration_ms=50,
                success=True,
            ),
            ToolCallRecord(
                tool_name="write_file",
                input_params={"path": "src/new.py", "content": "..."},
                output=None,
                duration_ms=30,
                success=True,
            ),
        ]

        record = logger.log_llm_call(
            request={},
            response="Created the file",
            tool_calls=tool_calls,
        )

        assert len(record.tool_calls) == 2
        assert record.tool_calls[0].tool_name == "read_file"
        assert record.tool_calls[1].tool_name == "write_file"

    def test_list_transactions(self, tmp_path):
        """List all transactions in order."""
        logger = TransactionLogger(tmp_path, "test-thread")

        logger.log_llm_call(request={}, response="First")
        logger.log_llm_call(request={}, response="Second")
        logger.log_spawn(spawned_thread_id="child", reason="test")

        tx_list = logger.list_transactions()

        assert tx_list == ["TX-0001", "TX-0002", "TX-0003"]

    def test_get_transaction(self, tmp_path):
        """Retrieve a specific transaction."""
        logger = TransactionLogger(tmp_path, "test-thread")

        logger.log_llm_call(
            request={},
            response="Test response",
            action_name="test_action",
        )

        record = logger.get_transaction("TX-0001")

        assert record is not None
        assert record.transaction_id == "TX-0001"

    def test_get_full_llm_content(self, tmp_path):
        """Retrieve full LLM content for a transaction."""
        logger = TransactionLogger(tmp_path, "test-thread")

        logger.log_llm_call(
            request={"system": "Test system prompt"},
            response="Test response content",
        )

        content = logger.get_full_llm_content("TX-0001")

        assert content is not None
        assert "Test system prompt" in content
        assert "Test response content" in content

    def test_chain_file_updated(self, tmp_path):
        """Chain YAML file should be updated."""
        import yaml

        logger = TransactionLogger(tmp_path, "test-thread")

        logger.log_llm_call(request={}, response="First")
        logger.log_llm_call(request={}, response="Second")

        chain_path = tmp_path / ".agentforge" / "audit" / "threads" / "test-thread" / "chain.yaml"
        assert chain_path.exists()

        data = yaml.safe_load(chain_path.read_text())
        assert len(data["blocks"]) == 2
        assert data["blocks"][0]["block_id"] == "TX-0001"
        assert data["blocks"][1]["block_id"] == "TX-0002"

    def test_persistence_across_instances(self, tmp_path):
        """Logger should resume sequence across instances."""
        # First instance
        logger1 = TransactionLogger(tmp_path, "test-thread")
        logger1.log_llm_call(request={}, response="First")
        logger1.log_llm_call(request={}, response="Second")

        # Second instance
        logger2 = TransactionLogger(tmp_path, "test-thread")
        r3 = logger2.log_llm_call(request={}, response="Third")

        assert r3.transaction_id == "TX-0003"
        assert r3.previous_hash is not None  # Should link to TX-0002


class TestTransactionRecord:
    """Tests for TransactionRecord dataclass."""

    def test_to_dict(self):
        """Serialize transaction to dictionary."""
        record = TransactionRecord(
            transaction_id="TX-0001",
            thread_id="test-thread",
            sequence=1,
            transaction_type=TransactionType.LLM_CALL,
            stage_name="analyze",
            tokens_input=100,
            tokens_output=50,
            action_name="analyze_code",
            action_params={"file": "main.py"},
        )

        data = record.to_dict()

        assert data["transaction_id"] == "TX-0001"
        assert data["transaction_type"] == "llm_call"
        assert data["stage_name"] == "analyze"
        assert data["tokens"]["input"] == 100
        assert data["action"]["name"] == "analyze_code"


class TestToolCallRecord:
    """Tests for ToolCallRecord dataclass."""

    def test_tool_call_success(self):
        """Record successful tool call."""
        tc = ToolCallRecord(
            tool_name="read_file",
            input_params={"path": "test.py"},
            output="file content",
            duration_ms=50,
            success=True,
        )

        assert tc.tool_name == "read_file"
        assert tc.success is True
        assert tc.error is None

    def test_tool_call_failure(self):
        """Record failed tool call."""
        tc = ToolCallRecord(
            tool_name="write_file",
            input_params={"path": "/invalid/path"},
            output=None,
            duration_ms=10,
            success=False,
            error="Permission denied",
        )

        assert tc.success is False
        assert tc.error == "Permission denied"
