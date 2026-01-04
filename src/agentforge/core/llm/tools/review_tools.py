"""
Review Tool Definitions
=======================

Tools for code_review tasks.
"""

from ..interface import ToolDefinition

ANALYZE_DIFF = ToolDefinition(
    name="analyze_diff",
    description="Analyze a code diff for potential issues, style violations, and improvements.",
    input_schema={
        "type": "object",
        "properties": {
            "diff_content": {
                "type": "string",
                "description": "The diff content to analyze (unified diff format)",
            },
            "focus_areas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific areas to focus on (e.g., 'security', 'performance', 'style')",
            },
        },
        "required": ["diff_content"],
    },
)

ADD_REVIEW_COMMENT = ToolDefinition(
    name="add_review_comment",
    description="Add a review comment on a specific line or range in the diff.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file being commented on",
            },
            "line_number": {
                "type": "integer",
                "description": "Line number in the new version",
            },
            "comment": {
                "type": "string",
                "description": "The review comment",
            },
            "severity": {
                "type": "string",
                "enum": ["critical", "warning", "suggestion", "nitpick"],
                "description": "Severity of the issue",
            },
            "category": {
                "type": "string",
                "enum": ["bug", "security", "performance", "style", "documentation", "design"],
                "description": "Category of the comment",
            },
        },
        "required": ["file_path", "line_number", "comment", "severity"],
    },
)

GENERATE_REVIEW_SUMMARY = ToolDefinition(
    name="generate_review_summary",
    description="Generate an overall summary of the code review findings.",
    input_schema={
        "type": "object",
        "properties": {
            "include_stats": {
                "type": "boolean",
                "description": "Include statistics about changes",
            },
            "recommendation": {
                "type": "string",
                "enum": ["approve", "request_changes", "comment"],
                "description": "Overall recommendation for the review",
            },
        },
        "required": ["recommendation"],
    },
)

# Collection of review tools
REVIEW_TOOLS: list[ToolDefinition] = [
    ANALYZE_DIFF,
    ADD_REVIEW_COMMENT,
    GENERATE_REVIEW_SUMMARY,
]
