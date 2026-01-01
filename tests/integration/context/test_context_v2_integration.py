# @spec_file: .agentforge/specs/core-context-v1.yaml
# @spec_id: core-context-v1
# @component_id: context-v2-integration-tests

"""
Integration Tests for Context Management V2

These tests verify the full context management stack works together:
- AgentConfigLoader + FingerprintGenerator + Templates
- CompactionManager + ContextAuditLogger
- MinimalContextExecutorV2

Run with simulated LLM:
    pytest tests/integration/context/ -v

Run with real API (requires ANTHROPIC_API_KEY):
    pytest tests/integration/context/ -v --run-real-api

Environment Variables:
    AGENTFORGE_LLM_MODE: simulated|real|record|playback
    AGENTFORGE_CONTEXT_V2: true to enable v2
    ANTHROPIC_API_KEY: Required for real API tests
"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from agentforge.core.context import (
    AgentConfigLoader,
    CompactionManager,
    ContextAuditLogger,
    FingerprintGenerator,
    get_template_for_task,
)


class TestFullContextStack:
    """Integration tests for the complete context management stack."""

    @pytest.fixture
    def realistic_project(self):
        """Create a realistic Python project structure."""
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "my_project"
            project.mkdir()

            # Create realistic project structure
            (project / "src").mkdir()
            (project / "src" / "my_project").mkdir()
            (project / "src" / "my_project" / "__init__.py").write_text("")
            (project / "src" / "my_project" / "main.py").write_text(
                '''"""Main entry point."""

def main():
    """Run the application."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
            )

            (project / "tests").mkdir()
            (project / "tests" / "__init__.py").write_text("")
            (project / "tests" / "test_main.py").write_text(
                '''"""Tests for main module."""

def test_main():
    """Test main function."""
    assert True
'''
            )

            # Create pyproject.toml
            (project / "pyproject.toml").write_text(
                '''[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0.0",
    "pytest>=7.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
'''
            )

            # Create .agentforge config
            (project / ".agentforge").mkdir()
            (project / ".agentforge" / "AGENT.md").write_text(
                '''---
preferences:
  communication_style: technical
  risk_tolerance: conservative
defaults:
  max_steps: 25
  require_tests: true
constraints:
  - "Always run tests after changes"
  - "Prefer small, focused changes"
---

# Project Configuration

This is my Python project.
'''
            )

            # Create task-specific config
            (project / ".agentforge" / "tasks").mkdir()
            (project / ".agentforge" / "tasks" / "fix_violation.md").write_text(
                '''---
defaults:
  max_steps: 30
constraints:
  - "Verify fix with check command"
---

# Fix Violation Task

Use semantic refactoring tools when available.
'''
            )

            yield project

    def test_config_fingerprint_template_integration(self, realistic_project):
        """Test that config, fingerprint, and template work together."""
        # Load config
        config_loader = AgentConfigLoader(realistic_project)
        config = config_loader.load(task_type="fix_violation")

        # Generate fingerprint
        fingerprint_gen = FingerprintGenerator(realistic_project)
        fingerprint = fingerprint_gen.with_task_context(
            task_type="fix_violation",
            constraints={"correctness_first": True},
            success_criteria=config.constraints,
        )

        # Get template
        template = get_template_for_task("fix_violation")

        # Verify integration
        assert config.defaults.max_steps == 30  # Task-specific override
        assert "Verify fix with check command" in config.constraints
        assert fingerprint.technical.language == "python"
        assert "pydantic" in fingerprint.technical.frameworks
        assert template.task_type == "fix_violation"

        # Verify fingerprint YAML includes constraints
        yaml_output = fingerprint.to_context_yaml()
        assert "correctness_first" in yaml_output

    def test_compaction_with_realistic_context(self, realistic_project):
        """Test compaction with realistic context sizes."""
        # Create a large context that needs compaction
        large_context = {
            "fingerprint": "project: test\nlanguage: python\n",
            "task": {"id": "test-001", "goal": "Fix complexity"},
            "phase": {"current": "implement"},
            "target_source": "def foo():\n" + "    pass\n" * 200,  # ~600 lines
            "similar_fixes": [
                {"name": f"fix_{i}", "description": "x" * 100}
                for i in range(20)
            ],
            "understanding": [
                {"fact": f"fact_{i}", "confidence": 0.8}
                for i in range(30)
            ],
            "recent": [{"action": f"action_{i}"} for i in range(10)],
        }

        # Create manager with tight budget
        manager = CompactionManager(threshold=0.80, max_budget=500)

        # Should need compaction
        assert manager.needs_compaction(large_context)

        # Compact
        result, audit = manager.compact(large_context)

        # Verify preserved sections
        assert result["fingerprint"] == large_context["fingerprint"]
        assert result["task"] == large_context["task"]
        assert result["phase"] == large_context["phase"]

        # Verify compaction occurred
        assert audit.original_tokens > audit.final_tokens
        assert len(audit.rules_applied) > 0

    def test_audit_captures_full_workflow(self, realistic_project):
        """Test that audit logger captures complete workflow."""
        task_id = "test-workflow-001"
        logger = ContextAuditLogger(realistic_project, task_id)

        # Simulate a 3-step workflow
        for step in range(1, 4):
            context = {
                "step": step,
                "action": f"action_{step}",
                "result": "success" if step < 3 else "complete",
            }
            token_breakdown = {"action": 50, "result": 30}

            logger.log_step(
                step=step,
                context=context,
                token_breakdown=token_breakdown,
                thinking=f"Thinking about step {step}..." if step == 2 else None,
                response=f"Executed action_{step}",
            )

        # Log summary
        logger.log_task_summary(
            total_steps=3,
            final_status="completed",
            total_tokens=3000,
            cached_tokens=1000,
        )

        # Verify all steps captured
        steps = logger.list_steps()
        assert steps == [1, 2, 3]

        # Verify thinking captured for step 2
        thinking = logger.get_thinking(2)
        assert thinking is not None
        assert "step 2" in thinking

        # Verify summary
        summary = logger.get_summary()
        assert summary["total_steps"] == 3
        assert summary["final_status"] == "completed"
        assert summary["effective_tokens"] == 3000 - int(1000 * 0.9)

        # Verify audit directory structure
        audit_dir = realistic_project / ".agentforge" / "context_audit" / task_id
        assert (audit_dir / "summary.yaml").exists()
        assert (audit_dir / "step_1.yaml").exists()
        assert (audit_dir / "step_1_context.yaml").exists()
        assert (audit_dir / "step_2_thinking.md").exists()

    def test_template_token_budgets(self, realistic_project):
        """Test that template token budgets are reasonable."""
        for task_type in ["fix_violation", "implement_feature"]:
            template = get_template_for_task(task_type)

            # Check total budget
            total = template.get_total_budget()
            assert 2000 < total < 5000, f"{task_type} budget {total} out of range"

            # Check each phase
            for phase in template.phases:
                tier2 = template.get_tier2_for_phase(phase)
                assert tier2.max_tokens > 0
                assert tier2.max_tokens <= 2500

            # Check system prompt is cacheable
            prompt = template.get_system_prompt()
            prompt_tokens = len(prompt) // 4
            assert prompt_tokens < 200, f"{task_type} prompt {prompt_tokens} too large"

    def test_fingerprint_caching(self, realistic_project):
        """Test that fingerprint is properly cached."""
        gen = FingerprintGenerator(realistic_project)

        # First call generates
        fp1 = gen.generate()

        # Second call uses cache (same object)
        fp2 = gen.generate()
        assert fp1 is fp2

        # Force refresh creates new object
        fp3 = gen.generate(force_refresh=True)
        assert fp3 is not fp1

        # Clear cache
        FingerprintGenerator.clear_cache()
        fp4 = gen.generate()
        assert fp4 is not fp3

    def test_config_hierarchy_merging(self, realistic_project):
        """Test that config hierarchy merges correctly."""
        loader = AgentConfigLoader(realistic_project)

        # Load without task type
        base_config = loader.load()
        assert base_config.defaults.max_steps == 25  # From project AGENT.md

        # Load with task type
        loader.invalidate_cache()
        task_config = loader.load(task_type="fix_violation")
        assert task_config.defaults.max_steps == 30  # Overridden by task

        # Constraints accumulate
        assert "Always run tests after changes" in task_config.constraints
        assert "Verify fix with check command" in task_config.constraints


class TestContextReproducibility:
    """Tests for context reproducibility via hashing."""

    @pytest.fixture
    def temp_project(self):
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test"
            project.mkdir()
            (project / ".agentforge").mkdir()
            yield project

    def test_same_context_same_hash(self, temp_project):
        """Same context produces same hash."""
        logger = ContextAuditLogger(temp_project, "test-task")

        context = {"data": "test", "nested": {"value": 123}}

        hash1 = logger._hash_context(context)
        hash2 = logger._hash_context(context)

        assert hash1 == hash2

    def test_different_context_different_hash(self, temp_project):
        """Different context produces different hash."""
        logger = ContextAuditLogger(temp_project, "test-task")

        context1 = {"data": "test1"}
        context2 = {"data": "test2"}

        hash1 = logger._hash_context(context1)
        hash2 = logger._hash_context(context2)

        assert hash1 != hash2

    def test_hash_is_deterministic(self, temp_project):
        """Hash is deterministic across logger instances."""
        context = {"complex": {"nested": [1, 2, 3], "string": "value"}}

        logger1 = ContextAuditLogger(temp_project, "task-1")
        logger2 = ContextAuditLogger(temp_project, "task-2")

        hash1 = logger1._hash_context(context)
        hash2 = logger2._hash_context(context)

        assert hash1 == hash2


@pytest.mark.real_api
class TestRealAPIIntegration:
    """
    Tests that require real API access.

    Run with: pytest tests/integration/context/ --run-real-api
    Requires: ANTHROPIC_API_KEY environment variable
    """

    @pytest.fixture
    def temp_project(self):
        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test_project"
            project.mkdir()
            (project / ".agentforge").mkdir()
            (project / "pyproject.toml").write_text(
                "[project]\nname = 'test'\n"
            )
            yield project

    def test_llm_client_factory_creates_real_client(self, temp_project):
        """Test that factory creates real client when mode is 'real'."""
        # Skip if no API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        from agentforge.core.llm import LLMClientFactory, LLMClientMode

        client = LLMClientFactory.create(mode=LLMClientMode.REAL)

        # Should be able to make a simple call
        response = client.complete(
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        )

        assert response.content is not None
        assert "hello" in response.content.lower()

    def test_executor_v2_with_real_api(self, temp_project):
        """Test executor v2 with real API."""
        # Skip if no API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        from agentforge.core.harness.minimal_context import create_executor_v2

        executor = create_executor_v2(
            project_path=temp_project,
            task_type="fix_violation",
        )

        # Verify components are initialized
        assert executor.config is not None
        assert executor.template is not None
        assert executor.fingerprint_generator is not None

        # Get fingerprint
        fp = executor.get_fingerprint()
        assert fp.technical.language == "python"
