"""
Discovery Tool Definitions
==========================

Tools for discovery and bridge tasks.
"""

from ..interface import ToolDefinition

ANALYZE_DEPENDENCIES = ToolDefinition(
    name="analyze_dependencies",
    description="Map the import/dependency graph for a file or module.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to file or directory to analyze",
            },
            "depth": {
                "type": "integer",
                "description": "Maximum depth of dependency traversal (default: 3)",
            },
            "include_external": {
                "type": "boolean",
                "description": "Include external/third-party dependencies",
            },
        },
        "required": ["path"],
    },
)

DETECT_PATTERNS = ToolDefinition(
    name="detect_patterns",
    description="Detect architectural patterns and code structures in the codebase.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to analyze (file or directory)",
            },
            "patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific patterns to look for (e.g., 'singleton', 'factory', 'mvc')",
            },
        },
        "required": ["path"],
    },
)

MAP_STRUCTURE = ToolDefinition(
    name="map_structure",
    description="Analyze and map the project structure, identifying key directories and files.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Root path to analyze (default: project root)",
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Include hidden files and directories",
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum directory depth to traverse",
            },
        },
        "required": [],
    },
)

CREATE_MAPPING = ToolDefinition(
    name="create_mapping",
    description="Create a mapping between code elements and contracts/specifications.",
    input_schema={
        "type": "object",
        "properties": {
            "source_element": {
                "type": "string",
                "description": "Source code element (e.g., class name, function)",
            },
            "target_contract": {
                "type": "string",
                "description": "Target contract or specification ID",
            },
            "mapping_type": {
                "type": "string",
                "enum": ["implements", "uses", "extends", "validates"],
                "description": "Type of relationship",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score for the mapping (0.0-1.0)",
            },
        },
        "required": ["source_element", "target_contract", "mapping_type"],
    },
)

# Collection of discovery tools
DISCOVERY_TOOLS: list[ToolDefinition] = [
    ANALYZE_DEPENDENCIES,
    DETECT_PATTERNS,
    MAP_STRUCTURE,
    CREATE_MAPPING,
]
