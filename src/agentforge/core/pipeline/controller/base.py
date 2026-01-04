# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-controller
# @test_path: tests/unit/pipeline/test_controller.py

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
from pathlib import Path
from typing import Any

from ..escalation import EscalationType, Escalation, EscalationHandler, generate_escalation_id
from ..registry import StageExecutorRegistry, get_registry
from ..state import (
    PipelineState,
    PipelineStatus,
    create_pipeline_state,
)
from ..state_store import PipelineStateStore
from ..validator import ArtifactValidator

# Contract enforcement imports
from agentforge.core.contracts.draft import ApprovedContracts
from agentforge.core.contracts.enforcer import ContractEnforcer
from agentforge.core.contracts.operations.loader import OperationContractManager
from agentforge.core.contracts.registry import ContractRegistry

from .exceptions import PipelineNotFoundError, PipelineStateError
from .execution_mixin import ExecutionMixin
from .lifecycle_mixin import LifecycleMixin
from .result import PipelineResult
from .validation_mixin import ValidationMixin

logger = logging.getLogger(__name__)


class PipelineController(
    ValidationMixin,
    ExecutionMixin,
    LifecycleMixin,
):
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
        from ..discovery_integration import create_pipeline_context_from_discovery

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

    def _handle_escalation(self, state: PipelineState, result) -> None:
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
