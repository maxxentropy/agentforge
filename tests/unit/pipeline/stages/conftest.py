# @spec_file: specs/pipeline-controller/implementation/phase-2-design-pipeline.yaml
# @spec_id: pipeline-controller-phase2-v1

"""Shared fixtures for stage unit tests."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from agentforge.core.pipeline import StageContext


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response factory."""

    def _make_response(
        response_text: str = "",
        tool_results: list = None,
        final_artifact: dict = None,
    ):
        return {
            "response": response_text,
            "content": response_text,
            "tool_results": tool_results or [],
            "final_artifact": final_artifact,
        }

    return _make_response


@pytest.fixture
def mock_llm_with_tools():
    """Create a mock LLM that returns tool call results."""

    def _make_llm_with_tool_call(tool_name: str, tool_input: dict):
        return {
            "response": f"Called {tool_name}",
            "tool_results": [
                {
                    "tool_name": tool_name,
                    "input": tool_input,
                    "result": {"success": True},
                }
            ],
        }

    return _make_llm_with_tool_call


@pytest.fixture
def sample_intake_artifact():
    """Create a sample intake artifact."""
    return {
        "request_id": "REQ-20260101120000-0001",
        "original_request": "Add OAuth2 authentication",
        "detected_scope": "feature_addition",
        "priority": "high",
        "confidence": 0.85,
        "initial_questions": [
            {
                "question": "What OAuth provider should be used?",
                "priority": "blocking",
                "context": "Need to know for library selection",
            },
            {
                "question": "What scopes are needed?",
                "priority": "optional",
                "context": "Determines permission levels",
            },
        ],
        "detected_components": [
            {"name": "authentication", "confidence": 0.9},
            {"name": "user_management", "confidence": 0.7},
        ],
        "keywords": ["oauth", "authentication", "login"],
        "estimated_complexity": "medium",
    }


@pytest.fixture
def sample_clarify_artifact(sample_intake_artifact):
    """Create a sample clarify artifact."""
    return {
        "request_id": sample_intake_artifact["request_id"],
        "clarified_requirements": "Add OAuth2 authentication using Google as the provider with openid and email scopes.",
        "scope_confirmed": True,
        "answered_questions": [
            {
                "question": "What OAuth provider should be used?",
                "answer": "Google OAuth 2.0",
                "incorporated": True,
            }
        ],
        "remaining_questions": [],
        "refined_scope": "feature_addition",
        "ready_for_analysis": True,
        "original_request": sample_intake_artifact["original_request"],
        "priority": sample_intake_artifact["priority"],
        "keywords": sample_intake_artifact["keywords"],
    }


@pytest.fixture
def sample_analyze_artifact(sample_clarify_artifact):
    """Create a sample analyze artifact."""
    return {
        "request_id": sample_clarify_artifact["request_id"],
        "analysis": {
            "summary": "OAuth2 integration requires auth module changes",
            "complexity": "medium",
            "estimated_effort": "3-5 days",
        },
        "affected_files": [
            {
                "path": "src/auth/oauth.py",
                "change_type": "create",
                "reason": "New OAuth handler",
            },
            {
                "path": "src/auth/providers.py",
                "change_type": "modify",
                "reason": "Add Google provider",
            },
        ],
        "components": [
            {
                "name": "OAuthHandler",
                "type": "class",
                "description": "Handles OAuth authentication flow",
                "files": ["src/auth/oauth.py"],
            }
        ],
        "dependencies": ["google-auth", "google-auth-oauthlib"],
        "risks": [
            {
                "description": "Token storage security",
                "severity": "high",
                "mitigation": "Use encrypted storage",
            }
        ],
        "clarified_requirements": sample_clarify_artifact["clarified_requirements"],
        "priority": sample_clarify_artifact["priority"],
    }


@pytest.fixture
def sample_stage_context(tmp_path):
    """Create a sample stage context factory."""

    def _make_context(
        stage_name: str = "test",
        input_artifacts: dict = None,
        request: str = "Test request",
    ):
        return StageContext(
            pipeline_id="PL-20260101-abc12345",
            stage_name=stage_name,
            project_path=tmp_path,
            input_artifacts=input_artifacts or {},
            config={},
            request=request,
        )

    return _make_context
