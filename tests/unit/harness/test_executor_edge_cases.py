# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: llm-integration-v1
# @component_id: executor-edge-case-tests
# @impl_path: src/agentforge/core/harness/minimal_context/executor.py

"""
Edge Case Tests for MinimalContextExecutor.

Covers error handling and edge cases:
- Task not found scenarios
- Action executor failures
- Invalid LLM responses
- Phase transition edge cases
- Context building failures
- Malformed tool calls
- Timeout and retry scenarios
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agentforge.core.harness.minimal_context.executor import (
    AdaptiveBudget,
    MinimalContextExecutor,
    StepOutcome,
)
from agentforge.core.harness.minimal_context.state_store import Phase


class TestExecutorErrorHandling:
    """Tests for executor error handling in edge cases."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / "src").mkdir()
            (project / "tests").mkdir()
            (project / ".agentforge").mkdir()
            (project / ".agentforge" / "tasks").mkdir()
            (project / "pyproject.toml").write_text(
                """
[project]
name = "test-project"
requires-python = ">=3.11"
dependencies = ["pytest"]
"""
            )
            yield project

    def test_execute_step_task_not_found(self, temp_project):
        """execute_step returns error for non-existent task."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        outcome = executor.execute_step("non-existent-task-id")

        assert outcome.success is False, "Expected outcome.success is False"
        assert outcome.action_name == "error", "Expected outcome.action_name to equal 'error'"
        assert "not found" in outcome.summary.lower(), "Expected 'not found' in outcome.summary.lower()"
        assert outcome.should_continue is False, "Expected outcome.should_continue is False"

    def test_execute_step_already_complete(self, temp_project):
        """execute_step handles already completed tasks gracefully."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        # Create a task and mark it complete
        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )
        executor.state_store.update_phase(state.task_id, Phase.COMPLETE)

        outcome = executor.execute_step(state.task_id)

        assert outcome.success is True, "Expected outcome.success is True"
        assert outcome.action_name == "already_complete", "Expected outcome.action_name to equal 'already_complete'"
        assert outcome.should_continue is False, "Expected outcome.should_continue is False"

    def test_execute_step_already_failed(self, temp_project):
        """execute_step handles already failed tasks gracefully."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )
        executor.state_store.update_phase(state.task_id, Phase.FAILED)

        outcome = executor.execute_step(state.task_id)

        assert outcome.success is True, "Expected outcome.success is True"
        assert "FAILED" in outcome.summary.upper() or "failed" in outcome.summary.lower(), "Assertion failed"
        assert outcome.should_continue is False, "Expected outcome.should_continue is False"

    def test_execute_step_already_escalated(self, temp_project):
        """execute_step handles already escalated tasks gracefully."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )
        executor.state_store.update_phase(state.task_id, Phase.ESCALATED)

        outcome = executor.execute_step(state.task_id)

        assert outcome.success is True, "Expected outcome.success is True"
        assert outcome.should_continue is False, "Expected outcome.should_continue is False"

    def test_action_executor_raises_exception(self, temp_project):
        """Action executor exception is handled gracefully."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        def failing_action(name, params, state):
            raise RuntimeError("Simulated action failure")

        executor.register_action("failing_action", failing_action)

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )

        # Execute the action directly
        result = executor._execute_action("failing_action", {}, state)

        assert result["status"] == "failure", "Expected result['status'] to equal 'failure'"
        assert "Simulated action failure" in result["error"], "Expected 'Simulated action failure' in result['error']"

    def test_action_executor_returns_non_dict(self, temp_project):
        """Action executor returning non-dict is wrapped."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        def string_action(name, params, state):
            return "Simple string result"

        executor.register_action("string_action", string_action)

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )

        result = executor._execute_action("string_action", {}, state)

        assert result["status"] == "success", "Expected result['status'] to equal 'success'"
        assert result["summary"] == "Simple string result", "Expected result['summary'] to equal 'Simple string result'"

    def test_unknown_action_returns_failure(self, temp_project):
        """Unknown action returns failure result."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )

        result = executor._execute_action("completely_unknown_action", {}, state)

        assert result["status"] == "failure", "Expected result['status'] to equal 'failure'"
        assert "unknown action" in result["summary"].lower(), "Expected 'unknown action' in result['summary'].lower()"


class TestParseActionEdgeCases:
    """Tests for action parsing edge cases."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / ".agentforge").mkdir()
            (project / "pyproject.toml").write_text('[project]\nname = "test"')
            yield project

    def test_parse_action_empty_response(self, temp_project):
        """Empty LLM response returns unknown action."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        action_name, params = executor._parse_action("")

        assert action_name == "unknown", "Expected action_name to equal 'unknown'"
        assert params == {}, "Expected params to equal {}"

    def test_parse_action_no_action_block(self, temp_project):
        """Response without action block tries fallbacks."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        response = "I will now complete the task successfully."
        action_name, params = executor._parse_action(response)

        assert action_name == "complete", "Expected action_name to equal 'complete'"

    def test_parse_action_malformed_yaml(self, temp_project):
        """Malformed YAML in action block is handled."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        response = """```action
name: test_action
parameters:
  - this is not valid yaml:
    missing: proper: structure
```"""

        action_name, params = executor._parse_action(response)
        # Should fall back gracefully
        assert action_name in ("unknown", "test_action"), "Expected action_name in ('unknown', 'test_action')"

    def test_parse_action_yaml_without_name(self, temp_project):
        """YAML without name/action field returns None from parser."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        response = """```action
parameters:
  path: /some/file.py
```"""

        action_name, params = executor._parse_action(response)
        assert action_name == "unknown", "Expected action_name to equal 'unknown'"

    def test_parse_action_simple_pattern_fallback(self, temp_project):
        """Simple action: pattern is detected."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        response = "action: read_file\npath: /some/file.py"
        action_name, params = executor._parse_action(response)

        assert action_name == "read_file", "Expected action_name to equal 'read_file'"

    def test_parse_action_name_pattern_fallback(self, temp_project):
        """Simple name: pattern is detected."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        response = "name: write_file\npath: /some/file.py"
        action_name, params = executor._parse_action(response)

        assert action_name == "write_file", "Expected action_name to equal 'write_file'"


class TestAdaptiveBudgetEdgeCases:
    """Tests for AdaptiveBudget edge cases."""

    def test_empty_recent_actions(self):
        """Empty recent actions list is handled."""
        budget = AdaptiveBudget(base_budget=15, max_budget=50)

        should_continue, reason, loop = budget.check_continue(1, [])

        assert should_continue is True, "Expected should_continue is True"
        assert "Continue" in reason, "Expected 'Continue' in reason"

    def test_single_action_no_loop(self):
        """Single action doesn't trigger loop detection."""
        budget = AdaptiveBudget(base_budget=15, max_budget=50)

        actions = [{"action": "read_file", "result": "success", "summary": "Read OK"}]
        should_continue, reason, loop = budget.check_continue(1, actions)

        assert should_continue is True, "Expected should_continue is True"
        assert loop is None, "Expected loop is None"

    def test_repeated_failures_trigger_loop(self):
        """Repeated identical failures trigger loop detection."""
        budget = AdaptiveBudget(
            base_budget=15,
            max_budget=50,
            runaway_threshold=3,
            use_enhanced_loop_detection=False,  # Use legacy detection
        )

        actions = [
            {"action": "read_file", "result": "failure", "error": "File not found", "parameters": {"path": "/x"}},
            {"action": "read_file", "result": "failure", "error": "File not found", "parameters": {"path": "/x"}},
            {"action": "read_file", "result": "failure", "error": "File not found", "parameters": {"path": "/x"}},
        ]
        should_continue, reason, loop = budget.check_continue(3, actions)

        assert should_continue is False, "Expected should_continue is False"
        assert "runaway" in reason.lower() or "stopped" in reason.lower(), "Assertion failed"

    def test_budget_exhaustion(self):
        """Budget exhaustion stops execution."""
        budget = AdaptiveBudget(base_budget=3, max_budget=3)

        actions = [{"action": "read_file", "result": "success", "summary": "Read OK"}]
        should_continue, reason, loop = budget.check_continue(3, actions)

        assert should_continue is False, "Expected should_continue is False"
        assert "budget" in reason.lower(), "Expected 'budget' in reason.lower()"

    def test_no_progress_streak_stops(self):
        """No progress for several steps stops execution."""
        budget = AdaptiveBudget(
            base_budget=15,
            max_budget=50,
            no_progress_threshold=3,
            use_enhanced_loop_detection=False,
        )

        # Actions that don't make progress
        non_progress_actions = [
            {"action": "analyze", "result": "success", "summary": "Analyzed"},
            {"action": "think", "result": "success", "summary": "Thinking"},
            {"action": "plan", "result": "success", "summary": "Planning"},
        ]

        # First few checks should continue
        budget.check_continue(1, non_progress_actions[:1])
        budget.check_continue(2, non_progress_actions[:2])
        should_continue, reason, loop = budget.check_continue(3, non_progress_actions)

        assert should_continue is False, "Expected should_continue is False"
        assert "no progress" in reason.lower(), "Expected 'no progress' in reason.lower()"

    def test_progress_extends_budget(self):
        """Making progress extends the dynamic budget."""
        budget = AdaptiveBudget(base_budget=5, max_budget=50)

        # Write file makes progress
        progress_action = [
            {"action": "write_file", "result": "success", "summary": "Wrote file"}
        ]
        budget.check_continue(1, progress_action)

        # Check that budget extended
        dynamic = budget._calculate_budget()
        assert dynamic > 5, "Expected dynamic > 5"


class TestNativeToolEdgeCases:
    """Tests for native tool execution edge cases."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / "src").mkdir()
            (project / ".agentforge").mkdir()
            (project / ".agentforge" / "tasks").mkdir()
            (project / "pyproject.toml").write_text('[project]\nname = "test"')
            yield project

    def test_run_task_native_no_tool_calls(self, temp_project):
        """Response without tool calls is handled."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        # Client returns text without tool calls
        client = create_simple_client([
            {"content": "I cannot help with this task.", "tool_calls": []},
        ])

        result = executor.run_task_native(
            task_id="test-no-tools",
            domain_context={"violation": {"id": "V-001", "file": "test.py", "line": 1, "description": "Test"}},
            llm_client=client,
            max_steps=3,
        )

        # Should stop after processing - may complete if executor handles no-tool gracefully
        assert result["steps"] >= 1, "Expected result['steps'] >= 1"
        # Result could be various statuses depending on how executor handles no-tool response
        assert result["status"] in ("stopped", "failed", "no_outcomes", "completed"), "Expected result['status'] in ('stopped', 'failed', 'no_o..."

    def test_run_task_native_minimal_domain_context(self, temp_project):
        """Minimal domain context works properly."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        client = create_simple_client([
            {"tool_calls": [{"id": "tc_1", "name": "complete", "input": {"summary": "Done"}}]},
        ])

        # fix_violation requires violation context
        result = executor.run_task_native(
            task_id="test-minimal-context",
            domain_context={"violation": {"id": "V-001", "file": "test.py", "line": 1, "description": "Test"}},
            llm_client=client,
            max_steps=3,
        )

        assert result["status"] == "completed", "Expected result['status'] to equal 'completed'"

    def test_run_task_native_cannot_fix(self, temp_project):
        """cannot_fix action is handled correctly."""
        from agentforge.core.llm import create_simple_client

        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        client = create_simple_client([
            {
                "tool_calls": [
                    {"id": "tc_1", "name": "cannot_fix", "input": {"reason": "Requires manual intervention"}}
                ]
            },
        ])

        result = executor.run_task_native(
            task_id="test-cannot-fix",
            domain_context={"violation": {"id": "V-001", "file": "test.py"}},
            llm_client=client,
            max_steps=3,
        )

        assert result["status"] == "escalated", "Expected result['status'] to equal 'escalated'"


class TestCompleteActionEdgeCases:
    """Tests for complete action verification."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / ".agentforge").mkdir()
            (project / "pyproject.toml").write_text('[project]\nname = "test"')
            yield project

    def test_complete_without_verification_fails(self, temp_project):
        """Complete action fails if verification not passing."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )
        # Mark verification as NOT ready
        state.verification.ready_for_completion = False

        result = executor._execute_action("complete", {}, state)

        assert result["status"] == "failure", "Expected result['status'] to equal 'failure'"
        assert "verification" in result["summary"].lower(), "Expected 'verification' in result['summary'].lower()"

    def test_complete_with_verification_succeeds(self, temp_project):
        """Complete action succeeds when verification passing."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )
        # Mark verification as ready
        state.verification.ready_for_completion = True

        result = executor._execute_action("complete", {}, state)

        assert result["status"] == "success", "Expected result['status'] to equal 'success'"


class TestPhaseTransitionEdgeCases:
    """Tests for phase transition edge cases."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / ".agentforge").mkdir()
            (project / "pyproject.toml").write_text('[project]\nname = "test"')
            yield project

    def test_fatal_action_transitions_to_failed(self, temp_project):
        """Fatal action result transitions to FAILED phase."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
            audit_enabled=False,
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )

        action_result = {
            "status": "failure",
            "fatal": True,
            "error": "Critical file system error",
        }

        executor._handle_phase_transition(state.task_id, "write_file", action_result, state)

        updated_state = executor.state_store.load(state.task_id)
        assert updated_state.phase == Phase.FAILED, "Expected updated_state.phase to equal Phase.FAILED"

    def test_escalate_transitions_to_escalated(self, temp_project):
        """Escalate action transitions to ESCALATED phase."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
            audit_enabled=False,
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )

        action_result = {"status": "success"}

        executor._handle_phase_transition(state.task_id, "escalate", action_result, state)

        updated_state = executor.state_store.load(state.task_id)
        assert updated_state.phase == Phase.ESCALATED, "Expected updated_state.phase to equal Phase.ESCALATED"

    def test_cannot_fix_stores_reason(self, temp_project):
        """cannot_fix action stores the reason in context data."""
        executor = MinimalContextExecutor(
            project_path=temp_project,
            task_type="fix_violation",
            audit_enabled=False,
        )

        state = executor.state_store.create_task(
            task_type="fix_violation",
            goal="Test goal",
            success_criteria=["Test passes"],
            context_data={"violation": {"id": "V-001"}},
        )

        action_result = {
            "status": "success",
            "cannot_fix_reason": "Requires architectural changes",
        }

        executor._handle_phase_transition(state.task_id, "cannot_fix", action_result, state)

        updated_state = executor.state_store.load(state.task_id)
        assert updated_state.phase == Phase.ESCALATED, "Expected updated_state.phase to equal Phase.ESCALATED"
        assert updated_state.context_data.get("cannot_fix_reason") == "Requires architectural changes", "Expected updated_state.context_data.... to equal 'Requires architectural cha..."


class TestStepOutcomeEdgeCases:
    """Tests for StepOutcome edge cases."""

    def test_step_outcome_to_dict_without_loop(self):
        """StepOutcome.to_dict works without loop detection."""
        outcome = StepOutcome(
            success=True,
            action_name="read_file",
            action_params={"path": "/test.py"},
            result="success",
            summary="Read file successfully",
            should_continue=True,
            tokens_used=100,
            duration_ms=50,
        )

        result = outcome.to_dict()

        assert result["success"] is True, "Expected result['success'] is True"
        assert result["action_name"] == "read_file", "Expected result['action_name'] to equal 'read_file'"
        assert "loop_detection" not in result, "Expected 'loop_detection' not in result"

    def test_step_outcome_to_dict_with_loop(self):
        """StepOutcome.to_dict includes loop detection info."""
        from agentforge.core.harness.minimal_context.loop_detector import (
            LoopDetection,
            LoopType,
        )

        loop = LoopDetection(
            detected=True,
            loop_type=LoopType.IDENTICAL_ACTION,
            description="Same action repeated",
            confidence=0.9,
            suggestions=["Try a different approach"],
        )

        outcome = StepOutcome(
            success=True,
            action_name="read_file",
            action_params={"path": "/test.py"},
            result="failure",
            summary="Read file failed",
            should_continue=False,
            tokens_used=100,
            duration_ms=50,
            loop_detected=loop,
        )

        result = outcome.to_dict()

        assert "loop_detection" in result, "Expected 'loop_detection' in result"
        assert result["loop_detection"]["type"] == "identical_action", "Expected result['loop_detection']['t... to equal 'identical_action'"
        assert result["loop_detection"]["confidence"] == 0.9, "Expected result['loop_detection']['c... to equal 0.9"
