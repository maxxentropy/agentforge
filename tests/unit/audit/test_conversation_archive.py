# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: conversation-archive-tests

"""Tests for ConversationArchive - full LLM conversation storage."""

import pytest

from agentforge.core.audit.conversation_archive import (
    ConversationArchive,
    ConversationTurn,
    ToolCallDetail,
)


class TestToolCallDetail:
    """Tests for ToolCallDetail."""

    def test_tool_call_to_dict(self):
        """Serialize tool call detail."""
        tc = ToolCallDetail(
            tool_name="read_file",
            input_params={"path": "main.py"},
            output="file contents here",
            success=True,
            duration_ms=100,
        )

        data = tc.to_dict()

        assert data["tool_name"] == "read_file", "Expected data['tool_name'] to equal 'read_file'"
        assert data["success"] is True, "Expected data['success'] is True"
        assert data["duration_ms"] == 100, "Expected data['duration_ms'] to equal 100"

    def test_tool_call_truncates_large_output(self):
        """Large outputs are truncated in to_dict."""
        large_output = "x" * 1000
        tc = ToolCallDetail(
            tool_name="read_file",
            input_params={},
            output=large_output,
            success=True,
        )

        data = tc.to_dict()

        assert len(data["output"]) == 500, "Expected len(data['output']) to equal 500"
        assert data["output_length"] == 1000, "Expected data['output_length'] to equal 1000"


class TestConversationTurn:
    """Tests for ConversationTurn."""

    def test_turn_creation(self):
        """Create a conversation turn."""
        turn = ConversationTurn(
            turn_id="TURN-0001",
            thread_id="thread-001",
            sequence=1,
            system_prompt="You are helpful.",
            user_message="Help me code.",
            response="Sure, I can help.",
            model="claude-sonnet-4-20250514",
            tokens_input=100,
            tokens_output=50,
        )

        assert turn.turn_id == "TURN-0001", "Expected turn.turn_id to equal 'TURN-0001'"
        assert turn.model == "claude-sonnet-4-20250514", "Expected turn.model to equal 'claude-sonnet-4-20250514'"

    def test_turn_to_dict(self):
        """Serialize turn to dictionary."""
        turn = ConversationTurn(
            turn_id="TURN-0001",
            thread_id="thread-001",
            sequence=1,
            system_prompt="System",
            user_message="User",
            response="Response",
            model="claude-sonnet-4-20250514",
            tokens_input=100,
            tokens_output=50,
        )

        data = turn.to_dict()

        assert data["turn_id"] == "TURN-0001", "Expected data['turn_id'] to equal 'TURN-0001'"
        assert data["tokens"]["input"] == 100, "Expected data['tokens']['input'] to equal 100"
        assert data["content_lengths"]["system_prompt"] == 6, "Expected data['content_lengths']['sy... to equal 6"

    def test_turn_to_markdown(self):
        """Format turn as markdown."""
        turn = ConversationTurn(
            turn_id="TURN-0001",
            thread_id="thread-001",
            sequence=1,
            system_prompt="You are helpful.",
            user_message="Help me.",
            response="Sure!",
            model="claude-sonnet-4-20250514",
        )

        md = turn.to_markdown()

        assert "# Conversation Turn TURN-0001" in md, "Expected '# Conversation Turn TURN-0... in md"
        assert "You are helpful." in md, "Expected 'You are helpful.' in md"
        assert "Help me." in md, "Expected 'Help me.' in md"
        assert "Sure!" in md, "Expected 'Sure!' in md"

    def test_turn_with_tool_calls(self):
        """Turn with tool calls."""
        turn = ConversationTurn(
            turn_id="TURN-0001",
            thread_id="thread-001",
            sequence=1,
            system_prompt="...",
            user_message="...",
            response="...",
            model="claude-sonnet-4-20250514",
            tool_calls=[
                ToolCallDetail(
                    tool_name="read_file",
                    input_params={"path": "main.py"},
                    output="contents",
                    success=True,
                ),
            ],
        )

        data = turn.to_dict()

        assert data["tool_call_count"] == 1, "Expected data['tool_call_count'] to equal 1"
        assert data["tool_calls"][0]["tool_name"] == "read_file", "Expected data['tool_calls'][0]['tool... to equal 'read_file'"


class TestConversationArchive:
    """Tests for ConversationArchive."""

    def test_archive_turn(self, tmp_path):
        """Archive a conversation turn."""
        archive = ConversationArchive(tmp_path)

        turn = archive.archive_turn(
            system_prompt="You are an expert.",
            user_message="Analyze this code.",
            response="Here is my analysis...",
            model="claude-sonnet-4-20250514",
            thread_id="thread-001",
            tokens_input=100,
            tokens_output=200,
            duration_ms=1500,
        )

        assert turn.turn_id == "TURN-0001", "Expected turn.turn_id to equal 'TURN-0001'"
        assert turn.thread_id == "thread-001", "Expected turn.thread_id to equal 'thread-001'"

        # Verify files created
        assert (tmp_path / "conversations" / "TURN-0001.md").exists(), "Expected (tmp_path / 'conversations'...() to be truthy"
        assert (tmp_path / "conversations" / "TURN-0001.yaml").exists(), "Expected (tmp_path / 'conversations'...() to be truthy"

    def test_sequential_turn_ids(self, tmp_path):
        """Turns get sequential IDs."""
        archive = ConversationArchive(tmp_path)

        t1 = archive.archive_turn("...", "...", "...", "model", "thread")
        t2 = archive.archive_turn("...", "...", "...", "model", "thread")
        t3 = archive.archive_turn("...", "...", "...", "model", "thread")

        assert t1.turn_id == "TURN-0001", "Expected t1.turn_id to equal 'TURN-0001'"
        assert t2.turn_id == "TURN-0002", "Expected t2.turn_id to equal 'TURN-0002'"
        assert t3.turn_id == "TURN-0003", "Expected t3.turn_id to equal 'TURN-0003'"

    def test_list_turns(self, tmp_path):
        """List all turns."""
        archive = ConversationArchive(tmp_path)

        archive.archive_turn("...", "...", "...", "model", "thread")
        archive.archive_turn("...", "...", "...", "model", "thread")

        turns = archive.list_turns()

        assert turns == ["TURN-0001", "TURN-0002"], "Expected turns to equal ['TURN-0001', 'TURN-0002']"

    def test_get_turn_content(self, tmp_path):
        """Get full markdown content of turn."""
        archive = ConversationArchive(tmp_path)

        archive.archive_turn(
            system_prompt="System prompt here",
            user_message="User message here",
            response="Response here",
            model="claude-sonnet-4-20250514",
            thread_id="thread-001",
        )

        content = archive.get_turn_content("TURN-0001")

        assert content is not None, "Expected content is not None"
        assert "System prompt here" in content, "Expected 'System prompt here' in content"
        assert "User message here" in content, "Expected 'User message here' in content"
        assert "Response here" in content, "Expected 'Response here' in content"

    def test_get_summary(self, tmp_path):
        """Get archive summary."""
        archive = ConversationArchive(tmp_path)

        archive.archive_turn("...", "...", "...", "model", "thread", tokens_input=100)
        archive.archive_turn("...", "...", "...", "model", "thread", tokens_input=200)

        summary = archive.get_summary()

        assert summary["total_turns"] == 2, "Expected summary['total_turns'] to equal 2"
        assert len(summary["turns"]) == 2, "Expected len(summary['turns']) to equal 2"

    def test_get_total_tokens(self, tmp_path):
        """Get total token usage."""
        archive = ConversationArchive(tmp_path)

        archive.archive_turn(
            "...", "...", "...", "model", "thread",
            tokens_input=100, tokens_output=50
        )
        archive.archive_turn(
            "...", "...", "...", "model", "thread",
            tokens_input=200, tokens_output=100
        )

        totals = archive.get_total_tokens()

        assert totals["input"] == 300, "Expected totals['input'] to equal 300"
        assert totals["output"] == 150, "Expected totals['output'] to equal 150"
        assert totals["total"] == 450, "Expected totals['total'] to equal 450"

    def test_persistence_across_instances(self, tmp_path):
        """Archive persists across instances."""
        archive1 = ConversationArchive(tmp_path)
        archive1.archive_turn("...", "...", "...", "model", "thread")

        archive2 = ConversationArchive(tmp_path)
        t2 = archive2.archive_turn("...", "...", "...", "model", "thread")

        assert t2.turn_id == "TURN-0002", "Expected t2.turn_id to equal 'TURN-0002'"
        assert len(archive2.list_turns()) == 2, "Expected len(archive2.list_turns()) to equal 2"

    def test_archive_with_tool_calls(self, tmp_path):
        """Archive turn with tool calls."""
        archive = ConversationArchive(tmp_path)

        tool_calls = [
            ToolCallDetail(
                tool_name="read_file",
                input_params={"path": "main.py"},
                output="file contents",
                success=True,
                duration_ms=50,
            ),
        ]

        turn = archive.archive_turn(
            system_prompt="...",
            user_message="...",
            response="...",
            model="claude-sonnet-4-20250514",
            thread_id="thread-001",
            tool_calls=tool_calls,
        )

        assert len(turn.tool_calls) == 1, "Expected len(turn.tool_calls) to equal 1"

        # Verify in markdown
        content = archive.get_turn_content("TURN-0001")
        assert "read_file" in content, "Expected 'read_file' in content"

    def test_archive_with_stage_context(self, tmp_path):
        """Archive turn with pipeline context."""
        archive = ConversationArchive(tmp_path)

        turn = archive.archive_turn(
            system_prompt="...",
            user_message="...",
            response="...",
            model="claude-sonnet-4-20250514",
            thread_id="thread-001",
            stage_name="intake",
            pipeline_id="pipeline-001",
        )

        assert turn.stage_name == "intake", "Expected turn.stage_name to equal 'intake'"
        assert turn.pipeline_id == "pipeline-001", "Expected turn.pipeline_id to equal 'pipeline-001'"

        summary = archive.get_summary()
        assert summary["turns"][0]["stage_name"] == "intake", "Expected summary['turns'][0]['stage_... to equal 'intake'"
