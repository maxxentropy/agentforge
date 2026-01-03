# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
# @component_id: llm-factory-tests

"""
Tests for LLMClientFactory.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from agentforge.core.llm.factory import LLMClientFactory, LLMClientMode
from agentforge.core.llm.simulated import SimulatedLLMClient


class TestLLMClientMode:
    """Tests for LLMClientMode enum."""

    def test_mode_values(self):
        """LLMClientMode should have expected values."""
        assert LLMClientMode.REAL.value == "real", "Expected LLMClientMode.REAL.value to equal 'real'"
        assert LLMClientMode.SIMULATED.value == "simulated", "Expected LLMClientMode.SIMULATED.value to equal 'simulated'"
        assert LLMClientMode.RECORD.value == "record", "Expected LLMClientMode.RECORD.value to equal 'record'"
        assert LLMClientMode.PLAYBACK.value == "playback", "Expected LLMClientMode.PLAYBACK.value to equal 'playback'"

    def test_string_subclass(self):
        """LLMClientMode should work as string."""
        assert LLMClientMode.SIMULATED == "simulated", "Expected LLMClientMode.SIMULATED to equal 'simulated'"


class TestLLMClientFactorySimulated:
    """Tests for factory in simulated mode."""

    def test_create_simulated_explicit(self):
        """Factory should create simulated client with explicit mode."""
        client = LLMClientFactory.create(mode="simulated")

        assert isinstance(client, SimulatedLLMClient), "Expected isinstance() to be truthy"

    def test_create_simulated_from_env(self):
        """Factory should read mode from environment."""
        with patch.dict(os.environ, {"AGENTFORGE_LLM_MODE": "simulated"}):
            client = LLMClientFactory.create()

            assert isinstance(client, SimulatedLLMClient), "Expected isinstance() to be truthy"

    def test_create_simulated_with_script(self):
        """Factory should load script file when provided."""
        script = {
            "responses": [
                {"content": "From script"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(script, f)
            f.flush()

            client = LLMClientFactory.create(
                mode="simulated",
                script_path=Path(f.name),
            )

            response = client.complete(system="", messages=[])
            assert response.content == "From script", "Expected response.content to equal 'From script'"

    def test_simulated_script_from_env(self):
        """Factory should read script path from environment."""
        script = {"responses": [{"content": "Env script"}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(script, f)
            f.flush()

            with patch.dict(os.environ, {
                "AGENTFORGE_LLM_MODE": "simulated",
                "AGENTFORGE_LLM_SCRIPT": f.name,
            }):
                client = LLMClientFactory.create()
                response = client.complete(system="", messages=[])
                assert response.content == "Env script", "Expected response.content to equal 'Env script'"

    def test_missing_script_raises(self):
        """Factory should raise when script file not found."""
        with pytest.raises(ValueError, match="not found"):
            LLMClientFactory.create(
                mode="simulated",
                script_path=Path("/nonexistent/script.yaml"),
            )


class TestLLMClientFactoryTesting:
    """Tests for create_for_testing helper."""

    def test_create_with_responses_list(self):
        """create_for_testing should accept simple response list."""
        client = LLMClientFactory.create_for_testing(responses=[
            {"content": "Response 1"},
            {"tool_calls": [{"name": "test", "input": {}}]},
        ])

        r1 = client.complete(system="", messages=[])
        r2 = client.complete(system="", messages=[])

        assert r1.content == "Response 1", "Expected r1.content to equal 'Response 1'"
        assert r2.tool_calls[0].name == "test", "Expected r2.tool_calls[0].name to equal 'test'"

    def test_create_with_script_data(self):
        """create_for_testing should accept full script format."""
        client = LLMClientFactory.create_for_testing(script_data={
            "metadata": {"name": "Test"},
            "responses": [
                {"step": 1, "content": "Step one"},
            ],
        })

        response = client.complete(system="", messages=[])
        assert response.content == "Step one", "Expected response.content to equal 'Step one'"

    def test_create_empty(self):
        """create_for_testing with no args should create default client."""
        client = LLMClientFactory.create_for_testing()

        response = client.complete(system="", messages=[])
        # Should get default response
        assert response is not None, "Expected response is not None"


class TestLLMClientFactoryPlayback:
    """Tests for factory in playback mode."""

    def test_playback_loads_recording(self):
        """Factory should load recording file for playback."""
        recording = {
            "responses": [
                {"content": "Recorded response", "tool_calls": []},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(recording, f)
            f.flush()

            client = LLMClientFactory.create(
                mode="playback",
                recording_path=Path(f.name),
            )

            response = client.complete(system="", messages=[])
            assert response.content == "Recorded response", "Expected response.content to equal 'Recorded response'"

    def test_playback_missing_path_raises(self):
        """Factory should raise when recording path missing."""
        with pytest.raises(ValueError, match="required for playback"):
            LLMClientFactory.create(mode="playback")

    def test_playback_missing_file_raises(self):
        """Factory should raise when recording file not found."""
        with pytest.raises(ValueError, match="not found"):
            LLMClientFactory.create(
                mode="playback",
                recording_path=Path("/nonexistent/recording.yaml"),
            )


class TestLLMClientFactoryReal:
    """Tests for factory in real mode."""

    def test_real_without_api_key_raises(self):
        """Factory should raise when API key missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing API key
            os.environ.pop("ANTHROPIC_API_KEY", None)

            with pytest.raises(ValueError, match="API key"):
                LLMClientFactory.create(mode="real")

    def test_real_with_api_key_creates_client(self):
        """Factory should create real client with API key."""
        # This test just verifies the factory path, doesn't make real API calls
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-key"}):
            # Import here to avoid dependency issues
            from agentforge.core.llm.client import AnthropicLLMClient

            client = LLMClientFactory.create(mode="real")
            assert isinstance(client, AnthropicLLMClient), "Expected isinstance() to be truthy"


class TestLLMClientFactoryRecord:
    """Tests for factory in record mode."""

    def test_record_without_api_key_raises(self):
        """Factory should raise when API key missing for record."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)

            with pytest.raises(ValueError, match="API key"):
                LLMClientFactory.create(
                    mode="record",
                    recording_path=Path("/tmp/test.yaml"),
                )

    def test_record_without_path_raises(self):
        """Factory should raise when recording path missing."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            with pytest.raises(ValueError, match="required for record"):
                LLMClientFactory.create(mode="record")


class TestLLMClientFactoryHelpers:
    """Tests for factory helper methods."""

    def test_get_current_mode_default(self):
        """get_current_mode should return 'real' by default."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AGENTFORGE_LLM_MODE", None)

            assert LLMClientFactory.get_current_mode() == "real", "Expected LLMClientFactory.get_curren... to equal 'real'"

    def test_get_current_mode_from_env(self):
        """get_current_mode should read from environment."""
        with patch.dict(os.environ, {"AGENTFORGE_LLM_MODE": "simulated"}):
            assert LLMClientFactory.get_current_mode() == "simulated", "Expected LLMClientFactory.get_curren... to equal 'simulated'"

    def test_is_simulated_true(self):
        """is_simulated should return True for simulated/playback."""
        with patch.dict(os.environ, {"AGENTFORGE_LLM_MODE": "simulated"}):
            assert LLMClientFactory.is_simulated() is True, "Expected LLMClientFactory.is_simulat... is True"

        with patch.dict(os.environ, {"AGENTFORGE_LLM_MODE": "playback"}):
            assert LLMClientFactory.is_simulated() is True, "Expected LLMClientFactory.is_simulat... is True"

    def test_is_simulated_false(self):
        """is_simulated should return False for real/record."""
        with patch.dict(os.environ, {"AGENTFORGE_LLM_MODE": "real"}):
            assert LLMClientFactory.is_simulated() is False, "Expected LLMClientFactory.is_simulat... is False"

        with patch.dict(os.environ, {"AGENTFORGE_LLM_MODE": "record"}):
            assert LLMClientFactory.is_simulated() is False, "Expected LLMClientFactory.is_simulat... is False"


class TestLLMClientFactoryValidation:
    """Tests for factory input validation."""

    def test_invalid_mode_raises(self):
        """Factory should raise for invalid mode."""
        with pytest.raises(ValueError, match="Invalid LLM mode"):
            LLMClientFactory.create(mode="invalid_mode")

    def test_mode_case_insensitive(self):
        """Factory should accept modes in any case."""
        client = LLMClientFactory.create(mode="SIMULATED")
        assert isinstance(client, SimulatedLLMClient), "Expected isinstance() to be truthy"

        client = LLMClientFactory.create(mode="Simulated")
        assert isinstance(client, SimulatedLLMClient), "Expected isinstance() to be truthy"
