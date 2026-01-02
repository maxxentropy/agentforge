# Pipeline Controller Specification - Stage 4: Analyze & Spec Stages

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1-3  
**Estimated Effort:** 5-6 days

---

## 1. Overview

### 1.1 Purpose

The Analyze and Spec stages bridge requirements to implementation:

1. **ANALYZE**: Deep codebase analysis to understand impact and dependencies
2. **SPEC**: Generate detailed technical specification with components and test cases

### 1.2 Stage Flow

```
ClarifiedRequirements (from CLARIFY)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ANALYZE                                  │
│                                                                  │
│  Input: Clarified requirements + codebase context               │
│  Tools: search_code, read_file, find_related                    │
│  Output: AnalysisResult with affected files, components, risks  │
│                                                                  │
│  Actions:                                                       │
│  1. Search codebase for related code                            │
│  2. Identify affected files and modules                         │
│  3. Map dependencies                                            │
│  4. Assess risks and complexity                                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                          SPEC                                    │
│                                                                  │
│  Input: AnalysisResult + clarified requirements                 │
│  Output: Specification with components, interfaces, tests       │
│                                                                  │
│  Actions:                                                       │
│  1. Design component architecture                               │
│  2. Define interfaces and contracts                             │
│  3. Create test case specifications                             │
│  4. Define acceptance criteria                                  │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
   RED (test generation stage)
```

---

## 2. ANALYZE Stage

### 2.1 AnalyzeExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/analyze.py

from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

from ..llm_stage_executor import ToolBasedStageExecutor
from ..stage_executor import StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class AnalyzeExecutor(ToolBasedStageExecutor):
    """
    ANALYZE stage executor.
    
    Performs deep codebase analysis to understand:
    - What files/modules are affected
    - Dependencies between components
    - Potential risks and conflicts
    - Complexity assessment
    
    Uses tool calls (search_code, read_file) to gather information.
    """
    
    stage_name = "analyze"
    artifact_type = "analysis_result"
    
    required_input_fields = ["request_id", "clarified_requirements"]
    
    output_fields = [
        "request_id",
        "analysis",
        "affected_files",
        "components",
    ]
    
    # Tools available for analysis
    tools = [
        {
            "name": "search_code",
            "description": "Search codebase for patterns, symbols, or concepts",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern or query"},
                    "file_pattern": {"type": "string", "description": "Optional file glob pattern"},
                    "search_type": {"type": "string", "enum": ["regex", "semantic"]},
                },
                "required": ["pattern"],
            },
        },
        {
            "name": "read_file",
            "description": "Read contents of a source file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to project root"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "find_related",
            "description": "Find files related to a given file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Source file path"},
                    "type": {"type": "string", "enum": ["imports", "same_dir", "tests", "all"]},
                },
                "required": ["file_path"],
            },
        },
        {
            "name": "submit_analysis",
            "description": "Submit the final analysis result",
            "input_schema": {
                "type": "object",
                "properties": {
                    "analysis_summary": {"type": "string"},
                    "affected_files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "change_type": {"type": "string", "enum": ["modify", "create", "delete"]},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "components": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "files": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "risks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                                "mitigation": {"type": "string"},
                            },
                        },
                    },
                    "complexity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "estimated_effort": {"type": "string"},
                },
                "required": ["analysis_summary", "affected_files", "components"],
            },
        },
    ]
    
    artifact_tool_name = "submit_analysis"
    
    SYSTEM_PROMPT = """You are an expert software architect analyzing a codebase to understand the impact of a proposed change.

Your task is to:
1. Search the codebase for relevant code using search_code
2. Read key files to understand the current implementation
3. Identify all files that will need to be modified
4. Map dependencies and potential conflicts
5. Assess risks and complexity

You have access to these tools:
- search_code: Search for patterns, symbols, or concepts
- read_file: Read file contents
- find_related: Find related files (imports, tests, etc.)
- submit_analysis: Submit your final analysis (required)

IMPORTANT:
- Be thorough - search for multiple relevant patterns
- Read the actual code, don't guess
- Consider both direct changes and ripple effects
- Identify risks proactively
- You MUST call submit_analysis with your final analysis
"""

    USER_MESSAGE_TEMPLATE = """Analyze the codebase to understand the impact of this change:

REQUEST:
{requirements}

SCOPE: {scope}
PRIORITY: {priority}

KNOWN COMPONENTS:
{components}

KEYWORDS TO SEARCH:
{keywords}

Instructions:
1. Use search_code to find relevant code
2. Read key files to understand current implementation
3. Identify affected files and required changes
4. Map dependencies
5. Assess risks
6. Call submit_analysis with your complete analysis

Begin your analysis.
"""

    def get_system_prompt(self, context: StageContext) -> str:
        """Get analysis system prompt."""
        return self.SYSTEM_PROMPT
    
    def get_user_message(self, context: StageContext) -> str:
        """Build user message for analysis."""
        artifact = context.input_artifact
        
        # Format components
        components = artifact.get("refined_components", []) or artifact.get("detected_components", [])
        components_str = "\n".join([
            f"  - {c.get('name', 'unknown')}"
            for c in components
        ]) or "  (none identified)"
        
        # Format keywords
        keywords = artifact.get("keywords", [])
        keywords_str = ", ".join(keywords) if keywords else "(none)"
        
        return self.USER_MESSAGE_TEMPLATE.format(
            requirements=artifact.get("clarified_requirements", artifact.get("original_request", "")),
            scope=artifact.get("refined_scope", artifact.get("detected_scope", "unknown")),
            priority=artifact.get("priority", "medium"),
            components=components_str,
            keywords=keywords_str,
        )
    
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Parse analysis from tool call result."""
        # Look for submit_analysis tool call
        tool_results = llm_result.get("tool_results", [])
        
        for tool_result in tool_results:
            if tool_result.get("tool_name") == "submit_analysis":
                analysis = tool_result.get("input", {})
                
                # Add request_id
                analysis["request_id"] = context.input_artifact.get("request_id")
                
                # Restructure for artifact format
                return {
                    "request_id": analysis.get("request_id"),
                    "analysis": {
                        "summary": analysis.get("analysis_summary", ""),
                        "complexity": analysis.get("complexity", "medium"),
                        "estimated_effort": analysis.get("estimated_effort", "unknown"),
                    },
                    "affected_files": analysis.get("affected_files", []),
                    "components": analysis.get("components", []),
                    "dependencies": analysis.get("dependencies", []),
                    "risks": analysis.get("risks", []),
                    # Carry forward
                    "clarified_requirements": context.input_artifact.get("clarified_requirements"),
                    "priority": context.input_artifact.get("priority"),
                }
        
        # Fallback: try to extract from text response
        logger.warning("submit_analysis tool not called, falling back to text parsing")
        return self._parse_text_response(llm_result, context)
    
    def _parse_text_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Fallback: parse analysis from text response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")
        
        # Try YAML extraction
        artifact = self.extract_yaml_from_response(response_text)
        if artifact:
            artifact["request_id"] = context.input_artifact.get("request_id")
            return artifact
        
        # Minimal fallback
        return {
            "request_id": context.input_artifact.get("request_id"),
            "analysis": {"summary": response_text[:500], "complexity": "medium"},
            "affected_files": [],
            "components": [],
            "dependencies": [],
            "risks": [{"description": "Analysis incomplete - tool not used", "severity": "medium"}],
        }
    
    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """Validate analysis artifact."""
        from ..stage_executor import OutputValidation
        
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])
        
        errors = []
        warnings = []
        
        if not artifact.get("analysis"):
            errors.append("Missing analysis section")
        
        if not artifact.get("affected_files"):
            warnings.append("No affected files identified")
        
        if not artifact.get("components"):
            warnings.append("No components identified")
        
        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


def create_analyze_executor(config: Optional[Dict] = None) -> AnalyzeExecutor:
    """Create AnalyzeExecutor instance."""
    return AnalyzeExecutor(config)
```

### 2.2 AnalysisResult Schema

```yaml
# Schema for AnalysisResult artifact

request_id: string

analysis:
  summary: string           # High-level analysis summary
  complexity: enum [low, medium, high]
  estimated_effort: string  # e.g., "2-3 days", "1 week"

affected_files:
  - path: string
    change_type: enum [modify, create, delete]
    reason: string
    lines_affected: number  # Optional estimate

components:
  - name: string
    type: enum [module, class, function, api, config]
    description: string
    files: [string]
    new: boolean            # Is this a new component?

dependencies:
  - string                  # External dependencies to add/update

risks:
  - description: string
    severity: enum [low, medium, high]
    mitigation: string

# Carried forward
clarified_requirements: string
priority: string
```

---

## 3. SPEC Stage

### 3.1 SpecExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/spec.py

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

from ..llm_stage_executor import LLMStageExecutor
from ..stage_executor import StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class SpecExecutor(LLMStageExecutor):
    """
    SPEC stage executor.
    
    Generates a detailed technical specification including:
    - Component design
    - Interface definitions
    - Test case specifications
    - Acceptance criteria
    
    This is a critical stage that bridges analysis to implementation.
    """
    
    stage_name = "spec"
    artifact_type = "specification"
    
    required_input_fields = ["request_id", "analysis", "components"]
    
    output_fields = [
        "spec_id",
        "request_id",
        "components",
        "test_cases",
    ]
    
    SYSTEM_PROMPT = """You are an expert software architect creating a detailed technical specification.

Given the requirements and codebase analysis, you must produce a specification that includes:

1. COMPONENT DESIGN
   - Clear component definitions with responsibilities
   - Interface contracts between components
   - Data models and schemas

2. IMPLEMENTATION PLAN
   - Ordered list of implementation steps
   - File-by-file changes required
   - Dependencies between changes

3. TEST CASES
   - Unit test specifications for each component
   - Integration test specifications
   - Edge cases and error conditions

4. ACCEPTANCE CRITERIA
   - Clear, measurable success criteria
   - Performance requirements if applicable
   - Security considerations

Output your specification as YAML in a code block.

IMPORTANT:
- Be precise and actionable
- Include enough detail for implementation
- Test cases should be concrete, not abstract
- Consider the existing codebase structure
"""

    USER_MESSAGE_TEMPLATE = """Create a technical specification for this feature:

REQUIREMENTS:
{requirements}

ANALYSIS SUMMARY:
{analysis_summary}

COMPLEXITY: {complexity}
ESTIMATED EFFORT: {effort}

AFFECTED FILES:
{affected_files}

IDENTIFIED COMPONENTS:
{components}

RISKS:
{risks}

Create a detailed specification:

```yaml
spec_id: "{spec_id}"
request_id: "{request_id}"
title: "Feature Title"
version: "1.0"
created_at: "{timestamp}"

overview:
  description: |
    Brief description of what this specification covers.
  goals:
    - Primary goal 1
    - Primary goal 2
  non_goals:
    - What this does NOT include

components:
  - name: "ComponentName"
    type: "class"  # class, module, function, api
    file_path: "src/path/to/file.py"
    description: "What this component does"
    responsibilities:
      - "Responsibility 1"
      - "Responsibility 2"
    interface:
      methods:
        - name: "method_name"
          signature: "def method_name(param1: str) -> bool"
          description: "What it does"
          params:
            - name: "param1"
              type: "str"
              description: "Parameter description"
          returns: "bool indicating success"
          raises:
            - "ValueError: when param1 is empty"
    dependencies:
      - "other_module"

test_cases:
  - id: "TC001"
    component: "ComponentName"
    type: "unit"  # unit, integration, e2e
    description: "Test description"
    given: "Initial state or preconditions"
    when: "Action taken"
    then: "Expected outcome"
    priority: "high"  # high, medium, low

  - id: "TC002"
    component: "ComponentName"
    type: "unit"
    description: "Edge case test"
    given: "Edge case setup"
    when: "Edge case action"
    then: "Expected handling"
    priority: "medium"

interfaces:
  - name: "InterfaceName"
    type: "protocol"  # protocol, abstract_class, api
    methods:
      - signature: "def method(args) -> return_type"

data_models:
  - name: "ModelName"
    type: "dataclass"
    fields:
      - name: "field_name"
        type: "str"
        description: "Field description"
        required: true

implementation_order:
  - step: 1
    description: "First implementation step"
    files: ["file1.py"]
    depends_on: []
  - step: 2
    description: "Second step"
    files: ["file2.py"]
    depends_on: [1]

acceptance_criteria:
  - criterion: "All unit tests pass"
    measurable: true
  - criterion: "No regressions in existing tests"
    measurable: true
  - criterion: "Code coverage >= 80%"
    measurable: true

security_considerations:
  - consideration: "Input validation required"
    mitigation: "Validate all inputs before processing"

performance_requirements:
  - requirement: "Response time < 200ms"
    applies_to: "API endpoints"
```
"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._spec_counter = 0
    
    def get_system_prompt(self, context: StageContext) -> str:
        """Get spec generation system prompt."""
        return self.SYSTEM_PROMPT
    
    def get_user_message(self, context: StageContext) -> str:
        """Build user message for spec generation."""
        artifact = context.input_artifact
        analysis = artifact.get("analysis", {})
        
        # Generate spec ID
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self._spec_counter += 1
        spec_id = f"SPEC-{timestamp}-{self._spec_counter:04d}"
        
        # Format affected files
        affected_files = artifact.get("affected_files", [])
        files_str = "\n".join([
            f"  - {f.get('path', 'unknown')} ({f.get('change_type', 'modify')}): {f.get('reason', '')}"
            for f in affected_files
        ]) or "  (none identified)"
        
        # Format components
        components = artifact.get("components", [])
        components_str = "\n".join([
            f"  - {c.get('name', 'unknown')} ({c.get('type', 'unknown')}): {c.get('description', '')}"
            for c in components
        ]) or "  (none identified)"
        
        # Format risks
        risks = artifact.get("risks", [])
        risks_str = "\n".join([
            f"  - [{r.get('severity', 'medium')}] {r.get('description', '')}"
            for r in risks
        ]) or "  (none identified)"
        
        return self.USER_MESSAGE_TEMPLATE.format(
            requirements=artifact.get("clarified_requirements", ""),
            analysis_summary=analysis.get("summary", "No analysis summary"),
            complexity=analysis.get("complexity", "medium"),
            effort=analysis.get("estimated_effort", "unknown"),
            affected_files=files_str,
            components=components_str,
            risks=risks_str,
            spec_id=spec_id,
            request_id=artifact.get("request_id", "REQ-UNKNOWN"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    def parse_response(
        self,
        llm_result: Dict[str, Any],
        context: StageContext,
    ) -> Optional[Dict[str, Any]]:
        """Parse specification from LLM response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")
        
        spec = self.extract_yaml_from_response(response_text)
        
        if spec is None:
            logger.error("Failed to extract YAML specification")
            return None
        
        # Ensure required fields
        if "spec_id" not in spec:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            spec["spec_id"] = f"SPEC-{timestamp}"
        
        spec.setdefault("request_id", context.input_artifact.get("request_id"))
        spec.setdefault("components", [])
        spec.setdefault("test_cases", [])
        spec.setdefault("interfaces", [])
        spec.setdefault("acceptance_criteria", [])
        
        return spec
    
    def validate_output(self, artifact: Optional[Dict[str, Any]]) -> "OutputValidation":
        """Validate specification artifact."""
        from ..stage_executor import OutputValidation
        
        if artifact is None:
            return OutputValidation(valid=False, errors=["No artifact"])
        
        errors = []
        warnings = []
        
        # Required fields
        if not artifact.get("spec_id"):
            errors.append("Missing spec_id")
        
        # Must have components
        components = artifact.get("components", [])
        if not components:
            errors.append("Specification must define at least one component")
        
        # Validate components have required fields
        for i, comp in enumerate(components):
            if not comp.get("name"):
                errors.append(f"Component {i} missing name")
            if not comp.get("file_path") and not comp.get("files"):
                warnings.append(f"Component {comp.get('name', i)} has no file path")
        
        # Must have test cases
        test_cases = artifact.get("test_cases", [])
        if not test_cases:
            warnings.append("No test cases defined")
        
        # Validate test cases
        for i, tc in enumerate(test_cases):
            if not tc.get("id"):
                warnings.append(f"Test case {i} missing id")
            if not tc.get("description"):
                warnings.append(f"Test case {tc.get('id', i)} missing description")
        
        # Must have acceptance criteria
        if not artifact.get("acceptance_criteria"):
            warnings.append("No acceptance criteria defined")
        
        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def finalize(self, context: StageContext, result: StageResult) -> None:
        """Save spec to standard location."""
        super().finalize(context, result)
        
        # Also save to .agentforge/specs/ for easy access
        if result.success and result.artifact:
            specs_dir = context.agentforge_path / "specs"
            specs_dir.mkdir(parents=True, exist_ok=True)
            
            spec_id = result.artifact.get("spec_id", "unknown")
            spec_file = specs_dir / f"{spec_id}.yaml"
            
            import yaml
            with open(spec_file, "w") as f:
                yaml.dump(result.artifact, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved specification to {spec_file}")


def create_spec_executor(config: Optional[Dict] = None) -> SpecExecutor:
    """Create SpecExecutor instance."""
    return SpecExecutor(config)
```

### 3.2 Specification Schema

```yaml
# Schema for Specification artifact

spec_id: string
request_id: string
title: string
version: string
created_at: datetime

overview:
  description: string
  goals: [string]
  non_goals: [string]

components:
  - name: string
    type: enum [class, module, function, api, config]
    file_path: string
    description: string
    responsibilities: [string]
    interface:
      methods:
        - name: string
          signature: string
          description: string
          params:
            - name: string
              type: string
              description: string
          returns: string
          raises: [string]
    dependencies: [string]
    new: boolean

test_cases:
  - id: string
    component: string
    type: enum [unit, integration, e2e]
    description: string
    given: string
    when: string
    then: string
    priority: enum [high, medium, low]

interfaces:
  - name: string
    type: enum [protocol, abstract_class, api]
    methods:
      - signature: string

data_models:
  - name: string
    type: string
    fields:
      - name: string
        type: string
        description: string
        required: boolean

implementation_order:
  - step: number
    description: string
    files: [string]
    depends_on: [number]

acceptance_criteria:
  - criterion: string
    measurable: boolean

security_considerations:
  - consideration: string
    mitigation: string

performance_requirements:
  - requirement: string
    applies_to: string
```

---

## 4. Pipeline Configuration

### 4.1 Design Pipeline (Exits at SPEC)

```yaml
# .agentforge/pipelines/design.yaml

pipeline_type: design
description: "Design phase - produces specification without implementation"

stages:
  - intake
  - clarify
  - analyze
  - spec

exit_after: spec

supervised: true  # Pause for spec approval

config:
  analyze:
    max_files_to_read: 20
    search_depth: 3
  spec:
    include_tests: true
    include_implementation_order: true
```

### 4.2 Full Implementation Pipeline

```yaml
# .agentforge/pipelines/implement.yaml

pipeline_type: implement
description: "Full implementation pipeline"

stages:
  - intake
  - clarify
  - analyze
  - spec
  - red
  - green
  - refactor
  - deliver

supervised: false  # Full autonomous

iteration_enabled: true
max_iterations_per_stage: 3
```

---

## 5. Integration Points

### 5.1 Tool Handler Integration

The ANALYZE stage uses tool handlers from P0:

```python
# Integration with existing tool handlers

from agentforge.core.harness.minimal_context.tool_handlers import (
    create_search_code_handler,
    create_read_file_handler,
    create_find_related_handler,
)

# In AnalyzeExecutor._get_executor():
def _get_executor(self, context: StageContext):
    from agentforge.core.harness.minimal_context import MinimalContextExecutor
    
    executor = MinimalContextExecutor(
        project_path=context.project_path,
        task_type=f"stage_{self.stage_name}",
    )
    
    # Register analysis tools
    executor.native_tool_executor.register_action(
        "search_code", create_search_code_handler(context.project_path)
    )
    executor.native_tool_executor.register_action(
        "read_file", create_read_file_handler(context.project_path)
    )
    executor.native_tool_executor.register_action(
        "find_related", create_find_related_handler(context.project_path)
    )
    
    return executor
```

### 5.2 Existing Contract Integration

The SPEC stage can optionally wrap existing draft contract:

```python
# Alternative: Use existing spec.draft contract

spec_executor = ContractStageExecutor(
    stage_name="spec",
    contract_id="spec.draft.v1",
    input_mapping={
        "analysis_result": None,  # Pass whole artifact
    },
)
```

---

## 6. Test Specification

### 6.1 Unit Tests

```python
# tests/unit/pipeline/stages/test_analyze.py

class TestAnalyzeExecutor:
    """Tests for AnalyzeExecutor."""
    
    def test_uses_search_code_tool(self, mock_llm, tmp_path):
        """Executor uses search_code for codebase exploration."""
    
    def test_uses_read_file_tool(self, mock_llm, tmp_path):
        """Executor uses read_file to examine code."""
    
    def test_produces_affected_files_list(self, mock_llm):
        """Output includes affected files."""
    
    def test_identifies_risks(self, mock_llm):
        """Output includes risk assessment."""
    
    def test_handles_empty_codebase(self, mock_llm, tmp_path):
        """Handles project with no matching files."""


class TestSpecExecutor:
    """Tests for SpecExecutor."""
    
    def test_generates_component_specs(self, mock_llm):
        """Generates component specifications."""
    
    def test_generates_test_cases(self, mock_llm):
        """Generates test case specifications."""
    
    def test_includes_acceptance_criteria(self, mock_llm):
        """Includes acceptance criteria."""
    
    def test_saves_to_specs_directory(self, mock_llm, tmp_path):
        """Saves spec to .agentforge/specs/."""
    
    def test_validates_component_completeness(self):
        """Validates components have required fields."""
```

### 6.2 Integration Tests

```python
# tests/integration/pipeline/stages/test_analyze_spec.py

class TestAnalyzeSpecWorkflow:
    """Integration tests for analyze->spec flow."""
    
    def test_analysis_flows_to_spec(self, mock_llm, tmp_path):
        """AnalysisResult properly feeds SpecExecutor."""
    
    def test_spec_reflects_analysis_components(self, mock_llm, tmp_path):
        """Spec components match analysis findings."""
    
    def test_full_clarify_to_spec_pipeline(self, mock_llm, tmp_path):
        """Full flow from clarify through spec."""
```

---

## 7. Success Criteria

1. **Functional:**
   - [ ] AnalyzeExecutor searches codebase effectively
   - [ ] AnalyzeExecutor identifies affected files
   - [ ] SpecExecutor generates complete specifications
   - [ ] Specifications include test cases

2. **Quality:**
   - [ ] Analysis uses codebase tools, not guessing
   - [ ] Specifications are detailed enough for implementation
   - [ ] Test cases follow Given/When/Then format

3. **Integration:**
   - [ ] Works with P0 tool handlers
   - [ ] Artifacts flow correctly between stages
   - [ ] Design pipeline exits at SPEC correctly

---

## 8. Dependencies

- **Stage 1-3:** PipelineController, StageExecutor, INTAKE/CLARIFY
- **P0 Tool Handlers:** search_code, read_file, find_related
- **Existing:** MinimalContextExecutor

---

*Next: Stage 5 - RED Phase (Test Generation)*
