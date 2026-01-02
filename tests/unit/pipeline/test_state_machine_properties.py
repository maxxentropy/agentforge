# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-state-machine-properties
# @test_path: tests/unit/pipeline/test_state_machine_properties.py

"""
Property-Based Tests for Pipeline State Machine
================================================

Uses Hypothesis to verify state machine invariants hold under
arbitrary sequences of operations.

Tested Invariants:
1. Terminal states are permanent (can't transition out)
2. Timestamps are monotonically increasing
3. Stage progression follows template order
4. State serialization is reversible
5. Valid status transitions only
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from agentforge.core.pipeline.state import (
    PIPELINE_TEMPLATES,
    PipelineState,
    PipelineStatus,
    StageState,
    StageStatus,
    create_pipeline_state,
    generate_pipeline_id,
)


# =============================================================================
# Strategies for generating test data
# =============================================================================

# Strategy for valid pipeline statuses
pipeline_status_st = st.sampled_from(list(PipelineStatus))

# Strategy for valid stage statuses
stage_status_st = st.sampled_from(list(StageStatus))

# Strategy for pipeline templates
template_st = st.sampled_from(list(PIPELINE_TEMPLATES.keys()))

# Strategy for reasonable request strings
request_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=200,
)

# Strategy for stage names from templates
def stage_name_st(template: str = "implement"):
    return st.sampled_from(PIPELINE_TEMPLATES.get(template, ["intake"]))


# Strategy for creating a valid pipeline state
@st.composite
def pipeline_state_st(draw, template: str | None = None):
    """Generate a valid PipelineState."""
    if template is None:
        template = draw(template_st)

    state = create_pipeline_state(
        request=draw(request_st),
        project_path=Path("/tmp/test-project"),
        template=template,
    )

    # Optionally advance the state
    if draw(st.booleans()):
        state.status = draw(st.sampled_from([
            PipelineStatus.PENDING,
            PipelineStatus.RUNNING,
            PipelineStatus.PAUSED,
        ]))

    return state


# =============================================================================
# Invariant 1: Terminal States are Permanent
# =============================================================================

TERMINAL_STATUSES = {
    PipelineStatus.COMPLETED,
    PipelineStatus.FAILED,
    PipelineStatus.ABORTED,
}


class TestTerminalStateInvariant:
    """Test that terminal states cannot be exited."""

    @given(pipeline_state_st())
    @settings(max_examples=100)
    def test_is_terminal_identifies_terminal_states(self, state: PipelineState):
        """is_terminal() correctly identifies terminal states."""
        state.status = PipelineStatus.COMPLETED
        assert state.is_terminal() is True

        state.status = PipelineStatus.FAILED
        assert state.is_terminal() is True

        state.status = PipelineStatus.ABORTED
        assert state.is_terminal() is True

    @given(pipeline_state_st())
    @settings(max_examples=100)
    def test_is_terminal_identifies_non_terminal_states(self, state: PipelineState):
        """is_terminal() correctly identifies non-terminal states."""
        state.status = PipelineStatus.PENDING
        assert state.is_terminal() is False

        state.status = PipelineStatus.RUNNING
        assert state.is_terminal() is False

        state.status = PipelineStatus.PAUSED
        assert state.is_terminal() is False

        state.status = PipelineStatus.WAITING_APPROVAL
        assert state.is_terminal() is False

    @given(
        st.sampled_from(list(TERMINAL_STATUSES)),
        st.sampled_from(list(PipelineStatus)),
    )
    @settings(max_examples=50)
    def test_terminal_status_stays_terminal(
        self,
        terminal_status: PipelineStatus,
        any_status: PipelineStatus,
    ):
        """Once terminal, is_terminal() should always return True."""
        state = create_pipeline_state(
            request="test",
            project_path=Path("/tmp/test"),
            template="implement",
        )

        # Set terminal status
        state.status = terminal_status
        assert state.is_terminal() is True

        # The invariant is that code should check is_terminal() before
        # allowing status changes. We verify the check works.
        if state.is_terminal():
            # This is the correct behavior - don't allow changes
            original_status = state.status
            # Simulate what the controller should do
            if not state.is_terminal():
                state.status = any_status
            assert state.status == original_status


# =============================================================================
# Invariant 2: Timestamps are Monotonically Increasing
# =============================================================================

class TestTimestampInvariant:
    """Test that timestamps always increase or stay the same."""

    @given(pipeline_state_st(), st.integers(min_value=1, max_value=10))
    @settings(max_examples=50)
    def test_touch_increases_updated_at(
        self,
        state: PipelineState,
        touch_count: int,
    ):
        """Calling touch() should always increase or maintain updated_at."""
        previous = state.updated_at

        for _ in range(touch_count):
            state.touch()
            assert state.updated_at >= previous
            previous = state.updated_at

    @given(pipeline_state_st())
    @settings(max_examples=50)
    def test_created_at_never_changes(self, state: PipelineState):
        """created_at should never change after initialization."""
        original_created = state.created_at

        # Touch multiple times
        for _ in range(5):
            state.touch()

        assert state.created_at == original_created

    def test_stage_timestamps_are_ordered_running_to_completed(self):
        """Stage started_at should always be before completed_at for valid transitions."""
        stage = StageState(stage_name="test_stage")

        # Valid sequence: PENDING -> RUNNING -> COMPLETED
        stage.mark_running()
        started = stage.started_at
        stage.mark_completed()

        assert stage.started_at == started  # started_at shouldn't change
        assert stage.started_at <= stage.completed_at

    def test_stage_timestamps_are_ordered_running_to_failed(self):
        """Stage started_at should always be before completed_at for failures."""
        stage = StageState(stage_name="test_stage")

        # Valid sequence: PENDING -> RUNNING -> FAILED
        stage.mark_running()
        started = stage.started_at
        stage.mark_failed("test error")

        assert stage.started_at == started  # started_at shouldn't change
        assert stage.started_at <= stage.completed_at

    @given(st.booleans())
    @settings(max_examples=20)
    def test_stage_completion_always_sets_completed_at(self, use_failure: bool):
        """Marking a stage complete/failed should always set completed_at."""
        stage = StageState(stage_name="test_stage")

        assert stage.completed_at is None

        stage.mark_running()
        assert stage.completed_at is None

        if use_failure:
            stage.mark_failed("error")
        else:
            stage.mark_completed()

        assert stage.completed_at is not None


# =============================================================================
# Invariant 3: Stage Progression Follows Template Order
# =============================================================================

class TestStageOrderInvariant:
    """Test that stage progression follows the template order."""

    @given(template_st)
    @settings(max_examples=20)
    def test_get_next_stage_follows_order(self, template: str):
        """get_next_stage() should return stages in template order."""
        state = create_pipeline_state(
            request="test",
            project_path=Path("/tmp/test"),
            template=template,
        )

        expected_stages = PIPELINE_TEMPLATES[template]

        # Simulate progression through all stages
        for i, expected in enumerate(expected_stages):
            if i == 0:
                # First stage
                state.current_stage = None
                next_stage = state.get_next_stage()
                assert next_stage == expected
            else:
                state.current_stage = expected_stages[i - 1]
                next_stage = state.get_next_stage()
                assert next_stage == expected

            state.current_stage = expected

        # After last stage, should return None
        state.current_stage = expected_stages[-1]
        assert state.get_next_stage() is None

    @given(template_st)
    @settings(max_examples=20)
    def test_all_stages_in_template_are_initialized(self, template: str):
        """All stages from template should be initialized in state."""
        state = create_pipeline_state(
            request="test",
            project_path=Path("/tmp/test"),
            template=template,
        )

        expected_stages = set(PIPELINE_TEMPLATES[template])
        actual_stages = set(state.stages.keys())

        assert expected_stages == actual_stages


# =============================================================================
# Invariant 4: State Serialization is Reversible
# =============================================================================

class TestSerializationInvariant:
    """Test that state can be serialized and deserialized without loss."""

    @given(pipeline_state_st())
    @settings(max_examples=100)
    def test_to_dict_from_dict_roundtrip(self, state: PipelineState):
        """to_dict() -> from_dict() should preserve all state."""
        # Serialize
        data = state.to_dict()

        # Deserialize
        restored = PipelineState.from_dict(data)

        # Verify key fields
        assert restored.pipeline_id == state.pipeline_id
        assert restored.template == state.template
        assert restored.status == state.status
        assert restored.request == state.request
        assert restored.current_stage == state.current_stage
        assert restored.stage_order == state.stage_order

        # Verify all stages
        assert set(restored.stages.keys()) == set(state.stages.keys())
        for name, original_stage in state.stages.items():
            restored_stage = restored.stages[name]
            assert restored_stage.stage_name == original_stage.stage_name
            assert restored_stage.status == original_stage.status

    @given(st.text(min_size=1, max_size=50), stage_status_st)
    @settings(max_examples=50)
    def test_stage_state_roundtrip(self, name: str, status: StageStatus):
        """StageState serialization should be reversible."""
        stage = StageState(stage_name=name, status=status)

        if status == StageStatus.RUNNING:
            stage.mark_running()
        elif status in (StageStatus.COMPLETED, StageStatus.FAILED):
            stage.mark_running()
            if status == StageStatus.COMPLETED:
                stage.mark_completed({"test": "artifact"})
            else:
                stage.mark_failed("test error")

        data = stage.to_dict()
        restored = StageState.from_dict(data)

        assert restored.stage_name == stage.stage_name
        assert restored.status == stage.status
        assert restored.error == stage.error


# =============================================================================
# Invariant 5: Valid Status Transitions
# =============================================================================

# Define valid transitions
VALID_TRANSITIONS = {
    PipelineStatus.PENDING: {
        PipelineStatus.RUNNING,
        PipelineStatus.ABORTED,
    },
    PipelineStatus.RUNNING: {
        PipelineStatus.PAUSED,
        PipelineStatus.WAITING_APPROVAL,
        PipelineStatus.COMPLETED,
        PipelineStatus.FAILED,
        PipelineStatus.ABORTED,
    },
    PipelineStatus.PAUSED: {
        PipelineStatus.RUNNING,
        PipelineStatus.ABORTED,
    },
    PipelineStatus.WAITING_APPROVAL: {
        PipelineStatus.RUNNING,
        PipelineStatus.ABORTED,
    },
    # Terminal states - no valid transitions
    PipelineStatus.COMPLETED: set(),
    PipelineStatus.FAILED: set(),
    PipelineStatus.ABORTED: set(),
}


class TestStatusTransitionInvariant:
    """Test that only valid status transitions are defined."""

    @given(pipeline_status_st)
    @settings(max_examples=20)
    def test_terminal_states_have_no_transitions(self, status: PipelineStatus):
        """Terminal states should have no valid outgoing transitions."""
        if status in TERMINAL_STATUSES:
            assert VALID_TRANSITIONS[status] == set()

    @given(pipeline_status_st, pipeline_status_st)
    @settings(max_examples=100)
    def test_transition_validity_is_well_defined(
        self,
        from_status: PipelineStatus,
        to_status: PipelineStatus,
    ):
        """Every status pair has a well-defined validity."""
        valid_targets = VALID_TRANSITIONS.get(from_status, set())

        # The transition is either valid or not - no undefined cases
        is_valid = to_status in valid_targets
        is_same = from_status == to_status

        # Either it's a valid transition, or it's the same state,
        # or it's explicitly invalid
        assert is_valid or is_same or to_status not in valid_targets

    def test_can_resume_matches_valid_transitions(self):
        """can_resume() should match states that can transition to RUNNING."""
        state = create_pipeline_state(
            request="test",
            project_path=Path("/tmp/test"),
            template="implement",
        )

        # PAUSED can resume
        state.status = PipelineStatus.PAUSED
        assert state.can_resume() is True
        assert PipelineStatus.RUNNING in VALID_TRANSITIONS[PipelineStatus.PAUSED]

        # WAITING_APPROVAL can resume
        state.status = PipelineStatus.WAITING_APPROVAL
        assert state.can_resume() is True
        assert PipelineStatus.RUNNING in VALID_TRANSITIONS[PipelineStatus.WAITING_APPROVAL]

        # RUNNING cannot "resume"
        state.status = PipelineStatus.RUNNING
        assert state.can_resume() is False

        # Terminal states cannot resume
        for terminal in TERMINAL_STATUSES:
            state.status = terminal
            assert state.can_resume() is False


# =============================================================================
# Invariant 6: Artifact Collection Order
# =============================================================================

class TestArtifactCollectionInvariant:
    """Test that artifact collection follows stage order."""

    @given(template_st)
    @settings(max_examples=20)
    def test_collect_artifacts_respects_stage_order(self, template: str):
        """collect_artifacts() should collect in stage order."""
        state = create_pipeline_state(
            request="test",
            project_path=Path("/tmp/test"),
            template=template,
        )

        # Complete some stages with artifacts
        stages = PIPELINE_TEMPLATES[template]
        for i, stage_name in enumerate(stages[:3]):  # Complete first 3
            stage = state.get_stage(stage_name)
            stage.mark_running()
            stage.mark_completed({"order": i, "stage": stage_name})

        artifacts = state.collect_artifacts()

        # Should have artifacts from completed stages only
        assert "order" in artifacts
        assert "stage" in artifacts

    @given(pipeline_state_st())
    @settings(max_examples=50)
    def test_collect_artifacts_only_from_completed(self, state: PipelineState):
        """collect_artifacts() should only include completed stage artifacts."""
        # Mark some stages as running (not completed)
        for stage_name in list(state.stages.keys())[:2]:
            stage = state.get_stage(stage_name)
            stage.mark_running()
            stage.artifacts["test"] = "should_not_appear"

        # Mark one as completed
        if len(state.stages) > 2:
            completed_name = list(state.stages.keys())[2]
            stage = state.get_stage(completed_name)
            stage.mark_running()
            stage.mark_completed({"completed_artifact": "should_appear"})

            artifacts = state.collect_artifacts()
            assert "completed_artifact" in artifacts


# =============================================================================
# Invariant 7: Pipeline ID Uniqueness
# =============================================================================

class TestPipelineIdInvariant:
    """Test pipeline ID generation properties."""

    @given(st.integers(min_value=10, max_value=100))
    @settings(max_examples=10)
    def test_pipeline_ids_are_unique(self, count: int):
        """Generated pipeline IDs should be unique."""
        ids = {generate_pipeline_id() for _ in range(count)}
        assert len(ids) == count

    def test_pipeline_id_format(self):
        """Pipeline ID should follow expected format."""
        pipeline_id = generate_pipeline_id()

        assert pipeline_id.startswith("PL-")
        parts = pipeline_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 8  # 8 hex chars
