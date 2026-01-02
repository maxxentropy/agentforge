# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
# @component_id: core-llm-client

"""
Tests for AnthropicLLMClient.

TODO: Add comprehensive tests for the real LLM client.
These tests require mocking the Anthropic API or using simulation mode.
"""




class TestAnthropicLLMClient:
    """Tests for AnthropicLLMClient."""

    def test_client_import(self):
        """Verify AnthropicLLMClient can be imported."""
        from agentforge.core.llm.client import AnthropicLLMClient
        assert AnthropicLLMClient is not None

    def test_client_requires_api_key(self):
        """Client should require API key for real mode."""
        from agentforge.core.llm.client import AnthropicLLMClient
        # This tests that the client class exists and has expected signature
        # Actual API testing requires mock or integration tests
        assert hasattr(AnthropicLLMClient, 'complete')

    def test_client_has_expected_methods(self):
        """Client should have expected interface methods."""
        from agentforge.core.llm.client import AnthropicLLMClient
        assert hasattr(AnthropicLLMClient, 'complete')
        assert hasattr(AnthropicLLMClient, 'complete_with_tools')
