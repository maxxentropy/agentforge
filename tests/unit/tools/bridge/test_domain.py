"""Unit tests for bridge domain entities."""

from datetime import datetime

from agentforge.core.bridge.domain import (
    CheckTemplate,
    ConfidenceTier,
    Conflict,
    ConflictType,
    GeneratedCheck,
    GeneratedContract,
    GenerationMetadata,
    MappingContext,
    ResolutionStrategy,
)


class TestConfidenceTier:
    """Tests for confidence tier classification."""

    def test_from_score_high(self):
        """Scores >= 0.9 are HIGH confidence."""
        assert ConfidenceTier.from_score(0.9) == ConfidenceTier.HIGH, "Expected ConfidenceTier.from_score(0.9) to equal ConfidenceTier.HIGH"
        assert ConfidenceTier.from_score(0.95) == ConfidenceTier.HIGH, "Expected ConfidenceTier.from_score(0... to equal ConfidenceTier.HIGH"
        assert ConfidenceTier.from_score(1.0) == ConfidenceTier.HIGH, "Expected ConfidenceTier.from_score(1.0) to equal ConfidenceTier.HIGH"

    def test_from_score_medium(self):
        """Scores 0.6-0.9 are MEDIUM confidence."""
        assert ConfidenceTier.from_score(0.6) == ConfidenceTier.MEDIUM, "Expected ConfidenceTier.from_score(0.6) to equal ConfidenceTier.MEDIUM"
        assert ConfidenceTier.from_score(0.7) == ConfidenceTier.MEDIUM, "Expected ConfidenceTier.from_score(0.7) to equal ConfidenceTier.MEDIUM"
        assert ConfidenceTier.from_score(0.89) == ConfidenceTier.MEDIUM, "Expected ConfidenceTier.from_score(0... to equal ConfidenceTier.MEDIUM"

    def test_from_score_low(self):
        """Scores 0.3-0.6 are LOW confidence."""
        assert ConfidenceTier.from_score(0.3) == ConfidenceTier.LOW, "Expected ConfidenceTier.from_score(0.3) to equal ConfidenceTier.LOW"
        assert ConfidenceTier.from_score(0.5) == ConfidenceTier.LOW, "Expected ConfidenceTier.from_score(0.5) to equal ConfidenceTier.LOW"
        assert ConfidenceTier.from_score(0.59) == ConfidenceTier.LOW, "Expected ConfidenceTier.from_score(0... to equal ConfidenceTier.LOW"

    def test_from_score_uncertain(self):
        """Scores < 0.3 are UNCERTAIN."""
        assert ConfidenceTier.from_score(0.0) == ConfidenceTier.UNCERTAIN, "Expected ConfidenceTier.from_score(0.0) to equal ConfidenceTier.UNCERTAIN"
        assert ConfidenceTier.from_score(0.2) == ConfidenceTier.UNCERTAIN, "Expected ConfidenceTier.from_score(0.2) to equal ConfidenceTier.UNCERTAIN"
        assert ConfidenceTier.from_score(0.29) == ConfidenceTier.UNCERTAIN, "Expected ConfidenceTier.from_score(0... to equal ConfidenceTier.UNCERTAIN"

    def test_auto_enable_only_high(self):
        """Only HIGH tier auto-enables."""
        assert ConfidenceTier.HIGH.auto_enable is True, "Expected ConfidenceTier.HIGH.auto_en... is True"
        assert ConfidenceTier.MEDIUM.auto_enable is False, "Expected ConfidenceTier.MEDIUM.auto_... is False"
        assert ConfidenceTier.LOW.auto_enable is False, "Expected ConfidenceTier.LOW.auto_enable is False"
        assert ConfidenceTier.UNCERTAIN.auto_enable is False, "Expected ConfidenceTier.UNCERTAIN.au... is False"

    def test_needs_review(self):
        """MEDIUM and LOW need review."""
        assert ConfidenceTier.HIGH.needs_review is False, "Expected ConfidenceTier.HIGH.needs_r... is False"
        assert ConfidenceTier.MEDIUM.needs_review is True, "Expected ConfidenceTier.MEDIUM.needs... is True"
        assert ConfidenceTier.LOW.needs_review is True, "Expected ConfidenceTier.LOW.needs_re... is True"
        assert ConfidenceTier.UNCERTAIN.needs_review is False, "Expected ConfidenceTier.UNCERTAIN.ne... is False"# Not generated


class TestCheckTemplate:
    """Tests for check templates."""

    def test_create_template(self):
        """Can create a check template."""
        template = CheckTemplate(
            id_template="{zone}-cqrs-command-naming",
            name="CQRS Command Naming",
            description="Commands should end with 'Command'",
            check_type="naming",
            config={"pattern": ".*Command$"},
            severity="warning",
        )

        assert template.id_template == "{zone}-cqrs-command-naming", "Expected template.id_template to equal '{zone}-cqrs-command-naming'"
        assert template.name == "CQRS Command Naming", "Expected template.name to equal 'CQRS Command Naming'"
        assert template.check_type == "naming", "Expected template.check_type to equal 'naming'"

    def test_resolve_id(self):
        """Can resolve template ID placeholders."""
        template = CheckTemplate(
            id_template="{zone}-test-check",
            name="Test",
            description="Test check",
            check_type="naming",
            config={},
        )

        resolved = template.resolve_id("core")
        assert resolved == "core-test-check", "Expected resolved to equal 'core-test-check'"


class TestMappingContext:
    """Tests for mapping context."""

    def test_is_pattern_detected(self):
        """Can check if a pattern is detected."""
        context = MappingContext(
            zone_name="core",
            language="csharp",
            patterns={"cqrs": {"confidence": 0.9, "primary": "MediatR"}},
            structure={},
            frameworks=["MediatR"],
        )

        assert context.is_pattern_detected("cqrs") is True, "Expected context.is_pattern_detected... is True"
        assert context.is_pattern_detected("nonexistent") is False, "Expected context.is_pattern_detected... is False"

    def test_get_pattern_confidence(self):
        """Can get pattern confidence."""
        context = MappingContext(
            zone_name="core",
            language="csharp",
            patterns={"cqrs": {"confidence": 0.9}},
            structure={},
            frameworks=[],
        )

        assert context.get_pattern_confidence("cqrs") == 0.9, "Expected context.get_pattern_confide... to equal 0.9"
        assert context.get_pattern_confidence("nonexistent") == 0.0, "Expected context.get_pattern_confide... to equal 0.0"

    def test_get_pattern_primary(self):
        """Can get pattern primary implementation."""
        context = MappingContext(
            zone_name="core",
            language="csharp",
            patterns={"cqrs": {"confidence": 0.9, "primary": "MediatR"}},
            structure={},
            frameworks=[],
        )

        assert context.get_pattern_primary("cqrs") == "MediatR", "Expected context.get_pattern_primary... to equal 'MediatR'"
        assert context.get_pattern_primary("nonexistent") is None, "Expected context.get_pattern_primary... is None"

    def test_has_framework(self):
        """Can check for framework presence."""
        context = MappingContext(
            zone_name="core",
            language="csharp",
            patterns={},
            structure={},
            frameworks=["MediatR", "EFCore"],
        )

        assert context.has_framework("MediatR") is True, "Expected context.has_framework('Medi... is True"
        assert context.has_framework("mediatr") is True, "Expected context.has_framework('medi... is True"# case insensitive
        assert context.has_framework("nonexistent") is False, "Expected context.has_framework('none... is False"

    def test_language_attribute(self):
        """Can access language directly."""
        context = MappingContext(
            zone_name="core",
            language="csharp",
            patterns={},
            structure={},
            frameworks=[],
        )

        assert context.language == "csharp", "Expected context.language to equal 'csharp'"

    def test_get_architecture_style(self):
        """Can get architecture style."""
        context = MappingContext(
            zone_name="core",
            language="csharp",
            patterns={},
            structure={"architecture_style": "clean-architecture"},
            frameworks=[],
        )

        assert context.get_architecture_style() == "clean-architecture", "Expected context.get_architecture_st... to equal 'clean-architecture'"


class TestGeneratedCheck:
    """Tests for generated checks."""

    def test_create_check(self):
        """Can create a generated check."""
        check = GeneratedCheck(
            id="core-test",
            name="Test Check",
            description="A test check",
            check_type="naming",
            enabled=True,
            severity="warning",
            config={"pattern": ".*"},
            applies_to={"paths": ["**/*.cs"]},
            source_pattern="test_pattern",
            source_confidence=0.95,
        )

        assert check.id == "core-test", "Expected check.id to equal 'core-test'"
        assert check.enabled is True, "Expected check.enabled is True"

    def test_to_dict(self):
        """Can convert to dictionary."""
        check = GeneratedCheck(
            id="core-test",
            name="Test Check",
            description="A test check",
            check_type="naming",
            enabled=True,
            severity="warning",
            config={"pattern": ".*"},
            applies_to={"paths": ["**/*.cs"]},
            source_pattern="test_pattern",
            source_confidence=0.95,
        )

        result = check.to_dict()

        assert result["id"] == "core-test", "Expected result['id'] to equal 'core-test'"
        assert result["name"] == "Test Check", "Expected result['name'] to equal 'Test Check'"
        assert result["enabled"] is True, "Expected result['enabled'] is True"
        assert "generation" in result, "Expected 'generation' in result"


class TestGeneratedContract:
    """Tests for generated contracts."""

    def test_enabled_disabled_counts(self):
        """Can count enabled and disabled checks."""
        checks = [
            GeneratedCheck(
                id="check-1",
                name="Check 1",
                description="Check 1",
                check_type="naming",
                enabled=True,
                severity="warning",
                config={},
                applies_to={},
                source_pattern="pattern1",
                source_confidence=0.9,
            ),
            GeneratedCheck(
                id="check-2",
                name="Check 2",
                description="Check 2",
                check_type="naming",
                enabled=False,
                severity="warning",
                config={},
                applies_to={},
                source_pattern="pattern1",
                source_confidence=0.7,
            ),
            GeneratedCheck(
                id="check-3",
                name="Check 3",
                description="Check 3",
                check_type="naming",
                enabled=True,
                severity="warning",
                config={},
                applies_to={},
                source_pattern="pattern2",
                source_confidence=0.95,
            ),
        ]

        contract = GeneratedContract(
            name="test",
            zone="core",
            language="csharp",
            checks=checks,
            metadata=GenerationMetadata(
                source_profile="test.yaml",
                source_hash="sha256:abc",
                generated_at=datetime.now(),
                generator_version="1.0.0",
            ),
        )

        assert contract.enabled_count == 2, "Expected contract.enabled_count to equal 2"
        assert contract.disabled_count == 1, "Expected contract.disabled_count to equal 1"

    def test_to_dict(self):
        """Can convert to dictionary."""
        metadata = GenerationMetadata(
            source_profile="test.yaml",
            source_hash="sha256:abc",
            generated_at=datetime(2025, 1, 1, 12, 0, 0),
            generator_version="1.0.0",
        )

        contract = GeneratedContract(
            name="test",
            zone="core",
            language="csharp",
            checks=[],
            metadata=metadata,
            description="Test contract",
            tags=["generated", "test"],
        )

        result = contract.to_dict()

        assert result["contract"]["name"] == "test", "Expected result['contract']['name'] to equal 'test'"
        assert result["contract"]["description"] == "Test contract", "Expected result['contract']['descrip... to equal 'Test contract'"
        assert result["generation_metadata"]["source_profile"] == "test.yaml", "Expected result['generation_metadata... to equal 'test.yaml'"
        assert result["checks"] == [], "Expected result['checks'] to equal []"


class TestConflict:
    """Tests for conflict detection."""

    def test_create_conflict(self):
        """Can create a conflict."""
        conflict = Conflict(
            conflict_type=ConflictType.DUPLICATE_ID,
            generated_check_id="test-check",
            reason="Duplicate check ID",
            resolution=ResolutionStrategy.SKIP,
        )

        assert conflict.conflict_type == ConflictType.DUPLICATE_ID, "Expected conflict.conflict_type to equal ConflictType.DUPLICATE_ID"
        assert conflict.generated_check_id == "test-check", "Expected conflict.generated_check_id to equal 'test-check'"
        assert conflict.resolution == ResolutionStrategy.SKIP, "Expected conflict.resolution to equal ResolutionStrategy.SKIP"

    def test_to_dict(self):
        """Can convert to dictionary."""
        conflict = Conflict(
            conflict_type=ConflictType.DUPLICATE_ID,
            generated_check_id="test-check",
            reason="Duplicate check ID",
            resolution=ResolutionStrategy.RENAME,
            new_id="test-check-v2",
        )

        result = conflict.to_dict()

        assert result["type"] == "duplicate_id", "Expected result['type'] to equal 'duplicate_id'"
        assert result["generated_check"] == "test-check", "Expected result['generated_check'] to equal 'test-check'"
        assert result["resolution"] == "rename", "Expected result['resolution'] to equal 'rename'"
        assert result["new_id"] == "test-check-v2", "Expected result['new_id'] to equal 'test-check-v2'"
