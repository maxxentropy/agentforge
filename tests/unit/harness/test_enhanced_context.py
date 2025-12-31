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
