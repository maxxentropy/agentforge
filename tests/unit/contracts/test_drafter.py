# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-drafter-tests

"""Tests for contract drafter."""

import pytest

from agentforge.core.contracts.drafter import (
    CodebaseContext,
    ContractDrafter,
    DrafterConfig,
)
from agentforge.core.contracts.draft import ContractDraft
from agentforge.core.llm.factory import LLMClientFactory


class TestCodebaseContext:
    """Tests for CodebaseContext."""

    def test_empty_context(self):
        """Empty context produces minimal output."""
        ctx = CodebaseContext()
        result = ctx.to_prompt_context()

        assert result == "No codebase context provided.", "Expected result to equal 'No codebase context provid..."

    def test_full_context(self):
        """Full context formats properly."""
        ctx = CodebaseContext(
            project_name="MyProject",
            language="Python",
            framework="FastAPI",
            patterns=["Repository", "Service Layer"],
            conventions=["Use type hints", "Write docstrings"],
        )

        result = ctx.to_prompt_context()

        assert "Project: MyProject" in result, "Expected 'Project: MyProject' in result"
        assert "Language: Python" in result, "Expected 'Language: Python' in result"
        assert "Framework: FastAPI" in result, "Expected 'Framework: FastAPI' in result"
        assert "Repository" in result, "Expected 'Repository' in result"
        assert "Use type hints" in result, "Expected 'Use type hints' in result"


class TestDrafterConfig:
    """Tests for DrafterConfig."""

    def test_default_config(self):
        """Default config has reasonable values."""
        config = DrafterConfig()

        assert config.use_thinking is True, "Expected config.use_thinking is True"
        assert config.thinking_budget > 0, "Expected config.thinking_budget > 0"
        assert config.max_tokens > 0, "Expected config.max_tokens > 0"
        assert len(config.default_stages) > 0, "Expected len(config.default_stages) > 0"

    def test_custom_config(self):
        """Custom config overrides defaults."""
        config = DrafterConfig(
            use_thinking=False,
            max_tokens=4096,
            default_stages=["intake", "implement"],
        )

        assert config.use_thinking is False, "Expected config.use_thinking is False"
        assert config.max_tokens == 4096, "Expected config.max_tokens to equal 4096"
        assert len(config.default_stages) == 2, "Expected len(config.default_stages) to equal 2"


class TestContractDrafter:
    """Tests for ContractDrafter."""

    @pytest.fixture
    def mock_llm_response_yaml(self):
        """YAML response for successful drafting."""
        return """```yaml
draft_id: DRAFT-20240103-120000
request_summary: Add user authentication with JWT
detected_scope: feature
confidence: 0.85

stage_contracts:
  - stage_name: intake
    output_requirements:
      - request_id
      - detected_scope
      - auth_type
    validation_rules:
      - rule_id: R-001
        description: Auth type must be valid
        check_type: enum_constraint
        field_path: output.auth_type
        constraint:
          enum: [jwt, session, oauth]
        severity: error
        rationale: Only these auth methods are supported
    rationale: Capture initial request analysis

  - stage_name: clarify
    input_requirements:
      - request_id
    output_requirements:
      - clarified_requirements
      - token_strategy
    rationale: Resolve any ambiguities

escalation_triggers:
  - trigger_id: T-001
    condition: Confidence below 0.7
    severity: blocking
    prompt: Low confidence - please review
    rationale: Need human verification

quality_gates:
  - gate_id: G-001
    stage: spec
    checks:
      - All components defined
      - Security review completed
    failure_action: escalate

open_questions:
  - question_id: Q-001
    question: Should we support refresh tokens?
    priority: high
    suggested_answers:
      - Yes, with 7-day expiry
      - No, require re-auth

assumptions:
  - assumption_id: A-001
    statement: JWT tokens stored in httpOnly cookies
    confidence: 0.7
    impact_if_wrong: Security implications
    alternative: Use localStorage with XSS protection
```"""

    @pytest.fixture
    def mock_llm_client(self, mock_llm_response_yaml):
        """Create a simulated LLM client."""
        return LLMClientFactory.create_for_testing(
            responses=[{"content": mock_llm_response_yaml}]
        )

    def test_drafter_creation(self, mock_llm_client):
        """Create a contract drafter."""
        drafter = ContractDrafter(mock_llm_client)

        assert drafter.llm_client is mock_llm_client, "Expected drafter.llm_client is mock_llm_client"
        assert drafter.config is not None, "Expected drafter.config is not None"
        assert len(drafter.system_prompt) > 0, "Expected len(drafter.system_prompt) > 0"

    def test_drafter_with_config(self, mock_llm_client):
        """Drafter accepts custom config."""
        config = DrafterConfig(use_thinking=False)
        drafter = ContractDrafter(mock_llm_client, config=config)

        assert drafter.config.use_thinking is False, "Expected drafter.config.use_thinking is False"

    def test_draft_basic_request(self, mock_llm_client):
        """Draft contracts from basic request."""
        drafter = ContractDrafter(mock_llm_client)

        draft = drafter.draft("Add user authentication with JWT")

        assert isinstance(draft, ContractDraft), "Expected isinstance() to be truthy"
        assert draft.draft_id == "DRAFT-20240103-120000", "Expected draft.draft_id to equal 'DRAFT-20240103-120000'"
        assert draft.detected_scope == "feature", "Expected draft.detected_scope to equal 'feature'"
        assert draft.confidence == 0.85, "Expected draft.confidence to equal 0.85"

    def test_draft_includes_stages(self, mock_llm_client):
        """Draft includes stage contracts."""
        drafter = ContractDrafter(mock_llm_client)

        draft = drafter.draft("Add user authentication")

        assert len(draft.stage_contracts) >= 2, "Expected len(draft.stage_contracts) >= 2"
        assert draft.get_stage_contract("intake") is not None, "Expected draft.get_stage_contract('i... is not None"
        assert draft.get_stage_contract("clarify") is not None, "Expected draft.get_stage_contract('c... is not None"

    def test_draft_includes_validation_rules(self, mock_llm_client):
        """Stage contracts include validation rules."""
        drafter = ContractDrafter(mock_llm_client)

        draft = drafter.draft("Add auth")
        intake = draft.get_stage_contract("intake")

        assert intake is not None, "Expected intake is not None"
        assert len(intake.validation_rules) > 0, "Expected len(intake.validation_rules) > 0"
        assert intake.validation_rules[0].rule_id == "R-001", "Expected intake.validation_rules[0].... to equal 'R-001'"

    def test_draft_includes_triggers(self, mock_llm_client):
        """Draft includes escalation triggers."""
        drafter = ContractDrafter(mock_llm_client)

        draft = drafter.draft("Add auth")

        assert len(draft.escalation_triggers) > 0, "Expected len(draft.escalation_triggers) > 0"
        assert draft.escalation_triggers[0].trigger_id == "T-001", "Expected draft.escalation_triggers[0... to equal 'T-001'"

    def test_draft_includes_gates(self, mock_llm_client):
        """Draft includes quality gates."""
        drafter = ContractDrafter(mock_llm_client)

        draft = drafter.draft("Add auth")

        assert len(draft.quality_gates) > 0, "Expected len(draft.quality_gates) > 0"
        assert draft.quality_gates[0].gate_id == "G-001", "Expected draft.quality_gates[0].gate_id to equal 'G-001'"

    def test_draft_includes_questions(self, mock_llm_client):
        """Draft surfaces open questions."""
        drafter = ContractDrafter(mock_llm_client)

        draft = drafter.draft("Add auth")

        assert len(draft.open_questions) > 0, "Expected len(draft.open_questions) > 0"
        assert "refresh tokens" in draft.open_questions[0].question, "Expected 'refresh tokens' in draft.open_questions[0].que..."

    def test_draft_includes_assumptions(self, mock_llm_client):
        """Draft surfaces assumptions."""
        drafter = ContractDrafter(mock_llm_client)

        draft = drafter.draft("Add auth")

        assert len(draft.assumptions) > 0, "Expected len(draft.assumptions) > 0"
        assert draft.assumptions[0].confidence == 0.7, "Expected draft.assumptions[0].confid... to equal 0.7"

    def test_draft_with_codebase_context(self, mock_llm_client):
        """Draft uses codebase context."""
        drafter = ContractDrafter(mock_llm_client)
        ctx = CodebaseContext(
            project_name="AuthService",
            language="Python",
            framework="FastAPI",
        )

        draft = drafter.draft("Add auth", codebase_context=ctx)

        assert draft is not None, "Expected draft is not None"

    def test_draft_handles_yaml_without_codeblock(self):
        """Parser handles YAML without code block."""
        yaml_response = """draft_id: DRAFT-001
request_summary: Test request
detected_scope: bugfix
confidence: 0.9
stage_contracts: []
escalation_triggers: []
quality_gates: []
open_questions: []
assumptions: []
"""
        client = LLMClientFactory.create_for_testing(
            responses=[{"content": yaml_response}]
        )
        drafter = ContractDrafter(client)

        draft = drafter.draft("Fix bug")

        assert draft.draft_id == "DRAFT-001", "Expected draft.draft_id to equal 'DRAFT-001'"
        assert draft.detected_scope == "bugfix", "Expected draft.detected_scope to equal 'bugfix'"

    def test_draft_handles_invalid_yaml(self):
        """Parser handles invalid YAML gracefully."""
        client = LLMClientFactory.create_for_testing(
            responses=[{"content": "not: valid: yaml: [["}]
        )
        drafter = ContractDrafter(client)

        draft = drafter.draft("Some request")

        # Should return error draft, not crash
        assert draft is not None, "Expected draft is not None"
        assert draft.confidence == 0.0, "Expected draft.confidence to equal 0.0"
        assert len(draft.open_questions) > 0, "Expected len(draft.open_questions) > 0"
        assert "failed" in draft.open_questions[0].question.lower(), "Expected 'failed' in draft.open_questions[0].que..."

    def test_draft_handles_empty_response(self):
        """Parser handles empty response."""
        client = LLMClientFactory.create_for_testing(
            responses=[{"content": ""}]
        )
        drafter = ContractDrafter(client)

        draft = drafter.draft("Some request")

        # Should return error draft
        assert draft is not None, "Expected draft is not None"
        assert draft.confidence == 0.0, "Expected draft.confidence to equal 0.0"


class TestContractDrafterRefine:
    """Tests for refinement functionality."""

    @pytest.fixture
    def initial_draft(self):
        """Create an initial draft for refinement."""
        from agentforge.core.contracts.draft import (
            ContractDraft,
            StageContract,
        )

        return ContractDraft(
            draft_id="DRAFT-001",
            request_summary="Add authentication",
            detected_scope="feature",
            stage_contracts=[
                StageContract(stage_name="intake"),
            ],
        )

    def test_refine_adds_revision(self, initial_draft):
        """Refinement adds to revision history."""
        refined_yaml = """draft_id: DRAFT-001
request_summary: Add authentication
detected_scope: feature
confidence: 0.9
stage_contracts:
  - stage_name: intake
    output_requirements:
      - request_id
      - auth_method
escalation_triggers: []
quality_gates: []
open_questions: []
assumptions: []
"""
        client = LLMClientFactory.create_for_testing(
            responses=[{"content": refined_yaml}]
        )
        drafter = ContractDrafter(client)

        refined = drafter.refine(initial_draft, "Add auth_method to outputs")

        assert len(refined.revision_history) == 1, "Expected len(refined.revision_history) to equal 1"
        assert "auth_method" in refined.revision_history[0].reason.lower(), "Expected 'auth_method' in refined.revision_history[0]..."
        assert "Refined based on human feedback" in refined.revision_history[0].changes[0], "Expected 'Refined based on human fee... in refined.revision_history[0]..."


class TestDrafterSystemPrompt:
    """Tests for system prompt loading."""

    def test_default_prompt_exists(self):
        """Default system prompt is loaded."""
        client = LLMClientFactory.create_for_testing(
            responses=[{"content": "draft_id: X\ndetected_scope: feature"}]
        )
        drafter = ContractDrafter(client)

        assert len(drafter.system_prompt) > 100, "Expected len(drafter.system_prompt) > 100"
        assert "Contract" in drafter.system_prompt, "Expected 'Contract' in drafter.system_prompt"

    def test_prompt_includes_role(self):
        """System prompt includes role definition."""
        client = LLMClientFactory.create_for_testing(
            responses=[{"content": "draft_id: X\ndetected_scope: feature"}]
        )
        drafter = ContractDrafter(client)

        assert "Role" in drafter.system_prompt or "role" in drafter.system_prompt.lower(), "Assertion failed"

    def test_prompt_includes_output_format(self):
        """System prompt includes output format."""
        client = LLMClientFactory.create_for_testing(
            responses=[{"content": "draft_id: X\ndetected_scope: feature"}]
        )
        drafter = ContractDrafter(client)

        assert "yaml" in drafter.system_prompt.lower(), "Expected 'yaml' in drafter.system_prompt.lower()"
