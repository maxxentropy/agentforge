# @spec_file: .agentforge/specs/bridge-mappings-v1.yaml
# @spec_id: bridge-mappings-v1
# @component_id: bridge-mappings-cqrs
# @test_path: tests/unit/tools/bridge/test_registry.py

"""
CQRS/MediatR Pattern Mappings
=============================

Mappings for CQRS pattern detection, particularly MediatR-based implementations.
"""

from typing import List

from bridge.mappings.base import PatternMapping
from bridge.mappings.registry import MappingRegistry
from bridge.domain import CheckTemplate, MappingContext


@MappingRegistry.register
class CQRSMediatRMapping(PatternMapping):
    """
    CQRS with MediatR implementation.

    Generates checks for:
    - Command naming (ends with 'Command')
    - Query naming (ends with 'Query')
    - Handler naming (ends with 'Handler')
    - Commands implement IRequest
    """

    pattern_key = "cqrs"
    languages = ["csharp"]
    min_confidence = 0.5
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when CQRS/MediatR pattern is detected."""
        if not context.is_pattern_detected("cqrs"):
            # Also check for mediatr_cqrs pattern key
            if not context.is_pattern_detected("mediatr_cqrs"):
                return False
            return context.get_pattern_confidence("mediatr_cqrs") >= self.min_confidence

        confidence = context.get_pattern_confidence("cqrs")
        if confidence < self.min_confidence:
            return False

        # Check for MediatR specifically or any CQRS
        primary = context.get_pattern_primary("cqrs")
        return primary in ("MediatR", None) or context.has_framework("MediatR")

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get CQRS check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-cqrs-command-naming",
                name="CQRS Command Naming",
                description="Commands should end with 'Command'",
                check_type="naming",
                severity="minor",
                config={
                    "pattern": ".*Command$",
                    "symbol_type": "class",
                },
                applies_to_paths=[
                    "**/Commands/**/*.cs",
                    "**/Application/**/Commands/**/*.cs",
                ],
            ),
            CheckTemplate(
                id_template="{zone}-cqrs-query-naming",
                name="CQRS Query Naming",
                description="Queries should end with 'Query'",
                check_type="naming",
                severity="minor",
                config={
                    "pattern": ".*Query$",
                    "symbol_type": "class",
                },
                applies_to_paths=[
                    "**/Queries/**/*.cs",
                    "**/Application/**/Queries/**/*.cs",
                ],
            ),
            CheckTemplate(
                id_template="{zone}-cqrs-handler-naming",
                name="CQRS Handler Naming",
                description="Handlers should end with 'Handler'",
                check_type="naming",
                severity="minor",
                config={
                    "pattern": ".*Handler$",
                    "symbol_type": "class",
                },
                applies_to_paths=[
                    "**/Handlers/**/*.cs",
                    "**/*Handler.cs",
                ],
            ),
            CheckTemplate(
                id_template="{zone}-cqrs-command-interface",
                name="Commands Implement IRequest",
                description="Commands must implement IRequest<TResponse>",
                check_type="ast",
                severity="warning",
                config={
                    "class_pattern": ".*Command$",
                    "must_implement": ["IRequest", "IRequest<"],
                },
                applies_to_paths=[
                    "**/Commands/**/*.cs",
                ],
            ),
        ]


@MappingRegistry.register
class CQRSGenericMapping(PatternMapping):
    """
    Generic CQRS pattern (non-MediatR).

    Generates basic naming checks only.
    """

    pattern_key = "cqrs"
    languages = ["csharp", "typescript"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when CQRS is detected but NOT MediatR."""
        if not context.is_pattern_detected("cqrs"):
            return False

        confidence = context.get_pattern_confidence("cqrs")
        if confidence < self.min_confidence:
            return False

        # Only match if NOT MediatR (that's handled by CQRSMediatRMapping)
        primary = context.get_pattern_primary("cqrs")
        return primary not in ("MediatR",) and not context.has_framework("MediatR")

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get generic CQRS check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-cqrs-command-naming",
                name="CQRS Command Naming",
                description="Commands should end with 'Command'",
                check_type="naming",
                severity="minor",
                config={
                    "pattern": ".*Command$",
                    "symbol_type": "class",
                },
                applies_to_paths=["**/*.cs", "**/*.ts"],
            ),
            CheckTemplate(
                id_template="{zone}-cqrs-handler-naming",
                name="CQRS Handler Naming",
                description="Handlers should end with 'Handler'",
                check_type="naming",
                severity="minor",
                config={
                    "pattern": ".*Handler$",
                    "symbol_type": "class",
                },
                applies_to_paths=["**/*.cs", "**/*.ts"],
            ),
        ]
