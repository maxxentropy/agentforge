# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @component_id: pipeline-controller
# @component_id: pipeline-result
# @test_path: tests/unit/pipeline/test_controller.py
# @test_path: tests/unit/pipeline/test_controller_api.py

"""
Pipeline Controller
===================

Main orchestration engine for pipeline execution.

Public API:
    execute(request, template, config) -> PipelineResult  # Create and run
    resume(pipeline_id) -> PipelineResult                 # Resume paused
    approve(pipeline_id) -> bool                          # Approve escalation
    reject(pipeline_id, reason) -> bool                   # Reject escalation
    abort(pipeline_id, reason) -> bool                    # Abort pipeline
    list_pipelines(status, limit) -> List[PipelineState]  # Query history
    provide_feedback(pipeline_id, feedback) -> None       # Store feedback
    get_status(pipeline_id) -> PipelineState              # Get current state
    pause(pipeline_id) -> bool                            # Pause running
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .escalation import (
    Escalation,
    EscalationHandler,
    EscalationType,
    generate_escalation_id,
)
from .registry import StageExecutorRegistry, StageNotFoundError, get_registry
from .stage_executor import StageContext, StageResult
from .state import (
    PipelineState,
    PipelineStatus,
    StageStatus,
    create_pipeline_state,
)
from .state_store import PipelineStateStore
from .validator import ArtifactValidator

# Contract enforcement imports
from agentforge.core.contracts.enforcer import (
    ContractEnforcer,
    ValidationResult,
    ViolationSeverity,
)
from agentforge.core.contracts.operations.loader import OperationContractManager
from agentforge.core.contracts.registry import ContractRegistry
from agentforge.core.contracts.draft import ApprovedContracts

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Base exception for pipeline errors."""

    pass


class PipelineNotFoundError(PipelineError):
    """Raised when a pipeline is not found."""

    pass


class PipelineStateError(PipelineError):
    """Raised when pipeline is in invalid state for operation."""

    pass


@dataclass
class PipelineResult:
    """
    Result object returned by execute() and resume().

    Provides consistent interface for CLI to consume.
    """

    success: bool
    pipeline_id: str
    stages_completed: list[str] = field(default_factory=list)
    current_stage: str | None = None
    deliverable: dict[str, Any] | None = None
    error: str | None = None
    total_duration_seconds: float = 0.0

    @classmethod
    def from_state(cls, state: PipelineState, start_time: float) -> "PipelineResult":
        """Create PipelineResult from PipelineState."""
        completed_stages = [
            name for name, stage in state.stages.items()
            if stage.status == StageStatus.COMPLETED
        ]

        # Get deliverable from deliver stage if completed
        deliverable = None
        if "deliver" in state.stages:
            deliver_stage = state.stages["deliver"]
            if deliver_stage.status == StageStatus.COMPLETED:
                deliverable = deliver_stage.artifacts

        # Determine error message
        error = None
        if state.status == PipelineStatus.FAILED:
            for _name, stage in state.stages.items():
                if stage.status == StageStatus.FAILED and stage.error:
                    error = stage.error
                    break

        return cls(
            success=state.status == PipelineStatus.COMPLETED,
            pipeline_id=state.pipeline_id,
            stages_completed=completed_stages,
            current_stage=state.current_stage,
            deliverable=deliverable,
            error=error,
            total_duration_seconds=time.time() - start_time,
        )


class PipelineController:
    """
    Main orchestration engine for pipeline execution.

    Manages pipeline lifecycle and stage execution.
    """

    def __init__(
        self,
        project_path: Path,
        state_store: PipelineStateStore | None = None,
        registry: StageExecutorRegistry | None = None,
        escalation_handler: EscalationHandler | None = None,
        config: dict[str, Any] | None = None,
        operation_manager: OperationContractManager | None = None,
    ):
        """
        Initialize pipeline controller.

        Args:
            project_path: Root path for the project
            state_store: Optional custom state store (creates default if None)
            registry: Optional custom registry (uses global if None)
            escalation_handler: Optional custom escalation handler
            config: Optional default configuration for pipelines
            operation_manager: Optional operation contract manager
        """
        self.project_path = Path(project_path)
        self.state_store = state_store or PipelineStateStore(self.project_path)
        self.registry = registry or get_registry()
        self.escalation_handler = escalation_handler or EscalationHandler(
            self.project_path
        )
        self.validator = ArtifactValidator()
        self.config = config or {}

        # Contract enforcement
        self.operation_manager = operation_manager or OperationContractManager()
        self.contract_registry = ContractRegistry(self.project_path)
        self._contract_enforcer: ContractEnforcer | None = None

    # =========================================================================
    # Public API
    # =========================================================================

    def execute_with_discovery(
        self,
        request: str,
        profile: Any,  # CodebaseProfile from discovery
        template: str = "implement",
        config: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """
        Create and execute a pipeline with brownfield discovery context.

        This connects the brownfield discovery system to pipeline execution,
        providing language-aware validation and codebase context.

        Args:
            request: User request describing what to build
            profile: CodebaseProfile from brownfield discovery
            template: Pipeline template (implement, design, test, fix)
            config: Optional configuration overrides

        Returns:
            PipelineResult with execution outcome
        """
        from .discovery_integration import create_pipeline_context_from_discovery

        # Create pipeline context from discovery
        discovery_context = create_pipeline_context_from_discovery(
            profile, self.project_path
        )

        # Merge discovery context with provided config
        # Enable strict schema validation when using discovery (we have full context)
        merged_config = {
            **self.config,
            **(config or {}),
            **discovery_context,
            "strict_schema_validation": True,  # Enable with discovery
        }

        logger.info(
            f"Executing pipeline with discovery context: "
            f"language={discovery_context.get('primary_language')}, "
            f"frameworks={discovery_context.get('frameworks')}"
        )

        return self.execute(request, template, merged_config)

    def execute(
        self,
        request: str,
        template: str = "implement",
        config: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """
        Create and execute a new pipeline.

        Args:
            request: User request describing what to build
            template: Pipeline template (implement, design, test, fix)
            config: Optional configuration overrides

        Returns:
            PipelineResult with execution outcome
        """
        start_time = time.time()

        merged_config = {**self.config, **(config or {})}
        state = self._create(request, template, merged_config)
        state = self._run(state)

        return PipelineResult.from_state(state, start_time)

    def resume(self, pipeline_id: str) -> PipelineResult:
        """
        Resume a paused pipeline.

        Args:
            pipeline_id: ID of pipeline to resume

        Returns:
            PipelineResult with execution outcome

        Raises:
            PipelineNotFoundError: If pipeline not found
            PipelineStateError: If pipeline cannot be resumed
        """
        start_time = time.time()

        state = self._load_or_raise(pipeline_id)

        if not state.can_resume():
            raise PipelineStateError(
                f"Pipeline {pipeline_id} cannot be resumed from status: "
                f"{state.status.value}"
            )

        # Check for pending escalations
        pending = self.escalation_handler.get_pending(pipeline_id)
        if pending:
            raise PipelineStateError(
                f"Pipeline {pipeline_id} has {len(pending)} pending escalations. "
                "Resolve them before resuming."
            )

        state.status = PipelineStatus.RUNNING
        self.state_store.save(state)
        logger.info(f"Resumed pipeline {pipeline_id}")

        state = self._run(state)
        return PipelineResult.from_state(state, start_time)

    def approve(self, pipeline_id: str) -> bool:
        """
        Approve pending escalation and continue pipeline.

        Args:
            pipeline_id: ID of pipeline to approve

        Returns:
            True if approval succeeded, False otherwise
        """
        # Use transaction for atomic load-modify-save
        with self.state_store.transaction(pipeline_id):
            state = self.state_store.load(pipeline_id)
            if not state:
                logger.warning(f"Pipeline not found for approval: {pipeline_id}")
                return False

            if state.status != PipelineStatus.WAITING_APPROVAL:
                logger.warning(f"Pipeline {pipeline_id} is not waiting for approval")
                return False

            pending = self.escalation_handler.get_pending(pipeline_id)
            if not pending:
                logger.warning(f"No pending escalations for pipeline {pipeline_id}")
                return False

            escalation_id = pending[0].escalation_id
            self.escalation_handler.resolve(escalation_id, "approved")

            state.status = PipelineStatus.RUNNING
            next_stage = state.get_next_stage()
            if next_stage:
                state.current_stage = next_stage
            else:
                state.status = PipelineStatus.COMPLETED

            self.state_store.save(state)
            logger.info(f"Approved escalation {escalation_id} for pipeline {pipeline_id}")

        if state.status == PipelineStatus.RUNNING:
            self._run(state)

        return True

    def reject(self, pipeline_id: str, reason: str = "Rejected") -> bool:
        """
        Reject pending escalation and abort pipeline.

        Args:
            pipeline_id: ID of pipeline
            reason: Rejection reason

        Returns:
            True if rejection succeeded, False otherwise
        """
        # Use transaction for atomic load-modify-save
        with self.state_store.transaction(pipeline_id):
            state = self.state_store.load(pipeline_id)
            if not state:
                logger.warning(f"Pipeline not found for rejection: {pipeline_id}")
                return False

            if state.status != PipelineStatus.WAITING_APPROVAL:
                logger.warning(f"Pipeline {pipeline_id} is not waiting for approval")
                return False

            pending = self.escalation_handler.get_pending(pipeline_id)
            if not pending:
                logger.warning(f"No pending escalations for pipeline {pipeline_id}")
                return False

            escalation_id = pending[0].escalation_id
            self.escalation_handler.reject(escalation_id, reason)

            state.status = PipelineStatus.ABORTED
            self.state_store.save(state)
            logger.info(f"Rejected escalation {escalation_id}, aborted pipeline {pipeline_id}")

        return True

    def abort(self, pipeline_id: str, reason: str = "Aborted") -> bool:
        """
        Abort a running pipeline.

        Args:
            pipeline_id: ID of pipeline to abort
            reason: Abort reason

        Returns:
            True if abort succeeded, False if not found or already terminal
        """
        # Use transaction for atomic load-modify-save
        with self.state_store.transaction(pipeline_id):
            state = self.state_store.load(pipeline_id)
            if not state:
                logger.warning(f"Pipeline not found for abort: {pipeline_id}")
                return False

            if state.is_terminal():
                logger.warning(
                    f"Pipeline {pipeline_id} is already in terminal state: "
                    f"{state.status.value}"
                )
                return False

            state.status = PipelineStatus.ABORTED

            if state.current_stage:
                stage_state = state.get_stage(state.current_stage)
                if stage_state.status == StageStatus.RUNNING:
                    stage_state.mark_failed(reason)

            self.state_store.save(state)
            logger.info(f"Aborted pipeline {pipeline_id}: {reason}")

        return True

    def pause(self, pipeline_id: str) -> bool:
        """
        Pause a running pipeline.

        Args:
            pipeline_id: ID of pipeline to pause

        Returns:
            True if paused, False if not found or not running
        """
        # Use transaction for atomic load-modify-save
        with self.state_store.transaction(pipeline_id):
            state = self.state_store.load(pipeline_id)
            if not state:
                logger.warning(f"Pipeline not found for pause: {pipeline_id}")
                return False

            if state.status != PipelineStatus.RUNNING:
                logger.warning(f"Pipeline {pipeline_id} is not running, cannot pause")
                return False

            state.status = PipelineStatus.PAUSED
            self.state_store.save(state)
            logger.info(f"Paused pipeline {pipeline_id}")

        return True

    def list_pipelines(
        self,
        status: PipelineStatus | None = None,
        limit: int = 10,
    ) -> list[PipelineState]:
        """
        List pipelines with optional filtering.

        Args:
            status: Filter by status (None = all)
            limit: Maximum number to return

        Returns:
            List of PipelineState objects, newest first
        """
        return self.state_store.list(status=status, limit=limit)

    def provide_feedback(self, pipeline_id: str, feedback: str) -> None:
        """
        Store feedback for pipeline.

        Args:
            pipeline_id: Pipeline to provide feedback for
            feedback: Human feedback text

        Raises:
            PipelineNotFoundError: If pipeline not found
        """
        state = self._load_or_raise(pipeline_id)

        if "feedback_history" not in state.config:
            state.config["feedback_history"] = []

        state.config["feedback_history"].append(feedback)
        state.config["feedback"] = feedback

        self.state_store.save(state)
        logger.info(f"Stored feedback for pipeline {pipeline_id}")

    def get_status(self, pipeline_id: str) -> PipelineState:
        """
        Get current pipeline status.

        Args:
            pipeline_id: ID of pipeline

        Returns:
            Current PipelineState

        Raises:
            PipelineNotFoundError: If pipeline not found
        """
        return self._load_or_raise(pipeline_id)

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _create(
        self,
        request: str,
        template: str,
        config: dict[str, Any],
    ) -> PipelineState:
        """Create a new pipeline."""
        state = create_pipeline_state(
            request=request,
            project_path=self.project_path,
            template=template,
            config=config,
        )
        self.state_store.save(state)
        logger.info(f"Created pipeline {state.pipeline_id} with template '{template}'")
        return state

    def _load_or_raise(self, pipeline_id: str) -> PipelineState:
        """Load pipeline state or raise PipelineNotFoundError."""
        state = self.state_store.load(pipeline_id)
        if not state:
            raise PipelineNotFoundError(f"Pipeline not found: {pipeline_id}")
        return state

    def _get_contract_enforcer(
        self, state: PipelineState
    ) -> ContractEnforcer | None:
        """Get or create contract enforcer for a pipeline.

        Looks up approved contracts for the pipeline's request_id and
        creates an enforcer if contracts exist.

        Args:
            state: Pipeline state

        Returns:
            ContractEnforcer if contracts exist, None otherwise
        """
        # Check if we already have a cached enforcer
        if self._contract_enforcer is not None:
            return self._contract_enforcer

        # Look for contracts associated with this pipeline
        request_id = state.config.get("request_id") or state.config.get("contract_id")
        if request_id:
            contracts = self.contract_registry.get_for_request(request_id)
            if contracts:
                self._contract_enforcer = ContractEnforcer(
                    contracts, self.operation_manager
                )
                return self._contract_enforcer

        # Check if explicit contracts were provided in config
        contract_set_id = state.config.get("contract_set_id")
        if contract_set_id:
            contracts = self.contract_registry.get(contract_set_id)
            if contracts:
                self._contract_enforcer = ContractEnforcer(
                    contracts, self.operation_manager
                )
                return self._contract_enforcer

        # No approved contracts - create a minimal enforcer for operation rules only
        # This allows operation contracts to be enforced even without task contracts
        if state.config.get("enforce_operation_contracts", True):
            # Create a minimal ApprovedContracts with no stage contracts
            # but still use operation manager for tool usage rules
            minimal_contracts = ApprovedContracts(
                contract_set_id="operation-only",
                draft_id="none",
                request_id="none",
                stage_contracts=[],
            )
            self._contract_enforcer = ContractEnforcer(
                minimal_contracts, self.operation_manager
            )
            return self._contract_enforcer

        return None

    def _update_stage_state(self, state: PipelineState, result: StageResult) -> None:
        """Update stage state based on execution result."""
        stage_state = state.get_stage(state.current_stage)
        if result.is_success():
            stage_state.mark_completed(result.artifacts)
        elif result.is_failed():
            stage_state.mark_failed(result.error or "Unknown error")
            state.status = PipelineStatus.FAILED
        elif result.status == StageStatus.SKIPPED:
            stage_state.mark_skipped(result.artifacts.get("skip_reason"))

    def _advance_to_next_stage(self, state: PipelineState, result: StageResult) -> None:
        """Advance pipeline to next stage or mark complete."""
        next_stage = self._get_next_stage(state, result)
        if next_stage:
            state.current_stage = next_stage
        else:
            if state.status == PipelineStatus.RUNNING:
                state.status = PipelineStatus.COMPLETED
            state.current_stage = None

    def _run(self, state: PipelineState) -> PipelineState:
        """
        Execute pipeline stages until completion or pause.

        Args:
            state: Pipeline state to execute

        Returns:
            Updated PipelineState
        """
        pipeline_id = state.pipeline_id

        if state.is_terminal():
            raise PipelineStateError(
                f"Pipeline {pipeline_id} is in terminal state: {state.status.value}"
            )

        if state.status == PipelineStatus.PENDING:
            state.status = PipelineStatus.RUNNING
            state.current_stage = state.get_next_stage()
            self.state_store.save(state)

        while state.status == PipelineStatus.RUNNING and state.current_stage is not None:
            result = self._execute_stage(state, state.current_stage)
            self._update_stage_state(state, result)

            if result.needs_escalation():
                self._handle_escalation(state, result)
                self.state_store.save(state)
                break

            self._advance_to_next_stage(state, result)
            self.state_store.save(state)

            if state.status != PipelineStatus.RUNNING:
                break

        logger.info(
            f"Pipeline {pipeline_id} execution stopped: "
            f"status={state.status.value}, stage={state.current_stage}"
        )
        return state

    def _validate_input_with_contracts(
        self, stage_name: str, errors: list[str], enforcer: ContractEnforcer | None,
        input_artifacts: dict[str, Any], enforce_contracts: bool
    ) -> None:
        """Add contract validation errors to the error list."""
        if not enforcer or not enforce_contracts:
            return
        contract_result = enforcer.validate_stage_input(stage_name, input_artifacts)
        if not contract_result.valid:
            for violation in contract_result.violations:
                if violation.severity == ViolationSeverity.ERROR:
                    errors.append(f"[{violation.rule_id}] {violation.message}")
                else:
                    logger.warning(f"Contract warning for {stage_name}: {violation.message}")

    def _validate_output_with_contracts(
        self, stage_name: str, enforcer: ContractEnforcer | None,
        artifacts: dict[str, Any], enforce_contracts: bool
    ) -> None:
        """Log contract validation issues for output artifacts."""
        if not enforcer or not enforce_contracts:
            return
        contract_result = enforcer.validate_stage_output(stage_name, artifacts)
        if not contract_result.valid:
            for violation in contract_result.violations:
                if violation.severity == ViolationSeverity.ERROR:
                    logger.error(f"Contract violation in {stage_name}: {violation.message}")
                else:
                    logger.warning(f"Contract warning for {stage_name}: {violation.message}")

    def _check_contract_escalation_triggers(
        self, stage_name: str, enforcer: ContractEnforcer | None,
        artifacts: dict[str, Any], config: dict[str, Any]
    ) -> StageResult | None:
        """Check contract escalation triggers and return escalation result if triggered."""
        if not enforcer:
            return None
        escalation_context = {"artifacts": artifacts, "stage_name": stage_name, **config}
        for check in enforcer.check_escalation_triggers(stage_name, escalation_context):
            if check.triggered and check.trigger and check.trigger.severity == "blocking":
                logger.info(f"Contract escalation trigger fired: {check.trigger.trigger_id}")
                return StageResult(
                    status=StageStatus.PENDING, artifacts=artifacts,
                    escalation={
                        "type": "contract_escalation",
                        "message": check.trigger.prompt or check.trigger.condition,
                        "context": {"trigger_id": check.trigger.trigger_id, "rationale": check.trigger.rationale},
                    },
                )
        return None

    def _validate_stage_input(
        self, state: PipelineState, stage_name: str, executor, input_artifacts: dict
    ) -> list[str]:
        """Validate stage input and return list of errors."""
        errors = executor.validate_input(input_artifacts)

        if state.config.get("strict_schema_validation", False):
            errors.extend(self.validator.validate_stage_input(stage_name, input_artifacts))

        enforcer = self._get_contract_enforcer(state)
        enforce_contracts = state.config.get("enforce_contracts", True)
        self._validate_input_with_contracts(
            stage_name, errors, enforcer, input_artifacts, enforce_contracts
        )
        return errors

    def _validate_stage_output(
        self, state: PipelineState, stage_name: str, artifacts: dict
    ) -> None:
        """Validate stage output against schema and contracts."""
        if state.config.get("strict_schema_validation", False):
            output_errors = self.validator.validate_stage_output(stage_name, artifacts)
            language = state.config.get("primary_language")
            if language:
                output_errors.extend(
                    self.validator.validate_stage_output_for_language(
                        stage_name, artifacts, language
                    )
                )
            if output_errors:
                logger.warning(f"Output validation warnings for stage {stage_name}: {output_errors}")

        enforcer = self._get_contract_enforcer(state)
        enforce_contracts = state.config.get("enforce_contracts", True)
        if enforce_contracts:
            self._validate_output_with_contracts(
                stage_name, enforcer, artifacts, enforce_contracts
            )

    def _check_output_escalation(
        self, state: PipelineState, stage_name: str, artifacts: dict
    ) -> StageResult | None:
        """Check for contract escalation triggers after stage output."""
        enforce_contracts = state.config.get("enforce_contracts", True)
        if not enforce_contracts:
            return None
        enforcer = self._get_contract_enforcer(state)
        return self._check_contract_escalation_triggers(
            stage_name, enforcer, artifacts, state.config
        )

    def _execute_stage(self, state: PipelineState, stage_name: str) -> StageResult:
        """Execute a single stage."""
        logger.info(f"Executing stage '{stage_name}' for pipeline {state.pipeline_id}")

        stage_state = state.get_stage(stage_name)
        stage_state.mark_running()
        self.state_store.save(state)

        try:
            executor = self.registry.get(stage_name)
        except StageNotFoundError as e:
            logger.error(f"Stage executor not found: {stage_name}")
            return StageResult.failed(str(e))

        input_artifacts = state.collect_artifacts()
        errors = self._validate_stage_input(state, stage_name, executor, input_artifacts)

        if errors:
            logger.error(f"Input validation failed for stage {stage_name}: {errors}")
            return StageResult.failed(f"Input validation failed: {'; '.join(errors)}")

        context = StageContext(
            pipeline_id=state.pipeline_id,
            stage_name=stage_name,
            project_path=state.project_path,
            input_artifacts=input_artifacts,
            config=state.config,
            state_store=self.state_store,
            request=state.request,
        )

        try:
            result = executor.execute(context)
        except Exception as e:
            logger.exception(f"Stage {stage_name} raised exception")
            return StageResult.failed(f"Stage execution error: {e}")

        if result.is_success():
            self._validate_stage_output(state, stage_name, result.artifacts)
            escalation_result = self._check_output_escalation(state, stage_name, result.artifacts)
            if escalation_result:
                return escalation_result

        logger.info(f"Stage '{stage_name}' completed with status: {result.status.value}")
        return result

    def _get_next_stage(self, state: PipelineState, result: StageResult) -> str | None:
        """Determine next stage based on result."""
        if result.next_stage:
            if result.next_stage in state.stage_order:
                return result.next_stage
            logger.warning(f"Requested next stage '{result.next_stage}' not in pipeline")

        if result.is_failed():
            return None

        return state.get_next_stage()

    def _handle_escalation(self, state: PipelineState, result: StageResult) -> None:
        """Create escalation record and pause pipeline."""
        escalation_data = result.escalation
        if not escalation_data:
            return

        escalation = Escalation(
            escalation_id=generate_escalation_id(),
            pipeline_id=state.pipeline_id,
            stage_name=state.current_stage,
            type=EscalationType(escalation_data.get("type", "approval_required")),
            message=escalation_data.get("message", "Human input required"),
            options=escalation_data.get("options"),
            context=escalation_data.get("context", {}),
        )

        self.escalation_handler.create(escalation)
        state.status = PipelineStatus.WAITING_APPROVAL

        logger.info(
            f"Pipeline {state.pipeline_id} paused for escalation: "
            f"{escalation.escalation_id}"
        )
