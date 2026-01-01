# @spec_file: .agentforge/specs/harness-v1.yaml
# @spec_id: harness-v1
# @component_id: tools-harness-auto_fix_daemon
# @test_path: tests/integration/harness/test_harness_workflow.py

"""
Auto-Fix Daemon
===============

Continuously monitors and fixes violations with configurable policies.
"""

import logging
import time
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .fix_violation_workflow import FixViolationWorkflow, FixPhase, FixAttempt
from .violation_tools import ViolationTools
from .llm_executor import LLMExecutor
from .tool_executor_bridge import ToolExecutorBridge


@dataclass
class AutoFixConfig:
    """Configuration for auto-fix daemon."""

    max_concurrent: int = 1
    max_attempts_per_violation: int = 3
    cooldown_after_failure: timedelta = field(default_factory=lambda: timedelta(hours=1))
    severity_order: List[str] = field(default_factory=lambda: ["blocker", "critical", "major", "minor"])
    require_approval: bool = True
    pause_on_test_failure: bool = True
    max_fixes_per_run: int = 10
    poll_interval: int = 60  # seconds between checks

    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "max_concurrent": self.max_concurrent,
            "max_attempts_per_violation": self.max_attempts_per_violation,
            "cooldown_after_failure_seconds": int(self.cooldown_after_failure.total_seconds()),
            "severity_order": self.severity_order,
            "require_approval": self.require_approval,
            "pause_on_test_failure": self.pause_on_test_failure,
            "max_fixes_per_run": self.max_fixes_per_run,
            "poll_interval": self.poll_interval,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AutoFixConfig":
        """Deserialize from dict."""
        return cls(
            max_concurrent=data.get("max_concurrent", 1),
            max_attempts_per_violation=data.get("max_attempts_per_violation", 3),
            cooldown_after_failure=timedelta(
                seconds=data.get("cooldown_after_failure_seconds", 3600)
            ),
            severity_order=data.get(
                "severity_order", ["blocker", "critical", "major", "minor"]
            ),
            require_approval=data.get("require_approval", True),
            pause_on_test_failure=data.get("pause_on_test_failure", True),
            max_fixes_per_run=data.get("max_fixes_per_run", 10),
            poll_interval=data.get("poll_interval", 60),
        )


@dataclass
class DaemonStatus:
    """Current status of the daemon."""

    state: str  # "idle", "running", "paused", "stopped"
    current_violation: Optional[str] = None
    fixes_completed: int = 0
    fixes_failed: int = 0
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "state": self.state,
            "current_violation": self.current_violation,
            "fixes_completed": self.fixes_completed,
            "fixes_failed": self.fixes_failed,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "error": self.error,
        }


class AutoFixDaemon:
    """
    Daemon that automatically fixes violations.
    """

    def __init__(
        self,
        project_path: Path,
        config: Optional[AutoFixConfig] = None,
    ):
        """
        Initialize the daemon.

        Args:
            project_path: Project root directory
            config: Configuration options
        """
        self.project_path = Path(project_path)
        self.config = config or AutoFixConfig()
        self.logger = logging.getLogger("auto_fix")

        # State
        self._status = DaemonStatus(state="idle")
        self._attempts: Dict[str, List[FixAttempt]] = {}
        self._running = False

        # Load previous attempt history
        self._load_attempt_history()

    def _load_attempt_history(self):
        """Load previous attempt history."""
        attempts_dir = self.project_path / ".agentforge" / "fix_attempts"
        if not attempts_dir.exists():
            return

        for f in attempts_dir.glob("V-*.yaml"):
            try:
                with open(f) as fp:
                    data = yaml.safe_load(fp)
                vid = data.get("violation_id")
                if vid:
                    if vid not in self._attempts:
                        self._attempts[vid] = []
                    attempt = FixAttempt.from_dict(data)
                    self._attempts[vid].append(attempt)
            except Exception as e:
                self.logger.warning(f"Failed to load attempt {f}: {e}")

    def should_attempt_fix(self, violation_id: str) -> tuple:
        """
        Check if we should attempt to fix this violation.

        Returns:
            Tuple of (should_attempt, reason)
        """
        attempts = self._attempts.get(violation_id, [])

        # Check attempt count
        if len(attempts) >= self.config.max_attempts_per_violation:
            return False, f"Max attempts ({self.config.max_attempts_per_violation}) reached"

        # Check cooldown after failure
        if attempts:
            last = attempts[-1]
            if last.phase == FixPhase.FAILED and last.completed_at:
                cooldown_until = last.completed_at + self.config.cooldown_after_failure
                if datetime.utcnow() < cooldown_until:
                    return False, f"In cooldown until {cooldown_until}"

        return True, "OK"

    def get_next_violation(self) -> Optional[str]:
        """Get next violation to fix based on priority."""
        tools = ViolationTools(self.project_path)

        for severity in self.config.severity_order:
            result = tools.list_violations(
                "list_violations", {"status": "open", "severity": severity, "limit": 10}
            )

            if not result.success:
                continue

            # Parse violation IDs from output
            for line in result.output.split("\n"):
                line = line.strip()
                if line.startswith("V-"):
                    vid = line.split()[0]
                    should, reason = self.should_attempt_fix(vid)
                    if should:
                        return vid

        return None

    def get_status(self) -> DaemonStatus:
        """Get current daemon status."""
        return self._status

    def run_once(self) -> Optional[FixAttempt]:
        """
        Run one fix cycle.

        Returns:
            FixAttempt if a fix was attempted, None if nothing to do
        """
        violation_id = self.get_next_violation()
        if not violation_id:
            self.logger.info("No violations to fix")
            return None

        self.logger.info(f"Attempting to fix: {violation_id}")
        self._status.current_violation = violation_id
        self._status.state = "running"

        try:
            # Create executor and workflow
            tool_bridge = ToolExecutorBridge(self.project_path)
            llm_executor = LLMExecutor(
                tool_executors=tool_bridge.get_default_executors()
            )

            workflow = FixViolationWorkflow(
                project_path=self.project_path,
                llm_executor=llm_executor,
                require_commit_approval=self.config.require_approval,
            )

            # Run fix
            attempt = workflow.fix_violation(violation_id)

            # Track attempt
            if violation_id not in self._attempts:
                self._attempts[violation_id] = []
            self._attempts[violation_id].append(attempt)

            # Save attempt log
            self._save_attempt(attempt)

            # Update status
            if attempt.phase == FixPhase.COMPLETE:
                self.logger.info(f"Successfully fixed: {violation_id}")
                self._status.fixes_completed += 1
            else:
                self.logger.warning(f"Failed to fix {violation_id}: {attempt.error}")
                self._status.fixes_failed += 1

            return attempt

        except Exception as e:
            self.logger.error(f"Error fixing {violation_id}: {e}")
            self._status.error = str(e)
            self._status.fixes_failed += 1
            return None

        finally:
            self._status.current_violation = None
            self._status.last_run = datetime.utcnow()

    def _save_attempt(self, attempt: FixAttempt):
        """Save attempt to log file."""
        attempts_dir = self.project_path / ".agentforge" / "fix_attempts"
        attempts_dir.mkdir(parents=True, exist_ok=True)

        log_file = (
            attempts_dir
            / f"{attempt.violation_id}_{attempt.started_at.strftime('%Y%m%d_%H%M%S')}.yaml"
        )

        with open(log_file, "w") as f:
            yaml.dump(attempt.to_dict(), f, default_flow_style=False)

    def run_batch(self, max_fixes: Optional[int] = None) -> List[FixAttempt]:
        """
        Run multiple fix cycles.

        Args:
            max_fixes: Max fixes to attempt (default: from config)

        Returns:
            List of fix attempts
        """
        max_fixes = max_fixes or self.config.max_fixes_per_run
        attempts = []

        for i in range(max_fixes):
            attempt = self.run_once()
            if attempt is None:
                break
            attempts.append(attempt)

            # Pause if configured and test failed
            if (
                self.config.pause_on_test_failure
                and attempt.phase == FixPhase.FAILED
                and "test" in str(attempt.error).lower()
            ):
                self.logger.warning("Pausing due to test failure")
                self._status.state = "paused"
                self._status.error = "Paused due to test failure"
                break

        self._status.state = "idle"
        return attempts

    def run_continuous(self, duration: Optional[int] = None):
        """
        Run continuously until stopped.

        Args:
            duration: Optional maximum duration in seconds
        """
        self._running = True
        self._status.state = "running"
        start_time = time.time()

        try:
            while self._running:
                # Check duration limit
                if duration and (time.time() - start_time) > duration:
                    self.logger.info(f"Duration limit ({duration}s) reached")
                    break

                # Run one fix cycle
                self.run_once()

                # Wait before next check
                self._status.next_run = datetime.utcnow() + timedelta(
                    seconds=self.config.poll_interval
                )
                time.sleep(self.config.poll_interval)

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        finally:
            self._running = False
            self._status.state = "stopped"

    def stop(self):
        """Stop the daemon if running continuously."""
        self._running = False
        self._status.state = "stopping"


def create_auto_fix_daemon(
    project_path: Path,
    config_file: Optional[Path] = None,
) -> AutoFixDaemon:
    """
    Factory function to create an AutoFixDaemon.

    Args:
        project_path: Project root directory
        config_file: Optional path to config YAML file

    Returns:
        Configured AutoFixDaemon
    """
    config = AutoFixConfig()

    if config_file and config_file.exists():
        with open(config_file) as f:
            data = yaml.safe_load(f)
        config = AutoFixConfig.from_dict(data)

    return AutoFixDaemon(project_path=project_path, config=config)
