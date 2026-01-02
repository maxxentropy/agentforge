# Pipeline Controller Specification - Stage 2: Stage Executor Interface

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1 (Core Architecture)  
**Estimated Effort:** 3-4 days

---

## 1. Overview

### 1.1 Purpose

The Stage Executor Interface defines the contract that all pipeline stages must implement. This provides a consistent abstraction for stage execution, enabling:

- Uniform stage lifecycle management
- Standardized artifact input/output
- Integration with MinimalContextExecutor
- Pluggable stage implementations

### 1.2 Key Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                      Stage Executor                              │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ StageContext │ -> │ StageExecutor│ -> │ StageResult      │  │
│  │              │    │   .execute() │    │ (artifact/error) │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                     │             │
│         │                   ▼                     │             │
│         │         ┌──────────────────┐           │             │
│         │         │ MinimalContext   │           │             │
│         │         │ Executor         │           │             │
│         │         │ (LLM + Tools)    │           │             │
│         │         └──────────────────┘           │             │
│         │                   │                     │             │
│         └───────────────────┼─────────────────────┘             │
│                             ▼                                    │
│                    Stage Artifacts                               │
│              (YAML files in .agentforge/)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Interfaces

### 2.1 StageExecutor Base Class

```python
# src/agentforge/core/pipeline/stage_executor.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import logging
import yaml

from .controller import StageResult, StageStatus
from .state import PipelineState

logger = logging.getLogger(__name__)


class StagePhase(Enum):
    """Phases within a stage execution."""
    INITIALIZE = "initialize"
    VALIDATE_INPUT = "validate_input"
    EXECUTE = "execute"
    VALIDATE_OUTPUT = "validate_output"
    FINALIZE = "finalize"


@dataclass
class StageContext:
    """
    Context provided to stage executors.
    
    Contains all information needed to execute a stage.
    """
    # Pipeline context
    pipeline_id: str
    pipeline_type: str
    stage_name: str
    stage_index: int
    
    # Input
    input_artifact: Dict[str, Any]
    user_request: str
    
    # Project
    project_path: Path
    agentforge_path: Path
    
    # Previous stages
    completed_stages: List[str] = field(default_factory=list)
    stage_artifacts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Iteration
    iteration: int = 0
    previous_feedback: Optional[str] = None
    previous_attempt: Optional[Dict[str, Any]] = None
    
    # Configuration
    timeout_seconds: int = 600
    max_tokens: int = 100000
    
    @classmethod
    def from_pipeline_state(
        cls,
        state: PipelineState,
        stage_name: str,
        input_artifact: Dict[str, Any],
        project_path: Path,
    ) -> "StageContext":
        """Create context from pipeline state."""
        return cls(
            pipeline_id=state.pipeline_id,
            pipeline_type=state.pipeline_type,
            stage_name=stage_name,
            stage_index=state.current_stage_index,
            input_artifact=input_artifact,
            user_request=state.user_request,
            project_path=project_path,
            agentforge_path=project_path / ".agentforge",
            completed_stages=state.completed_stages.copy(),
            stage_artifacts=state.stage_artifacts.copy(),
            iteration=state.iteration_count.get(stage_name, 0),
            previous_feedback=state.pending_feedback,
        )


@dataclass
class StageArtifact:
    """
    Structured artifact produced by a stage.
    
    Provides standard methods for serialization and validation.
    """
    stage_name: str
    artifact_type: str
    version: str = "1.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "_artifact_meta": {
                "stage_name": self.stage_name,
                "artifact_type": self.artifact_type,
                "version": self.version,
                "created_at": self.created_at.isoformat(),
            },
            **self.data,
            "_metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageArtifact":
        """Deserialize from dictionary."""
        meta = data.pop("_artifact_meta", {})
        metadata = data.pop("_metadata", {})
        
        return cls(
            stage_name=meta.get("stage_name", "unknown"),
            artifact_type=meta.get("artifact_type", "unknown"),
            version=meta.get("version", "1.0"),
            created_at=datetime.fromisoformat(meta["created_at"]) if meta.get("created_at") else datetime.now(timezone.utc),
            data=data,
            metadata=metadata,
        )
    
    def save(self, path: Path) -> None:
        """Save artifact to YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
    
    @classmethod
    def load(cls, path: Path) -> "StageArtifact":
        """Load artifact from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class StageExecutor(ABC):
    """
    Abstract base class for stage executors.
    
    Each pipeline stage (intake, clarify, analyze, etc.) implements
    this interface to define its behavior.
    
    Lifecycle:
        1. initialize() - Setup, load resources
        2. validate_input() - Check input artifact
        3. execute() - Main stage logic
        4. validate_output() - Check output artifact
        5. finalize() - Cleanup, save artifacts
    
    Usage:
        class IntakeExecutor(StageExecutor):
            stage_name = "intake"
            
            def execute(self, context: StageContext) -> StageResult:
                # Stage implementation
                ...
    """
    
    # Class attributes to override
    stage_name: str = "unknown"
    artifact_type: str = "generic"
    required_input_fields: List[str] = []
    output_fields: List[str] = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize executor.
        
        Args:
            config: Stage-specific configuration
        """
        self.config = config or {}
        self._executor = None  # MinimalContextExecutor, lazily created
    
    # --- Main Entry Point ---
    
    def execute(
        self,
        input_artifact: Dict[str, Any],
        pipeline_state: PipelineState,
        project_path: Path,
    ) -> StageResult:
        """
        Execute the stage.
        
        This is called by PipelineController. Subclasses should override
        _execute() instead of this method.
        
        Args:
            input_artifact: Artifact from previous stage
            pipeline_state: Current pipeline state
            project_path: Project root path
            
        Returns:
            StageResult with status and output artifact
        """
        start_time = datetime.now(timezone.utc)
        
        # Build context
        context = StageContext.from_pipeline_state(
            state=pipeline_state,
            stage_name=self.stage_name,
            input_artifact=input_artifact,
            project_path=project_path,
        )
        
        try:
            # Phase 1: Initialize
            logger.info(f"Stage {self.stage_name}: Initializing")
            self._phase = StagePhase.INITIALIZE
            init_result = self.initialize(context)
            if init_result and not init_result.success:
                return init_result
            
            # Phase 2: Validate input
            logger.info(f"Stage {self.stage_name}: Validating input")
            self._phase = StagePhase.VALIDATE_INPUT
            validation = self.validate_input(context)
            if not validation.valid:
                return StageResult(
                    stage_name=self.stage_name,
                    status=StageStatus.FAILED,
                    error=f"Input validation failed: {validation.errors}"
                )
            
            # Phase 3: Execute
            logger.info(f"Stage {self.stage_name}: Executing")
            self._phase = StagePhase.EXECUTE
            result = self._execute(context)
            
            if not result.success:
                return result
            
            # Phase 4: Validate output
            logger.info(f"Stage {self.stage_name}: Validating output")
            self._phase = StagePhase.VALIDATE_OUTPUT
            output_validation = self.validate_output(result.artifact)
            if not output_validation.valid:
                return StageResult(
                    stage_name=self.stage_name,
                    status=StageStatus.FAILED,
                    error=f"Output validation failed: {output_validation.errors}"
                )
            
            # Phase 5: Finalize
            logger.info(f"Stage {self.stage_name}: Finalizing")
            self._phase = StagePhase.FINALIZE
            self.finalize(context, result)
            
            # Record duration
            result.duration_seconds = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()
            
            return result
            
        except Exception as e:
            logger.exception(f"Stage {self.stage_name} failed: {e}")
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error=str(e),
                duration_seconds=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    # --- Lifecycle Methods (Override as needed) ---
    
    def initialize(self, context: StageContext) -> Optional[StageResult]:
        """
        Initialize stage execution.
        
        Override to perform setup, load resources, etc.
        Return StageResult only if initialization fails.
        """
        return None
    
    def validate_input(self, context: StageContext) -> "InputValidation":
        """
        Validate input artifact.
        
        Default implementation checks required_input_fields.
        Override for custom validation.
        """
        errors = []
        for field_name in self.required_input_fields:
            if field_name not in context.input_artifact:
                errors.append(f"Missing required field: {field_name}")
        
        return InputValidation(valid=len(errors) == 0, errors=errors)
    
    @abstractmethod
    def _execute(self, context: StageContext) -> StageResult:
        """
        Execute stage logic.
        
        This is the main method to override. Implement the stage's
        core functionality here.
        
        Args:
            context: Stage execution context
            
        Returns:
            StageResult with artifact or error
        """
        pass
    
    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """
        Validate output artifact.
        
        Default implementation checks output_fields.
        Override for custom validation.
        """
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact produced"])
        
        errors = []
        for field_name in self.output_fields:
            if field_name not in artifact:
                errors.append(f"Missing output field: {field_name}")
        
        return OutputValidation(valid=len(errors) == 0, errors=errors)
    
    def finalize(
        self,
        context: StageContext,
        result: StageResult,
    ) -> None:
        """
        Finalize stage execution.
        
        Override to perform cleanup, save artifacts, etc.
        Default implementation saves artifact to .agentforge/artifacts/.
        """
        if result.success and result.artifact:
            self._save_artifact(context, result.artifact)
    
    # --- Helper Methods ---
    
    def _save_artifact(
        self,
        context: StageContext,
        artifact: Dict[str, Any],
    ) -> Path:
        """Save artifact to standard location."""
        artifacts_dir = context.agentforge_path / "artifacts" / context.pipeline_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{context.stage_index:02d}-{self.stage_name}.yaml"
        artifact_path = artifacts_dir / filename
        
        # Wrap in StageArtifact
        stage_artifact = StageArtifact(
            stage_name=self.stage_name,
            artifact_type=self.artifact_type,
            data=artifact,
            metadata={
                "pipeline_id": context.pipeline_id,
                "iteration": context.iteration,
            }
        )
        stage_artifact.save(artifact_path)
        
        logger.info(f"Saved artifact: {artifact_path}")
        return artifact_path
    
    def _get_executor(self, context: StageContext) -> "MinimalContextExecutor":
        """Get or create MinimalContextExecutor for this stage."""
        if self._executor is None:
            from agentforge.core.harness.minimal_context import MinimalContextExecutor
            
            self._executor = MinimalContextExecutor(
                project_path=context.project_path,
                task_type=f"stage_{self.stage_name}",
            )
        return self._executor
    
    def _run_with_llm(
        self,
        context: StageContext,
        system_prompt: str,
        user_message: str,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Execute LLM-based stage logic.
        
        Convenience method for stages that delegate to LLM.
        
        Args:
            context: Stage context
            system_prompt: System prompt for LLM
            user_message: User message
            tools: Optional tool definitions
            
        Returns:
            LLM response with extracted artifact
        """
        executor = self._get_executor(context)
        
        # Build task
        task_context = {
            "pipeline_id": context.pipeline_id,
            "stage_name": self.stage_name,
            "input_artifact": context.input_artifact,
            "user_request": context.user_request,
        }
        
        if context.previous_feedback:
            task_context["feedback"] = context.previous_feedback
        
        # Execute
        result = executor.execute_task(
            task_description=user_message,
            system_prompt=system_prompt,
            context=task_context,
            tools=tools,
            max_iterations=10,
        )
        
        return result
    
    def escalate(
        self,
        context: StageContext,
        reason: str,
        partial_artifact: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        """
        Escalate to human intervention.
        
        Use when the stage cannot proceed without human input.
        
        Args:
            context: Stage context
            reason: Reason for escalation
            partial_artifact: Any partial work completed
            
        Returns:
            StageResult with escalation flag
        """
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.PENDING,  # Not failed, just waiting
            artifact=partial_artifact,
            escalation_reason=reason,
        )


@dataclass
class InputValidation:
    """Result of input validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass 
class OutputValidation:
    """Result of output validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```

### 2.2 LLMStageExecutor

Specialized base class for LLM-driven stages.

```python
# src/agentforge/core/pipeline/llm_stage_executor.py

from abc import abstractmethod
from typing import Any, Dict, List, Optional
import yaml

from .stage_executor import (
    StageExecutor,
    StageContext,
    StageResult,
    StageStatus,
)


class LLMStageExecutor(StageExecutor):
    """
    Base class for stages that use LLM for execution.
    
    Provides common patterns for LLM-based stages:
    - System prompt templating
    - Response parsing
    - Retry with feedback
    
    Subclasses implement:
    - get_system_prompt(): System prompt for LLM
    - get_user_message(): User message construction
    - parse_response(): Extract artifact from LLM response
    """
    
    # LLM configuration
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8000
    temperature: float = 0.7
    
    # Tools to provide (override in subclass)
    tools: List[Dict[str, Any]] = []
    
    def _execute(self, context: StageContext) -> StageResult:
        """Execute stage using LLM."""
        # Build prompts
        system_prompt = self.get_system_prompt(context)
        user_message = self.get_user_message(context)
        
        # Execute with LLM
        try:
            llm_result = self._run_with_llm(
                context=context,
                system_prompt=system_prompt,
                user_message=user_message,
                tools=self.tools if self.tools else None,
            )
            
            # Parse response
            artifact = self.parse_response(llm_result, context)
            
            if artifact is None:
                return StageResult(
                    stage_name=self.stage_name,
                    status=StageStatus.FAILED,
                    error="Failed to parse LLM response into artifact",
                )
            
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.COMPLETED,
                artifact=artifact,
            )
            
        except Exception as e:
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error=f"LLM execution failed: {e}",
            )
    
    @abstractmethod
    def get_system_prompt(self, context: StageContext) -> str:
        """
        Get system prompt for this stage.
        
        Override to provide stage-specific system prompt.
        Can use context to include relevant information.
        """
        pass
    
    @abstractmethod
    def get_user_message(self, context: StageContext) -> str:
        """
        Get user message for this stage.
        
        Override to construct the user message from context.
        """
        pass
    
    @abstractmethod
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response into stage artifact.
        
        Override to extract structured artifact from LLM output.
        Return None if parsing fails.
        """
        pass
    
    # --- Utility Methods ---
    
    def extract_yaml_from_response(self, response_text: str) -> Optional[Dict]:
        """Extract YAML block from LLM response."""
        import re
        
        # Try to find YAML code block
        yaml_match = re.search(
            r"```ya?ml\s*\n(.*?)\n```",
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        
        if yaml_match:
            try:
                return yaml.safe_load(yaml_match.group(1))
            except yaml.YAMLError:
                pass
        
        # Try to parse entire response as YAML
        try:
            return yaml.safe_load(response_text)
        except yaml.YAMLError:
            pass
        
        return None
    
    def extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extract JSON from LLM response."""
        import json
        import re
        
        # Try to find JSON code block
        json_match = re.search(
            r"```json\s*\n(.*?)\n```",
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None


class ToolBasedStageExecutor(LLMStageExecutor):
    """
    Stage executor that relies on tool use for output.
    
    Instead of parsing LLM text, this expects the LLM to use
    a specific tool to produce the artifact.
    """
    
    # Tool that produces the artifact
    artifact_tool_name: str = "complete"
    
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Extract artifact from tool use result."""
        # Check if the expected tool was called
        tool_results = llm_result.get("tool_results", [])
        
        for tool_result in tool_results:
            if tool_result.get("tool_name") == self.artifact_tool_name:
                return tool_result.get("result", {})
        
        # Fall back to final response
        return llm_result.get("final_artifact")
```

### 2.3 ContractStageExecutor

Stage executor that wraps existing contracts.

```python
# src/agentforge/core/pipeline/contract_stage_executor.py

from typing import Any, Dict, Optional

from .stage_executor import (
    StageExecutor,
    StageContext,
    StageResult,
    StageStatus,
)


class ContractStageExecutor(StageExecutor):
    """
    Stage executor that delegates to an existing contract.
    
    This allows reuse of existing contract-based implementations
    (intake, clarify, analyze, etc.) within the pipeline.
    
    Usage:
        intake_executor = ContractStageExecutor(
            stage_name="intake",
            contract_id="spec.intake.v1",
            input_mapping={"raw_request": "user_request"},
            output_mapping={"intake_record": None},
        )
    """
    
    def __init__(
        self,
        stage_name: str,
        contract_id: str,
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize contract-based executor.
        
        Args:
            stage_name: Name of this stage
            contract_id: Contract ID to execute (e.g., "spec.intake.v1")
            input_mapping: Map artifact fields to contract inputs
            output_mapping: Map contract outputs to artifact fields
            config: Additional configuration
        """
        super().__init__(config)
        self.stage_name = stage_name
        self.contract_id = contract_id
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}
    
    def _execute(self, context: StageContext) -> StageResult:
        """Execute by running contract."""
        from cli.core import execute_contract
        
        # Build contract inputs from artifact
        contract_inputs = {}
        for contract_field, artifact_field in self.input_mapping.items():
            if artifact_field in context.input_artifact:
                contract_inputs[contract_field] = context.input_artifact[artifact_field]
            elif artifact_field == "user_request":
                contract_inputs[contract_field] = context.user_request
        
        # Add any defaults from config
        contract_inputs.update(self.config.get("defaults", {}))
        
        try:
            # Execute contract
            result = execute_contract(
                self.contract_id,
                contract_inputs,
                use_api=True,  # Always use API for pipeline
            )
            
            # Map outputs to artifact
            artifact = dict(context.input_artifact)  # Carry forward
            
            if self.output_mapping:
                for output_field, artifact_field in self.output_mapping.items():
                    if output_field in result:
                        target = artifact_field or output_field
                        artifact[target] = result[output_field]
            else:
                # Merge all outputs
                artifact.update(result)
            
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.COMPLETED,
                artifact=artifact,
            )
            
        except Exception as e:
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error=f"Contract execution failed: {e}",
            )
```

---

## 3. Artifact Contracts

### 3.1 Standard Artifact Schema

Each stage produces artifacts following this schema:

```yaml
# .agentforge/artifacts/{pipeline_id}/{stage_index}-{stage_name}.yaml

_artifact_meta:
  stage_name: "intake"
  artifact_type: "intake_record"
  version: "1.0"
  created_at: "2026-01-02T15:30:00Z"

# Stage-specific data
request_id: "REQ-20260102-abc123"
detected_scope: "feature_addition"
initial_questions:
  - question: "What authentication provider?"
    priority: "blocking"

_metadata:
  pipeline_id: "PL-20260102-xyz789"
  iteration: 0
  tokens_used: 1500
  duration_seconds: 3.2
```

### 3.2 Artifact Type Definitions

```python
# src/agentforge/core/pipeline/artifacts.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IntakeArtifact:
    """Artifact produced by INTAKE stage."""
    request_id: str
    original_request: str
    detected_scope: str  # "bug_fix", "feature_addition", "refactoring", "unclear"
    priority: str  # "low", "medium", "high", "critical"
    initial_questions: List[Dict[str, Any]] = field(default_factory=list)
    detected_components: List[str] = field(default_factory=list)


@dataclass
class ClarifyArtifact:
    """Artifact produced by CLARIFY stage."""
    request_id: str
    clarified_requirements: str
    answered_questions: List[Dict[str, Any]] = field(default_factory=list)
    remaining_questions: List[Dict[str, Any]] = field(default_factory=list)
    scope_confirmed: bool = False


@dataclass
class AnalyzeArtifact:
    """Artifact produced by ANALYZE stage."""
    request_id: str
    analysis: Dict[str, Any] = field(default_factory=dict)
    affected_files: List[str] = field(default_factory=list)
    components: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    risks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SpecArtifact:
    """Artifact produced by SPEC stage."""
    spec_id: str
    request_id: str
    components: List[Dict[str, Any]] = field(default_factory=list)
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class RedArtifact:
    """Artifact produced by RED (test-first) stage."""
    spec_id: str
    test_files: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    failing_tests: List[str] = field(default_factory=list)


@dataclass
class GreenArtifact:
    """Artifact produced by GREEN (implementation) stage."""
    spec_id: str
    implementation_files: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    passing_tests: List[str] = field(default_factory=list)


@dataclass
class RefactorArtifact:
    """Artifact produced by REFACTOR stage."""
    spec_id: str
    refactored_files: List[str] = field(default_factory=list)
    improvements: List[Dict[str, Any]] = field(default_factory=list)
    final_files: List[str] = field(default_factory=list)


@dataclass
class DeliverArtifact:
    """Artifact produced by DELIVER stage."""
    spec_id: str
    deliverable_type: str  # "commit", "pr", "files"
    commit_sha: Optional[str] = None
    pr_url: Optional[str] = None
    files_modified: List[str] = field(default_factory=list)
    summary: str = ""
```

---

## 4. Directory Structure

```
src/agentforge/core/pipeline/
├── __init__.py
├── controller.py              # PipelineController (Stage 1)
├── state.py                   # PipelineState (Stage 1)
├── state_store.py             # PipelineStateStore (Stage 1)
├── registry.py                # StageExecutorRegistry (Stage 1)
├── escalation.py              # EscalationHandler (Stage 1)
├── validator.py               # ArtifactValidator (Stage 1)
├── stage_executor.py          # StageExecutor base class
├── llm_stage_executor.py      # LLMStageExecutor
├── contract_stage_executor.py # ContractStageExecutor
├── artifacts.py               # Artifact dataclasses
└── stages/                    # Individual stage implementations (Stage 3-7)
    ├── __init__.py
    ├── intake.py
    ├── clarify.py
    └── ...
```

---

## 5. Test Specification

### 5.1 Unit Tests

```python
# tests/unit/pipeline/test_stage_executor.py

class TestStageExecutor:
    """Tests for StageExecutor base class."""
    
    def test_execute_calls_lifecycle_methods_in_order(self):
        """Lifecycle methods called: init, validate_input, execute, validate_output, finalize."""
    
    def test_execute_stops_on_input_validation_failure(self):
        """Execution stops if input validation fails."""
    
    def test_execute_stops_on_output_validation_failure(self):
        """Execution stops if output validation fails."""
    
    def test_initialize_failure_stops_execution(self):
        """Non-None return from initialize stops execution."""
    
    def test_escalate_returns_pending_status(self):
        """escalate() returns StageResult with escalation_reason."""
    
    def test_save_artifact_creates_yaml_file(self, tmp_path):
        """_save_artifact creates correct YAML file."""


class TestLLMStageExecutor:
    """Tests for LLMStageExecutor."""
    
    def test_execute_calls_get_prompts_and_parse(self, mock_llm):
        """Execute calls get_system_prompt, get_user_message, parse_response."""
    
    def test_extract_yaml_from_response_handles_code_block(self):
        """YAML in code blocks is extracted correctly."""
    
    def test_extract_yaml_from_response_handles_raw_yaml(self):
        """Raw YAML is parsed correctly."""


class TestContractStageExecutor:
    """Tests for ContractStageExecutor."""
    
    def test_input_mapping_transforms_artifact(self):
        """Input mapping correctly transforms artifact fields."""
    
    def test_output_mapping_transforms_result(self):
        """Output mapping correctly transforms contract output."""


class TestStageArtifact:
    """Tests for StageArtifact."""
    
    def test_to_dict_includes_metadata(self):
        """to_dict includes _artifact_meta."""
    
    def test_from_dict_restores_artifact(self):
        """from_dict correctly restores artifact."""
    
    def test_save_and_load_roundtrip(self, tmp_path):
        """save() and load() produce identical artifact."""
```

### 5.2 Integration Tests

```python
# tests/integration/pipeline/test_stage_execution.py

class TestStageExecution:
    """Integration tests for stage execution."""
    
    def test_llm_stage_produces_artifact(self, mock_llm, tmp_path):
        """LLM-based stage produces valid artifact."""
    
    def test_contract_stage_executes_contract(self, tmp_path):
        """Contract-based stage correctly executes contract."""
    
    def test_stage_saves_artifact_to_disk(self, tmp_path):
        """Stage execution saves artifact to correct location."""
```

---

## 6. Success Criteria

1. **Functional:**
   - [ ] StageExecutor lifecycle works correctly
   - [ ] LLMStageExecutor integrates with MinimalContextExecutor
   - [ ] ContractStageExecutor wraps existing contracts
   - [ ] Artifacts are saved and loadable

2. **Quality:**
   - [ ] Clear separation between stage logic and infrastructure
   - [ ] Easy to implement new stages
   - [ ] Comprehensive error handling

3. **Extensibility:**
   - [ ] New stages only need to implement _execute()
   - [ ] Artifact schema is versioned and evolvable

---

## 7. Dependencies

- **Stage 1:** PipelineController, StageResult, PipelineState
- **Existing:** MinimalContextExecutor, execute_contract

---

*Next: Stage 3 - Intake & Clarify Stages*
