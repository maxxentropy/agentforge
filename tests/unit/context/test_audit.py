# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: audit-tests

"""
Tests for ContextAuditLogger.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from agentforge.core.context.audit import ContextAuditLogger


class TestContextAuditLogger:
    """Tests for ContextAuditLogger."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            yield project

    @pytest.fixture
    def logger(self, temp_project):
        """Create an audit logger."""
        return ContextAuditLogger(temp_project, task_id="test-task-001")

    @pytest.fixture
    def sample_context(self):
        """Create a sample context."""
        return {
            "fingerprint": "project: test",
            "task": {"id": "test-001", "goal": "Fix bug"},
            "phase": {"current": "implement"},
        }

    @pytest.fixture
    def sample_breakdown(self):
        """Create a sample token breakdown."""
        return {
            "fingerprint": 50,
            "task": 100,
            "phase": 30,
        }

    def test_audit_directory_created(self, logger, temp_project):
        """Audit directory is created on init."""
        expected = temp_project / ".agentforge" / "context_audit" / "test-task-001"
        assert expected.exists()
        assert expected.is_dir()

    def test_step_audit_created(self, logger, sample_context, sample_breakdown):
        """Step audit file is created."""
        logger.log_step(
            step=1,
            context=sample_context,
            token_breakdown=sample_breakdown,
        )

        audit_file = logger.audit_dir / "step_1.yaml"
        assert audit_file.exists()

        audit = yaml.safe_load(audit_file.read_text())
        assert audit["task_id"] == "test-task-001"
        assert audit["step"] == 1
        assert "timestamp" in audit
        assert audit["total_tokens"] == 180

    def test_context_snapshot_saved(self, logger, sample_context, sample_breakdown):
        """Context snapshot is saved."""
        logger.log_step(
            step=1,
            context=sample_context,
            token_breakdown=sample_breakdown,
        )

        context_file = logger.audit_dir / "step_1_context.yaml"
        assert context_file.exists()

        saved_context = yaml.safe_load(context_file.read_text())
        assert saved_context == sample_context

    def test_thinking_saved_separately(self, logger, sample_context, sample_breakdown):
        """Thinking content is saved to separate file."""
        thinking = "Let me analyze this problem step by step..."

        logger.log_step(
            step=2,
            context=sample_context,
            token_breakdown=sample_breakdown,
            thinking=thinking,
        )

        # Check thinking file created
        thinking_file = logger.audit_dir / "step_2_thinking.md"
        assert thinking_file.exists()
        assert thinking in thinking_file.read_text()

        # Check audit references thinking
        audit = logger.get_step_audit(2)
        assert audit["thinking_file"] == "step_2_thinking.md"
        assert "thinking_tokens" in audit

    def test_compaction_logged(self, logger, sample_context, sample_breakdown):
        """Compaction info is logged when provided."""
        compaction = {
            "applied": True,
            "original_tokens": 5000,
            "final_tokens": 3000,
            "rules_applied": [{"section": "data", "strategy": "truncate"}],
        }

        logger.log_step(
            step=1,
            context=sample_context,
            token_breakdown=sample_breakdown,
            compaction=compaction,
        )

        audit = logger.get_step_audit(1)
        assert audit["compaction"] == compaction

    def test_hash_reproducible(self, logger, sample_context):
        """Same context produces same hash."""
        hash1 = logger._hash_context(sample_context)
        hash2 = logger._hash_context(sample_context)

        assert hash1 == hash2
        assert len(hash1) == 16

    def test_hash_changes_on_diff(self, logger, sample_context):
        """Different contexts produce different hashes."""
        hash1 = logger._hash_context(sample_context)

        modified_context = dict(sample_context)
        modified_context["extra"] = "data"
        hash2 = logger._hash_context(modified_context)

        assert hash1 != hash2

    def test_summary_created(self, logger):
        """Task summary is created correctly."""
        logger.log_task_summary(
            total_steps=5,
            final_status="completed",
            total_tokens=10000,
            cached_tokens=4000,
        )

        summary_file = logger.audit_dir / "summary.yaml"
        assert summary_file.exists()

        summary = yaml.safe_load(summary_file.read_text())
        assert summary["task_id"] == "test-task-001"
        assert summary["total_steps"] == 5
        assert summary["final_status"] == "completed"
        assert summary["total_input_tokens"] == 10000
        assert summary["cached_tokens"] == 4000
        # effective = 10000 - (4000 * 0.9) = 6400
        assert summary["effective_tokens"] == 6400

    def test_summary_with_compaction(self, logger):
        """Summary includes compaction stats."""
        logger.log_task_summary(
            total_steps=5,
            final_status="completed",
            total_tokens=10000,
            cached_tokens=4000,
            compaction_events=3,
            tokens_saved=2000,
        )

        summary = logger.get_summary()
        assert summary["compaction_events"] == 3
        assert summary["total_tokens_saved"] == 2000

    def test_summary_with_thinking(self, logger, sample_context, sample_breakdown):
        """Summary includes thinking stats when thinking was logged."""
        logger.log_step(
            step=1,
            context=sample_context,
            token_breakdown=sample_breakdown,
            thinking="Thinking content here...",
        )

        logger.log_task_summary(
            total_steps=1,
            final_status="completed",
            total_tokens=5000,
            cached_tokens=0,
        )

        summary = logger.get_summary()
        assert summary["thinking_enabled"] is True
        assert summary["total_thinking_tokens"] > 0


class TestRetrieval:
    """Tests for audit retrieval methods."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            yield project

    @pytest.fixture
    def logger_with_data(self, temp_project):
        """Create logger with some logged data."""
        logger = ContextAuditLogger(temp_project, task_id="test-task")

        # Log multiple steps
        for step in [1, 2, 3]:
            logger.log_step(
                step=step,
                context={"step": step, "data": f"step{step}"},
                token_breakdown={"data": step * 100},
                thinking=f"Thinking for step {step}",
            )

        logger.log_task_summary(
            total_steps=3,
            final_status="completed",
            total_tokens=6000,
            cached_tokens=2000,
        )

        return logger

    def test_get_step_audit(self, logger_with_data):
        """Can retrieve step audit."""
        audit = logger_with_data.get_step_audit(2)

        assert audit is not None
        assert audit["step"] == 2
        assert "timestamp" in audit

    def test_get_step_audit_missing(self, logger_with_data):
        """Missing step returns None."""
        audit = logger_with_data.get_step_audit(99)
        assert audit is None

    def test_get_step_context(self, logger_with_data):
        """Can retrieve step context."""
        context = logger_with_data.get_step_context(2)

        assert context is not None
        assert context["step"] == 2
        assert context["data"] == "step2"

    def test_get_thinking(self, logger_with_data):
        """Can retrieve thinking content."""
        thinking = logger_with_data.get_thinking(2)

        assert thinking is not None
        assert "step 2" in thinking

    def test_get_summary(self, logger_with_data):
        """Can retrieve task summary."""
        summary = logger_with_data.get_summary()

        assert summary is not None
        assert summary["total_steps"] == 3
        assert summary["final_status"] == "completed"

    def test_list_steps(self, logger_with_data):
        """Can list all logged steps."""
        steps = logger_with_data.list_steps()

        assert steps == [1, 2, 3]


class TestClassMethods:
    """Tests for class-level methods."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            yield project

    def test_load_task_audit(self, temp_project):
        """Can load existing task audit."""
        # Create some audit data
        logger = ContextAuditLogger(temp_project, task_id="existing-task")
        logger.log_step(
            step=1,
            context={"data": "test"},
            token_breakdown={"data": 100},
        )
        logger.log_task_summary(
            total_steps=1,
            final_status="completed",
            total_tokens=1000,
            cached_tokens=0,
        )

        # Load it back
        loaded = ContextAuditLogger.load_task_audit(temp_project, "existing-task")

        assert loaded is not None
        assert loaded.get_step_audit(1) is not None

    def test_load_missing_task(self, temp_project):
        """Loading missing task returns None."""
        loaded = ContextAuditLogger.load_task_audit(temp_project, "nonexistent")
        assert loaded is None

    def test_list_task_audits(self, temp_project):
        """Can list all task audits."""
        # Create multiple audits
        for task_id in ["task-a", "task-b", "task-c"]:
            logger = ContextAuditLogger(temp_project, task_id=task_id)
            logger.log_task_summary(
                total_steps=1,
                final_status="completed",
                total_tokens=1000,
                cached_tokens=0,
            )

        task_ids = ContextAuditLogger.list_task_audits(temp_project)

        assert len(task_ids) == 3
        assert "task-a" in task_ids
        assert "task-b" in task_ids
        assert "task-c" in task_ids

    def test_list_empty_audits(self, temp_project):
        """Empty project returns empty list."""
        task_ids = ContextAuditLogger.list_task_audits(temp_project)
        assert task_ids == []


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            yield project

    def test_unicode_content(self, temp_project):
        """Handles unicode content correctly."""
        logger = ContextAuditLogger(temp_project, task_id="unicode-test")

        logger.log_step(
            step=1,
            context={"data": "日本語テスト 🎉"},
            token_breakdown={"data": 50},
            thinking="考え中... 思考プロセス",
        )

        context = logger.get_step_context(1)
        assert context["data"] == "日本語テスト 🎉"

        thinking = logger.get_thinking(1)
        assert "考え中" in thinking

    def test_empty_context(self, temp_project):
        """Handles empty context."""
        logger = ContextAuditLogger(temp_project, task_id="empty-test")

        logger.log_step(
            step=1,
            context={},
            token_breakdown={},
        )

        audit = logger.get_step_audit(1)
        assert audit["total_tokens"] == 0
        assert audit["sections_present"] == []

    def test_large_context(self, temp_project):
        """Handles large context."""
        logger = ContextAuditLogger(temp_project, task_id="large-test")

        large_context = {
            "data": "x" * 100000,
            "list": list(range(1000)),
        }

        logger.log_step(
            step=1,
            context=large_context,
            token_breakdown={"data": 25000, "list": 5000},
        )

        # Should still be retrievable
        retrieved = logger.get_step_context(1)
        assert retrieved["data"] == large_context["data"]
        assert len(retrieved["list"]) == 1000
