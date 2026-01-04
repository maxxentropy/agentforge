"""
Execution Mixin
===============

Stage execution and pipeline run loop.
"""

import logging
from typing import Any

from ..registry import StageNotFoundError
from ..stage_executor import StageContext, StageResult
from ..state import PipelineState, PipelineStatus, StageStatus
from .exceptions import PipelineStateError

logger = logging.getLogger(__name__)


class ExecutionMixin:
    """Mixin providing stage execution capabilities."""

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
