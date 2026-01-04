"""
Validation Mixin
================

Stage input/output validation with contract enforcement.
"""

import logging
from typing import Any, TYPE_CHECKING

from ..state import PipelineState, StageStatus
from ..stage_executor import StageResult

if TYPE_CHECKING:
    from agentforge.core.contracts.enforcer import ContractEnforcer, ViolationSeverity

logger = logging.getLogger(__name__)


class ValidationMixin:
    """Mixin providing validation capabilities for pipeline stages."""

    def _validate_input_with_contracts(
        self, stage_name: str, errors: list[str], enforcer: "ContractEnforcer | None",
        input_artifacts: dict[str, Any], enforce_contracts: bool
    ) -> None:
        """Add contract validation errors to the error list."""
        from agentforge.core.contracts.enforcer import ViolationSeverity

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
        self, stage_name: str, enforcer: "ContractEnforcer | None",
        artifacts: dict[str, Any], enforce_contracts: bool
    ) -> None:
        """Log contract validation issues for output artifacts."""
        from agentforge.core.contracts.enforcer import ViolationSeverity

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
        self, stage_name: str, enforcer: "ContractEnforcer | None",
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
