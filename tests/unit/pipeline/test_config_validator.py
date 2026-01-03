# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: config-validator, config-validation-error

"""Unit tests for ConfigValidator class."""



class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_validation_error_stores_fields(self):
        """ValidationError stores path, message, severity."""
        from agentforge.core.pipeline.config_validator import ValidationError

        error = ValidationError(
            path="stages.unknown",
            message="Unknown stage: unknown",
            severity="error",
        )
        assert error.path == "stages.unknown", "Expected error.path to equal 'stages.unknown'"
        assert error.message == "Unknown stage: unknown", "Expected error.message to equal 'Unknown stage: unknown'"
        assert error.severity == "error", "Expected error.severity to equal 'error'"

    def test_validation_error_severity_options(self):
        """ValidationError accepts error and warning severities."""
        from agentforge.core.pipeline.config_validator import ValidationError

        error = ValidationError(path="test", message="An error", severity="error")
        assert error.severity == "error", "Expected error.severity to equal 'error'"

        warning = ValidationError(path="test", message="A warning", severity="warning")
        assert warning.severity == "warning", "Expected warning.severity to equal 'warning'"


class TestConfigValidator:
    """Tests for ConfigValidator class."""

    def test_validates_valid_template(self):
        """Returns no errors for valid template."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["intake", "clarify", "analyze", "spec"],
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        assert len(errors) == 0, "Expected len(errors) to equal 0"

    def test_validates_stage_names(self):
        """Rejects invalid stage names."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["intake", "unknown_stage", "spec"],
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        assert len(errors) == 1, "Expected len(errors) to equal 1"
        assert errors[0].severity == "error", "Expected errors[0].severity to equal 'error'"
        assert "unknown_stage" in errors[0].message, "Expected 'unknown_stage' in errors[0].message"
        assert "stages.unknown_stage" in errors[0].path, "Expected 'stages.unknown_stage' in errors[0].path"

    def test_validates_multiple_invalid_stages(self):
        """Reports all invalid stage names."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["bad1", "intake", "bad2"],
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        assert len(errors) == 2, "Expected len(errors) to equal 2"
        messages = [e.message for e in errors]
        assert any("bad1" in m for m in messages), "Expected any() to be truthy"
        assert any("bad2" in m for m in messages), "Expected any() to be truthy"

    def test_warns_green_without_red(self):
        """Warns when GREEN without RED."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["analyze", "green", "refactor"],
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) == 1, "Expected len(warnings) to equal 1"
        assert "RED" in warnings[0].message or "red" in warnings[0].message.lower(), "Assertion failed"

    def test_no_warning_when_green_with_red(self):
        """No warning when GREEN has RED."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["red", "green", "refactor"],
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) == 0, "Expected len(warnings) to equal 0"

    def test_validates_exit_after(self):
        """Error when exit_after not in stages."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["intake", "clarify", "analyze"],
            defaults={"exit_after": "spec"},  # spec not in stages
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        error_messages = [e for e in errors if e.severity == "error"]
        assert len(error_messages) == 1, "Expected len(error_messages) to equal 1"
        assert "exit_after" in error_messages[0].path, "Expected 'exit_after' in error_messages[0].path"
        assert "spec" in error_messages[0].message, "Expected 'spec' in error_messages[0].message"

    def test_valid_exit_after(self):
        """No error when exit_after is in stages."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["intake", "clarify", "analyze", "spec"],
            defaults={"exit_after": "spec"},
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        error_messages = [e for e in errors if e.severity == "error"]
        assert len(error_messages) == 0, "Expected len(error_messages) to equal 0"

    def test_valid_stages_constant(self):
        """VALID_STAGES contains all expected stages."""
        from agentforge.core.pipeline.config_validator import ConfigValidator

        expected = [
            "intake", "clarify", "analyze", "spec",
            "red", "green", "refactor", "deliver"
        ]

        validator = ConfigValidator()
        for stage in expected:
            assert stage in validator.VALID_STAGES, "Expected stage in validator.VALID_STAGES"

    def test_validates_settings_valid(self):
        """Returns no errors for valid settings."""
        from agentforge.core.pipeline.config import GlobalSettings
        from agentforge.core.pipeline.config_validator import ConfigValidator

        settings = GlobalSettings(
            project_name="TestProject",
            language="python",
            max_cost_per_pipeline=10.0,
        )

        validator = ConfigValidator()
        errors = validator.validate_settings(settings)

        assert len(errors) == 0, "Expected len(errors) to equal 0"

    def test_validates_settings_negative_cost(self):
        """Warns on negative cost limit."""
        from agentforge.core.pipeline.config import GlobalSettings
        from agentforge.core.pipeline.config_validator import ConfigValidator

        settings = GlobalSettings(
            max_cost_per_pipeline=-5.0,
        )

        validator = ConfigValidator()
        errors = validator.validate_settings(settings)

        assert len(errors) == 1, "Expected len(errors) to equal 1"
        assert errors[0].severity == "warning", "Expected errors[0].severity to equal 'warning'"
        assert "cost" in errors[0].path.lower(), "Expected 'cost' in errors[0].path.lower()"

    def test_validates_settings_zero_cost_ok(self):
        """Zero cost is valid (unlimited)."""
        from agentforge.core.pipeline.config import GlobalSettings
        from agentforge.core.pipeline.config_validator import ConfigValidator

        settings = GlobalSettings(
            max_cost_per_pipeline=0.0,
        )

        validator = ConfigValidator()
        errors = validator.validate_settings(settings)

        # Zero is acceptable (means unlimited)
        cost_errors = [e for e in errors if "cost" in e.path.lower()]
        assert len(cost_errors) == 0, "Expected len(cost_errors) to equal 0"

    def test_validates_empty_stages(self):
        """Error when stages is empty."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=[],
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        error_messages = [e for e in errors if e.severity == "error"]
        assert len(error_messages) == 1, "Expected len(error_messages) to equal 1"
        assert "empty" in error_messages[0].message.lower() or "no stages" in error_messages[0].message.lower(), "Assertion failed"

    def test_validates_duplicate_stages(self):
        """Warns on duplicate stages."""
        from agentforge.core.pipeline.config import PipelineTemplate
        from agentforge.core.pipeline.config_validator import ConfigValidator

        template = PipelineTemplate(
            name="test",
            description="Test pipeline",
            stages=["intake", "clarify", "intake", "spec"],
        )

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        warnings = [e for e in errors if e.severity == "warning"]
        assert any("duplicate" in w.message.lower() for w in warnings), "Expected any() to be truthy"


class TestConfigValidatorIntegration:
    """Integration tests for ConfigValidator with real templates."""

    def test_validates_implement_template(self, tmp_path):
        """Implement template passes validation."""
        from agentforge.core.pipeline.config import ConfigurationLoader
        from agentforge.core.pipeline.config_validator import ConfigValidator

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("implement")

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        error_messages = [e for e in errors if e.severity == "error"]
        assert len(error_messages) == 0, "Expected len(error_messages) to equal 0"

    def test_validates_design_template(self, tmp_path):
        """Design template passes validation."""
        from agentforge.core.pipeline.config import ConfigurationLoader
        from agentforge.core.pipeline.config_validator import ConfigValidator

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("design")

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        error_messages = [e for e in errors if e.severity == "error"]
        assert len(error_messages) == 0, "Expected len(error_messages) to equal 0"

    def test_validates_test_template(self, tmp_path):
        """Test template passes validation."""
        from agentforge.core.pipeline.config import ConfigurationLoader
        from agentforge.core.pipeline.config_validator import ConfigValidator

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("test")

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        error_messages = [e for e in errors if e.severity == "error"]
        assert len(error_messages) == 0, "Expected len(error_messages) to equal 0"

    def test_validates_fix_template(self, tmp_path):
        """Fix template passes validation (green without red is intentional)."""
        from agentforge.core.pipeline.config import ConfigurationLoader
        from agentforge.core.pipeline.config_validator import ConfigValidator

        loader = ConfigurationLoader(tmp_path)
        template = loader.load_pipeline_template("fix")

        validator = ConfigValidator()
        errors = validator.validate_template(template)

        # Fix template may have a warning for green without red, but no errors
        error_messages = [e for e in errors if e.severity == "error"]
        assert len(error_messages) == 0, "Expected len(error_messages) to equal 0"
