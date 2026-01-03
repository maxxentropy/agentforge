# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: audit-manager-tests

"""Tests for AuditManager - central audit trail coordinator."""

import pytest

from agentforge.core.audit import AuditManager
from agentforge.core.audit.thread_correlator import SpawnType, ThreadStatus


class TestAuditManagerThreads:
    """Tests for thread management."""

    def test_create_root_thread(self, tmp_path):
        """Create a root thread."""
        audit = AuditManager(tmp_path)

        thread_id = audit.create_root_thread(
            name="Test Pipeline",
            description="A test pipeline execution",
            thread_type="pipeline",
        )

        assert thread_id is not None, "Expected thread_id is not None"
        assert "pipeline" in thread_id, "Expected 'pipeline' in thread_id"

        info = audit.get_thread_info(thread_id)
        assert info is not None, "Expected info is not None"
        assert info.name == "Test Pipeline", "Expected info.name to equal 'Test Pipeline'"
        assert info.status == ThreadStatus.RUNNING, "Expected info.status to equal ThreadStatus.RUNNING"# Auto-started

    def test_spawn_child_thread(self, tmp_path):
        """Spawn a child thread for delegation."""
        audit = AuditManager(tmp_path)

        parent_id = audit.create_root_thread(name="Parent")

        child_id = audit.spawn_child_thread(
            parent_thread_id=parent_id,
            name="Security Review",
            reason="Delegating security analysis",
            thread_type="agent",
        )

        assert child_id is not None, "Expected child_id is not None"

        child_info = audit.get_thread_info(child_id)
        assert child_info.parent_thread_id == parent_id, "Expected child_info.parent_thread_id to equal parent_id"
        assert child_info.name == "Security Review", "Expected child_info.name to equal 'Security Review'"

        # Parent should have spawn transaction
        parent_txs = audit.get_transactions(parent_id)
        assert len(parent_txs) >= 1, "Expected len(parent_txs) >= 1"

    def test_spawn_parallel_group(self, tmp_path):
        """Spawn parallel execution group."""
        audit = AuditManager(tmp_path)

        parent_id = audit.create_root_thread(name="Parent")

        tasks = [
            {"name": "Code Review"},
            {"name": "Security Scan"},
            {"name": "Style Check"},
        ]

        child_ids = audit.spawn_parallel_group(
            parent_thread_id=parent_id,
            tasks=tasks,
            group_name="quality-checks",
        )

        assert len(child_ids) == 3, "Expected len(child_ids) to equal 3"

        # All children should reference same parallel group
        for child_id in child_ids:
            info = audit.get_thread_info(child_id)
            assert info.parallel_group_id == "quality-checks", "Expected info.parallel_group_id to equal 'quality-checks'"
            assert info.parent_thread_id == parent_id, "Expected info.parent_thread_id to equal parent_id"

    def test_complete_thread(self, tmp_path):
        """Complete a thread with statistics."""
        audit = AuditManager(tmp_path)

        thread_id = audit.create_root_thread(name="Test")

        # Log some activity
        audit.log_llm_interaction(
            thread_id=thread_id,
            system_prompt="You are helpful.",
            user_message="Hello",
            response="Hi there!",
            tokens_input=100,
            tokens_output=50,
        )

        audit.complete_thread(thread_id, outcome="success")

        info = audit.get_thread_info(thread_id)
        assert info.status == ThreadStatus.COMPLETED, "Expected info.status to equal ThreadStatus.COMPLETED"
        assert info.outcome == "success", "Expected info.outcome to equal 'success'"


class TestAuditManagerLogging:
    """Tests for logging operations."""

    def test_log_llm_interaction(self, tmp_path):
        """Log complete LLM interaction."""
        audit = AuditManager(tmp_path)
        thread_id = audit.create_root_thread(name="Test")

        tx_id = audit.log_llm_interaction(
            thread_id=thread_id,
            system_prompt="You are an expert Python developer.",
            user_message="Implement a binary search function.",
            response="Here's a binary search implementation...",
            thinking="I need to consider edge cases...",
            action_name="write_code",
            action_params={"file": "search.py"},
            tokens_input=500,
            tokens_output=200,
            tokens_thinking=100,
            duration_ms=3000,
            stage_name="implement",
        )

        assert tx_id is not None, "Expected tx_id is not None"
        assert tx_id.startswith("TX-"), "Expected tx_id.startswith() to be truthy"

        # Verify transaction exists
        tx = audit.get_transaction(thread_id, tx_id)
        assert tx is not None, "Expected tx is not None"

        # Verify conversation archived
        turns = audit.get_conversation_turns(thread_id)
        assert len(turns) == 1, "Expected len(turns) to equal 1"

        content = audit.get_conversation_content(thread_id, turns[0])
        assert "binary search" in content, "Expected 'binary search' in content"

    def test_log_llm_interaction_with_tool_calls(self, tmp_path):
        """Log LLM interaction with tool calls."""
        audit = AuditManager(tmp_path)
        thread_id = audit.create_root_thread(name="Test")

        tool_calls = [
            {
                "tool_name": "read_file",
                "input_params": {"path": "main.py"},
                "output": "file content...",
                "success": True,
                "duration_ms": 50,
            },
            {
                "tool_name": "write_file",
                "input_params": {"path": "new.py", "content": "..."},
                "output": None,
                "success": True,
                "duration_ms": 30,
            },
        ]

        tx_id = audit.log_llm_interaction(
            thread_id=thread_id,
            system_prompt="...",
            user_message="...",
            response="...",
            tool_calls=tool_calls,
        )

        tx = audit.get_transaction(thread_id, tx_id)
        assert len(tx.tool_calls) == 2, "Expected len(tx.tool_calls) to equal 2"

    def test_log_human_interaction(self, tmp_path):
        """Log human-in-the-loop interaction."""
        audit = AuditManager(tmp_path)
        thread_id = audit.create_root_thread(name="Test")

        tx_id = audit.log_human_interaction(
            thread_id=thread_id,
            prompt="Should we use OAuth or JWT for authentication?",
            response="Use JWT - we need stateless auth.",
            context={"current_auth": "none", "requirements": ["scalable"]},
            duration_ms=30000,
        )

        assert tx_id is not None, "Expected tx_id is not None"

        tx = audit.get_transaction(thread_id, tx_id)
        assert tx.human_prompt == "Should we use OAuth or JWT for authentication?", "Expected tx.human_prompt to equal 'Should we use OAuth or JWT..."
        assert tx.human_response == "Use JWT - we need stateless auth.", "Expected tx.human_response to equal 'Use JWT - we need stateles..."


class TestAuditManagerIntegrity:
    """Tests for integrity verification."""

    def test_verify_thread(self, tmp_path):
        """Verify thread integrity."""
        audit = AuditManager(tmp_path)
        thread_id = audit.create_root_thread(name="Test")

        # Log some transactions
        audit.log_llm_interaction(
            thread_id=thread_id,
            system_prompt="...",
            user_message="First",
            response="...",
        )
        audit.log_llm_interaction(
            thread_id=thread_id,
            system_prompt="...",
            user_message="Second",
            response="...",
        )

        result = audit.verify_thread(thread_id)

        assert result.valid is True, "Expected result.valid is True"
        assert result.total_blocks >= 2, "Expected result.total_blocks >= 2"


class TestAuditManagerQueries:
    """Tests for query operations."""

    def test_get_thread_tree(self, tmp_path):
        """Get complete thread tree."""
        audit = AuditManager(tmp_path)

        root_id = audit.create_root_thread(name="Root")
        child1_id = audit.spawn_child_thread(
            parent_thread_id=root_id,
            name="Child 1",
            reason="delegation",
        )
        child2_id = audit.spawn_child_thread(
            parent_thread_id=root_id,
            name="Child 2",
            reason="delegation",
        )
        audit.spawn_child_thread(
            parent_thread_id=child1_id,
            name="Grandchild",
            reason="sub-delegation",
        )

        tree = audit.get_thread_tree(root_id)

        assert tree["thread_id"] == root_id, "Expected tree['thread_id'] to equal root_id"
        assert len(tree["children"]) == 2, "Expected len(tree['children']) to equal 2"

    def test_get_ancestry(self, tmp_path):
        """Get ancestry chain."""
        audit = AuditManager(tmp_path)

        root_id = audit.create_root_thread(name="Root")
        child_id = audit.spawn_child_thread(
            parent_thread_id=root_id,
            name="Child",
            reason="delegation",
        )
        grandchild_id = audit.spawn_child_thread(
            parent_thread_id=child_id,
            name="Grandchild",
            reason="delegation",
        )

        ancestry = audit.get_ancestry(grandchild_id)

        assert len(ancestry) == 3, "Expected len(ancestry) to equal 3"
        assert ancestry[0].thread_id == grandchild_id, "Expected ancestry[0].thread_id to equal grandchild_id"
        assert ancestry[1].thread_id == child_id, "Expected ancestry[1].thread_id to equal child_id"
        assert ancestry[2].thread_id == root_id, "Expected ancestry[2].thread_id to equal root_id"

    def test_list_root_threads(self, tmp_path):
        """List all root threads."""
        audit = AuditManager(tmp_path)

        id1 = audit.create_root_thread(name="Pipeline 1")
        id2 = audit.create_root_thread(name="Pipeline 2")

        roots = audit.list_root_threads()

        assert id1 in roots, "Expected id1 in roots"
        assert id2 in roots, "Expected id2 in roots"

    def test_get_summary(self, tmp_path):
        """Get thread summary with statistics."""
        audit = AuditManager(tmp_path)
        thread_id = audit.create_root_thread(name="Test Pipeline")

        # Log activity
        audit.log_llm_interaction(
            thread_id=thread_id,
            system_prompt="...",
            user_message="...",
            response="...",
            tokens_input=100,
            tokens_output=50,
        )

        child_id = audit.spawn_child_thread(
            parent_thread_id=thread_id,
            name="Child",
            reason="delegation",
        )

        summary = audit.get_summary(thread_id)

        assert summary["name"] == "Test Pipeline", "Expected summary['name'] to equal 'Test Pipeline'"
        assert summary["transaction_count"] >= 1, "Expected summary['transaction_count'] >= 1"
        assert "token_summary" in summary, "Expected 'token_summary' in summary"
        assert len(summary.get("children_summary", [])) == 1, "Expected len(summary.get('children_s... to equal 1"


class TestAuditManagerEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow(self, tmp_path):
        """Test complete audit trail workflow."""
        audit = AuditManager(tmp_path)

        # 1. Create root pipeline
        pipeline_id = audit.create_root_thread(
            name="implement-feature",
            description="Implement user authentication",
            thread_type="pipeline",
        )

        # 2. Log initial analysis
        audit.log_llm_interaction(
            thread_id=pipeline_id,
            system_prompt="You are an architecture expert.",
            user_message="Analyze the authentication requirements.",
            response="I recommend using JWT with refresh tokens...",
            thinking="Considering stateless vs stateful auth...",
            tokens_input=500,
            tokens_output=200,
            stage_name="analyze",
        )

        # 3. Human escalation
        audit.log_human_interaction(
            thread_id=pipeline_id,
            prompt="Should we support social login?",
            response="Yes, add Google and GitHub OAuth.",
        )

        # 4. Spawn parallel tasks
        child_ids = audit.spawn_parallel_group(
            parent_thread_id=pipeline_id,
            tasks=[
                {"name": "JWT Implementation"},
                {"name": "OAuth Integration"},
            ],
            group_name="auth-impl",
        )

        # 5. Work in child threads
        for child_id in child_ids:
            audit.log_llm_interaction(
                thread_id=child_id,
                system_prompt="...",
                user_message="Implement the assigned task.",
                response="Implementation complete.",
                tokens_input=300,
                tokens_output=400,
            )
            audit.complete_thread(child_id, outcome="success")

        # 6. Complete pipeline
        audit.complete_thread(pipeline_id, outcome="success")

        # 7. Verify integrity
        result = audit.verify_thread(pipeline_id)
        assert result.valid is True, "Expected result.valid is True"

        # 8. Check summary
        summary = audit.get_summary(pipeline_id)
        assert summary["status"] == "completed", "Expected summary['status'] to equal 'completed'"
        assert len(summary["children_summary"]) == 2, "Expected len(summary['children_summa... to equal 2"
        assert all(c["outcome"] == "success" for c in summary["children_summary"]), "Expected all() to be truthy"

        # 9. Check ancestry
        ancestry = audit.get_ancestry(child_ids[0])
        assert len(ancestry) == 2, "Expected len(ancestry) to equal 2"
        assert ancestry[1].thread_id == pipeline_id, "Expected ancestry[1].thread_id to equal pipeline_id"
