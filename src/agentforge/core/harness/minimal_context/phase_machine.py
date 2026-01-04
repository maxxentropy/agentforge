# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: phase-machine
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Phase Machine
=============

Explicit state machine for task phase management with guards and transitions.

Key principles:
1. Explicit transitions: Every phase change must go through a defined transition
2. Guards: Preconditions that must be true before transition
3. Max steps: Hard limits per phase prevent getting stuck
4. Phase-specific success: Clear criteria for phase completion

Phase Diagram:
                          ┌────────────┐
                          │   INIT     │
                          └─────┬──────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               │
          ┌──────────┐    ┌──────────┐         │
          │ ANALYZE  │───▶│   PLAN   │         │
          └────┬─────┘    └────┬─────┘         │
               │               │               │
               └───────┬───────┘               │
                       │                       │
                       ▼                       │
                ┌──────────┐◄──────────────────┘
                │IMPLEMENT │◄─────────┐
                └────┬─────┘          │
                     │                │
                     ▼                │
                ┌──────────┐          │
                │  VERIFY  │──────────┘
                └────┬─────┘     (fails)
                     │
                     ▼ (passes)
                ┌──────────┐
                │ COMPLETE │
                └──────────┘

  [Any phase can transition to FAILED or ESCALATED]
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .context_models import PhaseState


class Phase(str, Enum):
    """Task execution phases."""

    INIT = "init"
    ANALYZE = "analyze"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    COMPLETE = "complete"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class PhaseContext:
    """
    Context available to guards and transitions.

    Contains all information needed to evaluate whether a transition
    should be allowed.
    """

    current_phase: Phase
    steps_in_phase: int
    total_steps: int
    verification_passing: bool
    tests_passing: bool
    files_modified: list[str]
    facts: list[Any]  # List[Fact] from context_models
    last_action: str | None = None
    last_action_result: str | None = None

    def has_modifications(self) -> bool:
        return len(self.files_modified) > 0

    def has_fact_of_type(self, category: str) -> bool:
        return any(
            f.category.value == category for f in self.facts if hasattr(f, "category")
        )


@dataclass(frozen=True)
class Transition:
    """
    A transition between phases.

    Transitions have:
    - from_phase: Source phase
    - to_phase: Target phase
    - guards: List of conditions that must be true
    - description: Human-readable description
    """

    from_phase: Phase
    to_phase: Phase
    guards: tuple = field(default_factory=tuple)  # Tuple of callables
    description: str = ""


@dataclass
class PhaseConfig:
    """Configuration for a single phase."""

    phase: Phase
    max_steps: int
    success_condition: Callable[[PhaseContext], bool]
    failure_condition: Callable[[PhaseContext], bool] | None = None
    description: str = ""


class PhaseMachine:
    """
    State machine for task phase management.

    Provides:
    - Explicit transition definitions
    - Guard evaluation before transitions
    - Max step enforcement per phase
    - Clear success/failure conditions
    """

    def __init__(self):
        self._transitions: dict[Phase, list[Transition]] = {}
        self._phase_configs: dict[Phase, PhaseConfig] = {}
        self._current_phase: Phase = Phase.INIT
        self._steps_in_phase: int = 0
        self._phase_history: list[Phase] = []

        # Initialize with default configuration
        self._setup_default_transitions()
        self._setup_default_phase_configs()

    def _setup_default_transitions(self) -> None:
        """Set up default phase transitions for fix_violation tasks."""
        # Define individual phase transitions
        transitions = [
            # INIT transitions
            (Phase.INIT, Phase.ANALYZE, (), "Begin analysis"),
            (Phase.INIT, Phase.IMPLEMENT,
             (lambda ctx: ctx.has_fact_of_type("code_structure"),),
             "Skip to implement when precomputed analysis available"),
            # ANALYZE transitions
            (Phase.ANALYZE, Phase.PLAN,
             (lambda ctx: ctx.steps_in_phase >= 1, lambda ctx: ctx.has_fact_of_type("code_structure")),
             "Move to planning after analysis"),
            (Phase.ANALYZE, Phase.IMPLEMENT,
             (lambda ctx: ctx.has_fact_of_type("code_structure"),),
             "Skip to implement for simple cases"),
            # PLAN -> IMPLEMENT
            (Phase.PLAN, Phase.IMPLEMENT, (), "Begin implementation"),
            # IMPLEMENT <-> VERIFY
            (Phase.IMPLEMENT, Phase.VERIFY,
             (lambda ctx: ctx.has_modifications(),),
             "Verify changes after modification"),
            (Phase.VERIFY, Phase.IMPLEMENT,
             (lambda ctx: not ctx.verification_passing,),
             "Return to implement if verification fails"),
            # VERIFY -> COMPLETE
            (Phase.VERIFY, Phase.COMPLETE,
             (lambda ctx: ctx.verification_passing, lambda ctx: ctx.tests_passing),
             "Complete when all checks pass"),
        ]
        for from_phase, to_phase, guards, desc in transitions:
            self.add_transition(Transition(from_phase, to_phase, guards, desc))

        # Universal transitions: any active phase -> FAILED/ESCALATED
        active_phases = [Phase.INIT, Phase.ANALYZE, Phase.PLAN, Phase.IMPLEMENT, Phase.VERIFY]
        for phase in active_phases:
            self.add_transition(Transition(
                phase, Phase.FAILED,
                (lambda ctx: ctx.last_action_result == "fatal",),
                "Fail on fatal error"))
            self.add_transition(Transition(
                phase, Phase.ESCALATED,
                (lambda ctx: ctx.last_action in ("escalate", "cannot_fix"),),
                "Escalate to human"))

    def _setup_default_phase_configs(self) -> None:
        """Set up default phase configurations."""
        self._phase_configs = {
            Phase.INIT: PhaseConfig(
                phase=Phase.INIT,
                max_steps=2,
                success_condition=lambda ctx: True,  # Always can leave init
                description="Initial setup phase",
            ),
            Phase.ANALYZE: PhaseConfig(
                phase=Phase.ANALYZE,
                max_steps=5,
                success_condition=lambda ctx: ctx.has_fact_of_type("code_structure"),
                description="Understand the code and violation",
            ),
            Phase.PLAN: PhaseConfig(
                phase=Phase.PLAN,
                max_steps=2,
                success_condition=lambda ctx: True,
                description="Plan the fix approach",
            ),
            Phase.IMPLEMENT: PhaseConfig(
                phase=Phase.IMPLEMENT,
                max_steps=15,
                success_condition=lambda ctx: ctx.verification_passing,
                failure_condition=lambda ctx: ctx.steps_in_phase >= 12
                and not ctx.has_modifications(),
                description="Make code changes to fix violation",
            ),
            Phase.VERIFY: PhaseConfig(
                phase=Phase.VERIFY,
                max_steps=5,
                success_condition=lambda ctx: ctx.verification_passing
                and ctx.tests_passing,
                description="Verify fix is complete",
            ),
        }

    def add_transition(self, transition: Transition) -> None:
        """Add a transition to the machine."""
        if transition.from_phase not in self._transitions:
            self._transitions[transition.from_phase] = []
        self._transitions[transition.from_phase].append(transition)

    def configure_phase(self, config: PhaseConfig) -> None:
        """Configure a phase."""
        self._phase_configs[config.phase] = config

    @property
    def current_phase(self) -> Phase:
        return self._current_phase

    @property
    def steps_in_phase(self) -> int:
        return self._steps_in_phase

    @property
    def phase_history(self) -> list[Phase]:
        return list(self._phase_history)

    def can_transition(self, to_phase: Phase, context: PhaseContext) -> bool:
        """Check if transition to target phase is allowed."""
        transitions = self._transitions.get(self._current_phase, [])

        for t in transitions:
            if t.to_phase == to_phase:
                # Check all guards
                if all(guard(context) for guard in t.guards):
                    return True

        return False

    def get_available_transitions(self, context: PhaseContext) -> list[Transition]:
        """Get all currently valid transitions."""
        transitions = self._transitions.get(self._current_phase, [])
        return [t for t in transitions if all(guard(context) for guard in t.guards)]

    def transition(self, to_phase: Phase, context: PhaseContext) -> bool:
        """
        Attempt to transition to a new phase.

        Args:
            to_phase: Target phase
            context: Current execution context

        Returns:
            True if transition succeeded, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self.can_transition(to_phase, context):
            # Log why transition failed for debugging
            logger.debug(
                f"Phase transition blocked: {self._current_phase.value} -> {to_phase.value}. "
                f"Context: steps_in_phase={context.steps_in_phase}, "
                f"has_modifications={context.has_modifications()}, "
                f"verification_passing={context.verification_passing}"
            )
            return False

        logger.info(
            f"Phase transition: {self._current_phase.value} -> {to_phase.value}"
        )
        self._phase_history.append(self._current_phase)
        self._current_phase = to_phase
        self._steps_in_phase = 0

        return True

    def advance_step(self) -> None:
        """Record that a step was taken in current phase."""
        self._steps_in_phase += 1

    def validate_state(self, context: PhaseContext) -> list[str]:
        """
        Validate current phase state and return any issues.

        This is a runtime check to catch phase machine problems early.

        Returns:
            List of issue descriptions (empty if valid)
        """
        issues = []

        # Check 1: Are we stuck in ANALYZE without code_structure facts?
        if self._current_phase == Phase.ANALYZE and self._steps_in_phase >= 3:
            if not context.has_fact_of_type("code_structure"):
                issues.append(
                    f"Stuck in ANALYZE phase (step {self._steps_in_phase}) without "
                    "code_structure facts. Cannot transition to IMPLEMENT. "
                    "Check if precomputed analysis is seeding CODE_STRUCTURE facts."
                )

        # Check 2: Are we in IMPLEMENT without code_structure facts?
        if self._current_phase == Phase.IMPLEMENT:
            if not context.has_fact_of_type("code_structure"):
                issues.append(
                    "In IMPLEMENT phase without code_structure facts. "
                    "Agent may lack understanding of the code to fix."
                )

        # Check 3: Check for blocked transitions
        available = self.get_available_transitions(context)
        config = self._phase_configs.get(self._current_phase)

        if config and self._steps_in_phase >= config.max_steps // 2 and not available:
            issues.append(
                f"No transitions available from {self._current_phase.value} "
                f"after {self._steps_in_phase} steps. May get stuck."
            )

        return issues

    # Standard phase progression order
    _PHASE_ORDER = [
        Phase.INIT, Phase.ANALYZE, Phase.PLAN,
        Phase.IMPLEMENT, Phase.VERIFY, Phase.COMPLETE,
    ]

    def _find_forward_transition(self, context: PhaseContext) -> Phase | None:
        """Find next forward phase transition if available."""
        available = self.get_available_transitions(context)
        current_idx = (
            self._PHASE_ORDER.index(self._current_phase)
            if self._current_phase in self._PHASE_ORDER
            else 0
        )
        for t in available:
            if t.to_phase in self._PHASE_ORDER:
                if self._PHASE_ORDER.index(t.to_phase) > current_idx:
                    return t.to_phase
        return None

    def should_auto_transition(self, context: PhaseContext) -> Phase | None:
        """Check if we should automatically transition based on conditions."""
        config = self._phase_configs.get(self._current_phase)
        if not config:
            return None

        # Max steps exceeded - try any transition, else escalate
        if self._steps_in_phase >= config.max_steps:
            available = self.get_available_transitions(context)
            return available[0].to_phase if available else Phase.ESCALATED

        # Failure condition met
        if config.failure_condition and config.failure_condition(context):
            return Phase.FAILED

        # Success condition met - find forward transition
        if config.success_condition(context):
            return self._find_forward_transition(context)

        return None

    def get_phase_info(self) -> dict[str, Any]:
        """Get current phase information for context."""
        config = self._phase_configs.get(self._current_phase)
        return {
            "current": self._current_phase.value,
            "steps_in_phase": self._steps_in_phase,
            "max_steps": config.max_steps if config else 0,
            "description": config.description if config else "",
            "history": [p.value for p in self._phase_history[-5:]],
        }

    def to_state(self) -> PhaseState:
        """Convert to PhaseState model."""
        return PhaseState(
            current_phase=self._current_phase.value,
            steps_in_phase=self._steps_in_phase,
            phase_history=[p.value for p in self._phase_history],
        )

    @classmethod
    def from_state(cls, state: PhaseState) -> "PhaseMachine":
        """Reconstruct from persisted state."""
        machine = cls()
        machine._current_phase = Phase(state.current_phase)
        machine._steps_in_phase = state.steps_in_phase
        machine._phase_history = [Phase(p) for p in state.phase_history]
        return machine

    def reset(self) -> None:
        """Reset to initial state."""
        self._current_phase = Phase.INIT
        self._steps_in_phase = 0
        self._phase_history = []
