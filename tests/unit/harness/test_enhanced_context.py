"""
Tests for Enhanced Context Engineering
======================================

Tests the new Pydantic v2 models, understanding extraction,
loop detection, and phase machine.
"""

import pytest
from datetime import datetime

from agentforge.core.harness.minimal_context import (
    # Context Models
    FactCategory,
    ActionResult,
    Fact,
    ActionDef,
    ActionRecord,
    TaskSpec,
    ViolationSpec,
    VerificationState,
    Understanding,
    PhaseState,
    StateSpec,
    ActionsSpec,
    AgentContext,
    AgentResponse,
    # Understanding
    ExtractionRule,
    ExtractionRuleSet,
    UnderstandingExtractor,
    FactStore,
    # Loop Detection
    LoopType,
    LoopDetection,
    ActionSignature,
    LoopDetector,
    # Phase Machine
    Phase,
    PhaseContext,
    Transition,
    PhaseConfig,
    PhaseMachine,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Context Models Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestFact:
    """Tests for Fact model."""

    def test_create_fact(self):
        """Test creating a fact."""
        fact = Fact(
            id="fact_001",
            category=FactCategory.VERIFICATION,
            statement="Check passed",
            confidence=0.95,
            source="run_check:test",
            step=1,
        )
        assert fact.id == "fact_001"
        assert fact.category == FactCategory.VERIFICATION
        assert fact.confidence == 0.95

    def test_fact_immutable(self):
        """Test that facts are immutable (frozen)."""
        fact = Fact(
            id="fact_001",
            category=FactCategory.VERIFICATION,
            statement="Check passed",
            confidence=0.95,
            source="run_check:test",
            step=1,
        )
        with pytest.raises(Exception):  # Pydantic validation error
            fact.statement = "Modified"

    def test_confidence_rounding(self):
        """Test confidence is rounded to 2 decimal places."""
        fact = Fact(
            id="fact_001",
            category=FactCategory.VERIFICATION,
            statement="Check passed",
            confidence=0.9567,
            source="run_check:test",
            step=1,
        )
        assert fact.confidence == 0.96

    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(Exception):  # Pydantic validation error
            Fact(
                id="fact_001",
                category=FactCategory.VERIFICATION,
                statement="Check passed",
                confidence=1.5,  # Invalid
                source="run_check:test",
                step=1,
            )


class TestUnderstanding:
    """Tests for Understanding model."""

    def test_get_active_facts(self):
        """Test filtering superseded facts."""
        facts = [
            Fact(
                id="fact_001",
                category=FactCategory.VERIFICATION,
                statement="Check failed",
                confidence=1.0,
                source="run_check",
                step=1,
            ),
            Fact(
                id="fact_002",
                category=FactCategory.VERIFICATION,
                statement="Check passed",
                confidence=1.0,
                source="run_check",
                step=2,
                supersedes="fact_001",
            ),
        ]
        understanding = Understanding(facts=facts, superseded_facts=["fact_001"])

        active = understanding.get_active_facts()
        assert len(active) == 1
        assert active[0].id == "fact_002"

    def test_get_by_category(self):
        """Test filtering facts by category."""
        facts = [
            Fact(
                id="fact_001",
                category=FactCategory.VERIFICATION,
                statement="Check passed",
                confidence=1.0,
                source="run_check",
                step=1,
            ),
            Fact(
                id="fact_002",
                category=FactCategory.ERROR,
                statement="Edit failed",
                confidence=1.0,
                source="edit_file",
                step=2,
            ),
        ]
        understanding = Understanding(facts=facts)

        errors = understanding.get_by_category(FactCategory.ERROR)
        assert len(errors) == 1
        assert errors[0].statement == "Edit failed"

    def test_get_high_confidence(self):
        """Test filtering facts by confidence threshold."""
        facts = [
            Fact(
                id="fact_001",
                category=FactCategory.VERIFICATION,
                statement="Certain fact",
                confidence=0.95,
                source="test",
                step=1,
            ),
            Fact(
                id="fact_002",
                category=FactCategory.INFERENCE,
                statement="Uncertain fact",
                confidence=0.6,
                source="test",
                step=2,
            ),
        ]
        understanding = Understanding(facts=facts)

        high_conf = understanding.get_high_confidence(threshold=0.8)
        assert len(high_conf) == 1
        assert high_conf[0].confidence >= 0.8


class TestAgentContext:
    """Tests for AgentContext model."""

    def test_to_yaml(self):
        """Test YAML serialization."""
        task = TaskSpec(
            task_id="task_001",
            task_type="fix_violation",
            goal="Fix complexity violation",
            success_criteria=["Check passes"],
        )
        state = StateSpec()
        actions = ActionsSpec(
            available=[
                ActionDef(name="edit_file", description="Edit a file"),
            ]
        )
        context = AgentContext(task=task, state=state, actions=actions)

        yaml_output = context.to_yaml()
        assert "task:" in yaml_output
        assert "goal:" in yaml_output
        assert "Fix complexity violation" in yaml_output


# ═══════════════════════════════════════════════════════════════════════════════
# Understanding Extraction Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtractionRuleSet:
    """Tests for extraction rules."""

    def test_extract_check_passed(self):
        """Test extracting 'check passed' fact."""
        extractor = UnderstandingExtractor()
        facts = extractor.extract(
            tool_name="run_check",
            output="✓ Check PASSED - no violations",
            result=ActionResult.SUCCESS,
            step=1,
        )

        assert len(facts) >= 1
        # Should find check passed fact
        passed_facts = [f for f in facts if "passed" in f.statement.lower()]
        assert len(passed_facts) >= 1

    def test_extract_complexity_violation(self):
        """Test extracting complexity violation."""
        extractor = UnderstandingExtractor()
        facts = extractor.extract(
            tool_name="run_check",
            output="Function 'process_data' has complexity 15 (threshold: 10)",
            result=ActionResult.FAILURE,
            step=1,
        )

        assert len(facts) >= 1
        complexity_facts = [f for f in facts if "complexity" in f.statement.lower()]
        assert len(complexity_facts) >= 1
        assert "process_data" in complexity_facts[0].statement

    def test_extract_test_results(self):
        """Test extracting test results."""
        extractor = UnderstandingExtractor()
        facts = extractor.extract(
            tool_name="run_tests",
            output="10 passed, 2 failed in 1.5s",
            result=ActionResult.PARTIAL,
            step=1,
        )

        assert len(facts) >= 1
        # Should extract both passed and failed counts
        statements = [f.statement for f in facts]
        assert any("passed" in s.lower() for s in statements)


class TestFactStore:
    """Tests for FactStore."""

    def test_add_fact(self):
        """Test adding a fact."""
        store = FactStore()
        fact = Fact(
            id="fact_001",
            category=FactCategory.VERIFICATION,
            statement="Check passed",
            confidence=1.0,
            source="test",
            step=1,
        )
        store.add(fact)

        assert len(store.get_active()) == 1

    def test_supersession(self):
        """Test fact supersession."""
        store = FactStore()

        # Add initial verification fact
        fact1 = Fact(
            id="fact_001",
            category=FactCategory.VERIFICATION,
            statement="Check passed - 5 violations",
            confidence=1.0,
            source="run_check",
            step=1,
        )
        store.add(fact1)

        # Add newer verification fact (should supersede)
        fact2 = Fact(
            id="fact_002",
            category=FactCategory.VERIFICATION,
            statement="Check passed - 3 violations",
            confidence=1.0,
            source="run_check",
            step=2,
        )
        store.add(fact2)

        # Only newer fact should be active
        active = store.get_active()
        assert len(active) == 1
        assert active[0].id == "fact_002"

    def test_compaction(self):
        """Test fact compaction when threshold exceeded."""
        store = FactStore(max_facts=5, compaction_threshold=5)

        # Add many facts
        for i in range(10):
            fact = Fact(
                id=f"fact_{i:03d}",
                category=FactCategory.INFERENCE,
                statement=f"Inference {i}",
                confidence=0.5,
                source="test",
                step=i,
            )
            store.add(fact)

        # Should compact to max_facts
        active = store.get_active()
        assert len(active) <= 5

    def test_to_understanding(self):
        """Test converting to Understanding model."""
        store = FactStore()
        fact = Fact(
            id="fact_001",
            category=FactCategory.VERIFICATION,
            statement="Check passed",
            confidence=1.0,
            source="test",
            step=1,
        )
        store.add(fact)

        understanding = store.to_understanding()
        assert isinstance(understanding, Understanding)
        assert len(understanding.facts) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Loop Detection Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestLoopDetector:
    """Tests for LoopDetector."""

    def test_detect_identical_loop(self):
        """Test detecting identical action loop."""
        detector = LoopDetector(identical_threshold=3)

        actions = [
            ActionRecord(
                step=i,
                action="edit_file",
                target="file.py",
                parameters={"old_text": "foo"},
                result=ActionResult.FAILURE,
                summary="Edit failed",
                error="text not found",
            )
            for i in range(3)
        ]

        result = detector.check(actions)
        assert result.detected
        assert result.loop_type == LoopType.IDENTICAL_ACTION
        assert len(result.suggestions) > 0

    def test_no_loop_with_different_actions(self):
        """Test no loop when actions differ."""
        detector = LoopDetector()

        actions = [
            ActionRecord(
                step=1,
                action="read_file",
                result=ActionResult.SUCCESS,
                summary="Read file",
            ),
            ActionRecord(
                step=2,
                action="edit_file",
                result=ActionResult.SUCCESS,
                summary="Edited file",
            ),
            ActionRecord(
                step=3,
                action="run_check",
                result=ActionResult.SUCCESS,
                summary="Check passed",
            ),
        ]

        result = detector.check(actions)
        assert not result.detected

    def test_detect_no_progress(self):
        """Test detecting no-progress loop."""
        detector = LoopDetector(no_progress_threshold=4)

        actions = [
            ActionRecord(
                step=i,
                action="run_check",
                result=ActionResult.SUCCESS,
                summary="Check ran",
            )
            for i in range(4)
        ]

        result = detector.check(actions)
        assert result.detected
        assert result.loop_type == LoopType.NO_PROGRESS

    def test_error_cycle_detection(self):
        """Test detecting A->B->A error cycles."""
        detector = LoopDetector(cycle_threshold=2)

        # Create A->B->A->B->A pattern
        actions = []
        for i in range(5):
            action = "edit_file" if i % 2 == 0 else "extract_function"
            actions.append(
                ActionRecord(
                    step=i,
                    action=action,
                    target="file.py",
                    result=ActionResult.FAILURE,
                    summary=f"{action} failed",
                    error="operation failed",
                )
            )

        result = detector.check(actions)
        assert result.detected
        assert result.loop_type == LoopType.ERROR_CYCLE


class TestActionSignature:
    """Tests for ActionSignature."""

    def test_signature_matching(self):
        """Test signature comparison."""
        sig1 = ActionSignature(
            action_type="edit",
            target_file="file.py",
            target_entity="func",
            outcome=ActionResult.FAILURE,
        )
        sig2 = ActionSignature(
            action_type="edit",
            target_file="other.py",
            target_entity="other",
            outcome=ActionResult.FAILURE,
        )

        # Non-strict match (same type and outcome)
        assert sig1.matches(sig2, strict=False)
        # Strict match fails (different targets)
        assert not sig1.matches(sig2, strict=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase Machine Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPhaseMachine:
    """Tests for PhaseMachine."""

    def test_initial_phase(self):
        """Test machine starts in INIT phase."""
        machine = PhaseMachine()
        assert machine.current_phase == Phase.INIT
        assert machine.steps_in_phase == 0

    def test_advance_step(self):
        """Test step advancement."""
        machine = PhaseMachine()
        machine.advance_step()
        assert machine.steps_in_phase == 1

    def test_transition_init_to_analyze(self):
        """Test transitioning from INIT to ANALYZE."""
        machine = PhaseMachine()
        context = PhaseContext(
            current_phase=Phase.INIT,
            steps_in_phase=0,
            total_steps=0,
            verification_passing=False,
            tests_passing=False,
            files_modified=[],
            facts=[],
        )

        assert machine.can_transition(Phase.ANALYZE, context)
        success = machine.transition(Phase.ANALYZE, context)
        assert success
        assert machine.current_phase == Phase.ANALYZE

    def test_guard_blocks_transition(self):
        """Test that guards can block transitions."""
        machine = PhaseMachine()
        # Start in IMPLEMENT phase
        machine._current_phase = Phase.IMPLEMENT

        context = PhaseContext(
            current_phase=Phase.IMPLEMENT,
            steps_in_phase=1,
            total_steps=5,
            verification_passing=False,
            tests_passing=False,
            files_modified=[],  # No modifications - guard should block
            facts=[],
        )

        # Should not be able to transition to VERIFY without modifications
        assert not machine.can_transition(Phase.VERIFY, context)

    def test_verify_to_complete(self):
        """Test transitioning from VERIFY to COMPLETE."""
        machine = PhaseMachine()
        machine._current_phase = Phase.VERIFY

        context = PhaseContext(
            current_phase=Phase.VERIFY,
            steps_in_phase=1,
            total_steps=10,
            verification_passing=True,
            tests_passing=True,
            files_modified=["file.py"],
            facts=[],
        )

        assert machine.can_transition(Phase.COMPLETE, context)
        success = machine.transition(Phase.COMPLETE, context)
        assert success
        assert machine.current_phase == Phase.COMPLETE

    def test_max_steps_triggers_auto_transition(self):
        """Test auto-transition when max steps exceeded."""
        machine = PhaseMachine()
        machine._current_phase = Phase.ANALYZE
        machine._steps_in_phase = 10  # Exceeds max_steps=5

        context = PhaseContext(
            current_phase=Phase.ANALYZE,
            steps_in_phase=10,
            total_steps=10,
            verification_passing=False,
            tests_passing=False,
            files_modified=[],
            facts=[],
        )

        # Should suggest escalation when stuck
        next_phase = machine.should_auto_transition(context)
        assert next_phase is not None

    def test_to_state_and_from_state(self):
        """Test state persistence round-trip."""
        machine = PhaseMachine()
        machine._current_phase = Phase.IMPLEMENT
        machine._steps_in_phase = 3
        machine._phase_history = [Phase.INIT, Phase.ANALYZE]

        # Convert to state
        state = machine.to_state()
        assert state.current_phase == "implement"
        assert state.steps_in_phase == 3

        # Reconstruct from state
        restored = PhaseMachine.from_state(state)
        assert restored.current_phase == Phase.IMPLEMENT
        assert restored.steps_in_phase == 3
        assert len(restored.phase_history) == 2

    def test_get_available_transitions(self):
        """Test getting available transitions."""
        machine = PhaseMachine()
        machine._current_phase = Phase.VERIFY

        # Context where verification failed
        context = PhaseContext(
            current_phase=Phase.VERIFY,
            steps_in_phase=1,
            total_steps=10,
            verification_passing=False,  # Failed
            tests_passing=True,
            files_modified=["file.py"],
            facts=[],
        )

        available = machine.get_available_transitions(context)
        # Should be able to go back to IMPLEMENT
        target_phases = [t.to_phase for t in available]
        assert Phase.IMPLEMENT in target_phases


class TestPhaseContext:
    """Tests for PhaseContext."""

    def test_has_modifications(self):
        """Test modification detection."""
        ctx_no_mods = PhaseContext(
            current_phase=Phase.IMPLEMENT,
            steps_in_phase=1,
            total_steps=5,
            verification_passing=False,
            tests_passing=False,
            files_modified=[],
            facts=[],
        )
        assert not ctx_no_mods.has_modifications()

        ctx_with_mods = PhaseContext(
            current_phase=Phase.IMPLEMENT,
            steps_in_phase=1,
            total_steps=5,
            verification_passing=False,
            tests_passing=False,
            files_modified=["file.py"],
            facts=[],
        )
        assert ctx_with_mods.has_modifications()

    def test_has_fact_of_type(self):
        """Test fact type detection."""
        fact = Fact(
            id="fact_001",
            category=FactCategory.CODE_STRUCTURE,
            statement="Function found",
            confidence=1.0,
            source="test",
            step=1,
        )

        ctx = PhaseContext(
            current_phase=Phase.ANALYZE,
            steps_in_phase=1,
            total_steps=5,
            verification_passing=False,
            tests_passing=False,
            files_modified=[],
            facts=[fact],
        )

        assert ctx.has_fact_of_type("code_structure")
        assert not ctx.has_fact_of_type("verification")


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests (Phase 2)
# ═══════════════════════════════════════════════════════════════════════════════

import tempfile
from pathlib import Path

from agentforge.core.harness.minimal_context.working_memory import WorkingMemoryManager


class TestWorkingMemoryFactStorage:
    """Tests for fact storage in WorkingMemoryManager."""

    def test_add_and_get_fact(self):
        """Test adding and retrieving facts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkingMemoryManager(Path(tmpdir))

            mgr.add_fact(
                fact_id="fact_001",
                category="verification",
                statement="Check passed",
                confidence=0.95,
                source="run_check:test",
                step=1,
            )

            facts = mgr.get_facts()
            assert len(facts) == 1
            assert facts[0]["statement"] == "Check passed"
            assert facts[0]["confidence"] == 0.95

    def test_supersession(self):
        """Test fact supersession in working memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkingMemoryManager(Path(tmpdir))

            # Add old fact
            mgr.add_fact(
                fact_id="fact_001",
                category="verification",
                statement="Check failed",
                confidence=1.0,
                source="run_check",
                step=1,
            )

            # Add new fact that supersedes
            mgr.add_fact(
                fact_id="fact_002",
                category="verification",
                statement="Check passed",
                confidence=1.0,
                source="run_check",
                step=2,
                supersedes="fact_001",
            )

            # Only new fact should be returned
            facts = mgr.get_facts()
            assert len(facts) == 1
            assert facts[0]["id"] == "fact_002"

    def test_get_facts_for_context(self):
        """Test getting facts formatted for context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkingMemoryManager(Path(tmpdir))

            mgr.add_fact(
                fact_id="fact_001",
                category="verification",
                statement="Check passed",
                confidence=0.9,
                source="run_check",
                step=1,
            )

            mgr.add_fact(
                fact_id="fact_002",
                category="error",
                statement="Edit failed",
                confidence=0.85,
                source="edit_file",
                step=2,
            )

            ctx_facts = mgr.get_facts_for_context()

            # Should be grouped by category
            assert "verification" in ctx_facts
            assert "error" in ctx_facts
            assert len(ctx_facts["verification"]) == 1
            assert "Check passed" in ctx_facts["verification"][0]

    def test_high_confidence_pinning(self):
        """Test that high-confidence facts are pinned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkingMemoryManager(Path(tmpdir), max_items=2)

            # Add high-confidence fact (should be pinned)
            mgr.add_fact(
                fact_id="high_conf",
                category="verification",
                statement="Definitely true",
                confidence=0.95,
                source="test",
                step=1,
            )

            # Add low-confidence facts (should be evictable)
            for i in range(5):
                mgr.add_fact(
                    fact_id=f"low_conf_{i}",
                    category="inference",
                    statement=f"Maybe true {i}",
                    confidence=0.5,
                    source="test",
                    step=i + 2,
                )

            # High-confidence fact should still be there
            facts = mgr.get_facts(min_confidence=0.9)
            assert len(facts) >= 1
            high_conf_facts = [f for f in facts if f["id"] == "high_conf"]
            assert len(high_conf_facts) == 1

    def test_add_facts_from_list(self):
        """Test adding facts from Fact model objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkingMemoryManager(Path(tmpdir))

            facts = [
                Fact(
                    id="fact_001",
                    category=FactCategory.VERIFICATION,
                    statement="Check passed",
                    confidence=0.95,
                    source="run_check",
                    step=1,
                ),
                Fact(
                    id="fact_002",
                    category=FactCategory.ERROR,
                    statement="Edit failed",
                    confidence=0.8,
                    source="edit_file",
                    step=2,
                ),
            ]

            mgr.add_facts_from_list(facts, step=1)

            stored = mgr.get_facts()
            assert len(stored) == 2

    def test_clear_facts(self):
        """Test clearing all facts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = WorkingMemoryManager(Path(tmpdir))

            mgr.add_fact(
                fact_id="fact_001",
                category="verification",
                statement="Test",
                confidence=0.9,
                source="test",
                step=1,
            )

            # Also add a regular action result
            mgr.add_action_result(
                action="test",
                result="success",
                summary="Test action",
                step=1,
            )

            cleared = mgr.clear_facts()
            assert cleared == 1

            # Facts should be gone
            facts = mgr.get_facts()
            assert len(facts) == 0

            # Action results should still be there
            actions = mgr.get_action_results()
            assert len(actions) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# AdaptiveBudget Integration Tests (Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════

from agentforge.core.harness.minimal_context import AdaptiveBudget


class TestAdaptiveBudgetEnhancedLoopDetection:
    """Tests for enhanced loop detection in AdaptiveBudget."""

    def test_identical_loop_detection(self):
        """Test detection of identical action loops."""
        budget = AdaptiveBudget(
            base_budget=15,
            runaway_threshold=3,
            use_enhanced_loop_detection=True,
        )

        # Create identical failing actions
        actions = [
            {
                "step": i,
                "action": "edit_file",
                "parameters": {"path": "test.py"},
                "result": "failure",
                "summary": "Edit failed",
                "error": "text not found",
            }
            for i in range(1, 4)
        ]

        should_continue, reason, loop_detection = budget.check_continue(3, actions)

        assert not should_continue
        assert "IDENTICAL_ACTION" in reason
        assert loop_detection is not None
        assert loop_detection.detected
        assert loop_detection.loop_type == LoopType.IDENTICAL_ACTION

    def test_error_cycle_detection(self):
        """Test detection of A->B->A error cycling."""
        budget = AdaptiveBudget(
            base_budget=15,
            use_enhanced_loop_detection=True,
        )

        # Create A->B->A->B->A pattern
        actions = []
        for i in range(5):
            action = "edit_file" if i % 2 == 0 else "extract_function"
            actions.append({
                "step": i + 1,
                "action": action,
                "parameters": {},
                "result": "failure",
                "summary": f"{action} failed",
                "error": "operation failed",
            })

        should_continue, reason, loop_detection = budget.check_continue(5, actions)

        assert not should_continue
        assert loop_detection is not None
        assert loop_detection.detected
        assert loop_detection.loop_type == LoopType.ERROR_CYCLE

    def test_no_loop_with_progress(self):
        """Test that successful actions don't trigger loop detection."""
        budget = AdaptiveBudget(
            base_budget=15,
            use_enhanced_loop_detection=True,
        )

        actions = [
            {"step": 1, "action": "read_file", "result": "success", "summary": "Read file"},
            {"step": 2, "action": "edit_file", "result": "success", "summary": "Edited file"},
            {"step": 3, "action": "run_check", "result": "success", "summary": "Check PASSED"},
        ]

        should_continue, reason, loop_detection = budget.check_continue(3, actions)

        assert should_continue
        assert "Continue" in reason
        assert loop_detection is None

    def test_legacy_fallback(self):
        """Test fallback to legacy detection when enhanced is disabled."""
        budget = AdaptiveBudget(
            base_budget=15,
            runaway_threshold=3,
            use_enhanced_loop_detection=False,
        )

        assert budget.loop_detector is None

        # Create identical failing actions
        actions = [
            {
                "step": i,
                "action": "edit_file",
                "parameters": {"path": "test.py"},
                "result": "failure",
                "summary": "Edit failed",
                "error": "text not found",
            }
            for i in range(1, 4)
        ]

        should_continue, reason, loop_detection = budget.check_continue(3, actions)

        assert not should_continue
        assert "Runaway" in reason
        assert loop_detection is None  # No LoopDetection in legacy mode

    def test_get_loop_suggestions(self):
        """Test getting suggestions from last loop detection."""
        budget = AdaptiveBudget(
            base_budget=15,
            runaway_threshold=3,
            use_enhanced_loop_detection=True,
        )

        # No suggestions initially
        assert budget.get_loop_suggestions() == []

        # Trigger a loop
        actions = [
            {
                "step": i,
                "action": "edit_file",
                "parameters": {},
                "result": "failure",
                "summary": "failed",
                "error": "not found",
            }
            for i in range(1, 4)
        ]

        budget.check_continue(3, actions)

        suggestions = budget.get_loop_suggestions()
        assert len(suggestions) > 0
        assert any("re-read" in s.lower() or "replace_lines" in s.lower() for s in suggestions)

    def test_budget_exhaustion(self):
        """Test budget exhaustion still works with enhanced detection."""
        budget = AdaptiveBudget(
            base_budget=3,
            max_budget=3,
            use_enhanced_loop_detection=True,
        )

        # Use varied actions that don't trigger loop detection
        actions = [
            {"step": 1, "action": "read_file", "result": "success", "summary": "Read config"},
            {"step": 2, "action": "edit_file", "result": "success", "summary": "Edit code"},
            {"step": 3, "action": "run_tests", "result": "success", "summary": "Tests passed"},
        ]

        should_continue, reason, loop_detection = budget.check_continue(3, actions)

        assert not should_continue
        assert "Budget exhausted" in reason

    def test_step_outcome_includes_loop_info(self):
        """Test that StepOutcome can include loop detection info."""
        from agentforge.core.harness.minimal_context import StepOutcome

        loop_detection = LoopDetection(
            detected=True,
            loop_type=LoopType.IDENTICAL_ACTION,
            confidence=1.0,
            description="Same action repeated",
            suggestions=["Try something different"],
        )

        outcome = StepOutcome(
            success=True,
            action_name="edit_file",
            action_params={},
            result="failure",
            summary="Failed",
            should_continue=False,
            tokens_used=100,
            duration_ms=50,
            loop_detected=loop_detection,
        )

        outcome_dict = outcome.to_dict()

        assert "loop_detection" in outcome_dict
        assert outcome_dict["loop_detection"]["type"] == "identical_action"
        assert outcome_dict["loop_detection"]["suggestions"] == ["Try something different"]


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4: Phase Machine Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPhaseMachineIntegration:
    """Tests for PhaseMachine integration with state_store and executor."""

    def test_task_state_phase_machine_persistence(self, tmp_path):
        """Test that PhaseMachine state persists across save/load."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            TaskPhase,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
            Phase,
        )

        store = TaskStateStore(tmp_path)

        # Create a task
        task = store.create_task(
            task_type="test",
            goal="Test phase machine persistence",
            success_criteria=["Persist state"],
        )

        # Initialize and modify phase machine
        machine = PhaseMachine()
        machine._current_phase = Phase.IMPLEMENT
        machine._steps_in_phase = 3
        machine._phase_history = [Phase.INIT, Phase.ANALYZE]

        # Persist
        task.set_phase_machine(machine)
        store._save_state(task)

        # Reload
        loaded_task = store.load(task.task_id)
        loaded_machine = loaded_task.get_phase_machine()

        assert loaded_machine.current_phase == Phase.IMPLEMENT
        assert loaded_machine.steps_in_phase == 3
        assert len(loaded_machine.phase_history) == 2

    def test_task_state_backward_compatible(self, tmp_path):
        """Test that legacy tasks without phase_machine_state still work."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            Phase,
        )

        store = TaskStateStore(tmp_path)

        # Create a task (no phase_machine_state)
        task = store.create_task(
            task_type="test",
            goal="Test backward compat",
            success_criteria=["Load without error"],
        )

        # Reload without phase_machine_state set
        loaded_task = store.load(task.task_id)

        # Should get a fresh machine
        machine = loaded_task.get_phase_machine()
        assert machine.current_phase == Phase.INIT
        assert machine.steps_in_phase == 0

    def test_update_phase_machine_method(self, tmp_path):
        """Test state_store.update_phase_machine method."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
            Phase,
        )

        store = TaskStateStore(tmp_path)

        # Create a task
        task = store.create_task(
            task_type="test",
            goal="Test update_phase_machine",
            success_criteria=["Update works"],
        )

        # Modify machine externally
        machine = PhaseMachine()
        machine._current_phase = Phase.VERIFY
        machine._steps_in_phase = 2

        # Use the new method
        store.update_phase_machine(task.task_id, machine)

        # Verify persistence
        loaded = store.load(task.task_id)
        loaded_machine = loaded.get_phase_machine()

        assert loaded_machine.current_phase == Phase.VERIFY
        assert loaded_machine.steps_in_phase == 2

    def test_phase_context_building(self, tmp_path):
        """Test that PhaseContext is built correctly from state."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            MinimalContextExecutor,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
            Phase,
        )

        store = TaskStateStore(tmp_path)
        executor = MinimalContextExecutor(
            project_path=tmp_path,
            state_store=store,
            use_phase_machine=True,
        )

        # Create a task with some context
        task = store.create_task(
            task_type="test",
            goal="Test context building",
            success_criteria=["Build context"],
            context_data={"files_modified": ["test.py"]},
        )

        # Set verification status
        store.update_verification(
            task.task_id,
            checks_passing=1,
            checks_failing=0,
            tests_passing=True,
        )

        # Reload and build context
        task = store.load(task.task_id)
        machine = task.get_phase_machine()

        context = executor._build_phase_context(
            machine=machine,
            state=task,
            last_action="edit_file",
            last_action_result="success",
        )

        assert context.current_phase == Phase.INIT
        assert context.verification_passing is True
        assert context.tests_passing is True
        assert context.files_modified == ["test.py"]
        assert context.last_action == "edit_file"

    def test_phase_transition_via_handle_method(self, tmp_path):
        """Test _handle_phase_transition updates both legacy and machine state."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            TaskPhase,
            MinimalContextExecutor,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
            Phase,
        )

        store = TaskStateStore(tmp_path)
        executor = MinimalContextExecutor(
            project_path=tmp_path,
            state_store=store,
            use_phase_machine=True,
        )

        # Create a task
        task = store.create_task(
            task_type="test",
            goal="Test transition",
            success_criteria=["Complete"],
        )

        # Initialize phase machine
        machine = PhaseMachine()
        task.set_phase_machine(machine)
        store._save_state(task)

        # Simulate "complete" action
        executor._handle_phase_transition(
            task_id=task.task_id,
            action_name="complete",
            action_result={"status": "success"},
            state=task,
        )

        # Verify both states updated
        loaded = store.load(task.task_id)
        assert loaded.phase == TaskPhase.COMPLETE

        loaded_machine = loaded.get_phase_machine()
        assert loaded_machine.current_phase == Phase.COMPLETE

    def test_legacy_mode_fallback(self, tmp_path):
        """Test that use_phase_machine=False uses legacy behavior."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            TaskPhase,
            MinimalContextExecutor,
        )

        store = TaskStateStore(tmp_path)
        executor = MinimalContextExecutor(
            project_path=tmp_path,
            state_store=store,
            use_phase_machine=False,  # Legacy mode
        )

        # Create a task (no machine initialization)
        task = store.create_task(
            task_type="test",
            goal="Test legacy mode",
            success_criteria=["Escalate"],
        )

        # Simulate "escalate" action
        executor._handle_phase_transition(
            task_id=task.task_id,
            action_name="escalate",
            action_result={"status": "success"},
            state=task,
        )

        # Verify legacy phase updated
        loaded = store.load(task.task_id)
        assert loaded.phase == TaskPhase.ESCALATED

        # phase_machine_state should be empty (legacy mode)
        assert loaded.phase_machine_state == {}


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 5: Enhanced Context Builder Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedContextBuilder:
    """Tests for EnhancedContextBuilder integration."""

    def test_build_from_task_state(self, tmp_path):
        """Test building AgentContext from TaskState."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            EnhancedContextBuilder,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
        )

        store = TaskStateStore(tmp_path)
        builder = EnhancedContextBuilder(tmp_path, store)

        # Create a task
        task = store.create_task(
            task_type="fix_violation",
            goal="Fix complexity violation",
            success_criteria=["Checks pass", "Tests pass"],
            context_data={
                "violation": {"rule": "max-complexity", "severity": "high"},
                "precomputed": {"suggestions": ["extract_function"]},
            },
        )

        # Initialize phase machine
        machine = PhaseMachine()
        task.set_phase_machine(machine)
        store._save_state(task)

        # Build context
        context = builder.build_from_task_state(task.task_id)

        assert context.task.task_id == task.task_id
        assert context.task.goal == "Fix complexity violation"
        assert context.state.current_step == 0
        assert context.state.phase.current_phase == "init"
        assert context.domain_context == {"rule": "max-complexity", "severity": "high"}

    def test_phase_aware_actions(self, tmp_path):
        """Test that actions are filtered by phase."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            EnhancedContextBuilder,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
            Phase,
        )

        store = TaskStateStore(tmp_path)
        builder = EnhancedContextBuilder(tmp_path, store)

        # Create a task
        task = store.create_task(
            task_type="fix_violation",
            goal="Test phase actions",
            success_criteria=["Pass"],
        )

        # Test INIT phase
        machine = PhaseMachine()
        task.set_phase_machine(machine)
        store._save_state(task)

        context = builder.build_from_task_state(task.task_id)
        init_actions = [a.name for a in context.actions.available]

        assert "read_file" in init_actions
        assert "load_context" in init_actions
        assert "extract_function" not in init_actions  # Not in init phase

        # Test IMPLEMENT phase
        machine._current_phase = Phase.IMPLEMENT
        task.set_phase_machine(machine)
        store._save_state(task)

        context = builder.build_from_task_state(task.task_id)
        impl_actions = [a.name for a in context.actions.available]

        assert "extract_function" in impl_actions
        assert "edit_file" in impl_actions
        assert "complete" not in impl_actions  # Not in implement phase

    def test_recommended_action(self, tmp_path):
        """Test that recommended action is set correctly."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            EnhancedContextBuilder,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
            Phase,
        )

        store = TaskStateStore(tmp_path)
        builder = EnhancedContextBuilder(tmp_path, store)

        task = store.create_task(
            task_type="fix_violation",
            goal="Test recommendations",
            success_criteria=["Pass"],
        )

        # INIT phase should recommend read_file
        machine = PhaseMachine()
        task.set_phase_machine(machine)
        store._save_state(task)

        context = builder.build_from_task_state(task.task_id)
        assert context.actions.recommended == "read_file"

        # IMPLEMENT phase should recommend extract_function
        machine._current_phase = Phase.IMPLEMENT
        task.set_phase_machine(machine)
        store._save_state(task)

        context = builder.build_from_task_state(task.task_id)
        assert context.actions.recommended == "extract_function"

    def test_blocked_actions(self, tmp_path):
        """Test that blocked actions are identified."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            EnhancedContextBuilder,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
            Phase,
        )

        store = TaskStateStore(tmp_path)
        builder = EnhancedContextBuilder(tmp_path, store)

        task = store.create_task(
            task_type="fix_violation",
            goal="Test blocked actions",
            success_criteria=["Pass"],
        )

        machine = PhaseMachine()
        task.set_phase_machine(machine)
        store._save_state(task)

        context = builder.build_from_task_state(task.task_id)

        # Complete should be blocked (not in verify phase)
        blocked_names = [b.split(":")[0] for b in context.actions.blocked]
        assert "complete" in blocked_names

    def test_build_messages(self, tmp_path):
        """Test building LLM messages."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            EnhancedContextBuilder,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
        )

        store = TaskStateStore(tmp_path)
        builder = EnhancedContextBuilder(tmp_path, store)

        task = store.create_task(
            task_type="fix_violation",
            goal="Test messages",
            success_criteria=["Pass"],
        )

        machine = PhaseMachine()
        task.set_phase_machine(machine)
        store._save_state(task)

        messages = builder.build_messages(task.task_id)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        # Check system prompt has phase guidance
        assert "CURRENT PHASE: INIT" in messages[0]["content"]

        # Check user message has context
        assert "# Task" in messages[1]["content"]
        assert "# Available Actions" in messages[1]["content"]

    def test_token_breakdown(self, tmp_path):
        """Test token breakdown calculation."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            EnhancedContextBuilder,
        )
        from agentforge.core.harness.minimal_context.phase_machine import (
            PhaseMachine,
        )

        store = TaskStateStore(tmp_path)
        builder = EnhancedContextBuilder(tmp_path, store)

        task = store.create_task(
            task_type="fix_violation",
            goal="Test tokens",
            success_criteria=["Pass"],
        )

        machine = PhaseMachine()
        task.set_phase_machine(machine)
        store._save_state(task)

        breakdown = builder.get_token_breakdown(task.task_id)

        assert "total_tokens" in breakdown
        assert "within_budget" in breakdown
        assert breakdown["total_tokens"] > 0
        assert breakdown["within_budget"] is True  # Should be within 6000 default

    def test_executor_uses_enhanced_builder(self, tmp_path):
        """Test executor always uses enhanced context builder."""
        from agentforge.core.harness.minimal_context import (
            TaskStateStore,
            MinimalContextExecutor,
            EnhancedContextBuilder,
        )

        store = TaskStateStore(tmp_path)

        # Create executor - enhanced builder is always used
        executor = MinimalContextExecutor(
            project_path=tmp_path,
            state_store=store,
            use_enhanced_context_builder=True,
        )

        assert executor.use_enhanced_context_builder is True
        assert isinstance(executor.context_builder, EnhancedContextBuilder)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 6: Feature Flag Migration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedContextAlwaysEnabled:
    """Tests that enhanced context features are always enabled."""

    def test_workflow_has_enhanced_context_enabled(self, tmp_path):
        """Test that workflow always uses enhanced context."""
        from agentforge.core.harness.minimal_context import (
            MinimalContextFixWorkflow,
            EnhancedContextBuilder,
        )

        # Create workflow - enhanced context is always enabled
        workflow = MinimalContextFixWorkflow(project_path=tmp_path)

        assert workflow.executor.use_phase_machine is True
        assert workflow.executor.use_enhanced_context_builder is True
        assert workflow.executor.enable_understanding_extraction is True
        assert isinstance(workflow.executor.context_builder, EnhancedContextBuilder)

    def test_factory_function_creates_enhanced_workflow(self, tmp_path):
        """Test factory function creates workflow with enhanced context."""
        from agentforge.core.harness.minimal_context import (
            create_minimal_fix_workflow,
            EnhancedContextBuilder,
        )

        workflow = create_minimal_fix_workflow(project_path=tmp_path)

        assert isinstance(workflow.executor.context_builder, EnhancedContextBuilder)
        assert workflow.executor.use_phase_machine is True
        assert workflow.executor.use_enhanced_context_builder is True

    def test_enhanced_token_limits_exported(self):
        """Test that ENHANCED_TOKEN_LIMITS is exported and correct."""
        from agentforge.core.harness.minimal_context import (
            TOKEN_BUDGET_LIMITS,
            ENHANCED_TOKEN_LIMITS,
        )

        # Check legacy limits (for reference)
        assert sum(TOKEN_BUDGET_LIMITS.values()) == 8000

        # Check enhanced limits are reduced
        assert sum(ENHANCED_TOKEN_LIMITS.values()) == 5000

        # Check specific reductions
        assert ENHANCED_TOKEN_LIMITS["system_prompt"] < TOKEN_BUDGET_LIMITS["system_prompt"]
        assert ENHANCED_TOKEN_LIMITS["recent_actions"] < TOKEN_BUDGET_LIMITS["recent_actions"]

        # Check new sections exist
        assert "understanding" in ENHANCED_TOKEN_LIMITS
        assert "precomputed" in ENHANCED_TOKEN_LIMITS

    def test_workflow_preserves_custom_iterations(self, tmp_path):
        """Test that custom iteration settings are preserved."""
        from agentforge.core.harness.minimal_context import MinimalContextFixWorkflow

        workflow = MinimalContextFixWorkflow(
            project_path=tmp_path,
            base_iterations=20,
            max_iterations=100,
        )

        assert workflow.base_iterations == 20
        assert workflow.max_iterations == 100

    def test_module_docstring_documents_features(self):
        """Test that module docstring documents enhanced features."""
        import agentforge.core.harness.minimal_context as mc

        docstring = mc.__doc__

        assert "Enhanced Context Engineering" in docstring
        assert "PhaseMachine" in docstring
        assert "EnhancedContextBuilder" in docstring
        assert "Token Budget Enforcement" in docstring
        assert "Fact Compaction" in docstring


class TestTokenBudgetEnforcement:
    """Tests for token budget enforcement with compaction."""

    def test_agent_context_estimate_tokens(self):
        """Test that AgentContext can estimate its token count."""
        from agentforge.core.harness.minimal_context import (
            AgentContext,
            TaskSpec,
            StateSpec,
            ActionsSpec,
            ActionDef,
        )

        context = AgentContext(
            task=TaskSpec(
                task_id="test-123",
                task_type="fix",
                goal="Fix the bug",
                success_criteria=["Tests pass"],
            ),
            state=StateSpec(),
            actions=ActionsSpec(
                available=[
                    ActionDef(
                        name="read_file",
                        description="Read a file",
                    )
                ],
            ),
        )

        tokens = context.estimate_tokens()

        # Should be a reasonable positive number
        assert tokens > 0
        assert tokens < 1000  # Simple context should be under 1000 tokens

    def test_compaction_triggered_when_over_budget(self):
        """Test that compaction is triggered when context exceeds budget."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            ActionsSpec,
            ActionDef,
            PhaseMachine,
            Understanding,
            Fact,
            FactCategory,
        )

        # Create builder with very small budget
        builder = EnhancedContextBuilder(
            project_path=Path("/tmp"),
            max_tokens=100,  # Very small to trigger compaction
        )

        # Create context with lots of data
        facts = [
            Fact(
                id=f"fact-{i}",
                category=FactCategory.CODE_STRUCTURE,
                statement=f"This is fact number {i} with some additional content to make it longer",
                confidence=0.6,  # Low confidence to test compaction
                source="test",
                step=1,
            )
            for i in range(20)
        ]

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Fix it",
                success_criteria=["Done"],
            ),
            state_spec=StateSpec(
                understanding=Understanding(facts=facts),
            ),
            domain_context={"key": "x" * 1000},  # Large domain context
            precomputed={"analysis": "y" * 2000},  # Large precomputed
            phase_machine=PhaseMachine(),
        )

        # Compaction should have been applied
        # Low-confidence facts should be removed
        high_conf_facts = [f for f in context.state.understanding.facts if f.confidence >= 0.8]
        assert len(context.state.understanding.facts) <= 10

    def test_compaction_preserves_high_confidence_facts(self):
        """Test that high-confidence facts are preserved during compaction."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            ActionsSpec,
            Understanding,
            Fact,
            FactCategory,
            PhaseMachine,
        )

        builder = EnhancedContextBuilder(
            project_path=Path("/tmp"),
            max_tokens=200,
        )

        # Create facts with varying confidence
        facts = [
            Fact(
                id="high-1",
                category=FactCategory.CODE_STRUCTURE,
                statement="High confidence fact",
                confidence=0.95,
                source="test",
                step=1,
            ),
            Fact(
                id="low-1",
                category=FactCategory.INFERENCE,
                statement="Low confidence fact" * 50,
                confidence=0.5,
                source="test",
                step=1,
            ),
            Fact(
                id="high-2",
                category=FactCategory.VERIFICATION,
                statement="Another high confidence fact",
                confidence=0.85,
                source="test",
                step=1,
            ),
        ]

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Fix it",
                success_criteria=["Done"],
            ),
            state_spec=StateSpec(
                understanding=Understanding(facts=facts),
            ),
            domain_context={},
            precomputed={"large_data": "z" * 5000},  # Force compaction
            phase_machine=PhaseMachine(),
        )

        # High confidence facts should still be there
        fact_ids = [f.id for f in context.state.understanding.facts]
        assert "high-1" in fact_ids or "high-2" in fact_ids

    def test_compaction_truncates_precomputed_first(self):
        """Test that precomputed is truncated before other content."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            ActionsSpec,
            PhaseMachine,
        )

        builder = EnhancedContextBuilder(
            project_path=Path("/tmp"),
            max_tokens=500,
        )

        original_precomputed = {"analysis": "x" * 10000}

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Fix it",
                success_criteria=["Done"],
            ),
            state_spec=StateSpec(),
            domain_context={},
            precomputed=original_precomputed,
            phase_machine=PhaseMachine(),
        )

        # Precomputed should be truncated or empty
        if context.precomputed.get("analysis"):
            assert len(context.precomputed["analysis"]) < 10000
        # Context should fit in budget
        assert context.estimate_tokens() <= 500 or len(context.precomputed) == 0

    def test_normal_context_not_compacted(self):
        """Test that normal-sized context is not compacted."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            ActionsSpec,
            ActionDef,
            PhaseMachine,
        )

        builder = EnhancedContextBuilder(
            project_path=Path("/tmp"),
            max_tokens=6000,  # Default budget
        )

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Simple fix",
                success_criteria=["Tests pass"],
            ),
            state_spec=StateSpec(),
            domain_context={"file": "test.py", "line": 42},
            precomputed={"complexity": 5},
            phase_machine=PhaseMachine(),
        )

        # Should not be compacted
        assert context.precomputed.get("complexity") == 5
        assert context.domain_context.get("file") == "test.py"


class TestResponseValidation:
    """Tests for LLM response validation against AgentResponse schema."""

    def test_parse_action_block_format(self):
        """Test parsing action block format."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor

        executor = MinimalContextExecutor(project_path=Path("/tmp"))

        response = '''Here is my action:
```action
name: read_file
parameters:
  path: /tmp/test.py
```'''

        action, params = executor._parse_action(response)

        assert action == "read_file"
        assert params == {"path": "/tmp/test.py"}

    def test_parse_yaml_block_format(self):
        """Test parsing YAML block format with 'action' key."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor

        executor = MinimalContextExecutor(project_path=Path("/tmp"))

        response = '''I will read the file:
```yaml
action: read_file
parameters:
  path: /tmp/test.py
```'''

        action, params = executor._parse_action(response)

        assert action == "read_file"
        assert params == {"path": "/tmp/test.py"}

    def test_parse_with_reasoning(self):
        """Test that reasoning is accepted but not returned."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor

        executor = MinimalContextExecutor(project_path=Path("/tmp"))

        response = '''```yaml
action: edit_file
parameters:
  path: /tmp/test.py
  old_text: "foo"
  new_text: "bar"
reasoning: "Replacing foo with bar to fix the bug"
```'''

        action, params = executor._parse_action(response)

        assert action == "edit_file"
        assert params == {"path": "/tmp/test.py", "old_text": "foo", "new_text": "bar"}

    def test_parse_validates_against_schema(self):
        """Test that response is validated against AgentResponse schema."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor
        from agentforge.core.harness.minimal_context import AgentResponse

        executor = MinimalContextExecutor(project_path=Path("/tmp"))

        # Valid response should work
        response = '''```yaml
action: complete
parameters:
  summary: "Task completed"
```'''

        action, params = executor._parse_action(response)
        assert action == "complete"

        # The parsed values should be valid for AgentResponse
        validated = AgentResponse(action=action, parameters=params)
        assert validated.action == "complete"

    def test_parse_fallback_to_simple_pattern(self):
        """Test fallback to simple pattern matching."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor

        executor = MinimalContextExecutor(project_path=Path("/tmp"))

        response = "I will use action: read_file to examine the code."

        action, params = executor._parse_action(response)

        assert action == "read_file"
        assert params == {}

    def test_parse_handles_malformed_yaml(self):
        """Test handling of malformed YAML."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor

        executor = MinimalContextExecutor(project_path=Path("/tmp"))

        response = '''```yaml
action: [this is not valid yaml
parameters:
  foo: bar
```'''

        action, params = executor._parse_action(response)

        # Should fallback to unknown when YAML is malformed
        assert action == "unknown"
        assert params == {}

    def test_parse_handles_empty_parameters(self):
        """Test handling of empty/null parameters."""
        from agentforge.core.harness.minimal_context.executor import MinimalContextExecutor

        executor = MinimalContextExecutor(project_path=Path("/tmp"))

        response = '''```yaml
action: complete
parameters:
```'''

        action, params = executor._parse_action(response)

        assert action == "complete"
        assert params == {}


class TestValueHintsPopulation:
    """Tests for value_hints population from precomputed context."""

    def test_extract_function_gets_hints_from_candidates(self):
        """Test that extract_function action gets hints from extraction candidates."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            PhaseMachine,
            Phase,
        )

        builder = EnhancedContextBuilder(project_path=Path("/tmp"))
        machine = PhaseMachine()
        machine._current_phase = Phase.IMPLEMENT

        precomputed = {
            "extraction_candidates": [
                {
                    "start_line": 42,
                    "end_line": 65,
                    "suggested_name": "calculate_total",
                    "source_function": "process_order",
                    "file_path": "/tmp/orders.py",
                }
            ]
        }

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Extract function",
                success_criteria=["Done"],
            ),
            state_spec=StateSpec(),
            domain_context={},
            precomputed=precomputed,
            phase_machine=machine,
        )

        # Find extract_function action
        extract_action = next(
            (a for a in context.actions.available if a.name == "extract_function"),
            None,
        )

        assert extract_action is not None
        assert extract_action.value_hints.get("start_line") == "42"
        assert extract_action.value_hints.get("end_line") == "65"
        assert extract_action.value_hints.get("new_function_name") == "calculate_total"
        assert extract_action.value_hints.get("source_function") == "process_order"

    def test_read_file_gets_path_hint(self):
        """Test that read_file action gets path hint from precomputed."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            PhaseMachine,
            Phase,
        )

        builder = EnhancedContextBuilder(project_path=Path("/tmp"))
        machine = PhaseMachine()
        machine._current_phase = Phase.ANALYZE

        precomputed = {
            "file_path": "/tmp/target_file.py",
        }

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Analyze file",
                success_criteria=["Done"],
            ),
            state_spec=StateSpec(),
            domain_context={},
            precomputed=precomputed,
            phase_machine=machine,
        )

        # Find read_file action
        read_action = next(
            (a for a in context.actions.available if a.name == "read_file"),
            None,
        )

        assert read_action is not None
        assert read_action.value_hints.get("path") == "/tmp/target_file.py"

    def test_edit_file_gets_line_hint(self):
        """Test that edit_file action gets line number hint."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            PhaseMachine,
            Phase,
        )

        builder = EnhancedContextBuilder(project_path=Path("/tmp"))
        machine = PhaseMachine()
        machine._current_phase = Phase.IMPLEMENT

        precomputed = {
            "file_path": "/tmp/target.py",
            "line_number": 123,
        }

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Edit file",
                success_criteria=["Done"],
            ),
            state_spec=StateSpec(),
            domain_context={},
            precomputed=precomputed,
            phase_machine=machine,
        )

        # Find edit_file action
        edit_action = next(
            (a for a in context.actions.available if a.name == "edit_file"),
            None,
        )

        assert edit_action is not None
        assert edit_action.value_hints.get("path") == "/tmp/target.py"
        assert edit_action.value_hints.get("start_line") == "123"

    def test_no_hints_without_precomputed(self):
        """Test that no hints are added when precomputed is empty."""
        from agentforge.core.harness.minimal_context import (
            EnhancedContextBuilder,
            TaskSpec,
            StateSpec,
            PhaseMachine,
            Phase,
        )

        builder = EnhancedContextBuilder(project_path=Path("/tmp"))
        machine = PhaseMachine()
        machine._current_phase = Phase.IMPLEMENT

        context = builder.build_context(
            task_spec=TaskSpec(
                task_id="test",
                task_type="fix",
                goal="Edit file",
                success_criteria=["Done"],
            ),
            state_spec=StateSpec(),
            domain_context={},
            precomputed={},  # Empty
            phase_machine=machine,
        )

        # Actions should have no value hints
        for action in context.actions.available:
            assert action.value_hints == {}


class TestSchemaVersioning:
    """Tests for state store schema versioning and migration."""

    def test_schema_version_exported(self):
        """Test that SCHEMA_VERSION is exported."""
        from agentforge.core.harness.minimal_context import SCHEMA_VERSION

        assert SCHEMA_VERSION == "2.0"

    def test_new_task_has_schema_version(self, tmp_path):
        """Test that newly created tasks have schema version."""
        from agentforge.core.harness.minimal_context import TaskStateStore
        import yaml

        store = TaskStateStore(tmp_path)
        task = store.create_task(
            task_type="test",
            goal="Test goal",
            success_criteria=["Done"],
        )

        # Read state.yaml directly
        state_file = tmp_path / ".agentforge" / "tasks" / task.task_id / "state.yaml"
        with open(state_file) as f:
            state_data = yaml.safe_load(f)

        assert state_data["schema_version"] == "2.0"

    def test_migrate_v1_to_v2(self, tmp_path):
        """Test migration from v1.0 (no version) to v2.0."""
        from agentforge.core.harness.minimal_context import TaskStateStore, TaskPhase
        import yaml

        # Create a v1.0 style state (no schema_version, no phase_machine_state)
        task_dir = tmp_path / ".agentforge" / "tasks" / "legacy-task"
        task_dir.mkdir(parents=True)

        # Write legacy task.yaml
        task_data = {
            "task_id": "legacy-task",
            "task_type": "fix_violation",
            "goal": "Fix a legacy bug",
            "success_criteria": ["Tests pass"],
            "constraints": [],
            "created_at": "2024-01-01T00:00:00+00:00",
        }
        with open(task_dir / "task.yaml", "w") as f:
            yaml.dump(task_data, f)

        # Write legacy state.yaml (v1.0 - no schema_version)
        state_data = {
            "phase": "init",
            "current_step": 5,
            "verification": {
                "checks_passing": 0,
                "checks_failing": 1,
                "tests_passing": True,
            },
            "last_updated": "2024-01-01T01:00:00+00:00",
            "error": None,
            "context_data": {"file_path": "test.py"},
            # Note: no phase_machine_state, no ready_for_completion
        }
        with open(task_dir / "state.yaml", "w") as f:
            yaml.dump(state_data, f)

        # Load the task - should trigger migration
        store = TaskStateStore(tmp_path)
        loaded = store.load("legacy-task")

        # Verify migration
        assert loaded is not None
        assert loaded.phase == TaskPhase.INIT
        assert loaded.current_step == 5
        assert loaded.phase_machine_state == {}  # Added by migration
        assert loaded.verification.ready_for_completion is False  # Added by migration

        # Verify state.yaml was updated with new version
        with open(task_dir / "state.yaml") as f:
            updated_data = yaml.safe_load(f)

        assert updated_data["schema_version"] == "2.0"
        assert "phase_machine_state" in updated_data

    def test_load_current_version_no_migration(self, tmp_path):
        """Test that current version doesn't trigger migration."""
        from agentforge.core.harness.minimal_context import TaskStateStore

        store = TaskStateStore(tmp_path)

        # Create a new task (v2.0)
        task = store.create_task(
            task_type="test",
            goal="Test",
            success_criteria=["Done"],
        )

        # Load it back
        loaded = store.load(task.task_id)

        assert loaded is not None
        assert loaded.task_id == task.task_id

    def test_migration_preserves_data(self, tmp_path):
        """Test that migration preserves all existing data."""
        from agentforge.core.harness.minimal_context import TaskStateStore
        import yaml

        task_dir = tmp_path / ".agentforge" / "tasks" / "preserve-test"
        task_dir.mkdir(parents=True)

        # Write task.yaml
        task_data = {
            "task_id": "preserve-test",
            "task_type": "fix_violation",
            "goal": "Preserve my data",
            "success_criteria": ["Data preserved"],
            "constraints": ["No data loss"],
            "created_at": "2024-06-15T12:00:00+00:00",
        }
        with open(task_dir / "task.yaml", "w") as f:
            yaml.dump(task_data, f)

        # Write v1.0 state with lots of data
        state_data = {
            "phase": "implement",
            "current_step": 42,
            "verification": {
                "checks_passing": 5,
                "checks_failing": 2,
                "tests_passing": True,
                "details": {"custom": "data"},
            },
            "last_updated": "2024-06-15T14:30:00+00:00",
            "error": "Previous error",
            "context_data": {
                "file_path": "important.py",
                "line_number": 123,
                "precomputed": {"analysis": "results"},
            },
        }
        with open(task_dir / "state.yaml", "w") as f:
            yaml.dump(state_data, f)

        # Load and verify all data preserved
        store = TaskStateStore(tmp_path)
        loaded = store.load("preserve-test")

        assert loaded.current_step == 42
        assert loaded.verification.checks_passing == 5
        assert loaded.verification.checks_failing == 2
        assert loaded.verification.details == {"custom": "data"}
        assert loaded.error == "Previous error"
        assert loaded.context_data["file_path"] == "important.py"
        assert loaded.context_data["precomputed"]["analysis"] == "results"


class TestFactCompaction:
    """Tests for proactive fact compaction."""

    def test_understanding_compact_reduces_facts(self):
        """Test that compact() reduces facts to max threshold."""
        from agentforge.core.harness.minimal_context import (
            Understanding,
            Fact,
            FactCategory,
        )

        # Create 30 low-confidence facts
        facts = [
            Fact(
                id=f"fact-{i}",
                category=FactCategory.INFERENCE,
                statement=f"Fact number {i}",
                confidence=0.5,
                source="test",
                step=i,
            )
            for i in range(30)
        ]

        understanding = Understanding(facts=facts)
        assert len(understanding.get_active_facts()) == 30

        # Compact to 15
        compacted = understanding.compact(max_facts=15)
        assert len(compacted.get_active_facts()) == 15

    def test_understanding_compact_preserves_high_value(self):
        """Test that compaction preserves high-value facts."""
        from agentforge.core.harness.minimal_context import (
            Understanding,
            Fact,
            FactCategory,
        )

        # Create mix of low and high value facts
        facts = [
            # High value: verification + high confidence
            Fact(
                id="high-1",
                category=FactCategory.VERIFICATION,
                statement="Check passed",
                confidence=1.0,
                source="test",
                step=1,
            ),
            # High value: error fact
            Fact(
                id="high-2",
                category=FactCategory.ERROR,
                statement="Important error",
                confidence=0.9,
                source="test",
                step=2,
            ),
            # Low value: inference with low confidence
            *[
                Fact(
                    id=f"low-{i}",
                    category=FactCategory.INFERENCE,
                    statement=f"Low value fact {i}",
                    confidence=0.3,
                    source="test",
                    step=i + 10,
                )
                for i in range(20)
            ],
        ]

        understanding = Understanding(facts=facts)
        compacted = understanding.compact(max_facts=5)

        active_ids = [f.id for f in compacted.get_active_facts()]
        assert "high-1" in active_ids
        assert "high-2" in active_ids

    def test_understanding_compact_noop_under_threshold(self):
        """Test that compaction is a no-op under threshold."""
        from agentforge.core.harness.minimal_context import (
            Understanding,
            Fact,
            FactCategory,
        )

        facts = [
            Fact(
                id=f"fact-{i}",
                category=FactCategory.INFERENCE,
                statement=f"Fact {i}",
                confidence=0.5,
                source="test",
                step=i,
            )
            for i in range(10)
        ]

        understanding = Understanding(facts=facts)
        compacted = understanding.compact(max_facts=20)

        # Should be the same object since under threshold
        assert compacted is understanding
        assert len(compacted.get_active_facts()) == 10

    def test_understanding_compact_prioritizes_categories(self):
        """Test that compaction prioritizes by category importance."""
        from agentforge.core.harness.minimal_context import (
            Understanding,
            Fact,
            FactCategory,
        )

        # All same confidence, different categories
        facts = [
            Fact(
                id="verify",
                category=FactCategory.VERIFICATION,
                statement="Verification fact",
                confidence=0.7,
                source="test",
                step=1,
            ),
            Fact(
                id="error",
                category=FactCategory.ERROR,
                statement="Error fact",
                confidence=0.7,
                source="test",
                step=2,
            ),
            Fact(
                id="code",
                category=FactCategory.CODE_STRUCTURE,
                statement="Code structure fact",
                confidence=0.7,
                source="test",
                step=3,
            ),
            Fact(
                id="infer",
                category=FactCategory.INFERENCE,
                statement="Inference fact",
                confidence=0.7,
                source="test",
                step=4,
            ),
        ]

        understanding = Understanding(facts=facts)
        compacted = understanding.compact(max_facts=2)

        active_ids = [f.id for f in compacted.get_active_facts()]
        # VERIFICATION (0.7 + 0.3 = 1.0) and ERROR (0.7 + 0.2 = 0.9) should be kept
        assert "verify" in active_ids
        assert "error" in active_ids
        assert "infer" not in active_ids
