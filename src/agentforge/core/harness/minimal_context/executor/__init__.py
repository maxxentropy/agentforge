# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: minimal-context-executor
# @test_path: tests/unit/harness/test_minimal_context.py

"""
Minimal Context Executor Package
================================

Executes agent steps with stateless, bounded context.
Each step is a fresh conversation with exactly 2 messages.

Key guarantees:
- Step 1 and Step 100 use same token count (±10%)
- No step exceeds ~4K tokens
- All state recoverable from disk after crash
- Rate limits never exceeded

Module Structure:
- base.py: MinimalContextExecutor main class
- phase_mixin.py: Phase machine management
- llm_mixin.py: LLM interaction and parsing
- run_mixin.py: Run lifecycle and loop detection
- native_mixin.py: Native Anthropic tool execution
- helpers.py: Standalone helper functions
- step_outcome.py: StepOutcome re-export
"""

from .base import (
    ActionExecutor,
    MinimalContextExecutor,
    create_executor,
    should_use_native_tools,
)
from .step_outcome import StepOutcome

# Re-export AdaptiveBudget from sibling module for backwards compatibility
from ..adaptive_budget import AdaptiveBudget

# For backwards compatibility, also export helper functions
from .helpers import (
    convert_actions_to_dicts,
    determine_final_status,
    determine_target_phase_legacy,
    determine_target_phase_with_machine,
    load_facts_for_loop_detection,
)

# Backwards-compatible aliases with underscore prefix
_determine_target_phase_legacy = determine_target_phase_legacy
_determine_target_phase_with_machine = determine_target_phase_with_machine
_convert_actions_to_dicts = convert_actions_to_dicts
_load_facts_for_loop_detection = load_facts_for_loop_detection
_determine_final_status = determine_final_status

__all__ = [
    # Main exports
    "MinimalContextExecutor",
    "StepOutcome",
    "ActionExecutor",
    "AdaptiveBudget",
    "create_executor",
    "should_use_native_tools",
    # Helper functions
    "determine_target_phase_legacy",
    "determine_target_phase_with_machine",
    "convert_actions_to_dicts",
    "load_facts_for_loop_detection",
    "determine_final_status",
    # Backwards-compatible aliases
    "_determine_target_phase_legacy",
    "_determine_target_phase_with_machine",
    "_convert_actions_to_dicts",
    "_load_facts_for_loop_detection",
    "_determine_final_status",
]
