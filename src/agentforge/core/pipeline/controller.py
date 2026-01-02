# @spec_file: specs/pipeline-controller/implementation/phase-1-foundation.yaml
# @spec_id: pipeline-controller-phase1-v1
# @component_id: pipeline-controller
# @test_path: tests/unit/pipeline/test_controller.py

"""
Pipeline Controller
===================

Main orchestration engine for pipeline execution.

Responsibilities:
- Create new pipelines from user requests
- Execute stages in order, persisting state after each
- Handle escalations and pauses
- Support resume from saved state
- Manage pipeline lifecycle (abort, approve, reject)
"""

import logging
from pathlib import Path
from typing import Optional

from .escalation import (
    Escalation,
    EscalationHandler,
    EscalationStatus,
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


class PipelineController:
    """
    Main orchestration engine for pipeline execution.

    Manages pipeline lifecycle and stage execution.
    """

    def __init__(
        self,
        project_path: Path,
        state_store: Optional[PipelineStateStore] = None,
        registry: Optional[StageExecutorRegistry] = None,
        escalation_handler: Optional[EscalationHandler] = None,
    ):
        """
        Initialize pipeline controller.

        Args:
            project_path: Root path for the project
            state_store: Optional custom state store (creates default if None)
            registry: Optional custom registry (uses global if None)
            escalation_handler: Optional custom escalation handler
        """
        self.project_path = Path(project_path)
        self.state_store = state_store or PipelineStateStore(self.project_path)
        self.registry = registry or get_registry()
        self.escalation_handler = escalation_handler or EscalationHandler(
            self.project_path
        )
        self.validator = ArtifactValidator()

    def create(
        self,
        request: str,
        template: str = "implement",
        config: dict = None,
    ) -> PipelineState:
        """
        Create a new pipeline from a request.

        Args:
            request: Original user request
            template: Pipeline template (design, implement, test, fix)
            config: Optional configuration overrides

        Returns:
            Created PipelineState
        """
        state = create_pipeline_state(
            request=request,
            project_path=self.project_path,
            template=template,
            config=config,
        )

        self.state_store.save(state)

        logger.info(f"Created pipeline {state.pipeline_id} with template '{template}'")
        return state

    def execute(self, pipeline_id: str) -> PipelineState:
        """
        Execute pipeline until completion or pause.

        Runs stages in order, persisting state after each stage.
        Stops on completion, failure, or escalation.

        Args:
            pipeline_id: ID of pipeline to execute

        Returns:
            Final PipelineState

        Raises:
            PipelineNotFoundError: If pipeline not found
            PipelineStateError: If pipeline cannot be executed
        """
        state = self._load_or_raise(pipeline_id)

        # Check if we can execute
        if state.is_terminal():
            raise PipelineStateError(
                f"Pipeline {pipeline_id} is in terminal state: {state.status.value}"
            )

        # Start pipeline if pending
        if state.status == PipelineStatus.PENDING:
            state.status = PipelineStatus.RUNNING
            state.current_stage = state.get_next_stage()
            self.state_store.save(state)

        # Execute stages until done or paused
        while (
            state.status == PipelineStatus.RUNNING
            and state.current_stage is not None
        ):
            result = self._execute_stage(state, state.current_stage)

            # Update stage state
            stage_state = state.get_stage(state.current_stage)
            if result.is_success():
                stage_state.mark_completed(result.artifacts)
            elif result.is_failed():
                stage_state.mark_failed(result.error or "Unknown error")
                state.status = PipelineStatus.FAILED
            elif result.status == StageStatus.SKIPPED:
                stage_state.mark_skipped(result.artifacts.get("skip_reason"))

            # Handle escalation
            if result.needs_escalation():
                self._handle_escalation(state, result)
                self.state_store.save(state)
                break  # Stop execution, wait for human

            # Transition to next stage
            next_stage = self._transition_stage(state, result)
            if next_stage:
                state.current_stage = next_stage
            else:
                # No next stage - either completed or failed
                if state.status == PipelineStatus.RUNNING:
                    state.status = PipelineStatus.COMPLETED
                state.current_stage = None

            # Persist state after each stage
            self.state_store.save(state)

            # Break if we hit a non-success status
            if state.status != PipelineStatus.RUNNING:
                break

        logger.info(
            f"Pipeline {pipeline_id} execution stopped: "
            f"status={state.status.value}, stage={state.current_stage}"
        )
        return state

    def resume(self, pipeline_id: str) -> PipelineState:
        """
        Resume a paused pipeline.

        Args:
            pipeline_id: ID of pipeline to resume

        Returns:
            Updated PipelineState

        Raises:
            PipelineNotFoundError: If pipeline not found
            PipelineStateError: If pipeline cannot be resumed
        """
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

        # Continue execution
        return self.execute(pipeline_id)

    def approve(
        self,
        pipeline_id: str,
        escalation_id: str,
        response: str = "approved",
    ) -> PipelineState:
        """
        Approve an escalation and continue pipeline.

        Args:
            pipeline_id: ID of pipeline
            escalation_id: ID of escalation to approve
            response: Optional response text

        Returns:
            Updated PipelineState
        """
        state = self._load_or_raise(pipeline_id)

        if state.status != PipelineStatus.WAITING_APPROVAL:
            raise PipelineStateError(
                f"Pipeline {pipeline_id} is not waiting for approval"
            )

        # Resolve the escalation
        self.escalation_handler.resolve(escalation_id, response)

        # Resume pipeline
        state.status = PipelineStatus.RUNNING

        # Move to next stage
        next_stage = state.get_next_stage()
        if next_stage:
            state.current_stage = next_stage
        else:
            state.status = PipelineStatus.COMPLETED

        self.state_store.save(state)

        logger.info(f"Approved escalation {escalation_id} for pipeline {pipeline_id}")

        # Continue execution if not complete
        if state.status == PipelineStatus.RUNNING:
            return self.execute(pipeline_id)

        return state

    def reject(
        self,
        pipeline_id: str,
        escalation_id: str,
        reason: str,
    ) -> PipelineState:
        """
        Reject an escalation.

        Args:
            pipeline_id: ID of pipeline
            escalation_id: ID of escalation to reject
            reason: Rejection reason

        Returns:
            Updated PipelineState (aborted)
        """
        state = self._load_or_raise(pipeline_id)

        if state.status != PipelineStatus.WAITING_APPROVAL:
            raise PipelineStateError(
                f"Pipeline {pipeline_id} is not waiting for approval"
            )

        # Reject the escalation
        self.escalation_handler.reject(escalation_id, reason)

        # Abort the pipeline
        state.status = PipelineStatus.ABORTED
        self.state_store.save(state)

        logger.info(f"Rejected escalation {escalation_id}, aborted pipeline {pipeline_id}")

        return state

    def abort(
        self,
        pipeline_id: str,
        reason: str = None,
    ) -> PipelineState:
        """
        Abort a running pipeline.

        Args:
            pipeline_id: ID of pipeline to abort
            reason: Optional abort reason

        Returns:
            Updated PipelineState
        """
        state = self._load_or_raise(pipeline_id)

        if state.is_terminal():
            raise PipelineStateError(
                f"Pipeline {pipeline_id} is already in terminal state: "
                f"{state.status.value}"
            )

        state.status = PipelineStatus.ABORTED

        # Mark current stage as failed if running
        if state.current_stage:
            stage_state = state.get_stage(state.current_stage)
            if stage_state.status == StageStatus.RUNNING:
                stage_state.mark_failed(reason or "Pipeline aborted")

        self.state_store.save(state)

        logger.info(f"Aborted pipeline {pipeline_id}: {reason}")

        return state

    def pause(self, pipeline_id: str) -> PipelineState:
        """
        Pause a running pipeline.

        Args:
            pipeline_id: ID of pipeline to pause

        Returns:
            Updated PipelineState
        """
        state = self._load_or_raise(pipeline_id)

        if state.status != PipelineStatus.RUNNING:
            raise PipelineStateError(
                f"Pipeline {pipeline_id} is not running, cannot pause"
            )

        state.status = PipelineStatus.PAUSED
        self.state_store.save(state)

        logger.info(f"Paused pipeline {pipeline_id}")

        return state

    def get_status(self, pipeline_id: str) -> PipelineState:
        """
        Get current pipeline status.

        Args:
            pipeline_id: ID of pipeline

        Returns:
            Current PipelineState
        """
        return self._load_or_raise(pipeline_id)

    def _load_or_raise(self, pipeline_id: str) -> PipelineState:
        """Load pipeline state or raise PipelineNotFoundError."""
        state = self.state_store.load(pipeline_id)
        if not state:
            raise PipelineNotFoundError(f"Pipeline not found: {pipeline_id}")
        return state

    def _execute_stage(
        self,
        state: PipelineState,
        stage_name: str,
    ) -> StageResult:
        """
        Execute a single stage.

        Args:
            state: Current pipeline state
            stage_name: Name of stage to execute

        Returns:
            StageResult from executor
        """
        logger.info(f"Executing stage '{stage_name}' for pipeline {state.pipeline_id}")

        # Mark stage as running
        stage_state = state.get_stage(stage_name)
        stage_state.mark_running()
        self.state_store.save(state)

        try:
            # Get executor from registry
            executor = self.registry.get(stage_name)
        except StageNotFoundError as e:
            logger.error(f"Stage executor not found: {stage_name}")
            return StageResult.failed(str(e))

        # Collect input artifacts from prior stages
        input_artifacts = state.collect_artifacts()

        # Validate inputs
        errors = executor.validate_input(input_artifacts)
        if errors:
            logger.error(f"Input validation failed for stage {stage_name}: {errors}")
            return StageResult.failed(f"Input validation failed: {'; '.join(errors)}")

        # Create context
        context = StageContext(
            pipeline_id=state.pipeline_id,
            stage_name=stage_name,
            project_path=state.project_path,
            input_artifacts=input_artifacts,
            config=state.config,
            state_store=self.state_store,
            request=state.request,
        )

        # Execute
        try:
            result = executor.execute(context)
        except Exception as e:
            logger.exception(f"Stage {stage_name} raised exception")
            return StageResult.failed(f"Stage execution error: {e}")

        logger.info(
            f"Stage '{stage_name}' completed with status: {result.status.value}"
        )

        return result

    def _transition_stage(
        self,
        state: PipelineState,
        result: StageResult,
    ) -> Optional[str]:
        """
        Determine next stage based on result.

        Args:
            state: Current pipeline state
            result: Result from last stage

        Returns:
            Next stage name, or None if pipeline is complete
        """
        # Check for explicit next stage override
        if result.next_stage:
            if result.next_stage in state.stage_order:
                return result.next_stage
            logger.warning(
                f"Requested next stage '{result.next_stage}' not in pipeline"
            )

        # Failed stages stop the pipeline
        if result.is_failed():
            return None

        # Get default next stage from pipeline order
        return state.get_next_stage()

    def _handle_escalation(
        self,
        state: PipelineState,
        result: StageResult,
    ) -> None:
        """
        Handle escalation from stage result.

        Creates escalation record and pauses pipeline.
        """
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
