# @spec_file: .agentforge/specs/bridge-mappings-v1.yaml
# @spec_id: bridge-mappings-v1
# @component_id: bridge-mappings-base
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

"""
Pattern Mapping Base Class
==========================

Abstract base class for pattern-to-check mappings.
Each mapping transforms a discovered pattern into conformance checks.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from bridge.domain import (
    CheckTemplate,
    GeneratedCheck,
    MappingContext,
    ConfidenceTier,
)


class PatternMapping(ABC):
    """
    Abstract base class for pattern-to-check mappings.

    Each mapping:
    1. Declares which patterns it handles (pattern_key)
    2. Declares which languages it applies to (languages)
    3. Implements matches() to determine if it should run
    4. Implements get_templates() to return check templates
    5. Optionally overrides generate() for custom logic

    Example:
        class CQRSMediatRMapping(PatternMapping):
            pattern_key = "cqrs"
            languages = ["csharp"]

            def matches(self, context: MappingContext) -> bool:
                return (
                    context.is_pattern_detected("cqrs") and
                    context.get_pattern_primary("cqrs") == "MediatR" and
                    context.get_pattern_confidence("cqrs") >= 0.5
                )

            def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
                return [
                    CheckTemplate(
                        id_template="{zone}-cqrs-command-naming",
                        name="CQRS Command Naming",
                        ...
                    ),
                ]
    """

    # Class-level attributes (override in subclasses)
    pattern_key: str = ""                    # Key in profile patterns dict
    languages: List[str] = []                # Applicable languages
    min_confidence: float = 0.5              # Minimum confidence to generate
    version: str = "1.0"                     # Mapping version for tracking

    @abstractmethod
    def matches(self, context: MappingContext) -> bool:
        """
        Check if this mapping should be applied for the given context.

        Args:
            context: The mapping context with profile data

        Returns:
            True if this mapping should generate checks
        """
        pass

    @abstractmethod
    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """
        Get check templates for this mapping.

        Args:
            context: The mapping context with profile data

        Returns:
            List of check templates to generate
        """
        pass

    def generate(self, context: MappingContext) -> List[GeneratedCheck]:
        """
        Generate checks from this mapping.

        Default implementation:
        1. Checks if mapping matches
        2. Gets templates
        3. Resolves templates to checks with proper enablement

        Override for custom generation logic.

        Args:
            context: The mapping context with profile data

        Returns:
            List of generated checks
        """
        if not self.matches(context):
            return []

        templates = self.get_templates(context)
        checks = []

        for template in templates:
            check = self._template_to_check(template, context)
            if check:
                checks.append(check)

        return checks

    def _template_to_check(
        self,
        template: CheckTemplate,
        context: MappingContext
    ) -> Optional[GeneratedCheck]:
        """Convert a template to a generated check."""
        confidence = context.get_pattern_confidence(self.pattern_key)
        tier = ConfidenceTier.from_score(confidence)

        if not tier.should_generate:
            return None

        zone_name = context.zone_name or "default"
        check_id = template.resolve_id(zone_name)

        # Build applies_to
        applies_to = {}
        if template.applies_to_paths:
            applies_to["paths"] = template.applies_to_paths
        if template.exclude_paths:
            applies_to["exclude_paths"] = template.exclude_paths

        # Determine review reason
        review_reason = template.review_reason
        if tier.needs_review and not review_reason:
            review_reason = f"{tier.value.upper()} confidence ({confidence:.2f}) - verify pattern is intentional"

        return GeneratedCheck(
            id=check_id,
            name=template.name,
            description=template.description,
            check_type=template.check_type,
            enabled=tier.auto_enable,
            severity=template.severity,
            config=template.config,
            applies_to=applies_to,
            source_pattern=self.pattern_key,
            source_confidence=confidence,
            mapping_version=self.version,
            review_required=tier.needs_review,
            review_reason=review_reason,
            fix_hint=template.fix_hint,
        )

    def get_info(self) -> dict:
        """Get metadata about this mapping for display."""
        return {
            "pattern_key": self.pattern_key,
            "languages": self.languages,
            "min_confidence": self.min_confidence,
            "version": self.version,
            "description": self.__class__.__doc__ or "",
        }
