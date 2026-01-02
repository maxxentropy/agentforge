# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: config-validator, config-validation-error
# @test_path: tests/unit/pipeline/test_config_validator.py

"""
Pipeline Configuration Validator
=================================

Validates pipeline configuration for correctness:
- Stage names are valid
- Stage order is logical
- Required fields are present
- References are valid
"""

from dataclasses import dataclass

from .config import GlobalSettings, PipelineTemplate


@dataclass
class ValidationError:
    """Configuration validation error."""

    path: str
    message: str
    severity: str  # "error", "warning"


class ConfigValidator:
    """Validates pipeline configuration."""

    VALID_STAGES = [
        "intake",
        "clarify",
        "analyze",
        "spec",
        "red",
        "green",
        "refactor",
        "deliver",
    ]

    def validate_template(self, template: PipelineTemplate) -> list[ValidationError]:
        """
        Validate a pipeline template.

        Args:
            template: Pipeline template to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for empty stages
        if not template.stages:
            errors.append(
                ValidationError(
                    path="stages",
                    message="Pipeline has no stages defined",
                    severity="error",
                )
            )
            return errors  # Can't validate further without stages

        # Check stages are valid
        for stage in template.stages:
            if stage not in self.VALID_STAGES:
                errors.append(
                    ValidationError(
                        path=f"stages.{stage}",
                        message=f"Unknown stage: {stage}",
                        severity="error",
                    )
                )

        # Check for duplicate stages
        seen = set()
        for stage in template.stages:
            if stage in seen:
                errors.append(
                    ValidationError(
                        path=f"stages.{stage}",
                        message=f"Duplicate stage: {stage}",
                        severity="warning",
                    )
                )
            seen.add(stage)

        # Check stage order makes sense
        if "green" in template.stages and "red" not in template.stages:
            errors.append(
                ValidationError(
                    path="stages",
                    message="GREEN stage requires RED stage",
                    severity="warning",
                )
            )

        # Check exit_after is in stages
        exit_after = template.defaults.get("exit_after")
        if exit_after and exit_after not in template.stages:
            errors.append(
                ValidationError(
                    path="defaults.exit_after",
                    message=f"exit_after stage '{exit_after}' not in stages",
                    severity="error",
                )
            )

        return errors

    def validate_settings(self, settings: GlobalSettings) -> list[ValidationError]:
        """
        Validate global settings.

        Args:
            settings: Global settings to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check cost limit
        if settings.max_cost_per_pipeline < 0:
            errors.append(
                ValidationError(
                    path="cost.max_per_pipeline_usd",
                    message="Cost limit cannot be negative",
                    severity="warning",
                )
            )

        return errors
