# @spec_file: .agentforge/specs/bridge-mappings-v1.yaml
# @spec_id: bridge-mappings-v1
# @component_id: bridge-mappings-conventions
# @test_path: tests/unit/tools/bridge/test_registry.py

"""
Convention Pattern Mappings
===========================

Mappings for naming conventions, coding standards, and language-specific patterns.
"""

from typing import List

from bridge.mappings.base import PatternMapping
from bridge.mappings.registry import MappingRegistry
from bridge.domain import CheckTemplate, MappingContext


@MappingRegistry.register
class InterfacePrefixMapping(PatternMapping):
    """
    Interface I-prefix convention (C#).

    Enforces interfaces start with 'I' followed by capital letter.
    """

    pattern_key = "interface_prefix"
    languages = ["csharp"]
    min_confidence = 0.7
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when interface prefix convention is detected."""
        # Check for interface_prefix pattern directly
        if context.is_pattern_detected("interface_prefix"):
            return context.get_pattern_confidence("interface_prefix") >= self.min_confidence

        # Check for i_prefix pattern
        if context.is_pattern_detected("i_prefix"):
            return context.get_pattern_confidence("i_prefix") >= self.min_confidence

        # Check conventions.naming.interfaces
        if context.conventions:
            naming = context.conventions.get("naming", {})
            interfaces = naming.get("interfaces", {})
            pattern = interfaces.get("pattern", "")
            consistency = interfaces.get("consistency", 0)
            if "I{" in pattern or pattern.startswith("I") or "I[A-Z]" in pattern:
                return consistency >= 0.8
        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get interface prefix check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-interface-i-prefix",
                name="Interface I-Prefix",
                description="Interfaces must start with 'I' followed by capital letter",
                check_type="naming",
                severity="warning",
                config={
                    "pattern": "^I[A-Z]",
                    "symbol_type": "interface",
                },
                applies_to_paths=["**/*.cs"],
            ),
        ]


@MappingRegistry.register
class AsyncSuffixMapping(PatternMapping):
    """
    Async method suffix convention.

    Enforces async methods end with 'Async'.
    """

    pattern_key = "async_suffix"
    languages = ["csharp"]
    min_confidence = 0.7
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when async suffix convention is detected."""
        if context.is_pattern_detected("async_suffix"):
            return context.get_pattern_confidence("async_suffix") >= self.min_confidence

        # Check conventions.naming.async_methods
        if context.conventions:
            naming = context.conventions.get("naming", {})
            async_methods = naming.get("async_methods", {})
            pattern = async_methods.get("pattern", "")
            consistency = async_methods.get("consistency", 0)
            if "Async" in pattern:
                return consistency >= 0.8
        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get async suffix check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-async-suffix",
                name="Async Method Suffix",
                description="Async methods should end with 'Async'",
                check_type="naming",
                severity="info",
                config={
                    "pattern": ".*Async$",
                    "symbol_type": "method",
                    "has_modifier": "async",
                },
                applies_to_paths=["**/*.cs"],
            ),
        ]


@MappingRegistry.register
class ResultPatternMapping(PatternMapping):
    """
    Result<T> error handling pattern.

    Enforces use of Result<T> or similar for error handling.
    """

    pattern_key = "result_type"
    languages = ["csharp", "python"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when Result pattern is detected."""
        # Check various pattern keys
        for key in ["result_type", "error_handling", "result_pattern"]:
            if context.is_pattern_detected(key):
                confidence = context.get_pattern_confidence(key)
                if confidence >= self.min_confidence:
                    return True
        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get Result pattern check templates."""
        if context.language == "csharp":
            return [
                CheckTemplate(
                    id_template="{zone}-result-return-types",
                    name="Application Returns Result",
                    description="Application layer methods should return Result<T>",
                    check_type="ast",
                    severity="info",
                    config={
                        "method_scope": "public",
                        "layer": "application",
                        "return_pattern": "Result<|ErrorOr<|Either<",
                    },
                    applies_to_paths=["**/Application/**/*.cs"],
                    review_reason="Result pattern enforcement may require significant changes",
                    fix_hint="Enable after confirming Result<T> is the intended pattern",
                ),
            ]
        else:
            return [
                CheckTemplate(
                    id_template="{zone}-result-return-types",
                    name="Functions Return Result Types",
                    description="Functions should return typed Result objects",
                    check_type="ast",
                    severity="info",
                    config={
                        "return_type_pattern": "Result|Either|Success|Failure",
                    },
                    applies_to_paths=["**/*.py"],
                    review_reason="Result pattern enforcement may require significant changes",
                ),
            ]


@MappingRegistry.register
class PytestMarkersMapping(PatternMapping):
    """
    pytest markers convention.

    Enforces use of pytest markers on test functions.
    """

    pattern_key = "framework_pytest"
    languages = ["python"]
    min_confidence = 0.7
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when pytest framework is detected."""
        # Check for pytest framework detection
        if context.is_pattern_detected("framework_pytest"):
            return context.get_pattern_confidence("framework_pytest") >= self.min_confidence

        # Check if pytest is in frameworks list
        if context.has_framework("pytest"):
            return True

        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get pytest marker check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-pytest-markers",
                name="pytest Markers",
                description="Tests should have appropriate pytest markers",
                check_type="ast",
                severity="info",
                config={
                    "decorator_patterns": ["@pytest.mark"],
                    "scope": "test_*",
                },
                applies_to_paths=[
                    "**/tests/**/*.py",
                    "**/test_*.py",
                ],
                review_reason="Marker requirements vary by project",
            ),
        ]


@MappingRegistry.register
class TypeHintsMapping(PatternMapping):
    """
    Python type hints convention.

    Enforces use of type hints on function signatures.
    """

    pattern_key = "type_hints"
    languages = ["python"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when type hints convention is detected."""
        if context.is_pattern_detected("type_hints"):
            return context.get_pattern_confidence("type_hints") >= self.min_confidence

        # Check conventions
        if context.conventions:
            type_hints = context.conventions.get("type_hints", {})
            return type_hints.get("consistency", 0) >= 0.7
        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get type hints check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-type-hints",
                name="Type Hints Required",
                description="Functions should have type hints",
                check_type="ast",
                severity="info",
                config={
                    "require_return_type": True,
                    "require_param_types": True,
                },
                applies_to_paths=["**/*.py"],
                exclude_paths=["**/tests/**", "**/__pycache__/**"],
                review_reason="Type hint requirements vary by codebase maturity",
            ),
        ]


@MappingRegistry.register
class DDDValueObjectMapping(PatternMapping):
    """
    DDD Value Object pattern.

    Enforces value object immutability and equality.
    """

    pattern_key = "ddd_value_object"
    languages = ["csharp"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when DDD Value Object pattern is detected."""
        if context.is_pattern_detected("ddd_value_object"):
            return context.get_pattern_confidence("ddd_value_object") >= self.min_confidence
        if context.is_pattern_detected("ddd"):
            meta = context.get_pattern_metadata("ddd")
            return "value_object" in str(meta.get("patterns", [])).lower()
        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get DDD Value Object check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-value-object-immutable",
                name="Value Objects Immutable",
                description="Value objects should be immutable (use records or readonly)",
                check_type="ast",
                severity="warning",
                config={
                    "class_pattern": ".*Value$|.*ValueObject$",
                    "require_readonly": True,
                },
                applies_to_paths=["**/Domain/**/*.cs"],
            ),
        ]


@MappingRegistry.register
class DDDEntityMapping(PatternMapping):
    """
    DDD Entity pattern.

    Enforces entity identity patterns.
    """

    pattern_key = "ddd_entity"
    languages = ["csharp"]
    min_confidence = 0.6
    version = "1.0"

    def matches(self, context: MappingContext) -> bool:
        """Match when DDD Entity pattern is detected."""
        if context.is_pattern_detected("ddd_entity"):
            return context.get_pattern_confidence("ddd_entity") >= self.min_confidence
        if context.is_pattern_detected("ddd"):
            meta = context.get_pattern_metadata("ddd")
            return "entity" in str(meta.get("patterns", [])).lower()
        return False

    def get_templates(self, context: MappingContext) -> List[CheckTemplate]:
        """Get DDD Entity check templates."""
        return [
            CheckTemplate(
                id_template="{zone}-entity-has-id",
                name="Entities Have Identity",
                description="Entities should have an Id property",
                check_type="ast",
                severity="warning",
                config={
                    "class_pattern": ".*Entity$|Entity<",
                    "required_property": "Id",
                },
                applies_to_paths=["**/Domain/**/*.cs"],
            ),
        ]
