# @spec_file: specs/pipeline-controller/implementation/phase-5-cli-commands.yaml
# @spec_id: pipeline-controller-phase5-v1

"""Shared fixtures for CLI integration tests."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock
from datetime import datetime, timezone
import tempfile
import shutil

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Create a Click CliRunner for testing."""
    return CliRunner()


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with .agentforge structure."""
    agentforge_dir = tmp_path / ".agentforge"
    agentforge_dir.mkdir()

    # Create subdirectories
    (agentforge_dir / "specs").mkdir()
    (agentforge_dir / "artifacts").mkdir()
    (agentforge_dir / "pipelines").mkdir()
    (agentforge_dir / "state").mkdir()

    # Create a minimal project structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    return tmp_path


@pytest.fixture
def temp_project_with_state(temp_project):
    """Create a project with existing pipeline state."""
    state_dir = temp_project / ".agentforge" / "state"

    # Create a sample pipeline state
    state_content = """
pipeline_id: PL-20260102-int001
pipeline_type: implement
status: completed
current_stage: deliver
completed_stages:
  - intake
  - clarify
  - analyze
  - spec
  - red
  - green
  - refactor
  - deliver
user_request: Add integration test feature
created_at: "2026-01-02T10:00:00Z"
updated_at: "2026-01-02T10:05:00Z"
total_tokens_used: 15000
total_cost_usd: 0.075
"""
    (state_dir / "PL-20260102-int001.yaml").write_text(state_content)

    return temp_project


@pytest.fixture
def temp_project_with_spec(temp_project):
    """Create a project with an existing specification."""
    specs_dir = temp_project / ".agentforge" / "specs"

    spec_content = """
spec_id: SPEC-20260102-INT
title: Integration Test Feature
version: "1.0"
overview:
  description: A test feature for integration testing
  goals:
    - Test CLI commands
components:
  - id: test-component
    name: TestComponent
    type: module
test_cases:
  - id: test-basic
    description: Basic functionality test
acceptance_criteria:
  - Commands work correctly
"""
    (specs_dir / "SPEC-20260102-INT.yaml").write_text(spec_content)

    return temp_project


@pytest.fixture
def temp_project_with_artifacts(temp_project):
    """Create a project with pipeline artifacts."""
    pipeline_id = "PL-20260102-int001"
    artifacts_dir = temp_project / ".agentforge" / "artifacts" / pipeline_id
    artifacts_dir.mkdir(parents=True)

    # Create artifacts for each stage
    (artifacts_dir / "01-intake.yaml").write_text("""
request_id: REQ-INT-001
original_request: Add integration test feature
detected_scope: feature_addition
priority: medium
confidence: 0.85
""")

    (artifacts_dir / "02-clarify.yaml").write_text("""
request_id: REQ-INT-001
clarified_requirements: Add comprehensive integration tests for CLI
scope_confirmed: true
ready_for_analysis: true
""")

    (artifacts_dir / "03-analyze.yaml").write_text("""
request_id: REQ-INT-001
affected_files:
  - path: tests/integration/cli/test_commands.py
    change_type: create
components:
  - name: CLITests
    type: test_suite
dependencies:
  - click
  - pytest
""")

    (artifacts_dir / "04-spec.yaml").write_text("""
spec_id: SPEC-20260102-INT
request_id: REQ-INT-001
title: Integration Test Feature
version: "1.0"
components:
  - id: cli-tests
    name: CLIIntegrationTests
test_cases:
  - id: test-start-command
    description: Test start command integration
""")

    return temp_project


@pytest.fixture
def mock_pipeline_controller():
    """Create a mock PipelineController for integration tests."""
    from unittest.mock import MagicMock

    controller = MagicMock()

    # Setup successful execute
    result = MagicMock()
    result.success = True
    result.pipeline_id = "PL-20260102-int001"
    result.stages_completed = ["intake", "clarify", "analyze", "spec", "red", "green", "refactor", "deliver"]
    result.total_duration_seconds = 120.0
    result.deliverable = {
        "commit_sha": "abc123int",
        "files_modified": ["src/feature.py", "tests/test_feature.py"],
    }
    result.error = None
    result.current_stage = None
    controller.execute.return_value = result

    # Setup status
    state = MagicMock()
    state.pipeline_id = "PL-20260102-int001"
    state.pipeline_type = "implement"
    state.status = MagicMock()
    state.status.value = "completed"
    state.current_stage = "deliver"
    state.completed_stages = ["intake", "clarify", "analyze", "spec", "red", "green", "refactor", "deliver"]
    state.error = None
    state.user_request = "Add integration test feature"
    state.created_at = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    state.updated_at = datetime(2026, 1, 2, 10, 5, 0, tzinfo=timezone.utc)
    state.total_tokens_used = 15000
    state.total_cost_usd = 0.075
    controller.get_status.return_value = state
    controller.list_pipelines.return_value = [state]

    controller.approve.return_value = True
    controller.abort.return_value = True

    return controller
