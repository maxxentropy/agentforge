# @spec_file: specs/tools/01-tool-handlers.yaml
# @spec_id: tool-handlers-v1
# @component_id: terminal-handlers

"""
Tests for terminal_handlers module.
"""

import pytest
import yaml
from pathlib import Path

from agentforge.core.harness.minimal_context.tool_handlers.terminal_handlers import (
    create_complete_handler,
    create_escalate_handler,
    create_cannot_fix_handler,
    create_request_help_handler,
    create_plan_fix_handler,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    agentforge = tmp_path / ".agentforge"
    agentforge.mkdir()
    violations = agentforge / "violations"
    violations.mkdir()
    return tmp_path


class TestCompleteHandler:
    """Tests for complete handler."""

    def test_complete_basic(self):
        """Complete with default summary."""
        handler = create_complete_handler()

        result = handler({})

        assert "COMPLETE" in result
        assert "completed" in result.lower()

    def test_complete_with_summary(self):
        """Complete with custom summary."""
        handler = create_complete_handler()

        result = handler({"summary": "Fixed the bug in module.py"})

        assert "COMPLETE" in result
        assert "Fixed the bug" in result

    def test_complete_with_files_modified(self):
        """Complete shows modified files."""
        handler = create_complete_handler()

        result = handler({
            "summary": "Done",
            "files_modified": ["a.py", "b.py"],
        })

        assert "COMPLETE" in result
        assert "a.py" in result
        assert "b.py" in result

    def test_complete_with_context_files(self):
        """Complete uses context for files."""
        handler = create_complete_handler()

        result = handler({
            "summary": "Done",
            "_context": {"files_modified": ["c.py"]},
        })

        assert "COMPLETE" in result
        assert "c.py" in result


class TestEscalateHandler:
    """Tests for escalate handler."""

    def test_escalate_basic(self):
        """Escalate with reason."""
        handler = create_escalate_handler()

        result = handler({"reason": "Need human review"})

        assert "ESCALATE" in result
        assert "human review" in result.lower()

    def test_escalate_with_priority(self):
        """Escalate includes priority."""
        handler = create_escalate_handler()

        result = handler({
            "reason": "Critical issue",
            "priority": "high",
        })

        assert "ESCALATE" in result
        assert "high" in result.lower()

    def test_escalate_with_suggestions(self):
        """Escalate includes suggestions."""
        handler = create_escalate_handler()

        result = handler({
            "reason": "Stuck",
            "suggestions": ["Try approach A", "Consider option B"],
        })

        assert "ESCALATE" in result
        assert "approach A" in result
        assert "option B" in result


class TestCannotFixHandler:
    """Tests for cannot_fix handler."""

    def test_cannot_fix_creates_escalation(self, temp_project):
        """Creates escalation YAML file."""
        handler = create_cannot_fix_handler(temp_project)

        result = handler({
            "reason": "Code is auto-generated and should not be modified",
            "constraints": ["File is marked as auto-generated"],
            "alternatives": ["Update the generator template instead"],
            "_context": {"violation_id": "V-001", "task_id": "T-123"},
        })

        assert "CANNOT_FIX" in result
        assert "ESC-" in result

        # Check file was created
        escalations = list((temp_project / ".agentforge" / "escalations").glob("ESC-*.yaml"))
        assert len(escalations) == 1

    def test_cannot_fix_records_details(self, temp_project):
        """Escalation file contains all details."""
        handler = create_cannot_fix_handler(temp_project)

        handler({
            "reason": "Test reason",
            "alternatives": ["Alt 1", "Alt 2"],
            "_context": {"violation_id": "V-002"},
        })

        escalation_file = next((temp_project / ".agentforge" / "escalations").glob("*.yaml"))
        with open(escalation_file) as f:
            data = yaml.safe_load(f)

        assert data["reason"] == "Test reason"
        assert data["alternatives"] == ["Alt 1", "Alt 2"]
        assert data["violation_id"] == "V-002"

    def test_cannot_fix_requires_reason(self, temp_project):
        """Error without reason parameter."""
        handler = create_cannot_fix_handler(temp_project)

        result = handler({})

        assert "ERROR" in result
        assert "reason" in result.lower()

    def test_cannot_fix_includes_constraints(self, temp_project):
        """Escalation includes constraints."""
        handler = create_cannot_fix_handler(temp_project)

        result = handler({
            "reason": "Cannot modify",
            "constraints": ["Frozen interface", "Breaking change"],
        })

        assert "CANNOT_FIX" in result
        assert "Frozen interface" in result
        assert "Breaking change" in result


class TestRequestHelpHandler:
    """Tests for request_help handler."""

    def test_request_help_basic(self, temp_project):
        """Create a help request."""
        handler = create_request_help_handler(temp_project)

        result = handler({
            "question": "Which approach should I use?",
            "_context": {"task_id": "T-001"},
        })

        assert "HELP_REQUESTED" in result
        assert "Which approach" in result

    def test_request_help_with_options(self, temp_project):
        """Help request includes options."""
        handler = create_request_help_handler(temp_project)

        result = handler({
            "question": "How to proceed?",
            "options": ["Option A", "Option B", "Option C"],
        })

        assert "HELP_REQUESTED" in result
        assert "Option A" in result
        assert "Option B" in result

    def test_request_help_requires_question(self, temp_project):
        """Error without question parameter."""
        handler = create_request_help_handler(temp_project)

        result = handler({})

        assert "ERROR" in result
        assert "question" in result.lower()

    def test_request_help_creates_file(self, temp_project):
        """Help request creates file."""
        handler = create_request_help_handler(temp_project)

        handler({
            "question": "Need guidance",
            "_context": {"task_id": "T-001"},
        })

        help_files = list((temp_project / ".agentforge" / "help_requests").glob("HELP-*.yaml"))
        assert len(help_files) == 1


class TestPlanFixHandler:
    """Tests for plan_fix handler."""

    def test_plan_fix_basic(self, temp_project):
        """Record a fix plan."""
        handler = create_plan_fix_handler(temp_project)

        result = handler({
            "diagnosis": "The function is too complex",
            "approach": "Extract helper functions",
        })

        assert "PLAN_RECORDED" in result
        assert "Extract helper" in result

    def test_plan_fix_with_steps(self, temp_project):
        """Plan includes steps."""
        handler = create_plan_fix_handler(temp_project)

        result = handler({
            "approach": "Refactor",
            "steps": ["Step 1: Identify", "Step 2: Extract", "Step 3: Test"],
        })

        assert "PLAN_RECORDED" in result
        assert "Step 1" in result
        assert "Step 2" in result

    def test_plan_fix_requires_approach(self, temp_project):
        """Error without approach parameter."""
        handler = create_plan_fix_handler(temp_project)

        result = handler({})

        assert "ERROR" in result
        assert "approach" in result.lower()

    def test_plan_fix_truncates_long_text(self, temp_project):
        """Long text is truncated in output."""
        handler = create_plan_fix_handler(temp_project)

        long_approach = "x" * 200

        result = handler({
            "approach": long_approach,
        })

        assert "PLAN_RECORDED" in result
        assert "..." in result  # Truncation indicator
