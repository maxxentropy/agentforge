# Implementation Spec Part 5: Integration and Testing

## 6. Executor Integration

### 6.1 Updated Executor

```python
# src/agentforge/core/harness/minimal_context/executor.py (updated)

from pathlib import Path
from typing import Optional, Dict, Any

from ...context.agent_config import AgentConfigLoader
from ...context.fingerprint import FingerprintGenerator
from ...context.templates import get_template_for_task
from ...context.compaction import CompactionManager
from ...context.audit import ContextAuditLogger
from ...llm.interface import LLMClient, ThinkingConfig
from ...llm.factory import LLMClientFactory
from ...llm.tools import get_tools_for_task

from .context_models import TaskSpec, StateSpec, AgentContext
from .phase_machine import PhaseMachine


class MinimalContextExecutor:
    """
    Executor with full context management integration.
    
    Key features:
    - Configurable via AGENT.md chain
    - Dynamic project fingerprints
    - Task-type specific templates
    - LLM simulation for testing
    - Full audit trail
    """
    
    def __init__(
        self,
        project_path: Path,
        task_type: str = "fix_violation",
        llm_client: Optional[LLMClient] = None,
        llm_mode: Optional[str] = None,
    ):
        """
        Initialize executor.
        
        Args:
            project_path: Root path of the project
            task_type: Type of task to execute
            llm_client: Optional LLM client (uses factory if not provided)
            llm_mode: Optional LLM mode override (real|simulated|playback)
        """
        self.project_path = Path(project_path).resolve()
        self.task_type = task_type
        
        # Load configuration from AGENT.md chain
        self.config_loader = AgentConfigLoader(self.project_path)
        self.config = self.config_loader.load(task_type)
        
        # Initialize fingerprint generator
        self.fingerprint_generator = FingerprintGenerator(self.project_path)
        
        # Get context template for task type
        self.template = get_template_for_task(task_type)
        
        # Initialize LLM client
        self.llm_client = llm_client or LLMClientFactory.create(mode=llm_mode)
        
        # Configure thinking from config
        self.thinking_config = ThinkingConfig(
            enabled=self.config.defaults.thinking_enabled,
            budget_tokens=self.config.defaults.thinking_budget,
        )
        
        # Get tools for task type
        self.tools = get_tools_for_task(task_type)
        
        # Initialize compaction manager
        self.compaction_manager = CompactionManager(
            threshold=0.90,
            max_budget=self.config.defaults.token_budget,
        )
        
        # Audit logger (initialized per task)
        self.audit_logger: Optional[ContextAuditLogger] = None
        
        # Execution state
        self.phase_machine = PhaseMachine()
    
    def execute_task(
        self,
        task_spec: TaskSpec,
        precomputed: Dict[str, Any],
        domain_context: Dict[str, Any],
    ) -> TaskResult:
        """
        Execute a complete task.
        
        Args:
            task_spec: Task specification
            precomputed: Pre-computed analysis data
            domain_context: Domain-specific context
            
        Returns:
            TaskResult with outcome and audit info
        """
        # Initialize audit logger
        self.audit_logger = ContextAuditLogger(
            project_path=self.project_path,
            task_id=task_spec.task_id,
        )
        
        # Initialize state
        state_spec = StateSpec()
        
        # Execute steps until completion or limit
        max_steps = self.config.defaults.max_steps
        
        while state_spec.current_step < max_steps:
            step_result = self._execute_step(
                task_spec=task_spec,
                state_spec=state_spec,
                precomputed=precomputed,
                domain_context=domain_context,
            )
            
            # Update state
            state_spec = self._update_state(state_spec, step_result)
            
            # Check for completion
            if step_result.is_terminal:
                break
        
        # Log task summary
        usage = self.llm_client.get_usage_stats()
        self.audit_logger.log_task_summary(
            total_steps=state_spec.current_step,
            final_status=step_result.status,
            total_tokens=usage["total_input_tokens"],
            cached_tokens=usage.get("cached_tokens", 0),
        )
        
        return TaskResult(
            task_id=task_spec.task_id,
            status=step_result.status,
            summary=step_result.summary,
            steps=state_spec.current_step,
            usage=usage,
        )
    
    def _execute_step(
        self,
        task_spec: TaskSpec,
        state_spec: StateSpec,
        precomputed: Dict[str, Any],
        domain_context: Dict[str, Any],
    ) -> StepResult:
        """Execute a single step."""
        
        # Generate fingerprint with task context
        fingerprint = self.fingerprint_generator.with_task_context(
            task_type=self.task_type,
            constraints={
                "correctness_first": True,
                "test_verification": "required",
                **{c: True for c in self.config.constraints},
            },
            success_criteria=task_spec.success_criteria,
        )
        
        # Get current phase
        phase = self.phase_machine.current_phase.value
        
        # Build context using template
        context_dict = self.template.build_context_dict(
            fingerprint=fingerprint,
            task_spec=task_spec,
            state_spec=state_spec,
            phase=phase,
            precomputed=precomputed,
            domain_context=domain_context,
        )
        
        # Compute token breakdown
        token_breakdown = self._compute_token_breakdown(context_dict)
        
        # Compact if needed
        compaction_audit = None
        if self.compaction_manager.needs_compaction(context_dict):
            context_dict, compaction_audit = self.compaction_manager.compact(
                context_dict,
                preserve=["fingerprint", "task", "phase"],
            )
        
        # Build messages
        system_prompt = self.template.get_system_prompt(phase)
        user_message = self._format_context(context_dict)
        
        # Call LLM
        response = self.llm_client.complete(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=self.tools,
            thinking=self.thinking_config,
        )
        
        # Log for audit
        self.audit_logger.log_step(
            step=state_spec.current_step,
            context=context_dict,
            token_breakdown=token_breakdown,
            compaction=compaction_audit,
            thinking=response.thinking,
            response=response.content,
        )
        
        # Process response
        return self._process_response(response, state_spec)
    
    def _format_context(self, context_dict: Dict[str, Any]) -> str:
        """Format context dict as YAML for user message."""
        import yaml
        return yaml.dump(context_dict, default_flow_style=False, sort_keys=False)
    
    def _compute_token_breakdown(self, context: Dict[str, Any]) -> Dict[str, int]:
        """Compute tokens per section."""
        import yaml
        breakdown = {}
        for key, value in context.items():
            section_yaml = yaml.dump({key: value}, default_flow_style=False)
            breakdown[key] = len(section_yaml) // 4
        return breakdown
```

### 6.2 Result Models

```python
# src/agentforge/core/harness/minimal_context/results.py

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class StepResult:
    """Result of a single execution step."""
    action: str
    parameters: Dict[str, Any]
    status: str  # success, failure, pending
    summary: str
    is_terminal: bool = False
    error: Optional[str] = None


@dataclass
class TaskResult:
    """Result of a complete task execution."""
    task_id: str
    status: str  # completed, failed, escalated
    summary: str
    steps: int
    usage: Dict[str, int]
    
    @property
    def success(self) -> bool:
        return self.status == "completed"
```

---

## 7. Testing Strategy

### 7.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  Few, expensive, real API
                    │  Tests  │  (manual/scheduled)
                   ─┴─────────┴─
                  ┌─────────────┐
                  │ Integration │  Template + LLM sim
                  │    Tests    │  Full workflow mocks
                 ─┴─────────────┴─
                ┌───────────────────┐
                │    Unit Tests     │  All components
                │   (Simulated)     │  No API calls
               ─┴───────────────────┴─
```

### 7.2 Test Categories

```python
# tests/conftest.py

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentforge.core.llm.factory import LLMClientFactory, LLMClientMode
from agentforge.core.llm.simulated import SimulatedLLMClient


@pytest.fixture
def simulated_llm():
    """Provide a simulated LLM client for testing."""
    return LLMClientFactory.create_for_testing()


@pytest.fixture
def temp_project():
    """Provide a temporary project directory."""
    with TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "test_project"
        project.mkdir()
        (project / "src").mkdir()
        (project / "tests").mkdir()
        (project / ".agentforge").mkdir()
        yield project


@pytest.fixture
def sample_pyproject(temp_project):
    """Create a sample pyproject.toml."""
    pyproject = temp_project / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "test-project"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.0.0", "pytest>=7.0.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
""")
    return pyproject


# Marker for tests that need real API
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_api: mark test as requiring real API access"
    )


# Skip real API tests unless explicitly enabled
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-real-api", default=False):
        skip_real = pytest.mark.skip(reason="need --run-real-api option")
        for item in items:
            if "real_api" in item.keywords:
                item.add_marker(skip_real)
```

### 7.3 Unit Test Examples

```python
# tests/unit/context/test_integration.py

import pytest
from pathlib import Path

from agentforge.core.context.agent_config import AgentConfigLoader
from agentforge.core.context.fingerprint import FingerprintGenerator
from agentforge.core.context.templates import get_template_for_task
from agentforge.core.llm.factory import LLMClientFactory


class TestContextIntegration:
    """Integration tests for context management."""
    
    def test_full_context_build(self, temp_project, sample_pyproject):
        """Test building complete context."""
        # Setup
        config_loader = AgentConfigLoader(temp_project)
        fingerprint_gen = FingerprintGenerator(temp_project)
        template = get_template_for_task("fix_violation")
        
        # Build fingerprint
        fingerprint = fingerprint_gen.with_task_context(
            task_type="fix_violation",
            constraints={"correctness_first": True},
            success_criteria=["Tests pass"],
        )
        
        # Build context
        from agentforge.core.harness.minimal_context.context_models import (
            TaskSpec, StateSpec
        )
        
        task_spec = TaskSpec(
            task_id="test-001",
            task_type="fix_violation",
            goal="Reduce complexity",
            success_criteria=["Check passes"],
        )
        state_spec = StateSpec()
        
        context = template.build_context_dict(
            fingerprint=fingerprint,
            task_spec=task_spec,
            state_spec=state_spec,
            phase="implement",
            precomputed={
                "target_source": "def example(): pass",
                "extraction_suggestions": [{"name": "helper"}],
            },
            domain_context={
                "violation": {"id": "V-001", "type": "complexity"},
            },
        )
        
        # Verify structure
        assert "fingerprint" in context
        assert "task" in context
        assert "phase" in context
        assert "target_source" in context
    
    def test_context_with_simulated_llm(self, temp_project, sample_pyproject):
        """Test complete flow with simulated LLM."""
        # Create simulated client with scripted response
        client = LLMClientFactory.create_for_testing(responses=[
            {
                "tool_calls": [
                    {"name": "read_file", "input": {"path": "/src/file.py"}}
                ]
            },
            {
                "tool_calls": [
                    {"name": "complete", "input": {"summary": "Done"}}
                ]
            },
        ])
        
        # Execute would use this client
        # The test verifies the LLM is called with correct context
        
        # First call
        response1 = client.complete(
            system="Test",
            messages=[{"role": "user", "content": "Do task"}],
        )
        assert response1.tool_calls[0].name == "read_file"
        
        # Second call
        response2 = client.complete(
            system="Test",
            messages=[{"role": "user", "content": "Continue"}],
        )
        assert response2.tool_calls[0].name == "complete"
```

### 7.4 Fixture Scripts

```yaml
# tests/fixtures/llm_scripts/fix_violation_complexity.yaml
# Full workflow for fixing complexity violation

metadata:
  name: "Fix Complexity - Happy Path"
  task_type: fix_violation
  expected_steps: 4

responses:
  - step: 1
    phase: analyze
    thinking: |
      I need to understand the violation first.
      Reading the target file to see the complex function.
    tool_calls:
      - name: read_file
        input:
          path: "src/executor.py"

  - step: 2
    phase: implement
    thinking: |
      The function has complexity 15. I can see lines 67-78
      handle error cases - this is a good extraction target.
      Using the pre-computed suggestion.
    tool_calls:
      - name: extract_function
        input:
          file_path: "src/executor.py"
          source_function: "execute"
          start_line: 67
          end_line: 78
          new_function_name: "_handle_error"

  - step: 3
    phase: verify
    thinking: |
      Extraction succeeded. Running check to verify
      complexity is now under threshold.
    tool_calls:
      - name: run_check
        input:
          file_path: "src/executor.py"

  - step: 4
    phase: verify
    thinking: |
      Check passes - complexity is now 10.
      All tests still pass. Task complete.
    tool_calls:
      - name: complete
        input:
          summary: "Reduced complexity from 15 to 10 via extract_function"
```

### 7.5 Running Tests

```bash
# Run all unit tests (no API calls)
pytest tests/unit/ -v

# Run integration tests with simulated LLM
pytest tests/integration/ -v

# Run with real API (requires key, costs tokens)
pytest tests/ --run-real-api -v -k "real_api"

# Run with coverage
pytest tests/unit/ --cov=agentforge.core.context --cov-report=html

# Run specific test file
pytest tests/unit/context/test_agent_config.py -v
```

---

## 8. Environment Configuration

### 8.1 Environment Variables

```bash
# LLM Mode (defaults to 'real' if not set)
export AGENTFORGE_LLM_MODE=simulated  # or: real, playback, record

# Simulation script path
export AGENTFORGE_LLM_SCRIPT=/path/to/script.yaml

# Recording path (for record/playback modes)
export AGENTFORGE_LLM_RECORDING=/path/to/recording.yaml

# API key (for real mode)
export ANTHROPIC_API_KEY=sk-ant-...

# Debug mode
export AGENTFORGE_DEBUG=true
```

### 8.2 Development Workflow

```bash
# 1. Development with simulation (no API costs)
export AGENTFORGE_LLM_MODE=simulated
pytest tests/unit/ -v
python -m agentforge.cli fix src/file.py

# 2. Record a real session for later playback
export AGENTFORGE_LLM_MODE=record
export AGENTFORGE_LLM_RECORDING=recordings/session_001.yaml
python -m agentforge.cli fix src/file.py

# 3. Playback recorded session (deterministic)
export AGENTFORGE_LLM_MODE=playback
export AGENTFORGE_LLM_RECORDING=recordings/session_001.yaml
python -m agentforge.cli fix src/file.py

# 4. Production with real API
export AGENTFORGE_LLM_MODE=real
python -m agentforge.cli fix src/file.py
```

---

## 9. File Summary

### 9.1 New Files to Create

```
src/agentforge/core/
├── context/
│   ├── __init__.py
│   ├── agent_config.py      # Part 2
│   ├── fingerprint.py       # Part 3
│   ├── compaction.py        # From 06-compaction.yaml
│   ├── audit.py             # From 07-audit.yaml
│   └── templates/
│       ├── __init__.py      # Part 4
│       ├── models.py        # Part 4
│       ├── base.py          # Part 4
│       ├── fix_violation.py # Part 4
│       └── implement_feature.py  # Part 4
│
├── llm/
│   ├── __init__.py
│   ├── interface.py         # Part 1
│   ├── client.py            # Real Anthropic client
│   ├── simulated.py         # Part 1
│   ├── factory.py           # Part 1
│   └── tools.py             # Tool definitions

tests/
├── unit/
│   ├── context/
│   │   ├── test_agent_config.py
│   │   ├── test_fingerprint.py
│   │   ├── test_templates.py
│   │   └── test_compaction.py
│   └── llm/
│       ├── test_simulated.py
│       └── test_factory.py
├── integration/
│   └── context/
│       └── test_full_workflow.py
└── fixtures/
    └── llm_scripts/
        ├── fix_violation_success.yaml
        └── fix_violation_escalate.yaml
```

### 9.2 Files to Modify

```
src/agentforge/core/harness/minimal_context/
├── executor.py              # Integrate new components
└── enhanced_context_builder.py  # May be deprecated
```

---

## 10. Implementation Checklist

```
Phase 1: Foundation
├── [ ] Create context/ directory structure
├── [ ] Implement agent_config.py
├── [ ] Implement fingerprint.py
├── [ ] Write unit tests for both
└── [ ] Verify: pytest tests/unit/context/ passes

Phase 2: LLM Abstraction
├── [ ] Create llm/ directory structure
├── [ ] Implement interface.py
├── [ ] Implement simulated.py
├── [ ] Implement factory.py
├── [ ] Write unit tests
└── [ ] Verify: Can run with AGENTFORGE_LLM_MODE=simulated

Phase 3: Context Templates
├── [ ] Implement templates/models.py
├── [ ] Implement templates/base.py
├── [ ] Implement fix_violation.py
├── [ ] Implement implement_feature.py
├── [ ] Write unit tests
└── [ ] Verify: Templates produce valid context

Phase 4: Integration
├── [ ] Implement compaction.py
├── [ ] Implement audit.py
├── [ ] Update executor.py
├── [ ] Write integration tests
├── [ ] Create fixture scripts
└── [ ] Verify: Full workflow with simulated LLM

Phase 5: Validation
├── [ ] Run against real violations (with API)
├── [ ] Compare token usage before/after
├── [ ] Verify audit completeness
├── [ ] Document any changes
└── [ ] Update README
```

---

**[Implementation Specification Complete]**

This spec provides:
1. **LLM Simulation** - Develop/test without API costs
2. **Modular Components** - Each piece independently testable
3. **Clear Interfaces** - Abstract LLM client enables swapping
4. **Audit Trail** - Full transparency for debugging
5. **Test Strategy** - Unit/integration/E2E pyramid
