# @spec_file: .agentforge/specs/core-tdflow-v1.yaml
# @spec_id: core-tdflow-v1
# @component_id: tools-tdflow-orchestrator
# @impl_path: tools/tdflow/orchestrator.py

"""Tests for TDFLOW orchestrator."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentforge.core.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    TDFlowPhase,
    TDFlowSession,
    RunResult,
)
from agentforge.core.tdflow.orchestrator import TDFlowOrchestrator


class TestTDFlowOrchestrator:
    """Tests for TDFlowOrchestrator."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def spec_file(self, temp_dir: Path) -> Path:
        """Create a test specification file."""
        spec_path = temp_dir / "spec.yaml"
        spec_path.write_text(
            """
components:
  - name: TestService
    namespace: App.Services
    methods:
      - name: DoWork
        returns: Result<string>
        behavior: Does some work
"""
        )
        return spec_path

    @pytest.fixture
    def orchestrator(self, temp_dir: Path) -> TDFlowOrchestrator:
        """Create an orchestrator for tests."""
        return TDFlowOrchestrator(project_path=temp_dir)

    def test_start_creates_session(
        self, orchestrator: TDFlowOrchestrator, spec_file: Path
    ):
        """Start creates a new session."""
        session = orchestrator.start(
            spec_file=spec_file,
            test_framework="pytest",
            coverage_threshold=75.0,
        )

        assert session is not None, "Expected session is not None"
        assert session.session_id.startswith("tdflow_"), "Expected session.session_id.startswith() to be truthy"
        assert session.test_framework == "pytest", "Expected session.test_framework to equal 'pytest'"
        assert session.coverage_threshold == 75.0, "Expected session.coverage_threshold to equal 75.0"
        assert len(session.components) == 1, "Expected len(session.components) to equal 1"
        assert session.components[0].name == "TestService", "Expected session.components[0].name to equal 'TestService'"

    def test_get_status_no_session(self, temp_dir: Path):
        """Get status returns inactive when no session."""
        orchestrator = TDFlowOrchestrator(project_path=temp_dir)

        status = orchestrator.get_status()

        assert status["active"] is False, "Expected status['active'] is False"

    def test_get_status_with_session(
        self, orchestrator: TDFlowOrchestrator, spec_file: Path
    ):
        """Get status returns session info."""
        orchestrator.start(spec_file)

        status = orchestrator.get_status()

        assert status["active"] is True, "Expected status['active'] is True"
        assert "session_id" in status, "Expected 'session_id' in status"
        assert status["current_phase"] == "init", "Expected status['current_phase'] to equal 'init'"
        assert len(status["components"]) == 1, "Expected len(status['components']) to equal 1"

    def test_run_red_no_session(self, temp_dir: Path):
        """Run red fails without session."""
        orchestrator = TDFlowOrchestrator(project_path=temp_dir)

        result = orchestrator.run_red()

        assert result.success is False, "Expected result.success is False"
        assert "No active session" in result.errors[0], "Expected 'No active session' in result.errors[0]"

    @patch("agentforge.core.tdflow.phases.red.RedPhaseExecutor.execute")
    @patch("agentforge.core.tdflow.runners.base.TestRunner.for_framework")
    def test_run_red_success(
        self,
        mock_runner: MagicMock,
        mock_execute: MagicMock,
        orchestrator: TDFlowOrchestrator,
        spec_file: Path,
        temp_dir: Path,
    ):
        """Run red executes phase successfully."""
        from agentforge.core.tdflow.domain import PhaseResult

        # Mock runner
        runner_instance = MagicMock()
        mock_runner.return_value = runner_instance

        # Mock phase execution
        mock_execute.return_value = PhaseResult(
            phase=TDFlowPhase.RED,
            success=True,
            component="TestService",
            artifacts={"tests": temp_dir / "tests" / "test_file.py"},
            test_result=RunResult(
                total=3, passed=0, failed=3, errors=0, duration_seconds=0.5, output=""
            ),
        )

        # Start session and run red
        orchestrator.start(spec_file)
        result = orchestrator.run_red()

        assert result.success is True, "Expected result.success is True"
        assert result.component == "TestService", "Expected result.component to equal 'TestService'"
        mock_execute.assert_called_once()

    def test_run_green_no_session(self, temp_dir: Path):
        """Run green fails without session."""
        orchestrator = TDFlowOrchestrator(project_path=temp_dir)

        result = orchestrator.run_green()

        assert result.success is False, "Expected result.success is False"
        assert "No active session" in result.errors[0], "Expected 'No active session' in result.errors[0]"

    def test_run_green_no_red_component(
        self, orchestrator: TDFlowOrchestrator, spec_file: Path
    ):
        """Run green fails without RED component."""
        orchestrator.start(spec_file)

        result = orchestrator.run_green()

        assert result.success is False, "Expected result.success is False"
        assert "RED state" in result.errors[0], "Expected 'RED state' in result.errors[0]"

    def test_resume_loads_session(
        self, orchestrator: TDFlowOrchestrator, spec_file: Path
    ):
        """Resume loads the latest session."""
        # Start and modify session
        orchestrator.start(spec_file)
        session_id = orchestrator.session.session_id

        # Create new orchestrator and resume
        new_orchestrator = TDFlowOrchestrator(
            project_path=orchestrator.project_path
        )
        new_orchestrator.resume()

        assert new_orchestrator.session is not None, "Expected new_orchestrator.session is not None"
        assert new_orchestrator.session.session_id == session_id, "Expected new_orchestrator.session.se... to equal session_id"


class TestOrchestratorComponentSelection:
    """Tests for component selection logic."""

    @pytest.fixture
    def session_with_components(self) -> TDFlowSession:
        """Create a session with multiple components in different states."""
        return TDFlowSession(
            session_id="test",
            started_at=datetime.utcnow(),
            spec_file=Path("test.yaml"),
            spec_hash="abc123",
            components=[
                ComponentProgress(name="Pending1", status=ComponentStatus.PENDING),
                ComponentProgress(name="Red1", status=ComponentStatus.RED),
                ComponentProgress(name="Green1", status=ComponentStatus.GREEN),
                ComponentProgress(name="Pending2", status=ComponentStatus.PENDING),
            ],
        )

    def test_get_component_by_name(self, session_with_components: TDFlowSession):
        """Get component by specific name."""
        comp = session_with_components.get_component("Red1")

        assert comp is not None, "Expected comp is not None"
        assert comp.name == "Red1", "Expected comp.name to equal 'Red1'"
        assert comp.status == ComponentStatus.RED, "Expected comp.status to equal ComponentStatus.RED"

    def test_get_next_pending(self, session_with_components: TDFlowSession):
        """Get next pending returns first pending."""
        comp = session_with_components.get_next_pending()

        assert comp is not None, "Expected comp is not None"
        assert comp.name == "Pending1", "Expected comp.name to equal 'Pending1'"

    def test_get_current_component(self, session_with_components: TDFlowSession):
        """Get current component respects current_component field."""
        session_with_components.current_component = "Green1"

        comp = session_with_components.get_current_component()

        assert comp is not None, "Expected comp is not None"
        assert comp.name == "Green1", "Expected comp.name to equal 'Green1'"
