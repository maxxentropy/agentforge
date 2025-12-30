"""Shared pytest fixtures for AgentForge test suite."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import sys

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))


# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a sample Python file for testing."""
    test_file = tmp_path / "sample.py"
    test_file.write_text('''"""Sample module for testing."""

def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}"

class Calculator:
    """Simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
''')
    return test_file


@pytest.fixture
def sample_python_with_errors(tmp_path: Path) -> Path:
    """Create a Python file with type errors for testing."""
    test_file = tmp_path / "errors.py"
    test_file.write_text('''"""Sample module with type errors."""

def add(a: int, b: int) -> int:
    return "not an int"  # Type error

def greet(name: str) -> str:
    return 42  # Type error
''')
    return test_file


@pytest.fixture
def sample_long_function(tmp_path: Path) -> Path:
    """Create a Python file with a long function for testing."""
    lines = ['def long_function():']
    lines.extend([f'    x = {i}' for i in range(60)])
    lines.append('    return x')

    test_file = tmp_path / "long_func.py"
    test_file.write_text('\n'.join(lines))
    return test_file


@pytest.fixture
def sample_deeply_nested(tmp_path: Path) -> Path:
    """Create a Python file with deeply nested code."""
    test_file = tmp_path / "nested.py"
    test_file.write_text('''
def deep_nesting():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return "too deep"
''')
    return test_file


@pytest.fixture
def sample_clean_architecture(tmp_path: Path) -> Path:
    """Create a sample clean architecture project structure."""
    # Domain layer
    domain_dir = tmp_path / "src" / "domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "__init__.py").write_text("")
    (domain_dir / "entity.py").write_text('''
class User:
    """Domain entity."""
    def __init__(self, name: str):
        self.name = name
''')

    # Application layer
    app_dir = tmp_path / "src" / "application"
    app_dir.mkdir(parents=True)
    (app_dir / "__init__.py").write_text("")
    (app_dir / "service.py").write_text('''
from domain.entity import User

class UserService:
    def create_user(self, name: str) -> User:
        return User(name)
''')

    # Infrastructure layer
    infra_dir = tmp_path / "src" / "infrastructure"
    infra_dir.mkdir(parents=True)
    (infra_dir / "__init__.py").write_text("")
    (infra_dir / "repository.py").write_text('''
from domain.entity import User
from application.service import UserService

class UserRepository:
    def save(self, user: User) -> None:
        pass
''')

    return tmp_path


@pytest.fixture
def sample_layer_violation(tmp_path: Path) -> Path:
    """Create a C# file with a layer violation."""
    # Domain importing from infrastructure (C# syntax)
    domain_dir = tmp_path / "src" / "domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "BadEntity.cs").write_text('''
using Infrastructure.Repository;

namespace Domain
{
    public class BadEntity
    {
    }
}
''')
    return tmp_path


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def correctness_config() -> dict:
    """Return a minimal correctness config for testing."""
    return {
        "settings": {
            "working_dir": ".",
            "default_timeout": 30,
            "include_patterns": ["**/*.py"],
            "exclude_patterns": ["**/test_*.py", "**/__pycache__/**"]
        },
        "checks": [
            {
                "id": "test_command_success",
                "name": "Echo Test",
                "type": "command",
                "command": "echo 'hello'",
                "severity": "advisory"
            },
            {
                "id": "test_regex_match",
                "name": "Class Pattern",
                "type": "regex",
                "patterns": [{"name": "class", "pattern": r"class \w+"}],
                "file_patterns": ["**/*.py"],
                "severity": "advisory"
            },
            {
                "id": "test_file_exists",
                "name": "File Exists",
                "type": "file_exists",
                "files": ["sample.py"],
                "severity": "advisory"
            },
            {
                "id": "test_depends_on_success",
                "name": "Dependent Check",
                "type": "command",
                "command": "echo 'dependent'",
                "depends_on": ["test_command_success"],
                "severity": "advisory"
            }
        ],
        "profiles": {
            "quick": {"checks": ["test_command_success"]},
            "full": {"checks": ["test_command_success", "test_regex_match", "test_file_exists"]}
        }
    }


@pytest.fixture
def empty_config() -> dict:
    """Return an empty config for edge case testing."""
    return {"checks": [], "profiles": {}}


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run to return success."""
    with patch('subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=0,
            stdout="Success output",
            stderr=""
        )
        yield mock


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run to return failure."""
    with patch('subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: command failed"
        )
        yield mock


@pytest.fixture
def mock_subprocess_timeout():
    """Mock subprocess.run to raise TimeoutExpired."""
    import subprocess
    with patch('subprocess.run') as mock:
        mock.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=30)
        yield mock


@pytest.fixture
def mock_subprocess_not_found():
    """Mock subprocess.run for missing command."""
    with patch('subprocess.run') as mock:
        mock.side_effect = FileNotFoundError("Command not found")
        yield mock


@pytest.fixture
def mock_token_counter():
    """Mock token counter to return deterministic values."""
    def _count(text: str) -> int:
        # Approximate: 1 token per 4 characters
        return len(text) // 4
    return _count


# =============================================================================
# Verification Runner Fixtures
# =============================================================================

@pytest.fixture
def verification_runner(tmp_path: Path, correctness_config: dict):
    """Create a configured VerificationRunner instance."""
    from verification_runner import VerificationRunner

    # Write config to temp file
    import yaml
    config_path = tmp_path / "correctness.yaml"
    config_path.write_text(yaml.dump(correctness_config))

    runner = VerificationRunner(
        config_path=config_path,
        project_root=tmp_path
    )
    return runner


@pytest.fixture
def verification_runner_no_config(tmp_path: Path):
    """Create a VerificationRunner without config file."""
    from verification_runner import VerificationRunner
    return VerificationRunner(project_root=tmp_path)


# =============================================================================
# Context Retrieval Fixtures
# =============================================================================

@pytest.fixture
def context_retriever_config() -> dict:
    """Return a config for ContextRetriever testing."""
    return {
        "budget_tokens": 4000,
        "include_patterns": ["**/*.py"],
        "exclude_patterns": ["**/test_*.py"],
        "layer_detection": True
    }


@pytest.fixture
def mock_lsp_symbols():
    """Return mock LSP document symbols response."""
    return [
        {
            "name": "Calculator",
            "kind": 5,  # Class
            "range": {
                "start": {"line": 5, "character": 0},
                "end": {"line": 20, "character": 0}
            },
            "children": [
                {
                    "name": "add",
                    "kind": 6,  # Method
                    "range": {
                        "start": {"line": 7, "character": 4},
                        "end": {"line": 9, "character": 0}
                    }
                },
                {
                    "name": "divide",
                    "kind": 6,
                    "range": {
                        "start": {"line": 11, "character": 4},
                        "end": {"line": 15, "character": 0}
                    }
                }
            ]
        }
    ]


@pytest.fixture
def mock_embeddings():
    """Return deterministic mock embeddings."""
    def _embed(texts):
        import hashlib
        vectors = []
        for text in texts:
            h = hashlib.md5(text.encode()).hexdigest()
            vector = [int(h[i:i+4], 16) / 65535.0 for i in range(0, 32, 4)]
            vectors.append(vector)
        return vectors
    return _embed


# =============================================================================
# Helper Fixtures
# =============================================================================

@pytest.fixture
def create_temp_files(tmp_path: Path):
    """Factory fixture to create temporary files."""
    created_files = []

    def _create(filename: str, content: str) -> Path:
        file_path = tmp_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        created_files.append(file_path)
        return file_path

    yield _create

    # Cleanup is handled by tmp_path


@pytest.fixture
def custom_check_function(tmp_path: Path):
    """Create a custom check function module for testing."""
    module_path = tmp_path / "custom_checks.py"
    module_path.write_text('''
def check_always_pass(**kwargs):
    """Custom check that always passes."""
    return {"passed": True, "message": "Check passed"}

def check_always_fail(**kwargs):
    """Custom check that always fails."""
    return {"passed": False, "message": "Check failed", "errors": [{"message": "Intentional failure"}]}

def check_raises_exception(**kwargs):
    """Custom check that raises an exception."""
    raise RuntimeError("Intentional exception for testing")

def check_returns_bool(**kwargs):
    """Custom check that returns a boolean."""
    return True
''')
    return module_path
