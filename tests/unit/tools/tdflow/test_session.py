# @spec_file: .agentforge/specs/core-tdflow-v1.yaml
# @spec_id: core-tdflow-v1
# @component_id: tools-tdflow-session
# @impl_path: tools/tdflow/session.py

"""Tests for TDFLOW session management."""

import tempfile
from pathlib import Path

import pytest

from agentforge.core.tdflow.domain import (
    ComponentStatus,
    TDFlowPhase,
)
from agentforge.core.tdflow.session import SessionManager


class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
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
    methods:
      - name: DoSomething
        returns: Result<string>
  - name: OtherService
    methods:
      - name: Process
        returns: void
"""
        )
        return spec_path

    @pytest.fixture
    def manager(self, temp_dir: Path) -> SessionManager:
        """Create a session manager for tests."""
        return SessionManager(root_path=temp_dir)

    def test_create_session(self, manager: SessionManager, spec_file: Path):
        """Create session initializes correctly."""
        session = manager.create(spec_file, test_framework="pytest")

        assert session.session_id.startswith("tdflow_"), "Expected session.session_id.startswith() to be truthy"
        assert session.spec_file == spec_file, "Expected session.spec_file to equal spec_file"
        assert session.test_framework == "pytest", "Expected session.test_framework to equal 'pytest'"
        assert len(session.components) == 2, "Expected len(session.components) to equal 2"
        assert session.components[0].name == "TestService", "Expected session.components[0].name to equal 'TestService'"
        assert session.components[1].name == "OtherService", "Expected session.components[1].name to equal 'OtherService'"
        assert session.current_phase == TDFlowPhase.INIT, "Expected session.current_phase to equal TDFlowPhase.INIT"

    def test_save_and_load_session(self, manager: SessionManager, spec_file: Path):
        """Session can be saved and loaded."""
        # Create and save
        original = manager.create(spec_file)
        original.components[0].status = ComponentStatus.RED
        original.current_phase = TDFlowPhase.RED
        original.add_history("test_action")
        manager.save(original)

        # Load
        loaded = manager.load(original.session_id)

        assert loaded is not None, "Expected loaded is not None"
        assert loaded.session_id == original.session_id, "Expected loaded.session_id to equal original.session_id"
        assert loaded.spec_file == original.spec_file, "Expected loaded.spec_file to equal original.spec_file"
        assert loaded.current_phase == TDFlowPhase.RED, "Expected loaded.current_phase to equal TDFlowPhase.RED"
        assert loaded.components[0].status == ComponentStatus.RED, "Expected loaded.components[0].status to equal ComponentStatus.RED"
        assert len(loaded.history) == len(original.history), "Expected len(loaded.history) to equal len(original.history)"

    def test_load_nonexistent_session(self, manager: SessionManager):
        """Loading nonexistent session returns None."""
        result = manager.load("nonexistent_session")
        assert result is None, "Expected result is None"

    def test_get_latest(self, manager: SessionManager, spec_file: Path):
        """Get latest returns most recent session."""
        # Create multiple sessions
        manager.create(spec_file)
        latest = manager.create(spec_file)

        result = manager.get_latest()

        assert result is not None, "Expected result is not None"
        assert result.session_id == latest.session_id, "Expected result.session_id to equal latest.session_id"

    def test_get_latest_no_sessions(self, manager: SessionManager):
        """Get latest returns None when no sessions."""
        result = manager.get_latest()
        assert result is None, "Expected result is None"

    def test_list_sessions(self, manager: SessionManager, spec_file: Path):
        """List sessions returns all session summaries."""
        import time

        manager.create(spec_file)
        time.sleep(0.01)  # Ensure unique timestamps
        manager.create(spec_file)

        sessions = manager.list_sessions()

        assert len(sessions) == 2, "Expected len(sessions) to equal 2"
        for sess in sessions:
            assert "session_id" in sess, "Expected 'session_id' in sess"
            assert "started_at" in sess, "Expected 'started_at' in sess"
            assert "spec_file" in sess, "Expected 'spec_file' in sess"
            assert "current_phase" in sess, "Expected 'current_phase' in sess"

    def test_session_serialization_with_artifacts(
        self, manager: SessionManager, spec_file: Path, temp_dir: Path
    ):
        """Session with artifacts serializes correctly."""
        from agentforge.core.tdflow.domain import ImplementationFile, TestFile

        session = manager.create(spec_file)

        # Add test file artifact
        session.components[0].tests = TestFile(
            path=temp_dir / "tests" / "test_file.py",
            content="test content",
            framework="pytest",
        )

        # Add implementation artifact
        session.components[0].implementation = ImplementationFile(
            path=temp_dir / "src" / "service.py",
            content="impl content",
        )

        session.components[0].status = ComponentStatus.GREEN
        session.components[0].coverage = 85.5

        manager.save(session)
        loaded = manager.load(session.session_id)

        assert loaded.components[0].tests is not None, "Expected loaded.components[0].tests is not None"
        assert loaded.components[0].implementation is not None, "Expected loaded.components[0].implem... is not None"
        assert loaded.components[0].status == ComponentStatus.GREEN, "Expected loaded.components[0].status to equal ComponentStatus.GREEN"
        assert loaded.components[0].coverage == 85.5, "Expected loaded.components[0].coverage to equal 85.5"
