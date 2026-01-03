# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-schemas
# @test_path: tests/unit/pipeline/test_schemas.py

"""
Pipeline Phase Transition Schemas
=================================

Defines the artifact schemas for each pipeline stage transition.
These schemas ensure:
1. Each stage receives required inputs from previous stages
2. Each stage produces required outputs for next stages
3. Types and structures are validated at transition boundaries

The validation chain:
  INTAKE → CLARIFY → ANALYZE → SPEC → RED → GREEN → REFACTOR → DELIVER

Each schema defines:
- required: Fields that MUST be present
- properties: Field types and constraints
- additionalProperties: Whether extra fields are allowed
"""

from typing import Any

# =============================================================================
# Type Definitions for Schema Building
# =============================================================================

STRING = {"type": "string"}
STRING_REQUIRED = {"type": "string", "minLength": 1}
ARRAY_OF_STRINGS = {"type": "array", "items": {"type": "string"}}
OBJECT = {"type": "object"}
BOOLEAN = {"type": "boolean"}
INTEGER = {"type": "integer"}


def string_enum(*values: str) -> dict:
    """Create a string enum schema."""
    return {"type": "string", "enum": list(values)}


# =============================================================================
# Stage Output Schemas - What each stage produces
# =============================================================================

INTAKE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["request_id", "detected_scope", "original_request"],
    "properties": {
        "request_id": STRING_REQUIRED,
        "detected_scope": string_enum("feature", "bugfix", "refactor", "test", "docs", "unclear"),
        "original_request": STRING_REQUIRED,
        "priority": string_enum("low", "medium", "high", "critical"),
        "initial_questions": ARRAY_OF_STRINGS,
        "detected_files": ARRAY_OF_STRINGS,
        "detected_components": ARRAY_OF_STRINGS,
    },
    "additionalProperties": True,
}

CLARIFY_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["request_id", "clarified_requirements", "scope_confirmed"],
    "properties": {
        "request_id": STRING_REQUIRED,
        "clarified_requirements": STRING_REQUIRED,
        "scope_confirmed": string_enum("feature", "bugfix", "refactor", "test", "docs"),
        "priority": string_enum("low", "medium", "high", "critical"),
        "acceptance_criteria": ARRAY_OF_STRINGS,
        "constraints": ARRAY_OF_STRINGS,
    },
    "additionalProperties": True,
}

ANALYZE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["request_id", "analysis", "components"],
    "properties": {
        "request_id": STRING_REQUIRED,
        "analysis": {
            "type": "object",
            "required": ["summary", "impact"],
            "properties": {
                "summary": STRING_REQUIRED,
                "impact": string_enum("low", "medium", "high"),
                "affected_areas": ARRAY_OF_STRINGS,
                "dependencies": ARRAY_OF_STRINGS,
            },
        },
        "components": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "path"],
                "properties": {
                    "name": STRING_REQUIRED,
                    "path": STRING_REQUIRED,
                    "type": string_enum("new", "modify", "test"),
                    "description": STRING,
                },
            },
        },
        "affected_files": ARRAY_OF_STRINGS,
        "codebase_context": OBJECT,
    },
    "additionalProperties": True,
}

SPEC_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["spec_id", "request_id", "components", "test_cases"],
    "properties": {
        "spec_id": STRING_REQUIRED,
        "request_id": STRING_REQUIRED,
        "components": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["component_id", "name", "location"],
                "properties": {
                    "component_id": STRING_REQUIRED,
                    "name": STRING_REQUIRED,
                    "location": STRING_REQUIRED,
                    "test_location": STRING,
                    "description": STRING,
                    "methods": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": STRING_REQUIRED,
                                "signature": STRING,
                                "description": STRING,
                            },
                        },
                    },
                },
            },
        },
        "test_cases": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "description"],
                "properties": {
                    "id": STRING_REQUIRED,
                    "description": STRING_REQUIRED,
                    "component_id": STRING,
                    "type": string_enum("unit", "integration", "e2e"),
                    "assertions": ARRAY_OF_STRINGS,
                },
            },
        },
        "architecture_notes": STRING,
    },
    "additionalProperties": True,
}

RED_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["spec_id", "test_files", "test_results"],
    "properties": {
        "spec_id": STRING_REQUIRED,
        "test_files": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["path", "content"],
                "properties": {
                    "path": STRING_REQUIRED,
                    "content": STRING_REQUIRED,
                    "component_id": STRING,
                    "test_count": INTEGER,
                },
            },
        },
        "test_results": {
            "type": "object",
            "required": ["passed", "failed", "total"],
            "properties": {
                "passed": INTEGER,
                "failed": INTEGER,
                "total": INTEGER,
                "failing_tests": ARRAY_OF_STRINGS,
            },
        },
        "failing_tests": ARRAY_OF_STRINGS,  # Convenience field
    },
    "additionalProperties": True,
}

GREEN_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["spec_id", "implementation_files", "test_results"],
    "properties": {
        "spec_id": STRING_REQUIRED,
        "implementation_files": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["path", "content"],
                "properties": {
                    "path": STRING_REQUIRED,
                    "content": STRING_REQUIRED,
                    "component_id": STRING,
                    "action": string_enum("created", "modified"),
                },
            },
        },
        "test_results": {
            "type": "object",
            "required": ["passed", "failed", "total"],
            "properties": {
                "passed": INTEGER,
                "failed": INTEGER,
                "total": INTEGER,
                "all_passing": BOOLEAN,
            },
        },
        "iterations": INTEGER,
    },
    "additionalProperties": True,
}

REFACTOR_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["spec_id", "final_files", "test_results"],
    "properties": {
        "spec_id": STRING_REQUIRED,
        "refactored_files": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["path", "content"],
                "properties": {
                    "path": STRING_REQUIRED,
                    "content": STRING_REQUIRED,
                    "changes": ARRAY_OF_STRINGS,
                },
            },
        },
        "final_files": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": STRING_REQUIRED,
                    "content": STRING,
                    "type": string_enum("source", "test"),
                },
            },
        },
        "test_results": {
            "type": "object",
            "required": ["passed", "total"],
            "properties": {
                "passed": INTEGER,
                "total": INTEGER,
                "all_passing": BOOLEAN,
            },
        },
        "quality_metrics": OBJECT,
    },
    "additionalProperties": True,
}

DELIVER_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["spec_id", "deliverable_type", "files_modified"],
    "properties": {
        "spec_id": STRING_REQUIRED,
        "deliverable_type": string_enum("commit", "pr", "patch", "report"),
        "files_modified": ARRAY_OF_STRINGS,
        "commit_sha": STRING,
        "pr_url": STRING,
        "summary": STRING,
    },
    "additionalProperties": True,
}


# =============================================================================
# Stage Input Requirements - What each stage needs from previous stages
# =============================================================================

STAGE_INPUT_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "intake": {
        "required": [],  # First stage - no required inputs
        "optional": ["project_context", "codebase_profile"],
    },
    "clarify": {
        "required": ["request_id", "detected_scope"],
        "optional": ["initial_questions", "detected_files"],
    },
    "analyze": {
        "required": ["request_id", "clarified_requirements"],
        "optional": ["scope_confirmed", "priority", "constraints"],
    },
    "spec": {
        "required": ["request_id", "analysis", "components"],
        "optional": ["affected_files", "codebase_context"],
    },
    "red": {
        "required": ["spec_id", "components", "test_cases"],
        "optional": ["architecture_notes"],
    },
    "green": {
        "required": ["spec_id", "test_files", "failing_tests"],
        "optional": ["test_results"],
    },
    "refactor": {
        "required": ["spec_id", "implementation_files", "test_results"],
        "optional": ["quality_metrics"],
    },
    "deliver": {
        "required": ["spec_id", "final_files"],
        "optional": ["refactored_files", "test_results"],
    },
}


# =============================================================================
# Schema Registry - Maps stage names to their output schemas
# =============================================================================

STAGE_OUTPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "intake": INTAKE_OUTPUT_SCHEMA,
    "clarify": CLARIFY_OUTPUT_SCHEMA,
    "analyze": ANALYZE_OUTPUT_SCHEMA,
    "spec": SPEC_OUTPUT_SCHEMA,
    "red": RED_OUTPUT_SCHEMA,
    "green": GREEN_OUTPUT_SCHEMA,
    "refactor": REFACTOR_OUTPUT_SCHEMA,
    "deliver": DELIVER_OUTPUT_SCHEMA,
}


# =============================================================================
# Transition Definitions - Valid stage transitions
# =============================================================================

STAGE_TRANSITIONS: dict[str, list[str]] = {
    "intake": ["clarify"],
    "clarify": ["analyze"],
    "analyze": ["spec"],
    "spec": ["red"],
    "red": ["green"],
    "green": ["refactor"],
    "refactor": ["deliver"],
    "deliver": [],  # Terminal stage
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_input_schema(stage_name: str) -> dict[str, Any]:
    """
    Get the input validation schema for a stage.

    This is derived from the required inputs defined in STAGE_INPUT_REQUIREMENTS.
    """
    requirements = STAGE_INPUT_REQUIREMENTS.get(stage_name, {})
    required = requirements.get("required", [])

    return {
        "type": "object",
        "required": required,
        "additionalProperties": True,
    }


def get_output_schema(stage_name: str) -> dict[str, Any]:
    """Get the output validation schema for a stage."""
    return STAGE_OUTPUT_SCHEMAS.get(stage_name, {"type": "object"})


def get_next_stages(stage_name: str) -> list[str]:
    """Get valid next stages from current stage."""
    return STAGE_TRANSITIONS.get(stage_name, [])


def validate_transition(from_stage: str, to_stage: str) -> bool:
    """Check if a stage transition is valid."""
    return to_stage in STAGE_TRANSITIONS.get(from_stage, [])


def get_required_artifacts_for_stage(stage_name: str) -> list[str]:
    """Get the list of required artifact keys for a stage."""
    requirements = STAGE_INPUT_REQUIREMENTS.get(stage_name, {})
    return requirements.get("required", [])


def get_produced_artifacts_by_stage(stage_name: str) -> list[str]:
    """Get the list of artifact keys produced by a stage."""
    schema = STAGE_OUTPUT_SCHEMAS.get(stage_name, {})
    return schema.get("required", [])
