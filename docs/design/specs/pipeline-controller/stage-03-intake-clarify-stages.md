# Pipeline Controller Specification - Stage 3: Intake & Clarify Stages

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1 (Core), Stage 2 (Executor Interface)  
**Estimated Effort:** 4-5 days

---

## 1. Overview

### 1.1 Purpose

The Intake and Clarify stages are the entry point of the pipeline. They:

1. **INTAKE**: Parse and categorize the user's request, identify scope and initial questions
2. **CLARIFY**: Resolve ambiguities through Q&A, produce refined requirements

### 1.2 Stage Flow

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         INTAKE                                   │
│                                                                  │
│  Input: Raw user request string                                 │
│  Output: IntakeRecord with scope, priority, questions           │
│                                                                  │
│  "Add OAuth2 authentication" →                                  │
│     scope: feature_addition                                     │
│     priority: medium                                            │
│     questions: [Which OAuth provider?, What scopes needed?]     │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ (if questions.blocking exists)
┌─────────────────────────────────────────────────────────────────┐
│                         CLARIFY                                  │
│                                                                  │
│  Input: IntakeRecord + previous answers                         │
│  Output: ClarifiedRequirements with refined scope               │
│                                                                  │
│  Iterates until all blocking questions answered                 │
│  Escalates if human input required                              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
   ANALYZE (next stage)
```

---

## 2. INTAKE Stage

### 2.1 IntakeExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/intake.py

from typing import Any, Dict, List, Optional
import logging

from ..llm_stage_executor import LLMStageExecutor
from ..stage_executor import StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class IntakeExecutor(LLMStageExecutor):
    """
    INTAKE stage executor.
    
    Parses user request and produces an IntakeRecord with:
    - Detected scope (bug_fix, feature_addition, refactoring, etc.)
    - Priority assessment
    - Initial questions for clarification
    - Detected components/areas of codebase
    """
    
    stage_name = "intake"
    artifact_type = "intake_record"
    
    # No required input fields - this is the first stage
    required_input_fields = []
    
    # Fields we produce
    output_fields = [
        "request_id",
        "detected_scope", 
        "priority",
    ]
    
    # System prompt for intake analysis
    SYSTEM_PROMPT = """You are an expert software requirements analyst. Your task is to analyze a user's development request and produce a structured intake record.

You must:
1. Identify the TYPE of request (bug_fix, feature_addition, refactoring, documentation, testing, unclear)
2. Assess PRIORITY based on keywords and context (low, medium, high, critical)
3. Generate CLARIFYING QUESTIONS for any ambiguities
4. Identify likely AFFECTED COMPONENTS based on the request

Output your analysis as YAML in a code block.

IMPORTANT:
- Questions should be specific and actionable
- Mark questions as "blocking" if the answer is required before proceeding
- Mark questions as "optional" if they can be answered later
- Be conservative with scope detection - prefer "unclear" if genuinely ambiguous
"""

    USER_MESSAGE_TEMPLATE = """Analyze this development request:

REQUEST:
{request}

{context_section}

Produce an intake record with the following structure:

```yaml
request_id: "{request_id}"
original_request: "{request}"
detected_scope: "feature_addition"  # or bug_fix, refactoring, documentation, testing, unclear
priority: "medium"  # low, medium, high, critical
confidence: 0.85  # 0.0-1.0 confidence in scope detection

initial_questions:
  - question: "What OAuth provider should be used?"
    priority: "blocking"  # or "optional"
    context: "Need to know for library selection"
  - question: "..."
    priority: "optional"

detected_components:
  - name: "authentication"
    confidence: 0.9
  - name: "user_management"  
    confidence: 0.7

keywords:
  - "oauth"
  - "authentication"
  - "login"

estimated_complexity: "medium"  # low, medium, high
```
"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._request_counter = 0
    
    def get_system_prompt(self, context: StageContext) -> str:
        """Get system prompt for intake."""
        return self.SYSTEM_PROMPT
    
    def get_user_message(self, context: StageContext) -> str:
        """Build user message from context."""
        # Generate request ID
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self._request_counter += 1
        request_id = f"REQ-{timestamp}-{self._request_counter:04d}"
        
        # Build context section
        context_section = ""
        if context.input_artifact.get("project_context"):
            context_section = f"\nPROJECT CONTEXT:\n{context.input_artifact['project_context']}"
        
        return self.USER_MESSAGE_TEMPLATE.format(
            request=context.user_request,
            request_id=request_id,
            context_section=context_section,
        )
    
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Parse LLM response into IntakeRecord."""
        # Get text response
        response_text = llm_result.get("response", "")
        if not response_text:
            response_text = llm_result.get("content", "")
        
        # Extract YAML
        artifact = self.extract_yaml_from_response(response_text)
        
        if artifact is None:
            logger.error("Failed to extract YAML from intake response")
            return None
        
        # Validate required fields
        required = ["request_id", "detected_scope"]
        for field in required:
            if field not in artifact:
                logger.error(f"Missing required field in intake: {field}")
                return None
        
        # Ensure lists exist
        artifact.setdefault("initial_questions", [])
        artifact.setdefault("detected_components", [])
        artifact.setdefault("keywords", [])
        
        # Add original request if not present
        if "original_request" not in artifact:
            artifact["original_request"] = context.user_request
        
        # Default priority
        if "priority" not in artifact:
            artifact["priority"] = "medium"
        
        return artifact
    
    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """Validate intake artifact."""
        from ..stage_executor import OutputValidation
        
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])
        
        errors = []
        warnings = []
        
        # Required fields
        if not artifact.get("request_id"):
            errors.append("Missing request_id")
        if not artifact.get("detected_scope"):
            errors.append("Missing detected_scope")
        
        # Validate scope value
        valid_scopes = ["bug_fix", "feature_addition", "refactoring", 
                       "documentation", "testing", "unclear"]
        if artifact.get("detected_scope") not in valid_scopes:
            errors.append(f"Invalid scope: {artifact.get('detected_scope')}")
        
        # Validate priority
        valid_priorities = ["low", "medium", "high", "critical"]
        if artifact.get("priority") not in valid_priorities:
            warnings.append(f"Invalid priority, defaulting to medium")
        
        # Warn if no questions for unclear scope
        if artifact.get("detected_scope") == "unclear":
            if not artifact.get("initial_questions"):
                warnings.append("Unclear scope but no clarifying questions")
        
        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


# Factory function for registration
def create_intake_executor(config: Optional[Dict] = None) -> IntakeExecutor:
    """Create IntakeExecutor instance."""
    return IntakeExecutor(config)
```

### 2.2 IntakeRecord Schema

```yaml
# Schema for IntakeRecord artifact

request_id: string        # Unique ID for this request
original_request: string  # Original user request text

detected_scope: enum
  - bug_fix
  - feature_addition  
  - refactoring
  - documentation
  - testing
  - unclear

priority: enum
  - low
  - medium
  - high
  - critical

confidence: number  # 0.0-1.0

initial_questions:
  - question: string
    priority: enum [blocking, optional]
    context: string  # Why this question matters

detected_components:
  - name: string
    confidence: number

keywords: [string]

estimated_complexity: enum [low, medium, high]
```

---

## 3. CLARIFY Stage

### 3.1 ClarifyExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/clarify.py

from typing import Any, Dict, List, Optional
import logging

from ..llm_stage_executor import LLMStageExecutor
from ..stage_executor import StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class ClarifyExecutor(LLMStageExecutor):
    """
    CLARIFY stage executor.
    
    Iteratively resolves questions from INTAKE stage through:
    - Asking blocking questions
    - Incorporating answers
    - Producing refined requirements
    
    This stage may escalate to request human answers.
    """
    
    stage_name = "clarify"
    artifact_type = "clarified_requirements"
    
    required_input_fields = ["request_id", "detected_scope"]
    
    output_fields = [
        "request_id",
        "clarified_requirements",
        "scope_confirmed",
    ]
    
    SYSTEM_PROMPT = """You are a software requirements analyst refining a development request.

You have access to:
1. The original request
2. Initial analysis from intake
3. Any answers provided to clarifying questions

Your task is to:
1. Incorporate any answers into a refined understanding
2. Identify if there are remaining BLOCKING questions
3. Produce a clear, unambiguous requirements statement

If blocking questions remain unanswered, you should indicate this - do NOT make assumptions.

Output your analysis as YAML in a code block.
"""

    USER_MESSAGE_TEMPLATE = """Refine these requirements based on the information gathered:

ORIGINAL REQUEST:
{original_request}

INTAKE ANALYSIS:
- Scope: {scope}
- Priority: {priority}
- Initial Questions: {questions}

{answers_section}

{feedback_section}

Produce clarified requirements:

```yaml
request_id: "{request_id}"
clarified_requirements: |
  Clear, unambiguous description of what needs to be done.
  Include all relevant details from the answers.

scope_confirmed: true  # or false if still unclear

answered_questions:
  - question: "What OAuth provider?"
    answer: "Google OAuth 2.0"
    incorporated: true

remaining_questions:
  - question: "What scopes are needed?"
    priority: "blocking"
    reason: "Required for implementation"

refined_scope: "feature_addition"  # May change from initial detection
refined_components:
  - name: "auth_module"
    files_likely_affected:
      - "src/auth/oauth.py"
      - "src/auth/providers.py"

ready_for_analysis: true  # false if blocking questions remain
```
"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_clarification_rounds = config.get("max_rounds", 3) if config else 3
    
    def _execute(self, context: StageContext) -> StageResult:
        """Execute clarify stage with potential iteration."""
        input_artifact = context.input_artifact
        
        # Check if there are blocking questions
        initial_questions = input_artifact.get("initial_questions", [])
        blocking_questions = [
            q for q in initial_questions 
            if q.get("priority") == "blocking"
        ]
        
        # If no blocking questions, we can skip clarification
        if not blocking_questions:
            logger.info("No blocking questions, skipping clarification")
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.COMPLETED,
                artifact=self._create_passthrough_artifact(context),
            )
        
        # Check if we have answers (from feedback or context)
        answers = input_artifact.get("question_answers", {})
        feedback = context.previous_feedback
        
        # If we have blocking questions but no answers, escalate
        if blocking_questions and not answers and not feedback:
            return self._escalate_for_answers(context, blocking_questions)
        
        # Run LLM clarification with available information
        return super()._execute(context)
    
    def get_system_prompt(self, context: StageContext) -> str:
        """Get system prompt for clarify."""
        return self.SYSTEM_PROMPT
    
    def get_user_message(self, context: StageContext) -> str:
        """Build user message with intake data and answers."""
        artifact = context.input_artifact
        
        # Format questions
        questions = artifact.get("initial_questions", [])
        questions_str = "\n".join([
            f"  - [{q.get('priority', 'optional')}] {q.get('question', 'N/A')}"
            for q in questions
        ]) or "  (none)"
        
        # Format answers section
        answers = artifact.get("question_answers", {})
        answers_section = ""
        if answers:
            answers_lines = [f"  - Q: {q}\n    A: {a}" for q, a in answers.items()]
            answers_section = "ANSWERS PROVIDED:\n" + "\n".join(answers_lines)
        
        # Format feedback section
        feedback_section = ""
        if context.previous_feedback:
            feedback_section = f"ADDITIONAL CONTEXT FROM USER:\n{context.previous_feedback}"
        
        return self.USER_MESSAGE_TEMPLATE.format(
            original_request=artifact.get("original_request", context.user_request),
            scope=artifact.get("detected_scope", "unknown"),
            priority=artifact.get("priority", "medium"),
            questions=questions_str,
            answers_section=answers_section,
            feedback_section=feedback_section,
            request_id=artifact.get("request_id", "REQ-UNKNOWN"),
        )
    
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Parse clarification response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")
        
        artifact = self.extract_yaml_from_response(response_text)
        
        if artifact is None:
            logger.error("Failed to extract YAML from clarify response")
            return None
        
        # Carry forward request_id
        if "request_id" not in artifact:
            artifact["request_id"] = context.input_artifact.get("request_id")
        
        # Ensure required fields
        artifact.setdefault("clarified_requirements", "")
        artifact.setdefault("scope_confirmed", False)
        artifact.setdefault("answered_questions", [])
        artifact.setdefault("remaining_questions", [])
        artifact.setdefault("ready_for_analysis", False)
        
        return artifact
    
    def _create_passthrough_artifact(self, context: StageContext) -> Dict[str, Any]:
        """Create artifact when no clarification needed."""
        input_artifact = context.input_artifact
        
        return {
            "request_id": input_artifact.get("request_id"),
            "clarified_requirements": input_artifact.get("original_request"),
            "scope_confirmed": True,
            "answered_questions": [],
            "remaining_questions": [],
            "refined_scope": input_artifact.get("detected_scope"),
            "refined_components": input_artifact.get("detected_components", []),
            "ready_for_analysis": True,
            # Carry forward
            "original_request": input_artifact.get("original_request"),
            "priority": input_artifact.get("priority"),
            "keywords": input_artifact.get("keywords", []),
        }
    
    def _escalate_for_answers(
        self,
        context: StageContext,
        blocking_questions: List[Dict],
    ) -> StageResult:
        """Escalate to get answers to blocking questions."""
        questions_text = "\n".join([
            f"  - {q.get('question', 'N/A')} (context: {q.get('context', 'N/A')})"
            for q in blocking_questions
        ])
        
        return self.escalate(
            context=context,
            reason=f"Blocking questions require answers:\n{questions_text}",
            partial_artifact={
                "request_id": context.input_artifact.get("request_id"),
                "blocking_questions": blocking_questions,
                "status": "awaiting_answers",
            },
        )
    
    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """Validate clarify artifact."""
        from ..stage_executor import OutputValidation
        
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])
        
        errors = []
        warnings = []
        
        # Must have clarified requirements
        if not artifact.get("clarified_requirements"):
            errors.append("Missing clarified_requirements")
        
        # Check for remaining blocking questions
        remaining = artifact.get("remaining_questions", [])
        blocking_remaining = [q for q in remaining if q.get("priority") == "blocking"]
        
        if blocking_remaining and artifact.get("ready_for_analysis"):
            warnings.append("Marked ready but blocking questions remain")
        
        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


# Factory function
def create_clarify_executor(config: Optional[Dict] = None) -> ClarifyExecutor:
    """Create ClarifyExecutor instance."""
    return ClarifyExecutor(config)
```

### 3.2 ClarifiedRequirements Schema

```yaml
# Schema for ClarifiedRequirements artifact

request_id: string
clarified_requirements: string  # Full refined requirements text

scope_confirmed: boolean

answered_questions:
  - question: string
    answer: string
    incorporated: boolean  # Was answer used in refinement?

remaining_questions:
  - question: string
    priority: enum [blocking, optional]
    reason: string

refined_scope: enum [bug_fix, feature_addition, refactoring, etc.]

refined_components:
  - name: string
    files_likely_affected: [string]

ready_for_analysis: boolean  # Can proceed to ANALYZE?

# Carried forward from INTAKE
original_request: string
priority: string
keywords: [string]
```

---

## 4. Question-Answer Workflow

### 4.1 Answer Integration Pattern

When clarification is needed, the pipeline supports multiple answer sources:

```python
# Answer sources in priority order:

1. Direct answers in artifact:
   input_artifact["question_answers"] = {
       "What OAuth provider?": "Google OAuth 2.0",
       "What scopes?": "openid, email, profile"
   }

2. Feedback from escalation:
   context.previous_feedback = "Use Google OAuth with openid scope"
   
3. Interactive prompt (DefaultEscalationHandler):
   > Blocking questions require answers:
   >   - What OAuth provider?
   > 
   > Provide answers or feedback:
```

### 4.2 Pipeline Configuration for Clarify

```yaml
# .agentforge/config/pipeline_config.yaml

stages:
  clarify:
    enabled: true
    max_iterations: 3
    auto_skip_if_no_blocking_questions: true
    escalation_mode: "interactive"  # or "file", "webhook"
    timeout_seconds: 300
```

---

## 5. Integration with Existing Contracts

### 5.1 Wrapping Existing Implementation

The existing `spec.intake.v1` and `spec.clarify.v1` contracts can be reused:

```python
# Alternative: ContractStageExecutor wrapper

from ..contract_stage_executor import ContractStageExecutor

# Create intake executor using existing contract
intake_executor = ContractStageExecutor(
    stage_name="intake",
    contract_id="spec.intake.v1",
    input_mapping={
        "raw_request": "original_request",
        "priority": "priority",
    },
    output_mapping={
        # Contract output -> artifact field
    },
)

# Create clarify executor using existing contract
clarify_executor = ContractStageExecutor(
    stage_name="clarify", 
    contract_id="spec.clarify.v1",
    input_mapping={
        "intake_record": None,  # Pass whole artifact
        "answer": "question_answers",
    },
)
```

### 5.2 Choosing Between Implementations

| Approach | Pros | Cons |
|----------|------|------|
| LLMStageExecutor | Full control, custom prompts | More code to maintain |
| ContractStageExecutor | Reuse existing contracts | Less flexibility |

**Recommendation:** Use LLMStageExecutor for new pipelines, ContractStageExecutor for migration.

---

## 6. Directory Structure

```
src/agentforge/core/pipeline/stages/
├── __init__.py
├── intake.py           # IntakeExecutor
├── clarify.py          # ClarifyExecutor
└── _prompts/
    ├── intake_system.txt
    └── clarify_system.txt
```

---

## 7. Test Specification

### 7.1 Unit Tests

```python
# tests/unit/pipeline/stages/test_intake.py

class TestIntakeExecutor:
    """Tests for IntakeExecutor."""
    
    def test_parses_simple_request(self, mock_llm):
        """Simple request produces valid IntakeRecord."""
        
    def test_detects_bug_fix_scope(self, mock_llm):
        """Bug fix requests detected correctly."""
        
    def test_detects_feature_addition_scope(self, mock_llm):
        """Feature requests detected correctly."""
        
    def test_generates_blocking_questions_for_unclear(self, mock_llm):
        """Unclear requests generate blocking questions."""
        
    def test_generates_unique_request_ids(self):
        """Each execution generates unique request_id."""
        
    def test_validates_output_schema(self):
        """Output validation catches missing fields."""


class TestClarifyExecutor:
    """Tests for ClarifyExecutor."""
    
    def test_skips_when_no_blocking_questions(self):
        """Skips clarification if no blocking questions."""
        
    def test_escalates_when_blocking_unanswered(self):
        """Escalates when blocking questions have no answers."""
        
    def test_incorporates_answers_into_requirements(self, mock_llm):
        """Answers are incorporated into clarified requirements."""
        
    def test_handles_feedback_as_answers(self, mock_llm):
        """Feedback from escalation is treated as input."""
        
    def test_marks_ready_when_complete(self, mock_llm):
        """Sets ready_for_analysis when all blocking answered."""
```

### 7.2 Integration Tests

```python
# tests/integration/pipeline/stages/test_intake_clarify.py

class TestIntakeClarifyWorkflow:
    """Integration tests for intake->clarify flow."""
    
    def test_intake_to_clarify_artifact_flow(self, mock_llm, tmp_path):
        """IntakeRecord flows correctly to ClarifyExecutor."""
        
    def test_clarify_escalation_and_resume(self, mock_llm, tmp_path):
        """Escalation pauses, answer resumes clarification."""
        
    def test_full_intake_clarify_with_answers(self, mock_llm, tmp_path):
        """Complete flow with blocking questions and answers."""
```

---

## 8. Success Criteria

1. **Functional:**
   - [ ] IntakeExecutor produces valid IntakeRecord
   - [ ] ClarifyExecutor handles blocking questions
   - [ ] Escalation works for unanswered questions
   - [ ] Answer integration refines requirements

2. **Quality:**
   - [ ] Scope detection accuracy > 80%
   - [ ] Question generation is relevant
   - [ ] Clarified requirements are actionable

3. **Integration:**
   - [ ] Artifacts flow correctly between stages
   - [ ] Works with PipelineController
   - [ ] State persists across restarts

---

## 9. Dependencies

- **Stage 1:** PipelineController, StageResult
- **Stage 2:** LLMStageExecutor, StageContext
- **Existing:** MinimalContextExecutor, LLM abstraction

---

*Next: Stage 4 - Analyze & Spec Stages*
