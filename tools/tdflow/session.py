"""
Session Management
==================

Create, load, save, and manage TDFLOW sessions.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from tools.tdflow.domain import (
    ComponentProgress,
    ComponentStatus,
    SessionHistory,
    TDFlowPhase,
    TDFlowSession,
    TestFile,
    ImplementationFile,
)


class SessionManager:
    """
    Manages TDFLOW session lifecycle.

    Sessions are persisted to .agentforge/tdflow/ directory and can be
    resumed after interruption.
    """

    SESSIONS_DIR = Path(".agentforge/tdflow")

    def __init__(self, root_path: Optional[Path] = None):
        """
        Initialize session manager.

        Args:
            root_path: Root path for session storage. Defaults to current directory.
        """
        self.root_path = root_path or Path.cwd()
        self.sessions_dir = self.root_path / self.SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        spec_file: Path,
        test_framework: str = "xunit",
        coverage_threshold: float = 80.0,
    ) -> TDFlowSession:
        """
        Create a new TDFLOW session from a specification.

        Args:
            spec_file: Path to specification.yaml file
            test_framework: Test framework to use (xunit, nunit, pytest)
            coverage_threshold: Required coverage percentage

        Returns:
            New TDFlowSession instance
        """
        session_id = f"tdflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        # Load and hash spec
        spec_content = spec_file.read_text()
        spec_hash = hashlib.sha256(spec_content.encode()).hexdigest()[:16]

        # Parse components from spec
        spec_data = yaml.safe_load(spec_content)
        components = self._extract_components(spec_data)

        session = TDFlowSession(
            session_id=session_id,
            started_at=datetime.utcnow(),
            spec_file=spec_file,
            spec_hash=spec_hash,
            test_framework=test_framework,
            coverage_threshold=coverage_threshold,
            components=components,
            current_phase=TDFlowPhase.INIT,
        )

        session.add_history("session_created")
        self.save(session)

        return session

    def _extract_components(self, spec_data: Dict[str, Any]) -> List[ComponentProgress]:
        """
        Extract components from specification.

        Args:
            spec_data: Parsed specification data

        Returns:
            List of ComponentProgress instances
        """
        components = []

        for comp in spec_data.get("components", []):
            components.append(
                ComponentProgress(
                    name=comp.get("name", "Unknown"),
                    status=ComponentStatus.PENDING,
                )
            )

        return components

    def load(self, session_id: str) -> Optional[TDFlowSession]:
        """
        Load a session from disk.

        Args:
            session_id: Session identifier

        Returns:
            TDFlowSession or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.yaml"

        if not session_file.exists():
            return None

        with open(session_file) as f:
            data = yaml.safe_load(f)

        return self._deserialize(data)

    def save(self, session: TDFlowSession) -> Path:
        """
        Save session to disk.

        Args:
            session: Session to save

        Returns:
            Path to saved session file
        """
        session_file = self.sessions_dir / f"{session.session_id}.yaml"

        with open(session_file, "w") as f:
            yaml.dump(self._serialize(session), f, default_flow_style=False)

        return session_file

    def get_latest(self) -> Optional[TDFlowSession]:
        """
        Get the most recent session.

        Returns:
            Most recent TDFlowSession or None
        """
        sessions = sorted(self.sessions_dir.glob("tdflow_*.yaml"), reverse=True)
        if sessions:
            return self.load(sessions[0].stem)
        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions with summary info.

        Returns:
            List of session summaries
        """
        summaries = []
        for session_file in sorted(self.sessions_dir.glob("tdflow_*.yaml"), reverse=True):
            with open(session_file) as f:
                data = yaml.safe_load(f)
            summaries.append(
                {
                    "session_id": data.get("session_id"),
                    "started_at": data.get("started_at"),
                    "spec_file": data.get("spec_file"),
                    "current_phase": data.get("current_phase"),
                    "component_count": len(data.get("components", [])),
                }
            )
        return summaries

    def _serialize(self, session: TDFlowSession) -> Dict[str, Any]:
        """
        Serialize session to dict for YAML.

        Args:
            session: Session to serialize

        Returns:
            Dictionary representation
        """
        return {
            "schema_version": "1.0",
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat(),
            "spec_file": str(session.spec_file),
            "spec_hash": session.spec_hash,
            "test_framework": session.test_framework,
            "coverage_threshold": session.coverage_threshold,
            "auto_refactor": session.auto_refactor,
            "current_phase": session.current_phase.value,
            "current_component": session.current_component,
            "components": [self._serialize_component(c) for c in session.components],
            "history": [self._serialize_history(h) for h in session.history],
        }

    def _serialize_component(self, comp: ComponentProgress) -> Dict[str, Any]:
        """Serialize a component to dict."""
        return {
            "name": comp.name,
            "status": comp.status.value,
            "tests_file": str(comp.tests.path) if comp.tests else None,
            "tests_framework": comp.tests.framework if comp.tests else None,
            "impl_file": str(comp.implementation.path) if comp.implementation else None,
            "coverage": comp.coverage,
            "conformance_clean": comp.conformance_clean,
            "errors": comp.errors,
        }

    def _serialize_history(self, hist: SessionHistory) -> Dict[str, Any]:
        """Serialize a history entry to dict."""
        return {
            "timestamp": hist.timestamp.isoformat(),
            "action": hist.action,
            "phase": hist.phase.value if hist.phase else None,
            "component": hist.component,
            "details": hist.details,
        }

    def _deserialize(self, data: Dict[str, Any]) -> TDFlowSession:
        """
        Deserialize dict to session.

        Args:
            data: Dictionary from YAML

        Returns:
            TDFlowSession instance
        """
        components = [
            self._deserialize_component(c) for c in data.get("components", [])
        ]

        history = [self._deserialize_history(h) for h in data.get("history", [])]

        return TDFlowSession(
            session_id=data["session_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            spec_file=Path(data["spec_file"]),
            spec_hash=data["spec_hash"],
            test_framework=data.get("test_framework", "xunit"),
            coverage_threshold=data.get("coverage_threshold", 80.0),
            auto_refactor=data.get("auto_refactor", False),
            current_phase=TDFlowPhase(data.get("current_phase", "init")),
            current_component=data.get("current_component"),
            components=components,
            history=history,
        )

    def _deserialize_component(self, data: Dict[str, Any]) -> ComponentProgress:
        """Deserialize a component from dict."""
        tests = None
        if data.get("tests_file"):
            tests = TestFile(
                path=Path(data["tests_file"]),
                content="",  # Content not stored in session
                framework=data.get("tests_framework", "xunit"),
            )

        implementation = None
        if data.get("impl_file"):
            implementation = ImplementationFile(
                path=Path(data["impl_file"]),
                content="",  # Content not stored in session
            )

        return ComponentProgress(
            name=data["name"],
            status=ComponentStatus(data.get("status", "pending")),
            tests=tests,
            implementation=implementation,
            coverage=data.get("coverage", 0.0),
            conformance_clean=data.get("conformance_clean", True),
            errors=data.get("errors", []),
        )

    def _deserialize_history(self, data: Dict[str, Any]) -> SessionHistory:
        """Deserialize a history entry from dict."""
        return SessionHistory(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=data["action"],
            phase=TDFlowPhase(data["phase"]) if data.get("phase") else None,
            component=data.get("component"),
            details=data.get("details"),
        )
