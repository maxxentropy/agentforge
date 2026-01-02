# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1

"""Shared fixtures for stage unit tests."""


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


# ═══════════════════════════════════════════════════════════════════════════════
# TDD Stage Fixtures (Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_spec_artifact(sample_analyze_artifact):
    """Create a sample spec artifact for TDD tests."""
    return {
        "spec_id": "SPEC-20260101120000-0001",
        "request_id": sample_analyze_artifact["request_id"],
        "title": "OAuth2 Authentication",
        "version": "1.0",
        "overview": {
            "purpose": "Add OAuth2 authentication using Google provider",
            "scope": "Authentication module",
        },
        "components": [
            {
                "name": "OAuthProvider",
                "type": "class",
                "file_path": "src/auth/oauth_provider.py",
                "description": "Handles OAuth2 authentication flow",
                "interface": {
                    "methods": [
                        {
                            "signature": "authenticate(code: str) -> Dict[str, Any]",
                            "description": "Authenticate with authorization code",
                        },
                        {
                            "signature": "refresh_token(refresh_token: str) -> Dict[str, Any]",
                            "description": "Refresh access token",
                        },
                    ]
                },
            },
            {
                "name": "TokenManager",
                "type": "class",
                "file_path": "src/auth/token_manager.py",
                "description": "Manages OAuth tokens",
            },
        ],
        "test_cases": [
            {
                "id": "TC001",
                "description": "Test successful authentication",
                "component": "OAuthProvider",
                "type": "unit",
                "given": "Valid OAuth credentials",
                "when": "authenticate() is called with valid code",
                "then": "Returns access token",
            },
            {
                "id": "TC002",
                "description": "Test invalid code handling",
                "component": "OAuthProvider",
                "type": "unit",
                "given": "Invalid authorization code",
                "when": "authenticate() is called",
                "then": "Raises AuthenticationError",
            },
            {
                "id": "TC003",
                "description": "Test token refresh",
                "component": "OAuthProvider",
                "type": "unit",
                "given": "Valid refresh token",
                "when": "refresh_token() is called",
                "then": "Returns new access token",
            },
        ],
        "acceptance_criteria": [
            {"criterion": "OAuth flow completes successfully"},
            {"criterion": "Tokens are securely stored"},
            {"criterion": "Refresh tokens work correctly"},
        ],
        "implementation_order": [
            {"step": 1, "description": "Create OAuthProvider class"},
            {"step": 2, "description": "Implement authenticate method"},
            {"step": 3, "description": "Implement refresh_token method"},
            {"step": 4, "description": "Create TokenManager class"},
        ],
    }


@pytest.fixture
def sample_red_artifact(sample_spec_artifact):
    """Create a sample RED phase artifact."""
    return {
        "spec_id": sample_spec_artifact["spec_id"],
        "request_id": sample_spec_artifact["request_id"],
        "test_files": [
            {
                "path": "tests/unit/auth/test_oauth_provider.py",
                "content": "# Test file content",
            }
        ],
        "test_results": {
            "passed": 0,
            "failed": 3,
            "errors": 0,
            "skipped": 0,
            "total": 3,
            "exit_code": 1,
            "output": "FAILED test_authenticate\nFAILED test_invalid_code\nFAILED test_refresh",
            "test_details": [
                {"name": "test_authenticate", "status": "failed"},
                {"name": "test_invalid_code", "status": "failed"},
                {"name": "test_refresh", "status": "failed"},
            ],
        },
        "failing_tests": [
            "test_authenticate",
            "test_invalid_code",
            "test_refresh",
        ],
        "unexpected_passes": [],
        "warnings": [],
    }


@pytest.fixture
def sample_llm_test_generation_response():
    """Create a sample LLM response with test file generation."""
    return {
        "response": '''I'll generate the test files for the OAuth components.

### FILE: tests/unit/auth/test_oauth_provider.py
```python
"""Tests for OAuthProvider."""
import pytest
from src.auth.oauth_provider import OAuthProvider, AuthenticationError


class TestOAuthProvider:
    """Unit tests for OAuthProvider class."""

    @pytest.fixture
    def provider(self):
        """Create OAuthProvider instance."""
        return OAuthProvider(client_id="test", client_secret="secret")

    def test_authenticate_returns_token_on_success(self, provider):
        """TC001: Test successful authentication."""
        result = provider.authenticate("valid_code")
        assert "access_token" in result

    def test_authenticate_raises_on_invalid_code(self, provider):
        """TC002: Test invalid code handling."""
        with pytest.raises(AuthenticationError):
            provider.authenticate("invalid_code")

    def test_refresh_token_returns_new_token(self, provider):
        """TC003: Test token refresh."""
        result = provider.refresh_token("valid_refresh")
        assert "access_token" in result
```

### FILE: tests/unit/auth/test_token_manager.py
```python
"""Tests for TokenManager."""
import pytest
from src.auth.token_manager import TokenManager


class TestTokenManager:
    """Unit tests for TokenManager class."""

    def test_store_token(self):
        """Test token storage."""
        manager = TokenManager()
        manager.store("user_id", {"access_token": "token"})
        assert manager.get("user_id") is not None
```
''',
        "content": "",
        "tool_results": [],
    }


@pytest.fixture
def mock_pytest_passing_output():
    """Mock pytest output when all tests pass."""
    return """
============================= test session starts ==============================
collected 3 items

tests/unit/auth/test_oauth_provider.py::TestOAuthProvider::test_authenticate_returns_token_on_success PASSED
tests/unit/auth/test_oauth_provider.py::TestOAuthProvider::test_authenticate_raises_on_invalid_code PASSED
tests/unit/auth/test_oauth_provider.py::TestOAuthProvider::test_refresh_token_returns_new_token PASSED

============================== 3 passed in 0.05s ===============================
"""


@pytest.fixture
def mock_pytest_failing_output():
    """Mock pytest output when tests fail."""
    return """
============================= test session starts ==============================
collected 3 items

tests/unit/auth/test_oauth_provider.py::TestOAuthProvider::test_authenticate_returns_token_on_success FAILED
tests/unit/auth/test_oauth_provider.py::TestOAuthProvider::test_authenticate_raises_on_invalid_code FAILED
tests/unit/auth/test_oauth_provider.py::TestOAuthProvider::test_refresh_token_returns_new_token FAILED

=================================== FAILURES ===================================
_____ TestOAuthProvider.test_authenticate_returns_token_on_success _____

    def test_authenticate_returns_token_on_success(self, provider):
>       result = provider.authenticate("valid_code")
E       ModuleNotFoundError: No module named 'src.auth.oauth_provider'

============================= 3 failed in 0.05s ================================
"""


@pytest.fixture
def temp_project_path(tmp_path):
    """Create a temporary project path with basic structure."""
    # Create basic directories
    (tmp_path / "src" / "auth").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "auth").mkdir(parents=True)

    # Create __init__.py files
    (tmp_path / "src" / "__init__.py").write_text("")
    (tmp_path / "src" / "auth" / "__init__.py").write_text("")
    (tmp_path / "tests" / "__init__.py").write_text("")
    (tmp_path / "tests" / "unit" / "__init__.py").write_text("")
    (tmp_path / "tests" / "unit" / "auth" / "__init__.py").write_text("")

    return tmp_path


# ═══════════════════════════════════════════════════════════════════════════════
# REFACTOR & DELIVER Stage Fixtures (Phase 4)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_green_artifact(sample_red_artifact):
    """Create a sample GREEN phase artifact for REFACTOR tests."""
    return {
        "spec_id": sample_red_artifact["spec_id"],
        "request_id": sample_red_artifact["request_id"],
        "implementation_files": [
            "src/auth/oauth_provider.py",
            "src/auth/token_manager.py",
        ],
        "test_files": sample_red_artifact["test_files"],
        "test_results": {
            "passed": 3,
            "failed": 0,
            "errors": 0,
            "total": 3,
            "exit_code": 0,
            "output": "3 passed in 0.05s",
            "test_details": [
                {"name": "test_authenticate", "status": "passed"},
                {"name": "test_invalid_code", "status": "passed"},
                {"name": "test_refresh", "status": "passed"},
            ],
        },
        "passing_tests": 3,
        "iterations": 3,
        "all_tests_pass": True,
        "acceptance_criteria": [
            {"criterion": "OAuth flow completes successfully"},
            {"criterion": "Tokens are securely stored"},
        ],
        "clarified_requirements": "Add OAuth2 authentication using Google as the provider",
        "original_request": "Add OAuth2 authentication",
    }


@pytest.fixture
def sample_refactor_artifact(sample_green_artifact):
    """Create a sample REFACTOR phase artifact for DELIVER tests."""
    return {
        "spec_id": sample_green_artifact["spec_id"],
        "request_id": sample_green_artifact["request_id"],
        "refactored_files": [
            {
                "path": "src/auth/oauth_provider.py",
                "changes": "Improved docstrings and type hints",
            }
        ],
        "improvements": [
            {
                "type": "documentation",
                "description": "Added docstrings to all public methods",
                "file": "src/auth/oauth_provider.py",
            },
            {
                "type": "typing",
                "description": "Added type hints",
                "file": "src/auth/oauth_provider.py",
            },
        ],
        "final_files": [
            "src/auth/oauth_provider.py",
            "src/auth/token_manager.py",
            "tests/unit/auth/test_oauth_provider.py",
        ],
        "test_results": {
            "passed": 3,
            "failed": 0,
            "total": 3,
        },
        "conformance_passed": True,
        "remaining_violations": [],
        "clarified_requirements": sample_green_artifact.get("clarified_requirements"),
        "original_request": sample_green_artifact.get("original_request"),
    }


@pytest.fixture
def mock_conformance_passing():
    """Mock conformance check that passes."""
    return {
        "passed": True,
        "violations": [],
        "total_violations": 0,
    }


@pytest.fixture
def mock_conformance_violations():
    """Mock conformance check with violations."""
    return {
        "passed": False,
        "violations": [
            {
                "type": "complexity",
                "file": "src/auth/oauth_provider.py",
                "line": 45,
                "message": "Function complexity too high (12 > 10)",
            },
            {
                "type": "missing_docstring",
                "file": "src/auth/oauth_provider.py",
                "line": 10,
                "message": "Missing docstring for public method 'authenticate'",
            },
        ],
        "total_violations": 2,
    }


@pytest.fixture
def temp_git_project(tmp_path):
    """Create a temporary project with git initialized."""
    import subprocess

    # Create basic directories
    (tmp_path / "src" / "auth").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "auth").mkdir(parents=True)
    (tmp_path / ".agentforge" / "patches").mkdir(parents=True)

    # Create __init__.py files
    (tmp_path / "src" / "__init__.py").write_text("")
    (tmp_path / "src" / "auth" / "__init__.py").write_text("")
    (tmp_path / "tests" / "__init__.py").write_text("")
    (tmp_path / "tests" / "unit" / "__init__.py").write_text("")
    (tmp_path / "tests" / "unit" / "auth" / "__init__.py").write_text("")

    # Initialize git
    try:
        subprocess.run(
            ["git", "init"],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )
        # Initial commit
        subprocess.run(
            ["git", "add", "."],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # Git may not be available in test environment

    return tmp_path
