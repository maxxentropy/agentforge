"""
Lifecycle Mixin
===============

Pipeline lifecycle operations: approve, reject, abort, pause.
"""

import logging

from ..state import PipelineState, PipelineStatus, StageStatus

logger = logging.getLogger(__name__)


class LifecycleMixin:
    """Mixin providing pipeline lifecycle control operations."""

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
