# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_file: specs/pipeline-controller/implementation/phase-3-tdd-stages.yaml
# @spec_file: specs/pipeline-controller/implementation/phase-4-refactor-deliver.yaml
# @spec_id: pipeline-controller-phase2-v1
# @spec_id: pipeline-controller-phase3-v1
# @spec_id: pipeline-controller-phase4-v1
# @component_id: stages-init
# @component_id: stages-init-tdd
# @component_id: stages-init-phase4
# @test_path: tests/unit/pipeline/stages/test_stages_init.py

"""
Pipeline Stages Package
=======================

Stage executors for the pipeline controller.

Design Pipeline Stages (Phase 2):
- INTAKE: Parse and categorize user requests
- CLARIFY: Resolve ambiguities through Q&A
- ANALYZE: Deep codebase analysis with tools
- SPEC: Generate detailed technical specifications

TDD Pipeline Stages (Phase 3):
- RED: Generate failing tests from spec
- GREEN: Implement code to pass tests

Delivery Stages (Phase 4):
- REFACTOR: Code quality improvements
- DELIVER: Git commit and PR creation
"""

from .intake import IntakeExecutor, create_intake_executor
from .clarify import ClarifyExecutor, create_clarify_executor
from .analyze import AnalyzeExecutor, create_analyze_executor
from .spec import SpecExecutor, create_spec_executor
from .red import RedPhaseExecutor, create_red_executor
from .green import GreenPhaseExecutor, create_green_executor
from .refactor import RefactorPhaseExecutor, create_refactor_executor
from .deliver import DeliverPhaseExecutor, DeliveryMode, create_deliver_executor

__all__ = [
    # Design Pipeline Executor classes
    "IntakeExecutor",
    "ClarifyExecutor",
    "AnalyzeExecutor",
    "SpecExecutor",
    # TDD Pipeline Executor classes
    "RedPhaseExecutor",
    "GreenPhaseExecutor",
    # Delivery Pipeline Executor classes
    "RefactorPhaseExecutor",
    "DeliverPhaseExecutor",
    "DeliveryMode",
    # Design Pipeline Factory functions
    "create_intake_executor",
    "create_clarify_executor",
    "create_analyze_executor",
    "create_spec_executor",
    # TDD Pipeline Factory functions
    "create_red_executor",
    "create_green_executor",
    # Delivery Pipeline Factory functions
    "create_refactor_executor",
    "create_deliver_executor",
    # Registration functions
    "register_design_stages",
    "register_tdd_stages",
    "register_delivery_stages",
]


def register_design_stages(registry: "StageExecutorRegistry") -> None:
    """
    Register all design pipeline stages with the given registry.

    This registers INTAKE, CLARIFY, ANALYZE, and SPEC stages
    that make up the design pipeline.

    Args:
        registry: The StageExecutorRegistry to register with
    """
    registry.register("intake", create_intake_executor)
    registry.register("clarify", create_clarify_executor)
    registry.register("analyze", create_analyze_executor)
    registry.register("spec", create_spec_executor)


def register_tdd_stages(registry: "StageExecutorRegistry") -> None:
    """
    Register all TDD pipeline stages with the given registry.

    This registers RED and GREEN stages that make up the TDD pipeline.

    Args:
        registry: The StageExecutorRegistry to register with
    """
    registry.register("red", create_red_executor)
    registry.register("green", create_green_executor)


def register_delivery_stages(registry: "StageExecutorRegistry") -> None:
    """
    Register all delivery pipeline stages with the given registry.

    This registers REFACTOR and DELIVER stages that complete the
    TDD cycle and package the final result.

    Args:
        registry: The StageExecutorRegistry to register with
    """
    registry.register("refactor", create_refactor_executor)
    registry.register("deliver", create_deliver_executor)
