# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-drafter
# @test_path: tests/unit/contracts/test_drafter.py

"""
Contract Drafter
================

LLM-powered contract generation from natural language requirements.

The drafter analyzes a user request and generates a ContractDraft
containing stage contracts, validation rules, escalation triggers,
and quality gates. The draft is then reviewed by a human before
becoming enforceable.

Key Design Principles:
- Contracts encode human judgment for autonomous execution
- When uncertain, surface questions rather than assuming
- Include rationale for all constraints to aid human review
- Balance completeness with minimalism

Usage:
    ```python
    drafter = ContractDrafter(llm_client)
    draft = await drafter.draft(
        user_request="Add user authentication with JWT",
        codebase_context=profile,
    )
    # Human reviews draft...
    approved = ApprovedContracts.from_draft(draft, ...)
    ```
"""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from agentforge.core.llm.interface import LLMClient, LLMResponse, ThinkingConfig

from .draft import (
    Assumption,
    ContractDraft,
    EscalationTrigger,
    OpenQuestion,
    QualityGate,
    StageContract,
    ValidationRule,
)


@dataclass
class CodebaseContext:
    """Context about the codebase for contract drafting.

    Provides the drafter with information about existing patterns,
    conventions, and constraints in the codebase.
    """

    project_name: str = ""
    language: str = ""
    framework: str = ""
    patterns: list[str] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    existing_contracts: list[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Format as context for the prompt."""
        lines = []
        if self.project_name:
            lines.append(f"Project: {self.project_name}")
        if self.language:
            lines.append(f"Language: {self.language}")
        if self.framework:
            lines.append(f"Framework: {self.framework}")
        if self.patterns:
            lines.append(f"Patterns: {', '.join(self.patterns)}")
        if self.conventions:
            lines.append("Conventions:")
            for conv in self.conventions:
                lines.append(f"  - {conv}")
        return "\n".join(lines) if lines else "No codebase context provided."


@dataclass
class DrafterConfig:
    """Configuration for the contract drafter."""

    # LLM settings
    use_thinking: bool = True
    thinking_budget: int = 16000
    max_tokens: int = 8192

    # Drafting behavior
    include_all_stages: bool = False  # If True, include all pipeline stages
    default_stages: list[str] = field(
        default_factory=lambda: ["intake", "clarify", "analyze", "spec", "implement", "validate"]
    )

    # Output settings
    include_rationale: bool = True
    max_questions: int = 5
    max_assumptions: int = 10


class ContractDrafter:
    """Drafts contracts from natural language requirements.

    Uses an LLM to analyze the request and generate appropriate
    contracts including stage schemas, validation rules, escalation
    triggers, and quality gates.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: DrafterConfig | None = None,
        system_prompt_path: Path | None = None,
    ):
        """Initialize the contract drafter.

        Args:
            llm_client: LLM client for generation
            config: Drafter configuration
            system_prompt_path: Path to custom system prompt YAML
        """
        self.llm_client = llm_client
        self.config = config or DrafterConfig()
        self.system_prompt = self._load_system_prompt(system_prompt_path)

    # Section formatters: (key, header, is_list, custom_formatter)
    _PROMPT_SECTION_KEYS = [
        ("role", "Role", False),
        ("responsibilities", "Responsibilities", True),
        ("principles", "Principles", True),
        ("output_format", "Output Format", False),
    ]

    def _format_prompt_section(self, key: str, header: str, data: dict, is_list: bool) -> str | None:
        """Format a single prompt section if present."""
        if key not in data:
            return None
        value = data[key]
        if is_list:
            return f"# {header}\n" + "\n".join(f"- {item}" for item in value)
        return f"# {header}\n{value}"

    def _format_stages_section(self, data: dict) -> str | None:
        """Format stages section if present."""
        if "stages" not in data:
            return None
        lines = []
        for stage in data["stages"]:
            outputs = ", ".join(stage.get("typical_outputs", []))
            lines.append(f"- {stage['name']}: {stage['purpose']} (outputs: {outputs})")
        return f"# Pipeline Stages\n" + "\n".join(lines)

    def _load_system_prompt(self, path: Path | None = None) -> str:
        """Load the system prompt for contract drafting."""
        if path is None:
            path = Path(__file__).parent / "prompts" / "drafter_system.yaml"

        if not path.exists():
            return self._get_default_system_prompt()

        with open(path, encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)

        sections = []
        for key, header, is_list in self._PROMPT_SECTION_KEYS:
            section = self._format_prompt_section(key, header, prompt_data, is_list)
            if section:
                sections.append(section)

        stages = self._format_stages_section(prompt_data)
        if stages:
            sections.insert(3, stages)  # Insert before output_format

        return "\n\n".join(sections)

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if file not found."""
        return """# Role
You are a Contract Architect for autonomous agent systems.
Your job is to translate natural language requirements into
machine-verifiable contracts that will govern agent execution.

# Responsibilities
- Analyze requirements to identify scope and complexity
- Draft stage-by-stage contracts with precise schemas
- Identify validation rules that catch errors early
- Propose escalation triggers for human judgment points
- Surface assumptions so humans can validate them

# Principles
- COMPLETENESS: If not specified, the agent will not enforce it
- PRECISION: Ambiguity leads to drift and unexpected behavior
- ESCALATION: When uncertain, escalate to human

# Output Format
Produce a YAML document with:
- draft_id, request_summary, detected_scope, confidence
- stage_contracts with input/output requirements
- escalation_triggers for human judgment points
- quality_gates for stage transitions
- open_questions for clarifications needed
- assumptions that need validation
"""

    def draft(
        self,
        user_request: str,
        codebase_context: CodebaseContext | None = None,
        additional_context: str | None = None,
    ) -> ContractDraft:
        """Draft contracts for a user request.

        Args:
            user_request: Natural language request from user
            codebase_context: Information about the codebase
            additional_context: Any additional context to include

        Returns:
            ContractDraft with proposed contracts
        """
        # Build the user message
        user_message = self._build_user_message(
            user_request, codebase_context, additional_context
        )

        # Configure thinking if enabled
        thinking = None
        if self.config.use_thinking:
            thinking = ThinkingConfig(
                enabled=True,
                budget_tokens=self.config.thinking_budget,
            )

        # Make LLM call
        response = self.llm_client.complete(
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}],
            thinking=thinking,
            max_tokens=self.config.max_tokens,
        )

        # Parse response into ContractDraft
        return self._parse_response(response, user_request)

    def _build_user_message(
        self,
        user_request: str,
        codebase_context: CodebaseContext | None,
        additional_context: str | None,
    ) -> str:
        """Build the user message for the LLM."""
        sections = [
            "# User Request",
            user_request,
        ]

        if codebase_context:
            sections.extend([
                "",
                "# Codebase Context",
                codebase_context.to_prompt_context(),
            ])

        if additional_context:
            sections.extend([
                "",
                "# Additional Context",
                additional_context,
            ])

        sections.extend([
            "",
            "# Instructions",
            "Draft contracts for this request following the output format specified.",
            "Include all relevant stages, validation rules, and escalation triggers.",
            "Surface any assumptions or questions for human review.",
            "Output ONLY the YAML document, no other text.",
        ])

        return "\n".join(sections)

    def _parse_response(
        self,
        response: LLMResponse,
        original_request: str,
    ) -> ContractDraft:
        """Parse LLM response into a ContractDraft."""
        content = response.content

        # Extract YAML from response (may be wrapped in code blocks)
        yaml_content = self._extract_yaml(content)

        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            # If YAML parsing fails, create minimal draft with error
            return self._create_error_draft(original_request, str(e))

        if not isinstance(data, dict):
            return self._create_error_draft(
                original_request,
                f"Expected dict, got {type(data).__name__}",
            )

        # Build ContractDraft from parsed data
        return self._build_draft_from_data(data, original_request)

    def _extract_yaml(self, content: str) -> str:
        """Extract YAML content from response."""
        # Check for code blocks
        code_block_pattern = r"```(?:yaml)?\s*\n(.*?)\n```"
        match = re.search(code_block_pattern, content, re.DOTALL)
        if match:
            return match.group(1)

        # If no code block, assume entire content is YAML
        return content.strip()

    def _build_draft_from_data(
        self,
        data: dict[str, Any],
        original_request: str,
    ) -> ContractDraft:
        """Build a ContractDraft from parsed YAML data."""
        # Generate draft ID if not provided
        draft_id = data.get("draft_id") or self._generate_draft_id()

        # Parse stage contracts
        stage_contracts = []
        for sc_data in data.get("stage_contracts", []):
            stage_contracts.append(self._parse_stage_contract(sc_data))

        # Parse escalation triggers
        escalation_triggers = []
        for et_data in data.get("escalation_triggers", []):
            escalation_triggers.append(EscalationTrigger.from_dict(et_data))

        # Parse quality gates
        quality_gates = []
        for qg_data in data.get("quality_gates", []):
            quality_gates.append(QualityGate.from_dict(qg_data))

        # Parse open questions
        open_questions = []
        for oq_data in data.get("open_questions", []):
            open_questions.append(OpenQuestion.from_dict(oq_data))

        # Parse assumptions
        assumptions = []
        for a_data in data.get("assumptions", []):
            assumptions.append(Assumption.from_dict(a_data))

        return ContractDraft(
            draft_id=draft_id,
            request_summary=data.get("request_summary", original_request[:100]),
            detected_scope=data.get("detected_scope", "unknown"),
            stage_contracts=stage_contracts,
            escalation_triggers=escalation_triggers,
            quality_gates=quality_gates,
            confidence=data.get("confidence", 0.5),
            open_questions=open_questions,
            assumptions=assumptions,
        )

    def _parse_stage_contract(self, data: dict[str, Any]) -> StageContract:
        """Parse a single stage contract from data."""
        # Parse validation rules
        validation_rules = []
        for vr_data in data.get("validation_rules", []):
            validation_rules.append(ValidationRule.from_dict(vr_data))

        return StageContract(
            stage_name=data.get("stage_name", ""),
            input_schema=data.get("input_schema", {}),
            input_requirements=data.get("input_requirements", []),
            output_schema=data.get("output_schema", {}),
            output_requirements=data.get("output_requirements", []),
            validation_rules=validation_rules,
            escalation_conditions=data.get("escalation_conditions", []),
            rationale=data.get("rationale", ""),
        )

    def _create_error_draft(self, request: str, error: str) -> ContractDraft:
        """Create a minimal draft when parsing fails."""
        return ContractDraft(
            draft_id=self._generate_draft_id(),
            request_summary=request[:100],
            detected_scope="unknown",
            confidence=0.0,
            open_questions=[
                OpenQuestion(
                    question_id="Q-ERROR",
                    question=f"Contract drafting failed: {error}",
                    priority="high",
                )
            ],
        )

    def _generate_draft_id(self) -> str:
        """Generate a unique draft ID."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        return f"DRAFT-{timestamp}"

    def refine(
        self,
        draft: ContractDraft,
        feedback: str,
    ) -> ContractDraft:
        """Refine a draft based on human feedback.

        Args:
            draft: The draft to refine
            feedback: Human feedback on the draft

        Returns:
            Refined ContractDraft
        """
        # Build refinement message
        user_message = f"""# Current Draft
{draft.to_yaml()}

# Human Feedback
{feedback}

# Instructions
Refine the contract draft based on the feedback above.
Preserve what works well, adjust what was criticized.
Output the complete revised YAML document.
"""

        thinking = None
        if self.config.use_thinking:
            thinking = ThinkingConfig(
                enabled=True,
                budget_tokens=self.config.thinking_budget,
            )

        response = self.llm_client.complete(
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}],
            thinking=thinking,
            max_tokens=self.config.max_tokens,
        )

        refined = self._parse_response(response, draft.request_summary)

        # Add revision to history
        refined.add_revision(
            changes=["Refined based on human feedback"],
            reason=feedback[:200],
        )

        return refined
