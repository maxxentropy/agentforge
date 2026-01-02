# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1

"""Shared fixtures for CLI command tests."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Create a Click CliRunner for testing CLI commands."""
    return CliRunner()


@pytest.fixture
def mock_controller():
    """Create a mock PipelineController."""
    controller = MagicMock()

    # Default execute behavior
    result = MagicMock()
    result.success = True
    result.pipeline_id = "PL-20260102-abc123"
    result.stages_completed = ["intake", "clarify", "analyze", "spec"]
    result.total_duration_seconds = 45.2
    result.deliverable = {"commit_sha": "abc123def456"}
    result.error = None
    result.current_stage = None
    controller.execute.return_value = result

    # Default get_status behavior
    state = MagicMock()
    state.pipeline_id = "PL-20260102-abc123"
    state.pipeline_type = "implement"
    state.status = MagicMock()
    state.status.value = "completed"
    state.current_stage = "deliver"
    state.completed_stages = ["intake", "clarify", "analyze", "spec", "red", "green", "refactor"]
    state.error = None
    state.user_request = "Add OAuth authentication"
    state.created_at = datetime(2026, 1, 2, 10, 0, 0, tzinfo=UTC)
    state.updated_at = datetime(2026, 1, 2, 10, 1, 0, tzinfo=UTC)
    state.total_tokens_used = 10000
    state.total_cost_usd = 0.05
    controller.get_status.return_value = state

    # Default list_pipelines behavior
    controller.list_pipelines.return_value = [state]

    # Default approve/abort behavior
    controller.approve.return_value = True
    controller.abort.return_value = True

    return controller


@pytest.fixture
def mock_controller_paused():
    """Create a mock PipelineController with paused pipeline."""
    controller = MagicMock()

    state = MagicMock()
    state.pipeline_id = "PL-20260102-paused"
    state.pipeline_type = "implement"
    state.status = MagicMock()
    state.status.value = "paused"
    state.current_stage = "spec"
    state.completed_stages = ["intake", "clarify", "analyze"]
    state.error = None
    state.user_request = "Add feature"
    state.created_at = datetime(2026, 1, 2, 10, 0, 0, tzinfo=UTC)
    state.updated_at = datetime(2026, 1, 2, 10, 1, 0, tzinfo=UTC)
    state.total_tokens_used = 5000
    state.total_cost_usd = 0.025
    controller.get_status.return_value = state
    controller.list_pipelines.return_value = [state]

    return controller


@pytest.fixture
def mock_controller_awaiting():
    """Create a mock PipelineController awaiting approval."""
    controller = MagicMock()

    state = MagicMock()
    state.pipeline_id = "PL-20260102-await"
    state.pipeline_type = "design"
    state.status = MagicMock()
    state.status.value = "awaiting_approval"
    state.current_stage = "spec"
    state.completed_stages = ["intake", "clarify", "analyze"]
    state.error = None
    state.user_request = "Design authentication"
    state.created_at = datetime(2026, 1, 2, 10, 0, 0, tzinfo=UTC)
    state.updated_at = datetime(2026, 1, 2, 10, 1, 0, tzinfo=UTC)
    state.total_tokens_used = 5000
    state.total_cost_usd = 0.025
    controller.get_status.return_value = state
    controller.list_pipelines.return_value = [state]
    controller.approve.return_value = True

    return controller


@pytest.fixture
def mock_controller_failed():
    """Create a mock PipelineController with failed pipeline."""
    controller = MagicMock()

    result = MagicMock()
    result.success = False
    result.pipeline_id = "PL-20260102-fail"
    result.stages_completed = ["intake", "clarify"]
    result.total_duration_seconds = 15.0
    result.deliverable = None
    result.error = "Analysis failed: could not parse codebase"
    result.current_stage = "analyze"
    controller.execute.return_value = result

    state = MagicMock()
    state.pipeline_id = "PL-20260102-fail"
    state.pipeline_type = "implement"
    state.status = MagicMock()
    state.status.value = "failed"
    state.current_stage = "analyze"
    state.completed_stages = ["intake", "clarify"]
    state.error = "Analysis failed: could not parse codebase"
    state.user_request = "Add broken feature"
    state.created_at = datetime(2026, 1, 2, 10, 0, 0, tzinfo=UTC)
    state.updated_at = datetime(2026, 1, 2, 10, 1, 0, tzinfo=UTC)
    state.total_tokens_used = 2000
    state.total_cost_usd = 0.01
    controller.get_status.return_value = state
    controller.list_pipelines.return_value = [state]

    return controller


@pytest.fixture
def temp_project_with_spec(tmp_path):
    """Create a temp project with an existing spec file."""
    agentforge_dir = tmp_path / ".agentforge"
    specs_dir = agentforge_dir / "specs"
    specs_dir.mkdir(parents=True)

    # Create a sample spec file
    spec_content = """
spec_id: SPEC-20260102-0001
title: Add OAuth Authentication
version: "1.0"
overview:
  description: Add OAuth2 authentication flow
components:
  - id: oauth-handler
    name: OAuthHandler
test_cases:
  - id: test-oauth-flow
    description: Test OAuth flow
"""
    (specs_dir / "SPEC-20260102-0001.yaml").write_text(spec_content)

    return tmp_path


@pytest.fixture
def temp_project_with_artifacts(tmp_path):
    """Create a temp project with pipeline artifacts."""
    artifacts_dir = tmp_path / ".agentforge" / "artifacts" / "PL-20260102-abc123"
    artifacts_dir.mkdir(parents=True)

    # Create sample artifacts
    (artifacts_dir / "01-intake.yaml").write_text("""
request_id: REQ-001
detected_scope: feature_addition
priority: medium
""")

    (artifacts_dir / "02-clarify.yaml").write_text("""
request_id: REQ-001
clarified_requirements: Add OAuth2 authentication
scope_confirmed: true
""")

    (artifacts_dir / "03-analyze.yaml").write_text("""
request_id: REQ-001
affected_files:
  - path: src/auth/oauth.py
components:
  - name: AuthModule
""")

    (artifacts_dir / "04-spec.yaml").write_text("""
spec_id: SPEC-20260102-0001
title: OAuth Authentication
components:
  - id: oauth-handler
""")

    return tmp_path


@pytest.fixture
def sample_pipeline_result_success():
    """Create a successful pipeline result."""
    result = MagicMock()
    result.success = True
    result.pipeline_id = "PL-20260102-abc123"
    result.stages_completed = ["intake", "clarify", "analyze", "spec", "red", "green", "refactor", "deliver"]
    result.total_duration_seconds = 120.5
    result.deliverable = {
        "commit_sha": "abc123def456789",
        "pr_url": "https://github.com/user/repo/pull/42",
        "files_modified": ["src/auth/oauth.py", "tests/test_oauth.py"],
    }
    result.error = None
    result.current_stage = None
    return result


@pytest.fixture
def sample_pipeline_result_design():
    """Create a successful design-only result."""
    result = MagicMock()
    result.success = True
    result.pipeline_id = "PL-20260102-design"
    result.stages_completed = ["intake", "clarify", "analyze", "spec"]
    result.total_duration_seconds = 30.0
    result.deliverable = {"spec_id": "SPEC-20260102-0001"}
    result.error = None
    result.current_stage = None
    return result


@pytest.fixture
def multiple_pipelines():
    """Create multiple pipeline states for list testing."""
    pipelines = []

    for i, (status, stage) in enumerate([
        ("running", "green"),
        ("completed", "deliver"),
        ("failed", "analyze"),
        ("paused", "spec"),
    ]):
        state = MagicMock()
        state.pipeline_id = f"PL-20260102-{i:03d}"
        state.pipeline_type = "implement" if i % 2 == 0 else "design"
        state.status = MagicMock()
        state.status.value = status
        state.current_stage = stage
        state.completed_stages = ["intake", "clarify"]
        state.created_at = datetime(2026, 1, 2, 10, i, 0, tzinfo=UTC)
        pipelines.append(state)

    return pipelines
