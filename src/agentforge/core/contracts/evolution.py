# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-evolution
# @test_path: tests/unit/contracts/test_evolution.py

"""
Contract Evolution Handler
==========================

Handles contract evolution during execution.

When new information emerges that invalidates contract assumptions,
the evolution handler:
1. Detects the assumption violation
2. Creates an escalation for human review
3. Enables contract updates based on new information

Key Scenarios:
- Assumption was wrong (e.g., expected file doesn't exist)
- Scope changed (e.g., feature request became bug fix)
- New constraints discovered (e.g., security requirement)
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .draft import ApprovedContracts, Assumption, EscalationTrigger, StageContract


class EvolutionViolationType(str, Enum):
    """Type of assumption violation for evolution."""
    ASSUMPTION_WRONG = "assumption_wrong"
    SCOPE_CHANGE = "scope_change"
    NEW_CONSTRAINT = "new_constraint"
    CONTRACT_INCOMPLETE = "contract_incomplete"


@dataclass
class AssumptionViolation:
    """Detected violation of a contract assumption."""

    violation_id: str
    violation_type: EvolutionViolationType
    original_assumption: Assumption | None = None
    actual_situation: str = ""
    discovered_at_stage: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    impact: str = ""
    suggested_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type.value,
            "original_assumption": (
                self.original_assumption.to_dict()
                if self.original_assumption
                else None
            ),
            "actual_situation": self.actual_situation,
            "discovered_at_stage": self.discovered_at_stage,
            "context": self.context,
            "impact": self.impact,
            "suggested_action": self.suggested_action,
        }


@dataclass
class ContractChange:
    """A proposed change to contracts."""

    change_id: str
    change_type: str  # add_rule, modify_stage, add_trigger, etc.
    target: str  # Stage name or trigger ID
    description: str
    details: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass
class ContractEscalation:
    """Escalation for contract re-drafting."""

    escalation_id: str
    violations: list[AssumptionViolation] = field(default_factory=list)
    current_contracts: ApprovedContracts | None = None
    proposed_changes: list[ContractChange] = field(default_factory=list)
    severity: str = "blocking"  # blocking, advisory
    prompt: str = ""  # What to ask human
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    resolved: bool = False
    resolution: str = ""


class ContractEvolutionHandler:
    """Handles contract evolution during execution.

    Detects when contracts need to evolve based on runtime
    information and creates escalations for human review.
    """

    def __init__(self):
        """Initialize evolution handler."""
        self._violation_counter = 0
        self._escalation_counter = 0
        self._change_counter = 0

    def _next_violation_id(self) -> str:
        """Generate next violation ID."""
        self._violation_counter += 1
        return f"AV-{self._violation_counter:03d}"

    def _next_escalation_id(self) -> str:
        """Generate next escalation ID."""
        self._escalation_counter += 1
        return f"ESC-{self._escalation_counter:03d}"

    def _next_change_id(self) -> str:
        """Generate next change ID."""
        self._change_counter += 1
        return f"CHG-{self._change_counter:03d}"

    def detect_assumption_violation(
        self,
        stage: str,
        context: dict[str, Any],
        contracts: ApprovedContracts,
    ) -> AssumptionViolation | None:
        """Detect if execution reveals invalid contract assumptions.

        Args:
            stage: Current stage name
            context: Execution context with actual situation
            contracts: The current approved contracts

        Returns:
            AssumptionViolation if detected, None otherwise
        """
        # Check for explicit assumption violations
        assumptions_to_check = context.get("assumptions", [])
        for assumption_data in assumptions_to_check:
            assumption_id = assumption_data.get("id")
            is_valid = assumption_data.get("valid", True)

            if not is_valid:
                # Find the original assumption
                original = None
                for esc in contracts.escalation_triggers:
                    pass  # Assumptions aren't in escalation triggers

                return AssumptionViolation(
                    violation_id=self._next_violation_id(),
                    violation_type=EvolutionViolationType.ASSUMPTION_WRONG,
                    actual_situation=assumption_data.get("actual", ""),
                    discovered_at_stage=stage,
                    context=context,
                    impact=assumption_data.get("impact", ""),
                    suggested_action=assumption_data.get("action", "Review and update contracts"),
                )

        # Check for scope changes
        detected_scope = context.get("detected_scope")
        expected_scope = context.get("expected_scope")
        if detected_scope and expected_scope and detected_scope != expected_scope:
            return AssumptionViolation(
                violation_id=self._next_violation_id(),
                violation_type=EvolutionViolationType.SCOPE_CHANGE,
                actual_situation=f"Scope changed from {expected_scope} to {detected_scope}",
                discovered_at_stage=stage,
                context=context,
                impact="Contract may not be appropriate for new scope",
                suggested_action="Re-draft contracts for new scope",
            )

        # Check for missing required fields that indicate incomplete contracts
        missing_outputs = context.get("missing_outputs", [])
        if missing_outputs and context.get("indicates_incomplete_contract", False):
            return AssumptionViolation(
                violation_id=self._next_violation_id(),
                violation_type=EvolutionViolationType.CONTRACT_INCOMPLETE,
                actual_situation=f"Missing outputs: {', '.join(missing_outputs)}",
                discovered_at_stage=stage,
                context=context,
                impact="Stage cannot complete without additional outputs",
                suggested_action="Add missing output requirements to contract",
            )

        return None

    def escalate_for_redraft(
        self,
        violation: AssumptionViolation,
        current_contracts: ApprovedContracts,
    ) -> ContractEscalation:
        """Create escalation for contract re-drafting.

        Args:
            violation: The detected violation
            current_contracts: Current approved contracts

        Returns:
            ContractEscalation for human review
        """
        # Generate proposed changes based on violation type
        proposed_changes = self._generate_proposed_changes(violation, current_contracts)

        # Create prompt for human
        prompt = self._generate_escalation_prompt(violation, proposed_changes)

        return ContractEscalation(
            escalation_id=self._next_escalation_id(),
            violations=[violation],
            current_contracts=current_contracts,
            proposed_changes=proposed_changes,
            severity="blocking",
            prompt=prompt,
        )

    def _generate_proposed_changes(
        self,
        violation: AssumptionViolation,
        contracts: ApprovedContracts,
    ) -> list[ContractChange]:
        """Generate proposed changes based on violation."""
        changes = []

        if violation.violation_type == EvolutionViolationType.ASSUMPTION_WRONG:
            # Suggest adding validation rule to catch this
            changes.append(ContractChange(
                change_id=self._next_change_id(),
                change_type="add_trigger",
                target="global",
                description=f"Add check for: {violation.actual_situation}",
                details={"condition": violation.actual_situation},
                reason=f"Assumption violated at {violation.discovered_at_stage}",
            ))

        elif violation.violation_type == EvolutionViolationType.SCOPE_CHANGE:
            # Suggest re-drafting all contracts
            changes.append(ContractChange(
                change_id=self._next_change_id(),
                change_type="redraft",
                target="all",
                description="Re-draft contracts for new scope",
                reason=violation.actual_situation,
            ))

        elif violation.violation_type == EvolutionViolationType.CONTRACT_INCOMPLETE:
            # Suggest adding missing outputs
            stage_name = violation.discovered_at_stage
            missing = violation.context.get("missing_outputs", [])
            changes.append(ContractChange(
                change_id=self._next_change_id(),
                change_type="modify_stage",
                target=stage_name,
                description=f"Add missing outputs: {', '.join(missing)}",
                details={"add_outputs": missing},
                reason="Stage requires additional outputs",
            ))

        elif violation.violation_type == EvolutionViolationType.NEW_CONSTRAINT:
            # Suggest adding validation rule
            changes.append(ContractChange(
                change_id=self._next_change_id(),
                change_type="add_rule",
                target=violation.discovered_at_stage,
                description=f"Add constraint: {violation.actual_situation}",
                reason="New constraint discovered during execution",
            ))

        return changes

    def _generate_escalation_prompt(
        self,
        violation: AssumptionViolation,
        proposed_changes: list[ContractChange],
    ) -> str:
        """Generate prompt for human review."""
        lines = [
            "CONTRACT EVOLUTION REQUIRED",
            "=" * 40,
            "",
            f"Violation Type: {violation.violation_type.value}",
            f"Discovered At: {violation.discovered_at_stage}",
            "",
            "Situation:",
            f"  {violation.actual_situation}",
            "",
            "Impact:",
            f"  {violation.impact}",
            "",
            "Proposed Changes:",
        ]

        for change in proposed_changes:
            lines.append(f"  - {change.description}")
            if change.reason:
                lines.append(f"    Reason: {change.reason}")

        lines.extend([
            "",
            "Options:",
            "  [A] Accept proposed changes",
            "  [M] Modify proposed changes",
            "  [R] Re-draft contracts from scratch",
            "  [C] Continue without changes (risky)",
        ])

        return "\n".join(lines)

    def apply_evolution(
        self,
        original: ApprovedContracts,
        changes: list[ContractChange],
    ) -> ApprovedContracts:
        """Apply evolution changes to create new contract version.

        Args:
            original: Original approved contracts
            changes: Changes to apply

        Returns:
            New ApprovedContracts with changes applied
        """
        # Parse version
        major, minor = map(int, original.version.split("."))
        new_version = f"{major}.{minor + 1}"

        # Generate new ID
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        new_id = f"CONTRACT-{timestamp}"

        # Copy contracts
        new_stage_contracts = [
            StageContract(
                stage_name=sc.stage_name,
                input_schema=sc.input_schema.copy(),
                input_requirements=sc.input_requirements.copy(),
                output_schema=sc.output_schema.copy(),
                output_requirements=sc.output_requirements.copy(),
                validation_rules=sc.validation_rules.copy(),
                escalation_conditions=sc.escalation_conditions.copy(),
                rationale=sc.rationale,
            )
            for sc in original.stage_contracts
        ]

        new_triggers = original.escalation_triggers.copy()
        new_gates = original.quality_gates.copy()

        # Apply changes
        for change in changes:
            if change.change_type == "modify_stage":
                for sc in new_stage_contracts:
                    if sc.stage_name == change.target:
                        add_outputs = change.details.get("add_outputs", [])
                        sc.output_requirements.extend(add_outputs)
                        break

            elif change.change_type == "add_trigger":
                new_triggers.append(EscalationTrigger(
                    trigger_id=f"T-EVOLVED-{len(new_triggers)+1}",
                    condition=change.details.get("condition", change.description),
                    severity="advisory",
                    rationale=change.reason,
                ))

        return ApprovedContracts(
            contract_set_id=new_id,
            draft_id=original.draft_id,
            request_id=original.request_id,
            stage_contracts=new_stage_contracts,
            escalation_triggers=new_triggers,
            quality_gates=new_gates,
            version=new_version,
        )
