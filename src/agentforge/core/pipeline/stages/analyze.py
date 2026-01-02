# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: analyze-executor
# @test_path: tests/unit/pipeline/stages/test_analyze.py

"""
Analyze Stage Executor
======================

ANALYZE is the third stage of the pipeline. It performs deep codebase
analysis to understand:
- What files/modules are affected
- Dependencies between components
- Potential risks and conflicts
- Complexity assessment

Uses tool calls (search_code, read_file, find_related) to gather information.
"""

import logging
from typing import Any

from ..llm_stage_executor import OutputValidation, ToolBasedStageExecutor
from ..stage_executor import StageContext

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

    # Tool that produces the artifact
    artifact_tool_name = "submit_analysis"

    # Tools available for analysis
    tools = [
        {
            "name": "search_code",
            "description": "Search codebase for patterns, symbols, or concepts",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern or query",
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Optional file glob pattern",
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["regex", "semantic"],
                    },
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
                    "path": {
                        "type": "string",
                        "description": "File path relative to project root",
                    },
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
                    "file_path": {
                        "type": "string",
                        "description": "Source file path",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["imports", "same_dir", "tests", "all"],
                    },
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
                                "change_type": {
                                    "type": "string",
                                    "enum": ["modify", "create", "delete"],
                                },
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
                                "files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "risks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high"],
                                },
                                "mitigation": {"type": "string"},
                            },
                        },
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "estimated_effort": {"type": "string"},
                },
                "required": ["analysis_summary", "affected_files", "components"],
            },
        },
    ]

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
        artifact = context.input_artifacts

        # Format components
        components = artifact.get("refined_components", []) or artifact.get(
            "detected_components", []
        )
        components_str = (
            "\n".join([f"  - {c.get('name', 'unknown')}" for c in components])
            or "  (none identified)"
        )

        # Format keywords
        keywords = artifact.get("keywords", [])
        keywords_str = ", ".join(keywords) if keywords else "(none)"

        return self.USER_MESSAGE_TEMPLATE.format(
            requirements=artifact.get(
                "clarified_requirements", artifact.get("original_request", "")
            ),
            scope=artifact.get("refined_scope", artifact.get("detected_scope", "unknown")),
            priority=artifact.get("priority", "medium"),
            components=components_str,
            keywords=keywords_str,
        )

    def parse_response(
        self,
        llm_result: dict[str, Any],
        context: StageContext,
    ) -> dict[str, Any] | None:
        """Parse analysis from tool call result."""
        # Look for submit_analysis tool call
        tool_results = llm_result.get("tool_results", [])

        for tool_result in tool_results:
            if tool_result.get("tool_name") == "submit_analysis":
                analysis = tool_result.get("input", {})

                # Add request_id
                analysis["request_id"] = context.input_artifacts.get("request_id")

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
                    "clarified_requirements": context.input_artifacts.get(
                        "clarified_requirements"
                    ),
                    "priority": context.input_artifacts.get("priority"),
                }

        # Fallback: try to extract from text response
        logger.warning("submit_analysis tool not called, falling back to text parsing")
        return self._parse_text_response(llm_result, context)

    def _parse_text_response(
        self,
        llm_result: dict[str, Any],
        context: StageContext,
    ) -> dict[str, Any] | None:
        """Fallback: parse analysis from text response."""
        response_text = llm_result.get("response", "") or llm_result.get("content", "")

        # Try YAML extraction
        artifact = self.extract_yaml_from_response(response_text)
        if artifact:
            artifact["request_id"] = context.input_artifacts.get("request_id")
            # Ensure required structure
            if "analysis" not in artifact:
                artifact["analysis"] = {
                    "summary": artifact.get("analysis_summary", response_text[:500]),
                    "complexity": artifact.get("complexity", "medium"),
                }
            return artifact

        # Minimal fallback
        return {
            "request_id": context.input_artifacts.get("request_id"),
            "analysis": {"summary": response_text[:500], "complexity": "medium"},
            "affected_files": [],
            "components": [],
            "dependencies": [],
            "risks": [
                {
                    "description": "Analysis incomplete - tool not used",
                    "severity": "medium",
                }
            ],
            "clarified_requirements": context.input_artifacts.get(
                "clarified_requirements"
            ),
        }

    def validate_output(self, artifact: dict[str, Any] | None) -> OutputValidation:
        """Validate analysis artifact."""
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

    def get_required_inputs(self) -> list:
        """Get required inputs for analyze stage."""
        return self.required_input_fields


def create_analyze_executor(config: dict | None = None) -> AnalyzeExecutor:
    """Create AnalyzeExecutor instance."""
    return AnalyzeExecutor(config)
