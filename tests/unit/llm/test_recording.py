# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
# @component_id: core-llm-recording

"""
Tests for RecordingLLMClient.

TODO: Add comprehensive tests for recording/playback functionality.
"""



class TestRecordingLLMClient:
    """Tests for RecordingLLMClient."""

    def test_recording_client_import(self):
        """Verify RecordingLLMClient can be imported."""
        from agentforge.core.llm.recording import RecordingLLMClient
        assert RecordingLLMClient is not None

    def test_recording_client_has_expected_methods(self):
        """Recording client should have expected interface methods."""
        from agentforge.core.llm.recording import RecordingLLMClient
        assert hasattr(RecordingLLMClient, 'complete')
        assert hasattr(RecordingLLMClient, 'save')
        assert hasattr(RecordingLLMClient, 'get_recording')
