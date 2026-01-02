# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-state

"""Tests for pipeline state management."""

import re
from datetime import datetime

from agentforge.core.pipeline import (
    PIPELINE_TEMPLATES,
    PipelineState,
    PipelineStatus,
    StageState,
    StageStatus,
    create_pipeline_state,
    generate_pipeline_id,
)


class TestPipelineIdGeneration:
    """Tests for pipeline ID generation."""

    def test_generate_pipeline_id_format(self):
        """Pipeline ID follows format PL-YYYYMMDD-uuid8."""
        pipeline_id = generate_pipeline_id()

        # Should match pattern: PL-20260101-a1b2c3d4
        pattern = r"^PL-\d{8}-[a-f0-9]{8}$"
        assert re.match(pattern, pipeline_id), f"Invalid ID format: {pipeline_id}"

    def test_generate_pipeline_id_unique(self):
        """Each generated ID should be unique."""
        ids = [generate_pipeline_id() for _ in range(100)]
        assert len(ids) == len(set(ids)), "Generated duplicate IDs"

    def test_generate_pipeline_id_date_part(self):
        """Date part should reflect current date."""
        pipeline_id = generate_pipeline_id()
        date_part = pipeline_id.split("-")[1]
        today = datetime.now().strftime("%Y%m%d")
        assert date_part == today


class TestStageState:
    """Tests for StageState dataclass."""

    def test_stage_state_creation(self):
        """StageState can be created with defaults."""
        stage = StageState(stage_name="intake")

        assert stage.stage_name == "intake"
        assert stage.status == StageStatus.PENDING
        assert stage.started_at is None
        assert stage.completed_at is None
        assert stage.artifacts == {}
        assert stage.error is None

    def test_mark_running(self):
        """mark_running() updates status and started_at."""
        stage = StageState(stage_name="intake")
        stage.mark_running()

        assert stage.status == StageStatus.RUNNING
        assert stage.started_at is not None
        assert stage.completed_at is None

    def test_mark_completed(self):
        """mark_completed() updates status and timestamps."""
        stage = StageState(stage_name="intake")
        stage.mark_running()
        stage.mark_completed({"output": "result"})

        assert stage.status == StageStatus.COMPLETED
        assert stage.completed_at is not None
        assert stage.artifacts == {"output": "result"}

    def test_mark_failed(self):
        """mark_failed() updates status with error."""
        stage = StageState(stage_name="intake")
        stage.mark_running()
        stage.mark_failed("Something went wrong")

        assert stage.status == StageStatus.FAILED
        assert stage.error == "Something went wrong"
        assert stage.completed_at is not None

    def test_mark_skipped(self):
        """mark_skipped() updates status with reason."""
        stage = StageState(stage_name="intake")
        stage.mark_skipped("Not needed")

        assert stage.status == StageStatus.SKIPPED
        assert stage.artifacts.get("skip_reason") == "Not needed"

    def test_stage_state_serialization(self):
        """StageState serializes to/from dict correctly."""
        stage = StageState(stage_name="intake")
        stage.mark_running()
        stage.mark_completed({"output": "test"})

        data = stage.to_dict()
        restored = StageState.from_dict(data)

        assert restored.stage_name == stage.stage_name
        assert restored.status == stage.status
        assert restored.artifacts == stage.artifacts


class TestPipelineState:
    """Tests for PipelineState dataclass."""

    def test_pipeline_state_creation(self, temp_project):
        """PipelineState can be created with create_pipeline_state()."""
        state = create_pipeline_state(
            request="Add a button",
            project_path=temp_project,
            template="implement",
        )

        assert state.pipeline_id.startswith("PL-")
        assert state.template == "implement"
        assert state.status == PipelineStatus.PENDING
        assert state.request == "Add a button"
        assert state.project_path == temp_project
        assert state.stage_order == PIPELINE_TEMPLATES["implement"]

    def test_pipeline_templates(self):
        """Pipeline templates define stage order."""
        assert "design" in PIPELINE_TEMPLATES
        assert "implement" in PIPELINE_TEMPLATES
        assert "test" in PIPELINE_TEMPLATES
        assert "fix" in PIPELINE_TEMPLATES

        # Implement template has all stages
        assert PIPELINE_TEMPLATES["implement"] == [
            "intake", "clarify", "analyze", "spec",
            "red", "green", "refactor", "deliver"
        ]

    def test_get_next_stage_from_start(self, temp_project):
        """get_next_stage() returns first stage when current is None."""
        state = create_pipeline_state("request", temp_project, "implement")
        state.current_stage = None

        assert state.get_next_stage() == "intake"

    def test_get_next_stage_progression(self, temp_project):
        """get_next_stage() returns correct next stage."""
        state = create_pipeline_state("request", temp_project, "implement")
        state.current_stage = "intake"

        assert state.get_next_stage() == "clarify"

        state.current_stage = "clarify"
        assert state.get_next_stage() == "analyze"

    def test_get_next_stage_at_end(self, temp_project):
        """get_next_stage() returns None at last stage."""
        state = create_pipeline_state("request", temp_project, "implement")
        state.current_stage = "deliver"

        assert state.get_next_stage() is None

    def test_collect_artifacts(self, temp_project):
        """collect_artifacts() gathers all completed stage artifacts."""
        state = create_pipeline_state("request", temp_project, "implement")

        # Complete some stages with artifacts
        state.stages["intake"].mark_completed({"requirements": "data"})
        state.stages["clarify"].mark_completed({"questions": ["q1"]})
        state.stages["analyze"].status = StageStatus.PENDING  # Not complete

        artifacts = state.collect_artifacts()

        assert artifacts["requirements"] == "data"
        assert artifacts["questions"] == ["q1"]
        assert "analyze_output" not in artifacts

    def test_is_terminal(self, temp_project):
        """is_terminal() identifies terminal states correctly."""
        state = create_pipeline_state("request", temp_project)

        state.status = PipelineStatus.PENDING
        assert not state.is_terminal()

        state.status = PipelineStatus.RUNNING
        assert not state.is_terminal()

        state.status = PipelineStatus.COMPLETED
        assert state.is_terminal()

        state.status = PipelineStatus.FAILED
        assert state.is_terminal()

        state.status = PipelineStatus.ABORTED
        assert state.is_terminal()

    def test_can_resume(self, temp_project):
        """can_resume() identifies resumable states."""
        state = create_pipeline_state("request", temp_project)

        state.status = PipelineStatus.RUNNING
        assert not state.can_resume()

        state.status = PipelineStatus.PAUSED
        assert state.can_resume()

        state.status = PipelineStatus.WAITING_APPROVAL
        assert state.can_resume()

        state.status = PipelineStatus.COMPLETED
        assert not state.can_resume()

    def test_pipeline_state_serialization(self, temp_project):
        """PipelineState serializes to/from dict correctly."""
        state = create_pipeline_state(
            request="Test request",
            project_path=temp_project,
            template="design",
            config={"verbose": True},
        )
        state.current_stage = "intake"
        state.stages["intake"].mark_running()

        data = state.to_dict()
        restored = PipelineState.from_dict(data)

        assert restored.pipeline_id == state.pipeline_id
        assert restored.template == state.template
        assert restored.status == state.status
        assert restored.request == state.request
        assert restored.current_stage == state.current_stage
        assert restored.config == state.config
        assert restored.stage_order == state.stage_order

    def test_touch_updates_timestamp(self, temp_project):
        """touch() updates the updated_at timestamp."""
        state = create_pipeline_state("request", temp_project)
        original = state.updated_at

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        state.touch()
        assert state.updated_at > original
