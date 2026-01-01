# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-template-tests

"""
Tests for context templates.
"""

import pytest

from agentforge.core.context.templates import (
    BaseContextTemplate,
    BridgeTemplate,
    CodeReviewTemplate,
    CompactionLevel,
    ContextSection,
    DiscoveryTemplate,
    FixViolationTemplate,
    ImplementFeatureTemplate,
    RefactorTemplate,
    TierDefinition,
    WriteTestsTemplate,
    get_template_class,
    get_template_for_task,
    list_task_types,
    register_template,
)


class TestTemplateRegistry:
    """Tests for template registry functions."""

    def test_get_fix_violation_template(self):
        """Get fix_violation template returns correct type."""
        template = get_template_for_task("fix_violation")
        assert isinstance(template, FixViolationTemplate)
        assert template.task_type == "fix_violation"

    def test_get_implement_feature_template(self):
        """Get implement_feature template returns correct type."""
        template = get_template_for_task("implement_feature")
        assert isinstance(template, ImplementFeatureTemplate)
        assert template.task_type == "implement_feature"

    def test_unknown_task_type_raises(self):
        """Unknown task type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown task type"):
            get_template_for_task("nonexistent")

    def test_list_task_types(self):
        """list_task_types returns registered types."""
        types = list_task_types()
        assert "fix_violation" in types
        assert "implement_feature" in types

    def test_list_task_types_sorted(self):
        """list_task_types returns sorted list."""
        types = list_task_types()
        assert types == sorted(types)

    def test_get_template_class(self):
        """get_template_class returns class not instance."""
        cls = get_template_class("fix_violation")
        assert cls is FixViolationTemplate
        assert issubclass(cls, BaseContextTemplate)

    def test_register_template(self):
        """Custom template can be registered."""

        class TestTemplate(BaseContextTemplate):
            @property
            def task_type(self) -> str:
                return "test_task"

            @property
            def phases(self):
                return ["init"]

            def get_tier2_for_phase(self, phase):
                return TierDefinition(name="test", max_tokens=100, sections=[])

        register_template("test_task", TestTemplate)

        try:
            template = get_template_for_task("test_task")
            assert template.task_type == "test_task"
            assert "test_task" in list_task_types()
        finally:
            # Clean up
            from agentforge.core.context.templates import _TEMPLATE_REGISTRY

            del _TEMPLATE_REGISTRY["test_task"]


class TestFixViolationTemplate:
    """Tests for FixViolationTemplate."""

    @pytest.fixture
    def template(self):
        return FixViolationTemplate()

    def test_task_type(self, template):
        """Task type is fix_violation."""
        assert template.task_type == "fix_violation"

    def test_phases(self, template):
        """Has correct phases."""
        assert template.phases == ["init", "analyze", "implement", "verify"]

    def test_tier2_init_phase(self, template):
        """Init phase tier2 has violation section."""
        tier2 = template.get_tier2_for_phase("init")

        assert tier2.name == "init"
        assert tier2.max_tokens == 1000

        section_names = [s.name for s in tier2.sections]
        assert "violation" in section_names
        assert "overview" in section_names

        # Violation is required
        violation = tier2.get_section("violation")
        assert violation.required is True

    def test_tier2_analyze_phase(self, template):
        """Analyze phase has code analysis sections."""
        tier2 = template.get_tier2_for_phase("analyze")

        assert tier2.name == "analyze"
        assert tier2.max_tokens == 1500

        section_names = [s.name for s in tier2.sections]
        assert "violation" in section_names
        assert "check_definition" in section_names
        assert "file_overview" in section_names
        assert "related_patterns" in section_names

    def test_tier2_implement_phase(self, template):
        """Implement phase has source and suggestions."""
        tier2 = template.get_tier2_for_phase("implement")

        assert tier2.name == "implement"
        assert tier2.max_tokens == 2000

        section_names = [s.name for s in tier2.sections]
        assert "target_source" in section_names
        assert "extraction_suggestions" in section_names
        assert "action_hints" in section_names
        assert "similar_fixes" in section_names

        # Check compaction level for target_source
        target_source = tier2.get_section("target_source")
        assert target_source.compaction == CompactionLevel.TRUNCATE_MIDDLE
        assert target_source.required is True

    def test_tier2_verify_phase(self, template):
        """Verify phase has check results."""
        tier2 = template.get_tier2_for_phase("verify")

        assert tier2.name == "verify"
        assert tier2.max_tokens == 800

        section_names = [s.name for s in tier2.sections]
        assert "verification_command" in section_names
        assert "check_results" in section_names
        assert "remaining_issues" in section_names

    def test_tier2_unknown_phase_returns_init(self, template):
        """Unknown phase falls back to init."""
        tier2 = template.get_tier2_for_phase("unknown")
        assert tier2.name == "init"

    def test_required_sections_implement(self, template):
        """Implement phase has correct required sections."""
        tier2 = template.get_tier2_for_phase("implement")

        required = [s for s in tier2.sections if s.required]
        required_names = [s.name for s in required]

        assert "target_source" in required_names
        assert "extraction_suggestions" in required_names

    def test_system_prompt_is_small(self, template):
        """System prompt must be cacheable (< 200 tokens)."""
        prompt = template.get_system_prompt()
        tokens = len(prompt) // 4

        assert tokens < 200

    def test_system_prompt_contains_rules(self, template):
        """System prompt contains essential rules."""
        prompt = template.get_system_prompt()

        assert "RULES" in prompt
        assert "action" in prompt.lower()
        assert "yaml" in prompt.lower()


class TestImplementFeatureTemplate:
    """Tests for ImplementFeatureTemplate."""

    @pytest.fixture
    def template(self):
        return ImplementFeatureTemplate()

    def test_task_type(self, template):
        """Task type is implement_feature."""
        assert template.task_type == "implement_feature"

    def test_phases(self, template):
        """Has correct phases."""
        assert template.phases == ["init", "analyze", "implement", "verify"]

    def test_tier2_init_phase(self, template):
        """Init phase has spec and failing tests."""
        tier2 = template.get_tier2_for_phase("init")

        assert tier2.name == "init"

        section_names = [s.name for s in tier2.sections]
        assert "spec" in section_names
        assert "failing_tests" in section_names

        # Both are required
        spec = tier2.get_section("spec")
        assert spec.required is True

        failing_tests = tier2.get_section("failing_tests")
        assert failing_tests.required is True

    def test_tier2_analyze_phase(self, template):
        """Analyze phase has requirements and criteria."""
        tier2 = template.get_tier2_for_phase("analyze")

        section_names = [s.name for s in tier2.sections]
        assert "spec_requirements" in section_names
        assert "acceptance_criteria" in section_names
        assert "test_expectations" in section_names
        assert "related_code" in section_names

    def test_tier2_implement_phase(self, template):
        """Implement phase has tests and interface."""
        tier2 = template.get_tier2_for_phase("implement")

        assert tier2.max_tokens == 2000

        section_names = [s.name for s in tier2.sections]
        assert "failing_tests" in section_names
        assert "target_location" in section_names
        assert "interface_definition" in section_names
        assert "similar_implementations" in section_names

    def test_tier2_verify_phase(self, template):
        """Verify phase has test results."""
        tier2 = template.get_tier2_for_phase("verify")

        section_names = [s.name for s in tier2.sections]
        assert "test_results" in section_names
        assert "coverage_delta" in section_names
        assert "remaining_failures" in section_names

    def test_system_prompt_mentions_tdd(self, template):
        """System prompt mentions TDD green phase."""
        prompt = template.get_system_prompt()

        assert "TDD" in prompt
        assert "test" in prompt.lower()


class TestBaseContextTemplate:
    """Tests for BaseContextTemplate base class."""

    def test_tier1_always_present(self):
        """Tier1 has fingerprint, task, phase sections."""
        tier1 = BaseContextTemplate.TIER1_ALWAYS

        assert tier1.name == "always"
        assert tier1.max_tokens == 800

        section_names = [s.name for s in tier1.sections]
        assert "fingerprint" in section_names
        assert "task" in section_names
        assert "phase" in section_names

    def test_tier1_sections_never_compact(self):
        """All tier1 sections have NEVER compaction."""
        tier1 = BaseContextTemplate.TIER1_ALWAYS

        for section in tier1.sections:
            assert section.compaction == CompactionLevel.NEVER

    def test_tier1_sections_required(self):
        """All tier1 sections are required."""
        tier1 = BaseContextTemplate.TIER1_ALWAYS

        for section in tier1.sections:
            assert section.required is True

    def test_tier3_on_demand(self):
        """Tier3 has understanding, recent, additional sections."""
        tier3 = BaseContextTemplate.TIER3_ON_DEMAND

        assert tier3.name == "on_demand"
        assert tier3.max_tokens == 1000

        section_names = [s.name for s in tier3.sections]
        assert "understanding" in section_names
        assert "recent" in section_names
        assert "additional" in section_names

    def test_tier3_sections_aggressive_compaction(self):
        """All tier3 sections have AGGRESSIVE compaction."""
        tier3 = BaseContextTemplate.TIER3_ON_DEMAND

        for section in tier3.sections:
            assert section.compaction == CompactionLevel.AGGRESSIVE

    def test_total_budget(self):
        """Total budget is reasonable."""
        template = FixViolationTemplate()
        budget = template.get_total_budget()

        # Tier1 (800) + max Tier2 (2000 for implement) + Tier3 (1000) = 3800
        assert 2000 < budget < 5000

    def test_get_all_tiers(self):
        """get_all_tiers returns all three tiers."""
        template = FixViolationTemplate()
        tiers = template.get_all_tiers("analyze")

        assert len(tiers) == 3
        assert tiers[0].name == "always"
        assert tiers[1].name == "analyze"
        assert tiers[2].name == "on_demand"

    def test_base_system_prompt(self):
        """Base system prompt is present and small."""
        prompt = BaseContextTemplate.BASE_SYSTEM_PROMPT

        assert "RULES" in prompt
        assert len(prompt) // 4 < 200  # Cacheable


class TestContextSection:
    """Tests for ContextSection model."""

    def test_default_compaction(self):
        """Default compaction is NORMAL."""
        section = ContextSection(
            name="test",
            source="test_source",
            max_tokens=100,
        )
        assert section.compaction == CompactionLevel.NORMAL

    def test_default_not_required(self):
        """Default required is False."""
        section = ContextSection(
            name="test",
            source="test_source",
            max_tokens=100,
        )
        assert section.required is False

    def test_hashable(self):
        """ContextSection is hashable."""
        section = ContextSection(
            name="test",
            source="test_source",
            max_tokens=100,
        )
        # Should not raise
        hash(section)

        # Same name = same hash
        section2 = ContextSection(
            name="test",
            source="different",
            max_tokens=200,
        )
        assert hash(section) == hash(section2)


class TestTierDefinition:
    """Tests for TierDefinition model."""

    def test_get_section(self):
        """get_section returns section by name."""
        tier = TierDefinition(
            name="test",
            max_tokens=100,
            sections=[
                ContextSection(name="a", source="s1", max_tokens=50),
                ContextSection(name="b", source="s2", max_tokens=50),
            ],
        )

        section = tier.get_section("a")
        assert section.name == "a"

        missing = tier.get_section("missing")
        assert missing is None

    def test_get_required_sections(self):
        """get_required_sections returns only required ones."""
        tier = TierDefinition(
            name="test",
            max_tokens=100,
            sections=[
                ContextSection(name="a", source="s1", max_tokens=50, required=True),
                ContextSection(name="b", source="s2", max_tokens=50, required=False),
                ContextSection(name="c", source="s3", max_tokens=50, required=True),
            ],
        )

        required = tier.get_required_sections()
        names = [s.name for s in required]

        assert "a" in names
        assert "c" in names
        assert "b" not in names

    def test_get_section_names(self):
        """get_section_names returns all names."""
        tier = TierDefinition(
            name="test",
            max_tokens=100,
            sections=[
                ContextSection(name="a", source="s1", max_tokens=50),
                ContextSection(name="b", source="s2", max_tokens=50),
            ],
        )

        names = tier.get_section_names()
        assert names == ["a", "b"]


class TestCompactionLevel:
    """Tests for CompactionLevel enum."""

    def test_values(self):
        """CompactionLevel has expected values."""
        assert CompactionLevel.NEVER.value == "never"
        assert CompactionLevel.NORMAL.value == "normal"
        assert CompactionLevel.AGGRESSIVE.value == "aggressive"
        assert CompactionLevel.TRUNCATE_MIDDLE.value == "truncate_middle"

    def test_string_enum(self):
        """CompactionLevel is a string enum."""
        assert isinstance(CompactionLevel.NEVER, str)
        assert CompactionLevel.NEVER == "never"


class TestWriteTestsTemplate:
    """Tests for WriteTestsTemplate."""

    @pytest.fixture
    def template(self):
        return WriteTestsTemplate()

    def test_task_type(self, template):
        """Task type is write_tests."""
        assert template.task_type == "write_tests"

    def test_phases(self, template):
        """Has correct phases."""
        assert template.phases == ["init", "analyze", "implement", "verify"]

    def test_tier2_init_phase(self, template):
        """Init phase has spec requirements."""
        tier2 = template.get_tier2_for_phase("init")

        assert tier2.name == "init"
        section_names = [s.name for s in tier2.sections]
        assert "spec_requirements" in section_names

    def test_tier2_analyze_phase(self, template):
        """Analyze phase has testable interface and coverage."""
        tier2 = template.get_tier2_for_phase("analyze")

        assert tier2.max_tokens == 1500
        section_names = [s.name for s in tier2.sections]
        assert "acceptance_criteria" in section_names
        assert "testable_interface" in section_names
        assert "existing_test_patterns" in section_names
        assert "coverage_gaps" in section_names

    def test_tier2_implement_phase(self, template):
        """Implement phase has test template and fixtures."""
        tier2 = template.get_tier2_for_phase("implement")

        assert tier2.max_tokens == 2000
        section_names = [s.name for s in tier2.sections]
        assert "test_template" in section_names
        assert "assertion_hints" in section_names
        assert "fixture_examples" in section_names
        assert "edge_cases" in section_names

    def test_tier2_verify_phase(self, template):
        """Verify phase checks tests must fail."""
        tier2 = template.get_tier2_for_phase("verify")

        section_names = [s.name for s in tier2.sections]
        assert "tests_must_fail" in section_names
        assert "failure_reasons" in section_names

        # tests_must_fail is required (TDD red phase)
        tests_must_fail = tier2.get_section("tests_must_fail")
        assert tests_must_fail.required is True

    def test_system_prompt_mentions_tdd(self, template):
        """System prompt mentions TDD red phase."""
        prompt = template.get_system_prompt()

        assert "TDD" in prompt
        assert "fail" in prompt.lower()

    def test_system_prompt_is_small(self, template):
        """System prompt must be cacheable."""
        prompt = template.get_system_prompt()
        tokens = len(prompt) // 4
        assert tokens < 200


class TestDiscoveryTemplate:
    """Tests for DiscoveryTemplate."""

    @pytest.fixture
    def template(self):
        return DiscoveryTemplate()

    def test_task_type(self, template):
        """Task type is discovery."""
        assert template.task_type == "discovery"

    def test_phases(self, template):
        """Has correct phases (different from fix_violation)."""
        assert template.phases == ["scan", "analyze", "synthesize"]

    def test_tier2_scan_phase(self, template):
        """Scan phase has file structure and entry points."""
        tier2 = template.get_tier2_for_phase("scan")

        assert tier2.name == "scan"
        assert tier2.max_tokens == 1500
        section_names = [s.name for s in tier2.sections]
        assert "file_structure" in section_names
        assert "entry_points" in section_names
        assert "config_files" in section_names

    def test_tier2_analyze_phase(self, template):
        """Analyze phase has dependency and pattern analysis."""
        tier2 = template.get_tier2_for_phase("analyze")

        assert tier2.max_tokens == 2000
        section_names = [s.name for s in tier2.sections]
        assert "dependency_graph" in section_names
        assert "pattern_candidates" in section_names
        assert "architecture_hints" in section_names
        assert "zone_detection" in section_names

    def test_tier2_synthesize_phase(self, template):
        """Synthesize phase has discoveries and recommendations."""
        tier2 = template.get_tier2_for_phase("synthesize")

        section_names = [s.name for s in tier2.sections]
        assert "discovered_patterns" in section_names
        assert "zone_boundaries" in section_names
        assert "recommendations" in section_names

        # discovered_patterns is required
        discovered = tier2.get_section("discovered_patterns")
        assert discovered.required is True

    def test_system_prompt_is_small(self, template):
        """System prompt must be cacheable."""
        prompt = template.get_system_prompt()
        tokens = len(prompt) // 4
        assert tokens < 200


class TestBridgeTemplate:
    """Tests for BridgeTemplate."""

    @pytest.fixture
    def template(self):
        return BridgeTemplate()

    def test_task_type(self, template):
        """Task type is bridge."""
        assert template.task_type == "bridge"

    def test_phases(self, template):
        """Has correct phases."""
        assert template.phases == ["analyze", "map", "validate"]

    def test_tier2_analyze_phase(self, template):
        """Analyze phase has code structure and contracts."""
        tier2 = template.get_tier2_for_phase("analyze")

        assert tier2.max_tokens == 1500
        section_names = [s.name for s in tier2.sections]
        assert "existing_code_structure" in section_names
        assert "target_contracts" in section_names
        assert "mapping_rules" in section_names

        # target_contracts is required
        contracts = tier2.get_section("target_contracts")
        assert contracts.required is True

    def test_tier2_map_phase(self, template):
        """Map phase has candidate mappings and hints."""
        tier2 = template.get_tier2_for_phase("map")

        assert tier2.max_tokens == 2000
        section_names = [s.name for s in tier2.sections]
        assert "candidate_mappings" in section_names
        assert "conflict_analysis" in section_names
        assert "transformation_hints" in section_names

        # candidate_mappings is required
        mappings = tier2.get_section("candidate_mappings")
        assert mappings.required is True

    def test_tier2_validate_phase(self, template):
        """Validate phase has coverage and results."""
        tier2 = template.get_tier2_for_phase("validate")

        section_names = [s.name for s in tier2.sections]
        assert "mapping_coverage" in section_names
        assert "unmapped_elements" in section_names
        assert "validation_results" in section_names

    def test_system_prompt_is_small(self, template):
        """System prompt must be cacheable."""
        prompt = template.get_system_prompt()
        tokens = len(prompt) // 4
        assert tokens < 200


class TestCodeReviewTemplate:
    """Tests for CodeReviewTemplate."""

    @pytest.fixture
    def template(self):
        return CodeReviewTemplate()

    def test_task_type(self, template):
        """Task type is code_review."""
        assert template.task_type == "code_review"

    def test_phases(self, template):
        """Has correct phases."""
        assert template.phases == ["init", "analyze", "report"]

    def test_tier2_init_phase(self, template):
        """Init phase has diff summary and context."""
        tier2 = template.get_tier2_for_phase("init")

        section_names = [s.name for s in tier2.sections]
        assert "diff_summary" in section_names
        assert "changed_files" in section_names
        assert "pr_context" in section_names

        # diff_summary is required
        diff = tier2.get_section("diff_summary")
        assert diff.required is True

    def test_tier2_analyze_phase(self, template):
        """Analyze phase has full diff and coverage."""
        tier2 = template.get_tier2_for_phase("analyze")

        assert tier2.max_tokens == 2000
        section_names = [s.name for s in tier2.sections]
        assert "full_diff" in section_names
        assert "affected_functions" in section_names
        assert "test_coverage" in section_names
        assert "related_code" in section_names

        # full_diff uses truncate_middle
        full_diff = tier2.get_section("full_diff")
        assert full_diff.compaction == CompactionLevel.TRUNCATE_MIDDLE

    def test_tier2_report_phase(self, template):
        """Report phase has findings and suggestions."""
        tier2 = template.get_tier2_for_phase("report")

        section_names = [s.name for s in tier2.sections]
        assert "findings" in section_names
        assert "suggestions" in section_names
        assert "security_concerns" in section_names

        # findings is required
        findings = tier2.get_section("findings")
        assert findings.required is True

    def test_system_prompt_mentions_review(self, template):
        """System prompt mentions review concerns."""
        prompt = template.get_system_prompt()

        assert "review" in prompt.lower()
        assert "security" in prompt.lower()

    def test_system_prompt_is_small(self, template):
        """System prompt must be cacheable."""
        prompt = template.get_system_prompt()
        tokens = len(prompt) // 4
        assert tokens < 200


class TestRefactorTemplate:
    """Tests for RefactorTemplate."""

    @pytest.fixture
    def template(self):
        return RefactorTemplate()

    def test_task_type(self, template):
        """Task type is refactor."""
        assert template.task_type == "refactor"

    def test_phases(self, template):
        """Has correct phases."""
        assert template.phases == ["init", "analyze", "implement", "verify"]

    def test_tier2_init_phase(self, template):
        """Init phase has refactor goal and scope."""
        tier2 = template.get_tier2_for_phase("init")

        section_names = [s.name for s in tier2.sections]
        assert "refactor_goal" in section_names
        assert "scope" in section_names
        assert "constraints" in section_names

        # refactor_goal is required
        goal = tier2.get_section("refactor_goal")
        assert goal.required is True

    def test_tier2_analyze_phase(self, template):
        """Analyze phase has target code and dependencies."""
        tier2 = template.get_tier2_for_phase("analyze")

        assert tier2.max_tokens == 1500
        section_names = [s.name for s in tier2.sections]
        assert "target_code" in section_names
        assert "dependencies" in section_names
        assert "callers" in section_names
        assert "test_coverage" in section_names

        # target_code uses truncate_middle
        target = tier2.get_section("target_code")
        assert target.compaction == CompactionLevel.TRUNCATE_MIDDLE

    def test_tier2_implement_phase(self, template):
        """Implement phase has source and patterns."""
        tier2 = template.get_tier2_for_phase("implement")

        assert tier2.max_tokens == 2000
        section_names = [s.name for s in tier2.sections]
        assert "source_code" in section_names
        assert "refactoring_patterns" in section_names
        assert "similar_refactors" in section_names
        assert "action_hints" in section_names

        # source_code is required
        source = tier2.get_section("source_code")
        assert source.required is True

    def test_tier2_verify_phase(self, template):
        """Verify phase has test results."""
        tier2 = template.get_tier2_for_phase("verify")

        section_names = [s.name for s in tier2.sections]
        assert "test_command" in section_names
        assert "test_results" in section_names
        assert "behavior_diff" in section_names

    def test_system_prompt_mentions_behavior(self, template):
        """System prompt mentions behavior preservation."""
        prompt = template.get_system_prompt()

        assert "behavior" in prompt.lower()
        assert "refactor" in prompt.lower()

    def test_system_prompt_is_small(self, template):
        """System prompt must be cacheable."""
        prompt = template.get_system_prompt()
        tokens = len(prompt) // 4
        assert tokens < 200


class TestAllTemplatesRegistered:
    """Tests that all expected templates are registered."""

    def test_all_task_types_registered(self):
        """All 7 task types are registered."""
        types = list_task_types()

        assert "fix_violation" in types
        assert "implement_feature" in types
        assert "write_tests" in types
        assert "discovery" in types
        assert "bridge" in types
        assert "code_review" in types
        assert "refactor" in types

        assert len(types) == 7

    def test_all_templates_instantiable(self):
        """All registered templates can be instantiated."""
        for task_type in list_task_types():
            template = get_template_for_task(task_type)
            assert template.task_type == task_type
            assert len(template.phases) > 0

    def test_all_templates_have_valid_budgets(self):
        """All templates have reasonable token budgets."""
        for task_type in list_task_types():
            template = get_template_for_task(task_type)
            budget = template.get_total_budget()

            # Should be between 2000 and 5000 tokens
            assert 2000 < budget < 5000, f"{task_type} has budget {budget}"

    def test_all_system_prompts_cacheable(self):
        """All templates have small system prompts for caching."""
        for task_type in list_task_types():
            template = get_template_for_task(task_type)
            prompt = template.get_system_prompt()
            tokens = len(prompt) // 4

            assert tokens < 200, f"{task_type} prompt is {tokens} tokens"
