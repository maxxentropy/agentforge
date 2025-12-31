# Implementation Task: Chunk 6 - TDFLOW Workflow

## Overview

Implement the Test-Driven Flow (TDFLOW) workflow as specified in the specification document. This system consumes specifications from the SPEC workflow and produces tested implementations.

**Read the full specification first:** `chunk6_tdflow_specification.md`  
**Read design decisions:** `chunk6_tdflow_design_decisions.md`

---

## Architecture Summary

```
tools/tdflow/
├── __init__.py                 # Public exports
├── domain.py                   # Domain entities
├── session.py                  # Session management
├── orchestrator.py             # Main TDFLOW orchestrator
├── spec_loader.py              # Load and parse specifications
├── runners/
│   ├── __init__.py
│   ├── base.py                 # TestRunner ABC
│   ├── dotnet.py               # DotNet test runner
│   └── pytest.py               # Pytest runner
├── phases/
│   ├── __init__.py
│   ├── red.py                  # RED phase executor
│   ├── green.py                # GREEN phase executor
│   ├── refactor.py             # REFACTOR phase executor
│   └── verify.py               # VERIFY phase executor

cli/click_commands/tdflow.py    # CLI commands

contracts/
├── tdflow.red.v1.yaml          # RED phase prompt contract
├── tdflow.green.v1.yaml        # GREEN phase prompt contract
└── tdflow.refactor.v1.yaml     # REFACTOR phase prompt contract

Output:
.agentforge/tdflow/
├── session_{id}.yaml           # Session state
└── reports/
    └── verification_{id}.yaml  # Verification reports
```

---

## Phase 1: Domain Model

### 1.1 `tools/tdflow/domain.py`

```python
"""
TDFLOW Domain Model
===================

Domain entities for the Test-Driven Flow workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class TDFlowPhase(Enum):
    """Phases in the TDFLOW workflow."""
    INIT = "init"
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    VERIFY = "verify"
    DONE = "done"


class ComponentStatus(Enum):
    """Status of a component in TDFLOW."""
    PENDING = "pending"
    RED = "red"           # Tests generated, failing
    GREEN = "green"       # Implementation passes tests
    REFACTORED = "refactored"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class TestCase:
    """A generated test case."""
    name: str
    method_under_test: str
    scenario: str
    expected_result: str
    status: str = "pending"  # pending | pass | fail | error


@dataclass
class TestFile:
    """A generated test file."""
    path: Path
    content: str
    test_cases: List[TestCase] = field(default_factory=list)
    framework: str = "xunit"  # xunit | nunit | pytest | jest


@dataclass
class ImplementationFile:
    """A generated implementation file."""
    path: Path
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    coverage: float = 0.0


@dataclass
class ComponentProgress:
    """Progress tracking for a single component."""
    name: str
    status: ComponentStatus = ComponentStatus.PENDING
    tests: Optional[TestFile] = None
    implementation: Optional[ImplementationFile] = None
    coverage: float = 0.0
    conformance_clean: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of running tests."""
    total: int
    passed: int
    failed: int
    errors: int
    duration_seconds: float
    output: str
    coverage: Optional[float] = None
    
    @property
    def all_passed(self) -> bool:
        return self.passed == self.total and self.errors == 0
    
    @property
    def all_failed(self) -> bool:
        return self.failed == self.total or self.passed == 0


@dataclass
class PhaseResult:
    """Result of executing a phase."""
    phase: TDFlowPhase
    success: bool
    component: str
    artifacts: Dict[str, Path] = field(default_factory=dict)
    test_result: Optional[TestResult] = None
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class VerificationReport:
    """Final verification report for a component."""
    component: str
    tests_passing: int
    tests_total: int
    coverage: float
    conformance_violations: int
    traceability: List[Dict[str, str]] = field(default_factory=list)
    verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "tests": {
                "passing": self.tests_passing,
                "total": self.tests_total,
            },
            "coverage": round(self.coverage, 2),
            "conformance_violations": self.conformance_violations,
            "traceability": self.traceability,
            "verified": self.verified,
        }


@dataclass 
class SessionHistory:
    """A history entry in the session."""
    timestamp: datetime
    action: str
    phase: Optional[TDFlowPhase] = None
    component: Optional[str] = None
    details: Optional[str] = None


@dataclass
class TDFlowSession:
    """
    TDFLOW session state.
    
    Persisted to disk to allow resume after interruption.
    """
    session_id: str
    started_at: datetime
    spec_file: Path
    spec_hash: str
    
    # Configuration
    test_framework: str = "xunit"
    coverage_threshold: float = 80.0
    auto_refactor: bool = False
    
    # Progress
    components: List[ComponentProgress] = field(default_factory=list)
    current_phase: TDFlowPhase = TDFlowPhase.INIT
    current_component: Optional[str] = None
    
    # History
    history: List[SessionHistory] = field(default_factory=list)
    
    def get_component(self, name: str) -> Optional[ComponentProgress]:
        """Get component by name."""
        for comp in self.components:
            if comp.name == name:
                return comp
        return None
    
    def get_next_pending(self) -> Optional[ComponentProgress]:
        """Get next component to process."""
        for comp in self.components:
            if comp.status == ComponentStatus.PENDING:
                return comp
        return None
    
    def all_verified(self) -> bool:
        """Check if all components are verified."""
        return all(c.status == ComponentStatus.VERIFIED for c in self.components)
    
    def add_history(self, action: str, phase: TDFlowPhase = None, 
                   component: str = None, details: str = None):
        """Add history entry."""
        self.history.append(SessionHistory(
            timestamp=datetime.utcnow(),
            action=action,
            phase=phase,
            component=component,
            details=details,
        ))
```

---

## Phase 2: Test Runners

### 2.1 `tools/tdflow/runners/base.py`

```python
"""
Test Runner Base
================

Abstract base class for test runners.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ..domain import TestResult


class TestRunner(ABC):
    """
    Abstract test runner interface.
    
    Implementations handle specific frameworks (dotnet, pytest, etc.)
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    @abstractmethod
    def run_tests(self, filter_pattern: Optional[str] = None) -> TestResult:
        """
        Run tests and return results.
        
        Args:
            filter_pattern: Optional filter to run specific tests
            
        Returns:
            TestResult with pass/fail counts
        """
        pass
    
    @abstractmethod
    def get_coverage(self) -> float:
        """Get test coverage percentage."""
        pass
    
    @abstractmethod
    def discover_tests(self) -> List[str]:
        """Discover available tests."""
        pass
    
    @classmethod
    def detect(cls, project_path: Path) -> "TestRunner":
        """
        Detect appropriate runner for project.
        
        Examines project files to determine framework.
        """
        from .dotnet import DotNetTestRunner
        from .pytest_runner import PytestRunner
        
        # Check for .NET
        if list(project_path.glob("**/*.csproj")):
            return DotNetTestRunner(project_path)
        
        # Check for Python
        if (project_path / "pyproject.toml").exists():
            return PytestRunner(project_path)
        if (project_path / "pytest.ini").exists():
            return PytestRunner(project_path)
        if list(project_path.glob("**/test_*.py")):
            return PytestRunner(project_path)
        
        raise ValueError(f"Cannot detect test framework for {project_path}")
```

### 2.2 `tools/tdflow/runners/dotnet.py`

```python
"""
DotNet Test Runner
==================

Runs tests via 'dotnet test'.
"""

import subprocess
import re
from pathlib import Path
from typing import List, Optional

from .base import TestRunner
from ..domain import TestResult


class DotNetTestRunner(TestRunner):
    """Test runner for .NET projects using dotnet test."""
    
    def run_tests(self, filter_pattern: Optional[str] = None) -> TestResult:
        """Run dotnet test and parse results."""
        cmd = ["dotnet", "test", str(self.project_path), "--no-build"]
        
        if filter_pattern:
            cmd.extend(["--filter", filter_pattern])
        
        # Add coverage collection
        cmd.extend(["--collect:XPlat Code Coverage"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )
        
        return self._parse_output(result.stdout + result.stderr, result.returncode)
    
    def _parse_output(self, output: str, returncode: int) -> TestResult:
        """Parse dotnet test output."""
        # Parse: "Passed: X, Failed: Y, Skipped: Z, Total: N"
        total = passed = failed = 0
        
        match = re.search(r"Passed:\s*(\d+)", output)
        if match:
            passed = int(match.group(1))
            
        match = re.search(r"Failed:\s*(\d+)", output)
        if match:
            failed = int(match.group(1))
            
        match = re.search(r"Total:\s*(\d+)", output)
        if match:
            total = int(match.group(1))
        
        return TestResult(
            total=total,
            passed=passed,
            failed=failed,
            errors=0 if returncode == 0 or failed > 0 else 1,
            duration_seconds=0.0,  # Parse from output if needed
            output=output,
        )
    
    def get_coverage(self) -> float:
        """Get coverage from last run."""
        # Parse coverage.cobertura.xml
        # Implementation depends on coverage format
        return 0.0
    
    def discover_tests(self) -> List[str]:
        """Discover tests via dotnet test --list-tests."""
        cmd = ["dotnet", "test", str(self.project_path), "--list-tests"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        tests = []
        for line in result.stdout.split("\n"):
            if line.strip() and not line.startswith(" "):
                tests.append(line.strip())
        
        return tests
```

### 2.3 `tools/tdflow/runners/pytest_runner.py`

```python
"""
Pytest Runner
=============

Runs tests via pytest.
"""

import subprocess
import json
from pathlib import Path
from typing import List, Optional

from .base import TestRunner
from ..domain import TestResult


class PytestRunner(TestRunner):
    """Test runner for Python projects using pytest."""
    
    def run_tests(self, filter_pattern: Optional[str] = None) -> TestResult:
        """Run pytest and parse results."""
        cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
        
        if filter_pattern:
            cmd.extend(["-k", filter_pattern])
        
        # JSON output for parsing
        cmd.extend(["--json-report", "--json-report-file=.pytest_report.json"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )
        
        return self._parse_output(result.stdout, result.returncode)
    
    def _parse_output(self, output: str, returncode: int) -> TestResult:
        """Parse pytest output."""
        # Try JSON report first
        report_path = self.project_path / ".pytest_report.json"
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)
            
            summary = report.get("summary", {})
            return TestResult(
                total=summary.get("total", 0),
                passed=summary.get("passed", 0),
                failed=summary.get("failed", 0),
                errors=summary.get("error", 0),
                duration_seconds=report.get("duration", 0.0),
                output=output,
            )
        
        # Fall back to parsing output
        # "X passed, Y failed in Z seconds"
        total = passed = failed = 0
        # ... parse logic
        
        return TestResult(
            total=total,
            passed=passed,
            failed=failed,
            errors=0,
            duration_seconds=0.0,
            output=output,
        )
    
    def get_coverage(self) -> float:
        """Run with coverage and return percentage."""
        cmd = ["python", "-m", "pytest", "--cov", "--cov-report=json"]
        subprocess.run(cmd, cwd=self.project_path)
        
        cov_path = self.project_path / "coverage.json"
        if cov_path.exists():
            with open(cov_path) as f:
                data = json.load(f)
            return data.get("totals", {}).get("percent_covered", 0.0)
        
        return 0.0
    
    def discover_tests(self) -> List[str]:
        """Discover tests via pytest --collect-only."""
        cmd = ["python", "-m", "pytest", "--collect-only", "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_path)
        
        return [line.strip() for line in result.stdout.split("\n") if line.strip()]
```

---

## Phase 3: Session Management

### 3.1 `tools/tdflow/session.py`

```python
"""
Session Management
==================

Create, load, save, and manage TDFLOW sessions.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml

from .domain import TDFlowSession, TDFlowPhase, ComponentProgress, ComponentStatus


class SessionManager:
    """
    Manages TDFLOW session lifecycle.
    """
    
    SESSIONS_DIR = Path(".agentforge/tdflow")
    
    def __init__(self):
        self.sessions_dir = self.SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def create(self, spec_file: Path, test_framework: str = "xunit") -> TDFlowSession:
        """Create a new TDFLOW session from a specification."""
        session_id = f"tdflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Load and hash spec
        with open(spec_file) as f:
            spec_content = f.read()
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
            components=components,
            current_phase=TDFlowPhase.INIT,
        )
        
        session.add_history("session_created")
        self.save(session)
        
        return session
    
    def _extract_components(self, spec_data: dict) -> list:
        """Extract components from specification."""
        components = []
        
        for comp in spec_data.get("components", []):
            components.append(ComponentProgress(
                name=comp.get("name", "Unknown"),
                status=ComponentStatus.PENDING,
            ))
        
        return components
    
    def load(self, session_id: str) -> Optional[TDFlowSession]:
        """Load a session from disk."""
        session_file = self.sessions_dir / f"{session_id}.yaml"
        
        if not session_file.exists():
            return None
        
        with open(session_file) as f:
            data = yaml.safe_load(f)
        
        return self._deserialize(data)
    
    def save(self, session: TDFlowSession) -> Path:
        """Save session to disk."""
        session_file = self.sessions_dir / f"{session.session_id}.yaml"
        
        with open(session_file, 'w') as f:
            yaml.dump(self._serialize(session), f, default_flow_style=False)
        
        return session_file
    
    def get_latest(self) -> Optional[TDFlowSession]:
        """Get the most recent session."""
        sessions = sorted(self.sessions_dir.glob("tdflow_*.yaml"), reverse=True)
        if sessions:
            return self.load(sessions[0].stem)
        return None
    
    def _serialize(self, session: TDFlowSession) -> dict:
        """Serialize session to dict for YAML."""
        return {
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat(),
            "spec_file": str(session.spec_file),
            "spec_hash": session.spec_hash,
            "test_framework": session.test_framework,
            "coverage_threshold": session.coverage_threshold,
            "current_phase": session.current_phase.value,
            "current_component": session.current_component,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "tests_file": str(c.tests.path) if c.tests else None,
                    "impl_file": str(c.implementation.path) if c.implementation else None,
                    "coverage": c.coverage,
                }
                for c in session.components
            ],
            "history": [
                {
                    "timestamp": h.timestamp.isoformat(),
                    "action": h.action,
                    "phase": h.phase.value if h.phase else None,
                    "component": h.component,
                }
                for h in session.history
            ],
        }
    
    def _deserialize(self, data: dict) -> TDFlowSession:
        """Deserialize dict to session."""
        # Implementation mirrors _serialize
        pass
```

---

## Phase 4: Phase Executors

### 4.1 `tools/tdflow/phases/red.py`

```python
"""
RED Phase Executor
==================

Generates failing tests from specification.
"""

from pathlib import Path
from typing import Optional

from ..domain import (
    TDFlowSession, ComponentProgress, TestFile, TestCase,
    PhaseResult, TDFlowPhase, ComponentStatus
)
from ..runners.base import TestRunner


class RedPhaseExecutor:
    """
    Executes the RED phase: generate failing tests.
    
    Steps:
    1. Load component spec
    2. Generate test file via LLM
    3. Write test file
    4. Run tests
    5. Verify tests FAIL
    """
    
    def __init__(self, session: TDFlowSession, runner: TestRunner):
        self.session = session
        self.runner = runner
    
    def execute(self, component: ComponentProgress) -> PhaseResult:
        """Execute RED phase for a component."""
        errors = []
        
        # 1. Generate tests via LLM (uses prompt contract)
        test_content = self._generate_tests(component)
        if not test_content:
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component.name,
                errors=["Failed to generate tests"],
            )
        
        # 2. Write test file
        test_path = self._get_test_path(component)
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(test_content)
        
        # 3. Run tests
        result = self.runner.run_tests(filter_pattern=f"*{component.name}*")
        
        # 4. Verify tests FAIL (this is RED phase)
        if result.all_passed:
            errors.append("Tests passed in RED phase - tests may be trivial")
            return PhaseResult(
                phase=TDFlowPhase.RED,
                success=False,
                component=component.name,
                test_result=result,
                errors=errors,
            )
        
        # 5. Update component
        component.status = ComponentStatus.RED
        component.tests = TestFile(
            path=test_path,
            content=test_content,
            framework=self.session.test_framework,
        )
        
        return PhaseResult(
            phase=TDFlowPhase.RED,
            success=True,
            component=component.name,
            artifacts={"tests": test_path},
            test_result=result,
        )
    
    def _generate_tests(self, component: ComponentProgress) -> Optional[str]:
        """
        Generate test content via LLM.
        
        Uses tdflow.red.v1 prompt contract.
        """
        # Load spec for this component
        # Build prompt with contract
        # Call LLM
        # Parse response
        # Return test file content
        pass
    
    def _get_test_path(self, component: ComponentProgress) -> Path:
        """Determine test file path based on framework."""
        if self.session.test_framework in ("xunit", "nunit"):
            return Path(f"tests/Unit/{component.name}Tests.cs")
        else:
            return Path(f"tests/test_{component.name.lower()}.py")
```

### 4.2 `tools/tdflow/phases/green.py`

```python
"""
GREEN Phase Executor
====================

Generates implementation to pass failing tests.
"""

from pathlib import Path
from typing import Optional

from ..domain import (
    TDFlowSession, ComponentProgress, ImplementationFile,
    PhaseResult, TDFlowPhase, ComponentStatus
)
from ..runners.base import TestRunner


class GreenPhaseExecutor:
    """
    Executes the GREEN phase: generate implementation.
    
    Steps:
    1. Load failing tests
    2. Load spec requirements
    3. Gather context (similar code, patterns)
    4. Generate implementation via LLM
    5. Write implementation file
    6. Run tests
    7. Verify tests PASS
    """
    
    def __init__(self, session: TDFlowSession, runner: TestRunner):
        self.session = session
        self.runner = runner
    
    def execute(self, component: ComponentProgress) -> PhaseResult:
        """Execute GREEN phase for a component."""
        
        # 1. Get failing tests
        if not component.tests:
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component=component.name,
                errors=["No tests found - run RED phase first"],
            )
        
        # 2. Generate implementation via LLM
        impl_content = self._generate_implementation(component)
        if not impl_content:
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component=component.name,
                errors=["Failed to generate implementation"],
            )
        
        # 3. Write implementation
        impl_path = self._get_impl_path(component)
        impl_path.parent.mkdir(parents=True, exist_ok=True)
        impl_path.write_text(impl_content)
        
        # 4. Run tests
        result = self.runner.run_tests(filter_pattern=f"*{component.name}*")
        
        # 5. Verify tests PASS
        if not result.all_passed:
            # May need iteration - return partial success
            return PhaseResult(
                phase=TDFlowPhase.GREEN,
                success=False,
                component=component.name,
                test_result=result,
                errors=[f"Tests still failing: {result.failed}/{result.total}"],
            )
        
        # 6. Update component
        component.status = ComponentStatus.GREEN
        component.implementation = ImplementationFile(
            path=impl_path,
            content=impl_content,
        )
        component.coverage = self.runner.get_coverage()
        
        return PhaseResult(
            phase=TDFlowPhase.GREEN,
            success=True,
            component=component.name,
            artifacts={"implementation": impl_path},
            test_result=result,
        )
    
    def _generate_implementation(self, component: ComponentProgress) -> Optional[str]:
        """
        Generate implementation via LLM.
        
        Uses tdflow.green.v1 prompt contract.
        Context includes:
        - Failing tests
        - Spec requirements  
        - Similar code from codebase
        - Detected patterns
        """
        pass
    
    def _get_impl_path(self, component: ComponentProgress) -> Path:
        """Determine implementation file path."""
        # Use spec to determine layer/namespace
        if self.session.test_framework in ("xunit", "nunit"):
            return Path(f"src/Application/{component.name}.cs")
        else:
            return Path(f"src/{component.name.lower()}.py")
```

---

## Phase 5: CLI Commands

### 5.1 `cli/click_commands/tdflow.py`

```python
"""
TDFLOW CLI Commands
===================

Commands for the Test-Driven Flow workflow.
"""

import click
from pathlib import Path

from tools.tdflow.orchestrator import TDFlowOrchestrator
from tools.tdflow.session import SessionManager


@click.group('tdflow', help='Test-Driven Flow workflow commands')
def tdflow():
    """Test-Driven Flow (TDFLOW) commands."""
    pass


@tdflow.command('start')
@click.option('--spec', '-s', type=click.Path(exists=True), required=True,
              help='Path to specification.yaml')
@click.option('--framework', '-f', type=click.Choice(['xunit', 'nunit', 'pytest']),
              default='xunit', help='Test framework')
def start(spec, framework):
    """Start a new TDFLOW session from specification."""
    manager = SessionManager()
    session = manager.create(Path(spec), test_framework=framework)
    
    click.echo(f"\nTDFLOW Session Started")
    click.echo(f"{'━' * 40}")
    click.echo(f"Session ID: {session.session_id}")
    click.echo(f"Spec: {spec}")
    click.echo(f"Components: {len(session.components)}")
    for comp in session.components:
        click.echo(f"  - {comp.name}")
    click.echo(f"\nRun 'agentforge tdflow red' to generate tests.")


@tdflow.command('red')
@click.option('--component', '-c', help='Specific component (default: next pending)')
def red(component):
    """Execute RED phase: generate failing tests."""
    orchestrator = TDFlowOrchestrator()
    
    try:
        result = orchestrator.run_red(component_name=component)
        
        if result.success:
            click.echo(f"\n✓ RED phase complete for {result.component}")
            click.echo(f"  Tests: {result.artifacts.get('tests')}")
            click.echo(f"  Status: {result.test_result.failed} failing (expected)")
            click.echo(f"\nRun 'agentforge tdflow green' to implement.")
        else:
            click.echo(f"\n✗ RED phase failed: {result.errors}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@tdflow.command('green')
@click.option('--component', '-c', help='Specific component')
def green(component):
    """Execute GREEN phase: generate implementation."""
    orchestrator = TDFlowOrchestrator()
    
    try:
        result = orchestrator.run_green(component_name=component)
        
        if result.success:
            click.echo(f"\n✓ GREEN phase complete for {result.component}")
            click.echo(f"  Implementation: {result.artifacts.get('implementation')}")
            click.echo(f"  Tests: {result.test_result.passed}/{result.test_result.total} passing")
            click.echo(f"\nRun 'agentforge tdflow verify' or 'tdflow refactor'.")
        else:
            click.echo(f"\n✗ GREEN phase failed: {result.errors}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@tdflow.command('refactor')
@click.option('--component', '-c', help='Specific component')
def refactor(component):
    """Execute REFACTOR phase: clean up implementation."""
    orchestrator = TDFlowOrchestrator()
    result = orchestrator.run_refactor(component_name=component)
    # ... output handling


@tdflow.command('verify')
@click.option('--component', '-c', help='Specific component (default: all)')
def verify(component):
    """Verify implementation meets specification."""
    orchestrator = TDFlowOrchestrator()
    report = orchestrator.verify(component_name=component)
    
    click.echo(f"\nVerification Report")
    click.echo(f"{'━' * 40}")
    click.echo(f"Component: {report.component}")
    click.echo(f"Tests: {report.tests_passing}/{report.tests_total}")
    click.echo(f"Coverage: {report.coverage}%")
    click.echo(f"Violations: {report.conformance_violations}")
    click.echo(f"Status: {'✓ Verified' if report.verified else '✗ Not Verified'}")


@tdflow.command('status')
def status():
    """Show current session status."""
    manager = SessionManager()
    session = manager.get_latest()
    
    if not session:
        click.echo("No active session. Run 'agentforge tdflow start' first.")
        return
    
    click.echo(f"\nTDFLOW Session: {session.session_id}")
    click.echo(f"{'━' * 40}")
    click.echo(f"Phase: {session.current_phase.value}")
    click.echo(f"Components:")
    
    for comp in session.components:
        status_icon = {
            'pending': '○',
            'red': '◐',
            'green': '◑',
            'refactored': '◕',
            'verified': '●',
        }.get(comp.status.value, '?')
        click.echo(f"  {status_icon} {comp.name}: {comp.status.value}")


@tdflow.command('resume')
def resume():
    """Resume interrupted session."""
    orchestrator = TDFlowOrchestrator()
    orchestrator.resume()
    click.echo("Session resumed. Run 'agentforge tdflow status' for current state.")
```

---

## Phase 6: Prompt Contracts

### 6.1 `contracts/tdflow.red.v1.yaml`

```yaml
schema_version: "1.0"

contract:
  name: tdflow.red
  version: "1.0"
  description: |
    Generate failing tests from specification.
    Tests must fail initially (no implementation exists).
    
input:
  type: object
  required:
    - component
    - spec
  properties:
    component:
      type: object
      description: Component definition from specification
      properties:
        name:
          type: string
        methods:
          type: array
        dependencies:
          type: array
    spec:
      type: object
      description: Full specification for context
    test_framework:
      type: string
      enum: [xunit, nunit, pytest, jest]
    existing_patterns:
      type: object
      description: Test patterns from codebase discovery

output:
  type: object
  required:
    - test_file
  properties:
    test_file:
      type: object
      properties:
        path:
          type: string
          description: Relative path for test file
        content:
          type: string
          description: Complete test file content
    test_cases:
      type: array
      items:
        type: object
        properties:
          name:
            type: string
          method_under_test:
            type: string
          scenario:
            type: string
          expected_to_fail:
            type: boolean
            const: true

quality_criteria:
  - Each method in spec has at least 2 tests (happy path + error case)
  - Tests follow naming convention: {Method}_{Scenario}_{Expected}
  - Tests are isolated and independent
  - Tests will fail without implementation (verified at runtime)
  - Tests match existing codebase patterns if available
```

---

## Testing Requirements

### Unit Tests

```
tests/unit/tools/tdflow/
├── __init__.py
├── test_domain.py          # Domain entity tests
├── test_session.py         # Session management tests
├── test_orchestrator.py    # Orchestrator tests
├── runners/
│   ├── test_dotnet.py
│   └── test_pytest.py
└── phases/
    ├── test_red.py
    ├── test_green.py
    └── test_verify.py
```

### Integration Tests

- Full RED-GREEN cycle with mock LLM
- Session persistence and resume
- Test runner integration

---

## Validation Checklist

### Phase 1: Domain Model
- [ ] All domain entities have proper typing
- [ ] Session serialization/deserialization works
- [ ] Enums cover all states

### Phase 2: Test Runners
- [ ] DotNet runner parses output correctly
- [ ] Pytest runner parses output correctly
- [ ] Framework detection works

### Phase 3: Session Management
- [ ] Create session from spec
- [ ] Save and load sessions
- [ ] Resume interrupted sessions

### Phase 4: Phase Executors
- [ ] RED generates tests that fail
- [ ] GREEN generates implementation that passes
- [ ] REFACTOR maintains passing tests

### Phase 5: CLI
- [ ] All commands registered
- [ ] Status display works
- [ ] Error handling is user-friendly

### Phase 6: Integration
- [ ] SPEC output flows to TDFLOW
- [ ] Conformance checks integrate
- [ ] Full workflow E2E works
